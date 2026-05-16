"""Tests for the row-level canonical injury freshness rollup.

Covers the four scenarios called out in the May-17 patch directive:

  1. Canonical rows with at least one
     ``injury_freshness_status="latest_valid_report_selected"`` (or
     any other fresh-equivalent) MUST NOT produce
     ``injury_very_stale``.
  2. Canonical rows with all stale / missing / "unknown" injury
     freshness MUST produce ``injury_very_stale``.
  3. A "fresh" ``data/player_availability_asof.parquet`` file mtime
     alone is NOT sufficient — the rollup must look at row-level
     evidence, not the disk file's timestamp.
  4. ``injury_report_fetched_at_utc`` propagates feature_snapshot
     → stat_grid → canonical → manifest, and a recent
     row-level timestamp paired with an unknown status string is
     not promoted to fresh (status priority always wins).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from nba_props_model.data.injury_freshness import (
    INJURY_FRESH_WINDOW_HOURS,
    classify_canonical_injury_freshness,
    row_injury_freshness_verdict,
)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_canonical_with_any_fresh_status_is_not_very_stale() -> None:
    statuses = [
        "latest_valid_report_selected",
        "unknown",
        "unknown",
    ]
    fetched = [
        "2026-05-17T13:00:00Z",
        None,
        None,
    ]
    verdict = classify_canonical_injury_freshness(
        statuses=statuses, fetched_at_values=fetched
    )
    assert verdict.is_fresh_overall is True
    assert verdict.fresh_row_count == 1
    assert "row_level_injury_fresh_rows=1/3" in verdict.to_manifest_detail()


def test_canonical_with_all_unknown_produces_very_stale() -> None:
    statuses = ["unknown"] * 5
    fetched = [None, "", "2026-05-16T20:13:22Z", None, "2026-05-16T20:13:22Z"]
    verdict = classify_canonical_injury_freshness(
        statuses=statuses, fetched_at_values=fetched
    )
    assert verdict.is_fresh_overall is False
    assert verdict.fresh_row_count == 0
    detail = verdict.to_manifest_detail()
    assert "row_level_injury_fresh_rows=0/5" in detail
    assert "injury_report_not_yet_published_or_unavailable" in detail


def test_file_mtime_alone_does_not_promote_unknown_rows(tmp_path: Path) -> None:
    """Reproduce the pre-fix bug: writing a brand-new file with a
    fresh mtime must NOT cause the rollup to call the slate fresh
    when the canonical row-level status is still
    ``"unknown"``."""
    fresh_availability = tmp_path / "player_availability_asof.parquet"
    pd.DataFrame({"player_id": [1, 2, 3]}).to_parquet(
        fresh_availability, index=False
    )
    assert fresh_availability.is_file()
    # File mtime is brand new (just-created).
    age_seconds = (
        datetime.now(timezone.utc).timestamp() - fresh_availability.stat().st_mtime
    )
    assert age_seconds < 60.0

    statuses = ["unknown", "unknown", "unknown"]
    fetched = ["2026-05-16T20:13:22Z"] * 3
    verdict = classify_canonical_injury_freshness(
        statuses=statuses, fetched_at_values=fetched
    )
    assert verdict.is_fresh_overall is False
    detail = verdict.to_manifest_detail()
    assert "row_level_injury_fresh_rows=0/3" in detail


def test_row_level_fetched_at_propagates_through_pipeline_stages() -> None:
    """Simulate the propagation contract:

    feature_snapshot.row → stat_grid.row → canonical.row → manifest.

    Each downstream stage is supposed to *preserve* the row-level
    ``injury_report_fetched_at_utc``. We model this with a chain of
    dicts and assert the final canonical dataframe's column still
    carries the original value, and that the rollup is computed
    from that column rather than a freshly-stamped value."""
    fetched_at = "2026-05-17T14:00:00Z"

    feature_snapshot_row = {
        "player_id": 100,
        "injury_freshness_status": "latest_valid_report_selected",
        "injury_context_source": "bdl_plus_nba_official",
        "injury_report_fetched_at_utc": fetched_at,
    }
    stat_grid_row = {
        **feature_snapshot_row,
        "stat": "pts",
        "minutes_q50": 30.0,
    }
    canonical_row = {
        **stat_grid_row,
        "delivery_date": "2026-05-17",
    }
    canonical_df = pd.DataFrame([canonical_row, canonical_row])
    assert (
        canonical_df["injury_report_fetched_at_utc"].iloc[0] == fetched_at
    ), "row-level injury_report_fetched_at_utc must survive canonical"

    verdict = classify_canonical_injury_freshness(
        statuses=canonical_df["injury_freshness_status"].tolist(),
        fetched_at_values=canonical_df[
            "injury_report_fetched_at_utc"
        ].tolist(),
    )
    assert verdict.is_fresh_overall is True
    assert verdict.fresh_row_count == 2
    assert verdict.sample_fetched_at_utc == fetched_at


def test_row_verdict_treats_known_statuses() -> None:
    now = datetime(2026, 5, 17, 18, 0, tzinfo=timezone.utc)
    assert (
        row_injury_freshness_verdict(
            injury_freshness_status="latest_valid_report_selected",
            injury_report_fetched_at_utc="1999-01-01T00:00:00Z",
            now_utc=now,
        )
        is True
    )
    assert (
        row_injury_freshness_verdict(
            injury_freshness_status="fallback_used",
            injury_report_fetched_at_utc=None,
            now_utc=now,
        )
        is True
    )
    assert (
        row_injury_freshness_verdict(
            injury_freshness_status="unknown",
            injury_report_fetched_at_utc=_iso(now - timedelta(minutes=5)),
            now_utc=now,
        )
        is False
    ), "unknown status must not be promoted by recent timestamp alone"
    assert (
        row_injury_freshness_verdict(
            injury_freshness_status=None,
            injury_report_fetched_at_utc=_iso(now - timedelta(minutes=5)),
            now_utc=now,
        )
        is False
    ), "null status must not be promoted by recent timestamp alone"
    # When status is a non-canonical string but the row's fetched_at
    # is within the freshness window, recency is allowed to promote.
    assert (
        row_injury_freshness_verdict(
            injury_freshness_status="some_future_status",
            injury_report_fetched_at_utc=_iso(now - timedelta(hours=1)),
            now_utc=now,
        )
        is True
    )
    assert (
        row_injury_freshness_verdict(
            injury_freshness_status="some_future_status",
            injury_report_fetched_at_utc=_iso(
                now - timedelta(hours=INJURY_FRESH_WINDOW_HOURS + 1)
            ),
            now_utc=now,
        )
        is False
    )
