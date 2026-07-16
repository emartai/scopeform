from __future__ import annotations

import typer

from scopeform import __version__
from scopeform.commands import (
    deploy_command,
    init_command,
    login_command,
    logs_command,
    revoke_command,
    scan_command,
    status_command,
)
from scopeform.utils.config import resolve_api_url

app = typer.Typer(
    name="scopeform",
    help="Identity and access management for AI agents",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    api_url: str | None = typer.Option(
        None,
        "--api-url",
        help="Scopeform API base URL (default: SCOPEFORM_API_URL env, the URL saved at login, or http://localhost:8000).",
    ),
    version: bool | None = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the current package version.",
    ),
) -> None:
    """Configure shared CLI options."""
    ctx.obj = {"api_url": resolve_api_url(api_url)}


@app.command("login")
def login(ctx: typer.Context) -> None:
    login_command(api_url=ctx.obj["api_url"])


@app.command("init")
def init() -> None:
    init_command()


@app.command("deploy")
def deploy(ctx: typer.Context) -> None:
    deploy_command(api_url=ctx.obj["api_url"])


@app.command("revoke")
def revoke(agent_name: str, ctx: typer.Context) -> None:
    revoke_command(agent_name=agent_name, api_url=ctx.obj["api_url"])


@app.command("scan")
def scan(
    path: str = typer.Argument(".", help="Directory to scan (default: current directory)."),
    json_out: str | None = typer.Option(None, "--json", help="Also write the findings report to a JSON file."),
) -> None:
    """Scan for raw agent credentials — fully local, no login required."""
    from pathlib import Path

    scan_command(path=Path(path), json_out=Path(json_out) if json_out else None)


@app.command("status")
def status(ctx: typer.Context) -> None:
    """Show the current state of the agent declared in ./scopeform.yml."""
    status_command(api_url=ctx.obj["api_url"])


@app.command("logs")
def logs(
    agent_name: str,
    ctx: typer.Context,
    limit: int = typer.Option(20, "--limit", min=1, help="Maximum number of log entries to show."),
    service: str | None = typer.Option(None, "--service", help="Filter logs by service."),
    blocked_only: bool = typer.Option(False, "--blocked-only", help="Show only blocked calls."),
) -> None:
    logs_command(
        agent_name=agent_name,
        limit=limit,
        service=service,
        blocked_only=blocked_only,
        api_url=ctx.obj["api_url"],
    )
