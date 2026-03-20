from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from scopeform.commands.deploy import _find_agent_by_name
from scopeform.utils.api_client import ScopeformClient, ScopeformNotFoundError
from scopeform.utils.config import load_config

console = Console()


def _require_login() -> dict:
    config = load_config()
    if config is None:
        console.print("[bold red]Run `scopeform login` first[/bold red]")
        raise typer.Exit(code=1)
    return config


def _build_logs_table(agent_name: str, entries: list[dict]) -> Table:
    table = Table(title=f"Logs for {agent_name}")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Service", style="white")
    table.add_column("Action", style="white")
    table.add_column("Status", style="white")

    for entry in entries:
        status = "[green]\u2713 allowed[/green]" if entry["allowed"] else "[red]\u2717 blocked[/red]"
        table.add_row(entry["called_at"], entry["service"], entry["action"], status)

    return table


def logs_command(
    agent_name: str,
    limit: int = typer.Option(20, "--limit", min=1, help="Maximum number of log entries to show."),
    service: str | None = typer.Option(None, "--service", help="Filter logs by service."),
    blocked_only: bool = typer.Option(False, "--blocked-only", help="Show only blocked calls."),
    api_url: str = typer.Option("https://api.scopeform.dev", "--api-url", help="Scopeform API base URL."),
) -> None:
    """Display recent call logs for an agent."""
    config = _require_login()

    try:
        with ScopeformClient(base_url=api_url, token=config["token"]) as client:
            agent = _find_agent_by_name(client, agent_name)
            logs_response = client.get_logs(
                agent_id=agent["id"],
                limit=limit,
                allowed=False if blocked_only else None,
                service=service,
            )
    except ScopeformNotFoundError:
        console.print(f"[bold red]Agent '{agent_name}' not found in your organisation.[/bold red]")
        raise typer.Exit(code=1) from None

    items = logs_response.get("items", [])
    if not items:
        console.print(f"No logs yet for {agent_name}.")
        return

    console.print(_build_logs_table(agent_name, items))
