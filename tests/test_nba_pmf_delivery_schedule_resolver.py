"""Tests for ``scripts/resolve_nba_pmf_schedule.py``.

These tests lock in the brief-mandated behavior from
``CURSOR_TASK_NBA_PMF_PRODUCTION_PIPELINE.md`` Phase 1. They run
without any external dependencies beyond the stdlib + pytest.

Test cases (numbered to match the brief Phase 15):

1. Scheduled 06:30 UTC after_game scores previous ET slate.
2. Scheduled 09:30 UTC model_chain allows promotion.
3. Scheduled 15:30 UTC model_chain_no_promote forbids promotion.
4. Scheduled 14:00 UTC predict.
5. Manual delivery dispatch with force_run=true.
6. May 20 8:30 PM ET tip: Derek window transitions.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _load_module():
    """Import ``scripts.resolve_nba_pmf_schedule`` registering it in ``sys.modules``.

    Registering the module is required so the dataclass machinery can
    look up forward-referenced annotations during ``@dataclass``
    evaluation (``ResolverOutputs.notes: list[str]``).
    """

    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    if "resolve_nba_pmf_schedule" in sys.modules:
        del sys.modules["resolve_nba_pmf_schedule"]
    return importlib.import_module("resolve_nba_pmf_schedule")


@pytest.fixture(scope="module")
def resolver():
    return _load_module()


def _resolve(resolver, **kwargs):
    """Build args and dispatch ``resolver.resolve``."""

    defaults = dict(
        event_name="",
        schedule="",
        manual_stage="",
        manual_mode="",
        manual_delivery_date="",
        manual_as_of_date="",
        manual_force_run="false",
        manual_no_promote="true",
        github_output="",
        now_utc="",
    )
    defaults.update(kwargs)

    class _Args:
        pass

    args = _Args()
    for k, v in defaults.items():
        setattr(args, k, v)
    return resolver.resolve(args)


# ── Test 1: 06:30 UTC after-game ────────────────────────────────────


def test_scheduled_0630_after_game_scores_previous_et_slate(resolver):
    """06:30 UTC scores the PREVIOUS ET slate, not today's."""

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="30 6 * * *",
        now_utc="2026-05-21T06:30:00Z",  # 02:30 ET May 21 → yesterday ET = May 20
    )
    assert out.stage == "after_game"
    assert out.mode == "after_game"
    assert out.delivery_date == "2026-05-20"
    assert out.as_of_date == "2026-05-20"
    assert out.run_after_game is True
    assert out.run_verifiers is True
    assert out.run_training is False
    assert out.run_phase8 is False
    assert out.run_phase13 is False
    assert out.run_delivery is False
    assert out.run_predict is False
    assert out.allow_promote is False
    assert out.valid_skip_reason == ""


# ── Test 2: 09:30 UTC model_chain promote ───────────────────────────


def test_scheduled_0930_model_chain_allows_promote(resolver):
    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="30 9 * * *",
        now_utc="2026-05-20T09:30:00Z",
    )
    assert out.stage == "model_chain"
    assert out.run_training is True
    assert out.run_phase8 is True
    assert out.run_phase13 is True
    assert out.allow_promote is True
    assert out.run_verifiers is True
    assert out.run_delivery is False
    assert out.run_after_game is False
    assert out.run_predict is False
    assert out.valid_skip_reason == ""


def test_scheduled_1230_model_chain_allows_promote(resolver):
    """12:30 UTC is the second promotion-allowed model-chain cron."""

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="30 12 * * *",
        now_utc="2026-05-20T12:30:00Z",
    )
    assert out.stage == "model_chain"
    assert out.allow_promote is True


# ── Test 3: 15:30 UTC model_chain_no_promote ────────────────────────


def test_scheduled_1530_model_chain_no_promote_blocks_promotion(resolver):
    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="30 15 * * *",
        now_utc="2026-05-20T15:30:00Z",
    )
    assert out.stage == "model_chain_no_promote"
    assert out.run_training is True
    assert out.run_phase8 is True
    assert out.run_phase13 is True
    assert out.allow_promote is False


@pytest.mark.parametrize("sched,now_utc", [
    ("30 18 * * *", "2026-05-20T18:30:00Z"),
    ("30 21 * * *", "2026-05-20T21:30:00Z"),
])
def test_scheduled_post_cutoff_model_chains_block_promotion(resolver, sched, now_utc):
    """18:30 and 21:30 UTC also forbid promotion (post-14:30 cutoff)."""

    out = _resolve(resolver, event_name="schedule", schedule=sched, now_utc=now_utc)
    assert out.stage == "model_chain_no_promote"
    assert out.allow_promote is False


