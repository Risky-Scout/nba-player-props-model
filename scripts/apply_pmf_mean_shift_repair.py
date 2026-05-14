#!/usr/bin/env python3
"""Apply PMF mean-shift repair from a manifest to a JSON PMF (stdin/stdout or CLI)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO_ROOT / "src"))

from build_event_market_loss_rows import _normalize_pmf, _parse_pmf_value  # noqa: E402
from nba_props_model.calibration.pmf_mean_shift_repair import (  # noqa: E402
    apply_mean_shift_manifest_to_pmf,
    load_mean_shift_manifest,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, help="pmf_mean_shift_repair_*.json")
    ap.add_argument("--stat", required=True)
    ap.add_argument("--role-bucket", required=True)
    ap.add_argument(
        "--pmf-json",
        default=None,
        help='Atom PMF JSON, e.g. {"0":0.2,"1":0.8}. If omitted, read stdin.',
    )
    args = ap.parse_args()
    mp = Path(args.manifest)
    if not mp.is_absolute():
        mp = REPO_ROOT / mp
    if not mp.is_file():
        print(f"FATAL: manifest not found {mp}", file=sys.stderr)
        return 2
    man = load_mean_shift_manifest(mp)
    raw_s = args.pmf_json
    if raw_s is None:
        raw_s = sys.stdin.read()
    pmf_raw = _normalize_pmf(_parse_pmf_value(json.loads(raw_s)))
    out, _scope, _met, applied, rr = apply_mean_shift_manifest_to_pmf(
        pmf_raw,
        stat=str(args.stat).lower(),
        role_bucket=str(args.role_bucket).lower(),
        manifest=man,
    )
    print(
        json.dumps(
            {
                "pmf_out": {str(k): float(v) for k, v in (out or {}).items()},
                "applied": applied,
                "rollback_reason": rr,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
