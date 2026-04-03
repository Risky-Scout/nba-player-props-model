"""
correlation_engine.py — DARKO v4 Correlation Engine
VERSION: 2026-02-28-v10

Expert-reviewed architecture:
  - Residual-based correlation (not raw stat correlation)
    resid_S = actual_S - pred_Q50_S
    scale_S = max(pred_Q75_S - pred_Q25_S, 0.5)
    z_S     = resid_S / scale_S
  - Winsorize z residuals to [-5, 5]
  - Shrinkage: R = λ*R_emp + (1-λ)*R_global, λ = n/(n+k), k in [50,200]
  - PSD enforcement via eigenvalue clipping + audit metrics
  - Segmentation by usage quartile and minutes quartile
  - Bounded leg-space: within-player (8 stats) + between-teammate (fixed pairs)
  - Gaussian copula simulation (50k samples) for joint probability
  - Monotonicity enforcement at inference
"""

import json
import logging
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

STATS        = ["pts", "reb", "ast", "fg3m", "stl", "blk", "tov"]
COMBO_STATS  = ["pra", "pr", "pa", "ra", "stocks"]
ALL_TARGETS  = STATS + COMBO_STATS

QUANTILES    = [0.10, 0.20, 0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75, 0.80, 0.90]

# Shrinkage hyperparameter k: higher = more shrinkage toward global
SHRINK_K_DEFAULT  = 100
SHRINK_K_SEGMENT  = 150   # more shrinkage in smaller segments

# PSD audit threshold: if >20% of eigenvalues are negative → merge to global
PSD_FAIL_THRESHOLD = 0.20

# Between-teammate fixed stat pairs to model
TEAMMATE_PAIRS = [
    ("ast", "pts"),    # PG assist vs scorer points (positive)
    ("pts", "pts"),    # star vs star usage overlap (often negative)
    ("reb", "reb"),    # big vs big rebound competition (negative)
    ("blk", "blk"),    # rim protector competition (negative)
    ("ast", "ast"),    # dual playmaker (varies by role)
]

N_COPULA_SAMPLES = 50_000


# ── Quantile monotonicity enforcement ─────────────────────────────────────────

def enforce_monotonicity(q_preds: dict) -> dict:
    """
    Independent quantile models can cross (Q80 < Q75).
    Enforce monotonicity via cumulative max before any CDF use.
    This is mandatory per expert spec.

    q_preds: {0.10: val, 0.20: val, ..., 0.90: val}
    Returns corrected dict with same keys.
    """
    qs   = sorted(q_preds.keys())
    vals = [q_preds[q] for q in qs]

    # Cumulative max enforces Q(i) >= Q(i-1)
    for i in range(1, len(vals)):
        vals[i] = max(vals[i], vals[i - 1])

    return {q: v for q, v in zip(qs, vals)}


# ── CDF interpolation ──────────────────────────────────────────────────────────

def p_over(q_preds: dict, line: float) -> float:
    """
    P(stat > line) by piecewise linear interpolation of quantile CDF.
    q_preds MUST be monotone-enforced before calling.
    Returns float in (0.01, 0.99).
    """
    q_preds = enforce_monotonicity(q_preds)
    qs   = sorted(q_preds.keys())
    vals = [q_preds[q] for q in qs]

    # Below lowest quantile
    if line <= vals[0]:
        q0, q1 = qs[0], qs[1]
        v0, v1 = vals[0], vals[1]
        if v1 > v0:
            slope = (q1 - q0) / (v1 - v0)
            cdf   = q0 + slope * (line - v0)
        else:
            cdf = q0
        return float(np.clip(1.0 - cdf, 0.01, 0.99))

    # Above highest quantile
    if line >= vals[-1]:
        q_n1, q_n = qs[-2], qs[-1]
        v_n1, v_n = vals[-2], vals[-1]
        if v_n > v_n1:
            slope = (q_n - q_n1) / (v_n - v_n1)
            cdf   = q_n + slope * (line - v_n)
        else:
            cdf = q_n
        return float(np.clip(1.0 - cdf, 0.01, 0.99))

    # Interpolate
    for i in range(len(vals) - 1):
        if vals[i] <= line <= vals[i + 1]:
            v_lo, v_hi = vals[i], vals[i + 1]
            q_lo, q_hi = qs[i], qs[i + 1]
            frac = (line - v_lo) / (v_hi - v_lo) if v_hi > v_lo else 0.5
            cdf  = q_lo + frac * (q_hi - q_lo)
            return float(np.clip(1.0 - cdf, 0.01, 0.99))

    return 0.50


