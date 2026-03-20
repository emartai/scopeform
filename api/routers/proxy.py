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

import uuid
from typing import AsyncIterator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    # 4. Check scope
    allowed = _scope_allows(scopes, service, action)

    # 5. Log the call
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

    if not allowed:
        raise HTTPException(
            403,
            detail=f"Scope '{service}:{action}' not permitted for this agent.",
        )

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
    body = await request.body()

    # Pass through all headers except Authorization (replaced) and host
    forward_headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("authorization", "host", "content-length")
    }
    forward_headers.update(_provider_headers(service, real_api_key))

    # Keep the client open for the full duration of streaming
    client = httpx.AsyncClient(timeout=120)
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

    async def _stream_and_close() -> AsyncIterator[bytes]:
        try:
            async for chunk in provider_response.aiter_bytes():
                yield chunk
        finally:
            await provider_response.aclose()
            await client.aclose()

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
