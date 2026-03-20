from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

AGENT_NAME_PATTERN = r"^[a-zA-Z0-9_-]{1,64}$"

Environment = Literal["production", "staging", "development"]
AgentStatus = Literal["active", "suspended", "decommissioned"]
Service = Literal["openai", "anthropic", "github"]


class ScopeDefinition(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "service": "openai",
                "actions": ["chat.completions"],
            }
        },
    )

    service: Service
    actions: list[str] = Field(min_length=1)


class AgentCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "support-agent",
                "owner_email": "owner@example.com",
                "environment": "production",
                "scopes": [
                    {
                        "service": "openai",
                        "actions": ["chat.completions"],
                    }
                ],
            }
        },
    )

    name: str = Field(pattern=AGENT_NAME_PATTERN)
    owner_email: EmailStr
    environment: Environment
    scopes: list[ScopeDefinition] = Field(min_length=1)


class AgentUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": "suspended"}},
    )

    status: AgentStatus


class AgentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "9f9f42b0-ef34-4c4b-b91b-f2db09b9354f",
                "org_id": "b38064a3-e9d9-4d9f-a1d8-ac58f50563e9",
                "name": "support-agent",
                "owner_email": "owner@example.com",
                "environment": "production",
                "scopes": [
                    {
                        "service": "openai",
                        "actions": ["chat.completions"],
                    }
                ],
                "status": "active",
                "created_at": "2026-03-20T12:00:00Z",
                "updated_at": "2026-03-20T12:00:00Z",
            }
        },
    )

    id: UUID
    org_id: UUID
    name: str
    owner_email: EmailStr
    environment: Environment
    scopes: list[ScopeDefinition]
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime | None = None


class AgentListResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "9f9f42b0-ef34-4c4b-b91b-f2db09b9354f",
                        "org_id": "b38064a3-e9d9-4d9f-a1d8-ac58f50563e9",
                        "name": "support-agent",
                        "owner_email": "owner@example.com",
                        "environment": "production",
                        "scopes": [
                            {
                                "service": "openai",
                                "actions": ["chat.completions"],
                            }
                        ],
                        "status": "active",
                        "created_at": "2026-03-20T12:00:00Z",
                        "updated_at": "2026-03-20T12:00:00Z",
                    }
                ],
                "total": 1,
            }
        },
    )

    items: list[AgentResponse]
    total: int
