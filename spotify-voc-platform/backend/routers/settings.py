"""
Settings endpoints — get/update API keys and configuration.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Setting
from schemas import SettingsUpdate

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


def mask_key(key: str) -> str:
    """Mask an API key for display: 'sk-abc123def456' → 'sk-abc...456'"""
    if not key or len(key) < 8:
        return "***"
    return f"{key[:6]}...{key[-4:]}"


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    """Get all settings with masked API keys."""
    settings_dict = {}
    all_settings = db.query(Setting).all()
    for s in all_settings:
        if "key" in s.key.lower() or "secret" in s.key.lower():
            settings_dict[s.key] = mask_key(s.value)
        else:
            settings_dict[s.key] = s.value

    return {
        "gemini_api_key": settings_dict.get("gemini_api_key", ""),
        "grok_api_key": settings_dict.get("grok_api_key", ""),
        "has_gemini_key": bool(settings_dict.get("gemini_api_key")),
        "has_grok_key": bool(settings_dict.get("grok_api_key")),
    }


@router.put("")
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    """Update settings."""
    updated = []

    if data.gemini_api_key is not None:
        _upsert_setting(db, "gemini_api_key", data.gemini_api_key)
        updated.append("gemini_api_key")

    if data.grok_api_key is not None:
        _upsert_setting(db, "grok_api_key", data.grok_api_key)
        updated.append("grok_api_key")

    db.commit()
    return {"status": "updated", "keys": updated}


def _upsert_setting(db: Session, key: str, value: str):
    """Insert or update a setting."""
    existing = db.query(Setting).filter(Setting.key == key).first()
    if existing:
        existing.value = value
        existing.updated_at = datetime.utcnow()
    else:
        db.add(Setting(key=key, value=value))
