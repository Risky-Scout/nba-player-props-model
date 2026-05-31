from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .pmf import event_probability, parse_pmf
from .schema import SGPLeg, SGPTicket, prob_to_american, prob_to_decimal, calculate_ev
from .simulation import SimulationTape


# Combo stat → set of component direct stats that contribute to it algebraically.
# When a combo leg appears in a ticket alongside one of its component stats for
# the same player, the algebraic (non-anchored) tape value must be used to
# preserve joint consistency.  For standalone combo legs the rank-anchored tape
# value (stored as stat + "_anchored") should be used instead so that the
# simulated marginal matches the delivered calibrated combo PMF.
_COMBO_COMPONENTS: dict[str, frozenset[str]] = {
    "pa":     frozenset({"pts", "ast"}),
    "pr":     frozenset({"pts", "reb"}),
    "ra":     frozenset({"reb", "ast"}),
    "pra":    frozenset({"pts", "reb", "ast"}),
    "stocks": frozenset({"stl", "blk"}),
}

# Stats that have naturally sparse outcomes (few events per game).
_SPARSE_STATS = frozenset({"stl", "blk", "stocks"})


def _leg_hit(values: np.ndarray, line: float, side: str) -> np.ndarray:
    side_l = side.lower()
    if side_l in {"over", "o", ">", "gt"}:
        return values.astype(float) > float(line)
    if side_l in {"under", "u", "<", "lt"}:
        return values.astype(float) < float(line)
    if side_l in {"ge", ">="}:
        return values.astype(float) >= float(line)
    if side_l in {"le", "<="}:
        return values.astype(float) <= float(line)
    raise ValueError(f"Unknown leg side {side!r}")


