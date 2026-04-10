import gzip
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Any

import paho.mqtt.client as mqtt
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

import sparkplug_b_pb2

SOURCE_HOST = os.getenv("MQTT_SOURCE_HOST", "mqtt-source")
SOURCE_PORT = int(os.getenv("MQTT_SOURCE_PORT", "1883"))
TARGET_HOST = os.getenv("MQTT_TARGET_HOST", "mqtt-broker")
TARGET_PORT = int(os.getenv("MQTT_TARGET_PORT", "1883"))
SUB_TOPIC = os.getenv("MQTT_SUB_TOPIC", "spBv1.0/#")
TOPIC_PREFIX_STRIP = os.getenv("TOPIC_PREFIX_STRIP", "")


@dataclass
class ProcessedMessage:
    topic: str
    metric: str
    value: Any
    datatype: str
    timestamp: str
    quality: str
    status: str


class FeatureConfig(BaseModel):
    deadband: bool
    schema_validation: bool
    compression: bool
    fanout: bool


class EdgeState:
    def __init__(self) -> None:
        self.features = {
            "deadband": os.getenv("ENABLE_DEADBAND", "false").lower() == "true",
            "schema": os.getenv("ENABLE_SCHEMA_VALIDATION", "false").lower() == "true",
            "compression": os.getenv("ENABLE_COMPRESSION", "false").lower() == "true",
            "fanout": os.getenv("ENABLE_FANOUT", "false").lower() == "true",
        }
        self.metrics: dict[str, Any] = {
            "messages_in": 0,
            "messages_out": 0,
            "messages_dropped": 0,
            "bytes_in": 0,
            "bytes_out": 0,
            "bytes_saved_pct": 0.0,
            "validation_failures": 0,
            "current_features_enabled": self.features,
            "messages_in_rate": 0.0,
            "messages_out_rate": 0.0,
        }
        self.messages: deque[dict[str, Any]] = deque(maxlen=50)
        self.last_values: dict[str, float] = {}
        self._in_counter = 0
        self._out_counter = 0
        self._lock = threading.Lock()

    def add_message(self, msg: ProcessedMessage) -> None:
        with self._lock:
            self.messages.appendleft(asdict(msg))

    def tick_rates(self) -> None:
        with self._lock:
            self.metrics["messages_in_rate"] = round(self._in_counter / 2.0, 1)
            self.metrics["messages_out_rate"] = round(self._out_counter / 2.0, 1)
            self._in_counter = 0
            self._out_counter = 0


state = EdgeState()
app = FastAPI(title="Expanso Edge")

# Paho publisher client (threadsafe publish)
pub_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="expanso-publisher")


def metric_value(metric: sparkplug_b_pb2.Payload.Metric) -> tuple[Any, str]:
    if metric.HasField("float_value"):
        return float(metric.float_value), "float"
    if metric.HasField("double_value"):
        return float(metric.double_value), "double"
    if metric.HasField("int_value"):
        return int(metric.int_value), "int32"
    if metric.HasField("long_value"):
        return int(metric.long_value), "int64"
    if metric.HasField("boolean_value"):
        return bool(metric.boolean_value), "boolean"
    if metric.HasField("string_value"):
        return metric.string_value, "string"
    return None, "unknown"


def set_metric_value(metric: sparkplug_b_pb2.Payload.Metric, value: Any, dtype: str) -> None:
    if dtype in {"float", "double"}:
        metric.float_value = float(value)
    elif dtype in {"int32", "int64"}:
        metric.int_value = int(value)
    elif dtype == "boolean":
        metric.boolean_value = bool(value)
    else:
        metric.string_value = str(value)


def iso_ms(ts_ms: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts_ms / 1000.0)) + f".{ts_ms % 1000:03d}Z"


def validate_metric(name: str, value: Any) -> bool:
    if name == "DoorSensor":
        return value in {0, 1, 0.0, 1.0}
    if name == "Temperature":
        return -40 <= float(value) <= 150
    return True


def should_drop_deadband(name: str, value: Any) -> bool:
    if name not in {"Temperature", "Pressure"}:
        return False
    threshold = 1.0 if name == "Temperature" else 0.5
    prev = state.last_values.get(name)
    state.last_values[name] = float(value)
    if prev is None:
        return False
    return abs(float(value) - prev) < threshold


