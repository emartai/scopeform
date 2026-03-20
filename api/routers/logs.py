from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.deps import get_current_org_id
from api.models.agent import Agent
from api.models.log import CallLog
from api.schemas.log import LogEntry, LogListResponse

router = APIRouter(tags=["logs"])
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


def _apply_log_filters(
    stmt: Select,
    *,
    allowed: bool | None,
    service: str | None,
    agent_id: UUID | None = None,
) -> Select:
    if allowed is not None:
        stmt = stmt.where(CallLog.allowed == allowed)
    if service:
        stmt = stmt.where(CallLog.service == service)
    if agent_id is not None:
        stmt = stmt.where(CallLog.agent_id == agent_id)
    return stmt


@router.get("/agents/{agent_id}/logs", response_model=LogListResponse, responses=PROBLEM_RESPONSES)
async def get_agent_logs(
    agent_id: UUID,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    allowed: bool | None = None,
    service: str | None = None,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> LogListResponse:
    """List call logs for a single agent owned by the authenticated organisation."""
    agent = await db.scalar(select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id))
    if agent is None:
        raise _problem(status.HTTP_404_NOT_FOUND, "Not Found", "Agent not found.")

    stmt = (
        select(CallLog)
        .join(Agent, CallLog.agent_id == Agent.id)
        .where(Agent.org_id == org_id, CallLog.agent_id == agent_id)
        .order_by(CallLog.called_at.desc())
        .offset(offset)
        .limit(limit)
    )
    stmt = _apply_log_filters(stmt, allowed=allowed, service=service)

    logs = (await db.scalars(stmt)).all()

    count_stmt = (
        select(CallLog)
        .join(Agent, CallLog.agent_id == Agent.id)
        .where(Agent.org_id == org_id, CallLog.agent_id == agent_id)
    )
    count_stmt = _apply_log_filters(count_stmt, allowed=allowed, service=service)
    total = len((await db.scalars(count_stmt)).all())

    return LogListResponse(
        items=[LogEntry.model_validate(entry) for entry in logs],
        total=total,
    )


@router.get("/logs", response_model=LogListResponse, responses=PROBLEM_RESPONSES)
async def get_logs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    allowed: bool | None = None,
    service: str | None = None,
    agent_id: UUID | None = None,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> LogListResponse:
    """List all call logs visible to the authenticated organisation."""
    if agent_id is not None:
        agent = await db.scalar(select(Agent).where(Agent.id == agent_id, Agent.org_id == org_id))
        if agent is None:
            raise _problem(status.HTTP_404_NOT_FOUND, "Not Found", "Agent not found.")

    stmt = (
        select(CallLog)
        .join(Agent, CallLog.agent_id == Agent.id)
        .where(Agent.org_id == org_id)
        .order_by(CallLog.called_at.desc())
        .offset(offset)
        .limit(limit)
    )
    stmt = _apply_log_filters(stmt, allowed=allowed, service=service, agent_id=agent_id)

    logs = (await db.scalars(stmt)).all()

    count_stmt = select(CallLog).join(Agent, CallLog.agent_id == Agent.id).where(Agent.org_id == org_id)
    count_stmt = _apply_log_filters(count_stmt, allowed=allowed, service=service, agent_id=agent_id)
    total = len((await db.scalars(count_stmt)).all())

    return LogListResponse(
        items=[LogEntry.model_validate(entry) for entry in logs],
        total=total,
    )
