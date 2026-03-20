# Scopeform — 30 build prompts

Use these prompts sequentially with Claude Code, Codex, or Cursor. Each prompt builds on the previous one. Before starting, load `context.md`, `security.md`, and `design.md` into your AI context window.

> **Design note**: `design.md` is required context for all Phase 5 prompts (23–27). It defines every color, font, component style, logo construction, and interaction pattern. Claude Code must follow it exactly — do not use default shadcn/ui theme colors or Tailwind defaults where design.md specifies overrides.

---

## Phase 1 — Scaffold & database (prompts 1–5)

### Prompt 01 — Monorepo scaffold

```
Create the Scopeform monorepo scaffold using the structure defined in context.md.

Tasks:
- Create all directories: /api, /cli-py, /cli-node, /web
- Create root turbo.json with build, dev, test, lint pipelines
- Create root package.json as a Node workspace pointing to cli-node/ and web/
- Create root pyproject.toml with ruff and pytest config covering api/ and cli-py/
- Create .env.example with all env vars from context.md (placeholder values only)
- Create .gitignore covering: .env, __pycache__, .venv, node_modules, .next, dist, *.egg-info
- Create a root Makefile with targets: make dev, make migrate, make test, make lint

Do not create any application code yet — scaffold only.
```

---

### Prompt 02 — Database models

```
In api/models/, create SQLAlchemy async models for all five tables defined in context.md: users, organisations, agents, tokens, call_logs.

Requirements:
- Use SQLAlchemy 2.0 declarative style with async support
- All primary keys are UUID v4 (use sqlalchemy.dialects.postgresql.UUID)
- All timestamps are DateTime with timezone=True, default=func.now()
- agents.scopes is a JSONB column
- agents.status is a String with a check constraint: ('active', 'suspended', 'decommissioned')
- tokens.revoked_at is nullable
- Add __repr__ methods to each model
- Create api/models/__init__.py that exports all models
- Create a Base = declarative_base() in api/core/database.py

Follow all security rules in security.md — especially the org_id isolation requirement.
```

---

### Prompt 03 — Alembic migrations

```
Set up Alembic in api/migrations/ and create the initial migration.

Tasks:
- Run `alembic init api/migrations` and configure env.py to use the async SQLAlchemy engine from api/core/database.py
- Set script_location in alembic.ini to api/migrations
- Import all models in env.py so autogenerate works correctly
- Generate the first migration: `alembic revision --autogenerate -m "initial schema"`
- Verify the migration creates all five tables with correct columns, types, and constraints

The migration must be reversible — both upgrade() and downgrade() must be complete.
```

---

### Prompt 04 — FastAPI app setup

```
Create the FastAPI application factory in api/main.py and the core infrastructure files.

Files to create:
- api/core/config.py — pydantic-settings Settings class reading all env vars from context.md
- api/core/database.py — async SQLAlchemy engine, SessionLocal, get_db dependency
- api/core/redis.py — Redis async client using aioredis, get_redis dependency
- api/main.py — FastAPI app with:
  - CORS middleware (origins from config, not wildcard)
  - Security headers middleware (as defined in security.md)
  - Lifespan handler that tests DB and Redis connections on startup
  - GET /health endpoint returning {"status": "ok", "db": true, "redis": true}
  - Include routers from api/routers/ (create empty router files as stubs)
  - All routes prefixed with /api/v1/

Follow all security rules in security.md for CORS and headers.
```

---

### Prompt 05 — Docker local dev

```
Create Docker configuration for local development.

Files to create:
- api/Dockerfile — multi-stage build: base python:3.11-slim, install requirements, copy app, run with uvicorn
- docker-compose.yml in root with three services:
  - postgres: image postgres:15-alpine, port 5432, volume for persistence, healthcheck
  - redis: image redis:7-alpine, port 6379, healthcheck
  - api: builds from api/Dockerfile, depends_on postgres and redis with health conditions, mounts api/ as volume for hot reload, port 8000
- api/requirements.txt with pinned versions: fastapi, uvicorn[standard], sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, python-jose[cryptography], passlib[bcrypt], redis, aioredis, httpx, slowapi

Update Makefile:
- make dev: runs docker-compose up --build
- make migrate: runs alembic upgrade head inside the api container
- make test: runs pytest inside the api container
- make logs: tails docker-compose logs -f api
```

