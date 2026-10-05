"""
Application settings loaded from environment variables via pydantic-settings.
Copy .env.example → .env and fill in your values before running the server.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────
    APP_NAME: str = "Career Trajectory Simulator"
    APP_ENV: str = "development"          # development | staging | production
    DEBUG: bool = True

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/career_simulator"

    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",
    ]

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.ALGORITHM != "HS256":
            raise ValueError("Only HS256 is supported for access tokens.")
        if self.ACCESS_TOKEN_EXPIRE_MINUTES < 1:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive.")
        if self.APP_ENV.lower() == "production":
            if self.SECRET_KEY == "CHANGE_ME_IN_PRODUCTION" or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "Production requires a SECRET_KEY of at least 32 characters."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton)."""
    return Settings()


settings: Settings = get_settings()
