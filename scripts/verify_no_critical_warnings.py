#!/usr/bin/env python3
"""Fail if critical_warnings.json is non-empty."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()
    p = args.run_dir / "critical_warnings.json"
    if not p.is_file():
        print("NO_CRITICAL_WARNINGS_PASS (no critical_warnings.json)")
        return 0
    data = json.loads(p.read_text(encoding="utf-8"))
    if data:
        print("NO_CRITICAL_WARNINGS_FAIL", file=sys.stderr)
        print(json.dumps(data[:20], indent=2), file=sys.stderr)
        return 1
    print("NO_CRITICAL_WARNINGS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
