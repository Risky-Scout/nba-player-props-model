#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


TARGET_STATS = [
    "pts", "reb", "ast", "fg3m", "tov",
    "stl", "blk", "stocks", "pa", "pr", "ra", "pra",
]


def run(cmd):
    print("\n[$]", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def build_complete_actuals(date: str) -> Path:
    source = Path("data/player_game_stats.parquet")
    out = Path(f"/tmp/player_actuals_{date}_all_target_stats_long.parquet")

    if not source.exists():
        raise SystemExit(f"FAIL: missing {source}")

    df = pd.read_parquet(source).copy()

    if "game_date" not in df.columns:
        raise SystemExit("FAIL: player_game_stats missing game_date")

    df["game_date"] = pd.to_datetime(df["game_date"]).dt.strftime("%Y-%m-%d")
    df = df[df["game_date"].eq(date)].copy()

    if df.empty:
        raise SystemExit(f"FAIL: no BDL player_game_stats rows for {date}")

    if "turnover" in df.columns and "tov" not in df.columns:
        df["tov"] = df["turnover"]

    base_needed = ["pts", "reb", "ast", "fg3m", "tov", "stl", "blk"]
    missing = [c for c in base_needed if c not in df.columns]
    if missing:
        print("AVAILABLE COLUMNS:", list(df.columns))
        raise SystemExit(f"FAIL: missing base actual stat columns: {missing}")

    for c in base_needed:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df["stocks"] = df["stl"] + df["blk"]
    df["pa"] = df["pts"] + df["ast"]
    df["pr"] = df["pts"] + df["reb"]
    df["ra"] = df["reb"] + df["ast"]
    df["pra"] = df["pts"] + df["reb"] + df["ast"]

    id_cols = [
        c for c in [
            "game_date", "game_id", "player_id", "player_name",
            "team", "team_abbr", "team_id"
        ]
        if c in df.columns
    ]

    long = df[id_cols + TARGET_STATS].melt(
        id_vars=id_cols,
        value_vars=TARGET_STATS,
        var_name="stat",
        value_name="actual",
    )

    long["actual_value"] = long["actual"]
    long["outcome"] = long["actual"]
    long["k_actual"] = long["actual"]

    long.to_parquet(out, index=False)

    print(f"WROTE {out}", flush=True)
    print("source_rows:", len(df), flush=True)
    print("long_rows:", len(long), flush=True)
    print("stats:", flush=True)
    print(long["stat"].value_counts().sort_index().to_string(), flush=True)

    missing_after = sorted(set(TARGET_STATS) - set(long["stat"].unique()))
    if missing_after:
        raise SystemExit(f"FAIL: long actuals missing target stats: {missing_after}")

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    date = args.date

    run([
        sys.executable,
        "scripts/refresh_bdl_player_game_stats.py",
        "--start-date", date,
        "--end-date", date,
        "--force-rewrite",
    ])

    outcomes = build_complete_actuals(date)

    run([
        sys.executable,
        "scripts/score_daily_pmf_delivery_after_game.py",
        "--date", date,
        "--outcomes", str(outcomes),
    ])

    run([
        sys.executable,
        "scripts/score_derek_live_snapshots_after_game.py",
        "--delivery-date", date,
    ])

    run([
        sys.executable,
        "scripts/verify_after_game_scoring_package_consistency.py",
        "--delivery-date", date,
    ])

    print("AFTER_GAME_COMPLETE_SCORING_PASS", flush=True)


if __name__ == "__main__":
    main()
