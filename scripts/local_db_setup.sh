#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.local.yml"
LOCAL_SQL="$ROOT_DIR/db/local/001_local_init.sql"
CONTAINER_NAME="rc-open-jio-postgres"

echo "[1/3] Starting local Postgres container..."
docker compose -f "$COMPOSE_FILE" up -d postgres

echo "[2/3] Waiting for Postgres to be healthy..."
for i in {1..40}; do
  if docker exec "$CONTAINER_NAME" pg_isready -U postgres -d rc_open_jio >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker exec "$CONTAINER_NAME" pg_isready -U postgres -d rc_open_jio >/dev/null 2>&1; then
  echo "Postgres did not become healthy in time."
  exit 1
fi

echo "[3/3] Applying local schema..."
docker exec -i "$CONTAINER_NAME" psql -U postgres -d rc_open_jio < "$LOCAL_SQL"

echo "Local DB is ready."
