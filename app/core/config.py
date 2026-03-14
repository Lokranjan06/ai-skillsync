"""
app/core/config.py
------------------
Centralised settings loaded from environment variables / .env file.
All configuration lives here — no scattered os.getenv() calls.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "AI SkillSync"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./skillsync.db"

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["*"]

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/skillsync.log"

    # ── AI / Model ───────────────────────────────────────────────────────────
    MODEL_RANDOM_SEED: int = 42
    MODEL_N_ESTIMATORS: int = 100

    # ── Cache TTL (seconds) ──────────────────────────────────────────────────
    CACHE_TTL_SKILL_GRAPH: int = 300   # 5 minutes
    CACHE_TTL_JOB_MATCHES: int = 120   # 2 minutes

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance — cached after first call."""
    return Settings()
