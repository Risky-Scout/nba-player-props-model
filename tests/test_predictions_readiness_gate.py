"""Regression: ``scripts/predictions_readiness_gate.py`` must use
America/New_York slate semantics and honor ``--force-run-predict`` for
explicit manual replays.

Run 26006502952 root-caused to the Phase 13AM C1 readiness gate
comparing ``slate_date`` against ``today_utc`` instead of
``today_local``. A workflow_dispatch with ``force_run=true``,
``delivery_date=2026-05-17``, ``mode=derek_pre_tipoff_refresh`` invoked
at 19:59 ET / 00:08 UTC was rejected with::

    WAITING_FOR_PREDICTIONS_VALID_SKIP date=2026-05-17
        mode=derek_pre_tipoff_refresh reason=past_slate today_utc=2026-05-18

despite NBA tipoff for that slate still being hours away in ET and the
operator having explicitly opted into a manual replay. The gate now:

  * compares ``slate_date`` against ``today_local`` (America/New_York),
    so the UTC-overnight window of an ET-still-current slate no longer
    fake-greens; and
  * lets ``--force-run-predict`` (plumbed from ``force_run=true``)
    bypass the past_slate skip for explicit manual replays, so a
    verifier-fix backfill of yesterday's slate doesn't require a
    workflow change to land.
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "predictions_readiness_gate",
    REPO / "scripts" / "predictions_readiness_gate.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


# ── _today_local: ET vs UTC date semantics ─────────────────────────────


def test_today_local_in_utc_overnight_window_returns_et_date():
    """00:08 UTC on 2026-05-18 is still 20:08 ET on 2026-05-17. The
    NBA slate is denominated in ET, so today_local must report 5/17 in
    this window — not 5/18 — which is the exact run 26006502952 case."""
    fake_utc = _dt.datetime(2026, 5, 18, 0, 8, tzinfo=_dt.timezone.utc)
    assert mod._today_local(fake_utc) == "2026-05-17"


def test_today_local_after_et_midnight_advances():
    """At 04:30 UTC on 2026-05-18 = 00:30 ET on 2026-05-18, the ET
    slate has rolled. today_local must report 5/18."""
    fake_utc = _dt.datetime(2026, 5, 18, 4, 30, tzinfo=_dt.timezone.utc)
    assert mod._today_local(fake_utc) == "2026-05-18"


def test_today_local_naive_utc_treated_as_utc():
    """Defensive: naïve datetimes are treated as UTC, not local.
    Keeps the helper safe for callers that forget tzinfo."""
    naive_utc = _dt.datetime(2026, 5, 18, 0, 8)
    assert mod._today_local(naive_utc) == "2026-05-17"


def test_today_local_no_arg_uses_current_utc(monkeypatch):
    """When called with no args, the helper reads the current UTC clock
    and converts to ET."""
    fake_utc = _dt.datetime(2026, 5, 18, 0, 8, tzinfo=_dt.timezone.utc)
    monkeypatch.setattr(mod, "_now_utc", lambda: fake_utc)
    assert mod._today_local() == "2026-05-17"


# ── past_slate / future_slate gating ────────────────────────────────────


def _build_args(**overrides) -> SimpleNamespace:
    """Stand-in for argparse.Namespace covering every field main() uses."""
    base = {
        "date": "2026-05-17",
        "predict_cron_hour_utc": 13,
        "mode": "derek_pre_tipoff_refresh",
        "no_run_predict": False,
        "force_run_predict": False,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _make_gate_main_for_clock(
    monkeypatch: pytest.MonkeyPatch,
    args: SimpleNamespace,
    *,
    fake_utc: _dt.datetime,
    missing_files: bool,
    is_no_games: bool = False,
):
    """Wire a single gate.main() invocation to deterministic inputs and
    capture every (token, fields) emission it would make. Returns the
    captured list."""
    emissions: list[str] = []

    def fake_emit(line: str) -> None:
        emissions.append(line)

    monkeypatch.setattr(mod, "_emit", fake_emit)
    monkeypatch.setattr(mod, "_emit_github_output", lambda *a, **kw: None)
    monkeypatch.setattr(mod, "_now_utc", lambda: fake_utc)
    monkeypatch.setattr(mod, "_is_no_game_slate", lambda d: is_no_games)

    # Stateful missing-files stub: starts in the requested state and
    # transitions to "present" after _run_predict_py is invoked, so the
    # gate's post-predict still_missing check matches real production
    # behavior where predict.py writes the dated artifacts on success.
    state = {"missing": bool(missing_files)}

    def fake_missing(d: str):
        return (
            [Path(f"/fake/predictions/all_props_{d}.parquet")]
            if state["missing"]
            else []
        )

    monkeypatch.setattr(mod, "_missing", fake_missing)

    predict_invocations: list[str] = []

    def fake_run_predict(date: str):
        predict_invocations.append(date)
        state["missing"] = False  # predict.py wrote the dated artifacts
        return (0, "fake predict ok", False)

    monkeypatch.setattr(mod, "_run_predict_py", fake_run_predict)
    monkeypatch.setattr(mod, "_run_publish_nba_props_today", lambda d: 0)
    monkeypatch.setattr(mod, "_run_verifier", lambda d: 0)

    monkeypatch.setattr(
        "sys.argv",
        [
            "predictions_readiness_gate.py",
            "--date",
            args.date,
            "--mode",
            args.mode,
            "--predict-cron-hour-utc",
            str(args.predict_cron_hour_utc),
        ]
        + (["--no-run-predict"] if args.no_run_predict else [])
        + (["--force-run-predict"] if args.force_run_predict else []),
    )
    rc = mod.main()
    return rc, emissions, predict_invocations


def test_past_slate_in_utc_overnight_window_is_same_day_in_et(monkeypatch):
    """C2 regression: at 00:08 UTC on 2026-05-18 the ET slate is still
    5/17. A non-forced run for slate 5/17 must NOT past_slate-skip; it
    should fall through to the same-day logic (which, with predictions
    missing and predict cron not yet fired, valid-skips with
    ``before_predict_cron`` — a different, honest reason)."""
    args = _build_args(date="2026-05-17", force_run_predict=False)
    fake_utc = _dt.datetime(2026, 5, 18, 0, 8, tzinfo=_dt.timezone.utc)

    rc, emissions, predict_invocations = _make_gate_main_for_clock(
        monkeypatch, args, fake_utc=fake_utc, missing_files=True
    )

    assert rc == 0
    joined = "\n".join(emissions)
    assert "past_slate" not in joined, (
        "UTC-overnight window must be treated as same ET slate; "
        "run 26006502952 regression"
    )
    assert "today_local=2026-05-17" in joined
    assert "today_utc=2026-05-18" in joined
    assert "before_predict_cron" in joined  # honest pre-cron skip
    assert predict_invocations == []  # not forced, so no predict.py


def test_past_slate_after_et_midnight_still_skips_without_force(monkeypatch):
    """C1 invariant preserved: at 06:30 UTC on 2026-05-18 ET has
    advanced to 5/18 02:30. A scheduled (non-forced) cron firing for
    yesterday's slate 5/17 must still past_slate-skip and not silently
    fake-green."""
    args = _build_args(date="2026-05-17", force_run_predict=False)
    fake_utc = _dt.datetime(2026, 5, 18, 6, 30, tzinfo=_dt.timezone.utc)

    rc, emissions, predict_invocations = _make_gate_main_for_clock(
        monkeypatch, args, fake_utc=fake_utc, missing_files=True
    )

    assert rc == 0
    joined = "\n".join(emissions)
    assert "past_slate" in joined
    assert "today_local=2026-05-18" in joined
    assert predict_invocations == []  # never call predict.py from past-slate skip


def test_past_slate_manual_replay_override_proceeds_to_predict(monkeypatch):
    """Manual-replay override (run 26006502952 fix): when
    ``--force-run-predict`` is set, the past_slate skip must yield to
    predict.py invocation so a verifier-fix backfill of yesterday's
    slate completes end-to-end without a workflow file change."""
    args = _build_args(date="2026-05-17", force_run_predict=True)
    fake_utc = _dt.datetime(2026, 5, 18, 6, 30, tzinfo=_dt.timezone.utc)

    rc, emissions, predict_invocations = _make_gate_main_for_clock(
        monkeypatch, args, fake_utc=fake_utc, missing_files=True
    )

    assert rc == 0
    joined = "\n".join(emissions)
    assert "past_slate manual replay override" in joined
    assert "force_run_predict=True" in joined
    assert "WAITING_FOR_PREDICTIONS_VALID_SKIP" not in joined.split("PREDICTIONS_READY")[0]
    assert predict_invocations == ["2026-05-17"], (
        "force_run_predict must invoke predict.py for the past slate"
    )
    assert "PREDICTIONS_READY date=2026-05-17" in joined


def test_future_slate_uses_et_today_for_comparison(monkeypatch):
    """At 00:08 UTC on 2026-05-18 = 20:08 ET on 2026-05-17, slate
    2026-05-18 is FUTURE in ET. Must future_slate-skip on ET semantics."""
    args = _build_args(date="2026-05-18", force_run_predict=False)
    fake_utc = _dt.datetime(2026, 5, 18, 0, 8, tzinfo=_dt.timezone.utc)

    rc, emissions, _ = _make_gate_main_for_clock(
        monkeypatch, args, fake_utc=fake_utc, missing_files=True
    )

    assert rc == 0
    joined = "\n".join(emissions)
    assert "future_slate" in joined
    assert "today_local=2026-05-17" in joined


def test_same_day_et_proceeds_when_predictions_present(monkeypatch):
    """When predictions already exist for the slate (e.g. predict cron
    has already fired), the gate proceeds regardless of UTC overnight
    window or force flags. Sanity check that the C2 change doesn't
    regress the happy path."""
    args = _build_args(date="2026-05-17", force_run_predict=False)
    fake_utc = _dt.datetime(2026, 5, 18, 0, 8, tzinfo=_dt.timezone.utc)

    rc, emissions, predict_invocations = _make_gate_main_for_clock(
        monkeypatch, args, fake_utc=fake_utc, missing_files=False
    )

    assert rc == 0
    joined = "\n".join(emissions)
    assert "PREDICTIONS_READY date=2026-05-17" in joined
    assert predict_invocations == []  # files already present


def test_no_run_predict_still_skips_on_past_slate_manual_replay(monkeypatch):
    """``--no-run-predict`` (after-game mode) must still skip even when
    force_run_predict is set, because after-game has no business
    regenerating a past slate's predictions. Defends the
    after-game-job invariant."""
    args = _build_args(
        date="2026-05-17",
        force_run_predict=True,
        no_run_predict=True,
        mode="after_game",
    )
    fake_utc = _dt.datetime(2026, 5, 18, 6, 30, tzinfo=_dt.timezone.utc)

    rc, emissions, predict_invocations = _make_gate_main_for_clock(
        monkeypatch, args, fake_utc=fake_utc, missing_files=True
    )

    assert rc == 0
    joined = "\n".join(emissions)
    assert "PREDICT_NOT_INVOKED" in joined or "no_run_predict" in joined or \
           "WAITING_FOR_PREDICTIONS_VALID_SKIP" in joined
    assert predict_invocations == []
