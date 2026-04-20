"""Contract tests for the canonical minutes artifact.

The training pipeline logs minutes_result['mae_q50'], ['max_cal_error'], and
['coverage_50pct']. Any reshape of the trainer return value must preserve
these keys — their absence was the observed WARNING source 'mae_q50'.
"""
from __future__ import annotations

from nba_props_model.models import minutes as minutes_mod


def test_trainer_emits_contract_keys_in_return_dict(monkeypatch, tmp_path):
    """The trainer must always populate the canonical contract keys, even when
    the internal conditional-quantile fit short-circuits on small data. Use a
    tiny synthetic frame that exercises the return path."""
    import numpy as np
    import pandas as pd

    monkeypatch.setattr(minutes_mod, "MODEL_DIR", tmp_path)

    n_players = 40
    rows = []
    rng = np.random.default_rng(0)
    for pid in range(n_players):
        for day in range(30):
            mins = float(max(0.0, rng.normal(28, 6)))
            rows.append({
                "player_id": pid,
                "game_id": pid * 1000 + day,
                "game_date": pd.Timestamp("2024-10-01") + pd.Timedelta(days=day),
                "min": mins,
                "team_id": 1,
                "home_team_id": 1,
            })
    stats = pd.DataFrame(rows)

    meta = minutes_mod.train_state_aware_minutes_model(stats_df=stats, availability_df=None)
    assert meta, "trainer returned empty dict"
    for key in ("mae_q50", "max_cal_error", "coverage_50pct"):
        assert key in meta, f"trainer meta missing contract key {key!r}"
