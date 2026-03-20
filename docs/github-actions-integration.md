# GitHub Actions Integration

Scopeform can issue a scoped runtime token for your agent inside GitHub Actions so your workflow never needs to store a long-lived provider key directly.

## Prerequisites

- A registered Scopeform account and organisation
- A `scopeform.yml` file checked into your agent repository
- A Scopeform API key copied from the Scopeform dashboard

## Add the GitHub secret

1. Open the Scopeform dashboard.
2. Go to your agent or organisation settings.
3. Copy the `SCOPEFORM_API_KEY` value shown for GitHub Actions usage.
4. In your GitHub repository, open `Settings` -> `Secrets and variables` -> `Actions`.
5. Create a new repository secret named `SCOPEFORM_API_KEY`.

## Option 1: Use the composite action

```yaml
- uses: scopeform/scopeform@v1
  with:
    api-key: ${{ secrets.SCOPEFORM_API_KEY }}
```

This action:

- installs the Scopeform Python CLI
- writes a temporary `~/.scopeform/config.json` for the runner
- runs `scopeform deploy`
- exports `SCOPEFORM_TOKEN` to the workflow environment

## Option 2: Use the CLI directly

Copy the reference workflow in [.github/workflows/scopeform-example.yml](/C:/Users/DELL/Projects/scopeform/.github/workflows/scopeform-example.yml) into your own repository and adjust the final runtime step for your agent.

## Example project structure

Your repo should contain:

```text
.
├── scopeform.yml
├── agent.py
└── .github/
    └── workflows/
        └── deploy-agent.yml
```

## Example `scopeform.yml`

```yaml
identity:
  name: support-agent
  owner: dev@example.com
  environment: production

scopes:
  - service: openai
    actions:
      - chat.completions

ttl: 24h

integrations:
  ci: github-actions
```

## How the workflow works

1. GitHub Actions reads `SCOPEFORM_API_KEY` from repository secrets.
2. Scopeform deploys or refreshes the agent registration.
3. Scopeform writes a short-lived `SCOPEFORM_TOKEN` into the runner environment.
4. Your agent process uses `SCOPEFORM_TOKEN` at runtime.

## Security notes

- Store only `SCOPEFORM_API_KEY` as a GitHub secret.
- Do not commit `.env` files created during CI.
- `SCOPEFORM_TOKEN` is short-lived and scoped to the agent permissions in `scopeform.yml`.
- Revoke the key from the Scopeform dashboard if the repository or workflow is compromised.
