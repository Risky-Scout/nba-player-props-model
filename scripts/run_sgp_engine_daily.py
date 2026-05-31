#!/usr/bin/env python3
"""Daily SGP Engine orchestration script.

Loads the slate state bundle, runs the NBA simulator, generates candidate
SGP tickets, prices all candidates, applies calibrators where available,
adds market comparison columns, assigns tiers, and writes all outputs
to the standard deliveries/{date}/sgp_engine/ structure.

Usage
-----
  python3 scripts/run_sgp_engine_daily.py --date 2026-05-30 --repo-root . --n-sims 25000
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REPO_SRC = Path(__file__).resolve().parent.parent / "src"
if _REPO_SRC.is_dir():
    sys.path.insert(0, str(_REPO_SRC))

from sgp_engine.bundle import SlateStateBundle
from sgp_engine.pricing import price_tickets_to_frame, prob_to_american, prob_to_decimal
from sgp_engine.schema import SGPTicket, write_table
from sgp_engine.sports.nba.adapter import build_nba_slate_state_bundle
from sgp_engine.sports.nba.simulator import NBASimulator


# ── Candidate generation ─────────────────────────────────────────────────────

LINE_OFFSETS = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]


def _standard_lines(mean: float) -> list[float]:
    base = round(mean * 2) / 2
    candidates = sorted({base + o for o in LINE_OFFSETS if base + o >= 0.5})
    return candidates[:4]


def _candidate_legs(pmf_df: pd.DataFrame) -> dict[str, list[dict]]:
    """Build a map of game_id -> list of possible single-leg dicts."""
    by_game: dict[str, list[dict]] = {}
    for _, r in pmf_df.iterrows():
        if not r.get("pmf_valid", True):
            continue
        mean = r.get("mean")
        if mean is None or not np.isfinite(float(mean)):
            continue
        gid = str(r["game_id"])
        for line in _standard_lines(float(mean)):
            by_game.setdefault(gid, []).append({
                "game_id": gid,
                "player_id": str(r["player_id"]),
                "player_name": str(r.get("player_name", r["player_id"])),
                "team_id": str(r.get("team_id", "UNK")),
                "stat": str(r["stat"]).lower(),
                "line": line,
                "side": "over",
            })
    return by_game


def generate_sgp_candidates(
    pmf_df: pd.DataFrame,
    *,
    max_candidates: int = 500,
    seed: int = 20260530,
) -> list[SGPTicket]:
    """Generate 2-leg SGP candidate tickets from player-stat PMF data."""
    rng = np.random.default_rng(seed)
    by_game = _candidate_legs(pmf_df)
    tickets: list[SGPTicket] = []
    ticket_counter = 0

    for game_id, legs in by_game.items():
        # Group legs by (player_id, stat) to avoid same player+stat duplicates in one ticket
        by_player_stat: dict[tuple, list[dict]] = {}
        for leg in legs:
            key = (leg["player_id"], leg["stat"])
            by_player_stat.setdefault(key, []).append(leg)

        player_stat_keys = list(by_player_stat.keys())
        if len(player_stat_keys) < 2:
            continue

        # Sample pairs of distinct (player_id, stat) combinations
        pair_indices = list(itertools.combinations(range(len(player_stat_keys)), 2))
        rng.shuffle(pair_indices)

        game_count = 0
        for i, j in pair_indices:
            if game_count >= max_candidates // max(len(by_game), 1) + 10:
                break
            key_a = player_stat_keys[i]
            key_b = player_stat_keys[j]
            leg_options_a = by_player_stat[key_a]
            leg_options_b = by_player_stat[key_b]
            # Take the median line option for each
            leg_a = leg_options_a[len(leg_options_a) // 2]
            leg_b = leg_options_b[len(leg_options_b) // 2]

            ticket = SGPTicket.from_dict({
                "ticket_id": f"cand_{ticket_counter:07d}",
                "game_id": game_id,
                "legs": [
                    {"player_id": leg_a["player_id"], "stat": leg_a["stat"],
                     "line": leg_a["line"], "side": "over", "game_id": game_id,
                     "team_id": leg_a["team_id"], "label": leg_a["player_name"]},
                    {"player_id": leg_b["player_id"], "stat": leg_b["stat"],
                     "line": leg_b["line"], "side": "over", "game_id": game_id,
                     "team_id": leg_b["team_id"], "label": leg_b["player_name"]},
                ],
            })
            tickets.append(ticket)
            ticket_counter += 1
            game_count += 1

            if len(tickets) >= max_candidates:
                return tickets

    return tickets


# ── Tier / suppression logic ─────────────────────────────────────────────────

def _assign_tier(
    row: pd.Series,
    *,
    market_sup_certified: bool,
    calibration_available: bool,
) -> tuple[str, str | None]:
    """Return (tier, suppression_reason) for a price row."""
    prob = float(row.get("calibrated_joint_probability", row.get("raw_joint_probability", 0.0)))
    if not np.isfinite(prob) or prob <= 0:
        return "SUPPRESSED", "invalid_probability"

    ci_low = float(row.get("ci_low", 0.0))
    ci_high = float(row.get("ci_high", 1.0))
    ci_width = ci_high - ci_low
    if ci_width > 0.30:
        return "DIAGNOSTIC_ONLY", "wide_confidence_interval"

    if market_sup_certified:
        return "CERTIFIED", None
    if calibration_available:
        return "MODEL_PRICE", None
    return "MODEL_PRICE", None


def _add_tiers(
    df: pd.DataFrame,
    *,
    market_sup_certified: bool,
    calibration_available: bool,
) -> pd.DataFrame:
    out = df.copy()
    tiers, reasons = [], []
    for _, row in out.iterrows():
        t, r = _assign_tier(row, market_sup_certified=market_sup_certified,
                             calibration_available=calibration_available)
        tiers.append(t)
        reasons.append(r)
    out["tier"] = tiers
    out["suppression_reason"] = reasons
    return out


# ── Marginal preservation report ─────────────────────────────────────────────

def _marginal_preservation_report(
    tape,
    pmf_df: pd.DataFrame,
) -> pd.DataFrame:
    from sgp_engine.pmf import parse_pmf, event_probability

    rows = []
    for _, r in pmf_df.iterrows():
        if not r.get("pmf_valid", True):
            continue
        gid = str(r["game_id"])
        pid = str(r["player_id"])
        stat = str(r["stat"]).lower()
        if not tape.has(gid, pid, stat):
            continue
        sim_vals = tape.get(gid, pid, stat)
        median_line = float(r.get("mean", 0.0))
        if not np.isfinite(median_line) or median_line < 0.5:
            median_line = 0.5

        try:
            pmf = parse_pmf(r["pmf_json"], domain_max=r.get("domain_max"))
            pmf_prob = event_probability(pmf, median_line, "over")
        except Exception:
            continue

        sim_prob = float((sim_vals > median_line).mean())
        rows.append({
            "game_id": gid,
            "player_id": pid,
            "stat": stat,
            "line": median_line,
            "pmf_over_prob": pmf_prob,
            "sim_over_prob": sim_prob,
            "abs_error": abs(sim_prob - pmf_prob),
        })

    return pd.DataFrame(rows)


def _combo_coherence_report(
    tape,
    pmf_df: pd.DataFrame,
) -> pd.DataFrame:
    combo_map = {"pa": ("pts", "ast"), "pr": ("pts", "reb"),
                 "ra": ("reb", "ast"), "pra": ("pts", "reb", "ast"), "stocks": ("stl", "blk")}
    rows = []
    for _, r in pmf_df.iterrows():
        stat = str(r["stat"]).lower()
        if stat not in combo_map:
            continue
        gid = str(r["game_id"])
        pid = str(r["player_id"])
        comps = combo_map[stat]
        if not all(tape.has(gid, pid, c) for c in comps):
            continue
        algebraic = sum(tape.get(gid, pid, c).astype(float) for c in comps)
        stored = tape.get(gid, pid, stat).astype(float)
        rows.append({
            "game_id": gid,
            "player_id": pid,
            "stat": stat,
            "components": "+".join(comps),
            "algebraic_mean": float(algebraic.mean()),
            "stored_mean": float(stored.mean()),
            "mean_abs_diff": float(np.abs(algebraic - stored).mean()),
        })
    return pd.DataFrame(rows)


# ── Dependency diagnostics ────────────────────────────────────────────────────

def _dependency_diagnostics(
    tape,
    pmf_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute pairwise correlation diagnostics for all (player,stat) pairs in the same game.

    For each game, builds a matrix of simulated outcomes [n_sims × n_keys], computes
    the full Pearson correlation matrix, and returns records for every unique pair.

    Columns:
      game_id, player_a, stat_a, team_a, player_b, stat_b, team_b,
      relationship_type, simulated_pearson_r, n_sims,
      player_a_mean, player_b_mean, player_a_std, player_b_std
    """
    from sgp_engine.pricing import _classify_relationship
    from sgp_engine.schema import SGPLeg

    # Build lookup: (game_id, player_id, stat) -> team_id
    team_lookup: dict[tuple[str, str, str], str] = {}
    for _, r in pmf_df.iterrows():
        team_lookup[(str(r["game_id"]), str(r["player_id"]), str(r["stat"]).lower())] = str(r.get("team_id", "UNK"))

    rows = []
    # Group tape keys by game_id
    by_game: dict[str, list[tuple[str, str, str]]] = {}
    for (gid, pid, stat) in tape.stats:
        # Skip "minutes" in diagnostics to focus on scoring stats
        if stat == "minutes":
            continue
        by_game.setdefault(gid, []).append((gid, pid, stat))

    for game_id, keys in by_game.items():
        if len(keys) < 2:
            continue
        # Build matrix: columns = keys, rows = sims
        try:
            mat = np.stack([tape.get(*k).astype(np.float32) for k in keys], axis=1)  # (n_sims, n_keys)
        except Exception:
            continue
        # Vectorised Pearson correlation matrix
        try:
            corr_mat = np.corrcoef(mat.T)  # (n_keys, n_keys)
        except Exception:
            continue

        means = mat.mean(axis=0)
        stds = mat.std(axis=0)

        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                gid_a, pid_a, stat_a = keys[i]
                gid_b, pid_b, stat_b = keys[j]
                team_a = team_lookup.get((gid_a, pid_a, stat_a), "UNK")
                team_b = team_lookup.get((gid_b, pid_b, stat_b), "UNK")
                r_val = float(corr_mat[i, j]) if np.isfinite(corr_mat[i, j]) else np.nan

                # Classify relationship using pricing module logic
                leg_a = SGPLeg(player_id=pid_a, stat=stat_a, line=0.5, side="over",
                               game_id=game_id, team_id=team_a)
                leg_b = SGPLeg(player_id=pid_b, stat=stat_b, line=0.5, side="over",
                               game_id=game_id, team_id=team_b)
                rel = _classify_relationship([leg_a, leg_b])

                rows.append({
                    "game_id": game_id,
                    "player_a": pid_a,
                    "stat_a": stat_a,
                    "team_a": team_a,
                    "player_b": pid_b,
                    "stat_b": stat_b,
                    "team_b": team_b,
                    "relationship_type": rel,
                    "simulated_pearson_r": round(r_val, 6),
                    "n_sims": tape.n_sims,
                    "player_a_mean": round(float(means[i]), 4),
                    "player_b_mean": round(float(means[j]), 4),
                    "player_a_std": round(float(stds[i]), 4),
                    "player_b_std": round(float(stds[j]), 4),
                })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["game_id", "relationship_type", "simulated_pearson_r"],
                            ascending=[True, True, False]).reset_index(drop=True)
    return df


