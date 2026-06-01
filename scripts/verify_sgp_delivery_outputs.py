#!/usr/bin/env python3
"""Verify SGP delivery outputs for a given slate date.

Performs hard-failure checks (exits 1 on failure) and soft warnings
(prints to stderr, continues). Prints a structured summary line.

Usage
-----
  python3 scripts/verify_sgp_delivery_outputs.py --date 2026-05-30 --repo-root .
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="Slate date YYYY-MM-DD")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    slate_date = args.date
    sgp_root = repo_root / "deliveries" / slate_date / "sgp_engine"
    bundle_dir = sgp_root / "slate_state_bundle_v1"

    hard_failures: list[str] = []
    warnings: list[str] = []

    # ── Required file presence checks ─────────────────────────────────────────

    def _require(path: Path, label: str) -> bool:
        if not path.exists():
            hard_failures.append(f"MISSING REQUIRED: {label} ({path.relative_to(repo_root)})")
            return False
        return True

    def _warn_missing(path: Path, label: str) -> bool:
        if not path.exists():
            warnings.append(f"missing {label} ({path.relative_to(repo_root)})")
            return False
        return True

    # Bundle.
    _require(bundle_dir / "bundle_manifest.json", "bundle_manifest.json")
    _warn_missing(bundle_dir / "data_quality_report.json", "data_quality_report.json")
    _warn_missing(bundle_dir / "source_file_audit.json", "source_file_audit.json")
    _warn_missing(bundle_dir / "player_stat_pmfs.parquet", "player_stat_pmfs.parquet")
    _warn_missing(bundle_dir / "factor_weights_used.json", "factor_weights_used.json")
    _warn_missing(bundle_dir / "calibration_context.parquet", "calibration_context.parquet")

    # Simulation.
    _require(sgp_root / "simulation" / "simulation_diagnostics.json", "simulation_diagnostics.json")
    _require(sgp_root / "simulation" / "dependency_diagnostics.parquet", "dependency_diagnostics.parquet")
    _require(sgp_root / "simulation" / "marginal_preservation_report.parquet", "marginal_preservation_report.parquet")
    _warn_missing(sgp_root / "simulation" / "combo_coherence_report.parquet", "combo_coherence_report.parquet")

    # Prices.
    _require(sgp_root / "prices" / "sgp_price_grid.parquet", "sgp_price_grid.parquet")
    _warn_missing(sgp_root / "prices" / "sgp_price_grid.csv", "sgp_price_grid.csv")

    # Calibration.
    _require(sgp_root / "calibration" / "sgp_calibration_report.json", "sgp_calibration_report.json")
    _require(sgp_root / "calibration" / "sgp_gate_status.json", "sgp_gate_status.json")
    _warn_missing(sgp_root / "calibration" / "sgp_reliability_by_bucket.csv", "sgp_reliability_by_bucket.csv")
    _warn_missing(sgp_root / "calibration" / "sgp_reliability_by_segment.csv", "sgp_reliability_by_segment.csv")

    # Market comparison.
    _warn_missing(sgp_root / "market_comparison" / "sgp_market_comparison.parquet", "sgp_market_comparison.parquet")
    _warn_missing(sgp_root / "market_comparison" / "sgp_market_comparison.csv", "sgp_market_comparison.csv")
    _warn_missing(sgp_root / "market_comparison" / "sgp_publishable_edges.csv", "sgp_publishable_edges.csv")
    _warn_missing(sgp_root / "market_comparison" / "sgp_publishable_edges.parquet", "sgp_publishable_edges.parquet")

    # WoO export.
    _require(sgp_root / "woo_export" / "sgp_index.html", "woo_export/sgp_index.html")
    _warn_missing(
        repo_root / "public_export" / "wizard_of_odds" / "sgp" / "index.html",
        "public_export/wizard_of_odds/sgp/index.html",
    )

    # ── 1. bundle_manifest.json status = PASS ─────────────────────────────────
    manifest_path = bundle_dir / "bundle_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            status = manifest.get("bundle_status", manifest.get("status", "UNKNOWN"))
            if status != "PASS":
                hard_failures.append(f"bundle_manifest status={status!r} (expected PASS)")
        except Exception as exc:
            hard_failures.append(f"bundle_manifest.json unreadable: {exc}")

    # ── 2. as-of contract must pass ───────────────────────────────────────────
    asof_path = bundle_dir / "asof_contract.json"
    if asof_path.exists():
        try:
            asof = json.loads(asof_path.read_text())
            asof_status = asof.get("status", "UNKNOWN")
            if asof_status not in {"PASS", "VALID_SKIP"}:
                hard_failures.append(f"asof_contract.status={asof_status!r} (expected PASS or VALID_SKIP)")
        except Exception as exc:
            warnings.append(f"asof_contract.json unreadable: {exc}")
    else:
        warnings.append("asof_contract.json missing (as-of gate not run)")

    # ── 3. Price grid data checks ─────────────────────────────────────────────
    price_parquet = sgp_root / "prices" / "sgp_price_grid.parquet"
    price_df: pd.DataFrame | None = None
    if price_parquet.exists():
        try:
            price_df = pd.read_parquet(price_parquet)
        except Exception as exc:
            hard_failures.append(f"sgp_price_grid.parquet unreadable: {exc}")

    if price_df is not None and not price_df.empty:
        # Probability validity.
        for col in ["calibrated_joint_probability", "raw_joint_probability",
                    "independent_probability_pmf_marginals", "independent_probability"]:
            if col not in price_df.columns:
                continue
            col_vals = pd.to_numeric(price_df[col], errors="coerce").dropna()
            if len(col_vals) == 0:
                continue
            below = int((col_vals < 0).sum())
            above = int((col_vals > 1).sum())
            if below > 0 or above > 0:
                hard_failures.append(f"{col}: {below} below 0, {above} above 1")

        # fair_decimal_odds must be finite and positive.
        if "fair_decimal_odds" in price_df.columns:
            odds_vals = pd.to_numeric(price_df["fair_decimal_odds"], errors="coerce")
            n_bad = int((~np.isfinite(odds_vals.fillna(np.nan)) | (odds_vals <= 0)).sum())
            if n_bad > 0:
                hard_failures.append(f"fair_decimal_odds: {n_bad} rows not finite/positive")

        # simulation_count must be present and >= threshold.
        if "simulation_count" in price_df.columns:
            n_low = int((pd.to_numeric(price_df["simulation_count"], errors="coerce").fillna(0) < 1000).sum())
            if n_low > 0:
                warnings.append(f"{n_low} tickets have simulation_count < 1000")

        # No CERTIFIED rows when backtest is empty.
        backtest_path = repo_root / "data" / "sgp_backtest_rows.parquet"
        has_backtest = False
        if backtest_path.exists():
            try:
                bt = pd.read_parquet(backtest_path)
                has_backtest = len(bt.dropna(subset=["actual_hit"]
                                               if "actual_hit" in bt.columns
                                               else ["hit_result"] if "hit_result" in bt.columns
                                               else [])) > 50
            except Exception:
                pass
        if not has_backtest and "tier" in price_df.columns:
            n_cert = int((price_df["tier"] == "CERTIFIED").sum())
            if n_cert > 0:
                hard_failures.append(
                    f"{n_cert} CERTIFIED rows present but no backtest data exists "
                    "(market superiority not earned)"
                )

        # market_corr_factor_source must be present.
        if "market_corr_factor_source" not in price_df.columns:
            hard_failures.append("price grid missing market_corr_factor_source column")

        # actual_sgp_market_odds_available must be present.
        if "actual_sgp_market_odds_available" not in price_df.columns:
            hard_failures.append("price grid missing actual_sgp_market_odds_available column")

        # Correlation factor check.
        if "model_corr_factor" in price_df.columns:
            cf_vals = pd.to_numeric(price_df["model_corr_factor"], errors="coerce").dropna()
            if len(cf_vals) == 0:
                warnings.append("model_corr_factor column is entirely null")

    # ── 4. Marginal preservation check ───────────────────────────────────────
    marg_path = sgp_root / "simulation" / "marginal_preservation_report.parquet"
    if marg_path.exists():
        try:
            marg_df = pd.read_parquet(marg_path)
            if not marg_df.empty:
                err_col = "p_over_abs_diff" if "p_over_abs_diff" in marg_df.columns else "abs_error"
                if err_col in marg_df.columns:
                    errs = pd.to_numeric(marg_df[err_col], errors="coerce").dropna()
                    mean_err = float(errs.mean()) if len(errs) > 0 else 0.0
                    fail_rate = float((errs > 0.05).mean()) if len(errs) > 0 else 0.0

                    if mean_err > 0.05:
                        hard_failures.append(
                            f"Marginal preservation FAIL: mean abs_error={mean_err:.4f} > 0.05 "
                            "(structural bias detected — Dirichlet fix may not have taken effect)"
                        )
                    elif mean_err > 0.02:
                        warnings.append(
                            f"Marginal preservation WARN: mean abs_error={mean_err:.4f} > 0.02"
                        )

                    if fail_rate > 0.20:
                        hard_failures.append(
                            f"Marginal preservation FAIL: fail_rate={fail_rate:.2%} > 20% of rows"
                        )

                # Check for systematic bias.
                if "signed_p_over_diff" in marg_df.columns:
                    signed = pd.to_numeric(marg_df["signed_p_over_diff"], errors="coerce").dropna()
                    if len(signed) > 10:
                        mean_bias = float(signed.mean())
                        if abs(mean_bias) > 0.03:
                            warnings.append(
                                f"Marginal preservation systematic bias: mean_signed_diff={mean_bias:.4f} "
                                "(should be near 0)"
                            )
        except Exception as exc:
            warnings.append(f"marginal_preservation_report.parquet unreadable: {exc}")

    # ── 5. Simulation diagnostics ─────────────────────────────────────────────
    sim_diag_path = sgp_root / "simulation" / "simulation_diagnostics.json"
    if sim_diag_path.exists():
        try:
            sim_diag = json.loads(sim_diag_path.read_text())
            n_sims = int(sim_diag.get("n_sims", 0))
            if n_sims < 10_000:
                warnings.append(f"n_sims={n_sims} < 10000 (low simulation count)")
            # Check marginal preservation status from diagnostics.
            mp_status = sim_diag.get("marginal_preservation_status")
            if mp_status == "FAIL":
                hard_failures.append(
                    "simulation_diagnostics.json reports marginal_preservation_status=FAIL"
                )
        except Exception:
            warnings.append("simulation_diagnostics.json unreadable")

    # ── 6. Dependency diagnostics schema check ────────────────────────────────
    dep_diag_path = sgp_root / "simulation" / "dependency_diagnostics.parquet"
    if dep_diag_path.exists():
        try:
            dep_df = pd.read_parquet(dep_diag_path)
            if not dep_df.empty:
                required_dep_cols = {
                    "game_id", "player_a", "stat_a", "team_a",
                    "player_b", "stat_b", "team_b",
                    "relationship_type", "simulated_pearson_r",
                }
                missing_dep_cols = required_dep_cols - set(dep_df.columns)
                if missing_dep_cols:
                    warnings.append(
                        f"dependency_diagnostics.parquet missing columns: {sorted(missing_dep_cols)}"
                    )
                r_col = "simulated_pearson_r"
                if r_col in dep_df.columns:
                    bad_r = int((~np.isfinite(
                        pd.to_numeric(dep_df[r_col], errors="coerce").fillna(np.nan)
                    )).sum())
                    if bad_r > 0:
                        warnings.append(f"dependency_diagnostics: {bad_r} non-finite pearson_r values")
        except Exception as exc:
            warnings.append(f"dependency_diagnostics.parquet unreadable: {exc}")

    # ── 7. factor_weights_used.json check ────────────────────────────────────
    fw_used_path = bundle_dir / "factor_weights_used.json"
    if fw_used_path.exists():
        try:
            fw = json.loads(fw_used_path.read_text())
            if fw.get("fallback_used") and not fw.get("warnings"):
                warnings.append("factor_weights_used: fallback defaults used (no learned weights)")
        except Exception:
            warnings.append("factor_weights_used.json unreadable")

    # ── 8. Gate status check ──────────────────────────────────────────────────
    gate_path = sgp_root / "calibration" / "sgp_gate_status.json"
    if gate_path.exists():
        try:
            gate = json.loads(gate_path.read_text())
            gs = gate.get("gate_status", "UNKNOWN")
            if gs not in {"PASS", "MODEL_PRICE", "DIAGNOSTIC_ONLY", "INSUFFICIENT_SAMPLE"}:
                warnings.append(f"sgp_gate_status={gs!r} (unexpected value)")
        except Exception:
            warnings.append("sgp_gate_status.json unreadable")

    # ── Print warnings to stderr ───────────────────────────────────────────────
    for w in warnings:
        print(f"::warning::{w}", file=sys.stderr)

    # ── Print summary ─────────────────────────────────────────────────────────
    if hard_failures:
        print(
            f"SGP_DELIVERY_VERIFICATION  date={slate_date}  status=FAIL  "
            f"hard_failures={len(hard_failures)}  warnings={len(warnings)}"
        )
        for hf in hard_failures:
            print(f"::error::{hf}")
        return 1

    print(
        f"SGP_DELIVERY_VERIFICATION  date={slate_date}  status=PASS  "
        f"hard_failures=0  warnings={len(warnings)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
