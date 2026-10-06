#!/usr/bin/env python3
"""Replay the bounded Sparkplug fixture and verify every secured output."""

from __future__ import annotations

import gzip
import json
import os
import ssl
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt

import sparkplug_b_pb2


SOURCE_HOST = "mqtt-source"
SOURCE_PORT = 1883
TARGET_HOST = "mqtt-broker"
TARGET_PORT = 8883
SOURCE_TOPIC = "spBv1.0/Expanso/DDATA/edge1/sensors"
CA_FILE = "/run/hivemq-tls/ca.crt"
FIXTURE_FILE = Path("/fixtures/input.ndjson")
EXPECTED_FILE = Path("/fixtures/expected.json")
PERSISTENCE_TOPIC = "proof/persistence"
PERSISTENCE_PAYLOAD = b"hivemq-volume-survived"


def read_secret(name: str) -> str:
    return Path(f"/run/secrets/{name}").read_text().strip()


def metric_value(metric: dict[str, object], output: object) -> None:
    datatype = int(metric["datatype"])
    if datatype == 9:
        output.float_value = float(metric["floatValue"])
    elif datatype == 3:
        output.int_value = int(metric["intValue"])
    else:
        raise AssertionError(f"unsupported fixture datatype: {datatype}")


def encode_record(record: dict[str, object]) -> bytes:
    payload = sparkplug_b_pb2.Payload()
    payload.timestamp = int(record["timestamp"])
    payload.seq = int(record["seq"])
    for metric in record["metrics"]:
        output = payload.metrics.add()
        output.name = str(metric["name"])
        output.timestamp = int(record["timestamp"])
        output.datatype = int(metric["datatype"])
        metric_value(metric, output)
    return payload.SerializeToString()


def metric_names(payload: bytes) -> list[str]:
    decoded = sparkplug_b_pb2.Payload()
    decoded.ParseFromString(payload)
    return [metric.name for metric in decoded.metrics]


