"""
NBA Props Model — bet-selection layer.

Cleanly separated from the model layer, as required by the architecture.
The model layer (pipelines/predict.py) produces, for every (player, stat,
offered line) in the full universe:
  * a calibrated PMF / CDF
  * a model fair over/under probability
  * model uncertainty metrics
  * model-version metadata

This module consumes those outputs plus market prices and returns the
subset of plays to bet. It never mutates the model probabilities;
abstention-filter decisions are enforced on selection only, so downstream
diagnostics can continue to score the full universe.

Filters applied, in order
-------------------------
  1. minimum edge threshold (default 2.5%)
  2. minimum model probability floor (sparse-stat transitional guard)
  3. liquidity / book availability gate
  4. hold / vig filter (skip markets with > 8% implied vig)
  5. stability filter (model vs market gap implausibly large → skip)
  6. sparse-stat transitional restriction (during rebuild window)

Each filter explains why it rejected a candidate so the diagnostics
layer can report the abstention breakdown.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ── Price conversions ───────────────────────────────────────────────────────


def american_to_decimal(odds: int | float) -> float:
    o = float(odds)
    if o > 0:
        return 1.0 + o / 100.0
    return 1.0 + 100.0 / abs(o)


def american_to_implied_prob(odds: int | float) -> float:
    o = float(odds)
    if o > 0:
        return 100.0 / (o + 100.0)
    return abs(o) / (abs(o) + 100.0)


def decimal_to_american(decimal: float) -> int:
    d = float(decimal)
    if d <= 1.0:
        return -100_000
    if d >= 2.0:
        return int(round(100.0 * (d - 1.0)))
    return int(round(-100.0 / (d - 1.0)))


def devig_pair(over_american: int | float, under_american: int | float) -> tuple[float, float]:
    po = american_to_implied_prob(over_american)
    pu = american_to_implied_prob(under_american)
    s = max(po + pu, 1e-9)
    return float(po / s), float(pu / s)


def fair_odds_from_prob(prob: float) -> int:
    prob = float(np.clip(prob, 1e-6, 1 - 1e-6))
    decimal = 1.0 / prob
    return decimal_to_american(decimal)


# ── EV + Kelly ──────────────────────────────────────────────────────────────


def ev_from_model_prob(
    model_prob: float, offered_american: int | float,
) -> float:
    """Expected value per unit stake at the offered American odds."""
    decimal = american_to_decimal(offered_american)
    return float(model_prob * (decimal - 1.0) - (1.0 - model_prob))


def kelly_fraction(model_prob: float, offered_american: int | float) -> float:
    p = float(np.clip(model_prob, 0.0, 1.0))
    decimal = american_to_decimal(offered_american)
    b = decimal - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - p
    k = (b * p - q) / b
    return float(max(0.0, k))


# ── Selection ───────────────────────────────────────────────────────────────


@dataclass
class SelectionThresholds:
    min_edge: float = 0.025          # 2.5% EV floor
    min_model_prob: float = 0.45     # reject flips
    max_market_vig: float = 0.08     # skip >8% vig markets
    max_disagreement: float = 0.25   # reject if |model - devig| > 0.25
    kelly_fraction: float = 0.15     # 15% Kelly
    max_kelly_units: float = 1.5     # hard cap per single
    min_books: int = 1
    sparse_stat_probability_floor: dict = field(default_factory=lambda: {
        "stl": 0.52,  # transitional — tighten during rebuild
        "blk": 0.52,
        "stocks": 0.52,
    })


@dataclass
class BetCandidate:
    player_name: str
    player_id: int
    stat: str
    side: str                  # 'OVER' or 'UNDER'
    offered_line: float
    offered_american: int
    paired_american: Optional[int]
    model_prob: float
    books_available: int
    calibrator_version: str = "pmf_v1"
    closing_fair_prob: Optional[float] = None


@dataclass
class SelectionDecision:
    bet: BetCandidate
    selected: bool
    reject_reason: Optional[str]
    edge: float
    ev: float
    kelly_stake: float
    fair_american: int
    devigged_market_prob: Optional[float]

    def as_dict(self) -> dict:
        out = asdict(self)
        out["bet"] = asdict(self.bet)
        return out


def decide(
    bet: BetCandidate, thresholds: Optional[SelectionThresholds] = None,
) -> SelectionDecision:
    """Run filters against a single candidate. Returns a decision with
    reject_reason set when filtered out."""
    t = thresholds or SelectionThresholds()

    devigged = None
    if bet.paired_american is not None:
        over_fair, under_fair = devig_pair(bet.offered_american, bet.paired_american)
        market_fair = over_fair if bet.side == "OVER" else under_fair
        devigged = float(market_fair)

    edge = float(bet.model_prob - (devigged if devigged is not None
                                   else american_to_implied_prob(bet.offered_american)))
    ev = ev_from_model_prob(bet.model_prob, bet.offered_american)
    kelly = min(t.max_kelly_units,
                kelly_fraction(bet.model_prob, bet.offered_american) * t.kelly_fraction
                * t.max_kelly_units / max(t.kelly_fraction, 1e-6))
    # Normalized Kelly stake in units: Kelly fraction * bankroll (1 unit budget).
    raw_kelly = kelly_fraction(bet.model_prob, bet.offered_american)
    stake = min(t.max_kelly_units, raw_kelly * t.kelly_fraction * 10.0)

    fair_american = fair_odds_from_prob(bet.model_prob)
    decision = SelectionDecision(
        bet=bet, selected=False, reject_reason=None,
        edge=edge, ev=ev, kelly_stake=stake,
        fair_american=fair_american, devigged_market_prob=devigged,
    )

    # Filter 1: edge threshold
    if ev < t.min_edge:
        decision.reject_reason = "ev_below_threshold"
        return decision
    # Filter 2: sparse-stat probability floor
    if bet.stat in t.sparse_stat_probability_floor:
        if bet.model_prob < t.sparse_stat_probability_floor[bet.stat]:
            decision.reject_reason = "sparse_stat_probability_floor"
            return decision
    # Filter 3: probability floor
    if bet.model_prob < t.min_model_prob:
        decision.reject_reason = "model_prob_below_floor"
        return decision
    # Filter 4: liquidity
    if bet.books_available < t.min_books:
        decision.reject_reason = "insufficient_books"
        return decision
    # Filter 5: vig too high
    if bet.paired_american is not None:
        vig = (american_to_implied_prob(bet.offered_american)
               + american_to_implied_prob(bet.paired_american) - 1.0)
        if vig > t.max_market_vig:
            decision.reject_reason = "market_vig_too_high"
            return decision
    # Filter 6: disagreement too large
    if devigged is not None and abs(bet.model_prob - devigged) > t.max_disagreement:
        decision.reject_reason = "model_market_disagreement_too_large"
        return decision

    decision.selected = True
    return decision


def decide_many(
    bets: list[BetCandidate],
    thresholds: Optional[SelectionThresholds] = None,
) -> list[SelectionDecision]:
    return [decide(b, thresholds) for b in bets]


# ── Portfolio constraints (applied after per-bet filtering) ─────────────────


@dataclass
class PortfolioConstraints:
    max_singles_per_day: int = 25
    max_singles_per_player: int = 2
    max_singles_per_game: int = 4


def enforce_portfolio(
    decisions: list[SelectionDecision],
    game_key_fn,
    constraints: Optional[PortfolioConstraints] = None,
) -> list[SelectionDecision]:
    """Apply day / player / game caps to an already-filtered decision list.

    Accepts only decisions marked selected=True; returns the same list with
    some decisions flipped to selected=False + reject_reason="portfolio_cap".
    """
    c = constraints or PortfolioConstraints()
    accepted: list[SelectionDecision] = []
    per_player: dict[int, int] = {}
    per_game: dict[str, int] = {}

    # Rank by edge descending so the best bets keep slots under the caps.
    ranked = sorted(decisions, key=lambda d: (-d.edge, -d.ev))
    for d in ranked:
        if not d.selected:
            continue
        pid = d.bet.player_id
        gkey = game_key_fn(d.bet)
        if len(accepted) >= c.max_singles_per_day:
            d.selected = False
            d.reject_reason = "portfolio_cap_day"
            continue
        if per_player.get(pid, 0) >= c.max_singles_per_player:
            d.selected = False
            d.reject_reason = "portfolio_cap_player"
            continue
        if per_game.get(gkey, 0) >= c.max_singles_per_game:
            d.selected = False
            d.reject_reason = "portfolio_cap_game"
            continue
        accepted.append(d)
        per_player[pid] = per_player.get(pid, 0) + 1
        per_game[gkey] = per_game.get(gkey, 0) + 1

    # Rebuild in original order but with updated flags.
    return decisions
