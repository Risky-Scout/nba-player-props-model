"""Write (or update) artifacts/models/registry/fresh_delivery_model_pointer.json.

This script decouples the "freshest trained-and-calibrated model" from
"market-superior champion pointer". It runs after every training + calibration
cycle and advances the fresh pointer as long as basic health checks pass:

  1. Calibration artifacts exist in artifacts/models/ (pkl files present)
  2. No leakage detected (validation_report.json leakage_check passes or is absent)
  3. PMF validity passes (no pmf_validity issues in validation_report.json)

Market superiority gate failures do NOT block the fresh pointer. The market_quality_status
field records whether market gates passed so downstream consumers can filter if needed.

The delivery pipeline should preferentially use fresh_delivery_model_pointer.json
over champion_pointer.json when champion_pointer is stale (trained_through_date older
than 7 days), logging MODEL_SELECTION_OVERRIDES_STALE_CHAMPION_POINTER.

Usage:
    python3 scripts/write_fresh_delivery_pointer.py --as-of-date YYYY-MM-DD
    python3 scripts/write_fresh_delivery_pointer.py --as-of-date YYYY-MM-DD --force

Exit codes:
    0  pointer written (or unchanged because same date already written and --force not set)
    1  hard failure (leakage or PMF validity issue) — pointer not advanced
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    FRESH_DELIVERY_POINTER_PATH,
    REGISTRY_DIR,
    challenger_dir,
    git_commit,
    read_json,
    utcnow_iso,
    write_json_atomic,
)

# ── Constants ─────────────────────────────────────────────────────────────
MODEL_DIR = REPO_ROOT / "artifacts" / "models"
_SOFT_GATE_PREFIXES = ("m6_3_", "market_")
_SOFT_GATE_EXACT = frozenset({"no_severe_market_stat_bucket_regression", "m6_3_review_cells_guarded"})

# Hard gates that always block the fresh pointer
_HARD_GATE_PREFIXES = ("leakage_", "pmf_validity", "post_outcome_feature")
_HARD_GATE_EXACT = frozenset({
    "no_future_rows_leakage",
    "no_partial_rows_leakage",
    "leakage_check",
    "pmf_validity_failed",
})

# Minimum pkl files expected in artifacts/models/ for a healthy calibration
_MIN_PKL_FILES = 5


def _is_soft_gate(name: str) -> bool:
    for p in _SOFT_GATE_PREFIXES:
        if name.startswith(p):
            return True
    return name in _SOFT_GATE_EXACT


def _is_hard_gate(name: str) -> bool:
    for p in _HARD_GATE_PREFIXES:
        if name.startswith(p):
            return True
    return name in _HARD_GATE_EXACT


def _check_calibration_artifacts() -> tuple[bool, str]:
    """Return (ok, reason). Requires at least MIN_PKL_FILES .pkl files in MODEL_DIR."""
    pkl_files = list(MODEL_DIR.glob("*.pkl"))
    if len(pkl_files) < _MIN_PKL_FILES:
        return False, f"only {len(pkl_files)} pkl files in {MODEL_DIR} (need >= {_MIN_PKL_FILES})"
    pmf_cals = [f for f in pkl_files if f.name.startswith("pmf_cal_role_")]
    if len(pmf_cals) < 7:
        return False, f"only {len(pmf_cals)} pmf_cal_role_*.pkl files (need >= 7)"
    return True, f"{len(pmf_cals)} pmf_cal_role calibrators present"


def _classify_gates(validation: dict) -> tuple[list[str], list[str]]:
    """Return (hard_failures, soft_failures)."""
    gates_failed = validation.get("gates_failed") or []
    hard, soft = [], []
    for g in gates_failed:
        name = g.get("name") if isinstance(g, dict) else str(g)
        if not name:
            continue
        if _is_hard_gate(name):
            hard.append(name)
        else:
            soft.append(name)
    return hard, soft


def _market_quality_status(soft_failures: list[str]) -> str:
    market_failures = [g for g in soft_failures if g.startswith("market_") or g == "no_severe_market_stat_bucket_regression"]
    if not market_failures:
        return "market_superior_or_non_inferior"
    return f"market_underperforming:{','.join(sorted(market_failures))}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of-date", required=True, help="Training as-of date YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", help="Overwrite even if same date already written")
    args = parser.parse_args(argv)

    as_of_date: str = args.as_of_date
    ch_dir = challenger_dir(as_of_date)

    # ── 1. Check calibration artifacts ────────────────────────────────────
    cal_ok, cal_reason = _check_calibration_artifacts()
    if not cal_ok:
        print(f"FRESH_DELIVERY_POINTER_BLOCKED: calibration artifacts missing: {cal_reason}", flush=True)
        return 1

    # ── 2. Load validation report (best-effort; absence is not a hard block) ─
    validation_path = ch_dir / "validation_report.json"
    validation: dict = {}
    if validation_path.exists():
        try:
            validation = read_json(validation_path)
        except Exception as exc:
            print(f"FRESH_DELIVERY_POINTER_WARNING: could not read validation_report.json: {exc}", flush=True)

    # ── 3. PMF validity hard gate ─────────────────────────────────────────
    pmf_issues = validation.get("pmf_validity", {}).get("issues") or []
    if pmf_issues:
        print(f"FRESH_DELIVERY_POINTER_BLOCKED: pmf_validity issues: {pmf_issues}", flush=True)
        return 1

    # ── 4. Classify gates ─────────────────────────────────────────────────
    hard_failures, soft_failures = _classify_gates(validation)
    if hard_failures:
        print(f"FRESH_DELIVERY_POINTER_BLOCKED: hard gate failures: {hard_failures}", flush=True)
        return 1

    # ── 5. Idempotency check ──────────────────────────────────────────────
    existing: dict = {}
    if FRESH_DELIVERY_POINTER_PATH.exists():
        try:
            existing = read_json(FRESH_DELIVERY_POINTER_PATH)
        except Exception:
            pass

    if existing.get("trained_through_date") == as_of_date and not args.force:
        print(f"FRESH_DELIVERY_POINTER_ALREADY_CURRENT: trained_through_date={as_of_date}", flush=True)
        return 0

    # ── 6. Build train/cal manifests for metadata ─────────────────────────
    train_manifest: dict = {}
    tm_path = ch_dir / "train_manifest.json"
    if tm_path.exists():
        try:
            train_manifest = read_json(tm_path)
        except Exception:
            pass

    cal_manifest: dict = {}
    cm_path = ch_dir / "calibration_manifest.json"
    if cm_path.exists():
        try:
            cal_manifest = read_json(cm_path)
        except Exception:
            pass

    cutoff = (
        train_manifest.get("resolved_training_cutoff_date")
        or train_manifest.get("training_summary", {}).get("trained_through_date")
        or as_of_date
    )

    challenger_version = (
        validation.get("challenger", {}).get("model_version")
        or train_manifest.get("training_summary", {}).get("model_version")
        or f"challenger-{as_of_date}"
    )

    market_status = _market_quality_status(soft_failures)
    promotion_eligible = (market_status == "market_superior_or_non_inferior")

    # ── 7. Write pointer ───────────────────────────────────────────────────
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    pointer = {
        "schema_version": "1.0",
        "pointer_type": "fresh_delivery",
        "description": (
            "Freshest trained-and-calibrated base model. Market gates are diagnostics "
            "only — this pointer advances on freshness + leakage + PMF validity checks."
        ),
        "base_model_version": challenger_version,
        "trained_through_date": cutoff,
        "calibrated_through_date": cutoff,
        "as_of_date": as_of_date,
        "model_dir": str(MODEL_DIR.relative_to(REPO_ROOT)),
        "challenger_dir": str(ch_dir.relative_to(REPO_ROOT)),
        "code_commit": git_commit(),
        "written_at_utc": utcnow_iso(),
        # Diagnostic fields — do not use to gate delivery
        "market_quality_status": market_status,
        "promotion_eligible": promotion_eligible,
        "soft_gate_failures": sorted(soft_failures),
        "previous_pointer": {
            "base_model_version": existing.get("base_model_version"),
            "trained_through_date": existing.get("trained_through_date"),
        } if existing else None,
    }

    write_json_atomic(FRESH_DELIVERY_POINTER_PATH, pointer)

    print(
        f"FRESH_DELIVERY_POINTER_WRITTEN: "
        f"base_model={challenger_version} "
        f"trained_through={cutoff} "
        f"market_quality={market_status}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
