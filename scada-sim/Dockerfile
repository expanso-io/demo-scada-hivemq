FROM python:3.12-slim

WORKDIR /app
COPY scada-sim/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY sparkplug_b.proto /app/sparkplug_b.proto
RUN python -m grpc_tools.protoc -I/app --python_out=/app /app/sparkplug_b.proto
COPY scada-sim/app.py /app/app.py

CMD ["python", "/app/app.py"]
