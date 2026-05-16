"""Regression: ``scripts/verify_woo_public_export_contract.py`` must
accept every ``pmf_research.json`` shape the canonical builder and the
legacy producer emit.

Run 25955470154 root-caused to ``_check_pmf_research`` calling
``.items()`` on a list, because the canonical builder writes
``players[].stats`` as a *list* of stat-atom dicts. The verifier now
mirrors the schema-safe parsing logic in
``verify_woo_dashboard_render_contract.py`` so any payload that passes
the dashboard render contract also passes the public-export contract.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "verify_woo_public_export_contract",
    REPO / "scripts" / "verify_woo_public_export_contract.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


# ── _check_pmf_research: shape coverage ──────────────────────────────


def test_pmf_research_accepts_list_of_records():
    """Modern canonical builder shape: ``pmf_research.json`` root is a
    list of distribution-row dicts."""
    rows = [
        {
            "player_id": i,
            "player": f"P{i}",
            "stat": "pts",
            "support": [0, 1, 2],
            "probs": [0.25, 0.5, 0.25],
        }
        for i in range(5)
    ]
    failures = mod._check_pmf_research(rows, "pmf_research[date]")
    assert failures == [], failures


def test_pmf_research_accepts_dict_with_rows():
    payload = {
        "rows": [
            {
                "player_id": 1,
                "player": "Bob",
                "stat": "pts",
                "support": [0, 1, 2],
                "probs": [0.25, 0.5, 0.25],
            }
        ]
    }
    assert mod._check_pmf_research(payload, "pmf_research[date]") == []


def test_pmf_research_accepts_dict_with_records():
    payload = {
        "records": [
            {
                "player_id": 1,
                "player": "Bob",
                "stat": "pts",
                "support": [0, 1, 2],
                "probs": [0.25, 0.5, 0.25],
            }
        ]
    }
    assert mod._check_pmf_research(payload, "pmf_research[date]") == []


def test_pmf_research_accepts_legacy_dict_with_players_dict_stats():
    """Original producer shape (publish_woo_public_export.py): each
    player's ``stats`` is a dict keyed by stat name with
    ``support_points`` entries."""
    payload = {
        "players": [
            {
                "player": "Bob",
                "stats": {
                    "pts": {
                        "support_points": [
                            {"k": 0, "p": 0.25, "label": "0", "is_tail": False},
                            {"k": 1, "p": 0.50, "label": "1", "is_tail": False},
                            {"k": 2, "p": 0.25, "label": "2", "is_tail": False},
                        ]
                    }
                },
            }
        ]
    }
    assert mod._check_pmf_research(payload, "pmf_research[date]") == []


def test_pmf_research_accepts_canonical_dict_with_players_list_stats():
    """Canonical builder shape (the exact regression file): each
    player's ``stats`` is a *list* of stat-atom dicts. The verifier
    must NOT call ``.items()`` on it."""
    payload = {
        "players": [
            {
                "player": "Bob",
                "player_id": 1,
                "stats": [
                    {
                        "stat": "pts",
                        "support": [0, 1, 2],
                        "probs": [0.25, 0.5, 0.25],
                    },
                    {
                        "stat_key": "reb",
                        "support": [0, 1],
                        "probs": [0.6, 0.4],
                    },
                ],
            }
        ],
        "pmfs": [],
    }
    assert mod._check_pmf_research(payload, "pmf_research[date]") == []


# ── _check_pmf_research: structural error paths ──────────────────────


def test_pmf_research_emits_structured_error_on_invalid_shape():
    failures = mod._check_pmf_research(42, "pmf_research[date]")
    assert len(failures) == 1
    assert "WOO_PUBLIC_EXPORT_PMF_RESEARCH_SCHEMA_INVALID" in failures[0]
    assert "root_type=int" in failures[0]


def test_pmf_research_emits_structured_error_on_dict_without_known_keys():
    failures = mod._check_pmf_research({"foo": "bar"}, "pmf_research[date]")
    assert len(failures) == 1
    assert "WOO_PUBLIC_EXPORT_PMF_RESEARCH_SCHEMA_INVALID" in failures[0]
    assert "root_type=dict" in failures[0]


def test_pmf_research_never_calls_items_on_list_player_stats():
    """The exact crash from run 25955470154."""
    payload = {
        "players": [
            {
                "player": "Crash Test",
                "stats": [{"stat": "pts", "support": [0, 1], "probs": [0.5, 0.5]}],
            }
        ]
    }
    # Should not raise AttributeError.
    assert mod._check_pmf_research(payload, "pmf_research[date]") == []


def test_pmf_research_fails_on_malformed_distribution_row():
    """A distribution row with support/probs of mismatched length is
    flagged with a structured failure, not a traceback."""
    rows = [
        {
            "player_id": 1,
            "player": "Bob",
            "stat": "pts",
            "support": [0, 1, 2],
            "probs": [0.5, 0.5],
        }
    ]
    failures = mod._check_pmf_research(rows, "pmf_research[date]")
    assert failures
    assert any("WOO_PUBLIC_EXPORT_PMF_RESEARCH_DISTRIBUTION_MALFORMED" in f for f in failures)
    assert any("support_probs_length_mismatch" in f for f in failures)


def test_pmf_research_distribution_row_probs_sum_must_be_close_to_one():
    rows = [
        {
            "player_id": 1,
            "player": "Bob",
            "stat": "pts",
            "support": [0, 1, 2],
            "probs": [0.1, 0.1, 0.1],
        }
    ]
    failures = mod._check_pmf_research(rows, "pmf_research[date]")
    assert any("probs_sum_out_of_tolerance" in f for f in failures)


def test_pmf_research_distribution_row_can_use_pmf_dict():
    rows = [
        {
            "player_id": 1,
            "player": "Bob",
            "stat": "pts",
            "pmf": {"0": 0.25, "1": 0.5, "2": 0.25},
        }
    ]
    assert mod._check_pmf_research(rows, "pmf_research[date]") == []


def test_pmf_research_market_row_requires_model_prob():
    rows = [
        {
            "player_id": 1,
            "player": "Bob",
            "stat": "pts",
            "side": "OVER",
            "line": 23.5,
            "book": "bovada",
        }
    ]
    failures = mod._check_pmf_research(rows, "pmf_research[date]")
    assert any("market rows have null model_prob" in f for f in failures)


def test_pmf_research_market_row_with_model_prob_passes():
    rows = [
        {
            "player_id": 1,
            "player": "Bob",
            "stat": "pts",
            "side": "OVER",
            "line": 23.5,
            "book": "bovada",
            "model_prob": 0.55,
        }
    ]
    assert mod._check_pmf_research(rows, "pmf_research[date]") == []


def test_pmf_research_tail_bucket_check_still_flags_sparse_tail():
    payload = {
        "players": [
            {
                "player": "Bob",
                "stats": {
                    "pts": {
                        "support_points": [
                            {"k": 0, "p": 0.4, "label": "0"},
                            {"k": 1, "p": 0.4, "label": "1"},
                            {"k": 20, "p": 0.2, "label": "20"},
                        ]
                    }
                },
            }
        ]
    }
    failures = mod._check_pmf_research(payload, "pmf_research[date]")
    assert any("tail-bucket bug" in f for f in failures)


# ── _check_affiliate: existing strictness preserved ──────────────────


def test_affiliate_requires_canonical_columns():
    payload = {"rows": [{"player": "x", "stat": "pts", "model_prob": 0.5}]}
    failures = mod._check_affiliate(payload, "affiliate[date]")
    assert any("missing keys" in f for f in failures)


def test_affiliate_accepts_complete_row():
    payload = {
        "rows": [
            {
                "player": "x",
                "stat": "pts",
                "side": "OVER",
                "line": 23.5,
                "model_prob": 0.55,
                "market_prob": 0.51,
            }
        ]
    }
    assert mod._check_affiliate(payload, "affiliate[date]") == []


def test_affiliate_fails_on_non_dict_root():
    failures = mod._check_affiliate([1, 2, 3], "affiliate[date]")
    assert any("WOO_PUBLIC_EXPORT_AFFILIATE_SCHEMA_INVALID" in f for f in failures)


def test_affiliate_fails_on_empty_rows():
    failures = mod._check_affiliate({"rows": []}, "affiliate[date]")
    assert any("rows is empty" in f for f in failures)


# ── _read_json: returns dict OR list ─────────────────────────────────


def test_read_json_returns_list_when_root_is_list(tmp_path):
    p = tmp_path / "x.json"
    p.write_text("[1, 2, 3]")
    payload, err = mod._read_json(p)
    assert err is None
    assert payload == [1, 2, 3]


def test_read_json_returns_dict_when_root_is_dict(tmp_path):
    p = tmp_path / "x.json"
    p.write_text('{"a": 1}')
    payload, err = mod._read_json(p)
    assert err is None
    assert payload == {"a": 1}


def test_read_json_reports_parse_error_structurally(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid")
    payload, err = mod._read_json(p)
    assert payload is None
    assert err is not None
    assert "parse error" in err


# ── _payload_date: never crashes on list-root ─────────────────────────


def test_payload_date_returns_none_for_list_root():
    assert mod._payload_date([1, 2, 3]) is None


def test_payload_date_returns_value_when_dict_has_date():
    assert mod._payload_date({"date": "2026-05-15"}) == "2026-05-15"


def test_payload_date_returns_none_when_dict_lacks_date():
    assert mod._payload_date({"foo": "bar"}) is None


# ── End-to-end regression: any payload that passes the dashboard
# render contract must also pass this verifier ───────────────────────


def test_end_to_end_canonical_payload_passes_both_contracts(tmp_path, monkeypatch):
    """The exact regression from run 25955470154: a canonical-shape
    pmf_research.json that PASSED the dashboard render contract still
    crashed this verifier. They must now agree."""
    import sys

    repo = tmp_path
    date = "2026-05-15"

    pred_dir = repo / "predictions"
    pred_dir.mkdir(parents=True)
    aff_date_dir = repo / "public_export" / "wizard_of_odds" / date
    aff_date_dir.mkdir(parents=True)
    aff_latest_dir = repo / "public_export" / "wizard_of_odds" / "latest"
    aff_latest_dir.mkdir(parents=True)
    aff_root_dir = repo / "public_export" / "wizard_of_odds"

    # Required HTML stubs (size > 5KB for the props page).
    (pred_dir / "nba-props.html").write_text("a" * 8192)
    (pred_dir / "nba-pmf-research.html").write_text("a" * 4096)

    aff_payload = {
        "date": date,
        "rows": [
            {
                "player": "Bob",
                "stat": "pts",
                "side": "OVER",
                "line": 23.5,
                "model_prob": 0.55,
                "market_prob": 0.51,
            }
        ],
    }
    pmf_payload = {
        "date": date,
        "players": [
            {
                "player": "Bob",
                "player_id": 1,
                "stats": [
                    {
                        "stat": "pts",
                        "support": [0, 1, 2],
                        "probs": [0.25, 0.5, 0.25],
                    }
                ],
            }
        ],
        "pmfs": [
            {
                "player_id": 1,
                "stat": "pts",
                "player": "Bob",
                "support": [0, 1, 2],
                "probs": [0.25, 0.5, 0.25],
                "mean": 1.0,
                "variance": 0.5,
            }
        ],
    }
    for d in (aff_date_dir, aff_latest_dir, aff_root_dir):
        (d / "affiliate_dashboard.json").write_text(json.dumps(aff_payload))
        (d / "pmf_research.json").write_text(json.dumps(pmf_payload))

    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    monkeypatch.setattr(mod, "PRED_DIR", pred_dir)
    monkeypatch.setattr(mod, "EXPORT_ROOT", repo / "public_export" / "wizard_of_odds")
    monkeypatch.setattr(sys, "argv", ["verify", "--date", date])
    rc = mod.main()
    assert rc == 0


def test_end_to_end_legacy_payload_still_passes(tmp_path, monkeypatch):
    """Legacy producer (publish_woo_public_export.py) is still
    supported."""
    import sys

    repo = tmp_path
    date = "2026-05-15"

    pred_dir = repo / "predictions"
    pred_dir.mkdir(parents=True)
    for sub in ("", "latest", date):
        d = repo / "public_export" / "wizard_of_odds" / sub
        d.mkdir(parents=True, exist_ok=True)

    (pred_dir / "nba-props.html").write_text("a" * 8192)

    aff_payload = {
        "date": date,
        "rows": [
            {
                "player": "Bob",
                "stat": "pts",
                "side": "OVER",
                "line": 23.5,
                "model_prob": 0.55,
                "market_prob": 0.51,
            }
        ],
    }
    pmf_payload = {
        "date": date,
        "players": [
            {
                "player": "Bob",
                "stats": {
                    "pts": {
                        "support_points": [
                            {"k": 0, "p": 0.25, "label": "0", "is_tail": False},
                            {"k": 1, "p": 0.5, "label": "1", "is_tail": False},
                            {"k": 2, "p": 0.25, "label": "2", "is_tail": False},
                        ]
                    }
                },
            }
        ],
    }
    for sub in ("", "latest", date):
        d = repo / "public_export" / "wizard_of_odds" / sub
        (d / "affiliate_dashboard.json").write_text(json.dumps(aff_payload))
        (d / "pmf_research.json").write_text(json.dumps(pmf_payload))

    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    monkeypatch.setattr(mod, "PRED_DIR", pred_dir)
    monkeypatch.setattr(mod, "EXPORT_ROOT", repo / "public_export" / "wizard_of_odds")
    monkeypatch.setattr(sys, "argv", ["verify", "--date", date])
    rc = mod.main()
    assert rc == 0
