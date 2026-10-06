#!/bin/sh
set -eu

export SOURCE_MQTT_PASSWORD
SOURCE_MQTT_PASSWORD=$(tr -d '\n' < /run/secrets/source-password)
export HIVEMQ_PASSWORD
HIVEMQ_PASSWORD=$(tr -d '\n' < /run/secrets/hivemq-password)

exec expanso-edge run \
  --local \
  --no-watch \
  --name scada-hivemq-local \
  --api-listen 0.0.0.0:9010 \
  --data-dir /var/lib/expanso \
  --log-format console \
  --log-level info
