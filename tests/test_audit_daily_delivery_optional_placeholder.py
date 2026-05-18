"""Regression: optional after-game placeholder JSON must not fail morning audit."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

from nba_props_model.delivery.delivery_contract import DeliveryFileSpec, FilePresence, RunMode

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_audit_mod():
    p = REPO_ROOT / "scripts" / "audit_daily_delivery_completeness.py"
    spec = importlib.util.spec_from_file_location("audit_daily_delivery_completeness_mod", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def audit_mod():
    return _load_audit_mod()


def test_passes_allows_optional_after_game_placeholder_warn_flag(audit_mod):
    rows = [
        {
            "expected": "optional",
            "failure_reason": "",
            "exists": True,
            "placeholder_value_count": 3,
            "optional_after_game_placeholder_warn": True,
            "required_columns_present": None,
        }
    ]
    assert audit_mod._passes(rows) is True


def test_audit_date_downgrades_placeholder_manifest_for_morning_expected(
    audit_mod, tmp_path: Path
):
    date = "2026-05-15"
    delivery_root = tmp_path / "deliveries" / date
    ag = delivery_root / "after_game_scoring"
    ag.mkdir(parents=True)
    placeholder = ag / "after_game_scoring_placeholder_manifest.json"
    placeholder.write_text(
        '{"reason": "placeholder until scorer runs", "after_game_scoring_status": "pending_actuals"}\n',
        encoding="utf-8",
    )

    spec = DeliveryFileSpec(
        audit_mod.OPTIONAL_AFTER_GAME_PLACEHOLDER_REL,
        {m: FilePresence.OPTIONAL for m in RunMode},
    )
    with patch.object(audit_mod, "delivery_file_specs", lambda: [spec]):
        rows = audit_mod.audit_date(
            delivery_root,
            date,
            RunMode.MORNING_EXPECTED,
            include_current=False,
        )

    assert len(rows) == 1
    assert rows[0].get("optional_after_game_placeholder_warn") is True
    assert rows[0].get("failure_reason") == ""
    assert audit_mod._passes(rows) is True


@pytest.mark.parametrize(
    "mode",
    [RunMode.MORNING_EXPECTED, RunMode.T25, RunMode.T5, RunMode.BACKTEST],
)
def test_audit_date_downgrades_placeholder_manifest_for_every_pregame_mode(
    audit_mod, tmp_path: Path, mode: RunMode
):
    """The after-game placeholder manifest is a legitimate pre-game stub.

    Regression: production run 26012478679 (daily_pmf_delivery,
    delivery_date=2026-05-18) failed
    ``DAILY_DELIVERY_COMPLETENESS_AUDIT_FAIL`` because the
    placeholder manifest content literally contains the substring
    ``placeholder``. The audit's banned-token exemption only fired in
    ``morning_expected`` mode; this regression locks in the same
    exemption for every pre-game RunMode (``t25``, ``t5``,
    ``morning_expected``, ``backtest``).
    """

    date = "2026-05-18"
    delivery_root = tmp_path / "deliveries" / date
    ag = delivery_root / "after_game_scoring"
    ag.mkdir(parents=True)
    placeholder = ag / "after_game_scoring_placeholder_manifest.json"
    placeholder.write_text(
        '{"reason": "placeholder until scorer runs", "after_game_scoring_status": "pending_actuals"}\n',
        encoding="utf-8",
    )

    spec = DeliveryFileSpec(
        audit_mod.OPTIONAL_AFTER_GAME_PLACEHOLDER_REL,
        {m: FilePresence.OPTIONAL for m in RunMode},
    )
    with patch.object(audit_mod, "delivery_file_specs", lambda: [spec]):
        rows = audit_mod.audit_date(
            delivery_root,
            date,
            mode,
            include_current=False,
        )

    assert len(rows) == 1, rows
    assert rows[0].get("optional_after_game_placeholder_warn") is True, rows[0]
    assert rows[0].get("failure_reason") == "", rows[0]
    assert audit_mod._passes(rows) is True


def test_audit_date_still_fails_placeholder_manifest_for_final_after_game(
    audit_mod, tmp_path: Path
):
    """In FINAL_AFTER_GAME the placeholder must be replaced by real data.

    The exemption is intentionally scoped to pre-game modes only — if
    the placeholder manifest survives into ``final_after_game`` the
    audit should still surface that as a genuine post-game scoring
    regression instead of silently passing.
    """

    date = "2026-05-15"
    delivery_root = tmp_path / "deliveries" / date
    ag = delivery_root / "after_game_scoring"
    ag.mkdir(parents=True)
    placeholder = ag / "after_game_scoring_placeholder_manifest.json"
    placeholder.write_text(
        '{"reason": "placeholder until scorer runs", "after_game_scoring_status": "pending_actuals"}\n',
        encoding="utf-8",
    )

    spec = DeliveryFileSpec(
        audit_mod.OPTIONAL_AFTER_GAME_PLACEHOLDER_REL,
        {m: FilePresence.OPTIONAL for m in RunMode},
    )
    with patch.object(audit_mod, "delivery_file_specs", lambda: [spec]):
        rows = audit_mod.audit_date(
            delivery_root,
            date,
            RunMode.FINAL_AFTER_GAME,
            include_current=False,
        )

    assert len(rows) == 1
    assert rows[0].get("failure_reason") == "placeholder_or_banned_token"
    assert rows[0].get("optional_after_game_placeholder_warn") is not True
    assert audit_mod._passes(rows) is False
