#!/usr/bin/env python3
"""Anti-leakage audit for PMF mean-shift repair (read-only checks on source + manifests)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    fit_py = REPO_ROOT / "scripts" / "fit_pmf_mean_shift_repair.py"
    apply_py = REPO_ROOT / "scripts" / "apply_pmf_mean_shift_repair.py"
    lib_py = REPO_ROOT / "src" / "nba_props_model" / "calibration" / "pmf_mean_shift_repair.py"
    for p in (fit_py, apply_py, lib_py):
        if not p.is_file():
            print(f"FATAL: missing {p}", file=sys.stderr)
            return 2

    fit_t = _read(fit_py).lower()
    for tok in ("no_vig", "market_prob_over", "odds_implied_prob", "book_prob"):
        if tok in fit_t:
            print(f"FATAL: forbidden token {tok!r} in fit script", file=sys.stderr)
            return 2

    man_dir = REPO_ROOT / "artifacts" / "models"
    if man_dir.is_dir():
        for name in sorted(man_dir.glob("pmf_mean_shift_repair_*.json")):
            t = _read(name).lower().replace(" ", "")
            if '"uses_market_probability_as_label":true' in t:
                print(f"FATAL: bad manifest flag in {name}", file=sys.stderr)
                return 2
            if '"uses_market_probability_as_feature":true' in t:
                print(f"FATAL: bad manifest flag in {name}", file=sys.stderr)
                return 2

    print("PMF_MEAN_SHIFT_REPAIR_AUDIT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
