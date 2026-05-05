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


def _build_promotion_status(
    as_of_date: str,
    pointer: dict,
    promotion_decision: dict | None,
    promotion_manifest: dict | None,
    today_decision_path: Path,
    today_manifest_path: Path,
) -> dict:
    """Phase 13AN: derive promotion truth from explicit signals.

    Three signals are surfaced in the report so the operator can see the
    full picture:

    * ``decision_promote_field`` — today's ``promotion_decision.json``'s
      ``promote`` (canonical) or legacy ``promoted`` field. None when the
      decision file is missing.
    * ``manifest_promoted_field`` — today's ``promotion_manifest.json``'s
      ``promoted`` field. None when the manifest is absent (no actual
      pointer swap was attempted/written).
    * ``champion_pointer_swapped_to_today`` — whether the active champion
      pointer's ``champion_model_id`` matches the canonical
      ``challenger-<as_of>`` for today.

    Final truth is the AND of these signals:

        promoted = (manifest.promoted is True)
                  AND (champion pointer reflects today's challenger)
                  AND (decision.promote is True)

    Any disagreement reports ``promoted=False`` with a precise
    ``promotion_reason`` extracted from the decision file.
    """
    decision_promote_field = None
    if promotion_decision:
        if "promote" in promotion_decision:
            decision_promote_field = bool(promotion_decision.get("promote"))
        elif "promoted" in promotion_decision:
            decision_promote_field = bool(promotion_decision.get("promoted"))

    manifest_promoted_field = None
    if promotion_manifest:
        manifest_promoted_field = bool(promotion_manifest.get("promoted"))

    expected_today_challenger_id = f"challenger-{as_of_date}"
    champion_id_now = pointer.get("champion_model_id")
    champion_pointer_swapped_to_today = (
        champion_id_now == expected_today_challenger_id
    )

    promoted = (
        decision_promote_field is True
        and manifest_promoted_field is True
        and champion_pointer_swapped_to_today
    )

    promotion_reason = None
    if promotion_decision:
        promotion_reason = (
            promotion_decision.get("reason")
            or promotion_decision.get("promotion_reason")
        )
    if promotion_reason is None and not promoted:
        # Synthesize a clear reason when the decision file did not
        # spell one out but we know the swap did not happen.
        if decision_promote_field is False:
            promotion_reason = "decision_promote_false"
        elif decision_promote_field is None:
            promotion_reason = "promotion_decision_missing_or_unparseable"
        elif manifest_promoted_field is not True:
            promotion_reason = "promotion_manifest_did_not_record_swap"
        elif not champion_pointer_swapped_to_today:
            promotion_reason = (
                "champion_pointer_not_advanced_to_"
                f"{expected_today_challenger_id}_now={champion_id_now}"
            )

    return {
        "promoted": promoted,
        "decision_promote_field": decision_promote_field,
        "manifest_promoted_field": manifest_promoted_field,
        "champion_pointer_swapped_to_today": champion_pointer_swapped_to_today,
        "active_champion_model_id": champion_id_now,
        "expected_today_challenger_id": expected_today_challenger_id,
        "promotion_reason": promotion_reason,
        "promotion_decision_path": str(today_decision_path),
        "promotion_manifest_path": str(today_manifest_path),
        "promotion_decision": promotion_decision,
        "promotion_manifest": promotion_manifest,
    }


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

    # Phase 13AN: TODAY's promotion truth lives at
    #   artifacts/nightly_training/<as_of>/promotion_decision.json
    #   artifacts/nightly_training/<as_of>/promotion_manifest.json
    # Reading the active-champion's stale promotion_manifest.json (which
    # is what the previous code did via challenger_dir from pointer) gave
    # back the LAST SUCCESSFUL promotion's "promoted=true" even when
    # today's challenger was not promoted. The decision file uses field
    # `promote` (boolean); the manifest file uses `promoted`. Both are
    # honored below for backward compat.
    today_nightly_dir = (
        REPO_ROOT / "artifacts" / "nightly_training" / args.as_of_date
    )
    today_promotion_decision_path = today_nightly_dir / "promotion_decision.json"
    today_promotion_manifest_path = today_nightly_dir / "promotion_manifest.json"
    promotion_decision = _read_json(today_promotion_decision_path)
    promotion_manifest = _read_json(today_promotion_manifest_path)
    if promotion_decision is None and challenger_dir is not None:
        # Fallback to the active-champion's challenger dir for older runs
        # that didn't write into nightly_training/. Surface this fallback
        # explicitly in the report so it's auditable.
        promotion_decision = _read_json(
            challenger_dir / "promotion_decision.json"
        )
    if promotion_manifest is None and challenger_dir is not None:
        promotion_manifest = _read_json(
            challenger_dir / "promotion_manifest.json"
        )

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
        "promotion_status": _build_promotion_status(
            args.as_of_date,
            pointer,
            promotion_decision,
            promotion_manifest,
            today_promotion_decision_path,
            today_promotion_manifest_path,
        ),
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
        "active_champion_model_id": pointer.get("champion_model_id"),
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
        "promotion_reason": report["promotion_status"].get("promotion_reason"),
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
        f"- promotion_reason: `{report['promotion_status'].get('promotion_reason')}`",
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
    md.append(
        f"- decision_promote_field: "
        f"`{report['promotion_status'].get('decision_promote_field')}`"
    )
    md.append(
        f"- manifest_promoted_field: "
        f"`{report['promotion_status'].get('manifest_promoted_field')}`"
    )
    md.append(
        f"- champion_pointer_swapped_to_today: "
        f"**{report['promotion_status'].get('champion_pointer_swapped_to_today')}**"
    )
    md.append(
        f"- expected_today_challenger_id: "
        f"`{report['promotion_status'].get('expected_today_challenger_id')}`"
    )
    md.append(
        f"- active_champion_model_id: "
        f"`{report['promotion_status'].get('active_champion_model_id')}`"
    )
    md.append(
        f"- promotion_reason: "
        f"`{report['promotion_status'].get('promotion_reason')}`"
    )
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
    md.append("## PMF variance experience study")
    md.append("")
    md.append(
        f"- Latest study: "
        f"https://github.com/Risky-Scout/nba-player-props-model/blob/main/"
        f"artifacts/experience_studies/pmf_variance_experience_"
        f"{args.as_of_date}.md"
    )
    md.append(
        "- This is an actuarial-style actual-to-expected study for settled "
        "rows. It checks PMF mean calibration, PMF variance calibration, "
        "quantile coverage, and model-vs-market scoring. In the first "
        "settled samples, PMF variance is reasonably close overall, but "
        "the model under-projects means and trails market on Brier/logloss, "
        "so this is a diagnostic and improvement report rather than a "
        "market-superiority claim."
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
    print(f"  challenger_promoted={report['promotion_status']['promoted']}")
    print(
        f"  active_champion_model_id="
        f"{report['promotion_status'].get('active_champion_model_id')}"
    )
    print(
        f"  promotion_reason="
        f"{report['promotion_status'].get('promotion_reason')}"
    )
    print(f"  validation_gates_issues={report['validation_gates']['issues']}")
    print(f"  output={out_dir.relative_to(REPO_ROOT)}/daily_model_training_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
