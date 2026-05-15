#!/usr/bin/env python3
"""Cross-check OddsAPI/BDL prop coverage using event-market audit JSON.

Reads ``artifacts/model_diagnostics/event_market_coverage_{label}/coverage_by_stat.json``
produced by ``audit_event_market_coverage_by_stat.py``.

When using ``--date`` / ``--start-date``/``--end-date``, eligible dates are taken from
the inventory CSV (default: ``artifacts/model_diagnostics/event_market_backtest_date_inventory.csv``).
If the coverage JSON is missing and ``--ensure-audit`` is passed, runs the audit subprocess
for a filtered temporary inventory so a one-off ``--date`` check is self-contained.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = (
    REPO_ROOT / "artifacts" / "model_diagnostics" / "event_market_backtest_date_inventory.csv"
)


def _inventory_dates_in_range(
    inv: Path,
    *,
    start: str | None,
    end: str | None,
    single: str | None,
    eligible_only: bool,
) -> list[str]:
    df = pd.read_csv(inv)
    if "date" not in df.columns:
        print(f"ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_FAIL missing 'date' in {inv}", file=sys.stderr)
        raise SystemExit(2)
    df = df.copy()
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    if eligible_only and "eligible_for_event_market_backtest" in df.columns:
        ev = df["eligible_for_event_market_backtest"]
        if ev.dtype == object:
            ev = ev.astype(str).str.lower().isin(("1", "true", "t", "yes"))
        df = df.loc[ev == True]  # noqa: E712
    if single:
        df = df[df["date"] == single]
    elif start and end:
        df = df[(df["date"] >= start) & (df["date"] <= end)]
    return sorted(df["date"].dropna().unique().tolist())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dates-file",
        type=Path,
        default=None,
        help="Inventory CSV (default: artifacts/model_diagnostics/event_market_backtest_date_inventory.csv)",
    )
    ap.add_argument("--date", default=None, help="Single slate date (YYYY-MM-DD); exclusive with range/dates-file mode")
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument(
        "--snapshot-substr",
        default="auto",
        help="Passed through to audit when --ensure-audit runs (inventory-driven audits already encode choice).",
    )
    ap.add_argument(
        "--eligible-only",
        action="store_true",
        default=True,
        help="When resolving dates from inventory, keep only eligible_for_event_market_backtest rows (default: true).",
    )
    ap.add_argument(
        "--include-ineligible",
        action="store_true",
        help="If set, use all dates in range from inventory without eligible filter.",
    )
    ap.add_argument(
        "--ensure-audit",
        action="store_true",
        help="If coverage JSON is missing, run audit_event_market_coverage_by_stat.py on a filtered temp inventory.",
    )
    ap.add_argument(
        "--print-tov-diagnostics",
        action="store_true",
        help="Print per-date TOV-related inventory fields (raw/processed keys) to stdout.",
    )
    args = ap.parse_args()

    if args.date and (args.start_date or args.end_date):
        print("FATAL: use either --date or --start-date/--end-date, not both", file=sys.stderr)
        return 2
    if (args.start_date or args.end_date) and not (args.start_date and args.end_date):
        print("FATAL: --start-date and --end-date required together", file=sys.stderr)
        return 2

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from event_market_date_selection import (  # noqa: WPS433
        dates_fingerprint,
        dates_label_from_fingerprint,
    )

    inv_path = (args.dates_file or DEFAULT_INVENTORY).resolve()
    if not inv_path.is_file():
        print(f"MISSING_INVENTORY {inv_path}", file=sys.stderr)
        return 2

    eligible_only = not args.include_ineligible

    if args.date or args.start_date:
        dates_used = _inventory_dates_in_range(
            inv_path,
            start=args.start_date,
            end=args.end_date,
            single=args.date,
            eligible_only=eligible_only,
        )
        if not dates_used:
            # Slate-date callers (e.g. daily_pmf_delivery.yml) invoke this with
            # --date <today>. The inventory only marks a date eligible AFTER
            # games are played and actuals are joined; today's slate is therefore
            # structurally absent until next-day scoring catches up. Treat
            # single-date queries with no eligible inventory row as an audit
            # SKIP rather than a delivery-blocking failure. Range queries still
            # hard-fail when their entire window is empty.
            if args.date and not args.start_date:
                print(
                    f"ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_SKIP "
                    f"date={args.date} reason=not_yet_eligible_in_inventory "
                    f"inventory={inv_path}",
                )
                return 0
            print(
                "ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_FAIL no eligible dates for the requested filter",
                file=sys.stderr,
            )
            return 1
    else:
        from event_market_date_selection import load_dates_from_inventory_csv  # noqa: WPS433

        dates_used, _df = load_dates_from_inventory_csv(
            inv_path,
            eligible_only=eligible_only,
        )
        if not dates_used:
            print("ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_FAIL no dates in inventory", file=sys.stderr)
            return 1

    fp = dates_fingerprint(dates_used)
    label = dates_label_from_fingerprint(fp)
    cov_path = (
        REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_coverage_{label}" / "coverage_by_stat.json"
    )

    if args.print_tov_diagnostics:
        full = pd.read_csv(inv_path)
        full["date"] = full["date"].astype(str).str.slice(0, 10)
        sub = full[full["date"].isin(dates_used)]
        print(f"TOV_DIAGNOSTICS label={label} dates={dates_used}")
        for _, row in sub.iterrows():
            d = str(row.get("date", ""))
            print(
                f"  {d}: raw_market_keys_seen={row.get('raw_market_keys_seen')!s} "
                f"processed_market_keys_seen={row.get('processed_market_keys_seen')!s} "
                f"processed_stats_present={row.get('processed_stats_present')!s}"
            )

    if not cov_path.is_file():
        if not args.ensure_audit:
            print(
                f"ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_FAIL missing {cov_path}\n"
                f"  Expected label={label} from dates={dates_used}.\n"
                f"  Run: python3 scripts/audit_event_market_coverage_by_stat.py --dates-file <inventory> "
                f"--snapshot-substr {args.snapshot_substr}\n"
                f"  Or re-run with --ensure-audit.",
                file=sys.stderr,
            )
            return 1
        filt = pd.read_csv(inv_path)
        filt["date"] = filt["date"].astype(str).str.slice(0, 10)
        filt = filt[filt["date"].isin(dates_used)]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp:
            tmp_path = Path(tmp.name)
            filt.to_csv(tmp_path, index=False)
        try:
            rc = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "audit_event_market_coverage_by_stat.py"),
                    "--dates-file",
                    str(tmp_path),
                    "--snapshot-substr",
                    str(args.snapshot_substr),
                ],
                cwd=str(REPO_ROOT),
                check=False,
            )
            if rc.returncode != 0:
                print("ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_FAIL audit subprocess failed", file=sys.stderr)
                return 1
        finally:
            tmp_path.unlink(missing_ok=True)

    if not cov_path.is_file():
        print(f"ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_FAIL still missing {cov_path}", file=sys.stderr)
        return 1

    data = json.loads(cov_path.read_text(encoding="utf-8"))
    rows = data.get("stats") or []
    allowed = {
        "covered",
        "no_offered_market",
        "insufficient_scored_rows",
        "processed_parser_dropped_market",
        "not_requested_from_odds_api",
        "event_market_join_failed",
        "no_actuals",
        "no_model_pmfs",
    }
    bad = []
    for row in rows:
        st = str(row.get("stat", "")).lower()
        reason = str(row.get("final_missing_reason") or "")
        if reason not in allowed:
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
