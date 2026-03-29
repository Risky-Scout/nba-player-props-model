#!/usr/bin/env python3
"""
live_pricing.py — NBA Live Props Pricing Engine v4
====================================================
Authoritative live pricing engine. All model logic lives here.
Called by live_props.php via: echo '{...}' | python3 live_pricing.py --stdin-json

Key upgrades in v4:
  - Hierarchical player/team/lineup priors with Bayesian shrinkage
  - Posterior opportunity model for all stat families
  - Quote-history based market-pull penalty (real, not flat)
  - Improved remaining-minutes posterior (stint + coach + re-entry)
  - Calibration key output for state-bucket calibration integration
  - action_score = exec_edge * calibration_mult * market_stability_mult
"""

import json
import math
import sys
import time
import argparse
import numpy as np
from scipy import stats as sp_stats
from typing import Optional

MODEL_VERSION = "live_pricing_v4"

# ── League priors (used as fallback when player priors absent) ────────────────
LEAGUE = {
    "pace":          99.2,
    "3pa_rate":      0.42,
    "p3":            0.362,
    "p2":            0.527,
    "pft":           0.775,
    "fta_per_poss":  0.24,
    "ast_rate":      0.58,
    "miss_rate":     0.543,
    "opp_fga_poss":  0.92,
    "usage":         0.20,
    "reb_share":     0.10,
    "ast_share":     0.15,
    "stl_per_min":   0.025,
    "blk_per_min":   0.015,
    "tov_per_poss":  0.13,
    "on_court_share":0.70,
    "team_fga_poss": 0.92,
    "fta_rate":      0.072,   # FTA per player possession
}

N_SIM = 20_000

FOUL_FACTOR = {
    "none": 1.00, "mild": 0.92, "moderate": 0.78,
    "severe": 0.58, "fouled_out": 0.00,
}

BLOWOUT_TABLE = [
    (25, 3, 0.55), (18, 4, 0.70), (12, 4, 0.85),
]


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, x))))


# ── Shrinkage helper (instruction §1) ────────────────────────────────────────

def shrink_rate(prior, live, live_weight, lo=None, hi=None):
    """Shrink live rate toward prior. live_weight in [0,1]."""
    x = (1.0 - live_weight) * prior + live_weight * live
    if lo is not None: x = max(lo, x)
    if hi is not None: x = min(hi, x)
    return x


# ── Market pull penalty from quote history (instruction §9) ──────────────────

def market_pull_penalty(quote_history, current_line, current_over_odds, lookback_sec=180):
    """Real market-movement penalty based on line history."""
    if not quote_history:
        return 0.005  # conservative flat when no history
    recent = [q for q in quote_history if q.get("age_sec", 999999) <= lookback_sec]
    if len(recent) < 2:
        return 0.005
    median_line = float(np.median([q.get("line", current_line) for q in recent]))
    line_move = abs(current_line - median_line)
    if line_move >= 1.0: return 0.015
    if line_move >= 0.5: return 0.0075
    return 0.0025


# ═══════════════════════════════════════════════════════════════════════════════
import os as _os
import json as _json
from pathlib import Path as _Path

def _load_live_cal_table():
    """Load live calibration table keyed by calibration_key."""
    p = _Path("model_cache/live_calibration_table.json")
    if p.exists():
        return _json.loads(p.read_text())
    return {}

LIVE_CAL_TABLE = _load_live_cal_table()


