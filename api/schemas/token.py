from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.schemas.agent import Service

TTL_PATTERN = r"^\d+[smhd]$"


class TokenLimits(BaseModel):
    """Optional runtime limits embedded in the scoped token.

    Limits are part of the credential itself — a token carries not just what
    an agent may call, but how hard it may call it.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "models": ["gpt-4o-mini"],
                "max_calls_per_hour": 100,
                "max_tokens_per_day": 200000,
            }
        },
    )

    models: list[str] | None = None
    max_calls_per_hour: int | None = Field(default=None, gt=0)
    max_tokens_per_day: int | None = Field(default=None, gt=0)


class TokenIssueRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "agent_id": "9f9f42b0-ef34-4c4b-b91b-f2db09b9354f",
                "ttl": "24h",
            }
        },
    )

    agent_id: UUID
    ttl: str = Field(pattern=TTL_PATTERN)
    limits: TokenLimits | None = None


class TokenIssueResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "jti": "c61297a0-d274-4f0e-9f0f-4cb264cc9722",
                "expires_at": "2026-03-21T12:00:00Z",
            }
        },
    )

    token: str
    jti: str
    expires_at: datetime


class TokenRevokeRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"agent_id": "9f9f42b0-ef34-4c4b-b91b-f2db09b9354f"}},
    )

    jti: str | None = None
    agent_id: UUID | None = None

    @model_validator(mode="after")
    def validate_target(self) -> TokenRevokeRequest:
        if self.jti is None and self.agent_id is None:
            raise ValueError("Either jti or agent_id must be provided.")
        return self


class TokenValidateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "service": "openai",
                "action": "chat.completions",
            }
        },
    )

    token: str
    service: Service
    action: str


class TokenValidateResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"allowed": True}},
    )

    allowed: bool


class TokenRevokeResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"revoked": True, "count": 1}},
    )

    revoked: bool
    count: int
