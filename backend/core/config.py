"""
MentorOS – Core Configuration
All values sourced from environment variables. Never hardcode secrets.
"""
import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List

log = logging.getLogger("mentoross.config")

# Determine the base directory (where .env lives for local dev)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "MentorOS API"
    APP_VERSION: str = "3.0.0"
    # Auto-detect production via Vercel env; fallback to explicit ENVIRONMENT var
    ENVIRONMENT: str = os.environ.get(
        "ENVIRONMENT",
        "production" if os.environ.get("VERCEL") else "development",
    )
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Security ─────────────────────────────────────────
    SECRET_KEY: str = "change-this-in-vercel-env-vars-minimum-32-chars-required"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24        # 24 hours
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    # CORS — defaults cover both local dev and the Vercel deployment
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "https://mentoross-two.vercel.app",
        "https://mentoross.vercel.app",
        "null",
    ]
    # Regex allows any Vercel preview URL (mentoross-*.vercel.app) and localhost
    ALLOW_ORIGIN_REGEX: str = r"https://mentoross.*\.vercel\.app|http://localhost:\d+"

    # ── Database ──────────────────────────────────────────
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "mentoross"

    # ── Custom AI Engine ─────────────────────────────────
    AI_MAX_TOKENS: int = 2048

    # ── Rate Limiting ────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    AI_RATE_LIMIT_PER_MINUTE: int = 10

    # ── Scheduler ────────────────────────────────────────
    REMINDER_INTERVAL_MINUTES: int = 60

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def warn_if_insecure(self) -> None:
        """Log warnings for insecure defaults — never raises, never crashes startup."""
        if self.is_production:
            if "localhost" in self.MONGODB_URI:
                log.warning(
                    "⚠️  MONGODB_URI points to localhost in production. "
                    "Set MONGODB_URI in Vercel → Settings → Environment Variables."
                )
            if "change-this-in-vercel" in self.SECRET_KEY:
                log.warning(
                    "⚠️  SECRET_KEY is using the insecure default. "
                    "Set SECRET_KEY in Vercel → Settings → Environment Variables."
                )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
