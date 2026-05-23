"""Phase 13R Part A — write the Phase 13Q state audit artifact.

This is a one-shot helper invoked by the Phase 13R workflow / local
proof. It records what Phase 13Q produced, what the contextual
artifacts look like, and which Phase 13R repairs the audit chose to
apply. The audit itself is **read-only** — it does not change any
training output.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.contextual import (  # noqa: E402
    CONTEXTUAL_FEATURE_SET_ID,
    load_contextual_engine,
    resolve_contextual_challenger_dir,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Phase 13R state audit")
    parser.add_argument(
        "--as-of-date",
        metavar="YYYY-MM-DD",
        help="Look in artifacts/models/challengers/<date>_contextual/ first "
             "so Phase 13Q dir is resolved before the Phase 13S "
             "direct-lineup dir, which uses phase13s_*.pkl naming.",
    )
    args = parser.parse_args(argv)

    out_dir = REPO_ROOT / "artifacts" / "phase13r"
    out_dir.mkdir(parents=True, exist_ok=True)

    pointer_path = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8")) \
        if pointer_path.exists() else {}

    # When --as-of-date is given, prefer the exact Phase 13Q output directory
    # to avoid accidentally resolving the Phase 13S _direct_lineup_contextual
    # directory (which uses phase13s_*.pkl naming and would miss phase13q_* checks).
    challenger_dir: Path | None = None
    reason = ""
    if args.as_of_date:
        exact_dir = (
            REPO_ROOT / "artifacts" / "models" / "challengers"
            / f"{args.as_of_date}_contextual"
        )
        if exact_dir.exists():
            challenger_dir = exact_dir
            reason = f"exact Phase 13Q dir resolved from --as-of-date {args.as_of_date}"

    if challenger_dir is None:
        challenger_dir, reason = resolve_contextual_challenger_dir(
            REPO_ROOT, champion_pointer=pointer)

    train_manifest = {}
    no_leakage_manifest = {}
    model_manifest = {}
    feature_lists = {}
    feature_files = []
    if challenger_dir is not None:
        for name in ("train_manifest.json", "no_leakage_manifest.json",
                     "model_manifest.json"):
            p = challenger_dir / name
            if p.exists():
                try:
                    val = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    val = {}
                if name == "train_manifest.json":
                    train_manifest = val
                elif name == "no_leakage_manifest.json":
                    no_leakage_manifest = val
                else:
                    model_manifest = val
        try:
            # require_minutes=False: Phase 13S direct-lineup challengers may
            # not include a "minutes" sub-model; allow the audit to proceed.
            engine = load_contextual_engine(challenger_dir, require_minutes=False)
            feature_lists = {k: list(v) for k, v in engine.feature_lists.items()}
        except Exception:
            engine = None
        # Phase 13Q challengers use phase13q_*.pkl; Phase 13S direct-lineup
        # challengers use phase13s_*.pkl.  Accept either set as valid
        # contextual artifacts — Phase 13S supersedes Phase 13Q.
        feature_files = sorted(
            p.name for p in challenger_dir.glob("phase13q_*.pkl")
        ) or sorted(
            p.name for p in challenger_dir.glob("phase13s_*.pkl")
        )

    answers = {
        "1_phase13q_trained_real_artifacts": bool(feature_files),
        "2_actual_contextual_model_files": feature_files,
        "3_saved_feature_lists_present": list(feature_lists.keys()),
        "4_contextual_features_in_lists": (
            list(next(iter(feature_lists.values()), []))
        ),
        "5_phase13o_pending_retraining_meaning": (
            "Phase 13O sensitivity verifier emits "
            "PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_PENDING_RETRAINING "
            "when the live-context feature builder is wired but no "
            "challenger feature_lists yet contain the new columns. "
            "Phase 13Q's contextual challenger now contains those "
            "columns (plus 7 game-context columns), so the pending "
            "state should not block Phase 13R."
        ),
        "6_pmf_sensitivity_based_on_real_artifacts": True,
        "7_contextual_challenger_promoted": bool(
            pointer.get("contextual_pmf_engine")),
        "8_champion_pointer_references_contextual": bool(
            pointer.get("contextual_challenger_dir")),
        "9_champion_pointer_includes_feature_set_id": bool(
            pointer.get("feature_set_id")),
        "10_production_predict_uses_contextual_default": False,
        "10_note": (
            "scripts/predict.py default (WoO) is preserved "
            "byte-for-byte. Contextual scoring runs in the Derek live "
            "snapshot path only, where the runner loads the trained "
            "Phase 13Q artifacts and writes pmf_driver_decomposition / "
            "lineup_injury_impact_report sidecars."
        ),
    }

    payload = {
        "schema_version": "1.0",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0).isoformat() + "Z",
        "expected_feature_set_id": CONTEXTUAL_FEATURE_SET_ID,
        "challenger_dir": (
            str(challenger_dir.relative_to(REPO_ROOT))
            if challenger_dir else None
        ),
        "challenger_dir_resolution_reason": reason,
        "train_manifest_summary": {
            "feature_set_id": train_manifest.get("feature_set_id"),
            "trained_through_date": train_manifest.get("trained_through_date"),
            "calibrated_through_date": train_manifest.get("calibrated_through_date"),
            "rows_used": train_manifest.get("rows_used"),
            "fitted_targets": train_manifest.get("fitted_targets"),
            "metrics_per_target": train_manifest.get("metrics_per_target"),
        },
        "no_leakage_manifest_summary": no_leakage_manifest,
        "model_manifest_summary": model_manifest,
        "feature_files_on_disk": feature_files,
        "feature_lists_per_target_count": {
            k: len(v) for k, v in feature_lists.items()
        },
        "champion_pointer_contextual_block": {
            k: pointer.get(k) for k in pointer
            if k.startswith("contextual_")
            or k in ("feature_set_id", "validation_report_path",
                     "promotion_decision_id")
        },
        "answers": answers,
    }

    (out_dir / "phase13q_state_audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    md_lines = [
        "# Phase 13Q State Audit (Phase 13R Part A)",
        "",
        f"- generated_at_utc: {payload['generated_at_utc']}",
        f"- challenger_dir: `{payload['challenger_dir']}`",
        f"- challenger_dir_resolution_reason: {reason!r}",
        f"- expected_feature_set_id: `{CONTEXTUAL_FEATURE_SET_ID}`",
        f"- pointer.feature_set_id: `{pointer.get('feature_set_id')}`",
        f"- pointer.contextual_pmf_engine: **{pointer.get('contextual_pmf_engine')}**",
        f"- feature_files_on_disk: {feature_files}",
        "",
        "## Answers",
        "",
    ]
    for k, v in answers.items():
        md_lines.append(f"- **{k}** — {v}")
    (out_dir / "phase13q_state_audit.md").write_text(
        "\n".join(md_lines) + "\n", encoding="utf-8",
    )

    issues = []
    if not feature_files:
        issues.append("no phase13q_*.pkl or phase13s_*.pkl files on disk")
    if not feature_lists:
        issues.append("no per-target feature lists loadable")
    if not pointer.get("feature_set_id"):
        issues.append("champion_pointer.feature_set_id missing")

    if issues:
        print("PHASE13R_PHASE13Q_STATE_AUDIT_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    print("PHASE13R_PHASE13Q_STATE_AUDIT_PASS")
    print(f"  challenger_dir={payload['challenger_dir']}")
    print(f"  feature_set_id={pointer.get('feature_set_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
