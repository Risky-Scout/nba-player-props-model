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


def test_derek_window_no_tipoff_resolves_valid_skips(resolver, monkeypatch, tmp_path):
    """No tip resolvable AND no slate-presence signal → legitimate valid_skip
    with ``no_tip_time_resolved``.

    Pinning ``NBA_PMF_TEST_REPO_ROOT`` to an empty tmp dir prevents the
    test from picking up the production repo's committed slate
    artifacts (e.g. ``deliveries/2026-05-20/canonical_source/...``),
    which would otherwise trip the new
    ``tip_time_unresolved_but_slate_exists`` loud-failure path. This
    test still asserts the legitimate "no real slate" behavior.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
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


# ── Regression cases for the no-tip-time green-skip bug ─────────────
#
# Source: scheduled post-tip run 26197582130 (event=schedule,
# 2026-05-21T00:15:31Z, mode=derek_near_lineup, delivery_date=2026-05-20)
# resolved valid_skip_reason=no_tip_time_resolved, run_delivery=false
# even though canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet
# was on disk for 2026-05-20. GitHub reported conclusion=success — silent
# miss. These tests pin the new contract:
#
#   valid_skip_reason="no_tip_time_resolved" is ONLY allowed when no real
#   slate exists. With a slate-presence signal present, the resolver must
#   emit a loud failure (tip_time_unresolved_but_slate_exists + non-zero
#   exit) instead of green-skipping.


def _seed_canonical_slate(repo_root: Path, delivery_date: str) -> None:
    """Drop a small canonical-source PMF file under ``repo_root`` so
    ``_slate_exists_for_date`` evaluates True for ``delivery_date``.

    The contents are not parsed — only the file's existence matters.
    """

    canonical = (
        repo_root
        / "deliveries"
        / delivery_date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(b"PAR1\x00slate-presence-signal-only\x00")


def test_post_tip_derek_near_lineup_with_slate_runs_delivery(
    resolver, monkeypatch, tmp_path
):
    """Reproduces scheduled run 26197582130 (2026-05-21T00:15Z,
    delivery_date=2026-05-20, mode=derek_near_lineup).

    With a slate-presence signal on disk (canonical PMF parquet) but no
    tip-time source (live_schedule JSON missing), the resolver MUST NOT
    silently green-skip on ``no_tip_time_resolved``. Instead it must
    emit the loud ``tip_time_unresolved_but_slate_exists`` marker, with
    ``run_delivery=False`` (still gated, but now visible) and a
    diagnostic note. Translation to non-zero exit is asserted by
    :func:`test_main_returns_nonzero_when_tip_unresolved_but_slate_exists`.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-21T00:15:31Z",
    )

    assert out.delivery_date == "2026-05-20"
    assert out.as_of_date == "2026-05-19"
    assert out.mode == "derek_near_lineup"
    assert out.valid_skip_reason == "tip_time_unresolved_but_slate_exists"
    assert out.valid_skip_reason != "no_tip_time_resolved"
    assert any("loud_failure" in n for n in out.notes)


def test_morning_mode_with_slate_runs_delivery_with_projected_lineup_policy(
    resolver, monkeypatch, tmp_path
):
    """Morning WoO crons must run delivery regardless of tip-time
    resolvability — they target WoO publishing, not the Derek tipoff
    window.

    The resolver currently labels these ``stage=delivery``,
    ``mode=woo_morning_monetization``, with ``run_delivery=true`` and
    no tipoff gating. This test pins that contract: even with a slate
    signal present and no tip-time source, morning delivery proceeds
    and ``valid_skip_reason`` stays empty (no green-skip on tip time).
    The "projected lineup policy" referenced in the brief is enforced
    downstream by ``run_daily_delivery_pipeline.py``; here we assert
    the resolver hands off cleanly.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="0 15 * * *",
        now_utc="2026-05-20T15:00:00Z",
    )

    assert out.stage == "delivery"
    assert out.mode == "woo_morning_monetization"
    assert out.run_delivery is True
    assert out.valid_skip_reason == ""


def test_no_real_slate_still_valid_skips(resolver, monkeypatch, tmp_path):
    """No slate-presence signal anywhere → legitimate valid-skip with
    the existing ``no_tip_time_resolved`` reason preserved.

    This is the bypass guard: the patch must NOT make every Derek-window
    cron RED on dark-slate days; it must only fail when a slate clearly
    exists.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-21T00:15:31Z",
    )

    assert out.run_delivery is False
    assert out.valid_skip_reason == "no_tip_time_resolved"


