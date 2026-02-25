from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str  # async PostgreSQL connection string

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALGORITHM: str

    # Redis
    REDIS_URL: str

    # App behavior
    DEBUG: bool = False

    # CORS
    ALLOWED_ORIGINS: List[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value):
        """
        Allow ALLOWED_ORIGINS to be provided as:
        - Comma-separated string
        - JSON-style list
        """
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached settings instance.
    Ensures .env is loaded only once.
    """
    return Settings()
