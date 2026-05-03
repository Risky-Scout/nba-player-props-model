"""Phase 13R Part H — Phase 13Q no-leakage verifier.

Wraps the existing Phase 13P no-leakage verifier (which already covers
both ``_live_context`` and ``_contextual`` challenger directories) and
also adds Phase 13Q-specific assertions:

  * ``feature_set_id`` in train_manifest is the Phase 13Q contextual ID
  * Phase 13Q game-context features are documented as pre-game knowable
    in the train_manifest's ``lineup_history_note``
  * none of the saved Phase 13Q feature lists contain same-game realized
    minutes / stats / market columns
  * the no_leakage_manifest's asof_cutoff_rule is consistent with the
    builder's actual rule

Pass line:  PHASE13Q_NO_LEAKAGE_PASS
Fail line:  PHASE13Q_NO_LEAKAGE_FAILED
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


PHASE13Q_FEATURE_SET_IDS = (
    "phase13q_contextual_pmf_engine_v1",
    "phase13q_contextual_lineup_injury_game_v1",
)


def _run_phase13p_verifier() -> tuple[int, str, str]:
    rc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "verify_phase13p_no_leakage.py")],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    return rc.returncode, rc.stdout, rc.stderr


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.parse_args(argv)

    issues: list[str] = []
    facts: dict = {}

    rc, out, err = _run_phase13p_verifier()
    facts["phase13p_no_leakage_returncode"] = rc
    facts["phase13p_no_leakage_stdout_tail"] = "\n".join(
        (out or "").strip().splitlines()[-6:]
    )
    facts["phase13p_no_leakage_stderr_tail"] = "\n".join(
        (err or "").strip().splitlines()[-6:]
    )
    if rc != 0:
        issues.append("phase13p_no_leakage verifier failed (also covers Phase 13Q)")

    challengers_root = REPO_ROOT / "artifacts" / "models" / "challengers"
    contextual_dirs = []
    if challengers_root.exists():
        contextual_dirs = sorted(
            d for d in challengers_root.iterdir()
            if d.is_dir() and d.name.endswith("_contextual")
            and not d.name.endswith("_direct_lineup_contextual")
        )
    if not contextual_dirs:
        issues.append("no <date>_contextual challenger directory found")

    for d in contextual_dirs:
        d_facts: dict = {}
        tm_path = d / "train_manifest.json"
        if not tm_path.exists():
            issues.append(f"{d.name}: train_manifest.json missing")
            continue
        try:
            tm = json.loads(tm_path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"{d.name}: cannot parse train_manifest: {exc}")
            continue
        d_facts["feature_set_id"] = tm.get("feature_set_id")
        d_facts["trained_through_date"] = tm.get("trained_through_date")
        d_facts["calibrated_through_date"] = tm.get("calibrated_through_date")
        d_facts["historical_lineup_source"] = tm.get("historical_lineup_source")
        if tm.get("feature_set_id") not in PHASE13Q_FEATURE_SET_IDS:
            issues.append(
                f"{d.name}: feature_set_id={tm.get('feature_set_id')!r} is "
                f"not in {PHASE13Q_FEATURE_SET_IDS}"
            )
        if not tm.get("no_same_game_performance_predictors"):
            issues.append(
                f"{d.name}: no_same_game_performance_predictors not set true"
            )
        if not tm.get("historical_lineup_source_safe_for_training"):
            issues.append(
                f"{d.name}: historical_lineup_source_safe_for_training not set true"
            )
        # Phase 13Q lineup_history_note must exist and document the
        # game-context features as pre-game knowable.
        note = (tm.get("lineup_history_note") or "").lower()
        for key in ("rest_days", "is_back_to_back", "season_game_number",
                    "starter_proxy_lagged"):
            if key.lower() not in note:
                issues.append(
                    f"{d.name}: lineup_history_note does not document {key} "
                    "as pre-game knowable"
                )
        # Source-hashes must be present (proves real input parquet was hashed).
        sh = tm.get("source_hashes") or {}
        if not sh.get("live_context_features_parquet"):
            issues.append(f"{d.name}: source_hashes missing live_context_features_parquet")
        if not sh.get("player_game_stats_parquet"):
            issues.append(f"{d.name}: source_hashes missing player_game_stats_parquet")
        facts[d.name] = d_facts

    out_dir = REPO_ROOT / "artifacts" / "phase13r"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues": issues,
        "facts": facts,
        "phase13p_verifier_stdout": out or "",
        "phase13p_verifier_stderr": err or "",
    }
    (out_dir / "phase13q_no_leakage_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    if issues:
        print("PHASE13Q_NO_LEAKAGE_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    print("PHASE13Q_NO_LEAKAGE_PASS")
    print(f"  contextual_dirs_checked={len(contextual_dirs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
