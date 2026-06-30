"""
Multi-Provider LLM Service — Provider-agnostic completion with automatic failover.

Priority order: Gemini → Groq → Cerebras → OpenRouter
Supports retry with exponential backoff, prompt caching, concurrency control,
and automatic model fallback on rate limits or transient failures.
"""
import hashlib
import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Tuple

import requests

from config import settings

logger = logging.getLogger(__name__)

# ─── Constants ──────────────────────────────────────────────────────────────────

MAX_CONCURRENT_REQUESTS = 3
CACHE_TTL_SECONDS = 86400  # 24 hours
REQUEST_TIMEOUT = 60  # seconds

RETRYABLE_STATUS_CODES = {429, 500, 502, 503}
BACKOFF_SCHEDULE = [2, 4, 8]  # seconds per attempt

# ─── Provider Configs ───────────────────────────────────────────────────────────

GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]
GROQ_MODELS = ["llama-3.3-70b-versatile", "meta-llama/llama-4-scout-17b-16e-instruct"]
CEREBRAS_MODELS = ["qwen-3-235b-a22b", "llama-4-scout-17b-16e"]
OPENROUTER_MODELS = [
    "qwen/qwen3-235b-a22b:free",
    "deepseek/deepseek-r1-0528:free",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]


# ─── Data Types ─────────────────────────────────────────────────────────────────

@dataclass
class CompletionOptions:
    """Options for generate_completion."""
    system_prompt: str = "You are a senior product analyst. Return responses as valid JSON only. No markdown, no explanations."
    user_prompt: str = ""
    temperature: float = 0.2
    top_p: float = 0.9
    max_tokens: int = 4096
    json_mode: bool = True


@dataclass
class CompletionResult:
    """Result from a completion call."""
    content: Union[dict, list, str]
    provider: str
    model: str
    latency_ms: int
    tokens_used: Optional[int] = None
    retry_count: int = 0
    fallback_occurred: bool = False
    cached: bool = False


# ─── Cache ──────────────────────────────────────────────────────────────────────

_cache: Dict[str, Tuple[float, CompletionResult]] = {}
_cache_lock = threading.Lock()


def _cache_key(system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
    raw = f"{system_prompt}|{user_prompt}|{model}|{temperature}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_cached(key: str) -> Optional[CompletionResult]:
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry[0]) < CACHE_TTL_SECONDS:
            result = entry[1]
            result.cached = True
            return result
        if entry:
            del _cache[key]
    return None


def _set_cached(key: str, result: CompletionResult):
    with _cache_lock:
        _cache[key] = (time.time(), result)


# ─── Concurrency Control ────────────────────────────────────────────────────────

_semaphore = threading.Semaphore(MAX_CONCURRENT_REQUESTS)


# ─── JSON Parsing ───────────────────────────────────────────────────────────────

def _parse_json(text: str) -> Union[dict, list]:
    """Parse JSON from LLM response, handling markdown fences and common issues."""
    cleaned = text.strip()

    # Strip markdown code fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)

    # Strip leading/trailing non-JSON chars
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON object or array
    match = re.search(r"[\[{].*[\]}]", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("Cannot parse JSON from response", cleaned, 0)


# ─── Provider Implementations ───────────────────────────────────────────────────

def _get_api_key_from_db(key_name: str) -> str:
    """Try to get API key from the settings database table."""
    try:
        from database import SessionLocal
        from models import Setting
        db = SessionLocal()
        row = db.query(Setting).filter(Setting.key == key_name).first()
        db.close()
        if row and row.value:
            return row.value
    except Exception:
        pass
    return ""


def _resolve_api_key(key_name: str, env_value: str) -> str:
    """Resolve API key: DB first, then env fallback."""
    db_key = _get_api_key_from_db(key_name)
    return db_key or env_value


def _call_gemini(prompt_system: str, prompt_user: str, model: str,
                 temperature: float, top_p: float, max_tokens: int) -> Tuple[str, Optional[int]]:
    """Call Google Gemini API. Returns (text_response, token_count)."""
    import google.generativeai as genai

    api_key = _resolve_api_key("gemini_api_key", settings.gemini_api_key)
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")

    genai.configure(api_key=api_key)
    m = genai.GenerativeModel(model, system_instruction=prompt_system)

    response = m.generate_content(
        prompt_user,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_tokens,
        ),
        request_options={"timeout": REQUEST_TIMEOUT},
    )

    if not response.text:
        raise ValueError("Empty response from Gemini")

    token_count = None
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        token_count = getattr(response.usage_metadata, "total_token_count", None)

    return response.text, token_count


def _call_groq(prompt_system: str, prompt_user: str, model: str,
               temperature: float, top_p: float, max_tokens: int) -> Tuple[str, Optional[int]]:
    """Call Groq API (OpenAI-compatible). Returns (text_response, token_count)."""
    api_key = _resolve_api_key("grok_api_key", settings.effective_groq_key)
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user},
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        },
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code != 200:
        raise _HttpError(response.status_code, response.text[:300])

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens")
    return content, tokens


