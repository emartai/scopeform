from __future__ import annotations

"""Public README badge: live credential status for an agent.

GET /api/v1/badges/agent/{agent_id} returns a shields-style SVG:
  green  — active agent with a live scoped token
  amber  — registered, but the latest token is expired (or none issued yet)
  red    — revoked / suspended / unknown agent

The endpoint is public by design (badges must render in READMEs); agent IDs
are unguessable UUIDs and the badge reveals only a coarse status word.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.models.agent import Agent
from api.models.token import Token

router = APIRouter(prefix="/badges", tags=["badges"])

COLORS = {"green": "#3fb950", "amber": "#d29922", "red": "#f85149"}
LABEL = "scopeform"


def _render_badge(status_text: str, color: str) -> str:
    # Flat shields-style badge; widths approximated per character.
    label_w = 6 * len(LABEL) + 12
    status_w = 6 * len(status_text) + 12
    total_w = label_w + status_w
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20" role="img" aria-label="{LABEL}: {status_text}">
  <linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <clipPath id="r"><rect width="{total_w}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_w}" height="20" fill="#555"/>
    <rect x="{label_w}" width="{status_w}" height="20" fill="{color}"/>
    <rect width="{total_w}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_w / 2}" y="14">{LABEL}</text>
    <text x="{label_w + status_w / 2}" y="14">{status_text}</text>
  </g>
</svg>"""


def _svg_response(status_text: str, color_name: str) -> Response:
    return Response(
        content=_render_badge(status_text, COLORS[color_name]),
        media_type="image/svg+xml",
        headers={"Cache-Control": "max-age=300, s-maxage=300"},
    )


@router.get("/agent/{agent_id}")
async def agent_badge(agent_id: str, db: AsyncSession = Depends(get_db)) -> Response:
    try:
        parsed_id = uuid.UUID(agent_id)
    except ValueError:
        return _svg_response("unknown", "red")

    agent = await db.scalar(select(Agent).where(Agent.id == parsed_id))
    if agent is None:
        return _svg_response("unknown", "red")
    if agent.status != "active":
        return _svg_response(agent.status, "red")

    latest = await db.scalar(
        select(Token)
        .where(Token.agent_id == parsed_id, Token.revoked_at.is_(None))
        .order_by(Token.expires_at.desc())
        .limit(1)
    )
    if latest is None:
        return _svg_response("no token", "amber")

    expires_at = latest.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        return _svg_response("expired", "amber")

    return _svg_response("scoped", "green")
