from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from api.core.config import get_settings
from api.core.redis import redis_client
from fastapi import HTTPException, status
from jose import JWTError, jwt

MAX_TOKEN_TTL = timedelta(days=30)
TTL_UNITS: dict[str, str] = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
}


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "type": "about:blank",
            "title": "Unauthorized",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": "Authentication failed.",
        },
    )


def parse_ttl(ttl_string: str) -> timedelta:
    if len(ttl_string) < 2:
        raise ValueError("Invalid TTL format.")

    unit = ttl_string[-1]
    amount = ttl_string[:-1]

    if unit not in TTL_UNITS or not amount.isdigit():
        raise ValueError("Invalid TTL format.")

    ttl = timedelta(**{TTL_UNITS[unit]: int(amount)})
    if ttl <= timedelta(0):
        raise ValueError("TTL must be greater than zero.")
    if ttl > MAX_TOKEN_TTL:
        raise ValueError("TTL cannot exceed 30 days.")

    return ttl


def issue_token(
    agent_id: UUID | str,
    org_id: UUID | str,
    scopes: list[dict[str, Any]],
    ttl_string: str,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + parse_ttl(ttl_string)
    payload = {
        "jti": str(uuid4()),
        "sub": str(agent_id),
        "org": str(org_id),
        "scopes": scopes,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def verify_token(token: str) -> dict:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise _unauthorized_exception() from exc

    jti = payload.get("jti")
    if not jti:
        raise _unauthorized_exception()

    revoked = await redis_client.get(f"revoked:{jti}")
    if revoked:
        raise _unauthorized_exception()

    return payload


async def revoke_token(jti: str, expires_at: datetime, redis_client) -> None:
    now = datetime.now(UTC)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    ttl = max(0, int((expires_at - now).total_seconds()))
    if ttl == 0:
        return

    await redis_client.set(f"revoked:{jti}", "1", ex=ttl)
