#!/usr/bin/env python3
"""Phase 13AH — verify Wizard of Odds snapshot outputs for a date.

Inputs:
  --date YYYY-MM-DD

Required structure:
  predictions/woo_snapshots/<date>/morning/slate/nba_props_today.json
  predictions/woo_snapshots/<date>/t_minus_25/<game_id>/nba_props_today.json
  predictions/woo_snapshots/<date>/close_lock/<game_id>/nba_props_today.json

Required schema per file:
  date, snapshot_type, snapshot_scope, generated_at, count, games,
  props, upstream_statuses, status (with optional reason when count=0)

Pass / fail discipline:
  - Morning is required: WOO_MORNING_OUTPUTS_FAILED if missing or
    fields broken; WOO_MORNING_OUTPUTS_PASS otherwise.
  - For t_minus_25 and close_lock the verifier reads the predictions
    parquet to enumerate today's games. For each game:
      - If the snapshot file exists and parses, count it as present.
      - If the snapshot file is absent and the game has not yet
        tipped (or the predictions parquet has no commence_time),
        the snapshot is PENDING — the workflow should produce it at
        T-25 / T-5 to tip. PENDING does NOT pass; it WARN-s.
      - If the snapshot is absent and the game has already tipped,
        that is a FAIL (silent missed near-tip snapshot).

Pass lines (one per snapshot type):
  WOO_MORNING_OUTPUTS_PASS
  WOO_T_MINUS_25_OUTPUTS_PASS  (only when every game has a snapshot)
  WOO_CLOSE_LOCK_OUTPUTS_PASS  (only when every game has a snapshot)

Warn lines:
  WOO_T_MINUS_25_OUTPUTS_PENDING  (some games have not yet tipped)
  WOO_CLOSE_LOCK_OUTPUTS_PENDING

Fail lines:
  WOO_MORNING_OUTPUTS_FAILED
  WOO_T_MINUS_25_OUTPUTS_FAILED
  WOO_CLOSE_LOCK_OUTPUTS_FAILED

Exit code:
  0 — every snapshot type either PASS or PENDING with no FAIL.
  1 — any snapshot type FAILED.
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
WOO_SNAP_ROOT = PRED_DIR / "woo_snapshots"

REQUIRED_TOP_FIELDS = (
    "date", "snapshot_type", "snapshot_scope", "generated_at",
    "count", "games", "props", "upstream_statuses", "status",
)


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _validate_snapshot_payload(path: Path, expected_type: str,
                                  expected_scope: str | None) -> list[str]:
    failures: list[str] = []
    if not path.exists():
        failures.append(f"missing {path.relative_to(REPO_ROOT)}")
        return failures
    payload = _read_json(path)
    if payload is None:
        failures.append(f"parse error: {path.relative_to(REPO_ROOT)}")
        return failures
    for field in REQUIRED_TOP_FIELDS:
        if field not in payload:
            failures.append(f"{path.relative_to(REPO_ROOT)}: missing field '{field}'")
    if payload.get("snapshot_type") != expected_type:
        failures.append(
            f"{path.relative_to(REPO_ROOT)}: snapshot_type="
            f"{payload.get('snapshot_type')!r} expected {expected_type!r}"
        )
    if expected_scope and payload.get("snapshot_scope") != expected_scope:
        failures.append(
            f"{path.relative_to(REPO_ROOT)}: snapshot_scope="
            f"{payload.get('snapshot_scope')!r} expected {expected_scope!r}"
        )
    if int(payload.get("count", 0)) == 0 and not payload.get("reason"):
        failures.append(
            f"{path.relative_to(REPO_ROOT)}: count=0 with no reason — "
            "front-end will render blank without explanation"
        )
    return failures


def _games_for_date(date: str) -> pd.DataFrame:
    parquet = PRED_DIR / f"all_props_{date}.parquet"
    if not parquet.exists():
        return pd.DataFrame()
    cols = ["game_id", "game"]
    optional = ("game_start_time", "commence_time")
    df = pd.read_parquet(parquet)
    keep = [c for c in cols + list(optional) if c in df.columns]
    games = df[keep].drop_duplicates(subset=["game_id"]).reset_index(drop=True)
    return games


def _has_tipped(now_utc: dt.datetime, commence_time) -> bool | None:
    if commence_time is None or pd.isna(commence_time):
        return None
    if isinstance(commence_time, str):
        try:
            ts = pd.Timestamp(commence_time)
        except Exception:
            return None
    else:
        try:
            ts = pd.Timestamp(commence_time)
        except Exception:
            return None
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.to_pydatetime() <= now_utc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args(argv)
    date = args.date
    now_utc = dt.datetime.now(dt.timezone.utc)

    overall_exit = 0

    # 1. Morning
    morning_path = WOO_SNAP_ROOT / date / "morning" / "slate" / "nba_props_today.json"
    morning_failures = _validate_snapshot_payload(morning_path, "morning", "slate")
    if morning_failures:
        overall_exit = 1
        print(f"WOO_MORNING_OUTPUTS_FAILED  date={date}  "
              f"failures={len(morning_failures)}", file=sys.stderr)
        for f in morning_failures:
            print(f"  - {f}", file=sys.stderr)
    else:
        print(f"WOO_MORNING_OUTPUTS_PASS  date={date}  "
              f"path={morning_path.relative_to(REPO_ROOT)}")

    # 2. & 3. Per-game near-tip snapshots
    games = _games_for_date(date)
    n_games = int(len(games))

    for snap_type in ("t_minus_25", "close_lock"):
        if n_games == 0:
            print(f"WOO_{snap_type.upper()}_OUTPUTS_PENDING  date={date}  "
                  f"reason=no_predictions_parquet_for_date_yet")
            continue

        per_game_failures: list[str] = []
        per_game_pending: list[str] = []
        per_game_present: list[str] = []
        for _, g in games.iterrows():
            gid = str(int(g["game_id"]))
            scope_path = WOO_SNAP_ROOT / date / snap_type / gid / "nba_props_today.json"
            if scope_path.exists():
                fails = _validate_snapshot_payload(scope_path, snap_type, gid)
                if fails:
                    per_game_failures.extend(fails)
                else:
                    per_game_present.append(gid)
            else:
                # Determine pending vs failed based on tip status.
                commence_time = (g.get("game_start_time") or
                                  g.get("commence_time"))
                tipped = _has_tipped(now_utc, commence_time)
                if tipped is True:
                    per_game_failures.append(
                        f"{snap_type} snapshot missing for game_id={gid} "
                        f"and game has already tipped (commence_time="
                        f"{commence_time!r}); silent missed near-tip "
                        "snapshot is a hard fail"
                    )
                else:
                    # Either tip is in the future or commence_time is unknown.
                    per_game_pending.append(gid)

        if per_game_failures:
            overall_exit = 1
            print(f"WOO_{snap_type.upper()}_OUTPUTS_FAILED  date={date}  "
                  f"games_total={n_games}  "
                  f"games_present={len(per_game_present)}  "
                  f"failures={len(per_game_failures)}", file=sys.stderr)
            for f in per_game_failures:
                print(f"  - {f}", file=sys.stderr)
        elif per_game_pending:
            # Some or all games not yet tipped — pending state, exit 0.
            print(f"WOO_{snap_type.upper()}_OUTPUTS_PENDING  date={date}  "
                  f"games_total={n_games}  "
                  f"games_present={len(per_game_present)}  "
                  f"games_pending={len(per_game_pending)}")
        else:
            print(f"WOO_{snap_type.upper()}_OUTPUTS_PASS  date={date}  "
                  f"games_total={n_games}  "
                  f"games_present={len(per_game_present)}")

    return overall_exit


if __name__ == "__main__":
    sys.exit(main())
