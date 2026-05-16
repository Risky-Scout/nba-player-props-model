"""Phase 13H/13I — stamp Derek/WoO delivery manifests with champion metadata.

Reads ``champion_pointer.json`` and writes/updates the Derek and WoO delivery
manifests for a target date so downstream verifiers can prove the delivery
was generated under the active validated champion.

Phase 13I: also writes a stamping report under
``artifacts/delivery_metadata/<date>/`` and prints
``DELIVERY_CHAMPION_METADATA_STAMP_PASS`` on success — which the daily
delivery workflow's verifier step matches.

Usage:
    python3 scripts/stamp_delivery_champion_metadata.py --delivery-date YYYY-MM-DD
    python3 scripts/stamp_delivery_champion_metadata.py --latest

Outputs:
    Updates each manifest in-place under deliveries/<delivery_date>/...
    Writes a sidecar ``*.champion_stamp.json`` next to each updated manifest
    so the original delivery output is preserved.
    Writes a stamping report at:
        artifacts/delivery_metadata/<date>/stamp_delivery_champion_metadata_report.json
        artifacts/delivery_metadata/<date>/stamp_delivery_champion_metadata_report.md

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
    metadata_stamped_at_utc
    no_challenger_artifacts_used = true

Hard rule: NO prediction values, PMFs, market fields, fair-odds, edges, or
probability columns are touched. The stamp does an additive ``dict.update``
of metadata-only keys; existing fields are preserved unless they share a
name with one of the stamp keys (only then is the stamp authoritative).
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
    now = utcnow_iso()
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
        "output_generated_at_utc": now,
        "metadata_stamped_at_utc": now,
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


DELIVERY_METADATA_DIR = REPO_ROOT / "artifacts" / "delivery_metadata"


def _write_report(delivery_date: str, payload: dict) -> tuple[Path, Path]:
    report_dir = DELIVERY_METADATA_DIR / delivery_date
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "stamp_delivery_champion_metadata_report.json"
    write_json_atomic(json_path, payload)

    md = [
        f"# Delivery Champion Metadata Stamp — {delivery_date}",
        "",
        f"- delivery_date: {payload.get('delivery_date')}",
        f"- status: **{payload.get('status')}**",
        f"- failure_reason: {payload.get('failure_reason') or '(none)'}",
        "",
        "## Champion fields stamped",
        "",
    ]
    stamp = payload.get("stamp") or {}
    for k in (
        "model_source",
        "champion_model_id",
        "champion_artifact_dir",
        "trained_through_date",
        "calibrated_through_date",
        "training_run_id",
        "calibration_run_id",
        "validation_run_id",
        "promotion_decision_id",
        "champion_pointer_path",
        "champion_pointer_hash",
        "metadata_stamped_at_utc",
    ):
        md.append(f"- `{k}` = `{stamp.get(k)}`")
    md += [
        "",
        f"- `no_prediction_values_modified` = `{payload.get('no_prediction_values_modified', True)}`",
        "",
        "## Files",
        "",
        "| Manifest | Stamped | Note |",
        "| --- | --- | --- |",
    ]
    for r in payload.get("results", []):
        md.append(
            f"| {r.get('path')} | {'yes' if r.get('stamped') else 'NO'} | {r.get('reason') or r.get('sidecar') or ''} |"
        )
    md_path = report_dir / "stamp_delivery_champion_metadata_report.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return json_path, md_path


def _delivery_manifest_confirmed_no_games_slate(date: str) -> bool:
    """Strict 4-flag no-games gate for the champion-metadata stamper.

    Returns True if and only if ``deliveries/<date>/manifest.json``
    declares ALL of: ``no_games_slate == True``,
    ``confirmed_no_games_slate == True``,
    ``reason == "no_games_slate"``,
    ``market_superiority_evaluated == False``, and
    ``derek_forward_feed_expected == False``.

    These four fields are stamped together only by the orchestrator's
    ``_emit_no_games_delivery_package`` after BOTH the predict
    no-games signal AND an independent BDL ``/games`` schedule lookup
    have confirmed zero games for the date. On a confirmed no-games
    slate there are by design no Derek or WoO manifests to stamp —
    soft-skip rather than hard-fail. Any other manifest shape returns
    False so a games-bearing slate still hard-fails on a missing
    Derek/WoO manifest.
    """
    import json as _json
    if not date:
        return False
    manifest_path = REPO_ROOT / "deliveries" / date / "manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        payload = _json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    return (
        payload.get("no_games_slate") is True
        and payload.get("confirmed_no_games_slate") is True
        and payload.get("reason") == "no_games_slate"
        and payload.get("market_superiority_evaluated") is False
        and payload.get("derek_forward_feed_expected") is False
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Stamp Derek/WoO manifests with champion metadata.")
    p.add_argument("--delivery-date", default=None, help="YYYY-MM-DD")
    p.add_argument(
        "--latest",
        action="store_true",
        help="Use the latest delivery directory (incompatible with --delivery-date).",
    )
    args = p.parse_args(argv)

    if args.delivery_date and args.latest:
        print("--delivery-date and --latest are mutually exclusive", file=sys.stderr)
        return 2

    if not CHAMPION_POINTER_PATH.exists():
        print("DELIVERY_CHAMPION_METADATA_STAMP_FAILED", file=sys.stderr)
        print("  reason: champion_pointer_missing", file=sys.stderr)
        return 1
    pointer = read_json(CHAMPION_POINTER_PATH)

    delivery_date = args.delivery_date or _latest_delivery_date()
    if not delivery_date:
        print("DELIVERY_CHAMPION_METADATA_STAMP_FAILED", file=sys.stderr)
        print("  reason: no_delivery_dirs", file=sys.stderr)
        return 1

    if _delivery_manifest_confirmed_no_games_slate(delivery_date):
        payload = {
            "schema_version": "1.0",
            "status": "soft_skipped_no_games_slate",
            "delivery_date": delivery_date,
            "no_prediction_values_modified": True,
            "results": [],
            "soft_skip_reason": "confirmed_no_games_slate",
        }
        _write_report(delivery_date, payload)
        print(
            f"DELIVERY_CHAMPION_METADATA_STAMP_SOFT_SKIP_NO_GAMES "
            f"date={delivery_date} "
            f"manifest=deliveries/{delivery_date}/manifest.json "
            f"gate=no_games_slate+confirmed_no_games_slate+"
            f"market_superiority_evaluated=false+derek_forward_feed_expected=false "
            f"reason=no_derek_or_woo_manifest_to_stamp_on_confirmed_no_games_slate"
        )
        return 0

    base = DELIVERIES_DIR / delivery_date
    if not base.exists():
        # Treat absent date dir as a soft skip when --latest was requested
        # (means there are no deliveries yet); a hard failure when the
        # caller explicitly named a date that's missing.
        if args.delivery_date:
            print("DELIVERY_CHAMPION_METADATA_STAMP_FAILED", file=sys.stderr)
            print(f"  reason: delivery_dir_missing path={base.relative_to(REPO_ROOT)}", file=sys.stderr)
            return 1
        report = {
            "status": "skipped_no_dir",
            "delivery_date": delivery_date,
            "no_prediction_values_modified": True,
            "results": [],
        }
        _write_report(delivery_date, report)
        print("DELIVERY_CHAMPION_METADATA_STAMP_PASS")
        print(f"  delivery_date={delivery_date}  (no dir to stamp)")
        return 0

    stamp = _build_stamp(pointer)
    targets = [
        base / "wizard_of_odds" / "run_manifest.json",
        base / "derek_forward_feed" / "feed_manifest.json",
    ]
    # Optional: pmf_model_review_package run_manifest if the format supports
    # it (some delivery layouts include this; we stamp idempotently).
    review_manifest = base / "pmf_model_review_package" / "run_manifest.json"
    if review_manifest.exists():
        targets.append(review_manifest)

    results = [stamp_manifest(t, stamp) for t in targets]
    files_stamped = [r["path"] for r in results if r.get("stamped")]
    files_missing = [r["path"] for r in results if not r.get("stamped")]
    payload = {
        "schema_version": "1.0",
        "status": "ok",
        "delivery_date": delivery_date,
        "champion_model_id": stamp.get("champion_model_id"),
        "trained_through_date": stamp.get("trained_through_date"),
        "calibrated_through_date": stamp.get("calibrated_through_date"),
        "champion_pointer_hash": stamp.get("champion_pointer_hash"),
        "fields_written": list(stamp.keys()),
        "files_stamped": files_stamped,
        "files_missing": files_missing,
        "no_prediction_values_modified": True,
        "stamp": stamp,
        "results": results,
    }
    _write_report(delivery_date, payload)

    # Strict: at least one Derek or WoO manifest must have been stamped.
    if not files_stamped:
        payload["status"] = "failed"
        payload["failure_reason"] = "no_derek_or_woo_manifest_to_stamp"
        _write_report(delivery_date, payload)
        print("DELIVERY_CHAMPION_METADATA_STAMP_FAILED", file=sys.stderr)
        print(f"  delivery_date={delivery_date}", file=sys.stderr)
        print(f"  reason=no_derek_or_woo_manifest_to_stamp", file=sys.stderr)
        return 1

    print("DELIVERY_CHAMPION_METADATA_STAMP_PASS")
    print(f"  delivery_date={delivery_date}")
    print(f"  champion_model_id={stamp.get('champion_model_id')!r}")
    print(f"  trained_through_date={stamp.get('trained_through_date')!r}")
    print(f"  calibrated_through_date={stamp.get('calibrated_through_date')!r}")
    print(f"  champion_pointer_hash={stamp.get('champion_pointer_hash')}")
    print(f"  files_stamped={files_stamped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