def process_message(topic: str, payload: bytes) -> None:
    with state._lock:
        state.metrics["messages_in"] += 1
        state._in_counter += 1
        state.metrics["bytes_in"] += len(payload)

    try:
        parsed = sparkplug_b_pb2.Payload()
        parsed.ParseFromString(payload)
    except Exception as exc:
        state.add_message(ProcessedMessage(topic, "<decode_error>", str(exc), "unknown",
                                           iso_ms(int(time.time() * 1000)), "BAD", "invalid"))
        return

    if len(parsed.metrics) == 0:
        return

    forward_payload = sparkplug_b_pb2.Payload()
    forward_payload.timestamp = parsed.timestamp
    forward_payload.seq = parsed.seq

    dropped_any = False

    for m in parsed.metrics:
        value, dtype = metric_value(m)
        name = m.name or f"alias_{m.alias}"
        ts = m.timestamp if m.HasField("timestamp") else parsed.timestamp

        if state.features["schema"] and not validate_metric(name, value):
            with state._lock:
                state.metrics["messages_dropped"] += 1
                state.metrics["validation_failures"] += 1
            dropped_any = True
            state.add_message(ProcessedMessage(topic, name, value, dtype, iso_ms(ts), "BAD", "invalid"))
            continue

        if state.features["deadband"] and should_drop_deadband(name, value):
            with state._lock:
                state.metrics["messages_dropped"] += 1
            dropped_any = True
            state.add_message(ProcessedMessage(topic, name, value, dtype, iso_ms(ts), "GOOD", "dropped"))
            continue

        new_metric = forward_payload.metrics.add()
        new_metric.name = name
        if m.HasField("timestamp"):
            new_metric.timestamp = m.timestamp
        if m.HasField("datatype"):
            new_metric.datatype = m.datatype
        set_metric_value(new_metric, value, dtype)
        state.add_message(ProcessedMessage(
            topic, name, value, dtype, iso_ms(ts), "GOOD",
            "compressed" if state.features["compression"] else "passed",
        ))

    if dropped_any and len(forward_payload.metrics) == 0:
        return

    wire_payload = forward_payload.SerializeToString()
    out_topic = topic
    if TOPIC_PREFIX_STRIP and out_topic.startswith(TOPIC_PREFIX_STRIP):
        out_topic = out_topic[len(TOPIC_PREFIX_STRIP):]

    if state.features["compression"]:
        wire_payload = gzip.compress(wire_payload)

    pub_client.publish(out_topic, wire_payload, qos=0)
    if state.features["fanout"]:
        pub_client.publish(f"archive/{topic}", wire_payload, qos=0)

    with state._lock:
        state.metrics["messages_out"] += 1
        state._out_counter += 1
        state.metrics["bytes_out"] += len(wire_payload)
        if state.metrics["bytes_in"] > 0:
            saved = 1 - (state.metrics["bytes_out"] / state.metrics["bytes_in"])
            state.metrics["bytes_saved_pct"] = round(saved * 100, 2)


def mqtt_worker() -> None:
    """Subscriber thread — blocks forever, reconnects on failure."""
    def on_message(client, userdata, msg):
        try:
            process_message(msg.topic, msg.payload)
        except Exception:
            pass

    while True:
        try:
            sub = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="expanso-subscriber")
            sub.on_message = on_message
            sub.connect(SOURCE_HOST, SOURCE_PORT, keepalive=60)
            sub.subscribe(SUB_TOPIC, qos=0)
            sub.loop_forever()
        except Exception:
            time.sleep(2)


def rate_worker() -> None:
    while True:
        time.sleep(2)
        state.tick_rates()


# ─── FastAPI routes ────────────────────────────────────────────────────────────

@app.get("/metrics")
def get_metrics() -> dict[str, Any]:
    with state._lock:
        state.metrics["current_features_enabled"] = dict(state.features)
        return dict(state.metrics)


@app.get("/messages")
def get_messages() -> dict[str, Any]:
    with state._lock:
        return {"messages": list(state.messages)}


@app.post("/config")
def update_config(cfg: FeatureConfig) -> dict[str, Any]:
    with state._lock:
        state.features["deadband"] = cfg.deadband
        state.features["schema"] = cfg.schema_validation
        state.features["compression"] = cfg.compression
        state.features["fanout"] = cfg.fanout
        state.metrics["current_features_enabled"] = dict(state.features)
        return {"ok": True, "features": dict(state.features)}


# ─── Startup ──────────────────────────────────────────────────────────────────

def publisher_worker() -> None:
    """Publisher thread — connects to target broker with retries."""
    while True:
        try:
            pub_client.connect(TARGET_HOST, TARGET_PORT, keepalive=60)
            pub_client.loop_start()
            return  # loop_start runs in background; we're done here
        except Exception:
            time.sleep(2)


@app.on_event("startup")
def startup() -> None:
    threading.Thread(target=publisher_worker, daemon=True).start()
    threading.Thread(target=mqtt_worker, daemon=True).start()
    threading.Thread(target=rate_worker, daemon=True).start()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
