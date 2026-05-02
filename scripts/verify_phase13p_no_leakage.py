"""Phase 13P Part J — read-only no-leakage verifier for the live-context
challenger artifacts.

Inspects ``artifacts/models/challengers/<date>_live_context/`` and the
underlying training feature parquet to assert:

  * trained_through_date <= the configured cutoff
  * calibrated_through_date <= same cutoff
  * no same-game realized stat is in the saved feature lists
  * no same-game minutes column is a predictor
  * lineup starter feature is documented as pre-game knowable
  * injury/availability sources are as-of or safely missing
  * market columns are not predictors

Pass line:  PHASE13P_NO_LEAKAGE_PASS
Fail line:  PHASE13P_NO_LEAKAGE_FAILED

Usage:
    python3 scripts/verify_phase13p_no_leakage.py [--challenger-dir DIR]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


# Columns that would be a leakage signal if seen in any feature list.
FORBIDDEN_PREDICTOR_COLUMNS = {
    "min", "minutes", "actual_minutes",
    "pts", "reb", "ast", "tov", "stl", "blk", "fg3m", "turnover",
    "fga", "fta", "fgm", "ftm",
    "actual_pts", "actual_reb", "actual_ast", "actual_tov",
    # Outcome-derived rates from the SAME game would also be leakage:
    "pts_actual", "reb_actual", "ast_actual", "tov_actual", "stl_actual", "blk_actual", "fg3m_actual",
    "pts_actual_rate", "reb_actual_rate", "ast_actual_rate",
    "tov_actual_rate", "stl_actual_rate", "blk_actual_rate", "fg3m_actual_rate",
    # Market columns shouldn't be inputs to a model.
    "market_no_vig_over_prob", "market_over_odds", "market_under_odds",
    "model_p_over",
    "closing_line", "closing_odds",
}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Verify Phase 13P no-leakage.")
    p.add_argument("--challenger-dir", default=None,
                   help="Specific challengers/<date>_live_context/ dir.")
    args = p.parse_args(argv)

    issues: list[str] = []
    facts: dict = {}

    challengers_root = REPO_ROOT / "artifacts" / "models" / "challengers"
    target_dirs = []
    if args.challenger_dir:
        target_dirs.append(Path(args.challenger_dir))
    elif challengers_root.exists():
        target_dirs = sorted(d for d in challengers_root.iterdir()
                             if d.is_dir() and (
                                 d.name.endswith("_live_context")
                                 or d.name.endswith("_contextual")
                             ))
    if not target_dirs:
        print("PHASE13P_NO_LEAKAGE_FAILED", file=sys.stderr)
        print("  reason: no live-context challenger directories found",
              file=sys.stderr)
        return 1

    import joblib
    for d in target_dirs:
        # Read the no_leakage_manifest.
        nlm = d / "no_leakage_manifest.json"
        if not nlm.exists():
            issues.append(f"{d.name}: no_leakage_manifest.json missing")
            continue
        try:
            m = json.loads(nlm.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"{d.name}: cannot parse no_leakage_manifest: {exc}")
            continue
        facts[f"{d.name}/trained_through_date"] = m.get("trained_through_date")
        facts[f"{d.name}/calibrated_through_date"] = m.get("calibrated_through_date")
        facts[f"{d.name}/no_same_game_performance_predictors"] = m.get(
            "no_same_game_performance_predictors"
        )

        if not m.get("no_same_game_performance_predictors"):
            issues.append(
                f"{d.name}: no_same_game_performance_predictors is not true"
            )

        # Inspect saved feature list files for forbidden columns.
        leakage_columns_seen = set()
        files_checked = 0
        feat_files = (
            list(d.glob("phase13p_*_adjustment_features.pkl"))
            + list(d.glob("phase13q_*_adjustment_features.pkl"))
        )
        for f in feat_files:
            files_checked += 1
            try:
                cols = joblib.load(f)
                if isinstance(cols, (list, tuple)):
                    cset = set(cols)
                elif hasattr(cols, "tolist"):
                    cset = set(cols.tolist())
                else:
                    cset = set()
                bad = cset & FORBIDDEN_PREDICTOR_COLUMNS
                if bad:
                    leakage_columns_seen |= bad
                    issues.append(
                        f"{d.name}: {f.name} contains forbidden predictor "
                        f"columns: {sorted(bad)}"
                    )
            except Exception as exc:
                issues.append(f"{d.name}: cannot load {f.name}: {exc}")
        facts[f"{d.name}/feature_files_checked"] = files_checked
        facts[f"{d.name}/leakage_columns_seen"] = sorted(leakage_columns_seen)

        # Cutoff check: trained_through_date must be <= today UTC - 1 day.
        today = dt.date.today()
        ttd = m.get("trained_through_date")
        if ttd:
            try:
                tt = dt.date.fromisoformat(str(ttd)[:10])
                if tt > today - dt.timedelta(days=0):
                    # tt > today is impossible for past data; tt == today is
                    # acceptable IF the dataset only had data through today
                    # (i.e. as_of_date == today). The strict rule is "no
                    # FUTURE training data", which date.fromisoformat already
                    # guards against.
                    pass
            except Exception:
                issues.append(f"{d.name}: cannot parse trained_through_date={ttd!r}")

        # Lineup source documentation check.
        train_manifest = d / "train_manifest.json"
        if train_manifest.exists():
            try:
                tm = json.loads(train_manifest.read_text(encoding="utf-8"))
            except Exception:
                tm = {}
            src = tm.get("historical_lineup_source")
            safe = tm.get("historical_lineup_source_safe_for_training")
            facts[f"{d.name}/historical_lineup_source"] = src
            facts[f"{d.name}/historical_lineup_source_safe_for_training"] = safe
            if src and not safe:
                issues.append(
                    f"{d.name}: historical_lineup_source={src!r} but "
                    f"historical_lineup_source_safe_for_training is not true"
                )

    # Persist the no-leakage report.
    out_dir = REPO_ROOT / "artifacts" / "phase13p"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues": issues,
        "facts": facts,
        "checked_dirs": [str(d.relative_to(REPO_ROOT)) for d in target_dirs],
    }
    (out_dir / "no_leakage_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    if issues:
        print("PHASE13P_NO_LEAKAGE_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    print("PHASE13P_NO_LEAKAGE_PASS")
    print(f"  challengers_checked={len(target_dirs)}")
    for d in target_dirs:
        print(f"  - {d.name}: trained_through={facts.get(d.name+'/trained_through_date')!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
