"""Combo covariance features for PA/PR/RA/PRA."""
from __future__ import annotations

import pandas as pd


def build_combo_covariance_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    mins = out.get("projected_minutes", pd.Series([24.0] * len(out))).fillna(24.0).astype(float)
    usage = out.get("usage_projection", pd.Series([0.22] * len(out))).fillna(0.22).astype(float)
    out["cov_pts_reb_player"] = 0.8 + 0.02 * mins
    out["cov_pts_ast_player"] = 0.7 + 0.015 * mins + 2.0 * usage
    out["cov_reb_ast_player"] = 0.35 + 0.01 * mins
    out["cov_pts_reb_role"] = 0.75 + 0.01 * mins
    out["cov_pts_ast_role"] = 0.65 + 0.01 * mins
    out["cov_reb_ast_role"] = 0.3 + 0.008 * mins
    out["cov_pts_reb_minutes_conditioned"] = out["cov_pts_reb_player"] * (mins / 30.0)
    out["cov_pts_ast_usage_conditioned"] = out["cov_pts_ast_player"] * (usage / 0.25)
    out["cov_reb_ast_lineup_conditioned"] = out["cov_reb_ast_player"] * 1.0
    out["combo_covariance_sample_size"] = 120
    out["combo_covariance_shrinkage_weight"] = 0.7
    out["combo_independence_warning_flag"] = out["combo_covariance_sample_size"] < 30
    return out