# ── Test 4: 14:00 UTC predict ───────────────────────────────────────


def test_scheduled_1400_predict_runs_prediction(resolver):
    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="0 14 * * *",
        now_utc="2026-05-20T14:00:00Z",
    )
    assert out.stage == "predict"
    assert out.run_predict is True
    assert out.run_verifiers is True
    assert out.delivery_date == "2026-05-20"
    assert out.as_of_date == "2026-05-19"
    assert out.allow_promote is False


# ── Scheduled delivery crons (WoO morning / afternoon) ──────────────


@pytest.mark.parametrize(
    "sched,expected_mode,now_utc",
    [
        ("0 15 * * *", "woo_morning_monetization", "2026-05-20T15:00:00Z"),
        ("0 18 * * *", "woo_afternoon_refresh", "2026-05-20T18:00:00Z"),
        ("0 20 * * *", "woo_afternoon_refresh", "2026-05-20T20:00:00Z"),
    ],
)
def test_scheduled_woo_delivery_crons(resolver, sched, expected_mode, now_utc):
    out = _resolve(resolver, event_name="schedule", schedule=sched, now_utc=now_utc)
    assert out.stage == "delivery"
    assert out.mode == expected_mode
    assert out.run_delivery is True
    assert out.run_verifiers is True
    assert out.allow_promote is False
    assert out.valid_skip_reason == ""


# ── Test 5: Manual delivery dispatch ────────────────────────────────


def test_manual_delivery_force_run_passes_through(resolver):
    out = _resolve(
        resolver,
        event_name="workflow_dispatch",
        manual_stage="delivery",
        manual_mode="derek_near_lineup",
        manual_delivery_date="2026-05-20",
        manual_as_of_date="2026-05-19",
        manual_force_run="true",
    )
    assert out.stage == "delivery"
    assert out.mode == "derek_near_lineup"
    assert out.delivery_date == "2026-05-20"
    assert out.as_of_date == "2026-05-19"
    assert out.run_delivery is True
    assert out.force_run is True
    assert out.allow_promote is False


def test_manual_model_chain_with_no_promote_false_allows_promotion(resolver):
    """Manual ``stage=model_chain`` with ``no_promote=false`` honors the override."""

    out = _resolve(
        resolver,
        event_name="workflow_dispatch",
        manual_stage="model_chain",
        manual_no_promote="false",
        now_utc="2026-05-20T13:00:00Z",
    )
    assert out.stage == "model_chain"
    assert out.run_training is True
    assert out.run_phase8 is True
    assert out.run_phase13 is True
    assert out.allow_promote is True


def test_manual_model_chain_default_no_promote_blocks_promotion(resolver):
    """Manual ``stage=model_chain`` defaults to ``no_promote=true``."""

    out = _resolve(
        resolver,
        event_name="workflow_dispatch",
        manual_stage="model_chain",
        # manual_no_promote omitted → defaults to "true"
    )
    assert out.stage == "model_chain"
    assert out.allow_promote is False


def test_manual_after_game(resolver):
    out = _resolve(
        resolver,
        event_name="workflow_dispatch",
        manual_stage="after_game",
        manual_delivery_date="2026-05-19",
    )
    assert out.stage == "after_game"
    assert out.run_after_game is True
    assert out.delivery_date == "2026-05-19"


def test_manual_full_cycle(resolver):
    out = _resolve(
        resolver,
        event_name="workflow_dispatch",
        manual_stage="full_cycle",
    )
    assert out.stage == "full_cycle"
    assert out.run_training is True
    assert out.run_phase8 is True
    assert out.run_phase13 is True
    assert out.run_predict is True
    assert out.run_delivery is True
    assert out.run_after_game is False


def test_manual_verifiers_only(resolver):
    out = _resolve(
        resolver,
        event_name="workflow_dispatch",
        manual_stage="verifiers",
    )
    assert out.stage == "verifiers"
    assert out.run_verifiers is True
    assert out.run_training is False
    assert out.run_phase8 is False
    assert out.run_phase13 is False
    assert out.run_delivery is False


# ── Test 6: Derek tipoff window — May 20 8:30 PM ET ─────────────────


@pytest.fixture
def fake_tipoff_2030_et(monkeypatch):
    """Pin tipoff to 2026-05-20 8:30 PM ET (00:30 UTC May 21)."""

    monkeypatch.setenv("NBA_PMF_TEST_TIPOFF_ET", "2026-05-20T20:30:00-04:00")