# ── Market comparison ─────────────────────────────────────────────────────────

def _build_market_comparison(
    price_df: pd.DataFrame,
    market_lines: pd.DataFrame | None,
) -> pd.DataFrame:
    """Add market comparison columns to price grid (best-effort)."""
    df = price_df.copy()
    market_cols = ["market_over_no_vig_prob", "market_american_odds", "edge_over", "book"]
    for c in market_cols:
        df[c] = np.nan

    if market_lines is None or market_lines.empty:
        return df

    # Best-effort join on player_id + stat + line; market_lines may be sparse.
    try:
        mdf = market_lines.copy()
        if "line" not in mdf.columns:
            return df
        mdf = mdf.rename(columns={"market_no_vig_prob": "market_over_no_vig_prob",
                                   "american_odds": "market_american_odds"})
        for col in market_cols:
            if col not in mdf.columns:
                mdf[col] = np.nan
        # For each row in df, extract leg_1 info and try to join
        # (simplified: just expose the columns as null for now if structure doesn't match)
        if "legs_json" in df.columns:
            def _extract_leg1_player(legs_json: str) -> str | None:
                try:
                    legs = json.loads(legs_json)
                    return str(legs[0]["player_id"]) if legs else None
                except Exception:
                    return None

            df["_leg1_player"] = df["legs_json"].map(_extract_leg1_player)
    except Exception:
        pass

    return df