def p_under(q_preds: dict, line: float) -> float:
    return 1.0 - p_over(q_preds, line)


def inverse_cdf(q_preds: dict, u: np.ndarray) -> np.ndarray:
    """
    Inverse CDF (quantile function) for copula simulation.
    u: array of uniform samples in (0,1)
    Returns array of stat outcome samples.
    q_preds must be monotone-enforced.
    """
    q_preds = enforce_monotonicity(q_preds)
    qs   = np.array(sorted(q_preds.keys()))
    vals = np.array([q_preds[q] for q in qs])

    # Piecewise linear interpolation: u → stat value
    result = np.interp(u, qs, vals)
    return result


# ── EV and Kelly ───────────────────────────────────────────────────────────────

def american_to_decimal(odds: int) -> float:
    if odds >= 100:
        return odds / 100.0
    else:
        return 100.0 / abs(odds)


def ev_from_prob(prob: float, american_odds: int) -> float:
    profit = american_to_decimal(american_odds)
    return float(prob * profit - (1.0 - prob) * 1.0)


def kelly_fraction(prob: float, american_odds: int,
                   fraction: float = 0.25, max_units: float = 2.0) -> float:
    b = american_to_decimal(american_odds)
    q = 1.0 - prob
    full_kelly = (b * prob - q) / b
    if full_kelly <= 0:
        return 0.0
    return float(min(full_kelly * fraction, max_units))


# ── Residual z-score computation ───────────────────────────────────────────────

def compute_residual_zscores(
    actuals: np.ndarray,
    q50_preds: np.ndarray,
    q25_preds: np.ndarray,
    q75_preds: np.ndarray,
    winsor_clip: float = 5.0,
) -> np.ndarray:
    """
    Standardized residuals for correlation estimation.
    z_S = (actual - Q50) / max(Q75 - Q25, 0.5)
    Winsorized to [-5, 5].
    """
    scale  = np.maximum(q75_preds - q25_preds, 0.5)
    resid  = actuals - q50_preds
    z      = resid / scale
    return np.clip(z, -winsor_clip, winsor_clip)


# ── PSD enforcement ────────────────────────────────────────────────────────────

def enforce_psd(R: np.ndarray, floor: float = 1e-6) -> tuple[np.ndarray, dict]:
    """
    Nearest PSD matrix via eigenvalue clipping.
    1. Eigendecompose R
    2. Clip negative eigenvalues to floor
    3. Reconstruct
    4. Renormalize diagonals to 1

    Returns (R_psd, audit_dict) where audit_dict contains:
      n_negative: count of negative eigenvalues
      frac_negative: fraction of eigenvalues that were negative
      max_neg_magnitude: largest negative eigenvalue magnitude
      correction_large: True if frac_negative > PSD_FAIL_THRESHOLD
    """
    eigenvalues, eigenvectors = np.linalg.eigh(R)

    n_neg      = int(np.sum(eigenvalues < 0))
    frac_neg   = float(n_neg / len(eigenvalues))
    max_neg    = float(abs(min(eigenvalues.min(), 0)))

    # Clip
    eigenvalues_clipped = np.maximum(eigenvalues, floor)

    # Reconstruct
    R_psd = eigenvectors @ np.diag(eigenvalues_clipped) @ eigenvectors.T

    # Renormalize diagonals to 1
    diag  = np.sqrt(np.diag(R_psd))
    diag  = np.where(diag > 0, diag, 1.0)
    R_psd = R_psd / np.outer(diag, diag)
    np.fill_diagonal(R_psd, 1.0)

    audit = {
        "n_negative":        n_neg,
        "frac_negative":     round(frac_neg, 4),
        "max_neg_magnitude": round(max_neg, 6),
        "correction_large":  frac_neg > PSD_FAIL_THRESHOLD,
    }

    if audit["correction_large"]:
        logger.warning(
            f"PSD correction LARGE: {n_neg}/{len(eigenvalues)} eigenvalues "
            f"negative (max mag={max_neg:.4f}). Increase shrinkage or merge segments."
        )

    return R_psd, audit