---

## Phase 2 — Core API (prompts 6–13)

### Prompt 06 — Pydantic schemas

```
Create all Pydantic v2 request and response schemas in api/schemas/.

Files:
- api/schemas/agent.py — AgentCreate, AgentUpdate, AgentResponse, AgentListResponse
- api/schemas/token.py — TokenIssueRequest, TokenIssueResponse, TokenRevokeRequest, TokenValidateRequest, TokenValidateResponse
- api/schemas/log.py — LogEntry, LogListResponse
- api/schemas/auth.py — AuthTokenRequest, AuthTokenResponse

Requirements:
- Use model_config = ConfigDict(extra='forbid') on all input schemas
- Agent name validated with regex: ^[a-zA-Z0-9_-]{1,64}$
- Owner validated as EmailStr
- Environment is Literal['production', 'staging', 'development']
- Service is Literal['openai', 'anthropic', 'github']
- TTL validated with pattern ^\d+[smhd]$
- All response schemas use model_config = ConfigDict(from_attributes=True) for ORM compatibility
- UUIDs are serialised as strings in responses

Follow security.md validation rules exactly.
```

---

### Prompt 07 — JWT token core

```
Create the token issuance and validation logic in api/core/token.py.

Functions to implement:
- issue_token(agent_id, org_id, scopes, ttl_string) -> str
  - Generates a UUID v4 jti
  - Builds JWT payload with: jti, sub (agent_id), org (org_id), scopes, exp, iat, nbf
  - Signs with JWT_SECRET using HS256
  - Returns the signed JWT string

- verify_token(token: str) -> dict
  - Verifies signature, exp, nbf
  - Checks jti against Redis revocation set
  - On any failure raises HTTPException 401 (never reveals reason)
  - Returns the decoded payload dict

- revoke_token(jti: str, expires_at: datetime, redis_client)
  - Writes jti to Redis with TTL = max(0, expires_at - now) seconds
  - Key pattern: "revoked:{jti}"

- parse_ttl(ttl_string: str) -> timedelta
  - Parses "24h", "7d", "30m", "3600s" into a timedelta
  - Raises ValueError for invalid format or TTL > 30 days

Follow all token security rules in security.md exactly.
```

---

### Prompt 08 — Auth router

```
Create api/routers/auth.py with the auth endpoints.

Endpoints:
- POST /api/v1/auth/token
  - Accepts a Clerk session token in the request body
  - Verifies it with Clerk's API (GET https://api.clerk.com/v1/tokens/verify)
  - Looks up or creates the user and org record in the DB
  - Issues a Scopeform JWT (1h TTL) for the user
  - Returns AuthTokenResponse with the JWT and user email
  - Rate limited: 10 requests per minute per IP (use slowapi)

Create api/core/deps.py with:
- get_current_user(token) — verifies JWT, returns user record
- get_current_org_id(token) — verifies JWT, returns org UUID
- These are FastAPI dependencies used in all protected routes

Follow security.md auth rules. Never log the token value.
```

---

### Prompt 09 — Agents router

```
Create api/routers/agents.py with all agent CRUD endpoints.

Endpoints:
- POST /api/v1/agents — register a new agent
  - Validates AgentCreate schema
  - Checks agent name is unique within the org
  - Creates agent record with status='active'
  - Returns AgentResponse

- GET /api/v1/agents — list all agents for the org
  - Filters by org_id from JWT (never from query params)
  - Returns AgentListResponse

- GET /api/v1/agents/{agent_id} — get single agent
  - Filters by both agent_id AND org_id
  - Returns 404 if not found (even if agent exists in another org — do not reveal existence)
  - Returns AgentResponse

- PATCH /api/v1/agents/{agent_id}/status — update agent status
  - Accepts {"status": "suspended" | "decommissioned"}
  - When decommissioning: also revokes all active tokens for this agent
  - Returns updated AgentResponse

All endpoints require authentication via get_current_org_id dependency.
Follow org isolation rules in security.md exactly.
```

---

### Prompt 10 — Tokens router