def _call_cerebras(prompt_system: str, prompt_user: str, model: str,
                   temperature: float, top_p: float, max_tokens: int) -> Tuple[str, Optional[int]]:
    """Call Cerebras API (OpenAI-compatible). Returns (text_response, token_count)."""
    api_key = _resolve_api_key("cerebras_api_key", settings.cerebras_api_key)
    if not api_key:
        raise ValueError("CEREBRAS_API_KEY not configured")

    response = requests.post(
        "https://api.cerebras.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user},
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        },
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code != 200:
        raise _HttpError(response.status_code, response.text[:300])

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens")
    return content, tokens


def _call_openrouter(prompt_system: str, prompt_user: str, model: str,
                     temperature: float, top_p: float, max_tokens: int) -> Tuple[str, Optional[int]]:
    """Call OpenRouter API (OpenAI-compatible). Returns (text_response, token_count)."""
    api_key = _resolve_api_key("openrouter_api_key", settings.openrouter_api_key)
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not configured")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://spotify-voc.local",
            "X-Title": "Spotify VoC Platform",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user},
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        },
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code != 200:
        raise _HttpError(response.status_code, response.text[:300])

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens")
    return content, tokens


# ─── Error Types ────────────────────────────────────────────────────────────────

class _HttpError(Exception):
    """HTTP error with status code."""
    def __init__(self, status_code: int, body: str = ""):
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body}")

    @property
    def is_retryable(self) -> bool:
        return self.status_code in RETRYABLE_STATUS_CODES


class AllProvidersExhausted(Exception):
    """Raised when every provider has failed."""
    pass


# ─── Provider Registry ──────────────────────────────────────────────────────────

@dataclass
class _ProviderConfig:
    name: str
    call_fn: callable
    models: List[str]
    api_key_env: str

    def is_available(self) -> bool:
        """Check if provider has an API key configured."""
        if self.api_key_env == "groq_api_key":
            return bool(settings.effective_groq_key)
        # Check DB first, then env fallback
        db_key = _get_api_key_from_db(self.api_key_env)
        if db_key:
            return True
        env_key = getattr(settings, self.api_key_env, "")
        return bool(env_key)


def _get_providers() -> list[_ProviderConfig]:
    """Get ordered list of providers with their config."""
    providers = [
        _ProviderConfig(
            name="Gemini",
            call_fn=_call_gemini,
            models=([settings.gemini_model] if settings.gemini_model else []) + GEMINI_MODELS,
            api_key_env="gemini_api_key",
        ),
        _ProviderConfig(
            name="Groq",
            call_fn=_call_groq,
            models=([settings.groq_model] if settings.groq_model else []) + GROQ_MODELS,
            api_key_env="groq_api_key",
        ),
        _ProviderConfig(
            name="Cerebras",
            call_fn=_call_cerebras,
            models=([settings.cerebras_model] if settings.cerebras_model else []) + CEREBRAS_MODELS,
            api_key_env="cerebras_api_key",
        ),
        _ProviderConfig(
            name="OpenRouter",
            call_fn=_call_openrouter,
            models=([settings.openrouter_model] if settings.openrouter_model else []) + OPENROUTER_MODELS,
            api_key_env="openrouter_api_key",
        ),
    ]
    # Only return providers that have keys configured
    return [p for p in providers if p.is_available()]


# ─── Core Completion Logic ──────────────────────────────────────────────────────

def _attempt_provider(provider: _ProviderConfig, opts: CompletionOptions) -> CompletionResult:
    """
    Attempt completion with a single provider, trying each model in order.
    Retries on transient failures with exponential backoff.
    """
    last_error = None

    for model in _deduplicate(provider.models):
        retry_count = 0

        for attempt, backoff in enumerate(BACKOFF_SCHEDULE + [None]):
            try:
                start = time.time()
                text, tokens = provider.call_fn(
                    opts.system_prompt, opts.user_prompt, model,
                    opts.temperature, opts.top_p, opts.max_tokens,
                )
                latency_ms = int((time.time() - start) * 1000)

                logger.info(
                    f"✓ {provider.name} | Model: {model} | "
                    f"Latency: {latency_ms}ms | Tokens: {tokens or '?'} | "
                    f"Retries: {retry_count}"
                )

                return CompletionResult(
                    content=text,
                    provider=provider.name,
                    model=model,
                    latency_ms=latency_ms,
                    tokens_used=tokens,
                    retry_count=retry_count,
                )

            except _HttpError as e:
                last_error = e
                if e.is_retryable and backoff is not None:
                    retry_count += 1
                    logger.warning(
                        f"⚠ {provider.name} | {model} | HTTP {e.status_code} | "
                        f"Retry #{retry_count} in {backoff}s..."
                    )
                    time.sleep(backoff)
                    continue
                else:
                    # Non-retryable or retries exhausted for this model — try next model
                    logger.warning(
                        f"✗ {provider.name} | {model} | HTTP {e.status_code} | "
                        f"Switching to next model..."
                    )
                    break

            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e
                if backoff is not None:
                    retry_count += 1
                    logger.warning(
                        f"⚠ {provider.name} | {model} | {type(e).__name__} | "
                        f"Retry #{retry_count} in {backoff}s..."
                    )
                    time.sleep(backoff)
                    continue
                else:
                    break

            except Exception as e:
                last_error = e
                logger.warning(f"✗ {provider.name} | {model} | {type(e).__name__}: {e}")
                break  # Try next model

    # All models for this provider exhausted
    raise Exception(f"{provider.name} exhausted all models. Last error: {last_error}")


