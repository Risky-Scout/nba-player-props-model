from nba_props_model.features.player_prop_feature_contract import (
    FEATURE_CONTRACT_VERSION,
    LeakageStatus,
    assert_feature_contract_coherent,
    explicit_unavailable_statuses,
    feature_families,
    forbidden_model_only_training_features,
    model_only_feature_names,
)


def test_feature_contract_version_present():
    assert FEATURE_CONTRACT_VERSION


def test_feature_contract_contains_many_families():
    families = feature_families()
    assert len(families) >= 15


def test_market_family_is_residual_only():
    families = {f.name: f for f in feature_families()}
    market = families["market_residual_only"]
    assert market.leakage_status == LeakageStatus.MARKET_RESIDUAL_ONLY


def test_forbidden_market_columns_not_in_model_only():
    model_only = set(model_only_feature_names())
    forbidden = set(forbidden_model_only_training_features())
    assert model_only.isdisjoint(forbidden)


def test_explicit_unavailable_status_tokens():
    statuses = explicit_unavailable_statuses()
    assert "not_available_yet" in statuses
    assert "source_unavailable" in statuses


def test_feature_contract_coherent():
    assert_feature_contract_coherent()
