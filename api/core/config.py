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
    encryption_key: str = ""  # Fernet key; generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    next_public_api_url: str = "http://localhost:8000"

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        origins = {self.frontend_url}
        if "localhost" in self.frontend_url or "127.0.0.1" in self.frontend_url:
            origins.add("http://localhost:3000")
        return list(origins)


@lru_cache
def get_settings() -> Settings:
    return Settings()
