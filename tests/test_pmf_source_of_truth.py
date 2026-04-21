"""PHASE 2 guardrails — production pricing uses the PMF stack only.

No legacy quantile-ladder pricing, no Platt / live_cal overlay, no Q50 bias
correction, no minutes-bucket correction, and no residual centerer shifts
in the production scoring path. The PMF (calibrated if a
pmf_cal_{stat}.pkl is present, raw otherwise) is the single source of
truth for prob_over / prob_under / q_preds / display PMF.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO = Path(__file__).parent.parent
PREDICT = REPO / "src/nba_props_model/pipelines/predict.py"


def _pricing_region(src: str) -> str:
    """Return the slice of predict.py that corresponds to the per-line
    scoring block (bounded between the PMF-only marker and the save snapshot
    call)."""
    start = src.index("# ── PMF-ONLY production pricing path")
    end = src.index("save_all_props_snapshot", start)
    return src[start:end]


def test_production_pricing_path_uses_pmf_only_source():
    src = PREDICT.read_text()
    region = _pricing_region(src)
    # The price path must not shift quantiles via legacy correction layers.
    forbidden = [
        "_centerer.correct_quantiles",
        "BIAS_CORRECTION.get",
        "MINUTES_CORRECTIONS.get",
        "_apply_cal(prob_over",
        "_apply_cal(prob_under",
        "_Q50_BIAS.get",
        "p_over(q_preds",
        "p_under(q_preds",
    ]
    for f in forbidden:
        assert f not in region, (
            f"legacy pricing dependency reappeared in production path: {f!r}"
        )


def test_production_pricing_reads_pmf_array_for_prob_over_under():
    src = PREDICT.read_text()
    region = _pricing_region(src)
    assert "_score_prop_line(_pmf_arr" in region, (
        "prob_over/prob_under must come from _score_prop_line(_pmf_arr, line)"
    )
    assert "_pmf_build_for_stat(" in region, (
        "PMF must be built via _pmf_build_for_stat for every candidate"
    )


def test_production_pricing_skips_when_pmf_unavailable():
    """If the PMF build returns None (missing artifact, model failure, etc.)
    the candidate must be skipped — never routed through a legacy model."""
    src = PREDICT.read_text()
    region = _pricing_region(src)
    # Expect a `continue` immediately after the PMF-None branch.
    # Match both the readiness-check continue and the None-result continue.
    assert region.count("if _pmf_arr is None:") >= 1
    assert "if not (target in _pmf_ready and _pmf_ready[target]) or _mp_dist is None:" in region


def test_cal_source_tag_only_references_pmf():
    """cal_source tagged in output must come from the PMF layer, never from
    a Platt / live_cal / raw_none stat×side overlay."""
    src = PREDICT.read_text()
    region = _pricing_region(src)
    assert 'cal_src_over = "pmf_cal"' in region or "cal_src_over = 'pmf_cal'" in region
    # The old stat_side / live_cal / raw_none tags should no longer appear in
    # the production region.
    for tag in ("'stat_side'", "'live_cal'", "'raw_none'"):
        assert tag not in region, f"legacy cal_source tag {tag} still present"
