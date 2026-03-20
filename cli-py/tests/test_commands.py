from __future__ import annotations

import click
import pytest
import yaml

from scopeform.commands.deploy import deploy_command
from scopeform.commands.init import init_command
from scopeform.commands.logs import logs_command
from scopeform.commands.revoke import revoke_command
from scopeform.utils.api_client import ScopeformConflictError


def test_init_flow_writes_scopeform_yaml(monkeypatch, tmp_path, capsys):
    answers = iter(
        [
            "bad agent!",
            "alpha_agent",
            "not-an-email",
            "owner@example.com",
            "staging",
            "openai,github",
            "chat.completions,responses.create",
            "issues.read,contents.read",
            "24hours",
            "24h",
            "github-actions",
        ]
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "scopeform.commands.init.typer.prompt",
        lambda *args, **kwargs: next(answers),
    )
    monkeypatch.setattr(
        "scopeform.commands.init.typer.confirm",
        lambda *args, **kwargs: True,
    )

    init_command()

    config_path = tmp_path / "scopeform.yml"
    assert config_path.exists()

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config == {
        "identity": {
            "name": "alpha_agent",
            "owner": "owner@example.com",
            "environment": "staging",
        },
        "scopes": [
            {
                "service": "openai",
                "actions": ["chat.completions", "responses.create"],
            },
            {
                "service": "github",
                "actions": ["issues.read", "contents.read"],
            },
        ],
        "ttl": "24h",
        "integrations": {"ci": "github-actions"},
    }

    output = capsys.readouterr().out
    assert "scopeform.yml created successfully." in output
    assert "Run `scopeform deploy` to register your agent" in output


