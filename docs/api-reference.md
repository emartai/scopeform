# API Reference

## OpenAPI docs

Live API documentation is available at:

`https://api.scopeform.dev/api/v1/docs`

## Core endpoints

### Auth

- `POST /api/v1/auth/token`

Exchange a Clerk session token for a Scopeform user token.

### Agents

- `POST /api/v1/agents`
- `GET /api/v1/agents`
- `GET /api/v1/agents/{id}`
- `PATCH /api/v1/agents/{id}/status`

These endpoints create, list, inspect, suspend, and decommission agents.

### Tokens

- `POST /api/v1/tokens/issue`
- `POST /api/v1/tokens/revoke`
- `POST /api/v1/tokens/validate`

These endpoints issue scoped runtime tokens, revoke them, and validate runtime access.

### Logs

- `GET /api/v1/agents/{id}/logs`
- `GET /api/v1/logs`

These endpoints expose per-agent and org-wide call history.

## Runtime token validation flow

At runtime, agents use `SCOPEFORM_TOKEN` rather than a raw third-party API key.

Flow:

1. A developer runs `scopeform deploy`.
2. Scopeform issues a short-lived JWT scoped to the agent’s allowed services and actions.
3. The agent presents that JWT when requesting runtime validation.
4. `POST /api/v1/tokens/validate` verifies:
   - signature
   - expiry / not-before timestamps
   - revocation state
   - scope permissions for the requested service and action
5. Scopeform records the decision in `call_logs`.
6. The caller receives a minimal response: `{"allowed": true}` or `{"allowed": false}`.

## Security model highlights

- all user-facing API routes are org-scoped
- revoked tokens are blocked through both database state and Redis-backed revocation checks
- validation responses never expose extra policy detail beyond allow or deny
