"""Phase 13U Part J — daily model training / recalibration report.

Reads the active champion pointer + the contextual challenger
manifests, validation/no-leakage reports, and (when present) recent
after-game scoring outputs. Writes:

    artifacts/model_daily_reports/<as_of>/daily_model_training_report.json
    artifacts/model_daily_reports/<as_of>/daily_model_training_report.md

Pass line:  DAILY_MODEL_TRAINING_REPORT_PASS

Items that do not have available data are reported as "pending" with
the exact path/blocker — never fabricated.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _read_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of-date", required=True)
    args = p.parse_args(argv)

    out_dir = REPO_ROOT / "artifacts" / "model_daily_reports" / args.as_of_date
    out_dir.mkdir(parents=True, exist_ok=True)

    pointer = _read_json(REPO_ROOT / "artifacts" / "models" / "registry"
                         / "champion_pointer.json") or {}
    challenger_dir_rel = pointer.get("contextual_challenger_dir")
    challenger_dir = (REPO_ROOT / challenger_dir_rel) if challenger_dir_rel else None

    train_manifest = _read_json(challenger_dir / "train_manifest.json") \
        if challenger_dir else None
    no_leak_manifest = _read_json(challenger_dir / "no_leakage_manifest.json") \
        if challenger_dir else None
    promotion_decision = _read_json(challenger_dir / "promotion_decision.json") \
        if challenger_dir else None
    promotion_manifest = _read_json(challenger_dir / "promotion_manifest.json") \
        if challenger_dir else None

    validation_report_path = pointer.get("validation_report_path")
    validation_report = (
        _read_json(REPO_ROOT / validation_report_path) if validation_report_path else None
    )
    phase13s_no_leakage = _read_json(
        REPO_ROOT / "artifacts" / "phase13s" / "no_leakage_report.json"
    )
    phase13s_sensitivity = _read_json(
        REPO_ROOT / "artifacts" / "phase13s" / "direct_lineup_pmf_sensitivity.json"
    )

    # After-game scoring + rolling benchmark — pending if absent.
    after_game = _read_json(
        REPO_ROOT / "artifacts" / "phase13s" / "scoring" / args.as_of_date
        / "scoring_summary.json"
    )
    rolling_benchmark = _read_json(
        REPO_ROOT / "artifacts" / "automation_health"
        / f"rolling_derek_snapshot_benchmark_{args.as_of_date}.json"
    )

    metrics_per_target = (train_manifest or {}).get("metrics_per_target") or {}

    report = {
        "schema_version": "1.0",
        "as_of_date": args.as_of_date,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0).isoformat() + "Z",
        "champion": {
            "champion_model_id": pointer.get("champion_model_id"),
            "feature_set_id": pointer.get("feature_set_id"),
            "direct_lineup_pmf_driver": pointer.get("direct_lineup_pmf_driver"),
            "contextual_pmf_engine": pointer.get("contextual_pmf_engine"),
            "trained_through_date": (
                pointer.get("contextual_trained_through_date")
                or pointer.get("trained_through_date")
            ),
            "calibrated_through_date": (
                pointer.get("contextual_calibrated_through_date")
                or pointer.get("calibrated_through_date")
            ),
            "training_run_id": pointer.get("training_run_id"),
            "calibration_manifest_path": pointer.get("calibration_manifest_path"),
            "train_manifest_path": pointer.get("contextual_train_manifest_path")
                or pointer.get("train_manifest_path"),
            "validation_report_path": validation_report_path,
            "promotion_decision_path": pointer.get("contextual_promotion_decision_path")
                or pointer.get("promotion_decision_path"),
            "no_leakage_manifest_path": pointer.get("contextual_no_leakage_manifest_path"),
            "promotion_decision_id": pointer.get("promotion_decision_id"),
        },
        "promotion_status": {
            "promoted": bool((promotion_manifest or {}).get("promoted")
                              or promotion_decision and promotion_decision.get("promoted")),
            "promotion_decision": promotion_decision,
            "promotion_manifest": promotion_manifest,
        },
        "validation_gates": {
            "report": validation_report,
            "any_positive_improvement": (
                (validation_report or {}).get("any_positive_improvement")
            ),
            "issues": (validation_report or {}).get("issues"),
            "minutes_min_rel_improvement": (
                (validation_report or {}).get("minutes_min_rel_improvement")
            ),
            "safe_noninferiority_threshold": (
                (validation_report or {}).get("safe_noninferiority_threshold")
            ),
        },
        "metrics_per_target": metrics_per_target,
        "no_leakage": {
            "no_leakage_manifest": no_leak_manifest,
            "phase13s_no_leakage_report": phase13s_no_leakage,
        },
        "sensitivity": {
            "case_results": (phase13s_sensitivity or {}).get("case_results"),
            "issues_per_case": (phase13s_sensitivity or {}).get("issues_per_case"),
        },
        "after_game_scoring": after_game or {
            "outcome": "pending",
            "blocker": (
                "no after-game scoring summary found for as_of_date=" + args.as_of_date
            ),
        },
        "rolling_benchmark": rolling_benchmark or {
            "outcome": "pending",
            "blocker": (
                "no rolling Derek benchmark found for as_of_date=" + args.as_of_date
            ),
        },
        "calibration_metrics_pending": {
            "blocker": (
                "PMF NLL / RPS / ECE / p0 calibration / mean bias / tail "
                "calibration are reported once nightly post-game scoring "
                "produces realized outcomes. The Phase 13S/13T after-game "
                "scoring writes DEREK_LIVE_SNAPSHOT_SCORING_PENDING when "
                "outcomes are not yet available."
            ),
        },
    }

    (out_dir / "daily_model_training_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    # Phase 13T — explicit yes/no flags Derek can scan in 5 seconds.
    retrain_ran = bool((train_manifest or {}).get("trained_through_date"))
    recal_ran = bool((train_manifest or {}).get("calibrated_through_date"))
    no_leak_passed = bool(
        (no_leak_manifest or {}).get("no_leakage_verified")
        and (phase13s_no_leakage or {}).get("issues") in (None, [], [])
    )
    gates_passed = (
        validation_report is not None
        and not (validation_report or {}).get("issues")
        and (validation_report or {}).get("any_positive_improvement")
    )
    promoted = bool(report["promotion_status"]["promoted"])
    is_phase13s = (pointer.get("feature_set_id", "") or "").startswith("phase13s_")

    report["headline_summary"] = {
        "active_champion": pointer.get("champion_model_id"),
        "feature_set_id": pointer.get("feature_set_id"),
        "is_phase13s": is_phase13s,
        "trained_through_date": (
            pointer.get("contextual_trained_through_date")
            or pointer.get("trained_through_date")
        ),
        "calibrated_through_date": (
            pointer.get("contextual_calibrated_through_date")
            or pointer.get("calibrated_through_date")
        ),
        "retraining_ran": retrain_ran,
        "recalibration_ran": recal_ran,
        "no_leakage_passed": no_leak_passed,
        "validation_gates_passed": gates_passed,
        "challenger_promoted": promoted,
    }

    md = [
        f"# Daily model training / recalibration report — {args.as_of_date}",
        "",
        f"- generated_at_utc: {report['generated_at_utc']}",
        "",
        "## Headline",
        "",
        f"- active_champion_model_id: `{pointer.get('champion_model_id')}`",
        f"- feature_set_id: `{pointer.get('feature_set_id')}`",
        f"- is_phase13s_direct_lineup_driver: **{is_phase13s}**",
        f"- trained_through_date: "
        f"`{report['headline_summary']['trained_through_date']}`",
        f"- calibrated_through_date: "
        f"`{report['headline_summary']['calibrated_through_date']}`",
        f"- retraining_ran: **{retrain_ran}**",
        f"- recalibration_ran: **{recal_ran}**",
        f"- no_leakage_passed: **{no_leak_passed}**",
        f"- validation_gates_passed: **{gates_passed}**",
        f"- challenger_promoted: **{promoted}**",
        "",
        "## Active champion (full pointer block)",
        "",
    ]
    for k, v in report["champion"].items():
        md.append(f"- {k}: `{v}`")
    md.append("")
    md.append("## Promotion status")
    md.append("")
    md.append(f"- promoted: **{report['promotion_status']['promoted']}**")
    if promotion_decision:
        md.append(f"- decision_id: `{promotion_decision.get('decision_id')}`")
        md.append(f"- decided_at_utc: `{promotion_decision.get('decided_at_utc')}`")
    md.append("")
    md.append("## Validation gates")
    md.append("")
    md.append(
        f"- any_positive_improvement: "
        f"**{report['validation_gates']['any_positive_improvement']}**"
    )
    md.append(f"- issues: {report['validation_gates']['issues']}")
    md.append(
        f"- minutes_min_rel_improvement: "
        f"`{report['validation_gates']['minutes_min_rel_improvement']}`"
    )
    md.append(
        f"- safe_noninferiority_threshold: "
        f"`{report['validation_gates']['safe_noninferiority_threshold']}`"
    )
    md.append("")
    md.append("## Per-target metrics (training-time validation)")
    md.append("")
    md.append("| target | n_test | rel_improvement |")
    md.append("| --- | ---: | ---: |")
    for tgt, m in metrics_per_target.items():
        if isinstance(m, dict):
            ri = m.get("rel_improvement")
            md.append(
                f"| {tgt} | {m.get('n_test')} | "
                f"{ri:+.4%} |" if isinstance(ri, (int, float))
                else f"| {tgt} | {m.get('n_test')} | {ri} |"
            )
    md.append("")
    md.append("## Sensitivity")
    md.append("")
    sens = report["sensitivity"].get("case_results") or {}
    for case, vals in sens.items():
        md.append(f"- {case}: {vals}")
    md.append("")
    md.append("## After-game scoring")
    md.append("")
    md.append(f"```json\n{json.dumps(report['after_game_scoring'], indent=2)}\n```")
    md.append("")
    md.append("## Rolling Derek benchmark")
    md.append("")
    md.append(f"```json\n{json.dumps(report['rolling_benchmark'], indent=2)}\n```")
    md.append("")
    md.append("## Files to inspect")
    md.append("")
    md.append(
        "- champion_pointer: `artifacts/models/registry/champion_pointer.json`"
    )
    if challenger_dir_rel:
        md.append(
            f"- contextual challenger dir: `{challenger_dir_rel}`"
        )
        md.append(
            f"- train_manifest: "
            f"`{challenger_dir_rel}/train_manifest.json`"
        )
        md.append(
            f"- no_leakage_manifest: "
            f"`{challenger_dir_rel}/no_leakage_manifest.json`"
        )
        md.append(
            f"- promotion_decision: "
            f"`{challenger_dir_rel}/promotion_decision.json`"
        )
    if validation_report_path:
        md.append(f"- validation_report: `{validation_report_path}`")
    if pointer.get("contextual_no_leakage_manifest_path"):
        md.append(
            f"- contextual_no_leakage_manifest: "
            f"`{pointer.get('contextual_no_leakage_manifest_path')}`"
        )
    md.append(
        "- Phase 13S sensitivity: "
        "`artifacts/phase13s/direct_lineup_pmf_sensitivity.json`"
    )
    md.append(
        "- Phase 13S no-leakage report: "
        "`artifacts/phase13s/no_leakage_report.json`"
    )
    md.append(
        "- Derek snapshot E2E: "
        "`artifacts/automation_health/derek_production_live_e2e_<date>.json`"
    )
    md.append("")
    md.append("## Pending items")
    md.append("")
    md.append(report["calibration_metrics_pending"]["blocker"])
    (out_dir / "daily_model_training_report.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")

    print("DAILY_MODEL_TRAINING_REPORT_PASS")
    # Phase 13W — explicit pass line for the daily model report.
    print("PHASE13W_DAILY_MODEL_REPORT_PASS")
    print(f"  as_of_date={args.as_of_date}")
    print(f"  champion_model_id={pointer.get('champion_model_id')}")
    print(f"  feature_set_id={pointer.get('feature_set_id')}")
    print(f"  promoted={report['promotion_status']['promoted']}")
    print(f"  validation_gates_issues={report['validation_gates']['issues']}")
    print(f"  output={out_dir.relative_to(REPO_ROOT)}/daily_model_training_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
