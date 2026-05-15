"""Unit tests for structured NBA official injury PDF selection."""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("nbainjuries")
import PyPDF2  # noqa: E402

from nba_props_model.data.nba_official_injury_report_fetch import (  # noqa: E402
    FUTURE_REPORT,
    fetch_nba_official_injury_report,
)


def _sample_injury_df():
    return pd.DataFrame(
        [
            {
                "Player Name": "Doe, John",
                "Current Status": "Out",
                "Reason": "Rest",
                "Game Date": "05/15/2026",
                "Game Time": "7:00 pm ET",
                "Matchup": "A @ B",
                "Team": "Boston Celtics",
            }
        ]
    )


def test_future_slots_get_future_reason_then_success(tmp_path, monkeypatch):
    """5PM/7PM are future at ~3:48 PM ET; 1PM parses — no exception."""
    monkeypatch.setattr(
        PyPDF2,
        "PdfReader",
        lambda *_a, **_k: MagicMock(pages=[MagicMock()]),
    )

    def fake_get(url, **kwargs):
        return SimpleNamespace(status_code=200, content=b"%PDF-1.4 fake-for-test\n")

    def fake_reportdata(*_a, **_k):
        return _sample_injury_df()

    # 19:48 UTC ≈ 15:48 Eastern on 2026-05-15 (DST): 5PM/7PM ET reports are still future.
    now = datetime(2026, 5, 15, 19, 48, tzinfo=timezone.utc)
    res = fetch_nba_official_injury_report(
        report_day=date(2026, 5, 15),
        now_utc=now,
        slate_team_full_names={"Boston Celtics"},
        repo_root=tmp_path,
        slate_date_for_artifact="2026-05-15",
        requests_get=fake_get,
        get_reportdata=fake_reportdata,
        candidate_hours=[19, 17, 13],
    )

    assert res.injury_dict
    assert res.injury_report_fallback_used is True
    assert res.injury_freshness_status == "fallback_used"
    assert res.selected_injury_report_time is not None
    future_fails = [x for x in res.failed_injury_report_candidates if x["reason"] == FUTURE_REPORT]
    assert len(future_fails) == 2
    art = Path(tmp_path) / "artifacts" / "injury_report_selection" / "2026-05-15.json"
    assert art.is_file()


def test_only_future_candidates_returns_empty_without_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(
        PyPDF2,
        "PdfReader",
        lambda *_a, **_k: MagicMock(pages=[MagicMock()]),
    )

    def fake_get(_url, **_kwargs):
        raise AssertionError("should not download when all slots are future")

    now = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)  # morning ET
    res = fetch_nba_official_injury_report(
        report_day=date(2026, 5, 15),
        now_utc=now,
        repo_root=tmp_path,
        slate_date_for_artifact="2026-05-15",
        requests_get=fake_get,
        candidate_hours=[19, 17],
    )
    assert res.injury_dict == {}
    assert all(r["reason"] == FUTURE_REPORT for r in res.failed_injury_report_candidates)
