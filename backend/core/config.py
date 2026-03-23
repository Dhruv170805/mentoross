"""
MentorOS – Core Configuration
All values come from environment variables. Never hardcode secrets.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "MentorOS API"
    APP_VERSION: str = "3.0.0"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Security ─────────────────────────────────────────
    SECRET_KEY: str                          # REQUIRED – openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24       # 24 hours
    JWT_REFRESH_EXPIRE_DAYS: int = 30
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    ALLOW_ORIGIN_REGEX: str = ".*"  # Default to permissive for dev, restrict in .env for prod

    # ── Database ──────────────────────────────────────────
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "mentoross"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Custom AI Engine ─────────────────────────────────
    AI_MAX_TOKENS: int = 2048

    # ── Vector Store ─────────────────────────────────────
    VECTOR_STORE_PATH: str = "./data/vector.index"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── Rate Limiting ────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    AI_RATE_LIMIT_PER_MINUTE: int = 10

    # ── Scheduler ────────────────────────────────────────
    REMINDER_INTERVAL_MINUTES: int = 60

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"




@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
