"""Tests for PMF mean-shift repair application wiring."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_event_market_loss_rows import _parse_pmf_value  # noqa: E402
from nba_props_model.calibration.pmf_mean_shift_repair import (
    apply_mean_shift_manifest_to_pmf,
    load_mean_shift_manifest,
    normalize_pmf,
)


def _sha_series(s: pd.Series) -> str:
    h = hashlib.sha256()
    for v in s.fillna("").astype(str).values:
        h.update(v.encode("utf-8", errors="replace"))
    return h.hexdigest()


def test_model_pmf_raw_hash_unchanged_when_repaired_pmf_differs():
    pmf = normalize_pmf({0: 0.5, 1: 0.3, 2: 0.2})
    js = json.dumps({str(k): v for k, v in pmf.items()})
    rep, _a, _b, applied, _rr = apply_mean_shift_manifest_to_pmf(
        pmf,
        stat="pts",
        role_bucket="core",
        manifest={
            "segments": {
                "pts|core": {"accepted": True, "selected_method": "additive", "delta": 0.5}
            }
        },
    )
    assert applied
    js_rep = json.dumps({str(k): v for k, v in rep.items()})
    df = pd.DataFrame(
        [
            {
                "join_status": "matched",
                "stat": "pts",
                "role_bucket": "core",
                "model_pmf_raw": js,
                "model_pmf": js_rep,
                "model_prob_over_raw": 0.4,
                "model_prob_over_after_pmf_mean_shift": 0.45,
                "model_prob_over_active": 0.45,
                "pmf_mean_shift_repair_applied": True,
                "pmf_mean_shift_row_rollback_reason": None,
            }
        ]
    )
    assert _sha_series(df["model_pmf_raw"]) != _sha_series(df["model_pmf"])


def test_missing_manifest_segment_no_apply():
    pmf = normalize_pmf({0: 0.5, 1: 0.5})
    js = json.dumps({str(k): v for k, v in pmf.items()})
    out, _sc, _me, applied, _rr = apply_mean_shift_manifest_to_pmf(
        pmf, stat="pts", role_bucket="bench", manifest={"segments": {}}
    )
    assert not applied
    assert json.dumps({str(k): v for k, v in out.items()}) == js


def test_invalid_repair_rolls_back():
    pmf = normalize_pmf({0: 0.5, 1: 0.5})
    man = {
        "segments": {
            "pts|core": {"accepted": True, "selected_method": "not_a_method", "delta": 0.1}
        }
    }
    _out, _k, _m, applied, rr = apply_mean_shift_manifest_to_pmf(
        pmf, stat="pts", role_bucket="core", manifest=man
    )
    assert not applied
    assert rr == "unknown_method"


def test_load_manifest_roundtrip(tmp_path: Path):
    man = {
        "version": "1",
        "uses_market_probability_as_label": False,
        "uses_market_probability_as_feature": False,
        "segments": {},
    }
    p = tmp_path / "m.json"
    p.write_text(json.dumps(man), encoding="utf-8")
    m2 = load_mean_shift_manifest(p)
    assert m2["uses_market_probability_as_label"] is False


def test_parse_pmf_roundtrip():
    d = {0: 0.2, 1: 0.8}
    s = json.dumps({str(k): v for k, v in d.items()})
    p = _parse_pmf_value(s)
    n = normalize_pmf(p)
    assert abs(n[1] - 0.8) < 1e-9 and abs(n[0] - 0.2) < 1e-9
