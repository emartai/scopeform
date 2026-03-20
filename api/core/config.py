from __future__ import annotations

from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/scopeform"
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "replace-with-64-char-hex-string-placeholder"
    jwt_algorithm: str = "HS256"
    clerk_secret_key: str = "clerk_secret_key_placeholder"
    clerk_publishable_key: str = "clerk_publishable_key_placeholder"
    api_base_url: str = "http://localhost:8000"
    next_public_clerk_publishable_key: str = "clerk_publishable_key_placeholder"
    next_public_api_url: str = "http://localhost:8000"

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        if "localhost" in self.next_public_api_url or "127.0.0.1" in self.next_public_api_url:
            return ["http://localhost:3000"]
        return [self.next_public_api_url]


@lru_cache
def get_settings() -> Settings:
    return Settings()
