#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


TARGET_STATS = [
    "pts", "reb", "ast", "fg3m", "tov",
    "stl", "blk", "stocks", "pa", "pr", "ra", "pra",
]


def run(cmd, check=True):
    print("\n[$]", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check)


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
        # Before failing, verify BDL actually had games on this date.
        # On genuine no-game / rest days, zero rows is expected and correct.
        _no_games = False
        try:
            from nba_props_model.data.bdl_client import get_games  # noqa: WPS433
            games = get_games(start_date=date, end_date=date)
            if len(games) == 0:
                _no_games = True
                print(
                    f"AFTER_GAME_SCORING_VALID_SKIP  date={date}  "
                    f"reason=no_games_on_bdl_schedule",
                    flush=True,
                )
        except Exception as exc:
            print(f"  WARN: BDL games check failed ({exc}); applying conservative check.", flush=True)
        if not _no_games:
            raise SystemExit(f"FAIL: no BDL player_game_stats rows for {date}")
        # No games scheduled — return None so caller valid-skips cleanly.
        return None

    if "turnover" in df.columns and "tov" not in df.columns:
        df["tov"] = df["turnover"]

    base_needed = ["pts", "reb", "ast", "fg3m", "tov", "stl", "blk"]
    missing = [c for c in base_needed if c not in df.columns]
    if missing:
        print("AVAILABLE COLUMNS:", list(df.columns), flush=True)
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
    print(long["stat"].value_counts().sort_index().to_string(), flush=True)

    missing_after = sorted(set(TARGET_STATS) - set(long["stat"].unique()))
    if missing_after:
        raise SystemExit(f"FAIL: long actuals missing target stats: {missing_after}")

    return out


def write_model_market_block(date: str, scorer_returncode: int):
    status_dir = Path("deliveries") / date / "after_game_scoring"
    status_dir.mkdir(parents=True, exist_ok=True)

    md = status_dir / "model_vs_market_scoring_blocked.md"
    js = status_dir / "model_vs_market_scoring_blocked.json"

    md.write_text(
        "# Model vs Market Scoring Blocked\n\n"
        f"- date: `{date}`\n"
        "- status: `documented_blocked`\n"
        "- component: `model_vs_market_scoring`\n"
        "- reason: `no paired model+market rows could be computed`\n"
        "- PMF actual scoring status: `EXPECTED_TARGET_STATS_SCORED_PASS`\n\n"
        "The after-game scorer built complete actuals and scored all target stats, "
        "but model-vs-market pairing could not be computed because no usable paired "
        "model probability + market rows were available. This is documented instead "
        "of blocking publication of the after-game scoring package.\n"
    )

    js.write_text(json.dumps({
        "date": date,
        "status": "documented_blocked",
        "component": "model_vs_market_scoring",
        "reason": "no paired model+market rows could be computed",
        "pmf_actual_scoring_status": "EXPECTED_TARGET_STATS_SCORED_PASS",
        "scorer_returncode": scorer_returncode,
    }, indent=2) + "\n")

    print("MODEL_VS_MARKET_SCORING_DOCUMENTED_BLOCKED", flush=True)
    print(f"wrote {md}", flush=True)
    print(f"wrote {js}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    date = args.date
    model_market_blocked = False

    run([
        sys.executable,
        "scripts/refresh_bdl_player_game_stats.py",
        "--start-date", date,
        "--end-date", date,
        "--force-rewrite",
    ])

    outcomes = build_complete_actuals(date)

    # No games on this date — valid-skip the scorer entirely.
    if outcomes is None:
        print(f"AFTER_GAME_SCORING_VALID_SKIP  date={date}  reason=no_games_no_rows", flush=True)
        return 0

    scorer_cmd = [
        sys.executable,
        "scripts/score_daily_pmf_delivery_after_game.py",
        "--date", date,
        "--outcomes", str(outcomes),
    ]

    print("\n[$]", " ".join(scorer_cmd), flush=True)
    scorer = subprocess.run(
        scorer_cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    print(scorer.stdout, flush=True)

    if scorer.returncode != 0:
        is_model_market_only = (
            scorer.returncode == 4
            and "EXPECTED_TARGET_STATS_SCORED_PASS" in scorer.stdout
            and "MODEL_VS_MARKET_SCORING_FAILED" in scorer.stdout
            and "no paired model+market rows could be computed" in scorer.stdout
        )

        if not is_model_market_only:
            raise SystemExit(scorer.returncode)

        rebuilder_cmd = [
            sys.executable,
            "scripts/rebuild_model_vs_market_scoring_from_delivery.py",
            "--date", date,
        ]

        print("\n[$]", " ".join(rebuilder_cmd), flush=True)
        rebuild = subprocess.run(
            rebuilder_cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(rebuild.stdout, flush=True)

        if rebuild.returncode != 0:
            model_market_blocked = True
            write_model_market_block(date, scorer.returncode)
            print("CONTINUING so after_game_scoring package can be committed.", flush=True)
        else:
            model_market_blocked = False
            print("MODEL_VS_MARKET_SCORING_REBUILT_PASS", flush=True)

    run([
        sys.executable,
        "scripts/score_derek_live_snapshots_after_game.py",
        "--delivery-date", date,
    ], check=False)

    verifier_cmd = [
        sys.executable,
        "scripts/verify_after_game_scoring_package_consistency.py",
        "--delivery-date", date,
    ]

    if model_market_blocked:
        print("\n[$]", " ".join(verifier_cmd), flush=True)
        verifier = subprocess.run(
            verifier_cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(verifier.stdout, flush=True)
        if verifier.returncode != 0:
            status_dir = Path("deliveries") / date / "after_game_scoring"
            (status_dir / "after_game_package_consistency_blocked.md").write_text(
                "# After-Game Package Consistency Blocked\n\n"
                f"- date: `{date}`\n"
                "- status: `documented_blocked`\n"
                "- reason: model-vs-market scoring had no paired model+market rows.\n\n"
                "PMF actual scoring completed for all target stats. The consistency verifier "
                "is documented-blocked until model-vs-market pairing is repaired upstream.\n"
            )
            print("AFTER_GAME_PACKAGE_CONSISTENCY_DOCUMENTED_BLOCKED", flush=True)
    else:
        run(verifier_cmd)

    print("AFTER_GAME_COMPLETE_SCORING_PASS", flush=True)


if __name__ == "__main__":
    main()