```
Create api/routers/tokens.py with token management endpoints.

Endpoints:
- POST /api/v1/tokens/issue
  - Verifies agent belongs to the requesting org
  - Verifies agent status is 'active' (returns 403 if suspended/decommissioned)
  - Issues JWT token using api/core/token.py issue_token()
  - Saves token record to DB (storing jti, agent_id, expires_at)
  - Returns TokenIssueResponse with the JWT string
  - Rate limited: 30 requests/min per org

- POST /api/v1/tokens/revoke
  - Accepts jti or agent_id (revoke by agent = revoke all active tokens)
  - Verifies ownership (agent must belong to requesting org)
  - Calls revoke_token() for each token
  - Sets revoked_at in DB
  - Returns {"revoked": true, "count": N}

- POST /api/v1/tokens/validate
  - Does NOT require user auth — this is called by agents at runtime
  - Accepts the agent's SCOPEFORM_TOKEN + the service + action being requested
  - Validates token, checks scopes, writes to call_logs
  - Returns {"allowed": true/false} — never more detail
  - Rate limited: 300 requests/min per org

Follow all token security rules in security.md.
```

---

### Prompt 11 — Logs router

```
Create api/routers/logs.py with the call log endpoints.

Endpoints:
- GET /api/v1/agents/{agent_id}/logs
  - Requires authentication
  - Filters by agent_id AND org_id
  - Accepts query params: limit (default 50, max 500), offset, allowed (bool filter), service (string filter)
  - Orders by called_at DESC
  - Returns LogListResponse

- GET /api/v1/logs
  - Org-level log view
  - Same query params as above plus agent_id filter
  - Returns all logs for the org
  - Orders by called_at DESC

Logs are read-only — no create/update/delete endpoints.
All queries must filter by org_id derived from JWT.
```

---

### Prompt 12 — API tests

```
Create comprehensive pytest tests in api/tests/.

Files:
- api/tests/conftest.py
  - Async test client using httpx.AsyncClient
  - Test database using SQLite in-memory (override DATABASE_URL)
  - Mock Redis client
  - Fixtures: test_app, test_client, test_org, test_user, auth_headers, test_agent

- api/tests/test_agents.py
  - Test register agent (success)
  - Test register agent with duplicate name in same org (should fail 409)
  - Test register agent with invalid name characters (should fail 422)
  - Test list agents returns only current org's agents
  - Test get agent from different org returns 404 (not 403)
  - Test suspend agent also revokes active tokens

- api/tests/test_tokens.py
  - Test issue token for active agent (success)
  - Test issue token for suspended agent (should fail 403)
  - Test validate token (allowed action)
  - Test validate token (blocked action — not in scopes)
  - Test validate revoked token (should fail 401)
  - Test validate expired token (should fail 401)

- api/tests/test_logs.py
  - Test logs are created on validate calls
  - Test blocked calls are logged with allowed=false
  - Test org isolation on log queries

All security boundary tests from security.md must be covered.
```

---

### Prompt 13 — API documentation

```
Add clear OpenAPI documentation to every endpoint.

Tasks:
- Add docstrings to every router function describing what it does
- Add response_model to every endpoint
- Add responses={} dict to document 401, 403, 404, 422 error shapes for each endpoint
- Add tags to each router: ["agents"], ["tokens"], ["logs"], ["auth"]
- Create api/core/openapi.py with custom OpenAPI metadata:
  - title: "Scopeform API"
  - description: "Identity and access management for AI agents"
  - version: "0.1.0"
  - contact: {name: "Scopeform", url: "https://scopeform.dev"}
- Add example request/response bodies to all schemas using Field(example=...)
- Verify that GET /api/v1/docs renders correctly with all endpoints documented
```

---

## Phase 3 — Python CLI (prompts 14–19)

### Prompt 14 — CLI scaffold and config

