#!/usr/bin/env python3
"""M8.8 — verify GitHub Actions daily delivery workflow wiring."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.parse_args()
    wf = REPO_ROOT / ".github" / "workflows" / "daily_pmf_delivery.yml"
    out = REPO_ROOT / "artifacts" / "model_diagnostics" / "github_delivery_automation"
    out.mkdir(parents=True, exist_ok=True)
    if not wf.is_file():
        print("GITHUB_DELIVERY_AUTOMATION_AUDIT_FAIL missing_workflow")
        return 2
    txt = wf.read_text(encoding="utf-8")
    ok = True
    checks = [
        ("workflow_dispatch", "workflow_dispatch" in txt),
        ("odds_secret", "ODDS_API_KEY" in txt),
        ("bdl_secret", "BDL_API_KEY" in txt),
        ("pythonpath_src", "PYTHONPATH: src" in txt),
        ("run_daily_delivery_pipeline", "run_daily_delivery_pipeline.py" in txt),
        ("verify_daily_delivery_folder", "verify_daily_delivery_folder_contract.py" in txt),
    ]
    if not all(c[1] for c in checks):
        ok = False
    rows = [{"check": k, "ok": v} for k, v in checks]
    with (out / "workflow_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["check", "ok"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    summ = {"pass_all": ok, "workflow": str(wf.relative_to(REPO_ROOT))}
    (out / "summary.json").write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8")
    (out / "summary.md").write_text(
        f"# GitHub delivery automation audit\n\n- pass_all: `{ok}`\n", encoding="utf-8"
    )
    if ok:
        print("GITHUB_DELIVERY_AUTOMATION_AUDIT_PASS")
    else:
        print("GITHUB_DELIVERY_AUTOMATION_AUDIT_FAIL")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
