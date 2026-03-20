from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".scopeform" / "config.json"


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