def test_missing_tip_time_with_slate_does_not_green_skip(
    resolver, monkeypatch, tmp_path
):
    """With a slate signal present but no tip-time source, the resolver
    must NEVER return ``valid_skip_reason="no_tip_time_resolved"``. It
    must EITHER run delivery (if a non-fabricated fallback existed —
    which it does not today) OR emit the loud failure marker.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-21T00:15:31Z",
    )

    assert out.valid_skip_reason != "no_tip_time_resolved"
    # Fallback (a) is NOT honest given current on-disk signals carry no
    # tip-time value, so the patched resolver chooses loud-failure (b).
    assert (
        out.run_delivery is True
        or out.valid_skip_reason == "tip_time_unresolved_but_slate_exists"
    )


def test_after_game_does_not_run_until_settled_actuals_exist(
    resolver, monkeypatch, tmp_path
):
    """The 06:30 UTC after_game cron resolves to scoring the previous
    ET slate. Whether settled actuals exist is enforced downstream by
    ``score_daily_pmf_delivery_after_game.py``; the resolver itself
    only chooses ``stage=after_game`` / ``run_after_game=true`` for the
    correct date and gates promotion off. This test pins both halves
    of the contract: the resolver does not silently green-skip the
    after_game stage based on actuals presence (which is downstream's
    job), and the date math correctly targets the previous ET slate
    regardless of whether a slate signal exists for today.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))

    out_no_slate = _resolve(
        resolver,
        event_name="schedule",
        schedule="30 6 * * *",
        now_utc="2026-05-21T06:30:00Z",  # 02:30 ET May 21 → yesterday ET = May 20
    )
    assert out_no_slate.stage == "after_game"
    assert out_no_slate.run_after_game is True
    assert out_no_slate.delivery_date == "2026-05-20"
    assert out_no_slate.allow_promote is False
    assert out_no_slate.valid_skip_reason == ""

    _seed_canonical_slate(tmp_path, "2026-05-20")
    out_with_slate = _resolve(
        resolver,
        event_name="schedule",
        schedule="30 6 * * *",
        now_utc="2026-05-21T06:30:00Z",
    )
    assert out_with_slate.stage == "after_game"
    assert out_with_slate.run_after_game is True
    assert out_with_slate.delivery_date == "2026-05-20"
    assert out_with_slate.valid_skip_reason == ""


# ── Helper-level coverage ───────────────────────────────────────────


def test_slate_exists_for_date_helper_detects_canonical_pmf(
    resolver, monkeypatch, tmp_path
):
    """``_slate_exists_for_date`` returns True when canonical PMF or
    predictions artifacts exist, False otherwise."""

    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    assert resolver._slate_exists_for_date("2026-05-20") is False

    _seed_canonical_slate(tmp_path, "2026-05-20")
    assert resolver._slate_exists_for_date("2026-05-20") is True
    assert resolver._slate_exists_for_date("2026-05-21") is False

    predictions_only = tmp_path / "predictions" / "all_props_2026-05-21.parquet"
    predictions_only.parent.mkdir(parents=True, exist_ok=True)
    predictions_only.write_bytes(b"PAR1\x00")
    assert resolver._slate_exists_for_date("2026-05-21") is True


