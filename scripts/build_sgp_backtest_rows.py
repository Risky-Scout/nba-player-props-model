#!/usr/bin/env python3
"""Build SGP backtest rows from historical delivery dates.

For each slate date:
  1. Build (or load) the SGP slate state bundle from the delivery.
  2. Run the NBA simulator to produce a simulation tape.
  3. Sample intra-game player pairs and generate 2-leg SGP tickets
     covering a spread of line/side combinations.
  4. Price every ticket and record the raw simulator joint probability.
  5. Write all rows to --out as a Parquet file.

The output file contains a `hit_result` column that is left NULL by default.
Use --link-outcomes to populate `hit_result` (1 = all legs hit, 0 = at least
one leg missed) from data/player_game_stats.parquet automatically.
Once settled, pass the file to scripts/fit_sgp_joint_calibrator.py to train
the joint calibrator.

Usage
-----
  python scripts/build_sgp_backtest_rows.py \\
    --repo-root . \\
    --dates 2026-05-24,2026-05-25 \\
    --n-sims 100000 \\
    --max-pairs-per-game 200 \\
    --out tmp/sgp_backtest_rows.parquet \\
    --link-outcomes
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_SRC = Path(__file__).resolve().parent.parent / "src"
if _REPO_SRC.is_dir():
    sys.path.insert(0, str(_REPO_SRC))

from sgp_engine.bundle import SlateStateBundle
from sgp_engine.pricing import price_ticket
from sgp_engine.schema import SGPTicket
from sgp_engine.sports.nba.adapter import build_nba_slate_state_bundle
from sgp_engine.sports.nba.simulator import NBASimulator


# Standard line offsets tried for each player-stat mean.
LINE_OFFSETS = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]


def _standard_lines(mean: float) -> list[float]:
    """Generate a spread of .5-step lines around a player-stat mean."""
    base = round(mean * 2) / 2
    return sorted({base + o for o in LINE_OFFSETS if base + o >= 0.5})


def _sample_leg_configs(player_stat_pmfs: pd.DataFrame, rng: np.random.Generator, max_per_game: int) -> list[dict]:
    """For each game, sample up to max_per_game leg pairs."""
    all_configs = []
    for game_id, gdf in player_stat_pmfs.groupby("game_id"):
        game_id = str(game_id)
        # Candidate (player_id, stat) combos with valid means.
        candidates = []
        for _, r in gdf.iterrows():
            mean = r.get("mean")
            if mean is None or not np.isfinite(float(mean)):
                continue
            candidates.append({
                "game_id": game_id,
                "player_id": str(r["player_id"]),
                "stat": str(r["stat"]).lower(),
                "mean": float(mean),
                "team_id": str(r.get("team_id", "UNK")),
            })

        if len(candidates) < 2:
            continue

        # Enumerate all unique 2-leg combinations and shuffle.
        pairs = list(itertools.combinations(range(len(candidates)), 2))
        rng.shuffle(pairs)
        count = 0
        for i, j in pairs:
            if count >= max_per_game:
                break
            leg_a = candidates[i]
            leg_b = candidates[j]
            lines_a = _standard_lines(leg_a["mean"])[:3]   # cap for speed
            lines_b = _standard_lines(leg_b["mean"])[:3]
            for la, lb in itertools.product(lines_a, lines_b):
                all_configs.append({
                    "game_id": game_id,
                    "leg_a": {**leg_a, "line": la, "side": "over"},
                    "leg_b": {**leg_b, "line": lb, "side": "over"},
                })
                count += 1
                if count >= max_per_game:
                    break
    return all_configs


def _line_percentile(pmf_json: str | None, line: float, domain_max: int | None = None) -> float | None:
    """Compute CDF at line from PMF JSON (probability of outcome <= line)."""
    if pmf_json is None:
        return None
    try:
        _REPO_SRC_BT = Path(__file__).resolve().parent.parent / "src"
        if str(_REPO_SRC_BT) not in sys.path:
            sys.path.insert(0, str(_REPO_SRC_BT))
        from sgp_engine.pmf import parse_pmf
        pmf = parse_pmf(pmf_json, domain_max=domain_max)
        cdf = float(sum(pmf[k] for k in range(len(pmf)) if k <= line))
        return cdf
    except Exception:
        return None


def _bucket_percentile(p: float | None) -> str:
    if p is None:
        return "unknown"
    if p < 0.20:
        return "low_tail"
    if p < 0.40:
        return "lower_mid"
    if p < 0.60:
        return "mid"
    if p < 0.80:
        return "upper_mid"
    return "high_tail"


def _classify_leg_mix(stats: list[str]) -> str:
    """Classify the stat mix of a set of legs."""
    SPARSE = {"stl", "blk", "stocks"}
    COMBOS = {"pa", "pr", "ra", "pra"}
    s = set(s.lower() for s in stats)
    if s & SPARSE:
        return "includes_sparse"
    if s & COMBOS:
        return "includes_combo"
    if len(s) == 1:
        return f"same_stat:{list(s)[0]}"
    return "mixed"


def _price_configs(
    configs: list[dict],
    tape,
    pmf_df: pd.DataFrame,
    slate_date: str,
    as_of_date: str | None = None,
) -> list[dict]:
    from sgp_engine.pricing import _classify_relationship
    from sgp_engine.schema import SGPLeg

    # Build PMF JSON lookup for percentile computation.
    pmf_json_lut: dict[tuple[str, str, str], tuple[str, int | None]] = {}
    for _, r in pmf_df.iterrows():
        pmf_json_lut[(str(r["game_id"]), str(r["player_id"]), str(r["stat"]).lower())] = (
            str(r.get("pmf_json", "")), r.get("domain_max")
        )

    rows = []
    for i, cfg in enumerate(configs):
        game_id = cfg["game_id"]
        la, lb = cfg["leg_a"], cfg["leg_b"]
        ticket = SGPTicket.from_dict({
            "game_id": game_id,
            "ticket_id": f"bt_{slate_date}_{i:06d}",
            "legs": [
                {"player_id": la["player_id"], "stat": la["stat"], "line": la["line"], "side": la["side"],
                 "game_id": game_id, "team_id": la.get("team_id", "UNK")},
                {"player_id": lb["player_id"], "stat": lb["stat"], "line": lb["line"], "side": lb["side"],
                 "game_id": game_id, "team_id": lb.get("team_id", "UNK")},
            ],
        })
        try:
            result = price_ticket(ticket, tape, pmf_df)
        except Exception:
            continue

        # Relationship classification.
        leg_a_sgp = SGPLeg(player_id=la["player_id"], stat=la["stat"], line=la["line"], side=la["side"],
                           game_id=game_id, team_id=la.get("team_id", "UNK"))
        leg_b_sgp = SGPLeg(player_id=lb["player_id"], stat=lb["stat"], line=lb["line"], side=lb["side"],
                           game_id=game_id, team_id=lb.get("team_id", "UNK"))
        rel_type = _classify_relationship([leg_a_sgp, leg_b_sgp])

        # Demographic columns.
        same_player = 1 if la["player_id"] == lb["player_id"] else 0
        same_team = 1 if (la.get("team_id", "UNK") == lb.get("team_id", "UNK") and la.get("team_id") != "UNK") else 0
        opponent = 1 - same_player - same_team if (1 - same_player - same_team) >= 0 else 0

        stats_list = [la["stat"].lower(), lb["stat"].lower()]
        stat_mix = _classify_leg_mix(stats_list)

        COMBOS = {"pa", "pr", "ra", "pra"}
        COMBO_COMPONENTS = {"pa": {"pts","ast"}, "pr": {"pts","reb"}, "ra": {"reb","ast"},
                            "pra": {"pts","reb","ast"}, "stocks": {"stl","blk"}}
        contains_combo_overlap = False
        for combo_s in COMBOS:
            if combo_s in stats_list:
                other_stats = set(s for s in stats_list if s != combo_s)
                if other_stats & COMBO_COMPONENTS.get(combo_s, set()):
                    contains_combo_overlap = True
                    break

        SPARSE = {"stl", "blk", "stocks"}
        contains_sparse = any(s in SPARSE for s in stats_list)

        # Alt-line detection: line far from PMF mean.
        contains_alt_line = False
        for leg_d, stat_s in [(la, la["stat"].lower()), (lb, lb["stat"].lower())]:
            pmf_row = pmf_df[(pmf_df["player_id"].astype(str) == leg_d["player_id"]) &
                             (pmf_df["stat"].astype(str).str.lower() == stat_s) &
                             (pmf_df["game_id"].astype(str) == game_id)]
            if not pmf_row.empty:
                pmf_mean = float(pmf_row.iloc[0].get("mean", 0.0))
                if abs(leg_d["line"] - pmf_mean) > 3.0:
                    contains_alt_line = True
                    break

        # Line percentile buckets.
        pcts = []
        for leg_d, stat_s in [(la, la["stat"].lower()), (lb, lb["stat"].lower())]:
            pmf_j_key = (game_id, leg_d["player_id"], stat_s)
            pmf_j, dom = pmf_json_lut.get(pmf_j_key, (None, None))
            p = _line_percentile(pmf_j, leg_d["line"], dom)
            pcts.append(_bucket_percentile(p))
        # Combined bucket: if any extreme, mark tail.
        TAIL_BUCKETS = {"low_tail", "high_tail"}
        if any(b in TAIL_BUCKETS for b in pcts):
            combined_bucket = "tail"
        elif len(set(pcts)) == 1:
            combined_bucket = pcts[0]
        else:
            combined_bucket = "mixed"

        # Legs JSON.
        legs_json_str = json.dumps([
            {"player_id": la["player_id"], "stat": la["stat"], "line": la["line"], "side": la["side"]},
            {"player_id": lb["player_id"], "stat": lb["stat"], "line": lb["line"], "side": lb["side"]},
        ])
        sgp_id = f"sgp_{slate_date}_{i:06d}"

        raw_p = float(result.get("raw_joint_probability", np.nan))
        cal_p = float(result.get("calibrated_joint_probability", raw_p))
        indep_p = float(result.get("independent_probability_pmf_marginals", np.nan))
        corr_factor = float(result.get("correlation_factor_vs_pmf_independence", np.nan))
        model_corr = float(result.get("model_corr_factor", corr_factor))

        row = {
            "prediction_date": slate_date,
            "as_of_date": as_of_date or slate_date,
            "game_id": game_id,
            "sgp_id": sgp_id,
            "ticket_id": ticket.ticket_id,
            "leg_count": 2,
            "n_legs": 2,
            "legs_json": legs_json_str,
            "relationship_type": rel_type,
            "stat_mix": stat_mix,
            "role_mix": "unknown",
            "same_player_count": same_player,
            "same_team_count": same_team,
            "opponent_count": opponent,
            "contains_combo_overlap": contains_combo_overlap,
            "contains_sparse_stat": contains_sparse,
            "contains_alt_line": contains_alt_line,
            "line_percentile_bucket": combined_bucket,
            "lineup_status": "unknown",
            "raw_joint_probability": raw_p,
            "calibrated_joint_probability": cal_p,
            "independent_probability": indep_p,
            "correlation_factor": corr_factor,
            "model_corr_factor": model_corr,
            "market_sgp_probability": np.nan,
            "market_sgp_odds": np.nan,
            "market_corr_factor": 1.0,  # independence placeholder
            "market_corr_factor_source": "independence_placeholder",
            "corr_factor_delta_vs_market": model_corr - 1.0,
            "leg_1_player_id": la["player_id"],
            "leg_1_stat": la["stat"],
            "leg_1_line": la["line"],
            "leg_1_side": la["side"],
            "leg_1_marginal_probability_pmf": result["legs"][0]["marginal_probability_pmf"],
            "leg_2_player_id": lb["player_id"],
            "leg_2_stat": lb["stat"],
            "leg_2_line": lb["line"],
            "leg_2_side": lb["side"],
            "leg_2_marginal_probability_pmf": result["legs"][1]["marginal_probability_pmf"],
            "fair_american_odds": result.get("fair_american_odds"),
            "simulation_count": result.get("simulation_count"),
            "actual_hit": None,   # populated from settled outcomes
            "hit_result": None,   # backwards-compat alias
            # Loss fields — populated once actual_hit is known.
            "model_logloss": np.nan,
            "model_brier": np.nan,
            "market_logloss": np.nan,
            "market_brier": np.nan,
            "logloss_delta_vs_market": np.nan,
            "brier_delta_vs_market": np.nan,
            "independence_logloss": np.nan,
            "independence_brier": np.nan,
            "logloss_delta_vs_independence": np.nan,
            "brier_delta_vs_independence": np.nan,
        }
        rows.append(row)
    return rows


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


_COMBO_STAT_COMPONENTS = {
    "pa": ("pts", "ast"),
    "pr": ("pts", "reb"),
    "ra": ("reb", "ast"),
    "pra": ("pts", "reb", "ast"),
    "stocks": ("stl", "blk"),
}

_STAT_COL_RENAME = {
    "points": "pts", "rebounds": "reb", "assists": "ast",
    "steals": "stl", "blocks": "blk", "turnovers": "tov", "threes": "fg3m",
}


def _build_stats_lookup(
    stats_df: pd.DataFrame,
    slate_date: str,
) -> dict[tuple[str, str, str], float]:
    """Build (game_id, player_id, stat) -> value lookup for a slate date."""
    date_col = next(
        (c for c in ["game_date", "slate_date", "date"] if c in stats_df.columns), None
    )
    day_df = stats_df
    if date_col:
        try:
            day_mask = pd.to_datetime(stats_df[date_col]).dt.date.astype(str) == slate_date
            day_df = stats_df[day_mask]
        except Exception:
            pass

    stat_cols = [c for c in list(_STAT_COL_RENAME.keys()) + list(_STAT_COL_RENAME.values())
                 if c in day_df.columns]

    lookup: dict[tuple[str, str, str], float] = {}
    for _, row in day_df.iterrows():
        gid = str(row.get("game_id", ""))
        pid = str(row.get("player_id", ""))
        for col in stat_cols:
            val = row.get(col)
            if val is not None and not (isinstance(val, float) and np.isnan(val)):
                stat_name = _STAT_COL_RENAME.get(col, col)
                lookup[(gid, pid, stat_name)] = float(val)
    return lookup


def _link_outcomes(
    rows: list[dict],
    stats_lookup: dict[tuple[str, str, str], float],
) -> list[dict]:
    """Populate actual_hit for each row using settled stats lookup and compute loss fields."""
    EPS = 1e-7
    out = []
    for row in rows:
        game_id = str(row.get("game_id", ""))
        resolved = True
        all_hit = True

        for leg_num in [1, 2]:
            pid = str(row.get(f"leg_{leg_num}_player_id", ""))
            stat = str(row.get(f"leg_{leg_num}_stat", "")).lower()
            line = float(row.get(f"leg_{leg_num}_line", 0.0))
            side = str(row.get(f"leg_{leg_num}_side", "over"))

            val = stats_lookup.get((game_id, pid, stat))
            if val is None and stat in _COMBO_STAT_COMPONENTS:
                comps = _COMBO_STAT_COMPONENTS[stat]
                comp_vals = [stats_lookup.get((game_id, pid, c)) for c in comps]
                if all(v is not None for v in comp_vals):
                    val = sum(float(v) for v in comp_vals)
            if val is None:
                resolved = False
            elif not _evaluate_leg(val, line, side):
                all_hit = False

        new_row = dict(row)
        hit = int(all_hit) if resolved else None
        new_row["actual_hit"] = hit
        new_row["hit_result"] = hit  # backwards-compat

        if hit is not None:
            cal_p = float(row.get("calibrated_joint_probability", row.get("raw_joint_probability", 0.5)))
            cal_p = max(min(cal_p, 1 - EPS), EPS)
            indep_p = float(row.get("independent_probability", row.get("independent_probability_pmf_marginals", 0.5)))
            indep_p = max(min(indep_p, 1 - EPS), EPS)
            y = float(hit)

            new_row["model_logloss"] = -(y * np.log(cal_p) + (1 - y) * np.log(1 - cal_p))
            new_row["model_brier"] = (cal_p - y) ** 2
            new_row["independence_logloss"] = -(y * np.log(indep_p) + (1 - y) * np.log(1 - indep_p))
            new_row["independence_brier"] = (indep_p - y) ** 2
            new_row["logloss_delta_vs_independence"] = new_row["model_logloss"] - new_row["independence_logloss"]
            new_row["brier_delta_vs_independence"] = new_row["model_brier"] - new_row["independence_brier"]

            # Market losses: only if actual market SGP probability is available.
            mkt_p = float(row.get("market_sgp_probability", np.nan))
            if np.isfinite(mkt_p) and 0 < mkt_p < 1:
                mkt_p = max(min(mkt_p, 1 - EPS), EPS)
                new_row["market_logloss"] = -(y * np.log(mkt_p) + (1 - y) * np.log(1 - mkt_p))
                new_row["market_brier"] = (mkt_p - y) ** 2
                new_row["logloss_delta_vs_market"] = new_row["model_logloss"] - new_row["market_logloss"]
                new_row["brier_delta_vs_market"] = new_row["model_brier"] - new_row["market_brier"]

        out.append(new_row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument("--dates", required=True,
                    help="Comma-separated slate dates (YYYY-MM-DD) to process.")
    ap.add_argument("--n-sims", type=int, default=100_000,
                    help="Simulation draws per slate (default: 100000).")
    ap.add_argument("--max-pairs-per-game", type=int, default=200,
                    help="Max 2-leg ticket configurations per game (default: 200).")
    ap.add_argument("--seed", type=int, default=20260530)
    ap.add_argument("--out", required=True,
                    help="Output parquet path (e.g. tmp/sgp_backtest_rows.parquet).")
    ap.add_argument("--allow-bundle-fail", action="store_true",
                    help="Continue even if bundle status is not PASS (development mode).")
    ap.add_argument("--allow-missing-asof-metadata", action="store_true",
                    help="Warn instead of fail on missing trained/calibrated through metadata.")
    ap.add_argument("--link-outcomes", action="store_true",
                    help="Automatically populate hit_result from data/player_game_stats.parquet.")
    ap.add_argument("--stats-path", default=None,
                    help="Override path to player_game_stats.parquet for --link-outcomes.")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dates = [d.strip() for d in args.dates.split(",") if d.strip()]
    if not dates:
        print("ERROR: --dates produced no valid dates.", file=sys.stderr)
        return 1

    rng = np.random.default_rng(args.seed)
    all_rows: list[dict] = []

    for slate_date in dates:
        print(f"\n[{slate_date}] Building bundle ...", flush=True)
        try:
            bundle_root = repo_root / "deliveries" / slate_date / "sgp_engine" / "slate_state_bundle_v1"
            if bundle_root.exists():
                bundle = SlateStateBundle.load(bundle_root)
                print(f"  Loaded existing bundle: {bundle.status}", flush=True)
            else:
                bundle = build_nba_slate_state_bundle(
                    repo_root, slate_date,
                    allow_missing_asof_metadata=args.allow_missing_asof_metadata,
                    strict=False,
                )
                print(f"  Built bundle: {bundle.status}", flush=True)
        except Exception as exc:
            print(f"  SKIP: bundle build failed: {exc}", file=sys.stderr)
            continue

        if bundle.status != "PASS" and not args.allow_bundle_fail:
            print(f"  SKIP: bundle_status={bundle.status} (use --allow-bundle-fail to force)", file=sys.stderr)
            continue

        print(f"  Running simulator: n_sims={args.n_sims} ...", flush=True)
        try:
            tape = NBASimulator(bundle, n_sims=args.n_sims, seed=args.seed).run()
        except Exception as exc:
            print(f"  SKIP: simulation failed: {exc}", file=sys.stderr)
            continue

        pmf_df = bundle.player_stat_pmfs
        n_players = pmf_df["player_id"].nunique()
        n_games = pmf_df["game_id"].nunique()
        print(f"  {n_players} players / {n_games} games — sampling ticket configs ...", flush=True)

        configs = _sample_leg_configs(pmf_df, rng, max_per_game=args.max_pairs_per_game)
        print(f"  {len(configs)} ticket configurations to price ...", flush=True)

        rows = _price_configs(configs, tape, pmf_df, slate_date, as_of_date=slate_date)
        all_rows.extend(rows)
        print(f"  {len(rows)} rows priced for {slate_date}.", flush=True)

    if not all_rows:
        print("\nNo backtest rows generated. Check that delivery folders contain PMF sources.", file=sys.stderr)
        return 1

    # ── Link outcomes if requested ─────────────────────────────────────────────
    n_linked = 0
    if args.link_outcomes:
        stats_path = Path(args.stats_path) if args.stats_path else (
            repo_root / "data" / "player_game_stats.parquet"
        )
        if not stats_path.exists():
            print(f"  WARNING: --link-outcomes requested but {stats_path} not found; "
                  "hit_result will remain NULL.", file=sys.stderr)
        else:
            try:
                stats_df = pd.read_parquet(stats_path)
                # Build per-date lookup and score rows
                linked_rows: list[dict] = []
                for slate_date in dates:
                    date_rows = [r for r in all_rows if r.get("slate_date") == slate_date]
                    if not date_rows:
                        continue
                    lookup = _build_stats_lookup(stats_df, slate_date)
                    scored = _link_outcomes(date_rows, lookup)
                    linked_rows.extend(scored)
                    n_linked_date = sum(1 for r in scored if r.get("hit_result") is not None)
                    print(f"  [{slate_date}] Linked {n_linked_date}/{len(date_rows)} outcomes.",
                          flush=True)
                # Preserve rows for dates not processed above
                processed_dates = set(dates)
                leftover = [r for r in all_rows if r.get("slate_date") not in processed_dates]
                all_rows = linked_rows + leftover
                n_linked = sum(1 for r in all_rows if r.get("hit_result") is not None)
                print(f"  Total linked: {n_linked}/{len(all_rows)}", flush=True)
            except Exception as exc:
                print(f"  WARNING: Failed to link outcomes: {exc}", file=sys.stderr)

    df = pd.DataFrame(all_rows)
    df.to_parquet(out_path, index=False)

    hit_rate = None
    settled = df.dropna(subset=["actual_hit"])
    if not settled.empty:
        hit_rate = float(settled["actual_hit"].mean())

    summary = {
        "status": "DONE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dates_processed": dates,
        "total_rows": len(df),
        "n_linked_outcomes": n_linked,
        "hit_rate": hit_rate,
        "output": str(out_path),
        "note": (
            "Populate 'hit_result' (1=all legs hit, 0=at least one missed) "
            "from settled game outcomes (use --link-outcomes), then pass to "
            "fit_sgp_joint_calibrator.py."
        ),
    }
    print("\n" + json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
