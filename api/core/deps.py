from __future__ import annotations

import uuid

from api.core.database import get_db
from api.core.token import verify_token
from api.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


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


async def get_current_org_id(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    payload = await verify_token(token)

    try:
        return uuid.UUID(str(payload["org"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise _unauthorized_exception() from exc


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = await verify_token(token)

    try:
        user_id = uuid.UUID(str(payload["sub"]))
        org_id = uuid.UUID(str(payload["org"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise _unauthorized_exception() from exc

    user = await db.scalar(select(User).where(User.id == user_id, User.org_id == org_id))
    if user is None:
        raise _unauthorized_exception()

    return user
