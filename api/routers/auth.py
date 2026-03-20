from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.core.database import get_db
from api.core.token import issue_token
from api.models.organisation import Organisation
from api.models.user import User
from api.schemas.auth import AuthTokenRequest, AuthTokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)
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


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "type": "about:blank",
            "title": "Unauthorized",
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": "Authentication failed.",
        },
    )


def _extract_verified_claims(payload: dict) -> tuple[str, str, str | None]:
    claims = payload.get("claims") if isinstance(payload.get("claims"), dict) else payload
    user_id = claims.get("sub") or claims.get("user_id")
    email = (
        claims.get("email")
        or claims.get("email_address")
        or payload.get("email")
        or payload.get("email_address")
    )
    org_name = claims.get("org_name") or claims.get("org_slug") or payload.get("org_name")

    if not email:
        email_addresses = claims.get("email_addresses") or payload.get("email_addresses") or []
        if email_addresses:
            first_email = email_addresses[0]
            if isinstance(first_email, dict):
                email = (
                    first_email.get("email_address")
                    or first_email.get("email")
                    or first_email.get("value")
                )
            elif isinstance(first_email, str):
                email = first_email

    if not user_id or not email:
        raise _unauthorized_exception()

    return str(user_id), str(email), org_name


async def _verify_clerk_session_token(clerk_session_token: str) -> tuple[str, str, str | None]:
    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.clerk.com/v1/tokens/verify",
                params={"token": clerk_session_token},
                headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
            )
    except httpx.HTTPError as exc:
        raise _unauthorized_exception() from exc

    if response.status_code != status.HTTP_200_OK:
        raise _unauthorized_exception()

    return _extract_verified_claims(response.json())


def _default_org_name(email: str) -> str:
    local_part, _, domain = email.partition("@")
    if domain:
        return f"{domain.split('.')[0]}-org"
    return f"{local_part or uuid4().hex[:8]}-org"


@router.post("/token", response_model=AuthTokenResponse, responses=PROBLEM_RESPONSES)
@limiter.limit("10/minute")
async def issue_auth_token(
    request: Request,
    payload: AuthTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokenResponse:
    """Exchange a verified Clerk session token for a Scopeform JWT."""
    clerk_user_id, email, org_name = await _verify_clerk_session_token(payload.clerk_session_token)

    existing_user = await db.scalar(
        select(User).where((User.clerk_user_id == clerk_user_id) | (User.email == email))
    )

    if existing_user is None:
        organisation = Organisation(name=org_name or _default_org_name(email))
        db.add(organisation)
        await db.flush()

        user = User(clerk_user_id=clerk_user_id, email=email, org_id=organisation.id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user = existing_user

    token = issue_token(user.id, user.org_id, [], "1h")
    return AuthTokenResponse(token=token, email=user.email)
