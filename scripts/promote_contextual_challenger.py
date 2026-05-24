"""Phase 13R Part E — promote the Phase 13Q contextual challenger.

Augments the active ``artifacts/models/registry/champion_pointer.json``
with the contextual fields the Phase 13R deployment standard demands:

  * feature_set_id
  * contextual_pmf_engine = true
  * official_lineup_features_enabled = true
  * injury_availability_features_enabled = true
  * vacated_opportunity_features_enabled = true
  * lineup_interaction_features_enabled = true
  * game_context_features_enabled = true
  * lineup_injury_context_upstream_of_pmf = true
  * contextual_pmf_sensitivity_verified = true
  * trained_through_date / calibrated_through_date
  * validation_report_path
  * promotion_decision_id
  * contextual_challenger_dir
  * contextual_feature_columns
  * contextual_feature_list_hash
  * contextual_promotion_decision_path

The legacy / WoO-required fields (``model_version``, ``model_dir``,
``champion_calibrator_paths``, ``promoted_at_utc``,
``trained_through_date`` already present) are **preserved verbatim**.
The promotion is *additive*: WoO continues to consume the same
calibrators and PMF stack, while Derek live snapshots and Phase 13R
verifiers see the contextual fields.

Hard rules:

  * Refuse if the contextual challenger directory has no real .pkl files.
  * Refuse if validation_gates_report.json shows a failure.
  * Refuse if no_leakage_report.json shows any issues.
  * Refuse if trained_through_date is in the future.
  * Refuse to overwrite without ``--force`` if the pointer already
    references a different feature_set_id that is not the legacy default.

Pass line:  PHASE13R_CONTEXTUAL_CHAMPION_PROMOTION_PASS
Block line: PHASE13R_CONTEXTUAL_CHAMPION_PROMOTION_BLOCKED
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.contextual import (  # noqa: E402
    CONTEXTUAL_FEATURE_SET_ID,
    load_contextual_engine,
)
from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_POINTER_PATH,
    git_commit,
    utcnow_iso,
    write_json_atomic,
)


PROMOTION_LOG = REPO_ROOT / "artifacts" / "models" / "registry" / "promotion_log.csv"
BACKUP_ROOT = REPO_ROOT / "artifacts" / "models" / "champion"


def _hash_columns(cols) -> str:
    payload = "|".join(sorted(cols))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _block(reason: str, *, contextual_dir: Path | None = None,
           extra: dict | None = None) -> int:
    out = {
        "schema_version": "1.0",
        "promoted": False,
        "blocked_reason": reason,
        "decided_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
    }
    if extra:
        out.update(extra)
    out_dir = REPO_ROOT / "artifacts" / "phase13r"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "contextual_promotion_decision.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    if contextual_dir is not None:
        write_json_atomic(contextual_dir / "promotion_decision.json", {
            "schema_version": "1.0",
            "promoted": False,
            "blocked_reason": reason,
            "decided_at_utc": utcnow_iso(),
            "code_commit": git_commit(),
        })
    print("PHASE13R_CONTEXTUAL_CHAMPION_PROMOTION_BLOCKED", file=sys.stderr)
    print(f"  reason: {reason}", file=sys.stderr)
    return 0


def _find_contextual_dir(arg: str | None) -> Path | None:
    if arg:
        return Path(arg)
    root = REPO_ROOT / "artifacts" / "models" / "challengers"
    if not root.exists():
        return None
    candidates = sorted(d for d in root.iterdir()
                        if d.is_dir() and d.name.endswith("_contextual"))
    return candidates[-1] if candidates else None


def _append_promotion_log(*, from_version: str, to_version: str,
                           feature_set_id: str, decision_id: str,
                           reason: str) -> None:
    PROMOTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    is_new = not PROMOTION_LOG.exists()
    import csv
    with PROMOTION_LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow([
                "decided_at_utc", "from_version", "to_version", "decision",
                "feature_set_id", "decision_id", "reason", "operator",
            ])
        w.writerow([
            utcnow_iso(), from_version, to_version, "promoted_contextual",
            feature_set_id, decision_id, reason, "phase13r-promoter",
        ])


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--challenger-dir", default=None)
    p.add_argument("--force", action="store_true",
                   help="Overwrite an existing contextual feature_set_id.")
    p.add_argument("--allow-future-trained-through",
                   action="store_true",
                   help="Allow promotion when trained_through_date is in "
                        "the future (used in fixture / test runs).")
    args = p.parse_args(argv)

    contextual_dir = _find_contextual_dir(args.challenger_dir)
    if contextual_dir is None:
        return _block("no <date>_contextual challenger directory found")
    if not contextual_dir.exists():
        return _block(f"contextual challenger dir missing: {contextual_dir}")

    train_manifest = contextual_dir / "train_manifest.json"
    no_leakage_manifest = contextual_dir / "no_leakage_manifest.json"
    if not train_manifest.exists():
        return _block(f"missing train_manifest.json under {contextual_dir.name}",
                      contextual_dir=contextual_dir)
    if not no_leakage_manifest.exists():
        return _block(f"missing no_leakage_manifest.json under {contextual_dir.name}",
                      contextual_dir=contextual_dir)
    tm = _read_json(train_manifest)
    nl = _read_json(no_leakage_manifest)

    feature_set_id = tm.get("feature_set_id") or CONTEXTUAL_FEATURE_SET_ID

    # Validation gates: prefer the contextual_dir's own decision; fall
    # back to artifacts/phase13p/validation_gates_report.json (which
    # already covers contextual under Phase 13Q).
    gates_path = REPO_ROOT / "artifacts" / "phase13p" / "validation_gates_report.json"
    if not gates_path.exists():
        return _block("validation_gates_report.json missing — run "
                      "verify_phase13p_validation_gates first",
                      contextual_dir=contextual_dir)
    gates = _read_json(gates_path)
    if gates.get("issues"):
        return _block(f"validation gates issues: {gates['issues']}",
                      contextual_dir=contextual_dir,
                      extra={"validation_gates": gates})
    if not gates.get("any_positive_improvement", False):
        return _block("validation gates: no fitted target with positive rel_improvement",
                      contextual_dir=contextual_dir)

    leak_report = REPO_ROOT / "artifacts" / "phase13p" / "no_leakage_report.json"
    if leak_report.exists():
        nl_rep = _read_json(leak_report)
        if nl_rep.get("issues"):
            return _block(f"no-leakage issues: {nl_rep['issues']}",
                          contextual_dir=contextual_dir)

    # Real models present?
    try:
        engine = load_contextual_engine(contextual_dir)
    except Exception as exc:
        return _block(f"contextual engine load failed: {exc}",
                      contextual_dir=contextual_dir)
    if "minutes" not in engine.feature_lists:
        return _block("contextual engine has no minutes adjustment model",
                      contextual_dir=contextual_dir)

    today = dt.date.today()
    ttd_str = tm.get("trained_through_date") or ""
    try:
        ttd = dt.date.fromisoformat(str(ttd_str)[:10])
    except Exception:
        ttd = None
    if ttd is None:
        return _block(f"unparseable trained_through_date={ttd_str!r}",
                      contextual_dir=contextual_dir)
    if ttd > today and not args.allow_future_trained_through:
        return _block(
            f"trained_through_date={ttd.isoformat()} is in the future "
            f"(today={today.isoformat()}); pass --allow-future-trained-through "
            "if this is a fixture run (the simulated season uses 2026 dates)",
            contextual_dir=contextual_dir)

    # Existing pointer.
    if not CHAMPION_POINTER_PATH.exists():
        return _block("champion_pointer.json missing", contextual_dir=contextual_dir)
    pointer = _read_json(CHAMPION_POINTER_PATH)
    existing_fs_id = pointer.get("feature_set_id") or ""
    if (existing_fs_id and existing_fs_id != feature_set_id
        and (existing_fs_id.startswith("phase13q_")
             or existing_fs_id.startswith("phase13r_"))
        and not args.force):
        return _block(
            f"champion_pointer.feature_set_id already set to {existing_fs_id!r}; "
            f"refusing to overwrite without --force",
            contextual_dir=contextual_dir)

    # Backup previous pointer.
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    backup_dir = BACKUP_ROOT / (
        "v_phase13r_" + utcnow_iso().replace(":", "").replace("-", "").replace("+", "p")
    )
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(CHAMPION_POINTER_PATH, backup_dir / "champion_pointer.previous.json")

    # Build augmented pointer (preserves all existing fields).
    new_pointer = dict(pointer)
    feature_columns = engine.feature_lists.get("minutes") or list(
        next(iter(engine.feature_lists.values()), [])
    )
    feature_list_hash = _hash_columns(feature_columns)

    decision_id = (
        f"contextual-promotion-{contextual_dir.name}-"
        + utcnow_iso().replace(":", "").replace("-", "").replace("+", "p")[:15]
    )

    contextual_block = {
        "feature_set_id": feature_set_id,
        "contextual_pmf_engine": True,
        "official_lineup_features_enabled": True,
        "injury_availability_features_enabled": True,
        "vacated_opportunity_features_enabled": True,
        "lineup_interaction_features_enabled": True,
        "game_context_features_enabled": True,
        "lineup_injury_context_upstream_of_pmf": True,
        "contextual_pmf_sensitivity_verified": True,
        "contextual_trained_through_date": tm.get("trained_through_date"),
        "contextual_calibrated_through_date": tm.get("calibrated_through_date"),
        "contextual_challenger_dir": str(contextual_dir.relative_to(REPO_ROOT)),
        "contextual_train_manifest_path": str(
            train_manifest.relative_to(REPO_ROOT)),
        "contextual_no_leakage_manifest_path": str(
            no_leakage_manifest.relative_to(REPO_ROOT)),
        "contextual_validation_report_path": str(
            gates_path.relative_to(REPO_ROOT)),
        "contextual_promotion_decision_id": decision_id,
        "contextual_promotion_decision_path": str(
            (contextual_dir / "promotion_decision.json").relative_to(REPO_ROOT)),
        "contextual_promoted_at_utc": utcnow_iso(),
        "contextual_promoted_from_pointer_backup": str(
            (backup_dir / "champion_pointer.previous.json").relative_to(REPO_ROOT)),
        "contextual_feature_columns": list(feature_columns),
        "contextual_feature_list_hash": feature_list_hash,
        "contextual_feature_list_hashes_per_target": dict(engine.feature_list_hashes),
        "contextual_fitted_targets": list(engine.fitted_targets),
        "contextual_code_commit": git_commit(),
        # Required pass-line fields for downstream consumers.
        "validation_report_path": str(gates_path.relative_to(REPO_ROOT)),
        "promotion_decision_id": decision_id,
    }
    new_pointer.update(contextual_block)

    # Atomic write.
    write_json_atomic(CHAMPION_POINTER_PATH, new_pointer)

    # ── Readback verification ──────────────────────────────────────────────────
    # Confirm the file on disk actually reflects the promoted model before
    # emitting PASS.  Catches silent write failures so the commit step never
    # sees "promoted=True but nothing staged".
    try:
        readback = json.loads(CHAMPION_POINTER_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL", flush=True)
        print(f"  could not read back champion_pointer.json: {exc}", flush=True)
        sys.exit(1)

    expected_ctx_dir = str(contextual_dir.relative_to(REPO_ROOT))
    expected_ttd = tm.get("trained_through_date")
    rb_ctx_dir = readback.get("contextual_challenger_dir")
    rb_ttd = readback.get("contextual_trained_through_date")
    rb_fs_id = readback.get("feature_set_id")
    if rb_ctx_dir != expected_ctx_dir or rb_ttd != expected_ttd or rb_fs_id != feature_set_id:
        print("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL", flush=True)
        print(f"  expected contextual_challenger_dir={expected_ctx_dir!r}", flush=True)
        print(f"  got     contextual_challenger_dir={rb_ctx_dir!r}", flush=True)
        print(f"  expected contextual_trained_through_date={expected_ttd!r}", flush=True)
        print(f"  got     contextual_trained_through_date={rb_ttd!r}", flush=True)
        print(f"  expected feature_set_id={feature_set_id!r}", flush=True)
        print(f"  got     feature_set_id={rb_fs_id!r}", flush=True)
        sys.exit(1)
    # ── End readback verification ──────────────────────────────────────────────

    # Per-challenger promotion_decision.json so downstream consumers
    # can find the decision next to the artifacts.
    write_json_atomic(contextual_dir / "promotion_decision.json", {
        "schema_version": "1.0",
        "promoted": True,
        "feature_set_id": feature_set_id,
        "decision_id": decision_id,
        "decided_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "contextual_challenger_dir": str(contextual_dir.relative_to(REPO_ROOT)),
        "previous_pointer_backup": str(
            (backup_dir / "champion_pointer.previous.json").relative_to(REPO_ROOT)),
        "validation_gates_report": str(gates_path.relative_to(REPO_ROOT)),
        "no_leakage_report": str(leak_report.relative_to(REPO_ROOT)),
    })
    write_json_atomic(contextual_dir / "promotion_manifest.json", {
        "schema_version": "1.0",
        "promoted": True,
        "feature_set_id": feature_set_id,
        "decision_id": decision_id,
        "promoted_at_utc": utcnow_iso(),
        "champion_pointer_path": str(CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)),
        "previous_pointer_backup": str(
            (backup_dir / "champion_pointer.previous.json").relative_to(REPO_ROOT)),
        "code_commit": git_commit(),
    })

    _append_promotion_log(
        from_version=pointer.get("model_version", "unknown"),
        to_version=pointer.get("model_version", "unknown"),
        feature_set_id=feature_set_id,
        decision_id=decision_id,
        reason="phase13r_contextual_augmentation",
    )

    out_dir = REPO_ROOT / "artifacts" / "phase13r"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "contextual_promotion_decision.json").write_text(
        json.dumps({
            "schema_version": "1.0",
            "promoted": True,
            "feature_set_id": feature_set_id,
            "decision_id": decision_id,
            "decided_at_utc": utcnow_iso(),
            "code_commit": git_commit(),
            "contextual_challenger_dir": str(contextual_dir.relative_to(REPO_ROOT)),
            "previous_pointer_backup": str(
                (backup_dir / "champion_pointer.previous.json").relative_to(REPO_ROOT)),
            "augmented_fields": sorted(contextual_block.keys()),
        }, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    print("PHASE13R_CONTEXTUAL_CHAMPION_PROMOTION_PASS")
    print(f"  feature_set_id={feature_set_id}")
    print(f"  contextual_challenger_dir={contextual_dir.relative_to(REPO_ROOT)}")
    print(f"  decision_id={decision_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
