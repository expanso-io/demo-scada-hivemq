# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A self-contained Docker Compose demo showing Expanso Edge between industrial SCADA sensors (Sparkplug B over MQTT) and HiveMQ, with runtime toggles for dead-banding, schema validation, compression, and fan-out. Designed for narrated screen recordings (~8-10 min).

## Commands

```bash
# Run the demo (starts Docker services, optionally deploys pipelines to Expanso Cloud)
./run-demo.sh

# Stop all services
./stop-demo.sh

# Start services directly
docker compose up --build

# Rebuild just the dashboard (fastest iteration)
docker compose up -d --force-recreate dashboard
```

Endpoints when running:
- Dashboard: `http://localhost:8888`
- MQTT websocket (via nginx proxy): `ws://localhost:8888/mqtt`
- MQTT direct (HiveMQ): `tcp://localhost:1883`
- HiveMQ websocket (direct): `ws://localhost:8000/mqtt`

## Architecture

```
SCADA Simulator (Python, paho-mqtt)
  → HiveMQ CE (mqtt-broker, MQTT + websocket)
    → Dashboard (nginx, proxies websocket, static HTML)
```

**Services** in `docker-compose.yml`:
- `scada-sim` — Python MQTT publisher generating Temperature, Pressure, DoorSensor telemetry for 4 industrial sites (wind, solar, battery, distgen) every 1s
- `mqtt-broker` — HiveMQ Community Edition (MQTT TCP 1883, websocket 8000)
- `dashboard` — nginx on port 8888 serving static HTML + proxying websocket to HiveMQ

**Data flow**: scada-sim publishes JSON to `spBv1.0/SCADA/DDATA/<node>/<device>` topics. Dashboard subscribes via websocket and processes messages in the browser. Feature toggles (deadband, schema, compression, fan-out) demonstrate what Expanso Edge does when deployed in the data path.

**Cloud pipelines**: `pipelines/0*.yaml` are production pipeline configs for deployment to Expanso Cloud via `expanso-cli job deploy`. They contain the actual Expanso Edge processing logic.

## Key Files

- **`dashboard/index.html`** — Entire frontend (~480 lines). Single HTML file with inline CSS/JS. Connects to HiveMQ via MQTT.js websocket, renders animated architecture diagram with live metrics and feature toggles.
- **`dashboard/nginx.conf`** — nginx config with websocket proxy (`/mqtt` → `mqtt-broker:8000/mqtt`)
- **`scada-sim/sim.py`** — Python SCADA simulator using paho-mqtt. Publishes Sparkplug B-style JSON messages.
- **`scada-sim/Dockerfile`** — Python slim image with paho-mqtt
- **`hivemq/config.xml`** — HiveMQ CE config with TCP (1883) and websocket (8000) listeners
- **`pipelines/*.yaml`** — Expanso Edge pipeline configs for Cloud deployment (deadband, compression, schema validation, fan-out)
- **`run-demo.sh` / `stop-demo.sh`** — Lifecycle scripts
- **`DESIGN_BRIEF.md`** — Visual design requirements for the dashboard

## Dashboard Design Context

The dashboard is presentation-grade, not an admin panel. See `DESIGN_BRIEF.md` for full requirements. Key principles:
- Architecture diagram is the hero; metrics are supporting evidence
- Progressive reveal: toggles enable features one-by-one, architecture visually evolves
- Four feature toggles: deadband → schema validation → compression → fan-out
- Animation explains system behavior (data flow direction, filtering, branching)
- MQTT.js library loaded from CDN for browser websocket connection
- Real data from scada-sim; processing simulation in browser

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `EXPANSO_CLUSTER_ID` | Target cluster for pipeline deployment |
| `EXPANSO_CLI_ENDPOINT` | Expanso Cloud API endpoint |
| `MQTT_HOST` | MQTT broker for scada-sim (default: mqtt-broker) |
| `MQTT_PORT` | MQTT port (default: 1883) |
| `PUBLISH_INTERVAL` | Seconds between telemetry publishes (default: 1.0) |

## Pipeline Structure

All four pipelines follow the same pattern: MQTT input → Bloblang processors → MQTT output. They use Expanso Edge (not raw Benthos) and are deployed via Expanso Cloud, not run locally.

Pipeline naming convention: `scada-sparkplug-{feature}` (e.g., `scada-sparkplug-deadband`).

Note: The Expanso Edge container image (`ghcr.io/expanso-io/expanso-edge`) does not currently include the `mqtt` component in its build. For local demos, scada-sim publishes directly to HiveMQ and the dashboard simulates Expanso Edge processing in the browser.

## Unreconciled: two simulator variants live in this repo

A `chore: pre-migration state capture` commit landed on `master` from another
machine carrying a *second*, different build of this demo. Both are present in
the tree and neither has been deleted, but only one can be the demo you record.

| | Browser-simulation variant | Pre-migration variant |
|---|---|---|
| Simulator | `scada-sim/sim.py` (paho-mqtt, JSON) | `scada-sim/app.py` (real protobuf Sparkplug B via `sparkplug_b.proto`) |
| HiveMQ config | `hivemq/config.xml` | `hivemq/conf/config.xml` |
| Edge processing | simulated in the dashboard | real `expanso-edge/` service + `ignition-edge/` provisioning |

`scada-sim/Dockerfile` currently builds the **pre-migration** variant, because
that is the one whose `requirements.txt` and `.proto` were already published.
`dashboard/nginx.conf` proxies for both (`/mqtt` for the browser variant,
`/api/` and `/api-parallel/` for the edge services).

Pick one and delete the other before recording. The rest of this file documents
the browser-simulation variant.
