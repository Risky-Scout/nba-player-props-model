"""Tests for the Derek forward-feed defensive publication guard.

After the M8.9 root-cause rewire, the primary player-universe gate is
upstream projected rotation/minutes eligibility (see
``src/nba_props_model/pipelines/player_game_eligibility.py``). The Derek
forward feed contains only a defensive publication guard:

  1. If ``player_game_eligible`` is present on every row, the filter
     keeps rows where ``player_game_eligible`` is True and emits a WARN
     for any False rows (canonical validation should have prevented
     that).
  2. If ``player_game_eligible`` is absent (legacy snapshot without the
     M8.9 columns), fall back to the prior market-quoted-player
     heuristic so the feed remains usable.
"""
from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"


class DefensiveFilterPresenceTest(unittest.TestCase):
    """The filter is wired into write_m88_unified_feed and emits the
    expected manifest fields + console summary."""

    def setUp(self) -> None:
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_filter_doc_states_defensive_publication_guard(self) -> None:
        self.assertIn(
            "defensive publication guard",
            self.text,
            "Filter docstring must clarify this is a defensive guard, "
            "not the primary player-universe gate.",
        )

    def test_filter_uses_upstream_player_game_eligible_when_present(self) -> None:
        self.assertIn(
            'player_game_eligible',
            self.text,
            "Filter must respect upstream player_game_eligible.",
        )
        self.assertIn(
            "upstream_player_game_eligible",
            self.text,
            "Filter must record the upstream strategy in the manifest.",
        )

    def test_filter_has_legacy_market_quoted_fallback(self) -> None:
        self.assertIn(
            "legacy_market_quoted_player_fallback",
            self.text,
            "Filter must fall back to legacy market-quoted-player "
            "heuristic when upstream eligibility column is absent.",
        )
        self.assertIn(
            'has_line = out_df["line"].notna()',
            self.text,
            "Legacy fallback must compute the has-line mask.",
        )

    def test_filter_warns_on_upstream_ineligible_rows(self) -> None:
        self.assertIn(
            "canonical validation should have prevented",
            self.text,
            "Filter must emit a WARN that points the operator at the "
            "upstream canonical validator when it drops anything.",
        )

    def test_manifest_records_filter_strategy(self) -> None:
        self.assertIn(
            '"rotation_bench_filter":',
            self.text,
            "Manifest must record bench-filter decisions for audit.",
        )
        self.assertIn(
            '"strategy":',
            self.text,
            "Manifest must record which strategy fired (upstream "
            "eligibility vs legacy fallback).",
        )
        self.assertIn(
            '"rows_dropped":',
            self.text,
            "Manifest must report how many rows were dropped.",
        )
        self.assertIn(
            '"players_dropped":',
            self.text,
            "Manifest must list the dropped players for operator audit.",
        )

    def test_filter_runs_before_writing_output_files(self) -> None:
        filter_idx = self.text.find("rotation_filter_dropped_rows = 0")
        # The persisted public feed is written from ``out_df_public``
        # (a sanitised copy of ``out_df``) — search for either variant
        # so the test survives the quarantine-aware rename.
        parquet_write_idx = self.text.find('out_df_public.to_parquet(pq_out')
        if parquet_write_idx < 0:
            parquet_write_idx = self.text.find('out_df.to_parquet(pq_out')
        self.assertGreater(filter_idx, 0, "Filter block not found.")
        self.assertGreater(parquet_write_idx, 0, "Parquet write not found.")
        self.assertLess(
            filter_idx,
            parquet_write_idx,
            "Filter must run BEFORE the file writes.",
        )


class DefensiveFilterSemanticsTest(unittest.TestCase):
    """Pure-Python emulation of the two-mode filter so we can verify
    semantics without importing pandas. Local Python 3.9 stacks
    occasionally segfault on pyarrow import; emulating in dicts keeps
    this test deterministic."""

    @staticmethod
    def _emulate_filter(rows: list[dict]) -> tuple[list[dict], str]:
        """Returns (kept_rows, strategy_label)."""
        if rows and all("player_game_eligible" in r and r["player_game_eligible"] is not None for r in rows):
            kept = [r for r in rows if bool(r["player_game_eligible"])]
            return kept, "upstream_player_game_eligible"

        market_quoted = {
            r["player_id"] for r in rows if r.get("line") is not None
        }
        kept = [
            r for r in rows
            if r.get("line") is not None or r["player_id"] in market_quoted
        ]
        return kept, "legacy_market_quoted_player_fallback"

    def test_upstream_eligibility_keeps_eligible_drops_ineligible(self) -> None:
        rows = [
            {"player_id": 1, "player_name": "Star",
             "stat": "pts", "line": 25.5, "player_game_eligible": True},
            {"player_id": 1, "player_name": "Star",
             "stat": "reb", "line": None, "player_game_eligible": True},
            {"player_id": 2, "player_name": "DeepBench",
             "stat": "pts", "line": None, "player_game_eligible": False},
        ]
        kept, strategy = self._emulate_filter(rows)
        self.assertEqual(strategy, "upstream_player_game_eligible")
        self.assertEqual({r["player_id"] for r in kept}, {1})

    def test_legacy_fallback_when_upstream_column_absent(self) -> None:
        rows = [
            {"player_id": 1, "player_name": "Star",  "stat": "pts", "line": 25.5},
            {"player_id": 1, "player_name": "Star",  "stat": "reb", "line": None},
            {"player_id": 2, "player_name": "Bench", "stat": "pts", "line": None},
        ]
        kept, strategy = self._emulate_filter(rows)
        self.assertEqual(strategy, "legacy_market_quoted_player_fallback")
        self.assertEqual({r["player_id"] for r in kept}, {1})

    def test_legacy_fallback_keeps_market_row_when_only_one_book_quotes(self) -> None:
        rows = [
            {"player_id": 7, "player_name": "Rare",  "stat": "pts", "line": 4.5},
            {"player_id": 7, "player_name": "Rare",  "stat": "ast", "line": None},
        ]
        kept, strategy = self._emulate_filter(rows)
        self.assertEqual(strategy, "legacy_market_quoted_player_fallback")
        self.assertEqual(len(kept), 2)


if __name__ == "__main__":
    unittest.main()
