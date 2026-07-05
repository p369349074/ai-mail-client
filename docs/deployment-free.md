# Zero-cost deployment: Vercel frontend + Render Free backend + existing PostgreSQL/Redis

This project is split so the frontend can run on Vercel Hobby and the backend can run on Render Free, while using your existing PostgreSQL and Redis services.

## Architecture

```text
Vercel Hobby Free
└── frontend/ React + Vite static site

Render Free Web Service
└── backend/ FastAPI Docker web service

Existing infrastructure
├── PostgreSQL via DATABASE_URL
└── Redis via REDIS_URL, reserved for locks/cache in later phases
```

## Important limitations

Render Free web services can spin down when inactive and cold-start on the next request. Do not rely on a permanent background worker in the free version. Use manual/foreground sync endpoints first, then add GitHub Actions cron to call small sync batches later.

Render's pricing page says free compute plans can run web services at no charge, but account registration and payment-method requirements can change. Confirm in your Render account before relying on it.

## Backend environment variables

Set these in Render:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
REDIS_URL=redis://HOST:6379/0
SECRET_KEY=<long-random-secret>
CORS_ORIGINS=https://<your-vercel-app>.vercel.app
DEFAULT_USER_EMAIL=local@example.invalid
DEFAULT_USER_DISPLAY_NAME=Local User
MAIL_CONNECT_TIMEOUT_SECONDS=10
```

Notes:

- `DATABASE_URL` must point to your existing PostgreSQL. Do not use SQLite in production.
- `SECRET_KEY` controls the current placeholder reversible encryption. Changing it makes saved mailbox secrets undecryptable. Replace the placeholder encryption before serious production use.
- If you later attach a custom frontend domain, update `CORS_ORIGINS` to that domain.

## Backend deployment on Render Free

The repo includes `render.yaml` for Render Blueprint deployment.

Typical setup in Render UI:

1. Push this repository to GitHub.
2. Open Render dashboard.
3. Create a new Blueprint or Web Service from the GitHub repo.
4. If using Blueprint, select `render.yaml`.
5. Confirm the service uses:
   - Runtime: Docker
   - Root directory: `backend`
   - Dockerfile path: `./Dockerfile`
   - Plan: Free
   - Health check path: `/health`
6. Set `DATABASE_URL`, `REDIS_URL`, and `CORS_ORIGINS`.
7. Deploy.

The container runs `backend/start.sh`, which applies Alembic migrations then starts Uvicorn on `${PORT:-8000}`.

After deployment, verify:

```bash
curl https://<your-render-service>.onrender.com/health
curl https://<your-render-service>.onrender.com/accounts
```

## Frontend deployment on Vercel Hobby

Project settings:

```text
Root Directory: frontend
Install Command: npm install
Build Command: npm run build
Output Directory: dist
```

Environment variable:

```text
VITE_API_BASE_URL=https://<your-render-service>.onrender.com
```

Then redeploy the frontend.

## Local verification before deploy

```bash
cd backend
UV_CACHE_DIR=.uv-cache uv run pytest -q
UV_CACHE_DIR=.uv-cache uv run alembic upgrade head

cd ../frontend
npm run build
```

## Current sync model

To stay within free-tier limits:

- Account connection tests are request/response.
- Folder sync is manual via `POST /accounts/{account_id}/folders/sync`.
- Message sync should be added later as small bounded batches, e.g. `limit=50`, not long-running background jobs.
