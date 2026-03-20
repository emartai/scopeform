from __future__ import annotations

import pytest
from api.models.token import Token
from api.tests.conftest import create_agent_record
from sqlalchemy import select


@pytest.mark.asyncio
async def test_register_agent_success(test_client, auth_headers):
    response = await test_client.post(
        "/api/v1/agents",
        headers=auth_headers,
        json={
            "name": "new-agent",
            "owner_email": "owner@example.com",
            "environment": "production",
            "scopes": [{"service": "openai", "actions": ["chat.completions"]}],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "new-agent"
    assert body["status"] == "active"


@pytest.mark.asyncio
async def test_register_agent_duplicate_name_same_org(test_client, auth_headers, test_agent):
    response = await test_client.post(
        "/api/v1/agents",
        headers=auth_headers,
        json={
            "name": test_agent.name,
            "owner_email": "owner@example.com",
            "environment": "production",
            "scopes": [{"service": "openai", "actions": ["chat.completions"]}],
        },
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_agent_invalid_name_characters(test_client, auth_headers):
    response = await test_client.post(
        "/api/v1/agents",
        headers=auth_headers,
        json={
            "name": "bad agent!",
            "owner_email": "owner@example.com",
            "environment": "production",
            "scopes": [{"service": "openai", "actions": ["chat.completions"]}],
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_agents_returns_only_current_org(
    test_client,
    auth_headers,
    session_maker,
    test_org,
    other_org,
):
    own_agent = await create_agent_record(session_maker, org_id=test_org.id, name="own-agent")
    await create_agent_record(session_maker, org_id=other_org.id, name="foreign-agent")

    response = await test_client.get("/api/v1/agents", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(own_agent.id)


@pytest.mark.asyncio
async def test_get_agent_different_org_returns_404(
    test_client,
    auth_headers,
    session_maker,
    other_org,
):
    foreign_agent = await create_agent_record(session_maker, org_id=other_org.id, name="foreign-agent")

    response = await test_client.get(f"/api/v1/agents/{foreign_agent.id}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_suspend_agent_also_revokes_active_tokens(
    test_client,
    auth_headers,
    session_maker,
    test_agent,
):
    issued = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(test_agent.id), "ttl": "1h"},
    )
    assert issued.status_code == 200
    jti = issued.json()["jti"]

    response = await test_client.patch(
        f"/api/v1/agents/{test_agent.id}/status",
        headers=auth_headers,
        json={"status": "suspended"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "suspended"

    async with session_maker() as session:
        token = await session.scalar(select(Token).where(Token.jti == jti))
        assert token is not None
        assert token.revoked_at is not None
