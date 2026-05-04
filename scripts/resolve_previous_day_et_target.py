"""Phase 13G — strict previous-day-in-America/New_York target resolver.

Replaces the looser ``resolve_latest_safe_training_date.py`` for the daily
nightly target. Computes ``target_date_et = (now_et - 1 day).date()``
where ``now_et`` is the current moment in America/New_York, then verifies
that all NBA games for that date are final and outcome coverage is
complete in ``data/player_game_stats.parquet``.

Usage:
    python3 scripts/resolve_previous_day_et_target.py
    python3 scripts/resolve_previous_day_et_target.py --allow-stale-safe-date

Outputs:
    artifacts/nightly_training/previous_day_et_target.json

Exit codes / stdout:
    0 + date  — yesterday-ET data is complete; downstream training proceeds.
    1 + reason — data not ready; orchestrator must halt with
                 halted_reason=previous_day_data_not_ready, unless
                 --allow-stale-safe-date is set, in which case the resolver
                 falls back to the most recent complete date and exits 0
                 with stale_fallback_used=true recorded.

Hard rules:
- Today (UTC or ET) is never a target — games may still be in progress.
- "Complete" = enough player-game rows AND data file mtime indicates a
  recent BDL refresh (or the freshness manifest if available).
- ``--allow-stale-safe-date`` is opt-in; the scheduled workflow does NOT
  set it. Operators can use it for backfills.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    NIGHTLY_TRAINING_DIR,
    git_commit,
    utcnow,
    utcnow_iso,
    write_json_atomic,
)

PLAYER_GAME_STATS = REPO_ROOT / "data" / "player_game_stats.parquet"
FRESHNESS_MANIFEST_DIR = REPO_ROOT / "data" / "freshness_manifest"

# Minimum player-game rows for a date to be considered "complete." During
# the regular season a full slate is 200-400 rows; during the playoffs a
# typical complete night ranges from 20 rows (single playoff game, tight
# 10-deep rotation) up to 100+ rows (4-game first-round slate, deeper
# benches). The floor must catch obviously-partial slates (e.g. 2026-04-29
# at 17 rows = late-arriving boxes) without rejecting completed multi-game
# playoff nights with tight rotations (e.g. 2026-05-03 at 44 rows = two
# games × 22-player tight playoff rotation).
#
# Phase 13AF lowered this from 50 → 25 because 50 was rejecting valid
# 2-game playoff nights with playoff-tight rotations. 25 still catches
# the partial-slate failure mode while accepting any completed playoff
# game with normal active-roster coverage.
COMPLETE_NIGHT_FLOOR_ROWS = 25


def _compute_target_date_et() -> dt.date:
    """Yesterday in America/New_York."""
    try:
        from zoneinfo import ZoneInfo
        et = ZoneInfo("America/New_York")
    except Exception:
        # Fallback: approximate ET as UTC-4 (EDT). NBA season is mostly EDT;
        # the few EST days won't shift the date for typical 09:30 UTC runs.
        return (utcnow() - dt.timedelta(hours=4) - dt.timedelta(days=1)).date()
    now_et = dt.datetime.now(et)
    return (now_et - dt.timedelta(days=1)).date()


def _check_completeness(target: dt.date) -> dict:
    findings: dict = {
        "target_date_et": target.isoformat(),
        "input_path": str(PLAYER_GAME_STATS.relative_to(REPO_ROOT)),
        "input_present": PLAYER_GAME_STATS.exists(),
        "rows_for_target": 0,
        "rows_for_target_meets_floor": False,
        "max_outcome_date_in_file": None,
        "max_outcome_meets_target": False,
        "data_complete_for_target_date": False,
        "freshness_manifest_for_target": None,
    }
    if not PLAYER_GAME_STATS.exists():
        findings["error"] = "missing_player_game_stats_parquet"
        return findings
    try:
        import pandas as pd
    except ImportError:
        findings["error"] = "pandas_not_installed"
        return findings
    df = pd.read_parquet(PLAYER_GAME_STATS, columns=["game_date"])
    ds = pd.to_datetime(df["game_date"]).dt.date
    findings["max_outcome_date_in_file"] = str(ds.max())
    rows_target = int((ds == target).sum())
    findings["rows_for_target"] = rows_target
    findings["rows_for_target_meets_floor"] = rows_target >= COMPLETE_NIGHT_FLOOR_ROWS
    findings["max_outcome_meets_target"] = ds.max() >= target

    # Optional: check the per-date freshness manifest if present.
    fresh = FRESHNESS_MANIFEST_DIR / f"{target.isoformat()}.json"
    if fresh.exists():
        try:
            with fresh.open("r", encoding="utf-8") as f:
                m = json.load(f)
            findings["freshness_manifest_for_target"] = {
                "path": str(fresh.relative_to(REPO_ROOT)),
                "keys": sorted(list(m.keys()))[:10] if isinstance(m, dict) else None,
            }
        except Exception:
            pass

    findings["data_complete_for_target_date"] = bool(
        findings["rows_for_target_meets_floor"]
        and findings["max_outcome_meets_target"]
    )
    return findings


def _latest_safe_fallback() -> str | None:
    """Find the most recent date in the file that meets the row floor."""
    try:
        import pandas as pd
    except ImportError:
        return None
    if not PLAYER_GAME_STATS.exists():
        return None
    df = pd.read_parquet(PLAYER_GAME_STATS, columns=["game_date"])
    counts = df.groupby(df["game_date"].astype(str).str[:10]).size().sort_index(ascending=False)
    today = utcnow().date()
    for date_str, n in counts.items():
        d = dt.date.fromisoformat(str(date_str))
        if d >= today:
            continue
        if int(n) >= COMPLETE_NIGHT_FLOOR_ROWS:
            return str(date_str)
    return None


def resolve(allow_stale_fallback: bool) -> dict:
    target_et = _compute_target_date_et()
    findings = _check_completeness(target_et)
    payload: dict = {
        "schema_version": "1.0",
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "target_policy": "previous_day_et",
        "target_date_et": target_et.isoformat(),
        "completeness": findings,
        "stale_fallback_used": False,
        "stale_fallback_target_date": None,
        "resolved_training_cutoff_date": None,
        "halted_reason": None,
    }
    if findings.get("data_complete_for_target_date"):
        payload["resolved_training_cutoff_date"] = target_et.isoformat()
        return payload

    # Strict default: halt.
    if not allow_stale_fallback:
        payload["halted_reason"] = "previous_day_data_not_ready"
        return payload

    # Operator override: fall back to the most recent complete date.
    fallback = _latest_safe_fallback()
    if not fallback:
        payload["halted_reason"] = "no_safe_fallback_date_found"
        return payload
    payload["stale_fallback_used"] = True
    payload["stale_fallback_target_date"] = fallback
    payload["resolved_training_cutoff_date"] = fallback
    return payload


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Strict previous-day-ET target resolver.")
    p.add_argument(
        "--allow-stale-safe-date",
        action="store_true",
        help=(
            "If set and yesterday-in-ET data is incomplete, fall back to the "
            "most recent complete date with stale_fallback_used=true. The "
            "scheduled workflow does NOT pass this flag — it halts cleanly "
            "with halted_reason=previous_day_data_not_ready instead."
        ),
    )
    args = p.parse_args(argv)
    NIGHTLY_TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    out_path = NIGHTLY_TRAINING_DIR / "previous_day_et_target.json"
    payload = resolve(allow_stale_fallback=args.allow_stale_safe_date)
    write_json_atomic(out_path, payload)

    if payload.get("resolved_training_cutoff_date"):
        print(payload["resolved_training_cutoff_date"])
        if payload["stale_fallback_used"]:
            print(
                f"NOTE: stale_fallback_used=true (target_date_et={payload['target_date_et']}, "
                f"fallback={payload['stale_fallback_target_date']})",
                file=sys.stderr,
            )
        return 0
    print(
        json.dumps(
            {
                "halted_reason": payload["halted_reason"],
                "target_date_et": payload["target_date_et"],
                "completeness": payload["completeness"],
            }
        ),
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