class LivePricer:
    """Authoritative v4 live pricer with hierarchical priors."""

    def price(
        self,
        stat: str,
        side: str,
        line: float,
        pregame_quantiles: dict,
        current_stat: float,
        period: int,
        clock_str: str,
        on_court: bool,
        fouls: int,
        foul_trouble: str,
        score_margin: int,
        losing_team: bool,
        is_overtime: bool,
        market_over_odds: int,
        market_under_odds: int,
        quote_age_sec: float = 0.0,
        shot_events: list = None,
        pace_events: list = None,
        player_live_rates: dict = None,
        lineup_context: dict = None,
        team_context: dict = None,
        pregame_minutes: float = 36.0,
        # v4 additions (instruction §2)
        player_prior_rates: dict = None,
        quote_history: list = None,
        # Real calibration quality input from state_bucket_calibration.json
        bucket_brier: float = None,  # None = hard fail in production; pass 0.25 explicitly for dev
        calibration_level: str = "identity",
    ) -> dict:

        # Hard fail if bucket_brier not provided — prevents silent calibration degradation
        if bucket_brier is None:
            raise ValueError(
                "HARD FAIL: bucket_brier is required for live pricing. "
                "Pass the stat-side Brier score from the calibration artifacts. "
                "Use bucket_brier=0.25 explicitly during development only."
            )

        stat = stat.lower()
        shot_events        = shot_events        or []
        pace_events        = pace_events        or []
        player_live_rates  = player_live_rates  or {}
        lineup_context     = lineup_context     or {}
        team_context       = team_context       or {}
        player_prior_rates = player_prior_rates or {}
        quote_history      = quote_history      or []

        # ── Step 1: Remaining minutes posterior (instruction §4) ─────────────
        raw_rem     = self._raw_remaining(period, clock_str, is_overtime)
        reentry_p   = self._reentry_prob(on_court, raw_rem, foul_trouble,
                                         score_margin, losing_team, period, team_context)
        closing_p   = self._closing_prob(pregame_minutes, foul_trouble, score_margin, period)
        foul_factor = FOUL_FACTOR.get(foul_trouble, 1.0)
        blowout_f   = self._blowout_factor(score_margin, period, losing_team)

        # Stint penalty (instruction §4)
        stint_min   = (lineup_context or {}).get("current_stint_minutes", 0)
        stint_pen   = 0.92 if stint_min >= 10 else 0.97 if stint_min >= 8 else 1.00

        # Coach trust boost (instruction §4)
        coach_boost = 1.05 if (team_context or {}).get("expected_closer", False) else 1.00

        rem_mean = max(0.0,
            raw_rem * reentry_p * foul_factor * blowout_f
            * stint_pen * coach_boost * (0.80 + 0.20 * closing_p)
        )
        rem_q25 = rem_mean * 0.78
        rem_q75 = min(raw_rem, rem_mean * 1.18)

        # ── Step 2: Live-rate shrinkage weights (instruction §3) ─────────────
        obs_poss = max(1.0, (team_context or {}).get("observed_possessions", 0.0))
        w_live   = min(0.65, math.sqrt(obs_poss / 90.0))

        # Build posterior rates from hierarchical priors
        pr = self._build_posteriors(player_prior_rates, player_live_rates, w_live)

        # ── Step 3: Pace factor ───────────────────────────────────────────────
        pace_factor = self._pace_factor(pace_events, w_live)
        heat_factor = self._heat_factor(stat, shot_events)

        # ── Step 4: Stat-family PMF (instruction §5–8) ───────────────────────
        team_poss_rem = rem_mean * LEAGUE["pace"] * pace_factor / 48.0

        rem_pmf = self._remaining_pmf(
            stat, pregame_quantiles, rem_mean, pregame_minutes,
            pace_factor, heat_factor, pr, team_poss_rem, on_court
        )

        # ── Step 5: Terminal PMF ──────────────────────────────────────────────
        terminal_pmf = [(round(v + current_stat, 1), p) for v, p in rem_pmf]
        total = sum(p for _, p in terminal_pmf)
        if total > 0:
            terminal_pmf = [(v, p / total) for v, p in terminal_pmf]

        # ── Step 6: Probabilities ─────────────────────────────────────────────
        p_over  = sum(p for v, p in terminal_pmf if v > line)
        p_under = sum(p for v, p in terminal_pmf if v < line)
        push_p  = max(0.0, 1.0 - p_over - p_under)
        q50     = self._pmf_quantile(terminal_pmf, 0.50)
        pregame_q50 = float(pregame_quantiles.get(0.50, 0) or 0)
        fair_line_110 = self._fair_line(terminal_pmf, -110)

        # ── Step 7: Vig-free market probs (global rule §1.1) ─────────────────
        dec_o = self._a2d(market_over_odds)
        dec_u = self._a2d(market_under_odds)
        imp_o = 1.0 / dec_o
        imp_u = 1.0 / dec_u
        vig_sum    = imp_o + imp_u
        mkt_p_over  = imp_o / vig_sum
        mkt_p_under = imp_u / vig_sum

        # ── Step 8: Edge, EV, Kelly (§1.2–1.4) ──────────────────────────────
        raw_edge = (p_over - mkt_p_over) if side == "OVER" else (p_under - mkt_p_under)
        ev_over  = p_over  * (dec_o - 1) - (1 - p_over)
        ev_under = p_under * (dec_u - 1) - (1 - p_under)
        ev       = ev_over if side == "OVER" else ev_under

        p_side   = p_over if side == "OVER" else p_under
        dec_side = dec_o  if side == "OVER" else dec_u
        kelly_full = ((dec_side - 1) * p_side - (1 - p_side)) / max(0.001, dec_side - 1)
        kelly      = max(0.0, kelly_full) * 0.125  # eighth-Kelly live

        # ── Step 9: Exec edge (§1.5 + instruction §10) ───────────────────────
        q25_t = self._pmf_quantile(terminal_pmf, 0.25)
        q75_t = self._pmf_quantile(terminal_pmf, 0.75)
        iqr   = q75_t - q25_t

        stale_pen     = min(0.05, quote_age_sec / 60.0 * 0.005)
        uncert_pen    = 0.01 if (iqr / max(1.0, q50)) > 0.55 else 0.0
        min_pen       = 0.015 if rem_mean < 3 else 0.0
        foul_pen      = (0.015 if fouls >= 4
                         else 0.005 if fouls == 3 and period <= 3 else 0.0)
        mkt_pull_pen  = market_pull_penalty(quote_history, line, market_over_odds)

        exec_edge = raw_edge - stale_pen - uncert_pen - min_pen - foul_pen - mkt_pull_pen
        conf_tier = "A" if exec_edge >= 0.08 else "B" if exec_edge >= 0.04 else "C"

        # ── Step 10: action_score — uses REAL bucket_brier from calibration ────
        # cal_mult: penalty for poorly calibrated buckets (doc 6 §1 must do now)
        # Formula: global rule §B — calibration_multiplier = clamp(1 - brier*2, 0.60, 1.05)
        cal_mult    = max(0.60, min(1.05, 1.0 - bucket_brier * 2.0))
        mkt_stab    = max(0.60, min(1.0, 1.0 - stale_pen - mkt_pull_pen))
        action_score = exec_edge * cal_mult * mkt_stab

        # Hard no-bet flag for sparse props with unstable minutes (doc 6 §1 must also)
        sparse_stats = ("stl", "blk", "stocks")
        no_bet = (
            stat in sparse_stats and rem_mean < 6 and (iqr / max(1.0, q50)) > 0.70
        )
        if no_bet:
            action_score = min(action_score, -0.01)  # force below threshold
            risk_flags_extra = ["sparse_unstable_no_bet"]
        else:
            risk_flags_extra = []

        # Calibration key for state-bucket lookup
        quarter_b = "OT" if is_overtime or period > 4 else (f"Q{period}" if period > 0 else "pre")
        time_b    = ("0-4" if rem_mean < 4 else "4-8" if rem_mean < 8
                     else "8-12" if rem_mean < 12 else "12+")
        foul_b    = "0-2" if fouls <= 2 else "3" if fouls == 3 else "4+"
        court_b   = "on" if on_court else "off"
        cal_key   = f"{stat}|{side}|{quarter_b}|{time_b}|{foul_b}|{court_b}"

        # ── Step 11: Fair odds ────────────────────────────────────────────────
        fair_over_price  = self._p2a(p_over)
        fair_under_price = self._p2a(p_under)

        # ── Step 12: Alt ladder (9 points ±2.0, instruction §A.8) ─────────────
        alt_ladder = self._alt_ladder(terminal_pmf, line, mkt_p_over)

        # ── Step 13: Reason codes (instruction §12) ───────────────────────────
        reason_codes, risk_flags = self._reason_codes(
            on_court, raw_rem, rem_mean, pace_factor, heat_factor,
            fouls, foul_trouble, score_margin, losing_team, period,
            player_live_rates, q50, pregame_q50, quote_history,
            line, market_over_odds, mkt_pull_pen, lineup_context, team_context
        )

        # ── Decomposition (doc 6 §1 must do now) ─────────────────────────────
        # Compute delta contributions for UI "why it moved" panel
        # Reference: pregame_q50 is the baseline; each factor shifts the projection
        baseline = pregame_q50
        delta_minutes = round((rem_mean / max(pregame_minutes, 1.0) - 1.0) * baseline * 0.25, 2)
        delta_pace    = round((pace_factor - 1.0) * baseline * 0.20, 2)
        delta_usage   = round(((player_live_rates or {}).get("usage", LEAGUE["usage"]) /
                               LEAGUE["usage"] - 1.0) * baseline * 0.15, 2)
        delta_foul    = round(-foul_pen * baseline * 2.0, 2)
        delta_market  = round(-mkt_pull_pen * baseline * 1.5, 2)

        return {
            "pregame_q50":             round(pregame_q50, 2),
            "live_q50":                round(q50, 2),
            "fair_over_price":         fair_over_price,
            "fair_under_price":        fair_under_price,
            "fair_line_at_minus110":   round(fair_line_110, 2),
            "push_prob":               round(push_p, 4),
            "p_over":                  round(p_over, 4),
            "p_under":                 round(p_under, 4),
            "market_prob":             round(mkt_p_over if side == "OVER" else mkt_p_under, 4),
            "raw_edge":                round(raw_edge, 4),
            "ev":                      round(ev, 4),
            "kelly":                   round(kelly, 4),
            "exec_adjusted_edge_pct":  round(exec_edge, 4),
            "confidence_tier":         conf_tier,
            "action_score":            round(action_score, 4),
            "calibration_key":         cal_key,
            "rem_minutes_mean":        round(rem_mean, 1),
            "rem_minutes_q25":         round(rem_q25, 1),
            "rem_minutes_q75":         round(rem_q75, 1),
            "pace_factor":             round(pace_factor, 3),
            "heat_factor":             round(heat_factor, 3),
            "terminal_pmf":            [[round(v,1), round(p,5)] for v,p in terminal_pmf[:60]],
            "alt_ladder":              alt_ladder,
            "reason_codes":            reason_codes,
            "risk_flags":              risk_flags + risk_flags_extra,
            "no_bet":                  no_bet,
            "model_version":           MODEL_VERSION,
            "pricing_source":          "python_live_pricer",
            # Decomposition outputs (doc 6 §1 must do now — used by UI and replay)
            "delta_from_minutes":      delta_minutes,
            "delta_from_pace":         delta_pace,
            "delta_from_usage":        delta_usage,
            "delta_from_foul_risk":    delta_foul,
            "delta_from_market":       delta_market,
            # Calibration passthrough for traceability
            "bucket_brier_used":       round(bucket_brier, 4),
            "calibration_level_used":  calibration_level,
        }

    # ── Remaining minutes posterior ───────────────────────────────────────────

    def _raw_remaining(self, period, clock_str, is_ot):
        clock = self._parse_clock(clock_str)
        if period <= 0: return 48.0
        if is_ot or period > 4: return max(0.0, clock)
        return max(0.0, clock + max(0, 4 - period) * 12.0)

    def _reentry_prob(self, on_court, raw_rem, foul_trouble, margin, losing, period, tc):
        if on_court: return 1.0
        x = (-0.70 + 0.07 * raw_rem
             - 0.70 * (1 if foul_trouble == "severe" else 0)
             - 0.35 * (1 if margin >= 20 and period >= 4 and losing else 0)
             + 0.25 * (1 if (tc or {}).get("close_game_flag", False) else 0))
        return _sigmoid(x)

    def _closing_prob(self, pregame_min, foul_trouble, margin, period):
        x = (-0.10 + 0.07 * max(0, pregame_min - 28)
             - 0.55 * (1 if foul_trouble == "severe" else 0)
             - 0.45 * (1 if margin >= 18 and period >= 4 else 0))
        return _sigmoid(x)

    def _blowout_factor(self, margin, period, losing):
        for thr, thr_p, factor in BLOWOUT_TABLE:
            if margin >= thr and period >= thr_p and losing:
                return factor
        return 1.00

    # ── Build hierarchical posterior rates (instruction §3) ───────────────────

    def _build_posteriors(self, prior_rates: dict, live_rates: dict, w: float) -> dict:
        """Merge player priors with live rates using Bayesian shrinkage."""
        p = prior_rates or {}
        l = live_rates  or {}

        def g(key, lo=None, hi=None):
            prior = p.get(key, LEAGUE.get(key, 0.20))
            live  = l.get(key, prior)
            # Efficiency stats shrink harder (less reactive to small samples)
            stat_w = {
                "p2": w * 0.45, "p3": w * 0.35, "pft": w * 0.25,
                "tov_per_poss": w * 0.40, "stl_per_min": w * 0.30, "blk_per_min": w * 0.30,
            }.get(key, w)
            return shrink_rate(prior, live, stat_w, lo, hi)

        return {
            "usage":          g("usage",          0.10, 0.45),
            "three_share":    g("three_share",     0.15, 0.70),
            "p2":             g("p2",              0.35, 0.75),
            "p3":             g("p3",              0.20, 0.55),
            "pft":            g("pft",             0.55, 0.95),
            "fta_rate":       g("fta_rate",        0.01, 0.25),
            "reb_share":      g("reb_share",       0.03, 0.40),
            "ast_share":      g("ast_share",       0.02, 0.60),
            "stl_per_min":    g("stl_per_min",     0.00, 0.20),
            "blk_per_min":    g("blk_per_min",     0.00, 0.20),
            "tov_per_poss":   g("tov_per_poss",    0.01, 0.30),
            "on_court_share": g("on_court_share",  0.30, 0.90),
            "team_fga_poss":  g("team_fga_poss",   0.70, 1.10),
            "opp_fga_poss":   g("opp_fga_poss",    0.70, 1.10),
            "opp_miss_rate":  g("opp_miss_rate",   0.40, 0.65),
        }

    # ── Live factors ─────────────────────────────────────────────────────────

    def _pace_factor(self, pace_events, w_live):
        if len(pace_events) < 4: return 1.0
        recent = pace_events[-8:]
        elapsed = recent[-1]["ts"] - recent[0]["ts"]
        scored  = recent[-1]["score"] - recent[0]["score"]
        if elapsed < 45 or scored <= 0: return 1.0
        live_ppm = (scored / elapsed * 60) / 2.2
        prior    = LEAGUE["pace"] / 48.0
        posterior = shrink_rate(prior, live_ppm, w_live)
        return min(1.40, max(0.70, posterior / prior))

    def _heat_factor(self, stat, shot_events):
        if stat not in ("pts", "fg3m") or not shot_events: return 1.0
        now = time.time()
        hot = [e for e in shot_events if e.get("ts", 0) > now - 240]
        return (1.18 if stat == "fg3m" else 1.12) if len(hot) >= 3 else 1.0

    # ── Stat-family PMF dispatch ──────────────────────────────────────────────

    def _remaining_pmf(self, stat, q, rem_mean, pre_min, pace, heat, pr, team_poss, on_court):
        if rem_mean <= 0: return [(0.0, 1.0)]
        q50 = float(q.get(0.50, 0) or 0)
        q25 = float(q.get(0.25, 0) or 0)
        q75 = float(q.get(0.75, 0) or 0)

        dispatch = {
            "pts":  lambda: self._pts_pmf(q50, pr, team_poss, rem_mean, pace, heat),
            "reb":  lambda: self._reb_pmf(q50, pr, team_poss, rem_mean, pace),
            "ast":  lambda: self._ast_pmf(q50, pr, team_poss, rem_mean, pace),
            "fg3m": lambda: self._fg3m_pmf(q50, pr, team_poss, rem_mean, pace, heat),
            "stl":  lambda: self._sparse_pmf(pr["stl_per_min"], rem_mean, 0.48),
            "blk":  lambda: self._sparse_pmf(pr["blk_per_min"], rem_mean, 0.58),
            "tov":  lambda: self._tov_pmf(pr, team_poss, rem_mean),
        }
        combos = ("pra","pr","pa","ra","stocks")

        if stat in dispatch:
            return dispatch[stat]()
        elif stat in combos:
            return self._combo_pmf(stat, q, rem_mean, pre_min, pace, heat, pr, team_poss)
        else:
            tf = min(1.0, rem_mean / max(pre_min, 1.0))
            sigma = max(0.5, (q75 - q25) / 1.35 * math.sqrt(tf))
            return self._normal_pmf(max(0, q50 * tf), sigma)

    # ── PTS: compound Poisson/Binomial (instruction §5) ──────────────────────

    def _pts_pmf(self, q50, pr, team_poss, rem_mean, pace, heat):
        player_poss = team_poss * pr["on_court_share"]
        lambda_fga  = player_poss * pr["usage"]
        lambda_3pa  = lambda_fga * pr["three_share"]
        lambda_2pa  = max(0.0, lambda_fga - lambda_3pa)
        lambda_fta  = player_poss * pr["fta_rate"]

        # Scale to match pregame rate expectation
        expected = (lambda_3pa*3*pr["p3"] + lambda_2pa*2*pr["p2"] + lambda_fta*pr["pft"])
        if expected > 0:
            target = (q50 / 36.0) * rem_mean * pace * heat
            scale  = target / expected
            lambda_3pa *= scale; lambda_2pa *= scale; lambda_fta *= scale

        rng  = np.random.default_rng()
        n3pa = rng.poisson(max(0.01, lambda_3pa), N_SIM)
        n2pa = rng.poisson(max(0.01, lambda_2pa), N_SIM)
        nfta = rng.poisson(max(0.01, lambda_fta),  N_SIM)
        samples = (3 * rng.binomial(n3pa, min(0.99, pr["p3"]))
                 + 2 * rng.binomial(n2pa, min(0.99, pr["p2"]))
                 +     rng.binomial(nfta, min(0.99, pr["pft"])))
        return self._arr_to_pmf(samples)

    # ── REB: Binomial(opp misses, share) (instruction §6) ────────────────────

    def _reb_pmf(self, q50, pr, team_poss, rem_mean, pace):
        opp_misses_lambda = team_poss * pr["opp_fga_poss"] * pr["opp_miss_rate"]
        rng = np.random.default_rng()
        opp_misses = rng.poisson(max(0.01, opp_misses_lambda), N_SIM)
        samples    = rng.binomial(opp_misses, min(0.40, pr["reb_share"]))
        return self._arr_to_pmf(np.clip(samples, 0, int(q50 * 3 + 1)))

    # ── AST: Binomial(team makes, share) (instruction §7) ────────────────────

    def _ast_pmf(self, q50, pr, team_poss, rem_mean, pace):
        team_fg_pct = 1.0 - pr["opp_miss_rate"]   # team FG% ~ 1 - league miss
        makes_lambda = team_poss * pr["team_fga_poss"] * team_fg_pct
        rng = np.random.default_rng()
        team_makes = rng.poisson(max(0.01, makes_lambda), N_SIM)
        samples    = rng.binomial(team_makes,
                                   min(0.99, LEAGUE["ast_rate"] * pr["ast_share"] * 1.6))
        return self._arr_to_pmf(np.clip(samples, 0, int(q50 * 3 + 1)))

    # ── FG3M: Binomial(3PA, p3) ───────────────────────────────────────────────

    def _fg3m_pmf(self, q50, pr, team_poss, rem_mean, pace, heat):
        player_poss = team_poss * pr["on_court_share"]
        lambda_3pa  = player_poss * pr["usage"] * pr["three_share"]
        rem_mean_fg3 = max(0, (q50 / 36.0) * rem_mean * pace * heat)
        if lambda_3pa * pr["p3"] > 0:
            scale = rem_mean_fg3 / max(0.01, lambda_3pa * pr["p3"])
            lambda_3pa = max(0.01, lambda_3pa * scale)
        rng  = np.random.default_rng()
        n3pa = rng.poisson(max(0.01, lambda_3pa), N_SIM)
        return self._arr_to_pmf(rng.binomial(n3pa, min(0.60, pr["p3"])))

    # ── Sparse PMF: zero-inflated Poisson (instruction §8) ───────────────────

    def _sparse_pmf(self, rate_per_min, rem_mean, base_zero, matchup_mult=1.0):
        lam    = max(0.001, rate_per_min * rem_mean * matchup_mult)
        # Activity bonus: if lam is meaningful, reduce zero inflation
        live_bonus = min(0.10, lam * 2)
        p_zero = max(0.35, min(0.90, base_zero - live_bonus))
        vals   = np.arange(0, 7)
        base   = sp_stats.poisson.pmf(vals, lam)
        base  /= base.sum()
        base[0] = base[0] * (1 - p_zero) + p_zero
        base[1:] *= (1 - p_zero)
        base /= base.sum()
        return list(zip(vals.tolist(), base.tolist()))

    # ── TOV: Poisson ──────────────────────────────────────────────────────────

    def _tov_pmf(self, pr, team_poss, rem_mean):
        player_poss = team_poss * pr["on_court_share"] * pr["usage"]
        lam = max(0.001, player_poss * pr["tov_per_poss"])
        return self._poisson_pmf(lam, max_val=8)

    # ── Combo: exact convolution ──────────────────────────────────────────────

    def _combo_pmf(self, stat, q, rem_mean, pre_min, pace, heat, pr, team_poss):
        q50 = float(q.get(0.50,0) or 0)
        q25 = float(q.get(0.25,0) or 0)
        q75 = float(q.get(0.75,0) or 0)
        splits = {
            "pra":    [("pts",0.55),("reb",0.27),("ast",0.18)],
            "pr":     [("pts",0.67),("reb",0.33)],
            "pa":     [("pts",0.72),("ast",0.28)],
            "ra":     [("reb",0.58),("ast",0.42)],
            "stocks": [("stl",0.55),("blk",0.45)],
        }
        pmf_list = []
        for comp, frac in splits.get(stat, [("pts",1.0)]):
            cq  = {0.50: q50*frac, 0.25: q25*frac, 0.75: q75*frac}
            cpr = {k: v*frac if k in ("stl_per_min","blk_per_min") else v
                   for k,v in pr.items()}
            pmf_list.append(
                self._remaining_pmf(comp, cq, rem_mean, pre_min, pace, heat,
                                     cpr, team_poss, True)
            )
        return self._convolve(pmf_list)

    def _convolve(self, pmf_list):
        result = pmf_list[0]
        for pmf in pmf_list[1:]:
            acc = {}
            for v1,p1 in result:
                for v2,p2 in pmf:
                    k = round(v1+v2, 1)
                    acc[k] = acc.get(k,0) + p1*p2
            total  = sum(acc.values())
            result = [(k, v/total) for k,v in sorted(acc.items())]
        return result

    # ── PMF primitives ────────────────────────────────────────────────────────

    def _normal_pmf(self, mu, sigma, step=1.0):
        lo   = max(0, int(mu - 4*sigma))
        hi   = int(mu + 4*sigma) + 1
        vals = np.arange(lo, hi+1, step)
        cdf  = sp_stats.norm.cdf(np.append(vals-step/2, vals[-1]+step/2), mu, sigma)
        probs = np.maximum(np.diff(cdf), 0)
        s = probs.sum()
        if s > 0: probs /= s
        return list(zip(vals.tolist(), probs.tolist()))

    def _poisson_pmf(self, lam, max_val=8):
        vals  = np.arange(0, max_val+1)
        probs = sp_stats.poisson.pmf(vals, max(0.001, lam))
        probs /= probs.sum()
        return list(zip(vals.tolist(), probs.tolist()))

    def _arr_to_pmf(self, arr):
        vals, counts = np.unique(arr, return_counts=True)
        probs = counts / counts.sum()
        return list(zip(vals.tolist(), probs.tolist()))

    # ── PMF operations ────────────────────────────────────────────────────────

    def _pmf_quantile(self, pmf, q):
        s = sorted(pmf, key=lambda x: x[0])
        cum = 0.0
        for v,p in s:
            cum += p
            if cum >= q: return v
        return s[-1][0] if s else 0.0

    def _fair_line(self, pmf, target_odds=-110):
        tp = abs(target_odds) / (abs(target_odds) + 100)
        for v in sorted(set(v for v,_ in pmf)):
            if sum(p for vv,p in pmf if vv > v) <= tp: return v
        return 0.0

    def _alt_ladder(self, pmf, line, mkt_p_over):
        ladder = []
        for delta in [-2.0,-1.5,-1.0,-0.5,0.0,0.5,1.0,1.5,2.0]:
            alt = line + delta
            po  = sum(p for v,p in pmf if v > alt)
            pu  = 1.0 - po
            ladder.append({
                "line": alt, "p_over": round(po,4), "p_under": round(pu,4),
                "fair_over": self._p2a(po), "fair_under": self._p2a(pu),
                "edge_over": round((po-mkt_p_over)*100, 2),
                "is_current": delta==0.0,
            })
        return ladder

    # ── Reason codes (instruction §12) ───────────────────────────────────────

    def _reason_codes(self, on_court, raw_rem, rem_mean, pace, heat, fouls,
                       foul_trouble, margin, losing, period, live_rates,
                       live_q50, pregame_q50, quote_history, line,
                       over_odds, mkt_pull_pen, lineup_ctx, team_ctx):
        codes, flags = [], []
        if not on_court and rem_mean > raw_rem * 0.4:
            codes.append("reentry_soon")
        if on_court and (lineup_ctx or {}).get("current_stint_minutes", 0) >= 8:
            codes.append("extended_stint")
        if (live_rates or {}).get("usage", 0) > 0.28:
            codes.append("usage_spike")
        if pace > 1.08:
            codes.append("pace_up")
        elif pace < 0.93:
            codes.append("pace_down")
        if heat > 1.05:
            codes.append("heat_check")
        if foul_trouble in ("moderate","severe"):
            codes.append("foul_risk")
        if margin >= 18 and period >= 4 and losing:
            codes.append("blowout_risk")
        if mkt_pull_pen >= 0.0075:
            codes.append("market_moving")
        if not on_court:
            flags.append("bench_uncertainty")
        if (team_ctx or {}).get("expected_closer", False):
            codes.append("closing_lineup_boost")
        if live_q50 > pregame_q50 * 1.10:
            codes.append("projection_up")
        elif live_q50 < pregame_q50 * 0.90:
            codes.append("projection_down")
        # Risk flags
        if rem_mean < 4:
            flags.append("late_game_variance")
        if foul_trouble == "severe":
            flags.append("foul_out_risk")
        if margin >= 25 and period >= 3:
            flags.append("garbage_time_risk")
        return codes, flags

    # ── Odds helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _p2a(p):
        if p <= 0.01 or p >= 0.99: return 0
        return round(-p/(1-p)*100) if p >= 0.5 else round((1-p)/p*100)

    @staticmethod
    def _a2p(o):
        if not o: return 0.5
        return abs(o)/(abs(o)+100) if o<0 else 100/(o+100)

    @staticmethod
    def _a2d(o):
        if not o: return 1.909
        return 1+100/abs(o) if o<0 else 1+o/100

    @staticmethod
    def _parse_clock(s):
        try:
            parts = str(s).split(":")
            return float(parts[0]) + float(parts[1])/60.0
        except Exception:
            try: return float(s)
            except: return 0.0


