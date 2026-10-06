#!/usr/bin/env python3
"""Compile the shipped schema and decode every bounded fixture payload."""

from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path

from grpc_tools import protoc


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / ".runtime/proto-check"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result = protoc.main(
        [
            "grpc_tools.protoc",
            f"-I{ROOT}",
            f"--python_out={OUTPUT}",
            str(ROOT / "sparkplug_b.proto"),
        ]
    )
    assert result == 0

    module_path = OUTPUT / "sparkplug_b_pb2.py"
    spec = importlib.util.spec_from_file_location("sparkplug_b_pb2", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    fixture = ROOT / "fixtures/input.ndjson"
    for line in fixture.read_text().splitlines():
        record = json.loads(line)
        payload = module.Payload()
        payload.ParseFromString(base64.b64decode(record["payload_base64"]))
        assert payload.seq == record["seq"]
        assert [metric.name for metric in payload.metrics] == [
            metric["name"] for metric in record["metrics"]
        ]
    print("Sparkplug B schema decoded all fixture payloads")


if __name__ == "__main__":
    main()
