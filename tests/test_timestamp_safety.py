"""PHASE 4 guardrails — no post-prediction quote information in pregame features.

Pregame features may only reference opening or as-of-prediction quotes.
Closing-line data is reserved for ex-post CLV evaluation (see
evaluation/grading.py and scripts/snapshot_closing_lines.py).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


REPO = Path(__file__).parent.parent


def test_historical_odds_snapshots_are_all_pregame():
    """Every historical odds snapshot used in training must have
    snapshot_utc < commence_time. A single violation is a leakage bug."""
    p = REPO / "data/historical_game_odds.parquet"
    if not p.exists():
        pytest.skip("historical_game_odds.parquet not present")
    df = pd.read_parquet(p)
    ct = pd.to_datetime(df["commence_time"], utc=True, errors="coerce")
    su = pd.to_datetime(df["snapshot_utc"], utc=True, errors="coerce")
    violations = int((su > ct).sum())
    assert violations == 0, (
        f"{violations} odds rows have snapshot_utc AFTER commence_time — "
        "these are post-game quotes and must not be used as pregame features"
    )


def test_enrich_game_context_has_no_closing_line_fallback():
    """The open_close_*_delta fallback in enrich_game_context_with_snapshots
    was a closing-line path — it must not be reintroduced."""
    src = (REPO / "src/nba_props_model/data/bdl_client.py").read_text()
    enrich_start = src.index("def enrich_game_context_with_snapshots")
    enrich_end = src.index("\ndef ", enrich_start + 1)
    body = src[enrich_start:enrich_end]
    assert "open_close_total_delta" not in body, (
        "closing-line fallback re-introduced in enrich_game_context_with_snapshots"
    )
    assert "open_close_spread_delta" not in body, (
        "closing-line fallback re-introduced in enrich_game_context_with_snapshots"
    )


def test_pregame_feature_set_excludes_closing_columns():
    """If a training table exists, no pregame feature column may be named
    closing_* or *_close — those belong to the CLV/grading surface."""
    p = REPO / "data/training_table.parquet"
    if not p.exists():
        pytest.skip("training_table.parquet not present")
    cols = pd.read_parquet(p, columns=None).columns.tolist()
    forbidden = [
        c for c in cols
        if c.startswith("closing_") or c.endswith("_close") or c.endswith("_closing")
    ]
    # "clv" / "clv_proxy" are allowed in GRADED reports but NEVER in training.
    forbidden += [c for c in cols if c.lower() == "clv" or c.lower() == "clv_proxy"]
    assert not forbidden, f"leakage-suspect columns in training table: {forbidden}"
