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
  3. Sparse-stat PMFs from hurdle models (stl, blk marginals)
  4. FG3M PMF from the hurdle model's pmf() method
  5. Mission combo PMFs (stocks, pa, pr, pra) from joint samples
     via simulate_joint_stat_samples + build_combo_pmfs_for_group.
     - pa/pr/pra: production-grade. pts/reb/ast share the minutes
       draw in joint_simulation, preserving within-game correlation
       that convolution/independence destroyed.
     - stocks: routed through the same path for architectural
       consistency and so the role-aware stocks calibrator sees its
       training-time input distribution. BUT joint_simulation
       samples stl and blk INDEPENDENTLY from their hurdle PMFs
       (documented limitation in joint_simulation.py). M8.5 does
       NOT close stocks correlation quality; that remains an open
       M8.6/M9 item.
     ra/reb_ast are intentionally NOT emitted (non-mission).
  6. Apply per-stat pmf_calibration if trained
  7. Convert to fair over/under at each offered line
  8. Bet-selection filter against market prices

Outputs a DataFrame suitable for writing to
predictions/all_props_{date}.parquet and predictions/singles_{date}.json.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from nba_props_model.calibration.pmf_calibration import load_calibrator
from nba_props_model.calibration.role_buckets import role_bucket_from_minutes_dist
from nba_props_model.models import combos, simulation, sparse_hurdle
from nba_props_model.models.joint_simulation import (
    simulate_joint_stat_samples,
    JOINT_SAMPLER_VERSION,
)
from nba_props_model.models.joint_combo_pmfs import (
    build_combo_pmfs_for_group,
    JOINT_COMBO_PMF_VERSION,
)
from nba_props_model.models.minutes import MinutesDistribution, minutes_distribution
from nba_props_model.paths import MODEL_DIR
from nba_props_model.selection.bet_selection import (
    BetCandidate,
    SelectionThresholds,
    decide,
)

logger = logging.getLogger(__name__)

PMF_SIM_DRAWS = int(os.getenv("NBA_PMF_SIM_DRAWS", "50000"))


MAIN_STATS = ("pts", "reb", "ast", "tov")
SPARSE_STATS = ("stl", "blk")
COMBO_STATS = tuple(combos.COMBO_COMPONENTS.keys())

# M8.5: mission-required combos. The ONLY combos emitted to
# production. stocks, pa, pr, and pra each route through joint
# samples + role-aware calibrators, but the correctness story
# differs by combo:
#   - pa, pr, pra: production-grade. pts/reb/ast share the same
#     minutes draw in simulate_joint_stat_samples, so the resulting
#     PMFs preserve within-game correlation that convolution/
#     independence destroyed.
#   - stocks: routed through the same joint-sample path for
#     architectural consistency and so the role-aware M6.2 stocks
#     calibrator sees its training-time input distribution. BUT
#     joint_simulation samples stl/blk INDEPENDENTLY from their
#     hurdle PMFs (documented limitation). True stl/blk correlation
#     is NOT closed by M8.5; M8.6/M9 must track stocks/stl/blk
#     quality separately.
# ra/reb_ast are intentionally NOT in this set.
MISSION_COMBOS: tuple[str, ...] = ("stocks", "pa", "pr", "pra")

