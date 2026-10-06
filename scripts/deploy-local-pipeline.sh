#!/bin/sh
set -eu

endpoint=http://expanso-edge:9010
attempt=0
until expanso-cli --endpoint "$endpoint" status >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    echo "Expanso Edge local API did not become ready" >&2
    exit 1
  fi
  sleep 1
done

expanso-cli --endpoint "$endpoint" job deploy \
  /pipelines/scada-hivemq.yaml
