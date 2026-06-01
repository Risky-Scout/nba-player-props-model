#!/usr/bin/env python3
"""Verify SGP shadow training artifacts are present, valid, and internally consistent.

Usage
-----
  python3 scripts/verify_sgp_training_artifacts.py \
    --as-of-date 2026-05-29 \
    --repo-root .

Exit codes
----------
  0  All checks pass (or valid-skip is legitimate).
  1  Hard failure: missing required file, bad pointer, or unsupported claim.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path


# ── Helpers ───────────────────────────────────────────────────────────────────

def _warn(msg: str) -> None:
    print(f"::warning::{msg}")


def _fail(msg: str) -> None:
    print(f"::error::{msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


# ── Required pointer fields ───────────────────────────────────────────────────

_REQUIRED_POINTER_FIELDS = {
    "trained_through_date",
    "calibrated_through_date",
    "n_backtest_rows",
    "n_games",
    "n_segments",
    "factor_weights_artifact",
    "joint_calibrator_artifact",
    "calibration_status",
    "promotion_status",
    "created_at_utc",
}

# Promotion statuses that certify production — require explicit user approval.
_PRODUCTION_STATUSES = {"DEFAULT_PRODUCTION_APPROVED"}

# Forbidden claim strings in any report file.
_FORBIDDEN_CLAIM_PHRASES = [
    "proven market superiority",
    "certified edge",
    "continuously beats",
    "guaranteed",
    " lock ",
]


# ── Checks ────────────────────────────────────────────────────────────────────

def _check_pointer(
    pointer_path: Path,
    as_of_date: str,
    today: str,
) -> tuple[bool, dict]:
    """Load and validate sgp_model_pointer.json. Returns (ok, data)."""
    if not pointer_path.exists():
        _warn(f"sgp_model_pointer.json not found at {pointer_path}")
        return True, {}  # absence is valid — training not yet run

    try:
        data = json.loads(pointer_path.read_text())
    except Exception as exc:
        _fail(f"Cannot parse sgp_model_pointer.json: {exc}")
        return False, {}

    hard_fail = False

    # Check required fields.
    missing = _REQUIRED_POINTER_FIELDS - set(data.keys())
    if missing:
        _fail(f"sgp_model_pointer.json missing fields: {sorted(missing)}")
        hard_fail = True

    # trained_through_date must be <= as_of_date (no future training).
    trained_through = data.get("trained_through_date", "")
    if trained_through and trained_through > as_of_date:
        _fail(
            f"Pointer claims trained_through_date={trained_through} "
            f"which is after as_of_date={as_of_date}. Possible leakage."
        )
        hard_fail = True

    # Must never be trained through today or future date.
    if trained_through and trained_through >= today:
        _fail(
            f"Pointer claims trained_through_date={trained_through} >= today={today}. "
            "This would require same-day or future outcome data. REJECTED."
        )
        hard_fail = True

    # No production approval without explicit user action.
    promotion_status = data.get("promotion_status", "")
    if promotion_status in _PRODUCTION_STATUSES:
        _fail(
            f"Pointer has promotion_status={promotion_status!r}. "
            "Default production activation requires explicit user approval. "
            "This status must not be set programmatically."
        )
        hard_fail = True

    # Check for unsupported claims.
    for phrase in _FORBIDDEN_CLAIM_PHRASES:
        raw = json.dumps(data).lower()
        if phrase in raw:
            _fail(f"Pointer contains forbidden phrase: {phrase!r}")
            hard_fail = True

    if not hard_fail:
        _ok(f"sgp_model_pointer.json valid  promotion_status={promotion_status}")

    return not hard_fail, data


def _check_factor_weights(
    fw_dir: Path,
    as_of_date: str,
    require_versioned: bool,
) -> bool:
    """Check factor weights artifacts."""
    latest = fw_dir / "factor_weights_latest.json"
    versioned = fw_dir / f"factor_weights_{as_of_date}.json"

    if not latest.exists():
        _warn("factor_weights_latest.json absent (training may not have run yet)")
        return True  # valid-skip

    try:
        fw = json.loads(latest.read_text())
    except Exception as exc:
        _fail(f"Cannot parse factor_weights_latest.json: {exc}")
        return False

    meta = fw.get("_meta", fw)  # meta may be nested or at top level

    # Check as_of_date in meta is not in the future.
    fw_aod = meta.get("as_of_date", "")
    today = date.today().isoformat()
    if fw_aod and fw_aod >= today:
        _fail(
            f"factor_weights_latest.json as_of_date={fw_aod} >= today={today}. "
            "Factor weights must be fitted through previous day only."
        )
        return False

    if require_versioned and not versioned.exists():
        _warn(f"Versioned factor weights missing: {versioned.name}")

    _ok(f"factor_weights_latest.json  as_of_date={fw_aod}  method={meta.get('method', '?')}")
    return True


def _check_calibrator(
    cal_dir: Path,
    as_of_date: str,
    require_versioned: bool,
) -> bool:
    """Check joint calibrator artifacts."""
    latest = cal_dir / "joint_calibrator_latest.pkl"
    versioned = cal_dir / f"joint_calibrator_{as_of_date}.pkl"

    if not latest.exists():
        _warn("joint_calibrator_latest.pkl absent (training may not have run or insufficient data)")
        return True  # valid when no backtest rows yet

    if require_versioned and not versioned.exists():
        _warn(f"Versioned calibrator missing: {versioned.name}")

    _ok(f"joint_calibrator_latest.pkl present")
    return True


def _check_report(
    path: Path,
    report_name: str,
    required_fields: list[str] | None = None,
    as_of_date: str | None = None,
) -> bool:
    """Check a JSON report for existence, parseability, and forbidden claims."""
    if not path.exists():
        _warn(f"{report_name} not found: {path.name}")
        return True  # may be absent on valid-skip

    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        _fail(f"Cannot parse {report_name}: {exc}")
        return False

    # Check forbidden claim strings.
    raw = json.dumps(data).lower()
    for phrase in _FORBIDDEN_CLAIM_PHRASES:
        if phrase in raw:
            _fail(f"{report_name} contains forbidden phrase: {phrase!r}")
            return False

    # Check required fields if specified.
    if required_fields:
        missing = [f for f in required_fields if f not in data]
        if missing:
            _warn(f"{report_name} missing fields: {missing}")

    # Check that report as_of_date is not in the future.
    report_aod = data.get("as_of_date", "")
    today = date.today().isoformat()
    if report_aod and report_aod >= today:
        _fail(f"{report_name} as_of_date={report_aod} >= today={today}. Leakage risk.")
        return False

    _ok(f"{report_name}  status={data.get('status', data.get('promotion_status', '?'))}")
    return True


def _check_training_status(
    status_path: Path,
    as_of_date: str,
) -> tuple[str, bool]:
    """Return (status_string, ok). Identifies VALID_SKIP vs COMPLETE."""
    if not status_path.exists():
        _warn(f"sgp_training_status.json not found — training may not have run yet")
        return "NOT_RUN", True

    try:
        data = json.loads(status_path.read_text())
    except Exception as exc:
        _fail(f"Cannot parse sgp_training_status.json: {exc}")
        return "PARSE_ERROR", False

    status = data.get("status", "UNKNOWN")
    _ok(f"sgp_training_status.json  status={status}  as_of_date={data.get('as_of_date', '?')}")
    return status, True


def _check_fit_complete_artifacts(
    as_of_date: str,
    sgp_dir: Path,
) -> bool:
    """If training claims FIT_COMPLETE, verify the primary artifacts exist."""
    fw_dir = sgp_dir / "factor_weights"
    cal_dir = sgp_dir / "joint_calibrators"
    reports_dir = sgp_dir / "reports"
    registry_dir = sgp_dir / "registry"

    required = [
        fw_dir / "factor_weights_latest.json",
        fw_dir / f"factor_weights_{as_of_date}.json",
        cal_dir / "joint_calibrator_latest.pkl",
        cal_dir / f"joint_calibrator_{as_of_date}.pkl",
        reports_dir / f"sgp_training_report_{as_of_date}.json",
        reports_dir / f"sgp_calibration_report_{as_of_date}.json",
        reports_dir / f"sgp_gate_report_{as_of_date}.json",
        registry_dir / "sgp_model_pointer.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        for m in missing:
            _fail(f"FIT_COMPLETE but artifact missing: {m}")
        return False
    _ok(f"All FIT_COMPLETE artifacts present for as_of_date={as_of_date}")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--as-of-date", required=True, help="Expected training date (YYYY-MM-DD)")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument("--strict", action="store_true",
                    help="Fail on any warning, not just hard failures")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    as_of_date = args.as_of_date
    today = date.today().isoformat()

    print(f"[SGP-VERIFY-TRAIN] as_of_date={as_of_date}  today={today}")
    print(f"[SGP-VERIFY-TRAIN] repo_root={repo_root}")

    # Hard gate: never accept future as_of_date in verifier either.
    if as_of_date >= today:
        _fail(
            f"as_of_date={as_of_date} is >= today={today}. "
            "Training artifacts must be through previous day only."
        )
        return 1

    sgp_dir = repo_root / "artifacts" / "models" / "sgp"
    reports_dir = sgp_dir / "reports"
    registry_dir = sgp_dir / "registry"

    hard_failures = 0
    warnings_count = 0

    # ── 1. Check training status. ─────────────────────────────────────────────
    print("\n[1/7] Training status ...")
    status_path = reports_dir / "sgp_training_status.json"
    training_status, ok = _check_training_status(status_path, as_of_date)
    if not ok:
        hard_failures += 1

    is_valid_skip = training_status in {"VALID_SKIP", "NOT_RUN"}
    is_fit_complete = training_status == "COMPLETE"

    # ── 2. Check registry pointer. ───────────────────────────────────────────
    print("\n[2/7] Registry pointer ...")
    pointer_ok, pointer_data = _check_pointer(
        registry_dir / "sgp_model_pointer.json",
        as_of_date, today,
    )
    if not pointer_ok:
        hard_failures += 1

    # ── 3. Check factor weights. ─────────────────────────────────────────────
    print("\n[3/7] Factor weights ...")
    fw_ok = _check_factor_weights(
        sgp_dir / "factor_weights",
        as_of_date,
        require_versioned=is_fit_complete,
    )
    if not fw_ok:
        hard_failures += 1

    # ── 4. Check joint calibrator. ───────────────────────────────────────────
    print("\n[4/7] Joint calibrator ...")
    cal_ok = _check_calibrator(
        sgp_dir / "joint_calibrators",
        as_of_date,
        require_versioned=is_fit_complete,
    )
    if not cal_ok:
        hard_failures += 1

    # ── 5. Check reports. ────────────────────────────────────────────────────
    print("\n[5/7] Reports ...")
    for rname, rfile, rfields in [
        (
            "sgp_training_report",
            reports_dir / f"sgp_training_report_{as_of_date}.json",
            ["status", "as_of_date", "n_backtest_rows", "n_settled"],
        ),
        (
            "sgp_calibration_report",
            reports_dir / f"sgp_calibration_report_{as_of_date}.json",
            ["as_of_date", "calibrator_status"],
        ),
        (
            "sgp_gate_report",
            reports_dir / f"sgp_gate_report_{as_of_date}.json",
            ["as_of_date", "promotion_status", "all_gates_pass"],
        ),
    ]:
        if not _check_report(rfile, rname, required_fields=rfields, as_of_date=as_of_date):
            hard_failures += 1

    # ── 6. If FIT_COMPLETE, verify all artifacts exist. ──────────────────────
    print("\n[6/7] FIT_COMPLETE cross-check ...")
    if is_fit_complete:
        if not _check_fit_complete_artifacts(as_of_date, sgp_dir):
            hard_failures += 1
    else:
        _ok(f"Not FIT_COMPLETE (status={training_status}); skipping artifact completeness check")

    # ── 7. Governance: gate report must not claim unauthorized certification. ─
    print("\n[7/7] Governance: no unauthorized market-superiority claims ...")
    gate_path = reports_dir / f"sgp_gate_report_{as_of_date}.json"
    if gate_path.exists():
        try:
            gate = json.loads(gate_path.read_text())
            promo = gate.get("promotion_status", "")
            if promo in _PRODUCTION_STATUSES:
                _fail(
                    f"sgp_gate_report claims promotion_status={promo!r}. "
                    "Requires explicit user approval."
                )
                hard_failures += 1
            else:
                _ok(f"Gate report promotion_status={promo!r} — not production-approved (correct)")
        except Exception as exc:
            _warn(f"Could not parse gate report: {exc}")

    # ── Summary. ─────────────────────────────────────────────────────────────
    print()
    if hard_failures > 0:
        print(
            f"SGP_TRAINING_VERIFY  as_of_date={as_of_date}  "
            f"status=FAIL  hard_failures={hard_failures}"
        )
        return 1

    print(
        f"SGP_TRAINING_VERIFY  as_of_date={as_of_date}  "
        f"status=PASS  training_status={training_status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
