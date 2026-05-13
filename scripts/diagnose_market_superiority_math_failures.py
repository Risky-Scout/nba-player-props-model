#!/usr/bin/env python3
"""Summarize math-contract inequality failures vs bootstrap deltas."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    label = str(args.label).strip()
    base = REPO_ROOT / "artifacts" / "model_diagnostics" / f"market_superiority_math_contract_{label}"
    inf_path = base / "stat_role_inequality_failures.csv"
    boot_path = base / "bootstrap_deltas.csv"
    if not inf_path.is_file() or not boot_path.is_file():
        print(f"FATAL missing inputs under {base}", file=sys.stderr)
        return 2
    inf = pd.read_csv(inf_path)
    boot = pd.read_csv(boot_path)
    bcols = [
        "stat",
        "role_bucket",
        "mean_delta_brier",
        "bootstrap_upper95_mean_delta_brier",
        "mean_delta_logloss",
        "bootstrap_upper95_mean_delta_logloss",
    ]
    merged = inf.merge(boot[bcols], on=["stat", "role_bucket"], how="left")

    reason_vc = inf["reason"].value_counts().to_dict()
    pair_vc = inf.assign(pair=inf["stat"] + "|" + inf["role_bucket"])["pair"].value_counts().head(50).to_dict()

    rows = []
    for _, r in merged.iterrows():
        reasons = []
        rs = str(r.get("reason", ""))
        if "mean_delta" in rs:
            reasons.append("mean_delta_logloss_or_brier_not_negative_vs_market")
        if "bootstrap" in rs:
            reasons.append("bootstrap_upper95_not_better_than_market")
        mdb = r.get("mean_delta_brier")
        u95b = r.get("bootstrap_upper95_mean_delta_brier")
        mdl = r.get("mean_delta_logloss")
        u95l = r.get("bootstrap_upper95_mean_delta_logloss")
        smallest = []
        try:
            if mdl is not None and u95l is not None and float(mdl) > float(u95l):
                smallest.append("need_mean_logloss_delta <= observed bootstrap upper bound is impossible; widen data or improve model")
            if mdb is not None and u95b is not None and float(mdb) > float(u95b):
                smallest.append("need_mean_brier_delta more negative vs bootstrap noise")
        except Exception:
            pass
        rows.append(
            {
                "stat": r.get("stat"),
                "role_bucket": r.get("role_bucket"),
                "inequality_reason": rs,
                "mean_delta_brier": mdb,
                "bootstrap_upper95_mean_delta_brier": u95b,
                "mean_delta_logloss": mdl,
                "bootstrap_upper95_mean_delta_logloss": u95l,
                "interpretation": "; ".join(reasons) if reasons else rs,
            }
        )

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"market_superiority_math_failure_diag_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_dir / "math_failure_breakdown.csv", index=False)
    summary = {
        "label": label,
        "failure_row_count": int(len(inf)),
        "reason_counts": reason_vc,
        "top_stat_role_pairs": pair_vc,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    md = [
        f"# Math contract failure diagnosis — {label}",
        "",
        "## Reason counts",
        "",
        "```",
        json.dumps(reason_vc, indent=2),
        "```",
        "",
        "Inequalities require both **negative mean deltas** (model better) and **bootstrap upper CI** below zero for strict superiority.",
        "",
    ]
    (out_dir / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"MATH_FAILURE_DIAG wrote {out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
