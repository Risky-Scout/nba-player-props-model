"""Verify that the champion pointer satisfies the contextual contract.

Prevents a contextual champion pointer from being silently replaced by a
non-contextual one. This script is invoked by the nightly training workflow
immediately after promotion and before committing champion_pointer.json.

CLI:
    python3 scripts/verify_champion_pointer_contextual_contract.py
    python3 scripts/verify_champion_pointer_contextual_contract.py --require-contextual
    python3 scripts/verify_champion_pointer_contextual_contract.py --current-pointer <path>
    python3 scripts/verify_champion_pointer_contextual_contract.py --previous-pointer <path>

Pass line: CHAMPION_POINTER_CONTEXTUAL_CONTRACT_PASS
Fail line: CHAMPION_POINTER_CONTEXTUAL_CONTRACT_FAILED
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_POINTER = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: cannot load {path}: {exc}", file=sys.stderr)
        return {}


def _is_contextual(pointer: dict) -> bool:
    """Return True if a pointer has any contextual fields set."""
    fsi = pointer.get("feature_set_id") or ""
    if fsi.startswith("phase13q_") or fsi.startswith("phase13s_"):
        return True
    if pointer.get("contextual_challenger_dir"):
        return True
    if pointer.get("contextual_pmf_engine"):
        return True
    if pointer.get("direct_lineup_pmf_driver"):
        return True
    return False


def _check_current_pointer(pointer: dict) -> list[str]:
    """Return list of contract violations (empty = pass)."""
    issues: list[str] = []

    fsi = pointer.get("feature_set_id") or ""
    if not fsi:
        issues.append("feature_set_id is missing/null")
    elif not (fsi.startswith("phase13q_") or fsi.startswith("phase13s_")):
        issues.append(
            f"feature_set_id={fsi!r} does not start with phase13q_ or phase13s_"
        )

    has_contextual_block = any([
        pointer.get("contextual_challenger_dir"),
        pointer.get("contextual_pmf_engine"),
        pointer.get("direct_lineup_pmf_driver"),
    ])
    if not has_contextual_block:
        issues.append(
            "none of contextual_challenger_dir / contextual_pmf_engine / "
            "direct_lineup_pmf_driver are set"
        )

    if fsi.startswith("phase13q_"):
        ctx_dir_str = pointer.get("contextual_challenger_dir") or ""
        if ctx_dir_str:
            ctx_dir = REPO_ROOT / ctx_dir_str
            pkl_files = sorted(ctx_dir.glob("phase13q_*.pkl")) if ctx_dir.exists() else []
            if not pkl_files:
                issues.append(
                    f"feature_set_id starts with phase13q_ but contextual_challenger_dir "
                    f"({ctx_dir_str}) has no phase13q_*.pkl files"
                )
        else:
            issues.append(
                "feature_set_id starts with phase13q_ but contextual_challenger_dir is not set"
            )

    if fsi.startswith("phase13s_"):
        if not pointer.get("direct_lineup_pmf_driver"):
            issues.append(
                "feature_set_id starts with phase13s_ but direct_lineup_pmf_driver is not set"
            )

    return issues


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify champion pointer satisfies contextual contract"
    )
    parser.add_argument(
        "--require-contextual",
        action="store_true",
        help="Always require contextual fields regardless of previous pointer",
    )
    parser.add_argument(
        "--current-pointer",
        metavar="PATH",
        help=f"Path to current champion_pointer.json (default: {DEFAULT_POINTER})",
    )
    parser.add_argument(
        "--previous-pointer",
        metavar="PATH",
        help="Path to previous champion_pointer.json to determine if previous was contextual",
    )
    args = parser.parse_args(argv)

    current_path = Path(args.current_pointer) if args.current_pointer else DEFAULT_POINTER
    if not current_path.exists():
        print(
            f"CHAMPION_POINTER_CONTEXTUAL_CONTRACT_FAILED: "
            f"current pointer not found at {current_path}",
            file=sys.stderr,
        )
        return 1

    current = _load_json(current_path)

    # Determine if we need to enforce contextual contract.
    require_contextual = args.require_contextual

    if not require_contextual and args.previous_pointer:
        prev_path = Path(args.previous_pointer)
        if prev_path.exists():
            previous = _load_json(prev_path)
            if _is_contextual(previous):
                require_contextual = True
                print(
                    f"  Previous pointer at {prev_path} was contextual — "
                    "enforcing contextual contract on current pointer."
                )
        else:
            print(f"  WARNING: --previous-pointer {prev_path} not found; skipping check.")

    if not require_contextual:
        # Try to find previous pointer from current pointer's backup reference.
        prev_backup = current.get("previous_pointer_backup") or ""
        if prev_backup:
            prev_path = REPO_ROOT / prev_backup
            if prev_path.exists():
                previous = _load_json(prev_path)
                if _is_contextual(previous):
                    require_contextual = True
                    print(
                        f"  Previous backup pointer ({prev_backup}) was contextual — "
                        "enforcing contextual contract on current pointer."
                    )

    if not require_contextual:
        print("CHAMPION_POINTER_CONTEXTUAL_CONTRACT_PASS")
        print(
            "  No contextual requirement detected "
            "(previous pointer was not contextual and --require-contextual not set)"
        )
        return 0

    issues = _check_current_pointer(current)
    if issues:
        print("CHAMPION_POINTER_CONTEXTUAL_CONTRACT_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1

    print("CHAMPION_POINTER_CONTEXTUAL_CONTRACT_PASS")
    fsi = current.get("feature_set_id", "")
    ctx_dir = current.get("contextual_challenger_dir", "")
    print(f"  feature_set_id={fsi}")
    print(f"  contextual_challenger_dir={ctx_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
