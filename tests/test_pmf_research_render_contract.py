"""Regression: ``build_woo_pmf_research_from_canonical.py`` must
producer-side gate its own output. The downstream verifier should never
be the first place ``rows have null model_prob`` or
``'list' object has no attribute 'items'`` surfaces.

Run 25953498606 surfaced a follow-on regression: the contract was
requiring ``model_prob`` on PMF *distribution* rows (player+stat
support/probs) that have no market-side structure (no line/side/book).
The contract now splits row classes:
  * distribution rows → validate ``support``/``probs`` / pmf shape
  * market-side rows  → require derivable ``model_prob``
"""

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


def _distribution_record(player_id, stat="pts"):
    return {
        "player_id": player_id,
        "player": f"Player {player_id}",
        "stat": stat,
        "team": "TM",
        "opponent": "OPP",
        "support": [0, 1, 2, 3],
        "probs": [0.1, 0.4, 0.3, 0.2],
        "mean": 1.6,
        "variance": 0.84,
        "support_min": 0,
        "support_max": 3,
        "support_size": 4,
        "atom_probability_sum": 1.0,
        "pmf": {"0": 0.1, "1": 0.4, "2": 0.3, "3": 0.2},
        "atom_pmf": [
            {"outcome": 0, "probability": 0.1},
            {"outcome": 1, "probability": 0.4},
            {"outcome": 2, "probability": 0.3},
            {"outcome": 3, "probability": 0.2},
        ],
        "atom_pmf_policy": "atom_source_only_no_ladder_fallback",
        "pmf_source_policy": "canonical_atom_pmf_only",
        "market_implied_pmf_policy": "forbidden_not_generated",
    }


def _market_record(player_id, side, **probs):
    rec = {
        "player_id": player_id,
        "stat": "pts",
        "side": side,
        "line": 23.5,
        "book": "bovada",
    }
    rec.update(probs)
    return rec


def _fixture_payload(records, *, players=None):
    if players is None:
        players = [{"player": "Bob", "player_id": 1, "stats": [], "pmfs": [], "props": []}]
    return {
        "schema_version": "m8_6o_pmf_research_v1",
        "date": "2026-05-15",
        "players": players,
        "pmfs": records,
        "props": records,
    }


# ── _classify_pmf_research_record ─────────────────────────────────────


def test_classify_distribution_row_with_support_probs():
    rec = _distribution_record(1)
    assert builder._classify_pmf_research_record(rec) == "distribution"


def test_classify_market_row_with_side_and_line():
    rec = _market_record(1, "OVER", model_prob_over=0.55)
    assert builder._classify_pmf_research_record(rec) == "market"


def test_classify_market_row_with_only_side_aware_probs():
    rec = {"player_id": 1, "stat": "pts", "model_p_over": 0.55, "model_p_under": 0.45}
    assert builder._classify_pmf_research_record(rec) == "market"


def test_classify_market_row_with_only_book():
    rec = {"player_id": 1, "stat": "pts", "book": "bovada"}
    assert builder._classify_pmf_research_record(rec) == "market"


# ── _renderable_model_prob_for_pmf_record ────────────────────────────


def test_renderable_model_prob_picks_over_when_no_side():
    rec = {"player": "Bob", "model_prob_over": 0.55, "model_prob_under": 0.45}
    assert builder._renderable_model_prob_for_pmf_record(rec) == pytest.approx(0.55)


def test_renderable_model_prob_for_under_uses_under_field():
    rec = {"side": "UNDER", "model_prob_under": 0.41}
    assert builder._renderable_model_prob_for_pmf_record(rec) == pytest.approx(0.41)


def test_renderable_model_prob_falls_back_to_complement():
    rec = {"side": "UNDER", "model_prob_over": 0.7}
    assert builder._renderable_model_prob_for_pmf_record(rec) == pytest.approx(0.3)


# ── distribution-only payloads pass ──────────────────────────────────


