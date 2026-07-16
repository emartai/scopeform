from __future__ import annotations

"""scopeform status — current state of the agent declared in ./scopeform.yml."""

from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from scopeform.commands.deploy import _find_agent_by_name, _require_login, _require_scopeform_yaml
from scopeform.utils.api_client import ScopeformClient, ScopeformNotFoundError
from scopeform.utils.config import resolve_api_url

console = Console()


def _summarise_logs(logs_response: dict[str, Any]) -> tuple[int, int, str | None]:
    items = logs_response.get("items", [])
    total = len(items)
    blocked = sum(1 for entry in items if not entry.get("allowed", True))
    last_call = items[0].get("called_at") if items else None
    return total, blocked, last_call


def status_command(
    api_url: str = typer.Option(None, "--api-url", help="Scopeform API base URL (default: env, saved login, or http://localhost:8000)."),
) -> None:
    """Show the current state of the agent declared in ./scopeform.yml."""
    config = _require_login()
    scopeform_config = _require_scopeform_yaml()
    agent_name = scopeform_config["identity"]["name"]

    try:
        with ScopeformClient(base_url=resolve_api_url(api_url), token=config["token"]) as client:
            agent = _find_agent_by_name(client, agent_name)
            logs_response = client.get_logs(agent_id=agent["id"], limit=50)
    except ScopeformNotFoundError:
        console.print(
            f"[yellow]Agent '{agent_name}' is not registered yet.[/yellow] Run [cyan]scopeform deploy[/cyan] first."
        )
        raise typer.Exit(code=1) from None

    total, blocked, last_call = _summarise_logs(logs_response)
    scopes = agent.get("scopes", [])
    scope_summary = ", ".join(
        f"{scope.get('service')}:{'|'.join(scope.get('actions', []))}" for scope in scopes
    ) or "(none)"

    table = Table(title=f"Scopeform Status — {agent_name}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Status", str(agent.get("status", "unknown")))
    table.add_row("Environment", str(agent.get("environment", "unknown")))
    table.add_row("Owner", str(agent.get("owner_email", "unknown")))
    table.add_row("Scopes", scope_summary)
    table.add_row("Last seen", str(agent.get("last_seen_at") or "never"))
    table.add_row("Recent calls (last 50)", str(total))
    table.add_row("Blocked calls (last 50)", str(blocked))
    if last_call:
        table.add_row("Most recent call", str(last_call))
    console.print(table)

    if blocked:
        console.print(
            f"[yellow]{blocked} recent call(s) were blocked.[/yellow] Run [cyan]scopeform logs {agent_name} --blocked-only[/cyan] to inspect."
        )
