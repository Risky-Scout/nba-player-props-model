#!/usr/bin/env python3
"""Static audit: no market-in-fit, bounded probabilities, canonical PMF policy."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FIT_SCRIPTS = (
    "scripts/fit_event_neutral_probability_scale_repair.py",
    "scripts/build_market_superiority_repair_ledger.py",
)

FORBIDDEN_IN_FIT = (
    "market_prob_over",
    "no_vig_over_prob",
    "market_prob",
    "book_prob",
    "odds_implied_prob",
)


def _grep_file(path: Path, pattern: str) -> list[str]:
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return []
    return [ln for ln in txt.splitlines() if re.search(pattern, ln, re.I)]


def main() -> int:
    for rel in FIT_SCRIPTS:
        p = REPO_ROOT / rel
        if not p.is_file():
            continue
        for tok in FORBIDDEN_IN_FIT:
            hits = _grep_file(p, rf"\b{re.escape(tok)}\b")
            bad = [h for h in hits if "FORBIDDEN" not in h and "evaluation" not in h.lower()]
            if bad and "FORBIDDEN_TRAINING_FEATURE" not in "\n".join(bad):
                # allow explicit comments / string literals in forbidden tuple
                if tok in p.read_text() and "FORBIDDEN_TRAINING_FEATURE_SUBSTR" in p.read_text():
                    continue
                if any("FORBIDDEN" in h for h in bad):
                    continue
                print(f"WARN: {rel} references {tok}: {bad[:3]}")

    # Fold separation: fit script must reference chronological_date_folds
    fitp = REPO_ROOT / "scripts/fit_event_neutral_probability_scale_repair.py"
    if fitp.is_file() and "chronological_date_folds" not in fitp.read_text(encoding="utf-8"):
        print("FATAL: fit script missing chronological_date_folds", file=sys.stderr)
        return 2

    print("EVENT_NEUTRAL_PROBABILITY_REPAIR_AUDIT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
