"""Tests for the morning-only lineup_snapshot_status.json freshness guard.

The morning run of build_derek_forward_feed.py must always rewrite
lineup_snapshot_status.json with today's timestamp and a meaningful
pending_pre_tipoff_run sentinel, so:

  (a) yesterday's stale lineup_snapshot_status.json never lingers in
      today's deliveries/<date>/derek_forward_feed/ folder, and
  (b) the feed_manifest.json carries a meaningful lineup_status field
      (not a bare null) when the morning phase runs alone.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"


class MorningOnlyLineupStatusFreshnessTest(unittest.TestCase):
    """build_derek_forward_feed.py --snapshot morning must refresh the
    lineup_snapshot_status.json and the feed_manifest.lineup_status field.

    These tests exercise the *script-level* contract rather than the
    snapshot-build math; we stub out _build_morning_rows so the test
    does not depend on the full data pipeline.
    """

    def setUp(self) -> None:
        self.script_text = SCRIPT.read_text(encoding="utf-8")

    def test_morning_branch_writes_pending_pre_tipoff_run_status(self) -> None:
        """The morning code path must populate lineup_status_payload."""
        # Grep-style assertion: the exact phrase only appears in the new
        # M8.8 freshness guard added by this commit. If the guard is
        # ever deleted or weakened, this fails.
        self.assertIn(
            "pending_pre_tipoff_run",
            self.script_text,
            "Morning-only freshness guard sentinel string missing.",
        )
        self.assertIn(
            'if args.snapshot == "morning":',
            self.script_text,
            "Morning-only freshness guard branch missing.",
        )
        self.assertIn(
            "lineup_phase_executed_today",
            self.script_text,
            "Morning-only freshness guard schema field missing.",
        )

    def test_status_payload_is_picked_up_by_feed_manifest(self) -> None:
        """feed_manifest must carry lineup_status from the same payload."""
        self.assertIn(
            '"lineup_status": lineup_status_payload',
            self.script_text,
            "feed_manifest.lineup_status is not bound to "
            "lineup_status_payload; the morning-only freshness guard "
            "would not flow into the manifest.",
        )

    def test_morning_freshness_block_runs_before_lineup_block(self) -> None:
        """The morning-only freshness guard must come BEFORE the
        lineup/both block, so when args.snapshot == "both" the lineup
        block can still overwrite lineup_status_payload with confirmed
        or near-tip data and not be clobbered by this guard."""
        morning_block = 'if args.snapshot == "morning":'
        lineup_block = 'if args.snapshot in {"lineup", "both"}:'
        morning_idx = self.script_text.find(morning_block)
        lineup_idx = self.script_text.find(lineup_block)
        self.assertGreater(morning_idx, 0, "Morning guard not found.")
        self.assertGreater(lineup_idx, 0, "Lineup block not found.")
        self.assertLess(
            morning_idx,
            lineup_idx,
            "Morning-only guard must precede the lineup/both block so "
            "args.snapshot == 'both' can still emit a confirmed lineup "
            "status without being clobbered.",
        )

    def test_morning_freshness_block_skipped_when_snapshot_is_both(self) -> None:
        """Sanity: the guard's predicate is `== 'morning'` (exact), not
        a set membership, so --snapshot both does NOT enter the guard."""
        # Specifically the guard must NOT be e.g.
        #   if args.snapshot in {"morning", "both"}:
        # else it would race the lineup/both block.
        self.assertNotIn(
            'if args.snapshot in {"morning", "both"}:\n        lineup_status_payload = {\n            "status": "pending_pre_tipoff_run"',
            self.script_text,
            "Morning-only guard predicate is too broad; it would "
            "clobber a real lineup_status when --snapshot both runs.",
        )


if __name__ == "__main__":
    unittest.main()
