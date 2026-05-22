"""Tests for the --as-of-date argument on scripts/train.py and the
corresponding filtering logic in pipelines/train.py.

Guardrails verified:
  - scripts/train.py CLI accepts --as-of-date
  - fetch_all_data respects as_of_date (no rows > AS_OF_DATE returned)
  - build_training_table filters rows to <= as_of_date
  - workflow passes resolved as_of_date to training-table rebuild
  - workflow is freshness-aware (not just file-existence-aware)
  - no hardcoded YYYY-MM-DD dates introduced in the workflow (except
    pre-existing phase13 start-date and diagnostics window constants)
  - verify_training_data_alignment.py is called without || true
  - Phase 8 still includes allowed stats pts,reb,ast,tov,fg3m,stl,blk
  - delivery layout / schema untouched
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "nba_pmf_delivery.yml"
TRAIN_CLI = REPO_ROOT / "scripts" / "train.py"
PIPELINE_TRAIN = REPO_ROOT / "src" / "nba_props_model" / "pipelines" / "train.py"
VERIFIER = REPO_ROOT / "scripts" / "verify_training_data_alignment.py"


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow() -> dict:
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    on = data.get("on") or data.get(True)
    assert on is not None
    data["__on__"] = on
    return data


# ── CLI contract ───────────────────────────────────────────────────────────────


def test_train_cli_accepts_as_of_date():
    """scripts/train.py must parse --as-of-date without error."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    # Import with importlib to avoid side effects
    import importlib.util

    spec = importlib.util.spec_from_file_location("train_cli", TRAIN_CLI)
    mod = importlib.util.module_from_spec(spec)
    # Patch sys.argv then call _cli()
    with patch("sys.argv", ["train.py", "--as-of-date", "2026-05-20", "--build-table-only"]):
        spec.loader.exec_module(mod)
        args = mod._cli()
    assert args.as_of_date == "2026-05-20"
    assert args.build_table_only is True