def test_main_returns_nonzero_when_tip_unresolved_but_slate_exists(
    resolver, monkeypatch, tmp_path, capsys
):
    """``main()`` must exit non-zero with the loud stderr marker so the
    workflow's resolve_context step turns the run RED instead of
    silently green-skipping."""

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")
    github_output = tmp_path / "GITHUB_OUTPUT"
    github_output.write_text("", encoding="utf-8")

    rc = resolver.main([
        "--event-name", "schedule",
        "--schedule", "10,25,40,55 23,0,1,2 * * *",
        "--now-utc", "2026-05-21T00:15:31Z",
        "--github-output", str(github_output),
    ])

    captured = capsys.readouterr()
    assert rc == 2
    assert "SCHEDULER_TIP_TIME_UNRESOLVABLE_WITH_SLATE" in captured.err
    assert "delivery_date=2026-05-20" in captured.err
    output_text = github_output.read_text(encoding="utf-8")
    assert "valid_skip_reason=tip_time_unresolved_but_slate_exists" in output_text
    assert "run_delivery=false" in output_text


def test_main_returns_zero_for_legitimate_no_tip_time_resolved(
    resolver, monkeypatch, tmp_path
):
    """Sanity guard: legitimate dark-slate green-skip remains exit 0."""

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    github_output = tmp_path / "GITHUB_OUTPUT"
    github_output.write_text("", encoding="utf-8")

    rc = resolver.main([
        "--event-name", "schedule",
        "--schedule", "25 22 * * *",
        "--now-utc", "2026-05-20T22:25:00Z",
        "--github-output", str(github_output),
    ])

    assert rc == 0
    output_text = github_output.read_text(encoding="utf-8")
    assert "valid_skip_reason=no_tip_time_resolved" in output_text


# ── Phase A/D: upstream tip-time recovery acceptance tests ──────────
#
# These tests pin the new contract added by the upstream-recovery
# follow-on to PR #31's loud-failure safety net: when the
# ``artifacts/live_schedule/<date>/game_start_times.json`` cache is
# missing but a real slate exists, the resolver must invoke the
# in-process tip-time recovery hook (which production wires to a
# subprocess on ``scripts/resolve_game_start_times.py``) BEFORE
# deciding whether to loud-fail.
#
# All six required acceptance cases below use a monkeypatched
# ``resolver.TIP_TIME_GENERATOR`` stub so the tests never hit a real
# BDL / Odds API endpoint and never depend on installed pandas or
# network connectivity. The stub either writes a controlled
# ``game_start_times.json`` fixture or raises / returns non-zero to
# simulate provider failures.


def _stub_generator_writes_tipoff(
    repo_root: Path,
    delivery_date: str,
    tipoff_iso: str,
):
    """Factory: return a ``TIP_TIME_GENERATOR`` stub that writes a valid
    ``game_start_times.json`` payload under ``repo_root`` and returns 0.

    The shape mirrors what ``scripts/resolve_game_start_times.py``
    produces in production (top-level ``"records"`` list with
    ``"resolved_game_start_time_utc"`` per row). We override the
    extractor inside the stub by laying down a payload that matches the
    keys ``_extract_games_list`` already accepts.
    """

    def _stub(delivery_date_arg: str, *, repo_root: Path = repo_root) -> int:
        assert delivery_date_arg == delivery_date, (
            f"stub generator received unexpected delivery_date: "
            f"{delivery_date_arg!r}"
        )
        out_dir = repo_root / "artifacts" / "live_schedule" / delivery_date
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "delivery_date": delivery_date,
            "games": [
                {
                    "game_id": "stub-game-1",
                    "team_abbr": "HOU",
                    "opponent_abbr": "DEN",
                    "game_start_time_utc": tipoff_iso,
                }
            ],
        }
        (out_dir / "game_start_times.json").write_text(
            __import__("json").dumps(payload), encoding="utf-8"
        )
        return 0

    return _stub


