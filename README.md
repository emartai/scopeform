<p align="center">
  <img src="logo.svg" alt="Scopeform" width="96" height="96" />
</p>

<h1 align="center">Scopeform</h1>
<p align="center"><strong>Okta for AI agents.</strong> Register every agent, issue scoped short-lived tokens, and give your security team one place to monitor and revoke access.</p>

<p align="center">
  <a href="https://scopeform-web.vercel.app">Dashboard</a> ·
  <a href="https://scopeform-web.vercel.app/docs/quickstart">Quickstart</a> ·
  <a href="#installation">Install CLI</a>
</p>

---

## Why Scopeform?

Your AI agents call OpenAI, GitHub, and Anthropic with long-lived API keys hardcoded in `.env` files. When an agent is compromised, you have no way to revoke just that agent's access without rotating the key for everyone.

Scopeform fixes this. Each agent gets its own **scoped, short-lived token** — tied to the exact services and actions it needs, nothing more. Revoke one agent in one click without touching anything else.

```
Without Scopeform          With Scopeform
──────────────────         ──────────────────────────────
OPENAI_API_KEY=sk-...  →   SCOPEFORM_TOKEN=eyJ... (24h, openai:chat.completions only)
Shared across agents       Per-agent, per-service, revocable
No audit trail             Full call log in dashboard
No revocation              One-click revoke
```

---

## Quickstart

### 1. Install the CLI

**Python**
```bash
pip install scopeform
```

**Node.js**
```bash
npm install -g scopeform
```

### 2. Sign up and log in

```bash
scopeform login
# Email: you@example.com
# Password: ••••••••
# ✓ Logged in as you@example.com
```

### 3. Initialise your agent

```bash
cd my-agent/
scopeform init
```

This creates `scopeform.yml`:

```yaml
identity:
  name: support-agent
  owner: you@example.com
  environment: production

ttl: 24h

scopes:
  - service: openai
    actions:
      - chat.completions
  - service: github
    actions:
      - repos.read

integrations:
  ci: github-actions
```

### 4. Deploy

```bash
scopeform deploy
```

```
✓ Registering agent...
✓ Issuing scoped token...
✓ Deploy successful.

┌─────────────────┬──────────────────────────────┐
│ Agent           │ support-agent                │
│ Environment     │ production                   │
│ Token expires   │ 2026-03-21 12:00 UTC         │
│ Token written   │ .env                         │
└─────────────────┴──────────────────────────────┘
```

Your scoped token is written to `.env` as `SCOPEFORM_TOKEN`. Use it in your agent instead of raw API keys.

### 5. Use the token in your agent

**Python**
```python
import os
import openai

# Scopeform validates this token and enforces your declared scopes
openai.api_key = os.environ["SCOPEFORM_TOKEN"]
```

**Node.js**
```js
const token = process.env.SCOPEFORM_TOKEN;
// Pass to your OpenAI / Anthropic / GitHub client
```

---

## Dashboard

Sign in at **[scopeform-web.vercel.app](https://scopeform-web.vercel.app)** to see all your agents, their status, token expiry, and last activity. Revoke any agent's tokens with one click.

![Dashboard showing agent list with status badges and revoke buttons](https://via.placeholder.com/800x400/111111/22c55e?text=Dashboard+screenshot)

---

## GitHub Actions

Add `SCOPEFORM_TOKEN` to your repo secrets (copy from `~/.scopeform/config.json` after logging in), then use the example workflow:

```yaml
- name: Deploy agent and issue scoped token
  run: scopeform deploy
  env:
    SCOPEFORM_TOKEN: ${{ secrets.SCOPEFORM_TOKEN }}

- name: Run agent
  run: python agent.py
  env:
    SCOPEFORM_TOKEN: ${{ env.AGENT_TOKEN }}
```

See [`.github/workflows/scopeform-example.yml`](.github/workflows/scopeform-example.yml) for the full workflow.

---

## Supported integrations

| Service | Actions |
|---|---|
| **OpenAI** | `chat.completions` · `embeddings` · `images.generations` |
| **Anthropic** | `messages` |
| **GitHub** | `repos.read` · `repos.write` · `issues.read` · `issues.write` · `pulls.read` |

More integrations coming soon.

---

## Pricing

| | Free | Pro (coming soon) |
|---|---|---|
| Agents | 5 forever | Unlimited |
| Token TTL | Up to 30 days | Up to 30 days |
| Revocation | ✓ | ✓ |
| Audit logs | ✓ | ✓ |
| Team members | 1 | Unlimited |
| Price | $0 | TBD |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Your agent repo                                │
│  scopeform.yml ──► scopeform deploy             │
│                         │                       │
│                         ▼                       │
│              SCOPEFORM_TOKEN (.env)             │
│                         │                       │
│              agent.py reads token              │
└────────────────────┬────────────────────────────┘
                     │ API call with Bearer token
                     ▼
         ┌───────────────────────┐
         │  Scopeform API        │  ← FastAPI on Railway
         │  - Validate token     │
         │  - Check scope        │
         │  - Log call           │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  Dashboard            │  ← Next.js on Vercel
         │  - Agent list         │
         │  - Call logs          │
         │  - Revoke tokens      │
         └───────────────────────┘
```

---

## Self-hosting

```bash
git clone https://github.com/emartai/scopeform
cd scopeform

# Copy and fill in environment variables
cp .env.example .env

# Start everything
docker compose up
```

Requires: Docker, PostgreSQL, Redis.

---

## Contributing

PRs welcome. Please open an issue first for large changes.

```bash
# API (Python / FastAPI)
cd api && pip install -r requirements.txt
pytest

# Dashboard (Next.js)
cd web && npm install && npm test

# Python CLI
cd cli-py && pip install -e . && pytest

# Node CLI
cd cli-node && npm install && npm test
```

---

<p align="center">Built with ♥ · <a href="https://scopeform-web.vercel.app">scopeform-web.vercel.app</a></p>
