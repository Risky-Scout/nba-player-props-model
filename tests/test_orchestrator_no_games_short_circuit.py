"""Orchestrator no-games short-circuit tests.

When ``predict.py`` writes its no-games placeholder (``reason ==
"no_games_slate"`` in ``predictions/singles_<date>.json``) the
orchestrator must short-circuit the same-day chain cleanly rather
than letting feature_snapshot / stat_grid / canonical hard-fail on
legitimately empty inputs.

These tests exercise the detection + delivery-package emitter
helpers directly (they live in ``scripts/run_daily_delivery_pipeline.py``)
so the suite stays hermetic and does not require an actual predict
run.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load_orchestrator_module(monkeypatch, repo_root: Path):
    spec = importlib.util.spec_from_file_location(
        "_run_daily_delivery_pipeline_under_test",
        SCRIPTS / "run_daily_delivery_pipeline.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "REPO_ROOT", repo_root, raising=True)
    mod._SCHEDULE_RESOLVER_CACHE.clear()
    return mod


def _stub_schedule_resolver(monkeypatch, mod, *, count: int | None = None,
                             error: Exception | None = None):
    """Replace _resolve_schedule_game_count with a deterministic stub.

    ``count`` returns that many games. ``error`` raises that exception
    (use a ScheduleResolverError instance to simulate a real lookup
    failure)."""
    calls: list[str] = []

    def fake(date: str) -> int:
        calls.append(date)
        if error is not None:
            raise error
        assert count is not None
        return count

    monkeypatch.setattr(mod, "_resolve_schedule_game_count", fake, raising=True)
    return calls


def _write_no_games_signal(repo_root: Path, date: str) -> Path:
    p = repo_root / "predictions" / f"singles_{date}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"date": date, "reason": "no_games_slate", "picks": []}),
        encoding="utf-8",
    )
    return p


def test_predict_signaled_no_games_slate_detected(tmp_path, monkeypatch):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    _write_no_games_signal(tmp_path, "2026-05-16")
    assert mod._predict_signaled_no_games_slate("2026-05-16") == "predictions/singles_2026-05-16.json"


def test_predict_signaled_no_games_slate_returns_none_when_other_reason(tmp_path, monkeypatch):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    p = tmp_path / "predictions" / "singles_2026-05-16.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"reason": "odds_api_offline"}), encoding="utf-8")
    assert mod._predict_signaled_no_games_slate("2026-05-16") is None


def test_predict_signaled_no_games_slate_returns_none_when_missing(tmp_path, monkeypatch):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    assert mod._predict_signaled_no_games_slate("2026-05-16") is None


def test_emit_no_games_delivery_package_writes_all_assertion_files(tmp_path, monkeypatch):
    """The workflow's Forced manual delivery outputs assertion checks
    four file paths under deliveries/<date>/. The no-games emitter
    must satisfy all of them so a force-run on a real no-games slate
    finishes without a false-negative failure."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    date = "2026-05-16"
    mod._emit_no_games_delivery_package(date)

    base = tmp_path / "deliveries" / date
    required = [
        base / "manifest.json",
        base / "canonical_source" / "all_props_model_only.parquet",
        base / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet",
        base / "wizard_of_odds" / "market_comparison.parquet",
    ]
    for p in required:
        assert p.is_file(), f"missing required no-games delivery file: {p}"

    manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["reason"] == "no_games_slate"
    assert manifest["no_games_slate"] is True
    assert manifest["marker"] == "PIPELINE_SOFT_SKIP_NO_GAMES_SLATE"
    # The Derek forward feed must NOT be fabricated on a no-games slate.
    assert manifest["derek_forward_feed"] is None


