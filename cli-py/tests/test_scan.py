from __future__ import annotations

import json

import pytest
import typer
import yaml

from scopeform.commands.scan import scan_command, scan_directory
from scopeform.commands.status import status_command
from scopeform.utils.config import DEFAULT_API_URL, resolve_api_url


def test_scan_finds_provider_keys_in_env(tmp_path):
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwx123456\n"
        "ANTHROPIC_API_KEY=sk-ant-abcdefghijklmnopqrstuvwx\n"
        "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz0123456789\n"
        "SCOPEFORM_TOKEN=eyJhbGciOiJIUzI1NiJ9.payload.sig\n",
        encoding="utf-8",
    )

    findings = scan_directory(tmp_path)
    kinds = {f.kind for f in findings}
    assert "OpenAI API key" in kinds
    assert "Anthropic API key" in kinds
    assert "GitHub token" in kinds
    # An Anthropic key must not double-report as an OpenAI key
    assert sum(1 for f in findings if f.line == 2) == 1
    # SCOPEFORM_TOKEN is the fix, not a finding
    assert not any("SCOPEFORM_TOKEN" in f.detail for f in findings)
    # Raw secret values must never appear in the report
    assert not any("abcdefghijklmnopqrstuvwx123456" in f.detail for f in findings)


def test_scan_finds_hardcoded_key_in_source_and_workflow(tmp_path):
    (tmp_path / "agent.py").write_text(
        'client = OpenAI(api_key="sk-abcdefghijklmnopqrstuvwx123456")\n', encoding="utf-8"
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    workflows.joinpath("run.yml").write_text(
        "env:\n  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}\n  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n",
        encoding="utf-8",
    )

    findings = scan_directory(tmp_path)
    assert any(f.kind == "OpenAI API key" and f.file == "agent.py" for f in findings)
    assert any(f.kind == "Secret in CI workflow" for f in findings)
    # Native GITHUB_TOKEN should not be flagged
    assert not any("secrets.GITHUB_TOKEN" in f.detail for f in findings)


def test_scan_skips_placeholders_and_vendored_dirs(tmp_path):
    (tmp_path / ".env.example").write_text("OPENAI_API_KEY=your-key-here-placeholder\n", encoding="utf-8")
    vendored = tmp_path / "node_modules" / "pkg"
    vendored.mkdir(parents=True)
    vendored.joinpath("index.js").write_text('key = "sk-abcdefghijklmnopqrstuvwx123456"', encoding="utf-8")

    assert scan_directory(tmp_path) == []


def test_scan_command_exit_codes_and_json(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    # Clean directory exits 0
    with pytest.raises(typer.Exit) as exc:
        scan_command(path=tmp_path, json_out=None)
    assert exc.value.exit_code == 0

    # Findings exit 1 + write JSON + suggest scopeform.yml
    (tmp_path / ".env").write_text("OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwx123456\n", encoding="utf-8")
    report = tmp_path / "report.json"
    with pytest.raises(typer.Exit) as exc:
        scan_command(path=tmp_path, json_out=report)
    assert exc.value.exit_code == 1

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["findings"], "expected findings in JSON report"

    output = capsys.readouterr().out
    assert "Suggested scopeform.yml" in output
    assert "chat.completions" in output


def test_status_command_renders_agent_state(tmp_path, monkeypatch, capsys):
    class FakeClient:
        def __init__(self, base_url, token=None):
            assert base_url == "http://localhost:8000"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def list_agents(self):
            return {
                "items": [
                    {
                        "id": "agent-123",
                        "name": "alpha-agent",
                        "status": "active",
                        "environment": "production",
                        "owner_email": "owner@example.com",
                        "scopes": [{"service": "openai", "actions": ["chat.completions"]}],
                        "last_seen_at": "2026-07-16T00:00:00Z",
                    }
                ]
            }

        def get_logs(self, agent_id, limit):
            assert agent_id == "agent-123"
            return {
                "items": [
                    {"allowed": True, "called_at": "2026-07-16T01:00:00Z"},
                    {"allowed": False, "called_at": "2026-07-16T00:30:00Z"},
                ]
            }

    monkeypatch.chdir(tmp_path)
    (tmp_path / "scopeform.yml").write_text(
        yaml.safe_dump(
            {
                "identity": {"name": "alpha-agent", "owner": "owner@example.com", "environment": "production"},
                "scopes": [{"service": "openai", "actions": ["chat.completions"]}],
                "ttl": "24h",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("scopeform.commands.status._require_login", lambda: {"token": "user-token"})
    monkeypatch.setattr("scopeform.commands.status.ScopeformClient", FakeClient)

    status_command(api_url="http://localhost:8000")

    output = capsys.readouterr().out
    assert "alpha-agent" in output
    assert "active" in output
    assert "--blocked-only" in output  # one blocked call surfaced


def test_resolve_api_url_precedence(tmp_path, monkeypatch):
    fake_config = tmp_path / "config.json"
    monkeypatch.setattr("scopeform.utils.config.CONFIG_PATH", fake_config)
    monkeypatch.delenv("SCOPEFORM_API_URL", raising=False)

    # Default is local-first
    assert resolve_api_url(None) == DEFAULT_API_URL

    # Saved login URL wins over default
    fake_config.write_text(json.dumps({"api_url": "https://team.example.com"}), encoding="utf-8")
    assert resolve_api_url(None) == "https://team.example.com"

    # Env wins over saved
    monkeypatch.setenv("SCOPEFORM_API_URL", "https://env.example.com")
    assert resolve_api_url(None) == "https://env.example.com"

    # Explicit flag wins over everything
    assert resolve_api_url("https://flag.example.com") == "https://flag.example.com"
