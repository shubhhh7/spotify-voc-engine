"""
Application configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/spotify_voc"
    gemini_api_key: str = ""
    groq_api_key: str = ""
    # Keep the old field name as alias for backwards compat with DB lookups
    grok_api_key: str = ""
    cerebras_api_key: str = ""
    openrouter_api_key: str = ""
    environment: str = "development"

    # Scraper defaults
    reddit_post_limit: int = 75
    reddit_min_comments: int = 5
    appstore_count: int = 300
    playstore_count: int = 300

    # AI model overrides (optional — defaults used if empty)
    gemini_model: str = ""
    groq_model: str = ""
    cerebras_model: str = ""
    openrouter_model: str = ""

    # Legacy (kept for backwards compat)
    gemini_flash_model: str = "gemini-2.0-flash"
    gemini_pro_model: str = "gemini-2.5-flash"
    batch_size: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def effective_groq_key(self) -> str:
        """Return whichever Groq key is available (handles both spellings)."""
        return self.groq_api_key or self.grok_api_key


settings = Settings()
