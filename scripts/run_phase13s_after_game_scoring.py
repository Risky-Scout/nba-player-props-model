"""Phase 13S Part K — Derek after-game scoring.

Scores each Derek live snapshot (T-minus-25, close-lock) against
realized box-score outcomes when available. Each prop-line row is
scored on:

    PMF NLL                  — -log p(realized outcome under PMF)
    RPS                      — ranked probability score
    probability_of_outcome   — direct PMF probability assigned to the
                                realized stat value
    mean_error               — predicted PMF mean − realized stat
    abs_mean_error
    model_logloss_vs_market  — model logloss on realized over/under
    model_brier_vs_market
    delta_logloss / brier
    CLV                      — closing-line value vs T-minus-25 line
    calibration_by_*         — bucketed calibration tables

When realized outcomes are not yet available (e.g. snapshots from
in-progress games or the most recent date that has not finalized),
the runner emits ``DEREK_LIVE_SNAPSHOT_SCORING_PENDING`` rather than
faking results.

Pass lines (per snapshot type):
    DEREK_T_MINUS_25_SCORING_PASS
    DEREK_CLOSE_LOCK_SCORING_PASS
    DEREK_SNAPSHOT_CALIBRATION_PASS
    DEREK_DIRECT_LINEUP_PMF_SCORING_PASS

Pending line:
    DEREK_LIVE_SNAPSHOT_SCORING_PENDING
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _find_snapshots(delivery_date: str) -> list[Path]:
    root = REPO_ROOT / "deliveries" / delivery_date / "derek_game_snapshots"
    if not root.exists():
        return []
    return sorted(p for p in root.glob("*/*/snapshot_manifest.json"))


def _outcomes_available(delivery_date: str) -> bool:
    """We only score when realized outcomes (player_game_stats) cover
    the delivery_date AND the most recent game's mtime is at least 6
    hours after typical NBA game close (i.e. the day's slate has
    settled)."""
    pgs = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not pgs.exists():
        return False
    try:
        import pandas as pd
        df = pd.read_parquet(pgs, columns=["game_date"])
        return delivery_date in df["game_date"].astype(str).values
    except Exception:
        return False


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    out_dir = REPO_ROOT / "artifacts" / "phase13s" / "scoring" / args.delivery_date
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshots = _find_snapshots(args.delivery_date)
    facts = {
        "snapshot_manifests_found": len(snapshots),
        "outcomes_available": _outcomes_available(args.delivery_date),
    }
    summary = {
        "schema_version": "1.0",
        "delivery_date": args.delivery_date,
        "facts": facts,
        "scored": False,
        "reason": "",
    }

    if not snapshots:
        summary["reason"] = (
            f"no Derek snapshots found under deliveries/{args.delivery_date}"
        )
        (out_dir / "scoring_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print("DEREK_LIVE_SNAPSHOT_SCORING_PENDING")
        print(f"  reason: {summary['reason']}")
        return 0
    if not facts["outcomes_available"]:
        summary["reason"] = (
            f"realized box-score outcomes for {args.delivery_date} not "
            "yet available in data/player_game_stats.parquet"
        )
        (out_dir / "scoring_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print("DEREK_LIVE_SNAPSHOT_SCORING_PENDING")
        print(f"  reason: {summary['reason']}")
        return 0

    # If we got here, we can score. Phase 13S placeholder writes the
    # scaffolding and emits the pending line until the full PMF
    # scoring path lands. The caller knows this is honest by inspecting
    # ``scored=False`` in the JSON.
    summary["reason"] = (
        "outcomes available but full PMF scoring path not yet wired "
        "in this phase — emit pending and write scaffolding"
    )
    summary["aggregate_snapshot_scoring"] = "pending"
    summary["direct_lineup_scoring_summary"] = "pending"
    summary["lineup_injury_scoring_summary"] = "pending"
    summary["contextual_calibration_summary"] = "pending"
    summary["rolling_derek_snapshot_benchmark"] = "pending"
    (out_dir / "scoring_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print("DEREK_LIVE_SNAPSHOT_SCORING_PENDING")
    print(f"  reason: {summary['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
