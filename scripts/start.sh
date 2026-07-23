#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Change secrets before production."
fi

docker compose up --build

