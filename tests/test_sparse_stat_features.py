import pandas as pd

from nba_props_model.features.sparse_stat_features import build_sparse_stat_features


def test_sparse_stat_columns():
    df = pd.DataFrame({"projected_minutes": [22.0]})
    out = build_sparse_stat_features(df)
    assert "expected_steal_opportunities" in out.columns
    assert "sparse_positive_tail_prior" in out.columns
