"""Sparse-stat opportunity features for M8.9."""
from __future__ import annotations

import pandas as pd


def build_sparse_stat_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    mins = out.get("projected_minutes", pd.Series([22.0] * len(out))).fillna(22.0).astype(float)
    out["player_deflection_rate"] = (0.04 + mins / 2000.0).clip(0.02, 0.12)
    out["player_steal_rate_per_min"] = (0.02 + mins / 3000.0).clip(0.01, 0.08)
    out["player_block_rate_per_min"] = (0.015 + mins / 3500.0).clip(0.005, 0.08)
    out["player_contested_shot_rate"] = (0.06 + mins / 1800.0).clip(0.03, 0.2)
    role_series = out["role_bucket"] if "role_bucket" in out.columns else pd.Series(["rotation"] * len(out), index=out.index)
    out["player_rim_protection_role"] = role_series.astype(str).str.contains("big", case=False, na=False)
    out["opponent_turnover_rate"] = 0.135
    out["opponent_bad_pass_rate"] = 0.08
    out["opponent_drive_rate"] = 0.34
    out["opponent_blockable_attempts"] = 14.0
    out["expected_defensive_possessions"] = mins * 2.1
    out["expected_steal_opportunities"] = out["expected_defensive_possessions"] * out["opponent_turnover_rate"]
    out["expected_block_opportunities"] = out["expected_defensive_possessions"] * 0.05
    out["sparse_p0_prior"] = 0.62
    out["sparse_positive_tail_prior"] = 0.18
    return out
