from __future__ import annotations

"""Credential broker — GitHub App installation tokens.

Where a provider supports native scoped short-lived credentials, Scopeform
brokers them instead of proxying traffic. GitHub Apps do exactly this: the
agent exchanges its SCOPEFORM_TOKEN for a real installation token scoped to
the permissions its scopeform.yml declares (~1h TTL, minted by GitHub).
Scopeform never sits in the GitHub traffic path.

Setup (self-hosted): create a GitHub App on your org, install it on the
repositories your agents need, then store its credentials under
Integrations → github_app as JSON: {"app_id": "...", "installation_id": "...",
"private_key": "-----BEGIN RSA PRIVATE KEY-----..."}.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.token import verify_token
from api.models.integration import OrgIntegration
from api.models.log import CallLog
from api.models.token import Token

router = APIRouter(prefix="/broker", tags=["broker"])

GITHUB_API = "https://api.github.com"

# scopeform.yml github actions → GitHub App fine-grained permissions.
# The installation token gets the union of permissions for the agent's scopes.
ACTION_PERMISSIONS: dict[str, dict[str, str]] = {
    "repos.read": {"contents": "read", "metadata": "read"},
    "repos.write": {"contents": "write", "metadata": "read"},
    "issues.read": {"issues": "read"},
    "issues.write": {"issues": "write"},
    "pulls.read": {"pull_requests": "read"},
}

_PERMISSION_RANK = {"read": 1, "write": 2, "admin": 3}


def _permissions_for(actions: list[str]) -> dict[str, str]:
    permissions: dict[str, str] = {}
    for action in actions:
        for name, level in ACTION_PERMISSIONS.get(action, {}).items():
            current = permissions.get(name)
            if current is None or _PERMISSION_RANK[level] > _PERMISSION_RANK[current]:
                permissions[name] = level
    return permissions


def _build_app_jwt(app_id: str, private_key: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "iat": now - timedelta(seconds=60),
        "exp": now + timedelta(minutes=9),
        "iss": app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


async def _fetch_installation_token(
    app_jwt: str, installation_id: str, permissions: dict[str, str]
) -> dict:
    """Mint the installation token from GitHub. Split out for testability."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{GITHUB_API}/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
            },
            json={"permissions": permissions} if permissions else {},
        )
    if response.status_code != 201:
        raise HTTPException(
            502,
            detail=f"GitHub rejected the installation token request ({response.status_code}).",
        )
    return response.json()


@router.post("/github")
async def broker_github_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Exchange a Scopeform runtime token for a natively-scoped GitHub App token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, detail="Missing Bearer token.")
    payload = await verify_token(auth_header.removeprefix("Bearer ").strip())

    try:
        agent_id = uuid.UUID(str(payload.get("sub", "")))
        org_id = uuid.UUID(str(payload.get("org", "")))
    except ValueError as exc:
        raise HTTPException(401, detail="Malformed token.") from exc

    github_actions = [
        action
        for scope in payload.get("scopes", [])
        if scope.get("service") == "github"
        for action in scope.get("actions", [])
    ]

    token_row = await db.scalar(select(Token).where(Token.jti == payload.get("jti", "")))

    async def _log(allowed: bool) -> None:
        if token_row is None:
            return
        db.add(
            CallLog(
                agent_id=agent_id,
                token_id=token_row.id,
                service="github",
                action="broker.token",
                allowed=allowed,
            )
        )
        await db.commit()

    if not github_actions:
        await _log(False)
        raise HTTPException(403, detail="This agent has no github scopes.")

    integration = await db.scalar(
        select(OrgIntegration).where(
            OrgIntegration.org_id == org_id,
            OrgIntegration.service == "github_app",
        )
    )
    if integration is None:
        raise HTTPException(
            422,
            detail=(
                "No GitHub App configured. Add one under Integrations → github_app "
                '(JSON: {"app_id", "installation_id", "private_key"}).'
            ),
        )

    from api.routers.integrations import _decrypt

    try:
        app_config = json.loads(_decrypt(integration.encrypted_api_key))
        app_id = str(app_config["app_id"])
        installation_id = str(app_config["installation_id"])
        private_key = str(app_config["private_key"])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise HTTPException(500, detail="Stored GitHub App credentials are malformed.") from exc

    permissions = _permissions_for(github_actions)
    app_jwt = _build_app_jwt(app_id, private_key)
    token_response = await _fetch_installation_token(app_jwt, installation_id, permissions)

    await _log(True)
    return {
        "token": token_response.get("token"),
        "expires_at": token_response.get("expires_at"),
        "permissions": token_response.get("permissions", permissions),
    }
