"""Phase 13W Part C — daily retrain / recalibration proof verifier.

For ``--as-of-date``, asserts that the daily training pipeline left
real artifacts behind:

  * artifacts/model_daily_reports/<date>/daily_model_training_report.{json,md}
  * the contextual challenger's train_manifest, no_leakage_manifest,
    promotion_decision (when promoted)
  * champion_pointer references the Phase 13S feature_set_id

Pass:    PHASE13W_DAILY_RETRAIN_RECALIBRATION_PASS
Pending: PHASE13W_DAILY_RETRAIN_RECALIBRATION_PENDING
Fail:    PHASE13W_DAILY_RETRAIN_RECALIBRATION_FAILED
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


PHASE13S_FEATURE_SET_ID = "phase13s_direct_lineup_injury_pmf_driver_v1"


def _exists(p: Path) -> bool:
    return p.exists() and p.stat().st_size > 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of-date", required=True)
    args = p.parse_args(argv)

    issues: list[str] = []
    facts: dict = {"as_of_date": args.as_of_date}

    pointer_path = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    if not _exists(pointer_path):
        return _emit("FAILED", ["champion_pointer.json missing"], facts)
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    facts["champion_model_id"] = pointer.get("champion_model_id")
    facts["feature_set_id"] = pointer.get("feature_set_id")
    facts["direct_lineup_pmf_driver"] = pointer.get("direct_lineup_pmf_driver")
    facts["trained_through_date"] = (
        pointer.get("contextual_trained_through_date")
        or pointer.get("trained_through_date")
    )
    facts["calibrated_through_date"] = (
        pointer.get("contextual_calibrated_through_date")
        or pointer.get("calibrated_through_date")
    )

    if pointer.get("feature_set_id") != PHASE13S_FEATURE_SET_ID:
        issues.append(
            f"champion_pointer.feature_set_id="
            f"{pointer.get('feature_set_id')!r} expected "
            f"{PHASE13S_FEATURE_SET_ID!r}"
        )

    daily_dir = REPO_ROOT / "artifacts" / "model_daily_reports" / args.as_of_date
    daily_md = daily_dir / "daily_model_training_report.md"
    daily_json = daily_dir / "daily_model_training_report.json"
    if not _exists(daily_md):
        issues.append(f"daily_model_training_report.md missing at {daily_md}")
    if not _exists(daily_json):
        issues.append(f"daily_model_training_report.json missing at {daily_json}")

    challenger_dir_rel = pointer.get("contextual_challenger_dir")
    if not challenger_dir_rel:
        issues.append("champion_pointer.contextual_challenger_dir empty")
    else:
        ch_dir = REPO_ROOT / challenger_dir_rel
        for required in (
            "train_manifest.json",
            "no_leakage_manifest.json",
            "promotion_decision.json",
        ):
            p = ch_dir / required
            if not _exists(p):
                issues.append(f"{required} missing at {p}")
            else:
                facts.setdefault("contextual_challenger_files", {})[required] = (
                    str(p.relative_to(REPO_ROOT))
                )

        # Train manifest must show trained_through and calibrated_through.
        tm_path = ch_dir / "train_manifest.json"
        if _exists(tm_path):
            tm = json.loads(tm_path.read_text(encoding="utf-8"))
            facts["train_manifest"] = {
                "trained_through_date": tm.get("trained_through_date"),
                "calibrated_through_date": tm.get("calibrated_through_date"),
                "feature_set_id": tm.get("feature_set_id"),
                "fitted_targets": tm.get("fitted_targets"),
                "any_positive_improvement": (
                    any(
                        isinstance(v, dict)
                        and float(v.get("rel_improvement") or 0.0) > 0
                        for v in (tm.get("metrics_per_target") or {}).values()
                    )
                ),
            }
            if not tm.get("trained_through_date"):
                issues.append("train_manifest.trained_through_date empty")
            if not tm.get("calibrated_through_date"):
                issues.append("train_manifest.calibrated_through_date empty")

        # No-leakage manifest must say no_leakage_verified=True.
        nl_path = ch_dir / "no_leakage_manifest.json"
        if _exists(nl_path):
            nl = json.loads(nl_path.read_text(encoding="utf-8"))
            facts["no_leakage_manifest"] = {
                "no_leakage_verified": nl.get("no_leakage_verified"),
                "no_same_game_performance_predictors": nl.get(
                    "no_same_game_performance_predictors"
                ),
                "asof_cutoff_rule_recorded": bool(nl.get("asof_cutoff_rule")),
            }
            if not nl.get("no_leakage_verified"):
                issues.append("no_leakage_manifest.no_leakage_verified is not True")

        # Promotion decision: either promoted=True, or contains an
        # explicit blocker.
        pd_path = ch_dir / "promotion_decision.json"
        if _exists(pd_path):
            pd = json.loads(pd_path.read_text(encoding="utf-8"))
            facts["promotion_decision"] = {
                "promoted": pd.get("promoted"),
                "decision_id": pd.get("decision_id"),
                "blocked_reason": pd.get("blocked_reason"),
            }
            if pd.get("promoted") is not True and not pd.get("blocked_reason"):
                issues.append(
                    "promotion_decision.promoted is not True and no "
                    "blocked_reason recorded"
                )

    # Validation report path from pointer must exist and have no issues.
    vr_path_rel = pointer.get("validation_report_path")
    if vr_path_rel:
        vr_path = REPO_ROOT / vr_path_rel
        if _exists(vr_path):
            vr = json.loads(vr_path.read_text(encoding="utf-8"))
            facts["validation_report"] = {
                "any_positive_improvement": vr.get("any_positive_improvement"),
                "issues": vr.get("issues"),
                "minutes_min_rel_improvement": vr.get("minutes_min_rel_improvement"),
                "safe_noninferiority_threshold": vr.get(
                    "safe_noninferiority_threshold"
                ),
            }
            if vr.get("issues"):
                issues.append(
                    f"validation_report has issues: {vr.get('issues')}"
                )
        else:
            issues.append(f"validation_report missing at {vr_path}")

    facts["issues"] = issues
    out_dir = REPO_ROOT / "artifacts" / "automation_health"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"daily_retrain_recalibration_{args.as_of_date}.json").write_text(
        json.dumps({
            "schema_version": "1.0",
            "outcome": "fail" if issues else "pass",
            "facts": facts,
        }, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    if issues:
        return _emit("FAILED", issues, facts)
    return _emit("PASS", [], facts)


def _emit(outcome: str, issues: list[str], facts: dict) -> int:
    if outcome == "PASS":
        print("PHASE13W_DAILY_RETRAIN_RECALIBRATION_PASS")
        print(
            f"  feature_set_id={facts.get('feature_set_id')} "
            f"trained_through={facts.get('trained_through_date')} "
            f"calibrated_through={facts.get('calibrated_through_date')}"
        )
        return 0
    if outcome == "PENDING":
        print("PHASE13W_DAILY_RETRAIN_RECALIBRATION_PENDING")
        for i in issues:
            print(f"  - {i}")
        return 0
    print("PHASE13W_DAILY_RETRAIN_RECALIBRATION_FAILED", file=sys.stderr)
    for i in issues:
        print(f"  - {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