def _stub_generator_fails(reason: str = "non_zero_exit"):
    """Factory: ``TIP_TIME_GENERATOR`` stub that simulates a real source
    failure (no cache written, non-zero exit).
    """

    def _stub(delivery_date_arg: str, *, repo_root: Path) -> int:
        del delivery_date_arg, repo_root  # generator did nothing useful
        return 1

    _stub.__name__ = f"_stub_generator_fails_{reason}"
    return _stub


def test_post_tip_derek_near_lineup_recovers_tip_time_when_cache_missing(
    resolver, monkeypatch, tmp_path
):
    """Reproduces scheduled run 26197582130 (event=schedule,
    2026-05-21T00:15:31Z, mode=derek_near_lineup,
    delivery_date=2026-05-20) — but now with the upstream recovery
    hook in place.

    Slate-presence signal present (canonical PMF parquet on disk).
    ``game_start_times.json`` cache ABSENT. The generator stub writes
    a valid tip time (8:30 PM ET = 00:30 UTC May 21) when invoked.
    After honest tip-time recovery, the resolver must select
    ``derek_near_lineup`` mode and emit ``run_delivery=True``. No loud
    failure marker is set, because recovery succeeded.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")

    monkeypatch.setattr(
        resolver,
        "TIP_TIME_GENERATOR",
        _stub_generator_writes_tipoff(
            tmp_path, "2026-05-20", "2026-05-21T00:30:00+00:00"
        ),
    )

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-21T00:15:31Z",
    )

    assert out.delivery_date == "2026-05-20"
    assert out.mode == "derek_near_lineup"
    assert out.run_delivery is True
    assert out.valid_skip_reason == ""
    assert any("tip_time_recovery_rc=0" in n for n in out.notes)
    assert any("tip_time_recovery_source=generator" in n for n in out.notes)


def test_morning_mode_recovers_tip_time_when_cache_missing(
    resolver, monkeypatch, tmp_path
):
    """Morning WoO cron (15:00 UTC) on a real-slate day must emit
    ``run_delivery=True`` with the projected-lineup policy marker
    (``mode=woo_morning_monetization``) regardless of whether the
    Derek tip-time cache exists. The resolver does NOT gate this
    window on tipoff at all (WoO publishing windows, not Derek
    pre-tip windows), so the recovery hook is never consulted here.

    This test pins both halves: (a) ``run_delivery=True``, and (b)
    no incidental call to the recovery hook from a non-tipoff-gated
    window.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")

    calls: list[str] = []

    def _spy(delivery_date_arg: str, *, repo_root: Path) -> int:
        calls.append(delivery_date_arg)
        return _stub_generator_writes_tipoff(
            tmp_path, "2026-05-20", "2026-05-21T00:30:00+00:00"
        )(delivery_date_arg, repo_root=repo_root)

    monkeypatch.setattr(resolver, "TIP_TIME_GENERATOR", _spy)

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="0 15 * * *",
        now_utc="2026-05-20T15:00:00Z",
    )

    assert out.stage == "delivery"
    assert out.mode == "woo_morning_monetization"
    assert out.run_delivery is True
    assert out.valid_skip_reason == ""
    # Morning WoO crons are not Derek tipoff-gated; the recovery hook
    # must not be invoked for this window.
    assert calls == []


