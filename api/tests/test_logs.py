from __future__ import annotations

import pytest
from api.tests.conftest import count_logs, create_agent_record


@pytest.mark.asyncio
async def test_logs_created_on_validate_calls(test_client, auth_headers, test_agent, session_maker):
    issued = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(test_agent.id), "ttl": "1h"},
    )
    token = issued.json()["token"]

    before = await count_logs(session_maker)
    response = await test_client.post(
        "/api/v1/tokens/validate",
        json={"token": token, "service": "openai", "action": "chat.completions"},
    )
    after = await count_logs(session_maker)

    assert response.status_code == 200
    assert after == before + 1


@pytest.mark.asyncio
async def test_blocked_calls_logged_with_allowed_false(
    test_client,
    auth_headers,
    test_agent,
):
    issued = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(test_agent.id), "ttl": "1h"},
    )
    token = issued.json()["token"]

    validate = await test_client.post(
        "/api/v1/tokens/validate",
        json={"token": token, "service": "openai", "action": "embeddings.create"},
    )
    assert validate.status_code == 403

    logs = await test_client.get(f"/api/v1/agents/{test_agent.id}/logs", headers=auth_headers)
    assert logs.status_code == 200
    assert logs.json()["items"][0]["allowed"] is False


@pytest.mark.asyncio
async def test_org_isolation_on_log_queries(
    test_client,
    auth_headers,
    session_maker,
    other_org,
):
    foreign_agent = await create_agent_record(session_maker, org_id=other_org.id, name="foreign-agent")

    response = await test_client.get(
        f"/api/v1/agents/{foreign_agent.id}/logs",
        headers=auth_headers,
    )

    assert response.status_code == 404
