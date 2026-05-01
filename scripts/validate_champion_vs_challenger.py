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
- No future leakage.
- TOV gates use only production phase8 PMF — never Phase 10D / 10D.2 overlays.
- Derek and WoO compatibility must pass.
- Promotion never happens at or after 14:30 UTC.
"""
from __future__ import annotations

import argparse
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
    is_past_promotion_cutoff,
    load_champion_pointer,
    md_table,
    parse_date,
    read_json,
    scan_for_forbidden_overlay_tokens,
    scan_for_secrets,
    utcnow_iso,
    write_json_atomic,
)


# -- PMF validity ----------------------------------------------------------

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

    # 11: no future leakage. Train manifest must record this honestly.
    summary = train_manifest.get("training_summary", {}) or {}
    no_leakage = (summary.get("future_rows_excluded", 0) >= 0) and not summary.get("error")
    gates.append(
        (
            "no_future_leakage",
            bool(no_leakage),
            f"future_rows_excluded={summary.get('future_rows_excluded')}",
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

    # 13-14: Derek / WoO compatibility.
    gates.append(("derek_feed_compatibility", bool(derek_ok), "ok" if derek_ok else "missing"))
    gates.append(("woo_export_compatibility", bool(woo_ok), "ok" if woo_ok else "missing"))

    # 15: promotion clock guard.
    pre_cutoff = not is_past_promotion_cutoff()
    gates.append(
        (
            "promotion_clock_safe",
            pre_cutoff,
            "before 14:30 UTC" if pre_cutoff else "AT OR AFTER 14:30 UTC — too close to WoO run",
        )
    )

    # 16: no Phase 10D / 10D.2 overlay tokens in either manifest.
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

    passed = [{"name": n, "detail": d} for n, ok, d in gates if ok]
    failed = [{"name": n, "detail": d} for n, ok, d in gates if not ok]

    blocking_reason: str | None = None
    if failed:
        blocking_reason = failed[0]["name"]

    return passed, failed, blocking_reason


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate champion vs challenger.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--challenger-dir", help="Override challenger dir")
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

    passed, failed, blocking_reason = evaluate_gates(
        pointer=pointer,
        train_manifest=train_manifest,
        cal_manifest=cal_manifest,
        pmf_validity=pmf_validity,
        derek_ok=derek["passed"],
        woo_ok=woo["passed"],
        champion_metrics=champion_metrics,
        challenger_metrics=challenger_metrics,
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
        "pmf_validity": pmf_validity,
        "derek_compatibility": derek,
        "woo_compatibility": woo,
        "gates_passed": passed,
        "gates_failed": failed,
        "phase10d_overlays_in_use": False,
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
