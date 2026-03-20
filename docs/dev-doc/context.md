# Scopeform — project context

## What this product is

Scopeform is an "Okta for AI agents" — an identity and access management platform for AI agents. Every AI agent a team deploys gets a registered identity, a scoped short-lived token, an owner, and a lifecycle. The product prevents developers from running agents with hardcoded, unscoped, long-lived API keys and gives security/ops teams visibility over every agent running in their environment.

## Who uses it

Two personas:

1. **Developer** — deploys AI agents via CLI (`scopeform init`, `scopeform deploy`). Wants zero friction. Never wants to think about security setup.
2. **Security/ops person** — monitors agents via web dashboard. Wants visibility, risk signals, and one-click revocation. Never touches the CLI.

## MVP scope (what we are building now)

Only these features ship in MVP. Nothing else.

### CLI commands
- `scopeform login` — opens browser auth, stores token at `~/.scopeform/config.json`
- `scopeform init` — interactive prompts, generates `scopeform.yml` in current directory
- `scopeform deploy` — reads `scopeform.yml`, registers agent, issues scoped token, writes token to `.env`
- `scopeform revoke <agent-name>` — revokes agent token immediately
- `scopeform logs <agent-name>` — prints recent call history for the agent

### API endpoints
- `POST /auth/token` — issue a CLI auth token after Clerk login
- `POST /agents` — register a new agent
- `GET /agents` — list all agents for the org
- `GET /agents/{id}` — get single agent detail
- `PATCH /agents/{id}/status` — suspend or decommission an agent
- `POST /tokens/issue` — issue a scoped token for a registered agent
- `POST /tokens/revoke` — revoke a token immediately (also invalidates Redis cache)
- `POST /tokens/validate` — validate an incoming token (called by agent at runtime)
- `GET /agents/{id}/logs` — get call log for an agent

### Dashboard screens
- Agent list — table of all agents, status badges, revoke button per row
- Agent detail — identity card, scopes list, token status, last 5 log entries
- Logs page — filterable table of all agent call events

### Integrations (MVP only)
- OpenAI
- Anthropic
- GitHub

### CI target (MVP only)
- GitHub Actions only

## What is NOT in MVP
Do not build any of these until explicitly instructed:
- Behavior monitoring or anomaly detection
- Secrets rotation (scheduled)
- Compliance reports (SOC 2, ISO 27001)
- SSO / SAML
- Team RBAC inside Scopeform
- Terraform provider
- SDK wrappers for LangChain, CrewAI, etc.
- Multi-environment scoping beyond the `environment` field in `scopeform.yml`

---

## Tech stack

### Backend
- Language: Python 3.11+
- Framework: FastAPI (async)
- ORM: SQLAlchemy (async) + Alembic for migrations
- Validation: Pydantic v2
- Auth tokens: python-jose (JWT, HS256)
- Password/secret hashing: passlib + bcrypt
- Database: PostgreSQL 15
- Cache/revocation: Redis 7
- HTTP client (for Clerk): httpx

### Python CLI (`cli-py/`)
- Framework: Typer
- Terminal output: Rich
- YAML parsing: PyYAML
- HTTP to API: httpx
- Published to: PyPI as `scopeform`

### Node CLI (`cli-node/`)
- Framework: Commander.js
- Terminal output: Chalk + Ora
- YAML parsing: js-yaml
- HTTP to API: axios
- Published to: npm as `scopeform`

### Web dashboard (`web/`)
- Framework: Next.js 14 (App Router)
- Styling: Tailwind CSS
- Components: shadcn/ui
- Auth: Clerk (Next.js SDK)
- HTTP client: fetch / axios

### Infrastructure
- Backend hosting: Railway (FastAPI + PostgreSQL + Redis in one project)
- Frontend hosting: Vercel
- Containerisation: Docker + docker-compose for local dev
- CI/CD: GitHub Actions

### Monorepo
- Tool: Turborepo
- Root `package.json` for Node workspaces
- Root `pyproject.toml` for shared Python tooling (ruff, pytest)

---

## Repository structure

