#!/usr/bin/env python3
"""Placeholder: write identity monotone calibration manifest (v0)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "artifacts" / "models" / "monotone_pmf_cdf_v0.json"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "version": "monotone_identity_v0",
                "fitted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "note": "Identity pass-through; replace with isotonic CDF fit when OOF PIT pipeline lands.",
            },
            indent=2,
        )
        + "\n"
    )
    print(f"MONOTONE_CDF_FIT_PASS {OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
