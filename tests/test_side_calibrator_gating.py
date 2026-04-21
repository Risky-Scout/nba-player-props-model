"""PHASE 4 guardrails — harmful side calibrators must not land in production.

A global side calibrator is only saved to MODEL_DIR (production load path)
when OOF Brier improves AND log-loss doesn't meaningfully degrade. When
the gate fails, the artifact goes to MODEL_DIR/calibration_diagnostics/
and any stale production copy is removed.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pytest

from nba_props_model.calibration import stat_side_platt as sp


def _rows(side, n, correct_prob=0.7):
    """Generate synthetic graded rows. Outcomes follow the model prob
    draw so calibration metrics can be gamed either way."""
    rng = np.random.default_rng(3)
    out = []
    for _ in range(n):
        p = float(rng.uniform(0.45, 0.85))
        outcome = int(rng.uniform(0, 1) < (correct_prob if p > 0.55 else 0.30))
        out.append({
            "date": "2026-04-01", "stat": "pts", "side": side,
            "prob": p, "outcome": outcome,
        })
    return out


def test_worsening_side_calibrator_is_not_loaded_in_production(monkeypatch, tmp_path):
    monkeypatch.setattr(sp, "MODEL_DIR", tmp_path)

    # Seed a STALE production platt_OVER.pkl that must be removed when the
    # new fit fails the gate.
    stale = tmp_path / "platt_OVER.pkl"
    stale.parent.mkdir(parents=True, exist_ok=True)
    # Write a dummy placeholder.
    joblib.dump(object(), stale)
    assert stale.exists()

    # Feed graded rows where calibration cannot improve Brier (random labels).
    rng = np.random.default_rng(0)
    rows = [
        {"date": "2026-04-01", "stat": "pts", "side": s,
         "prob": float(rng.uniform(0.1, 0.9)),
         "outcome": int(rng.uniform(0, 1) < 0.5)}
        for s in ("OVER", "UNDER") for _ in range(200)
    ]
    monkeypatch.setattr(sp, "load_graded", lambda: rows)

    sp.main()

    # Either the production artifact was removed or the gate flagged it.
    # At minimum, diagnostics subdir exists when gating kicked in.
    diag = tmp_path / "calibration_diagnostics"
    assert diag.exists(), "diagnostics subdir missing"
    # If a stale stale production file existed and the new fit was a DIAGNOSTICS-ONLY,
    # the production copy must be removed.
    manifest_path = tmp_path / "calibration_manifest.json"
    import json
    manifest = json.loads(manifest_path.read_text())
    for side in ("OVER", "UNDER"):
        entry = manifest.get(f"global_{side}")
        assert entry is not None, f"global_{side} missing from manifest"
        if not entry["promoted"]:
            prod = tmp_path / f"platt_{side}.pkl"
            assert not prod.exists(), (
                f"non-promoted calibrator platt_{side}.pkl still in production dir"
            )
            diag_f = diag / f"platt_{side}.pkl"
            assert diag_f.exists(), (
                f"non-promoted calibrator platt_{side}.pkl not stashed to diagnostics"
            )


def test_improving_side_calibrator_is_promoted(monkeypatch, tmp_path):
    monkeypatch.setattr(sp, "MODEL_DIR", tmp_path)

    # Construct data where isotonic can materially help — the model raw
    # probs are strongly systematically biased (logit shift) so the
    # monotone calibrator can flatten the mapping back toward empirical.
    rng = np.random.default_rng(21)
    rows = []
    for side in ("OVER", "UNDER"):
        for _ in range(1500):
            p_true = float(rng.uniform(0.2, 0.9))
            # Miscalibrate by pushing raw probs toward the extreme — isotonic
            # will pull them back toward truth.
            p_raw = 1 - (1 - p_true) ** 2 if side == "OVER" else p_true ** 2
            outcome = int(rng.uniform(0, 1) < p_true)
            rows.append({
                "date": "2026-04-01", "stat": "pts", "side": side,
                "prob": float(np.clip(p_raw, 0.02, 0.98)),
                "outcome": outcome,
            })
    monkeypatch.setattr(sp, "load_graded", lambda: rows)

    sp.main()

    import json
    manifest = json.loads((tmp_path / "calibration_manifest.json").read_text())
    any_promoted = any(
        v.get("promoted")
        for k, v in manifest.items()
        if k.startswith("global_") and isinstance(v, dict)
    )
    assert any_promoted, "at least one global side calibrator must have promoted"
