# Quickstart

## Prerequisites

- Python `3.8+` or Node `18+`
- A Scopeform account
- Access to your organisation in the Scopeform dashboard

## Step 1: Install Scopeform

Python:

```bash
pip install scopeform
```

Node:

```bash
npm install -g scopeform
```

## Step 2: Log in

```bash
scopeform login
```

This opens the browser sign-in flow and stores your CLI session in `~/.scopeform/config.json`.

## Step 3: Initialise your agent project

```bash
cd your-agent
scopeform init
```

This creates `scopeform.yml` with your agent identity, scopes, token TTL, and CI integration settings.

## Step 4: Deploy and issue a scoped token

```bash
scopeform deploy
```

Scopeform will:

- register the agent if it does not exist yet
- issue a short-lived scoped token
- write `SCOPEFORM_TOKEN` to `.env`

## Step 5: Use `SCOPEFORM_TOKEN` in your agent code

Python example:

```python
import os

scopeform_token = os.environ["SCOPEFORM_TOKEN"]

print(f"Loaded Scopeform token: {scopeform_token[:8]}...")
```

Node example:

```js
const scopeformToken = process.env.SCOPEFORM_TOKEN;

console.log(`Loaded Scopeform token: ${scopeformToken.slice(0, 8)}...`);
```

## Step 6: View your agent in Scopeform

Open `https://app.scopeform.dev` to:

- inspect the registered agent
- review recent logs
- revoke access when needed

## Next steps

- Read the [CLI Reference](/C:/Users/DELL/Projects/scopeform/docs/cli-reference.md)
- Read the [scopeform.yml Reference](/C:/Users/DELL/Projects/scopeform/docs/scopeform-yml.md)
- Read the [GitHub Actions Integration](/C:/Users/DELL/Projects/scopeform/docs/github-actions-integration.md)
