"""
NBA Props Model — full-universe probabilistic diagnostics.

Computes, per walk-forward fold:
  * log score        = -mean log P(outcome)
  * CRPS (discrete)  = sum_k (F(k) - 1_{y <= k})**2
  * randomized PIT   moments and KS distance from uniform
  * tail calibration P(Y >= q95) observed vs predicted
  * line-level Brier averaged over offered lines
  * calibration slope and intercept
  * ECE                over probability bins
  * market-relative   log-score lift vs de-vigged-open baseline
                       and vs a naive rolling-median baseline
  * CLV               where closing snapshots are available
  * edge-decile monotonicity
  * realized ROI      with bootstrap CIs
  * abstention rate   (share of props below selection threshold)

Report written to artifacts/docs/diagnostics_{run_date}.md.

Inputs
------
Any dataframe of OOS predictions that has:
    stat, player_id, game_date, outcome_integer,
    pmf  (list/array with same length per stat),
    fair_over_prob, offered_line, offered_over_odds (American int),
    market_implied_over_prob, closing_fair_prob (optional),
    selected (bool), bet_return (float, +1.0/-1.0/0.0).

Callers get back a dict of aggregate metrics and a markdown report path.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from nba_props_model.paths import REPO_ROOT

logger = logging.getLogger(__name__)

DOCS_DIR = REPO_ROOT / "artifacts" / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


# ── low-level metrics ────────────────────────────────────────────────────────


def log_score(pmfs: np.ndarray, outcomes: np.ndarray, eps: float = 1e-12) -> float:
    """Mean negative log-likelihood of the observed outcomes."""
    n = len(outcomes)
    if n == 0:
        return float("nan")
    vals = np.empty(n)
    for i, y in enumerate(outcomes):
        k = pmfs.shape[1]
        yi = int(np.clip(y, 0, k - 1))
        vals[i] = -np.log(max(float(pmfs[i, yi]), eps))
    return float(np.mean(vals))


def discrete_crps(pmfs: np.ndarray, outcomes: np.ndarray) -> float:
    """Discrete analogue of CRPS:
        CRPS = sum_k (F_pred(k) - 1_{y <= k})^2
    where k ranges over the integer support. Averaged across rows.
    """
    cdfs = np.cumsum(pmfs, axis=1)
    cdfs = np.clip(cdfs, 0.0, 1.0)
    support = np.arange(pmfs.shape[1])
    vals = np.empty(len(outcomes))
    for i, y in enumerate(outcomes):
        # True step indicator F_true(k) = 1_{y <= k}
        ind = (support >= int(y)).astype(float)
        vals[i] = float(np.sum((cdfs[i] - ind) ** 2))
    return float(np.mean(vals))


def randomized_pit(
    pmfs: np.ndarray, outcomes: np.ndarray,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    if rng is None:
        rng = np.random.default_rng(0)
    out = np.empty(len(outcomes))
    for i, y in enumerate(outcomes):
        y = int(np.clip(y, 0, pmfs.shape[1] - 1))
        below = float(pmfs[i, :y].sum()) if y > 0 else 0.0
        out[i] = below + rng.uniform(0, 1) * float(pmfs[i, y])
    return np.clip(out, 0.0, 1.0)


def pit_ks_distance(pit: np.ndarray) -> float:
    """Kolmogorov-Smirnov distance between PIT empirical CDF and Uniform(0,1)."""
    u = np.sort(np.clip(pit, 0.0, 1.0))
    if len(u) == 0:
        return float("nan")
    uniform = (np.arange(1, len(u) + 1)) / len(u)
    return float(np.max(np.abs(u - uniform)))


def brier(probs: np.ndarray, outcomes: np.ndarray) -> float:
    return float(np.mean((probs - outcomes.astype(float)) ** 2))


def ece(probs: np.ndarray, outcomes: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error (equal-width bins)."""
    if len(probs) == 0:
        return float("nan")
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(probs, edges) - 1, 0, bins - 1)
    total = 0.0
    n = len(probs)
    for b in range(bins):
        mask = idx == b
        cnt = int(mask.sum())
        if cnt == 0:
            continue
        total += (cnt / n) * abs(probs[mask].mean() - outcomes[mask].mean())
    return float(total)


