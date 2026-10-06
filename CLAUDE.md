> **Directory-wide rules apply.** Read [`../AGENTS.md`](../AGENTS.md) first.
> It governs every demo in `projects/demos/`. For work involving a screen
> recording, finished video, publishing copy, or a launch, read
> [`../demo-guidance/README.md`](../demo-guidance/README.md) before acting.
> `_demo-kit` runs before recording; `demo-guidance` runs after.

# CLAUDE.md

## What this repository runs

This demo sends Sparkplug B protobuf records from an authenticated Mosquitto
source through Expanso Edge v2.1.21 to an authenticated TLS-only HiveMQ broker.
The Edge job decodes, validates, deadbands, re-encodes, and fans out the records.
The dashboard is a localhost presenter and fixture explorer; it does not process
or invent runtime results in the browser.

## Commands

```bash
./run-demo.sh       # reset, start, replay, and verify the bounded fixture
./stop-demo.sh      # stop only the local Compose project
just static-check   # source checks without browser or runtime startup
just ui-check       # rendered browser checks
just check          # full source, browser, and runtime acceptance
just live           # acceptance, then optional continuous OPC UA source
just cloud-deploy   # deploy the job through the configured Cloud CLI profile
```

The local dashboard is <http://127.0.0.1:8888>. HiveMQ exposes MQTT over TLS at
`127.0.0.1:8883`. The source broker and Expanso Edge API stay on the internal
Compose network.

## Key files

- `pipelines/scada-hivemq.yaml`: the only published Expanso job.
- `fixtures/input.ndjson`: three decoded records used to build the protobuf
  inputs.
- `fixtures/expected.json`: expected output counts and metric names.
- `fixtures/stages.json`: per-stage explorer input and output.
- `scripts/verify_fixture.py`: secured end-to-end runtime assertion.
- `dashboard/index.html`, `styles.css`, `app.js`: presenter and explorer.
- `hivemq/config.xml`: TLS listener.
- `hivemq/extension-config.xml`: file RBAC extension configuration.
- `docker-compose.yml`: pinned services, networks, volumes, and security.

## Proof boundaries

The Compose lane uses Expanso Edge local mode and generated broker credentials.
It proves the shipped fixture, pipeline, protocol handling, TLS, authentication,
and output assertions. Production uses Expanso Cloud to assign the same job to
nodes labeled `demo=scada-hivemq`. A local pass is not a Cloud execution.

Commits `919390c` and `5477d01` removed the uncommissioned Ignition runtime. The
current OPC UA simulator publishes real Sparkplug B directly. Files under
`ignition-edge/provisioning/` are optional references and are not a running
service.
