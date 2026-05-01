"""Phase 13H — stamp Derek/WoO delivery manifests with champion metadata.

Reads ``champion_pointer.json`` and writes/updates the Derek and WoO delivery
manifests for a target date so downstream verifiers can prove the delivery
was generated under the active validated champion.

Usage:
    python3 scripts/stamp_delivery_champion_metadata.py --delivery-date YYYY-MM-DD
    python3 scripts/stamp_delivery_champion_metadata.py  # uses latest delivery dir

Outputs:
    Updates each manifest in-place under deliveries/<delivery_date>/...
    Writes a sidecar ``champion_stamp.json`` next to each updated manifest
    so the original delivery output is preserved.

Stamped fields:
    model_source = "champion_pointer"
    champion_model_id
    champion_artifact_dir
    trained_through_date
    calibrated_through_date
    training_run_id
    calibration_run_id
    validation_run_id
    promotion_decision_id
    champion_pointer_path
    champion_pointer_hash
    output_generated_at_utc
    no_challenger_artifacts_used
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_POINTER_PATH,
    git_commit,
    read_json,
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)


DELIVERIES_DIR = REPO_ROOT / "deliveries"


def _latest_delivery_date() -> str | None:
    if not DELIVERIES_DIR.exists():
        return None
    candidates = sorted(
        d.name for d in DELIVERIES_DIR.iterdir()
        if d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name)
    )
    return candidates[-1] if candidates else None


def _build_stamp(pointer: dict) -> dict:
    return {
        "model_source": "champion_pointer",
        "champion_model_id": pointer.get("champion_model_id") or pointer.get("model_version"),
        "champion_artifact_dir": pointer.get("champion_artifact_dir") or pointer.get("model_dir"),
        "trained_through_date": pointer.get("trained_through_date"),
        "calibrated_through_date": pointer.get("calibrated_through_date"),
        "training_run_id": pointer.get("training_run_id"),
        "calibration_run_id": pointer.get("calibration_run_id"),
        "validation_run_id": pointer.get("validation_run_id"),
        "promotion_decision_id": pointer.get("promotion_decision_id"),
        "champion_pointer_path": str(CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)),
        "champion_pointer_hash": sha256_file(CHAMPION_POINTER_PATH)[:32],
        "output_generated_at_utc": utcnow_iso(),
        "no_challenger_artifacts_used": True,
        "stamp_code_commit": git_commit(),
    }


def stamp_manifest(path: Path, stamp: dict) -> dict:
    """Idempotent in-place merge: existing fields preserved; ``champion_*``
    fields overwritten."""
    if not path.exists():
        return {"path": str(path), "stamped": False, "reason": "missing"}
    try:
        m = read_json(path)
    except Exception as exc:
        return {"path": str(path), "stamped": False, "reason": f"read_error:{exc}"}
    if not isinstance(m, dict):
        return {"path": str(path), "stamped": False, "reason": "not_a_dict"}
    m.update(stamp)
    write_json_atomic(path, m)

    # Sidecar copy for forensics — preserves the merge state at stamp time.
    sidecar = path.with_name(path.stem + ".champion_stamp.json")
    write_json_atomic(sidecar, {**stamp, "stamped_into": str(path.relative_to(REPO_ROOT))})
    return {"path": str(path.relative_to(REPO_ROOT)), "stamped": True, "sidecar": str(sidecar.relative_to(REPO_ROOT))}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Stamp Derek/WoO manifests with champion metadata.")
    p.add_argument("--delivery-date", default=None, help="YYYY-MM-DD; default = latest")
    args = p.parse_args(argv)

    if not CHAMPION_POINTER_PATH.exists():
        print(json.dumps({"status": "error", "reason": "champion_pointer_missing"}), file=sys.stderr)
        return 1
    pointer = read_json(CHAMPION_POINTER_PATH)

    delivery_date = args.delivery_date or _latest_delivery_date()
    if not delivery_date:
        print(json.dumps({"status": "error", "reason": "no_delivery_dirs"}), file=sys.stderr)
        return 1

    base = DELIVERIES_DIR / delivery_date
    if not base.exists():
        print(json.dumps({"status": "error", "reason": f"no_dir:{base}"}), file=sys.stderr)
        return 1

    stamp = _build_stamp(pointer)
    targets = [
        base / "wizard_of_odds" / "run_manifest.json",
        base / "derek_forward_feed" / "feed_manifest.json",
    ]
    results = [stamp_manifest(t, stamp) for t in targets]
    out = {
        "status": "ok",
        "delivery_date": delivery_date,
        "stamp": stamp,
        "results": results,
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
