set shell := ["bash", "-euo", "pipefail", "-c"]

default: check

validate:
  expanso-edge validate pipelines/scada-hivemq.yaml --output json

static-check: validate
  docker compose config --quiet
  xmllint --noout hivemq/config.xml hivemq/extension-config.xml
  shellcheck run-demo.sh stop-demo.sh scripts/*.sh
  uv run scripts/check_fixtures.py
  uv run --with grpcio-tools==1.71.0 \
    --with protobuf==5.29.3 scripts/validate_sparkplug.py
  node --check dashboard/app.js
  /Users/daaronch/code/second-brain/projects/anti-slop/check \
    dashboard/app.js
  git diff --check

ui-check:
  ./scripts/check-ui.sh

acceptance:
  ./run-demo.sh

check: static-check ui-check acceptance

live: acceptance
  docker compose --profile live up -d scada-sim

down:
  ./stop-demo.sh

cloud-deploy: static-check
  ./scripts/deploy-cloud.sh
