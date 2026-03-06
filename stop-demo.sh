#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

echo "▶ Stopping local services..."
docker compose down

if [ -n "${EXPANSO_CLI_ENDPOINT:-}" ]; then
  echo "▶ Removing cloud pipelines from $EXPANSO_CLI_ENDPOINT..."
  jobs=$(EXPANSO_CLI_ENDPOINT="$EXPANSO_CLI_ENDPOINT" expanso-cli job list 2>/dev/null | grep '^scada-' | awk '{print $1}' || true)
  if [ -n "$jobs" ]; then
    for job in $jobs; do
      EXPANSO_CLI_ENDPOINT="$EXPANSO_CLI_ENDPOINT" expanso-cli job delete "$job" && echo "  Deleted: $job"
    done
  else
    echo "  No scada-* jobs found on cluster."
  fi
fi

echo "✅ Demo stopped."