def test_contract_pass_on_456_like_distribution_only_payload(tmp_path, capsys):
    """The exact regression in run 25953498606: 456 PMF distribution
    rows with support/probs but no line/side/book/model_prob must pass
    the producer-side render contract."""
    records = [_distribution_record(i, stat="pts") for i in range(456)]
    players = [
        {"player": f"P{i}", "player_id": i, "stats": [], "pmfs": [], "props": []}
        for i in range(38)
    ]
    payload = _fixture_payload(records, players=players)
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    builder.assert_pmf_research_render_contract(payload, [out])
    captured = capsys.readouterr().out
    assert "PMF_RESEARCH_RENDER_CONTRACT_PASS" in captured
    assert "rows=456" in captured
    assert "pmf_rows=456" in captured
    assert "market_rows=0" in captured
    assert "model_prob_required=0" in captured


def test_contract_pass_with_only_pmf_dict_no_support_probs(tmp_path, capsys):
    rec = _distribution_record(1)
    rec.pop("support")
    rec.pop("probs")
    payload = _fixture_payload([rec])
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    builder.assert_pmf_research_render_contract(payload, [out])
    captured = capsys.readouterr().out
    assert "PMF_RESEARCH_RENDER_CONTRACT_PASS" in captured
    assert "pmf_rows=1" in captured


# ── distribution-only payloads fail when malformed ───────────────────


def test_contract_fail_when_distribution_support_probs_mismatched(tmp_path):
    rec = _distribution_record(1)
    rec["probs"] = [0.5, 0.5]  # was 4-long
    payload = _fixture_payload([rec])
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    msg = str(excinfo.value)
    assert "PMF_RESEARCH_RENDER_CONTRACT_FAIL" in msg
    assert "PMF_DISTRIBUTION_MALFORMED" in msg
    assert "support_probs_length_mismatch" in msg


def test_contract_fail_when_distribution_probs_dont_sum_to_one(tmp_path):
    rec = _distribution_record(1)
    rec["probs"] = [0.1, 0.1, 0.1, 0.1]  # sums to 0.4
    payload = _fixture_payload([rec])
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    assert "probs_sum_out_of_tolerance" in str(excinfo.value)


def test_contract_fail_when_distribution_missing_stat(tmp_path):
    rec = _distribution_record(1)
    rec.pop("stat")
    payload = _fixture_payload([rec])
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    assert "missing_stat" in str(excinfo.value)


# ── market-side rows still require derivable model_prob ──────────────


def test_contract_pass_on_market_row_with_model_prob_over(tmp_path, capsys):
    market = _market_record(1, "OVER", model_prob_over=0.6, model_prob_under=0.4)
    distribution = _distribution_record(1)
    payload = _fixture_payload([distribution, market])
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    builder.assert_pmf_research_render_contract(payload, [out])
    captured = capsys.readouterr().out
    assert "PMF_RESEARCH_RENDER_CONTRACT_PASS" in captured
    assert "pmf_rows=1" in captured
    assert "market_rows=1" in captured
    assert "model_prob_required=1" in captured
    assert "model_prob_non_null=1" in captured
    assert market["model_prob"] == pytest.approx(0.6)


def test_contract_fail_on_market_row_missing_model_prob(tmp_path):
    market = _market_record(1, "OVER")  # no probs at all
    payload = _fixture_payload([market])
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    msg = str(excinfo.value)
    assert "PMF_RESEARCH_RENDER_CONTRACT_FAIL" in msg
    assert "WOO_MODEL_PROB_UNMAPPABLE" in msg


# ── structural error paths ───────────────────────────────────────────


def test_contract_fail_when_rows_empty(tmp_path):
    payload = _fixture_payload([])
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    assert "PMF_RESEARCH_RENDER_CONTRACT_FAIL" in str(excinfo.value)
    assert "empty_rows" in str(excinfo.value)


def test_contract_fail_when_no_players(tmp_path):
    payload = _fixture_payload([_distribution_record(1)])
    payload["players"] = []
    out = tmp_path / "pmf_research.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    assert "PMF_RESEARCH_RENDER_CONTRACT_FAIL" in str(excinfo.value)
    assert "empty_players" in str(excinfo.value)


def test_contract_round_trips_written_file(tmp_path):
    """If the file on disk is corrupt, the contract surfaces a
    structured parse_error instead of the downstream verifier being the
    first thing to fail."""
    payload = _fixture_payload([_distribution_record(1)])
    out = tmp_path / "pmf_research.json"
    out.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        builder.assert_pmf_research_render_contract(payload, [out])
    msg = str(excinfo.value)
    assert "PMF_RESEARCH_RENDER_CONTRACT_FAIL" in msg
    assert "parse_error" in msg
