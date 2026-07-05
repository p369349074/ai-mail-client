# AI Mail Client

AI Mail Client is a lightweight, self-hostable email management system designed for individuals who want a modern webmail experience, private data ownership, and practical AI-assisted workflows without running a heavy infrastructure stack.

The project is optimized for small servers and free-tier deployment paths. It separates the frontend, backend, database, and cache so users can deploy each piece where it is cheapest or already available.

## Why this project exists

Email remains one of the most important personal knowledge stores, but most email clients still suffer from the same problems:

- **Fragmented inboxes**: personal, work, domain, Gmail, Outlook, and custom IMAP mailboxes often live in separate apps.
- **Poor ownership of data**: hosted mail clients make it hard to keep a personal, queryable, portable archive.
- **Weak automation**: rules are usually rigid, provider-specific, and hard to combine with modern AI workflows.
- **Expensive infrastructure assumptions**: many self-hosted mail tools assume a larger VPS, Elasticsearch/OpenSearch, object storage, or always-on workers.
- **Attachment bloat**: full attachment archiving quickly overwhelms small personal servers.
- **Limited mobile-readiness**: many DIY tools are not API-first, making mobile clients difficult later.

AI Mail Client addresses these constraints with a deliberately lightweight architecture.

## Product advantages

- **Personal-data first**: mailbox metadata, folders, message state, and future AI outputs are stored in your own PostgreSQL database.
- **Lightweight by design**: no Elasticsearch, no OpenSearch, no MinIO, no local LLM, and no mandatory Celery/Redis worker in the initial version.
- **API-first backend**: FastAPI endpoints are designed to support both the web UI and future mobile clients.
- **Provider-compatible foundation**: starts with IMAP/SMTP and leaves room for Gmail/Outlook OAuth integrations.
- **Resource-aware sync model**: starts with manual and bounded sync flows instead of long-running background workers.
- **Attachment-safe strategy**: attachments are planned as metadata-first and on-demand downloads rather than full local archiving.
- **AI-ready but not AI-dependent**: AI summaries, reply drafts, and todo extraction can be added as on-demand features without blocking core email management.
- **Free-tier friendly deployment**: Vercel can host the frontend, Render Free can host the backend, and existing PostgreSQL/Redis services can be reused.

## Current status

The project is in early MVP development. Implemented so far:

- FastAPI backend skeleton
- SQLAlchemy data models
- Alembic migrations
- Health endpoint
- Mail account CRUD APIs
- IMAP/SMTP connection testing
- Placeholder reversible secret encryption for MVP use
- IMAP folder sync via `LIST`
- Folder upsert into PostgreSQL-compatible schema
- React/Vite/Tailwind frontend skeleton
- Account settings UI for account creation, connection testing, folder sync, and folder display
- Docker backend deployment path
- Vercel frontend config
- Render Blueprint config
- Backend tests with network calls monkeypatched

## Architecture

```text
Vercel / Static Hosting
└── React + Vite frontend

FastAPI Backend
├── Account settings API
├── IMAP/SMTP connectivity checks
├── IMAP folder sync
├── Future bounded message sync
└── Future AI endpoints

PostgreSQL
├── Users
├── Mail accounts
├── Folders
├── Messages
├── Recipients
├── Bodies
├── Attachments metadata
└── AI outputs

Redis
└── Reserved for future locks, rate limits, and lightweight sync coordination
```

## Target deployment profile

The first production target is intentionally small:

```text
Frontend: Vercel Hobby / static hosting
Backend: Render Free or any Docker-capable web service
Database: existing PostgreSQL
Cache: existing Redis
Workers: none in the first free-tier deployment
```

For a zero-additional-cost deployment guide, see:

```text
docs/deployment-free.md
```

## Resource constraints

The design avoids heavy services so it can run with limited resources:

- No Elasticsearch / OpenSearch / Meilisearch in the initial version
- No MinIO or object storage requirement in the initial version
- No local LLM requirement
- No full historical mailbox sync by default
- No default long-term attachment archiving
- No always-on background worker requirement for the free-tier deployment

## Tech stack

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL via `psycopg`
- Pydantic v2
- pytest
- Python stdlib `imaplib` / `smtplib` for current mail connectivity checks

### Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- TanStack Query

### Deployment

- Docker backend image
- Render Blueprint (`render.yaml`)
- Vercel config (`frontend/vercel.json`)

## Implemented API surface

### System

```text
GET /health
```

### Accounts

```text
GET    /accounts
POST   /accounts
GET    /accounts/{account_id}
PATCH  /accounts/{account_id}
DELETE /accounts/{account_id}
POST   /accounts/test
POST   /accounts/{account_id}/test
```

### Folders

```text
GET  /accounts/{account_id}/folders
POST /accounts/{account_id}/folders/sync
```

## Planned API surface

```text
GET  /accounts/{account_id}/folders/{folder_id}/messages
POST /accounts/{account_id}/folders/{folder_id}/messages/sync?limit=50
GET  /messages/{message_id}
POST /messages/{message_id}/load-body
POST /messages/{message_id}/mark-read
POST /messages/{message_id}/mark-unread
POST /messages/{message_id}/star
POST /messages/{message_id}/unstar
POST /messages/{message_id}/move
DELETE /messages/{message_id}
POST /compose/send
POST /compose/reply
POST /compose/forward
GET  /attachments/{attachment_id}/download
POST /ai/messages/{message_id}/summarize
POST /ai/messages/{message_id}/draft-reply
POST /ai/messages/{message_id}/extract-todos
GET  /system/storage
POST /system/cleanup
```

## Local development

### Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run pytest
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
```

The frontend reads the API base URL from:

```text
window.API_BASE_URL
VITE_API_BASE_URL
API_BASE_URL
http://localhost:8000 fallback
```

## Environment variables

Backend:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
REDIS_URL=redis://HOST:6379/0
SECRET_KEY=<long-random-secret>
CORS_ORIGINS=https://your-frontend-domain
DEFAULT_USER_EMAIL=local@example.invalid
DEFAULT_USER_DISPLAY_NAME=Local User
MAIL_CONNECT_TIMEOUT_SECONDS=10
```

Frontend:

```text
VITE_API_BASE_URL=https://your-backend-domain
```

## Security notes

This project is still an MVP. Before serious production use:

- Replace the placeholder reversible secret encryption with authenticated encryption such as Fernet, age, KMS, or a platform secret manager.
- Do not log mailbox credentials, OAuth tokens, or full email bodies.
- Restrict `CORS_ORIGINS` to the actual frontend domain.
- Use HTTPS for both frontend and backend.
- Add authentication before exposing the app beyond personal testing.
- Keep sync operations bounded to avoid free-tier timeouts.

## Roadmap

### Phase 1 — Foundation

- FastAPI app
- SQLAlchemy models
- Alembic migrations
- Health endpoint
- React/Vite shell
- Docker and deployment skeleton

### Phase 2 — Accounts and folders

- Mail account CRUD
- IMAP/SMTP connection tests
- IMAP folder sync
- Account settings UI

### Phase 3 — Message envelope sync

- Folder-level bounded message sync
- UID/flags/header persistence
- Message list API
- Frontend message list backed by real data

### Phase 4 — Message details and actions

- On-demand body fetch
- Sanitized HTML rendering
- Mark read/unread
- Star/unstar
- Move/delete

### Phase 5 — AI-assisted workflows

- On-demand summaries
- Reply drafts
- Todo extraction
- Lightweight semantic search options

## License

No license has been selected yet.