def anonymous_connection_is_rejected() -> bool:
    complete = threading.Event()
    result = {"accepted": False}

    def on_connect(
        client: mqtt.Client,
        userdata: object,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        del client, userdata, flags, properties
        result["accepted"] = not reason_code.is_failure
        complete.set()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="fixture-anonymous-negative-check",
    )
    client.tls_set(ca_certs=CA_FILE, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect = on_connect
    client.connect(TARGET_HOST, TARGET_PORT, 10)
    client.loop_start()
    complete.wait(5)
    client.disconnect()
    client.loop_stop()
    return complete.is_set() and not result["accepted"]


def publish_persistence_marker() -> None:
    connected = threading.Event()

    def on_connect(
        client: mqtt.Client,
        userdata: object,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        del client, userdata, flags, properties
        if reason_code.is_failure:
            raise AssertionError(f"persistence publisher failed: {reason_code}")
        connected.set()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="fixture-persistence-publisher",
    )
    client.username_pw_set(
        "fixture-observer", read_secret("hivemq-observer-password")
    )
    client.tls_set(ca_certs=CA_FILE, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect = on_connect
    client.connect(TARGET_HOST, TARGET_PORT, 10)
    client.loop_start()
    if not connected.wait(10):
        raise AssertionError("persistence publisher did not connect")
    publication = client.publish(
        PERSISTENCE_TOPIC,
        PERSISTENCE_PAYLOAD,
        qos=1,
        retain=True,
    )
    publication.wait_for_publish(5)
    client.disconnect()
    client.loop_stop()


def verify_persistence_marker() -> None:
    connected = threading.Event()
    retained = threading.Event()

    def on_connect(
        client: mqtt.Client,
        userdata: object,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        del userdata, flags, properties
        if reason_code.is_failure:
            raise AssertionError(f"persistence observer failed: {reason_code}")
        client.subscribe(PERSISTENCE_TOPIC, qos=1)
        connected.set()

    def on_message(
        client: mqtt.Client,
        userdata: object,
        message: mqtt.MQTTMessage,
    ) -> None:
        del client, userdata
        if (
            message.topic == PERSISTENCE_TOPIC
            and bytes(message.payload) == PERSISTENCE_PAYLOAD
            and message.retain
        ):
            retained.set()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="fixture-persistence-observer",
    )
    client.username_pw_set(
        "fixture-observer", read_secret("hivemq-observer-password")
    )
    client.tls_set(ca_certs=CA_FILE, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(TARGET_HOST, TARGET_PORT, 10)
    client.loop_start()
    if not connected.wait(10):
        raise AssertionError("persistence observer did not connect")
    if not retained.wait(10):
        raise AssertionError("retained marker did not survive broker recreation")
    client.disconnect()
    client.loop_stop()


def persistence_only() -> None:
    result_path = Path(os.environ["RESULT_PATH"])
    report = json.loads(result_path.read_text())
    verify_persistence_marker()
    report["persistence"] = "retained message survived broker recreation"
    result_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


def main() -> None:
    if os.getenv("VERIFY_PERSISTENCE_ONLY") == "1":
        persistence_only()
        return

    fixture = [json.loads(line) for line in FIXTURE_FILE.read_text().splitlines()]
    expected = json.loads(EXPECTED_FILE.read_text())
    received: list[tuple[str, bytes]] = []
    connected = threading.Event()
    complete = threading.Event()
    expected_total = sum(
        expected[key]
        for key in (
            "primary_records",
            "archive_records",
            "metrics_records",
            "quarantine_records",
        )
    )

    def on_connect(
        client: mqtt.Client,
        userdata: object,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        del userdata, flags, properties
        if reason_code.is_failure:
            raise AssertionError(f"authenticated TLS connection failed: {reason_code}")
        client.subscribe("#", qos=1)
        connected.set()

    def on_message(
        client: mqtt.Client,
        userdata: object,
        message: mqtt.MQTTMessage,
    ) -> None:
        del client, userdata
        received.append((message.topic, bytes(message.payload)))
        if len(received) >= expected_total:
            complete.set()

    observer = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="fixture-output-observer",
    )
    observer.username_pw_set("fixture-observer", read_secret("hivemq-observer-password"))
    observer.tls_set(ca_certs=CA_FILE, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    observer.on_connect = on_connect
    observer.on_message = on_message
    observer.connect(TARGET_HOST, TARGET_PORT, 10)
    observer.loop_start()
    if not connected.wait(10):
        raise AssertionError("authenticated TLS observer did not connect")

    producer = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="fixture-source-publisher",
    )
    producer.username_pw_set("source-publisher", read_secret("source-password"))
    producer.connect(SOURCE_HOST, SOURCE_PORT, 10)
    producer.loop_start()
    for record in fixture:
        publication = producer.publish(SOURCE_TOPIC, encode_record(record), qos=1)
        publication.wait_for_publish(5)
        time.sleep(0.15)
    producer.disconnect()
    producer.loop_stop()

    if not complete.wait(15):
        raise AssertionError(
            f"timed out after {len(received)} of {expected_total} expected outputs"
        )
    observer.disconnect()
    observer.loop_stop()

    grouped: dict[str, list[bytes]] = {
        "primary": [],
        "archive": [],
        "metrics": [],
        "quarantine": [],
    }
    for topic, payload in received:
        if topic.startswith("archive/"):
            grouped["archive"].append(payload)
        elif topic.startswith("metrics/"):
            grouped["metrics"].append(payload)
        elif topic.startswith("quarantine/"):
            grouped["quarantine"].append(payload)
        elif topic.startswith("spBv1.0/"):
            grouped["primary"].append(payload)

    actual_counts = {name: len(records) for name, records in grouped.items()}
    expected_counts = {
        "primary": expected["primary_records"],
        "archive": expected["archive_records"],
        "metrics": expected["metrics_records"],
        "quarantine": expected["quarantine_records"],
    }
    assert actual_counts == expected_counts, (actual_counts, expected_counts)

    primary_metrics = [metric_names(payload) for payload in grouped["primary"]]
    assert primary_metrics == [
        record["metric_names"] for record in expected["primary"]
    ], primary_metrics
    archive_metrics = [
        metric_names(gzip.decompress(payload)) for payload in grouped["archive"]
    ]
    assert archive_metrics == primary_metrics, archive_metrics

    metrics_records = [json.loads(payload) for payload in grouped["metrics"]]
    assert [record["metric_names"] for record in metrics_records] == primary_metrics
    quarantine = [json.loads(payload) for payload in grouped["quarantine"]]
    assert quarantine[0]["errors"] == expected["quarantine"][0]["errors"]
    assert int(quarantine[0]["payload"]["seq"]) == expected["quarantine"][0]["seq"]
    assert anonymous_connection_is_rejected(), "anonymous TLS connection was accepted"
    publish_persistence_marker()

    report = {
        "fixture": str(FIXTURE_FILE),
        "input_records": len(fixture),
        "outputs": actual_counts,
        "primary_metric_names": primary_metrics,
        "authenticated_tls": "accepted",
        "anonymous_tls": "rejected",
        "persistence": "retained marker published",
        "result": "pass",
    }
    result_path = os.getenv("RESULT_PATH")
    if result_path:
        Path(result_path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
