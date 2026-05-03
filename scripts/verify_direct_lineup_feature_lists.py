"""Phase 13S Part E — direct lineup feature-list proof.

Inspects the Phase 13S challenger artifacts and asserts the trained
models genuinely consume direct lineup, lineup-composition, injury,
vacated-opportunity, and game-context features.

Pass line:  PHASE13S_DIRECT_LINEUP_FEATURE_LISTS_PASS
Fail line:  PHASE13S_DIRECT_LINEUP_FEATURE_LISTS_FAILED
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.contextual import load_contextual_engine  # noqa: E402
from nba_props_model.features.direct_lineup_context import (  # noqa: E402
    DIRECT_LINEUP_FEATURE_SET_ID,
)


REQUIRED_GROUPS = {
    "direct_lineup": (
        "current_starter",
        "confirmed_starter",
        "confirmed_bench",
    ),
    "starter_streak": (
        "consecutive_starter_streak",
        "recent_starter_rate_5",
    ),
    "lineup_composition": (
        "team_lineup_usage_competition_proxy",
        "team_lineup_rebound_competition_proxy",
        "team_confirmed_starters_count",
    ),
    "player_in_lineup_interaction": (
        "player_usage_competition_proxy",
        "player_rebound_competition_proxy",
    ),
    "injury": (
        "is_actionable",
        "is_confirmed_out",
        "injury_status_encoded",
    ),
    "vacated_opportunity": (
        "vacated_minutes_total",
        "num_teammates_out_total",
    ),
    "game_context": (
        "is_home", "rest_days", "is_back_to_back",
        "season_game_number", "opponent_team_id_hash",
    ),
}

EXPECTED_RATE_TARGETS = ("pts", "reb", "ast", "tov", "stl", "blk", "fg3m")


def _find_dirs(arg: str | None) -> list[Path]:
    if arg:
        return [Path(arg)]
    root = REPO_ROOT / "artifacts" / "models" / "challengers"
    if not root.exists():
        return []
    return sorted(d for d in root.iterdir()
                  if d.is_dir() and d.name.endswith("_direct_lineup_contextual"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--challenger-dir", default=None)
    args = p.parse_args(argv)

    issues: list[str] = []
    facts: dict = {}
    targets = _find_dirs(args.challenger_dir)
    if not targets:
        print("PHASE13S_DIRECT_LINEUP_FEATURE_LISTS_FAILED", file=sys.stderr)
        print("  reason: no <date>_direct_lineup_contextual dirs found",
              file=sys.stderr)
        return 1

    for d in targets:
        d_facts: dict = {"path": str(d.relative_to(REPO_ROOT))}
        try:
            engine = load_contextual_engine(d)
        except Exception as exc:
            issues.append(f"{d.name}: load failed: {exc}")
            facts[d.name] = d_facts
            continue
        d_facts["feature_set_id"] = engine.feature_set_id
        d_facts["fitted_targets"] = list(engine.fitted_targets)
        d_facts["minutes_feature_count"] = len(engine.feature_lists.get("minutes", []))

        if engine.feature_set_id != DIRECT_LINEUP_FEATURE_SET_ID:
            issues.append(
                f"{d.name}: feature_set_id={engine.feature_set_id!r} != "
                f"{DIRECT_LINEUP_FEATURE_SET_ID!r}"
            )

        if "minutes" not in engine.feature_lists:
            issues.append(f"{d.name}: minutes feature list missing")
        seen_rate = next(
            (s for s in EXPECTED_RATE_TARGETS if s in engine.feature_lists),
            None,
        )
        if seen_rate is None:
            issues.append(
                f"{d.name}: no stat-rate adjustment feature list found"
            )

        for stat, cols in engine.feature_lists.items():
            cset = set(cols)
            for group, members in REQUIRED_GROUPS.items():
                missing = [c for c in members if c not in cset]
                if missing:
                    issues.append(
                        f"{d.name}/{stat}: missing {group} columns {missing}"
                    )
        # Real .pkl artifacts present?
        pkl_count = len(list(d.glob("phase13s_*_features.pkl"))) + len(
            list(d.glob("phase13s_*_adjustment.pkl"))
        )
        d_facts["pkl_files_count"] = pkl_count
        if pkl_count < 2:
            issues.append(f"{d.name}: expected >= 2 phase13s_*.pkl files; got {pkl_count}")

        # Functional smoke test.
        synthetic = {
            "is_actionable": 1.0, "is_probable": 1.0,
            "current_starter": 1.0, "confirmed_starter": 1.0,
            "starter_proxy_lagged": 1.0, "is_home": 1.0,
            "rest_days": 2.0, "season_game_number": 41.0,
            "season_game_number_norm": 0.5,
            "team_lineup_usage_competition_proxy": 2.5,
            "team_lineup_rebound_competition_proxy": 1.0,
        }
        try:
            scores = engine.score_row(synthetic)
        except Exception as exc:
            issues.append(f"{d.name}: score_row raised: {exc}")
            scores = {}
        d_facts["score_keys"] = sorted(scores.keys())
        if "minutes_delta" not in scores:
            issues.append(f"{d.name}: engine produced no minutes_delta")

        facts[d.name] = d_facts

    out_dir = REPO_ROOT / "artifacts" / "phase13s"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues": issues,
        "facts": facts,
        "expected_feature_set_id": DIRECT_LINEUP_FEATURE_SET_ID,
        "required_groups": {k: list(v) for k, v in REQUIRED_GROUPS.items()},
    }
    (out_dir / "direct_lineup_feature_lists_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    if issues:
        print("PHASE13S_DIRECT_LINEUP_FEATURE_LISTS_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    print("PHASE13S_DIRECT_LINEUP_FEATURE_LISTS_PASS")
    for d in targets:
        f = facts.get(d.name) or {}
        print(
            f"  - {d.name}: feature_set_id={f.get('feature_set_id')} "
            f"fitted={f.get('fitted_targets')} "
            f"feat_count={f.get('minutes_feature_count')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
