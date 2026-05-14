#!/usr/bin/env python3
"""M8.7 — diagnose PMF mean-shift targets from repair ledger + loss rows."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from build_event_market_loss_rows import _parse_pmf_value, _normalize_pmf  # noqa: E402
from nba_props_model.calibration.pmf_mean_shift_repair import (  # noqa: E402
    combo_stat_needs_coherence,
    pmf_mean,
    segment_key,
)

ART = REPO_ROOT / "artifacts" / "model_diagnostics"


def _parse_pmf_row(v) -> dict:
    p = _parse_pmf_value(v)
    return _normalize_pmf(p) if p else {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    label = str(args.label)
    ledger_path = ART / f"market_superiority_repair_{label}" / "repair_ledger.csv"
    loss_path = ART / f"event_market_loss_rows_{label}.parquet"
    if not ledger_path.is_file():
        raise SystemExit(f"FATAL: missing {ledger_path}")
    if not loss_path.is_file():
        raise SystemExit(f"FATAL: missing {loss_path}")

    led = pd.read_csv(ledger_path)
    loss = pd.read_parquet(loss_path)
    if "model_pmf" not in loss.columns and "model_pmf_raw" not in loss.columns:
        raise SystemExit("FATAL: loss rows missing model_pmf / model_pmf_raw")

    pmf_col = "model_pmf_raw" if "model_pmf_raw" in loss.columns else "model_pmf"

    targets = led[
        (led["dominant_failure"].astype(str) == "mean_too_low")
        | led["allowed_repair_family"].astype(str).str.contains("pmf_mean_shift", na=False)
    ].copy()

    rows = []
    for _, lr in targets.iterrows():
        stat = str(lr["stat"]).lower()
        role = str(lr["role_bucket"]).lower()
        sub = loss[
            (loss["stat"].astype(str).str.lower() == stat)
            & (loss["role_bucket"].astype(str).str.lower() == role)
        ]
        sub = sub[sub["actual"].notna() & sub[pmf_col].notna()].copy()
        if sub.empty:
            continue
        mus = []
        acts = []
        for _, r in sub.iterrows():
            pmf = _parse_pmf_row(r[pmf_col])
            if not pmf:
                continue
            try:
                a = int(r["actual"])
            except Exception:
                continue
            mus.append(pmf_mean(pmf))
            acts.append(float(a))
        if not mus:
            continue
        model_mean_avg = float(pd.Series(mus).mean())
        actual_mean_avg = float(pd.Series(acts).mean())
        mean_bias = model_mean_avg - actual_mean_avg
        mean_abs_error = float(pd.Series([abs(m - a) for m, a in zip(mus, acts)]).mean())
        n_dates = int(sub["date"].nunique()) if "date" in sub.columns else 0

        bfail = str(lr.get("bootstrap_failure_type") or "")

        direction = "increase_pmf_mean" if mean_bias < 0 else "decrease_pmf_mean"

        rows.append(
            {
                "stat": stat,
                "role_bucket": role,
                "segment_key": segment_key(stat, role),
                "n": int(len(mus)),
                "n_dates": n_dates,
                "model_mean_avg": model_mean_avg,
                "actual_mean_avg": actual_mean_avg,
                "mean_bias": mean_bias,
                "mean_abs_error": mean_abs_error,
                "model_logloss": float(lr.get("model_logloss", float("nan"))),
                "market_logloss": float(lr.get("market_logloss", float("nan"))),
                "model_brier": float(lr.get("model_brier", float("nan"))),
                "market_brier": float(lr.get("market_brier", float("nan"))),
                "delta_logloss": float(lr.get("delta_logloss", float("nan"))),
                "delta_brier": float(lr.get("delta_brier", float("nan"))),
                "calibration_pass": bool(lr.get("calibration_pass", False)),
                "market_superiority_pass": bool(lr.get("market_superiority_pass", False)),
                "bootstrap_failure_type": bfail,
                "recommended_mean_repair_direction": direction,
                "combo_stat_coherence_required": combo_stat_needs_coherence(stat),
            }
        )

    out = pd.DataFrame(rows)
    out_dir = ART / f"pmf_mean_shift_repair_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / "target_segments.csv", index=False)
    md = [f"# PMF mean-shift targets ({label})", "", f"- Segments: **{len(out)}**", ""]
    if len(out):
        md.append(out.head(50).to_string())
        if len(out) > 50:
            md.append(f"\n... ({len(out) - 50} more rows)")
    else:
        md.append("_No target rows._")
    (out_dir / "target_segments.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {out_dir.relative_to(REPO_ROOT)}/target_segments.csv rows={len(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
