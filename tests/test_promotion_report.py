"""Phase 13AN regression tests for the daily model training report.

The previous implementation read the *active champion's* stale
``promotion_manifest.json`` and reported its old ``promoted=true`` even
when today's challenger was NOT promoted. The fix derives promoted
truth from THREE explicit signals (decision-file ``promote``, today's
``promotion_manifest.promoted``, and a champion-pointer cross-check).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build_daily_model_training_report.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "build_daily_model_training_report", SCRIPT
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_challenger_trained_but_not_promoted() -> None:
    """promote=false → challenger_promoted=False, even if a STALE
    promotion_manifest.json from yesterday says promoted=true."""
    mod = _load_script_module()

    pointer = {"champion_model_id": "challenger-2026-04-30"}
    today_decision = {
        "as_of_date": "2026-05-04",
        "promote": False,
        "reason": "gate_failed:market_logloss_non_inferior_or_better",
    }
    # Stale manifest from a prior successful promotion still on disk.
    stale_manifest = {
        "as_of_date": "2026-04-30",
        "promoted": True,
        "to_version": "challenger-2026-04-30",
    }

    status = mod._build_promotion_status(
        as_of_date="2026-05-04",
        pointer=pointer,
        promotion_decision=today_decision,
        promotion_manifest=stale_manifest,
        today_decision_path=Path("/dev/null"),
        today_manifest_path=Path("/dev/null"),
    )
    assert status["promoted"] is False
    assert status["decision_promote_field"] is False
    assert status["active_champion_model_id"] == "challenger-2026-04-30"
    assert status["expected_today_challenger_id"] == "challenger-2026-05-04"
    assert status["champion_pointer_swapped_to_today"] is False
    assert status["promotion_reason"].startswith(
        "gate_failed:market_logloss_non_inferior_or_better"
    )


def test_challenger_actually_promoted() -> None:
    """All three signals say yes → promoted=True."""
    mod = _load_script_module()
    pointer = {"champion_model_id": "challenger-2026-05-04"}
    decision = {"promote": True, "reason": "gates_passed"}
    manifest = {"promoted": True, "to_version": "challenger-2026-05-04"}
    status = mod._build_promotion_status(
        as_of_date="2026-05-04",
        pointer=pointer,
        promotion_decision=decision,
        promotion_manifest=manifest,
        today_decision_path=Path("/dev/null"),
        today_manifest_path=Path("/dev/null"),
    )
    assert status["promoted"] is True
    assert status["decision_promote_field"] is True
    assert status["manifest_promoted_field"] is True
    assert status["champion_pointer_swapped_to_today"] is True


def test_decision_missing_synthesizes_reason() -> None:
    mod = _load_script_module()
    pointer = {"champion_model_id": "challenger-2026-04-30"}
    status = mod._build_promotion_status(
        as_of_date="2026-05-04",
        pointer=pointer,
        promotion_decision=None,
        promotion_manifest=None,
        today_decision_path=Path("/dev/null"),
        today_manifest_path=Path("/dev/null"),
    )
    assert status["promoted"] is False
    assert status["promotion_reason"] == "promotion_decision_missing_or_unparseable"


def test_legacy_decision_promoted_field_alias() -> None:
    """Older promotion_decision.json files used 'promoted' instead of 'promote'."""
    mod = _load_script_module()
    pointer = {"champion_model_id": "challenger-2026-05-04"}
    decision = {"promoted": True, "reason": "legacy_field_name"}
    manifest = {"promoted": True}
    status = mod._build_promotion_status(
        as_of_date="2026-05-04",
        pointer=pointer,
        promotion_decision=decision,
        promotion_manifest=manifest,
        today_decision_path=Path("/dev/null"),
        today_manifest_path=Path("/dev/null"),
    )
    assert status["decision_promote_field"] is True
    assert status["promoted"] is True
