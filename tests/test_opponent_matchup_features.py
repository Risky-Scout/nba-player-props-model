import pandas as pd

from nba_props_model.features.opponent_matchup_features import build_opponent_matchup_features


def test_opponent_matchup_columns():
    df = pd.DataFrame({"role_bucket": ["guard"]})
    out = build_opponent_matchup_features(df)
    assert "opp_allowed_pts_by_position" in out.columns
    assert "matchup_archetype" in out.columns
