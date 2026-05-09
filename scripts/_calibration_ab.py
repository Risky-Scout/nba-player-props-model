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
CALIBRATION_MODES = ("raw", "global_only", "role_aware")

AB_STARTER_REGRESSION_THRESHOLD  = 0.005   # NLL absolute
AB_LOW_VOLUME_BLEED_THRESHOLD    = 0.020   # NLL absolute
AB_OVERALL_IMPROVEMENT_THRESHOLD = 0.001
AB_MIN_N_FOR_CONCLUSION          = 500
AB_MIN_N_PER_BUCKET              = 50
AB_HIGH_VOLUME_STATS  = ("pts", "reb")
AB_LOW_VOLUME_BUCKETS = ("bench", "rotation", "core", "fringe")

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
def _apply_calibrator_mode(cal, pmf, role_bucket, mode):
    if mode == "raw":
        a = np.asarray(pmf, dtype=float)
        a = np.clip(a, 0.0, None)
        s = float(a.sum())
        return a / s if s > 0 else None
    if cal is None:
        return None
    try:
        if mode == "global_only":
            return cal.apply(np.asarray(pmf), role_bucket=None)
        if mode == "role_aware":
            return cal.apply(np.asarray(pmf), role_bucket=role_bucket)
    except TypeError:
        try:
            return cal.apply(np.asarray(pmf))
        except Exception:
            return None
    except Exception:
        return None
    return None

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
    for stat in sorted(oof["stat"].unique()):
        if stat not in SUPPORTED_STATS:
            continue
        cals[stat] = _vcvc._load_role_calibrator(model_dir, stat)
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

    return {
        "oof_path": str(oof_path),
        "model_dir": str(model_dir),
        "modes": list(CALIBRATION_MODES),
        "rows_loaded": len(oof),
        "rows_scored_per_mode": len(rows) // max(len(CALIBRATION_MODES), 1),
        "skipped_no_calibrator": n_no_cal,
        "skipped_no_pmf": n_no_pmf,
        "invalid_pmf_counts": dict(invalid),
        "breakouts": breakouts,
        "thresholds": {
            "starter_regression":  AB_STARTER_REGRESSION_THRESHOLD,
            "low_volume_bleed":    AB_LOW_VOLUME_BLEED_THRESHOLD,
            "overall_improvement": AB_OVERALL_IMPROVEMENT_THRESHOLD,
            "min_n_for_conclusion": AB_MIN_N_FOR_CONCLUSION,
        },
    }

