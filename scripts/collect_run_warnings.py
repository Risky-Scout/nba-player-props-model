#!/usr/bin/env python3
"""Scan captured logs and emit warnings_summary.json + critical_warnings.json."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CRITICAL_PATTERNS = [
    (r"market_eval_not_wired", "market_eval_not_wired"),
    (r"Traceback \(most recent call last\)", "traceback"),
    (r"invalid_pmf", "invalid_pmf"),
    (r"PHASE8_MARKET_EVAL_NOT_WIRED_FAIL", "phase8_market_eval_not_wired"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()
    run_dir = args.run_dir
    if not run_dir.is_dir():
        print(f"MISSING {run_dir}", file=sys.stderr)
        return 2
    hits: list[dict] = []
    crit: list[dict] = []
    for f in sorted(run_dir.glob("*.log")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), 1):
            for pat, name in CRITICAL_PATTERNS:
                if re.search(pat, line, re.I):
                    rec = {"file": str(f.name), "line": line_no, "pattern": name, "text": line[:500]}
                    hits.append(rec)
                    crit.append(rec)
    summ = {"n_lines_scanned": sum(1 for _ in run_dir.glob("*.log")), "n_critical": len(crit)}
    (run_dir / "warnings_summary.json").write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8")
    (run_dir / "critical_warnings.json").write_text(json.dumps(crit, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote warnings_summary.json ({len(crit)} critical)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
