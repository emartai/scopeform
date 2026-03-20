# CLI Reference

## Global flags

- `--api-url TEXT`: Override the Scopeform API base URL. Default: `SCOPEFORM_API_URL` or `https://api.scopeform.dev`
- `--version`: Show the installed CLI version

## `scopeform login`

Open the browser login flow and store your CLI session securely.

```bash
scopeform login
```

Behavior:

- opens the sign-in flow in the browser
- exchanges the Clerk session for a Scopeform JWT
- saves the session to `~/.scopeform/config.json`

## `scopeform init`

Create `scopeform.yml` interactively.

```bash
scopeform init
```

Prompts include:

- agent name
- owner email
- environment
- scopes
- token TTL
- CI integration

## `scopeform deploy`

Register the current agent and issue a scoped runtime token.

```bash
scopeform deploy
```

Behavior:

- reads `scopeform.yml`
- registers the agent if needed
- issues a token
- writes `SCOPEFORM_TOKEN` to `.env`

## `scopeform revoke <agent-name>`

Revoke all active tokens for an agent.

```bash
scopeform revoke support-agent
```

Behavior:

- confirms the action
- revokes all active sessions for the named agent

## `scopeform logs <agent-name>`

Show recent call history for an agent.

```bash
scopeform logs support-agent
```

Flags:

- `--limit INTEGER`: Maximum number of rows to return. Default: `20`
- `--service TEXT`: Filter logs by service
- `--blocked-only`: Show only blocked calls

Example:

```bash
scopeform logs support-agent --service openai --blocked-only --limit 50
```