```
Set up the Python CLI package in cli-py/.

Tasks:
- Create cli-py/pyproject.toml:
  - Package name: scopeform
  - Entry point: scopeform = scopeform.main:app
  - Dependencies: typer[all], rich, pyyaml, httpx, pydantic
  - Dev dependencies: pytest, pytest-asyncio, respx (for httpx mocking)

- Create cli-py/scopeform/utils/config.py:
  - CONFIG_PATH = Path.home() / ".scopeform" / "config.json"
  - save_config(data: dict) — writes with os.chmod 0o600
  - load_config() -> dict | None — returns None if file missing or expired
  - clear_config() — deletes the config file

- Create cli-py/scopeform/utils/api_client.py:
  - ScopeformClient(base_url, token) wrapping httpx
  - Methods for every API endpoint: register_agent, list_agents, get_agent, issue_token, revoke_token, get_logs
  - Raises clear errors on 401, 403, 404 with Rich-formatted messages
  - Never logs the auth token

Follow security.md rules for config file permissions.
```

---

### Prompt 15 — login command

```
Create cli-py/scopeform/commands/login.py implementing `scopeform login`.

Behaviour:
- Print "Opening browser for authentication..."
- Open https://app.scopeform.dev/sign-in?cli=true&callback=http://localhost:9876 in the browser using webbrowser.open()
- Start a temporary local HTTP server on port 9876 waiting for the callback
- The callback delivers a Clerk session token as a query param
- Exchange the Clerk token for a Scopeform JWT via POST /api/v1/auth/token
- Save the JWT and email to ~/.scopeform/config.json with chmod 0600
- Print success: "✓ Logged in as user@example.com" using Rich green text
- If browser can't open, print the URL and ask user to open manually
- Timeout after 120 seconds with a clear error message

The local server must shut down cleanly after receiving the token (success or timeout).
Never print the JWT value to the terminal.
```

---

### Prompt 16 — init command

```
Create cli-py/scopeform/commands/init.py implementing `scopeform init`.

Behaviour:
- Check if scopeform.yml already exists in cwd — if so, ask "Overwrite? [y/N]"
- Use Rich prompts (typer.prompt or questionary) for interactive input:
  - Agent name (validate regex ^[a-zA-Z0-9_-]{1,64}$ inline, re-prompt on invalid)
  - Owner email (validate email format inline)
  - Environment (select from: production, staging, development)
  - Services (multi-select from: openai, anthropic, github)
  - For each selected service, show available actions and let user select
  - TTL (default: 24h, validate format)
  - CI integration (select from: github-actions, none)
- Write scopeform.yml to cwd
- Print success with a summary table using Rich
- Print next step: "Run `scopeform deploy` to register your agent"

Write a comprehensive test in cli-py/tests/test_commands.py covering the init flow with mocked prompts.
```

---

### Prompt 17 — deploy command

```
Create cli-py/scopeform/commands/deploy.py implementing `scopeform deploy`.

Behaviour:
- Check user is logged in (load_config()) — if not, print "Run `scopeform login` first" and exit
- Read and validate scopeform.yml from cwd — if missing, print "Run `scopeform init` first" and exit
- Show a Rich spinner: "Registering agent..."
- Call POST /api/v1/agents to register the agent
- If agent already exists (409), show "Agent already registered. Issuing new token..." and skip registration
- Show spinner: "Issuing scoped token..."
- Call POST /api/v1/tokens/issue
- Write SCOPEFORM_TOKEN=<value> to .env in cwd (append if .env exists, replace if key already present)
- Add .env to .gitignore if not already present
- Print success table using Rich:
  - Agent: <name>
  - Environment: <env>
  - Token expires: <human-readable time>
  - Token written to: .env
- If CI is github-actions, print a tip: "Add SCOPEFORM_API_KEY to your GitHub Actions secrets"

Never print the token value in plain text — mask it as "****" in the success output.
Write tests covering: successful deploy, already-registered agent, missing yml, not logged in.
```

---

### Prompt 18 — revoke and logs commands

```
Create the remaining two CLI commands.

cli-py/scopeform/commands/revoke.py — `scopeform revoke <agent-name>`:
- Check user is logged in
- Show confirmation: "Revoke all tokens for <agent-name>? This cannot be undone. [y/N]"
- Call POST /api/v1/tokens/revoke with agent name
- Show success: "✓ Tokens revoked for <agent-name>. All active sessions terminated."
- On 404: "Agent '<name>' not found in your organisation."

cli-py/scopeform/commands/logs.py — `scopeform logs <agent-name>`:
- Check user is logged in
- Accept optional flags: --limit (default 20), --service (filter), --blocked-only (flag)
- Call GET /api/v1/agents/{id}/logs
- Render as a Rich table with columns: Timestamp, Service, Action, Status
- Status column: green ✓ allowed / red ✗ blocked
- If no logs yet: "No logs yet for <agent-name>."
- If agent not found: clear 404 message

Write tests for both commands.
```

