#!/usr/bin/env python3
"""Check expected morning delivery folder layout for a slate date."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = (
    "canonical_source",
    "wizard_of_odds",
    "pmf_model_review_package",
    "after_game_scoring",
    "derek_forward_feed",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    root = REPO_ROOT / "deliveries" / args.date
    fails: list[str] = []
    if not root.is_dir():
        fails.append(f"missing_delivery_root:{root}")

    for d in REQUIRED_DIRS:
        p = root / d
        if not p.is_dir():
            fails.append(f"missing_dir:{d}")

    woo = root / "wizard_of_odds" / "run_manifest.json"
    if woo.is_file():
        try:
            m = json.loads(woo.read_text(encoding="utf-8"))
            if m.get("market_superiority_claim_allowed") is True:
                fails.append("market_superiority_claim_allowed_true_without_external_verifier")
        except Exception:
            fails.append("invalid_run_manifest_json")

    if fails:
        print("MORNING_DELIVERY_COMPLETENESS_FAIL")
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("MORNING_DELIVERY_COMPLETENESS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
