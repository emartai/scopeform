# `scopeform.yml` Reference

## Full schema

```yaml
identity:
  name: string
  owner: string
  environment: production | staging | development

scopes:
  - service: openai | anthropic | github
    actions:
      - string

ttl: <number><s|m|h|d>

integrations:
  ci: github-actions | none
```

## Fields

### `identity.name`

- Type: `string`
- Required: yes
- Pattern: `^[a-zA-Z0-9_-]{1,64}$`
- Meaning: unique agent name within your organisation

Example:

```yaml
identity:
  name: support-agent
```

### `identity.owner`

- Type: `string`
- Required: yes
- Meaning: responsible developer email

Example:

```yaml
identity:
  owner: dev@example.com
```

### `identity.environment`

- Type: `string`
- Allowed values: `production`, `staging`, `development`

### `scopes`

- Type: `array`
- Required: yes
- Meaning: list of allowed services and actions

Example:

```yaml
scopes:
  - service: openai
    actions:
      - chat.completions
      - responses.create
```

### `ttl`

- Type: `string`
- Required: yes
- Pattern: `^\d+[smhd]$`
- Meaning: token lifetime

Examples:

- `30m`
- `24h`
- `7d`

### `integrations.ci`

- Type: `string`
- Allowed values: `github-actions`, `none`

## Common examples

### OpenAI-only agent

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
  ci: none
```

### Multi-service agent

```yaml
identity:
  name: orchestrator
  owner: ops@example.com
  environment: staging

scopes:
  - service: openai
    actions:
      - chat.completions
  - service: anthropic
    actions:
      - messages.create
  - service: github
    actions:
      - issues.create

ttl: 12h

integrations:
  ci: none
```

### GitHub Actions setup

```yaml
identity:
  name: ci-agent
  owner: platform@example.com
  environment: production

scopes:
  - service: github
    actions:
      - checks.write
      - issues.create

ttl: 1h

integrations:
  ci: github-actions
```
