<p align="center">
  <img src="logo.svg" alt="Scopeform" width="96" height="96" />
</p>

<h1 align="center">Scopeform</h1>
<p align="center"><strong>The open-source Okta for AI agents.</strong> Register every agent, issue scoped short-lived tokens, and revoke any agent's access in one click — on your own infrastructure.</p>

<p align="center">
  <a href="#quickstart-self-hosted">Quickstart</a> ·
  <a href="#scopeform-scan--find-your-shadow-agent-credentials">scopeform scan</a> ·
  <a href="#runtime-limits">Runtime limits</a> ·
  <a href="https://scopeform-web.vercel.app">Hosted demo</a>
</p>

---

## Why Scopeform?

Your AI agents call OpenAI, GitHub, and Anthropic with long-lived API keys hardcoded in `.env` files. When an agent is compromised — or just goes into a retry loop at 3am — you have no way to revoke *that agent's* access without rotating the key for everyone, and no record of what it did.

Scopeform fixes this. Each agent gets its own **scoped, short-lived token** — tied to the exact services, actions, models, and budgets it needs, nothing more. Revoke one agent in one click without touching anything else.

```
Without Scopeform          With Scopeform
──────────────────         ──────────────────────────────
OPENAI_API_KEY=sk-...  →   SCOPEFORM_TOKEN=eyJ... (24h, openai:chat.completions only)
Shared across agents       Per-agent, per-service, revocable
No audit trail             Full call log you own
No revocation              One-click revoke
No spending guardrails     Model allowlists + call & token budgets
```

**Free and open-source. Self-hosted by default** — your keys, your traffic, and your audit log never leave your infrastructure. A managed cloud is planned as an optional convenience; the core is free forever.

---

## `scopeform scan` — find your shadow agent credentials

No signup, no server, nothing leaves your machine:

```bash
pip install scopeform
scopeform scan
```

```
Scopeform Scan — 3 finding(s)
┌──────┬──────────────────┬─────────────────────────────────────────────────────────┐
│ Risk │ Location         │ Finding                                                 │
├──────┼──────────────────┼─────────────────────────────────────────────────────────┤
│ HIGH │ .env:1           │ OpenAI API key (sk-proj-a…) — unscoped, unrevocable     │
│ HIGH │ agent.py:14      │ GitHub token (ghp_4f9c…) — unscoped, unrevocable        │
│ MED  │ .github/…/ci.yml │ secrets.OPENAI_API_KEY passed directly to a step        │
└──────┴──────────────────┴─────────────────────────────────────────────────────────┘

Suggested scopeform.yml — scoped, short-lived, revocable: …
```

It reports raw keys in `.env` files, hardcoded keys in source, and CI workflows that hand secrets straight to scripts — with a suggested `scopeform.yml` to fix each one. Add `--json report.json` for CI; exit code is `1` when findings exist.

---

## Quickstart (self-hosted)

### 1. Start your Scopeform instance

```bash
git clone https://github.com/emartai/scopeform
cd scopeform
cp .env.example .env   # then set JWT_SECRET and ENCRYPTION_KEY (instructions inside)
docker compose up
```

That's the full stack: API on `:8000`, dashboard on `:3000`, PostgreSQL, and Redis — all yours.

### 2. Install the CLI

```bash
pip install scopeform        # Python
npm install -g scopeform     # or Node.js
```

### 3. Create your account (on your own instance)

```bash
scopeform login              # defaults to http://localhost:8000
```

The CLI targets `http://localhost:8000` by default. Point it elsewhere with `--api-url`, `SCOPEFORM_API_URL`, or just log in once — the URL is remembered.

### 4. Declare your agent

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

# Optional runtime limits — enforced by the proxy, carried in the token
limits:
  models: [gpt-4o-mini]
  max_calls_per_hour: 100
  max_tokens_per_day: 200000
```

### 5. Add your provider keys — to *your* instance

Open your dashboard at `http://localhost:3000` → **Integrations** and add your OpenAI / Anthropic / GitHub keys. They're encrypted with your `ENCRYPTION_KEY` and stored in your database. No third party ever sees them.

### 6. Deploy and point your SDK at your proxy

```bash
scopeform deploy    # registers the agent, writes SCOPEFORM_TOKEN to .env
```

**Python (OpenAI)**
```python
import os, openai

openai.api_key  = os.environ["SCOPEFORM_TOKEN"]
openai.base_url = "http://localhost:8000/api/v1/proxy/openai/v1"
```

**Python (Anthropic)**
```python
import os, anthropic

client = anthropic.Anthropic(
    api_key=os.environ["SCOPEFORM_TOKEN"],
    base_url="http://localhost:8000/api/v1/proxy/anthropic/v1",
)
```

**Node.js (OpenAI)**
```js
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.SCOPEFORM_TOKEN,
  baseURL: "http://localhost:8000/api/v1/proxy/openai/v1",
});
```

The proxy validates the token, checks scopes and limits, logs the call, then forwards to the real provider. Out-of-scope calls return `403` and never reach the provider. Over-budget calls return `429`.

### 7. Operate

```bash
scopeform status               # agent state, recent + blocked calls
scopeform logs support-agent   # call log, --blocked-only to filter
scopeform revoke support-agent # kill every token for this agent, now
```

Or use the dashboard: agent registry, call logs, one-click revoke.

---

## Runtime limits

The most common agent incident isn't a stolen key — it's a runaway retry loop burning money overnight. Limits are declared in `scopeform.yml` and travel **inside the token**:

| Limit | Effect |
|---|---|
| `models: [gpt-4o-mini]` | Requests for any other model are blocked with `403` |
| `max_calls_per_hour: 100` | Calls beyond this return `429` for the rest of the hour |
| `max_tokens_per_day: 200000` | Metered from real provider usage; exhausted budget returns `429` until tomorrow |

Token metering applies to non-streaming responses; streaming calls still count toward the hourly call cap.

---

## GitHub Actions

Issue a fresh scoped token on every CI run instead of storing a long-lived credential:

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

See [`.github/workflows/scopeform-example.yml`](.github/workflows/scopeform-example.yml).

---

## Supported integrations

| Service | Actions |
|---|---|
| **OpenAI** | `chat.completions` · `embeddings` · `images.generations` |
| **Anthropic** | `messages` |
| **GitHub** | `repos.read` · `repos.write` · `issues.read` · `issues.write` · `pulls.read` |

More integrations coming — MCP server scoping is next on the roadmap.

---

## Pricing

**Self-hosted: free forever.** Unlimited agents, full call history on your own database, every feature in this repo. No account with us, no credit card, no telemetry.

A **managed cloud** (hosted proxy, team collaboration, cross-machine revocation) is planned as an optional paid convenience. The open-source core will never be feature-gated.

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
│              agent.py reads token               │
└────────────────────┬────────────────────────────┘
                     │ API call with Bearer token
                     ▼
         ┌───────────────────────┐
         │  Scopeform API        │  ← FastAPI — YOUR infrastructure
         │  - Validate token     │
         │  - Check scope        │
         │  - Enforce limits     │
         │  - Log call           │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  Dashboard            │  ← Next.js — YOUR infrastructure
         │  - Agent registry     │
         │  - Call logs          │
         │  - One-click revoke   │
         └───────────────────────┘
```

Availability stance: when the revocation store is unreachable, the proxy **fails closed** (blocks) — a security tool should never quietly stop enforcing.

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

<p align="center">An <a href="https://github.com/emartai">Emart AI</a> project · MIT licensed · Built in the open</p>
