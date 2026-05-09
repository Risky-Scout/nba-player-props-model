"""Phase 14 Step 1 — same-row calibration A/B (extension to
scripts/validate_champion_vs_challenger.py per Joseph/LLM spec).

Score legacy (global-only) vs role_aware vs raw on identical OOF rows.
Break out by stat / role / line bin / role x line bin / date.
Apply 5-rule promotion gate. Emit recommendation enum.

Key trick: RoleAwarePMFCalibrator.apply(pmf, role_bucket=None) returns the
global-only output (legacy semantics). So 'legacy' is just role_aware with
role_bucket=None — no separate legacy pickle file is needed.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Reuse existing helpers (avoid double-loading when invoked from __main__)
_vcvc = sys.modules.get("__main__")
if not (_vcvc and hasattr(_vcvc, "_load_role_calibrator")):
    import validate_champion_vs_challenger as _vcvc  # type: ignore

from nba_props_model.training_automation import (  # noqa: E402
    SUPPORTED_STATS, write_json_atomic, utcnow_iso,
)

# ── Configuration ──────────────────────────────────────────────────────────────
# Phase 14 Step 2: shrinkage policy challengers. Each role_aware_* candidate
# is a pure apply-time blend override; no refit, no module-constant mutation.
# The pickle's fitted global_calibrator and bucket_calibrators are reused for
# every candidate; only the (shrink_k, cap) blend changes.
_CURRENT_K   = {"inactive_risk": 700.0, "fringe": 700.0, "bench": 900.0,
                "rotation": 1200.0, "core": 1500.0, "starter": 2000.0}
_CURRENT_CAP = {"inactive_risk": 0.85,  "fringe": 0.85,  "bench": 0.80,
                "rotation": 0.75,  "core": 0.60,  "starter": 0.45}

CALIBRATION_CANDIDATES = {
    "raw":         {"kind": "raw"},
    "global_only": {"kind": "global_only"},

    "role_aware_current": {
        "kind": "role_aware_override",
        "shrink_k":   dict(_CURRENT_K),
        "weight_cap": dict(_CURRENT_CAP),
        "global_only_buckets": frozenset(),
    },
    "role_aware_inactive_strong": {
        "kind": "role_aware_override",
        "shrink_k":   {**_CURRENT_K, "inactive_risk": 5000.0},
        "weight_cap": {**_CURRENT_CAP, "inactive_risk": 0.30},
        "global_only_buckets": frozenset(),
    },
    "role_aware_small_bucket_strong": {
        "kind": "role_aware_override",
        "shrink_k":   {**_CURRENT_K, "inactive_risk": 5000.0,
                       "fringe": 5000.0, "bench": 4500.0},
        "weight_cap": {**_CURRENT_CAP, "inactive_risk": 0.30,
                       "fringe": 0.30, "bench": 0.40},
        "global_only_buckets": frozenset(),
    },
    "role_aware_global_for_inactive": {
        "kind": "role_aware_override",
        "shrink_k":   dict(_CURRENT_K),
        "weight_cap": {**_CURRENT_CAP, "inactive_risk": 0.0},
        "global_only_buckets": frozenset({"inactive_risk"}),
    },
    "role_aware_inverted_curve": {
        "kind": "role_aware_override",
        "shrink_k":   {"inactive_risk": 5000.0, "fringe": 5000.0,
                       "bench": 3500.0, "rotation": 2000.0,
                       "core": 1500.0, "starter": 1200.0},
        "weight_cap": {"inactive_risk": 0.30, "fringe": 0.30,
                       "bench": 0.45, "rotation": 0.60,
                       "core": 0.70, "starter": 0.75},
        "global_only_buckets": frozenset(),
    },
    "role_aware_monotone_hierarchy": {
        "kind": "role_aware_override",
        "shrink_k":   {"inactive_risk": 8000.0, "fringe": 7000.0,
                       "bench": 5000.0, "rotation": 3000.0,
                       "core": 2000.0, "starter": 1500.0},
        "weight_cap": {"inactive_risk": 0.20, "fringe": 0.25,
                       "bench": 0.35, "rotation": 0.50,
                       "core": 0.65, "starter": 0.70},
        "global_only_buckets": frozenset(),
    },
    "role_aware_monotone_inactive_global": {
        "kind": "role_aware_override",
        "shrink_k":   {"inactive_risk": 8000.0, "fringe": 7000.0,
                       "bench": 5000.0, "rotation": 3000.0,
                       "core": 2000.0, "starter": 1500.0},
        "weight_cap": {"inactive_risk": 0.0, "fringe": 0.25,
                       "bench": 0.35, "rotation": 0.50,
                       "core": 0.65, "starter": 0.70},
        "global_only_buckets": frozenset({"inactive_risk"}),
    },
    "role_aware_monotone_inactive_ultra": {
        "kind": "role_aware_override",
        "shrink_k":   {"inactive_risk": 12000.0, "fringe": 7000.0,
                       "bench": 5000.0, "rotation": 3000.0,
                       "core": 2000.0, "starter": 1500.0},
        "weight_cap": {"inactive_risk": 0.10, "fringe": 0.25,
                       "bench": 0.35, "rotation": 0.50,
                       "core": 0.65, "starter": 0.70},
        "global_only_buckets": frozenset(),
    },
}
CALIBRATION_MODES = tuple(CALIBRATION_CANDIDATES.keys())

AB_OVERALL_TIE_TOLERANCE             = 0.001
AB_FG3M_INACTIVE_VS_GLOBAL_THRESHOLD = 0.003
AB_STARTER_VS_CURRENT_THRESHOLD      = 0.003
AB_CORE_VS_CURRENT_THRESHOLD         = 0.005
AB_HIGH_VOLUME_VS_CURRENT_THRESHOLD  = 0.005
AB_LOW_VOLUME_BLEED_THRESHOLD        = 0.025
AB_ROLE_VS_GLOBAL_THRESHOLD          = 0.020
AB_MIN_N_FOR_CONCLUSION              = 500
AB_MIN_N_PER_BUCKET                  = 50
AB_HIGH_VOLUME_STATS                 = ("pts", "reb")
AB_LOW_VOLUME_BUCKETS                = ("bench", "rotation", "core", "fringe", "inactive_risk")

_PROMOTE_ENUM = {
    "role_aware_inactive_strong":         "PROMOTE_INACTIVE_STRONG_SHRINKAGE",
    "role_aware_small_bucket_strong":     "PROMOTE_SMALL_BUCKET_STRONG_SHRINKAGE",
    "role_aware_global_for_inactive":     "PROMOTE_GLOBAL_FOR_INACTIVE_RISK",
    "role_aware_inverted_curve":          "PROMOTE_INVERTED_CURVE",
    "role_aware_monotone_hierarchy":      "PROMOTE_MONOTONE_HIERARCHY",
    "role_aware_monotone_inactive_global":"PROMOTE_MONOTONE_INACTIVE_GLOBAL",
    "role_aware_monotone_inactive_ultra": "PROMOTE_MONOTONE_INACTIVE_ULTRA",
}

# Per-stat predicted-median quartile cutoffs (proxy for market line bins,
# since OOF data has no market lines)
_LINE_BIN_CUTOFFS = {
    "pts":    (8, 16, 24),
    "reb":    (3, 6,  9),
    "ast":    (2, 4,  7),
    "tov":    (1, 2,  3),
    "fg3m":   (1, 2,  3),
    "blk":    (0, 1,  2),
    "stl":    (0, 1,  2),
    "stocks": (1, 2,  4),
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def _apply_role_aware_with_overrides(
    cal, pmf, role_bucket,
    shrink_k_overrides=None, weight_cap_overrides=None,
    global_only_buckets=None,
):
    """Pure blend override: reuse the fitted global+bucket isotonics from the
    pickle but blend with candidate-specific shrinkage params. No module
    constants mutated."""
    shrink_k_overrides = shrink_k_overrides or {}
    weight_cap_overrides = weight_cap_overrides or {}
    global_only_buckets = global_only_buckets or frozenset()
    if pmf is None or len(pmf) == 0:
        return None
    raw = np.asarray(pmf, dtype=float)
    raw = np.clip(raw, 0.0, None)
    s = float(raw.sum())
    if not np.isfinite(s) or s <= 0:
        return None
    raw = raw / s
    try:
        global_pmf = cal.global_calibrator.apply(raw)
    except Exception:
        return None
    bucket_key = role_bucket if isinstance(role_bucket, str) else None
    if not bucket_key or bucket_key == "unknown":
        return global_pmf
    if bucket_key in global_only_buckets:
        return global_pmf
    bucket_cal = getattr(cal, "bucket_calibrators", {}).get(bucket_key)
    if bucket_cal is None:
        return global_pmf
    try:
        bucket_pmf = bucket_cal.apply(raw)
    except Exception:
        return global_pmf
    n = int(getattr(cal, "bucket_counts", {}).get(bucket_key, 0))
    k = float(shrink_k_overrides.get(bucket_key, 1200.0))
    cap = float(weight_cap_overrides.get(bucket_key, 0.75))
    denom = n + k
    w = min(cap, n / denom) if denom > 0 else 0.0
    out = (1.0 - w) * np.asarray(global_pmf, dtype=float) + w * np.asarray(bucket_pmf, dtype=float)
    out = np.clip(out, 0.0, None)
    s_out = float(out.sum())
    if not np.isfinite(s_out) or s_out <= 0:
        return global_pmf
    return out / s_out


def _apply_calibrator_mode(cal, pmf, role_bucket, mode):
    """Dispatch a row through one of the named CALIBRATION_CANDIDATES."""
    spec = CALIBRATION_CANDIDATES.get(mode)
    if spec is None:
        return None
    kind = spec["kind"]
    if kind == "raw":
        a = np.asarray(pmf, dtype=float)
        a = np.clip(a, 0.0, None)
        s = float(a.sum())
        return a / s if s > 0 else None
    if cal is None:
        return None
    if kind == "global_only":
        try:
            return cal.apply(np.asarray(pmf), role_bucket=None)
        except TypeError:
            try:
                return cal.apply(np.asarray(pmf))
            except Exception:
                return None
        except Exception:
            return None
    if kind == "role_aware_override":
        return _apply_role_aware_with_overrides(
            cal, pmf, role_bucket,
            shrink_k_overrides=spec["shrink_k"],
            weight_cap_overrides=spec["weight_cap"],
            global_only_buckets=spec.get("global_only_buckets") or frozenset(),
        )
    return None


def _compute_effective_weights(bucket_counts_by_stat):
    """Build the mandatory hierarchy table per Step 3."""
    rows = []
    candidates = [(name, spec) for name, spec in CALIBRATION_CANDIDATES.items()
                  if spec["kind"] == "role_aware_override"]
    all_buckets = sorted(set().union(
        *(c["shrink_k"].keys() for _, c in candidates)
    ))
    repr_counts = {}
    if bucket_counts_by_stat:
        any_stat = next(iter(bucket_counts_by_stat))
        repr_counts = bucket_counts_by_stat[any_stat]
    for cand_name, spec in candidates:
        sk = spec["shrink_k"]; cap = spec["weight_cap"]
        gob = spec.get("global_only_buckets") or frozenset()
        for bucket in all_buckets:
            n = int(repr_counts.get(bucket, 0))
            k = float(sk.get(bucket, 1200.0))
            c = float(cap.get(bucket, 0.75))
            if bucket in gob:
                w = 0.0
            elif n + k > 0:
                w = min(c, n / (n + k))
            else:
                w = 0.0
            rows.append({"candidate": cand_name, "bucket": bucket,
                         "bucket_count": n, "K": k, "cap": c,
                         "global_only": bucket in gob,
                         "effective_w": round(w, 4)})
    return rows

def _predicted_median_index(pmf):
    a = np.asarray(pmf, dtype=float)
    a = np.clip(a, 0.0, None)
    s = a.sum()
    if s <= 0:
        return 0
    cdf = np.cumsum(a / s)
    return int(np.searchsorted(cdf, 0.5))

def _line_bin(median_idx, stat):
    cuts = _LINE_BIN_CUTOFFS.get(stat, (3, 6, 10))
    if median_idx <= cuts[0]: return "low"
    if median_idx <= cuts[1]: return "mid_low"
    if median_idx <= cuts[2]: return "mid_high"
    return "high"

def _agg(rows, group_keys):
    accum = defaultdict(lambda: {"n": 0, "nll_sum": 0.0, "rps_sum": 0.0,
                                  "p0_err_sum": 0.0, "mean_bias_sum": 0.0})
    for r in rows:
        key = tuple(str(r.get(k, "?")) for k in group_keys)
        a = accum[key]
        a["n"] += 1
        a["nll_sum"]      += r["nll"]
        a["rps_sum"]      += r["rps"]
        a["p0_err_sum"]   += r["p0_err"]
        a["mean_bias_sum"] += r["mean_bias"]
    out = {}
    for key, a in accum.items():
        n = max(a["n"], 1)
        out["|".join(key)] = {
            "n": a["n"],
            "nll": a["nll_sum"] / n,
            "rps": a["rps_sum"] / n,
            "p0_err": a["p0_err_sum"] / n,
            "mean_bias": a["mean_bias_sum"] / n,
        }
    return out

# ── Main scoring routine ───────────────────────────────────────────────────────
def score_oof_ab(oof_path, model_dir):
    oof = pd.read_parquet(oof_path)
    print(f"[ab] Loaded {len(oof):,} OOF rows from {oof_path}", flush=True)

    cals = {}
    bucket_counts_by_stat = {}
    for stat in sorted(oof["stat"].unique()):
        if stat not in SUPPORTED_STATS:
            continue
        cals[stat] = _vcvc._load_role_calibrator(model_dir, stat)
        if cals[stat] is not None:
            bucket_counts_by_stat[stat] = dict(
                getattr(cals[stat], "bucket_counts", {}) or {}
            )
    n_cals = sum(1 for c in cals.values() if c is not None)
    print(f"[ab] Loaded calibrators for {n_cals} stats", flush=True)

    rows = []
    invalid = defaultdict(int)
    n_no_cal = 0
    n_no_pmf = 0

    for r in oof.itertuples(index=False):
        stat = str(r.stat)
        cal = cals.get(stat)
        if cal is None:
            n_no_cal += 1
            continue
        pmf_raw = getattr(r, "pmf", None)
        if pmf_raw is None:
            n_no_pmf += 1
            continue
        outcome = int(r.outcome)
        role = str(getattr(r, "role_bucket", "unknown") or "unknown")
        date = str(getattr(r, "game_date", "?"))[:10]
        med = _predicted_median_index(pmf_raw)
        lbin = _line_bin(med, stat)

        for mode in CALIBRATION_MODES:
            pmf_cal = _apply_calibrator_mode(cal, pmf_raw, role, mode)
            if pmf_cal is None:
                invalid[f"{mode}:none"] += 1
                continue
            ok, reason = _vcvc._validate_pmf_array(pmf_cal)
            if not ok:
                invalid[f"{mode}:{reason}"] += 1
                continue
            sc = _vcvc._score_one_pmf(pmf_cal, outcome)
            rows.append({
                "stat": stat, "role_bucket": role, "line_bin": lbin,
                "date": date, "mode": mode,
                "nll": sc["nll"], "rps": sc["rps"],
                "p0_err": sc["p0_err"], "mean_bias": sc["mean_bias"],
            })

    print(
        f"[ab] Scored {len(rows):,} (row x mode) records. "
        f"skipped_no_cal={n_no_cal} skipped_no_pmf={n_no_pmf} "
        f"invalid={dict(invalid)}",
        flush=True,
    )

    breakouts = {
        "overall":            _agg(rows, ("mode",)),
        "by_stat":            _agg(rows, ("mode", "stat")),
        "by_role_bucket":     _agg(rows, ("mode", "role_bucket")),
        "by_line_bin":        _agg(rows, ("mode", "line_bin")),
        "by_role_x_line_bin": _agg(rows, ("mode", "role_bucket", "line_bin")),
        "by_date":            _agg(rows, ("mode", "date")),
        "by_stat_x_role":     _agg(rows, ("mode", "stat", "role_bucket")),
    }

    market_line_status = "MARKET_LINE_METRICS_UNAVAILABLE_IN_OOF_SCHEMA"

    return {
        "oof_path": str(oof_path),
        "model_dir": str(model_dir),
        "modes": list(CALIBRATION_MODES),
        "candidates": {name: {k: (sorted(list(v)) if isinstance(v, frozenset) else v)
                              for k, v in spec.items()}
                       for name, spec in CALIBRATION_CANDIDATES.items()},
        "rows_loaded": len(oof),
        "rows_scored_per_mode": len(rows) // max(len(CALIBRATION_MODES), 1),
        "skipped_no_calibrator": n_no_cal,
        "skipped_no_pmf": n_no_pmf,
        "invalid_pmf_counts": dict(invalid),
        "bucket_counts_by_stat": bucket_counts_by_stat,
        "effective_weights_table": _compute_effective_weights(bucket_counts_by_stat),
        "breakouts": breakouts,
        "market_line_metrics": market_line_status,
        "thresholds": {
            "overall_tie_tolerance":          AB_OVERALL_TIE_TOLERANCE,
            "fg3m_inactive_vs_global":        AB_FG3M_INACTIVE_VS_GLOBAL_THRESHOLD,
            "starter_vs_current":             AB_STARTER_VS_CURRENT_THRESHOLD,
            "core_vs_current":                AB_CORE_VS_CURRENT_THRESHOLD,
            "high_volume_vs_current":         AB_HIGH_VOLUME_VS_CURRENT_THRESHOLD,
            "low_volume_bleed":               AB_LOW_VOLUME_BLEED_THRESHOLD,
            "role_vs_global":                 AB_ROLE_VS_GLOBAL_THRESHOLD,
            "min_n_for_conclusion":           AB_MIN_N_FOR_CONCLUSION,
        },
    }

# ── Promotion gate ─────────────────────────────────────────────────────────────
def evaluate_promotion_ab(report):
    """Apply the 8 promotion gates from Phase 14 Step 2."""
    overall = report["breakouts"]["overall"]
    by_role = report["breakouts"]["by_role_bucket"]
    by_stat = report["breakouts"]["by_stat"]
    by_stat_role = report["breakouts"]["by_stat_x_role"]

    legacy = overall.get("global_only")
    current = overall.get("role_aware_current")
    if not legacy or not current:
        return {"recommendation": "NEEDS_MORE_DATA",
                "reason": "missing global_only or role_aware_current overall metrics",
                "evidence": {"overall": overall}}
    if (legacy["n"] < AB_MIN_N_FOR_CONCLUSION
            or current["n"] < AB_MIN_N_FOR_CONCLUSION):
        return {"recommendation": "NEEDS_MORE_DATA",
                "reason": (f"insufficient sample legacy_n={legacy['n']}, "
                           f"current_n={current['n']}, "
                           f"threshold={AB_MIN_N_FOR_CONCLUSION}"),
                "evidence": {"overall": overall}}

    candidate_names = [n for n in CALIBRATION_MODES
                       if CALIBRATION_CANDIDATES[n]["kind"] == "role_aware_override"
                       and n != "role_aware_current"]

    pair_violations = []
    for name in candidate_names:
        c = overall.get(name)
        if not c or c["n"] != current["n"]:
            pair_violations.append({"candidate": name,
                                    "n_candidate": c["n"] if c else 0,
                                    "n_current": current["n"]})
    if pair_violations:
        return {"recommendation": "BLOCKED_BY_UNPAIRED_COMPARISON",
                "reason": f"candidates dropped rows vs current: {pair_violations}",
                "evidence": {"pair_violations": pair_violations}}

    invalid = report.get("invalid_pmf_counts", {})

    gate_results = {}
    for name in candidate_names:
        c_overall = overall.get(name)
        gates = []
        cand_invalids = sum(v for k, v in invalid.items() if k.startswith(f"{name}:"))
        gates.append(("pmf_validity", cand_invalids == 0,
                      {"invalid_count": cand_invalids}))

        d_overall = c_overall["nll"] - current["nll"]
        gates.append(("overall_vs_current", d_overall <= AB_OVERALL_TIE_TOLERANCE,
                      {"delta": round(d_overall, 5),
                       "threshold": AB_OVERALL_TIE_TOLERANCE}))

        cand_cell = by_stat_role.get(f"{name}|fg3m|inactive_risk")
        glob_cell = by_stat_role.get("global_only|fg3m|inactive_risk")
        if cand_cell and glob_cell:
            d_fg3m_inact = cand_cell["nll"] - glob_cell["nll"]
            gates.append(("fg3m_inactive_vs_global",
                          d_fg3m_inact <= AB_FG3M_INACTIVE_VS_GLOBAL_THRESHOLD,
                          {"delta": round(d_fg3m_inact, 5),
                           "threshold": AB_FG3M_INACTIVE_VS_GLOBAL_THRESHOLD,
                           "n": cand_cell["n"]}))
        else:
            gates.append(("fg3m_inactive_vs_global", True, {"skipped": "missing cell"}))

        s_cand = by_role.get(f"{name}|starter")
        s_curr = by_role.get("role_aware_current|starter")
        if s_cand and s_curr:
            d_starter = s_cand["nll"] - s_curr["nll"]
            gates.append(("starter_vs_current",
                          d_starter <= AB_STARTER_VS_CURRENT_THRESHOLD,
                          {"delta": round(d_starter, 5),
                           "threshold": AB_STARTER_VS_CURRENT_THRESHOLD,
                           "n": s_cand["n"]}))
        else:
            gates.append(("starter_vs_current", True, {"skipped": "missing cell"}))

        co_cand = by_role.get(f"{name}|core")
        co_curr = by_role.get("role_aware_current|core")
        if co_cand and co_curr:
            d_core = co_cand["nll"] - co_curr["nll"]
            gates.append(("core_vs_current",
                          d_core <= AB_CORE_VS_CURRENT_THRESHOLD,
                          {"delta": round(d_core, 5),
                           "threshold": AB_CORE_VS_CURRENT_THRESHOLD,
                           "n": co_cand["n"]}))
        else:
            gates.append(("core_vs_current", True, {"skipped": "missing cell"}))

        hv_violations = []
        for stat in AB_HIGH_VOLUME_STATS:
            sc = by_stat.get(f"{name}|{stat}")
            sr = by_stat.get(f"role_aware_current|{stat}")
            if sc and sr:
                d = sc["nll"] - sr["nll"]
                if d > AB_HIGH_VOLUME_VS_CURRENT_THRESHOLD:
                    hv_violations.append({"stat": stat, "delta": round(d, 5)})
        gates.append(("high_volume_vs_current", len(hv_violations) == 0,
                      {"violations": hv_violations,
                       "threshold": AB_HIGH_VOLUME_VS_CURRENT_THRESHOLD}))

        bleed_violations = []
        for k, v in by_stat_role.items():
            if not k.startswith(f"{name}|"):
                continue
            if v["n"] < 200:
                continue
            parts = k.split("|")
            if len(parts) != 3:
                continue
            _, stat_k, bucket_k = parts
            glob_v = by_stat_role.get(f"global_only|{stat_k}|{bucket_k}")
            if not glob_v:
                continue
            d = v["nll"] - glob_v["nll"]
            if d > AB_LOW_VOLUME_BLEED_THRESHOLD:
                bleed_violations.append({"stat": stat_k, "bucket": bucket_k,
                                         "n": v["n"], "delta": round(d, 5)})
        gates.append(("low_volume_bleed", len(bleed_violations) == 0,
                      {"violations": bleed_violations,
                       "threshold": AB_LOW_VOLUME_BLEED_THRESHOLD}))

        cat_violations = []
        for bucket in AB_LOW_VOLUME_BUCKETS:
            bc = by_role.get(f"{name}|{bucket}")
            bg = by_role.get(f"global_only|{bucket}")
            if not bc or not bg:
                continue
            d = bc["nll"] - bg["nll"]
            if d > AB_ROLE_VS_GLOBAL_THRESHOLD:
                cat_violations.append({"bucket": bucket, "n": bc["n"],
                                       "delta": round(d, 5)})
        gates.append(("role_vs_global_catastrophe", len(cat_violations) == 0,
                      {"violations": cat_violations,
                       "threshold": AB_ROLE_VS_GLOBAL_THRESHOLD}))

        all_pass = all(g[1] for g in gates)
        gate_results[name] = {
            "gates": [{"name": g[0], "pass": g[1], "detail": g[2]} for g in gates],
            "all_pass": all_pass,
            "overall_nll": c_overall["nll"],
            "overall_delta_vs_current": round(d_overall, 5),
        }

    passing = {n: r for n, r in gate_results.items() if r["all_pass"]}
    if passing:
        winner_name, winner_data = min(
            passing.items(), key=lambda kv: kv[1]["overall_nll"]
        )
        if winner_data["overall_delta_vs_current"] < -AB_OVERALL_TIE_TOLERANCE:
            return {"recommendation": _PROMOTE_ENUM.get(winner_name,
                                                         "KEEP_CURRENT_ROLE_AWARE"),
                    "reason": (f"winner={winner_name} passes all 8 gates, "
                               f"overall_delta_vs_current="
                               f"{winner_data['overall_delta_vs_current']:+.5f}"),
                    "evidence": {"winner": winner_name,
                                 "winner_results": winner_data,
                                 "all_gate_results": gate_results}}
        # Hard gate 3 (fg3m|inactive_risk vs global_only <= +0.003) already
        # passed for the winner. The +0.001 tightness threshold is advisory:
        # attach FG3M_INACTIVE_RISK_RESIDUAL_GAP_WARN but still promote.
        glob_cell = by_stat_role.get("global_only|fg3m|inactive_risk")
        winner_cell = by_stat_role.get(f"{winner_name}|fg3m|inactive_risk")
        warnings = []
        if (glob_cell and winner_cell
                and winner_cell["nll"] - glob_cell["nll"] > 0.001):
            warnings.append({
                "name": "FG3M_INACTIVE_RISK_RESIDUAL_GAP_WARN",
                "detail": (f"winner={winner_name} fg3m|inactive_risk "
                           f"{winner_cell['nll'] - glob_cell['nll']:+.5f} vs global_only "
                           f"(passes +0.003 hard gate, exceeds +0.001 advisory)"),
                "delta_vs_global": round(winner_cell["nll"] - glob_cell["nll"], 5),
                "advisory_threshold": 0.001,
                "hard_gate_threshold": AB_FG3M_INACTIVE_VS_GLOBAL_THRESHOLD,
            })
        return {"recommendation": _PROMOTE_ENUM.get(winner_name,
                                                     "KEEP_CURRENT_ROLE_AWARE"),
                "reason": (f"winner={winner_name} passes all 8 hard gates; "
                           f"overall_delta_vs_current="
                           f"{winner_data['overall_delta_vs_current']:+.5f} "
                           f"(within tie tolerance {AB_OVERALL_TIE_TOLERANCE})"),
                "warnings": warnings,
                "evidence": {"winner": winner_name,
                             "winner_results": winner_data,
                             "all_gate_results": gate_results}}

    blocker_priority = [
        ("starter_vs_current",        "BLOCKED_BY_STARTER_REGRESSION"),
        ("high_volume_vs_current",    "BLOCKED_BY_HIGH_VOLUME_STAT_REGRESSION"),
        ("core_vs_current",           "BLOCKED_BY_CORE_REGRESSION"),
        ("low_volume_bleed",          "BLOCKED_BY_LOW_VOLUME_BUCKET_BLEED"),
        ("role_vs_global_catastrophe","BLOCKED_BY_LOW_VOLUME_BUCKET_BLEED"),
    ]
    for gate_name, enum_value in blocker_priority:
        for cand_name, r in gate_results.items():
            for g in r["gates"]:
                if g["name"] == gate_name and not g["pass"]:
                    return {"recommendation": enum_value,
                            "reason": f"candidate {cand_name} failed {gate_name}: {g['detail']}",
                            "evidence": {"all_gate_results": gate_results}}
    return {"recommendation": "KEEP_CURRENT_ROLE_AWARE",
            "reason": "no candidate passes all gates; no specific blocker pattern",
            "evidence": {"all_gate_results": gate_results}}


# ── Markdown report ────────────────────────────────────────────────────────────
def _emit_md_report(report, decision, out_path):
    bro = report["breakouts"]
    lines = [
        "# Calibration A/B Report (Phase 14 Step 2 — shrinkage challengers)",
        "",
        f"- Generated (UTC): {utcnow_iso()}",
        f"- OOF: `{report['oof_path']}`",
        f"- Model dir: `{report['model_dir']}`",
        f"- Rows scored per mode: {report['rows_scored_per_mode']:,}",
        f"- Market-line metrics: {report.get('market_line_metrics', 'unknown')}",
        "",
        f"## Recommendation: **{decision['recommendation']}**",
        "",
        f"**Reason:** {decision['reason']}",
        "",
        "## Effective bucket weights by candidate (mandatory hierarchy table)",
        "",
        "| candidate | bucket | bucket_count | K | cap | global_only | effective_w |",
        "|---|---|---:|---:|---:|:---:|---:|",
    ]
    for r in report.get("effective_weights_table", []):
        lines.append(
            f"| {r['candidate']} | {r['bucket']} | {r['bucket_count']:,} | "
            f"{r['K']:.0f} | {r['cap']:.2f} | "
            f"{'YES' if r['global_only'] else ''} | {r['effective_w']:.4f} |"
        )
    lines += ["", "## Overall metrics", "",
              "| candidate | n | NLL | RPS | p0_err | mean_bias |",
              "|---|---:|---:|---:|---:|---:|"]
    for mode in CALIBRATION_MODES:
        v = bro["overall"].get(mode)
        if v:
            lines.append(
                f"| {mode} | {v['n']:,} | {v['nll']:.4f} | {v['rps']:.4f} | "
                f"{v['p0_err']:.4f} | {v['mean_bias']:+.4f} |"
            )

    lines += ["", "## Focus cells (mandatory breakouts)", "",
              "| cell | candidate | n | NLL | delta_vs_current |",
              "|---|---|---:|---:|---:|"]
    focus_cells = [
        ("by_stat_x_role", "fg3m|inactive_risk"),
        ("by_role_bucket", "inactive_risk"),
        ("by_role_bucket", "fringe"),
        ("by_role_bucket", "bench"),
        ("by_role_bucket", "rotation"),
        ("by_role_bucket", "core"),
        ("by_role_bucket", "starter"),
        ("by_stat_x_role", "pts|starter"),
        ("by_stat_x_role", "reb|starter"),
        ("by_stat_x_role", "ast|starter"),
        ("by_stat_x_role", "fg3m|starter"),
        ("by_stat_x_role", "tov|starter"),
    ]
    for breakout_name, cell_key in focus_cells:
        breakout = bro.get(breakout_name, {})
        current_v = breakout.get(f"role_aware_current|{cell_key}")
        for mode in CALIBRATION_MODES:
            v = breakout.get(f"{mode}|{cell_key}")
            if not v:
                continue
            d = (v["nll"] - current_v["nll"]) if (current_v and mode != "role_aware_current") else None
            d_s = f"{d:+.4f}" if d is not None else "-"
            lines.append(f"| {cell_key} | {mode} | {v['n']:,} | {v['nll']:.4f} | {d_s} |")

    def tbl(name, title):
        out = ["", f"## {title}", "",
               "| key | candidate | n | NLL | delta_vs_current |",
               "|---|---|---:|---:|---:|"]
        if name not in bro:
            return out
        keyed = defaultdict(dict)
        for k, v in bro[name].items():
            parts = k.split("|")
            mode = parts[0]
            grp = "|".join(parts[1:])
            keyed[grp][mode] = v
        for grp in sorted(keyed.keys()):
            modes = keyed[grp]
            cur = modes.get("role_aware_current")
            for mode in CALIBRATION_MODES:
                v = modes.get(mode)
                if not v:
                    continue
                d = (v["nll"] - cur["nll"]) if (cur and mode != "role_aware_current") else None
                d_s = f"{d:+.4f}" if d is not None else "-"
                out.append(f"| {grp} | {mode} | {v['n']:,} | {v['nll']:.4f} | {d_s} |")
        return out

    lines += tbl("by_stat",            "By stat")
    lines += tbl("by_role_bucket",     "By role bucket")
    lines += tbl("by_line_bin",        "By line bin (predicted-median quartile proxy)")
    lines += tbl("by_role_x_line_bin", "By role x line bin")
    lines += tbl("by_stat_x_role",     "By stat x role")
    lines += tbl("by_date",            "By date")

    lines += [
        "", "## Pair-count audit", "",
        "| candidate | n | matches role_aware_current? |",
        "|---|---:|:---:|",
    ]
    cur_n = bro["overall"].get("role_aware_current", {}).get("n", 0)
    for mode in CALIBRATION_MODES:
        v = bro["overall"].get(mode)
        if v:
            ok = "yes" if v["n"] == cur_n else "NO"
            lines.append(f"| {mode} | {v['n']:,} | {ok} |")

    lines += [
        "", "## Promotion gate thresholds applied",
        f"- overall_tie_tolerance: {AB_OVERALL_TIE_TOLERANCE}",
        f"- fg3m_inactive_vs_global: {AB_FG3M_INACTIVE_VS_GLOBAL_THRESHOLD}",
        f"- starter_vs_current: {AB_STARTER_VS_CURRENT_THRESHOLD}",
        f"- core_vs_current: {AB_CORE_VS_CURRENT_THRESHOLD}",
        f"- high_volume_vs_current: {AB_HIGH_VOLUME_VS_CURRENT_THRESHOLD}",
        f"- low_volume_bleed: {AB_LOW_VOLUME_BLEED_THRESHOLD}",
        f"- role_vs_global: {AB_ROLE_VS_GLOBAL_THRESHOLD}",
        f"- min_n_for_conclusion: {AB_MIN_N_FOR_CONCLUSION}",
        "", "## Evidence",
        "```json",
        json.dumps(decision.get("evidence", {}), indent=2, default=str),
        "```", "",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Entrypoint ─────────────────────────────────────────────────────────────────
def ab_main(argv=None):
    parser = argparse.ArgumentParser(
        prog="validate_champion_vs_challenger.py --ab-mode",
        description="Same-row calibration A/B (Phase 14 Step 1).",
    )
    parser.add_argument("--ab-mode", action="store_true")
    parser.add_argument("--ab-oof", type=Path,
                        default=REPO_ROOT / "data" / "oof_pmfs.parquet")
    parser.add_argument("--ab-model-dir", type=Path,
                        default=REPO_ROOT / "artifacts" / "models")
    parser.add_argument("--ab-output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    out_dir = args.ab_output_dir
    if out_dir is None:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        out_dir = REPO_ROOT / "artifacts" / "calibration_ab" / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    report = score_oof_ab(args.ab_oof, args.ab_model_dir)
    decision = evaluate_promotion_ab(report)
    report["recommendation"] = decision

    write_json_atomic(out_dir / "ab_report.json", report)
    write_json_atomic(out_dir / "recommendation.json", decision)
    _emit_md_report(report, decision, out_dir / "ab_report.md")

    print(f"\n[ab] Recommendation: {decision['recommendation']}")
    print(f"[ab] Reason: {decision['reason']}")
    print(f"[ab] Output: {out_dir}/ab_report.md")
    return 0
