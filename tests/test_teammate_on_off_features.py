import pandas as pd

from nba_props_model.features.teammate_on_off_features import build_teammate_on_off_features


def test_teammate_on_off_columns():
    df = pd.DataFrame({"num_teammates_out_total": [0, 2], "projected_minutes": [24.0, 32.0]})
    out = build_teammate_on_off_features(df)
    assert "usage_with_top_usage_teammates_off" in out.columns
    assert "on_off_sample_size" in out.columns
