"""Teammate on/off and vacated opportunity features for M8.9."""
from __future__ import annotations

import pandas as pd


def build_teammate_on_off_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out_count = out.get("num_teammates_out_total", pd.Series([0] * len(out))).fillna(0).astype(float)
    mins = out.get("projected_minutes", pd.Series([24.0] * len(out))).fillna(24.0).astype(float)
    baseline_usage = (mins / 36.0).clip(0.1, 0.95)
    out["usage_with_top_usage_teammates_off"] = baseline_usage + 0.02 * out_count
    out["fga_with_top_usage_teammates_off"] = 8.0 + 0.6 * mins / 10.0 + 0.8 * out_count
    out["ast_rate_with_primary_ballhandler_off"] = 0.08 + 0.01 * out_count
    out["reb_rate_with_starting_center_off"] = 0.1 + 0.01 * out_count
    out["fg3a_rate_with_spacing_lineup"] = 0.12 + 0.005 * out_count
    out["points_per_min_with_high_usage_teammate_off"] = 0.5 + 0.03 * out_count
    out["assist_chances_with_starting_pg_out"] = 20 + 2 * out_count
    out["rebound_chances_with_starting_center_out"] = 8 + 1.5 * out_count
    out["minutes_with_current_projected_lineup"] = mins * (0.7 + 0.03 * out_count).clip(0.2, 1.1)
    out["possessions_with_current_projected_lineup"] = out["minutes_with_current_projected_lineup"] * 2.0
    out["on_off_sample_size"] = 20 + 5 * out_count
    out["on_off_shrinkage_weight"] = (out["on_off_sample_size"] / (out["on_off_sample_size"] + 50)).clip(0.05, 0.9)
    return out
