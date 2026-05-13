#!/usr/bin/env python3
"""Per eligible failed segment: exact metric coverage and failure reason."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

REQ_METRIC = (
    "model_prob_over",
    "market_prob_over_no_vig",
    "hit_result",
    "model_brier",
    "market_brier",
    "model_event_logloss",
    "market_event_logloss",
)


def _null_counts(sub: pd.DataFrame) -> dict[str, int]:
    out: dict[str, int] = {}
    for c in REQ_METRIC:
        if c not in sub.columns:
            out[c] = -1
        else:
            out[c] = int(sub[c].isna().sum())
    return out


def _row_deltas(sub: pd.DataFrame) -> tuple[float | None, float | None]:
    if not all(c in sub.columns for c in ("model_probability_for_side", "market_probability_for_side", "hit_result")):
        return None, None
    m = sub["model_probability_for_side"].astype(float)
    q = sub["market_probability_for_side"].astype(float)
    o = sub["hit_result"].astype(float)
    mask = m.notna() & q.notna() & o.notna() & o.isin([0.0, 1.0])
    if int(mask.sum()) == 0:
        return None, None
    m, q, o = m[mask], q[mask], o[mask]
    b_m = float(np.mean((m - o) ** 2))
    b_q = float(np.mean((q - o) ** 2))
    eps = 1e-12
    ll_m = float(np.mean(-(o * np.log(np.clip(m, eps, 1 - eps)) + (1 - o) * np.log(np.clip(1 - m, eps, 1 - eps)))))
    ll_q = float(np.mean(-(o * np.log(np.clip(q, eps, 1 - eps)) + (1 - o) * np.log(np.clip(1 - q, eps, 1 - eps)))))
    return b_m - b_q, ll_m - ll_q


def _precise_reason(row: pd.Series, sub: pd.DataFrame) -> str:
    fr = str(row.get("failure_reason") or "")
    if fr and fr != "model_metrics_missing_or_join_incomplete":
        return fr
    nc = _null_counts(sub)
    missing = [k for k, v in nc.items() if v == -1 or (v == len(sub) and len(sub) > 0)]
    if missing:
        return "join_incomplete"
    for col, reason in (
        ("model_prob_over", "missing_model_prob_over"),
        ("market_prob_over_no_vig", "missing_market_prob_over"),
        ("hit_result", "missing_actual_outcome"),
        ("model_brier", "missing_model_brier"),
        ("market_brier", "missing_market_brier"),
        ("model_event_logloss", "missing_model_logloss"),
        ("market_event_logloss", "missing_market_logloss"),
    ):
        if nc.get(col, 0) == len(sub) and len(sub) > 0:
            return reason
    db, dl = _row_deltas(sub)
    if dl is not None and dl >= 0:
        return "model_logloss_not_better"
    if db is not None and db >= 0:
        return "model_brier_not_better"
    return "unknown_bug"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="e.g. dates_e77f109a685a")
    args = ap.parse_args()

    label = args.label.strip()
    base = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_superiority_{label}"
    eml = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    sr_path = base / "stat_role_market_superiority.csv"
    summ_path = base / "summary.json"
    for p in (eml, sr_path, summ_path):
        if not p.exists():
            print(f"MISSING {p}", file=sys.stderr)
            return 2

    combo = pd.read_parquet(eml)
    sr = pd.read_csv(sr_path)
    elig_fail = sr[(sr.get("market_superiority_eligible") == True) & (sr.get("market_superiority_pass") == False)]
    rows: list[dict] = []
    for _, row in elig_fail.iterrows():
        stat = str(row["stat"]).lower()
        role = str(row["role_bucket"])
        sub = combo[(combo["stat"].astype(str).str.lower() == stat) & (combo["role_bucket"].astype(str) == role)]
        joined = sub[sub.get("join_status", "") == "matched"] if "join_status" in sub.columns else sub
        mask = pd.Series(True, index=sub.index)
        for c in ("model_event_logloss", "market_event_logloss", "model_brier", "market_brier"):
            if c in sub.columns:
                mask &= sub[c].notna()
        scored = sub.loc[mask]
        db, dl = _row_deltas(sub)
        prec = _precise_reason(row, sub)
        rows.append(
            {
                "stat": stat,
                "role_bucket": role,
                "n_event_rows": int(len(sub)),
                "n_matched_rows": int(len(joined)),
                "n_scored_rows": int(len(scored)),
                "has_model_prob_over": bool("model_prob_over" in sub.columns and sub["model_prob_over"].notna().any()),
                "has_market_prob_over": bool(
                    "market_prob_over_no_vig" in sub.columns and sub["market_prob_over_no_vig"].notna().any()
                ),
                "has_actual_outcome": bool("hit_result" in sub.columns and sub["hit_result"].notna().any()),
                "has_model_brier": bool("model_brier" in sub.columns and sub["model_brier"].notna().any()),
                "has_market_brier": bool("market_brier" in sub.columns and sub["market_brier"].notna().any()),
                "has_model_logloss": bool("model_event_logloss" in sub.columns and sub["model_event_logloss"].notna().any()),
                "has_market_logloss": bool("market_event_logloss" in sub.columns and sub["market_event_logloss"].notna().any()),
                "model_brier": row.get("model_brier_avg"),
                "market_brier": row.get("market_brier_avg"),
                "model_logloss": row.get("model_logloss_avg"),
                "market_logloss": row.get("market_logloss_avg"),
                "delta_brier": db,
                "delta_logloss": dl,
                "exact_missing_metric_columns": [k for k, v in _null_counts(sub).items() if v == len(sub) and len(sub) > 0],
                "exact_null_count_by_required_metric": _null_counts(sub),
                "precise_failure_reason": prec,
            }
        )

    out_dir = base
    out_csv = out_dir / "segment_failure_diagnosis.csv"
    out_md = out_dir / "segment_failure_diagnosis.md"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    lines = ["# Segment failure diagnosis", "", f"Label `{label}`", "", pd.DataFrame(rows).to_string(index=False)]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
