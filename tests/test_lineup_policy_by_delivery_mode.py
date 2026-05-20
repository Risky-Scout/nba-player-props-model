"""Mode-aware lineup-source policy contract.

Locks in the Phase 12D-amend (May 2026) lineup-source policy:

  * Morning / WoO morning use PROJECTED lineups. They MUST NOT require
    the BDL confirmed-lineup endpoint, because confirmed lineups
    generally do not populate until ~30 minutes before tip.
  * Afternoon WoO refresh uses projected lineups by default; it does
    not gate on confirmed lineups.
  * Derek near-lineup (T-25) prefers confirmed BDL lineups; if not
    available it falls back to projected with status logging.
  * Close-lock (T-5) requires confirmed BDL lineups. Under
    ``force_run=True`` it may proceed with a stamped projected
    fallback for manual smoke tests.

Tests pull the helper directly from ``scripts/run_daily_delivery_pipeline.py``
to avoid touching real BDL endpoints or running the full pipeline.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_daily_delivery_pipeline.py"


def _load_orchestrator_module() -> ModuleType:
    """Load ``scripts/run_daily_delivery_pipeline.py`` as an importable
    module without running its ``main()``.

    The module is heavy at import time (pandas, project deps); for these
    contract tests we only need the helper functions. Loading via
    ``importlib`` keeps the test self-contained and matches the pattern
    used by ``tests/test_nba_pmf_delivery_schedule_resolver.py``.
    """

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "run_daily_delivery_pipeline", str(SCRIPT_PATH)
    )
    assert spec and spec.loader, "could not load run_daily_delivery_pipeline"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def orch() -> ModuleType:
    return _load_orchestrator_module()


# ── 1. Morning mode uses projected lineup ───────────────────────────


@pytest.mark.parametrize(
    "morning_mode",
    ["morning", "woo_morning_monetization"],
)
def test_morning_mode_uses_projected_lineup_policy(orch, morning_mode: str):
    policy = orch._lineup_policy_for_mode(morning_mode)
    assert policy["lineup_source_policy"] == "projected"
    assert policy["run_mode_stamp"] == "morning_expected"
    assert policy["fetch_confirmed_bdl_lineups"] is False
    assert policy["confirmed_lineup_required"] is False
    assert policy["allow_projected_lineup_fallback"] is True


# ── 2. Morning mode does not call fetch_bdl_game_lineups ────────────


def test_morning_preflight_does_not_invoke_bdl_lineup_fetch(
    orch, monkeypatch, capsys
):
    """When ``pipeline_mode`` is morning/WoO morning, the orchestrator's
    pre-stat-grid preflight must NOT shell out to
    ``scripts/fetch_bdl_game_lineups.py``. It logs the projected-skip
    marker instead.
    """

    invocations: list[list[str]] = []

    def fake_run(cmd, label):
        invocations.append(list(cmd))
        return None

    monkeypatch.setattr(orch, "_run", fake_run)
    # Make every optional preflight target script "absent" so we only
    # observe the lineup-fetch gating decision. Targets are pathlib.Path
    # constants in the orchestrator.
    for attr in (
        "FETCH_BDL_LINEUPS",
        "BUILD_AVAILABILITY",
        "VERIFY_ODDSAPI_REGISTRY",
        "VERIFY_AVAILABILITY",
    ):
        fake_path = Path("/nonexistent") / f"{attr.lower()}.py"
        monkeypatch.setattr(orch, attr, fake_path)

    rc = orch._preflight_before_stat_grid(
        "2026-05-20",
        availability_mode="close_lock",
        pipeline_mode="woo_morning_monetization",
        force_run=False,
    )
    assert rc == 0
    # No subprocesses invoked because every target script was made absent
    # AND because the gating decision precedes the fetch path.
    assert invocations == []
    out = capsys.readouterr().out
    assert "LINEUP_POLICY_PROJECTED_SKIP_CONFIRMED_FETCH" in out
    assert "lineup_source_policy=projected" in out


def test_morning_preflight_skips_bdl_fetch_even_when_script_present(
    orch, monkeypatch, capsys, tmp_path: Path
):
    """Even if ``scripts/fetch_bdl_game_lineups.py`` exists on disk,
    morning mode must skip invoking it. This proves the gate is on
    the policy, not on script presence.
    """

    invocations: list[list[str]] = []

    def fake_run(cmd, label):
        invocations.append(list(cmd))
        return None

    monkeypatch.setattr(orch, "_run", fake_run)
    # Force FETCH_BDL_LINEUPS to point at a real existing file so the
    # `.exists()` check would otherwise pass.
    existing = tmp_path / "fetch_bdl_game_lineups.py"
    existing.write_text("# placeholder", encoding="utf-8")
    monkeypatch.setattr(orch, "FETCH_BDL_LINEUPS", existing)
    for attr in ("BUILD_AVAILABILITY", "VERIFY_ODDSAPI_REGISTRY", "VERIFY_AVAILABILITY"):
        monkeypatch.setattr(orch, attr, tmp_path / f"{attr.lower()}.py")

    rc = orch._preflight_before_stat_grid(
        "2026-05-20",
        availability_mode="close_lock",
        pipeline_mode="morning",
        force_run=False,
    )
    assert rc == 0
    # The fetch command must NOT be in the invocations list.
    for cmd in invocations:
        joined = " ".join(str(x) for x in cmd)
        assert "fetch_bdl_game_lineups" not in joined, (
            f"morning mode must not invoke fetch_bdl_game_lineups; got {cmd}"
        )
    out = capsys.readouterr().out
    assert "LINEUP_POLICY_PROJECTED_SKIP_CONFIRMED_FETCH" in out


# ── 3. Derek near-lineup uses confirmed BDL preferred ───────────────


@pytest.mark.parametrize(
    "derek_mode",
    ["derek_pre_tipoff_refresh", "derek_near_lineup", "pre_close"],
)
def test_derek_near_lineup_uses_confirmed_bdl_preferred(
    orch, derek_mode: str
):
    policy = orch._lineup_policy_for_mode(derek_mode)
    assert policy["lineup_source_policy"] == "confirmed_bdl_preferred"
    assert policy["run_mode_stamp"] == "t25"
    assert policy["fetch_confirmed_bdl_lineups"] is True
    # Derek T-25 prefers but does NOT hard-require confirmed lineups —
    # the documented fallback is to projected with status logging.
    assert policy["confirmed_lineup_required"] is False
    assert policy["allow_projected_lineup_fallback"] is True


def test_derek_preflight_invokes_bdl_lineup_fetch(
    orch, monkeypatch, capsys, tmp_path: Path
):
    invocations: list[list[str]] = []

    def fake_run(cmd, label):
        invocations.append(list(cmd))
        return None

    monkeypatch.setattr(orch, "_run", fake_run)
    fetch = tmp_path / "fetch_bdl_game_lineups.py"
    fetch.write_text("# placeholder", encoding="utf-8")
    monkeypatch.setattr(orch, "FETCH_BDL_LINEUPS", fetch)
    for attr in ("BUILD_AVAILABILITY", "VERIFY_ODDSAPI_REGISTRY", "VERIFY_AVAILABILITY"):
        monkeypatch.setattr(orch, attr, tmp_path / f"{attr.lower()}.py")

    rc = orch._preflight_before_stat_grid(
        "2026-05-20",
        availability_mode="close_lock",
        pipeline_mode="derek_pre_tipoff_refresh",
        force_run=False,
    )
    assert rc == 0
    assert any(
        "fetch_bdl_game_lineups" in " ".join(str(x) for x in cmd)
        for cmd in invocations
    ), "derek_pre_tipoff_refresh must invoke fetch_bdl_game_lineups"
    out = capsys.readouterr().out
    assert "LINEUP_POLICY_CONFIRMED_FETCH_PREFERRED" in out


# ── 4. Close-lock uses confirmed BDL required ───────────────────────


def test_close_lock_requires_confirmed_bdl(orch):
    policy = orch._lineup_policy_for_mode("close_lock", force_run=False)
    assert policy["lineup_source_policy"] == "confirmed_bdl_required"
    assert policy["run_mode_stamp"] == "t5"
    assert policy["fetch_confirmed_bdl_lineups"] is True
    assert policy["confirmed_lineup_required"] is True
    assert policy["allow_projected_lineup_fallback"] is False


def test_close_lock_force_run_allows_projected_fallback(orch):
    policy = orch._lineup_policy_for_mode("close_lock", force_run=True)
    assert policy["lineup_source_policy"] == "confirmed_bdl_required"
    assert policy["run_mode_stamp"] == "t5"
    assert policy["fetch_confirmed_bdl_lineups"] is True
    assert policy["confirmed_lineup_required"] is False
    assert policy["allow_projected_lineup_fallback"] is True


def test_close_lock_preflight_hard_skips_when_confirmed_missing(
    orch, monkeypatch, tmp_path: Path, capsys
):
    """Close-lock without ``force_run`` must hard-fail (sys.exit) when
    confirmed lineups are not in the BDL artifact dir.
    """

    monkeypatch.setattr(orch, "_run", lambda cmd, label: None)
    for attr in (
        "FETCH_BDL_LINEUPS",
        "BUILD_AVAILABILITY",
        "VERIFY_ODDSAPI_REGISTRY",
        "VERIFY_AVAILABILITY",
    ):
        monkeypatch.setattr(orch, attr, tmp_path / f"{attr.lower()}.py")
    # Point artifact discovery at an empty tmp_path so aggregate returns
    # no confirmed games.
    monkeypatch.setattr(orch, "REPO_ROOT", tmp_path)

    with pytest.raises(SystemExit) as exc:
        orch._preflight_before_stat_grid(
            "2026-05-20",
            availability_mode="close_lock",
            pipeline_mode="close_lock",
            force_run=False,
        )
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "LINEUP_POLICY_CONFIRMED_LINEUP_MISSING" in out


# ── 5. Manifest stamping by mode ────────────────────────────────────


def test_lineup_status_payload_morning_writes_projected_pre_game(
    orch, monkeypatch, tmp_path: Path
):
    """The payload that feeds the delivery manifest must record
    ``lineup_source_policy=projected``, ``lineup_status=projected_pre_game``,
    and ``lineup_confirmed=False`` for morning mode.
    """

    monkeypatch.setattr(orch, "REPO_ROOT", tmp_path)
    policy = orch._lineup_policy_for_mode("woo_morning_monetization")
    payload = orch._compute_lineup_status_payload("2026-05-20", policy)
    assert payload["lineup_source_policy"] == "projected"
    assert payload["lineup_status"] == "projected_pre_game"
    assert payload["lineup_confirmed"] is False
    assert payload["run_mode_stamp"] == "morning_expected"
    assert payload["confirmed_lineup_required"] is False
    assert payload["projected_lineup_fallback_used"] is True
    assert payload["fetch_confirmed_bdl_lineups_invoked"] is False


def test_lineup_status_payload_derek_with_unavailable_confirmed_marks_fallback(
    orch, monkeypatch, tmp_path: Path
):
    """When Derek mode fetches but confirmed lineups are not yet
    available (the documented morning-time smoke failure), the payload
    must record ``confirmed_lineups_not_available_yet`` and
    ``projected_lineup_fallback_used=True``.
    """

    monkeypatch.setattr(orch, "REPO_ROOT", tmp_path)
    # Simulate a per-game artifact that says "not yet available".
    live = tmp_path / "artifacts" / "live_lineups" / "2026-05-20" / "12345"
    live.mkdir(parents=True)
    (live / "lineup_status.json").write_text(
        json.dumps(
            {
                "lineup_confirmed": False,
                "lineup_blocker": "confirmed_lineups_not_available_yet",
                "lineup_status": "confirmed_lineups_not_available_yet",
            }
        ),
        encoding="utf-8",
    )

    policy = orch._lineup_policy_for_mode("derek_pre_tipoff_refresh")
    payload = orch._compute_lineup_status_payload("2026-05-20", policy)
    assert payload["lineup_source_policy"] == "confirmed_bdl_preferred"
    assert payload["lineup_confirmed"] is False
    assert payload["lineup_status"] == "confirmed_lineups_not_available_yet"
    assert payload["projected_lineup_fallback_used"] is True
    assert payload["fetch_confirmed_bdl_lineups_invoked"] is True


def test_lineup_status_payload_derek_with_confirmed_lineups_marks_confirmed(
    orch, monkeypatch, tmp_path: Path
):
    """When confirmed lineups are present for every game in the
    artifact dir, the payload must record ``lineup_confirmed=True``
    and ``projected_lineup_fallback_used=False``.
    """

    monkeypatch.setattr(orch, "REPO_ROOT", tmp_path)
    for gid in ("100", "200"):
        live = tmp_path / "artifacts" / "live_lineups" / "2026-05-20" / gid
        live.mkdir(parents=True)
        (live / "lineup_status.json").write_text(
            json.dumps(
                {
                    "lineup_confirmed": True,
                    "lineup_status": "confirmed",
                }
            ),
            encoding="utf-8",
        )

    policy = orch._lineup_policy_for_mode("derek_pre_tipoff_refresh")
    payload = orch._compute_lineup_status_payload("2026-05-20", policy)
    assert payload["lineup_confirmed"] is True
    assert payload["lineup_status"] == "confirmed"
    assert payload["projected_lineup_fallback_used"] is False


# ── 6. Audit script does not fail morning for missing confirmed ─────


def test_audit_run_mode_contract_csv_does_not_require_morning_confirmed():
    """Static contract: the audit's run-mode contract CSV must record
    ``official_lineup_required=False`` for ``morning_expected``.

    This is a regression guard against future regressions that would
    fail the WoO morning workflow merely because confirmed lineups
    haven't dropped yet (which is the entire point of morning mode).
    """

    text = (REPO_ROOT / "scripts" / "audit_injury_lineup_run_modes.py").read_text(
        encoding="utf-8"
    )
    # The contract DataFrame literal must contain these exact strings.
    assert (
        '"run_mode": "morning_expected", "official_lineup_required": False'
        in text
    )
    assert (
        '"run_mode": "t25", "official_lineup_required": True'
        in text
    )
    assert (
        '"run_mode": "t5", "official_lineup_required": True'
        in text
    )


def test_audit_emits_per_mode_lineup_policy_markers():
    """The audit script must emit LINEUP_POLICY_PASS / LINEUP_POLICY_AUDIT_FAIL
    markers per run mode so operators can grep the workflow log for the
    morning-vs-near-tip-vs-close-lock contract decisions.
    """

    text = (REPO_ROOT / "scripts" / "audit_injury_lineup_run_modes.py").read_text(
        encoding="utf-8"
    )
    assert "LINEUP_POLICY_PASS" in text
    assert "LINEUP_POLICY_AUDIT_FAIL" in text
    # The three named modes must all be referenced in the per-mode loop.
    assert '"morning_expected", "projected"' in text
    assert '"t25", "confirmed_bdl_preferred"' in text
    assert '"t5", "confirmed_bdl_required"' in text
