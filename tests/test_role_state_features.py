import pandas as pd

from nba_props_model.features.role_state_features import build_role_state_features


def test_role_state_probabilities_exist():
    df = pd.DataFrame({"projected_minutes": [30.0, 18.0], "prob_active_current": [0.95, 0.7]})
    out = build_role_state_features(df)
    for c in ["p_inactive", "p_fringe", "p_bench", "p_rotation", "p_core", "p_starter", "role_entropy"]:
        assert c in out.columns
