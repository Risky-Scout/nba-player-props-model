import pandas as pd

from nba_props_model.features.combo_covariance_features import build_combo_covariance_features


def test_combo_covariance_columns():
    df = pd.DataFrame({"projected_minutes": [28.0], "usage_projection": [0.25]})
    out = build_combo_covariance_features(df)
    assert "cov_pts_reb_player" in out.columns
    assert "combo_covariance_shrinkage_weight" in out.columns
