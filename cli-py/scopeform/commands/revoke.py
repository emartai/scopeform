from __future__ import annotations

import typer
from rich.console import Console

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


def revoke_command(
    agent_name: str,
    api_url: str = typer.Option("https://scopeform-production-f0b7.up.railway.app", "--api-url", help="Scopeform API base URL."),
) -> None:
    """Revoke all active tokens for an agent in the current organisation."""
    config = _require_login()
    confirmed = typer.confirm(
        f"Revoke all tokens for {agent_name}? This cannot be undone. [y/N]",
        default=False,
    )
    if not confirmed:
        console.print("Revocation cancelled.")
        raise typer.Exit(code=0)

    try:
        with ScopeformClient(base_url=api_url, token=config["token"]) as client:
            agent = _find_agent_by_name(client, agent_name)
            client.revoke_token(agent_id=agent["id"])
    except ScopeformNotFoundError:
        console.print(f"[bold red]Agent '{agent_name}' not found in your organisation.[/bold red]")
        raise typer.Exit(code=1) from None

    console.print(f"[green]\u2713 Tokens revoked for {agent_name}. All active sessions terminated.[/green]")
