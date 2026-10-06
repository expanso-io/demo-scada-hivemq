FROM alpine:3.22.2@sha256:4b7ce07002c69e8f3d704a9c5d6fd3053be500b7f1c69fc0d80990c2ad8dd412 AS extension

ADD --checksum=sha256:4089d09e5d2b6621a07aa86032230dce5aefbcc37130ef5c714fb6fa7185e3e6 \
  https://github.com/hivemq/hivemq-file-rbac-extension/releases/download/4.6.18/hivemq-file-rbac-extension-4.6.18.zip \
  /tmp/rbac.zip
RUN mkdir -p /out \
  && unzip -q /tmp/rbac.zip -d /out

FROM hivemq/hivemq-ce:2025.5@sha256:7ae39e84654a41ced6e946dd84f131d508bc2b862ec96265b7f23d241db214da

USER root
RUN rm -rf /opt/hivemq/extensions/hivemq-allow-all-extension
COPY --from=extension --chown=10000:0 \
  /out/hivemq-file-rbac-extension \
  /opt/hivemq/extensions/hivemq-file-rbac-extension
COPY --chown=10000:0 hivemq/extension-config.xml \
  /opt/hivemq/extensions/hivemq-file-rbac-extension/conf/config.xml
RUN rm -f \
  /opt/hivemq/extensions/hivemq-file-rbac-extension/conf/credentials.xml \
  && ln -s /run/demo-secrets/hivemq-credentials.xml \
  /opt/hivemq/extensions/hivemq-file-rbac-extension/conf/credentials.xml
USER 10000:0
