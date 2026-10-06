#!/bin/sh
set -eu

export MQTT_PASSWORD
MQTT_PASSWORD=$(tr -d '\n' < /run/secrets/source-password)
exec uv run --active --no-sync /app/app.py
