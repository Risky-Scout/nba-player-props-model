#!/usr/bin/env python3
"""Apply event-neutral probability scale repair (library wrapper / smoke CLI)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.calibration.event_neutral_probability_scale import (  # noqa: E402
    apply_manifest_to_probability,
    load_probability_scale_manifest,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply manifest to a single (p, stat, role).")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--p", type=float, required=True)
    ap.add_argument("--stat", required=True)
    ap.add_argument("--role-bucket", required=True)
    args = ap.parse_args()
    man = load_probability_scale_manifest(Path(args.manifest))
    p2, scope, method, ok = apply_manifest_to_probability(
        args.p, stat=args.stat, role_bucket=args.role_bucket, manifest=man
    )
    print(json.dumps({"p_out": p2, "scope": scope, "method": method, "applied": ok}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
