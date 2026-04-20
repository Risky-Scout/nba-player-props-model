"""PHASE 3 guardrail — odds ingestion is not a silent zero.

The retrain pipeline reads `data/historical_game_odds.parquet` and the daily
graded reports carry over/under odds and result columns. If either source
disappears, the market-relative evaluation in run_diagnostics.py must
hard-gate to PRICING-ONLY MODE instead of silently continuing with 0 rows.
"""
from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd
import pytest


REPO = Path(__file__).parent.parent


def test_historical_odds_parquet_nonempty_or_absent():
    """If historical_game_odds.parquet exists, it must have rows. A zero-row
    parquet is a silent ingestion failure."""
    p = REPO / "data/historical_game_odds.parquet"
    if not p.exists():
        pytest.skip("historical_game_odds.parquet not present in this env")
    df = pd.read_parquet(p)
    assert len(df) > 0, "historical_game_odds.parquet is empty — ingestion broken"
    for col in ("game_date", "home_team", "away_team", "consensus_total"):
        assert col in df.columns, f"historical odds missing column {col!r}"


def test_graded_reports_carry_odds_and_result():
    """Each graded CSV must carry the line, odds columns, and a result so
    market-relative evaluation has real inputs."""
    files = sorted(glob.glob(str(REPO / "artifacts/graded/graded_*.csv")))
    if not files:
        pytest.skip("no graded reports in this env")
    required = {"line", "over_odds", "under_odds", "result", "model_prob"}
    for f in files[-5:]:  # sample last 5 days
        df = pd.read_csv(f)
        missing = required - set(df.columns)
        assert not missing, f"{f} missing columns: {missing}"
        assert len(df) > 0, f"{f} is empty"
