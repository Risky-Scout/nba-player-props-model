#!/usr/bin/env python3
"""Phase 13AD — verify daily prediction outputs are present, fresh, and
internally consistent.

Required files:
  predictions/all_props_<date>.parquet
  predictions/singles_<date>.json
  predictions/pmf_display_<date>.json
  predictions/nba_props_today.json

Checks:
  - all four files exist;
  - dates inside JSON files match the requested date;
  - if slate has props, row counts > 0;
  - if no props / no slate, an explicit ``reason`` field is present;
  - ``predictions/nba_props_today.json`` is not stale — its ``date`` must
    equal the requested date OR the file must contain a no-data ``reason``;
  - parquet has the expected core columns.

Pass:   DAILY_PREDICTION_OUTPUTS_PASS
Fail:   DAILY_PREDICTION_OUTPUTS_FAILED  with the exact reason
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = REPO_ROOT / "predictions"

CORE_PARQUET_COLS = ("player_id", "stat", "line", "model_prob", "pmf")


def _fail(reason: str, date: str) -> int:
    print(f"DAILY_PREDICTION_OUTPUTS_FAILED  date={date}  reason={reason}",
          file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args(argv)
    date = args.date

    parquet = PRED_DIR / f"all_props_{date}.parquet"
    singles = PRED_DIR / f"singles_{date}.json"
    pmf_display = PRED_DIR / f"pmf_display_{date}.json"
    today = PRED_DIR / "nba_props_today.json"

    failures: list[str] = []
    summary: dict = {"date": date, "files": {}}

    # Existence checks.
    for label, path in (
        ("all_props_parquet", parquet),
        ("singles_json", singles),
        ("pmf_display_json", pmf_display),
        ("nba_props_today_json", today),
    ):
        exists = path.exists()
        summary["files"][label] = {
            "path": str(path.relative_to(REPO_ROOT)),
            "exists": exists,
        }
        if not exists:
            failures.append(f"{label} missing at {path.relative_to(REPO_ROOT)}")

    if failures:
        print(f"DAILY_PREDICTION_OUTPUTS_FAILED  date={date}  failures={len(failures)}",
              file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    # Parquet content checks.
    df = pd.read_parquet(parquet)
    parquet_rows = int(len(df))
    summary["files"]["all_props_parquet"]["rows"] = parquet_rows
    summary["files"]["all_props_parquet"]["games"] = int(
        df["game_id"].nunique()) if "game_id" in df.columns else 0

    missing_cols = [c for c in CORE_PARQUET_COLS if c not in df.columns]
    if missing_cols:
        failures.append(
            f"all_props parquet missing core columns: {missing_cols}"
        )

    # Singles JSON.
    sj = json.loads(singles.read_text(encoding="utf-8"))
    if str(sj.get("date")) != date:
        failures.append(
            f"singles json date={sj.get('date')!r} does not match requested {date!r}"
        )
    sj_picks = sj.get("picks", sj.get("singles", []))
    summary["files"]["singles_json"]["count"] = len(sj_picks)
    summary["files"]["singles_json"]["date"] = sj.get("date")

    # PMF display JSON.
    pj = json.loads(pmf_display.read_text(encoding="utf-8"))
    if str(pj.get("date")) != date:
        failures.append(
            f"pmf_display json date={pj.get('date')!r} does not match requested {date!r}"
        )
    pj_props = pj.get("props", [])
    summary["files"]["pmf_display_json"]["count"] = len(pj_props)
    summary["files"]["pmf_display_json"]["date"] = pj.get("date")

    # nba_props_today.json — staleness check.
    tj = json.loads(today.read_text(encoding="utf-8"))
    today_date = str(tj.get("date"))
    today_count = int(tj.get("count", len(tj.get("props", []))))
    today_reason = tj.get("reason")
    summary["files"]["nba_props_today_json"]["date"] = today_date
    summary["files"]["nba_props_today_json"]["count"] = today_count
    summary["files"]["nba_props_today_json"]["reason_present"] = bool(today_reason)

    if today_date != date:
        failures.append(
            f"nba_props_today.json date={today_date!r} is stale; "
            f"expected {date!r}. Run scripts/publish_nba_props_today.py "
            f"--date {date}."
        )

    # Slate consistency: if parquet has rows, today.json should too (or have a reason).
    if parquet_rows > 0 and today_count == 0 and not today_reason:
        failures.append(
            "parquet has rows but nba_props_today.json has count=0 and no "
            "reason — front-end will render blank without explanation."
        )
    if parquet_rows == 0 and not (sj.get("reason") or pj.get("reason") or today_reason):
        failures.append(
            "parquet is empty but no JSON provides a reason; front-end "
            "will render blank without explanation."
        )

    if failures:
        print(f"DAILY_PREDICTION_OUTPUTS_FAILED  date={date}  failures={len(failures)}",
              file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(f"DAILY_PREDICTION_OUTPUTS_PASS  date={date}  "
          f"parquet_rows={parquet_rows}  singles={summary['files']['singles_json']['count']}  "
          f"pmf_display={summary['files']['pmf_display_json']['count']}  "
          f"today_count={today_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