def _deduplicate(items: List[str]) -> List[str]:
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ─── Public API ─────────────────────────────────────────────────────────────────

def generate_completion(options: CompletionOptions) -> CompletionResult:
    """
    Generate an LLM completion with automatic provider failover.

    Tries providers in priority order: Gemini → Groq → Cerebras → OpenRouter.
    Each provider retries on transient failures (429, 500, 502, 503, timeout).
    If a provider is fully exhausted, moves to the next.

    Args:
        options: CompletionOptions with prompts and parameters.

    Returns:
        CompletionResult with the response content and metadata.

    Raises:
        AllProvidersExhausted: If every available provider has failed.
    """
    # Check cache first
    providers = _get_providers()
    if not providers:
        raise AllProvidersExhausted("No LLM providers configured. Set API keys in .env or Settings.")

    cache_model = providers[0].models[0] if providers else "unknown"
    ck = _cache_key(options.system_prompt, options.user_prompt, cache_model, options.temperature)
    cached = _get_cached(ck)
    if cached:
        logger.info(f"✓ Cache hit | Key: {ck[:12]}...")
        return cached

    # Acquire semaphore slot (concurrency control)
    _semaphore.acquire()
    try:
        errors = []
        fallback_occurred = False

        for i, provider in enumerate(providers):
            if i > 0:
                fallback_occurred = True
                logger.info(f"↓ Falling back to {provider.name}...")

            try:
                result = _attempt_provider(provider, options)
                result.fallback_occurred = fallback_occurred

                # Parse JSON if requested
                if options.json_mode:
                    try:
                        result.content = _parse_json(result.content)
                    except json.JSONDecodeError:
                        # Retry once with repair prompt
                        repaired = _attempt_json_repair(result.content, provider, options)
                        if repaired is not None:
                            result.content = repaired
                        else:
                            # Keep raw content as fallback
                            result.content = {"raw_response": result.content, "parse_error": True}

                # Cache successful result
                _set_cached(ck, result)
                return result

            except Exception as e:
                errors.append(f"{provider.name}: {e}")
                continue

        raise AllProvidersExhausted(
            f"All {len(providers)} providers failed. Errors:\n" +
            "\n".join(f"  • {err}" for err in errors)
        )
    finally:
        _semaphore.release()


def _attempt_json_repair(raw_text: str, provider: _ProviderConfig, opts: CompletionOptions):
    """Try to repair invalid JSON by asking the LLM to fix it."""
    repair_prompt = (
        f"The following text should be valid JSON but has formatting errors. "
        f"Fix it and return ONLY the valid JSON, nothing else:\n\n{raw_text[:3000]}"
    )
    try:
        repair_opts = CompletionOptions(
            system_prompt="Fix JSON syntax errors. Return only valid JSON.",
            user_prompt=repair_prompt,
            temperature=0.1,
            max_tokens=opts.max_tokens,
            json_mode=False,  # Avoid recursion
        )
        text, _ = provider.call_fn(
            repair_opts.system_prompt, repair_opts.user_prompt,
            provider.models[0], repair_opts.temperature, 0.9, repair_opts.max_tokens,
        )
        return _parse_json(text)
    except Exception:
        return None


# ─── Convenience Wrapper (drop-in replacement for old AI clients) ───────────────

def generate(prompt: str, temperature: float = 0.2) -> Union[dict, list]:
    """
    Simple interface matching the old gemini_generate/groq_generate signature.
    Returns parsed JSON response.

    This is the function that insight_service.py should call.
    """
    result = generate_completion(CompletionOptions(
        user_prompt=prompt,
        temperature=temperature,
        json_mode=True,
    ))
    return result.content


def generate_with_metadata(prompt: str, temperature: float = 0.2) -> tuple:
    """
    Like generate() but also returns the model identifier.
    Returns (parsed_content, model_name).
    """
    result = generate_completion(CompletionOptions(
        user_prompt=prompt,
        temperature=temperature,
        json_mode=True,
    ))
    return result.content, f"{result.provider}/{result.model}"
