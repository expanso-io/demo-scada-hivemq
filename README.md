# SCADA to HiveMQ through Expanso Edge

This repository runs a complete Sparkplug B pipeline between a private MQTT
source broker and HiveMQ. Expanso Edge decodes the protobuf payload, checks the
topic and metric schema, applies stateful deadbands, re-encodes the remaining
metrics, and fans them out to primary, archive, and metrics topics. Invalid
readings go to quarantine.

The bounded fixture has three records. The first establishes deadband state,
the second keeps only `DoorSensor`, and the third is quarantined because its
temperature is `999.0`.

## Architecture

```text
fixture publisher
      |
      | Sparkplug B protobuf, MQTT 3.1.1, authenticated
      v
Mosquitto source broker
      |
      v
Expanso Edge v2.1.21
      |-- decode and validate
      |-- stateful deadband
      |-- protobuf re-encode
      |
      | MQTT over TLS 1.2+, authenticated
      v
HiveMQ
      |-- spBv1.0/#          Sparkplug B protobuf
      |-- archive/#          gzip Sparkplug B protobuf
      |-- metrics/#          JSON summary
      `-- quarantine/#       JSON rejection record
```

Docker Compose pins every image by tag and digest. Both brokers use generated
runtime credentials. HiveMQ exposes only its TLS listener, persists broker data
in named volumes, drops Linux capabilities, and uses the file RBAC extension.
The source broker is confined to the internal data-plane network.

## Pipeline explorer

The dashboard follows the same six stages as
[`pipelines/scada-hivemq.yaml`](pipelines/scada-hivemq.yaml):

1. authenticated MQTT ingest;
2. Sparkplug B protobuf decode;
3. topic, datatype, metric, and value checks;
4. stateful temperature and pressure deadbands;
5. Sparkplug B protobuf re-encode;
6. authenticated TLS fan-out to HiveMQ.

Each stage shows the real fixture input, output, and matching lines from the
shipped pipeline. The page fetches
[`fixtures/stages.json`](fixtures/stages.json) and the pipeline file at runtime,
so it does not carry an embedded copy of the YAML. Use Left and Right to page
stages without moving the page. Light mode is the default; the header includes
an explicit dark-mode toggle.

## Run the local proof lane

Requirements:

- Docker Desktop with Compose;
- `curl` on the host;
- ports `8883` and `8888` available.

Start and stop:

```bash
just up
just down
```

`just up` resets the local containers, starts both brokers and Expanso Edge,
deploys the pipeline through the local Edge API, and replays the three fixture
records. It exits only after the verifier observes:

- 2 primary Sparkplug B records;
- 2 gzip archive records;
- 2 JSON metrics records;
- 1 quarantine record;
- only `DoorSensor` in the second primary record;
- a successful authenticated TLS connection to HiveMQ;
- a rejected anonymous TLS connection.

Open <http://127.0.0.1:8888> after `just up` passes. `just down` stops every
local container and fails unless ports 8883 and 8888 are free. It affects only
the local Compose project. It does not delete Cloud
jobs or broker volumes.

The optional continuous OPC UA source and Sparkplug publisher is separate from
the bounded acceptance lane:

```bash
just live
```

It publishes changing temperature, pressure, and door readings after the
fixture acceptance has passed.

## Verify the repository

Run the full local gate:

```bash
just check
```

`just check` validates the Expanso job, Compose configuration, XML, shell and
JavaScript, explorer fixtures, rendered page behavior, and the secured runtime
acceptance. `just static-check` omits browsers and containers when only a fast
source check is needed.

The dated acceptance report is committed at
[`docs/verification/2026-10-05-public-bar.md`](docs/verification/2026-10-05-public-bar.md).

## Deploy with Expanso Cloud

Production execution is Cloud-managed. Prepare an Expanso Edge node with the
label `demo=scada-hivemq`, then give that node network access to the source and
destination brokers. Its runtime environment must define:

| Variable | Required value |
| --- | --- |
| `SOURCE_MQTT_URL` | MQTT URL for the authenticated source broker |
| `SOURCE_MQTT_USER` | source username |
| `SOURCE_MQTT_PASSWORD` | source password from the node secret store |
| `HIVEMQ_URL` | TLS MQTT URL for HiveMQ, such as `ssl://broker:8883` |
| `HIVEMQ_USER` | HiveMQ publisher username |
| `HIVEMQ_PASSWORD` | HiveMQ password from the node secret store |
| `HIVEMQ_CA_FILE` | mounted CA certificate path |

Do not put passwords or bootstrap tokens in the repository. Authenticate
`expanso-cli` with its normal profile, then deploy:

Run the target Edge service with a working directory that contains the shipped
`sparkplug_b.proto` file. The local container mounts it at `/schemas` and uses
that directory as its working directory.

```bash
just cloud-deploy
```

Deployment acceptance and workload execution are separate states. Confirm the
assigned execution before reporting that the production job is running:

```bash
expanso-cli execution list --job scada-hivemq
```

The Compose acceptance lane proves the same processing config without Cloud
credentials. It is not evidence of a Cloud execution.

## Ignition provisioning assets

Commits `919390c` and `5477d01` removed the uncommissioned Ignition container
and its dashboard references. The current stack publishes Sparkplug B directly
from the in-repository OPC UA simulator, so the pipeline runs without a trial
gateway. The files under `ignition-edge/provisioning/` remain as optional
mapping references; Compose does not claim to provision or run Ignition.

Local ports are declared in `ports.json`. `just ports` shows the stable
assignments. `just down` retains them, so the next `just up` reuses the URL.
An occupied assigned port fails startup without silently changing the URL.
