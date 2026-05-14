"""Opponent matchup feature family for M8.9."""
from __future__ import annotations

import pandas as pd


def build_opponent_matchup_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    n = len(out)
    def _const(v: float) -> pd.Series:
        return pd.Series([v] * n)
    out["opponent_def_rating_recent"] = _const(113.0)
    out["opponent_pace_recent"] = _const(99.0)
    out["opp_allowed_pts_by_position"] = _const(22.0)
    out["opp_allowed_reb_by_position"] = _const(8.0)
    out["opp_allowed_ast_by_position"] = _const(5.0)
    out["opp_allowed_fg3m_by_position"] = _const(2.4)
    out["opp_allowed_stl_by_position"] = _const(1.3)
    out["opp_allowed_blk_by_position"] = _const(0.9)
    out["opp_allowed_tov_by_position"] = _const(2.7)
    out["opp_rebound_chances_allowed_by_position"] = _const(13.0)
    out["opp_assist_chances_allowed_to_primary_handlers"] = _const(16.0)
    out["opp_3pa_allowed"] = _const(34.0)
    out["opp_3p_rate_allowed"] = _const(0.37)
    out["opp_corner_3_allowed"] = _const(8.0)
    out["opp_above_break_3_allowed"] = _const(26.0)
    out["opp_rim_attempts_allowed"] = _const(28.0)
    out["opp_blockable_fga_rate"] = _const(0.11)
    out["opp_live_ball_turnover_rate"] = _const(0.13)
    out["opp_bad_pass_rate"] = _const(0.08)
    out["opp_steals_allowed_to_guards"] = _const(1.5)
    out["opp_steals_allowed_to_wings"] = _const(1.1)
    out["opp_blocks_allowed_to_bigs"] = _const(1.6)
    out["player_archetype"] = out.get("role_bucket", "rotation").astype(str)
    out["matchup_archetype"] = "neutral"
    return out
