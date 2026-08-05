#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose up --build -d

echo "Cinturão do FABR is running:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
