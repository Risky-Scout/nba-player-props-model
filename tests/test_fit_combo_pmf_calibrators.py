"""Tests for ``scripts/fit_combo_pmf_calibrators.py``.

Regression source: model-chain run ``26196295263`` failed at the
``phase8_pmf_calibration_diagnostics_market_eval`` job's
"Run Phase 8 PMF calibration folds + OOF aggregation + combo PMFs"
step with exit code 4 and the verbatim error::

    [ERROR] Combo OOF missing mission combos: ['stocks'].
    Expected all of ('stocks', 'pa', 'pr', 'ra', 'pra').

The upstream combo OOF builder
(``scripts/build_combo_oof_pmfs_from_base_oof.py``) had finished
successfully with ``status="partial"`` and a structured
``combos_skipped=[{"combo": "stocks", "reason": "missing components: stl, blk"}]``
manifest entry — ``stocks`` was deliberately and cleanly skipped because
``stl`` and ``blk`` were not present in the base OOF that day. The
calibrator fitter still aborted because it required all five mission
combos to appear in the OOF parquet.

The patched fitter classifies missing combos via the upstream manifest:

* "structurally skipped" (manifest names a missing required base
  component, matched by the substring ``"missing components"``) →
  log a warning, surface the skip in the merged
  ``pmf_cal_meta.json``, and proceed with the remaining combos.
* "unexplained" (no manifest, malformed manifest, or the manifest does
  not document the missing combo) → keep returning exit code 4 so
  silent data loss is never masked.

These tests exercise both classifications without touching the real
``artifacts/models/`` directory: every write the script performs is
redirected into the test's ``tmp_path`` via ``monkeypatch``, and
``fit_all`` is stubbed so no real calibrators are fit.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "fit_combo_pmf_calibrators.py"


@pytest.fixture
def fit_module():
    """Import ``scripts/fit_combo_pmf_calibrators.py`` as a module."""
    src_path = REPO_ROOT / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    spec = importlib.util.spec_from_file_location(
        "_fit_combo_pmf_calibrators_under_test", str(SCRIPT_PATH)
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_synthetic_combo_oof(stats: list[str], rows_per_stat: int = 600) -> pd.DataFrame:
    """Build a synthetic combo-OOF DataFrame matching the production schema.

    Each combo gets ``rows_per_stat`` rows spread over multiple game
    dates so the downstream walk-forward fold logic has enough span.
    PMFs are uniform over a 5-element support; outcomes are integers
    inside that support.
    """
    rng = np.random.default_rng(7)
    rows: list[dict] = []
    support = np.full(5, 1.0 / 5, dtype=np.float64)
    for stat in stats:
        for i in range(rows_per_stat):
            day = pd.Timestamp("2026-01-01") + pd.Timedelta(days=i % 90)
            rows.append({
                "game_date": day.strftime("%Y-%m-%d"),
                "game_id": int(50_000 + i),
                "player_id": int(1000 + (i % 17)),
                "role_bucket": ["bench", "rotation", "core", "starter"][i % 4],
                "stat": stat,
                "mission_stat": {
                    "pa": "pts_ast", "pr": "pts_reb", "ra": "reb_ast",
                    "pra": "pts_reb_ast", "stocks": "stl_blk",
                }[stat],
                "components": {
                    "pa": ["pts", "ast"], "pr": ["pts", "reb"],
                    "ra": ["reb", "ast"], "pra": ["pts", "reb", "ast"],
                    "stocks": ["stl", "blk"],
                }[stat],
                "outcome": int(rng.integers(0, 5)),
                "pmf": support.tolist(),
                "pmf_json": json.dumps({str(j): float(p) for j, p in enumerate(support)}),
                "support_min": 0,
                "support_max": 4,
                "pmf_sum_error": 0.0,
                "pmf_valid": True,
                "n_draws": 256,
                "combo_oof_method": "independence_cold_start_v1",
                "combo_pmf_version": "combo_oof_pmf_v1",
                "dataset_status": "fresh_oof_v1",
                "oof_window_start": "2026-01-01",
                "oof_window_end": "2026-03-31",
                "training_cutoff_date": "2026-03-31",
                "days_since_oof_window_end": 0,
                "path_building_warning": "",
                "production_promoted": False,
                "final_calibration_ready": False,
                "calibrated": False,
                "calibration_status": "pending_m6_stat_role_calibration",
                "source_oof_path": "data/oof_pmfs.parquet",
            })
    return pd.DataFrame(rows)


def _stage_outputs(tmp_path: Path, monkeypatch, fit_module) -> tuple[Path, Path]:
    """Redirect every write performed by the script into ``tmp_path``.

    Returns ``(model_dir, cal_meta_path)``.
    """
    model_dir = tmp_path / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    cal_meta_path = model_dir / "pmf_cal_meta.json"
    cal_meta_backup_path = model_dir / "pmf_cal_meta_base_only.json.bak"

    monkeypatch.setattr(fit_module, "MODEL_DIR", model_dir, raising=True)
    monkeypatch.setattr(fit_module, "CAL_META_PATH", cal_meta_path, raising=True)
    monkeypatch.setattr(
        fit_module, "CAL_META_BACKUP_PATH", cal_meta_backup_path, raising=True
    )

    base_meta = {
        "stats": {
            base: {"fitted": True, "role_aware": True}
            for base in ("pts", "reb", "ast", "fg3m", "tov")
        }
    }
    cal_meta_path.write_text(json.dumps(base_meta))

    return model_dir, cal_meta_path


def _stub_fit_all(fit_module, model_dir: Path, expected_combos: set[str]):
    """Replace ``fit_all`` with a stub that writes the meta + stub pkls.

    The stub mirrors the side effects the real ``fit_all`` would have
    (overwriting ``pmf_cal_meta.json`` with combo-only meta and writing
    one ``pmf_cal_role_{stat}.pkl`` per fitted stat) so that the
    post-fit verification path in ``main()`` exercises the patched code
    end-to-end.
    """

    def fake_fit_all(per_stat_inputs, **_kwargs):  # noqa: ANN001
        assert set(per_stat_inputs.keys()) == expected_combos, (
            per_stat_inputs.keys(), expected_combos,
        )
        meta = {
            "stats": {
                combo: {"fitted": True, "role_aware": True}
                for combo in per_stat_inputs.keys()
            }
        }
        with open(fit_module.CAL_META_PATH, "w") as f:
            json.dump(meta, f)
        for combo in per_stat_inputs.keys():
            (model_dir / f"pmf_cal_role_{combo}.pkl").write_bytes(b"stub-pkl")
        return meta

    return fake_fit_all


def _run_main(fit_module, oof_path: Path, monkeypatch) -> int:
    monkeypatch.setattr(
        sys, "argv",
        ["fit_combo_pmf_calibrators.py", "--oof", str(oof_path), "--seed", "0"],
    )
    return fit_module.main()


def test_stocks_structurally_skipped_does_not_exit_4(
    tmp_path: Path, monkeypatch, fit_module
):
    """Reproduces the exact run-26196295263 failure path.

    Combo OOF parquet has ``pa, pr, ra, pra`` only (``stocks`` absent
    because the base OOF lacked ``stl/blk``). The sibling manifest
    documents the structural skip with the verbatim reason string the
    upstream builder emitted on that run. The patched fitter must
    proceed with the four available combos and exit 0.
    """
    model_dir, cal_meta_path = _stage_outputs(tmp_path, monkeypatch, fit_module)

    oof_path = tmp_path / "oof_combo_pmfs.parquet"
    df = _make_synthetic_combo_oof(["pa", "pr", "ra", "pra"])
    df.to_parquet(oof_path, index=False)

    manifest = {
        "schema_version": "1.0",
        "status": "partial",
        "available_base_stats": ["ast", "pts", "reb"],
        "combo_requirements": {
            "pa": ["pts", "ast"], "pr": ["pts", "reb"],
            "ra": ["reb", "ast"], "pra": ["pts", "reb", "ast"],
            "stocks": ["stl", "blk"],
        },
        "combos_attempted": ["stocks", "pa", "pr", "ra", "pra"],
        "combos_built": [
            {"combo": "pa", "rows": 600},
            {"combo": "pr", "rows": 600},
            {"combo": "ra", "rows": 600},
            {"combo": "pra", "rows": 600},
        ],
        "combos_skipped": [
            {"combo": "stocks", "reason": "missing components: stl, blk"}
        ],
        "skip_reasons": {"stocks": "missing components: stl, blk"},
        "n_rows_written": 2400,
    }
    manifest_path = oof_path.parent / "oof_combo_pmfs.manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    monkeypatch.setattr(
        fit_module, "fit_all",
        _stub_fit_all(fit_module, model_dir, {"pa", "pr", "ra", "pra"}),
    )

    rc = _run_main(fit_module, oof_path, monkeypatch)
    assert rc == 0, f"expected exit 0, got {rc}"

    merged = json.loads(cal_meta_path.read_text())
    fitted_combos = set(merged.get("stats", {}).keys()) & {
        "pa", "pr", "ra", "pra", "stocks",
    }
    assert fitted_combos == {"pa", "pr", "ra", "pra"}
    skips = merged.get("combo_calibration_structural_skips") or {}
    assert "stocks" in skips, merged.get("combo_calibration_structural_skips")
    assert "missing components" in skips["stocks"].lower()
    assert merged["combo_calibration_combos_fitted"] == sorted(["pa", "pr", "ra", "pra"])
    for combo in ("pa", "pr", "ra", "pra"):
        assert (model_dir / f"pmf_cal_role_{combo}.pkl").exists()
    assert not (model_dir / "pmf_cal_role_stocks.pkl").exists()


def test_unexplained_missing_combo_still_returns_exit_4(
    tmp_path: Path, monkeypatch, fit_module
):
    """The contract still fails closed when the absence is unexplained.

    Combo OOF parquet has ``pa, pr, ra, pra`` only and NO sibling
    manifest. The fitter cannot prove that ``stocks`` was structurally
    skipped (missing required base components) versus dropped silently
    by an upstream bug, so it must return exit code 4 — the same
    behavior that protected the contract before this fix.
    """
    model_dir, cal_meta_path = _stage_outputs(tmp_path, monkeypatch, fit_module)

    oof_path = tmp_path / "oof_combo_pmfs.parquet"
    df = _make_synthetic_combo_oof(["pa", "pr", "ra", "pra"])
    df.to_parquet(oof_path, index=False)

    assert not (oof_path.parent / "oof_combo_pmfs.manifest.json").exists()

    def _explode_fit_all(*_args, **_kwargs):  # noqa: ANN001
        raise AssertionError("fit_all must NOT be invoked when the gate fails")

    monkeypatch.setattr(fit_module, "fit_all", _explode_fit_all)

    rc = _run_main(fit_module, oof_path, monkeypatch)
    assert rc == 4, f"expected exit 4, got {rc}"


def test_missing_combo_with_non_structural_manifest_reason_returns_exit_4(
    tmp_path: Path, monkeypatch, fit_module
):
    """Non-structural skip reasons must NOT be treated as structural.

    The manifest is present and lists ``stocks`` as skipped, but the
    reason string does not name a missing required component
    (``STRUCTURAL_SKIP_MARKER`` substring). The fitter must still fail
    closed with exit 4, because relaxing that contract would mask
    upstream regressions where the builder dropped a combo for some
    other reason (data corruption, code bug, etc.).
    """
    model_dir, cal_meta_path = _stage_outputs(tmp_path, monkeypatch, fit_module)

    oof_path = tmp_path / "oof_combo_pmfs.parquet"
    df = _make_synthetic_combo_oof(["pa", "pr", "ra", "pra"])
    df.to_parquet(oof_path, index=False)

    manifest = {
        "status": "partial",
        "combos_skipped": [
            {"combo": "stocks", "reason": "transient internal sampler error"}
        ],
        "skip_reasons": {"stocks": "transient internal sampler error"},
        "available_base_stats": ["ast", "pts", "reb", "stl", "blk"],
    }
    (oof_path.parent / "oof_combo_pmfs.manifest.json").write_text(json.dumps(manifest))

    def _explode_fit_all(*_args, **_kwargs):  # noqa: ANN001
        raise AssertionError("fit_all must NOT be invoked for non-structural skips")

    monkeypatch.setattr(fit_module, "fit_all", _explode_fit_all)

    rc = _run_main(fit_module, oof_path, monkeypatch)
    assert rc == 4, f"expected exit 4, got {rc}"


def test_all_five_combos_present_keeps_status_quo(
    tmp_path: Path, monkeypatch, fit_module
):
    """Happy path — when every mission combo is present, behavior is unchanged."""
    model_dir, cal_meta_path = _stage_outputs(tmp_path, monkeypatch, fit_module)

    oof_path = tmp_path / "oof_combo_pmfs.parquet"
    df = _make_synthetic_combo_oof(["pa", "pr", "ra", "pra", "stocks"])
    df.to_parquet(oof_path, index=False)

    monkeypatch.setattr(
        fit_module, "fit_all",
        _stub_fit_all(
            fit_module, model_dir, {"pa", "pr", "ra", "pra", "stocks"}
        ),
    )

    rc = _run_main(fit_module, oof_path, monkeypatch)
    assert rc == 0, f"expected exit 0, got {rc}"

    merged = json.loads(cal_meta_path.read_text())
    fitted = set(merged["stats"].keys()) & {"pa", "pr", "ra", "pra", "stocks"}
    assert fitted == {"pa", "pr", "ra", "pra", "stocks"}
    assert "combo_calibration_structural_skips" not in merged


def test_classify_missing_combos_helper(fit_module):
    """Direct unit test for the classifier helper."""
    structural, unexplained = fit_module._classify_missing_combos(set(), None)
    assert structural == {} and unexplained == []

    structural, unexplained = fit_module._classify_missing_combos(
        {"stocks"}, None
    )
    assert structural == {} and unexplained == ["stocks"]

    structural, unexplained = fit_module._classify_missing_combos(
        {"stocks"},
        {"skip_reasons": {"stocks": "missing components: stl, blk"}},
    )
    assert structural == {"stocks": "missing components: stl, blk"}
    assert unexplained == []

    structural, unexplained = fit_module._classify_missing_combos(
        {"stocks"},
        {"combos_skipped": [
            {"combo": "stocks", "reason": "Missing Components: stl"}
        ]},
    )
    assert structural == {"stocks": "Missing Components: stl"}
    assert unexplained == []

    structural, unexplained = fit_module._classify_missing_combos(
        {"stocks"},
        {"skip_reasons": {"stocks": "transient sampler issue"}},
    )
    assert structural == {} and unexplained == ["stocks"]

    structural, unexplained = fit_module._classify_missing_combos(
        {"stocks", "ra"},
        {
            "skip_reasons": {"stocks": "missing components: stl, blk"},
            "combos_skipped": [{"combo": "stocks", "reason": "missing components: stl, blk"}],
        },
    )
    assert structural == {"stocks": "missing components: stl, blk"}
    assert unexplained == ["ra"]