def _publishable_edges(price_df: pd.DataFrame) -> pd.DataFrame:
    """Return rows that represent publishable MODEL_PRICE or CERTIFIED edges."""
    mask = price_df["tier"].isin({"MODEL_PRICE", "CERTIFIED"})
    cols = [c for c in [
        "ticket_id", "game_id", "n_legs", "legs_json",
        "calibrated_joint_probability", "fair_american_odds", "fair_decimal_odds",
        "tier", "suppression_reason", "correlation_factor_vs_pmf_independence",
        "ci_low", "ci_high",
    ] if c in price_df.columns]
    return price_df.loc[mask, cols].copy()


# ── Gate status ───────────────────────────────────────────────────────────────

def _compute_gate_status(
    slate_date: str,
    backtest_path: Path,
    calibration_available: bool,
    market_comparison_available: bool,
) -> dict[str, Any]:
    gate = {
        "slate_date": slate_date,
        "calibration_available": calibration_available,
        "market_comparison_available": market_comparison_available,
        "ece": None,
        "calibration_slope": None,
        "ucb95_logloss_delta_vs_market": None,
        "ucb95_brier_delta_vs_market": None,
        "gate_status": "INSUFFICIENT_SAMPLE",
        "market_superiority_certified": False,
    }

    if not backtest_path.exists():
        return gate

    try:
        from sgp_engine.calibration import expected_calibration_error
        bt = pd.read_parquet(backtest_path)
        settled = bt.dropna(subset=["hit_result"])
        if len(settled) < 100:
            gate["gate_status"] = "INSUFFICIENT_SAMPLE"
            return gate

        ece = expected_calibration_error(
            settled,
            pred_col="calibrated_joint_probability",
            y_col="hit_result",
        )
        gate["ece"] = float(ece)
        gate["gate_status"] = "MODEL_PRICE"
        gate["calibration_available"] = True

        # Rough calibration slope
        x = settled["calibrated_joint_probability"].clip(1e-6, 1 - 1e-6)
        y = settled["hit_result"].astype(float)
        if len(x) > 1 and x.std() > 1e-6:
            slope = float(np.corrcoef(x, y)[0, 1] * y.std() / x.std())
            gate["calibration_slope"] = slope
    except Exception as exc:
        gate["gate_status"] = "COMPUTE_ERROR"

    return gate


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="Slate date YYYY-MM-DD")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument("--n-sims", type=int, default=200_000, help="Simulation draws (default: 200000)")
    ap.add_argument("--allow-missing-asof-metadata", action="store_true")
    ap.add_argument("--no-fail-on-missing-calibrator", action="store_true",
                    help="Never fail if calibrator is absent (default behavior).")
    ap.add_argument("--max-candidates", type=int, default=500,
                    help="Max SGP candidate tickets to generate (default: 500).")
    ap.add_argument("--seed", type=int, default=20260530)
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    slate_date = args.date
    sgp_root = repo_root / "deliveries" / slate_date / "sgp_engine"

    print(f"[SGP] date={slate_date}  n_sims={args.n_sims}  max_candidates={args.max_candidates}")

    # ── 1. Load / build slate state bundle ───────────────────────────────────
    print("[SGP] Loading slate state bundle ...", flush=True)
    bundle_root = sgp_root / "slate_state_bundle_v1"
    t0 = time.time()
    try:
        if bundle_root.exists() and (bundle_root / "bundle_manifest.json").exists():
            bundle = SlateStateBundle.load(bundle_root)
            print(f"  Loaded existing bundle: status={bundle.status}", flush=True)
        else:
            bundle = build_nba_slate_state_bundle(
                repo_root, slate_date,
                allow_missing_asof_metadata=args.allow_missing_asof_metadata,
                strict=False,
            )
            print(f"  Built new bundle: status={bundle.status}", flush=True)
    except Exception as exc:
        print(f"::error::Bundle build failed: {exc}", file=sys.stderr)
        return 1

    # ── 2. PMF validity check ─────────────────────────────────────────────────
    pmf_df = bundle.player_stat_pmfs
    invalid_pmfs = (~pmf_df.get("pmf_valid", pd.Series(True, index=pmf_df.index)).fillna(True))
    if invalid_pmfs.any():
        n_bad = int(invalid_pmfs.sum())
        print(f"::error::PMF validity check failed: {n_bad} invalid PMFs", file=sys.stderr)
        return 1

    n_players = int(pmf_df["player_id"].nunique())
    n_games = int(pmf_df["game_id"].nunique())
    n_stat_keys = int(len(pmf_df))
    print(f"  {n_players} players / {n_games} games / {n_stat_keys} stat PMFs", flush=True)

    # ── 3. Run simulator ──────────────────────────────────────────────────────
    print(f"[SGP] Running NBASimulator (n_sims={args.n_sims}) ...", flush=True)
    t_sim_start = time.time()
    try:
        tape = NBASimulator(bundle, n_sims=args.n_sims, seed=args.seed).run()
    except Exception as exc:
        print(f"::error::Simulation failed: {exc}", file=sys.stderr)
        return 1
    sim_runtime = time.time() - t_sim_start
    print(f"  Simulation complete in {sim_runtime:.1f}s", flush=True)

    # ── 4. Simulation diagnostics ─────────────────────────────────────────────
    print("[SGP] Computing marginal preservation report ...", flush=True)
    marg_df = _marginal_preservation_report(tape, pmf_df)
    combo_df = _combo_coherence_report(tape, pmf_df)

    sim_dir = sgp_root / "simulation"
    sim_dir.mkdir(parents=True, exist_ok=True)

    # Check for factor weights file
    fw_path = repo_root / "artifacts" / "models" / "sgp" / "factor_weights" / "factor_weights_latest.json"
    factor_weights_used = "learned" if (fw_path.exists() and json.loads(fw_path.read_text()).get("method") != "hardcoded_defaults_no_historical_data") else "default"

    marg_stats: dict[str, Any] = {"mean_abs_error": None, "max_abs_error": None,
                                   "n_stats": 0, "fraction_within_0.02": None}
    if not marg_df.empty:
        errs = marg_df["abs_error"]
        marg_stats = {
            "mean_abs_error": float(errs.mean()),
            "max_abs_error": float(errs.max()),
            "n_stats": int(len(marg_df)),
            "fraction_within_0.02": float((errs <= 0.02).mean()),
        }

    sim_diag = {
        "slate_date": slate_date,
        "n_sims": args.n_sims,
        "n_stat_keys": n_stat_keys,
        "n_players": n_players,
        "n_games": n_games,
        "simulation_runtime_seconds": round(sim_runtime, 2),
        "factor_weights_used": factor_weights_used,
        "minutes_pool_used": True,
        "marginal_preservation": marg_stats,
    }
    (sim_dir / "simulation_diagnostics.json").write_text(
        json.dumps(sim_diag, indent=2, sort_keys=True)
    )
    (sim_dir / "simulation_tape_manifest.json").write_text(json.dumps({
        "slate_date": slate_date,
        "n_sims": tape.n_sims,
        "n_stat_keys": len(tape.stats),
        "simulator": "nba_mechanism_factor_marginal_anchored_v1",
        "seed": args.seed,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2, sort_keys=True))

    if not marg_df.empty:
        write_table(marg_df, sim_dir / "marginal_preservation_report.parquet")
    else:
        pd.DataFrame(columns=["game_id", "player_id", "stat", "line",
                               "pmf_over_prob", "sim_over_prob", "abs_error"]).to_parquet(
            sim_dir / "marginal_preservation_report.parquet", index=False
        )
    if not combo_df.empty:
        write_table(combo_df, sim_dir / "combo_coherence_report.parquet")
    else:
        pd.DataFrame(columns=["game_id", "player_id", "stat", "components",
                               "algebraic_mean", "stored_mean", "mean_abs_diff"]).to_parquet(
            sim_dir / "combo_coherence_report.parquet", index=False
        )

    # ── 4b. Dependency diagnostics per player-pair ─────────────────────────────
    print("[SGP] Computing pairwise dependency diagnostics ...", flush=True)
    dep_diag_df = _dependency_diagnostics(tape, pmf_df)
    if not dep_diag_df.empty:
        dep_diag_df.to_parquet(sim_dir / "dependency_diagnostics.parquet", index=False)
        n_pairs = len(dep_diag_df)
        n_positive = int((dep_diag_df["simulated_pearson_r"] > 0.05).sum())
        n_negative = int((dep_diag_df["simulated_pearson_r"] < -0.05).sum())
        print(
            f"  {n_pairs} pairs: {n_positive} positively correlated, "
            f"{n_negative} negatively correlated (|r|>0.05)",
            flush=True,
        )
    else:
        pd.DataFrame(columns=[
            "game_id", "player_a", "stat_a", "team_a",
            "player_b", "stat_b", "team_b", "relationship_type",
            "simulated_pearson_r", "n_sims",
            "player_a_mean", "player_b_mean", "player_a_std", "player_b_std",
        ]).to_parquet(sim_dir / "dependency_diagnostics.parquet", index=False)
        print("  No pairs to diagnose (single-player slate?)", flush=True)

    # ── 5. Generate candidate tickets ─────────────────────────────────────────
    print(f"[SGP] Generating up to {args.max_candidates} candidate tickets ...", flush=True)
    candidates = generate_sgp_candidates(
        pmf_df, max_candidates=args.max_candidates, seed=args.seed,
    )
    print(f"  Generated {len(candidates)} candidates", flush=True)

    # Define calibrator path and default flags before the candidates branch so
    # subsequent code (cal_report, gate_status) can reference them safely.
    cal_model_path = (
        repo_root / "artifacts" / "models" / "sgp" / "calibrator"
        / "sgp_joint_calibrator_latest.pkl"
    )
    registry = None
    calibration_available = False
    market_comparison_available = False

    if not candidates:
        print("[SGP] No candidates generated — writing empty price grid.", file=sys.stderr)
        price_df = pd.DataFrame()
    else:
        # ── 6. Load calibrator registry if available ──────────────────────────
        if cal_model_path.exists():
            try:
                from sgp_engine.calibration import HierarchicalCalibratorRegistry
                registry = HierarchicalCalibratorRegistry.load(cal_model_path)
                # Registry is useful only if it has at least a global calibrator or cells.
                calibration_available = (
                    registry.global_calibrator is not None or registry.cell_count > 0
                )
                status = (
                    f"{registry.cell_count} cells + global"
                    if registry.global_calibrator is not None
                    else f"{registry.cell_count} cells, no global"
                )
                print(f"  Loaded calibrator registry: {status}", flush=True)
            except Exception as exc:
                print(f"  WARNING: Could not load calibrator registry: {exc}",
                      file=sys.stderr)
        else:
            print("  No calibrator found — using raw joint probability.", flush=True)

        # ── 7. Price candidates ────────────────────────────────────────────────
        print(f"[SGP] Pricing {len(candidates)} tickets ...", flush=True)
        try:
            # Price without calibration; we apply the registry post-hoc so we can
            # pass ticket-level features (n_legs, stat_mix, relationship_type, role_mix).
            price_df = price_tickets_to_frame(
                candidates, tape, pmf_df, joint_calibrator=None
            )
        except Exception as exc:
            print(f"::error::Price grid generation failed: {exc}", file=sys.stderr)
            return 1
        print(f"  Priced {len(price_df)} tickets", flush=True)

        # Apply registry calibration per ticket using ticket-level features.
        if registry is not None and not price_df.empty:
            cal_probs: list[float] = []
            cal_confs: list[str]   = []
            for _, row in price_df.iterrows():
                raw_p = float(row.get("raw_joint_probability", 0.5))
                ticket_features = {
                    "n_legs":            row.get("n_legs"),
                    "stat_mix":          row.get("stat_mix"),
                    "relationship_type": row.get("dependency_explanation_json"),
                    "role_mix":          row.get("role_mix"),
                }
                cal_p, confidence = registry.predict(raw_p, ticket_features)
                cal_probs.append(float(cal_p))
                cal_confs.append(str(confidence))
            price_df = price_df.copy()
            price_df["calibrated_joint_probability"] = cal_probs
            price_df["calibrated_prob"]              = cal_probs
            price_df["calibration_confidence"]       = cal_confs
        else:
            raw_col = "raw_joint_probability"
            price_df = price_df.copy()
            price_df["calibrated_prob"] = (
                price_df[raw_col] if raw_col in price_df.columns else np.nan
            )
            price_df["calibration_confidence"] = "NO_CALIBRATOR"

        # ── 8. Market comparison ───────────────────────────────────────────────
        market_lines = bundle.market_lines
        market_comparison_available = market_lines is not None and not market_lines.empty
        price_df = _build_market_comparison(price_df, market_lines)

        # ── 9. Tiers and suppression ───────────────────────────────────────────
        gate = _compute_gate_status(
            slate_date,
            backtest_path=repo_root / "data" / "sgp_backtest_rows.parquet",
            calibration_available=calibration_available,
            market_comparison_available=market_comparison_available,
        )
        market_sup_certified = bool(gate.get("market_superiority_certified", False))
        price_df = _add_tiers(
            price_df,
            market_sup_certified=market_sup_certified,
            calibration_available=calibration_available,
        )

    # ── 10. Write price grid ──────────────────────────────────────────────────
    print("[SGP] Writing price grid ...", flush=True)
    prices_dir = sgp_root / "prices"
    prices_dir.mkdir(parents=True, exist_ok=True)

    try:
        if price_df is not None and not price_df.empty:
            price_df.to_parquet(prices_dir / "sgp_price_grid.parquet", index=False)
            price_df.to_csv(prices_dir / "sgp_price_grid.csv", index=False)
            price_df.to_json(prices_dir / "sgp_price_grid.jsonl", orient="records", lines=True)
        else:
            pd.DataFrame().to_parquet(prices_dir / "sgp_price_grid.parquet", index=False)
            pd.DataFrame().to_csv(prices_dir / "sgp_price_grid.csv", index=False)
            (prices_dir / "sgp_price_grid.jsonl").write_text("")
    except Exception as exc:
        print(f"::error::Price grid write failed: {exc}", file=sys.stderr)
        return 1

    # Sample ticket prices (first 10 for manifest)
    sample_rows: list[dict] = []
    if price_df is not None and not price_df.empty:
        for _, row in price_df.head(10).iterrows():
            sample_rows.append({
                "ticket_id": row.get("ticket_id"),
                "n_legs": row.get("n_legs"),
                "calibrated_joint_probability": row.get("calibrated_joint_probability"),
                "fair_american_odds": row.get("fair_american_odds"),
                "tier": row.get("tier"),
            })
    (prices_dir / "sample_ticket_prices.json").write_text(
        json.dumps({"slate_date": slate_date, "sample_count": len(sample_rows),
                    "tickets": sample_rows}, indent=2)
    )
    print(f"  Price grid written: {len(price_df) if price_df is not None else 0} rows", flush=True)

    # ── 11. Calibration report ────────────────────────────────────────────────
    cal_dir = sgp_root / "calibration"
    cal_dir.mkdir(parents=True, exist_ok=True)

    _has_prices = price_df is not None and not price_df.empty
    gate_status = _compute_gate_status(
        slate_date,
        backtest_path=repo_root / "data" / "sgp_backtest_rows.parquet",
        calibration_available=calibration_available and _has_prices,
        market_comparison_available=market_comparison_available and _has_prices,
    )

    cal_report = {
        "slate_date": slate_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_prices": int(len(price_df)) if price_df is not None else 0,
        "calibration_source": str(cal_model_path) if cal_model_path.exists() else None,
        "gate": gate_status,
    }
    (cal_dir / "sgp_calibration_report.json").write_text(
        json.dumps(cal_report, indent=2, sort_keys=True)
    )

    # Reliability by bucket CSV (stub if no backtest data)
    try:
        backtest_path = repo_root / "data" / "sgp_backtest_rows.parquet"
        if backtest_path.exists():
            from sgp_engine.calibration import reliability_table
            bt = pd.read_parquet(backtest_path)
            settled = bt.dropna(subset=["hit_result"])
            if len(settled) >= 20:
                rel_df = reliability_table(settled, pred_col="calibrated_joint_probability", y_col="hit_result")
                rel_df.to_csv(cal_dir / "sgp_reliability_by_bucket.csv", index=False)
            else:
                pd.DataFrame(columns=["bucket", "n", "mean_pred", "actual_rate"]).to_csv(
                    cal_dir / "sgp_reliability_by_bucket.csv", index=False
                )
        else:
            pd.DataFrame(columns=["bucket", "n", "mean_pred", "actual_rate"]).to_csv(
                cal_dir / "sgp_reliability_by_bucket.csv", index=False
            )
    except Exception:
        pd.DataFrame(columns=["bucket", "n", "mean_pred", "actual_rate"]).to_csv(
            cal_dir / "sgp_reliability_by_bucket.csv", index=False
        )

    (cal_dir / "sgp_gate_status.json").write_text(
        json.dumps(gate_status, indent=2, sort_keys=True)
    )

    # ── 12. Market comparison outputs ─────────────────────────────────────────
    mkt_dir = sgp_root / "market_comparison"
    mkt_dir.mkdir(parents=True, exist_ok=True)

    if price_df is not None and not price_df.empty and market_comparison_available:
        price_df.to_parquet(mkt_dir / "sgp_market_comparison.parquet", index=False)
        price_df.to_csv(mkt_dir / "sgp_market_comparison.csv", index=False)
        edges_df = _publishable_edges(price_df)
        edges_df.to_csv(mkt_dir / "sgp_publishable_edges.csv", index=False)
    else:
        pd.DataFrame().to_parquet(mkt_dir / "sgp_market_comparison.parquet", index=False)
        pd.DataFrame().to_csv(mkt_dir / "sgp_market_comparison.csv", index=False)
        pd.DataFrame().to_csv(mkt_dir / "sgp_publishable_edges.csv", index=False)

    total_runtime = time.time() - t0
    print(f"\n[SGP] Done in {total_runtime:.1f}s")
    print(f"  Prices:      {prices_dir}")
    print(f"  Calibration: {cal_dir}")
    print(f"  Gate status: {gate_status['gate_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
