"""Phase 13A — promote a validated challenger to champion (or no-op).

Reads the challenger's promotion_decision.json. If ``promote=true`` and all
safety gates clear, atomically swaps the champion pointer and backs up the
prior champion. Otherwise, writes a no-promotion marker and exits 0.

Usage:
    python3 scripts/promote_challenger_if_validated.py --as-of-date YYYY-MM-DD
    python3 scripts/promote_challenger_if_validated.py --as-of-date YYYY-MM-DD --force-no-promote

Hard rules:
- Promotion is forbidden at or after 14:30 UTC (protects 15:00 UTC WoO run).
- Promotion is forbidden if validation_report.json or promotion_decision.json
  is missing, malformed, or carries any failed safety gate.
- Promotion is forbidden if the lockfile cannot be acquired safely.
- Promotion is forbidden if Phase 10D / 10D.2 overlay tokens appear anywhere
  in the manifests.
- The champion_pointer.json swap is atomic (write tmp + os.replace) and
  preserves a previous-pointer backup.
- If anything fails between backup and swap, the prior pointer remains
  authoritative and the run exits non-zero.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_DIR,
    CHAMPION_MODELS_DIR,
    CHAMPION_POINTER_PATH,
    MODEL_REGISTRY_PATH,
    PROMOTION_LOG_PATH,
    REGISTRY_DIR,
    challenger_dir,
    git_commit,
    is_past_promotion_cutoff,
    load_champion_pointer,
    parse_date,
    promotion_lock,
    read_json,
    scan_for_forbidden_overlay_tokens,
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)


def _no_promotion(ch_dir: Path, *, reason: str, decision: dict | None = None) -> dict:
    marker = {
        "schema_version": "1.0",
        "promoted": False,
        "reason": reason,
        "decided_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "decision_seen": decision or {},
    }
    write_json_atomic(ch_dir / "promotion_manifest.json", marker)
    return marker


def _backup_dirname() -> str:
    return "v_" + utcnow_iso().replace(":", "").replace("-", "").replace("+", "p")


def _backup_existing_champion(model_dir: Path) -> Path:
    backup = CHAMPION_DIR / _backup_dirname()
    backup.mkdir(parents=True, exist_ok=False)
    # Copy lightweight metadata + the model_dir top level (NOT recursively
    # mirroring archive subdirs). For Phase 13A bootstrap dry-run, the actual
    # promotion path is exercised only when a real challenger ships its own
    # artifacts. We back up the pointer + meta jsons unconditionally so we can
    # always roll back the registry state.
    for name in (
        "training_meta.json",
        "calibration_meta.json",
        "pmf_cal_meta.json",
        "calibration_manifest.json",
    ):
        src = model_dir / name
        if src.exists():
            shutil.copy2(src, backup / name)
    # Also copy the previous champion_pointer.json next to it.
    if CHAMPION_POINTER_PATH.exists():
        shutil.copy2(CHAMPION_POINTER_PATH, backup / "champion_pointer.previous.json")
    return backup


def _append_promotion_log(*, from_version: str, to_version: str, decision: str, gates_passed: list[str], gates_failed: list[str], reason: str, operator: str) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not PROMOTION_LOG_PATH.exists()
    with PROMOTION_LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(
                [
                    "timestamp_utc",
                    "from_version",
                    "to_version",
                    "decision",
                    "gates_passed",
                    "gates_failed",
                    "reason",
                    "operator",
                    "code_commit",
                ]
            )
        w.writerow(
            [
                utcnow_iso(),
                from_version,
                to_version,
                decision,
                ";".join(gates_passed),
                ";".join(gates_failed),
                reason,
                operator,
                git_commit(),
            ]
        )


def _update_model_registry(*, new_entry: dict) -> None:
    if MODEL_REGISTRY_PATH.exists():
        registry = read_json(MODEL_REGISTRY_PATH)
    else:
        registry = {"schema_version": "1.0", "models": []}
    for m in registry.get("models", []):
        m["is_champion"] = False
    registry.setdefault("models", []).append(new_entry)
    write_json_atomic(MODEL_REGISTRY_PATH, registry)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Promote challenger if validated.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    p.add_argument(
        "--force-no-promote",
        action="store_true",
        help="Always decline to promote, regardless of decision file.",
    )
    args = p.parse_args(argv)

    parse_date(args.as_of_date)  # validate format
    ch_dir = challenger_dir(args.as_of_date)
    if not ch_dir.exists():
        print(json.dumps({"error": "challenger dir missing", "dir": str(ch_dir)}))
        return 2

    decision_path = ch_dir / "promotion_decision.json"
    validation_path = ch_dir / "validation_report.json"
    if not decision_path.exists() or not validation_path.exists():
        marker = _no_promotion(
            ch_dir,
            reason="missing_validation_or_decision",
        )
        print(json.dumps(marker))
        return 0

    decision = read_json(decision_path)
    validation = read_json(validation_path)

    # Hard veto checks before we even consider the decision file.
    if args.force_no_promote:
        marker = _no_promotion(ch_dir, reason="force_no_promote", decision=decision)
        print(json.dumps(marker))
        return 0
    if not decision.get("promote", False):
        marker = _no_promotion(
            ch_dir,
            reason=f"decision.promote=false ({decision.get('reason')})",
            decision=decision,
        )
        print(json.dumps(marker))
        return 0
    if validation.get("pmf_validity", {}).get("issues"):
        marker = _no_promotion(ch_dir, reason="pmf_validity_failed", decision=decision)
        print(json.dumps(marker))
        return 0
    if not validation.get("derek_compatibility", {}).get("passed"):
        marker = _no_promotion(ch_dir, reason="derek_compatibility_failed", decision=decision)
        print(json.dumps(marker))
        return 0
    if not validation.get("woo_compatibility", {}).get("passed"):
        marker = _no_promotion(ch_dir, reason="woo_compatibility_failed", decision=decision)
        print(json.dumps(marker))
        return 0
    overlay_hits = scan_for_forbidden_overlay_tokens({"validation": validation, "decision": decision})
    if overlay_hits:
        marker = _no_promotion(
            ch_dir,
            reason=f"phase10d_overlay_tokens_present:{overlay_hits[:1]}",
            decision=decision,
        )
        print(json.dumps(marker))
        return 0
    if is_past_promotion_cutoff():
        marker = _no_promotion(
            ch_dir,
            reason="promotion_clock_unsafe_at_or_after_14:30_utc",
            decision=decision,
        )
        print(json.dumps(marker))
        return 0

    # All vetoes cleared. Acquire the lock and swap the pointer.
    pointer = load_champion_pointer()
    from_version = pointer.get("model_version", "unknown")
    challenger_version = (
        validation.get("challenger", {}).get("model_version")
        or f"challenger-{args.as_of_date}"
    )

    try:
        with promotion_lock(timeout_s=0.0):
            backup = _backup_existing_champion(CHAMPION_MODELS_DIR)

            new_pointer = {
                "schema_version": "1.0",
                "model_version": challenger_version,
                "calibrator_version": validation.get("challenger", {}).get(
                    "calibrator_version", "phase8-role-bucket"
                ),
                "code_commit": git_commit(),
                "created_at_utc": utcnow_iso(),
                "promoted_at_utc": utcnow_iso(),
                "model_dir": pointer.get("model_dir", "artifacts/models"),
                "supported_stats": pointer.get("supported_stats"),
                "previous_pointer_backup": str(
                    (backup / "champion_pointer.previous.json").relative_to(REPO_ROOT)
                ),
                "previous_model_version": from_version,
                "promoted_from_challenger_dir": str(ch_dir.relative_to(REPO_ROOT)),
                "phase10d_overlays_in_use": False,
                "notes": "Promoted via scripts/promote_challenger_if_validated.py.",
            }
            # Atomic write_json_atomic also handles the rename.
            write_json_atomic(CHAMPION_POINTER_PATH, new_pointer)

            _update_model_registry(
                new_entry={
                    "id": f"champion-{args.as_of_date}",
                    "model_version": challenger_version,
                    "calibrator_version": new_pointer["calibrator_version"],
                    "code_commit": git_commit(),
                    "registered_at_utc": utcnow_iso(),
                    "is_champion": True,
                    "supported_stats": pointer.get("supported_stats"),
                    "model_dir": new_pointer["model_dir"],
                    "promoted_from_challenger_dir": str(ch_dir.relative_to(REPO_ROOT)),
                    "previous_model_version": from_version,
                }
            )

            _append_promotion_log(
                from_version=from_version,
                to_version=challenger_version,
                decision="promoted",
                gates_passed=decision.get("gates_passed", []),
                gates_failed=decision.get("gates_failed", []),
                reason=decision.get("reason", ""),
                operator="phase13a-orchestrator",
            )

            promotion_manifest = {
                "schema_version": "1.0",
                "promoted": True,
                "as_of_date": args.as_of_date,
                "from_version": from_version,
                "to_version": challenger_version,
                "promoted_at_utc": utcnow_iso(),
                "code_commit": git_commit(),
                "backup_dir": str(backup.relative_to(REPO_ROOT)),
                "champion_pointer_path": str(CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)),
                "champion_pointer_sha256_after_swap": sha256_file(CHAMPION_POINTER_PATH),
            }
            write_json_atomic(ch_dir / "promotion_manifest.json", promotion_manifest)

            print(json.dumps({"promoted": True, **promotion_manifest}, indent=2))
            return 0

    except Exception as exc:
        # Pointer write is atomic and only happens after backup; if anything
        # raised, the original champion pointer is still authoritative.
        marker = _no_promotion(
            ch_dir,
            reason=f"promotion_aborted:{exc}",
            decision=decision,
        )
        print(json.dumps(marker))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
