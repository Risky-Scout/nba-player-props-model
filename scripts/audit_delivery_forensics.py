#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

HARD_CODES = {
    "pmf_parse_failed",
    "pmf_sum_not_1",
    "pmf_negative_prob",
    "pmf_nonfinite_prob",
    "reported_over_mismatch_pmf",
    "reported_mean_mismatch",
    "reported_variance_mismatch",
    "over_under_no_push_not_sum_1",
    "duplicate_key_rows",
    "multiple_non_identical_model_only_candidates",
    "canonical_source_missing_while_alternative_exists",
    "join_status_not_ok",
    "excluded_scoring_blocker_without_reporting",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _safe_read_parquet(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_parquet(path)
    except Exception:
        return pd.DataFrame()


def _latest_delivery_date() -> str:
    candidates = []
    deliveries = REPO_ROOT / "deliveries"
    for p in deliveries.glob("*/wizard_of_odds/full_pmfs_wide.parquet"):
        try:
            candidates.append(p.parent.parent.name)
        except Exception:
            continue
    if not candidates:
        raise SystemExit("FATAL: no delivery dates with wizard_of_odds/full_pmfs_wide.parquet")
    return sorted(candidates)[-1]


def _parse_pmf_json(value: object) -> tuple[dict[int, float] | None, str | None]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None, "pmf_parse_failed"
    try:
        raw = json.loads(str(value))
        if not isinstance(raw, dict):
            return None, "pmf_parse_failed"
        out = {}
        for k, v in raw.items():
            out[int(k)] = float(v)
        return out, None
    except Exception:
        return None, "pmf_parse_failed"


def _pmf_stats(pmf: dict[int, float]) -> tuple[float, float, bool, bool]:
    ks = np.array(sorted(pmf.keys()), dtype=float)
    ps = np.array([pmf[int(k)] for k in ks], dtype=float)
    s = float(ps.sum())
    mean = float((ks * ps).sum())
    var = float((((ks - mean) ** 2) * ps).sum())
    has_negative = bool((ps < 0).any())
    nonfinite = bool((~np.isfinite(ps)).any())
    return s, mean, var, has_negative or nonfinite


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="Delivery date (YYYY-MM-DD). Defaults to latest available.")
    ap.add_argument(
        "--out-root",
        default="artifacts/delivery_forensics",
        help="Root directory for forensics output folders.",
    )
    args = ap.parse_args()

    date = args.date or _latest_delivery_date()
    out_dir = REPO_ROOT / args.out_root / _now_utc()
    out_dir.mkdir(parents=True, exist_ok=True)

    base = REPO_ROOT / "deliveries" / date
    canonical_path = base / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    alt_path = base / "pmf_model_review_package" / "machine_readable" / "model_only.parquet"
    wide_path = base / "wizard_of_odds" / "full_pmfs_wide.parquet"
    run_manifest_path = base / "wizard_of_odds" / "run_manifest.json"
    mc_path = base / "wizard_of_odds" / "market_comparison.parquet"
    lossrow_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{date}.parquet"

    canonical_df = _safe_read_parquet(canonical_path)
    alt_df = _safe_read_parquet(alt_path)
    wide_df = _safe_read_parquet(wide_path)
    mc_df = _safe_read_parquet(mc_path)
    loss_df = _safe_read_parquet(lossrow_path)

    # 1) inventory
    inv_rows: list[dict] = []
    for p in sorted(base.glob("**/*")):
        if p.is_dir():
            continue
        rel = p.relative_to(REPO_ROOT)
        row = {
            "date": date,
            "path": str(rel),
            "exists": True,
            "size_bytes": p.stat().st_size,
            "row_count": None,
            "file_type": p.suffix.lower(),
        }
        if p.suffix.lower() == ".parquet":
            try:
                row["row_count"] = int(len(pd.read_parquet(p, columns=[])))
            except Exception:
                row["row_count"] = None
        inv_rows.append(row)
    inventory_df = pd.DataFrame(inv_rows)
    inventory_df.to_csv(out_dir / "delivery_inventory.csv", index=False)

    # 2) schema report
    required = {
        "canonical_source": (canonical_df, ["player_id", "stat", "line", "game_id"]),
        "model_only_alternative": (alt_df, ["player_id", "stat", "line", "game_id", "pmf_json", "model_p_over"]),
        "full_pmfs_wide": (wide_df, ["player_id", "stat", "line", "game_id", "pmf_json", "model_p_over"]),
    }
    schema_rows = []
    for name, (df, cols) in required.items():
        for col in cols:
            schema_rows.append(
                {
                    "dataset": name,
                    "column": col,
                    "present": col in df.columns,
                    "null_count": int(df[col].isna().sum()) if col in df.columns else None,
                    "row_count": int(len(df)),
                }
            )
    schema_df = pd.DataFrame(schema_rows)
    schema_df.to_csv(out_dir / "delivery_schema_report.csv", index=False)

    # 3) PMF integrity + 4) probability consistency
    pmf_rows = []
    prob_rows = []
    for dataset_name, df in [("model_only_alternative", alt_df), ("full_pmfs_wide", wide_df)]:
        if df.empty or "pmf_json" not in df.columns:
            continue
        for row in df.itertuples(index=False):
            key = {
                "dataset": dataset_name,
                "player_id": getattr(row, "player_id", None),
                "stat": getattr(row, "stat", None),
                "line": getattr(row, "line", None),
                "game_id": getattr(row, "game_id", None),
            }
            pmf, err = _parse_pmf_json(getattr(row, "pmf_json", None))
            if err is not None:
                pmf_rows.append({**key, "error_code": err, "severity": "hard", "detail": "pmf_json parse failed"})
                continue
            s, mean, var, nonfinite_or_neg = _pmf_stats(pmf)
            if nonfinite_or_neg:
                ps = np.array(list(pmf.values()), dtype=float)
                if (~np.isfinite(ps)).any():
                    pmf_rows.append({**key, "error_code": "pmf_nonfinite_prob", "severity": "hard", "detail": "pmf has non-finite probabilities"})
                if (ps < 0).any():
                    pmf_rows.append({**key, "error_code": "pmf_negative_prob", "severity": "hard", "detail": "pmf has negative probabilities"})
            if abs(s - 1.0) > 1e-6:
                pmf_rows.append({**key, "error_code": "pmf_sum_not_1", "severity": "hard", "detail": f"pmf_sum={s:.8f}"})

            # reported value checks when columns exist
            model_p_over = getattr(row, "model_p_over", None)
            line = getattr(row, "line", None)
            if model_p_over is not None and line is not None and not (isinstance(line, float) and np.isnan(line)):
                line_f = float(line)
                p_over_raw = sum(v for k, v in pmf.items() if k > line_f)
                p_under_raw = sum(v for k, v in pmf.items() if k < line_f)
                denom = p_over_raw + p_under_raw
                p_over = (p_over_raw / denom) if denom > 0 else 0.5
                if abs(float(model_p_over) - p_over) > 5e-3:
                    prob_rows.append(
                        {
                            **key,
                            "error_code": "reported_over_mismatch_pmf",
                            "severity": "hard",
                            "reported_value": float(model_p_over),
                            "derived_value": float(p_over),
                            "delta": abs(float(model_p_over) - float(p_over)),
                        }
                    )
            model_p_under = getattr(row, "model_p_under", None)
            if model_p_over is not None and model_p_under is not None:
                s_ou = float(model_p_over) + float(model_p_under)
                if abs(s_ou - 1.0) > 1e-3:
                    prob_rows.append(
                        {
                            **key,
                            "error_code": "over_under_no_push_not_sum_1",
                            "severity": "hard",
                            "reported_value": s_ou,
                            "derived_value": 1.0,
                            "delta": abs(s_ou - 1.0),
                        }
                    )
            if hasattr(row, "mean"):
                rep_mean = getattr(row, "mean", None)
                if rep_mean is not None and not (isinstance(rep_mean, float) and np.isnan(rep_mean)):
                    if abs(float(rep_mean) - mean) > 1e-3:
                        prob_rows.append(
                            {
                                **key,
                                "error_code": "reported_mean_mismatch",
                                "severity": "hard",
                                "reported_value": float(rep_mean),
                                "derived_value": float(mean),
                                "delta": abs(float(rep_mean) - float(mean)),
                            }
                        )
            if hasattr(row, "variance"):
                rep_var = getattr(row, "variance", None)
                if rep_var is not None and not (isinstance(rep_var, float) and np.isnan(rep_var)):
                    if abs(float(rep_var) - var) > 1e-3:
                        prob_rows.append(
                            {
                                **key,
                                "error_code": "reported_variance_mismatch",
                                "severity": "hard",
                                "reported_value": float(rep_var),
                                "derived_value": float(var),
                                "delta": abs(float(rep_var) - float(var)),
                            }
                        )
    pmf_df = pd.DataFrame(pmf_rows)
    prob_df = pd.DataFrame(prob_rows)
    pmf_df.to_csv(out_dir / "delivery_pmf_integrity_report.csv", index=False)
    prob_df.to_csv(out_dir / "delivery_probability_consistency_report.csv", index=False)

    # 5) duplicate keys
    dup_rows = []
    for dataset_name, df, key_cols in [
        ("canonical_source", canonical_df, ["player_id", "stat", "line", "game_id"]),
        ("model_only_alternative", alt_df, ["player_id", "stat", "line", "game_id"]),
        ("full_pmfs_wide", wide_df, ["player_id", "stat", "line", "game_id", "book"]),
    ]:
        keep = [c for c in key_cols if c in df.columns]
        if not keep or df.empty:
            continue
        dups = df.duplicated(subset=keep, keep=False)
        if bool(dups.any()):
            dup_rows.append(
                {
                    "dataset": dataset_name,
                    "error_code": "duplicate_key_rows",
                    "severity": "hard",
                    "key_columns": ",".join(keep),
                    "duplicate_row_count": int(dups.sum()),
                }
            )
    dup_df = pd.DataFrame(dup_rows)
    dup_df.to_csv(out_dir / "delivery_duplicate_key_report.csv", index=False)

    # 6) canonical vs alternative
    compare_rows = []
    if canonical_df.empty and not alt_df.empty:
        compare_rows.append(
            {
                "error_code": "canonical_source_missing_while_alternative_exists",
                "severity": "hard",
                "detail": "canonical_source MODEL_ONLY parquet missing while alternative exists",
            }
        )
    elif not canonical_df.empty and not alt_df.empty:
        key_cols = [c for c in ("player_id", "stat", "line", "game_id") if c in canonical_df.columns and c in alt_df.columns]
        if key_cols:
            ckeys = set(map(tuple, canonical_df[key_cols].astype(str).itertuples(index=False, name=None)))
            akeys = set(map(tuple, alt_df[key_cols].astype(str).itertuples(index=False, name=None)))
            compare_rows.append(
                {
                    "error_code": "key_overlap",
                    "severity": "info",
                    "detail": f"canonical_keys={len(ckeys)} alternative_keys={len(akeys)} overlap={len(ckeys & akeys)}",
                }
            )
            shared_cols = [c for c in canonical_df.columns if c in alt_df.columns and c not in key_cols]
            if shared_cols:
                c_cmp = canonical_df[key_cols + shared_cols].astype(str).sort_values(key_cols).reset_index(drop=True)
                a_cmp = alt_df[key_cols + shared_cols].astype(str).sort_values(key_cols).reset_index(drop=True)
                merged = c_cmp.merge(a_cmp, on=key_cols, how="inner", suffixes=("_c", "_a"))
                mismatch_count = 0
                for col in shared_cols:
                    mismatch_count += int((merged[f"{col}_c"] != merged[f"{col}_a"]).sum())
                if mismatch_count > 0:
                    compare_rows.append(
                        {
                            "error_code": "multiple_non_identical_model_only_candidates",
                            "severity": "hard",
                            "detail": f"shared_column_mismatch_cells={mismatch_count}",
                        }
                    )
    compare_df = pd.DataFrame(compare_rows)
    compare_df.to_csv(out_dir / "delivery_canonical_vs_alternative_report.csv", index=False)

    # 7) lossrow join
    join_rows = []
    if mc_df.empty or loss_df.empty:
        join_rows.append(
            {
                "join_status": "missing_source",
                "error_code": "join_status_not_ok",
                "severity": "hard",
                "detail": "market_comparison or event_market_loss_rows file missing/empty",
            }
        )
    else:
        key_cols = [c for c in ("player_name", "stat") if c in mc_df.columns and c in loss_df.columns]
        if len(key_cols) < 2:
            join_rows.append(
                {
                    "join_status": "invalid_keys",
                    "error_code": "join_status_not_ok",
                    "severity": "hard",
                    "detail": "insufficient join key overlap between model_only and loss_rows",
                }
            )
        else:
            a = mc_df[key_cols].drop_duplicates()
            l = loss_df[key_cols].drop_duplicates()
            for c in key_cols:
                if c == "player_name":
                    a[c] = a[c].astype(str).str.lower().str.strip()
                    l[c] = l[c].astype(str).str.lower().str.strip()
                else:
                    a[c] = a[c].astype(str)
                    l[c] = l[c].astype(str)
            m = a.merge(l, on=key_cols, how="left", indicator=True)
            ok = int((m["_merge"] == "both").sum())
            miss = int((m["_merge"] != "both").sum())
            join_rows.append({"join_status": "ok", "error_code": "", "severity": "info", "detail": f"ok_rows={ok}"})
            if miss > 0:
                join_rows.append(
                    {
                        "join_status": "missing_loss_rows",
                        "error_code": "join_status_not_ok",
                        "severity": "hard",
                        "detail": f"rows_without_loss_join={miss}",
                    }
                )
    join_df = pd.DataFrame(join_rows)
    join_df.to_csv(out_dir / "delivery_lossrow_join_report.csv", index=False)

    # 8) scoring_blocker check
    if "scoring_blocker" in mc_df.columns:
        blocked = mc_df["scoring_blocker"].astype(str).str.strip() != ""
        if bool(blocked.any()) and "delivery_status" in mc_df.columns:
            excluded = blocked & mc_df["delivery_status"].astype(str).str.contains("excluded", case=False, na=False)
            if bool(excluded.any()):
                prob_df = pd.concat(
                    [
                        prob_df,
                        pd.DataFrame(
                            [
                                {
                                    "dataset": "market_comparison",
                                    "player_id": None,
                                    "stat": None,
                                    "line": None,
                                    "game_id": None,
                                    "error_code": "excluded_scoring_blocker_without_reporting",
                                    "severity": "hard",
                                    "reported_value": int(excluded.sum()),
                                    "derived_value": None,
                                    "delta": None,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )
                prob_df.to_csv(out_dir / "delivery_probability_consistency_report.csv", index=False)

    # 9) error examples + summary
    all_errors = []
    for df in (pmf_df, prob_df, dup_df, compare_df, join_df):
        if df.empty:
            continue
        cols = [c for c in ("dataset", "player_id", "stat", "line", "game_id", "error_code", "severity", "detail", "delta") if c in df.columns]
        all_errors.append(df.loc[:, cols])
    errors_df = pd.concat(all_errors, ignore_index=True) if all_errors else pd.DataFrame(columns=["error_code", "severity", "detail"])
    hard_mask = errors_df["error_code"].isin(HARD_CODES) if "error_code" in errors_df.columns else pd.Series(dtype=bool)
    hard_failures = int(hard_mask.sum()) if len(errors_df) else 0
    errors_df.head(500).to_csv(out_dir / "delivery_error_examples.csv", index=False)

    summary_lines = [
        f"# Delivery Forensics ({date})",
        "",
        f"- output_dir: `{out_dir.relative_to(REPO_ROOT)}`",
        f"- hard_failure_count: `{hard_failures}`",
        f"- pmf_integrity_issues: `{len(pmf_df)}`",
        f"- probability_consistency_issues: `{len(prob_df)}`",
        f"- duplicate_key_issues: `{len(dup_df)}`",
        f"- canonical_vs_alternative_issues: `{len(compare_df)}`",
        f"- lossrow_join_issues: `{len(join_df[join_df.get('error_code', '') == 'join_status_not_ok']) if not join_df.empty and 'error_code' in join_df.columns else 0}`",
        "",
        "## Hard blocker result",
        f"- {'PASS' if hard_failures == 0 else 'FAIL'}",
    ]
    (out_dir / "delivery_forensics_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(
        "DELIVERY_FORENSICS_PASS"
        if hard_failures == 0
        else f"DELIVERY_FORENSICS_FAIL hard_failure_count={hard_failures}"
    )
    print(f"DELIVERY_FORENSICS_OUTPUT_DIR {out_dir}")
    return 0 if hard_failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