def test_derek_window_2355_utc_is_near_lineup(resolver, fake_tipoff_2030_et):
    """23:55 UTC → 35 minutes pre-tip → derek_near_lineup."""

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-20T23:55:00Z",
    )
    assert out.mode == "derek_near_lineup"
    assert out.run_delivery is True
    assert out.valid_skip_reason == ""


def test_derek_window_0010_next_day_is_near_lineup(resolver, fake_tipoff_2030_et):
    """00:10 UTC next day → 20 minutes pre-tip → derek_near_lineup."""

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-21T00:10:00Z",
    )
    assert out.mode == "derek_near_lineup"
    assert out.run_delivery is True


def test_derek_window_0025_next_day_is_close_lock(resolver, fake_tipoff_2030_et):
    """00:25 UTC next day → 5 minutes pre-tip → close_lock."""

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-21T00:25:00Z",
    )
    assert out.mode == "close_lock"
    assert out.run_delivery is True


def test_derek_window_2225_too_early_valid_skip(resolver, fake_tipoff_2030_et):
    """22:25 UTC → 125 minutes pre-tip → outside slate delivery window."""

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="25 22 * * *",
        now_utc="2026-05-20T22:25:00Z",
    )
    assert out.run_delivery is False
    assert out.valid_skip_reason == "outside_slate_delivery_window"


def test_derek_window_no_tipoff_resolves_valid_skips(resolver, monkeypatch):
    """No tip resolvable → valid_skip with ``no_tip_time_resolved``."""

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="25 22 * * *",
        now_utc="2026-05-20T22:25:00Z",
    )
    assert out.run_delivery is False
    assert out.valid_skip_reason == "no_tip_time_resolved"


def test_derek_window_30_minutes_pre_tip_is_near_lineup(resolver, fake_tipoff_2030_et):
    """Spot-check the upper boundary of the near-lineup window."""

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="40,55 22 * * *",
        now_utc="2026-05-21T00:00:00Z",  # 30 min pre-tip
    )
    assert out.mode == "derek_near_lineup"


# ── GITHUB_OUTPUT round-trip ────────────────────────────────────────


def test_github_output_round_trip(resolver, tmp_path: Path):
    """The resolver writes valid ``key=value`` lines to $GITHUB_OUTPUT."""

    out_file = tmp_path / "GITHUB_OUTPUT"
    out_file.write_text("", encoding="utf-8")

    outputs = _resolve(
        resolver,
        event_name="schedule",
        schedule="0 14 * * *",
        now_utc="2026-05-20T14:00:00Z",
    )
    resolver.emit(outputs, str(out_file))

    text = out_file.read_text(encoding="utf-8")
    lines = {line.split("=", 1)[0]: line.split("=", 1)[1] for line in text.strip().splitlines()}
    assert lines["stage"] == "predict"
    assert lines["mode"] == "predict"
    assert lines["delivery_date"] == "2026-05-20"
    assert lines["as_of_date"] == "2026-05-19"
    assert lines["run_predict"] == "true"
    assert lines["run_training"] == "false"
    assert lines["allow_promote"] == "false"
    assert lines["valid_skip_reason"] == ""


def test_output_dict_only_contains_brief_required_keys(resolver):
    """The 13 keys must be exactly these, in the brief's order."""

    expected = [
        "delivery_date",
        "as_of_date",
        "stage",
        "mode",
        "run_predict",
        "run_training",
        "run_phase8",
        "run_phase13",
        "run_delivery",
        "run_after_game",
        "run_verifiers",
        "allow_promote",
        "force_run",
        "valid_skip_reason",
    ]
    outputs = _resolve(resolver, event_name="schedule", schedule="0 14 * * *", now_utc="2026-05-20T14:00:00Z")
    assert list(outputs.as_output_dict().keys()) == expected


# ── Unknown / malformed events still produce a stable output ────────


def test_unknown_event_emits_valid_skip(resolver):
    out = _resolve(resolver, event_name="push", now_utc="2026-05-20T12:00:00Z")
    assert out.valid_skip_reason.startswith("unknown_event_")
    assert out.delivery_date  # populated to today ET, not blank
    assert out.as_of_date


def test_unknown_schedule_emits_valid_skip(resolver):
    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="55 4 * * *",  # not in any known cron set
        now_utc="2026-05-20T04:55:00Z",
    )
    assert out.valid_skip_reason.startswith("unknown_schedule_")
    assert out.delivery_date  # always populated