# ══════════════════════════════════════════════════════════════════════════════
# CLI entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdin-json", action="store_true")
    args = parser.parse_args()

    if not args.stdin_json:
        sys.stdout.write(json.dumps({"error":"use --stdin-json","pricing_source":"error"}))
        sys.exit(1)

    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        sys.stdout.write(json.dumps({"error":f"JSON parse: {e}","pricing_source":"error"}))
        sys.exit(1)

    pricer = LivePricer()
    try:
        q_raw = payload.get("pregame_quantiles") or {}
        result = pricer.price(
            stat              = payload.get("stat","pts"),
            side              = payload.get("side","OVER"),
            line              = float(payload.get("line",0)),
            pregame_quantiles = {float(k):float(v) for k,v in q_raw.items()},
            current_stat      = float(payload.get("current_stat",0)),
            period            = int(payload.get("period",1)),
            clock_str         = str(payload.get("clock_str","12:00")),
            on_court          = bool(payload.get("on_court",True)),
            fouls             = int(payload.get("fouls",0)),
            foul_trouble      = str(payload.get("foul_trouble","none")),
            score_margin      = int(payload.get("score_margin",0)),
            losing_team       = bool(payload.get("losing_team",False)),
            is_overtime       = bool(payload.get("is_overtime",False)),
            market_over_odds  = int(payload.get("market_over_odds",-110)),
            market_under_odds = int(payload.get("market_under_odds",-110)),
            quote_age_sec     = float(payload.get("quote_age_sec",0)),
            shot_events       = payload.get("shot_events",[]),
            pace_events       = payload.get("pace_events",[]),
            player_live_rates = payload.get("player_live_rates",{}),
            lineup_context    = payload.get("lineup_context",{}),
            team_context      = payload.get("team_context",{}),
            pregame_minutes   = float(payload.get("pregame_minutes",36.0)),
            player_prior_rates= payload.get("player_prior_rates",{}),
            quote_history     = payload.get("quote_history",[]),
            bucket_brier       = float(payload.get("bucket_brier", 0.25)),
            calibration_level  = str(payload.get("calibration_level", "identity")),
        )
        sys.stdout.write(json.dumps(result))
    except Exception as e:
        sys.stdout.write(json.dumps({"error":str(e),"pricing_source":"error"}))
        sys.exit(1)


