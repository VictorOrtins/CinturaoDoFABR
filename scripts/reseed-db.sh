#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# backend/app/seed.py::seed_if_empty only ever seeds an EMPTY database - it's a no-op
# on every startup after the first. backend/data is a named Docker volume
# (backend_data), not a bind mount, so it survives `docker compose down`/restarts on
# its own; editing backend/seed_data/*.csv (e.g. after a new scrape run regenerates
# them) has no effect on an already-seeded app.db until that volume's copy is cleared.
# This is the manual stand-in for Phase 2's sync_from_csv (see docs/DATA_PIPELINE.md) -
# once that exists, this script won't be needed; until then, run it whenever
# backend/seed_data/*.csv changes and you want the running app to reflect it.

echo "Clearing the backend database so it reseeds from backend/seed_data/*.csv..."
docker compose run --rm --no-deps --entrypoint sh backend -c "rm -f /app/data/app.db"

echo "Rebuilding and restarting the backend with the current seed data..."
docker compose up -d --build --force-recreate backend

echo "Done - backend reseeded from backend/seed_data/games.csv and teams.csv."
