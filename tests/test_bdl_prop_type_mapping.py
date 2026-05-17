"""BDL prop_type → internal stat mapping contract tests.

These tests pin down the authoritative BDL prop_type names that
``scripts/build_derek_forward_feed.py`` uses when fetching the
``/v2/odds/player_props`` endpoint for the Derek BDL main-line
summary.

The mapping is authoritative per the official BDL docs
(https://docs.balldontlie.io/nba/api-reference/odds-player-props —
"Supported Prop Types" table, verified 2026-05-17).

Important: ``tov`` (turnovers) and ``stocks`` (steals+blocks) are
internal model stats — BDL does NOT publish either as an
``over_under`` ``prop_type``. They must therefore NOT appear in the
Derek BDL main-line summary; tests below assert this explicitly so
a future regression cannot silently fabricate a "line" for an
unsupported stat.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load_build_derek_forward_feed_module():
    spec = importlib.util.spec_from_file_location(
        "_build_derek_forward_feed_mapping_test",
        REPO / "scripts" / "build_derek_forward_feed.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_bdl_prop_type_to_stat_singles_match_docs():
    mod = _load_build_derek_forward_feed_module()
    m = mod.BDL_PROP_TYPE_TO_STAT
    # Singles (over_under markets only).
    assert m["points"] == "pts"
    assert m["rebounds"] == "reb"
    assert m["assists"] == "ast"
    assert m["threes"] == "fg3m"
    assert m["blocks"] == "blk"
    assert m["steals"] == "stl"


def test_bdl_prop_type_to_stat_combos_match_docs():
    mod = _load_build_derek_forward_feed_module()
    m = mod.BDL_PROP_TYPE_TO_STAT
    # Combos (over_under markets only).
    assert m["points_rebounds"] == "pr"
    assert m["points_assists"] == "pa"
    assert m["rebounds_assists"] == "ra"
    assert m["points_rebounds_assists"] == "pra"


def test_bdl_mapping_excludes_milestone_and_quarter_markets():
    """BDL also exposes ``points_1q`` / ``assists_first3min`` /
    ``double_double`` / ``triple_double`` etc. Those are explicitly
    out of scope for Derek's main-line summary contract — they must
    not appear in the mapping."""
    mod = _load_build_derek_forward_feed_module()
    m = mod.BDL_PROP_TYPE_TO_STAT
    for excluded in (
        "points_1q", "rebounds_1q", "assists_1q",
        "points_first3min", "rebounds_first3min", "assists_first3min",
        "double_double", "triple_double",
    ):
        assert excluded not in m, (
            f"{excluded} must not appear in BDL_PROP_TYPE_TO_STAT — "
            "first-quarter / first-3-minute / milestone markets are "
            "out of scope for Derek's main-line summary."
        )


def test_bdl_mapping_omits_unsupported_internal_stats():
    """BDL does NOT publish turnovers (``tov``) or
    stocks/blocks_steals (``stocks``) as over_under prop_types.

    Internal model stats that have no BDL counterpart must NOT
    appear in the public Derek BDL summary — there is no offered
    market line, so no honest market_line can be selected.

    These two are recorded explicitly on the writer module as
    ``BDL_UNSUPPORTED_INTERNAL_STATS`` so any future engineer
    deciding to add them sees a deliberate guard.
    """
    mod = _load_build_derek_forward_feed_module()
    m = mod.BDL_PROP_TYPE_TO_STAT
    # No BDL prop_type maps to "tov".
    assert "tov" not in m.values()
    # No BDL prop_type maps to "stocks".
    assert "stocks" not in m.values()
    # No candidate BDL prop_type name appears in the mapping.
    for candidate in (
        "turnovers", "tov",
        "stocks", "blocks_steals", "steals_blocks",
    ):
        assert candidate not in m, (
            f"BDL does NOT publish {candidate!r} as an over_under "
            "prop_type — keep it out of BDL_PROP_TYPE_TO_STAT."
        )
    # Surface the explicit exclusion list for future audit clarity.
    assert "tov" in mod.BDL_UNSUPPORTED_INTERNAL_STATS
    assert "stocks" in mod.BDL_UNSUPPORTED_INTERNAL_STATS


def test_bdl_mapping_size_matches_user_contract():
    """The user contract enumerates exactly 10 main lines:
    pts, reb, ast, fg3m, blk, stl, pa, pr, ra, pra.

    Any addition or removal should be a conscious decision, so we
    pin the size."""
    mod = _load_build_derek_forward_feed_module()
    assert len(mod.BDL_PROP_TYPE_TO_STAT) == 10
