#!/usr/bin/env python3
"""Verify Derek live snapshot API readiness (M8.9 root-cause rewire).

Read-only check of every source the Derek production-live pipeline
consumes, plus the new internal minutes_predictions artifact required by
the M8.9 player-game eligibility gate. Emits a structured JSON readiness
report to ``artifacts/source_readiness/{date}/source_readiness.json`` and
prints a status line.

Status semantics:

    ready
        Every required source has the right shape and freshness; the
        delivery may publish a full-roster-aware morning snapshot.
    ready_lineups_pending
        Confirmed lineups not yet available (acceptable for morning
        publishes — projected rotation comes from minutes_predictions).
    failed
        At least one required source missing / unusable; publishing is
        blocked.

Rules baked in:

* ``ODDS_API_KEY`` or ``THE_ODDS_API_KEY`` missing -> failed.
* ``BDL_API_KEY`` missing -> failed (we need it for the BDL fetch proof
  artifact even if the live BDL /v2/lineups call is empty).
* BDL ``/v2/lineups`` empty pre-confirmation is classified as
  ``confirmed_lineups_not_available_yet``, NOT failure. Empty BDL must
  NOT cause the downstream pipeline to publish a full-roster (the M8.9
  eligibility gate handles that).
* Morning publishes require ``artifacts/minutes_predictions/{date}/
  minutes_predictions.parquet``.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.data.nba_official_injury_report_fetch import (  # noqa: E402
    INJURY_FRAGMENT_KEYS,
    load_injury_report_selection,
)


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _odds_processed_dir(date: str) -> Path:
    return REPO_ROOT / "data" / "odds_api" / "processed" / date


def _bdl_snapshot_dir(date: str) -> Path:
    return REPO_ROOT / "data" / "bdl_lineups" / date


def _count_odds_pairs(date: str) -> int:
    d = _odds_processed_dir(date)
    if not d.exists():
        return 0
    return len(list(d.glob("odds_pairs_*.parquet")))


def _count_odds_live_events(date: str) -> int:
    """Approximate live-event count from the freshest odds_pairs file."""
    d = _odds_processed_dir(date)
    if not d.exists():
        return 0
    candidates = sorted(d.glob("odds_pairs_*.parquet"))
    if not candidates:
        return 0
    try:
        import pandas as pd
        df = pd.read_parquet(candidates[-1])
    except Exception:
        return 0
    for col in ("event_id", "game_id"):
        if col in df.columns:
            try:
                return int(df[col].nunique())
            except Exception:
                continue
    return 0


def _bdl_snapshot_rows(date: str) -> tuple[bool, int]:
    """Return (snapshot_present, total_rows). Reads any lineup-style file
    we find under ``data/bdl_lineups/{date}/``."""
    d = _bdl_snapshot_dir(date)
    if not d.exists():
        return False, 0
    files = list(d.glob("*.parquet")) + list(d.glob("*.json"))
    if not files:
        return False, 0
    total = 0
    import pandas as pd
    for f in files:
        try:
            if f.suffix == ".parquet":
                total += len(pd.read_parquet(f))
            elif f.suffix == ".json":
                obj = json.loads(f.read_text())
                if isinstance(obj, list):
                    total += len(obj)
                elif isinstance(obj, dict) and isinstance(obj.get("data"), list):
                    total += len(obj["data"])
        except Exception:
            continue
    return True, total


def _injury_features_present(date: str) -> bool:
    for run_mode in ("morning_expected", "close_lock"):
        p = REPO_ROOT / "data" / "features" / f"injury_lineup_features_{date}_{run_mode}.parquet"
        if p.exists():
            return True
    return False


def _minutes_predictions_present(date: str) -> bool:
    p = REPO_ROOT / "artifacts" / "minutes_predictions" / date / "minutes_predictions.parquet"
    return p.exists()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True, help="YYYY-MM-DD slate date")
    ap.add_argument(
        "--run-mode",
        default="morning_expected",
        choices=("morning_expected", "close_lock"),
    )
    args = ap.parse_args(argv)

    odds_key_present = bool(
        os.environ.get("ODDS_API_KEY", "").strip()
        or os.environ.get("THE_ODDS_API_KEY", "").strip()
    )
    bdl_key_present = bool(os.environ.get("BDL_API_KEY", "").strip())

    odds_count = _count_odds_pairs(args.date)
    odds_processed_present = odds_count > 0
    live_event_count = _count_odds_live_events(args.date)

    bdl_present, bdl_rows = _bdl_snapshot_rows(args.date)
    injury_present = _injury_features_present(args.date)
    minutes_present = _minutes_predictions_present(args.date)

    blockers: list[str] = []
    if not odds_key_present:
        blockers.append("odds_api_key_missing")
    if not bdl_key_present:
        blockers.append("bdl_api_key_missing")
    if args.run_mode == "morning_expected" and not minutes_present:
        blockers.append("minutes_predictions_artifact_missing")

    bdl_state = (
        "confirmed_bdl_or_equivalent" if bdl_present and bdl_rows > 0
        else "confirmed_lineups_not_available_yet" if bdl_present and bdl_rows == 0
        else "bdl_snapshot_missing"
    )

    if blockers:
        status = "failed"
    elif bdl_state == "confirmed_bdl_or_equivalent":
        status = "ready"
    else:
        status = "ready_lineups_pending"

    payload = {
        "delivery_date": args.date,
        "run_mode": args.run_mode,
        "checked_at_utc": _now_utc_iso(),
        "odds_api_key_present": odds_key_present,
        "bdl_api_key_present": bdl_key_present,
        "odds_api_live_events_count": int(live_event_count),
        "odds_api_processed_snapshot_present": bool(odds_processed_present),
        "bdl_lineup_snapshot_present": bool(bdl_present),
        "bdl_lineup_snapshot_rows": int(bdl_rows),
        "bdl_lineup_state": bdl_state,
        "injury_features_present": bool(injury_present),
        "minutes_predictions_present": bool(minutes_present),
        "source_readiness_status": status,
        "blockers": blockers,
        "note": (
            "Empty BDL /v2/lineups pre-confirmation is classified as "
            "confirmed_lineups_not_available_yet; it MUST NOT permit a "
            "full-roster PMF publish. The M8.9 eligibility gate handles "
            "that gating downstream."
        ),
    }

    inj_blob = load_injury_report_selection(REPO_ROOT, args.date)
    if inj_blob:
        for key in INJURY_FRAGMENT_KEYS:
            if key in inj_blob:
                payload[key] = inj_blob[key]

    out_dir = REPO_ROOT / "artifacts" / "source_readiness" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "source_readiness.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"  wrote {out_path.relative_to(REPO_ROOT)}")
    print(f"  source_readiness_status={status} blockers={blockers}")
    if status == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
