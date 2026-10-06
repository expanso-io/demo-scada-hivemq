#!/usr/bin/env python3
"""Check that explorer records and acceptance fixtures stay in sync."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    fixture_path = ROOT / "fixtures/input.ndjson"
    expected_path = ROOT / "fixtures/expected.json"
    stages_path = ROOT / "fixtures/stages.json"
    pipeline_path = ROOT / "pipelines/scada-hivemq.yaml"

    records = [json.loads(line) for line in fixture_path.read_text().splitlines()]
    expected = json.loads(expected_path.read_text())
    explorer = json.loads(stages_path.read_text())
    pipeline_lines = pipeline_path.read_text().splitlines()

    assert len(records) == expected["input_records"]
    assert explorer["fixture"] == "fixtures/input.ndjson"
    assert explorer["pipeline"] == "pipelines/scada-hivemq.yaml"
    assert len(explorer["stages"]) == 6
    assert len({stage["id"] for stage in explorer["stages"]}) == 6

    for stage in explorer["stages"]:
        start, end = stage["pipeline_lines"]
        assert 1 <= start <= end <= len(pipeline_lines), stage["id"]
        assert stage["input"], stage["id"]
        assert stage["output"], stage["id"]

    assert expected["primary"][1]["metric_names"] == ["DoorSensor"]
    print("fixture and explorer contracts are consistent")


if __name__ == "__main__":
    main()
