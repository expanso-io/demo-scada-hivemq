# SCADA → Expanso Edge → HiveMQ Live Demo
## Quick Start

1. Copy `.env.example` to `.env` and fill in your cluster details:
   ```
   cp .env.example .env
   # edit .env with your EXPANSO_CLUSTER_ID
   ```
2. Run the demo:
   ```
   ./run-demo.sh
   ```
3. Open **http://localhost:8888**

To stop: `./stop-demo.sh`

---


A self-contained Docker Compose demo showing how Expanso Edge sits between an upstream Sparkplug publisher and HiveMQ, with runtime toggles for dead-banding, schema validation, compression, and fan-out.

## Architecture

```text
                    (primary path)
+----------------+      +----------------------+      +------------------+      +----------------+
| SCADA Simulator| ---> | MQTT Source Broker  | ---> | Expanso Edge     | ---> | HiveMQ         |
| asyncua OPC-UA |      | (Mosquitto)         |      | (policy pipeline)|      | (final broker) |
+--------+-------+      +----------+-----------+      +--------+---------+      +--------+-------+
         |                         ^                           |                         |
         | OPC-UA                  | Sparkplug B              | archive/spBv1.0/#        | websocket
         v                         |                           v                         v
+----------------+                 |                   +------------------+      +----------------+
| Ignition Edge  |-----------------+                   | Expanso Parallel |----> | Dashboard      |
| Trial Gateway  |  provisioning assets               | bypass path       |      | (nginx static) |
+----------------+                                     +------------------+      +----------------+
```

## Services

- `scada-sim`: real OPC-UA server (`asyncua`) with 100ms updates.
- `ignition-edge`: official `inductiveautomation/ignition` image (trial mode) with mounted provisioning files.
- `mqtt-source`: Mosquitto broker for upstream Sparkplug input.
- `expanso-edge`: in-line Expanso pipeline (`spBv1.0/#` -> HiveMQ).
- `expanso-edge-parallel`: parallel Expanso pipeline (`parallel/spBv1.0/#` -> HiveMQ).
- `mqtt-broker`: HiveMQ Community (`1883` + websocket `8000`).
- `dashboard`: single-file web UI on `http://localhost:8888`.

## Quickstart

```bash
docker compose up --build
```

Endpoints:
- Dashboard: `http://localhost:8888`
- Expanso metrics API: `http://localhost:8080/metrics`
- Ignition Edge UI: `http://localhost:8088`
- HiveMQ TCP: `localhost:1883`
- HiveMQ websocket: `ws://localhost:8000/mqtt`
- SCADA OPC-UA endpoint: `opc.tcp://localhost:4840/freeopcua/server/`

## Progressive Demo Flow

### a) Default Flow (Panel A)
1. Open dashboard.
2. Keep all feature toggles OFF.
3. Observe raw ingest/out rates, bytes, and decoded Sparkplug metrics.

### b) Expanso In-Line (Panel B)
1. Toggle features one by one.
2. Watch immediate impact in dropped counts, validation failures, and byte savings.
3. Review message table status colors:
- green: passed
- red: dropped/invalid
- yellow: compressed

### c) Expanso Parallel (Panel C)
1. Enable the same toggles.
2. Compare the parallel path counters to the in-line path.
3. Confirm bypass route (`parallel/spBv1.0/#`) is independently processed.

## Feature Toggles

Runtime API:

```http
POST /config
Content-Type: application/json

{"deadband": true, "schema": true, "compression": true, "fanout": true}
```

Behavior:
- `deadband`: drops `Temperature` deltas `< 1.0 C` and `Pressure` deltas `< 0.5`.
- `schema`: rejects `DoorSensor` not in `{0,1}` and `Temperature` outside `[-40,150]`.
- `compression`: gzip compresses outgoing Sparkplug payload bytes, tracks savings.
- `fanout`: forwards to HiveMQ and `archive/spBv1.0/#`.

## Sparkplug B Assets

- `sparkplug_b.proto` is included at repo root.
- `sparkplug_b_pb2.py` is generated during Docker build via `grpcio-tools`.
- Expanso decodes/re-encodes protobuf payloads and exposes decoded metrics via `/messages`.

## Ignition Edge Provisioning

Provisioning artifacts are in `ignition-edge/provisioning/`:
- `gateway-init.env`
- `opcua-mqtt-mapping.json`
- `README.md`

The stack is live without manual commissioning (using deterministic Sparkplug feed), while keeping official Ignition Edge running for full trial setup and extension.
