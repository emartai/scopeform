from __future__ import annotations

import json

import pytest
from cryptography.fernet import Fernet

import api.routers.broker as broker_module
from api.core.config import get_settings
from api.routers.broker import _permissions_for
from api.tests.conftest import create_agent_record


def test_permissions_mapping_takes_highest_level():
    permissions = _permissions_for(["repos.read", "repos.write", "issues.read"])
    assert permissions["contents"] == "write"  # write beats read
    assert permissions["metadata"] == "read"
    assert permissions["issues"] == "read"


async def _issue_runtime_token(test_client, auth_headers, agent) -> str:
    response = await test_client.post(
        "/api/v1/tokens/issue",
        headers=auth_headers,
        json={"agent_id": str(agent.id), "ttl": "1h"},
    )
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.asyncio
async def test_broker_rejects_agent_without_github_scope(
    test_client, auth_headers, session_maker, test_org
):
    agent = await create_agent_record(
        session_maker,
        org_id=test_org.id,
        name="openai-only-agent",
        scopes=[{"service": "openai", "actions": ["chat.completions"]}],
    )
    token = await _issue_runtime_token(test_client, auth_headers, agent)

    response = await test_client.post(
        "/api/v1/broker/github",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_broker_requires_configured_github_app(
    test_client, auth_headers, session_maker, test_org
):
    agent = await create_agent_record(
        session_maker,
        org_id=test_org.id,
        name="github-agent-no-app",
        scopes=[{"service": "github", "actions": ["repos.read"]}],
    )
    token = await _issue_runtime_token(test_client, auth_headers, agent)

    response = await test_client.post(
        "/api/v1/broker/github",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert "GitHub App" in response.json()["detail"]


@pytest.mark.asyncio
async def test_broker_exchanges_for_installation_token(
    test_client, auth_headers, session_maker, test_org, monkeypatch
):
    agent = await create_agent_record(
        session_maker,
        org_id=test_org.id,
        name="github-agent",
        scopes=[{"service": "github", "actions": ["repos.read"]}],
    )

    # Enable encryption so the integration upsert works in tests.
    settings = get_settings()
    monkeypatch.setattr(settings, "encryption_key", Fernet.generate_key().decode())

    stored = await test_client.put(
        "/api/v1/integrations/github_app",
        headers=auth_headers,
        json={
            "api_key": json.dumps(
                {"app_id": "12345", "installation_id": "67890", "private_key": "fake-pem"}
            )
        },
    )
    assert stored.status_code == 200

    captured: dict = {}

    def fake_build_jwt(app_id: str, private_key: str) -> str:
        captured["app_id"] = app_id
        return "app-jwt"

    async def fake_fetch(app_jwt: str, installation_id: str, permissions: dict) -> dict:
        captured["installation_id"] = installation_id
        captured["permissions"] = permissions
        return {
            "token": "ghs_installation_token",
            "expires_at": "2026-07-17T12:00:00Z",
            "permissions": permissions,
        }

    monkeypatch.setattr(broker_module, "_build_app_jwt", fake_build_jwt)
    monkeypatch.setattr(broker_module, "_fetch_installation_token", fake_fetch)

    token = await _issue_runtime_token(test_client, auth_headers, agent)
    response = await test_client.post(
        "/api/v1/broker/github",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token"] == "ghs_installation_token"
    assert captured["app_id"] == "12345"
    assert captured["installation_id"] == "67890"
    # Native GitHub permission derived from the agent's scopeform.yml scope
    assert captured["permissions"].get("contents") == "read"
