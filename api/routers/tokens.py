from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.core.database import get_db
from api.core.deps import get_current_org_id
from api.core.redis import redis_client
from api.core.token import issue_token, revoke_token, verify_token
from api.models.agent import Agent
from api.models.log import CallLog
from api.models.token import Token
from api.schemas.token import (
    TokenIssueRequest,
    TokenIssueResponse,
    TokenRevokeRequest,
    TokenRevokeResponse,
    TokenValidateRequest,
    TokenValidateResponse,
)

router = APIRouter(prefix="/tokens", tags=["tokens"])
PROBLEM_RESPONSES = {
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {
                    "type": "about:blank",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "Authentication failed.",
                }
            }
        },
    },
    403: {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "example": {
                    "allowed": False,
                }
            }
        },
    },
    404: {
        "description": "Not Found",
        "content": {
            "application/json": {
                "example": {
                    "type": "about:blank",
                    "title": "Not Found",
                    "status": 404,
                    "detail": "Agent not found.",
                }
            }
        },
    },
    422: {"description": "Validation Error"},
    429: {
        "description": "Too Many Requests",
        "content": {
            "application/json": {
                "example": {
                    "type": "about:blank",
                    "title": "Too Many Requests",
                    "status": 429,
                    "detail": "Rate limit exceeded.",
                }
            }
        },
    },
}


def _problem(status_code: int, title: str, detail: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "type": "about:blank",
            "title": title,
            "status": status_code,
            "detail": detail,
        },
    )


async def _enforce_rate_limit(org_id: UUID, scope: str, limit: int, window_seconds: int = 60) -> None:
    key = f"ratelimit:{scope}:{org_id}"
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window_seconds)
    if current > limit:
        raise _problem(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too Many Requests",
            "Rate limit exceeded.",
        )


async def _get_org_agent(db: AsyncSession, agent_id: UUID, org_id: UUID) -> Agent | None:
    return await db.scalar(select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id))


def _decode_issued_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise _problem(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Failed to issue token.",
        ) from exc


async def _log_validation_result(
    db: AsyncSession,
    token_record: Token,
    service: str,
    action: str,
    allowed: bool,
) -> None:
    db.add(
        CallLog(
            agent_id=token_record.agent_id,
            token_id=token_record.id,
            service=service,
            action=action,
            allowed=allowed,
        )
    )
    await db.commit()


def _scope_allows(scopes: list[dict], service: str, action: str) -> bool:
    for scope in scopes:
        if scope.get("service") == service and action in scope.get("actions", []):
            return True
    return False


@router.post("/issue", response_model=TokenIssueResponse, responses=PROBLEM_RESPONSES)
async def issue_agent_token(
    payload: TokenIssueRequest,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> TokenIssueResponse:
    """Issue a short-lived scoped runtime token for an active agent."""
    await _enforce_rate_limit(org_id, "tokens_issue", 30)

    agent = await _get_org_agent(db, payload.agent_id, org_id)
    if agent is None:
        raise _problem(status.HTTP_404_NOT_FOUND, "Not Found", "Agent not found.")
    if agent.status != "active":
        raise _problem(
            status.HTTP_403_FORBIDDEN,
            "Forbidden",
            "Tokens cannot be issued for this agent.",
        )

    signed_token = issue_token(agent.id, agent.org_id, agent.scopes, payload.ttl)
    token_payload = _decode_issued_token(signed_token)
    expires_at = datetime.fromtimestamp(token_payload["exp"], tz=UTC)
    token_record = Token(
        agent_id=agent.id,
        jti=token_payload["jti"],
        expires_at=expires_at,
    )
    db.add(token_record)
    await db.commit()

    return TokenIssueResponse(
        token=signed_token,
        jti=token_record.jti,
        expires_at=token_record.expires_at,
    )


@router.post("/revoke", response_model=TokenRevokeResponse, responses=PROBLEM_RESPONSES)
async def revoke_agent_token(
    payload: TokenRevokeRequest,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> TokenRevokeResponse:
    """Revoke a single token or all active tokens for an agent."""
    await _enforce_rate_limit(org_id, "tokens_revoke", 60)

    tokens_to_revoke: list[Token]
    if payload.agent_id is not None:
        agent = await _get_org_agent(db, payload.agent_id, org_id)
        if agent is None:
            raise _problem(status.HTTP_404_NOT_FOUND, "Not Found", "Agent not found.")
        tokens_to_revoke = (
            await db.scalars(
                select(Token).where(Token.agent_id == agent.id, Token.revoked_at.is_(None))
            )
        ).all()
    else:
        token_record = await db.scalar(
            select(Token)
            .join(Agent, Token.agent_id == Agent.id)
            .where(Token.jti == payload.jti, Agent.org_id == org_id)
        )
        if token_record is None:
            raise _problem(status.HTTP_404_NOT_FOUND, "Not Found", "Token not found.")
        tokens_to_revoke = [token_record] if token_record.revoked_at is None else []

    for token_record in tokens_to_revoke:
        await revoke_token(token_record.jti, token_record.expires_at, redis_client)
        token_record.revoked_at = datetime.now(UTC)

    await db.commit()
    return TokenRevokeResponse(revoked=True, count=len(tokens_to_revoke))


@router.post("/validate", response_model=TokenValidateResponse, responses=PROBLEM_RESPONSES)
async def validate_agent_token(
    payload: TokenValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate a runtime token and enforce the requested service/action scope."""
    token_payload = await verify_token(payload.token)

    try:
        org_id = UUID(str(token_payload["org"]))
        agent_id = UUID(str(token_payload["sub"]))
        jti = str(token_payload["jti"])
        scopes = token_payload.get("scopes", [])
    except (KeyError, TypeError, ValueError) as exc:
        raise _problem(
            status.HTTP_401_UNAUTHORIZED,
            "Unauthorized",
            "Authentication failed.",
        ) from exc

    await _enforce_rate_limit(org_id, "tokens_validate", 300)

    token_record = await db.scalar(
        select(Token)
        .join(Agent, Token.agent_id == Agent.id)
        .where(Token.jti == jti, Token.agent_id == agent_id, Agent.org_id == org_id)
    )
    if token_record is None:
        raise _problem(
            status.HTTP_401_UNAUTHORIZED,
            "Unauthorized",
            "Authentication failed.",
        )

    allowed = _scope_allows(scopes, payload.service, payload.action)
    await _log_validation_result(db, token_record, payload.service, payload.action, allowed)

    if not allowed:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"allowed": False})

    return TokenValidateResponse(allowed=True)
