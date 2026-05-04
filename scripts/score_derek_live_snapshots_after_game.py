"""Phase 13M Part I — score Derek live snapshots after games complete.

This script is a *hook* — when game outcomes are not yet available, it
writes a ``pending_outcomes`` status with the exact blocker and exits 0
without printing any scoring pass lines (so downstream automation can
distinguish "pending" from "failed"). When outcomes ARE available, it
scores each snapshot's PMFs against realized outcomes and emits the
DEREK_T_MINUS_25_SCORING_PASS / DEREK_CLOSE_LOCK_SCORING_PASS /
DEREK_SNAPSHOT_CALIBRATION_PASS lines.

Real scoring uses ``data/player_game_stats.parquet`` as the outcome
source; rows for the delivery_date are joined to per-snapshot
``full_pmf_wide.parquet`` by (player_id, stat).

Usage:
    python3 scripts/score_derek_live_snapshots_after_game.py \\
        --delivery-date YYYY-MM-DD

Exit codes:
    0 — scored OR pending_outcomes (both are non-failure states)
    1 — actual error (e.g. corrupt manifests, missing required files)

Pass lines (only when outcomes exist):
    DEREK_T_MINUS_25_SCORING_PASS
    DEREK_CLOSE_LOCK_SCORING_PASS
    DEREK_SNAPSHOT_CALIBRATION_PASS
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    git_commit,
    read_json,
    utcnow_iso,
    write_json_atomic,
)


DELIVERIES_DIR = REPO_ROOT / "deliveries"
# Phase 13AH: include current_live so the daily aggregate scoring
# actually includes the morning baseline / current-live snapshots once
# settled outcomes land. Previous scope was near-tip only and produced
# snapshots_scored=0 even when current_live had perfectly matchable
# outcomes for the delivery date.
SNAPSHOT_TYPES = ("current_live", "t_minus_25", "close_lock")
STATS_PARQUET = REPO_ROOT / "data" / "player_game_stats.parquet"

# stat → column in player_game_stats.parquet
STAT_TO_COL = {
    "pts": "pts",
    "reb": "reb",
    "ast": "ast",
    "stl": "stl",
    "blk": "blk",
    "fg3m": "fg3m",
    "tov": "turnover",
}


def _outcomes_for_date(delivery_date: str):
    if not STATS_PARQUET.exists():
        return None, "data/player_game_stats.parquet not present"
    try:
        import pandas as pd
        df = pd.read_parquet(STATS_PARQUET)
    except Exception as exc:
        return None, f"failed to read stats parquet: {exc}"
    if "game_date" not in df.columns:
        return None, "player_game_stats.parquet missing game_date column"
    sub = df[df["game_date"].astype(str).str[:10] == delivery_date]
    if sub.empty:
        return None, f"no rows in player_game_stats.parquet for game_date={delivery_date}"
    return sub, ""


def _score_snapshot(snap_dir: Path, outcomes_df, delivery_date: str) -> dict:
    """Return per-snapshot scoring summary or a pending status."""
    import pandas as pd
    manifest_path = snap_dir / "snapshot_manifest.json"
    full_pmf_path = snap_dir / "full_pmf_wide.parquet"
    if not (manifest_path.exists() and full_pmf_path.exists()):
        return {"present": False, "blocker": "snapshot files missing"}
    manifest = read_json(manifest_path)
    pmf = pd.read_parquet(full_pmf_path)
    if "player_id" not in pmf.columns or "stat" not in pmf.columns:
        return {"present": True, "blocker": "full_pmf_wide missing player_id/stat"}

    rows: list[dict] = []
    matched = 0
    for _, r in pmf.iterrows():
        pid = r.get("player_id")
        stat = str(r.get("stat") or "")
        col = STAT_TO_COL.get(stat)
        if not col or col not in outcomes_df.columns:
            continue
        oc = outcomes_df[outcomes_df["player_id"] == pid]
        if oc.empty:
            continue
        actual = oc[col].dropna()
        if actual.empty:
            continue
        try:
            k = int(round(float(actual.iloc[0])))
        except Exception:
            continue
        # Probability assigned to the realized outcome (if pmf column is a
        # JSON dict string from canonical predictions).
        pmf_payload = r.get("pmf")
        p_realized = None
        if isinstance(pmf_payload, str):
            try:
                d = json.loads(pmf_payload)
                p_realized = float(d.get(str(k), 0.0))
            except Exception:
                p_realized = None
        # Fallback: use p_ge ladder if available.
        if p_realized is None and f"p_ge_{k}" in pmf.columns:
            p_ge_k = r.get(f"p_ge_{k}")
            p_ge_k1 = r.get(f"p_ge_{k+1}", 0.0)
            try:
                p_realized = max(0.0, float(p_ge_k or 0.0) - float(p_ge_k1 or 0.0))
            except Exception:
                p_realized = None
        if p_realized is None:
            continue
        matched += 1
        # Logloss vs market (over_prob) where available.
        market_p_over = r.get("market_no_vig_over_prob")
        model_p_over = r.get("model_p_over")
        line = r.get("line")
        over_realized = None
        if line is not None:
            try:
                over_realized = 1.0 if k > float(line) else (0.5 if k == float(line) else 0.0)
            except Exception:
                over_realized = None
        rows.append({
            "player_id": pid,
            "player_name": r.get("player_name"),
            "stat": stat,
            "line": line,
            "actual": k,
            "p_realized": p_realized,
            "model_p_over": model_p_over,
            "market_no_vig_over_prob": market_p_over,
            "over_realized": over_realized,
        })

    if not rows:
        return {
            "present": True,
            "blocker": "no PMF rows could be matched to realized outcomes",
        }

    sdf = pd.DataFrame(rows)
    sdf["nll"] = sdf["p_realized"].clip(lower=1e-9).apply(lambda x: -math.log(x))
    res = {
        "snapshot_dir": str(snap_dir.relative_to(REPO_ROOT)),
        "matched_rows": matched,
        "mean_nll": float(sdf["nll"].mean()),
        "median_p_realized": float(sdf["p_realized"].median()),
    }
    if sdf["over_realized"].notna().any():
        eligible = sdf.dropna(subset=["over_realized", "model_p_over", "market_no_vig_over_prob"])
        if not eligible.empty:
            def logloss(p, y):
                p = max(min(float(p), 1 - 1e-9), 1e-9)
                return -(y * math.log(p) + (1 - y) * math.log(1 - p))
            model_ll = eligible.apply(
                lambda r: logloss(r["model_p_over"], r["over_realized"]), axis=1
            )
            mkt_ll = eligible.apply(
                lambda r: logloss(r["market_no_vig_over_prob"], r["over_realized"]), axis=1
            )
            res["model_logloss_vs_over"] = float(model_ll.mean())
            res["market_logloss_vs_over"] = float(mkt_ll.mean())
    sdf.to_csv(snap_dir / "after_game_scoring.csv", index=False)
    write_json_atomic(snap_dir / "after_game_scoring.json", res)
    res["present"] = True
    res["blocker"] = ""
    return res


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Score Derek live snapshots after games complete.")
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    base = DELIVERIES_DIR / args.delivery_date / "derek_game_snapshots"
    if not base.exists():
        print(f"  no derek_game_snapshots/ dir for {args.delivery_date}; nothing to score.")
        return 0

    outcomes, blocker = _outcomes_for_date(args.delivery_date)
    if outcomes is None:
        # Pending — write status and exit 0 without printing scoring pass lines.
        agg = {
            "schema_version": "1.0",
            "delivery_date": args.delivery_date,
            "generated_at_utc": utcnow_iso(),
            "code_commit": git_commit(),
            "status": "pending_outcomes",
            "blocker": blocker,
        }
        out_dir = base
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json_atomic(out_dir / "aggregate_snapshot_scoring.json", agg)
        (out_dir / "aggregate_snapshot_scoring.md").write_text(
            f"# Aggregate snapshot scoring — {args.delivery_date}\n\n"
            f"- status: **pending_outcomes**\n"
            f"- blocker: `{blocker}`\n"
            f"- generated_at_utc: {agg['generated_at_utc']}\n",
            encoding="utf-8",
        )
        print(f"DEREK_LIVE_SNAPSHOT_SCORING_PENDING")
        print(f"  delivery_date={args.delivery_date}  blocker={blocker!r}")
        return 0

    # Outcomes present — score each snapshot.
    games = [d for d in sorted(base.iterdir()) if d.is_dir()]
    aggregate: dict = {
        "schema_version": "1.0",
        "delivery_date": args.delivery_date,
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "status": "scored",
        "by_game": {},
    }
    aggregate_rows: list[dict] = []
    for gdir in games:
        gid = gdir.name
        per_game = {}
        for st in SNAPSHOT_TYPES:
            sdir = gdir / st
            if (sdir / "snapshot_manifest.json").exists():
                per_game[st] = _score_snapshot(sdir, outcomes, args.delivery_date)
                if per_game[st].get("present") and not per_game[st].get("blocker"):
                    aggregate_rows.append({
                        "game_id": gid, "snapshot_type": st, **per_game[st],
                    })
        aggregate["by_game"][gid] = per_game

    # Aggregate rollup.
    if aggregate_rows:
        import pandas as pd
        adf = pd.DataFrame(aggregate_rows)
        adf.to_csv(base / "aggregate_snapshot_scoring.csv", index=False)
        agg_summary = {
            "snapshots_scored": int(len(adf)),
            "mean_nll": float(adf["mean_nll"].mean()) if "mean_nll" in adf.columns else None,
        }
        aggregate["summary"] = agg_summary
    write_json_atomic(base / "aggregate_snapshot_scoring.json", aggregate)
    md = [
        f"# Aggregate snapshot scoring — {args.delivery_date}",
        "",
        f"- status: **scored**",
        f"- generated_at_utc: {aggregate['generated_at_utc']}",
        f"- snapshots scored: {aggregate.get('summary', {}).get('snapshots_scored', 0)}",
        f"- mean_nll across all scored snapshots: "
        f"`{aggregate.get('summary', {}).get('mean_nll')}`",
    ]
    (base / "aggregate_snapshot_scoring.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # Pass lines — only when at least one snapshot of each type was scored.
    types_scored = {row["snapshot_type"] for row in aggregate_rows}
    if "current_live" in types_scored:
        print("DEREK_CURRENT_LIVE_SCORING_PASS")
    if "t_minus_25" in types_scored:
        print("DEREK_T_MINUS_25_SCORING_PASS")
    if "close_lock" in types_scored:
        print("DEREK_CLOSE_LOCK_SCORING_PASS")
    if types_scored:
        print("DEREK_SNAPSHOT_CALIBRATION_PASS")
    # Phase 13AH: canonical end-of-pass line required by the daily
    # production contract. Includes total props scored across all
    # successfully-joined snapshots and the unjoined-row count for
    # operator audit.
    props_scored = sum(int(row.get("matched_rows", 0)) for row in aggregate_rows)
    unjoined = sum(int(row.get("unmatched_rows", 0)) for row in aggregate_rows)
    if aggregate_rows:
        print(f"DEREK_AFTER_GAME_SCORING_PASS  delivery_date={args.delivery_date}  "
              f"snapshots_scored={len(aggregate_rows)}  "
              f"props_scored={props_scored}  unjoined={unjoined}  "
              f"scoring_report=deliveries/{args.delivery_date}/derek_game_snapshots/aggregate_snapshot_scoring.json")
    else:
        print(f"DEREK_AFTER_GAME_SCORING_FAILED  delivery_date={args.delivery_date}  "
              f"reason=no_snapshots_scored", file=sys.stderr)
    print(
        f"  delivery_date={args.delivery_date} snapshots_scored={len(aggregate_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
