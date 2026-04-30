"""One-shot bootstrap: register the current production model artifacts as champion.

Idempotent. Safe to re-run. Does NOT touch the model pickles themselves — only
writes metadata under artifacts/models/registry/ and a marker under
artifacts/models/champion/.

Usage:
    python3 scripts/_bootstrap_champion_registry.py
"""
from __future__ import annotations

import csv
import json
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
    SUPPORTED_STATS,
    git_commit,
    git_short_commit,
    read_json,
    utcnow_iso,
    write_json_atomic,
)


def main() -> int:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    CHAMPION_DIR.mkdir(parents=True, exist_ok=True)

    if CHAMPION_POINTER_PATH.exists():
        existing = read_json(CHAMPION_POINTER_PATH)
        print(
            f"champion_pointer.json already exists "
            f"(model_version={existing.get('model_version')!r}). Nothing to do."
        )
        return 0

    # Seed the pointer from existing training metadata where available.
    training_meta_path = CHAMPION_MODELS_DIR / "training_meta.json"
    cal_meta_path = CHAMPION_MODELS_DIR / "calibration_meta.json"
    pmf_cal_meta_path = CHAMPION_MODELS_DIR / "pmf_cal_meta.json"

    training_meta = read_json(training_meta_path) if training_meta_path.exists() else {}
    cal_meta = read_json(cal_meta_path) if cal_meta_path.exists() else {}
    pmf_cal_meta = read_json(pmf_cal_meta_path) if pmf_cal_meta_path.exists() else {}

    model_version = (
        training_meta.get("version")
        or training_meta.get("model_version")
        or "bootstrap-unversioned"
    )
    calibrator_version = (
        cal_meta.get("version")
        or pmf_cal_meta.get("version")
        or "phase8-role-bucket"
    )

    now = utcnow_iso()
    commit = git_commit()

    pointer = {
        "schema_version": "1.0",
        "model_version": model_version,
        "calibrator_version": calibrator_version,
        "code_commit": commit,
        "created_at_utc": now,
        "promoted_at_utc": now,
        "model_dir": "artifacts/models",
        "supported_stats": list(SUPPORTED_STATS),
        "notes": (
            "Phase 13A bootstrap. Records the existing production artifacts at "
            "artifacts/models/ as the current champion. No retraining performed; "
            "production read paths unchanged."
        ),
        "phase10d_overlays_in_use": False,
    }
    write_json_atomic(CHAMPION_POINTER_PATH, pointer)

    registry = {
        "schema_version": "1.0",
        "models": [
            {
                "id": f"champion-bootstrap-{git_short_commit()}",
                "model_version": model_version,
                "calibrator_version": calibrator_version,
                "code_commit": commit,
                "registered_at_utc": now,
                "is_champion": True,
                "supported_stats": list(SUPPORTED_STATS),
                "model_dir": "artifacts/models",
                "notes": "Bootstrap registration of existing production artifacts.",
            }
        ],
    }
    write_json_atomic(MODEL_REGISTRY_PATH, registry)

    if not PROMOTION_LOG_PATH.exists():
        with PROMOTION_LOG_PATH.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
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
                    now,
                    "",
                    model_version,
                    "bootstrap",
                    "",
                    "",
                    "Initial champion registration; no validation gates evaluated.",
                    "phase13a-bootstrap",
                    commit,
                ]
            )

    # Marker so the champion dir is non-empty / committable.
    marker = CHAMPION_DIR / "README.md"
    if not marker.exists():
        marker.write_text(
            "# artifacts/models/champion/\n\n"
            "This directory holds backups of prior champion artifacts after a successful\n"
            "promotion. Each backup is a snapshot named `v_<timestamp>/` containing the\n"
            "model pickles that used to live at `artifacts/models/`.\n\n"
            "Pickles in subdirectories are gitignored; the registry under\n"
            "`artifacts/models/registry/` is the source of truth for champion identity.\n"
        )

    print(
        json.dumps(
            {
                "bootstrap": "ok",
                "model_version": model_version,
                "calibrator_version": calibrator_version,
                "pointer": str(CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
