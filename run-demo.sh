#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(unset CDPATH; cd -- "$(dirname -- "$0")" && pwd)
cd "$repo_dir"

command -v docker >/dev/null 2>&1 || {
  echo "docker is required" >&2
  exit 1
}

export DEMO_HOST_UID
DEMO_HOST_UID=$(id -u)
export DEMO_HOST_GID
DEMO_HOST_GID=$(id -g)

install -d -m 0700 .runtime/results .runtime/secrets
install -d -m 0755 .runtime/tls
for secret_file in \
  source-password \
  source-passwords \
  hivemq-password \
  hivemq-observer-password \
  hivemq-credentials.xml; do
  if [[ ! -e ".runtime/secrets/$secret_file" ]]; then
    : > ".runtime/secrets/$secret_file"
  fi
  chmod 0600 ".runtime/secrets/$secret_file"
done

echo "Resetting the local fixture lane..."
docker compose down --remove-orphans
docker compose up -d --build

echo "Waiting for the localhost dashboard..."
dashboard_ready=false
for _ in $(seq 1 60); do
  if curl --fail --silent --show-error \
    http://127.0.0.1:8888/ >/dev/null 2>&1; then
    dashboard_ready=true
    break
  fi
  sleep 1
done

if [[ "$dashboard_ready" != true ]]; then
  echo "dashboard did not become ready" >&2
  docker compose ps
  exit 1
fi

echo "Replaying three Sparkplug B records through Expanso Edge..."
docker compose --profile verify run --rm fixture-check

echo
echo "Local acceptance passed."
echo "Dashboard: http://127.0.0.1:8888"
echo "Stop the stack with ./stop-demo.sh"