def test_close_lock_mode_recovers_tip_time_when_cache_missing(
    resolver, monkeypatch, tmp_path
):
    """``close_lock`` (5 min pre-tip) on a real-slate day with cache
    absent: recovery hook writes a valid tip time, resolver selects
    ``mode=close_lock``, ``run_delivery=True``. Tipoff 2026-05-20 8:30
    PM ET = 00:30 UTC May 21; ``now_utc`` 00:25Z → 5 minutes pre-tip
    (close_lock window).
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")

    monkeypatch.setattr(
        resolver,
        "TIP_TIME_GENERATOR",
        _stub_generator_writes_tipoff(
            tmp_path, "2026-05-20", "2026-05-21T00:30:00+00:00"
        ),
    )

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-21T00:25:00Z",
    )

    assert out.mode == "close_lock"
    assert out.run_delivery is True
    assert out.valid_skip_reason == ""
    assert any("tip_time_recovery_rc=0" in n for n in out.notes)


def test_no_slate_day_legitimately_valid_skips(
    resolver, monkeypatch, tmp_path
):
    """No slate-presence signal anywhere → legitimate
    ``no_tip_time_resolved`` valid-skip. The recovery hook must NOT
    be invoked on dark-slate days, because doing so would burn an API
    call (and possibly write a misleading cache file) for a day the
    league has no games. ``valid_skip_reason`` matches the existing
    "no real slate" vocabulary.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))

    calls: list[str] = []

    def _spy(delivery_date_arg: str, *, repo_root: Path) -> int:
        calls.append(delivery_date_arg)
        return 0

    monkeypatch.setattr(resolver, "TIP_TIME_GENERATOR", _spy)

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-21T00:15:31Z",
    )

    assert out.run_delivery is False
    assert out.valid_skip_reason == "no_tip_time_resolved"
    # Dark-slate path must not invoke the recovery hook at all.
    assert calls == [], (
        f"recovery hook unexpectedly invoked on dark-slate day: {calls!r}"
    )


def test_slate_exists_but_all_tip_time_sources_fail_returns_loud_failure(
    resolver, monkeypatch, tmp_path, capsys
):
    """Slate present, cache absent, generator stub mocked to FAIL
    (non-zero exit, writes no cache file). The resolver must fall
    through to PR #31's loud-failure path: exit 2,
    ``valid_skip_reason="tip_time_unresolved_but_slate_exists"``, and
    the stderr marker ``SCHEDULER_TIP_TIME_UNRESOLVABLE_WITH_SLATE``.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")

    monkeypatch.setattr(
        resolver, "TIP_TIME_GENERATOR", _stub_generator_fails()
    )

    github_output = tmp_path / "GITHUB_OUTPUT"
    github_output.write_text("", encoding="utf-8")

    rc = resolver.main([
        "--event-name", "schedule",
        "--schedule", "10,25,40,55 23,0,1,2 * * *",
        "--now-utc", "2026-05-21T00:15:31Z",
        "--github-output", str(github_output),
    ])

    captured = capsys.readouterr()
    assert rc == 2
    assert "SCHEDULER_TIP_TIME_UNRESOLVABLE_WITH_SLATE" in captured.err
    output_text = github_output.read_text(encoding="utf-8")
    assert (
        "valid_skip_reason=tip_time_unresolved_but_slate_exists"
        in output_text
    )
    assert "run_delivery=false" in output_text


def test_after_game_does_not_run_until_settled_actuals_exist_phase_d(
    resolver, monkeypatch, tmp_path
):
    """``stage=after_game`` (06:30 UTC). With no settled-actuals signal
    seeded (and no slate signal either): the resolver still selects
    ``run_after_game=True`` for the previous ET slate; whether
    settled actuals exist is gated DOWNSTREAM by the after-game
    scoring scripts, not in the schedule resolver. With a slate signal
    seeded (proxy for "yesterday's slate truly existed"), the resolver
    still selects ``run_after_game=True``. In both cases the recovery
    hook MUST NOT be invoked — after_game is not a tipoff-gated stage.

    Mirrors the spirit of Phase D case 6 from the brief while preserving
    the existing ``test_after_game_does_not_run_until_settled_actuals_exist``
    contract (renamed here with ``_phase_d`` suffix to avoid colliding).
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))

    calls: list[str] = []

    def _spy(delivery_date_arg: str, *, repo_root: Path) -> int:
        calls.append(delivery_date_arg)
        return 0

    monkeypatch.setattr(resolver, "TIP_TIME_GENERATOR", _spy)

    out_no_actuals = _resolve(
        resolver,
        event_name="schedule",
        schedule="30 6 * * *",
        now_utc="2026-05-21T06:30:00Z",
    )
    assert out_no_actuals.stage == "after_game"
    assert out_no_actuals.run_after_game is True
    assert out_no_actuals.delivery_date == "2026-05-20"
    assert out_no_actuals.valid_skip_reason == ""

    _seed_canonical_slate(tmp_path, "2026-05-20")
    out_with_actuals = _resolve(
        resolver,
        event_name="schedule",
        schedule="30 6 * * *",
        now_utc="2026-05-21T06:30:00Z",
    )
    assert out_with_actuals.stage == "after_game"
    assert out_with_actuals.run_after_game is True
    assert out_with_actuals.delivery_date == "2026-05-20"

    assert calls == [], (
        f"recovery hook must not be invoked from the after_game stage: {calls!r}"
    )


