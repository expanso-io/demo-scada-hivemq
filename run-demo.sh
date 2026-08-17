#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
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

# Optionally deploy pipelines to Expanso Cloud cluster
if [ -n "${EXPANSO_CLI_ENDPOINT:-}" ] \
  && [ -n "${EXPANSO_CLUSTER_ID:-}" ] \
  && command -v expanso-cli &>/dev/null; then
  echo "▶ Deploying pipelines to cluster: $EXPANSO_CLUSTER_ID"
  for f in pipelines/0*.yaml; do
    tmp=$(mktemp /tmp/expanso-pipeline.XXXXXX.yaml)
    sed "s/\${EXPANSO_CLUSTER_ID}/$EXPANSO_CLUSTER_ID/g" \
      "$f" > "$tmp"
    deploy_output=$(\
      EXPANSO_CLI_ENDPOINT="$EXPANSO_CLI_ENDPOINT" \
      expanso-cli job deploy "$tmp" 2>&1) \
      && deploy_status=0 || deploy_status=$?
    if [ "$deploy_status" -eq 0 ]; then
      echo "  Deployed: $f"
    elif printf '%s' "$deploy_output" \
      | grep -q "NO_CHANGES_DETECTED"; then
      echo "  Unchanged: $f"
    else
      printf '%s\n' "$deploy_output"
      echo "  WARN: Failed to deploy $f"
    fi
    rm "$tmp"
  done
else
  echo "▶ Skipping cloud pipeline deployment."
  echo "  Set EXPANSO_CLI_ENDPOINT, EXPANSO_CLUSTER_ID,"
  echo "  and install expanso-cli to deploy pipelines."
fi

echo ""
echo "✅ Demo running at http://localhost:8888"
if [ -n "${EXPANSO_CLUSTER_ID:-}" ]; then
  echo "   Cluster target: $EXPANSO_CLUSTER_ID"
fi
echo "   Run ./stop-demo.sh to tear down."
