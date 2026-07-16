from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".scopeform" / "config.json"

# Scopeform is local-first: the CLI targets your own instance by default.
DEFAULT_API_URL = "http://localhost:8000"


def resolve_api_url(flag_value: str | None = None) -> str:
    """Resolve the API base URL: --api-url flag > SCOPEFORM_API_URL env >
    api_url saved at login > local default."""
    if flag_value:
        return flag_value
    env_url = os.environ.get("SCOPEFORM_API_URL")
    if env_url:
        return env_url
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8")).get("api_url")
            if saved:
                return str(saved)
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_API_URL


def _parse_expires_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    expires_at = datetime.fromisoformat(normalized)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at


def save_config(data: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.chmod(CONFIG_PATH, 0o600)


def load_config() -> dict[str, Any] | None:
    env_token = os.environ.get("SCOPEFORM_TOKEN")
    if env_token:
        return {"token": env_token, "email": "ci"}

    if not CONFIG_PATH.exists():
        return None

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    expires_at = data.get("expires_at")
    if not expires_at:
        return data

    if _parse_expires_at(expires_at) <= datetime.now(UTC):
        clear_config()
        return None

    return data


def clear_config() -> None:
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