---

### Prompt 19 — CLI entry point and PyPI config

```
Wire up the CLI entry point and prepare for PyPI publishing.

Tasks:
- Create cli-py/scopeform/main.py:
  - Typer app with name="scopeform", help="Identity and access management for AI agents"
  - Add all commands: login, init, deploy, revoke, logs
  - Add --version flag showing current package version
  - Add --api-url option (default from SCOPEFORM_API_URL env var or https://api.scopeform.dev)

- Update cli-py/pyproject.toml:
  - Add all required metadata for PyPI: description, license, author, homepage, keywords
  - Add classifiers: Development Status, Intended Audience, Topic, License, Python versions
  - Configure hatch or flit as the build backend

- Create cli-py/README.md with:
  - Installation: pip install scopeform
  - Quickstart: the 5-step flow from context.md (login → init → deploy → use token → revoke)
  - All command reference with flags

- Test the full CLI end-to-end with a local API instance using the Makefile
```

---

## Phase 4 — Node CLI (prompts 20–22)

### Prompt 20 — Node CLI scaffold and shared commands

```
Create the Node.js CLI in cli-node/ that mirrors the Python CLI functionality.

Tasks:
- Create cli-node/package.json:
  - Name: scopeform, bin: {"scopeform": "./dist/index.js"}
  - Dependencies: commander, chalk, ora, js-yaml, axios, inquirer
  - Scripts: build (tsc), dev (ts-node), test (jest)

- Create cli-node/src/utils/config.ts — mirrors Python config.ts with same file path and 0600 permissions
- Create cli-node/src/utils/api-client.ts — axios client with same methods as Python client
- Create cli-node/src/commands/login.ts — same login flow as Python version
- Create cli-node/src/commands/init.ts — same init flow using inquirer prompts

All commands must produce identical output format to the Python CLI.
The Python CLI is the reference implementation — match its behaviour exactly.
```

---

### Prompt 21 — Node CLI deploy, revoke, logs

```
Create the remaining Node CLI commands, mirroring the Python CLI exactly.

Files:
- cli-node/src/commands/deploy.ts — identical behaviour to Python deploy command
- cli-node/src/commands/revoke.ts — identical behaviour to Python revoke command
- cli-node/src/commands/logs.ts — identical behaviour to Python logs command
- cli-node/src/index.ts — Commander app wiring all commands together, --version flag

Add Jest tests for all commands using axios-mock-adapter for HTTP mocking.

Verify: running `scopeform deploy` with the Node CLI and the Python CLI against the same API produces the same .env output.
```

---

### Prompt 22 — Node CLI npm publish config

```
Prepare the Node CLI for npm publishing.

Tasks:
- Add tsconfig.json with strict: true, target: ES2020, outDir: dist
- Add .npmignore excluding src/, tests/, tsconfig.json
- Update package.json:
  - Add description, keywords, homepage, bugs, repository fields
  - Set files: ["dist/**/*"]
  - Add prepublishOnly script that runs build and tests
- Create cli-node/README.md identical in content to cli-py/README.md but with npm install instructions
- Add a GitHub Actions workflow in .github/workflows/publish-node.yml that publishes to npm on tag push (v*.*.*)
- Add a GitHub Actions workflow in .github/workflows/publish-python.yml that publishes to PyPI on tag push
```

---

## Phase 5 — Web dashboard (prompts 23–27)

> Load `design.md` into context before running any prompt in this phase.

### Prompt 23 — Next.js scaffold, design system, and auth

