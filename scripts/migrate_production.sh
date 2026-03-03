#!/usr/bin/env bash
# migrate_production.sh — Run Alembic migrations against the production database.
#
# Usage:
#   DATABASE_URL=postgresql+asyncpg://... bash scripts/migrate_production.sh
#
# The DATABASE_URL environment variable must be set before running this script,
# either directly or via a .env.production file.
#
# On Cloud Run, this script is executed inside a Cloud Run Job that has access
# to Secret Manager; the DATABASE_URL secret is injected automatically.

set -euo pipefail

echo "=== NDIS CRM — Production Database Migration ==="
echo "Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL environment variable is not set." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}/backend"

echo "Running Alembic migrations..."
alembic upgrade head

echo "=== Migrations complete ==="
