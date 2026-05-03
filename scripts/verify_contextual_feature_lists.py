"""Phase 13R Part B — feature-list proof.

Inspects the actual Phase 13Q contextual challenger artifacts and
proves the trained models consume the contextual feature columns we
claimed:

  * ``feature_set_id == phase13q_contextual_pmf_engine_v1`` (or successor)
  * saved feature lists exist on disk (one .pkl per fitted target)
  * each saved feature list contains:
      - lineup / starter context  (``starter_proxy_lagged``)
      - injury / availability context (``is_actionable``,
        ``is_confirmed_out``, ``injury_status_encoded``, ...)
      - vacated-opportunity context (``vacated_minutes_*``,
        ``num_teammates_out_*``)
      - game-context (``is_home``, ``rest_days``, ``is_back_to_back``,
        ``season_game_number``, ``opponent_team_id_hash``)
  * the minutes model was actually fit on those columns
  * at least one stat-rate model was actually fit on those columns
  * the contextual scoring helper can load every saved list and produce
    a non-empty score dict for a synthetic row

If any of those fails, the verifier exits non-zero with the exact
column / artifact / target that is missing.

Pass line:  PHASE13R_CONTEXTUAL_FEATURE_LISTS_PASS
Fail line:  PHASE13R_CONTEXTUAL_FEATURE_LISTS_FAILED
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.contextual import (  # noqa: E402
    CONTEXTUAL_FEATURE_SET_ID,
    build_context_feature_row,
    load_contextual_engine,
)


REQUIRED_GROUPS = {
    "lineup_status": ("starter_proxy_lagged",),
    "injury_availability": (
        "is_actionable", "is_confirmed_out", "injury_status_encoded",
        "availability_status_encoded",
    ),
    "vacated_opportunity": (
        "vacated_minutes_total", "num_teammates_out_total",
    ),
    "game_context": (
        "is_home", "rest_days", "is_back_to_back", "is_three_in_four",
        "season_game_number", "opponent_team_id_hash",
    ),
}

# Targets we expect to see at least one of in fitted models.
EXPECTED_RATE_TARGETS = ("pts", "reb", "ast", "tov", "stl", "blk", "fg3m")


def _find_challenger_dirs(arg_dir: str | None) -> list[Path]:
    if arg_dir:
        return [Path(arg_dir)]
    root = REPO_ROOT / "artifacts" / "models" / "challengers"
    if not root.exists():
        return []
    # Phase 13R-baseline verifier accepts Phase 13Q + 13S directories.
    # When a Phase 13S direct-lineup challenger is present, exercise it
    # (it's a strict superset of the Phase 13Q feature set).
    direct = sorted(d for d in root.iterdir()
                    if d.is_dir() and d.name.endswith("_direct_lineup_contextual"))
    if direct:
        return direct
    return sorted(d for d in root.iterdir()
                  if d.is_dir() and d.name.endswith("_contextual"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--challenger-dir", default=None)
    args = p.parse_args(argv)

    issues: list[str] = []
    facts: dict = {}

    targets = _find_challenger_dirs(args.challenger_dir)
    if not targets:
        print("PHASE13R_CONTEXTUAL_FEATURE_LISTS_FAILED", file=sys.stderr)
        print("  reason: no <date>_contextual challenger directories found",
              file=sys.stderr)
        return 1

    for d in targets:
        d_facts: dict = {"path": str(d.relative_to(REPO_ROOT))}
        try:
            engine = load_contextual_engine(d)
        except Exception as exc:
            issues.append(f"{d.name}: cannot load contextual engine: {exc}")
            facts[d.name] = d_facts
            continue

        d_facts["feature_set_id"] = engine.feature_set_id
        d_facts["fitted_targets"] = list(engine.fitted_targets)
        d_facts["feature_list_hashes"] = dict(engine.feature_list_hashes)

        if not engine.feature_set_id.startswith(("phase13q_", "phase13r_", "phase13s_")):
            issues.append(
                f"{d.name}: feature_set_id={engine.feature_set_id!r} is not "
                "a Phase 13Q/13R/13S contextual feature set"
            )
        if engine.feature_set_id not in (
            CONTEXTUAL_FEATURE_SET_ID,
            "phase13q_contextual_lineup_injury_game_v1",  # alt name from prompt
        ):
            d_facts["feature_set_id_note"] = (
                f"observed={engine.feature_set_id!r} "
                f"expected={CONTEXTUAL_FEATURE_SET_ID!r}"
            )

        # Per-stat saved feature lists.
        if "minutes" not in engine.feature_lists:
            issues.append(f"{d.name}: minutes feature list missing")
        seen_rate_target = None
        for stat in EXPECTED_RATE_TARGETS:
            if stat in engine.feature_lists:
                seen_rate_target = stat
                break
        if seen_rate_target is None:
            issues.append(
                f"{d.name}: no stat-rate adjustment feature list found "
                f"(expected one of {EXPECTED_RATE_TARGETS})"
            )

        # Required column groups in EVERY saved list.
        for stat, cols in engine.feature_lists.items():
            cset = set(cols)
            for group, members in REQUIRED_GROUPS.items():
                missing = [c for c in members if c not in cset]
                if missing:
                    issues.append(
                        f"{d.name}/{stat}: missing {group} columns "
                        f"{missing}"
                    )

        # Functional check: build a synthetic feature row and produce a
        # score dict. This proves the on-disk feature lists are
        # *consumable* by the engine and not stale relative to the
        # builder.
        synthetic_row = {
            "is_actionable": True,
            "is_confirmed_out": False,
            "is_inactive": False,
            "is_doubtful": False,
            "is_questionable": False,
            "is_probable": True,
            "injury_status_encoded": 2.0,
            "availability_status_encoded": 1.0,
            "injury_features_missing": 0.0,
            "vacated_features_missing": 0.0,
            "num_teammates_out_total": 1.0,
            "num_teammates_out_guard": 0.0,
            "num_teammates_out_wing": 1.0,
            "num_teammates_out_big": 0.0,
            "vacated_minutes_total": 25.0,
            "vacated_minutes_guard": 0.0,
            "vacated_minutes_wing": 25.0,
            "vacated_minutes_big": 0.0,
            "vacated_fga_total": 12.0,
            "starter_proxy_lagged": 1.0,
            "is_home": 1.0,
            "rest_days": 2.0,
            "is_back_to_back": 0.0,
            "is_three_in_four": 0.0,
            "season_game_number": 41.0,
            "season_game_number_norm": 0.5,
            "opponent_team_id_hash": 7.0,
        }
        try:
            scores = engine.score_row(synthetic_row)
        except Exception as exc:
            issues.append(f"{d.name}: engine.score_row raised: {exc}")
            scores = {}
        d_facts["score_keys"] = sorted(scores.keys())
        if "minutes_delta" not in scores:
            issues.append(
                f"{d.name}: engine did not produce minutes_delta on "
                "synthetic row"
            )
        if not any(k.startswith("rate_delta_") for k in scores):
            issues.append(
                f"{d.name}: engine produced no rate_delta_* keys on "
                "synthetic row"
            )

        # Smoke test build_context_feature_row directly (cross-check
        # column-by-column projection).
        for stat, cols in engine.feature_lists.items():
            vec = build_context_feature_row(synthetic_row, feature_columns=cols)
            if len(vec) != len(cols):
                issues.append(
                    f"{d.name}/{stat}: build_context_feature_row produced "
                    f"{len(vec)} values for {len(cols)} columns"
                )
                break
        facts[d.name] = d_facts

    out_dir = REPO_ROOT / "artifacts" / "phase13r"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues": issues,
        "facts": facts,
        "expected_feature_set_id": CONTEXTUAL_FEATURE_SET_ID,
        "required_groups": {k: list(v) for k, v in REQUIRED_GROUPS.items()},
    }
    (out_dir / "contextual_feature_lists_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    if issues:
        print("PHASE13R_CONTEXTUAL_FEATURE_LISTS_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    print("PHASE13R_CONTEXTUAL_FEATURE_LISTS_PASS")
    for d in targets:
        f = facts.get(d.name) or {}
        print(
            f"  - {d.name}: feature_set_id={f.get('feature_set_id')} "
            f"fitted={f.get('fitted_targets')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
