from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.token import issue_token
from api.models.organisation import Organisation
from api.models.user import User
from api.schemas.auth import AuthTokenResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


def _conflict_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "type": "about:blank",
            "title": "Conflict",
            "status": status.HTTP_409_CONFLICT,
            "detail": detail,
        },
    )


def _default_org_name(email: str) -> str:
    local_part, _, domain = email.partition("@")
    if domain:
        return f"{domain.split('.')[0]}-org"
    return f"{local_part or uuid4().hex[:8]}-org"


@router.post("/register", response_model=AuthTokenResponse, responses=PROBLEM_RESPONSES, status_code=201)
@limiter.limit("10/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokenResponse:
    """Register a new user with email and password."""
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise _conflict_exception("An account with this email already exists.")

    org_name = payload.org_name or _default_org_name(payload.email)
    organisation = Organisation(name=org_name)
    db.add(organisation)
    await db.flush()

    user = User(
        email=payload.email,
        password_hash=pwd_context.hash(payload.password),
        org_id=organisation.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = issue_token(user.id, user.org_id, [], "24h")
    return AuthTokenResponse(token=token, email=user.email)


@router.post("/login", response_model=AuthTokenResponse, responses=PROBLEM_RESPONSES)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokenResponse:
    """Sign in with email and password."""
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.password_hash:
        raise _unauthorized_exception()

    if not pwd_context.verify(payload.password, user.password_hash):
        raise _unauthorized_exception()

    token = issue_token(user.id, user.org_id, [], "24h")
    return AuthTokenResponse(token=token, email=user.email)


