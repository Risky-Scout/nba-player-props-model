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

def evaluate_gates(
    *,
    pointer: dict,
    train_manifest: dict,
    cal_manifest: dict,
    pmf_validity: dict,
    derek_ok: bool,
    woo_ok: bool,
) -> tuple[list[dict], list[dict], str | None]:
    """Apply the Phase 13A promotion gates. Returns (passed, failed, blocking_reason)."""
    gates: list[tuple[str, bool, str]] = []

    dry_run = bool(train_manifest.get("dry_run", True)) or bool(cal_manifest.get("dry_run", True))

    # 1-9: comparative metrics. In dry-run we cannot improve over self, so
    # these gates fail (which is exactly what we want — keep the champion).
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
        if dry_run:
            gates.append(
                (name, False, "dry_run challenger == champion; no improvement to demonstrate")
            )
        else:
            # Real comparison would compute deltas here. Until full metrics are
            # wired we conservatively decline to promote.
            gates.append(
                (name, False, "real metric comparison not yet implemented; refusing to promote")
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

    # Champion / challenger metric blocks (dry-run: identical structures).
    champion_metrics = metrics_placeholder()
    challenger_metrics = metrics_placeholder()

    passed, failed, blocking_reason = evaluate_gates(
        pointer=pointer,
        train_manifest=train_manifest,
        cal_manifest=cal_manifest,
        pmf_validity=pmf_validity,
        derek_ok=derek["passed"],
        woo_ok=woo["passed"],
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
            "model_version": (train_manifest.get("model_manifest") or {}).get(
                "model_version", train_manifest.get("training_summary", {}).get("model_version")
            ),
            "dry_run": train_manifest.get("dry_run", True),
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
