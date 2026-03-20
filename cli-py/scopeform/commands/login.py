from __future__ import annotations

import base64
import json
import threading
import time
import webbrowser
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

import typer
from rich.console import Console

from scopeform.utils.api_client import ScopeformClient, ScopeformClientError
from scopeform.utils.config import save_config

console = Console()
CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = 9876
CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}"
SIGN_IN_URL = f"https://app.scopeform.dev/sign-in?cli=true&callback={CALLBACK_URL}"
LOGIN_TIMEOUT_SECONDS = 120


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


def _build_callback_server(result: dict[str, Any], received: threading.Event) -> HTTPServer:
    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            params = parse_qs(urlparse(self.path).query)
            clerk_session_token = (
                params.get("clerk_session_token", [None])[0]
                or params.get("session_token", [None])[0]
                or params.get("token", [None])[0]
            )

            if not clerk_session_token:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>Missing token</h1><p>You can close this window.</p>")
                return

            result["clerk_session_token"] = clerk_session_token
            received.set()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>Login complete</h1><p>You can return to the CLI.</p>")

            threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    return HTTPServer((CALLBACK_HOST, CALLBACK_PORT), CallbackHandler)


def login(api_url: str) -> None:
    """Authenticate via browser and store the resulting Scopeform JWT securely."""
    console.print("Opening browser for authentication...")

    callback_result: dict[str, Any] = {}
    token_received = threading.Event()
    server = _build_callback_server(callback_result, token_received)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        try:
            opened = webbrowser.open(SIGN_IN_URL)
        except Exception:
            opened = False
        if not opened:
            console.print("Could not open your browser automatically.")
            console.print("Open this URL in your browser to continue:")
            console.print(SIGN_IN_URL)

        deadline = time.monotonic() + LOGIN_TIMEOUT_SECONDS
        while not token_received.wait(timeout=0.2):
            if time.monotonic() >= deadline:
                console.print(
                    "[bold red]Timed out waiting for authentication callback after 120 seconds.[/bold red]"
                )
                raise typer.Exit(code=1)

        clerk_session_token = callback_result["clerk_session_token"]
        with ScopeformClient(base_url=api_url) as client:
            auth_response = client.exchange_auth_token(clerk_session_token)

        save_config(
            {
                "token": auth_response["token"],
                "email": auth_response["email"],
                "expires_at": _decode_token_expiry(auth_response["token"]),
            }
        )
        console.print(f"[green]\u2713 Logged in as {auth_response['email']}[/green]")
    except ScopeformClientError as exc:
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)


def login_command(
    api_url: str = typer.Option("https://api.scopeform.dev", "--api-url", help="Scopeform API base URL."),
) -> None:
    """Typer-compatible wrapper for browser-based CLI login."""
    login(api_url)
