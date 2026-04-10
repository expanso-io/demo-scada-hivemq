import asyncio
import math
import os
import random
import time
from dataclasses import dataclass

import paho.mqtt.client as mqtt
from asyncua import Server, ua

import sparkplug_b_pb2

UPDATE_INTERVAL = float(os.getenv("UPDATE_INTERVAL_SEC", "0.1"))
OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://0.0.0.0:4840/freeopcua/server/")
MQTT_HOST = os.getenv("MQTT_HOST", "mqtt-source")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
SPARKPLUG_TOPIC = os.getenv("SPARKPLUG_TOPIC", "spBv1.0/Expanso/DDATA/edge1/sensors")
PARALLEL_TOPIC = os.getenv("PARALLEL_SPARKPLUG_TOPIC", "parallel/spBv1.0/Expanso/DDATA/edge1/sensors")
ENABLE_DIRECT_SPARKPLUG = os.getenv("ENABLE_DIRECT_SPARKPLUG", "true").lower() == "true"
ENABLE_PARALLEL_FEED = os.getenv("ENABLE_PARALLEL_FEED", "true").lower() == "true"

# Sparkplug metric datatype ids used by this demo.
DT_INT32 = 3
DT_FLOAT = 9


@dataclass
class Sensors:
    temperature: float = 22.0
    pressure: float = 1.8
    door_sensor: float = 0.0


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def build_payload(sensors: Sensors) -> bytes:
    payload = sparkplug_b_pb2.Payload()
    now_ms = int(time.time() * 1000)
    payload.timestamp = now_ms
    payload.seq = now_ms % 256

    temp = payload.metrics.add()
    temp.name = "Temperature"
    temp.timestamp = now_ms
    temp.datatype = DT_FLOAT
    temp.float_value = float(sensors.temperature)

    pressure = payload.metrics.add()
    pressure.name = "Pressure"
    pressure.timestamp = now_ms
    pressure.datatype = DT_FLOAT
    pressure.float_value = float(sensors.pressure)

    door = payload.metrics.add()
    door.name = "DoorSensor"
    door.timestamp = now_ms
    if sensors.door_sensor in (0.0, 1.0):
        door.datatype = DT_INT32
        door.int_value = int(sensors.door_sensor)
    else:
        door.datatype = DT_FLOAT
        door.float_value = float(sensors.door_sensor)

    return payload.SerializeToString()


async def main() -> None:
    server = Server()
    await server.init()
    server.set_endpoint(OPC_ENDPOINT)
    server.set_server_name("SCADA Sensor Simulator")

    uri = "http://expanso.demo/scada"
    idx = await server.register_namespace(uri)

    objects = server.nodes.objects
    sensor_obj = await objects.add_object(idx, "SensorData")

    temp_var = await sensor_obj.add_variable(idx, "Temperature", ua.Variant(22.0, ua.VariantType.Float))
    pressure_var = await sensor_obj.add_variable(idx, "Pressure", ua.Variant(1.8, ua.VariantType.Float))
    door_var = await sensor_obj.add_variable(idx, "DoorSensor", ua.Variant(0.0, ua.VariantType.Float))

    for node in (temp_var, pressure_var, door_var):
        await node.set_writable()

    sensors = Sensors()
    mqtt_client = None
    if ENABLE_DIRECT_SPARKPLUG:
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="scada-sparkplug-pub")
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
        mqtt_client.loop_start()

    async with server:
        while True:
            sensors.temperature += random.uniform(-0.2, 0.2)
            sensors.temperature = clamp(sensors.temperature, 15.0, 90.0)

            if random.random() < 0.01:
                sensors.temperature = random.choice([999.0, -50.0])

            # Slow pressure drift with bounded sinusoidal behavior.
            sensors.pressure += (math.sin(time.time() / 15.0) * 0.01) + random.uniform(-0.01, 0.01)
            sensors.pressure = clamp(sensors.pressure, 0.5, 5.0)

            if random.random() < 0.08:
                sensors.door_sensor = 1.0 - float(bool(sensors.door_sensor))

            bad_door = None
            if random.random() < 0.02:
                bad_door = random.choice([1.5, 2.3])

            await temp_var.write_value(ua.Variant(float(sensors.temperature), ua.VariantType.Float))
            await pressure_var.write_value(ua.Variant(float(sensors.pressure), ua.VariantType.Float))
            if bad_door is None:
                await door_var.write_value(ua.Variant(float(sensors.door_sensor), ua.VariantType.Float))
            else:
                await door_var.write_value(ua.Variant(float(bad_door), ua.VariantType.Float))
                sensors.door_sensor = float(bad_door)

            if mqtt_client is not None:
                payload = build_payload(sensors)
                mqtt_client.publish(SPARKPLUG_TOPIC, payload, qos=0, retain=False)
                if ENABLE_PARALLEL_FEED:
                    mqtt_client.publish(PARALLEL_TOPIC, payload, qos=0, retain=False)

            await asyncio.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
