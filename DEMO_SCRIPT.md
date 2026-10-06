# SCADA to HiveMQ demo script

Run `./run-demo.sh` before recording. Start only after the command prints
`Local acceptance passed` and the dashboard loads at
<http://127.0.0.1:8888>.

## Opening

Show the topology first.

> Three Sparkplug B records enter through an authenticated MQTT broker. Expanso
> Edge decodes the protobuf payloads, enforces the sensor contract, removes
> readings inside the deadband, and sends secured outputs to HiveMQ. The
> telemetry stays on the data plane. Expanso Cloud owns production deployment
> and execution state.

Point out the proof boundary below the title. The page uses committed fixture
records. The terminal acceptance run proves the real local pipeline and broker
delivery. Neither is a claim that a Cloud execution is running.

## Walk the pipeline

Use Right Arrow for each stage. Do not scroll between stages.

1. **Authenticated MQTT ingest.** Show the 89-byte protobuf payload and source
   topic.
2. **Sparkplug B decode.** Point out the three decoded metrics: temperature,
   pressure, and door state.
3. **Payload schema checks.** Show the allowed names, datatypes, and empty error
   list for sequence 18. Mention that sequence 19 is quarantined at `999.0`.
4. **Stateful deadband.** Compare sequence 18 with sequence 17. Temperature
   changes by `0.2` and pressure by `0.1`, so only `DoorSensor` remains.
5. **Sparkplug B re-encode.** The valid output shrinks from 89 bytes to 34 bytes
   while remaining a Sparkplug B protobuf payload.
6. **Authenticated TLS fan-out.** Show the primary protobuf, gzip archive, and
   JSON metrics topics. Mention the separate quarantine topic for rejected
   records.

Use the copy control once. The `Copied` result appears beside the button. Then
download the stage records and show the `Downloaded` result in the same place.

## Close

Return to the topology.

> The acceptance run observed two primary messages, two archive messages, two
> metrics records, and one quarantine record. It also proved that authenticated
> TLS succeeds and an anonymous HiveMQ connection fails. Production uses the
> same job through Expanso Cloud on labeled edge nodes.

After recording, run `./stop-demo.sh` and confirm ports `8883` and `8888` are no
longer listening.
