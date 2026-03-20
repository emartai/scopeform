from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr


class AuthTokenRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"clerk_session_token": "sess_test_123"}},
    )

    clerk_session_token: str


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"email": "user@example.com", "password": "secret", "org_name": "acme"}},
    )

    email: EmailStr
    password: str
    org_name: str | None = None


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"email": "user@example.com", "password": "secret"}},
    )

    email: EmailStr
    password: str


class AuthTokenResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "email": "user@example.com",
            }
        },
    )

    token: str
    email: EmailStr