# ── Promotion gate ─────────────────────────────────────────────────────────────
def evaluate_promotion_ab(report):
    overall = report["breakouts"]["overall"]
    by_role = report["breakouts"]["by_role_bucket"]
    by_stat = report["breakouts"]["by_stat"]

    legacy = overall.get("global_only")
    role_aware = overall.get("role_aware")
    raw = overall.get("raw")

    if not legacy or not role_aware:
        return {"recommendation": "NEEDS_MORE_DATA",
                "reason": "missing legacy or role_aware overall metrics",
                "evidence": {"overall": overall}}

    if (legacy["n"] < AB_MIN_N_FOR_CONCLUSION
            or role_aware["n"] < AB_MIN_N_FOR_CONCLUSION):
        return {"recommendation": "NEEDS_MORE_DATA",
                "reason": (f"insufficient sample legacy_n={legacy['n']}, "
                           f"role_aware_n={role_aware['n']}, "
                           f"threshold={AB_MIN_N_FOR_CONCLUSION}"),
                "evidence": {"overall": overall}}

    overall_delta = role_aware["nll"] - legacy["nll"]

    s_leg = by_role.get("global_only|starter")
    s_ra  = by_role.get("role_aware|starter")
    starter_delta = None
    if s_leg and s_ra and s_leg["n"] >= 200:
        starter_delta = s_ra["nll"] - s_leg["nll"]
        if starter_delta > AB_STARTER_REGRESSION_THRESHOLD:
            return {"recommendation": "BLOCKED_BY_STARTER_REGRESSION",
                    "reason": (f"starter NLL regresses {starter_delta:+.4f} "
                               f"(legacy {s_leg['nll']:.4f} -> role_aware "
                               f"{s_ra['nll']:.4f})"),
                    "evidence": {"starter_legacy": s_leg,
                                 "starter_role_aware": s_ra,
                                 "overall_delta": overall_delta}}

    high_vol_regs = []
    for stat in AB_HIGH_VOLUME_STATS:
        leg = by_stat.get(f"global_only|{stat}")
        ra  = by_stat.get(f"role_aware|{stat}")
        if not leg or not ra or leg["n"] < 200:
            continue
        d = ra["nll"] - leg["nll"]
        if d > AB_STARTER_REGRESSION_THRESHOLD:
            high_vol_regs.append({"stat": stat, "legacy_nll": leg["nll"],
                                  "role_aware_nll": ra["nll"], "delta": d})
    if high_vol_regs:
        return {"recommendation": "BLOCKED_BY_STARTER_REGRESSION",
                "reason": f"high-volume stats regress: {[r['stat'] for r in high_vol_regs]}",
                "evidence": {"high_volume_regressions": high_vol_regs,
                             "overall_delta": overall_delta}}

    bleeding = []
    for b in AB_LOW_VOLUME_BUCKETS:
        leg = by_role.get(f"global_only|{b}")
        ra  = by_role.get(f"role_aware|{b}")
        if not leg or not ra or leg["n"] < AB_MIN_N_PER_BUCKET:
            continue
        d = ra["nll"] - leg["nll"]
        if d > AB_LOW_VOLUME_BLEED_THRESHOLD:
            bleeding.append({"bucket": b, "legacy_nll": leg["nll"],
                             "role_aware_nll": ra["nll"], "delta": d})
    if bleeding:
        return {"recommendation": "BLOCKED_BY_LOW_VOLUME_BUCKET_BLEED",
                "reason": (f"buckets {[x['bucket'] for x in bleeding]} bleed "
                           f"by > {AB_LOW_VOLUME_BLEED_THRESHOLD} NLL"),
                "evidence": {"bleeding_buckets": bleeding,
                             "overall_delta": overall_delta}}

    if overall_delta < -AB_OVERALL_IMPROVEMENT_THRESHOLD:
        return {"recommendation": "PROMOTE_ROLE_AWARE",
                "reason": (f"role_aware NLL {role_aware['nll']:.4f} beats "
                           f"legacy {legacy['nll']:.4f} by {-overall_delta:+.4f}"),
                "evidence": {"overall_delta": overall_delta,
                             "starter_delta": starter_delta,
                             "n_total": role_aware["n"],
                             "vs_raw_delta": (role_aware["nll"] - raw["nll"]
                                              if raw else None)}}

    return {"recommendation": "KEEP_LEGACY",
            "reason": (f"role_aware NLL {role_aware['nll']:.4f} does not beat "
                       f"legacy {legacy['nll']:.4f} (delta {overall_delta:+.4f})"),
            "evidence": {"overall_delta": overall_delta,
                         "starter_delta": starter_delta,
                         "n_total": role_aware["n"],
                         "vs_raw_delta": (role_aware["nll"] - raw["nll"]
                                          if raw else None)}}

# ── Markdown report ────────────────────────────────────────────────────────────
def _emit_md_report(report, decision, out_path):
    bro = report["breakouts"]
    lines = [
        "# Calibration A/B Report (Phase 14 Step 1)",
        "",
        f"- Generated (UTC): {utcnow_iso()}",
        f"- OOF: `{report['oof_path']}`",
        f"- Model dir: `{report['model_dir']}`",
        f"- Rows scored per mode: {report['rows_scored_per_mode']:,}",
        "",
        f"## Recommendation: **{decision['recommendation']}**",
        "",
        f"**Reason:** {decision['reason']}",
        "",
        "## Overall metrics",
        "",
        "| mode | n | NLL | RPS | p0_err | mean_bias |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode in ("raw", "global_only", "role_aware"):
        v = bro["overall"].get(mode)
        if v:
            lines.append(
                f"| {mode} | {v['n']:,} | {v['nll']:.4f} | {v['rps']:.4f} | "
                f"{v['p0_err']:.4f} | {v['mean_bias']:+.4f} |"
            )

    def tbl(name, title):
        out = ["", f"## {title}", "",
               "| key | mode | n | NLL | NLL_delta_vs_legacy |",
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
            legacy = modes.get("global_only")
            for mode in ("raw", "global_only", "role_aware"):
                v = modes.get(mode)
                if not v:
                    continue
                d = (v["nll"] - legacy["nll"]) if (legacy and mode != "global_only") else None
                d_s = f"{d:+.4f}" if d is not None else "-"
                out.append(f"| {grp} | {mode} | {v['n']:,} | {v['nll']:.4f} | {d_s} |")
        return out

    lines += tbl("by_stat",            "By stat")
    lines += tbl("by_role_bucket",     "By role bucket")
    lines += tbl("by_line_bin",        "By line bin (predicted-median quartile proxy)")
    lines += tbl("by_role_x_line_bin", "By role x line bin")
    lines += tbl("by_stat_x_role",     "By stat x role")
    lines += [
        "", "## Thresholds applied",
        f"- starter regression: > {AB_STARTER_REGRESSION_THRESHOLD} NLL",
        f"- low-volume bucket bleed: > {AB_LOW_VOLUME_BLEED_THRESHOLD} NLL",
        f"- overall improvement: < -{AB_OVERALL_IMPROVEMENT_THRESHOLD} NLL",
        f"- min n for conclusion: {AB_MIN_N_FOR_CONCLUSION}",
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
