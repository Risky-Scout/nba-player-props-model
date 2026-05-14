from pathlib import Path

from nba_props_model.features.injury_lineup_features import build_injury_lineup_features
from nba_props_model.features.player_prop_feature_contract import RunMode


REPO = Path(__file__).resolve().parents[1]


def test_injury_lineup_features_morning_mode():
    result = build_injury_lineup_features(REPO, "2026-05-12", RunMode.MORNING_EXPECTED)
    assert "expected_starter_prob" in result.frame.columns
    assert "official_lineup_status" in result.frame.columns
    assert (result.frame["official_lineup_status"] == "not_available_yet").all()


def test_injury_lineup_features_t25_mode():
    result = build_injury_lineup_features(REPO, "2026-05-12", RunMode.T25)
    assert "stale_lineup_flag" in result.frame.columns
    assert "unavailable_reason" in result.frame.columns
