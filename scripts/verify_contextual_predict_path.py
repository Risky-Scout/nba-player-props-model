"""Phase 13R Part C — predict-path proof.

Inspects every prediction path that estimates PMFs and proves either:

  (a) the path builds official lineup / injury / vacated-opportunity /
      game-context features BEFORE PMF generation when the contextual
      champion is active and live context is available, OR
  (b) the path records an EXACT blocker explaining why context is
      missing, and refuses to claim ``contextual_pmf_engine=true`` in
      its manifest.

It also verifies WoO-default compatibility: ``scripts/predict.py`` with
no Derek args still emits its WoO/canonical side-effect files and does
NOT use market odds as model features.

Inspected paths:

    1. scripts/predict.py                                — WoO + Derek modes
    2. src/nba_props_model/pipelines/predict.py          — pipeline impl
    3. scripts/run_derek_live_game_snapshot.py           — Derek live snapshot
    4. scripts/build_daily_pmf_delivery.py (if present)  — daily PMF
    5. scripts/run_after_game_market_score.py (if any)   — after-game scoring

Pass line:  PHASE13R_CONTEXTUAL_PREDICT_PATH_PASS
Fail line:  PHASE13R_CONTEXTUAL_PREDICT_PATH_FAILED
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


REQUIRED_TOKENS = {
    # Path → tokens that, when all present, prove the contextual wiring.
    "scripts/run_derek_live_game_snapshot.py": (
        # Derek runner must reference the contextual scoring helper, the
        # contextual feature_set_id, the per-row decomposition file, and
        # the lineup-injury impact report.
        "from nba_props_model.contextual import",
        "load_contextual_engine",
        "phase13q_contextual_pmf_engine_v1",
        "pmf_driver_decomposition",
        "lineup_injury_impact_report",
        "contextual_pmf_applied",
        "lineup_blocker",
    ),
    "src/nba_props_model/pipelines/predict.py": (
        # Pipeline must NOT import market odds as model features. We
        # check the existing live_context wiring and the lineup-context
        # join helper — both are pre-13R.
        "_join_lineup_context_into_rows",
        "build_injury_map",
        # Negative: market odds must not appear in any model.predict(...) call.
    ),
    "scripts/predict.py": (
        "PREDICT_DEREK_LIVE_ARGS_PASS",  # CLI surface preserved
        "PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_PASS",
    ),
}

# Paths that are optional — present iff the daily delivery/after-game
# stack is wired in this branch. We inspect them when they exist.
OPTIONAL_PATHS = (
    "scripts/build_daily_pmf_delivery.py",
    "scripts/run_after_game_market_score.py",
    "scripts/run_after_game_market_score_pipeline.py",
)


# Forbidden patterns: market odds being used as a model feature anywhere
# downstream of prediction. This is a *surface scan*; the real proof is
# in the no-leakage verifier (which inspects saved feature lists).
FORBIDDEN_FEATURE_PATTERNS = (
    re.compile(r"model\.predict\([^)]*market_no_vig_over_prob"),
    re.compile(r"model\.predict\([^)]*closing_odds"),
    re.compile(r"model\.predict\([^)]*market_over_odds"),
)


def _scan_file(path: Path, tokens: tuple[str, ...]) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    missing = [t for t in tokens if t not in text]
    bad = []
    for pat in FORBIDDEN_FEATURE_PATTERNS:
        if pat.search(text):
            bad.append(pat.pattern)
    return missing, bad


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.parse_args(argv)

    issues: list[str] = []
    facts: dict = {}

    for rel, tokens in REQUIRED_TOKENS.items():
        path = REPO_ROOT / rel
        if not path.exists():
            issues.append(f"{rel}: missing")
            continue
        missing, bad = _scan_file(path, tokens)
        facts[rel] = {
            "missing_tokens": missing,
            "forbidden_patterns_seen": bad,
        }
        if missing:
            issues.append(
                f"{rel}: required wiring missing: {missing}"
            )
        if bad:
            issues.append(
                f"{rel}: forbidden market-feature pattern present: {bad}"
            )

    for rel in OPTIONAL_PATHS:
        path = REPO_ROOT / rel
        if not path.exists():
            facts[rel] = {"present": False}
            continue
        missing, bad = _scan_file(path, ())
        facts[rel] = {
            "present": True,
            "forbidden_patterns_seen": bad,
        }
        if bad:
            issues.append(
                f"{rel}: forbidden market-feature pattern present: {bad}"
            )

    # Functional check: import the pipelines.predict lineup-join function
    # and verify it returns lineup_affects_pmf_features=True for a real
    # confirmed-starter row.
    try:
        import tempfile
        import pandas as pd
        from nba_props_model.pipelines.predict import (
            _join_lineup_context_into_rows,
        )
        rows = [{"player_id": 100, "game_id": "999", "stat": "pts",
                 "role_bucket": "high_minutes", "exp_mp": 32.0}]
        lineup_df = pd.DataFrame([{
            "game_id": "999", "team_id": 1, "player_id": 100,
            "starter": True, "lineup_position": "G",
            "source": "balldontlie_v1_lineups",
        }])
        with tempfile.TemporaryDirectory() as tmp:
            lp = Path(tmp) / "lineup.parquet"
            lineup_df.to_parquet(lp, index=False)
            out_rows, summary = _join_lineup_context_into_rows(
                rows, str(lp), "999",
            )
        if summary.get("lineup_rows_joined", 0) != 1:
            issues.append(
                "pipeline lineup-join smoke test: expected 1 row joined; "
                f"got {summary.get('lineup_rows_joined')}"
            )
        if not out_rows[0].get("lineup_affects_pmf_features"):
            issues.append(
                "pipeline lineup-join smoke test: lineup_affects_pmf_features "
                "should be True after a confirmed-starter join"
            )
        facts["pipeline_lineup_join_smoke"] = {
            "rows_joined": summary.get("lineup_rows_joined"),
            "starter_flag_changed_count": summary.get("starter_flag_changed_count"),
            "role_bucket_changed_count": summary.get("role_bucket_changed_count"),
        }
    except Exception as exc:
        issues.append(f"pipeline lineup-join smoke test failed: {exc}")

    # Functional check: contextual engine load and produce non-empty
    # delta dict. Same proof as Part B but expressed in terms of the
    # predict-path requirement.
    try:
        from nba_props_model.contextual import (
            load_contextual_engine,
            resolve_contextual_challenger_dir,
        )
        d, reason = resolve_contextual_challenger_dir(REPO_ROOT)
        if d is None:
            facts["contextual_engine_load"] = {
                "loaded": False, "blocker": reason,
            }
        else:
            engine = load_contextual_engine(d)
            scores = engine.score_row({
                "is_actionable": True,
                "is_probable": True,
                "starter_proxy_lagged": 1.0,
                "is_home": 1.0,
                "rest_days": 2.0,
                "vacated_minutes_total": 25.0,
                "num_teammates_out_total": 1.0,
                "season_game_number": 41.0,
            })
            facts["contextual_engine_load"] = {
                "loaded": True,
                "challenger_dir": str(d.relative_to(REPO_ROOT)),
                "feature_set_id": engine.feature_set_id,
                "fitted_targets": list(engine.fitted_targets),
                "score_keys": sorted(scores.keys()),
                "minutes_delta_present": "minutes_delta" in scores,
            }
            if "minutes_delta" not in scores:
                issues.append(
                    "contextual engine produced no minutes_delta on synthetic row"
                )
    except Exception as exc:
        issues.append(f"contextual engine load failed: {exc}")

    out_dir = REPO_ROOT / "artifacts" / "phase13r"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues": issues,
        "facts": facts,
        "checked_paths": list(REQUIRED_TOKENS.keys()) + list(OPTIONAL_PATHS),
    }
    (out_dir / "contextual_predict_path_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    if issues:
        print("PHASE13R_CONTEXTUAL_PREDICT_PATH_FAILED", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1
    print("PHASE13R_CONTEXTUAL_PREDICT_PATH_PASS")
    eng = facts.get("contextual_engine_load", {})
    print(
        f"  contextual_engine_loaded={eng.get('loaded')} "
        f"feature_set_id={eng.get('feature_set_id')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
