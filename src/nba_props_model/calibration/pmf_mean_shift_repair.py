"""OOF PMF location repair (actual outcomes only; no market in fit)."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from nba_props_model.calibration.event_neutral_probability_scale import (
    assert_no_forbidden_training_columns,
    binary_logloss,
    brier_score,
    chronological_date_folds,
)


def normalize_pmf(pmf: dict[int, float]) -> dict[int, float]:
    if not pmf:
        return {}
    clean = {int(k): max(0.0, float(p)) for k, p in pmf.items() if p is not None and float(p) == float(p)}
    s = sum(clean.values())
    if s <= 1e-15:
        return {}
    return {k: v / s for k, v in clean.items()}


def pmf_mean(pmf: dict[int, float]) -> float:
    if not pmf:
        return float("nan")
    return float(sum(k * p for k, p in pmf.items()))


def pmf_variance(pmf: dict[int, float]) -> float:
    mu = pmf_mean(pmf)
    if not math.isfinite(mu):
        return float("nan")
    return float(sum(((k - mu) ** 2) * p for k, p in pmf.items()))


def prob_over(pmf: dict[int, float], line: float | None) -> float | None:
    if not pmf or line is None or not math.isfinite(float(line)):
        return None
    lf = float(line)
    return float(sum(p for k, p in pmf.items() if k > lf))


def nll_at(pmf: dict[int, float], y: int | None) -> float | None:
    if not pmf or y is None or int(y) not in pmf:
        return None
    p = max(float(pmf[int(y)]), 1e-15)
    return float(-math.log(p))


def rps(pmf: dict[int, float], y: int | None) -> float | None:
    if not pmf or y is None:
        return None
    y = int(y)
    items = sorted(pmf.items())
    rpsv = 0.0
    cum_p = 0.0
    cum_y = 0.0
    for k, p in items:
        cum_p += p
        cum_y += 1.0 if k == y else 0.0
        rpsv += (cum_p - cum_y) ** 2
    return float(rpsv)


def shift_pmf_additive(pmf: dict[int, float], delta: float) -> dict[int, float]:
    """Shift location by delta on the integer lattice (linear interpolation)."""
    if not pmf:
        return {}
    out: dict[int, float] = {}
    for k, p in pmf.items():
        if p <= 0:
            continue
        kp = float(k) + float(delta)
        f0 = math.floor(kp)
        f1 = math.ceil(kp)
        if f0 == f1:
            kk = int(f0)
            out[kk] = out.get(kk, 0.0) + p
        else:
            w1 = kp - f0
            w0 = 1.0 - w1
            k0, k1 = int(f0), int(f1)
            out[k0] = out.get(k0, 0.0) + p * w0
            out[k1] = out.get(k1, 0.0) + p * w1
    return normalize_pmf(out)


def _tilted_mean(eta: float, ks: np.ndarray, ps: np.ndarray) -> float:
    w = ps * np.exp(eta * ks)
    s = float(w.sum())
    if s <= 1e-15:
        return float("nan")
    w = w / s
    return float(np.dot(w, ks))


def tilt_pmf_to_target_mean(pmf: dict[int, float], target_mean: float) -> dict[int, float] | None:
    """q(k) ∝ p(k)*exp(eta*k) with eta chosen so mean ≈ target_mean."""
    if not pmf or not math.isfinite(target_mean):
        return None
    items = sorted(pmf.items())
    ks = np.array([float(k) for k, _ in items], dtype=float)
    ps = np.array([float(p) for _, p in items], dtype=float)
    ps = ps / ps.sum()
    m0 = float(np.dot(ps, ks))
    if abs(target_mean - m0) < 1e-6:
        return normalize_pmf({int(k): float(p) for k, p in zip(ks, ps)})
    lo, hi = -4.0, 4.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        m = _tilted_mean(mid, ks, ps)
        if not math.isfinite(m):
            return None
        if m < target_mean:
            lo = mid
        else:
            hi = mid
    eta = 0.5 * (lo + hi)
    w = ps * np.exp(eta * ks)
    s = float(w.sum())
    if s <= 1e-15:
        return None
    w = w / s
    out: dict[int, float] = {}
    for i in range(len(ks)):
        kk = int(ks[i])
        out[kk] = out.get(kk, 0.0) + float(w[i])
    return normalize_pmf(out)


def scale_pmf_mean_multiplicative(pmf: dict[int, float], gamma: float) -> dict[int, float] | None:
    if not pmf or not math.isfinite(gamma) or gamma <= 0:
        return None
    m0 = pmf_mean(pmf)
    if not math.isfinite(m0):
        return None
    return tilt_pmf_to_target_mean(pmf, m0 * float(gamma))


def blend_additive_deltas(pmf: dict[int, float], d_sr: float, d_st: float, alpha: float) -> dict[int, float]:
    d = float(alpha) * float(d_sr) + (1.0 - float(alpha)) * float(d_st)
    return shift_pmf_additive(pmf, d)


def is_valid_pmf(pmf: dict[int, float]) -> bool:
    if not pmf:
        return False
    s = sum(pmf.values())
    if abs(s - 1.0) > 1e-3:
        return False
    if any(v < -1e-9 for v in pmf.values()):
        return False
    return True


def segment_key(stat: str, role: str) -> str:
    return f"{str(stat).lower()}|{str(role).lower()}"


def lookup_mean_shift_spec(
    manifest: dict[str, Any], stat: str, role_bucket: str
) -> tuple[str | None, dict[str, Any] | None]:
    segs = manifest.get("segments") or {}
    st = str(stat).lower()
    rb = str(role_bucket or "unknown").lower()
    for k in (f"{st}|{rb}", f"{st}|*", "global"):
        if k in segs and isinstance(segs[k], dict):
            return k, segs[k]
    return None, None


def apply_mean_shift_manifest_to_pmf(
    pmf: dict[int, float],
    *,
    stat: str,
    role_bucket: str,
    manifest: dict[str, Any] | None,
) -> tuple[dict[int, float] | None, str | None, str | None, bool, str | None]:
    """Return (pmf_out, scope_key, method, applied, rollback_reason).

    If not applied, returns (pmf unchanged copy, None, None, False, None).
    """
    if manifest is None or not pmf:
        return dict(pmf), None, None, False, None
    key, spec = lookup_mean_shift_spec(manifest, stat, role_bucket)
    if spec is None or not bool(spec.get("accepted", False)):
        return dict(pmf), None, None, False, None
    method = str(spec.get("selected_method") or "")
    raw = normalize_pmf(pmf)
    if not raw:
        return None, key, method, False, "empty_pmf"
    rep: dict[int, float] | None = None
    if method == "additive":
        d = float(spec.get("delta", 0.0))
        rep = shift_pmf_additive(raw, d)
    elif method == "multiplicative_gamma":
        g = float(spec.get("gamma", 1.0))
        rep = scale_pmf_mean_multiplicative(raw, g)
    elif method == "shrink_parent_additive":
        alpha = float(spec.get("alpha", 0.5))
        d_sr = float(spec.get("delta_stat_role", spec.get("delta", 0.0)))
        d_st = float(spec.get("delta_stat", 0.0))
        rep = blend_additive_deltas(raw, d_sr, d_st, alpha)
    else:
        return dict(raw), key, method, False, "unknown_method"
    if rep is None or not is_valid_pmf(rep):
        return dict(raw), key, method, False, "invalid_repaired_pmf"
    m_raw = pmf_mean(raw)
    m_rep = pmf_mean(rep)
    if not math.isfinite(m_raw) or not math.isfinite(m_rep):
        return dict(raw), key, method, False, "non_finite_mean"
    # Accept corrections in either direction, but require the mean actually moved.
    if abs(m_rep - m_raw) < 1e-9:
        return dict(raw), key, method, False, "mean_unchanged"
    return rep, key, method, True, None


def load_mean_shift_manifest(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def delta_grid_for_stat(stat: str) -> list[float]:
    st = str(stat).lower()
    if st in ("fg3m", "stl", "blk", "tov", "stocks"):
        return [-1.5, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5]
    if st in ("reb", "ast"):
        return [-1.5, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5]
    return [-3.0, -2.0, -1.5, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]


GAMMA_GRID = [0.80, 0.85, 0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.0, 1.02, 1.04, 1.06, 1.08, 1.10, 1.12, 1.15, 1.20]
ALPHA_GRID = [0.2, 0.35, 0.5, 0.65, 0.8]


def combo_stat_needs_coherence(stat: str) -> bool:
    return str(stat).lower() in ("pa", "pr", "pra", "ra")


def aggregate_row_metrics(
    pmfs: list[dict[int, float]],
    actuals: list[int],
    lines: list[float],
    overs: list[int],
) -> dict[str, float]:
    """Means of bias, mae, nll, rps, logloss, brier over rows (skip bad rows)."""
    biases = []
    maes = []
    nlls = []
    rpss = []
    lls = []
    brs = []
    for pmf, act, line, ov in zip(pmfs, actuals, lines, overs):
        if not pmf or act is None:
            continue
        mu = pmf_mean(pmf)
        if not math.isfinite(mu):
            continue
        biases.append(mu - float(act))
        maes.append(abs(mu - float(act)))
        nn = nll_at(pmf, int(act))
        rr = rps(pmf, int(act))
        if nn is not None:
            nlls.append(nn)
        if rr is not None:
            rpss.append(rr)
        po = prob_over(pmf, line)
        if po is not None and ov in (0, 1):
            lls.append(binary_logloss(np.array([po]), np.array([float(ov)])))
            brs.append(brier_score(np.array([po]), np.array([float(ov)])))
    def mean_or_nan(xs: list[float]) -> float:
        return float(np.mean(xs)) if xs else float("nan")

    return {
        "mean_bias": mean_or_nan(biases),
        "mean_abs_error": mean_or_nan(maes),
        "mean_nll": mean_or_nan(nlls),
        "mean_rps": mean_or_nan(rpss),
        "mean_event_ll": mean_or_nan(lls),
        "mean_event_brier": mean_or_nan(brs),
    }


def eval_candidate_on_rows(
    pmfs: list[dict[int, float]],
    actuals: list[int],
    lines: list[float],
    overs: list[int],
    *,
    method: str,
    delta: float | None,
    gamma: float | None,
    alpha: float | None,
    d_stat: float | None,
) -> dict[str, float] | None:
    reps: list[dict[int, float]] = []
    for pmf in pmfs:
        raw = normalize_pmf(pmf)
        if not raw:
            return None
        if method == "additive" and delta is not None:
            r = shift_pmf_additive(raw, float(delta))
        elif method == "multiplicative_gamma" and gamma is not None:
            r = scale_pmf_mean_multiplicative(raw, float(gamma))
        elif method == "shrink_parent_additive" and alpha is not None and d_stat is not None and delta is not None:
            r = blend_additive_deltas(raw, float(delta), float(d_stat), float(alpha))
        else:
            return None
        if not is_valid_pmf(r):
            return None
        reps.append(r)
    return aggregate_row_metrics(reps, actuals, lines, overs)


def passes_rollback(
    raw_m: dict[str, float],
    cal_m: dict[str, float],
    *,
    require_bias_improve: bool,
) -> tuple[bool, str]:
    if require_bias_improve and abs(cal_m.get("mean_bias", float("nan"))) >= abs(
        raw_m.get("mean_bias", float("nan"))
    ) - 1e-9:
        return False, "mean_bias_not_improved"
    if cal_m.get("mean_abs_error", float("nan")) > raw_m.get("mean_abs_error", float("nan")) + 0.02:
        return False, "mae_worsened"
    if cal_m.get("mean_nll", float("nan")) > raw_m.get("mean_nll", float("nan")) + 0.001:
        return False, "nll_worsened"
    if cal_m.get("mean_rps", float("nan")) > raw_m.get("mean_rps", float("nan")) + 0.001:
        return False, "rps_worsened"
    if cal_m.get("mean_event_ll", float("nan")) > raw_m.get("mean_event_ll", float("nan")) + 0.001:
        return False, "event_logloss_worsened"
    if cal_m.get("mean_event_brier", float("nan")) > raw_m.get("mean_event_brier", float("nan")) + 0.001:
        return False, "event_brier_worsened"
    return True, ""


def assert_fit_columns_allowed(columns: Iterable[str]) -> None:
    assert_no_forbidden_training_columns(columns)
