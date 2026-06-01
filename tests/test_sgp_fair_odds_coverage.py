"""Tests for exhaustive SGP candidate generation and fair odds computation.

Covers:
  - All 2-leg combinations are generated (not a random sample)
  - 3-leg combinations are generated when max_leg_count=3
  - fair_probability is non-null on every price grid row
  - fair_decimal_odds and fair_american_odds are consistent with fair_probability
  - fair_american_odds are included in publishable edges
  - Leg count breakdown is reported correctly
  - Per-game and global caps are respected
  - WoO page includes fair-odds columns
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO = Path(__file__).resolve().parent.parent

# Import the script as a module.
import importlib.util, sys

def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def engine_mod():
    return _load("run_sgp_engine_daily")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_pmf_df(n_players: int = 4, stats: list[str] | None = None, game_id: str = "G001") -> pd.DataFrame:
    """Minimal PMF dataframe for testing candidate generation."""
    if stats is None:
        stats = ["pts", "reb"]

    rows = []
    for pid in range(1, n_players + 1):
        for stat in stats:
            line = 10.5 if stat == "pts" else 5.5
            # Build a valid PMF array with known shape.
            pmf = np.zeros(41)
            pmf[int(line) + 1 :int(line) + 6] = 0.2
            pmf = pmf / pmf.sum()
            mean_val = float((np.arange(41) * pmf).sum())
            rows.append({
                "player_id": f"P{pid:03d}",
                "player_name": f"Player {pid}",
                "team_id": f"T{1 + (pid % 2):02d}",
                "stat": stat,
                "line": line,
                "game_id": game_id,
                "p_over": float(pmf[int(line) + 1:].sum()),
                "mean": mean_val,
                "pmf_valid": True,
                "pmf": pmf,
            })
    return pd.DataFrame(rows)


# ── 1. Exhaustive 2-leg: all C(n,2) pairs are generated ─────────────────────

class TestExhaustive2Leg:
    def test_all_two_leg_pairs_for_4_players_2_stats(self, engine_mod):
        """With 4 players × 2 stats = 8 (player,stat) keys, expect C(8,2) = 28 two-leg tickets."""
        pmf_df = _make_pmf_df(n_players=4, stats=["pts", "reb"])
        tickets = engine_mod.generate_sgp_candidates(
            pmf_df,
            max_candidates=9999,
            max_per_game=9999,
            max_three_leg_per_game=0,
            max_leg_count=2,
        )
        two_leg = [t for t in tickets if len(t.legs) == 2]
        expected = math.comb(8, 2)  # 28
        assert len(two_leg) == expected, f"Expected {expected} 2-leg tickets, got {len(two_leg)}"

    def test_no_same_player_stat_duplicates(self, engine_mod):
        """Each 2-leg ticket must have distinct (player_id, stat) pairs."""
        pmf_df = _make_pmf_df(n_players=5, stats=["pts", "reb", "ast"])
        tickets = engine_mod.generate_sgp_candidates(pmf_df, max_candidates=99999, max_per_game=99999, max_leg_count=2)
        for t in tickets:
            combos = [(l.player_id, l.stat) for l in t.legs]
            assert len(combos) == len(set(combos)), f"Duplicate (player,stat) in ticket {t.ticket_id}"

    def test_all_legs_are_overs(self, engine_mod):
        """Every generated leg must be 'over'."""
        pmf_df = _make_pmf_df(n_players=3, stats=["pts", "ast"])
        tickets = engine_mod.generate_sgp_candidates(pmf_df, max_candidates=9999, max_per_game=9999, max_leg_count=2)
        for t in tickets:
            for leg in t.legs:
                assert leg.side == "over", f"Leg side is not 'over': {leg.side}"


# ── 2. 3-leg generation ───────────────────────────────────────────────────────

class TestThreeLegGeneration:
    def test_three_leg_tickets_generated(self, engine_mod):
        """With max_leg_count=3, some 3-leg tickets must be generated."""
        pmf_df = _make_pmf_df(n_players=4, stats=["pts", "reb"])
        tickets = engine_mod.generate_sgp_candidates(
            pmf_df,
            max_candidates=99999,
            max_per_game=99999,
            max_three_leg_per_game=99999,
            max_leg_count=3,
        )
        three_leg = [t for t in tickets if len(t.legs) == 3]
        expected = math.comb(8, 3)  # C(8,3) = 56
        assert len(three_leg) == expected, f"Expected {expected} 3-leg tickets, got {len(three_leg)}"

    def test_max_leg_count_2_suppresses_three_leg(self, engine_mod):
        """With max_leg_count=2, no 3-leg tickets should be generated."""
        pmf_df = _make_pmf_df(n_players=5, stats=["pts", "reb"])
        tickets = engine_mod.generate_sgp_candidates(
            pmf_df,
            max_candidates=9999,
            max_per_game=9999,
            max_three_leg_per_game=9999,
            max_leg_count=2,
        )
        three_leg = [t for t in tickets if len(t.legs) == 3]
        assert len(three_leg) == 0

    def test_three_leg_no_duplicate_player_stat(self, engine_mod):
        """Every 3-leg ticket must have 3 distinct (player_id, stat) entries."""
        pmf_df = _make_pmf_df(n_players=6, stats=["pts", "reb"])
        tickets = engine_mod.generate_sgp_candidates(
            pmf_df,
            max_candidates=9999,
            max_per_game=9999,
            max_three_leg_per_game=9999,
            max_leg_count=3,
        )
        three_leg = [t for t in tickets if len(t.legs) == 3]
        for t in three_leg:
            combos = [(l.player_id, l.stat) for l in t.legs]
            assert len(combos) == len(set(combos))


# ── 3. Per-game and global caps ───────────────────────────────────────────────

class TestCaps:
    def test_per_game_cap_respected(self, engine_mod):
        """Number of tickets for any single game must not exceed max_per_game."""
        pmf_df = _make_pmf_df(n_players=8, stats=["pts", "reb", "ast"])
        max_pg = 30
        tickets = engine_mod.generate_sgp_candidates(
            pmf_df,
            max_candidates=9999,
            max_per_game=max_pg,
            max_three_leg_per_game=10,
            max_leg_count=3,
        )
        by_game: dict = {}
        for t in tickets:
            by_game.setdefault(t.game_id, 0)
            by_game[t.game_id] += 1
        for gid, count in by_game.items():
            assert count <= max_pg, f"Game {gid}: {count} tickets > max_per_game={max_pg}"

    def test_global_cap_respected(self, engine_mod):
        """Total tickets must not exceed max_candidates."""
        pmf_df = _make_pmf_df(n_players=10, stats=["pts", "reb", "ast"])
        max_c = 50
        tickets = engine_mod.generate_sgp_candidates(
            pmf_df,
            max_candidates=max_c,
            max_per_game=9999,
            max_three_leg_per_game=9999,
            max_leg_count=3,
        )
        assert len(tickets) <= max_c, f"Got {len(tickets)} > max_candidates={max_c}"

    def test_two_leg_priority_under_per_game_cap(self, engine_mod):
        """2-leg tickets fill the budget first; 3-leg fill the remainder up to their own cap."""
        pmf_df = _make_pmf_df(n_players=3, stats=["pts", "reb"])
        # 3p × 2s = 6 keys → C(6,2)=15 two-leg, C(6,3)=20 three-leg.
        # max_per_game=20, max_three_leg_per_game=5 → 15 two-leg + 5 three-leg = 20 total.
        tickets = engine_mod.generate_sgp_candidates(
            pmf_df,
            max_candidates=9999,
            max_per_game=20,
            max_three_leg_per_game=5,
            max_leg_count=3,
        )
        game_tickets = [t for t in tickets if t.game_id == "G001"]
        assert len(game_tickets) <= 20
        two_leg = [t for t in game_tickets if len(t.legs) == 2]
        assert len(two_leg) == 15, f"Expected all 15 two-leg, got {len(two_leg)}"
        three_leg = [t for t in game_tickets if len(t.legs) == 3]
        assert len(three_leg) == 5, f"Expected 5 three-leg (capped by max_three_leg_per_game), got {len(three_leg)}"


# ── 4. Fair odds on every price grid row ─────────────────────────────────────

class TestFairOddsInPriceGrid:
    _GRID_PATH = _REPO / "deliveries" / "2026-05-30" / "sgp_engine" / "prices" / "sgp_price_grid.parquet"

    @pytest.fixture(autouse=True)
    def require_price_grid(self):
        if not self._GRID_PATH.exists():
            pytest.skip("Price grid not present; run smoke test first")

    def test_fair_probability_column_present(self):
        df = pd.read_parquet(self._GRID_PATH)
        assert "fair_probability" in df.columns, "fair_probability column missing from price grid"

    def test_fair_probability_non_null_on_non_suppressed(self):
        df = pd.read_parquet(self._GRID_PATH)
        non_sup = df[df["tier"].astype(str) != "SUPPRESSED"]
        null_fair_p = non_sup["fair_probability"].isna().sum()
        assert null_fair_p == 0, f"{null_fair_p} non-suppressed rows have null fair_probability"

    def test_fair_probability_in_valid_range(self):
        df = pd.read_parquet(self._GRID_PATH)
        valid = df.dropna(subset=["fair_probability"])
        out_of_range = ((valid["fair_probability"] <= 0) | (valid["fair_probability"] >= 1)).sum()
        assert out_of_range == 0, f"{out_of_range} rows have fair_probability outside (0,1)"

    def test_fair_decimal_odds_column_present(self):
        df = pd.read_parquet(self._GRID_PATH)
        assert "fair_decimal_odds" in df.columns, "fair_decimal_odds column missing from price grid"

    def test_fair_american_odds_column_present(self):
        df = pd.read_parquet(self._GRID_PATH)
        assert "fair_american_odds" in df.columns, "fair_american_odds column missing from price grid"

    def test_fair_decimal_odds_consistent_with_fair_probability(self):
        """fair_decimal_odds ≈ 1 / fair_probability for non-null rows."""
        df = pd.read_parquet(self._GRID_PATH)
        valid = df.dropna(subset=["fair_probability", "fair_decimal_odds"])
        if len(valid) == 0:
            pytest.skip("No rows with both fair_probability and fair_decimal_odds")
        expected = 1.0 / valid["fair_probability"].astype(float)
        actual = valid["fair_decimal_odds"].astype(float)
        max_err = (expected - actual).abs().max()
        assert max_err < 0.01, f"fair_decimal_odds inconsistent with fair_probability; max error={max_err:.6f}"

    def test_fair_american_odds_sign_consistency(self):
        """Underdogs (p < 0.5) should have positive American odds; favourites negative."""
        df = pd.read_parquet(self._GRID_PATH)
        valid = df.dropna(subset=["fair_probability", "fair_american_odds"])
        if len(valid) == 0:
            pytest.skip("No valid rows")
        underdogs = valid[valid["fair_probability"] < 0.5]
        if len(underdogs):
            wrong = (underdogs["fair_american_odds"].astype(float) < 0).sum()
            assert wrong == 0, f"{wrong} underdog SGPs have negative American odds (should be positive)"
        favourites = valid[valid["fair_probability"] > 0.5]
        if len(favourites):
            wrong = (favourites["fair_american_odds"].astype(float) > 0).sum()
            assert wrong == 0, f"{wrong} favourite SGPs have positive American odds (should be negative)"


# ── 5. Publishable edges include fair odds ────────────────────────────────────

class TestPublishableEdgesFairOdds:
    _EDGES_PATH = _REPO / "deliveries" / "2026-05-30" / "sgp_engine" / "market_comparison" / "sgp_publishable_edges.parquet"

    @pytest.fixture(autouse=True)
    def require_edges(self):
        if not self._EDGES_PATH.exists():
            pytest.skip("Publishable edges not present; run smoke test first")

    def test_fair_probability_in_edges(self):
        df = pd.read_parquet(self._EDGES_PATH)
        assert "fair_probability" in df.columns, "fair_probability missing from publishable edges"

    def test_fair_decimal_odds_in_edges(self):
        df = pd.read_parquet(self._EDGES_PATH)
        assert "fair_decimal_odds" in df.columns, "fair_decimal_odds missing from publishable edges"

    def test_fair_american_odds_in_edges(self):
        df = pd.read_parquet(self._EDGES_PATH)
        assert "fair_american_odds" in df.columns, "fair_american_odds missing from publishable edges"


# ── 6. Leg count breakdown ────────────────────────────────────────────────────

class TestLegCountBreakdown:
    def test_leg_count_column_in_price_grid(self):
        grid_path = _REPO / "deliveries" / "2026-05-30" / "sgp_engine" / "prices" / "sgp_price_grid.parquet"
        if not grid_path.exists():
            pytest.skip("Price grid not present")
        df = pd.read_parquet(grid_path)
        assert "leg_count" in df.columns or "n_legs" in df.columns, \
            "Neither leg_count nor n_legs column in price grid"

    def test_price_grid_has_three_leg_rows(self):
        """After exhaustive generation with max_leg_count=3, price grid must contain 3-leg rows."""
        grid_path = _REPO / "deliveries" / "2026-05-30" / "sgp_engine" / "prices" / "sgp_price_grid.parquet"
        if not grid_path.exists():
            pytest.skip("Price grid not present; run smoke test first")
        df = pd.read_parquet(grid_path)
        lc_col = "leg_count" if "leg_count" in df.columns else "n_legs"
        three_leg = df[df[lc_col].astype(str) == "3"]
        assert len(three_leg) > 0, \
            "No 3-leg rows in price grid. Run smoke with --max-leg-count=3 (now default)."


# ── 7. WoO page includes fair-odds columns ────────────────────────────────────

class TestWoOFairOddsColumns:
    def test_woo_page_has_fair_odds_headers(self):
        woo_path = _REPO / "public_export" / "wizard_of_odds" / "sgp" / "index.html"
        if not woo_path.exists():
            pytest.skip("WoO SGP page not present; run build_sgp_woo_page.py first")
        content = woo_path.read_text()
        assert "Fair Odds (Am.)" in content, "WoO SGP page missing 'Fair Odds (Am.)' column header"
        assert "Fair Odds (Dec.)" in content, "WoO SGP page missing 'Fair Odds (Dec.)' column header"
        assert "Fair Prob." in content, "WoO SGP page missing 'Fair Prob.' column header"

    def test_woo_page_has_leg_count_column(self):
        woo_path = _REPO / "public_export" / "wizard_of_odds" / "sgp" / "index.html"
        if not woo_path.exists():
            pytest.skip("WoO SGP page not present")
        content = woo_path.read_text()
        assert "Leg#" in content, "WoO SGP page missing 'Leg#' column header"
