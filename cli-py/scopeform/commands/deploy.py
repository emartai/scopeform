from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from scopeform.utils.api_client import (
    ScopeformClient,
    ScopeformConflictError,
    ScopeformNotFoundError,
)
from scopeform.utils.config import load_config
from scopeform.utils.yaml_utils import SCOPEFORM_YML_PATH, read_scopeform_yaml

console = Console()
ENV_PATH = Path(".env")
GITIGNORE_PATH = Path(".gitignore")


def _require_login() -> dict[str, Any]:
    config = load_config()
    if config is None:
        console.print("[bold red]Run `scopeform login` first[/bold red]")
        raise typer.Exit(code=1)
    return config


def _require_scopeform_yaml() -> dict[str, Any]:
    if not SCOPEFORM_YML_PATH.exists():
        console.print("[bold red]Run `scopeform init` first[/bold red]")
        raise typer.Exit(code=1)
    return read_scopeform_yaml(SCOPEFORM_YML_PATH)


def _find_agent_by_name(client: ScopeformClient, agent_name: str) -> dict[str, Any]:
    agents_response = client.list_agents()
    for agent in agents_response.get("items", []):
        if agent.get("name") == agent_name:
            return agent
    raise ScopeformNotFoundError(f"Agent '{agent_name}' not found.")


def _write_env_token(token: str, env_path: Path = ENV_PATH) -> None:
    line = f"SCOPEFORM_TOKEN={token}"
    if not env_path.exists():
        env_path.write_text(f"{line}\n", encoding="utf-8")
        return

    lines = env_path.read_text(encoding="utf-8").splitlines()
    replaced = False
    updated_lines: list[str] = []
    for existing in lines:
        if existing.startswith("SCOPEFORM_TOKEN="):
            updated_lines.append(line)
            replaced = True
        else:
            updated_lines.append(existing)
    if not replaced:
        updated_lines.append(line)
    env_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def _ensure_gitignore_has_env(gitignore_path: Path = GITIGNORE_PATH) -> None:
    if not gitignore_path.exists():
        gitignore_path.write_text(".env\n", encoding="utf-8")
        return

    lines = [line.strip() for line in gitignore_path.read_text(encoding="utf-8").splitlines()]
    if ".env" not in lines:
        contents = gitignore_path.read_text(encoding="utf-8")
        if contents and not contents.endswith("\n"):
            contents += "\n"
        gitignore_path.write_text(contents + ".env\n", encoding="utf-8")


def _format_expiry(expires_at: str) -> str:
    normalized = expires_at.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _build_success_table(agent_name: str, environment: str, expires_at: str) -> Table:
    table = Table(title="Scopeform Deploy")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Agent", agent_name)
    table.add_row("Environment", environment)
    table.add_row("Token expires", _format_expiry(expires_at))
    table.add_row("Token written to", ".env")
    table.add_row("Token", "****")
    return table


def deploy_command(
    api_url: str = typer.Option("https://scopeform-production-f0b7.up.railway.app", "--api-url", help="Scopeform API base URL."),
) -> None:
    """Register the current project as an agent and write its scoped token to .env."""
    config = _require_login()
    scopeform_config = _require_scopeform_yaml()
    identity = scopeform_config["identity"]
    agent_payload = {
        "name": identity["name"],
        "owner_email": identity["owner"],
        "environment": identity["environment"],
        "scopes": scopeform_config["scopes"],
    }

    with ScopeformClient(base_url=api_url, token=config["token"]) as client:
        try:
            with console.status("Registering agent..."):
                agent = client.register_agent(agent_payload)
        except ScopeformConflictError:
            console.print("Agent already registered. Issuing new token...")
            agent = _find_agent_by_name(client, identity["name"])

        with console.status("Issuing scoped token..."):
            token_response = client.issue_token(agent["id"], scopeform_config["ttl"])

    _write_env_token(token_response["token"])
    _ensure_gitignore_has_env()
    console.print("[green]Deploy successful.[/green]")
    console.print(
        _build_success_table(
            agent_name=identity["name"],
            environment=identity["environment"],
            expires_at=token_response["expires_at"],
        )
    )
    if scopeform_config.get("integrations", {}).get("ci") == "github-actions":
        console.print("Add SCOPEFORM_API_KEY to your GitHub Actions secrets")
