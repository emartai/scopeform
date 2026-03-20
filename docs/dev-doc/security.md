# Scopeform — security rules

This file defines the security requirements that must be followed across every part of the codebase. Claude Code must apply these rules in every file it generates or edits.

---

## Authentication

### CLI auth
- After `scopeform login`, store the auth token at `~/.scopeform/config.json` with mode `0600` (owner read/write only)
- Never log or print the auth token to the terminal
- Token file format:
  ```json
  {
    "token": "<jwt>",
    "email": "user@example.com",
    "expires_at": "2024-01-01T00:00:00Z"
  }
  ```
- If token is expired or missing, redirect user to `scopeform login` with a clear message

### API auth
- Every protected endpoint requires a valid Bearer token in the `Authorization` header
- Token is a JWT signed with `JWT_SECRET` using `HS256`
- Verify: signature, expiry (`exp`), not-before (`nbf`), and that the `jti` is not in the Redis revocation set
- On validation failure return `401 Unauthorized` with RFC 7807 body — never expose the reason (expired vs invalid vs revoked)
- Clerk verifies the user identity. The API exchanges a Clerk session token for a Scopeform JWT on `POST /auth/token`

---

## Token issuance and revocation

### Issuing tokens
- Every token must include:
  - `jti` — a random UUID v4 (used for revocation)
  - `sub` — the agent ID
  - `org` — the org ID
  - `scopes` — the list of permitted service/action pairs
  - `exp` — expiry timestamp derived from the `ttl` field in `scopeform.yml`
  - `iat` — issued at timestamp
- Tokens are short-lived. Maximum TTL is 30 days. Default is 24 hours.
- Never issue a token without a registered agent record in the database
- Never issue a token for a suspended or decommissioned agent — return `403 Forbidden`

### Revoking tokens
- Revocation must be immediate — no waiting for natural expiry
- On revoke: write the `jti` to Redis with a TTL equal to the remaining token lifetime, AND set `revoked_at` in the `tokens` table
- Token validation checks Redis first (O(1) lookup), then falls back to DB
- Revoking an agent (`PATCH /agents/{id}/status`) must revoke all active tokens for that agent

### Token storage
- Tokens are written to the project `.env` file as `SCOPEFORM_TOKEN=<value>`
- In GitHub Actions they are injected as masked environment variables — never echoed in logs
- Never store tokens in `scopeform.yml` — that file is committed to version control

---

## Input validation

- All request bodies validated with Pydantic v2 — no raw dict access
- Reject any `scopeform.yml` with unknown fields (use `model_config = ConfigDict(extra='forbid')`)
- Agent names: alphanumeric, hyphens, underscores only. Max 64 chars. Regex: `^[a-zA-Z0-9_-]{1,64}$`
- Owner email: validated as email format
- Environment field: enum — `production`, `staging`, `development` only
- Service field: enum — `openai`, `anthropic`, `github` only (MVP)
- TTL field: must match pattern `^\d+[smhd]$` (seconds/minutes/hours/days). Reject anything else.
- All UUIDs validated as valid UUID v4 before DB queries

---

## Org isolation (multi-tenancy)

- Every database query that returns agent, token, or log data MUST filter by `org_id`
- `org_id` is derived from the authenticated JWT — never from request body or query params
- A user in org A must never be able to read, modify, or revoke agents belonging to org B
- Dependency injection pattern — `get_current_org_id()` is a FastAPI dependency injected into every protected route:

```python
async def get_current_org_id(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    payload = verify_token(token)  # raises 401 if invalid
    return uuid.UUID(payload["org"])
```

- Never trust `org_id` from the request. Only trust it from the verified JWT payload.

---

## Secrets handling

- `JWT_SECRET` must be at least 32 bytes of random data. Generate with `secrets.token_hex(32)`.
- Never hardcode secrets in source code
- Never commit `.env` to version control — `.env` is in `.gitignore`
- `.env.example` contains only placeholder values, never real secrets
- Clerk keys (`CLERK_SECRET_KEY`) are server-side only — never exposed to the browser or CLI
- `NEXT_PUBLIC_*` variables are safe for the browser — only `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `NEXT_PUBLIC_API_URL` are public

---

## Scope enforcement

- When an agent presents a token at runtime and calls `POST /tokens/validate`, the API checks:
  1. Is the token signature valid?
  2. Is the token expired?
  3. Is the jti in the Redis revocation set?
  4. Does the requested `service` + `action` pair exist in the token's `scopes` claim?
- If any check fails, return `403 Forbidden` — do not reveal which check failed
- Log every validation call to `call_logs` — both allowed and blocked calls

---

## API security headers

Add these headers to every API response:

```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
```

---

## CORS

- In development: allow `http://localhost:3000`
- In production: allow only the Vercel dashboard domain
- Never use `allow_origins=["*"]` in production
- Allowed methods: `GET, POST, PATCH, DELETE, OPTIONS`
- Allowed headers: `Authorization, Content-Type`

---

## Rate limiting

- Apply rate limiting to all auth and token endpoints
- Use Redis-backed rate limiting (slowapi or custom middleware)
- Limits:
  - `POST /auth/token`: 10 requests per minute per IP
  - `POST /tokens/issue`: 30 requests per minute per org
  - `POST /tokens/validate`: 300 requests per minute per org (agents call this frequently)
  - All other endpoints: 60 requests per minute per org

---

## Logging and audit

- Never log JWT values, raw token strings, or secret keys
- Log the `jti` (token ID) instead of the token itself for tracing
- Every agent action (register, deploy, revoke, validate) writes to `call_logs`
- Logs are immutable — no update or delete endpoints for call_logs
- Log fields: agent_id, token_id (jti), service, action, allowed, called_at, source_ip

---

## Dependency security

- Pin all Python dependencies with exact versions in `requirements.txt`
- Run `pip audit` in CI to catch known vulnerabilities
- Run `npm audit` in CI for the Node CLI
- Do not use packages with known CVEs — fail the CI build if audit finds high/critical issues

---

## Error handling

- Never expose internal error messages, stack traces, or database errors to API responses
- In production, all 5xx errors return a generic message: `{"title": "Internal server error", "status": 500}`
- Log full error details server-side only
- Validation errors (422) may return field-level detail — Pydantic handles this safely

---

## Testing security requirements

Every PR must include tests for:
- Attempting to access another org's agents (should return 404, not 403, to avoid leaking existence)
- Attempting to use a revoked token (should return 401)
- Attempting to issue a token for a suspended agent (should return 403)
- Attempting to call a service/action not in the token's scopes (should return 403)
- Submitting `scopeform.yml` with invalid agent name characters (should return 422)
