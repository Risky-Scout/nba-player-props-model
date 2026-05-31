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

    hard_failures: list[str] = []
    warnings: list[str] = []

    # ── Hard failure checks ───────────────────────────────────────────────────

    # 1. bundle_manifest.json must exist and have status=PASS
    manifest_path = sgp_root / "slate_state_bundle_v1" / "bundle_manifest.json"
    if not manifest_path.exists():
        hard_failures.append("bundle_manifest.json missing")
    else:
        try:
            manifest = json.loads(manifest_path.read_text())
            status = manifest.get("bundle_status", manifest.get("status", "UNKNOWN"))
            if status != "PASS":
                hard_failures.append(f"bundle_manifest status={status!r} (expected PASS)")
        except Exception as exc:
            hard_failures.append(f"bundle_manifest.json unreadable: {exc}")

    # 2. Price grid must exist
    price_parquet = sgp_root / "prices" / "sgp_price_grid.parquet"
    price_df: pd.DataFrame | None = None
    if not price_parquet.exists():
        hard_failures.append(f"sgp_price_grid.parquet missing at {price_parquet}")
    else:
        try:
            price_df = pd.read_parquet(price_parquet)
        except Exception as exc:
            hard_failures.append(f"sgp_price_grid.parquet unreadable: {exc}")

    # 3. Probability validity — all probabilities in [0, 1]
    if price_df is not None and not price_df.empty:
        prob_cols = [c for c in [
            "calibrated_joint_probability", "raw_joint_probability",
            "independent_probability_pmf_marginals",
        ] if c in price_df.columns]
        for col in prob_cols:
            col_vals = pd.to_numeric(price_df[col], errors="coerce").dropna()
            if len(col_vals) == 0:
                continue
            below = (col_vals < 0).sum()
            above = (col_vals > 1).sum()
            if below > 0 or above > 0:
                hard_failures.append(
                    f"{col}: {below} below 0, {above} above 1 (must be in [0,1])"
                )

    # 4. fair_decimal_odds must be finite and positive
    if price_df is not None and not price_df.empty and "fair_decimal_odds" in price_df.columns:
        odds_vals = pd.to_numeric(price_df["fair_decimal_odds"], errors="coerce")
        n_bad = int((~np.isfinite(odds_vals.fillna(np.nan)) | (odds_vals <= 0)).sum())
        if n_bad > 0:
            hard_failures.append(
                f"fair_decimal_odds: {n_bad} rows not finite and positive"
            )

    # 5. WoO HTML must exist
    woo_html = sgp_root / "woo_export" / "sgp_index.html"
    if not woo_html.exists():
        hard_failures.append(f"sgp_index.html missing at {woo_html}")

    # ── Soft warnings ─────────────────────────────────────────────────────────

    # Market comparison files missing
    mkt_parquet = sgp_root / "market_comparison" / "sgp_market_comparison.parquet"
    mkt_csv = sgp_root / "market_comparison" / "sgp_market_comparison.csv"
    if not mkt_parquet.exists() and not mkt_csv.exists():
        warnings.append("market_comparison files missing (no market data for this slate)")

    # Calibration gate status
    gate_path = sgp_root / "calibration" / "sgp_gate_status.json"
    if gate_path.exists():
        try:
            gate = json.loads(gate_path.read_text())
            gs = gate.get("gate_status", "UNKNOWN")
            if gs == "INSUFFICIENT_SAMPLE":
                warnings.append(f"calibration_gate_status={gs} (not enough backtest data yet)")
        except Exception:
            warnings.append("sgp_gate_status.json unreadable")
    else:
        warnings.append("sgp_gate_status.json missing (calibration not run)")

    # Simulation count check
    sim_diag_path = sgp_root / "simulation" / "simulation_diagnostics.json"
    if sim_diag_path.exists():
        try:
            sim_diag = json.loads(sim_diag_path.read_text())
            n_sims = int(sim_diag.get("n_sims", 0))
            if n_sims < 10_000:
                warnings.append(f"n_sims={n_sims} < 10000 (low simulation count)")
        except Exception:
            warnings.append("simulation_diagnostics.json unreadable")
    else:
        warnings.append("simulation_diagnostics.json missing")

    # Dependency diagnostics parquet check (soft — may be missing on single-player slates)
    dep_diag_path = sgp_root / "simulation" / "dependency_diagnostics.parquet"
    if not dep_diag_path.exists():
        warnings.append("dependency_diagnostics.parquet missing")
    else:
        try:
            dep_df = pd.read_parquet(dep_diag_path)
            if not dep_df.empty:
                required_dep_cols = {
                    "game_id", "player_a", "stat_a", "player_b", "stat_b",
                    "relationship_type", "simulated_pearson_r",
                }
                missing_dep_cols = required_dep_cols - set(dep_df.columns)
                if missing_dep_cols:
                    warnings.append(
                        f"dependency_diagnostics.parquet missing columns: {sorted(missing_dep_cols)}"
                    )
                bad_r = (~np.isfinite(pd.to_numeric(dep_df["simulated_pearson_r"], errors="coerce").fillna(np.nan))).sum()
                if bad_r > 0:
                    warnings.append(f"dependency_diagnostics: {bad_r} non-finite simulated_pearson_r values")
        except Exception as exc:
            warnings.append(f"dependency_diagnostics.parquet unreadable: {exc}")

    # Correlation factor check (soft — only when market baseline is populated)
    if price_df is not None and not price_df.empty and "model_corr_factor" in price_df.columns:
        cf_vals = pd.to_numeric(price_df["model_corr_factor"], errors="coerce").dropna()
        if len(cf_vals) == 0:
            warnings.append("model_corr_factor column is entirely null — market baseline not computed")

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