def test_train_cli_as_of_date_defaults_none():
    """--as-of-date must default to None when omitted."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("train_cli2", TRAIN_CLI)
    mod = importlib.util.module_from_spec(spec)
    with patch("sys.argv", ["train.py"]):
        spec.loader.exec_module(mod)
        args = mod._cli()
    assert args.as_of_date is None


# ── fetch_all_data filtering ───────────────────────────────────────────────────


def _make_stats_df(*dates: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "player_id": range(len(dates)),
            "game_id": range(len(dates)),
            "game_date": list(dates),
            "min": [20.0] * len(dates),
            "pts": [10.0] * len(dates),
        }
    )


def test_fetch_all_data_load_from_disk_filters_to_as_of_date(tmp_path, monkeypatch):
    """When the on-disk parquet has rows beyond as_of_date, fetch_all_data
    must return only rows with game_date <= as_of_date."""
    import importlib
    import nba_props_model.pipelines.train as _train_mod

    # Patch DATA_DIR to tmp_path
    monkeypatch.setattr(_train_mod, "DATA_DIR", tmp_path)

    # Write a parquet with dates 2026-05-19, 2026-05-20, 2026-05-21
    stats_path = tmp_path / "player_game_stats.parquet"
    adv_path = tmp_path / "advanced_stats.parquet"
    odds_path = tmp_path / "game_odds.parquet"
    df_full = _make_stats_df("2026-05-19", "2026-05-20", "2026-05-21")
    df_full.to_parquet(stats_path, index=False)
    pd.DataFrame().to_parquet(adv_path, index=False)
    pd.DataFrame().to_parquet(odds_path, index=False)

    # Stub BDL API key so the function doesn't fail on secrets
    with patch.dict("os.environ", {"BDL_API_KEY": "fake-key"}):
        stats_df, adv_df, odds_df = _train_mod.fetch_all_data(as_of_date="2026-05-20")

    assert len(stats_df) == 2, (
        f"Expected 2 rows (<= 2026-05-20), got {len(stats_df)}: "
        f"{stats_df['game_date'].tolist()}"
    )
    assert stats_df["game_date"].astype(str).str[:10].max() == "2026-05-20"


def test_fetch_all_data_no_future_rows_when_as_of_date_provided(tmp_path, monkeypatch):
    """No row returned by fetch_all_data may have game_date > as_of_date."""
    import nba_props_model.pipelines.train as _train_mod

    monkeypatch.setattr(_train_mod, "DATA_DIR", tmp_path)

    stats_path = tmp_path / "player_game_stats.parquet"
    df_full = _make_stats_df("2026-05-18", "2026-05-20", "2026-05-21", "2026-05-22")
    df_full.to_parquet(stats_path, index=False)
    pd.DataFrame().to_parquet(tmp_path / "advanced_stats.parquet", index=False)
    pd.DataFrame().to_parquet(tmp_path / "game_odds.parquet", index=False)

    with patch.dict("os.environ", {"BDL_API_KEY": "fake-key"}):
        stats_df, _, _ = _train_mod.fetch_all_data(as_of_date="2026-05-20")

    future = stats_df[stats_df["game_date"].astype(str).str[:10] > "2026-05-20"]
    assert future.empty, (
        f"fetch_all_data returned future rows: {future['game_date'].tolist()}"
    )


# ── build_training_table filtering ────────────────────────────────────────────


def test_build_training_table_no_rows_beyond_as_of_date(tmp_path, monkeypatch):
    """build_training_table must not produce any row with game_date > as_of_date."""
    import nba_props_model.pipelines.train as _train_mod

    monkeypatch.setattr(_train_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(_train_mod, "INJURY_SNAPSHOT_PATH", tmp_path / "injury_snapshots.parquet")

    # Build a stats_df that contains a row for 2026-05-21
    n_players = 3
    rows = []
    for pid in range(n_players):
        for game_num in range(20):  # 20 games per player so MIN_GAMES=15 is satisfied
            rows.append(
                {
                    "player_id": pid,
                    "player_name": f"Player {pid}",
                    "game_id": pid * 100 + game_num,
                    "game_date": (
                        pd.Timestamp("2026-01-01") + pd.Timedelta(days=game_num * 3)
                    ).strftime("%Y-%m-%d"),
                    "season": 2025,
                    "home_team_id": 1,
                    "visitor_team_id": 2,
                    "team_id": 1,
                    "team_abbr": "TST",
                    "min": 30.0,
                    "pts": 20.0,
                    "reb": 5.0,
                    "ast": 4.0,
                    "fg3m": 2.0,
                    "stl": 1.0,
                    "blk": 0.5,
                    "turnover": 1.5,
                    "fga": 10.0,
                    "fg3a": 5.0,
                    "fta": 4.0,
                    "ftm": 3.0,
                    "oreb": 1.0,
                    "dreb": 4.0,
                    "pf": 2.0,
                    "fg_pct": 0.5,
                    "fg3_pct": 0.4,
                    "ft_pct": 0.75,
                }
            )
    stats_df = pd.DataFrame(rows)

    # Inject a future row that should be filtered out
    future_row = rows[0].copy()
    future_row["game_date"] = "2026-05-22"
    future_row["game_id"] = 9999
    stats_df = pd.concat([stats_df, pd.DataFrame([future_row])], ignore_index=True)

    as_of_date = "2026-05-20"

    # Call with the as_of_date; we need to stub many internals
    with (
        patch.object(_train_mod, "build_game_context_map", return_value={}),
        patch.object(
            _train_mod,
            "build_player_game_features",
            return_value={"dummy_feat": 0.0},
        ),
        patch.object(_train_mod, "add_interaction_features", side_effect=lambda d, _: d),
        patch.object(_train_mod, "set_league_3p_prior", return_value=None),
    ):
        df = _train_mod.build_training_table(
            stats_df, pd.DataFrame(), pd.DataFrame(), as_of_date=as_of_date
        )

    if not df.empty:
        future_rows = df[df["game_date"].astype(str).str[:10] > as_of_date]
        assert future_rows.empty, (
            f"training_table has rows beyond as_of_date={as_of_date}: "
            f"{future_rows['game_date'].unique().tolist()}"
        )


# ── Workflow structural checks ─────────────────────────────────────────────────


def _steps(workflow: dict, job: str) -> list[dict]:
    return [s for s in workflow["jobs"][job]["steps"] if isinstance(s, dict)]


def test_workflow_phase8_training_table_passes_as_of_date(workflow_text):
    """Phase 8 'Build training table' step must pass --as-of-date to train.py."""
    assert '--as-of-date "$ASOF"' in workflow_text, (
        "Phase 8 training table rebuild must pass --as-of-date"
    )


def test_workflow_phase8_training_table_is_freshness_aware(workflow_text):
    """Phase 8 must rebuild training table if max date != as_of_date,
    not only when the file is absent."""
    body_start = workflow_text.index("Build training table if absent or stale")
    body = workflow_text[body_start : body_start + 3000]
    assert "ACTUAL_MAX" in body, (
        "Phase 8 training table step must check existing table's max date"
    )
    assert "NEED_BUILD=true" in body
    assert "!= as_of_date" in body or "!= $ASOF" in body or "ACTUAL_MAX" in body


def test_workflow_phase8_verifies_max_date_after_build(workflow_text):
    """After building the training table, the workflow must verify max date == ASOF."""
    body_start = workflow_text.index("Build training table if absent or stale")
    body = workflow_text[body_start : body_start + 3000]
    assert "FINAL_MAX" in body, (
        "Phase 8 must verify training table max date after build"
    )
    assert "exit 1" in body


def test_workflow_phase8_calls_verifier_before_calibration(workflow):
    """Phase 8 must call verify_training_data_alignment.py before calibration folds."""
    steps = _steps(workflow, "phase8_pmf_calibration_diagnostics_market_eval")
    verifier_idx = None
    calibration_idx = None
    for i, step in enumerate(steps):
        run = step.get("run", "") or ""
        if "verify_training_data_alignment.py" in run and verifier_idx is None:
            verifier_idx = i
        if "scripts/calibrate_pmf.py" in run and calibration_idx is None:
            calibration_idx = i
    assert verifier_idx is not None, (
        "phase8 must contain verify_training_data_alignment.py step"
    )
    assert calibration_idx is not None, (
        "phase8 must contain calibrate_pmf.py step"
    )
    assert verifier_idx < calibration_idx, (
        "verify_training_data_alignment.py must run before calibrate_pmf.py"
    )


def test_workflow_model_chain_calls_verifier_before_training(workflow):
    """model_chain must call verify_training_data_alignment.py before
    run_nightly_training_and_calibration.py."""
    steps = _steps(workflow, "model_chain_training_calibration")
    verifier_idx = None
    training_idx = None
    for i, step in enumerate(steps):
        run = step.get("run", "") or ""
        if "verify_training_data_alignment.py" in run and verifier_idx is None:
            verifier_idx = i
        if "run_nightly_training_and_calibration.py" in run and training_idx is None:
            training_idx = i
    assert verifier_idx is not None, (
        "model_chain must contain verify_training_data_alignment.py step"
    )
    assert training_idx is not None
    assert verifier_idx < training_idx, (
        "verify_training_data_alignment.py must precede nightly training"
    )


def test_workflow_verifier_not_suppressed(workflow_text):
    """verify_training_data_alignment.py must never be called with || true."""
    for line in workflow_text.splitlines():
        if "verify_training_data_alignment.py" in line:
            assert "|| true" not in line, (
                f"verify_training_data_alignment.py suppressed with || true: {line!r}"
            )


def test_workflow_no_newly_hardcoded_dates(workflow_text):
    """No 2026-05-2x or similar dates must be hardcoded in the workflow
    (the root bug was a hardcoded date that caused misalignment)."""
    # Pre-existing allowed constants: phase13 start date + diagnostics window
    allowed_hardcoded = {"2023-10-24", "2026-04-01"}
    found = set(re.findall(r"\b20\d\d-\d\d-\d\d\b", workflow_text))
    disallowed = found - allowed_hardcoded
    assert not disallowed, (
        f"Hardcoded ISO dates found in workflow (not in allowed set): {disallowed}. "
        f"Use resolver outputs (${{{{ needs.resolve_context.outputs.as_of_date }}}}) "
        f"instead."
    )


def test_workflow_resolver_outputs_used_in_training_table_step(workflow_text):
    """The training table rebuild must source as_of_date from the resolver,
    not a hardcoded literal."""
    assert (
        'needs.resolve_context.outputs.as_of_date' in workflow_text
    )
    body_start = workflow_text.index("Build training table if absent or stale")
    body = workflow_text[body_start : body_start + 3000]
    assert "needs.resolve_context.outputs.as_of_date" in body


# ── Phase 8 allowed stats regression guard ────────────────────────────────────


def test_phase8_still_includes_allowed_stats(workflow):
    """Phase 8 OOF folds must still include pts,reb,ast,tov,fg3m,stl,blk."""
    steps = _steps(workflow, "phase8_pmf_calibration_diagnostics_market_eval")
    for step in steps:
        run = step.get("run", "") or ""
        if "calibrate_pmf.py" in run and "--allowed-stats" in run:
            assert "pts" in run
            assert "reb" in run
            assert "ast" in run
            assert "tov" in run
            assert "fg3m" in run
            assert "stl" in run
            assert "blk" in run
            return
    pytest.fail("phase8 missing --allowed-stats clause with required stats")


# ── Delivery layout untouched ──────────────────────────────────────────────────


def test_delivery_layout_schema_untouched(workflow_text):
    """delivery layout and derek_unique_props_summary schema must be unchanged."""
    assert "deliveries/README.md" in workflow_text
    assert "derek_unique_props_summary.csv" in workflow_text
    assert "player_name" in workflow_text
    assert "projected_minutes" in workflow_text
    assert "pmf_mean" in workflow_text
    assert "market_line" in workflow_text
    assert "p_over" in workflow_text


# ── verifier script self-checks ────────────────────────────────────────────────


def test_verifier_script_exists():
    assert VERIFIER.exists(), "scripts/verify_training_data_alignment.py not found"


def test_verifier_compiles():
    """verify_training_data_alignment.py must be syntactically valid Python."""
    import py_compile

    py_compile.compile(str(VERIFIER), doraise=True)


def test_verifier_accepts_as_of_date_argument(tmp_path):
    """verify_training_data_alignment.py must accept --as-of-date and
    --check-training-table flags."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("verifier", VERIFIER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Build minimal parquets so file-check passes
    pd.DataFrame(
        {"player_id": [1], "game_id": [1], "game_date": ["2026-05-20"]}
    ).to_parquet(tmp_path / "player_game_stats.parquet", index=False)
    pd.DataFrame(
        {"player_id": [1], "game_date": ["2026-05-20"]}
    ).to_parquet(tmp_path / "player_availability_asof.parquet", index=False)

    import importlib

    import nba_props_model  # ensure src is importable

    # Patch DATA_DIR
    original = mod.DATA_DIR
    mod.DATA_DIR = tmp_path
    try:
        with patch("sys.argv", ["verify_training_data_alignment.py", "--as-of-date", "2026-05-20"]):
            try:
                mod.main()
            except SystemExit as exc:
                # Exit 0 = pass, exit 1 = data not found (expected for minimal fixture)
                assert exc.code in (0, 1), f"unexpected exit code: {exc.code}"
    finally:
        mod.DATA_DIR = original


def test_verifier_fails_on_future_max_date(tmp_path):
    """verify_training_data_alignment.py must exit 1 when max > as_of_date."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("verifier2", VERIFIER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # player_game_stats has max date beyond as_of_date
    pd.DataFrame(
        {"player_id": [1], "game_id": [1], "game_date": ["2026-05-21"]}
    ).to_parquet(tmp_path / "player_game_stats.parquet", index=False)
    pd.DataFrame(
        {"player_id": [1], "game_date": ["2026-05-20"]}
    ).to_parquet(tmp_path / "player_availability_asof.parquet", index=False)

    original = mod.DATA_DIR
    mod.DATA_DIR = tmp_path
    try:
        with patch("sys.argv", ["verifier", "--as-of-date", "2026-05-20"]):
            with pytest.raises(SystemExit) as exc_info:
                mod.main()
        assert exc_info.value.code == 1, (
            "verifier must exit 1 when max date exceeds as_of_date"
        )
    finally:
        mod.DATA_DIR = original