# Stats whose simulation embeds inactive/DNP zero-mass via
# `minutes_dist.sample()` and therefore must be active-conditioned
# before applying a calibrator that was fit on active-conditioned
# PMFs. FG3M / sparse / stocks / combos are NOT active-conditioned
# by this patch (their PMFs are already conditional on appearing or
# use different math entirely).
ACTIVE_CONDITION_STATS = {"pts", "reb", "ast", "tov"}


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
        n_draws=PMF_SIM_DRAWS, rng=rng,
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

    # FG3M via hurdle's pmf().
    if fg3m_hurdle_model is not None:
        try:
            fg3m_pmf = fg3m_hurdle_model.pmf(feature_row)
            out["fg3m"] = PropPMF(stat="fg3m", pmf=fg3m_pmf, calibrated=False,
                                  model_version="fg3m_hurdle_v1")
        except Exception as e:
            logger.debug(f"fg3m pmf failed: {e}")

    # M8.5: mission combo PMFs from joint samples (replaces legacy
    # convolution stocks + independence pa/pr/pra). The M6.2 role-aware
    # combo calibrators (pmf_cal_role_{stocks,pa,pr,pra}.pkl) were fit
    # on joint-sample combo OOF; this path routes each of stocks, pa,
    # pr, and pra through joint samples to match the calibrators'
    # training input distribution. No ra/reb_ast (non-mission).
    #
    # Correctness story differs by combo:
    #   - pa, pr, pra: production-grade. pts/reb/ast share the same
    #     minutes draw in simulate_joint_stat_samples, preserving
    #     within-game correlation.
    #   - stocks: simulate_joint_stat_samples samples stl/blk
    #     INDEPENDENTLY from their hurdle PMFs (documented limitation
    #     in joint_simulation.py). M8.5 closes the train/serve skew
    #     against the calibrator but does NOT capture true stl/blk
    #     correlation. Stocks correlation quality is an open M8.6/M9
    #     item.
    try:
        joint = simulate_joint_stat_samples(
            minutes_dist=minutes_dist,
            feature_row=feature_row,
            n_draws=PMF_SIM_DRAWS,
            rng=rng,
            fg3m_hurdle_model=fg3m_hurdle_model,
        )
    except Exception as e:
        raise RuntimeError(
            f"M8.5: simulate_joint_stat_samples failed: "
            f"{type(e).__name__}: {e}. Production combo emission "
            f"requires joint samples; cannot fall back to "
            f"convolution/independence (would re-introduce M6.2 "
            f"train/serve skew)."
        )
    if joint is None:
        raise RuntimeError(
            "M8.5: simulate_joint_stat_samples returned None. "
            "Production mission combo emission requires joint samples; "
            "cannot fall back to legacy stocks-convolution or combo-independence paths."
        )
    samples_df = pd.DataFrame({
        "pts":  joint["pts"],
        "reb":  joint["reb"],
        "ast":  joint["ast"],
        "tov":  joint["tov"],
        "fg3m": joint["fg3m"],
        "stl":  joint["stl"],
        "blk":  joint["blk"],
    })
    combo_pmfs = build_combo_pmfs_for_group(
        group=samples_df,
        combos=MISSION_COMBOS,
    )
    combo_model_version = f"{JOINT_SAMPLER_VERSION}+{JOINT_COMBO_PMF_VERSION}"
    for combo_key in MISSION_COMBOS:
        arr = combo_pmfs.get(combo_key)
        if arr is None:
            raise RuntimeError(
                f"M8.5: build_combo_pmfs_for_group returned None "
                f"for mission combo {combo_key!r}. Cannot silently "
                f"fall back."
            )
        out[combo_key] = PropPMF(
            stat=combo_key, pmf=arr, calibrated=False,
            model_version=combo_model_version,
        )

    # Ex-ante role bucket: depends only on the predicted minutes
    # distribution, never on realized minutes or outcomes. Used as the
    # calibrator key for role-aware bundles.
    role_bucket = role_bucket_from_minutes_dist(minutes_dist)
    # Ex-ante P(inactive) used only when the loaded calibrator's
    # training target is active-conditioned (per pmf_cal_meta.json).
    # In legacy mode, target_pmf falls through to the raw PMF and
    # downstream behavior is identical to pre-patch.
    calibration_target_active = _is_active_conditioned_calibration()
    try:
        p_inactive = float(np.clip(float(minutes_dist.state_probs[0]), 0.0, 0.99))
    except Exception:
        p_inactive = 0.0

    # Per-stat target PMF + calibrator application. The target PMF is
    # decided FIRST, independent of whether a calibrator is loaded —
    # so prop pricing always sees the market-aligned (active-
    # conditioned) distribution for RATE_STATS in active mode, even
    # when no calibrator artifact exists for that stat.
    for stat, prop in out.items():
        # Decide the calibration-target shape for this stat.
        if (
            calibration_target_active
            and stat in ACTIVE_CONDITION_STATS
            and p_inactive > 0.0
        ):
            target_pmf = active_condition_pmf(prop.pmf, p_inactive)
            active_tag = "+active_conditioned"
        else:
            target_pmf = prop.pmf
            active_tag = ""

        cal = load_calibrator(stat)
        if cal is None:
            # No calibrator artifact for this stat. In active mode we
            # still persist the active-conditioned PMF so downstream
            # pricing/export sees the market-aligned distribution; in
            # legacy mode we leave out[stat] alone (raw uncalibrated).
            if active_tag:
                out[stat] = PropPMF(
                    stat=stat, pmf=target_pmf, calibrated=False,
                    model_version=f"{prop.model_version}{active_tag}",
                )
            continue

        # Calibrator exists; apply it to target_pmf. Detect role-aware
        # bundles explicitly via the bundle's `version` attribute —
        # no broad TypeError fallback, so a real bug inside apply()
        # surfaces rather than silently routing to the legacy branch.
        if getattr(cal, "version", None) == "role_aware_pmf_cal_v1":
            cal_pmf = cal.apply(target_pmf, role_bucket=role_bucket)
            version_tag = f"role_aware_pmf_cal_v1:{role_bucket}"
        else:
            cal_pmf = cal.apply(target_pmf)
            version_tag = "pmf_cal_v1"
        out[stat] = PropPMF(
            stat=stat, pmf=cal_pmf, calibrated=True,
            model_version=f"{prop.model_version}+{version_tag}{active_tag}",
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


def active_condition_pmf(pmf: np.ndarray, p_inactive: float) -> np.ndarray:
    """Return P(stat | played) from a raw unconditional PMF + P(inactive).

    Decomposes the unconditional PMF as
        pmf[0] = p_inactive + (1 - p_inactive) * pmf_active[0]
        pmf[k] = (1 - p_inactive) * pmf_active[k]    for k > 0
    and solves for pmf_active.

    Edge cases (preserves PMF validity in all branches):
      - empty input: returns the singleton PMF [1.0].
      - p_inactive clipped to [0.0, 0.99].
      - p_inactive <= 0: returns a normalized copy of pmf.
      - pmf[0] < p_inactive: clipped to 0; renormalize.
      - degenerate / non-finite output: fall back to a normalized copy
        of the original pmf.

    Returns a finite, nonneg array summing to 1.0 with the same shape.
    """
    arr = np.asarray(pmf, dtype=float).copy()
    if arr.size == 0:
        return np.array([1.0], dtype=float)
    arr = np.clip(arr, 0.0, None)
    s = arr.sum()
    if not np.isfinite(s) or s <= 0:
        n = max(len(arr), 1)
        return np.full_like(arr, 1.0 / n)
    arr = arr / s
    p_inactive = float(np.clip(p_inactive, 0.0, 0.99))
    if p_inactive <= 0.0:
        return arr
    denom = 1.0 - p_inactive
    out = arr / denom
    out[0] = max(0.0, arr[0] - p_inactive) / denom
    out = np.clip(out, 0.0, None)
    s_out = out.sum()
    if not np.isfinite(s_out) or s_out <= 0:
        return arr
    return out / s_out


def _is_active_conditioned_calibration() -> bool:
    """Return True iff `artifacts/models/pmf_cal_meta.json` declares
    `calibration_target == "active_conditioned_prop_live"`.

    Returns False (legacy raw-PMF calibration target) when the
    metadata file is missing, malformed, or carries a different
    target. Without this gate, applying a legacy raw-target
    calibrator to an active-conditioned PMF would be a silent
    target mismatch.
    """
    try:
        meta_path = MODEL_DIR / "pmf_cal_meta.json"
        if not meta_path.exists():
            return False
        meta = json.loads(meta_path.read_text())
        return meta.get("calibration_target") == "active_conditioned_prop_live"
    except Exception:
        return False


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
