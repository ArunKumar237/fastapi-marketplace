#!/usr/bin/env sh
set -eu

# Ensure schema migrations are applied before serving traffic.
alembic upgrade head

if [ "${UVICORN_RELOAD:-false}" = "true" ]; then
  exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
