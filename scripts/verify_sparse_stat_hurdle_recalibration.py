#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "artifacts" / "models" / "sparse_hurdle_offsets.json"


def main() -> int:
    if not OUT.exists():
        print("SPARSE_HURDLE_VERIFY_FAIL missing offsets", file=sys.stderr)
        return 1
    j = json.loads(OUT.read_text())
    assert "offsets" in j
    print("SPARSE_HURDLE_VERIFY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
