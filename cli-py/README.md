# Scopeform CLI

Identity and access management for AI agents.

## Installation

```bash
pip install scopeform
```

## Quickstart

1. Log in:

```bash
scopeform login
```

2. Initialize your agent project:

```bash
scopeform init
```

3. Register the agent and issue a scoped token:

```bash
scopeform deploy
```

4. Use `SCOPEFORM_TOKEN` in your agent runtime environment.

5. Revoke active sessions when needed:

```bash
scopeform revoke <agent-name>
```

## Commands

### `scopeform login`

Open the browser login flow and store your CLI auth token securely in `~/.scopeform/config.json`.

Flags:

- `--api-url TEXT` Override the Scopeform API base URL.

### `scopeform init`

Create a `scopeform.yml` file for the current project using interactive prompts.

### `scopeform deploy`

Register the current project as an agent and write `SCOPEFORM_TOKEN` to `.env`.

Flags:

- `--api-url TEXT` Override the Scopeform API base URL.

### `scopeform revoke <agent-name>`

Revoke all active tokens for the named agent.

Flags:

- `--api-url TEXT` Override the Scopeform API base URL.

### `scopeform logs <agent-name>`

Show recent logs for the named agent.

Flags:

- `--limit INTEGER` Maximum number of log entries to show. Default: `20`
- `--service TEXT` Filter by service
- `--blocked-only` Show only blocked calls
- `--api-url TEXT` Override the Scopeform API base URL.

### Global flags

- `--api-url TEXT` Default: `SCOPEFORM_API_URL` or `https://api.scopeform.dev`
- `--version` Show the installed package version
