#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(unset CDPATH; cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_dir"

command -v expanso-cli >/dev/null 2>&1 || {
  echo "expanso-cli v2.1.21 is required" >&2
  exit 1
}

expanso-cli job validate pipelines/scada-hivemq.yaml
expanso-cli job deploy pipelines/scada-hivemq.yaml

echo "Deployment accepted by Expanso Cloud."
echo "Confirm assignment and execution before claiming the job is running:"
echo "  expanso-cli execution list --job scada-hivemq"
