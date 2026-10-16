#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(unset CDPATH; cd -- "$(dirname -- "$0")" && pwd)
cd "$repo_dir"
source "$repo_dir/scripts/port-env.sh"
demo_ports_load "$repo_dir" --allow-bound

docker compose down --remove-orphans
echo "Local demo containers stopped. Broker data volumes were retained."
