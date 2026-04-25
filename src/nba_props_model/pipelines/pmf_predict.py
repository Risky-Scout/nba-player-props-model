"""
NBA Props Model — PMF-first prediction orchestration.

Glue layer that turns feature rows into calibrated PMFs via the new
architecture and runs the bet-selection module against offered lines.
Invoked from scripts/predict.py when the calibrated-PMF artifacts are
present; falls back silently when they aren't so the live path stays
functional during the migration window.

Pipeline per prop
-----------------
  1. MinutesDistribution from state-aware minutes model
  2. Main-stat PMFs from minutes x rate simulation
  3. Sparse-stat PMFs from hurdle models; stocks by component convolution
  4. FG3M PMF from the hurdle model's pmf() method
  5. Combo PMFs (pra, pr, pa, ra) derived from component PMFs via copula
  6. Apply per-stat pmf_calibration if trained
  7. Convert to fair over/under at each offered line
  8. Bet-selection filter against market prices

Outputs a DataFrame suitable for writing to
predictions/all_props_{date}.parquet and predictions/singles_{date}.json.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from nba_props_model.calibration.pmf_calibration import load_calibrator
from nba_props_model.calibration.role_buckets import role_bucket_from_minutes_dist
from nba_props_model.models import combos, simulation, sparse_hurdle
from nba_props_model.models.minutes import MinutesDistribution, minutes_distribution
from nba_props_model.selection.bet_selection import (
    BetCandidate,
    SelectionThresholds,
    decide,
)

logger = logging.getLogger(__name__)


MAIN_STATS = ("pts", "reb", "ast", "tov")
SPARSE_STATS = ("stl", "blk")
COMBO_STATS = tuple(combos.COMBO_COMPONENTS.keys())


@dataclass
class PropPMF:
    stat: str
    pmf: np.ndarray
    calibrated: bool
    model_version: str


# ── Per-player PMF build ─────────────────────────────────────────────────────


def build_prop_pmfs(
    minutes_dist: MinutesDistribution,
    feature_row: dict,
    fg3m_hurdle_model=None,
    rng: Optional[np.random.Generator] = None,
) -> dict[str, PropPMF]:
    """Build the full per-stat PMF collection for one player-game.

    Returns `{stat: PropPMF}` keyed by stat name. Missing artifacts
    silently drop their stat from the output.
    """
    if rng is None:
        rng = np.random.default_rng()
    out: dict[str, PropPMF] = {}

    # Main stats via minutes x rate.
    main_pmfs = simulation.simulate_all_main_stats(
        minutes_dist=minutes_dist, feature_row=feature_row,
        n_draws=5_000, rng=rng,
    )
    for stat, spmf in main_pmfs.items():
        out[stat] = PropPMF(stat=stat, pmf=spmf.pmf, calibrated=False,
                            model_version="pmf_sim_v1")

    # Sparse stats via hurdle.
    for stat in SPARSE_STATS:
        pmf = sparse_hurdle.hurdle_pmf(stat, feature_row)
        if pmf is not None:
            out[stat] = PropPMF(stat=stat, pmf=pmf, calibrated=False,
                                model_version="hurdle_v1")

    # stocks = convolution of stl + blk.
    if "stl" in out and "blk" in out:
        stocks_arr = sparse_hurdle.stocks_pmf(out["stl"].pmf, out["blk"].pmf)
        if stocks_arr is not None:
            out["stocks"] = PropPMF(
                stat="stocks", pmf=stocks_arr, calibrated=False,
                model_version="stocks_conv_v1",
            )

    # FG3M via hurdle's pmf().
    if fg3m_hurdle_model is not None:
        try:
            fg3m_pmf = fg3m_hurdle_model.pmf(feature_row)
            out["fg3m"] = PropPMF(stat="fg3m", pmf=fg3m_pmf, calibrated=False,
                                  model_version="fg3m_hurdle_v1")
        except Exception as e:
            logger.debug(f"fg3m pmf failed: {e}")

    # Combos — only if all components available.
    main_stat_pmfs = {k: simulation.StatPMF(stat=k, pmf=out[k].pmf)
                      for k in ("pts", "reb", "ast") if k in out}
    for combo_key, component_stats in combos.COMBO_COMPONENTS.items():
        if not all(s in main_stat_pmfs for s in component_stats):
            continue
        comp_map = {s: main_stat_pmfs[s] for s in component_stats}
        combo_pmf = combos.build_combo_pmf(
            combo_key, comp_map, correlation=None, rng=rng,
        )
        if combo_pmf is not None:
            out[combo_key] = PropPMF(
                stat=combo_key, pmf=combo_pmf.pmf, calibrated=False,
                model_version="combo_independence_v1",
            )

    # Ex-ante role bucket: depends only on the predicted minutes
    # distribution, never on realized minutes or outcomes. Used as the
    # calibrator key for role-aware bundles.
    role_bucket = role_bucket_from_minutes_dist(minutes_dist)

    # Apply per-stat PMF calibration if present. Detect role-aware
    # bundles explicitly via the bundle's `version` attribute — no
    # broad TypeError fallback, so a real bug inside apply() surfaces
    # rather than silently routing to the legacy branch.
    for stat, prop in out.items():
        cal = load_calibrator(stat)
        if cal is None:
            continue
        if getattr(cal, "version", None) == "role_aware_pmf_cal_v1":
            cal_pmf = cal.apply(prop.pmf, role_bucket=role_bucket)
            version_tag = f"role_aware_pmf_cal_v1:{role_bucket}"
        else:
            cal_pmf = cal.apply(prop.pmf)
            version_tag = "pmf_cal_v1"
        out[stat] = PropPMF(
            stat=stat, pmf=cal_pmf, calibrated=True,
            model_version=f"{prop.model_version}+{version_tag}",
        )
    return out


# ── Scoring to offered lines ────────────────────────────────────────────────


def score_prop_line(pmf: np.ndarray, line: float) -> tuple[float, float]:
    """Return P(over), P(under) for an integer-valued stat PMF.

    For standard half-point NBA prop lines:
        over hits iff Y > line
        under hits iff Y < line

    For whole-number lines, returns no-push conditional probabilities
    (P(over) and P(under) sum to 1.0 with push mass excluded). The
    caller's EV engine handles push semantics separately.
    """
    arr = np.asarray(pmf, dtype=float)
    arr = np.clip(arr, 0.0, None)
    s = arr.sum()
    if s <= 0:
        return 0.5, 0.5
    arr = arr / s
    values = np.arange(len(arr))
    p_over_raw = float(arr[values > line].sum())
    p_under_raw = float(arr[values < line].sum())
    denom = p_over_raw + p_under_raw
    if denom <= 0:
        return 0.5, 0.5
    return p_over_raw / denom, p_under_raw / denom


# ── Top-level per-day driver ─────────────────────────────────────────────────


def score_full_universe(
    universe_rows: list[dict],
    prop_pmfs_by_player: dict[int, dict[str, PropPMF]],
    thresholds: Optional[SelectionThresholds] = None,
) -> pd.DataFrame:
    """Score every offered prop against its PMF and run selection.

    `universe_rows` is a list of offered-prop dicts with keys:
        player_id, player_name, stat, side, offered_line,
        offered_american, paired_american, books_available
    (anything else is preserved on output).

    Returns a DataFrame mirroring `all_props_{date}.parquet`.
    """
    out_rows = []
    for row in universe_rows:
        pid = int(row["player_id"])
        stat = row["stat"]
        pmfs = prop_pmfs_by_player.get(pid, {})
        prop = pmfs.get(stat)
        if prop is None:
            out_rows.append({
                **row, "model_prob": None, "fair_american": None,
                "ev": None, "edge": None, "selected": False,
                "reject_reason": "no_pmf", "calibrated": False,
                "model_version": None,
            })
            continue

        p_over, p_under = score_prop_line(prop.pmf, float(row["offered_line"]))
        model_prob = p_over if row["side"] == "OVER" else p_under
        candidate = BetCandidate(
            player_name=row.get("player_name", ""),
            player_id=pid, stat=stat, side=row["side"],
            offered_line=float(row["offered_line"]),
            offered_american=int(row["offered_american"]),
            paired_american=int(row["paired_american"]) if row.get("paired_american") is not None else None,
            model_prob=float(model_prob),
            books_available=int(row.get("books_available", 1)),
            calibrator_version=prop.model_version,
        )
        decision = decide(candidate, thresholds)
        out_rows.append({
            **row,
            "model_prob": float(model_prob),
            "fair_american": decision.fair_american,
            "ev": decision.ev,
            "edge": decision.edge,
            "kelly_stake": decision.kelly_stake,
            "selected": decision.selected,
            "reject_reason": decision.reject_reason,
            "devigged_market_prob": decision.devigged_market_prob,
            "calibrated": prop.calibrated,
            "model_version": prop.model_version,
        })
    return pd.DataFrame(out_rows)
