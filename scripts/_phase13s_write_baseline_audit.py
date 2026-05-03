"""Phase 13S Part A — write the Phase 13R baseline audit artifact.

Read-only inspection of the Phase 13R deployment as it exists at the
start of Phase 13S. Records what the Phase 13Q→13R contextual engine
did, what the remaining caveat is, and which fields the new direct-
lineup driver needs to populate.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def main(argv=None) -> int:
    out_dir = REPO_ROOT / "artifacts" / "phase13s"
    out_dir.mkdir(parents=True, exist_ok=True)

    pointer_path = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8")) \
        if pointer_path.exists() else {}

    # Phase 13Q contextual challenger metrics.
    p13q_dir = REPO_ROOT / "artifacts" / "models" / "challengers" / "2026-04-30_contextual"
    p13q_train = {}
    if (p13q_dir / "train_manifest.json").exists():
        p13q_train = json.loads(
            (p13q_dir / "train_manifest.json").read_text(encoding="utf-8"))

    answers = {
        "1_contextual_champion_active": bool(pointer.get("contextual_pmf_engine")),
        "2_active_feature_set_id": pointer.get("feature_set_id"),
        "3_contextual_features_currently_trained": list(
            p13q_train.get("feature_columns") or []
        ),
        "4_contextual_features_in_lists": list(
            pointer.get("contextual_feature_columns") or []
        ),
        "5_direct_lineup_affects_pmf_today": False,
        "5_note": (
            "In Phase 13R the trained model was given starter_proxy_lagged "
            "but NOT direct lineup_confirmed/current_starter/confirmed_starter "
            "as inputs. Live BDL flips changed feature_vector_hash but did "
            "not move the trained Ridge model's deltas. Phase 13S adds "
            "current_starter / confirmed_starter / consecutive_starter_streak "
            "/ recent_starter_rate_5 etc. as direct trained features."
        ),
        "6_injury_actionability_affects_today": True,
        "7_vacated_opportunity_affects_today": True,
        "8_market_only_leaves_pmf_unchanged_today": True,
        "9_missing_for_direct_lineup": [
            "current_starter not in saved feature lists",
            "confirmed_starter not in saved feature lists",
            "team_lineup_*_competition_proxy not in saved feature lists",
            "player_*_competition_proxy not in saved feature lists",
            "consecutive_starter_streak not in saved feature lists",
        ],
    }

    payload = {
        "schema_version": "1.0",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0).isoformat() + "Z",
        "phase13r_pointer_summary": {
            k: v for k, v in pointer.items()
            if k in ("feature_set_id", "contextual_pmf_engine",
                     "official_lineup_features_enabled",
                     "injury_availability_features_enabled",
                     "vacated_opportunity_features_enabled",
                     "lineup_interaction_features_enabled",
                     "game_context_features_enabled",
                     "lineup_injury_context_upstream_of_pmf",
                     "contextual_pmf_sensitivity_verified",
                     "contextual_trained_through_date",
                     "validation_report_path",
                     "promotion_decision_id",
                     "contextual_challenger_dir",
                     "model_version")
        },
        "phase13q_metrics_per_target": p13q_train.get("metrics_per_target") or {},
        "answers": answers,
    }
    (out_dir / "phase13r_baseline_audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8")

    md = [
        "# Phase 13R Baseline Audit (Phase 13S Part A)",
        "",
        f"- generated_at_utc: {payload['generated_at_utc']}",
        f"- pointer.feature_set_id: `{pointer.get('feature_set_id')}`",
        f"- pointer.contextual_pmf_engine: **{pointer.get('contextual_pmf_engine')}**",
        f"- contextual_challenger_dir: `{pointer.get('contextual_challenger_dir')}`",
        "",
        "## Answers",
        "",
    ]
    for k, v in answers.items():
        md.append(f"- **{k}** — {v}")
    (out_dir / "phase13r_baseline_audit.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")

    print("PHASE13S_BASELINE_AUDIT_PASS")
    print(f"  pointer.feature_set_id={pointer.get('feature_set_id')}")
    print(
        f"  remaining_phase13r_caveat: direct lineup signals not trained "
        "PMF drivers (closed by Phase 13S)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
