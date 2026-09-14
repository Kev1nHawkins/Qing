#!/usr/bin/env sh
set -eu

echo "Applying database migrations..."
alembic upgrade head

echo "Seeding demo data..."
python -m app.scripts.seed

echo "Starting API in demo mode..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
