#!/usr/bin/env python3
"""Contextual deployment contract verifier for the champion pointer.

Prevents an active contextual/direct-lineup champion pointer from being
replaced by a non-contextual champion pointer.  Intended to run after
every ``promote_challenger_if_validated.py`` call and before any
``git add artifacts/models/registry/champion_pointer.json`` commit step.

Usage:
    python3 scripts/verify_champion_pointer_contextual_contract.py
    python3 scripts/verify_champion_pointer_contextual_contract.py \\
        --require-contextual
    python3 scripts/verify_champion_pointer_contextual_contract.py \\
        --current-pointer <path>
    python3 scripts/verify_champion_pointer_contextual_contract.py \\
        --previous-pointer <path>

Behavior:
  1. Load ``current`` from artifacts/models/registry/champion_pointer.json
     (or --current-pointer override).
  2. Optionally load ``previous`` from the path stored in
     current.previous_pointer_backup or --previous-pointer override.
  3. Determine whether the previous pointer was contextual (by inspecting
     feature_set_id, contextual_challenger_dir, contextual_pmf_engine,
     or direct_lineup_pmf_driver).
  4. If the previous pointer WAS contextual, the current pointer must also
     be contextual unless an explicit override is passed.
  5. When --require-contextual is passed, the current pointer must be
     contextual regardless of what the previous pointer was.
  6. Verify that all required contextual fields are present and that
     the referenced contextual_challenger_dir exists on disk.

Exit codes:
    0  +  CHAMPION_POINTER_CONTEXTUAL_CONTRACT_PASS
    1  +  CHAMPION_POINTER_CONTEXTUAL_CONTRACT_FAILED  +  list of issues
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CHAMPION_POINTER_PATH = (
    REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
)

# feature_set_id prefixes that indicate a contextual/direct-lineup deployment.
CONTEXTUAL_FS_PREFIXES = ("phase13q_", "phase13r_", "phase13s_")

# Fields required when a pointer claims to be contextual.
REQUIRED_CONTEXTUAL_FIELDS = (
    "feature_set_id",
    "contextual_trained_through_date",
    "contextual_challenger_dir",
)

# Base fields required in any promoted champion pointer.
REQUIRED_BASE_FIELDS = (
    "champion_model_id",
    "model_version",
    "train_manifest_path",
    "validation_report_path",
    "trained_through_date",
)


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def _is_contextual(pointer: dict) -> bool:
    """Return True when the pointer represents a contextual/direct-lineup champion."""
    fs_id = pointer.get("feature_set_id") or ""
    if fs_id.startswith(CONTEXTUAL_FS_PREFIXES):
        return True
    if pointer.get("contextual_challenger_dir"):
        return True
    if pointer.get("contextual_pmf_engine"):
        return True
    if pointer.get("direct_lineup_pmf_driver"):
        return True
    return False


def _verify_contextual_fields(pointer: dict, issues: list[str]) -> None:
    """Append issues for any missing or invalid contextual fields."""
    # Base fields always required.
    for field in REQUIRED_BASE_FIELDS:
        if not pointer.get(field):
            issues.append(f"missing required base field: {field}")

    # Contextual fields.
    for field in REQUIRED_CONTEXTUAL_FIELDS:
        if field not in pointer or pointer[field] is None:
            issues.append(f"missing required contextual field: {field}")

    # feature_set_id must start with a recognized contextual prefix.
    fs_id = pointer.get("feature_set_id") or ""
    if not fs_id:
        issues.append("feature_set_id is empty/null")
    elif not fs_id.startswith(CONTEXTUAL_FS_PREFIXES):
        issues.append(
            f"feature_set_id={fs_id!r} does not start with a recognized "
            f"contextual prefix {CONTEXTUAL_FS_PREFIXES}"
        )

    # Must have at least one contextual engine field.
    has_engine = bool(
        pointer.get("contextual_pmf_engine")
        or pointer.get("direct_lineup_pmf_driver")
    )
    if not has_engine:
        issues.append(
            "pointer has no contextual_pmf_engine or direct_lineup_pmf_driver"
        )

    # contextual_challenger_dir must exist on disk if present.
    contextual_dir = pointer.get("contextual_challenger_dir")
    if contextual_dir:
        p = (
            REPO_ROOT / contextual_dir
            if not Path(contextual_dir).is_absolute()
            else Path(contextual_dir)
        )
        if not p.exists():
            issues.append(
                f"contextual_challenger_dir does not exist on disk: {contextual_dir}"
            )

    # contextual_train_manifest_path or direct-lineup equivalent should exist.
    for field in (
        "contextual_train_manifest_path",
        "contextual_validation_report_path",
        "contextual_no_leakage_manifest_path",
    ):
        path_val = pointer.get(field)
        if path_val:
            p = (
                REPO_ROOT / path_val
                if not Path(path_val).is_absolute()
                else Path(path_val)
            )
            if not p.exists():
                issues.append(f"{field} referenced but does not exist: {path_val}")

    # Must have contextual_trained_through_date or equivalent.
    if not pointer.get("contextual_trained_through_date"):
        issues.append("contextual_trained_through_date is missing or null")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify champion pointer contextual deployment contract."
    )
    parser.add_argument(
        "--current-pointer",
        default=None,
        help="Path to the current champion pointer JSON. "
        "Defaults to artifacts/models/registry/champion_pointer.json.",
    )
    parser.add_argument(
        "--previous-pointer",
        default=None,
        help="Path to the previous champion pointer JSON. "
        "If omitted, resolved from current.previous_pointer_backup.",
    )
    parser.add_argument(
        "--require-contextual",
        action="store_true",
        help="Fail if the current pointer is not contextual, regardless "
        "of what the previous pointer was.",
    )
    args = parser.parse_args(argv)

    # Load current pointer.
    current_path = (
        Path(args.current_pointer) if args.current_pointer else CHAMPION_POINTER_PATH
    )
    if not current_path.exists():
        print("CHAMPION_POINTER_CONTEXTUAL_CONTRACT_FAILED", file=sys.stderr)
        print("  champion_pointer.json not found", file=sys.stderr)
        return 1

    current = _load_json(current_path)

    # Optionally load previous pointer.
    previous: dict | None = None
    previous_path: Path | None = None
    if args.previous_pointer:
        previous_path = Path(args.previous_pointer)
    else:
        backup = current.get("previous_pointer_backup")
        if backup:
            previous_path = (
                REPO_ROOT / backup
                if not Path(backup).is_absolute()
                else Path(backup)
            )
    if previous_path and previous_path.exists():
        previous = _load_json(previous_path)

    # Determine if previous pointer was contextual.
    previous_was_contextual = previous is not None and _is_contextual(previous)
    current_is_contextual = _is_contextual(current)

    issues: list[str] = []

    # If require-contextual is set OR previous was contextual → current must be too.
    if args.require_contextual or previous_was_contextual:
        if not current_is_contextual:
            issues.append(
                "previous pointer was contextual (or --require-contextual was passed) "
                "but current pointer has no contextual/direct-lineup fields — "
                "refusing to accept a non-contextual pointer in contextual production mode"
            )
        else:
            # Verify all contextual fields.
            _verify_contextual_fields(current, issues)
    else:
        # Not in contextual mode — just verify the base fields.
        for field in REQUIRED_BASE_FIELDS:
            if not current.get(field):
                issues.append(f"missing required base field: {field}")

    if issues:
        print("CHAMPION_POINTER_CONTEXTUAL_CONTRACT_FAILED", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    print("CHAMPION_POINTER_CONTEXTUAL_CONTRACT_PASS")
    print(f"  champion_model_id: {current.get('champion_model_id')}")
    print(f"  feature_set_id: {current.get('feature_set_id')}")
    print(f"  contextual_challenger_dir: {current.get('contextual_challenger_dir')}")
    print(f"  previous_was_contextual: {previous_was_contextual}")
    print(f"  require_contextual_flag: {args.require_contextual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
