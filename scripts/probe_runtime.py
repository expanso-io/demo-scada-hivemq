#!/usr/bin/env python3
"""Read back the secured runtime acceptance produced by run-demo.sh."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    path = Path(".runtime/results/acceptance.json")
    report = json.loads(path.read_text())
    assert report["result"] == "pass"
    assert report["authenticated_tls"] == "accepted"
    assert report["anonymous_tls"] == "rejected"
    assert report["outputs"] == {
        "archive": 2,
        "metrics": 2,
        "primary": 2,
        "quarantine": 1,
    }
    assert report["primary_metric_names"][1] == ["DoorSensor"]
    assert report["persistence"] == "retained message survived broker recreation"
    print("secured MQTT wire probe passed")


if __name__ == "__main__":
    main()
