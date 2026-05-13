#!/usr/bin/env python3
"""Cross-check OddsAPI/BDL prop coverage using existing event-market audit JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates-file", type=Path, required=True)
    args = ap.parse_args()

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from event_market_date_selection import (  # noqa: WPS433
        dates_fingerprint,
        load_dates_from_inventory_csv,
    )

    inv = args.dates_file.resolve()
    if not inv.is_file():
        print(f"MISSING {inv}", file=sys.stderr)
        return 2
    dates, _df = load_dates_from_inventory_csv(inv, eligible_only=True)
    label = f"dates_{dates_fingerprint(dates)}"
    cov_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_coverage_{label}" / "coverage_by_stat.json"
    if not cov_path.is_file():
        print(f"ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_FAIL missing {cov_path}", file=sys.stderr)
        return 1

    data = json.loads(cov_path.read_text(encoding="utf-8"))
    rows = data.get("stats") or []
    bad = []
    for row in rows:
        st = str(row.get("stat", "")).lower()
        reason = str(row.get("final_missing_reason") or "")
        if reason not in ("covered", "no_offered_market", "insufficient_scored_rows", "processed_parser_dropped_market", "not_requested_from_odds_api", "event_market_join_failed", "no_actuals", "no_model_pmfs"):
            bad.append((st, reason))
    if bad:
        print("ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_FAIL", file=sys.stderr)
        for b in bad[:40]:
            print(f"  {b}", file=sys.stderr)
        return 1
    print("ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
