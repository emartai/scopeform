from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import api.core.redis as redis_module
import api.core.token as token_module
import api.main as main_module
import api.routers.agents as agents_router
import api.routers.tokens as tokens_router
from api.core.config import get_settings
from api.core.database import Base, get_db
from api.core.token import issue_token
from api.main import create_app
from api.models.agent import Agent
from api.models.log import CallLog
from api.models.organisation import Organisation
from api.models.token import Token
from api.models.user import User


def _adapt_metadata_for_sqlite() -> None:
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.type.__class__.__module__.startswith("sqlalchemy.dialects.postgresql"):
                if column.type.__class__.__name__ == "UUID":
                    column.type = sa.String(36)
                elif column.type.__class__.__name__ == "JSONB":
                    column.type = sa.JSON()


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, Any] = {}
        self.expiry: dict[str, int] = {}

    async def get(self, key: str) -> Any:
        return self.store.get(key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        self.store[key] = value
        if ex is not None:
            self.expiry[key] = ex
        return True

    async def incr(self, key: str) -> int:
        value = int(self.store.get(key, 0)) + 1
        self.store[key] = value
        return value

    async def expire(self, key: str, seconds: int) -> bool:
        self.expiry[key] = seconds
        return True

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None


@pytest_asyncio.fixture
async def session_maker(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    _adapt_metadata_for_sqlite()
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionTesting = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    fake_redis = FakeRedis()

    monkeypatch.setattr(redis_module, "redis_client", fake_redis)
    monkeypatch.setattr(token_module, "redis_client", fake_redis)
    monkeypatch.setattr(tokens_router, "redis_client", fake_redis)
    monkeypatch.setattr(agents_router, "redis_client", fake_redis)
    monkeypatch.setattr(main_module, "redis_client", fake_redis)

    yield SessionTesting
    await engine.dispose()


@pytest_asyncio.fixture
async def test_app(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator:
    app = create_app()

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.state.db_healthy = True
    app.state.redis_healthy = True
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_client(test_app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def test_org(session_maker: async_sessionmaker[AsyncSession]) -> Organisation:
    async with session_maker() as session:
        org = Organisation(id=uuid4(), name="scopeform-org")
        session.add(org)
        await session.commit()
        await session.refresh(org)
        return org


@pytest_asyncio.fixture
async def other_org(session_maker: async_sessionmaker[AsyncSession]) -> Organisation:
    async with session_maker() as session:
        org = Organisation(id=uuid4(), name="other-org")
        session.add(org)
        await session.commit()
        await session.refresh(org)
        return org


@pytest_asyncio.fixture
async def test_user(
    session_maker: async_sessionmaker[AsyncSession],
    test_org: Organisation,
) -> User:
    async with session_maker() as session:
        user = User(
            id=uuid4(),
            clerk_user_id="clerk_test_user",
            email="user@example.com",
            org_id=test_org.id,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
def auth_headers(test_user: User, test_org: Organisation) -> dict[str, str]:
    token = issue_token(test_user.id, test_org.id, [], "1h")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_agent(
    session_maker: async_sessionmaker[AsyncSession],
    test_org: Organisation,
) -> Agent:
    async with session_maker() as session:
        agent = Agent(
            id=uuid4(),
            org_id=test_org.id,
            name="alpha-agent",
            owner_email="owner@example.com",
            environment="production",
            scopes=[{"service": "openai", "actions": ["chat.completions"]}],
            status="active",
        )
        session.add(agent)
        await session.commit()
        await session.refresh(agent)
        return agent


async def create_agent_record(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    org_id: UUID | str,
    name: str,
    owner_email: str = "owner@example.com",
    environment: str = "production",
    scopes: list[dict[str, Any]] | None = None,
    status: str = "active",
) -> Agent:
    async with session_maker() as session:
        agent = Agent(
            id=uuid4(),
            org_id=org_id,
            name=name,
            owner_email=owner_email,
            environment=environment,
            scopes=scopes or [{"service": "openai", "actions": ["chat.completions"]}],
            status=status,
        )
        session.add(agent)
        await session.commit()
        await session.refresh(agent)
        return agent


async def create_token_record(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    agent_id: UUID | str,
    jti: str,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> Token:
    async with session_maker() as session:
        token = Token(
            id=uuid4(),
            agent_id=agent_id,
            jti=jti,
            expires_at=expires_at or datetime.now(UTC) + timedelta(hours=1),
            revoked_at=revoked_at,
        )
        session.add(token)
        await session.commit()
        await session.refresh(token)
        return token


async def count_logs(session_maker: async_sessionmaker[AsyncSession]) -> int:
    async with session_maker() as session:
        return len((await session.scalars(sa.select(CallLog))).all())


def make_expired_runtime_token(agent_id: UUID | str, org_id: UUID | str, scopes: list[dict[str, Any]]) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "jti": str(uuid4()),
        "sub": str(agent_id),
        "org": str(org_id),
        "scopes": scopes,
        "iat": now - timedelta(hours=2),
        "nbf": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
