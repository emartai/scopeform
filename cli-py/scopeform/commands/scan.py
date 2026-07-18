from __future__ import annotations

"""scopeform scan — free, local shadow-agent / raw-credential detector.

Runs fully locally: nothing is sent anywhere and no login is required.
Finds raw provider API keys in .env files, source code, and config files,
plus GitHub Actions workflows that hand secrets straight to scripts, then
suggests the scopeform.yml that would replace them with scoped tokens.
"""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

console = Console()

# ── What we look for ──────────────────────────────────────────────────────────

# Provider-accurate secret patterns. Each maps to the service we can scope.
SECRET_PATTERNS: list[tuple[str, str, str, str]] = [
    # (finding label, service for scopeform.yml, risk, regex)
    ("Anthropic API key", "anthropic", "high", r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    ("OpenAI API key", "openai", "high", r"sk-(?!ant-)(?:proj-)?[A-Za-z0-9_\-]{20,}"),
    ("GitHub token", "github", "high", r"(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})"),
    ("Slack token", "slack", "high", r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    ("AWS access key", "aws", "high", r"AKIA[0-9A-Z]{16}"),
    ("Stripe live key", "stripe", "high", r"[sr]k_live_[A-Za-z0-9]{24,}"),
    ("Google API key", "google", "medium", r"AIza[0-9A-Za-z_\-]{35}"),
]

# Generic KEY=value assignments in .env-style files.
ENV_ASSIGNMENT = re.compile(
    r"^\s*(?P<name>[A-Z0-9_]*(?:API_KEY|APIKEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*)\s*=\s*(?P<value>[^\s#]{12,})",
)

# Values that are clearly placeholders, not live credentials.
PLACEHOLDER_HINTS = ("placeholder", "your", "xxx", "changeme", "example", "dummy", "<", "${", "REPLACE", "todo")

# GitHub Actions: secrets handed straight to run steps.
WORKFLOW_SECRET = re.compile(r"\$\{\{\s*secrets\.(?P<name>[A-Za-z0-9_]+)\s*\}\}")

SOURCE_SUFFIXES = {".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}
CONFIG_SUFFIXES = {".json", ".yml", ".yaml", ".toml", ".cfg", ".ini"}

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", "out", ".next", "coverage",
    ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "target", "vendor", ".turbo",
}

MAX_FILE_BYTES = 1_000_000  # skip anything bigger — not a config/source file


@dataclass
class Finding:
    file: str
    line: int
    kind: str          # e.g. "OpenAI API key"
    service: str | None  # scopeform service name when known
    risk: str          # high | medium
    detail: str        # human explanation with the REDACTED value


def _redact(value: str) -> str:
    return f"{value[:8]}…" if len(value) > 8 else "…"


def _looks_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(hint.lower() in lowered for hint in PLACEHOLDER_HINTS)


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield path


def _scan_line_for_secrets(rel: str, line_no: int, line: str) -> list[Finding]:
    findings: list[Finding] = []
    for kind, service, risk, pattern in SECRET_PATTERNS:
        for match in re.finditer(pattern, line):
            value = match.group(0)
            if _looks_placeholder(value):
                continue
            findings.append(
                Finding(
                    file=rel,
                    line=line_no,
                    kind=kind,
                    service=service,
                    risk=risk,
                    detail=f"{kind} ({_redact(value)}) — unscoped, unrevocable, unaudited",
                )
            )
            break  # one finding per pattern per line is enough
    return findings


def _scan_env_file(path: Path, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return findings

    for idx, line in enumerate(lines, start=1):
        specific = _scan_line_for_secrets(rel, idx, line)
        if specific:
            findings.extend(specific)
            continue
        match = ENV_ASSIGNMENT.match(line)
        if match and not _looks_placeholder(match.group("value")):
            name = match.group("name")
            if name == "SCOPEFORM_TOKEN":
                continue  # already scoped — that's the fix, not a finding
            findings.append(
                Finding(
                    file=rel,
                    line=idx,
                    kind="Credential in .env",
                    service=None,
                    risk="medium",
                    detail=f"{name}={_redact(match.group('value'))} — long-lived credential in plain text",
                )
            )
    return findings


def _scan_text_file(path: Path, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return findings
    for idx, line in enumerate(lines, start=1):
        findings.extend(_scan_line_for_secrets(rel, idx, line))
    return findings


def _scan_workflow(path: Path, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return findings
    for idx, line in enumerate(lines, start=1):
        for match in WORKFLOW_SECRET.finditer(line):
            name = match.group("name")
            if name in ("SCOPEFORM_TOKEN", "GITHUB_TOKEN"):
                continue  # scoped/native tokens are fine
            findings.append(
                Finding(
                    file=rel,
                    line=idx,
                    kind="Secret in CI workflow",
                    service=None,
                    risk="medium",
                    detail=f"secrets.{name} passed directly to a workflow step — prefer a fresh scoped token per run",
                )
            )
    return findings


def scan_directory(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(root):
        rel = path.relative_to(root).as_posix()
        name = path.name

        if name == "scopeform.yml":
            continue
        if name.startswith(".env"):
            findings.extend(_scan_env_file(path, rel))
        elif ".github/workflows/" in rel and path.suffix in (".yml", ".yaml"):
            findings.extend(_scan_workflow(path, rel))
        elif path.suffix in SOURCE_SUFFIXES or path.suffix in CONFIG_SUFFIXES:
            findings.extend(_scan_text_file(path, rel))
    return findings


# ── Suggested fix ─────────────────────────────────────────────────────────────

DEFAULT_ACTIONS = {
    "openai": ["chat.completions"],
    "anthropic": ["messages"],
    "github": ["repos.read"],
}


def build_suggested_config(findings: list[Finding]) -> dict | None:
    services = sorted({f.service for f in findings if f.service and f.service in DEFAULT_ACTIONS})
    if not services:
        return None
    return {
        "identity": {
            "name": "my-agent",
            "owner": "you@example.com",
            "environment": "production",
        },
        "ttl": "24h",
        "scopes": [{"service": svc, "actions": DEFAULT_ACTIONS[svc]} for svc in services],
    }


# ── Command ───────────────────────────────────────────────────────────────────

def scan_command(
    path: Path = typer.Argument(Path("."), help="Directory to scan (default: current directory)."),
    json_out: Path | None = typer.Option(None, "--json", help="Also write the findings report to a JSON file."),
) -> None:
    """Scan for raw agent credentials. Fully local — nothing leaves this machine."""
    root = path.resolve()
    if not root.is_dir():
        console.print(f"[bold red]Not a directory: {root}[/bold red]")
        raise typer.Exit(code=2)

    with console.status(f"Scanning {root}..."):
        findings = scan_directory(root)

    if json_out is not None:
        json_out.write_text(
            json.dumps({"root": str(root), "findings": [asdict(f) for f in findings]}, indent=2),
            encoding="utf-8",
        )

    if not findings:
        console.print("[green]✓ No raw agent credentials found.[/green]")
        console.print("Nothing to fix — or your keys are already behind scoped tokens.")
        raise typer.Exit(code=0)

    table = Table(title=f"Scopeform Scan — {len(findings)} finding(s)")
    table.add_column("Risk", style="bold")
    table.add_column("Location")
    table.add_column("Finding")
    for f in sorted(findings, key=lambda f: (f.risk != "high", f.file, f.line)):
        risk_style = "red" if f.risk == "high" else "yellow"
        table.add_row(f"[{risk_style}]{f.risk.upper()}[/{risk_style}]", f"{f.file}:{f.line}", f.detail)
    console.print(table)

    suggestion = build_suggested_config(findings)
    if suggestion is not None:
        console.print("\n[bold]Suggested scopeform.yml[/bold] — scoped, short-lived, revocable:")
        console.print(yaml.safe_dump(suggestion, sort_keys=False).rstrip())
        console.print("\nRun [cyan]scopeform init[/cyan] then [cyan]scopeform deploy[/cyan] to replace these keys with a scoped token.")

    if json_out is not None:
        console.print(f"\nReport written to [cyan]{json_out}[/cyan]")

    raise typer.Exit(code=1)
