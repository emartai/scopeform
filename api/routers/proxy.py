from __future__ import annotations

"""
Scopeform proxy router.

Agents point their SDK base URL here instead of the provider directly:

    openai.api_key  = SCOPEFORM_TOKEN
    openai.base_url = "https://<railway-url>/api/v1/proxy/openai/v1"

The proxy:
  1. Extracts the Bearer SCOPEFORM_TOKEN from the Authorization header.
  2. Validates the token (signature + revocation check).
  3. Resolves the requested action from the HTTP method + path.
  4. Checks the agent's declared scopes allow that action.
  5. Logs the call (allowed or blocked).
  6. If allowed: looks up the org's real provider API key and forwards.
  7. Returns the provider response, including streaming.
"""

import json
import uuid
from datetime import UTC, datetime
from typing import AsyncIterator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core import redis as redis_core
from api.core.database import get_db
from api.core.token import verify_token
from api.models.integration import OrgIntegration
from api.models.log import CallLog
from api.models.token import Token
from api.routers.integrations import _decrypt

router = APIRouter(prefix="/proxy", tags=["proxy"])

# ── Provider base URLs ────────────────────────────────────────────────────────

PROVIDER_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com",
    "anthropic": "https://api.anthropic.com",
    "github": "https://api.github.com",
}

# One shared upstream client (connection pooling) instead of one per request.
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=120)
    return _client


def _fail_closed(exc: Exception) -> HTTPException:
    """Limit state unavailable → block. A security proxy must not quietly stop enforcing."""
    return HTTPException(
        503,
        detail="Limit enforcement store unavailable — failing closed.",
    )

# ── Action resolution ─────────────────────────────────────────────────────────

def _resolve_action(service: str, method: str, path: str) -> str:
    """Map service + HTTP method + URL path → scope action string."""
    m = method.upper()
    if service == "openai":
        if "chat/completions" in path:
            return "chat.completions"
        if "embeddings" in path:
            return "embeddings"
        if "images/generations" in path:
            return "images.generations"
    elif service == "anthropic":
        if "messages" in path:
            return "messages"
    elif service == "github":
        if "issues" in path:
            return "issues.read" if m == "GET" else "issues.write"
        if "pulls" in path:
            return "pulls.read"
        return "repos.read" if m == "GET" else "repos.write"
    # Fallback: derive from last non-empty path segment
    segments = [s for s in path.split("/") if s]
    return segments[-1] if segments else service


def _scope_allows(scopes: list[dict], service: str, action: str) -> bool:
    for entry in scopes:
        if entry.get("service") == service and action in entry.get("actions", []):
            return True
    return False


# ── Auth header builder ───────────────────────────────────────────────────────

