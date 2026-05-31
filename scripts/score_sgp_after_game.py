#!/usr/bin/env python3
"""Post-game SGP outcome scorer.

Loads the SGP price grid for a slate date and settled player game stats,
evaluates each ticket's legs against actual outcomes, and appends scored
rows to data/sgp_backtest_rows.parquet for calibrator training.

Usage
-----
  python3 scripts/score_sgp_after_game.py --date 2026-05-30 --repo-root .
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def _valid_skip(reason: str, repo_root: Path, slate_date: str) -> int:
    status = {
        "slate_date": slate_date,
        "status": "VALID_SKIP",
        "reason": reason,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    out_dir = repo_root / "deliveries" / slate_date / "sgp_engine"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sgp_after_game_scoring_status.json").write_text(
        json.dumps(status, indent=2)
    )
    print(f"[SGP SCORE] VALID_SKIP: {reason}", flush=True)
    return 0


def _evaluate_leg(actual_value: float, line: float, side: str) -> bool:
    side_l = side.lower()
    if side_l in {"over", "o", ">", "gt"}:
        return float(actual_value) > float(line)
    if side_l in {"under", "u", "<", "lt"}:
        return float(actual_value) < float(line)
    if side_l in {"ge", ">="}:
        return float(actual_value) >= float(line)
    if side_l in {"le", "<="}:
        return float(actual_value) <= float(line)
    return False


# Combo stat → algebraic formula
_COMBO_STATS = {
    "pa": ("pts", "ast"),
    "pr": ("pts", "reb"),
    "ra": ("reb", "ast"),
    "pra": ("pts", "reb", "ast"),
    "stocks": ("stl", "blk"),
}


def _resolve_stat_value(
    stat: str,
    player_id: str,
    game_id: str,
    stats_lookup: dict[tuple[str, str, str], float],
) -> float | None:
    stat_l = stat.lower()
    key = (str(game_id), str(player_id), stat_l)
    if key in stats_lookup:
        return stats_lookup[key]
    # Try combo
    if stat_l in _COMBO_STATS:
        comps = _COMBO_STATS[stat_l]
        values = [stats_lookup.get((str(game_id), str(player_id), c)) for c in comps]
        if all(v is not None for v in values):
            return sum(float(v) for v in values)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="Slate date YYYY-MM-DD")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument("--stats-path", default=None,
                    help="Override path to player_game_stats.parquet")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    slate_date = args.date
    sgp_root = repo_root / "deliveries" / slate_date / "sgp_engine"

    print(f"[SGP SCORE] date={slate_date}", flush=True)

    # ── Load settled stats ────────────────────────────────────────────────────
    stats_path = Path(args.stats_path) if args.stats_path else (
        repo_root / "data" / "player_game_stats.parquet"
    )
    if not stats_path.exists():
        return _valid_skip(
            f"player_game_stats.parquet not found at {stats_path}",
            repo_root, slate_date,
        )

    try:
        stats_df = pd.read_parquet(stats_path)
    except Exception as exc:
        return _valid_skip(f"Failed to read stats: {exc}", repo_root, slate_date)

    # Filter to this slate date
    date_cols = [c for c in ["game_date", "slate_date", "date"] if c in stats_df.columns]
    if date_cols:
        mask = None
        for col in date_cols:
            try:
                col_dates = pd.to_datetime(stats_df[col]).dt.date.astype(str)
                if mask is None:
                    mask = col_dates == slate_date
                else:
                    mask = mask | (col_dates == slate_date)
            except Exception:
                pass
        if mask is not None:
            stats_df = stats_df[mask]

    if stats_df.empty:
        return _valid_skip(
            f"No settled stats found for date {slate_date}",
            repo_root, slate_date,
        )

    # Build fast lookup: (game_id, player_id, stat) -> value
    stats_lookup: dict[tuple[str, str, str], float] = {}
    stat_cols = [c for c in ["pts", "reb", "ast", "stl", "blk", "tov", "fg3m",
                              "points", "rebounds", "assists", "steals", "blocks",
                              "turnovers", "threes"] if c in stats_df.columns]
    stat_rename = {
        "points": "pts", "rebounds": "reb", "assists": "ast",
        "steals": "stl", "blocks": "blk", "turnovers": "tov",
        "threes": "fg3m",
    }

    for _, row in stats_df.iterrows():
        gid = str(row.get("game_id", ""))
        pid = str(row.get("player_id", ""))
        for col in stat_cols:
            val = row.get(col)
            if val is not None and not (isinstance(val, float) and np.isnan(val)):
                stat_name = stat_rename.get(col, col)
                stats_lookup[(gid, pid, stat_name)] = float(val)

    print(f"  Loaded {len(stats_df)} stat rows for {slate_date}", flush=True)

    # ── Load price grid ────────────────────────────────────────────────────────
    price_path = sgp_root / "prices" / "sgp_price_grid.parquet"
    if not price_path.exists():
        price_path_csv = sgp_root / "prices" / "sgp_price_grid.csv"
        if price_path_csv.exists():
            try:
                price_df = pd.read_csv(price_path_csv)
            except Exception as exc:
                return _valid_skip(f"Could not load price CSV: {exc}", repo_root, slate_date)
        else:
            return _valid_skip(
                f"Price grid not found at {price_path}",
                repo_root, slate_date,
            )
    else:
        try:
            price_df = pd.read_parquet(price_path)
        except Exception as exc:
            return _valid_skip(f"Could not load price parquet: {exc}", repo_root, slate_date)

    if price_df.empty:
        return _valid_skip("Price grid is empty", repo_root, slate_date)

    print(f"  Loaded {len(price_df)} price rows", flush=True)

    # ── Score each ticket ─────────────────────────────────────────────────────
    scored_rows: list[dict] = []
    n_scored = 0
    n_unresolvable = 0

    for _, prow in price_df.iterrows():
        legs_json = prow.get("legs_json")
        if not isinstance(legs_json, str):
            n_unresolvable += 1
            continue

        try:
            legs = json.loads(legs_json)
        except Exception:
            n_unresolvable += 1
            continue

        game_id = str(prow.get("game_id", ""))
        all_resolved = True
        all_hit = True

        for leg in legs:
            player_id = str(leg.get("player_id", ""))
            stat = str(leg.get("stat", "")).lower()
            line = float(leg.get("line", 0.0))
            side = str(leg.get("side", "over"))
            leg_game_id = str(leg.get("game_id") or game_id)

            actual = _resolve_stat_value(stat, player_id, leg_game_id, stats_lookup)
            if actual is None:
                all_resolved = False
                break
            leg_hit = _evaluate_leg(actual, line, side)
            if not leg_hit:
                all_hit = False

        if not all_resolved:
            n_unresolvable += 1
            continue

        row = {
            "slate_date": slate_date,
            "ticket_id": prow.get("ticket_id"),
            "game_id": game_id,
            "n_legs": prow.get("n_legs"),
            "raw_joint_probability": prow.get("raw_joint_probability"),
            "calibrated_joint_probability": prow.get("calibrated_joint_probability"),
            "independent_probability_pmf_marginals": prow.get("independent_probability_pmf_marginals"),
            "correlation_factor_vs_pmf_independence": prow.get("correlation_factor_vs_pmf_independence"),
            "fair_american_odds": prow.get("fair_american_odds"),
            "simulation_count": prow.get("simulation_count"),
            "legs_json": legs_json,
            "hit_result": int(all_hit),
            "scored_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        scored_rows.append(row)
        n_scored += 1

    print(f"  Scored: {n_scored}  Unresolvable: {n_unresolvable}", flush=True)

    if not scored_rows:
        return _valid_skip(
            f"No tickets could be scored (all {n_unresolvable} unresolvable)",
            repo_root, slate_date,
        )

    new_df = pd.DataFrame(scored_rows)

    # ── Append to sgp_backtest_rows.parquet ────────────────────────────────────
    out_path = repo_root / "data" / "sgp_backtest_rows.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists():
        try:
            existing = pd.read_parquet(out_path)
            # Deduplicate on ticket_id + slate_date to allow re-runs
            combined = pd.concat([existing, new_df], ignore_index=True)
            if "ticket_id" in combined.columns and "slate_date" in combined.columns:
                combined = combined.drop_duplicates(
                    subset=["ticket_id", "slate_date"], keep="last"
                )
            combined.to_parquet(out_path, index=False)
            print(f"  Appended {n_scored} rows → {out_path} ({len(combined)} total)", flush=True)
        except Exception as exc:
            print(f"  WARNING: Could not append to existing file, overwriting: {exc}", file=sys.stderr)
            new_df.to_parquet(out_path, index=False)
    else:
        new_df.to_parquet(out_path, index=False)
        print(f"  Created {out_path} with {n_scored} rows", flush=True)

    # Write status file
    status = {
        "slate_date": slate_date,
        "status": "DONE",
        "n_scored": n_scored,
        "n_unresolvable": n_unresolvable,
        "hit_rate": float(new_df["hit_result"].mean()) if not new_df.empty else None,
        "output": str(out_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    sgp_root.mkdir(parents=True, exist_ok=True)
    (sgp_root / "sgp_after_game_scoring_status.json").write_text(
        json.dumps(status, indent=2)
    )

    print("[SGP SCORE] Done.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
