#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(unset CDPATH; cd -- "$(dirname -- "$0")" && pwd)
cd "$repo_dir"

docker compose down --remove-orphans
echo "Local demo containers stopped. Broker data volumes were retained."
