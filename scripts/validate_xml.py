#!/usr/bin/env python3
"""Parse the supplied XML files with the Python standard library."""

import sys
from pathlib import Path
from xml.etree import ElementTree


def main(paths: list[str]) -> int:
    if not paths:
        print("usage: validate_xml.py FILE [FILE ...]", file=sys.stderr)
        return 2

    failed = False
    for value in paths:
        path = Path(value)
        try:
            ElementTree.parse(path)
        except (OSError, ElementTree.ParseError) as error:
            print(f"{path}: {error}", file=sys.stderr)
            failed = True

    if failed:
        return 1

    print(f"validated {len(paths)} XML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
