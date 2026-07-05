#!/usr/bin/env sh
set -eu

# Run database migrations on startup. For a single free-tier web service this is
# the simplest zero-extra-cost deployment path. If a dedicated worker is added
# later, move migrations to a release step.
uv run alembic upgrade head

exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
