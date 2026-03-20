from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from api.schemas.agent import Service


class LogEntry(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "f6e3ee96-654e-4ee0-bcd4-b64bafc7dfd0",
                "agent_id": "9f9f42b0-ef34-4c4b-b91b-f2db09b9354f",
                "token_id": "90b854af-1ee7-4f2f-a413-cbaaf3cce9f3",
                "service": "openai",
                "action": "chat.completions",
                "allowed": True,
                "called_at": "2026-03-20T12:10:00Z",
            }
        },
    )

    id: UUID
    agent_id: UUID
    token_id: UUID
    service: Service
    action: str
    allowed: bool
    called_at: datetime


class LogListResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "f6e3ee96-654e-4ee0-bcd4-b64bafc7dfd0",
                        "agent_id": "9f9f42b0-ef34-4c4b-b91b-f2db09b9354f",
                        "token_id": "90b854af-1ee7-4f2f-a413-cbaaf3cce9f3",
                        "service": "openai",
                        "action": "chat.completions",
                        "allowed": True,
                        "called_at": "2026-03-20T12:10:00Z",
                    }
                ],
                "total": 1,
            }
        },
    )

    items: list[LogEntry]
    total: int
