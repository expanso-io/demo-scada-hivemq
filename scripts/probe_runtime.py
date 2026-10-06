#!/usr/bin/env python3
"""Read back the secured runtime acceptance produced by run-demo.sh."""

from __future__ import annotations

import json
import time
from pathlib import Path


def wait_for_report(path: Path, timeout_seconds: float = 45.0) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    last_state = "acceptance report not written"

    while time.monotonic() < deadline:
        try:
            report = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            last_state = str(error)
        else:
            if not isinstance(report, dict):
                last_state = "acceptance report is not a JSON object"
                time.sleep(0.25)
                continue
            last_state = str(report.get("persistence", "persistence proof missing"))
            if last_state == "retained message survived broker recreation":
                return report
        time.sleep(0.25)

    raise TimeoutError(f"secured runtime acceptance timed out: {last_state}")


def main() -> None:
    path = Path(".runtime/results/acceptance.json")
    report = wait_for_report(path)
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
