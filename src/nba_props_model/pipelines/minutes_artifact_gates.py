"""Guards for artifacts/minutes_predictions — keep stat-grid from half-built runs."""

from __future__ import annotations

import sys
from pathlib import Path


def require_minutes_predictions_eligible_present(repo_root: Path, slate_date: str) -> None:
    """Fail before stat-grid when the universe parquet exists but eligible is absent."""
    uni = (
        repo_root
        / "artifacts"
        / "minutes_predictions"
        / slate_date
        / "minutes_predictions.parquet"
    )
    elig = (
        repo_root
        / "artifacts"
        / "minutes_predictions"
        / slate_date
        / "minutes_predictions_eligible.parquet"
    )
    if uni.is_file() and not elig.is_file():
        msg = (
            "FATAL: MINUTES_PREDICTIONS_ELIGIBLE_MISSING "
            f"universe exists at {uni} but eligible parquet missing at {elig}"
        )
        print(msg, file=sys.stderr)
        raise SystemExit(msg)
