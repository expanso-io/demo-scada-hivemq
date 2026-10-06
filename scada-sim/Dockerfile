FROM ghcr.io/astral-sh/uv:0.8.22@sha256:9874eb7afe5ca16c363fe80b294fe700e460df29a55532bbfea234a0f12eddb1 AS uv

FROM python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY scada-sim/requirements.txt ./requirements.txt
RUN uv venv /opt/venv \
  && uv pip install \
  --python /opt/venv/bin/python \
  --no-cache \
  --requirement requirements.txt

ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV=/opt/venv

COPY sparkplug_b.proto /app/sparkplug_b.proto
RUN uv run \
  --active \
  --no-sync \
  python -m grpc_tools.protoc \
  -I/app \
  --python_out=/app \
  /app/sparkplug_b.proto
COPY scada-sim/app.py /app/app.py

USER 65532:65532