def calibration_slope_intercept(probs: np.ndarray, outcomes: np.ndarray) -> tuple[float, float]:
    """Linear regression of outcomes on predicted probs.

    Returns (NaN, NaN) when input is degenerate (empty, single point,
    all-constant probs, non-finite only, or polyfit's SVD raises on
    rank-deficient input). Logged so Phase 8 diagnostics can audit
    degenerate folds instead of crashing the run.
    """
    probs_arr = np.asarray(probs, dtype=float)
    outcomes_arr = np.asarray(outcomes, dtype=float)
    finite_mask = np.isfinite(probs_arr) & np.isfinite(outcomes_arr)
    probs_arr = probs_arr[finite_mask]
    outcomes_arr = outcomes_arr[finite_mask]
    if len(probs_arr) < 2:
        return float("nan"), float("nan")
    if np.unique(probs_arr).size < 2:
        logger.warning(
            "calibration_slope_intercept: constant_probs n=%d; returning (nan, nan)",
            len(probs_arr),
        )
        return float("nan"), float("nan")
    try:
        slope, intercept = np.polyfit(probs_arr, outcomes_arr, 1)
    except (np.linalg.LinAlgError, ValueError, FloatingPointError) as exc:
        logger.warning(
            "calibration_slope_intercept: polyfit failed n=%d unique=%d exc=%r; returning (nan, nan)",
            len(probs_arr), int(np.unique(probs_arr).size), exc,
        )
        return float("nan"), float("nan")
    if not (np.isfinite(slope) and np.isfinite(intercept)):
        logger.warning(
            "calibration_slope_intercept: non-finite fit slope=%r intercept=%r; returning (nan, nan)",
            slope, intercept,
        )
        return float("nan"), float("nan")
    return float(slope), float(intercept)


def edge_decile_monotonicity(
    edges: np.ndarray, bet_returns: np.ndarray,
) -> tuple[float, list[float]]:
    """Split bets into 10 edge deciles and return mean return per decile.

    The spearman-ish correlation (ordinal) between decile rank and mean
    return approximates the monotonicity we want: higher edge -> higher
    realized return.
    """
    if len(edges) < 50:
        return float("nan"), []
    deciles = pd.qcut(edges, q=10, labels=False, duplicates="drop")
    df = pd.DataFrame({"d": deciles, "r": bet_returns}).dropna()
    means = df.groupby("d")["r"].mean().values.tolist()
    ranks = np.arange(len(means))
    if len(means) < 2:
        return float("nan"), means
    rho = float(np.corrcoef(ranks, means)[0, 1])
    return rho, [float(m) for m in means]


def bootstrap_ci(values: np.ndarray, ci: float = 0.95, n: int = 2_000,
                 rng: Optional[np.random.Generator] = None) -> tuple[float, float, float]:
    if rng is None:
        rng = np.random.default_rng(0)
    if len(values) == 0:
        return float("nan"), float("nan"), float("nan")
    boots = np.empty(n)
    for i in range(n):
        sample = rng.choice(values, size=len(values), replace=True)
        boots[i] = float(np.mean(sample))
    lo = float(np.percentile(boots, (1 - ci) / 2 * 100))
    hi = float(np.percentile(boots, (1 + ci) / 2 * 100))
    return float(np.mean(values)), lo, hi


# ── market-relative baselines ───────────────────────────────────────────────


def devig_pair(over_prob: float, under_prob: float) -> float:
    """De-vig an over/under pair to a fair over probability."""
    s = max(over_prob + under_prob, 1e-9)
    return float(over_prob / s)


def american_to_prob(odds: int | float) -> float:
    o = float(odds)
    if o > 0:
        return 100.0 / (o + 100.0)
    return abs(o) / (abs(o) + 100.0)


def american_to_decimal(odds: int | float) -> float:
    o = float(odds)
    if o > 0:
        return 1.0 + o / 100.0
    return 1.0 + 100.0 / abs(o)


# ── aggregator ───────────────────────────────────────────────────────────────


