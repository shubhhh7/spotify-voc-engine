"""
Google Gemini API client for insight generation.
"""
import json
import re
import logging

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)


def _get_api_key():
    """Get Gemini API key from database (Settings page) or .env fallback."""
    # Try database first (set via the Settings page in the UI)
    try:
        from database import SessionLocal
        from models import Setting
        db = SessionLocal()
        row = db.query(Setting).filter(Setting.key == "gemini_api_key").first()
        db.close()
        if row and row.value:
            return row.value
    except Exception:
        pass

    # Fallback to .env / environment variable
    return settings.gemini_api_key


def _configure():
    """Configure the Gemini SDK with API key."""
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured. Set it in Settings.")
    genai.configure(api_key=api_key)


def _parse_json_response(text: str):
    """Parse JSON from Gemini response, handling markdown code fences."""
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (```json or ```)
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
        # Remove closing fence
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object/array in the text
        match = re.search(r"[\[{].*[\]}]", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        # Return as wrapped object if parsing fails
        logger.warning("Failed to parse JSON from Gemini response, returning raw text")
        return {"raw_response": text, "parse_error": True}


def generate(prompt: str, model=None):
    """
    Generate content using Gemini and parse the JSON response.

    Args:
        prompt: The prompt to send to Gemini.
        model: Model name override. Defaults to gemini-1.5-flash from config.

    Returns:
        Parsed JSON response as dict or list.
    """
    _configure()

    model_name = model or settings.gemini_flash_model
    m = genai.GenerativeModel(model_name)

    logger.info(f"Generating with {model_name} (prompt length: {len(prompt)} chars)")

    try:
        response = m.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=8192,
            ),
            request_options={"timeout": 60},
        )
    except Exception as e:
        logger.error(f"Gemini generate_content failed: {e}")
        raise

    if not response.text:
        logger.error("Empty response from Gemini")
        return {"error": "Empty response from AI model"}

    return _parse_json_response(response.text)


def generate_pro(prompt: str):
    """Generate using the Pro model (for deeper analysis)."""
    return generate(prompt, model=settings.gemini_pro_model)
