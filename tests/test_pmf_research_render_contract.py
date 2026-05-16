"""Regression: ``build_woo_pmf_research_from_canonical.py`` must
producer-side gate its own output. The downstream verifier should never
be the first place ``rows have null model_prob`` or
``'list' object has no attribute 'items'`` surfaces."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "build_woo_pmf_research_from_canonical",
    REPO / "scripts" / "build_woo_pmf_research_from_canonical.py",
)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def _fixture_payload(records):
    players = [{"player": "Bob", "player_id": 1, "stats": [], "pmfs": [], "props": []}]
    return {
        "schema_version": "m8_6o_pmf_research_v1",
        "date": "2026-05-15",
        "players": players,
        "pmfs": records,
        "props": records,
    }


def test_renderable_model_prob_picks_over_when_no_side():
    rec = {"player": "Bob", "model_prob_over": 0.55, "model_prob_under": 0.45}
    assert builder._renderable_model_prob_for_pmf_record(rec) == pytest.approx(0.55)


def test_renderable_model_prob_for_under_uses_under_field():
    rec = {"side": "UNDER", "model_prob_under": 0.41}
    assert builder._renderable_model_prob_for_pmf_record(rec) == pytest.approx(0.41)


def test_renderable_model_prob_falls_back_to_complement():
    rec = {"side": "UNDER", "model_prob_over": 0.7}
    assert builder._renderable_model_prob_for_pmf_record(rec) == pytest.approx(0.3)


def test_contract_pass_on_complete_payload(tmp_path, capsys):
    records = [
        {"player_id": 1, "stat": "pts", "model_prob_over": 0.6, "model_prob_under": 0.4},
        {"player_id": 2, "stat": "reb", "model_prob_over": 0.55, "model_prob_under": 0.45},
    ]
    payload = _fixture_payload(records)
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    builder.assert_pmf_research_render_contract(payload, [out])
    captured = capsys.readouterr().out
    assert "PMF_RESEARCH_RENDER_CONTRACT_PASS" in captured
    assert "rows=2" in captured
    assert "players=1" in captured
    assert "model_prob_non_null=2" in captured


def test_contract_fail_when_model_prob_unmappable(tmp_path):
    records = [
        {"player_id": 1, "stat": "pts"},
        {"player_id": 2, "stat": "reb"},
    ]
    payload = _fixture_payload(records)
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    msg = str(excinfo.value)
    assert "PMF_RESEARCH_RENDER_CONTRACT_FAIL" in msg
    assert "WOO_MODEL_PROB_UNMAPPABLE" in msg


def test_contract_fail_when_rows_empty(tmp_path):
    payload = _fixture_payload([])
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    assert "PMF_RESEARCH_RENDER_CONTRACT_FAIL" in str(excinfo.value)
    assert "empty_rows" in str(excinfo.value)


def test_contract_fail_when_no_players(tmp_path):
    payload = _fixture_payload([{"player_id": 1, "model_prob_over": 0.6}])
    payload["players"] = []
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    assert "PMF_RESEARCH_RENDER_CONTRACT_FAIL" in str(excinfo.value)
    assert "empty_players" in str(excinfo.value)


def test_contract_round_trips_written_file(tmp_path, capsys):
    """If the file on disk is corrupt, the contract surfaces a
    structured parse_error instead of the downstream verifier being the
    first thing to fail."""
    records = [{"player_id": 1, "stat": "pts", "model_prob_over": 0.6}]
    payload = _fixture_payload(records)
    out = tmp_path / "pmf_research.json"
    out.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    msg = str(excinfo.value)
    assert "PMF_RESEARCH_RENDER_CONTRACT_FAIL" in msg
    assert "parse_error" in msg
