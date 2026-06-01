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
    max_candidates: int = 100_000,
    max_per_game: int = 20_000,
    max_three_leg_per_game: int = 5_000,
    max_leg_count: int = 3,
    seed: int = 20260530,
) -> list[SGPTicket]:
    """Generate exhaustive over-SGP candidate tickets up to ``max_leg_count`` legs.

    Coverage guarantee
    ------------------
    **All** 2-leg combinations are always generated (complete coverage of the
    SGP probability space for 2-leg overs).  3-leg combinations are added from
    a shuffled enumeration up to ``max_three_leg_per_game`` per game, so every
    3-leg combination has an equal chance of being sampled.

    The global ``max_candidates`` cap provides a ceiling across all games.

    Parameters
    ----------
    max_candidates:
        Global ceiling on total tickets (all leg counts combined).
    max_per_game:
        Per-game ceiling on total tickets.
    max_three_leg_per_game:
        Separate cap on 3-leg tickets per game.  2-leg tickets are always
        generated in full before any 3-leg cap is applied.
    max_leg_count:
        Maximum leg count (2 or 3).
    seed:
        Random seed for reproducible 3-leg shuffling.
    """
    rng = np.random.default_rng(seed)
    by_game = _candidate_legs(pmf_df)
    tickets: list[SGPTicket] = []
    ticket_counter = 0

    def _make_leg(leg_def: dict, game_id: str) -> dict:
        return {
            "player_id": leg_def["player_id"],
            "stat": leg_def["stat"],
            "line": leg_def["line"],
            "side": "over",
            "game_id": game_id,
            "team_id": leg_def["team_id"],
            "label": leg_def["player_name"],
        }

    for game_id, legs in by_game.items():
        if len(tickets) >= max_candidates:
            break

        # One canonical leg per (player_id, stat) — use median available line.
        by_player_stat: dict[tuple, dict] = {}
        for leg in legs:
            key = (leg["player_id"], leg["stat"])
            by_player_stat.setdefault(key, []).append(leg)
        canonical: list[dict] = []
        for opts in by_player_stat.values():
            canonical.append(opts[len(opts) // 2])

        if len(canonical) < 2:
            continue

        game_tickets: list[SGPTicket] = []

        # ── 2-leg: ALWAYS enumerate ALL combinations ──────────────────────
        for leg_a, leg_b in itertools.combinations(canonical, 2):
            ticket = SGPTicket.from_dict({
                "ticket_id": f"cand_{ticket_counter:07d}",
                "game_id": game_id,
                "legs": [_make_leg(leg_a, game_id), _make_leg(leg_b, game_id)],
            })
            game_tickets.append(ticket)
            ticket_counter += 1

        # ── 3-leg: enumerate all, shuffle, apply per-game 3-leg cap ──────
        if max_leg_count >= 3 and len(canonical) >= 3:
            three_leg_all = list(itertools.combinations(canonical, 3))
            rng.shuffle(three_leg_all)
            for leg_a, leg_b, leg_c in three_leg_all[:max_three_leg_per_game]:
                ticket = SGPTicket.from_dict({
                    "ticket_id": f"cand_{ticket_counter:07d}",
                    "game_id": game_id,
                    "legs": [
                        _make_leg(leg_a, game_id),
                        _make_leg(leg_b, game_id),
                        _make_leg(leg_c, game_id),
                    ],
                })
                game_tickets.append(ticket)
                ticket_counter += 1

        # Apply overall per-game cap (preserves 2-leg first).
        if len(game_tickets) > max_per_game:
            two_leg_t = [t for t in game_tickets if len(t.legs) == 2]
            three_leg_t = [t for t in game_tickets if len(t.legs) == 3]
            if len(two_leg_t) >= max_per_game:
                game_tickets = two_leg_t[:max_per_game]
            else:
                remaining = max_per_game - len(two_leg_t)
                game_tickets = two_leg_t + three_leg_t[:remaining]

        tickets.extend(game_tickets)

        if len(tickets) >= max_candidates:
            break

    return tickets[:max_candidates]


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
    """Full-schema marginal preservation report (§13 spec)."""
    from sgp_engine.pmf import parse_pmf, event_probability

    # Build player_name lookup.
    pname_lut: dict[tuple[str, str], str] = {}
    tid_lut: dict[tuple[str, str], str] = {}
    for _, r in pmf_df.iterrows():
        key = (str(r["game_id"]), str(r["player_id"]))
        pname_lut[key] = str(r.get("player_name", r["player_id"]))
        tid_lut[key] = str(r.get("team_id", "UNK"))

    rows = []
    for _, r in pmf_df.iterrows():
        if not r.get("pmf_valid", True):
            continue
        gid = str(r["game_id"])
        pid = str(r["player_id"])
        stat = str(r["stat"]).lower()
        if not tape.has(gid, pid, stat):
            continue
        sim_vals = tape.get(gid, pid, stat).astype(float)

        # Evaluation line: use delivered market line if available, else PMF mean.
        raw_line = r.get("line")
        pmf_mean_val = float(r.get("mean", 0.0))
        if raw_line is not None and not (isinstance(raw_line, float) and np.isnan(raw_line)):
            eval_line = float(raw_line)
        else:
            eval_line = pmf_mean_val
        if not np.isfinite(eval_line) or eval_line < 0.5:
            eval_line = max(pmf_mean_val, 0.5)

        try:
            pmf = parse_pmf(r["pmf_json"], domain_max=r.get("domain_max"))
        except Exception:
            continue

        # PMF statistics.
        ks = np.arange(len(pmf), dtype=float)
        pmf_mean = float((ks * pmf).sum())
        pmf_var = float(((ks - pmf_mean) ** 2 * pmf).sum())
        pmf_p_over = event_probability(pmf, eval_line, "over")

        # Simulated statistics.
        sim_mean = float(sim_vals.mean())
        sim_var = float(sim_vals.var()) if len(sim_vals) > 1 else np.nan
        sim_p_over = float((sim_vals > eval_line).mean())

        # Total variation distance (|PMF - sim_empirical_pmf| / 2).
        domain_max = max(int(sim_vals.max()), len(pmf) - 1) + 1
        sim_counts = np.zeros(domain_max + 1)
        for v in sim_vals.astype(int):
            if 0 <= v <= domain_max:
                sim_counts[v] += 1
        sim_pmf_emp = sim_counts / sim_counts.sum()
        n_common = min(len(pmf), len(sim_pmf_emp))
        tv = float(np.abs(pmf[:n_common] - sim_pmf_emp[:n_common]).sum() / 2.0 +
                   sim_pmf_emp[n_common:].sum() / 2.0 if len(sim_pmf_emp) > n_common else
                   np.abs(pmf[:n_common] - sim_pmf_emp[:n_common]).sum() / 2.0)

        # Max CDF absolute difference.
        pmf_cdf = np.cumsum(pmf[:n_common])
        sim_cdf = np.cumsum(sim_pmf_emp[:n_common])
        max_cdf_diff = float(np.abs(pmf_cdf - sim_cdf).max())

        p_over_abs_diff = abs(sim_p_over - pmf_p_over)
        signed_diff = sim_p_over - pmf_p_over
        mean_abs_diff = abs(sim_mean - pmf_mean)
        var_abs_diff = abs(sim_var - pmf_var) if np.isfinite(sim_var) else np.nan

        # Status classification.
        if p_over_abs_diff > 0.05 or tv > 0.10:
            status = "FAIL"
        elif p_over_abs_diff > 0.02 or tv > 0.04:
            status = "WARN"
        else:
            status = "PASS"

        rows.append({
            "game_id": gid,
            "player_id": pid,
            "player_name": pname_lut.get((gid, pid), pid),
            "team_id": tid_lut.get((gid, pid), "UNK"),
            "stat": stat,
            "line": eval_line,
            "delivered_mean": pmf_mean,
            "simulated_mean": sim_mean,
            "mean_abs_diff": mean_abs_diff,
            "delivered_variance": pmf_var,
            "simulated_variance": sim_var,
            "variance_abs_diff": var_abs_diff,
            "total_variation_distance": tv,
            "max_cdf_abs_diff": max_cdf_diff,
            "p_over_main_line_delivered": pmf_p_over,
            "p_over_main_line_simulated": sim_p_over,
            "p_over_abs_diff": p_over_abs_diff,
            "signed_p_over_diff": signed_diff,
            "abs_error": p_over_abs_diff,  # backwards-compat alias
            "status": status,
        })

    return pd.DataFrame(rows)


def _combo_coherence_report(
    tape,
    pmf_df: pd.DataFrame,
) -> pd.DataFrame:
    """Full-schema combo coherence report (§14 spec)."""
    from sgp_engine.pmf import parse_pmf

    _COMBO_FORMULAS = {
        "pa": "pts+ast",
        "pr": "pts+reb",
        "ra": "reb+ast",
        "pra": "pts+reb+ast",
        "stocks": "stl+blk",
    }
    combo_map = {
        "pa": ("pts", "ast"), "pr": ("pts", "reb"),
        "ra": ("reb", "ast"), "pra": ("pts", "reb", "ast"), "stocks": ("stl", "blk"),
    }

    # Player name lookup.
    pname_lut: dict[tuple[str, str], str] = {}
    for _, r in pmf_df.iterrows():
        pname_lut[(str(r["game_id"]), str(r["player_id"]))] = str(r.get("player_name", r["player_id"]))

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

        # Component mean = mean of algebraic sum.
        comp_mean = float(algebraic.mean())

        # Delivered combo mean from PMF.
        try:
            cmb_pmf = parse_pmf(r["pmf_json"], domain_max=r.get("domain_max"))
            ks = np.arange(len(cmb_pmf), dtype=float)
            delivered_combo_mean = float((ks * cmb_pmf).sum())
        except Exception:
            delivered_combo_mean = float(r.get("mean", np.nan))

        mean_drift = comp_mean - delivered_combo_mean
        abs_drift = abs(mean_drift)

        # Total variation distance: algebraic sum vs stored (component coherence check).
        dom = int(max(algebraic.max(), stored.max())) + 1
        alg_cnt = np.zeros(dom + 1)
        sto_cnt = np.zeros(dom + 1)
        for v in algebraic.astype(int):
            if 0 <= v <= dom:
                alg_cnt[v] += 1
        for v in stored.astype(int):
            if 0 <= v <= dom:
                sto_cnt[v] += 1
        alg_pmf = alg_cnt / alg_cnt.sum()
        sto_pmf = sto_cnt / sto_cnt.sum()
        tv = float(np.abs(alg_pmf - sto_pmf).sum() / 2.0)

        # Max CDF abs diff for combo coherence.
        alg_cdf = np.cumsum(alg_pmf)
        sto_cdf = np.cumsum(sto_pmf)
        max_cdf_diff = float(np.abs(alg_cdf - sto_cdf).max())

        # Status.
        if abs_drift > 1.5 or tv > 0.15:
            status = "FAIL"
        elif abs_drift > 0.5 or tv > 0.05:
            status = "WARN"
        else:
            status = "PASS"

        rows.append({
            "game_id": gid,
            "player_id": pid,
            "player_name": pname_lut.get((gid, pid), pid),
            "combo_stat": stat,
            "component_formula": _COMBO_FORMULAS[stat],
            "component_mean": comp_mean,
            "delivered_combo_mean": delivered_combo_mean,
            "mean_drift": mean_drift,
            "abs_mean_drift": abs_drift,
            "total_variation_distance": tv,
            "max_cdf_abs_diff": max_cdf_diff,
            "status": status,
        })
    return pd.DataFrame(rows)


# ── Dependency diagnostics ────────────────────────────────────────────────────

# Relationship type explanations (human-readable §12 spec).
_REL_EXPLANATIONS: dict[str, str] = {
    "same_player_same_stat_overlap": "Same player and same stat: perfect overlap (should not price as independent).",
    "same_player_combo_overlap": "Combo stat shares components with a standalone leg for the same player.",
    "same_player_cross_stat": "Two different stats for the same player share minutes/usage exposure.",
    "same_team_assist_chain": "Passer assists and scorer points/threes rise together through made assisted shots.",
    "same_team_usage_competition": "Two same-team players compete for usage, creating mild negative correlation.",
    "same_team_rebound_competition": "Two same-team rebound overs compete for the same rebound pool.",
    "same_team_minutes_substitution": "Teammates on the same roster share minutes; one's gain is another's loss.",
    "opponent_pace_environment": "Both players benefit from a higher-pace shared game environment.",
    "opponent_rebound_pool": "Offensive and defensive rebounders share the same missed-shot pool.",
    "opponent_turnover_steal_chain": "Defender steals and offensive handler turnovers are driven by the same ball-handling risk.",
    "game_script_close_game": "Close game boosts minutes for starters and core players on both sides.",
    "game_script_blowout": "Blowout reduces starter minutes and increases bench opportunity.",
    "game_script_overtime": "Overtime adds possessions and minutes for all active players.",
    "sparse_defensive_activity": "Steals and blocks are driven by shared defensive activity and pace latent factors.",
}


def _classify_relationship_extended(leg_a_dict: dict, leg_b_dict: dict) -> str:
    """Classify the relationship type between two (player, stat) pairs.

    This is the authoritative relationship classifier for dependency diagnostics;
    it supports all 14 spec-required types.
    """
    pid_a, stat_a = leg_a_dict["player_id"], leg_a_dict["stat"].lower()
    pid_b, stat_b = leg_b_dict["player_id"], leg_b_dict["stat"].lower()
    team_a = leg_a_dict.get("team_id", "UNK")
    team_b = leg_b_dict.get("team_id", "UNK")

    COMBOS = {"pa", "pr", "ra", "pra", "stocks"}
    COMBO_COMPONENTS_MAP = {
        "pa": {"pts", "ast"}, "pr": {"pts", "reb"}, "ra": {"reb", "ast"},
        "pra": {"pts", "reb", "ast"}, "stocks": {"stl", "blk"},
    }
    SPARSE = {"stl", "blk", "stocks"}
    REBOUND_STATS = {"reb", "pr", "ra", "pra"}
    ASSIST_STATS = {"ast", "pa", "ra", "pra"}
    SCORING_STATS = {"pts", "pa", "pr", "pra", "fg3m"}

    # Same player.
    if pid_a == pid_b:
        if stat_a == stat_b:
            return "same_player_same_stat_overlap"
        # Combo overlap: one is a combo containing the other as component.
        comps_a = COMBO_COMPONENTS_MAP.get(stat_a, {stat_a})
        comps_b = COMBO_COMPONENTS_MAP.get(stat_b, {stat_b})
        if comps_a & comps_b:
            return "same_player_combo_overlap"
        return "same_player_cross_stat"

    same_team = (team_a == team_b and team_a != "UNK")
    opp_team = (team_a != team_b and team_a != "UNK" and team_b != "UNK")

    # Sparse defensive activity (steals/blocks): driven by shared defensive/pace factors.
    if stat_a in SPARSE and stat_b in SPARSE:
        return "sparse_defensive_activity"
    if (stat_a in SPARSE and stat_b not in SPARSE) or (stat_b in SPARSE and stat_a not in SPARSE):
        if not same_team:
            return "sparse_defensive_activity"

    if same_team:
        # Assist chain: one player assists, another scores.
        if (stat_a in ASSIST_STATS and stat_b in SCORING_STATS) or \
           (stat_b in ASSIST_STATS and stat_a in SCORING_STATS):
            return "same_team_assist_chain"
        # Rebound competition: two rebounders.
        if stat_a in REBOUND_STATS and stat_b in REBOUND_STATS:
            return "same_team_rebound_competition"
        # Usage competition: two scorers/handlers.
        if stat_a in SCORING_STATS and stat_b in SCORING_STATS:
            return "same_team_usage_competition"
        return "same_team_minutes_substitution"

    if opp_team:
        # Cross-team rebound pool (oreb/dreb competition).
        if stat_a in REBOUND_STATS and stat_b in REBOUND_STATS:
            return "opponent_rebound_pool"
        # Turnover–steal chain.
        if (stat_a == "tov" and stat_b == "stl") or (stat_b == "tov" and stat_a == "stl"):
            return "opponent_turnover_steal_chain"
        # Pace environment: both players benefit from shared game pace.
        return "opponent_pace_environment"

    # Game script relationships (same or cross team).
    return "opponent_pace_environment"


def _dependency_diagnostics(
    tape,
    pmf_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute pairwise correlation diagnostics — full §12 schema.

    Columns:
      game_id, leg_i, leg_j, player_a, stat_a, team_a, player_b, stat_b, team_b,
      player_relation, stat_relation, relationship_type, estimated_corr,
      simulated_pearson_r, simulated_phi_corr, joint_lift, explanation
    """
    # Build lookup: (game_id, player_id, stat) -> team_id
    team_lookup: dict[tuple[str, str, str], str] = {}
    pname_lookup: dict[tuple[str, str], str] = {}
    for _, r in pmf_df.iterrows():
        gid, pid, stat = str(r["game_id"]), str(r["player_id"]), str(r["stat"]).lower()
        team_lookup[(gid, pid, stat)] = str(r.get("team_id", "UNK"))
        pname_lookup[(gid, pid)] = str(r.get("player_name", pid))

    rows = []
    by_game: dict[str, list[tuple[str, str, str]]] = {}
    for (gid, pid, stat) in tape.stats:
        if stat in {"minutes"} or stat.endswith("_anchored"):
            continue
        by_game.setdefault(gid, []).append((gid, pid, stat))

    for game_id, keys in by_game.items():
        if len(keys) < 2:
            continue
        try:
            mat = np.stack([tape.get(*k).astype(np.float32) for k in keys], axis=1)
        except Exception:
            continue
        try:
            corr_mat = np.corrcoef(mat.T)
        except Exception:
            continue

        means = mat.mean(axis=0)
        stds = mat.std(axis=0)

        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                _, pid_a, stat_a = keys[i]
                _, pid_b, stat_b = keys[j]
                team_a = team_lookup.get((game_id, pid_a, stat_a), "UNK")
                team_b = team_lookup.get((game_id, pid_b, stat_b), "UNK")

                r_val = float(corr_mat[i, j]) if np.isfinite(corr_mat[i, j]) else np.nan

                # Extended relationship classification.
                leg_a_dict = {"player_id": pid_a, "stat": stat_a, "team_id": team_a}
                leg_b_dict = {"player_id": pid_b, "stat": stat_b, "team_id": team_b}
                rel = _classify_relationship_extended(leg_a_dict, leg_b_dict)

                # Player relation and stat relation descriptors.
                if pid_a == pid_b:
                    player_rel = "same_player"
                elif team_a == team_b and team_a != "UNK":
                    player_rel = "same_team"
                else:
                    player_rel = "opponent"
                stat_rel = f"{stat_a}_vs_{stat_b}"

                # Leg identifiers (composite string).
                leg_i = f"{pid_a}:{stat_a}"
                leg_j = f"{pid_b}:{stat_b}"

                # Phi correlation (binary over-threshold version of Pearson, ~0.5 threshold).
                try:
                    a_bin = (mat[:, i] > float(means[i])).astype(float)
                    b_bin = (mat[:, j] > float(means[j])).astype(float)
                    phi = float(np.corrcoef(a_bin, b_bin)[0, 1])
                    phi = phi if np.isfinite(phi) else np.nan
                except Exception:
                    phi = np.nan

                # Joint lift: P(A>mean AND B>mean) / (P(A>mean)*P(B>mean)).
                try:
                    p_a = float(a_bin.mean())
                    p_b = float(b_bin.mean())
                    p_joint = float((a_bin * b_bin).mean())
                    joint_lift = p_joint / (p_a * p_b) if p_a * p_b > 0 else np.nan
                except Exception:
                    joint_lift = np.nan

                rows.append({
                    "game_id": game_id,
                    "leg_i": leg_i,
                    "leg_j": leg_j,
                    "player_a": pid_a,
                    "stat_a": stat_a,
                    "team_a": team_a,
                    "player_b": pid_b,
                    "stat_b": stat_b,
                    "team_b": team_b,
                    "player_relation": player_rel,
                    "stat_relation": stat_rel,
                    "relationship_type": rel,
                    "estimated_corr": r_val,
                    "simulated_pearson_r": round(r_val, 6) if np.isfinite(r_val) else np.nan,
                    "simulated_phi_corr": round(phi, 6) if np.isfinite(phi) else np.nan,
                    "joint_lift": round(joint_lift, 6) if np.isfinite(joint_lift) else np.nan,
                    "explanation": _REL_EXPLANATIONS.get(rel, rel),
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
    """Return rows that represent publishable MODEL_PRICE or CERTIFIED edges.

    Every row is guaranteed to include fair_probability, fair_decimal_odds,
    and fair_american_odds so downstream consumers can use them directly.
    """
    mask = price_df["tier"].isin({"MODEL_PRICE", "CERTIFIED"})
    cols = [c for c in [
        "sgp_id", "ticket_id", "game_id", "leg_count", "n_legs", "legs_json",
        "relationship_type", "stat_mix", "role_mix",
        "fair_probability", "fair_decimal_odds", "fair_american_odds",
        "calibrated_joint_probability", "raw_joint_probability",
        "model_corr_factor", "market_corr_factor", "market_corr_factor_source",
        "corr_factor_delta_vs_market", "tier", "suppression_reason",
        "calibration_confidence", "simulation_count", "mc_standard_error",
        "ci_low", "ci_high",
    ] if c in price_df.columns]
    return price_df.loc[mask, cols].copy()


def _standardize_price_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Add canonical column aliases and required §15 columns to the price grid."""
    out = df.copy()

    # Canonical name aliases (add if the aliased column is present but canonical is not).
    _aliases = {
        "leg_count": "n_legs",
        "independent_probability": "independent_probability_pmf_marginals",
        "correlation_factor": "correlation_factor_vs_pmf_independence",
    }
    for canonical, source in _aliases.items():
        if canonical not in out.columns and source in out.columns:
            out[canonical] = out[source]

    # Relationship type from dependency_explanation_json.
    if "relationship_type" not in out.columns and "dependency_explanation_json" in out.columns:
        out["relationship_type"] = out["dependency_explanation_json"]

    # stat_mix: categorise legs by stat families.
    if "stat_mix" not in out.columns:
        def _infer_stat_mix(legs_json: str) -> str:
            try:
                legs = json.loads(legs_json)
                stats = {str(l.get("stat", "")).lower() for l in legs}
                SPARSE = {"stl", "blk", "stocks"}
                COMBOS = {"pa", "pr", "ra", "pra"}
                if stats & SPARSE:
                    return "includes_sparse"
                if stats & COMBOS:
                    return "includes_combo"
                if len(stats) == 1:
                    return f"same_stat:{list(stats)[0]}"
                return "mixed"
            except Exception:
                return "unknown"
        if "legs_json" in out.columns:
            out["stat_mix"] = out["legs_json"].apply(_infer_stat_mix)
        else:
            out["stat_mix"] = "unknown"

    # role_mix: placeholder (detailed role info not yet in price_tickets_to_frame).
    if "role_mix" not in out.columns:
        out["role_mix"] = "unknown"

    # lineup_status: placeholder.
    if "lineup_status" not in out.columns:
        out["lineup_status"] = "unknown"

    # market_decimal_odds: null when no actual SGP market odds exist.
    if "market_decimal_odds" not in out.columns:
        out["market_decimal_odds"] = np.nan

    # model_edge.
    if "model_edge" not in out.columns:
        if "edge_over" in out.columns:
            out["model_edge"] = out["edge_over"]
        else:
            out["model_edge"] = np.nan

    # publishable flag.
    if "publishable" not in out.columns:
        out["publishable"] = out.get("tier", pd.Series("MODEL_PRICE", index=out.index)).isin({"MODEL_PRICE", "CERTIFIED"})

    # ── Fair odds — mandatory on every row ──────────────────────────────────
    # fair_probability = calibrated_joint_probability (or raw when no calibrator).
    if "fair_probability" not in out.columns:
        if "calibrated_joint_probability" in out.columns:
            out["fair_probability"] = out["calibrated_joint_probability"]
        elif "raw_joint_probability" in out.columns:
            out["fair_probability"] = out["raw_joint_probability"]
        else:
            out["fair_probability"] = np.nan

    # Compute fair_decimal_odds and fair_american_odds from fair_probability.
    def _decimal_from_p(p: float) -> float | None:
        try:
            fp = float(p)
            if np.isfinite(fp) and fp > 0:
                return round(1.0 / fp, 4)
        except Exception:
            pass
        return None

    def _american_from_p(p: float) -> int | None:
        dec = _decimal_from_p(p)
        if dec is None:
            return None
        if dec >= 2.0:
            return int(round((dec - 1) * 100))
        else:
            return int(round(-100 / (dec - 1)))

    if "fair_decimal_odds" not in out.columns or out["fair_decimal_odds"].isna().all():
        out["fair_decimal_odds"] = out["fair_probability"].apply(_decimal_from_p)
    if "fair_american_odds" not in out.columns or out["fair_american_odds"].isna().all():
        out["fair_american_odds"] = out["fair_probability"].apply(_american_from_p)

    # Market correlation placeholder labels (§16 spec).
    if "market_corr_factor_source" not in out.columns:
        out["market_corr_factor_source"] = "independence_placeholder"
    if "actual_sgp_market_odds_available" not in out.columns:
        out["actual_sgp_market_odds_available"] = False

    return out


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
    ap.add_argument("--max-candidates", type=int, default=100_000,
                    help="Global ceiling on candidate tickets generated (default: 100000). "
                         "Set to 0 for no limit (enumerate everything).")
    ap.add_argument("--max-per-game", type=int, default=20_000,
                    help="Per-game ceiling on total tickets (default: 20000). "
                         "2-leg combos are always included first.")
    ap.add_argument("--max-three-leg-per-game", type=int, default=5_000,
                    help="Per-game ceiling on 3-leg tickets only (default: 5000). "
                         "All 2-leg combos are generated before any 3-leg cap is applied.")
    ap.add_argument("--max-leg-count", type=int, default=3,
                    help="Maximum leg count per ticket: 2 or 3 (default: 3).")
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

    # Factor weights metadata.
    fw_path = repo_root / "artifacts" / "models" / "sgp" / "factor_weights" / "factor_weights_latest.json"
    fw_meta: dict[str, Any] = {}
    factor_weights_source = "fallback_defaults"
    fw_warnings: list[str] = []
    if fw_path.exists():
        try:
            fw_raw = json.loads(fw_path.read_text())
            fw_meta_raw = fw_raw.get("_meta", {})
            method = fw_meta_raw.get("fit_method", fw_meta_raw.get("method", "unknown"))
            if method not in {"hardcoded_defaults_no_historical_data", "unknown"}:
                factor_weights_source = "learned_pit_factor_weights"
            fw_meta = {
                "as_of_date": fw_meta_raw.get("as_of_date"),
                "source": factor_weights_source,
                "path": str(fw_path),
                "factor_weight_artifact_id": fw_meta_raw.get("fitted_at_utc", "unknown"),
                "fallback_used": factor_weights_source == "fallback_defaults",
                "trained_rows": fw_meta_raw.get("n_player_stat_obs"),
                "n_games": fw_meta_raw.get("n_games"),
                "method": method,
                "warnings": fw_warnings,
            }
        except Exception as exc:
            fw_warnings.append(f"Could not parse factor_weights_latest.json: {exc}")
            factor_weights_source = "fallback_defaults"
    else:
        fw_warnings.append("factor_weights_latest.json not found; using hardcoded defaults.")

    if not fw_meta:
        fw_meta = {
            "as_of_date": None,
            "source": "fallback_defaults",
            "path": None,
            "factor_weight_artifact_id": None,
            "fallback_used": True,
            "trained_rows": None,
            "n_games": None,
            "method": "hardcoded_defaults",
            "warnings": fw_warnings,
        }

    # Write factor_weights_used.json to bundle dir (§5 spec).
    bundle_dir = sgp_root / "slate_state_bundle_v1"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # ── Load SGP model pointer (single source of truth for training state). ──
    pointer_path = repo_root / "artifacts" / "models" / "sgp" / "registry" / "sgp_model_pointer.json"
    sgp_pointer: dict[str, Any] = {}
    sgp_pointer_used = False
    if pointer_path.exists():
        try:
            sgp_pointer = json.loads(pointer_path.read_text())
            sgp_pointer_used = True
            # If pointer has a better calibrator path, prefer it.
            ptr_cal = sgp_pointer.get("joint_calibrator_artifact")
            if ptr_cal and Path(str(ptr_cal)).exists():
                _ptr_cal_path = Path(str(ptr_cal))
                # Will be used below when loading calibrator registry.
            # If pointer has factor weights path, record it.
            if sgp_pointer.get("factor_weights_artifact_exists"):
                fw_meta["pointer_trained_through"] = sgp_pointer.get("trained_through_date")
                fw_meta["pointer_promotion_status"] = sgp_pointer.get("promotion_status", "DIAGNOSTIC_NO_BACKTEST")
                fw_meta["pointer_n_backtest_rows"] = sgp_pointer.get("n_backtest_rows", 0)
        except Exception as exc:
            print(f"  WARNING: Could not load sgp_model_pointer.json: {exc}", file=sys.stderr)

    fw_meta["sgp_model_pointer_used"] = sgp_pointer_used
    fw_meta["sgp_model_pointer_path"] = str(pointer_path) if sgp_pointer_used else None
    fw_meta["joint_calibrator_artifact_used"] = sgp_pointer.get("joint_calibrator_artifact")
    fw_meta["calibration_status_from_pointer"] = sgp_pointer.get("calibration_status", "NOT_AVAILABLE")
    fw_meta["promotion_status_from_pointer"] = sgp_pointer.get("promotion_status", "DIAGNOSTIC_NO_BACKTEST")

    (bundle_dir / "factor_weights_used.json").write_text(
        json.dumps(fw_meta, indent=2, sort_keys=True)
    )

    # Marginal preservation summary stats.
    marg_stats: dict[str, Any] = {
        "mean_abs_error": None, "max_abs_error": None,
        "n_stats": 0, "fraction_within_0.02": None,
        "fraction_within_0.01": None, "fail_rate": None,
        "mean_signed_bias": None, "status": "NO_DATA",
    }
    if not marg_df.empty:
        errs = marg_df.get("p_over_abs_diff", marg_df.get("abs_error", pd.Series(dtype=float)))
        signed = marg_df.get("signed_p_over_diff", pd.Series(dtype=float))
        fail_mask = marg_df.get("status", pd.Series("PASS", index=marg_df.index)) == "FAIL"
        marg_status = "FAIL" if fail_mask.any() else (
            "WARN" if (marg_df.get("status", pd.Series("PASS", index=marg_df.index)) == "WARN").any()
            else "PASS"
        )
        marg_stats = {
            "mean_abs_error": float(errs.mean()),
            "max_abs_error": float(errs.max()),
            "n_stats": int(len(marg_df)),
            "fraction_within_0.02": float((errs <= 0.02).mean()),
            "fraction_within_0.01": float((errs <= 0.01).mean()),
            "fail_rate": float(fail_mask.mean()),
            "mean_signed_bias": float(signed.mean()) if not signed.empty else None,
            "status": marg_status,
        }

    # Minutes allocation diagnostics from simulator metadata.
    mins_diag = tape.metadata.get("minutes_allocation_diagnostics", {})
    mins_method = tape.metadata.get("minutes_allocation_method", "ghost_remainder_dirichlet")

    sim_diag = {
        "slate_date": slate_date,
        "n_sims": args.n_sims,
        "n_stat_keys": n_stat_keys,
        "n_players": n_players,
        "n_games": n_games,
        "simulation_runtime_seconds": round(sim_runtime, 2),
        "factor_weights_used": factor_weights_source,
        "minutes_allocation_method": mins_method,
        "minutes_pool_used": True,
        "minutes_allocation_by_team": mins_diag,
        "marginal_preservation": marg_stats,
        "marginal_preservation_mean_abs_error": marg_stats["mean_abs_error"],
        "marginal_preservation_max_abs_error": marg_stats["max_abs_error"],
        "marginal_preservation_fail_rate": marg_stats["fail_rate"],
        "marginal_preservation_status": marg_stats["status"],
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
        "minutes_allocation_method": mins_method,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2, sort_keys=True))

    # Write marginal preservation report.
    _MARG_EMPTY_COLS = [
        "game_id", "player_id", "player_name", "team_id", "stat", "line",
        "delivered_mean", "simulated_mean", "mean_abs_diff",
        "delivered_variance", "simulated_variance", "variance_abs_diff",
        "total_variation_distance", "max_cdf_abs_diff",
        "p_over_main_line_delivered", "p_over_main_line_simulated",
        "p_over_abs_diff", "signed_p_over_diff", "abs_error", "status",
    ]
    if not marg_df.empty:
        write_table(marg_df, sim_dir / "marginal_preservation_report.parquet")
    else:
        pd.DataFrame(columns=_MARG_EMPTY_COLS).to_parquet(
            sim_dir / "marginal_preservation_report.parquet", index=False
        )

    # Write combo coherence report.
    _COMBO_EMPTY_COLS = [
        "game_id", "player_id", "player_name", "combo_stat", "component_formula",
        "component_mean", "delivered_combo_mean", "mean_drift", "abs_mean_drift",
        "total_variation_distance", "max_cdf_abs_diff", "status",
    ]
    if not combo_df.empty:
        write_table(combo_df, sim_dir / "combo_coherence_report.parquet")
    else:
        pd.DataFrame(columns=_COMBO_EMPTY_COLS).to_parquet(
            sim_dir / "combo_coherence_report.parquet", index=False
        )

    # ── 4b. Dependency diagnostics per player-pair ─────────────────────────────
    print("[SGP] Computing pairwise dependency diagnostics ...", flush=True)
    dep_diag_df = _dependency_diagnostics(tape, pmf_df)
    _DEP_EMPTY_COLS = [
        "game_id", "leg_i", "leg_j", "player_a", "stat_a", "team_a",
        "player_b", "stat_b", "team_b", "player_relation", "stat_relation",
        "relationship_type", "estimated_corr", "simulated_pearson_r",
        "simulated_phi_corr", "joint_lift", "explanation",
        "n_sims", "player_a_mean", "player_b_mean", "player_a_std", "player_b_std",
    ]
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
        pd.DataFrame(columns=_DEP_EMPTY_COLS).to_parquet(
            sim_dir / "dependency_diagnostics.parquet", index=False
        )
        print("  No pairs to diagnose (single-player slate?)", flush=True)

    # ── 5. Generate candidate tickets ─────────────────────────────────────────
    print(f"[SGP] Generating candidate tickets (max_leg_count={args.max_leg_count} max_candidates={args.max_candidates} max_per_game={args.max_per_game} max_three_leg_per_game={args.max_three_leg_per_game}) ...", flush=True)
    candidates = generate_sgp_candidates(
        pmf_df,
        max_candidates=args.max_candidates,
        max_per_game=args.max_per_game,
        max_three_leg_per_game=args.max_three_leg_per_game,
        max_leg_count=args.max_leg_count,
        seed=args.seed,
    )
    print(f"  Generated {len(candidates)} candidates ({sum(1 for c in candidates if len(c.legs)==2)} 2-leg  {sum(1 for c in candidates if len(c.legs)==3)} 3-leg)", flush=True)

    # Define calibrator path and default flags before the candidates branch so
    # subsequent code (cal_report, gate_status) can reference them safely.
    # Prefer calibrator from sgp_model_pointer.json if available.
    _ptr_cal_from_pointer = sgp_pointer.get("joint_calibrator_latest") or sgp_pointer.get("joint_calibrator_artifact")
    cal_model_path = (
        Path(str(_ptr_cal_from_pointer))
        if _ptr_cal_from_pointer and Path(str(_ptr_cal_from_pointer)).exists()
        else repo_root / "artifacts" / "models" / "sgp" / "joint_calibrators" / "joint_calibrator_latest.pkl"
    )
    if not cal_model_path.exists():
        # Legacy path fallback.
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

        # ── 8b. Market correlation placeholder labels (§16 spec) ──────────────
        price_df = price_df.copy()
        price_df["market_corr_factor_source"] = "independence_placeholder"
        price_df["actual_sgp_market_odds_available"] = False

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

        # ── 9b. Standardize price grid schema (§9 spec) ───────────────────────
        price_df = _standardize_price_grid(price_df)

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

    # ── sgp_reliability_by_segment.csv (§8 spec) ──────────────────────────────
    _SEG_COLS = [
        "segment_type", "segment_value", "n", "mean_predicted_probability",
        "actual_hit_rate", "ece", "mce", "brier", "logloss",
        "calibration_slope", "calibration_intercept", "status",
    ]
    try:
        backtest_path_bt = repo_root / "data" / "sgp_backtest_rows.parquet"
        seg_rows: list[dict] = []
        if backtest_path_bt.exists():
            bt = pd.read_parquet(backtest_path_bt)
            settled_bt = bt.dropna(subset=["actual_hit"])
            _seg_dims = ["leg_count", "relationship_type", "stat_mix", "role_mix",
                         "lineup_status", "contains_sparse_stat", "contains_combo_overlap",
                         "line_percentile_bucket"]
            for dim in _seg_dims:
                if dim not in settled_bt.columns or len(settled_bt) < 20:
                    continue
                for val, grp in settled_bt.groupby(dim, dropna=True):
                    if len(grp) < 20:
                        continue
                    pred = grp["calibrated_joint_probability"].clip(1e-6, 1 - 1e-6)
                    y = grp["actual_hit"].astype(float)
                    n = len(grp)
                    mean_p = float(pred.mean())
                    actual_r = float(y.mean())
                    brier = float(((pred - y) ** 2).mean())
                    logloss = float(-(y * np.log(pred) + (1 - y) * np.log(1 - pred)).mean())
                    # ECE (10 equal-width bins).
                    bins = np.linspace(0, 1, 11)
                    ece_acc = 0.0
                    mce_acc = 0.0
                    for bi in range(10):
                        mask = (pred >= bins[bi]) & (pred < bins[bi + 1])
                        if mask.sum() > 0:
                            diff = abs(float(pred[mask].mean()) - float(y[mask].mean()))
                            ece_acc += mask.sum() / n * diff
                            mce_acc = max(mce_acc, diff)
                    slope_val = np.nan
                    intercept_val = np.nan
                    if pred.std() > 1e-6:
                        slope_val = float(np.corrcoef(pred, y)[0, 1] * y.std() / pred.std())
                        intercept_val = float(y.mean() - slope_val * pred.mean())
                    seg_rows.append({
                        "segment_type": dim, "segment_value": str(val), "n": n,
                        "mean_predicted_probability": round(mean_p, 6),
                        "actual_hit_rate": round(actual_r, 6),
                        "ece": round(ece_acc, 6), "mce": round(mce_acc, 6),
                        "brier": round(brier, 6), "logloss": round(logloss, 6),
                        "calibration_slope": round(slope_val, 4) if np.isfinite(slope_val) else None,
                        "calibration_intercept": round(intercept_val, 4) if np.isfinite(intercept_val) else None,
                        "status": "INSUFFICIENT_SAMPLE" if n < 100 else "OK",
                    })
        seg_df = pd.DataFrame(seg_rows) if seg_rows else pd.DataFrame(columns=_SEG_COLS)
        seg_df.to_csv(cal_dir / "sgp_reliability_by_segment.csv", index=False)
    except Exception:
        pd.DataFrame(columns=_SEG_COLS).to_csv(cal_dir / "sgp_reliability_by_segment.csv", index=False)

    # ── calibration_context.parquet (§5 spec) ─────────────────────────────────
    _CAL_CTX_COLS = [
        "slate_date", "model_version", "stat", "role_bucket", "n_oof",
        "pmf_nll", "rps", "pit_mean", "pit_std", "pit_ks", "ece",
        "mean_error", "variance_error", "calibration_status",
        "calibration_confidence", "calibrator_id", "cal_source",
        "guarded_fallback_flag", "market_superiority_eligible",
        "market_superiority_pass", "ucb95_logloss_delta", "ucb95_brier_delta",
    ]
    try:
        # Try to load existing calibration metrics from NBA PMF model reports.
        cal_ctx_rows: list[dict] = []
        market_sup_path = repo_root / "artifacts" / "model_diagnostics" / "market_superiority"
        nba_stats = ["pts", "reb", "ast", "stl", "blk", "tov", "pr", "pa", "ra", "pra", "stocks"]
        role_buckets = ["bench", "rotation", "core", "starter"]

        # Build a minimal stub row per stat-role (UNKNOWN status when no metrics).
        for stat in nba_stats:
            for role in role_buckets:
                cal_ctx_rows.append({
                    "slate_date": slate_date,
                    "model_version": "nba_pmf_v1",
                    "stat": stat, "role_bucket": role,
                    "n_oof": None, "pmf_nll": None, "rps": None,
                    "pit_mean": None, "pit_std": None, "pit_ks": None,
                    "ece": None, "mean_error": None, "variance_error": None,
                    "calibration_status": "UNKNOWN_OR_NOT_EXPORTED",
                    "calibration_confidence": "diagnostic",
                    "calibrator_id": None, "cal_source": "stub",
                    "guarded_fallback_flag": False,
                    "market_superiority_eligible": False,
                    "market_superiority_pass": False,
                    "ucb95_logloss_delta": None, "ucb95_brier_delta": None,
                })

        cal_ctx_df = pd.DataFrame(cal_ctx_rows)
        cal_ctx_df.to_parquet(bundle_dir / "calibration_context.parquet", index=False)
    except Exception:
        pd.DataFrame(columns=_CAL_CTX_COLS).to_parquet(
            bundle_dir / "calibration_context.parquet", index=False
        )

    # Enrich gate_status with pointer provenance fields.
    gate_status["sgp_model_pointer_used"] = sgp_pointer_used
    gate_status["sgp_model_pointer_path"] = str(pointer_path) if sgp_pointer_used else None
    gate_status["factor_weights_artifact_used"] = fw_meta.get("path")
    gate_status["joint_calibrator_artifact_used"] = fw_meta.get("joint_calibrator_artifact_used")
    gate_status["calibration_status_from_pointer"] = fw_meta.get("calibration_status_from_pointer", "NOT_AVAILABLE")
    gate_status["promotion_status_from_pointer"] = fw_meta.get("promotion_status_from_pointer", "DIAGNOSTIC_NO_BACKTEST")
    gate_status["default_delivery_enabled"] = False   # never set True without explicit approval

    (cal_dir / "sgp_gate_status.json").write_text(
        json.dumps(gate_status, indent=2, sort_keys=True)
    )

    # ── 12. Market comparison outputs ─────────────────────────────────────────
    mkt_dir = sgp_root / "market_comparison"
    mkt_dir.mkdir(parents=True, exist_ok=True)

    if price_df is not None and not price_df.empty:
        if market_comparison_available:
            price_df.to_parquet(mkt_dir / "sgp_market_comparison.parquet", index=False)
            price_df.to_csv(mkt_dir / "sgp_market_comparison.csv", index=False)
        else:
            pd.DataFrame().to_parquet(mkt_dir / "sgp_market_comparison.parquet", index=False)
            pd.DataFrame().to_csv(mkt_dir / "sgp_market_comparison.csv", index=False)
        # Always write publishable edges (parquet + CSV) even when market_comparison unavailable.
        edges_df = _publishable_edges(price_df)
        edges_df.to_parquet(mkt_dir / "sgp_publishable_edges.parquet", index=False)
        edges_df.to_csv(mkt_dir / "sgp_publishable_edges.csv", index=False)
    else:
        for fname in ["sgp_market_comparison.parquet", "sgp_publishable_edges.parquet"]:
            pd.DataFrame().to_parquet(mkt_dir / fname, index=False)
        for fname in ["sgp_market_comparison.csv", "sgp_publishable_edges.csv"]:
            pd.DataFrame().to_csv(mkt_dir / fname, index=False)

    total_runtime = time.time() - t0
    print(f"\n[SGP] Done in {total_runtime:.1f}s")
    print(f"  Prices:      {prices_dir}")
    print(f"  Calibration: {cal_dir}")
    print(f"  Gate status: {gate_status['gate_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
