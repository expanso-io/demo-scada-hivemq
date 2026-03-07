# Demo Recording Script
## SCADA → Expanso Edge → HiveMQ

**Runtime:** ~8–10 minutes  
**Format:** Screen recording with voiceover  
**URL:** http://localhost:8888  

---

## Before You Hit Record

```bash
./run-demo.sh          # start the stack
# wait ~15 seconds for all services to come up
open http://localhost:8888
```

Confirm the dashboard is live and metrics are ticking (Rate In should show ~2–5 msg/s). All four toggles should be **OFF**.

---

## PART 1 — The Problem (0:00–1:00)

**[Screen: dashboard, all toggles OFF, metrics accumulating]**

> "This is a live SCADA environment — industrial sensors reporting temperature, pressure, and door state over MQTT using the Sparkplug B protocol.
>
> Right now, every single message from every sensor is flowing straight through to HiveMQ — our downstream broker. No filtering, no compression, no intelligence at the edge.
>
> Watch the numbers. Messages In and Messages Out are basically the same. Bytes In equals Bytes Out. We're shipping everything, including noise — tiny temperature fluctuations that don't mean anything, malformed payloads, redundant readings.
>
> At scale, that's egress cost. That's HiveMQ broker load. That's downstream processing you're paying for on data that doesn't matter.
>
> Expanso Edge sits between the source and the destination. Let's turn it on, one capability at a time."

---

## PART 2 — Dead-Banding (1:00–3:00)

**[Click DEADBAND toggle → ON]**

> "First: dead-banding.
>
> Temperature and Pressure are noisy sensors. They fluctuate constantly within a narrow range — half a degree, a fraction of a PSI. None of that is actionable.
>
> Dead-banding says: only forward a reading if it's changed by more than a threshold. Temperature needs to move more than 1°C. Pressure more than 0.5 units. Anything inside that band? Dropped at the edge.
>
> Watch Messages Dropped climb. Watch Rate Out drop relative to Rate In. Same physical sensors, same data — but we're only forwarding what changed."

**[Pause — let the numbers move for 10–15 seconds]**

> "That's a real reduction in downstream traffic. And we haven't touched the data that matters. Look at the message log — the readings still coming through are the ones with meaningful delta."

---

## PART 3 — Schema Validation (3:00–5:00)

**[Click SCHEMA toggle → ON]**

> "Second: schema validation.
>
> In industrial environments, sensors fail. Firmware bugs produce garbage values. A door sensor that reads 0 or 1 suddenly reports 47. A temperature sensor goes negative 200 in January in Phoenix.
>
> Schema validation catches that at the edge — before it ever hits your data pipeline, your historian, or your ML model.
>
> The rules here are tight: DoorSensor must be 0 or 1. Temperature must be between -40 and 150°C. Anything outside those bounds is flagged and dropped.
>
> Watch Validation Failures. The message log will show those readings in red — caught before they caused a bad alert downstream."

**[Pause — let a few validation failures accumulate]**

> "This is the principle of least privilege applied to data. Bad data doesn't earn the right to travel downstream just because it arrived."

---

## PART 4 — Compression (5:00–6:30)

**[Click COMPRESSION toggle → ON]**

> "Third: compression.
>
> Sparkplug B uses protobuf — already compact. But gzip on top of that cuts payload size by another 60–80% for typical telemetry.
>
> Watch Bytes Out drop relative to Bytes In. The Saved % stat shows your real-time bandwidth reduction.
>
> For a plant sending thousands of readings per minute over a cellular or satellite link, that's direct infrastructure cost savings. You're paying per byte in most industrial WAN scenarios."

**[Pause — let Saved % settle]**

> "The downstream broker receives exactly the same data — it just gets there cheaper."

---

## PART 5 — Fan-Out (6:30–8:00)

**[Click FANOUT toggle → ON]**

> "Fourth: fan-out.
>
> One stream in, two streams out. Every message that passes through Expanso Edge is now published to two topics simultaneously: the primary HiveMQ topic, and an archive topic — `archive/spBv1.0/#`.
>
> Look at the bottom panel. Archive Topic flips to ACTIVE. That second stream could feed a historian, a cold storage sink, a compliance archive, a separate analytics pipeline — whatever your architecture needs.
>
> Zero changes to the SCADA source. Zero changes to HiveMQ. The routing logic lives in Expanso Edge."

---

## PART 6 — The Payoff (8:00–9:00)

**[Screen: full dashboard with all four toggles ON, Saved % visible]**

> "So let's look at what we've built.
>
> All four features on, simultaneously. Dead-banding filtering noise. Schema validation catching bad data. Compression reducing wire size. Fan-out routing to two destinations.
>
> Messages Dropped shows what we eliminated. Saved % shows what we saved on bandwidth. Validation Failures shows what we protected downstream systems from.
>
> This is Expanso Edge. Move computation to the data — don't move data you don't need to."

---

## PART 7 — Wrap / CTA (9:00–9:30)

> "The full source for this demo is on GitHub at expanso-io/demo-scada-hivemq. Docker Compose, one command to run, no cloud account required.
>
> If you're running industrial workloads over MQTT — or any streaming protocol — and you're tired of paying to move data you don't use, talk to us."

---

## After Recording

```bash
./stop-demo.sh
```

---

## Cheat Sheet (on-screen reference)

| Toggle | What it does | Metric to watch |
|--------|-------------|-----------------|
| DEADBAND | Drops readings within threshold | Messages Dropped ↑, Rate Out ↓ |
| SCHEMA | Rejects out-of-range values | Validation Failures ↑ |
| COMPRESSION | gzip on wire payloads | Saved % ↑, Bytes Out ↓ |
| FANOUT | Duplicates to archive topic | Archive Topic → ACTIVE |

---

## Timing Notes

- Let each toggle run for **10–15 seconds** before narrating the numbers — give the metrics time to visibly move.
- Dead-banding has the most dramatic visual effect — spend the most time here.
- The message log table updates live — scroll it slowly during schema validation to show red flagged rows.
