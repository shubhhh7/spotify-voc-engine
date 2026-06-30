"""
Groq API client for insight generation.
Uses the OpenAI-compatible API endpoint at api.groq.com.

Includes retry logic with exponential backoff for 429 rate limit errors.
"""
import json
import re
import time
import logging

import requests

from config import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Rate limiting - Groq free tier is 30 RPM
MAX_RETRIES = 2
INITIAL_BACKOFF_SECONDS = 5   # Start with 5s on first 429
BACKOFF_MULTIPLIER = 2        # Double each retry: 5s, 10s


def _parse_json_response(text: str):
    """Parse JSON from Groq response."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"[\[{].*[\]}]", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning("Failed to parse JSON from Groq response, returning raw text")
        return {"raw_response": text, "parse_error": True}


def _get_api_key():
    """Get Groq API key from database (Settings page) or .env fallback."""
    try:
        from database import SessionLocal
        from models import Setting
        db = SessionLocal()
        row = db.query(Setting).filter(Setting.key == "grok_api_key").first()
        db.close()
        if row and row.value:
            return row.value
    except Exception:
        pass
    return settings.grok_api_key


def generate(prompt: str, model: str = "llama-3.3-70b-versatile"):
    """
    Generate content using Groq API with automatic retry on rate limits.
    Falls back to smaller model if primary model hits daily token limit.

    Args:
        prompt: The prompt to send to Groq.
        model: Model name. Defaults to llama-3.3-70b-versatile.

    Returns:
        Parsed JSON response as dict or list.

    Raises:
        ValueError: If API key is not configured.
        Exception: If all retries and fallback models exhausted.
    """
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured. Set it in Settings.")

    # Try primary model first, then fallback to smaller model
    models_to_try = [model, "llama-3.1-8b-instant"]
    last_error = None

    for current_model in models_to_try:
        try:
            result = _call_groq(api_key, prompt, current_model)
            return result
        except _DailyLimitError as e:
            logger.warning(f"Daily limit hit for {current_model}, trying next model...")
            last_error = e
            continue
        except Exception as e:
            # For non-daily-limit errors, don't try other models
            raise

    # All models exhausted their daily limits
    raise Exception(f"All Groq models hit daily token limits. {last_error}")


class _DailyLimitError(Exception):
    """Raised when Groq daily token limit is hit."""
    pass


def _call_groq(api_key: str, prompt: str, model: str):
    """Make the actual Groq API call with retry logic for per-minute rate limits."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a senior product analyst. Return responses as valid JSON only. No markdown, no explanations.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    logger.info(f"Generating with Groq {model} (prompt length: {len(prompt)} chars)")

    last_error = None
    backoff = INITIAL_BACKOFF_SECONDS

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                if not content:
                    logger.error("Empty response from Groq")
                    return {"error": "Empty response from AI model"}
                return _parse_json_response(content)

            elif response.status_code == 429:
                # Rate limited - check if it's a daily limit (no point retrying)
                error_body = response.text or ""
                if "tokens per day" in error_body.lower() or "TPD" in error_body:
                    raise _DailyLimitError(
                        f"Groq daily token limit reached for {model}. Details: {error_body[:200]}"
                    )

                # Per-minute rate limit — wait and retry
                retry_after = response.headers.get("retry-after")
                wait_time = int(retry_after) if retry_after else backoff

                logger.warning(
                    f"Groq 429 rate limited (attempt {attempt+1}/{MAX_RETRIES}). "
                    f"Waiting {wait_time}s before retry..."
                )
                time.sleep(wait_time)
                backoff *= BACKOFF_MULTIPLIER
                last_error = f"429 Rate Limited (attempt {attempt+1})"
                continue

            elif response.status_code == 413:
                # Payload too large - no point retrying with same data
                raise requests.HTTPError(
                    f"413 Payload Too Large - reduce chunk size", response=response
                )

            else:
                # Other errors - raise immediately
                response.raise_for_status()

        except requests.HTTPError as e:
            if "429" in str(e):
                # Sometimes raise_for_status gives us the 429
                logger.warning(f"Groq rate limited (attempt {attempt+1}). Waiting {backoff}s...")
                time.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER
                last_error = e
                continue
            raise
        except requests.Timeout:
            logger.warning(f"Groq timeout (attempt {attempt+1}). Retrying in 10s...")
            time.sleep(10)
            last_error = Exception("Request timed out")
            continue

    # All retries exhausted
    raise Exception(
        f"Groq rate limit exceeded after {MAX_RETRIES} retries "
        f"(waited up to {INITIAL_BACKOFF_SECONDS * (BACKOFF_MULTIPLIER ** MAX_RETRIES)}s total). "
        f"Last error: {last_error}"
    )
