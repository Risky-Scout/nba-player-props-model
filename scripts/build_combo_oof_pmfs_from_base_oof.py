"""Build combo OOF PMF dataset from base OOF PMFs (NBA Props Model M5C).

For each (game_date, game_id, player_id) group in data/oof_pmfs.parquet,
derive leakage-safe combo OOF PMFs for stocks, pa, pr, pra using a
Gaussian copula whose correlation matrix is estimated from PRIOR dates
only. If insufficient prior data exists, fall back to independence
sampling and label the row accordingly.

Combos derived (canonical -> mission alias):
    stocks -> stl_blk      = stl + blk
    pa     -> pts_ast      = pts + ast
    pr     -> pts_reb      = pts + reb
    pra    -> pts_reb_ast  = pts + reb + ast

Methodology:
    For each unique current_date d:
        prior = OOF rows with game_date < d (expanding window)
        if |prior_player_games| >= MIN_PRIOR_ROWS:
            corr_d = Pearson correlation of (pts, reb, ast, stl, blk)
                     ACTUAL outcomes over prior rows
            method_d = "prior_actual_corr_gaussian_copula_v1"
        else:
            corr_d = None
            method_d = "independence_cold_start_v1"

    For each (player_id, game_id) at date d, for each combo:
        components = COMBO_DEFS[combo]
        seed = sha256(date|player_id|game_id|combo|combo_oof_v1)[:8] -> int
        rng = np.random.default_rng(seed)
        if corr_d is not None:
            sub_corr = corr_d sub-matrix for these components, PSD-projected
            sample 20,000 joint draws via Cholesky(sub_corr) + norm.cdf + inv_pmf
        else:
            sample 20,000 independent draws per component via inv_pmf
        sum component samples -> integer combo totals
        histogram over [0, sum(component_max)] -> normalized PMF
        combo_outcome = sum of component ACTUAL outcomes

The held-out actual is NEVER used to shape the PMF — only to fill the
`outcome` column for downstream calibration.

Output:
    data/oof_combo_pmfs.parquet
    data/oof_combo_pmfs.manifest.json

This dataset is the foundation for M6 combo role-aware calibrator
fitting. M5C does NOT promote combos to production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

logger = logging.getLogger(__name__)

# Lazy scipy import (transitive dep of sklearn 1.4.2 which is pinned).
try:
    from scipy.special import ndtr as _scipy_norm_cdf

    def _norm_cdf(z: np.ndarray) -> np.ndarray:
        return _scipy_norm_cdf(z)
except ImportError:  # pragma: no cover
    from math import erf as _math_erf

    def _norm_cdf(z: np.ndarray) -> np.ndarray:
        z_arr = np.asarray(z, dtype=np.float64)
        flat_in = z_arr.ravel()
        flat_out = np.empty_like(flat_in)
        inv_sqrt2 = 1.0 / np.sqrt(2.0)
        for i, v in enumerate(flat_in):
            flat_out[i] = 0.5 * (1.0 + _math_erf(float(v) * inv_sqrt2))
        return flat_out.reshape(z_arr.shape)


# ── Constants ────────────────────────────────────────────────────────────

COMBO_PMF_VERSION = "combo_oof_pmf_v1"
SOURCE_OOF_PATH = "data/oof_pmfs.parquet"

# Staleness flagging (M5C-amend Phase 2)
STALENESS_WARN_DAYS = 7
DATASET_STATUS_STALE = "path_building_stale_oof_v1"
DATASET_STATUS_FRESH = "fresh_oof_v1"
CALIBRATION_STATUS_PENDING_M6 = "pending_m6_stat_role_calibration"

# Mission-required combos (canonical -> (mission_alias, components))
COMBO_DEFS: dict[str, tuple[str, tuple[str, ...]]] = {
    "stocks": ("stl_blk",     ("stl", "blk")),
    "pa":     ("pts_ast",     ("pts", "ast")),
    "pr":     ("pts_reb",     ("pts", "reb")),
    "pra":    ("pts_reb_ast", ("pts", "reb", "ast")),
}

BASE_COMPONENT_STATS: tuple[str, ...] = ("pts", "reb", "ast", "stl", "blk")

DEFAULT_N_DRAWS = 20_000
DEFAULT_MIN_PRIOR_ROWS = 200

METHOD_COPULA = "prior_actual_corr_gaussian_copula_v1"
METHOD_COLD_START = "independence_cold_start_v1"


# ── Sampling primitives ──────────────────────────────────────────────────

def _psd_project(mat: np.ndarray) -> np.ndarray:
    """Symmetrize and clip eigenvalues at small epsilon to ensure PSD."""
    sym = 0.5 * (mat + mat.T)
    w, V = np.linalg.eigh(sym)
    w = np.clip(w, 1e-9, None)
    return V @ np.diag(w) @ V.T


def _inverse_pmf_cdf(pmf: np.ndarray, u: np.ndarray) -> np.ndarray:
    """For each u in [0, 1], return smallest k such that cumsum(pmf)[k] >= u."""
    cdf = np.cumsum(pmf)
    cdf = np.minimum(cdf, 1.0)
    if len(cdf) > 0:
        cdf[-1] = 1.0
    idx = np.searchsorted(cdf, u, side="left")
    idx = np.clip(idx, 0, max(len(pmf) - 1, 0))
    return idx.astype(np.int64)


def _sample_via_copula(
    component_pmfs: list[np.ndarray],
    correlation: np.ndarray,
    rng: np.random.Generator,
    n_draws: int,
) -> np.ndarray:
    """Sample joint component outcomes via Gaussian copula. Returns (n_draws, k) ints."""
    k = len(component_pmfs)
    L = np.linalg.cholesky(correlation + 1e-9 * np.eye(k))
    z = rng.standard_normal(size=(n_draws, k)) @ L.T
    u = _norm_cdf(z)
    u = np.clip(u, 1e-12, 1.0 - 1e-12)
    samples = np.zeros((n_draws, k), dtype=np.int64)
    for j, pmf in enumerate(component_pmfs):
        samples[:, j] = _inverse_pmf_cdf(pmf, u[:, j])
    return samples


def _sample_via_independence(
    component_pmfs: list[np.ndarray],
    rng: np.random.Generator,
    n_draws: int,
) -> np.ndarray:
    """Sample independent component outcomes. Returns (n_draws, k) ints."""
    k = len(component_pmfs)
    samples = np.zeros((n_draws, k), dtype=np.int64)
    for j, pmf in enumerate(component_pmfs):
        u = rng.random(size=n_draws)
        samples[:, j] = _inverse_pmf_cdf(pmf, u)
    return samples


def _empirical_pmf(samples_total: np.ndarray, support_max: int) -> np.ndarray:
    """Histogram integer combo totals into a normalized PMF over [0, support_max]."""
    samples_total = np.clip(samples_total, 0, support_max).astype(np.int64)
    counts = np.bincount(samples_total, minlength=support_max + 1).astype(np.float64)
    if len(counts) > support_max + 1:
        counts = counts[: support_max + 1]
    total = counts.sum()
    if total <= 0:
        pmf = np.zeros(support_max + 1, dtype=np.float64)
        pmf[0] = 1.0
        return pmf
    return counts / total


def _deterministic_seed(game_date: str, player_id: int, game_id: int, combo: str) -> int:
    """Stable 64-bit seed from row identifiers."""
    s = f"{game_date}|{int(player_id)}|{int(game_id)}|{combo}|combo_oof_v1"
    h = hashlib.sha256(s.encode()).digest()
    return int.from_bytes(h[:8], "big")


def _derive_combo_pmf(
    component_pmfs: list[np.ndarray],
    correlation: np.ndarray | None,
    seed: int,
    n_draws: int,
) -> tuple[np.ndarray, int, str, int]:
    """Return (pmf, support_max, method, n_draws_used)."""
    support_max = int(sum(len(p) - 1 for p in component_pmfs))
    rng = np.random.default_rng(seed)
    if correlation is not None:
        samples = _sample_via_copula(component_pmfs, correlation, rng, n_draws)
        method = METHOD_COPULA
    else:
        samples = _sample_via_independence(component_pmfs, rng, n_draws)
        method = METHOD_COLD_START
    totals = samples.sum(axis=1)
    pmf = _empirical_pmf(totals, support_max)
    return pmf, support_max, method, n_draws


# ── CLI / driver ─────────────────────────────────────────────────────────

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate combo OOF PMFs from base OOF (NBA Props Model M5C).",
    )
    p.add_argument(
        "--in", dest="in_path", default=str(REPO_ROOT / SOURCE_OOF_PATH),
        help=f"Source base-OOF parquet (default: {SOURCE_OOF_PATH})",
    )
    p.add_argument(
        "--out", default=str(REPO_ROOT / "data" / "oof_combo_pmfs.parquet"),
        help="Output parquet path (default: data/oof_combo_pmfs.parquet)",
    )
    p.add_argument(
        "--manifest", default=str(REPO_ROOT / "data" / "oof_combo_pmfs.manifest.json"),
        help="Manifest path (default: data/oof_combo_pmfs.manifest.json)",
    )
    p.add_argument(
        "--as-of-date", default=None,
        help="As-of date (YYYY-MM-DD) for staleness gap calc. Default: today UTC.",
    )
    p.add_argument(
        "--n-draws", type=int, default=DEFAULT_N_DRAWS,
        help=f"Joint samples per (player, game, combo) (default: {DEFAULT_N_DRAWS})",
    )
    p.add_argument(
        "--min-prior-rows", type=int, default=DEFAULT_MIN_PRIOR_ROWS,
        help=f"Minimum prior player-games for copula method (default: {DEFAULT_MIN_PRIOR_ROWS})",
    )
    p.add_argument(
        "--limit", type=int, default=None,
        help="Process only first N (player, game) records (debug only)",
    )
    p.add_argument(
        "--self-test", action="store_true",
        help="Run synthetic smoke test only (no I/O against real OOF).",
    )
    return p


def _self_test() -> int:
    print("=== M5C SELF-TEST ===")
    pmf_pts = np.zeros(81); pmf_pts[15:30] = 1; pmf_pts /= pmf_pts.sum()
    pmf_reb = np.zeros(31); pmf_reb[3:10] = 1; pmf_reb /= pmf_reb.sum()
    pmf_ast = np.zeros(26); pmf_ast[2:8] = 1; pmf_ast /= pmf_ast.sum()
    pmf_stl = np.zeros(11); pmf_stl[0:4] = 1; pmf_stl /= pmf_stl.sum()
    pmf_blk = np.zeros(11); pmf_blk[0:3] = 1; pmf_blk /= pmf_blk.sum()

    corr3 = np.array([[1.0, 0.3, 0.2], [0.3, 1.0, 0.1], [0.2, 0.1, 1.0]])
    pmf_pra, smax, method, n = _derive_combo_pmf([pmf_pts, pmf_reb, pmf_ast], corr3, 42, n_draws=20_000)
    assert abs(pmf_pra.sum() - 1.0) < 1e-6, f"copula sum {pmf_pra.sum()} not ~1"
    assert (pmf_pra >= 0).all(), "negative in copula PMF"
    assert np.isfinite(pmf_pra).all(), "non-finite in copula PMF"
    print(f"  pra (copula): support_max={smax} sum={pmf_pra.sum():.10f} method={method} n={n}")

    pmf_stocks, smax2, method2, _ = _derive_combo_pmf([pmf_stl, pmf_blk], None, 7, n_draws=20_000)
    assert abs(pmf_stocks.sum() - 1.0) < 1e-6
    assert method2 == METHOD_COLD_START
    print(f"  stocks (cold-start): support_max={smax2} sum={pmf_stocks.sum():.10f} method={method2}")

    pmf_a, _, _, _ = _derive_combo_pmf([pmf_pts, pmf_reb], None, 999, n_draws=10_000)
    pmf_b, _, _, _ = _derive_combo_pmf([pmf_pts, pmf_reb], None, 999, n_draws=10_000)
    assert np.allclose(pmf_a, pmf_b), "seed determinism broken"
    print("  determinism: PASS")

    seed = _deterministic_seed("2026-01-01", 1234, 567890, "pra")
    print(f"  seed determinism: sha256-derived seed = {seed}")
    print("M5C_SELF_TEST_PASS")
    return 0


def _format_pmf_json(pmf: np.ndarray) -> str:
    return json.dumps({str(i): float(p) for i, p in enumerate(pmf) if p > 0.0})


def _date_str(v) -> str:
    return str(v)[:10]


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = _build_argparser().parse_args()

    if args.self_test:
        return _self_test()

    in_path = Path(args.in_path)
    out_path = Path(args.out)
    manifest_path = Path(args.manifest)

    if not in_path.exists():
        print(f"ABORT: source OOF not found: {in_path}", file=sys.stderr)
        return 2

    print(f"  source: {in_path}")
    oof = pd.read_parquet(in_path)
    print(f"  source rows: {len(oof):,}")

    required_cols = {"stat", "player_id", "game_id", "game_date", "outcome", "pmf", "role_bucket"}
    missing = required_cols - set(oof.columns)
    if missing:
        print(f"ABORT: source OOF missing required columns: {missing}", file=sys.stderr)
        return 3

    oof_base = oof[oof["stat"].astype(str).isin(BASE_COMPONENT_STATS)].copy()
    print(f"  base-component rows: {len(oof_base):,}")
    print(f"  base stats present: {sorted(oof_base['stat'].astype(str).unique())}")

    print("  building per-player-game record dict...")
    records: dict[tuple[int, int], dict] = {}
    for (pid, gid), grp in oof_base.groupby(["player_id", "game_id"], sort=False):
        rec = {
            "game_date": _date_str(grp["game_date"].iloc[0]),
            "role_bucket": str(grp["role_bucket"].iloc[0]) if grp["role_bucket"].iloc[0] is not None else "unknown",
            "pmf": {},
            "outcome": {},
        }
        for _, r in grp.iterrows():
            s = str(r["stat"])
            rec["pmf"][s] = np.asarray(r["pmf"], dtype=np.float64)
            rec["outcome"][s] = int(r["outcome"])
        if set(rec["pmf"].keys()) >= set(BASE_COMPONENT_STATS):
            records[(int(pid), int(gid))] = rec

    print(f"  player-game records (with all 5 base stats): {len(records):,}")

    if args.limit is not None and args.limit > 0:
        keys = list(records.keys())[: args.limit]
        records = {k: records[k] for k in keys}
        print(f"  --limit applied: processing {len(records):,} records")

    print("  computing per-date prior correlation matrices...")
    keys_by_date: dict[str, list[tuple[int, int]]] = {}
    for k, rec in records.items():
        keys_by_date.setdefault(rec["game_date"], []).append(k)
    unique_dates = sorted(keys_by_date.keys())
    print(f"  unique game_dates: {len(unique_dates)} (range {unique_dates[0]} -> {unique_dates[-1]})")

    # Staleness flagging (M5C-amend Phase 2)
    from datetime import date as _date_cls
    oof_window_start = str(unique_dates[0])
    oof_window_end = str(unique_dates[-1])
    training_cutoff_date = oof_window_end
    if args.as_of_date:
        as_of_date_obj = _date_cls.fromisoformat(args.as_of_date)
    else:
        as_of_date_obj = datetime.now(timezone.utc).date()
    as_of_date_str = as_of_date_obj.isoformat()
    _end_d = _date_cls.fromisoformat(oof_window_end)
    days_since_oof_window_end = (as_of_date_obj - _end_d).days
    if days_since_oof_window_end > STALENESS_WARN_DAYS:
        dataset_status = DATASET_STATUS_STALE
        path_building_warning = (
            f"Source OOF window ends {oof_window_end}; as-of date {as_of_date_str} "
            f"is {days_since_oof_window_end} days later (>{STALENESS_WARN_DAYS}-day threshold). "
            f"Combo OOF rows are derived from stale base OOF and MUST NOT be used for "
            f"production-elite calibrator fitting until base OOF is refreshed."
        )
    else:
        dataset_status = DATASET_STATUS_FRESH
        path_building_warning = ""
    production_promoted = False
    final_calibration_ready = False
    print(f"  staleness: dataset_status={dataset_status} "
          f"oof_window={oof_window_start}..{oof_window_end} "
          f"as_of={as_of_date_str} days_since_end={days_since_oof_window_end}")

    record_outcomes = {
        k: np.array([rec["outcome"][s] for s in BASE_COMPONENT_STATS], dtype=np.float64)
        for k, rec in records.items()
    }

    correlation_by_date: dict[str, np.ndarray | None] = {}
    n_copula_dates = 0
    n_cold_start_dates = 0
    for d in unique_dates:
        prior_keys: list[tuple[int, int]] = []
        for prior_d, ks in keys_by_date.items():
            if prior_d < d:
                prior_keys.extend(ks)
        if len(prior_keys) >= args.min_prior_rows:
            outcomes_arr = np.stack([record_outcomes[k] for k in prior_keys], axis=0)
            corr = np.corrcoef(outcomes_arr, rowvar=False)
            corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
            np.fill_diagonal(corr, 1.0)
            correlation_by_date[d] = corr
            n_copula_dates += 1
        else:
            correlation_by_date[d] = None
            n_cold_start_dates += 1
    print(f"  dates with copula: {n_copula_dates}; cold-start dates: {n_cold_start_dates}")

    print(f"  generating combo OOF rows: {len(records):,} player-games x {len(COMBO_DEFS)} combos...")
    out_rows: list[dict] = []
    n_processed = 0
    n_total = len(records)
    for (pid, gid), rec in records.items():
        d = rec["game_date"]
        date_corr = correlation_by_date[d]
        for canonical, (mission, components) in COMBO_DEFS.items():
            comp_pmfs = [rec["pmf"][c] for c in components]
            comp_outcomes = [rec["outcome"][c] for c in components]
            combo_outcome = int(sum(comp_outcomes))

            seed = _deterministic_seed(d, pid, gid, canonical)

            if date_corr is not None:
                comp_indices = [BASE_COMPONENT_STATS.index(c) for c in components]
                sub_corr = date_corr[np.ix_(comp_indices, comp_indices)]
                sub_corr = _psd_project(sub_corr)
                np.fill_diagonal(sub_corr, 1.0)
                pmf, support_max, method, n_draws_used = _derive_combo_pmf(
                    comp_pmfs, sub_corr, seed, n_draws=args.n_draws,
                )
            else:
                pmf, support_max, method, n_draws_used = _derive_combo_pmf(
                    comp_pmfs, None, seed, n_draws=args.n_draws,
                )

            pmf_sum_error = float(abs(pmf.sum() - 1.0))
            pmf_valid = bool(
                pmf_sum_error < 1e-6
                and bool(np.isfinite(pmf).all())
                and bool((pmf >= 0.0).all())
            )

            out_rows.append({
                "game_date": d,
                "game_id": int(gid),
                "player_id": int(pid),
                "role_bucket": rec["role_bucket"],
                "stat": canonical,
                "mission_stat": mission,
                "components": list(components),
                "outcome": combo_outcome,
                "pmf": pmf.astype(np.float64),
                "pmf_json": _format_pmf_json(pmf),
                "support_min": 0,
                "support_max": int(support_max),
                "pmf_sum_error": pmf_sum_error,
                "pmf_valid": pmf_valid,
                "n_draws": int(n_draws_used),
                "combo_oof_method": method,
                "combo_pmf_version": COMBO_PMF_VERSION,
                "dataset_status": dataset_status,
                "oof_window_start": oof_window_start,
                "oof_window_end": oof_window_end,
                "training_cutoff_date": training_cutoff_date,
                "days_since_oof_window_end": days_since_oof_window_end,
                "path_building_warning": path_building_warning,
                "production_promoted": production_promoted,
                "final_calibration_ready": final_calibration_ready,
                "calibrated": False,
                "calibration_status": CALIBRATION_STATUS_PENDING_M6,
                "source_oof_path": SOURCE_OOF_PATH,
            })
        n_processed += 1
        if n_processed % 1000 == 0 or n_processed == n_total:
            print(f"    processed {n_processed:,}/{n_total:,} player-games")

    print(f"  total output rows: {len(out_rows):,}")

    out_df = pd.DataFrame(out_rows)
    out_df["pmf"] = out_df["pmf"].apply(lambda a: a.tolist() if hasattr(a, "tolist") else list(a))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(out_path, index=False)
    print(f"  wrote: {out_path}  ({out_path.stat().st_size:,} bytes)")

    method_counts = out_df["combo_oof_method"].value_counts().to_dict()
    pmf_validity_rate = float(out_df["pmf_valid"].mean())
    pmf_sum_error_max = float(out_df["pmf_sum_error"].max())

    manifest = {
        "schema_version": "1.0",
        "input": str(in_path),
        "output": str(out_path),
        "source_oof_path": SOURCE_OOF_PATH,
        "rows": len(out_rows),
        "player_games": len(records),
        "combos_canonical": list(COMBO_DEFS.keys()),
        "combos_mission": [v[0] for v in COMBO_DEFS.values()],
        "combo_pmf_version": COMBO_PMF_VERSION,
        "dataset_status": dataset_status,
        "oof_window_start": oof_window_start,
        "oof_window_end": oof_window_end,
        "training_cutoff_date": training_cutoff_date,
        "as_of_date": as_of_date_str,
        "days_since_oof_window_end": days_since_oof_window_end,
        "path_building_warning": path_building_warning,
        "production_promoted": production_promoted,
        "final_calibration_ready": final_calibration_ready,
        "staleness_warn_days": STALENESS_WARN_DAYS,
        "method_counts": {str(k): int(v) for k, v in method_counts.items()},
        "n_draws_default": int(args.n_draws),
        "min_prior_rows_for_copula": int(args.min_prior_rows),
        "n_copula_dates": int(n_copula_dates),
        "n_cold_start_dates": int(n_cold_start_dates),
        "calibrated": False,
        "calibration_status": CALIBRATION_STATUS_PENDING_M6,
        "pmf_validity_rate": pmf_validity_rate,
        "pmf_sum_error_max": pmf_sum_error_max,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": (
            "M5C foundation. Combo OOF dataset for downstream M6 role-aware "
            "calibrator fitting. Combo rows are calibrated=False / "
            "calibration_status=pending_m6_stat_role_calibration. NOT yet "
            "wired into production delivery; M7+ handles production wiring."
        ),
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  wrote manifest: {manifest_path}")

    print("BUILD_COMBO_OOF_PMFS_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
