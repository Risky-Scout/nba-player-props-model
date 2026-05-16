"""Regression: WoO dashboard verifier must be schema-safe across both
``pmf_research.json`` producer regimes.

Run 25952350180 root-caused to the verifier calling ``.items()`` on a
``list`` because ``build_woo_pmf_research_from_canonical.py`` emits
``players[].stats`` as a list of stat-atom dicts while the legacy
producer emits it as a dict keyed by stat name."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "verify_woo_dashboard_render_contract",
    REPO / "scripts" / "verify_woo_dashboard_render_contract.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_extract_players_from_legacy_dict_shape():
    """Legacy shape: ``{"players": [{...}]}`` — the historical contract."""
    payload = {"players": [{"player": "Alice", "stats": {}}]}
    assert mod._extract_pmf_research_players(payload) == payload["players"]


def test_extract_players_from_canonical_dict_shape():
    """Canonical builder shape: dict with ``players`` *list* of atom dicts."""
    payload = {
        "players": [
            {"player": "Bob", "stats": [{"stat": "pts", "support": [0, 1], "probs": [0.5, 0.5]}]}
        ],
        "pmfs": [{"stat": "pts"}],
    }
    out = mod._extract_pmf_research_players(payload)
    assert len(out) == 1
    assert isinstance(out[0]["stats"], list)


def test_extract_players_from_list_root():
    """Bare-list root: treat the list itself as the players collection."""
    payload = [{"player": "Cara", "stats": {}}]
    assert mod._extract_pmf_research_players(payload) == payload


def test_extract_players_falls_back_to_rows_records_data_keys():
    for key in ("rows", "data", "records", "items"):
        payload = {key: [{"player": "X", "stats": {}}]}
        assert mod._extract_pmf_research_players(payload) == payload[key]


def test_extract_players_invalid_shape_raises_with_marker():
    with pytest.raises(ValueError) as excinfo:
        mod._extract_pmf_research_players(42)
    assert "PMF_RESEARCH_JSON_SCHEMA_INVALID" in str(excinfo.value)
    assert "root_type=int" in str(excinfo.value)


def test_iter_player_stats_never_calls_items_on_list():
    """The exact regression: ``stats`` is a list. The iterator must
    extract ``(stat_name, obj)`` pairs without ``AttributeError``."""
    player = {
        "player": "Bob",
        "stats": [
            {"stat": "pts", "support": [0, 1], "probs": [0.5, 0.5]},
            {"stat_key": "reb", "support": [0], "probs": [1.0]},
        ],
    }
    pairs = list(mod._iter_player_stats(player))
    assert pairs[0][0] == "pts"
    assert pairs[1][0] == "reb"
    assert all(isinstance(o, dict) for _, o in pairs)


def test_iter_player_stats_legacy_dict_shape():
    player = {"player": "Alice", "stats": {"pts": {"support_points": []}}}
    pairs = list(mod._iter_player_stats(player))
    assert pairs == [("pts", {"support_points": []})]


def test_iter_player_stats_unknown_shape_raises():
    with pytest.raises(ValueError):
        list(mod._iter_player_stats({"stats": "bad"}))


def test_stat_support_points_from_support_probs():
    obj = {"support": [0, 1, 2], "probs": [0.2, 0.3, 0.5]}
    sp = mod._stat_support_points(obj)
    assert [pt["k"] for pt in sp] == [0, 1, 2]
    assert [pt["p"] for pt in sp] == [0.2, 0.3, 0.5]
    assert all(pt["is_tail"] is False for pt in sp)


def test_stat_support_points_passthrough_legacy_support_points():
    obj = {"support_points": [{"k": 0, "p": 1.0, "label": "0", "is_tail": False}]}
    sp = mod._stat_support_points(obj)
    assert sp == obj["support_points"]


def test_stat_support_points_empty_when_no_recognised_shape():
    assert mod._stat_support_points({}) == []
    assert mod._stat_support_points({"support": [1, 2], "probs": [0.5]}) == []


def test_verifier_does_not_require_model_prob_on_pmf_distribution_rows(tmp_path, monkeypatch):
    """The dashboard render-contract verifier only enforces
    ``model_prob`` non-null on ``affiliate_dashboard.json`` rows — the
    *market-side* artifact. ``pmf_research.json`` rows are PMF
    distribution rows and must not be probed for ``model_prob``."""
    import json
    import sys

    repo = tmp_path
    date = "2026-05-15"

    aff_dir = repo / "public_export" / "wizard_of_odds" / date
    aff_dir.mkdir(parents=True)
    pred_dir = repo / "predictions"
    pred_dir.mkdir()

    # Market rows DO carry model_prob (verifier requirement for the
    # affiliate dashboard).
    aff_rows = [
        {"player_id": pid, "stat": "pts", "side": "OVER", "model_prob": 0.55}
        for pid in range(3)
    ]
    (aff_dir / "affiliate_dashboard.json").write_text(
        json.dumps({"rows": aff_rows, "count": len(aff_rows)})
    )

    # PMF distribution rows DO NOT carry model_prob. The verifier must
    # tolerate this.
    pmf_payload = {
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
                "support": [0, 1, 2],
                "probs": [0.25, 0.5, 0.25],
                "mean": 1.0,
                "variance": 0.5,
            }
        ],
    }
    (aff_dir / "pmf_research.json").write_text(json.dumps(pmf_payload))

    props_html = "\n".join(["dummy", *mod.REQUIRED_PROPS_PRESENT])
    pmf_html = "\n".join(["dummy", *mod.REQUIRED_PMF_PRESENT])
    (pred_dir / "nba-props.html").write_text(props_html)
    (pred_dir / "nba-pmf-research.html").write_text(pmf_html)

    monkeypatch.setattr(sys, "argv", ["verify", "--date", date])
    monkeypatch.setattr(mod, "__file__", str(repo / "scripts" / "verify.py"))
    rc = mod.main()
    assert rc == 0


def test_verifier_passes_on_canonical_shape_fixture(tmp_path, monkeypatch):
    """End-to-end sanity: synthesize a canonical-shape pmf_research.json
    plus matching affiliate_dashboard.json (every row has a non-null
    ``model_prob``) and confirm ``main()`` exits 0."""
    import json
    import sys

    repo = tmp_path
    date = "2026-05-15"

    aff_dir = repo / "public_export" / "wizard_of_odds" / date
    aff_dir.mkdir(parents=True)
    pred_dir = repo / "predictions"
    pred_dir.mkdir()

    # 456-row-like affiliate payload, all model_prob set.
    aff_rows = [
        {
            "player_id": pid,
            "stat": "pts",
            "side": "OVER" if pid % 2 == 0 else "UNDER",
            "model_prob": 0.55 if pid % 2 == 0 else 0.45,
        }
        for pid in range(456)
    ]
    (aff_dir / "affiliate_dashboard.json").write_text(
        json.dumps({"rows": aff_rows, "count": len(aff_rows)})
    )

    # Canonical-shape PMF research: stats as a list of stat-atom dicts.
    pmf_payload = {
        "schema_version": "m8_6o_pmf_research_v1",
        "players": [
            {
                "player": f"Player {i}",
                "player_id": i,
                "stats": [
                    {
                        "stat": "pts",
                        "support": [0, 1, 2],
                        "probs": [0.25, 0.5, 0.25],
                    }
                ],
            }
            for i in range(5)
        ],
        "pmfs": [],
    }
    (aff_dir / "pmf_research.json").write_text(json.dumps(pmf_payload))

    # Minimal HTML shells satisfying the required-needle checks. We test
    # JSON shape here; the HTML checks have their own separate coverage.
    props_html = "\n".join(["dummy", *mod.REQUIRED_PROPS_PRESENT])
    pmf_html = "\n".join(["dummy", *mod.REQUIRED_PMF_PRESENT])
    (pred_dir / "nba-props.html").write_text(props_html)
    (pred_dir / "nba-pmf-research.html").write_text(pmf_html)

    monkeypatch.setattr(sys, "argv", ["verify", "--date", date])
    monkeypatch.setattr(mod, "__file__", str(repo / "scripts" / "verify.py"))
    # The verifier resolves the repo root via __file__.parent.parent so
    # the patch above puts ``tmp_path`` at the repo root.
    rc = mod.main()
    assert rc == 0
