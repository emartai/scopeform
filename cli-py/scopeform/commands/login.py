from __future__ import annotations

import base64
import json
from datetime import UTC, datetime

import typer
from rich.console import Console

from scopeform.utils.api_client import ScopeformClient, ScopeformClientError
from scopeform.utils.config import resolve_api_url, save_config

console = Console()


def _decode_token_expiry(token: str) -> str:
    try:
        payload_part = token.split(".")[1]
        padding = "=" * (-len(payload_part) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_part + padding)
        payload = json.loads(payload_bytes.decode("utf-8"))
        exp = int(payload["exp"])
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Could not parse token expiry from API response.") from exc

    return datetime.fromtimestamp(exp, tz=UTC).isoformat().replace("+00:00", "Z")


def login(api_url: str) -> None:
    """Authenticate with email and password and store the resulting Scopeform JWT."""
    email = typer.prompt("Email")
    password = typer.prompt("Password", hide_input=True)

    try:
        with ScopeformClient(base_url=api_url) as client:
            auth_response = client.login(email, password)

        save_config(
            {
                "token": auth_response["token"],
                "email": auth_response["email"],
                "expires_at": _decode_token_expiry(auth_response["token"]),
                # Remember which instance we logged into so later commands target it.
                "api_url": api_url,
            }
        )
        console.print(f"[green]\u2713 Logged in as {auth_response['email']}[/green]")
    except ScopeformClientError as exc:
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc


def login_command(
    api_url: str = typer.Option(None, "--api-url", help="Scopeform API base URL (default: env, saved login, or http://localhost:8000)."),
) -> None:
    """Sign in with email and password."""
    login(resolve_api_url(api_url))
