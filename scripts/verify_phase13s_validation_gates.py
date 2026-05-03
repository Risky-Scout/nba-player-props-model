"""Phase 13S Part G — recalibration + validation gates.

Reads the Phase 13S challenger's metrics_per_target and asserts:

  * minutes adjustment shows positive rel_improvement >= 5%;
  * no fitted target regresses past -0.5%;
  * direct_lineup_pmf_driver flag is true;
  * the recalibration manifest documents the trained-through and
    calibrated-through cutoffs as identical (the same Ridge model
    serves both).

Pass lines:
    PHASE13S_DIRECT_LINEUP_CALIBRATION_PASS
    PHASE13S_VALIDATION_GATES_PASS

Fail line:
    PHASE13S_VALIDATION_GATES_FAILED
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


SAFE_NONINFERIORITY_THRESHOLD = -0.005   # -0.5%
MINUTES_MIN_RELIMPROVEMENT = 0.05        # +5%


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--challenger-dir", default=None)
    args = p.parse_args(argv)

    issues: list[str] = []
    facts: dict = {}

    root = REPO_ROOT / "artifacts" / "models" / "challengers"
    targets = []
    if args.challenger_dir:
        targets.append(Path(args.challenger_dir))
    else:
        if root.exists():
            targets = sorted(d for d in root.iterdir()
                              if d.is_dir() and d.name.endswith("_direct_lineup_contextual"))
    if not targets:
        print("PHASE13S_VALIDATION_GATES_FAILED", file=sys.stderr)
        print("  reason: no <date>_direct_lineup_contextual dir found",
              file=sys.stderr)
        return 1

    any_positive = False
    for d in targets:
        tm_path = d / "train_manifest.json"
        if not tm_path.exists():
            issues.append(f"{d.name}: train_manifest.json missing")
            continue
        tm = json.loads(tm_path.read_text(encoding="utf-8"))
        per_target = tm.get("metrics_per_target") or {}
        d_facts: dict = {}
        for tgt, m in per_target.items():
            if not isinstance(m, dict):
                d_facts[tgt] = {"skipped": str(m)}
                continue
            rel = float(m.get("rel_improvement") or 0.0)
            d_facts[tgt] = {
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
        # Minutes gate.
        minutes_metrics = per_target.get("minutes")
        if not isinstance(minutes_metrics, dict):
            issues.append(f"{d.name}: minutes metrics missing")
        else:
            mr = float(minutes_metrics.get("rel_improvement") or 0.0)
            if mr < MINUTES_MIN_RELIMPROVEMENT:
                issues.append(
                    f"{d.name}: minutes rel_improvement={mr:+.4%} below "
                    f"required floor {MINUTES_MIN_RELIMPROVEMENT:+.4%}"
                )
        if not tm.get("direct_lineup_pmf_driver"):
            issues.append(f"{d.name}: direct_lineup_pmf_driver flag not true")
        # trained_through == calibrated_through (additive challenger).
        if tm.get("trained_through_date") != tm.get("calibrated_through_date"):
            issues.append(
                f"{d.name}: trained_through ({tm.get('trained_through_date')}) "
                f"!= calibrated_through ({tm.get('calibrated_through_date')})"
            )
        facts[d.name] = d_facts

    if not any_positive:
        issues.append("no fitted target showed positive rel_improvement")

    out_dir = REPO_ROOT / "artifacts" / "phase13s"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues": issues,
        "facts": facts,
        "any_positive_improvement": any_positive,
        "minutes_min_rel_improvement": MINUTES_MIN_RELIMPROVEMENT,
        "safe_noninferiority_threshold": SAFE_NONINFERIORITY_THRESHOLD,
    }
    (out_dir / "validation_gates_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    if issues:
        print("PHASE13S_VALIDATION_GATES_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    print("PHASE13S_DIRECT_LINEUP_CALIBRATION_PASS")
    print("PHASE13S_VALIDATION_GATES_PASS")
    print(
        f"  challengers={len(targets)} "
        f"any_positive={any_positive} "
        f"minutes_floor={MINUTES_MIN_RELIMPROVEMENT:+.4%} "
        f"safe_noninferiority_threshold={SAFE_NONINFERIORITY_THRESHOLD:+.4%}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
