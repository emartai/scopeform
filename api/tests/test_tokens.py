from __future__ import annotations

import pytest
from api.tests.conftest import create_agent_record, make_expired_runtime_token


@pytest.mark.asyncio
async def test_issue_token_for_active_agent_success(test_client, auth_headers, test_agent):
    response = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(test_agent.id), "ttl": "1h"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["jti"]


@pytest.mark.asyncio
async def test_issue_token_for_suspended_agent_fails(test_client, auth_headers, session_maker, test_org):
    suspended_agent = await create_agent_record(
        session_maker,
        org_id=test_org.id,
        name="suspended-agent",
        status="suspended",
    )

    response = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(suspended_agent.id), "ttl": "1h"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_validate_token_allowed_action(test_client, auth_headers, test_agent):
    issued = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(test_agent.id), "ttl": "1h"},
    )
    token = issued.json()["token"]

    response = await test_client.post(
        "/api/v1/tokens/validate",
        json={"token": token, "service": "openai", "action": "chat.completions"},
    )

    assert response.status_code == 200
    assert response.json() == {"allowed": True}


@pytest.mark.asyncio
async def test_validate_token_blocked_action(test_client, auth_headers, test_agent):
    issued = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(test_agent.id), "ttl": "1h"},
    )
    token = issued.json()["token"]

    response = await test_client.post(
        "/api/v1/tokens/validate",
        json={"token": token, "service": "openai", "action": "images.generate"},
    )

    assert response.status_code == 403
    assert response.json() == {"allowed": False}


@pytest.mark.asyncio
async def test_validate_revoked_token_returns_401(test_client, auth_headers, test_agent):
    issued = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(test_agent.id), "ttl": "1h"},
    )
    token = issued.json()["token"]
    jti = issued.json()["jti"]

    revoked = await test_client.post(
        "/api/v1/tokens/revoke",
        headers=auth_headers,
        json={"jti": jti},
    )
    assert revoked.status_code == 200

    response = await test_client.post(
        "/api/v1/tokens/validate",
        json={"token": token, "service": "openai", "action": "chat.completions"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_validate_expired_token_returns_401(test_client, test_agent, test_org):
    expired_token = make_expired_runtime_token(
        test_agent.id,
        test_org.id,
        [{"service": "openai", "actions": ["chat.completions"]}],
    )

    response = await test_client.post(
        "/api/v1/tokens/validate",
        json={"token": expired_token, "service": "openai", "action": "chat.completions"},
    )

    assert response.status_code == 401
