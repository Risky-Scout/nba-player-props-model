"""Phase 13P Part F — validation gate for the live-context challenger.

Reads each ``challengers/<date>_live_context/train_manifest.json``,
inspects the per-target metrics, and decides whether the challenger
beats or safely matches the zero-baseline (which is the champion's
behavior — no live-context adjustment). Promotes only if at least one
material target shows positive relative improvement, AND none of the
fitted targets regress beyond the safe-non-inferiority threshold.

Pass:  PHASE13P_VALIDATION_GATES_PASS  — at least one positive,
       no target worse than -0.5%.
Fail:  PHASE13P_VALIDATION_GATES_FAILED — any target regresses past the
       safe-non-inferiority threshold, or no positive improvement.

This verifier does NOT promote. Promotion is owned by the existing
nightly pipeline + promote_challenger_if_validated.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


SAFE_NONINFERIORITY_THRESHOLD = -0.005  # -0.5%


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--challenger-dir", default=None)
    args = p.parse_args(argv)

    challengers_root = REPO_ROOT / "artifacts" / "models" / "challengers"
    targets_dirs = []
    if args.challenger_dir:
        targets_dirs.append(Path(args.challenger_dir))
    elif challengers_root.exists():
        targets_dirs = sorted(d for d in challengers_root.iterdir()
                              if d.is_dir() and d.name.endswith("_live_context"))
    if not targets_dirs:
        print("PHASE13P_VALIDATION_GATES_FAILED", file=sys.stderr)
        print("  reason: no live-context challenger directories found", file=sys.stderr)
        return 1

    issues: list[str] = []
    facts: dict = {}
    any_positive = False

    for d in targets_dirs:
        tm_path = d / "train_manifest.json"
        if not tm_path.exists():
            issues.append(f"{d.name}: train_manifest.json missing")
            continue
        try:
            tm = json.loads(tm_path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"{d.name}: cannot parse train_manifest: {exc}")
            continue

        per_target = tm.get("metrics_per_target") or {}
        per_target_summary = {}
        for tgt, m in per_target.items():
            if not isinstance(m, dict):
                per_target_summary[tgt] = {"skipped": str(m)}
                continue
            rel = float(m.get("rel_improvement") or 0.0)
            per_target_summary[tgt] = {
                "rel_improvement": rel,
                "n_test": m.get("n_test"),
            }
            if rel > 0:
                any_positive = True
            if rel < SAFE_NONINFERIORITY_THRESHOLD:
                issues.append(
                    f"{d.name}/{tgt}: rel_improvement={rel:+.4%} regresses "
                    f"past safe-non-inferiority threshold "
                    f"({SAFE_NONINFERIORITY_THRESHOLD:+.4%})"
                )
        facts[d.name] = per_target_summary

    if not any_positive:
        issues.append("no fitted target showed positive rel_improvement vs baseline")

    out_dir = REPO_ROOT / "artifacts" / "phase13p"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues": issues,
        "facts": facts,
        "any_positive_improvement": any_positive,
        "safe_noninferiority_threshold": SAFE_NONINFERIORITY_THRESHOLD,
    }
    (out_dir / "validation_gates_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    if issues:
        print("PHASE13P_VALIDATION_GATES_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    print("PHASE13P_VALIDATION_GATES_PASS")
    print(
        f"  challengers={len(targets_dirs)}  any_positive={any_positive}  "
        f"safe_noninferiority_threshold={SAFE_NONINFERIORITY_THRESHOLD:+.4%}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
