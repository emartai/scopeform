from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_badge_unknown_agent(test_client):
    response = await test_client.get(f"/api/v1/badges/agent/{uuid4()}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert "unknown" in response.text


@pytest.mark.asyncio
async def test_badge_not_a_uuid(test_client):
    response = await test_client.get("/api/v1/badges/agent/not-a-uuid")
    assert response.status_code == 200
    assert "unknown" in response.text


@pytest.mark.asyncio
async def test_badge_agent_without_token_is_amber(test_client, test_agent):
    response = await test_client.get(f"/api/v1/badges/agent/{test_agent.id}")
    assert response.status_code == 200
    assert "no token" in response.text


@pytest.mark.asyncio
async def test_badge_agent_with_live_token_is_green(test_client, auth_headers, test_agent):
    issued = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(test_agent.id), "ttl": "1h"},
    )
    assert issued.status_code == 200

    response = await test_client.get(f"/api/v1/badges/agent/{test_agent.id}")
    assert response.status_code == 200
    assert "scoped" in response.text
