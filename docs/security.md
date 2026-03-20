# Security

## How tokens work

Scopeform issues short-lived, scoped JWTs for agents.

Each token is:

- tied to a specific registered agent
- scoped to specific services and actions
- revocable before expiry
- validated centrally before use

Tokens are not long-lived third-party provider secrets.

## What Scopeform can see

Scopeform can see:

- agent identity metadata
- token issuance and revocation events
- requested service and action names
- whether a request was allowed or blocked

Scopeform does not need your raw third-party API keys to issue agent tokens.

## What Scopeform cannot see

Scopeform does not promise to inspect the full business content of your model prompts, responses, or repository data as part of the core token and logging model described in this MVP.

## Operational protections

- short-lived runtime tokens
- org-scoped access boundaries
- immediate revocation support
- call logging for audit visibility
- Redis-backed revocation checks for fast deny decisions

## Report a security issue

If you discover a security issue, contact:

`security@scopeform.dev`

Please include:

- a clear description of the issue
- reproduction steps
- affected components
- any mitigation you already identified
