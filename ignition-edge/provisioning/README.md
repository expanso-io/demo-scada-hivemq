# Ignition Edge Provisioning

This folder is mounted into the Ignition container so the trial gateway can be commissioned with deterministic settings.

## Intended provisioning
- OPC-UA connection target: `opc.tcp://scada-sim:4840/freeopcua/server/`
- Sparkplug destination topic: `spBv1.0/Expanso/DDATA/edge1/sensors`
- MQTT broker target: `mqtt-source:1883`

## Files
- `gateway-init.env`: canonical env var values for container startup.
- `opcua-mqtt-mapping.json`: source-to-metric mapping used during commissioning.

## Trial bootstrap steps (Gateway Web UI)
1. Open Ignition at `http://localhost:8088`.
2. Complete trial commissioning.
3. Configure OPC-UA client connection to `scada-sim` endpoint.
4. Configure MQTT Transmission/Distributor to `mqtt-source:1883`.
5. Publish DDATA payloads on `spBv1.0/Expanso/DDATA/edge1/sensors`.

These provisioning assets keep configuration reproducible across demo runs.
