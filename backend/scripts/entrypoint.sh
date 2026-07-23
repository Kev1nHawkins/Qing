#!/usr/bin/env sh
set -eu

echo "Applying database migrations..."
alembic upgrade head

echo "Seeding development data..."
python -m app.scripts.seed

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

