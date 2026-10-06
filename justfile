set shell := ["bash", "-euo", "pipefail", "-c"]

default: check

validate:
  expanso-edge validate pipelines/scada-hivemq.yaml --output json

static-check: validate
  docker compose config --quiet
  uv run -s scripts/validate_xml.py \
    hivemq/config.xml hivemq/extension-config.xml
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

# Start both brokers, Expanso Edge and the dashboard, then replay the fixtures.
up:
  ./run-demo.sh

# Stop every local container (live and verify included); fail unless ports free.
down:
  COMPOSE_PROFILES=live,verify ./stop-demo.sh
  @for port in 8883 8888; do \
    if lsof -nP -iTCP:$port -sTCP:LISTEN >/dev/null 2>&1; then \
      echo "FAIL: port $port still in use"; exit 1; \
    fi; \
  done; echo "down: ports 8883 and 8888 are free"

# everything that must be true before a take: gates + live dashboard + checklist
record-check: check
  curl -fsS "http://127.0.0.1:8888/" > /dev/null || { echo "FAIL: dashboard not reachable — just up first"; exit 1; }
  @echo ""
  @echo "RECORD CHECKLIST"
  @echo "  [ ] demo-guidance/RECORDING.md read; DEMO_SCRIPT.md beats rehearsed"
  @echo "  [ ] Opera, no browser chrome in frame"
  @echo "  [ ] just up printed Local acceptance passed"
  @echo "  [ ] RECORDING_PREFLIGHT.md warnings reviewed"

# human story/proof declaration; validates only and never starts anything
recording-preflight:
  @uv run -s ../_demo-kit/recording-preflight.py .

cloud-deploy: static-check
  ./scripts/deploy-cloud.sh