```
scopeform/
├── api/
│   ├── main.py                  # FastAPI app factory
│   ├── routers/
│   │   ├── agents.py
│   │   ├── tokens.py
│   │   ├── logs.py
│   │   └── auth.py
│   ├── models/
│   │   ├── agent.py
│   │   ├── token.py
│   │   ├── log.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── agent.py
│   │   ├── token.py
│   │   ├── log.py
│   │   └── auth.py
│   ├── core/
│   │   ├── config.py            # pydantic-settings env config
│   │   ├── database.py          # async SQLAlchemy engine + session
│   │   ├── redis.py             # Redis client
│   │   ├── token.py             # JWT issue/validate/revoke logic
│   │   └── deps.py              # FastAPI dependency injection
│   ├── migrations/              # Alembic
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_agents.py
│   │   ├── test_tokens.py
│   │   └── test_logs.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── cli-py/
│   ├── scopeform/
│   │   ├── __init__.py
│   │   ├── main.py              # Typer app entry point
│   │   ├── commands/
│   │   │   ├── init.py
│   │   │   ├── deploy.py
│   │   │   ├── revoke.py
│   │   │   ├── logs.py
│   │   │   └── login.py
│   │   └── utils/
│   │       ├── yaml_utils.py    # read/write scopeform.yml
│   │       ├── api_client.py    # httpx calls to backend
│   │       └── config.py        # read/write ~/.scopeform/config.json
│   ├── tests/
│   │   └── test_commands.py
│   └── pyproject.toml
│
├── cli-node/
│   ├── src/
│   │   ├── index.ts
│   │   └── commands/
│   │       ├── init.ts
│   │       ├── deploy.ts
│   │       ├── revoke.ts
│   │       ├── logs.ts
│   │       └── login.ts
│   ├── tests/
│   └── package.json
│
├── web/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # landing page
│   │   ├── dashboard/
│   │   │   ├── page.tsx         # agent list
│   │   │   ├── agents/
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx # agent detail
│   │   │   └── logs/
│   │   │       └── page.tsx     # logs
│   │   └── sign-in/
│   │       └── page.tsx
│   ├── components/
│   │   ├── AgentTable.tsx
│   │   ├── AgentDetail.tsx
│   │   ├── LogsTable.tsx
│   │   ├── StatusBadge.tsx
│   │   └── RevokeButton.tsx
│   ├── lib/
│   │   └── api.ts               # typed fetch wrappers
│   └── package.json
│
├── docker-compose.yml
├── Makefile
├── turbo.json
├── package.json                 # root Node workspace
└── .env.example
```

---

## scopeform.yml schema

```yaml
identity:
  name: string          # unique agent name within the org
  owner: string         # email of the responsible developer
  environment: string   # production | staging | development

scopes:
  - service: string     # openai | anthropic | github
    actions: [string]   # list of permitted actions

ttl: string             # e.g. 1h, 24h, 7d

integrations:
  ci: string            # github-actions (MVP only)
```

---

## Environment variables

All env vars live in `.env` (local) and are set in Railway/Vercel for production.

```
# API
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/scopeform
REDIS_URL=redis://localhost:6379
JWT_SECRET=<random 64-char hex string>
JWT_ALGORITHM=HS256
CLERK_SECRET_KEY=<from Clerk dashboard>
CLERK_PUBLISHABLE_KEY=<from Clerk dashboard>
API_BASE_URL=http://localhost:8000

# Web
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=<from Clerk dashboard>
CLERK_SECRET_KEY=<from Clerk dashboard>
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Database schema (summary)

### users
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| clerk_user_id | text unique | from Clerk |
| email | text unique | |
| org_id | uuid FK | |
| created_at | timestamptz | |

### organisations
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| name | text | |
| created_at | timestamptz | |

### agents
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| org_id | uuid FK | |
| name | text | unique per org |
| owner_email | text | |
| environment | text | production/staging/development |
| scopes | jsonb | array of {service, actions} |
| status | text | active/suspended/decommissioned |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### tokens
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| agent_id | uuid FK | |
| jti | text unique | JWT ID for revocation |
| expires_at | timestamptz | |
| revoked_at | timestamptz nullable | null = still valid |
| created_at | timestamptz | |

### call_logs
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| agent_id | uuid FK | |
| token_id | uuid FK | |
| service | text | e.g. openai |
| action | text | e.g. chat.completions |
| allowed | boolean | was the call permitted |
| called_at | timestamptz | |

---

## Key conventions

- All API routes are prefixed `/api/v1/`
- All timestamps are UTC, stored as `timestamptz`
- UUIDs everywhere (no integer PKs)
- Org-scoped queries — every DB query filters by `org_id` derived from the authenticated user
- Token revocation works by: (1) setting `revoked_at` in DB, (2) writing jti to Redis with TTL matching token expiry. Validation checks Redis first (fast path), then DB.
- The `SCOPEFORM_TOKEN` env var is what agents use at runtime — it is a JWT issued by Scopeform, not a raw third-party API key
- Errors follow RFC 7807 (problem+json): `{"type": "...", "title": "...", "status": 400, "detail": "..."}`
