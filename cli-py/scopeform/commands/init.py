from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from scopeform.utils.yaml_utils import SCOPEFORM_YML_PATH, write_scopeform_yaml

console = Console()
AGENT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
TTL_PATTERN = re.compile(r"^\d+[smhd]$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ENVIRONMENTS = ["production", "staging", "development"]
CI_OPTIONS = ["github-actions", "none"]
SERVICE_ACTIONS = {
    "openai": ["chat.completions", "responses.create", "embeddings.create"],
    "anthropic": ["messages.create", "messages.stream"],
    "github": ["issues.read", "issues.write", "contents.read", "pull_requests.write"],
}


def _prompt_until_valid(
    prompt_text: str,
    validator: Callable[[str], bool],
    error_message: str,
    *,
    default: str | None = None,
) -> str:
    while True:
        value = typer.prompt(prompt_text, default=default).strip()
        if validator(value):
            return value
        console.print(f"[bold red]{error_message}[/bold red]")


def _prompt_choice(prompt_text: str, options: list[str], *, default: str | None = None) -> str:
    option_text = ", ".join(options)
    return _prompt_until_valid(
        f"{prompt_text} [{option_text}]",
        lambda value: value in options,
        f"Choose one of: {option_text}",
        default=default,
    )


def _prompt_multi_choice(prompt_text: str, options: list[str]) -> list[str]:
    option_text = ", ".join(options)

    def validator(value: str) -> bool:
        selections = [item.strip() for item in value.split(",") if item.strip()]
        return bool(selections) and all(selection in options for selection in selections)

    raw_value = _prompt_until_valid(
        f"{prompt_text} [{option_text}]",
        validator,
        f"Enter one or more comma-separated values from: {option_text}",
    )
    seen: list[str] = []
    for item in [entry.strip() for entry in raw_value.split(",") if entry.strip()]:
        if item not in seen:
            seen.append(item)
    return seen


def _build_summary_table(config: dict) -> Table:
    table = Table(title="Scopeform Agent Config")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Agent name", config["identity"]["name"])
    table.add_row("Owner email", config["identity"]["owner"])
    table.add_row("Environment", config["identity"]["environment"])
    table.add_row("Services", ", ".join(scope["service"] for scope in config["scopes"]))
    table.add_row("TTL", config["ttl"])
    table.add_row("CI integration", config["integrations"]["ci"])
    return table


def init_command() -> None:
    """Interactively create a scopeform.yml file in the current directory."""
    config_path = Path.cwd() / SCOPEFORM_YML_PATH
    if config_path.exists() and not typer.confirm("Overwrite? [y/N]", default=False):
        console.print("Keeping the existing scopeform.yml.")
        raise typer.Exit(code=0)

    agent_name = _prompt_until_valid(
        "Agent name",
        lambda value: bool(AGENT_NAME_PATTERN.fullmatch(value)),
        "Agent name must match ^[a-zA-Z0-9_-]{1,64}$.",
    )
    owner_email = _prompt_until_valid(
        "Owner email",
        lambda value: bool(EMAIL_PATTERN.fullmatch(value)),
        "Enter a valid email address.",
    )
    environment = _prompt_choice("Environment", ENVIRONMENTS, default="development")
    selected_services = _prompt_multi_choice("Services", list(SERVICE_ACTIONS))

    scopes: list[dict[str, list[str] | str]] = []
    for service in selected_services:
        actions = _prompt_multi_choice(f"Actions for {service}", SERVICE_ACTIONS[service])
        scopes.append({"service": service, "actions": actions})

    ttl = _prompt_until_valid(
        "TTL",
        lambda value: bool(TTL_PATTERN.fullmatch(value)),
        "TTL must match ^\\d+[smhd]$.",
        default="24h",
    )
    ci_integration = _prompt_choice("CI integration", CI_OPTIONS, default="github-actions")

    config = {
        "identity": {
            "name": agent_name,
            "owner": owner_email,
            "environment": environment,
        },
        "scopes": scopes,
        "ttl": ttl,
        "integrations": {
            "ci": ci_integration,
        },
    }

    write_scopeform_yaml(config, config_path)
    console.print("[green]scopeform.yml created successfully.[/green]")
    console.print(_build_summary_table(config))
    console.print("Run `scopeform deploy` to register your agent")
