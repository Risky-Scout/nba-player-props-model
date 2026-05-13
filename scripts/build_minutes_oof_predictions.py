#!/usr/bin/env python3
"""Ensure data/oof_minutes_predictions.parquet exists (delegates to train)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OOF = REPO_ROOT / "data" / "oof_minutes_predictions.parquet"


def main() -> int:
    if OOF.exists():
        print(f"MINUTES_OOF_ALREADY_PRESENT {OOF}")
        return 0
    return subprocess.call(
        [sys.executable, str(REPO_ROOT / "scripts" / "train_minutes_model.py"), "--walk-forward"],
        cwd=str(REPO_ROOT),
    )


if __name__ == "__main__":
    raise SystemExit(main())
