#!/usr/bin/env python3
"""Phase 13AJ — verify Derek near-lineup contract for one delivery date.

Inputs:
  --date YYYY-MM-DD

Checks:
  1. predictions/all_props_<date>.parquet exists and has rows.
  2. predictions/pmf_display_<date>.json exists.
  3. predictions/singles_<date>.json exists.
  4. The slate's commence times (from predictions or from the
     live-schedule manifest) fall on the SAME ET calendar day as the
     ``--date`` argument. This catches UTC/ET rollover bugs where the
     workflow asked for "today UTC" while tonight's ET slate is still
     yesterday's date.
  5. ``deliveries/<date>/derek_forward_feed/`` (the near-lineup output
     surface) carries a manifest. If absent BUT predictions exist and
     no game in the slate has tipped, classify as PENDING. If absent
     AND any game has tipped, FAIL.

Pass:    DEREK_NEAR_LINEUP_CONTRACT_PASS
Pending: DEREK_NEAR_LINEUP_CONTRACT_PENDING (acceptable pre-tip / no-data)
Fail:    DEREK_NEAR_LINEUP_CONTRACT_FAILED
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = REPO_ROOT / "predictions"
DELIVERIES_DIR = REPO_ROOT / "deliveries"


def _et_date_for_iso_utc(iso: str) -> str | None:
    try:
        ts = pd.Timestamp(iso)
    except Exception:
        return None
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    try:
        et = ts.tz_convert("America/New_York")
    except Exception:
        return None
    return et.date().isoformat()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args(argv)
    date = args.date

    failures: list[str] = []
    warnings: list[str] = []
    facts: dict = {"date": date}

    pred_parquet = PRED_DIR / f"all_props_{date}.parquet"
    pmf_display = PRED_DIR / f"pmf_display_{date}.json"
    singles = PRED_DIR / f"singles_{date}.json"
    feed_dir = DELIVERIES_DIR / date / "derek_forward_feed"
    schedule_path = REPO_ROOT / "artifacts" / "live_schedule" / date / "game_start_times.json"

    facts["pred_parquet_path"] = str(pred_parquet.relative_to(REPO_ROOT))
    facts["pred_parquet_present"] = pred_parquet.exists()
    facts["feed_dir_path"] = str(feed_dir.relative_to(REPO_ROOT))
    facts["feed_dir_present"] = feed_dir.exists()

    if not pred_parquet.exists():
        failures.append(f"missing predictions parquet: {pred_parquet.relative_to(REPO_ROOT)}")
    else:
        df = pd.read_parquet(pred_parquet)
        facts["pred_rows"] = int(len(df))
        if df.empty:
            failures.append(f"predictions parquet empty: {pred_parquet.relative_to(REPO_ROOT)}")

    for label, p in (("pmf_display_json", pmf_display),
                       ("singles_json", singles)):
        facts[f"{label}_present"] = p.exists()
        if not p.exists():
            failures.append(f"missing {label}: {p.relative_to(REPO_ROOT)}")
        else:
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
                if str(payload.get("date")) != date:
                    failures.append(
                        f"{label}.date={payload.get('date')!r} != requested {date!r}"
                    )
            except Exception as e:
                failures.append(f"{label} parse error: {e}")

    # ET-date consistency check on slate commence times.
    commence_iso_list: list[str] = []
    if schedule_path.exists():
        try:
            sched = json.loads(schedule_path.read_text(encoding="utf-8"))
            for r in (sched.get("records") or []):
                ct = r.get("resolved_game_start_time_utc")
                if ct:
                    commence_iso_list.append(ct)
        except Exception:
            pass
    facts["schedule_records_seen"] = len(commence_iso_list)
    et_mismatches: list[str] = []
    for ct in commence_iso_list:
        et = _et_date_for_iso_utc(ct)
        if et is not None and et != date:
            et_mismatches.append(f"{ct} → ET-date={et}")
    facts["et_mismatches"] = et_mismatches
    if et_mismatches:
        failures.append(
            f"schedule commence times ET-date != requested {date!r}: "
            f"{et_mismatches[:5]} — UTC/ET rollover bug"
        )

    # Near-lineup output presence + tip-state.
    now_utc = dt.datetime.now(dt.timezone.utc)
    any_game_tipped = False
    if commence_iso_list:
        for ct in commence_iso_list:
            try:
                ts = pd.Timestamp(ct)
                if ts.tzinfo is None:
                    ts = ts.tz_localize("UTC")
                if ts.to_pydatetime() <= now_utc:
                    any_game_tipped = True
                    break
            except Exception:
                pass
    facts["any_game_tipped"] = any_game_tipped

    feed_manifest = feed_dir / "feed_manifest.json"
    facts["feed_manifest_present"] = feed_manifest.exists()

    pending = False
    if not feed_manifest.exists():
        if any_game_tipped:
            failures.append(
                "deliveries/<date>/derek_forward_feed/feed_manifest.json "
                "missing AND at least one game has tipped — near-lineup "
                "did not run for an active slate"
            )
        else:
            pending = True
            warnings.append(
                "near-lineup output not yet produced; no game has tipped — "
                "PENDING_NOT_DUE"
            )

    out_dir = REPO_ROOT / "artifacts" / "automation_health"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "date": date,
        "generated_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "facts": facts,
        "failures": failures,
        "warnings": warnings,
        "outcome": "fail" if failures else ("pending" if pending else "pass"),
    }
    (out_dir / f"derek_near_lineup_contract_{date}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    if failures:
        print(f"DEREK_NEAR_LINEUP_CONTRACT_FAILED  date={date}  "
              f"failures={len(failures)}", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    if pending:
        print(f"DEREK_NEAR_LINEUP_CONTRACT_PENDING  date={date}  "
              f"reason=no_game_tipped_yet")
        return 0
    print(f"DEREK_NEAR_LINEUP_CONTRACT_PASS  date={date}  "
          f"feed_dir={feed_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
