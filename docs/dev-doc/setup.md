# Scopeform — manual setup guide

These are the steps you must do manually before running any code. Everything in this file requires clicking through a UI or running a one-time command. None of it can be automated by Claude Code.

Do these in order before running prompt 01.

---

## 1. GitHub — create the repository

1. Go to https://github.com/new
2. Repository name: `scopeform`
3. Set to **Private** until you are ready to launch
4. Do NOT initialise with README, .gitignore, or licence — the prompts will create these
5. Click "Create repository"
6. Copy the remote URL — you will need it in step: `git remote add origin <url>`

---

## 2. Clerk — create your application

Clerk handles user auth for the dashboard and CLI login flow.

1. Go to https://clerk.com and sign up for a free account
2. Click "Create application"
3. Application name: `Scopeform`
4. Enable sign-in methods: **GitHub** and **Email**
5. Click "Create application"
6. In the Clerk dashboard, go to **API Keys**
7. Copy these two values into your `.env`:
   ```
   CLERK_SECRET_KEY=sk_test_...
   CLERK_PUBLISHABLE_KEY=pk_test_...
   ```
8. In Clerk dashboard → **JWT Templates** → click "New template"
   - Name: `scopeform-api`
   - This is not strictly required for MVP but set it up now
9. In Clerk dashboard → **Allowed redirect URLs**, add:
   - `http://localhost:3000`
   - `http://localhost:9876` (this is the CLI callback server)
   - Your production Vercel URL (add this after Vercel setup)

Free tier: 10,000 monthly active users. No credit card required.

---

## 3. Railway — create your project

Railway hosts the FastAPI backend, PostgreSQL database, and Redis.

1. Go to https://railway.app and sign up (GitHub login recommended)
2. Click "New Project"
3. Select "Empty project"
4. Project name: `scopeform`

### Add PostgreSQL
1. Inside the project, click "+ New" → "Database" → "PostgreSQL"
2. After it provisions, click on the PostgreSQL service
3. Go to the "Connect" tab
4. Copy the `DATABASE_URL` value — it will look like `postgresql://postgres:...@...railway.app:5432/railway`
5. Change `postgresql://` to `postgresql+asyncpg://` in your `.env`

### Add Redis
1. Click "+ New" → "Database" → "Redis"
2. After it provisions, click on the Redis service
3. Go to "Connect" tab
4. Copy the `REDIS_URL` value into your `.env`

### Add the API service (do this after prompt 05)
1. Click "+ New" → "GitHub Repo"
2. Connect your GitHub account and select the `scopeform` repo
3. Set the root directory to `/api`
4. Railway will auto-detect the Dockerfile
5. Go to the service "Variables" tab and add all env vars from your `.env`

### Get your Railway deploy token (for GitHub Actions)
1. Go to https://railway.app/account/tokens
2. Click "New Token"
3. Name: `github-actions`
4. Copy the token — you will add it to GitHub secrets as `RAILWAY_TOKEN`

Free tier: $5 credit/month. More than enough for MVP development.

---

## 4. Vercel — connect your repository

Vercel hosts the Next.js dashboard.

1. Go to https://vercel.com and sign up (GitHub login recommended)
2. Click "Add New Project"
3. Import your `scopeform` GitHub repository
4. Set the root directory to `/web`
5. Framework preset: Next.js (auto-detected)
6. Add environment variables:
   ```
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
   CLERK_SECRET_KEY=sk_test_...
   NEXT_PUBLIC_API_URL=https://your-railway-api-url.railway.app
   ```
7. Click "Deploy"
8. Copy your Vercel production URL (e.g. `https://scopeform.vercel.app`)
9. Go back to Clerk dashboard → "Allowed redirect URLs" and add this URL

Free tier: unlimited deployments, 100GB bandwidth/month. No credit card required.

---

## 5. PyPI — create your account

You need this to publish `pip install scopeform`.

1. Go to https://pypi.org/account/register/ and create an account
2. Verify your email
3. Go to https://pypi.org/manage/account/token/ and create an API token
   - Token name: `github-actions-scopeform`
   - Scope: "Entire account" (you can restrict to the project after first publish)
4. Copy the token — you will add it to GitHub secrets as `PYPI_API_TOKEN`
5. Also create a TestPyPI account at https://test.pypi.org for testing before real publish

Free. No cost to publish open source packages.

---

## 6. npm — create your account

You need this to publish `npm install -g scopeform`.

1. Go to https://www.npmjs.com/signup and create an account
2. Verify your email
3. Run `npm login` locally and authenticate
4. Go to https://www.npmjs.com/settings/YOUR_USERNAME/tokens
5. Click "Generate New Token" → "Classic Token" → "Automation"
6. Copy the token — you will add it to GitHub secrets as `NPM_TOKEN`

Free for public packages.

---

## 7. GitHub — add repository secrets

After completing steps 3–6, add these secrets to your GitHub repository.

1. Go to your `scopeform` repo on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret" for each:

| Secret name | Value | Where to get it |
|---|---|---|
| `RAILWAY_TOKEN` | Railway deploy token | Railway → Account → Tokens |
| `PYPI_API_TOKEN` | PyPI automation token | PyPI → Account → API tokens |
| `NPM_TOKEN` | npm automation token | npmjs.com → Access tokens |
| `CLERK_SECRET_KEY` | Clerk secret key | Clerk → API Keys |
| `JWT_SECRET` | 64-char random hex | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |

---

## 8. Local environment setup

Run these commands once on your local machine before starting development.

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/scopeform.git
cd scopeform

# Copy env example
cp .env.example .env
# Edit .env and fill in all values from steps 2-3 above

# Install Python tooling
pip install ruff pytest

# Install Node tooling
npm install -g turbo

# Start local services
make dev
# This starts PostgreSQL and Redis via docker-compose

# Run initial migration
make migrate
# This runs alembic upgrade head inside the api container

# Verify everything is working
curl http://localhost:8000/api/v1/health
# Should return: {"status": "ok", "db": true, "redis": true}
```

---

## 9. Generate your JWT secret

Run this once to generate a secure JWT secret for local development:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output into `.env` as `JWT_SECRET=<value>`.

Use a different secret for production (set it in Railway environment variables).

---

## 10. Verify checklist before running prompt 01

- [ ] GitHub repo created and cloned locally
- [ ] Clerk app created, both keys copied to `.env`
- [ ] Railway project created with PostgreSQL and Redis provisioned, URLs copied to `.env`
- [ ] Vercel project connected (can do after prompt 23)
- [ ] PyPI account created, token added to GitHub secrets
- [ ] npm account created, token added to GitHub secrets
- [ ] All Railway and Clerk tokens added to GitHub secrets
- [ ] JWT_SECRET generated and in `.env`
- [ ] Docker Desktop running locally
- [ ] `make dev` starts without errors

Once all boxes are checked, open `prompts.md` and start with prompt 01.