```
Set up the Next.js dashboard in web/ following design.md exactly.

Tasks:
- Initialise Next.js 14 with App Router, TypeScript, and Tailwind CSS
- Install @clerk/nextjs and shadcn/ui
- Install Inter and JetBrains Mono via Google Fonts link in web/app/layout.tsx

Tailwind config (web/tailwind.config.js):
- Extend colors with the brand tokens from design.md:
  brand.green=#22c55e, brand.bg=#0a0a0a, brand.card=#111111,
  brand.elevated=#161616, brand.subtle=#1a1a1a, brand.border=#1f1f1f
- Extend fontFamily: sans=['Inter','sans-serif'], mono=['JetBrains Mono','monospace']

Override shadcn CSS variables in web/app/globals.css to match design.md colors exactly.
Do not use default shadcn dark theme — override every variable.

Create web/components/brand/Logo.tsx:
- Renders the SVG logo from design.md (ring + dot, exact opacity values)
- Accepts size prop: 'sm' (16px) | 'md' (24px) | 'lg' (40px)
- Accepts showWordmark prop: boolean
- Wordmark: lowercase 'scopeform', Inter 600

Create web/app/dashboard/layout.tsx (Shell):
- Left sidebar: 240px fixed, bg #111111, right border #1f1f1f
  - Logo section at top (icon + wordmark, 40px height)
  - Nav items: Agents, Logs, Settings (placeholder)
  - Active item: bg #1a1a1a, white text, 2px left border #22c55e
  - Inactive: text #a1a1aa, hover bg #161616
- Top bar: 48px, bg #0a0a0a, bottom border #1f1f1f
  - Left: current page breadcrumb (13px, #a1a1aa)
  - Right: org name (13px, white) + Clerk UserButton
- Main slot: padding 24px, max-width 1200px

Create web/middleware.ts protecting all /dashboard/* routes.
Create web/app/sign-in/page.tsx: centered card (380px, bg #111111, border #1f1f1f),
  Logo + wordmark at top, Clerk SignIn component below.
Create web/lib/api.ts with typed fetch wrappers for all API endpoints.

Create these reusable components per design.md specs:
- web/components/ui/StatusBadge.tsx (status + environment badges, exact colors from design.md badge color map)
- web/components/ui/SkeletonRow.tsx (shimmer animation, same height as table rows)
- web/components/ui/Toast.tsx (bottom-right, success/error left border)
- web/components/ui/RevokeButton.tsx (danger button + confirmation dialog per design.md spec)
```

---

### Prompt 24 — Agent list page

```
Create the agent list page at web/app/dashboard/page.tsx following design.md exactly.

Page header row:
- Left: "Agents" title (20px/600, white) + agent count gray pill badge
- Right: "Register Agent" primary button (white bg, dark text, 32px height)

Table (see design.md table specs):
- Wrapper: border #1f1f1f, border-radius 8px, overflow hidden
- Header: bg #111111, text 11px/500 uppercase #52525b, letter-spacing 0.04em, height 36px
- Rows: height 48px, hover bg #161616, bottom border #1f1f1f, cursor pointer
- Columns and widths exactly as specified in design.md agent list section

Column rendering:
- Agent Name: JetBrains Mono, white, 13px/500 — links to /dashboard/agents/[id]
- Owner: Inter, #a1a1aa, truncated with ellipsis
- Environment: StatusBadge component with exact colors from design.md
- Status: StatusBadge with dot indicator
- Token Expiry: relative time — yellow (#eab308) if expiring within 24h
- Last Active: relative time, #a1a1aa
- Actions: RevokeButton (disabled + grayed if already revoked/decommissioned)

Loading state: show 5 SkeletonRow components while fetching.

Empty state (centered in table area):
- "No agents registered yet." in #a1a1aa
- Code block below: $ scopeform deploy — bg #111111, border #1f1f1f, green text #22c55e, JetBrains Mono

Revoke flow:
- RevokeButton opens confirmation dialog (dialog spec from design.md)
- On confirm: optimistically update row status badge to "Revoked" immediately
- Call POST /api/v1/tokens/revoke
- On success: show success Toast "Token revoked for [agent-name]"
- On error: roll back optimistic update, show error Toast
```

---

### Prompt 25 — Agent detail page

