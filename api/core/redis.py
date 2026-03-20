from __future__ import annotations

from collections.abc import AsyncGenerator

try:
    from redis import asyncio as aioredis
except Exception:  # pragma: no cover - fallback for environments without redis>=4
    from redis import asyncio as aioredis

from api.core.config import get_settings

redis_client = aioredis.from_url(
    get_settings().redis_url,
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=10,
    socket_timeout=10,
)


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    yield redis_client


async def check_redis_connection() -> bool:
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False