def _binomial_ci(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    p = float(p)
    se = np.sqrt(max(p * (1 - p), 0.0) / max(int(n), 1))
    return max(0.0, p - z * se), min(1.0, p + z * se)


def _ticket_sgp_id(ticket: SGPTicket) -> str:
    """Stable hash of ticket contents for deduplication."""
    payload = json.dumps(asdict(ticket), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _classify_relationship(legs: list[SGPLeg]) -> str:
    """Classify the dependency relationship type of a set of SGP legs.

    Returns one of:
      same_player_cross_stat, same_player_combo_overlap,
      same_team_assist_chain, same_team_usage_competition,
      same_team_rebound_competition, same_team_minutes_substitution,
      opponent_pace_environment, game_script_close_game,
      sparse_defensive_activity, mixed
    """
    if not legs:
        return "mixed"

    player_ids = [str(leg.player_id) for leg in legs]
    stats = [leg.stat.lower() for leg in legs]
    unique_players = set(player_ids)

    if len(unique_players) == 1:
        # All same player.
        stat_set = set(stats)
        for combo, comps in _COMBO_COMPONENTS.items():
            if combo in stat_set and comps.intersection(stat_set - {combo}):
                return "same_player_combo_overlap"
        return "same_player_cross_stat"

    # Multiple players.
    team_ids = {str(leg.team_id) for leg in legs if leg.team_id}

    stat_set = set(stats)
    if _SPARSE_STATS.intersection(stat_set):
        if len(unique_players) > 1:
            return "sparse_defensive_activity"

    if len(team_ids) == 1:
        if "ast" in stat_set and "pts" in stat_set:
            return "same_team_assist_chain"
        if "reb" in stat_set:
            return "same_team_rebound_competition"
        if "minutes_mean" in stat_set or len(stat_set - {"pts", "reb", "ast", "fg3m"}) == 0:
            return "same_team_usage_competition"
        return "same_team_minutes_substitution"

    if len(team_ids) == 2:
        return "opponent_pace_environment"

    return "mixed"


def _assign_tier(
    marginal_gaps: list[float],
    any_pmf_invalid: bool,
    calibrated: bool,
    market_comparison_done: bool,
    n_sims: int,
    *,
    stats_in_ticket: set[str] | None = None,
) -> tuple[str, str | None]:
    """Assign a pricing tier and optional suppression reason.

    Returns:
        (tier, suppression_reason) where tier is one of:
        SUPPRESSED, CERTIFIED, MODEL_PRICE, DIAGNOSTIC_ONLY
    """
    if any_pmf_invalid:
        return "SUPPRESSED", "invalid_pmf"

    max_gap = max(abs(g) for g in marginal_gaps) if marginal_gaps else 0.0
    if max_gap > 0.05:
        return "SUPPRESSED", f"marginal_gap_{max_gap:.4f}_exceeds_0.05"

    if n_sims < 1000:
        return "DIAGNOSTIC_ONLY", "insufficient_simulations"

    if stats_in_ticket and _SPARSE_STATS.intersection(stats_in_ticket) and n_sims < 5000:
        return "DIAGNOSTIC_ONLY", "insufficient_sample_sparse_stat"

    if not calibrated:
        return "DIAGNOSTIC_ONLY", "no_calibrator_applied"

    if market_comparison_done:
        return "CERTIFIED", None

    return "MODEL_PRICE", None


def load_ticket(path: str | Path) -> SGPTicket:
    return SGPTicket.from_dict(json.loads(Path(path).read_text()))


def price_ticket(
    ticket: SGPTicket,
    tape: SimulationTape,
    pmf_df: pd.DataFrame,
    *,
    joint_calibrator: Any | None = None,
) -> dict[str, Any]:
    """Price an SGP ticket directly from the simulation tape.

    Marginal leg probabilities are estimated both from PMF atom sums and from simulated hits.
    PMF marginals are reported as the canonical marginal probability; simulation marginals are
    diagnostics for marginal preservation.

    Returns a dict with full output schema including tier, sgp_id, mc_standard_error,
    dependency_explanation_json, model_corr_factor, and optional market comparison fields.
    """
    if not ticket.legs:
        raise ValueError("Ticket has no legs")
    game_id = ticket.game_id or ticket.legs[0].game_id
    if game_id is None:
        games = {leg.game_id for leg in ticket.legs if leg.game_id}
        if len(games) == 1:
            game_id = next(iter(games))
        else:
            raise ValueError("Ticket game_id is required when legs do not all include one game_id")
    game_id = str(game_id)

    pmf_idx = {}
    for _, row in pmf_df.iterrows():
        pmf_idx[(str(row.get("game_id")), str(row.get("player_id")), str(row.get("stat")).lower())] = row

    ticket_stats_by_player: dict[tuple[str, str], set[str]] = {}
    for leg in ticket.legs:
        _pkey = (str(leg.game_id or game_id), str(leg.player_id))
        ticket_stats_by_player.setdefault(_pkey, set()).add(leg.stat.lower())

    hit_matrix = []
    leg_rows = []
    pmf_probs = []
    sim_probs = []

    for leg in ticket.legs:
        leg_game_id = str(leg.game_id or game_id)
        stat = leg.stat.lower()

        tape_stat = stat
        if stat in _COMBO_COMPONENTS:
            components = _COMBO_COMPONENTS[stat]
            other_stats = ticket_stats_by_player.get((leg_game_id, str(leg.player_id)), set()) - {stat}
            if not components.intersection(other_stats):
                anchored_key = stat + "_anchored"
                if tape.has(leg_game_id, leg.player_id, anchored_key):
                    tape_stat = anchored_key

        values = tape.get(leg_game_id, leg.player_id, tape_stat)
        hits = _leg_hit(values, leg.line, leg.side)
        hit_matrix.append(hits)
        sim_prob = float(hits.mean())
        sim_probs.append(sim_prob)

        pmf_prob = None
        row = pmf_idx.get((leg_game_id, str(leg.player_id), stat))
        if row is not None and "pmf_json" in row:
            try:
                pmf_prob = event_probability(
                    parse_pmf(row["pmf_json"], domain_max=row.get("domain_max")),
                    leg.line, leg.side,
                )
            except Exception:
                pmf_prob = None
        if pmf_prob is None:
            pmf_prob = sim_prob
        pmf_probs.append(float(pmf_prob))

        leg_rows.append({
            "player_id": leg.player_id,
            "stat": stat,
            "line": leg.line,
            "side": leg.side,
            "game_id": leg_game_id,
            "label": leg.label,
            "marginal_probability_pmf": float(pmf_prob),
            "marginal_probability_simulated": sim_prob,
            "marginal_gap_sim_minus_pmf": sim_prob - float(pmf_prob),
        })

    all_hit = np.logical_and.reduce(hit_matrix)
    raw_joint = float(all_hit.mean())

    # Calibration.
    calibrated_joint = raw_joint
    calibrator_id = None
    calibration_confidence: str | None = None
    if joint_calibrator is not None:
        if hasattr(joint_calibrator, "predict"):
            calibrated_joint = float(joint_calibrator.predict(np.array([raw_joint]).reshape(-1, 1))[0])
            calibrator_id = getattr(joint_calibrator, "calibrator_id", "external_predict")
            # Try to read cell count as proxy for calibration confidence.
            n_train = getattr(joint_calibrator, "n_train", None)
            if n_train is not None:
                calibration_confidence = "high" if n_train >= 1000 else ("medium" if n_train >= 300 else "low")
        elif callable(joint_calibrator):
            calibrated_joint = float(joint_calibrator(raw_joint, ticket))
            calibrator_id = getattr(joint_calibrator, "__name__", "callable")
    calibrated_joint = min(max(calibrated_joint, 1e-9), 1 - 1e-9)

    independent_pmf = float(np.prod(pmf_probs))
    independent_sim = float(np.prod(sim_probs))
    model_corr_factor = float(calibrated_joint / independent_pmf) if independent_pmf > 0 else np.nan

    # ── Market correlation baseline ────────────────────────────────────────────
    # Attempt to read per-leg no-vig market over probability from pmf_df.
    # Columns tried in order: market_over_prob, no_vig_over_prob, p_over_market.
    # Fallback: evaluate the model PMF at the delivered line (model's over prob).
    # The market's *SGP joint* is unobservable without actual SGP market prices,
    # so we use the independence assumption as the market baseline:
    #   market_corr_factor = 1.0  (market prices the joint as if legs are independent)
    #   corr_factor_delta_vs_market = model_corr_factor - 1.0
    # A positive delta means our model detects positive correlation not priced by
    # the market → the SGP is cheaper relative to its fair value than the market assumes.
    market_prob_cols = ("market_over_prob", "no_vig_over_prob", "p_over_market")
    market_marginal_probs: list[float] = []
    for leg in ticket.legs:
        leg_game_id_str = str(leg.game_id or game_id)
        pmf_row = pmf_idx.get((leg_game_id_str, str(leg.player_id), leg.stat.lower()))
        market_p: float | None = None
        if pmf_row is not None:
            for col in market_prob_cols:
                v = pmf_row.get(col)
                if v is not None and not (isinstance(v, float) and np.isnan(v)):
                    market_p = float(v)
                    break
        if market_p is None:
            # Fall back to model PMF evaluated at the leg's line — best available proxy.
            market_p = pmf_probs[ticket.legs.index(leg)] if ticket.legs.index(leg) < len(pmf_probs) else None
        if market_p is not None and 0 < market_p < 1:
            market_marginal_probs.append(market_p)

    if len(market_marginal_probs) == len(ticket.legs):
        market_independent_joint = float(np.prod(market_marginal_probs))
        # Market SGP corr factor defaults to 1.0 (independence baseline).
        # Will be overridden when actual market SGP prices are ingested.
        market_corr_factor: float = 1.0
        market_joint_price = market_independent_joint * market_corr_factor
        corr_factor_delta_vs_market = model_corr_factor - market_corr_factor if not np.isnan(model_corr_factor) else np.nan
    else:
        market_independent_joint = np.nan
        market_corr_factor = np.nan
        market_joint_price = np.nan
        corr_factor_delta_vs_market = np.nan

    ci_low, ci_high = _binomial_ci(calibrated_joint, tape.n_sims)
    mc_standard_error = float(np.sqrt(max(calibrated_joint * (1 - calibrated_joint), 0.0) / max(tape.n_sims, 1)))

    offered_decimal = ticket.offered_decimal_odds
    if offered_decimal is None and ticket.offered_american_odds is not None:
        from .schema import american_to_decimal
        offered_decimal = american_to_decimal(ticket.offered_american_odds)

    # Dependency classification.
    relationship_type = _classify_relationship(list(ticket.legs))

    # Marginal gap check for tier assignment.
    marginal_gaps = [row["marginal_gap_sim_minus_pmf"] for row in leg_rows]
    any_pmf_invalid = any(
        pmf_idx.get((str(leg.game_id or game_id), str(leg.player_id), leg.stat.lower()), {}).get("pmf_valid") is False
        for leg in ticket.legs
    )
    stats_in_ticket = {leg.stat.lower() for leg in ticket.legs}
    tier, suppression_reason = _assign_tier(
        marginal_gaps,
        any_pmf_invalid,
        calibrated=joint_calibrator is not None,
        market_comparison_done=False,
        n_sims=tape.n_sims,
        stats_in_ticket=stats_in_ticket,
    )

    result: dict[str, Any] = {
        "ticket_id": ticket.ticket_id,
        "sgp_id": _ticket_sgp_id(ticket),
        "game_id": game_id,
        "n_legs": len(ticket.legs),
        "simulation_count": tape.n_sims,
        "raw_joint_probability": raw_joint,
        "calibrated_joint_probability": calibrated_joint,
        "independent_probability_pmf_marginals": independent_pmf,
        "independent_probability_sim_marginals": independent_sim,
        "correlation_factor_vs_pmf_independence": model_corr_factor,
        "model_corr_factor": model_corr_factor,
        "market_corr_factor": market_corr_factor,
        "corr_factor_delta_vs_market": corr_factor_delta_vs_market,
        "market_independent_joint": market_independent_joint,
        "fair_decimal_odds": prob_to_decimal(calibrated_joint),
        "fair_american_odds": prob_to_american(calibrated_joint),
        "confidence_interval_95": {"low": ci_low, "high": ci_high},
        "mc_standard_error": mc_standard_error,
        "tier": tier,
        "suppression_reason": suppression_reason,
        "calibration_confidence": calibration_confidence,
        "dependency_explanation_json": relationship_type,
        "legs": leg_rows,
        "calibration": {
            "applied": joint_calibrator is not None,
            "calibrator_id": calibrator_id,
        },
    }
    if offered_decimal is not None:
        result["offered_decimal_odds"] = float(offered_decimal)
        result["ev"] = calculate_ev(calibrated_joint, float(offered_decimal))
    return result


def price_tickets_to_frame(
    tickets: list[SGPTicket],
    tape: SimulationTape,
    pmf_df: pd.DataFrame,
    *,
    joint_calibrator: Any | None = None,
) -> pd.DataFrame:
    rows = []
    for t in tickets:
        r = price_ticket(t, tape, pmf_df, joint_calibrator=joint_calibrator)
        flat = {k: v for k, v in r.items() if k not in {"legs", "confidence_interval_95", "calibration"}}
        flat["legs_json"] = json.dumps(r["legs"], sort_keys=True)
        flat["ci_low"] = r["confidence_interval_95"]["low"]
        flat["ci_high"] = r["confidence_interval_95"]["high"]
        flat["calibration_json"] = json.dumps(r["calibration"], sort_keys=True)
        rows.append(flat)
    return pd.DataFrame(rows)


def generate_sgp_candidates(
    pmf_df: pd.DataFrame,
    game_id: str,
    *,
    max_candidates: int = 500,
) -> list[SGPTicket]:
    """Generate 2-leg and 3-leg SGP ticket candidates for a given game.

    Produces:
      - Same-player cross-stat combos: pts+reb, pts+ast, pts+fg3m, pts+pra, reb+ast, stl+blk
      - Same-team cross-player combos: high-usage pts + teammate ast, etc.

    Lines are taken from ``line`` column in pmf_df when ``has_current_market_line`` is True,
    otherwise midpoint of support_min/support_max or PMF median.
    """
    gdf = pmf_df[pmf_df["game_id"].astype(str) == str(game_id)].copy()
    if gdf.empty:
        return []

    def _get_line(row: Any) -> float:
        # Prefer delivered market line when available.
        has_mkt = row.get("has_current_market_line", False)
        if has_mkt:
            line_val = row.get("line")
            if line_val is not None and not (isinstance(line_val, float) and np.isnan(line_val)):
                return float(line_val)
        # Fallback: midpoint of support domain.
        dmin = row.get("domain_min", row.get("support_min", 0)) or 0
        dmax = row.get("domain_max", row.get("support_max"))
        if dmax is not None and not (isinstance(dmax, float) and np.isnan(dmax)):
            return float((float(dmin) + float(dmax)) / 2.0)
        # Last resort: PMF mean.
        mean_v = row.get("mean")
        if mean_v is not None and not (isinstance(mean_v, float) and np.isnan(mean_v)):
            return float(mean_v)
        return 10.5

    tickets: list[SGPTicket] = []

    # Same-player combos.
    SAME_PLAYER_COMBOS = [
        ("pts", "reb"), ("pts", "ast"), ("pts", "fg3m"), ("pts", "pra"),
        ("reb", "ast"), ("stl", "blk"),
    ]
    for player_id, pgrp in gdf.groupby("player_id"):
        stat_rows = {str(r["stat"]).lower(): r for _, r in pgrp.iterrows()}
        for s1, s2 in SAME_PLAYER_COMBOS:
            if s1 not in stat_rows or s2 not in stat_rows:
                continue
            r1, r2 = stat_rows[s1], stat_rows[s2]
            team_id = str(r1.get("team_id") or "")
            tickets.append(SGPTicket.from_dict({
                "game_id": str(game_id),
                "legs": [
                    {"player_id": str(player_id), "stat": s1, "line": _get_line(r1), "side": "over",
                     "game_id": str(game_id), "team_id": team_id},
                    {"player_id": str(player_id), "stat": s2, "line": _get_line(r2), "side": "over",
                     "game_id": str(game_id), "team_id": team_id},
                ],
            }))
            if len(tickets) >= max_candidates:
                return tickets

    # Same-team cross-player combos: high-usage pts scorer + teammate ast creator.
    CROSS_PLAYER_PAIRS = [("pts", "ast"), ("pts", "reb"), ("ast", "reb")]
    for team_id, tgrp in gdf.groupby("team_id"):
        for s1, s2 in CROSS_PLAYER_PAIRS:
            players_s1 = tgrp[tgrp["stat"].astype(str).str.lower() == s1]
            players_s2 = tgrp[tgrp["stat"].astype(str).str.lower() == s2]
            if players_s1.empty or players_s2.empty:
                continue
            # Pick highest-mean player for each stat.
            r1 = players_s1.sort_values("mean", ascending=False, na_position="last").iloc[0]
            for _, r2 in players_s2.iterrows():
                if str(r2["player_id"]) == str(r1["player_id"]):
                    continue
                tickets.append(SGPTicket.from_dict({
                    "game_id": str(game_id),
                    "legs": [
                        {"player_id": str(r1["player_id"]), "stat": s1, "line": _get_line(r1),
                         "side": "over", "game_id": str(game_id), "team_id": str(team_id)},
                        {"player_id": str(r2["player_id"]), "stat": s2, "line": _get_line(r2),
                         "side": "over", "game_id": str(game_id), "team_id": str(team_id)},
                    ],
                }))
                if len(tickets) >= max_candidates:
                    return tickets

    return tickets[:max_candidates]
