from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.deps import get_current_org_id
from api.core.redis import redis_client
from api.core.token import revoke_token
from api.models.agent import Agent
from api.models.log import CallLog
from api.models.token import Token
from api.schemas.agent import AgentCreate, AgentListResponse, AgentResponse, AgentUpdate

FREE_TIER_AGENT_LIMIT = 5

router = APIRouter(prefix="/agents", tags=["agents"])
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
    409: {
        "description": "Conflict",
        "content": {
            "application/json": {
                "example": {
                    "type": "about:blank",
                    "title": "Conflict",
                    "status": 409,
                    "detail": "An agent with that name already exists in this organisation.",
                }
            }
        },
    },
    422: {"description": "Validation Error"},
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


async def _get_agent_for_org(
    db: AsyncSession,
    agent_id: UUID,
    org_id: UUID,
) -> Agent | None:
    return await db.scalar(select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id))


async def _revoke_active_agent_tokens(db: AsyncSession, agent_id: UUID) -> None:
    active_tokens = (
        await db.scalars(
            select(Token).where(Token.agent_id == agent_id, Token.revoked_at.is_(None))
        )
    ).all()

    for token in active_tokens:
        await revoke_token(token.jti, token.expires_at, redis_client)
        token.revoked_at = token.revoked_at or datetime.now(UTC)


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    responses=PROBLEM_RESPONSES,
)
async def create_agent(
    payload: AgentCreate,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Register a new agent for the authenticated organisation."""
    agent_count = await db.scalar(select(func.count(Agent.id)).where(Agent.org_id == org_id))
    if (agent_count or 0) >= FREE_TIER_AGENT_LIMIT:
        raise _problem(
            status.HTTP_403_FORBIDDEN,
            "Free Tier Limit",
            f"Free tier allows up to {FREE_TIER_AGENT_LIMIT} agents. Upgrade your plan to register more.",
        )

    existing_agent = await db.scalar(
        select(Agent).where(Agent.org_id == org_id, Agent.name == payload.name)
    )
    if existing_agent is not None:
        raise _problem(
            status.HTTP_409_CONFLICT,
            "Conflict",
            "An agent with that name already exists in this organisation.",
        )

    agent = Agent(
        org_id=org_id,
        name=payload.name,
        owner_email=str(payload.owner_email),
        environment=payload.environment,
        scopes=[scope.model_dump() for scope in payload.scopes],
        status="active",
    )
    db.add(agent)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise _problem(
            status.HTTP_409_CONFLICT,
            "Conflict",
            "An agent with that name already exists in this organisation.",
        ) from exc

    await db.refresh(agent)
    return AgentResponse.model_validate(agent)


def _last_seen_subquery():
    return (
        select(CallLog.agent_id, func.max(CallLog.called_at).label("last_seen_at"))
        .group_by(CallLog.agent_id)
        .subquery()
    )


@router.get("", response_model=AgentListResponse, responses={401: PROBLEM_RESPONSES[401]})
async def list_agents(
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> AgentListResponse:
    """List all agents belonging to the authenticated organisation."""
    last_seen = _last_seen_subquery()
    rows = (
        await db.execute(
            select(Agent, last_seen.c.last_seen_at)
            .outerjoin(last_seen, Agent.id == last_seen.c.agent_id)
            .where(Agent.org_id == org_id)
        )
    ).all()
    items = [
        AgentResponse.model_validate(agent).model_copy(update={"last_seen_at": last_seen_at})
        for agent, last_seen_at in rows
    ]
    return AgentListResponse(items=items, total=len(items))


@router.get("/{agent_id}", response_model=AgentResponse, responses=PROBLEM_RESPONSES)
async def get_agent(
    agent_id: UUID,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Return a single agent if it belongs to the authenticated organisation."""
    last_seen = _last_seen_subquery()
    row = (
        await db.execute(
            select(Agent, last_seen.c.last_seen_at)
            .outerjoin(last_seen, Agent.id == last_seen.c.agent_id)
            .where(Agent.id == agent_id, Agent.org_id == org_id)
        )
    ).first()
    if row is None:
        raise _problem(status.HTTP_404_NOT_FOUND, "Not Found", "Agent not found.")

    agent, last_seen_at = row
    return AgentResponse.model_validate(agent).model_copy(update={"last_seen_at": last_seen_at})


@router.patch("/{agent_id}/status", response_model=AgentResponse, responses=PROBLEM_RESPONSES)
async def update_agent_status(
    agent_id: UUID,
    payload: AgentUpdate,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Update an agent status and revoke active tokens when the agent is disabled."""
    agent = await _get_agent_for_org(db, agent_id, org_id)
    if agent is None:
        raise _problem(status.HTTP_404_NOT_FOUND, "Not Found", "Agent not found.")

    agent.status = payload.status
    if payload.status in {"suspended", "decommissioned"}:
        await _revoke_active_agent_tokens(db, agent.id)

    await db.commit()
    await db.refresh(agent)
    return AgentResponse.model_validate(agent)