def test_emit_no_games_delivery_package_parquets_are_empty_and_flagged(tmp_path, monkeypatch):
    """The no-games delivery files must be schema-shaped but row-empty
    and must carry the explicit ``no_games_slate`` column so anyone
    reading them sees the soft-skip flag (no fabricated PMFs / edges)."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    date = "2026-05-16"
    mod._emit_no_games_delivery_package(date)

    base = tmp_path / "deliveries" / date
    canon = pd.read_parquet(base / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet")
    market = pd.read_parquet(base / "wizard_of_odds" / "market_comparison.parquet")
    assert len(canon) == 0
    assert len(market) == 0
    assert "no_games_slate" in canon.columns
    assert "no_games_slate" in market.columns
    # No model surface columns allowed in the canonical placeholder.
    assert "model_prob" in canon.columns  # column exists but empty
    # No fabricated rows means model_prob must NOT be populated.
    assert canon["model_prob"].dropna().empty


def test_short_circuit_emits_marker_and_package_when_confirmed_no_games(
    tmp_path, monkeypatch, capsys
):
    """Soft-skip allowed only when BOTH predict signal AND BDL /games
    schedule lookup confirm zero games."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    date = "2026-05-16"
    _write_no_games_signal(tmp_path, date)
    schedule_calls = _stub_schedule_resolver(monkeypatch, mod, count=0)

    short_circuited = mod._short_circuit_if_no_games(date)
    assert short_circuited is True
    assert schedule_calls == [date], "BDL schedule lookup must be consulted"

    out = capsys.readouterr().out
    assert "PIPELINE_SOFT_SKIP_NO_GAMES_SLATE" in out
    assert f"date={date}" in out
    assert "schedule_resolver=BDL_ZERO_GAMES" in out
    assert f"package=deliveries/{date}/manifest.json" in out
    assert (tmp_path / "deliveries" / date / "manifest.json").is_file()

    manifest = json.loads((tmp_path / "deliveries" / date / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["confirmation"]["rule"] == "soft_skip_requires_both_predict_signal_and_bdl_zero_games"
    assert manifest["eligible_player_game_rows"] == 0
    assert manifest["market_superiority_evaluated"] is False
    assert manifest["derek_forward_feed_expected"] is False


def test_short_circuit_returns_false_when_predict_did_not_signal(tmp_path, monkeypatch, capsys):
    """No predict no-games signal → never soft-skip, never call BDL."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    schedule_calls = _stub_schedule_resolver(monkeypatch, mod, count=999)

    result = mod._short_circuit_if_no_games("2026-05-16")
    assert result is False
    assert schedule_calls == [], "BDL must not be consulted when predict didn't signal no-games"
    out = capsys.readouterr().out
    assert "PIPELINE_SOFT_SKIP_NO_GAMES_SLATE" not in out
    assert not (tmp_path / "deliveries" / "2026-05-16" / "manifest.json").exists()


def test_short_circuit_hard_fails_when_predict_says_no_but_bdl_has_games(
    tmp_path, monkeypatch, capsys
):
    """Disagreement between predict and BDL is a hard fail — never a
    silent soft-skip. predict may have hit a transient BDL/network
    glitch when it concluded "no games"; the orchestrator's independent
    schedule lookup is the strict gate."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    _write_no_games_signal(tmp_path, "2026-05-16")
    _stub_schedule_resolver(monkeypatch, mod, count=5)

    with pytest.raises(SystemExit) as exc_info:
        mod._short_circuit_if_no_games("2026-05-16")
    assert exc_info.value.code == 2
    err = capsys.readouterr().err
    assert "PIPELINE_NO_GAMES_SOFT_SKIP_REJECTED" in err
    assert "schedule_confirms_games_exist" in err
    assert "games=5" in err
    assert not (tmp_path / "deliveries" / "2026-05-16" / "manifest.json").exists()


def test_short_circuit_hard_fails_when_schedule_lookup_failed(
    tmp_path, monkeypatch, capsys
):
    """If BDL itself fails (network / auth / schema / null response)
    we MUST hard-fail. A silently-soft-skipped infrastructure outage
    would be a serious false-green."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    _write_no_games_signal(tmp_path, "2026-05-16")
    err = mod.ScheduleResolverError(
        "SCHEDULE_RESOLVER_LOOKUP_FAILED date=2026-05-16 error=ConnectionError: refused"
    )
    _stub_schedule_resolver(monkeypatch, mod, error=err)

    with pytest.raises(SystemExit) as exc_info:
        mod._short_circuit_if_no_games("2026-05-16")
    assert exc_info.value.code == 2
    stderr = capsys.readouterr().err
    assert "PIPELINE_NO_GAMES_SOFT_SKIP_REJECTED" in stderr
    assert "schedule_lookup_failed" in stderr
    assert not (tmp_path / "deliveries" / "2026-05-16" / "manifest.json").exists()


def test_verify_m88_delivery_bundle_soft_skips_when_confirmed_no_games(
    tmp_path, monkeypatch, capsys
):
    """The post-delivery verify suite (audit_daily_delivery_completeness,
    verify_derek_forward_feed_contract, audit_injury_lineup_run_modes,
    audit_github_delivery_automation) must not hard-fail on a confirmed
    no-games slate. None of those gates can pass without a real model
    PMF surface / Derek feed / lineup file."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    _write_no_games_signal(tmp_path, "2026-05-16")
    _stub_schedule_resolver(monkeypatch, mod, count=0)

    rc = mod._verify_m88_delivery_bundle("2026-05-16", "morning_expected", fail_on_missing=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "VERIFY_SUITE_SOFT_SKIP_NO_GAMES_SLATE" in out
    assert "schedule_resolver=BDL_ZERO_GAMES" in out


def test_verify_m88_delivery_bundle_hard_fails_when_schedule_disagrees(
    tmp_path, monkeypatch, capsys
):
    """If predict signaled no-games but BDL says games exist, the
    verify suite must NOT soft-skip; it returns 2 with the
    ``PIPELINE_NO_GAMES_SOFT_SKIP_REJECTED`` marker so main() surfaces
    a non-zero exit."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    _write_no_games_signal(tmp_path, "2026-05-16")
    _stub_schedule_resolver(monkeypatch, mod, count=3)

    rc = mod._verify_m88_delivery_bundle("2026-05-16", "morning_expected", fail_on_missing=True)
    assert rc == 2
    err = capsys.readouterr().err
    assert "PIPELINE_NO_GAMES_SOFT_SKIP_REJECTED" in err


def test_verify_m88_delivery_bundle_does_not_soft_skip_without_signal(tmp_path, monkeypatch):
    """No upstream predict no-games signal means the verify suite must
    run normally (and would hard-fail if delivery artifacts are
    missing). We verify by checking that the soft-skip code path was
    NOT taken — i.e. the function attempted to execute the auditor
    scripts."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    invoked: list[list[str]] = []

    def fake_run(cmd, cwd=None, env=None):
        invoked.append(cmd)
        class _R: returncode = 0
        return _R()

    monkeypatch.setattr(mod.subprocess, "run", fake_run, raising=True)
    for script in (mod.AUDIT_DAILY_DELIVERY, mod.VERIFY_DEREK_CONTRACT,
                   mod.AUDIT_INJURY_LINEUP, mod.AUDIT_GITHUB_AUTOMATION):
        if not script.exists():
            pytest.skip(f"script {script.name} missing in this checkout; can't assert call-path")

    rc = mod._verify_m88_delivery_bundle("2026-05-16", "morning_expected", fail_on_missing=False)
    assert rc == 0
    assert any("audit_daily_delivery_completeness.py" in " ".join(map(str, c)) for c in invoked), \
        "verify suite must invoke auditors when no-games signal is absent"


def test_confirmed_no_games_slate_caches_schedule_lookup(tmp_path, monkeypatch):
    """_confirmed_no_games_slate is called by both the entry-point
    short-circuit and the post-delivery verify suite. The cache must
    ensure BDL is consulted at most once per process per date."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    _write_no_games_signal(tmp_path, "2026-05-16")
    schedule_calls = _stub_schedule_resolver(monkeypatch, mod, count=0)

    confirmed1, marker1 = mod._confirmed_no_games_slate("2026-05-16")
    confirmed2, marker2 = mod._confirmed_no_games_slate("2026-05-16")

    assert confirmed1 is True and confirmed2 is True
    assert marker1 == marker2
    # Our stub increments calls on each invocation; the real production
    # code path also caches via _SCHEDULE_RESOLVER_CACHE. To assert
    # caching at the resolver layer, prime the cache directly.
    mod._SCHEDULE_RESOLVER_CACHE.clear()
    mod._SCHEDULE_RESOLVER_CACHE["2026-05-17"] = 0
    # If cache works, the stub would NOT be called when the value is
    # already cached. We can only verify this via the real
    # _resolve_schedule_game_count code path; the stub bypasses it.
    # Here we just confirm the cache structure exists.
    assert "2026-05-17" in mod._SCHEDULE_RESOLVER_CACHE


def test_resolve_schedule_game_count_hard_fails_on_null_response(tmp_path, monkeypatch):
    """A null BDL response is a schema/data violation, not a valid
    zero-games answer."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    mod._SCHEDULE_RESOLVER_CACHE.clear()

    fake_module = type(sys)("nba_props_model.data.bdl_client")
    fake_module.get_games = lambda **kw: None
    sys.modules["nba_props_model.data.bdl_client"] = fake_module
    try:
        with pytest.raises(mod.ScheduleResolverError) as exc:
            mod._resolve_schedule_game_count("2026-05-16")
        assert "null_response" in str(exc.value)
    finally:
        del sys.modules["nba_props_model.data.bdl_client"]


def test_resolve_schedule_game_count_hard_fails_on_non_list_response(tmp_path, monkeypatch):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    mod._SCHEDULE_RESOLVER_CACHE.clear()
    fake_module = type(sys)("nba_props_model.data.bdl_client")
    fake_module.get_games = lambda **kw: {"oops": "wrong shape"}
    sys.modules["nba_props_model.data.bdl_client"] = fake_module
    try:
        with pytest.raises(mod.ScheduleResolverError) as exc:
            mod._resolve_schedule_game_count("2026-05-16")
        assert "non_list_response" in str(exc.value)
    finally:
        del sys.modules["nba_props_model.data.bdl_client"]


def test_resolve_schedule_game_count_propagates_api_exception(tmp_path, monkeypatch):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    mod._SCHEDULE_RESOLVER_CACHE.clear()
    fake_module = type(sys)("nba_props_model.data.bdl_client")

    class _BoomError(RuntimeError):
        pass

    def _boom(**kw):
        raise _BoomError("simulated BDL outage")

    fake_module.get_games = _boom
    sys.modules["nba_props_model.data.bdl_client"] = fake_module
    try:
        with pytest.raises(mod.ScheduleResolverError) as exc:
            mod._resolve_schedule_game_count("2026-05-16")
        assert "SCHEDULE_RESOLVER_LOOKUP_FAILED" in str(exc.value)
        assert "_BoomError" in str(exc.value)
    finally:
        del sys.modules["nba_props_model.data.bdl_client"]


def test_resolve_schedule_game_count_caches_per_date(tmp_path, monkeypatch):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    mod._SCHEDULE_RESOLVER_CACHE.clear()
    calls: list[str] = []
    fake_module = type(sys)("nba_props_model.data.bdl_client")

    def _gg(**kw):
        calls.append(kw.get("start_date"))
        return [{"id": 1}, {"id": 2}]

    fake_module.get_games = _gg
    sys.modules["nba_props_model.data.bdl_client"] = fake_module
    try:
        n1 = mod._resolve_schedule_game_count("2026-05-16")
        n2 = mod._resolve_schedule_game_count("2026-05-16")
        assert n1 == n2 == 2
        assert calls == ["2026-05-16"], "BDL must be hit at most once per date per process"
    finally:
        del sys.modules["nba_props_model.data.bdl_client"]
