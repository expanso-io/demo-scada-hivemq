FROM alpine:3.22.2@sha256:4b7ce07002c69e8f3d704a9c5d6fd3053be500b7f1c69fc0d80990c2ad8dd412

RUN apk add --no-cache libcap=2.78-r0 \
  && cp /bin/busybox /usr/local/bin/busybox \
  && setcap \
    cap_chown,cap_dac_override,cap_fowner=ep \
    /usr/local/bin/busybox

USER 65534:65534