```
Create the agent detail page at web/app/dashboard/agents/[id]/page.tsx following design.md exactly.

Header:
- "← Agents" back link (13px, #a1a1aa, hover #ffffff)
- Agent name on next line: JetBrains Mono, 24px, white
- Status badge inline after name

Two-column layout (left 55%, right 45%, gap 20px):

LEFT COLUMN — Identity card (design.md card styles: bg #111111, border #1f1f1f, border-radius 8px):
- Card header: "Identity" label (11px/500 uppercase, #52525b)
- Rows for: Name / Owner / Environment / Status / Created / Agent ID
- Each row: label (11px/500 uppercase, #52525b) + value (13px, #ffffff)
- Name + Agent ID values in JetBrains Mono
- Agent ID has copy-to-clipboard button (icon, 14px, #52525b, hover #ffffff)

LEFT COLUMN — Scopes card below identity:
- Card header: "Permitted scopes"
- Each scope: service pill + "→" arrow + action pill
- Pill style: bg #1a1a1a, border #1f1f1f, border-radius 4px, 11px/500, JetBrains Mono
- e.g. openai → chat.completions

RIGHT COLUMN — Token card (most prominent):
- Card header: "Current token"
- Status badge (24px height, large)
- Expiry line: countdown if active ("Expires in 6h 23m"), red "Expired" text if expired
- "Revoke Token" danger button: full width of card, 40px height, exact colors from design.md

RIGHT COLUMN — Recent activity mini-table below token card:
- Last 5 log entries
- Columns: Time (JetBrains Mono, #52525b) / Service (JetBrains Mono) / Action (JetBrains Mono) / Status badge
- Blocked rows: bg #1a0505, left border 2px solid #ef4444
- "View all logs →" link below (13px, #a1a1aa, hover #ffffff)

Show not-found.tsx if agent ID does not belong to the org (404).
```

---

### Prompt 26 — Logs page

```
Create the logs page at web/app/dashboard/logs/page.tsx following design.md exactly.

Filter bar (inline row, gap 8px):
- Agent dropdown: select from all org agents, default "All agents"
- Status filter: All / Allowed / Blocked
- Service filter: All / OpenAI / Anthropic / GitHub
- Date range: Last 1h / 6h / 24h / 7d buttons (toggle group style)
- "Clear filters" text link — appears only when any filter is active
- All inputs: 32px height, bg #111111, border #1f1f1f, text #a1a1aa
- Persist all filter state in URL search params (shareable/bookmarkable)

Logs table (design.md table specs):
Columns and widths exactly as in design.md logs section:
- Timestamp: JetBrains Mono, #52525b, 180px — show full datetime on hover (title attribute)
- Agent: JetBrains Mono, white, 180px
- Service / Action: JetBrains Mono, #a1a1aa, format "openai/chat.completions", 220px
- Status: "✓ Allowed" (green #22c55e) or "✗ Blocked" (red #ef4444), 100px

Blocked rows: bg #1a0505, left border 2px solid #ef4444.

Auto-refresh every 30 seconds.
"Last updated: X seconds ago" indicator — 12px, #52525b, top right of table.
Pagination: 50 rows per page, simple prev/next buttons.
- Empty state: "No logs yet. Logs appear here once your agents start making calls."

Use URL search params to persist filter state so the page is shareable/bookmarkable.
```

---

### Prompt 27 — Dashboard tests and polish

```
Add tests and final polish to the web dashboard. Use design.md as the visual reference.

Tests (Playwright or Vitest + React Testing Library):
- Agent list renders correctly with mock data, all columns visible
- Status badges use exact colors from design.md (test computed styles)
- Revoke button shows confirmation dialog before calling API
- Optimistic update: row badge changes to "Revoked" immediately on confirm
- Agent detail 404 state renders not-found.tsx correctly
- Logs filter state persists in URL params
- Blocked log rows have correct red tinted background and left border
- Auth redirect: unauthenticated user → /sign-in
- Logo renders at correct size for each context (sidebar=lg, topbar=md)

Polish tasks:
- Add loading.tsx for each route: skeleton rows matching exact table dimensions
- Add error.tsx for each route: minimal error message + retry button (secondary style)
- Add not-found.tsx for agent detail (404)
- Verify sidebar active indicator (2px green left bar) is correct on each route
- Verify JetBrains Mono is applied to all agent names, tokens, log entries, timestamps
- Verify all badge colors match design.md badge color map exactly
- Confirm blocked log rows in logs page have bg #1a0505 + 2px solid #ef4444 left border
- Add metadata exports to each route (title: "Agents — Scopeform", etc.)
- Sidebar collapses to 40px icon-only below 1024px viewport width
```

