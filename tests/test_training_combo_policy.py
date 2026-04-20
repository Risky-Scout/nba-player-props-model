"""Guardrail: combo targets must not be fed to the direct quantile trainer.

Combos are priced from component-PMF simulation downstream. Sending pra/pr/
pa/ra/stocks through train_target_model produced empty-row WARNINGs during
the rebuild — this test fails if the iteration list regresses.
"""
from __future__ import annotations

import ast
from pathlib import Path


def test_main_iterates_only_single_stats_for_direct_training():
    src = Path(__file__).parent.parent / "src/nba_props_model/pipelines/train.py"
    tree = ast.parse(src.read_text())
    main_fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    # Collect every `for target in <X>:` in main()
    for_targets: list[str] = []
    for node in ast.walk(main_fn):
        if (
            isinstance(node, ast.For)
            and isinstance(node.target, ast.Name)
            and node.target.id == "target"
            and isinstance(node.iter, ast.Name)
        ):
            for_targets.append(node.iter.id)

    assert for_targets, "no `for target in <iter>:` loop found in main()"
    # Every per-target training loop must iterate STATS, not ALL_TARGETS.
    assert all(name == "STATS" for name in for_targets), (
        f"direct trainer must iterate STATS only; found {for_targets}"
    )


def test_combo_formulas_reference_only_single_stats():
    """If someone adds a new combo, its formula must only reference single
    stats — combos composed of combos are a data-contract violation."""
    from nba_props_model.pipelines.train import COMBO_FORMULA

    SINGLE = {"pts", "reb", "ast", "fg3m", "stl", "blk", "tov"}
    for combo, parts in COMBO_FORMULA.items():
        for p in parts:
            assert p in SINGLE, f"combo {combo!r} references non-single stat {p!r}"
