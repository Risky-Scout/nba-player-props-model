"""Role-state feature engineering for M8.9."""
from __future__ import annotations

import pandas as pd
import numpy as np


def build_role_state_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    minutes = out.get("projected_minutes", pd.Series([24.0] * len(out))).fillna(24.0).astype(float)
    out["p_inactive"] = (1.0 - out.get("prob_active_current", pd.Series([0.8] * len(out))).fillna(0.8)).clip(0.0, 1.0)
    p_starter = (minutes / 36.0).clip(0.05, 0.9)
    p_core = (minutes / 40.0).clip(0.05, 0.7)
    p_rotation = (minutes / 30.0).clip(0.1, 0.9)
    p_bench = (1.0 - p_starter).clip(0.05, 0.95)
    p_fringe = (1.0 - p_rotation).clip(0.05, 0.95)
    total = p_starter + p_core + p_rotation + p_bench + p_fringe + out["p_inactive"]
    out["p_starter"] = p_starter / total
    out["p_core"] = p_core / total
    out["p_rotation"] = p_rotation / total
    out["p_bench"] = p_bench / total
    out["p_fringe"] = p_fringe / total
    out["p_inactive"] = out["p_inactive"] / total
    probs = out[["p_inactive", "p_fringe", "p_bench", "p_rotation", "p_core", "p_starter"]].clip(lower=1e-9)
    out["role_entropy"] = -(probs * np.log(probs)).sum(axis=1)
    out["role_bucket_confidence"] = out[["p_starter", "p_core", "p_rotation", "p_bench", "p_fringe", "p_inactive"]].max(axis=1)
    out["role_change_probability"] = (1.0 - out["role_bucket_confidence"]).clip(0.0, 1.0)
    out["role_source"] = "role_state_model_v1"
    out["role_source_asof_utc"] = out.get("source_data_asof_utc", pd.NA)
    out["hard_role_bucket"] = out.get("role_bucket", "rotation")
    out["role_mixture_enabled"] = True
    return out