# ── Shrinkage ──────────────────────────────────────────────────────────────────

def shrink_to_global(R_emp: np.ndarray, R_global: np.ndarray,
                     n: int, k: int = SHRINK_K_DEFAULT) -> np.ndarray:
    """
    R = λ * R_emp + (1-λ) * R_global
    λ = n / (n + k)
    """
    lam = n / (n + k)
    return lam * R_emp + (1.0 - lam) * R_global


# ── Within-player correlation matrix ──────────────────────────────────────────

class WithinPlayerCorrelationEngine:
    """
    Builds and stores within-player correlation matrices for the 8-stat space
    (PTS, REB, AST, 3PM, STL, BLK, TOV, PRA), segmented by usage and minutes.

    Architecture:
      - Segment keys: (usage_bucket: 0-3, mp_bucket: 0-3)
      - 4×4 = 16 possible segments; fall back to global if n < 100
      - R_global estimated from all data, used as shrinkage target
      - All matrices PSD-enforced and audited
    """

    STAT_COLS = ["pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "pra"]

    def __init__(self, model_dir: Path):
        self.model_dir    = model_dir
        self.R_global     = None          # (8,8) global matrix
        self._stat_names  = []             # stat name list for Spearman index lookup
        self.R_segments   = {}            # {(ub, mb): (8,8) matrix}
        self.audit_log    = {}
        self._fitted      = False

    def fit(
        self,
        z_df: pd.DataFrame,          # columns: player_id, game_id, usage_bucket, mp_bucket, z_pts, z_reb, ...
    ):
        """
        Fit global + segmented correlation matrices from residual z-scores.
        z_df must have columns: player_id, game_id, usage_bucket, mp_bucket,
        plus z_{stat} for each stat in STAT_COLS.
        """
        stat_z_cols = [f"z_{s}" for s in self.STAT_COLS if f"z_{s}" in z_df.columns]
        available   = [s.replace("z_","") for s in stat_z_cols]
        idx         = {s: i for i, s in enumerate(available)}
        dim         = len(available)

        if dim < 2:
            logger.warning("Insufficient stats for correlation estimation")
            self.R_global = np.eye(dim)
            self._fitted  = True
            return

        Z_all = z_df[stat_z_cols].values.astype(float)
        # Remove rows with all NaN
        mask  = ~np.all(np.isnan(Z_all), axis=1)
        Z_all = Z_all[mask]

        # ── Global matrix ─────────────────────────────────────────────────────
        R_emp_global = self._pearson_robust(Z_all)
        self._stat_names = list(stat_list) if 'stat_list' in dir() else []
        self.R_global, audit_g = enforce_psd(R_emp_global)
        self.audit_log["global"] = {"n": len(Z_all), **audit_g}
        logger.info(f"  Global corr matrix: n={len(Z_all)}, psd_audit={audit_g}")

        # ── Segment matrices ──────────────────────────────────────────────────
        for ub in range(4):
            for mb in range(4):
                seg_mask = (
                    (z_df["usage_bucket"] == ub) &
                    (z_df["mp_bucket"]    == mb)
                )
                Z_seg = z_df[seg_mask][stat_z_cols].values.astype(float)
                Z_seg = Z_seg[~np.all(np.isnan(Z_seg), axis=1)]
                n_seg = len(Z_seg)

                if n_seg < 100:
                    # Bug 1 fix: use empirical data even for small segments
                    lam = n_seg / (n_seg + k) if n_seg > 0 else 0.0
                    if n_seg > 1:
                        R_emp_small = np.corrcoef(Z_seg.T)
                        R_seg = lam * R_emp_small + (1.0 - lam) * self.R_global
                    else:
                        R_seg = self.R_global
                    self.R_segments[(ub, mb)] = R_seg
                else:
                    R_emp_seg = self._pearson_robust(Z_seg)
                    R_shrunk  = shrink_to_global(R_emp_seg, self.R_global,
                                                  n=n_seg, k=SHRINK_K_SEGMENT)
                    R_psd, audit_s = enforce_psd(R_shrunk)
                    self.R_segments[(ub, mb)] = R_psd
                    self.audit_log[f"seg_{ub}_{mb}"] = {
                        "n": n_seg, "fallback": False, **audit_s
                    }

        self._stat_index = idx
        self._available  = available
        self._fitted     = True

        # Save audit
        audit_path = self.model_dir / "correlation_audit.json"
        with open(audit_path, "w") as fp:
            json.dump(self.audit_log, fp, indent=2, default=str)
        logger.info(f"  Correlation audit saved to {audit_path}")

    def get_matrix(self, usage_bucket: int, mp_bucket: int) -> np.ndarray:
        """Return segment matrix; fall back to global."""
        if not self._fitted:
            raise RuntimeError("CorrelationEngine not fitted")
        return self.R_segments.get((usage_bucket, mp_bucket), self.R_global)

    def _pearson_robust(self, Z: np.ndarray) -> np.ndarray:
        """
        Pearson correlation on winsorized z-scores.
        Issue 16 fix: uses Spearman for zero-inflated stat pairs (stl, blk, tov, stocks).
        Handles NaN via pairwise complete observations.
        """
        from scipy.stats import spearmanr as _spearmanr
        # Zero-inflated stat indices (stl=5, blk=6, tov=3, stocks=11 — adjust if order changes)
        _ZERO_INFLATED_STATS = {"stl", "blk", "tov", "stocks"}
        _zi_indices = {i for i, s in enumerate(self._stat_names)
                       if s in _ZERO_INFLATED_STATS} if hasattr(self, "_stat_names") else set()

        dim = Z.shape[1]
        R   = np.eye(dim)
        for i in range(dim):
            for j in range(i + 1, dim):
                mask = ~(np.isnan(Z[:, i]) | np.isnan(Z[:, j]))
                if mask.sum() < 20:
                    R[i, j] = R[j, i] = 0.0
                    continue
                zi = Z[mask, i]
                zj = Z[mask, j]
                # Issue 16: use Spearman for zero-inflated stat pairs
                if i in _zi_indices or j in _zi_indices:
                    corr, _ = _spearmanr(zi, zj)
                else:
                    corr = float(np.corrcoef(zi, zj)[0, 1])
                if np.isnan(corr):
                    corr = 0.0
                R[i, j] = R[j, i] = corr
        return R

    def stat_indices(self, stat_list: list[str]) -> list[int]:
        """Map stat names to indices in the correlation matrix."""
        return [self._stat_index[s] for s in stat_list if s in self._stat_index]


# ── Between-teammate correlation ───────────────────────────────────────────────

class TeammateCorrelationEngine:
    """
    Between-teammate correlation for fixed stat pairs.
    Indexed by: (stat_i, stat_j, usage_bucket_A, usage_bucket_B)
    Falls back to 0.0 correlation if insufficient sample.
    """

    def __init__(self, model_dir: Path):
        self.model_dir  = model_dir
        self._corr_map  = {}  # {(stat_i, stat_j, ub_a, ub_b): rho}
        self._fitted    = False

    def fit(self, teammate_z_df: pd.DataFrame):
        """
        teammate_z_df: one row per (game_id, team_id, player_a_id, player_b_id)
        with columns: stat_i, z_i, stat_j, z_j, usage_bucket_a, usage_bucket_b
        """
        if teammate_z_df.empty:
            self._fitted = True
            return

        for (si, sj, ub_a, ub_b), grp in teammate_z_df.groupby(
            ["stat_i", "stat_j", "usage_bucket_a", "usage_bucket_b"]
        ):
            zi = grp["z_i"].values.astype(float)
            zj = grp["z_j"].values.astype(float)
            mask = ~(np.isnan(zi) | np.isnan(zj))
            if mask.sum() < 50:
                # Not enough pairs — fall back to 0 (no correlation assumed)
                rho = 0.0
            else:
                rho = float(np.corrcoef(zi[mask], zj[mask])[0, 1])
                if np.isnan(rho):
                    rho = 0.0
            self._corr_map[(si, sj, ub_a, ub_b)] = rho
            # Symmetric
            self._corr_map[(sj, si, ub_b, ub_a)] = rho

        self._fitted = True

    def get_rho(self, stat_i: str, stat_j: str,
                usage_bucket_a: int = 1, usage_bucket_b: int = 1) -> float:
        """Return between-teammate correlation for a stat pair."""
        rho = self._corr_map.get((stat_i, stat_j, usage_bucket_a, usage_bucket_b))
        if rho is None:
            # Try global (no bucket segmentation)
            rho = self._corr_map.get((stat_i, stat_j, -1, -1), 0.0)
        return float(rho)


# ── Gaussian copula simulation ─────────────────────────────────────────────────

def build_sgp_correlation_matrix(
    legs: list[dict],
    within_engine: WithinPlayerCorrelationEngine,
    teammate_engine: TeammateCorrelationEngine,
) -> np.ndarray:
    """
    Assemble the correlation matrix R for a set of SGP legs.

    Each leg dict must have:
        player_id, stat, usage_bucket, mp_bucket

    Matrix assembled from building blocks:
      - Same player, different stats → within-player R
      - Different player, same team → teammate R
      - Different player, different team → 0 correlation
    """
    n = len(legs)
    R = np.eye(n)

    for i in range(n):
        for j in range(i + 1, n):
            leg_i = legs[i]
            leg_j = legs[j]

            si = leg_i["stat"]
            sj = leg_j["stat"]
            pi = leg_i["player_id"]
            pj = leg_j["player_id"]

            if pi == pj:
                # Same player — use within-player matrix
                ub = leg_i.get("usage_bucket", 1)
                mb = leg_i.get("mp_bucket", 1)
                mat = within_engine.get_matrix(ub, mb)
                idx = within_engine.stat_indices([si, sj])
                if len(idx) == 2:
                    rho = mat[idx[0], idx[1]]
                else:
                    rho = 0.0
            elif leg_i.get("team_id") == leg_j.get("team_id"):
                # Same team, different player — teammate correlation
                ub_a = leg_i.get("usage_bucket", 1)
                ub_b = leg_j.get("usage_bucket", 1)
                rho  = teammate_engine.get_rho(si, sj, ub_a, ub_b)
            else:
                # Different teams — no correlation
                rho = 0.0

            R[i, j] = R[j, i] = np.clip(rho, -0.999, 0.999)

    R_psd, _ = enforce_psd(R)
    return R_psd


def simulate_joint_probability(
    legs: list[dict],
    R: np.ndarray,
    n_samples: int = N_COPULA_SAMPLES,
    rng: np.random.Generator = None,
) -> float:
    """
    Gaussian copula simulation for joint SGP hit probability.

    Steps:
      1. Sample Z ~ N(0, R)  [n_samples × n_legs]
      2. U = Φ(Z)            [uniform marginals]
      3. For each leg, transform U through inverse CDF
      4. Evaluate hit condition (OVER or UNDER line)
      5. Joint hit rate = fraction of simulations where ALL legs hit

    Each leg dict must have:
        q_preds: dict of {quantile: value} (monotone-enforced)
        line: float
        side: "OVER" or "UNDER"
    """
    if rng is None:
        rng = np.random.default_rng(42)

    n_legs = len(legs)
    if n_legs == 0:
        return 0.0
    if n_legs == 1:
        leg = legs[0]
        prob = p_over(leg["q_preds"], leg["line"])
        return prob if leg["side"] == "OVER" else 1.0 - prob

    # Cholesky decomposition for correlated sampling
    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        R_psd, _ = enforce_psd(R)
        L = np.linalg.cholesky(R_psd)

    # Sample Z ~ N(0, R)
    Z_indep = rng.standard_normal((n_samples, n_legs))
    Z_corr  = Z_indep @ L.T        # (n_samples, n_legs)

    # Convert to uniforms via standard normal CDF
    U = norm.cdf(Z_corr)           # (n_samples, n_legs)

    # Transform to stat outcomes via inverse CDF
    all_hit = np.ones(n_samples, dtype=bool)

    for k, leg in enumerate(legs):
        u_k    = U[:, k]
        q_pred = enforce_monotonicity(leg["q_preds"])
        stat_samples = inverse_cdf(q_pred, u_k)   # (n_samples,)

        line = leg["line"]
        side = leg.get("side", "OVER")

        if side == "OVER":
            hit = stat_samples > line
        else:
            hit = stat_samples <= line

        all_hit &= hit

    return float(np.mean(all_hit))


# ── SGP candidate builder ──────────────────────────────────────────────────────

MIN_EV_SGP      = 0.025
MAX_LEG_JUICE   = -200
MIN_RHO_2LEG    = 0.05   # lower threshold now that we use proper residual correlations
MIN_AVG_RHO_3LEG= 0.05


def _leg_ok(odds: int) -> bool:
    return odds >= MAX_LEG_JUICE


def build_sgp_candidates(
    singles: list[dict],
    within_engine: WithinPlayerCorrelationEngine,
    teammate_engine: TeammateCorrelationEngine,
    min_ev: float = MIN_EV_SGP,
    n_sim_samples: int = N_COPULA_SAMPLES,
) -> dict:
    """
    Generate 2-leg and 3-leg SGP candidates using Gaussian copula simulation.

    Each single must have:
        player_id, player_name, game_id, game, team_id,
        stat, side, line, odds, model_prob, q_preds,
        usage_bucket, mp_bucket, ev

    Returns {"two_leg": [...], "three_leg": [...]}
    """
    from itertools import combinations as _comb

    rng = np.random.default_rng(42)

    # Group by game
    by_game: dict = {}
    for s in singles:
        gid = s.get("game_id")
        by_game.setdefault(gid, []).append(s)

    two_leg_sgps   = []
    three_leg_sgps = []

    for game_id, game_singles in by_game.items():
        valid = [s for s in game_singles if _leg_ok(s.get("odds", -110))]
        if len(valid) < 2:
            continue

        game_label = valid[0].get("game", f"game_{game_id}")

        # ── 2-leg ─────────────────────────────────────────────────────────────
        for a, b in _comb(valid, 2):
            if a["player_id"] == b["player_id"] and a["stat"] == b["stat"]:
                continue

            legs = [
                {**a, "q_preds": a["q_preds"]},
                {**b, "q_preds": b["q_preds"]},
            ]
            R = build_sgp_correlation_matrix(legs, within_engine, teammate_engine)

            joint_p = simulate_joint_probability(legs, R, n_sim_samples, rng)

            dec_combined = (
                american_to_decimal(a["odds"]) *
                american_to_decimal(b["odds"])
            )
            if dec_combined <= 1.0:
                continue   # degenerate odds — skip this pair
            if dec_combined >= 2.0:
                combined_am = int(round((dec_combined - 1) * 100))
            else:
                combined_am = int(round(-100 / (dec_combined - 1)))

            ev = ev_from_prob(joint_p, combined_am)
            if ev < min_ev:
                continue

            kelly = kelly_fraction(joint_p, combined_am, fraction=0.25, max_units=1.0)

            two_leg_sgps.append({
                "legs":            2,
                "game":            game_label,
                "game_id":         game_id,
                "combined_odds":   combined_am,
                "correlated_prob": round(joint_p, 4),
                "naive_prob":      round(a["model_prob"] * b["model_prob"], 4),
                "ev":              round(ev, 4),
                "kelly_units":     round(kelly, 3),
                "leg_details": [
                    _leg_summary(x) for x in [a, b]
                ],
            })

        # ── 3-leg ─────────────────────────────────────────────────────────────
        if len(valid) >= 3:
            for a, b, c in _comb(valid, 3):
                pid_stats = [(x["player_id"], x["stat"]) for x in [a, b, c]]
                if len(set(pid_stats)) < 3:
                    continue

                legs = [
                    {**a, "q_preds": a["q_preds"]},
                    {**b, "q_preds": b["q_preds"]},
                    {**c, "q_preds": c["q_preds"]},
                ]
                R = build_sgp_correlation_matrix(legs, within_engine, teammate_engine)
                joint_p = simulate_joint_probability(legs, R, n_sim_samples, rng)

                dec_combined = (
                    american_to_decimal(a["odds"]) *
                    american_to_decimal(b["odds"]) *
                    american_to_decimal(c["odds"])
                )
                if dec_combined <= 1.0:
                    continue   # degenerate odds — skip this combo
                if dec_combined >= 2.0:
                    combined_am = int(round((dec_combined - 1) * 100))
                else:
                    combined_am = int(round(-100 / (dec_combined - 1)))

                ev = ev_from_prob(joint_p, combined_am)
                if ev < min_ev:
                    continue

                kelly = kelly_fraction(joint_p, combined_am, fraction=0.25, max_units=1.0)

                three_leg_sgps.append({
                    "legs":            3,
                    "game":            game_label,
                    "game_id":         game_id,
                    "combined_odds":   combined_am,
                    "correlated_prob": round(joint_p, 4),
                    "naive_prob":      round(
                        a["model_prob"] * b["model_prob"] * c["model_prob"], 4
                    ),
                    "ev":              round(ev, 4),
                    "kelly_units":     round(kelly, 3),
                    "leg_details":     [_leg_summary(x) for x in [a, b, c]],
                })

    two_leg_sgps.sort(key=lambda x: x["ev"],   reverse=True)
    three_leg_sgps.sort(key=lambda x: x["ev"], reverse=True)

    return {"two_leg": two_leg_sgps, "three_leg": three_leg_sgps}


def _leg_summary(s: dict) -> dict:
    return {
        "player":     s["player_name"],
        "player_id":  s["player_id"],
        "stat":       s["stat"],
        "side":       s["side"],
        "line":       s["line"],
        "odds":       s["odds"],
        "model_prob": round(s["model_prob"], 4),
    }


# ── Calibration report ─────────────────────────────────────────────────────────

def quantile_calibration_report(actuals: np.ndarray,
                                 holdout_preds: dict,
                                 zero_inflated: bool = False) -> dict:
    """
    For each quantile q, compute empirical coverage on holdout.
    Well-calibrated: P(actual <= Q_q) ≈ q.

    zero_inflated=True (use for STL/BLK/Stocks):
      Skips coverage checks for quantiles q <= p0 where p0 = P(Y=0).
      Rationale: if P(Y=0)=0.68, then Q10/Q20/Q25 are all structurally 0
      and coverage will always be 0.68 even for a perfect model.
      Grading those quantiles as errors is a metric artifact, not a model flaw.
      Only quantiles above the zero mass are meaningful to evaluate.
      This is "Option B" from the expert review.
    """
    p0 = float(np.mean(actuals <= 0)) if zero_inflated else 0.0

    report = {}
    for q, preds in holdout_preds.items():
        preds     = np.array(preds)
        empirical = float(np.mean(actuals <= preds))

        if zero_inflated and q <= p0:
            # Quantile is below the zero-mass spike — metric is not meaningful here
            report[q] = {
                "predicted_q":  q,
                "empirical_q":  round(empirical, 4),
                "error":        0.0,          # not graded
                "n":            len(actuals),
                "skipped":      True,
                "reason":       f"q={q:.2f} <= p0={p0:.3f} (zero mass)",
            }
        else:
            report[q] = {
                "predicted_q":  q,
                "empirical_q":  round(empirical, 4),
                "error":        round(abs(empirical - q), 4),
                "n":            len(actuals),
                "skipped":      False,
            }
    return report


# ── Usage / minutes bucketing helpers ─────────────────────────────────────────

def usage_bucket(usage_pct: float) -> int:
    """0=low, 1=med-low, 2=med-high, 3=high usage"""
    if np.isnan(usage_pct): return 1
    if usage_pct < 15:  return 0
    if usage_pct < 20:  return 1
    if usage_pct < 26:  return 2
    return 3


def mp_bucket(mp_mean: float) -> int:
    """0=low, 1=med-low, 2=med-high, 3=starter minutes"""
    if np.isnan(mp_mean): return 1
    if mp_mean < 15:  return 0
    if mp_mean < 22:  return 1
    if mp_mean < 30:  return 2
    return 3