---

## Phase 6 — Integration, CI/CD, and docs (prompts 28–30)

### Prompt 28 — GitHub Actions CI pipeline

```
Create the CI/CD pipeline in .github/workflows/.

Files to create:

.github/workflows/ci.yml — runs on every PR:
- Job: test-api
  - Python 3.11
  - Start PostgreSQL and Redis as services
  - pip install requirements
  - Run alembic upgrade head
  - Run pytest with coverage (fail if below 80%)
  - Run pip audit (fail on high/critical CVEs)
  - Run ruff lint

- Job: test-cli-py
  - Python 3.11
  - pip install cli-py
  - Run pytest in cli-py/tests/

- Job: test-cli-node
  - Node 20
  - npm ci in cli-node/
  - Run npm test
  - Run npm audit (fail on high/critical)

- Job: test-web
  - Node 20
  - npm ci in web/
  - Run next build (type check + build)
  - Run Playwright tests

.github/workflows/deploy-api.yml — runs on push to main:
- Deploys to Railway using RAILWAY_TOKEN secret

.github/workflows/deploy-web.yml — Vercel handles this automatically via GitHub integration (add a note, no file needed)
```

---

### Prompt 29 — GitHub Actions agent integration

```
Create the GitHub Actions integration that developers add to their own repos.

Create docs/github-actions-integration.md documenting the integration.

Create .github/workflows/scopeform-example.yml as a reference workflow that teams can copy:

```yaml
name: Deploy agent with Scopeform

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Scopeform
        run: pip install scopeform

      - name: Issue scoped token
        run: scopeform deploy
        env:
          SCOPEFORM_API_KEY: ${{ secrets.SCOPEFORM_API_KEY }}

      - name: Run agent
        run: python agent.py
        env:
          SCOPEFORM_TOKEN: ${{ env.SCOPEFORM_TOKEN }}
```

Also create a GitHub Actions composite action in action.yml at the repo root so teams can use:
  uses: scopeform/scopeform@v1
  with:
    api-key: ${{ secrets.SCOPEFORM_API_KEY }}

Document how to get the SCOPEFORM_API_KEY from the dashboard and add it as a GitHub secret.
```

---

### Prompt 30 — Final documentation

```
Create the final documentation files.

docs/README.md — main docs index linking to all other docs files

docs/quickstart.md:
- Prerequisites: Python 3.8+ or Node 18+
- Step 1: pip install scopeform
- Step 2: scopeform login
- Step 3: cd your-agent && scopeform init
- Step 4: scopeform deploy
- Step 5: use SCOPEFORM_TOKEN in your agent code (show Python and Node examples)
- Step 6: view your agent at app.scopeform.dev

docs/cli-reference.md:
- Full reference for every command and flag with examples

docs/api-reference.md:
- Link to the live OpenAPI docs at api.scopeform.dev/api/v1/docs
- Document the token validation flow that agents use at runtime

docs/scopeform-yml.md:
- Full schema reference with every field, type, allowed values, and examples
- Common configuration examples: OpenAI-only agent, multi-service agent, GitHub Actions setup

docs/security.md (public-facing version):
- How tokens work (short-lived, scoped JWTs)
- What Scopeform can and cannot see
- How to report security issues

web/app/page.tsx — update the landing page to link to docs/quickstart.md
```

---

## Notes for using these prompts

- Load `context.md`, `security.md`, and `design.md` into your AI context at the start of every session
- `design.md` is mandatory for Phase 5 (prompts 23–27) — without it the frontend will use wrong colors, fonts, and component styles
- Run each prompt in order — later prompts depend on earlier ones
- After every prompt, run `make test` before moving to the next prompt
- If a prompt produces incomplete code, ask the AI to complete it before moving on
- For Claude Code: use `/add context.md security.md design.md` before starting
- For Cursor: add all three files to the context panel
- Commit after each prompt so you have a clean rollback point
- The Stitch-generated UI from design.md is the visual reference — if anything in the dashboard diverges from it, trust design.md over defaults
