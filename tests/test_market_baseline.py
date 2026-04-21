"""PHASE 5 guardrails — de-vigged market baseline must produce valid PMFs."""
from __future__ import annotations

import numpy as np
import pytest

from nba_props_model.evaluation.market_baseline import (
    AltQuote,
    american_to_implied,
    devigged_main_line,
    market_implied_cdf_from_alt_lines,
    market_pmf_from_cdf,
    market_over_prob_at_line,
)


def test_american_to_implied_known_values():
    assert american_to_implied(-110) == pytest.approx(0.5238, abs=1e-3)
    assert american_to_implied(+100) == pytest.approx(0.5000, abs=1e-4)
    assert american_to_implied(+200) == pytest.approx(0.3333, abs=1e-3)


def test_devig_pair_sums_to_one_and_removes_vig():
    p_over, p_under = devigged_main_line(-110, -110)
    assert p_over == pytest.approx(0.5, abs=1e-6)
    assert p_under == pytest.approx(0.5, abs=1e-6)
    assert (p_over + p_under) == pytest.approx(1.0, abs=1e-9)
    # Asymmetric vig: still sums to 1.
    p_over, p_under = devigged_main_line(-150, +130)
    assert (p_over + p_under) == pytest.approx(1.0, abs=1e-9)


def test_over_prob_at_line_monotone_with_better_odds():
    """Longer payout on over should imply lower fair P(over)."""
    p_long  = market_over_prob_at_line(+200, -250)  # over is longshot
    p_short = market_over_prob_at_line(-250, +200)  # over is favorite
    assert p_long < p_short


def test_alt_line_ladder_produces_valid_monotone_cdf():
    quotes = [
        AltQuote(line=9.5,  over_odds=-250, under_odds=+210),
        AltQuote(line=14.5, over_odds=-150, under_odds=+130),
        AltQuote(line=19.5, over_odds=+100, under_odds=-120),
        AltQuote(line=24.5, over_odds=+180, under_odds=-210),
        AltQuote(line=29.5, over_odds=+350, under_odds=-450),
    ]
    cdf = market_implied_cdf_from_alt_lines(quotes, support_max=60)
    assert cdf is not None
    assert len(cdf) == 61
    # Monotone non-decreasing.
    assert np.all(np.diff(cdf) >= -1e-9)
    # Bounded [0, 1].
    assert cdf.min() >= 0.0 - 1e-9
    assert cdf.max() <= 1.0 + 1e-9
    assert cdf[-1] == pytest.approx(1.0, abs=1e-6)


def test_alt_line_ladder_returns_none_when_too_few_quotes():
    assert market_implied_cdf_from_alt_lines([], support_max=50) is None
    assert market_implied_cdf_from_alt_lines(
        [AltQuote(line=12.5, over_odds=-110, under_odds=-110)], support_max=50
    ) is None


def test_market_pmf_from_cdf_sums_to_one_nonnegative():
    quotes = [
        AltQuote(line=9.5,  over_odds=-250, under_odds=+210),
        AltQuote(line=14.5, over_odds=-150, under_odds=+130),
        AltQuote(line=19.5, over_odds=+100, under_odds=-120),
        AltQuote(line=24.5, over_odds=+180, under_odds=-210),
        AltQuote(line=29.5, over_odds=+350, under_odds=-450),
    ]
    cdf = market_implied_cdf_from_alt_lines(quotes, support_max=60)
    pmf = market_pmf_from_cdf(cdf)
    assert (pmf >= 0).all()
    assert pmf.sum() == pytest.approx(1.0, abs=1e-6)