def _provider_headers(service: str, api_key: str) -> dict[str, str]:
    if service == "anthropic":
        return {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    return {"Authorization": f"Bearer {api_key}"}


# ── Runtime limits (embedded in the scoped token) ─────────────────────────────

def _parse_json_body(body: bytes) -> dict | None:
    if not body:
        return None
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _hour_key(agent_id: str) -> str:
    return f"limit:calls:{agent_id}:{datetime.now(UTC).strftime('%Y%m%d%H')}"


def _day_key(agent_id: str) -> str:
    return f"limit:tokens:{agent_id}:{datetime.now(UTC).strftime('%Y%m%d')}"


def _extract_usage_tokens(service: str, data: dict) -> int:
    """Total tokens consumed, from the provider's usage block (0 if absent)."""
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return 0
    if service == "anthropic":
        return int(usage.get("input_tokens", 0) or 0) + int(usage.get("output_tokens", 0) or 0)
    return int(usage.get("total_tokens", 0) or 0)


# ── Main proxy handler ────────────────────────────────────────────────────────

@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(
    service: str,
    path: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    if service not in PROVIDER_BASE_URLS:
        raise HTTPException(400, detail=f"Unsupported service: {service}")

    # 1. Extract + validate the Scopeform token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, detail="Missing Bearer token.")
    raw_token = auth_header.removeprefix("Bearer ").strip()

    try:
        payload = await verify_token(raw_token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(401, detail="Invalid token.") from exc

    agent_id_str: str = payload.get("sub", "")
    org_id_str: str = payload.get("org", "")
    jti: str = payload.get("jti", "")
    scopes: list[dict] = payload.get("scopes", [])

    try:
        agent_id = uuid.UUID(agent_id_str)
        org_id = uuid.UUID(org_id_str)
    except ValueError as exc:
        raise HTTPException(401, detail="Malformed token.") from exc

    # 2. Resolve token DB record (for logging)
    token_row = await db.scalar(select(Token).where(Token.jti == jti))

    # 3. Resolve action
    action = _resolve_action(service, request.method, f"/{path}")

    async def _log_call(allowed: bool) -> None:
        db.add(
            CallLog(
                agent_id=agent_id,
                token_id=token_row.id if token_row else None,
                service=service,
                action=action,
                allowed=allowed,
            )
        )
        await db.commit()

    # 4. Check scope
    if not _scope_allows(scopes, service, action):
        await _log_call(False)
        raise HTTPException(
            403,
            detail=f"Scope '{service}:{action}' not permitted for this agent.",
        )

    # 5. Enforce runtime limits carried in the token
    body = await request.body()
    limits: dict = payload.get("limits") or {}
    request_json = _parse_json_body(body)

    allowed_models = limits.get("models")
    if allowed_models and request_json is not None:
        requested_model = request_json.get("model")
        if requested_model and requested_model not in allowed_models:
            await _log_call(False)
            raise HTTPException(
                403,
                detail=(
                    f"Model '{requested_model}' is not in this agent's allowlist "
                    f"({', '.join(allowed_models)})."
                ),
            )

    max_calls = limits.get("max_calls_per_hour")
    if max_calls:
        hour_key = _hour_key(agent_id_str)
        try:
            current_calls = await redis_core.redis_client.incr(hour_key)
            if current_calls == 1:
                await redis_core.redis_client.expire(hour_key, 3900)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001 - fail closed on store failure
            await _log_call(False)
            raise _fail_closed(exc) from exc
        if current_calls > int(max_calls):
            await _log_call(False)
            raise HTTPException(
                429,
                detail=f"Rate limit exceeded: {max_calls} calls/hour for this agent.",
            )

    max_tokens = limits.get("max_tokens_per_day")
    if max_tokens:
        try:
            used_raw = await redis_core.redis_client.get(_day_key(agent_id_str))
        except Exception as exc:  # noqa: BLE001 - fail closed on store failure
            await _log_call(False)
            raise _fail_closed(exc) from exc
        if used_raw is not None and int(used_raw) >= int(max_tokens):
            await _log_call(False)
            raise HTTPException(
                429,
                detail=f"Daily token budget exhausted: {max_tokens} tokens/day for this agent.",
            )

    await _log_call(True)

    # 6. Look up org's real API key for this service
    integration = await db.scalar(
        select(OrgIntegration).where(
            OrgIntegration.org_id == org_id,
            OrgIntegration.service == service,
        )
    )
    if not integration:
        raise HTTPException(
            422,
            detail=f"No {service} API key configured. Add it in the Scopeform dashboard → Integrations.",
        )

    real_api_key = _decrypt(integration.encrypted_api_key)

    # 7. Forward the request to the provider
    provider_url = f"{PROVIDER_BASE_URLS[service]}/{path}"

    # Pass through all headers except Authorization (replaced) and host
    forward_headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("authorization", "host", "content-length")
    }
    forward_headers.update(_provider_headers(service, real_api_key))

    is_streaming_request = bool(request_json and request_json.get("stream"))

    client = _get_client()
    provider_response = await client.send(
        client.build_request(
            method=request.method,
            url=provider_url,
            headers=forward_headers,
            content=body,
            params=dict(request.query_params),
        ),
        stream=True,
    )

    # Non-streaming + a daily token budget → buffer the JSON body so real
    # provider usage can be metered. (Streaming responses pass through
    # unmetered — their usage block is not reliably present.)
    if max_tokens and not is_streaming_request:
        try:
            content = await provider_response.aread()
        finally:
            await provider_response.aclose()

        response_json = _parse_json_body(content)
        if provider_response.status_code < 400 and response_json is not None:
            consumed = _extract_usage_tokens(service, response_json)
            if consumed:
                day_key = _day_key(agent_id_str)
                total = await redis_core.redis_client.incrby(day_key, consumed)
                if total == consumed:
                    await redis_core.redis_client.expire(day_key, 100_000)

        return Response(
            content=content,
            status_code=provider_response.status_code,
            headers={
                k: v
                for k, v in provider_response.headers.items()
                if k.lower() not in ("transfer-encoding", "content-length", "content-encoding")
            },
            media_type=provider_response.headers.get("content-type", "application/json"),
        )

    async def _stream_and_close() -> AsyncIterator[bytes]:
        try:
            async for chunk in provider_response.aiter_bytes():
                yield chunk
        finally:
            await provider_response.aclose()

    return StreamingResponse(
        _stream_and_close(),
        status_code=provider_response.status_code,
        headers={
            k: v
            for k, v in provider_response.headers.items()
            if k.lower() not in ("transfer-encoding",)
        },
        media_type=provider_response.headers.get("content-type", "application/json"),
    )
