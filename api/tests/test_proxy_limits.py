from __future__ import annotations

import pytest

import api.core.redis as redis_module
from api.routers.proxy import _day_key


async def _issue_token_with_limits(test_client, auth_headers, agent, limits: dict) -> str:
    response = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(agent.id), "ttl": "1h", "limits": limits},
    )
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.asyncio
async def test_proxy_blocks_model_outside_allowlist(test_client, auth_headers, test_agent):
    token = await _issue_token_with_limits(
        test_client, auth_headers, test_agent, {"models": ["gpt-4o-mini"]}
    )

    response = await test_client.post(
        "/api/v1/proxy/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}"},
        json={"model": "gpt-4", "messages": []},
    )

    assert response.status_code == 403
    assert "allowlist" in response.json()["detail"]


@pytest.mark.asyncio
async def test_proxy_allows_model_in_allowlist_up_to_integration(test_client, auth_headers, test_agent):
    token = await _issue_token_with_limits(
        test_client, auth_headers, test_agent, {"models": ["gpt-4o-mini"]}
    )

    response = await test_client.post(
        "/api/v1/proxy/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}"},
        json={"model": "gpt-4o-mini", "messages": []},
    )

    # Passes the allowlist; fails later only because no provider key is configured.
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_proxy_enforces_calls_per_hour(test_client, auth_headers, test_agent):
    token = await _issue_token_with_limits(
        test_client, auth_headers, test_agent, {"max_calls_per_hour": 2}
    )

    headers = {"Authorization": f"Bearer {token}"}
    body = {"model": "gpt-4o-mini", "messages": []}

    first = await test_client.post("/api/v1/proxy/openai/v1/chat/completions", headers=headers, json=body)
    second = await test_client.post("/api/v1/proxy/openai/v1/chat/completions", headers=headers, json=body)
    third = await test_client.post("/api/v1/proxy/openai/v1/chat/completions", headers=headers, json=body)

    assert first.status_code == 422   # within limit (blocked later by missing integration)
    assert second.status_code == 422  # within limit
    assert third.status_code == 429
    assert "calls/hour" in third.json()["detail"]


@pytest.mark.asyncio
async def test_proxy_enforces_daily_token_budget(test_client, auth_headers, test_agent):
    token = await _issue_token_with_limits(
        test_client, auth_headers, test_agent, {"max_tokens_per_day": 1000}
    )

    # Simulate a day of usage that has already exhausted the budget.
    await redis_module.redis_client.set(_day_key(str(test_agent.id)), 1000)

    response = await test_client.post(
        "/api/v1/proxy/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}"},
        json={"model": "gpt-4o-mini", "messages": []},
    )

    assert response.status_code == 429
    assert "token budget" in response.json()["detail"]


@pytest.mark.asyncio
async def test_proxy_without_limits_unaffected(test_client, auth_headers, test_agent):
    issued = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(test_agent.id), "ttl": "1h"},
    )
    token = issued.json()["token"]

    response = await test_client.post(
        "/api/v1/proxy/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}"},
        json={"model": "anything", "messages": []},
    )

    # No limits in the token → straight to the integration lookup.
    assert response.status_code == 422
