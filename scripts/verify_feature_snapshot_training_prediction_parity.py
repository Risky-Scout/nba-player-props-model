#!/usr/bin/env python3
"""Verify feature parity between training, prediction, diagnostics, and delivery."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REQUIRED_DIAGNOSTIC_COLUMNS = [
    "injury_status_current",
    "official_lineup_status",
    "expected_lineup_status",
    "projected_minutes",
    "minutes_q10",
    "minutes_q50",
    "minutes_q90",
    "p_starter",
    "p_inactive",
    "usage_projection",
    "opponent_def_rating_recent",
    "expected_steal_opportunities",
    "cov_pts_reb_player",
]

REQUIRED_DEREK_COLUMNS = [
    "expected_lineup_status",
    "official_lineup_status",
    "projected_minutes",
    "minutes_q10",
    "minutes_q50",
    "minutes_q90",
    "role_bucket",
    "hard_role_bucket",
    "role_entropy",
]

LEAKAGE_BLOCKED_COLUMNS = {
    "market_prob_over",
    "no_vig_market_prob_over",
    "market_fair_over_prob",
}
DEFAULT_KEY_COLUMNS = ("game_date", "player_id", "stat")
TIMESTAMP_COLUMNS = ("source_data_asof_utc", "asof_utc", "snapshot_time_utc")


def _load(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_parquet(path)


def _cols(df: pd.DataFrame) -> set[str]:
    return set(map(str, df.columns))


def _normalize_key_frame(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if not keys:
        return pd.DataFrame()
    out = df.loc[:, keys].copy()
    for key in keys:
        if key == "game_date":
            out[key] = pd.to_datetime(out[key], errors="coerce").dt.strftime("%Y-%m-%d")
        else:
            out[key] = out[key].astype(str)
    return out


def _write_debug_outputs(*, debug_dir: Path, diff_rows: list[dict], summary_lines: list[str]) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(diff_rows).to_csv(debug_dir / "latest_parity_diff.csv", index=False)
    (debug_dir / "latest_parity_summary.md").write_text(
        "\n".join(summary_lines).rstrip() + "\n",
        encoding="utf-8",
    )


def _is_unavailable_status(value: object) -> bool:
    text = str(value).strip().lower()
    return text in {
        "unavailable",
        "missing",
        "stale",
        "fallback",
        "unknown",
        "source_missing",
        "not_applicable",
        "n/a",
    }


def _datetime_str(value: object) -> str:
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return ""
    return ts.isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--training-table", required=True)
    ap.add_argument("--prediction-features", required=True)
    ap.add_argument("--event-market-rows", required=False, default=None)
    ap.add_argument("--derek-feed", required=False, default=None)
    ap.add_argument("--out-dir", default="artifacts/model_diagnostics/feature_parity")
    ap.add_argument("--debug-dir", default="artifacts/model_diagnostics/feature_snapshot_parity_debug")
    ap.add_argument(
        "--null-rate-delta-threshold",
        type=float,
        default=0.25,
        help="Absolute null-rate delta threshold for reporting mismatches.",
    )
    args = ap.parse_args()

    train_df = _load(Path(args.training_table))
    pred_df = _load(Path(args.prediction_features))
    event_df = _load(Path(args.event_market_rows)) if args.event_market_rows else pd.DataFrame()
    derek_df = _load(Path(args.derek_feed)) if args.derek_feed else pd.DataFrame()

    tcols = _cols(train_df)
    pcols = _cols(pred_df)
    ecols = _cols(event_df)
    dcols = _cols(derek_df)

    shared_cols = sorted(tcols.intersection(pcols))
    missing_training = sorted(pcols - tcols)
    missing_prediction = sorted(tcols - pcols)
    dtype_mismatches: list[dict] = []
    null_rate_mismatches: list[dict] = []
    diff_rows: list[dict] = []

    for col in shared_cols:
        t_dtype = str(train_df[col].dtype)
        p_dtype = str(pred_df[col].dtype)
        if t_dtype != p_dtype:
            dtype_mismatches.append(
                {
                    "category": "dtype_mismatch",
                    "column": col,
                    "training_value": t_dtype,
                    "prediction_value": p_dtype,
                    "delta": None,
                    "severity": "warn",
                    "notes": "",
                }
            )
        t_null = float(train_df[col].isna().mean())
        p_null = float(pred_df[col].isna().mean())
        if abs(t_null - p_null) >= float(args.null_rate_delta_threshold):
            null_rate_mismatches.append(
                {
                    "category": "null_rate_mismatch",
                    "column": col,
                    "training_value": t_null,
                    "prediction_value": p_null,
                    "delta": abs(t_null - p_null),
                    "severity": "warn",
                    "notes": "",
                }
            )

    for col in missing_training:
        diff_rows.append(
            {
                "category": "missing_training_column",
                "column": col,
                "training_value": None,
                "prediction_value": "present",
                "delta": None,
                "severity": "info",
                "notes": "prediction_only_field_not_used_in_training",
            }
        )
    for col in missing_prediction:
        diff_rows.append(
            {
                "category": "missing_prediction_column",
                "column": col,
                "training_value": "present",
                "prediction_value": None,
                "delta": None,
                "severity": "info",
                "notes": "training_only_field_not_required_for_same_day_snapshot",
            }
        )
    diff_rows.extend(dtype_mismatches)
    diff_rows.extend(null_rate_mismatches)

    key_cols = [c for c in DEFAULT_KEY_COLUMNS if c in tcols and c in pcols]
    train_dup_count = 0
    pred_dup_count = 0
    key_overlap_count = 0
    train_key_only_count = 0
    pred_key_only_count = 0
    if key_cols:
        train_keys_df = _normalize_key_frame(train_df, key_cols)
        pred_keys_df = _normalize_key_frame(pred_df, key_cols)
        train_dup_count = int(train_keys_df.duplicated(subset=key_cols).sum())
        pred_dup_count = int(pred_keys_df.duplicated(subset=key_cols).sum())

        train_keys = set(map(tuple, train_keys_df.itertuples(index=False, name=None)))
        pred_keys = set(map(tuple, pred_keys_df.itertuples(index=False, name=None)))
        key_overlap_count = len(train_keys.intersection(pred_keys))
        train_key_only_count = len(train_keys - pred_keys)
        pred_key_only_count = len(pred_keys - train_keys)

        if train_dup_count:
            diff_rows.append(
                {
                    "category": "duplicate_key_rows",
                    "column": ",".join(key_cols),
                    "training_value": train_dup_count,
                    "prediction_value": 0,
                    "delta": train_dup_count,
                    "severity": "fail",
                    "notes": "training_table_duplicate_keys",
                }
            )
        if pred_dup_count:
            diff_rows.append(
                {
                    "category": "duplicate_key_rows",
                    "column": ",".join(key_cols),
                    "training_value": 0,
                    "prediction_value": pred_dup_count,
                    "delta": pred_dup_count,
                    "severity": "fail",
                    "notes": "prediction_snapshot_duplicate_keys",
                }
            )

        diff_rows.append(
            {
                "category": "key_mismatch",
                "column": ",".join(key_cols),
                "training_value": train_key_only_count,
                "prediction_value": pred_key_only_count,
                "delta": key_overlap_count,
                "severity": "info",
                "notes": "training_only_keys, prediction_only_keys, overlap_keys",
            }
        )

    asof_mismatch_count = 0
    comparable_asof_rows = 0
    asof_cols = [c for c in TIMESTAMP_COLUMNS if c in tcols and c in pcols]
    if key_cols and asof_cols and key_overlap_count:
        train_overlap = _normalize_key_frame(train_df, key_cols).copy()
        pred_overlap = _normalize_key_frame(pred_df, key_cols).copy()
        for col in asof_cols:
            train_overlap[col] = train_df[col].map(_datetime_str)
            pred_overlap[col] = pred_df[col].map(_datetime_str)
        merged = train_overlap.merge(pred_overlap, on=key_cols, how="inner", suffixes=("_t", "_p"))
        comparable_asof_rows = int(len(merged))
        for col in asof_cols:
            diff_mask = merged[f"{col}_t"] != merged[f"{col}_p"]
            mismatches = int(diff_mask.sum())
            asof_mismatch_count += mismatches
            if mismatches:
                diff_rows.append(
                    {
                        "category": "asof_timestamp_mismatch",
                        "column": col,
                        "training_value": mismatches,
                        "prediction_value": comparable_asof_rows,
                        "delta": (mismatches / comparable_asof_rows) if comparable_asof_rows else None,
                        "severity": "fail",
                        "notes": "shared_key_timestamp_differences",
                    }
                )
    else:
        diff_rows.append(
            {
                "category": "asof_timestamp_mismatch",
                "column": ",".join(TIMESTAMP_COLUMNS),
                "training_value": None,
                "prediction_value": None,
                "delta": None,
                "severity": "info",
                "notes": "not_comparable_no_shared_keys_or_missing_timestamp_columns",
            }
        )

    unavailable_training_present: list[dict] = []
    status_cols = [c for c in pcols if c.endswith("_status")]
    for status_col in sorted(status_cols):
        unavailable_rate = float(pred_df[status_col].map(_is_unavailable_status).mean())
        if unavailable_rate <= 0.0:
            continue
        base_col = status_col.removesuffix("_status")
        if base_col in tcols:
            row = {
                "category": "training_feature_unavailable_at_prediction_time",
                "column": base_col,
                "training_value": "present",
                "prediction_value": unavailable_rate,
                "delta": unavailable_rate,
                "severity": "warn",
                "notes": f"status_col={status_col}",
            }
            unavailable_training_present.append(row)
            diff_rows.append(row)

    prediction_only_fields = sorted(pcols - tcols)
    for col in prediction_only_fields:
        diff_rows.append(
            {
                "category": "prediction_only_field_not_used_in_training",
                "column": col,
                "training_value": None,
                "prediction_value": "present",
                "delta": None,
                "severity": "info",
                "notes": "",
            }
        )

    event_missing = sorted([c for c in REQUIRED_DIAGNOSTIC_COLUMNS if c not in ecols]) if not event_df.empty else []
    derek_missing = sorted([c for c in REQUIRED_DEREK_COLUMNS if c not in dcols]) if not derek_df.empty else []
    for col in event_missing:
        diff_rows.append(
            {
                "category": "missing_event_market_diagnostic_column",
                "column": col,
                "training_value": None,
                "prediction_value": None,
                "delta": None,
                "severity": "warn",
                "notes": "event_market_rows_missing",
            }
        )
    for col in derek_missing:
        diff_rows.append(
            {
                "category": "missing_derek_column",
                "column": col,
                "training_value": None,
                "prediction_value": None,
                "delta": None,
                "severity": "warn",
                "notes": "derek_feed_missing",
            }
        )

    leakage_cols = sorted([c for c in tcols if c in LEAKAGE_BLOCKED_COLUMNS])
    for col in leakage_cols:
        diff_rows.append(
            {
                "category": "market_leakage_column_in_training",
                "column": col,
                "training_value": "present",
                "prediction_value": None,
                "delta": None,
                "severity": "fail",
                "notes": "",
            }
        )

    blocker_counts = {
        "duplicate_key_rows_training": train_dup_count,
        "duplicate_key_rows_prediction": pred_dup_count,
        "asof_timestamp_mismatch_count": asof_mismatch_count,
        "market_leakage_columns_in_training": len(leakage_cols),
    }

    summary = {
        "training_rows": int(len(train_df)),
        "prediction_rows": int(len(pred_df)),
        "training_columns": len(tcols),
        "prediction_columns": len(pcols),
        "common_columns": len(shared_cols),
        "missing_in_training_count": len(missing_training),
        "missing_in_prediction_count": len(missing_prediction),
        "missing_in_training": missing_training[:200],
        "missing_in_prediction": missing_prediction[:200],
        "dtype_mismatch_count": len(dtype_mismatches),
        "null_rate_mismatch_count": len(null_rate_mismatches),
        "key_columns_used": key_cols,
        "key_overlap_count": key_overlap_count,
        "training_only_key_count": train_key_only_count,
        "prediction_only_key_count": pred_key_only_count,
        "asof_columns_compared": asof_cols,
        "asof_rows_compared": comparable_asof_rows,
        "features_unavailable_at_prediction_time_count": len(unavailable_training_present),
        "prediction_only_fields_not_used_in_training_count": len(prediction_only_fields),
        "event_market_missing_diagnostics_count": len(event_missing),
        "event_market_missing_diagnostics": event_missing,
        "derek_feed_missing_columns_count": len(derek_missing),
        "derek_feed_missing_columns": derek_missing,
        "market_leakage_columns_in_training": leakage_cols,
        "blockers": blocker_counts,
    }
    summary["pass"] = all(value == 0 for value in blocker_counts.values())

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    summary_lines = [
        "# Feature Snapshot Training vs Prediction Parity",
        "",
        f"- result: {'PASS' if summary['pass'] else 'FAIL'}",
        f"- training rows/cols: {summary['training_rows']} / {summary['training_columns']}",
        f"- prediction rows/cols: {summary['prediction_rows']} / {summary['prediction_columns']}",
        f"- shared columns: {summary['common_columns']}",
        f"- missing training columns (prediction-only): {summary['missing_in_training_count']}",
        f"- missing prediction columns (training-only): {summary['missing_in_prediction_count']}",
        f"- dtype mismatches: {summary['dtype_mismatch_count']}",
        f"- null-rate mismatches: {summary['null_rate_mismatch_count']}",
        f"- key overlap: {summary['key_overlap_count']}",
        f"- training duplicate keys: {train_dup_count}",
        f"- prediction duplicate keys: {pred_dup_count}",
        f"- as-of mismatches: {asof_mismatch_count}",
        f"- event diagnostics missing: {len(event_missing)}",
        f"- derek missing required parity columns: {len(derek_missing)}",
        f"- blocked leakage columns in training: {len(leakage_cols)}",
    ]
    _write_debug_outputs(
        debug_dir=Path(args.debug_dir),
        diff_rows=diff_rows,
        summary_lines=summary_lines,
    )

    print(
        "FEATURE_SNAPSHOT_TRAINING_PREDICTION_PARITY_PASS"
        if summary["pass"]
        else "FEATURE_SNAPSHOT_TRAINING_PREDICTION_PARITY_FAIL"
    )
    return 0 if summary["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