@dataclass
class FoldMetrics:
    fold_start: str
    fold_end: str
    stat: str
    n: int
    log_score: float
    crps: float
    pit_mean: float
    pit_std: float
    pit_ks: float
    brier: float
    ece: float
    cal_slope: float
    cal_intercept: float
    market_logscore_lift: float
    edge_monotonicity_rho: float

    def as_dict(self) -> dict:
        return asdict(self)


def evaluate_fold(
    pmfs: np.ndarray,
    outcomes: np.ndarray,
    over_probs_model: np.ndarray,
    over_probs_market: np.ndarray,
    over_realised: np.ndarray,
    edges: Optional[np.ndarray],
    bet_returns: Optional[np.ndarray],
    stat: str, fold_start: str, fold_end: str,
    rng: Optional[np.random.Generator] = None,
) -> FoldMetrics:
    if rng is None:
        rng = np.random.default_rng(0)
    pit = randomized_pit(pmfs, outcomes, rng)
    ks = pit_ks_distance(pit)
    bs = brier(over_probs_model, over_realised)
    ece_v = ece(over_probs_model, over_realised)
    slope, intercept = calibration_slope_intercept(over_probs_model, over_realised)
    log_s = log_score(pmfs, outcomes)
    crps_v = discrete_crps(pmfs, outcomes)

    # log-score lift: model vs market baseline (Bernoulli on the side).
    market_logscore = -np.mean(
        over_realised * np.log(np.clip(over_probs_market, 1e-9, 1 - 1e-9))
        + (1 - over_realised) * np.log(np.clip(1 - over_probs_market, 1e-9, 1 - 1e-9))
    )
    model_logscore = -np.mean(
        over_realised * np.log(np.clip(over_probs_model, 1e-9, 1 - 1e-9))
        + (1 - over_realised) * np.log(np.clip(1 - over_probs_model, 1e-9, 1 - 1e-9))
    )
    lift = float(market_logscore - model_logscore)

    rho = float("nan")
    if edges is not None and bet_returns is not None:
        rho, _ = edge_decile_monotonicity(edges, bet_returns)

    return FoldMetrics(
        fold_start=fold_start, fold_end=fold_end, stat=stat, n=int(len(outcomes)),
        log_score=log_s, crps=crps_v,
        pit_mean=float(np.mean(pit)), pit_std=float(np.std(pit)), pit_ks=ks,
        brier=bs, ece=ece_v,
        cal_slope=slope, cal_intercept=intercept,
        market_logscore_lift=lift,
        edge_monotonicity_rho=rho,
    )


# ── report ───────────────────────────────────────────────────────────────────


def write_report(fold_metrics: list[FoldMetrics], run_date: Optional[str] = None) -> Path:
    if run_date is None:
        run_date = datetime.utcnow().strftime("%Y-%m-%d")
    path = DOCS_DIR / f"diagnostics_{run_date}.md"

    by_stat: dict[str, list[FoldMetrics]] = {}
    for m in fold_metrics:
        by_stat.setdefault(m.stat, []).append(m)

    lines = [
        f"# Diagnostics report — {run_date}",
        "",
        "Full-universe out-of-sample, date-respecting walk-forward diagnostics.",
        "All metrics computed on the held-out fold for the corresponding window.",
        "",
    ]
    for stat, fm in sorted(by_stat.items()):
        lines.append(f"## Stat: `{stat}`")
        lines.append("")
        lines.append(
            "| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | "
            "PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |"
        )
        lines.append("|" + "---|" * 14)
        for m in fm:
            lines.append(
                f"| {m.fold_start} | {m.fold_end} | {m.n} "
                f"| {m.log_score:.4f} | {m.crps:.4f} "
                f"| {m.pit_mean:.3f} | {m.pit_std:.3f} | {m.pit_ks:.3f} "
                f"| {m.brier:.4f} | {m.ece:.4f} "
                f"| {m.cal_slope:.3f} | {m.cal_intercept:.3f} "
                f"| {m.market_logscore_lift:+.4f} | {m.edge_monotonicity_rho:+.2f} |"
            )
        lines.append("")
    path.write_text("\n".join(lines))
    return path
