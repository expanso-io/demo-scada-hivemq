"""SCADA simulator — publishes Sparkplug B-style MQTT messages.

Generates Temperature, Pressure, and DoorSensor telemetry for 4 sites
(wind, solar, battery, distgen) and publishes to Mosquitto on
spBv1.0/<group>/DDATA/<node>/<device> topics.
"""

import json
import math
import os
import random
import time

import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_HOST", "mqtt-broker")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
INTERVAL = float(os.environ.get("PUBLISH_INTERVAL", "1.0"))
GROUP = "SCADA"

SITES = [
    {"node": "wind-turbine-01", "device": "nacelle-sensors"},
    {"node": "solar-array-02", "device": "inverter-sensors"},
    {"node": "battery-bank-03", "device": "bms-sensors"},
    {"node": "distgen-04", "device": "generator-sensors"},
]


def make_payload(node: str, tick: int) -> dict:
    """Generate realistic-ish sensor readings."""
    t = tick * INTERVAL
    base_temp = 45.0 + 15.0 * math.sin(t / 30.0)
    base_pressure = 101.3 + 2.0 * math.cos(t / 20.0)
    return {
        "timestamp": int(time.time() * 1000),
        "metrics": [
            {
                "name": "Temperature",
                "type": "Double",
                "value": round(base_temp + random.gauss(0, 0.3), 2),
            },
            {
                "name": "Pressure",
                "type": "Double",
                "value": round(base_pressure + random.gauss(0, 0.1), 2),
            },
            {
                "name": "DoorSensor",
                "type": "Boolean",
                "value": random.random() < 0.02,
            },
        ],
        "seq": tick,
    }


def main() -> None:
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="scada-sim",
        protocol=mqtt.MQTTv311,
    )

    print(f"Connecting to {BROKER}:{PORT} ...")
    connected = False
    for attempt in range(30):
        try:
            client.connect(BROKER, PORT, keepalive=60)
            connected = True
            break
        except (ConnectionRefusedError, OSError):
            print(f"  attempt {attempt + 1}/30 — broker not ready")
            time.sleep(2)

    if not connected:
        raise SystemExit("Could not connect to MQTT broker")

    client.loop_start()
    print("Publishing telemetry …")

    tick = 0
    try:
        while True:
            for site in SITES:
                topic = (
                    f"spBv1.0/{GROUP}/DDATA/"
                    f"{site['node']}/{site['device']}"
                )
                payload = make_payload(site["node"], tick)
                client.publish(topic, json.dumps(payload), qos=1)
            tick += 1
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        print("Stopped.")


if __name__ == "__main__":
    main()
