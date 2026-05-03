"""Phase 13S Part L — Phase 13S no-leakage verifier.

Reads the Phase 13S challenger artifacts and asserts no same-game
realized stats / minutes / market columns are predictors, the
starter proxy is documented as pre-game knowable, and the trained-
through cutoff is sane.

Pass line:  PHASE13S_NO_LEAKAGE_PASS
Fail line:  PHASE13S_NO_LEAKAGE_FAILED
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


FORBIDDEN_PREDICTOR_COLUMNS = {
    "min", "minutes", "actual_minutes",
    "pts", "reb", "ast", "tov", "stl", "blk", "fg3m", "turnover",
    "fga", "fta", "fgm", "ftm",
    "actual_pts", "actual_reb", "actual_ast", "actual_tov",
    "pts_actual", "reb_actual", "ast_actual", "tov_actual",
    "stl_actual", "blk_actual", "fg3m_actual",
    "pts_actual_rate", "reb_actual_rate", "ast_actual_rate",
    "tov_actual_rate", "stl_actual_rate", "blk_actual_rate", "fg3m_actual_rate",
    "market_no_vig_over_prob", "market_over_odds", "market_under_odds",
    "model_p_over",
    "closing_line", "closing_odds",
}


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
        print("PHASE13S_NO_LEAKAGE_FAILED", file=sys.stderr)
        print("  reason: no <date>_direct_lineup_contextual dir found",
              file=sys.stderr)
        return 1

    import joblib
    today = dt.date.today()
    for d in targets:
        nlm = d / "no_leakage_manifest.json"
        tm = d / "train_manifest.json"
        if not nlm.exists() or not tm.exists():
            issues.append(f"{d.name}: missing manifest")
            continue
        m = json.loads(nlm.read_text(encoding="utf-8"))
        t = json.loads(tm.read_text(encoding="utf-8"))
        facts[f"{d.name}/trained_through_date"] = m.get("trained_through_date")
        facts[f"{d.name}/calibrated_through_date"] = m.get("calibrated_through_date")
        facts[f"{d.name}/starter_proxy_used"] = m.get("starter_proxy_used")
        facts[f"{d.name}/starter_proxy_safe_for_training"] = m.get(
            "starter_proxy_safe_for_training")
        if not m.get("no_same_game_performance_predictors"):
            issues.append(f"{d.name}: no_same_game_performance_predictors not true")
        if not m.get("starter_proxy_safe_for_training"):
            issues.append(f"{d.name}: starter_proxy_safe_for_training not true")
        ttd = m.get("trained_through_date")
        if ttd:
            try:
                dt.date.fromisoformat(str(ttd)[:10])
            except Exception:
                issues.append(f"{d.name}: cannot parse trained_through_date={ttd!r}")
        # Inspect saved feature lists for forbidden columns.
        feat_files = list(d.glob("phase13s_*_features.pkl"))
        leakage_seen: set[str] = set()
        for f in feat_files:
            try:
                cols = list(joblib.load(f))
            except Exception as exc:
                issues.append(f"{d.name}: cannot load {f.name}: {exc}")
                continue
            bad = set(cols) & FORBIDDEN_PREDICTOR_COLUMNS
            if bad:
                leakage_seen |= bad
                issues.append(
                    f"{d.name}: {f.name} contains forbidden predictor columns {sorted(bad)}"
                )
        facts[f"{d.name}/feature_files_checked"] = len(feat_files)
        facts[f"{d.name}/leakage_columns_seen"] = sorted(leakage_seen)
        # Cutoff rule documented?
        rule = m.get("asof_cutoff_rule") or ""
        for kw in ("pre-game knowable", "lagged"):
            if kw not in rule.lower():
                issues.append(
                    f"{d.name}: asof_cutoff_rule does not mention {kw!r}"
                )

    out_dir = REPO_ROOT / "artifacts" / "phase13s"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues": issues,
        "facts": facts,
        "checked_dirs": [str(d.relative_to(REPO_ROOT)) for d in targets],
    }
    (out_dir / "no_leakage_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    if issues:
        print("PHASE13S_NO_LEAKAGE_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    print("PHASE13S_NO_LEAKAGE_PASS")
    print(f"  challengers_checked={len(targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
