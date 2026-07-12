from __future__ import annotations

from datetime import UTC, datetime

import typer
from rich.console import Console
from rich.table import Table

from scopeform.commands.deploy import _find_agent_by_name, _require_scopeform_yaml
from scopeform.utils.api_client import ScopeformClient, ScopeformNotFoundError
from scopeform.utils.config import load_config

console = Console()


def _require_login() -> dict:
    config = load_config()
    if config is None:
        console.print("[bold red]Run `scopeform login` first[/bold red]")
        raise typer.Exit(code=1)
    return config


def _format_timestamp(value: str | None) -> str:
    if value is None:
        return "Never"
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _build_status_table(agent: dict) -> Table:
    table = Table(title=f"Status for {agent['name']}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Agent", agent["name"])
    table.add_row("Environment", agent["environment"])
    table.add_row("State", agent["status"])
    table.add_row("Last activity", _format_timestamp(agent.get("last_seen_at")))
    table.add_row("Scopes", str(len(agent.get("scopes", []))))
    return table


def status_command(
    api_url: str = typer.Option("https://scopeform-production-f0b7.up.railway.app", "--api-url", help="Scopeform API base URL."),
) -> None:
    """Display the current state of the agent registered in this project."""
    config = _require_login()
    scopeform_config = _require_scopeform_yaml()
    identity = scopeform_config["identity"]

    try:
        with ScopeformClient(base_url=api_url, token=config["token"]) as client:
            agent = _find_agent_by_name(client, identity["name"])
    except ScopeformNotFoundError:
        console.print(f"[bold red]Agent '{identity['name']}' not found. Run `scopeform deploy` first.[/bold red]")
        raise typer.Exit(code=1) from None

    console.print(_build_status_table(agent))
