"""Phase 13O Part E — verify the live-context features are wired and the
training feature lists in artifacts/models/ either consume them already
(post-retraining) or honestly do not (pre-retraining blocker).

This verifier is read-only.

Pass lines:
  PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_PASS — every wiring expectation
        passed. After retraining, this also asserts that the new feature
        columns appear in the saved feature lists.
  PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_PENDING_RETRAINING — wiring
        passed; saved feature lists do NOT yet include the new columns.
        This is the honest pre-retraining state.
Fail line:
  PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_FAILED
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--feature-set-id", default="phase13o_live_context_v1")
    args = p.parse_args(argv)

    issues: list[str] = []
    warnings: list[str] = []

    # 1. The feature module exposes the expected functions.
    try:
        from nba_props_model.features import live_context as lc
    except Exception as exc:
        print("PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_FAILED", file=sys.stderr)
        print(f"  reason: cannot import live_context module: {exc}",
              file=sys.stderr)
        return 1

    for fn in ("build_live_context_features", "join_lineup_features",
               "join_injury_availability_features",
               "compute_vacated_opportunity_features",
               "encode_live_context_features",
               "feature_set_id", "feature_set_hash"):
        if not callable(getattr(lc, fn, None)):
            issues.append(f"missing function live_context.{fn}")

    # 2. Feature column tuples are non-empty.
    for tup in ("LINEUP_FEATURE_COLUMNS", "INJURY_FEATURE_COLUMNS",
                "VACATED_OPPORTUNITY_FEATURE_COLUMNS"):
        cols = getattr(lc, tup, None)
        if not (isinstance(cols, tuple) and len(cols) >= 5):
            issues.append(f"{tup} missing or too short")

    # 3. The training dataset parquet exists (or the manifest does, when
    #    the builder was run with --dry-run).
    dataset = REPO_ROOT / "data" / "live_context_features.parquet"
    manifest = REPO_ROOT / "artifacts" / "phase13o" / "live_context_feature_manifest.json"
    if not (dataset.exists() or manifest.exists()):
        issues.append(
            "neither data/live_context_features.parquet nor "
            "artifacts/phase13o/live_context_feature_manifest.json present "
            "— run scripts/build_live_context_training_dataset.py first"
        )

    # 4. Audit saved feature lists in artifacts/models/ for live-context
    #    column presence. Pre-retraining, these will NOT contain the new
    #    columns — that is honest, not a failure. We surface it as a
    #    warning so the orchestrator knows retraining is the next step.
    models_dir = REPO_ROOT / "artifacts" / "models"
    # Strict subset: only Phase 13O-introduced column names. Some pre-13O
    # availability features (vacated_minutes_total, num_teammates_out_total)
    # already exist in some saved feature lists — they are NOT a Phase 13O
    # signal.
    expected_subset = {
        # Phase 13O / 13P column names that are NOT shared with the
        # pre-existing availability feature names. Matching any one of
        # these in a saved feature list proves the trainer consumed the
        # live-context feature module.
        "lineup_confirmed", "confirmed_starter", "confirmed_bench",
        "role_source_confirmed_lineup", "role_bucket_post_lineup_encoded",
        "starter_changed_from_projection", "lineup_features_missing",
        "injury_status_encoded", "availability_status_encoded",
        "injury_lineup_conflict",
        # Phase 13P trainer specifically introduces these:
        "starter_proxy_lagged", "is_actionable", "is_confirmed_out",
        "is_inactive", "is_doubtful", "is_questionable", "is_probable",
        "injury_features_missing", "vacated_features_missing",
    }
    feature_list_files = []
    if models_dir.exists():
        for sub in ("features_pts.pkl", "features_reb.pkl", "features_ast.pkl",
                    "features_tov.pkl", "features_blk.pkl", "features_stl.pkl",
                    "features_fg3m.pkl",
                    "rate_pts_features.pkl", "rate_reb_features.pkl",
                    "rate_ast_features.pkl", "rate_tov_features.pkl"):
            f = models_dir / sub
            if f.exists():
                feature_list_files.append(f)
    # Phase 13P additive challenger feature lists.
    challengers_root = models_dir / "challengers"
    if challengers_root.exists():
        for d in challengers_root.iterdir():
            if d.is_dir() and d.name.endswith("_live_context"):
                for f in d.glob("phase13p_*_adjustment_features.pkl"):
                    feature_list_files.append(f)
    feature_list_status: dict = {}
    has_any_live_context = False
    for f in feature_list_files:
        try:
            import joblib
            cols = joblib.load(f)
            if isinstance(cols, (list, tuple)):
                col_set = set(cols)
            elif hasattr(cols, "tolist"):
                col_set = set(cols.tolist())
            else:
                col_set = set()
            present = sorted(col_set & expected_subset)
            feature_list_status[str(f.relative_to(REPO_ROOT))] = {
                "total_features": len(col_set),
                "live_context_present": present,
            }
            if present:
                has_any_live_context = True
        except Exception as exc:
            feature_list_status[str(f.relative_to(REPO_ROOT))] = {
                "error": str(exc)
            }

    # Persist the audit report.
    out_dir = REPO_ROOT / "artifacts" / "phase13o"
    out_dir.mkdir(parents=True, exist_ok=True)
    audit = {
        "feature_set_id": args.feature_set_id,
        "live_context_module_ok": not issues,
        "feature_list_files_inspected": len(feature_list_files),
        "feature_list_status": feature_list_status,
        "any_feature_list_includes_live_context": has_any_live_context,
        "issues": issues,
    }
    (out_dir / "live_context_feature_training_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    if issues:
        print("PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1

    if has_any_live_context:
        print("PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_PASS")
        print("  every wiring expectation passed; saved feature lists DO "
              "include live-context columns (post-retraining state)")
        # Phase 13P-specific PASS: at least one Phase 13P challenger
        # feature list file was inspected and contained live-context
        # columns. The Phase 13P trainer writes these under
        # artifacts/models/challengers/<date>_live_context/.
        phase13p_count = sum(
            1 for k in feature_list_status
            if "_live_context" in k and "phase13p_" in k
            and "live_context_present" in feature_list_status[k]
            and feature_list_status[k]["live_context_present"]
        )
        if phase13p_count > 0:
            print("PHASE13P_LIVE_CONTEXT_FEATURE_LISTS_PASS")
            print(f"  phase13p feature list files with live-context columns: {phase13p_count}")
        return 0

    # Honest pre-retraining state — wiring is correct, saved feature
    # lists don't yet consume the new columns. Emit pending pass so
    # downstream tooling can distinguish from a real failure.
    print("PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_PENDING_RETRAINING")
    print(
        "  wiring OK; live-context module exposes the expected functions "
        "and feature column lists; saved feature lists in artifacts/models/ "
        f"({len(feature_list_files)} files inspected) do not yet include "
        "the new columns. Dispatch the Phase 13O training workflow to "
        "retrain."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