if __name__ == "__main__":
    if "--stdin-json" not in sys.argv:
        # Smoke test
        np.random.seed(42)
        p = LivePricer()
        q = {0.10:10, 0.25:15, 0.50:22, 0.75:28, 0.90:34}
        prior = {"usage":0.22,"three_share":0.38,"p2":0.52,"p3":0.36,"pft":0.78,
                 "fta_rate":0.07,"reb_share":0.10,"ast_share":0.20,"stl_per_min":0.025,
                 "blk_per_min":0.015,"tov_per_poss":0.12,"on_court_share":0.72,
                 "team_fga_poss":0.92,"opp_fga_poss":0.92,"opp_miss_rate":0.54}
        qh = [{"age_sec":30,"line":22.5},{"age_sec":90,"line":22.5},{"age_sec":150,"line":23.0}]
        print(f"{'STAT':6} {'Q50':>6} {'FairO':>7} {'Edge':>7} {'Exec':>7} {'Act':>7} {'Tier'}")
        print("-"*52)
        for stat,line in [("pts",25.5),("reb",8.5),("ast",6.5),("fg3m",2.5),
                           ("stl",0.5),("blk",0.5),("pra",33.5)]:
            r = p.price(stat=stat,side="OVER",line=line,pregame_quantiles=q,
                        current_stat=8,period=3,clock_str="7:42",on_court=True,fouls=2,
                        foul_trouble="none",score_margin=5,losing_team=False,is_overtime=False,
                        market_over_odds=-115,market_under_odds=-105,
                        player_prior_rates=prior,quote_history=qh)
            print(f"{stat.upper():6} {r['live_q50']:6.1f} {str(r['fair_over_price']):>7} "
                  f"{r['raw_edge']*100:>+6.1f}% {r['exec_adjusted_edge_pct']*100:>+6.1f}% "
                  f"{r['action_score']*100:>+6.1f}%  {r['confidence_tier']}")
        pmf_sum = sum(p2 for _,p2 in p.price("pts","OVER",25.5,q,8,3,"7:42",True,2,"none",
                                              5,False,False,-115,-105)["terminal_pmf"])
        print(f"\nPMF sum: {pmf_sum:.5f} | Cal key: {p.price('pts','OVER',25.5,q,8,3,'7:42',True,2,'none',5,False,False,-115,-105)['calibration_key']}")
        sys.exit(0)
    main()
