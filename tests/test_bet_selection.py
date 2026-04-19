"""Tests for the bet-selection layer."""
from __future__ import annotations

import pytest

from nba_props_model.selection.bet_selection import (
    BetCandidate,
    PortfolioConstraints,
    SelectionDecision,
    SelectionThresholds,
    american_to_decimal,
    american_to_implied_prob,
    decide,
    decide_many,
    decimal_to_american,
    devig_pair,
    enforce_portfolio,
    ev_from_model_prob,
    fair_odds_from_prob,
    kelly_fraction,
)


def test_american_decimal_roundtrip():
    for odds in (-220, -150, -110, +100, +135, +300):
        dec = american_to_decimal(odds)
        back = decimal_to_american(dec)
        assert abs(back - odds) <= 1  # rounding tolerance


def test_implied_prob_pair_equals_1_plus_vig():
    po = american_to_implied_prob(-110)
    pu = american_to_implied_prob(-110)
    assert 1.04 < po + pu < 1.10   # classic ~4.8% vig


def test_devig_pair_sums_to_one():
    over, under = devig_pair(-110, -110)
    assert abs(over + under - 1.0) < 1e-9
    assert 0.49 < over < 0.51


def test_ev_positive_when_model_above_break_even():
    # -110 break-even is 52.38%. At 58% model prob EV should be positive.
    assert ev_from_model_prob(0.58, -110) > 0.05


def test_ev_negative_when_model_below_break_even():
    assert ev_from_model_prob(0.48, -110) < 0


def test_kelly_zero_when_no_edge():
    # Break-even at -110 is ~52.38%; Kelly at 52% prob is close to zero.
    assert kelly_fraction(0.52, -110) < 0.02
    assert kelly_fraction(0.5, -110) == 0.0


def test_fair_odds_from_prob_reflects_probability():
    assert fair_odds_from_prob(0.5) == 100
    assert fair_odds_from_prob(0.6) == -150  # 1/0.6 = 1.667 -> -150
    assert fair_odds_from_prob(0.4) == 150


def _candidate(**over) -> BetCandidate:
    defaults = dict(
        player_name="Test Player", player_id=1,
        stat="pts", side="OVER", offered_line=18.5,
        offered_american=-110, paired_american=-110,
        model_prob=0.58, books_available=3,
    )
    defaults.update(over)
    return BetCandidate(**defaults)


def test_decide_accepts_high_edge_bet():
    d = decide(_candidate(model_prob=0.60, offered_american=+100, paired_american=-120))
    assert d.selected
    assert d.reject_reason is None
    assert d.edge > 0.02
    assert d.ev > 0.025


def test_decide_rejects_sparse_stat_below_floor():
    # stl at 0.48 model prob: below sparse floor (0.52) → rejected.
    d = decide(_candidate(stat="stl", model_prob=0.48))
    assert not d.selected
    assert d.reject_reason == "ev_below_threshold" or d.reject_reason == "sparse_stat_probability_floor"


def test_decide_rejects_negative_edge():
    d = decide(_candidate(model_prob=0.40))
    assert not d.selected
    assert d.reject_reason is not None


def test_decide_respects_book_liquidity():
    d = decide(_candidate(books_available=0),
               SelectionThresholds(min_books=2))
    assert not d.selected
    assert d.reject_reason in ("ev_below_threshold", "insufficient_books")


def test_decide_rejects_large_disagreement():
    # Model 90%, market devigs to 55% -> disagreement 35% exceeds cap 25%.
    d = decide(_candidate(model_prob=0.90, offered_american=-110, paired_american=-110))
    assert not d.selected
    assert d.reject_reason == "model_market_disagreement_too_large"


def test_decide_many_returns_same_length():
    cands = [_candidate(model_prob=p) for p in (0.3, 0.55, 0.6, 0.7, 0.9)]
    decisions = decide_many(cands)
    assert len(decisions) == len(cands)


def test_enforce_portfolio_caps_player_and_day():
    # 5 high-edge bets on 3 players, day cap = 4, per-player cap = 1.
    cands = [
        _candidate(player_id=1, model_prob=0.60, offered_american=+100, paired_american=-120),
        _candidate(player_id=1, model_prob=0.60, offered_american=+100, paired_american=-120),
        _candidate(player_id=2, model_prob=0.60, offered_american=+100, paired_american=-120),
        _candidate(player_id=3, model_prob=0.60, offered_american=+100, paired_american=-120),
        _candidate(player_id=4, model_prob=0.60, offered_american=+100, paired_american=-120),
    ]
    decisions = decide_many(cands)
    def game_key(b: BetCandidate) -> str:
        return "GAME_A"
    out = enforce_portfolio(
        decisions, game_key_fn=game_key,
        constraints=PortfolioConstraints(
            max_singles_per_day=3, max_singles_per_player=1, max_singles_per_game=10,
        ),
    )
    sel = [d for d in out if d.selected]
    assert len(sel) == 3
    # No duplicate player.
    assert len({d.bet.player_id for d in sel}) == len(sel)
