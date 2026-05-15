"""Phase 13A — champion vs challenger validation.

Compares the current champion against the daily challenger on walk-forward /
rolling holdout data. Emits hard PMF validity checks and the promotion gate
decision.

Usage:
    python3 scripts/validate_champion_vs_challenger.py --as-of-date YYYY-MM-DD
    python3 scripts/validate_champion_vs_challenger.py --as-of-date YYYY-MM-DD \
        --challenger-dir artifacts/models/challengers/YYYY-MM-DD

Outputs (under <challenger-dir>):
    validation_report.json
    validation_summary.md
    promotion_decision.json

Hard rules:
- PMFs must sum to 1 within 1e-6, be non-negative, and finite.
- No future leakage (real training: train job status + OOF cutoff; dry-run: boxscore summary).
- TOV gates use only production phase8 PMF — never Phase 10D / 10D.2 overlays.
- Derek/WoO compatibility is a script-presence smoke recorded in the report.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_MODELS_DIR,
    SUPPORTED_STATS,
    challenger_dir,
    git_commit,
    load_champion_pointer,
    md_table,
    parse_date,
    read_json,
    scan_for_forbidden_overlay_tokens,
    scan_for_secrets,
    utcnow_iso,
    write_json_atomic,
)
from nba_props_model.targets import (  # noqa: E402
    MISSION_REQUIRED_TARGETS_CANONICAL,
)


# -- PMF validity ----------------------------------------------------------
ROLE_AWARE_BLEND_POLICY = "stat_role_guarded_expanded_v1"
M7_TARGET_STATS = tuple(MISSION_REQUIRED_TARGETS_CANONICAL)
M7_ROLE_BUCKETS = ("inactive_risk", "fringe", "bench", "rotation", "core", "starter")
M7_FORBIDDEN_STATS = {"ra", "reb_ast"}
M6_3_MATRIX_PATH = REPO_ROOT / "artifacts" / "docs" / "m6_3_stat_role_calibration_matrix_2026-05-11.csv"
M6_3_META_PATH = REPO_ROOT / "artifacts" / "docs" / "m6_3_stat_role_calibration_report_2026-05-11.meta.json"


def pmf_validity_checks(challenger_artifacts_dir: Path) -> dict:
    """Verify that any PMF parquets under the challenger dir are well-formed.

    In dry-run mode no PMF parquets are written under the challenger dir, so
    we exercise the same validation against the *most recent production PMF
    parquet* under predictions/. This proves the math is valid for the active
    champion. If no PMF parquet is found at all, we report no_data and treat
    PMF validity as advisory rather than a hard fail (so the framework can
    still bring up cleanly on a quiet day).
    """
    out = {
        "checked_files": 0,
        "issues": [],
        "rows_checked": 0,
        "stats_seen": [],
        "source": "none",
    }
    try:
        import numpy as np
        import pandas as pd
    except ImportError:
        out["issues"].append("pandas/numpy not installed; cannot validate PMFs")
        return out

    candidates: list[Path] = []
    if challenger_artifacts_dir.exists():
        candidates += sorted(challenger_artifacts_dir.glob("*.parquet"))
    if not candidates:
        # Fall back to the most recent production PMF parquet.
        pred_dir = REPO_ROOT / "predictions"
        if pred_dir.exists():
            candidates = sorted(pred_dir.glob("stat_grid_*.parquet"), reverse=True)[:1]
            if candidates:
                out["source"] = "predictions/stat_grid (champion)"
        if not candidates:
            out["issues"].append("no_pmf_parquet_found")
            return out
    else:
        out["source"] = str(challenger_artifacts_dir.relative_to(REPO_ROOT))

    stats_seen: set[str] = set()
    for path in candidates:
        try:
            df = pd.read_parquet(path)
        except Exception as exc:
            out["issues"].append(f"{path.name}: failed to read ({exc})")
            continue
        out["checked_files"] += 1
        out["rows_checked"] += int(len(df))
        # Find PMF columns: pattern stat_pmf_k or pmf_<stat>_k or pmf array col.
        pmf_cols_by_stat: dict[str, list[str]] = {}
        for col in df.columns:
            for s in SUPPORTED_STATS:
                if (
                    col.lower().startswith(f"pmf_{s}_")
                    or col.lower().startswith(f"{s}_pmf_")
                    or col.lower() == f"pmf_{s}"
                ):
                    pmf_cols_by_stat.setdefault(s, []).append(col)
        for s, cols in pmf_cols_by_stat.items():
            stats_seen.add(s)
            # Wide PMF: columns are scalar probability per support point.
            arr = df[cols].to_numpy(dtype=float, copy=False) if len(cols) > 1 else None
            if arr is not None:
                row_sums = np.nansum(arr, axis=1)
                if np.any((row_sums < 1.0 - 1e-6) | (row_sums > 1.0 + 1e-6)):
                    bad = int(((row_sums < 1.0 - 1e-6) | (row_sums > 1.0 + 1e-6)).sum())
                    out["issues"].append(
                        f"{path.name}/{s}: {bad} rows with PMF sum != 1 (tol 1e-6)"
                    )
                if np.any(arr < 0):
                    bad = int((arr < 0).sum())
                    out["issues"].append(f"{path.name}/{s}: {bad} negative probabilities")
                if not np.all(np.isfinite(arr[~np.isnan(arr)])):
                    out["issues"].append(f"{path.name}/{s}: non-finite probability values")
    out["stats_seen"] = sorted(stats_seen)
    return out


# -- Per-stat metrics ------------------------------------------------------

def metrics_placeholder() -> dict:
    """A neutral metric dict structure used when both sides reference identical
    artifacts (dry-run). Validation cannot improve and cannot regress.
    """
    return {
        "nll": None,
        "rps": None,
        "brier_logloss_at_market": None,
        "mean_error": None,
        "median_error": None,
        "p0_calibration": None,
        "ece": None,
        "by_stat": {s: {"nll": None, "rps": None, "ece": None} for s in SUPPORTED_STATS},
        "by_role_bucket": {},
        "by_line_bucket": {},
        "tov": {
            "p0_error": None,
            "mean_bias": None,
            "nll": None,
            "rps": None,
        },
        "market_comparison": None,
        "clv": None,
        "edge_buckets": None,
    }


# -- Real PMF scoring (Phase 13D) ------------------------------------------

# Holdout window (days). Validation rows are the last N days of the OOF
# universe at or before as_of_date — long enough to give meaningful sample
# size, short enough that both calibrators will have been fit on data
# strictly before this window when called via calibrate_pmf.py walk-forward.
HOLDOUT_DAYS = 28
EPS = 1e-12  # numerical floor for log/division


def _load_role_calibrator(model_dir: Path, stat: str):
    """Load the role-aware (or fallback global) PMF calibrator for ``stat``."""
    import joblib
    role_p = model_dir / f"pmf_cal_role_{stat}.pkl"
    if role_p.exists():
        try:
            return joblib.load(role_p)
        except Exception:
            return None
    legacy_p = model_dir / f"pmf_cal_{stat}.pkl"
    if legacy_p.exists():
        try:
            return joblib.load(legacy_p)
        except Exception:
            return None
    return None


def _apply_calibrator(cal, pmf, role_bucket: str):
    """Try the role-aware apply signature; fall back to global."""
    if cal is None:
        return None
    try:
        out = cal.apply(pmf, role_bucket=role_bucket)
    except TypeError:
        out = cal.apply(pmf)
    except Exception:
        return None
    return out


def _validate_pmf_array(arr) -> tuple[bool, str]:
    """Return (valid, reason). Enforces sum-to-1 ±1e-6, non-negative, finite."""
    import numpy as np
    a = np.asarray(arr, dtype=float)
    if not np.all(np.isfinite(a)):
        return False, "non_finite"
    if np.any(a < -1e-9):
        return False, "negative"
    s = a.sum()
    if not (1.0 - 1e-6 <= s <= 1.0 + 1e-6):
        return False, f"sum={s:.6f}"
    return True, "ok"


def _score_one_pmf(pmf, outcome: int) -> dict:
    """Compute NLL, RPS, p0_error, mean_bias for a single PMF + outcome."""
    import numpy as np
    a = np.asarray(pmf, dtype=float)
    a = np.clip(a, EPS, None)
    a = a / a.sum()
    K = len(a)
    o = int(outcome)
    if 0 <= o < K:
        nll = float(-np.log(a[o]))
    else:
        nll = float(-np.log(EPS))
    cdf = np.cumsum(a)
    indicator = (np.arange(K) >= o).astype(float)
    rps = float(np.sum((cdf - indicator) ** 2))
    p0 = float(a[0])
    p0_target = 1.0 if o == 0 else 0.0
    p0_err = abs(p0 - p0_target)
    mean_pred = float(np.dot(np.arange(K), a))
    mean_bias = mean_pred - float(o)
    return {"nll": nll, "rps": rps, "p0_err": p0_err, "mean_bias": mean_bias, "p0": p0}


def score_pmfs_from_oof(
    model_dir: Path,
    as_of_date: dt.date,
    holdout_days: int = HOLDOUT_DAYS,
    oof_path_override: Path | None = None,
) -> dict:
    """Score the PMF calibrators in ``model_dir`` on a leakage-safe holdout.

    Loads ``data/oof_pmfs.parquet`` (or override), filters to the last
    ``holdout_days`` strictly before ``as_of_date``, applies each side's
    role-aware calibrator, and returns NLL / RPS / p0_error / mean_bias
    aggregated overall, by stat, and by role bucket. Also runs the PMF
    validity gates on every produced calibrated PMF.
    """
    try:
        import numpy as np
        import pandas as pd
    except ImportError:
        return {"error": "pandas/numpy not installed", "by_stat": {}}

    oof_p = oof_path_override or (REPO_ROOT / "data" / "oof_pmfs.parquet")
    if not oof_p.exists():
        return {"error": f"oof parquet missing: {oof_p}", "by_stat": {}}

    df = pd.read_parquet(oof_p)
    df["game_date"] = pd.to_datetime(df["game_date"])
    cutoff = pd.Timestamp(as_of_date)
    # Phase 13H: when the OOF universe stops short of cutoff (typical when
    # cutoff is "yesterday" but OOF was last refreshed by phase8.yml days
    # earlier), clamp the upper bound to the OOF's own max date. This is
    # still leakage-safe by construction — every row in OOF is the
    # walk-forward fold's validation set, generated on data strictly before
    # the row's date — and the cutoff filter is preserved as min(cutoff,
    # oof_max).
    oof_max = df["game_date"].max()
    upper = min(cutoff, oof_max)
    holdout_start = upper - pd.Timedelta(days=holdout_days)
    holdout = df[
        (df["game_date"] >= holdout_start) & (df["game_date"] <= upper)
    ].copy()

    metrics = metrics_placeholder()
    metrics["holdout_window"] = {
        "start": str(holdout_start.date()),
        "end": str(cutoff.date()),
        "rows": int(len(holdout)),
    }
    metrics["model_dir"] = str(model_dir)

    if holdout.empty:
        metrics["error"] = "no_holdout_rows"
        return metrics

    by_stat: dict[str, dict] = {}
    by_role: dict[str, dict] = {}
    pmf_validity_issues: list[str] = []
    rows_scored_total = 0
    nll_sum = 0.0
    rps_sum = 0.0
    p0_err_sum = 0.0
    mean_bias_sum = 0.0
    rows_n = 0

    stats_in_oof = sorted(holdout["stat"].unique())
    for stat in stats_in_oof:
        if stat not in SUPPORTED_STATS:
            continue
        cal = _load_role_calibrator(model_dir, stat)
        if cal is None:
            by_stat[stat] = {
                "rows_scored": 0,
                "calibrator_present": False,
                "nll": None, "rps": None, "p0_err": None, "mean_bias": None,
            }
            continue
        sub = holdout[holdout["stat"] == stat]
        nll_s = 0.0; rps_s = 0.0; p0_s = 0.0; mb_s = 0.0; n_s = 0
        per_role_acc: dict[str, dict[str, float]] = {}
        for r in sub.itertuples(index=False):
            pmf_raw = getattr(r, "pmf", None)
            if pmf_raw is None:
                continue
            role = str(getattr(r, "role_bucket", "unknown"))
            cal_pmf = _apply_calibrator(cal, pmf_raw, role)
            if cal_pmf is None:
                continue
            ok, reason = _validate_pmf_array(cal_pmf)
            if not ok:
                if len(pmf_validity_issues) < 8:
                    pmf_validity_issues.append(f"{stat}/{role}: {reason}")
                continue
            outcome = int(r.outcome)
            sc = _score_one_pmf(cal_pmf, outcome)
            nll_s += sc["nll"]; rps_s += sc["rps"]
            p0_s += sc["p0_err"]; mb_s += sc["mean_bias"]
            n_s += 1
            acc = per_role_acc.setdefault(role, {"n": 0, "nll": 0.0, "p0": 0.0})
            acc["n"] += 1; acc["nll"] += sc["nll"]; acc["p0"] += sc["p0_err"]
        if n_s == 0:
            by_stat[stat] = {
                "rows_scored": 0,
                "calibrator_present": True,
                "nll": None, "rps": None, "p0_err": None, "mean_bias": None,
            }
            continue
        by_stat[stat] = {
            "rows_scored": n_s,
            "calibrator_present": True,
            "nll": nll_s / n_s,
            "rps": rps_s / n_s,
            "p0_err": p0_s / n_s,
            "mean_bias": mb_s / n_s,
        }
        for role, acc in per_role_acc.items():
            agg = by_role.setdefault(role, {"n": 0, "nll_sum": 0.0, "p0_sum": 0.0})
            agg["n"] += acc["n"]
            agg["nll_sum"] += acc["nll"]
            agg["p0_sum"] += acc["p0"]
        nll_sum += nll_s; rps_sum += rps_s
        p0_err_sum += p0_s; mean_bias_sum += mb_s
        rows_n += n_s
        rows_scored_total += n_s

    metrics["by_stat"] = by_stat
    metrics["by_role_bucket"] = {
        role: {
            "n": acc["n"],
            "nll": acc["nll_sum"] / acc["n"] if acc["n"] else None,
            "p0_err": acc["p0_sum"] / acc["n"] if acc["n"] else None,
        }
        for role, acc in by_role.items()
    }
    if rows_n > 0:
        metrics["nll"] = nll_sum / rows_n
        metrics["rps"] = rps_sum / rows_n
        metrics["p0_calibration"] = p0_err_sum / rows_n
        metrics["mean_error"] = mean_bias_sum / rows_n
    metrics["rows_scored_total"] = rows_scored_total
    metrics["pmf_validity_issues"] = pmf_validity_issues
    # TOV-specific extract for the gate.
    tov_block = by_stat.get("tov")
    if tov_block and tov_block.get("rows_scored", 0) > 0:
        metrics["tov"] = {
            "p0_error": tov_block["p0_err"],
            "mean_bias": tov_block["mean_bias"],
            "nll": tov_block["nll"],
            "rps": tov_block["rps"],
        }
    return metrics


# -- Compatibility smokes --------------------------------------------------

def derek_compat_check() -> dict:
    """Confirm the Derek delivery script + canonical PMF parquet shape are intact."""
    derek_script = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"
    canonical_parquet = REPO_ROOT / "scripts" / "build_daily_pmf_delivery.py"
    return {
        "passed": derek_script.exists() and canonical_parquet.exists(),
        "derek_script_present": derek_script.exists(),
        "canonical_builder_present": canonical_parquet.exists(),
        "notes": "Smoke check of script presence; full I/O smoke runs in orchestrator.",
    }


def woo_compat_check() -> dict:
    woo_script = REPO_ROOT / "scripts" / "build_wizard_of_odds_public_export.py"
    return {
        "passed": woo_script.exists(),
        "woo_script_present": woo_script.exists(),
        "notes": "Smoke check of script presence; full export smoke runs in orchestrator.",
    }


# -- Gate evaluation -------------------------------------------------------

def _delta(challenger: float | None, champion: float | None) -> float | None:
    """Challenger minus champion; None if either side is missing."""
    if challenger is None or champion is None:
        return None
    return float(challenger) - float(champion)


def _compare_gate(
    name: str,
    challenger: float | None,
    champion: float | None,
    *,
    lower_is_better: bool = True,
    tolerance: float = 0.0,
) -> tuple[str, bool, str]:
    """Generic comparator. Returns (gate_name, passed, detail).

    For lower-is-better metrics (NLL, RPS, ECE, p0_err, |mean_bias|),
    challenger is "non-worse" when (challenger - champion) <= tolerance.
    """
    if challenger is None or champion is None:
        return (name, False, f"missing metric (challenger={challenger}, champion={champion})")
    delta = challenger - champion
    if lower_is_better:
        passed = delta <= tolerance
    else:
        passed = delta >= -tolerance
    detail = (
        f"challenger={challenger:.6g} champion={champion:.6g} "
        f"delta={delta:+.6g} (tol={tolerance})"
    )
    return (name, passed, detail)



def _load_m6_3_stat_role_policy() -> dict:
    """Load M6.3's 66-cell report and build the M7 guarded fallback policy."""
    expected_stats = set(M7_TARGET_STATS)
    expected_roles = set(M7_ROLE_BUCKETS)

    summary = {
        "schema_version": "m7_m6_3_matrix_summary_v1",
        "matrix_path": str(M6_3_MATRIX_PATH.relative_to(REPO_ROOT)),
        "meta_path": str(M6_3_META_PATH.relative_to(REPO_ROOT)),
        "expected_rows": len(expected_stats) * len(expected_roles),
        "expected_stats": list(M7_TARGET_STATS),
        "expected_role_buckets": list(M7_ROLE_BUCKETS),
        "valid": False,
        "issues": [],
    }

    rows: list[dict] = []
    meta: dict = {}

    if not M6_3_MATRIX_PATH.exists():
        summary["issues"].append(f"missing matrix: {summary['matrix_path']}")
    else:
        with M6_3_MATRIX_PATH.open("r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    if not M6_3_META_PATH.exists():
        summary["issues"].append(f"missing meta: {summary['meta_path']}")
    else:
        meta = read_json(M6_3_META_PATH)

    observed_stats = {str(r.get("stat", "")) for r in rows}
    observed_roles = {str(r.get("role_bucket", "")) for r in rows}
    observed_cells = {(str(r.get("stat", "")), str(r.get("role_bucket", ""))) for r in rows}
    expected_cells = {(s, rb) for s in expected_stats for rb in expected_roles}
    forbidden_present = sorted((observed_stats | set(meta.get("observed_stats", []) or [])) & M7_FORBIDDEN_STATS)

    status_counts: dict[str, int] = {}
    for r in rows:
        status = str(r.get("status", "UNKNOWN"))
        status_counts[status] = status_counts.get(status, 0) + 1

    missing_cells = sorted(f"{s}|{rb}" for s, rb in (expected_cells - observed_cells))
    extra_cells = sorted(f"{s}|{rb}" for s, rb in (observed_cells - expected_cells))

    if len(rows) != summary["expected_rows"]:
        summary["issues"].append(f"expected 66 rows, found {len(rows)}")
    if observed_stats != expected_stats:
        summary["issues"].append(
            f"stat mismatch missing={sorted(expected_stats - observed_stats)} extra={sorted(observed_stats - expected_stats)}"
        )
    if observed_roles != expected_roles:
        summary["issues"].append(
            f"role mismatch missing={sorted(expected_roles - observed_roles)} extra={sorted(observed_roles - expected_roles)}"
        )
    if missing_cells:
        summary["issues"].append(f"missing_cells={missing_cells[:10]}")
    if extra_cells:
        summary["issues"].append(f"extra_cells={extra_cells[:10]}")
    if forbidden_present:
        summary["issues"].append(f"forbidden_stats_present={forbidden_present}")
    if meta.get("m6_3_report_pass") is not True:
        summary["issues"].append(f"m6_3_report_pass is not true: {meta.get('m6_3_report_pass')!r}")
    if meta.get("market_eval_available") is not False:
        summary["issues"].append(
            f"market_eval_available must remain false for M7: {meta.get('market_eval_available')!r}"
        )

    def _cell_payload(r: dict) -> dict:
        payload = {
            "stat": str(r.get("stat", "")),
            "role_bucket": str(r.get("role_bucket", "")),
            "status": str(r.get("status", "")),
        }
        for k in ("n", "delta_nll_cal_minus_raw", "nll_threshold", "caveats"):
            if k in r and r.get(k) not in (None, ""):
                payload[k] = r.get(k)
        return payload

    pass_cells = [_cell_payload(r) for r in rows if str(r.get("status")) == "PASS"]
    review_cells = [_cell_payload(r) for r in rows if str(r.get("status")) == "REVIEW"]
    needs_more_data_cells = [_cell_payload(r) for r in rows if str(r.get("status")) == "NEEDS_MORE_DATA"]
    guarded_fallback_cells = review_cells + needs_more_data_cells

    policy = {
        "policy_name": ROLE_AWARE_BLEND_POLICY,
        "target_stats_canonical": list(M7_TARGET_STATS),
        "role_buckets": list(M7_ROLE_BUCKETS),
        "role_aware_allowed_cells": pass_cells,
        "guarded_fallback_required_cells": guarded_fallback_cells,
        "needs_more_data_fallback_required_cells": needs_more_data_cells,
        "review_status_handling": "REVIEW cells are not promotion blockers if explicitly listed for guarded fallback.",
        "market_eval_available": False,
    }

    summary.update({
        "rows": len(rows),
        "observed_stats": sorted(observed_stats),
        "observed_role_buckets": sorted(observed_roles),
        "missing_cells": missing_cells,
        "extra_cells": extra_cells,
        "forbidden_stats_present": forbidden_present,
        "status_counts": status_counts,
        "review_cells_count": len(review_cells),
        "needs_more_data_cells_count": len(needs_more_data_cells),
        "guarded_fallback_cells_count": len(guarded_fallback_cells),
        "market_eval_available": meta.get("market_eval_available"),
        "m6_3_report_pass": meta.get("m6_3_report_pass"),
    })
    summary["valid"] = not summary["issues"]
    summary["detail"] = "valid" if summary["valid"] else "; ".join(summary["issues"])

    return {
        "summary": summary,
        "review_cells": review_cells,
        "needs_more_data_cells": needs_more_data_cells,
        "stat_role_guarded_policy": policy,
        "review_cells_require_guarded_fallback": bool(review_cells),
    }


def _load_rolling_market_benchmark(as_of_date: str) -> dict | None:
    """Phase 13K: load the rolling market benchmark for ``as_of_date`` if
    present. Returns the JSON payload or None when missing."""
    p = (
        REPO_ROOT
        / "artifacts"
        / "market_benchmark"
        / as_of_date
        / "rolling_market_benchmark.json"
    )
    if not p.exists():
        return None
    try:
        return read_json(p)
    except Exception:
        return None


def evaluate_gates(
    *,
    pointer: dict,
    train_manifest: dict,
    cal_manifest: dict,
    pmf_validity: dict,
    derek_ok: bool,
    woo_ok: bool,
    champion_metrics: dict | None = None,
    challenger_metrics: dict | None = None,
    market_benchmark: dict | None = None,
    allow_missing_market_benchmark: bool = False,
    m6_3_policy: dict | None = None,
) -> tuple[list[dict], list[dict], str | None]:
    """Apply the Phase 13A/D promotion gates. Returns (passed, failed, blocking_reason)."""
    gates: list[tuple[str, bool, str]] = []

    dry_run = bool(train_manifest.get("dry_run", True)) or bool(cal_manifest.get("dry_run", True))

    # 1-9: comparative metrics.
    cm = champion_metrics or {}
    chm = challenger_metrics or {}
    if dry_run:
        # In dry-run challenger == champion; comparisons cannot improve.
        for name in (
            "nll_improves_or_non_worse",
            "rps_improves_or_non_worse",
            "calibration_error_improves",
            "p0_error_improves_or_non_worse",
            "mean_bias_does_not_worsen",
            "tov_does_not_regress",
            "starter_core_role_buckets_do_not_regress",
            "bench_fringe_role_buckets_do_not_regress_materially",
            "no_severe_stat_bucket_regression",
        ):
            gates.append(
                (name, False, "dry_run challenger == champion; no improvement to demonstrate")
            )
    else:
        # Phase 13D: real numeric comparison. Tolerances are conservative.
        # NLL / RPS / p0: challenger may not be worse by more than 1% relative.
        # mean_bias: absolute value may not grow by more than 0.05.
        cm_nll = cm.get("nll") or 0.0
        cm_rps = cm.get("rps") or 0.0
        gates.append(
            _compare_gate("nll_improves_or_non_worse",
                          chm.get("nll"), cm.get("nll"),
                          lower_is_better=True,
                          tolerance=abs(cm_nll) * 0.01)
        )
        gates.append(
            _compare_gate("rps_improves_or_non_worse",
                          chm.get("rps"), cm.get("rps"),
                          lower_is_better=True,
                          tolerance=abs(cm_rps) * 0.01)
        )
        # Calibration error proxy: p0 calibration overall.
        gates.append(
            _compare_gate("calibration_error_improves",
                          chm.get("p0_calibration"), cm.get("p0_calibration"),
                          lower_is_better=True,
                          tolerance=0.0)  # strictly improve or tie
        )
        gates.append(
            _compare_gate("p0_error_improves_or_non_worse",
                          chm.get("p0_calibration"), cm.get("p0_calibration"),
                          lower_is_better=True,
                          tolerance=0.005)  # 0.5pp absolute slack
        )
        # Mean bias: compare absolute values.
        ch_bias = chm.get("mean_error")
        cm_bias = cm.get("mean_error")
        gates.append(
            _compare_gate("mean_bias_does_not_worsen",
                          abs(ch_bias) if ch_bias is not None else None,
                          abs(cm_bias) if cm_bias is not None else None,
                          lower_is_better=True,
                          tolerance=0.05)
        )
        # TOV: NLL must not regress.
        ch_tov = chm.get("tov", {}) or {}
        cm_tov = cm.get("tov", {}) or {}
        cm_tov_nll = cm_tov.get("nll") or 0.0
        gates.append(
            _compare_gate("tov_does_not_regress",
                          ch_tov.get("nll"), cm_tov.get("nll"),
                          lower_is_better=True,
                          tolerance=abs(cm_tov_nll) * 0.02)
        )
        # Role bucket gates: starter/core must not regress; bench/fringe/rotation
        # may degrade slightly.
        ch_roles = chm.get("by_role_bucket", {}) or {}
        cm_roles = cm.get("by_role_bucket", {}) or {}
        core_buckets = ("starter", "core")
        worst_core_delta: float | None = None
        for b in core_buckets:
            ch_v = (ch_roles.get(b) or {}).get("nll")
            cm_v = (cm_roles.get(b) or {}).get("nll")
            d = _delta(ch_v, cm_v)
            if d is not None:
                worst_core_delta = max(worst_core_delta, d) if worst_core_delta is not None else d
        gates.append(
            (
                "starter_core_role_buckets_do_not_regress",
                worst_core_delta is None or worst_core_delta <= 0.01,
                f"worst_core_nll_delta={worst_core_delta}",
            )
        )
        bench_buckets = ("bench", "fringe", "rotation")
        worst_bench_delta: float | None = None
        for b in bench_buckets:
            ch_v = (ch_roles.get(b) or {}).get("nll")
            cm_v = (cm_roles.get(b) or {}).get("nll")
            d = _delta(ch_v, cm_v)
            if d is not None:
                worst_bench_delta = max(worst_bench_delta, d) if worst_bench_delta is not None else d
        gates.append(
            (
                "bench_fringe_role_buckets_do_not_regress_materially",
                worst_bench_delta is None or worst_bench_delta <= 0.05,
                f"worst_bench_nll_delta={worst_bench_delta}",
            )
        )
        # No severe stat bucket regression: per-stat NLL delta cap.
        ch_by_stat = chm.get("by_stat", {}) or {}
        cm_by_stat = cm.get("by_stat", {}) or {}
        worst_stat_delta: float | None = None
        worst_stat: str | None = None
        for s in SUPPORTED_STATS:
            ch_v = (ch_by_stat.get(s) or {}).get("nll")
            cm_v = (cm_by_stat.get(s) or {}).get("nll")
            d = _delta(ch_v, cm_v)
            if d is not None:
                if worst_stat_delta is None or d > worst_stat_delta:
                    worst_stat_delta = d
                    worst_stat = s
        gates.append(
            (
                "no_severe_stat_bucket_regression",
                worst_stat_delta is None or worst_stat_delta <= 0.05,
                f"worst_stat={worst_stat} delta={worst_stat_delta}",
            )
        )

    # 10: PMF validity must have no issues.
    pmf_ok = not pmf_validity.get("issues")
    gates.append(
        (
            "pmf_validity",
            pmf_ok,
            "ok" if pmf_ok else f"issues={pmf_validity.get('issues', [])[:5]}",
        )
    )

    # 11: no future leakage.
    # Dry-run reads player_game_stats for an honest window summary; missing parquet/date
    # column correctly fails. Real aggregate training leakage is enforced when building
    # fold_aggregate.parquet — that path can succeed even when the boxscore parquet is
    # absent on a runner (summary may carry advisory error); do not falsely fail.
    summary = train_manifest.get("training_summary", {}) or {}
    is_dry = bool(train_manifest.get("dry_run", True))
    if is_dry:
        no_leakage = (summary.get("future_rows_excluded", 0) >= 0) and not summary.get(
            "error"
        )
        leak_detail = (
            f"dry_run future_rows_excluded={summary.get('future_rows_excluded')} "
            f"error={summary.get('error')!r}"
        )
    else:
        no_leakage = train_manifest.get("status") == "ok"
        leak_detail = (
            f"real_train train_manifest.status={train_manifest.get('status')!r}; "
            f"pg_stats_summary.error={summary.get('error')!r} "
            "(OOF fold_aggregate cutoff is leakage authority)"
        )
    gates.append(
        (
            "no_future_leakage",
            bool(no_leakage),
            leak_detail,
        )
    )

    # 12: enough sample for the decision.
    samples = sum((cal_manifest.get("details", {}) or {}).get("samples_by_stat", {}).values())
    gates.append(
        (
            "sufficient_calibration_samples",
            samples > 0,
            f"total_samples_in_calibration_window={samples}",
        )
    )

    # 13-14: Derek / WoO compatibility (script presence only; informational).
    gates.append(("derek_feed_compatibility", bool(derek_ok), "ok" if derek_ok else "missing"))
    gates.append(("woo_export_compatibility", bool(woo_ok), "ok" if woo_ok else "missing"))

    # 15: no Phase 10D / 10D.2 overlay tokens in either manifest.
    overlay_hits = scan_for_forbidden_overlay_tokens(
        {"pointer": pointer, "train": train_manifest, "calibration": cal_manifest}
    )
    gates.append(
        (
            "no_phase10d_overlays_referenced",
            not overlay_hits,
            "ok" if not overlay_hits else f"hits={overlay_hits[:3]}",
        )
    )

    # ── M7: M6.3 stat×role guarded calibration policy gate ─────────────
    m6_3_policy = m6_3_policy or {}
    m6_3_summary = m6_3_policy.get("summary", {}) or {}
    m6_3_review_cells = m6_3_policy.get("review_cells", []) or []
    m6_3_policy_block = m6_3_policy.get("stat_role_guarded_policy", {}) or {}
    guarded_cells = {
        (str(c.get("stat")), str(c.get("role_bucket")))
        for c in (m6_3_policy_block.get("guarded_fallback_required_cells") or [])
    }
    review_cells = {
        (str(c.get("stat")), str(c.get("role_bucket")))
        for c in m6_3_review_cells
    }
    gates.append((
        "m6_3_stat_role_matrix_valid",
        bool(m6_3_summary.get("valid")),
        m6_3_summary.get("detail", "m6_3 summary missing"),
    ))
    gates.append((
        "m6_3_review_cells_guarded",
        bool(m6_3_summary.get("valid")) and review_cells.issubset(guarded_cells),
        f"review_cells={len(review_cells)} guarded_cells={len(guarded_cells)}",
    ))

    # ── Phase 13K: rolling model-vs-market benchmark gates ─────────────
    # Hard when sample threshold is met; explicit insufficient_sample
    # failure when not — never silent pass. allow_missing_market_benchmark
    # is an opt-in operator override (e.g. for backfill runs).
    if market_benchmark is None:
        if allow_missing_market_benchmark:
            gates.append((
                "market_benchmark_available",
                True,
                "missing benchmark, but --allow-missing-market-benchmark is set",
            ))
        else:
            gates.append((
                "market_benchmark_available",
                False,
                "rolling market benchmark JSON not produced for this date",
            ))
    else:
        gates.append((
            "market_benchmark_available",
            True,
            f"rows_total={market_benchmark.get('rows_total')} "
            f"dates_included={len(market_benchmark.get('dates_included') or [])}",
        ))
        sample_passed = bool(market_benchmark.get("minimum_sample_passed"))
        delta_ll = market_benchmark.get("delta_logloss")
        delta_brier = market_benchmark.get("delta_brier")
        # Non-inferior tolerances (model may be slightly worse than market and
        # still pass on a noisy 28-day window). Lower-is-better; positive
        # delta = model worse than market.
        ll_tol = 0.005   # 0.5 abs nats
        brier_tol = 0.005  # 0.5 abs Brier
        if not sample_passed:
            gates.append((
                "market_logloss_non_inferior_or_better",
                False,
                f"insufficient_sample (rows_total={market_benchmark.get('rows_total')}, "
                f"min_required={market_benchmark.get('min_overall_rows')})",
            ))
            gates.append((
                "market_brier_non_inferior_or_better",
                False,
                "insufficient_sample (see market_logloss_non_inferior_or_better)",
            ))
            gates.append((
                "no_severe_market_stat_bucket_regression",
                False,
                "insufficient_sample",
            ))
        else:
            gates.append((
                "market_logloss_non_inferior_or_better",
                delta_ll is not None and delta_ll <= ll_tol,
                f"delta_logloss={delta_ll} tolerance={ll_tol} (negative favors model)",
            ))
            gates.append((
                "market_brier_non_inferior_or_better",
                delta_brier is not None and delta_brier <= brier_tol,
                f"delta_brier={delta_brier} tolerance={brier_tol} (negative favors model)",
            ))
            # Per-stat severe regression: any stat with delta_logloss > 0.05.
            severe_stat = None
            severe_delta = None
            for r in (market_benchmark.get("by_stat") or []):
                if not r.get("minimum_sample_passed"):
                    continue
                d = r.get("delta_logloss")
                if d is None:
                    continue
                if d > 0.05 and (severe_delta is None or d > severe_delta):
                    severe_stat, severe_delta = r.get("stat"), d
            gates.append((
                "no_severe_market_stat_bucket_regression",
                severe_stat is None,
                ("ok" if severe_stat is None
                 else f"severe market regression on {severe_stat}: delta_logloss={severe_delta:+.4f}"),
            ))

    passed = [{"name": n, "detail": d} for n, ok, d in gates if ok]
    failed = [{"name": n, "detail": d} for n, ok, d in gates if not ok]

    blocking_reason: str | None = None
    if failed:
        blocking_reason = failed[0]["name"]

    return passed, failed, blocking_reason


def main(argv: list[str] | None = None) -> int:
    # Phase 14 dispatch — calibration A/B short-circuit (extension per
    # Joseph + LLM spec). When invoked with --ab-mode, route to the
    # same-row A/B comparison and exit; do not run champion/challenger.
    _argv = list(argv) if argv is not None else sys.argv[1:]
    if "--ab-mode" in _argv:
        from _calibration_ab import ab_main as _ab_main
        return _ab_main(_argv)
    p = argparse.ArgumentParser(description="Validate champion vs challenger.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--challenger-dir", help="Override challenger dir")
    p.add_argument(
        "--allow-missing-market-benchmark",
        action="store_true",
        help=(
            "Phase 13K: opt-in operator override that lets validation proceed "
            "without a rolling market benchmark file. Combined with --no-promote "
            "this is safe for backfill / soak runs. The scheduled workflow does "
            "NOT pass this flag — missing benchmark is a hard fail by default."
        ),
    )
    args = p.parse_args(argv)

    as_of = parse_date(args.as_of_date)
    ch_dir = (
        Path(args.challenger_dir).resolve() if args.challenger_dir else challenger_dir(args.as_of_date)
    )
    if not ch_dir.exists():
        print(json.dumps({"error": f"challenger dir does not exist: {ch_dir}"}))
        return 2

    pointer = load_champion_pointer()
    train_manifest_path = ch_dir / "train_manifest.json"
    cal_manifest_path = ch_dir / "calibration_manifest.json"
    if not train_manifest_path.exists() or not cal_manifest_path.exists():
        print(
            json.dumps(
                {
                    "error": "train_manifest.json or calibration_manifest.json missing",
                    "challenger_dir": str(ch_dir.relative_to(REPO_ROOT)),
                }
            )
        )
        return 2

    train_manifest = read_json(train_manifest_path)
    cal_manifest = read_json(cal_manifest_path)

    pmf_validity = pmf_validity_checks(ch_dir)
    derek = derek_compat_check()
    woo = woo_compat_check()

    dry_run_combined = bool(train_manifest.get("dry_run", True)) or bool(
        cal_manifest.get("dry_run", True)
    )
    if dry_run_combined:
        # Dry-run: both sides reference identical artifacts; placeholder metrics suffice.
        champion_metrics = metrics_placeholder()
        challenger_metrics = metrics_placeholder()
    else:
        # Phase 13D: real numeric scoring. Score both sides on the same OOF
        # holdout window. The OOF parquet used here is the one written by
        # the challenger's calibrate_pmf.py run (under <ch_dir>/) — that
        # file is the ground-truth-uncalibrated-PMFs + actual outcomes for
        # the walk-forward holdout. We apply each side's calibrator on top.
        challenger_oof = ch_dir / "oof_pmfs.parquet"
        oof_path_for_scoring = challenger_oof if challenger_oof.exists() else None
        champion_dir = REPO_ROOT / pointer.get("model_dir", "artifacts/models")
        challenger_metrics = score_pmfs_from_oof(
            model_dir=ch_dir,
            as_of_date=as_of,
            oof_path_override=oof_path_for_scoring,
        )
        champion_metrics = score_pmfs_from_oof(
            model_dir=champion_dir,
            as_of_date=as_of,
            oof_path_override=oof_path_for_scoring,
        )
        # Surface PMF-validity issues from real scoring into the gate.
        for side, m in (("champion", champion_metrics), ("challenger", challenger_metrics)):
            issues = m.get("pmf_validity_issues") or []
            for iss in issues:
                pmf_validity.setdefault("issues", []).append(f"{side}: {iss}")

    # Phase 13K: load rolling market benchmark for the same as_of_date.
    market_benchmark = _load_rolling_market_benchmark(args.as_of_date)
    m6_3_policy = _load_m6_3_stat_role_policy()
    passed, failed, blocking_reason = evaluate_gates(
        pointer=pointer,
        train_manifest=train_manifest,
        cal_manifest=cal_manifest,
        pmf_validity=pmf_validity,
        derek_ok=derek["passed"],
        woo_ok=woo["passed"],
        champion_metrics=champion_metrics,
        challenger_metrics=challenger_metrics,
        market_benchmark=market_benchmark,
        allow_missing_market_benchmark=bool(args.allow_missing_market_benchmark),
        m6_3_policy=m6_3_policy,
    )

    promote = len(failed) == 0
    decision_reason = (
        "all_gates_passed"
        if promote
        else f"gate_failed:{blocking_reason}"
    )

    # Secret scan on what we're about to write.
    payload_for_secret_scan = {
        "pointer": pointer,
        "train_manifest": train_manifest,
        "cal_manifest": cal_manifest,
    }
    secret_hits = scan_for_secrets(payload_for_secret_scan)
    if secret_hits:
        promote = False
        decision_reason = "secret_in_manifest_aborted_promotion"
        failed.append({"name": "no_secrets_in_manifests", "detail": str(secret_hits[:3])})

    validation_report = {
        "schema_version": "1.0",
        "as_of_date": args.as_of_date,
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "champion": {
            "model_version": pointer.get("model_version"),
            "calibrator_version": pointer.get("calibrator_version"),
            "code_commit": pointer.get("code_commit"),
            "metrics": champion_metrics,
        },
        "challenger": {
            "model_version": (
                (train_manifest.get("training_summary") or {}).get("model_version")
                or f"challenger-{args.as_of_date}"
            ),
            "dry_run": bool(train_manifest.get("dry_run", True)),
            "calibrator_version": cal_manifest.get("calibrator_type", "phase8-role-bucket"),
            "code_commit": train_manifest.get("code_commit"),
            "metrics": challenger_metrics,
        },
        "calibration_blend_policy": ROLE_AWARE_BLEND_POLICY,
        "m6_3_stat_role_matrix_path": m6_3_policy["summary"]["matrix_path"],
        "m6_3_matrix_summary": m6_3_policy["summary"],
        "m6_3_review_cells": m6_3_policy["review_cells"],
        "m6_3_needs_more_data_cells": m6_3_policy["needs_more_data_cells"],
        "stat_role_guarded_policy": m6_3_policy["stat_role_guarded_policy"],
        "review_cells_require_guarded_fallback": m6_3_policy["review_cells_require_guarded_fallback"],
        "pmf_validity": pmf_validity,
        "derek_compatibility": derek,
        "woo_compatibility": woo,
        "gates_passed": passed,
        "gates_failed": failed,
        "phase10d_overlays_in_use": False,
        "market_benchmark": market_benchmark or None,
        "market_benchmark_manifest_path": (
            f"artifacts/market_benchmark/{args.as_of_date}/rolling_market_benchmark.json"
            if market_benchmark is not None else None
        ),
        "market_gates_passed": [
            g["name"] for g in passed if g["name"].startswith("market_") or g["name"].startswith("no_severe_market_")
        ],
        "market_gates_failed": [
            g["name"] for g in failed if g["name"].startswith("market_") or g["name"].startswith("no_severe_market_")
        ],
    }
    write_json_atomic(ch_dir / "validation_report.json", validation_report)

    promotion_decision = {
        "schema_version": "1.0",
        "as_of_date": args.as_of_date,
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "promote": bool(promote),
        "reason": decision_reason,
        "gates_passed": [g["name"] for g in passed],
        "gates_failed": [g["name"] for g in failed],
        "champion_metrics": champion_metrics,
        "challenger_metrics": challenger_metrics,
        "calibration_blend_policy": ROLE_AWARE_BLEND_POLICY,
        "m6_3_matrix_summary": m6_3_policy["summary"],
        "m6_3_review_cells": m6_3_policy["review_cells"],
        "stat_role_guarded_policy": m6_3_policy["stat_role_guarded_policy"],
        "market_benchmark": market_benchmark or None,
        "market_benchmark_manifest_path": (
            f"artifacts/market_benchmark/{args.as_of_date}/rolling_market_benchmark.json"
            if market_benchmark is not None else None
        ),
        "market_gates_passed": [
            g["name"] for g in passed if g["name"].startswith("market_") or g["name"].startswith("no_severe_market_")
        ],
        "market_gates_failed": [
            g["name"] for g in failed if g["name"].startswith("market_") or g["name"].startswith("no_severe_market_")
        ],
        "warnings": [],
    }
    write_json_atomic(ch_dir / "promotion_decision.json", promotion_decision)

    # validation_summary.md
    md_lines = [
        f"# Champion vs Challenger Validation — {args.as_of_date}",
        "",
        md_table(
            [
                ("Generated (UTC)", validation_report["generated_at_utc"]),
                ("Promote", "YES" if promote else "no"),
                ("Reason", decision_reason),
                ("Champion model_version", str(pointer.get("model_version"))),
                ("Challenger dry_run", str(train_manifest.get("dry_run", True))),
                ("PMF validity issues", str(len(pmf_validity.get("issues", [])))),
                ("Gates passed", str(len(passed))),
                ("Gates failed", str(len(failed))),
            ]
        ),
        "",
        "## Gates passed",
        "",
    ]
    md_lines += [f"- {g['name']}: {g['detail']}" for g in passed] or ["- (none)"]
    md_lines += ["", "## Gates failed", ""]
    md_lines += [f"- {g['name']}: {g['detail']}" for g in failed] or ["- (none)"]
    (ch_dir / "validation_summary.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "as_of_date": args.as_of_date,
                "promote": promote,
                "reason": decision_reason,
                "gates_failed": [g["name"] for g in failed],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
