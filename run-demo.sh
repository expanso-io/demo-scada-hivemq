#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Validate required vars
: "${EXPANSO_CLI_ENDPOINT:?Set EXPANSO_CLI_ENDPOINT in .env or environment (e.g. https://<cluster-id>.us1.cloud.expanso.io)}"
: "${EXPANSO_CLUSTER_ID:?Set EXPANSO_CLUSTER_ID in .env or environment}"

# Check expanso-cli
if ! command -v expanso-cli &>/dev/null; then
  echo "ERROR: expanso-cli not found. Install from https://docs.expanso.io/cli"
  exit 1
fi

echo "▶ Starting local services..."
docker compose up -d --build

echo "▶ Waiting for dashboard (http://localhost:8888)..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8888 >/dev/null 2>&1; then
    echo "  Dashboard is up."
    break
  fi
  sleep 1
done

echo "▶ Deploying pipelines to cluster: $EXPANSO_CLUSTER_ID"
for f in pipelines/*.yaml; do
  # Substitute cluster ID placeholder
  tmp=$(mktemp /tmp/expanso-pipeline-XXXXXX.yaml)
  sed "s/\${EXPANSO_CLUSTER_ID}/$EXPANSO_CLUSTER_ID/g" "$f" > "$tmp"
  EXPANSO_CLI_ENDPOINT="$EXPANSO_CLI_ENDPOINT" expanso-cli job deploy "$tmp"
  rm "$tmp"
  echo "  Deployed: $f"
done

echo ""
echo "✅ Demo running at http://localhost:8888"
echo "   Pipelines deployed to $EXPANSO_CLUSTER_ID"
echo "   Run ./stop-demo.sh to tear down."
