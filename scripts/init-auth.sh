#!/bin/sh
set -eu

umask 077
runtime_dir=/run/demo-secrets
mkdir -p "$runtime_dir"
chmod 0600 "$runtime_dir"/* 2>/dev/null || true

make_password() {
  dd if=/dev/urandom bs=24 count=1 2>/dev/null | base64 | tr -d '\n'
}

if [ ! -s "$runtime_dir/source-password" ]; then
  make_password > "$runtime_dir/source-password"
fi
if [ ! -s "$runtime_dir/hivemq-password" ]; then
  make_password > "$runtime_dir/hivemq-password"
fi
if [ ! -s "$runtime_dir/hivemq-observer-password" ]; then
  make_password > "$runtime_dir/hivemq-observer-password"
fi

source_password=$(tr -d '\n' < "$runtime_dir/source-password")
hivemq_password=$(tr -d '\n' < "$runtime_dir/hivemq-password")
observer_password=$(tr -d '\n' < "$runtime_dir/hivemq-observer-password")

printf 'source-publisher:%s\n' "$source_password" \
  > "$runtime_dir/source-passwords"
mosquitto_passwd -U "$runtime_dir/source-passwords"

{
  printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?>'
  printf '%s\n' '<file-rbac>'
  printf '%s\n' '  <users>'
  printf '%s\n' '    <user>'
  printf '%s\n' '      <name>expanso-edge</name>'
  printf '      <password>%s</password>\n' "$hivemq_password"
  printf '%s\n' '      <roles><id>edge-writer</id></roles>'
  printf '%s\n' '    </user>'
  printf '%s\n' '    <user>'
  printf '%s\n' '      <name>fixture-observer</name>'
  printf '      <password>%s</password>\n' "$observer_password"
  printf '%s\n' '      <roles><id>observer</id></roles>'
  printf '%s\n' '    </user>'
  printf '%s\n' '  </users>'
  printf '%s\n' '  <roles>'
  printf '%s\n' '    <role>'
  printf '%s\n' '      <id>edge-writer</id>'
  printf '%s\n' '      <permissions>'
  for topic in 'spBv1.0/#' 'archive/#' 'metrics/#' 'quarantine/#'; do
    printf '%s\n' '        <permission>'
    printf '          <topic>%s</topic>\n' "$topic"
    printf '%s\n' '          <activity>PUBLISH</activity>'
    printf '%s\n' '        </permission>'
  done
  printf '%s\n' '      </permissions>'
  printf '%s\n' '    </role>'
  printf '%s\n' '    <role>'
  printf '%s\n' '      <id>observer</id>'
  printf '%s\n' '      <permissions>'
  printf '%s\n' '        <permission>'
  printf '%s\n' '          <topic>#</topic>'
  printf '%s\n' '          <activity>SUBSCRIBE</activity>'
  printf '%s\n' '        </permission>'
  printf '%s\n' '        <permission>'
  printf '%s\n' '          <topic>proof/persistence</topic>'
  printf '%s\n' '          <activity>PUBLISH</activity>'
  printf '%s\n' '        </permission>'
  printf '%s\n' '      </permissions>'
  printf '%s\n' '    </role>'
  printf '%s\n' '  </roles>'
  printf '%s\n' '</file-rbac>'
} > "$runtime_dir/hivemq-credentials.xml"

chmod 0444 "$runtime_dir"/*
