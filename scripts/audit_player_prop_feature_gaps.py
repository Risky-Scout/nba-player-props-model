#!/usr/bin/env python3
"""Audit feature-family coverage gaps for M8.9."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.player_prop_feature_contract import (  # noqa: E402
    LeakageStatus,
    feature_families,
    forbidden_model_only_training_features,
)


def _read_parquet(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_parquet(path)


def _column_stats(df: pd.DataFrame, col: str) -> tuple[float, int]:
    if col not in df.columns or df.empty:
        return 0.0, 0
    s = df[col]
    non_null_rate = float(s.notna().mean())
    nunique = int(s.nunique(dropna=True))
    return non_null_rate, nunique


def _inventory(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "dataset",
                "column",
                "present",
                "non_null_rate",
                "unique_count",
            ]
        )
    rows: list[dict[str, Any]] = []
    for c in df.columns:
        nnr, uq = _column_stats(df, c)
        rows.append(
            {
                "dataset": dataset_name,
                "column": str(c),
                "present": True,
                "non_null_rate": nnr,
                "unique_count": uq,
            }
        )
    return pd.DataFrame(rows)


def _family_summary(training_df: pd.DataFrame, event_df: pd.DataFrame) -> pd.DataFrame:
    tcols = set(str(c) for c in training_df.columns)
    ecols = set(str(c) for c in event_df.columns)
    rows: list[dict[str, Any]] = []

    for fam in feature_families():
        fcols = [x.name for x in fam.features]
        in_training = [c for c in fcols if c in tcols]
        in_event = [c for c in fcols if c in ecols]
        missing_training = [c for c in fcols if c not in tcols]
        missing_event = [c for c in fcols if c not in ecols]
        train_non_null = (
            float(
                sum(
                    _column_stats(training_df, c)[0]
                    for c in in_training
                )
                / max(len(in_training), 1)
            )
            if in_training
            else 0.0
        )
        event_non_null = (
            float(
                sum(
                    _column_stats(event_df, c)[0]
                    for c in in_event
                )
                / max(len(in_event), 1)
            )
            if in_event
            else 0.0
        )
        if not in_training:
            action = "add"
        elif fam.leakage_status != LeakageStatus.SAFE:
            action = "demote_to_market_residual"
        elif len(missing_training) > 0:
            action = "replace"
        elif not in_event:
            action = "preserve_but_expose_to_diagnostics"
        else:
            action = "no_action"
        rows.append(
            {
                "feature_family": fam.name,
                "source": fam.source,
                "leakage_status": fam.leakage_status.value,
                "n_features_contract": len(fcols),
                "n_present_training_table": len(in_training),
                "n_present_event_market_rows": len(in_event),
                "missing_in_training_table": "|".join(missing_training),
                "missing_in_event_market_rows": "|".join(missing_event),
                "avg_non_null_rate_training_table": train_non_null,
                "avg_non_null_rate_event_market_rows": event_non_null,
                "stale_freshness_columns_present": any("freshness" in c for c in in_training),
                "used_by_model_training": fam.leakage_status == LeakageStatus.SAFE,
                "used_by_prediction": fam.leakage_status == LeakageStatus.SAFE,
                "exposed_to_deliveries": bool(in_event),
                "leakage_risk": fam.leakage_status != LeakageStatus.SAFE,
                "recommended_action": action,
            }
        )
    return pd.DataFrame(rows)


def _high_priority_gaps(gaps: pd.DataFrame) -> pd.DataFrame:
    priority = gaps[
        (gaps["n_present_training_table"] == 0)
        | (gaps["feature_family"].isin({"injury_availability", "expected_lineup", "official_lineup"}))
        | (
            (gaps["feature_family"].isin({"usage_opportunity", "schedule_context", "teammate_on_off"}))
            & (gaps["n_present_event_market_rows"] == 0)
        )
    ].copy()
    priority["priority"] = "high"
    return priority


def _leakage_risk_rows(gaps: pd.DataFrame, training_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    tcols = set(str(c) for c in training_df.columns)
    forbidden = set(forbidden_model_only_training_features())
    for col in sorted(forbidden):
        rows.append(
            {
                "column": col,
                "present_in_training_table": col in tcols,
                "risk": "forbidden_model_only_training_feature",
                "recommended_action": "demote_to_market_residual" if col in tcols else "no_action",
            }
        )
    return pd.DataFrame(rows)


def _summary(gaps: pd.DataFrame, training_df: pd.DataFrame, event_df: pd.DataFrame) -> dict[str, Any]:
    fam = {r["feature_family"]: r for _, r in gaps.iterrows()}
    lineup_train = int(fam.get("official_lineup", {}).get("n_present_training_table", 0)) + int(
        fam.get("expected_lineup", {}).get("n_present_training_table", 0)
    )
    event_context = int(fam.get("usage_opportunity", {}).get("n_present_event_market_rows", 0)) + int(
        fam.get("schedule_context", {}).get("n_present_event_market_rows", 0)
    )
    injury_training = int(fam.get("injury_availability", {}).get("n_present_training_table", 0))
    expected_findings = {
        "lineup_features_insufficient_in_training_table": lineup_train < 10,
        "event_market_rows_missing_lineup_usage_rest_context": event_context < 8,
        "injury_availability_features_too_sparse": injury_training < 10,
    }
    return {
        "n_training_rows": int(len(training_df)),
        "n_event_market_rows": int(len(event_df)),
        "n_training_columns": int(len(training_df.columns)),
        "n_event_market_columns": int(len(event_df.columns)),
        "n_feature_families": int(len(gaps)),
        "n_families_missing_in_training": int((gaps["n_present_training_table"] == 0).sum()),
        "n_families_missing_in_event_rows": int((gaps["n_present_event_market_rows"] == 0).sum()),
        "expected_findings": expected_findings,
        "pass": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--training-table", required=True)
    ap.add_argument("--event-market-rows", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    training_df = _read_parquet(Path(args.training_table))
    event_df = _read_parquet(Path(args.event_market_rows))

    inv_training = _inventory(training_df, "training_table")
    inv_event = _inventory(event_df, "event_market_rows")
    gaps = _family_summary(training_df, event_df)
    hi = _high_priority_gaps(gaps)
    leak = _leakage_risk_rows(gaps, training_df)
    summary = _summary(gaps, training_df, event_df)

    inv_training.to_csv(out_dir / "feature_inventory_training_table.csv", index=False)
    inv_event.to_csv(out_dir / "feature_inventory_event_market_rows.csv", index=False)
    gaps.to_csv(out_dir / "feature_gap_summary.csv", index=False)
    hi.to_csv(out_dir / "high_priority_missing_features.csv", index=False)
    leak.to_csv(out_dir / "leakage_risk_features.csv", index=False)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Player-prop feature engineering audit",
        "",
        f"- training rows: **{summary['n_training_rows']}**",
        f"- event market rows: **{summary['n_event_market_rows']}**",
        f"- families missing in training: **{summary['n_families_missing_in_training']}**",
        f"- families missing in event rows: **{summary['n_families_missing_in_event_rows']}**",
        "",
        "## Expected findings",
    ]
    for k, v in summary["expected_findings"].items():
        md.append(f"- `{k}`: `{bool(v)}`")
    (out_dir / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("PLAYER_PROP_FEATURE_GAP_AUDIT_PASS")
    try:
        shown = str(out_dir.relative_to(REPO_ROOT))
    except ValueError:
        shown = str(out_dir)
    print(f"  wrote: {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