def test_deploy_success(monkeypatch, tmp_path, capsys):
    class FakeClient:
        last_instance = None

        def __init__(self, base_url, token):
            self.base_url = base_url
            self.token = token
            self.calls = []
            FakeClient.last_instance = self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def register_agent(self, payload):
            self.calls.append(("register_agent", payload))
            return {"id": "agent-123", "name": payload["name"]}

        def issue_token(self, agent_id, ttl):
            self.calls.append(("issue_token", agent_id, ttl))
            return {
                "token": "secret-token-value",
                "jti": "jti-123",
                "expires_at": "2026-03-21T12:00:00Z",
            }

    monkeypatch.chdir(tmp_path)
    (tmp_path / "scopeform.yml").write_text(
        yaml.safe_dump(
            {
                "identity": {
                    "name": "alpha-agent",
                    "owner": "owner@example.com",
                    "environment": "production",
                },
                "scopes": [{"service": "openai", "actions": ["chat.completions"]}],
                "ttl": "24h",
                "integrations": {"ci": "github-actions"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

    monkeypatch.setattr("scopeform.commands.deploy.load_config", lambda: {"token": "user-token"})
    monkeypatch.setattr("scopeform.commands.deploy.ScopeformClient", FakeClient)

    deploy_command(api_url="http://localhost:8000")

    env_contents = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "SCOPEFORM_TOKEN=secret-token-value" in env_contents
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    output = capsys.readouterr().out
    assert "Deploy successful." in output
    assert "alpha-agent" in output
    assert "****" in output
    assert "Add SCOPEFORM_API_KEY to your GitHub Actions secrets" in output
    expected_call = (
        "register_agent",
        {
            "name": "alpha-agent",
            "owner_email": "owner@example.com",
            "environment": "production",
            "scopes": [{"service": "openai", "actions": ["chat.completions"]}],
        },
    )
    assert expected_call in FakeClient.last_instance.calls


def test_deploy_already_registered_agent(monkeypatch, tmp_path, capsys):
    class FakeClient:
        def __init__(self, base_url, token):
            self.base_url = base_url
            self.token = token

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def register_agent(self, payload):
            raise ScopeformConflictError("exists")

        def list_agents(self):
            return {"items": [{"id": "agent-123", "name": "alpha-agent"}], "total": 1}

        def issue_token(self, agent_id, ttl):
            assert agent_id == "agent-123"
            assert ttl == "24h"
            return {
                "token": "replacement-token",
                "jti": "jti-456",
                "expires_at": "2026-03-21T12:00:00Z",
            }

    monkeypatch.chdir(tmp_path)
    (tmp_path / "scopeform.yml").write_text(
        yaml.safe_dump(
            {
                "identity": {
                    "name": "alpha-agent",
                    "owner": "owner@example.com",
                    "environment": "staging",
                },
                "scopes": [{"service": "openai", "actions": ["chat.completions"]}],
                "ttl": "24h",
                "integrations": {"ci": "none"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("scopeform.commands.deploy.load_config", lambda: {"token": "user-token"})
    monkeypatch.setattr("scopeform.commands.deploy.ScopeformClient", FakeClient)

    deploy_command(api_url="http://localhost:8000")

    output = capsys.readouterr().out
    assert "Agent already registered. Issuing new token..." in output
    assert "SCOPEFORM_TOKEN=replacement-token" in (tmp_path / ".env").read_text(encoding="utf-8")


def test_deploy_missing_scopeform_yml(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("scopeform.commands.deploy.load_config", lambda: {"token": "user-token"})

    with pytest.raises(click.exceptions.Exit):
        deploy_command(api_url="http://localhost:8000")

    output = capsys.readouterr().out
    assert "Run `scopeform init` first" in output


def test_deploy_not_logged_in(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("scopeform.commands.deploy.load_config", lambda: None)

    with pytest.raises(click.exceptions.Exit):
        deploy_command(api_url="http://localhost:8000")

    output = capsys.readouterr().out
    assert "Run `scopeform login` first" in output


def test_revoke_command_success(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, base_url, token):
            self.base_url = base_url
            self.token = token
            self.revoked_agent_id = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def list_agents(self):
            return {"items": [{"id": "agent-123", "name": "alpha-agent"}], "total": 1}

        def revoke_token(self, *, jti=None, agent_id=None):
            self.revoked_agent_id = agent_id
            return {"revoked": True, "count": 2}

    monkeypatch.setattr("scopeform.commands.revoke.load_config", lambda: {"token": "user-token"})
    monkeypatch.setattr("scopeform.commands.revoke.ScopeformClient", FakeClient)
    monkeypatch.setattr("scopeform.commands.revoke.typer.confirm", lambda *args, **kwargs: True)

    revoke_command("alpha-agent", api_url="http://localhost:8000")

    output = capsys.readouterr().out
    assert "Tokens revoked for alpha-agent. All active sessions terminated." in output


def test_revoke_command_agent_not_found(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, base_url, token):
            self.base_url = base_url
            self.token = token

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def list_agents(self):
            return {"items": [], "total": 0}

    monkeypatch.setattr("scopeform.commands.revoke.load_config", lambda: {"token": "user-token"})
    monkeypatch.setattr("scopeform.commands.revoke.ScopeformClient", FakeClient)
    monkeypatch.setattr("scopeform.commands.revoke.typer.confirm", lambda *args, **kwargs: True)

    with pytest.raises(click.exceptions.Exit):
        revoke_command("missing-agent", api_url="http://localhost:8000")

    output = capsys.readouterr().out
    assert "Agent 'missing-agent' not found in your organisation." in output


def test_logs_command_renders_table(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, base_url, token):
            self.base_url = base_url
            self.token = token
            self.logs_request = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def list_agents(self):
            return {"items": [{"id": "agent-123", "name": "alpha-agent"}], "total": 1}

        def get_logs(self, **kwargs):
            self.logs_request = kwargs
            return {
                "items": [
                    {
                        "called_at": "2026-03-20T12:00:00Z",
                        "service": "openai",
                        "action": "chat.completions",
                        "allowed": True,
                    },
                    {
                        "called_at": "2026-03-20T12:05:00Z",
                        "service": "github",
                        "action": "issues.read",
                        "allowed": False,
                    },
                ],
                "total": 2,
            }

    monkeypatch.setattr("scopeform.commands.logs.load_config", lambda: {"token": "user-token"})
    monkeypatch.setattr("scopeform.commands.logs.ScopeformClient", FakeClient)

    logs_command("alpha-agent", limit=20, service="openai", blocked_only=True, api_url="http://localhost:8000")

    output = capsys.readouterr().out
    assert "Logs for alpha-agent" in output
    assert "chat.completions" in output
    assert "issues.read" in output
    assert "allowed" in output
    assert "blocked" in output


def test_logs_command_agent_not_found(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, base_url, token):
            self.base_url = base_url
            self.token = token

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def list_agents(self):
            return {"items": [], "total": 0}

    monkeypatch.setattr("scopeform.commands.logs.load_config", lambda: {"token": "user-token"})
    monkeypatch.setattr("scopeform.commands.logs.ScopeformClient", FakeClient)

    with pytest.raises(click.exceptions.Exit):
        logs_command("missing-agent", api_url="http://localhost:8000")

    output = capsys.readouterr().out
    assert "Agent 'missing-agent' not found in your organisation." in output
