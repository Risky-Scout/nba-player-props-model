#!/usr/bin/env python3
"""Summarize guarded event-market calibration candidates and rollbacks."""
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
    base = REPO_ROOT / "artifacts" / "model_diagnostics" / f"guarded_event_calibration_{label}"
    for name in ("candidate_results.csv", "rollback_report.csv", "summary.json"):
        if not (base / name).is_file():
            print(f"FATAL missing {base/name}", file=sys.stderr)
            return 2
    cand = pd.read_csv(base / "candidate_results.csv")
    roll = pd.read_csv(base / "rollback_report.csv")
    summ = json.loads((base / "summary.json").read_text(encoding="utf-8"))

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"guarded_event_calibration_diagnosis_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    roll_reasons = roll["reason"].value_counts().to_dict() if "reason" in roll.columns else {}
    method_attempts = cand["method"].value_counts().to_dict() if "method" in cand.columns else {}

    lines = [
        f"# Guarded event calibration rollback diagnosis — {label}",
        "",
        f"- **selected (summary):** n_selected={summ.get('n_selected')}",
        f"- **rollbacks (summary):** n_rollbacks={summ.get('n_rollbacks')}",
        "",
        "## Methods attempted (candidate_results)",
        "",
        "```",
        json.dumps(method_attempts, indent=2),
        "```",
        "",
        "## Rollback reasons",
        "",
        "```",
        json.dumps(roll_reasons, indent=2),
        "```",
        "",
        "## Interpretation",
        "",
        "- **`rollback_fold_worse`:** calibrator improved in-sample but hurt held-out logloss/Brier → treat as **overfit / too few fold rows**.",
        "- **`small_fold`:** not enough dated rows per segment for stable CV.",
        "- **Next candidate types:** lighter Platt / temperature scaling with stronger L2; hierarchical pooling across stat; skip line-aware until base passes.",
        "",
    ]
    (out_dir / "rollback_diagnosis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    pd.DataFrame(
        [
            {"kind": "rollback_reason", "key": k, "count": int(v)}
            for k, v in sorted(roll_reasons.items(), key=lambda kv: -kv[1])
        ]
    ).to_csv(out_dir / "rollback_reason_counts.csv", index=False)
    print(f"GUARDED_EVENT_CALIB_DIAG wrote {out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
