#!/bin/bash
set -euo pipefail

runtime_dir=/run/hivemq-tls
keystore="$runtime_dir/server.jks"
certificate="$runtime_dir/ca.crt"

mkdir -p "$runtime_dir"
if [[ ! -s "$keystore" || ! -s "$certificate" ]]; then
  rm -f "$keystore" "$certificate"
  keytool -genkeypair \
    -alias mqtt-broker \
    -keyalg RSA \
    -keysize 3072 \
    -validity 30 \
    -dname 'CN=mqtt-broker,OU=Demo,O=Expanso,L=Seattle,ST=WA,C=US' \
    -ext 'SAN=dns:mqtt-broker,dns:localhost,ip:127.0.0.1' \
    -keystore "$keystore" \
    -storepass changeit \
    -keypass changeit \
    -noprompt
  keytool -exportcert \
    -alias mqtt-broker \
    -keystore "$keystore" \
    -storepass changeit \
    -rfc \
    -file "$certificate"
fi

chmod 0444 "$keystore" "$certificate"