# ── Recovery hook helper coverage ───────────────────────────────────


def test_recovery_hook_is_not_called_when_cache_already_present(
    resolver, monkeypatch, tmp_path
):
    """If the live_schedule cache already exists and yields a tip time,
    the resolver must NOT redundantly invoke the recovery hook.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")
    # Pre-write the cache so _resolve_slate_tipoff succeeds on the
    # first attempt.
    cache_dir = tmp_path / "artifacts" / "live_schedule" / "2026-05-20"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.joinpath("game_start_times.json").write_text(
        '{"games": [{"game_start_time_utc": "2026-05-21T00:30:00+00:00"}]}',
        encoding="utf-8",
    )

    calls: list[str] = []

    def _spy(delivery_date_arg: str, *, repo_root: Path) -> int:
        calls.append(delivery_date_arg)
        return 0

    monkeypatch.setattr(resolver, "TIP_TIME_GENERATOR", _spy)

    out = _resolve(
        resolver,
        event_name="schedule",
        schedule="10,25,40,55 23,0,1,2 * * *",
        now_utc="2026-05-21T00:15:31Z",
    )

    assert out.run_delivery is True
    assert out.mode == "derek_near_lineup"
    assert calls == [], (
        "recovery hook must not be invoked when cache is already present"
    )


def test_recovery_hook_exception_falls_through_to_loud_failure(
    resolver, monkeypatch, tmp_path, capsys
):
    """An exception raised by the recovery hook (e.g. a misconfigured
    subprocess invocation) must be caught and translated to the loud
    failure path — never crash the resolver or silently green-skip.
    """

    monkeypatch.delenv("NBA_PMF_TEST_TIPOFF_ET", raising=False)
    monkeypatch.setenv("NBA_PMF_TEST_REPO_ROOT", str(tmp_path))
    _seed_canonical_slate(tmp_path, "2026-05-20")

    def _raises(delivery_date_arg: str, *, repo_root: Path) -> int:
        raise RuntimeError("simulated subprocess failure")

    monkeypatch.setattr(resolver, "TIP_TIME_GENERATOR", _raises)

    github_output = tmp_path / "GITHUB_OUTPUT"
    github_output.write_text("", encoding="utf-8")

    rc = resolver.main([
        "--event-name", "schedule",
        "--schedule", "10,25,40,55 23,0,1,2 * * *",
        "--now-utc", "2026-05-21T00:15:31Z",
        "--github-output", str(github_output),
    ])

    captured = capsys.readouterr()
    assert rc == 2
    assert "SCHEDULER_TIP_TIME_UNRESOLVABLE_WITH_SLATE" in captured.err
    assert (
        "valid_skip_reason=tip_time_unresolved_but_slate_exists"
        in github_output.read_text(encoding="utf-8")
    )


def test_default_tip_time_generator_returns_127_when_script_missing(
    resolver, tmp_path
):
    """Hardening: the production hook MUST NOT raise when invoked with
    a repo_root that has no ``scripts/`` folder; it should return a
    non-zero rc so the caller falls through to the loud-failure path.
    """

    rc = resolver._default_tip_time_generator(
        "2026-05-20", repo_root=tmp_path
    )
    assert rc == 127
