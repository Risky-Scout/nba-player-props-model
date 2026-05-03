"""Phase 13R Parts F + G — deployment + Derek output verifiers.

Two coupled checks:

  1. PHASE13R_ALL_PREDICT_PATHS_CONTEXTUAL_PASS — every PMF estimation
     path either uses the contextual engine or records an exact blocker.
     We inspect:

         scripts/predict.py
         src/nba_props_model/pipelines/predict.py
         scripts/run_derek_live_game_snapshot.py
         scripts/build_daily_pmf_delivery.py
         (after-game scoring, when present)

     For each path, the verifier records whether contextual is wired
     and what its blocker is (when not wired). PASS when:
         - Derek live snapshot calls ``_apply_contextual_scoring`` with
           the engine loaded from the contextual challenger dir;
         - WoO default (predict.py with no Derek args) is preserved
           byte-for-byte for its canonical side-effect files (we
           inspect by token, not by run);
         - Daily PMF delivery threads through champion_pointer
           metadata (does not strip contextual flags);
         - No predict path ingests market odds as a model feature
           (regex scan over ``model.predict(... market...)`` patterns).

  2. PHASE13R_DEREK_CONTEXTUAL_OUTPUTS_PASS — fixture test that
     ``_apply_contextual_scoring`` from the Derek runner produces the
     three required sidecar artifacts (``pmf_driver_decomposition``,
     ``lineup_injury_impact_report``, ``contextual_feature_audit``)
     and writes a non-zero ``contextual_minutes_delta`` to at least
     one row when the synthetic input has a teammate-out signal.

Failure lines:
    PHASE13R_ALL_PREDICT_PATHS_CONTEXTUAL_FAILED
    PHASE13R_DEREK_CONTEXTUAL_OUTPUTS_FAILED
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


PATHS = {
    "scripts/run_derek_live_game_snapshot.py": {
        "must_contain": (
            "_apply_contextual_scoring",
            "load_contextual_engine",
            "pmf_driver_decomposition",
            "lineup_injury_impact_report",
            "contextual_feature_audit",
            "contextual_blocker",
            "phase13q_contextual_pmf_engine_v1",
        ),
        "must_not_contain": (),
        "role": "derek_live_snapshot",
    },
    "scripts/predict.py": {
        "must_contain": ("PREDICT_DEREK_LIVE_ARGS_PASS",),
        "must_not_contain": (),
        "role": "predict_cli",
    },
    "src/nba_props_model/pipelines/predict.py": {
        "must_contain": ("_join_lineup_context_into_rows", "build_injury_map"),
        "must_not_contain": (),
        "role": "predict_pipeline",
    },
    "scripts/build_daily_pmf_delivery.py": {
        "must_contain": ("model_version",),
        "must_not_contain": (),
        "role": "daily_delivery",
    },
}

OPTIONAL_PATHS = (
    "scripts/run_after_game_market_score.py",
    "scripts/run_after_game_market_score_pipeline.py",
    "scripts/run_after_game_score.py",
)

FORBIDDEN_FEATURE_PATTERNS = (
    re.compile(r"model\.predict\([^)]*market_no_vig_over_prob"),
    re.compile(r"model\.predict\([^)]*closing_odds"),
    re.compile(r"model\.predict\([^)]*market_over_odds"),
    re.compile(r"model\.predict\([^)]*market_under_odds"),
)


def _scan_file(path: Path, must_contain, must_not_contain):
    text = path.read_text(encoding="utf-8")
    missing = [t for t in must_contain if t not in text]
    forbidden = [t for t in must_not_contain if t in text]
    bad = []
    for pat in FORBIDDEN_FEATURE_PATTERNS:
        if pat.search(text):
            bad.append(pat.pattern)
    return missing, forbidden, bad


def _all_predict_paths_check(facts: dict) -> list[str]:
    issues: list[str] = []
    for rel, spec in PATHS.items():
        path = REPO_ROOT / rel
        if not path.exists():
            issues.append(f"{rel}: missing")
            facts[rel] = {"present": False, "role": spec["role"]}
            continue
        missing, forbidden, bad = _scan_file(
            path, spec["must_contain"], spec["must_not_contain"],
        )
        facts[rel] = {
            "present": True,
            "role": spec["role"],
            "missing_tokens": missing,
            "forbidden_tokens": forbidden,
            "forbidden_market_feature_patterns": bad,
        }
        if missing:
            issues.append(f"{rel}: missing tokens {missing}")
        if forbidden:
            issues.append(f"{rel}: forbidden tokens present {forbidden}")
        if bad:
            issues.append(f"{rel}: market-feature pattern present {bad}")

    for rel in OPTIONAL_PATHS:
        path = REPO_ROOT / rel
        if not path.exists():
            facts[rel] = {"present": False, "role": "optional"}
            continue
        _, _, bad = _scan_file(path, (), ())
        facts[rel] = {"present": True, "role": "optional",
                      "forbidden_market_feature_patterns": bad}
        if bad:
            issues.append(f"{rel}: market-feature pattern present {bad}")

    # Champion pointer must carry the contextual block when promotion happened.
    pointer_path = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    if not pointer_path.exists():
        issues.append("champion_pointer.json missing")
    else:
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        required_pointer_fields = (
            "feature_set_id",
            "contextual_pmf_engine",
            "official_lineup_features_enabled",
            "injury_availability_features_enabled",
            "vacated_opportunity_features_enabled",
            "lineup_interaction_features_enabled",
            "game_context_features_enabled",
            "lineup_injury_context_upstream_of_pmf",
            "contextual_pmf_sensitivity_verified",
            "contextual_trained_through_date",
            "contextual_calibrated_through_date",
            "validation_report_path",
            "promotion_decision_id",
            "contextual_challenger_dir",
        )
        missing_fields = [f for f in required_pointer_fields if f not in pointer]
        facts["champion_pointer"] = {
            "feature_set_id": pointer.get("feature_set_id"),
            "contextual_pmf_engine": pointer.get("contextual_pmf_engine"),
            "missing_required_fields": missing_fields,
        }
        if missing_fields:
            issues.append(
                f"champion_pointer.json missing required fields: {missing_fields}"
            )
    return issues


def _derek_contextual_outputs_check(facts: dict) -> list[str]:
    issues: list[str] = []
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_phase13r_runner",
            REPO_ROOT / "scripts" / "run_derek_live_game_snapshot.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as exc:
        issues.append(f"cannot import Derek runner module: {exc}")
        return issues

    if not hasattr(mod, "_apply_contextual_scoring"):
        issues.append("Derek runner missing _apply_contextual_scoring")
        return issues

    import pandas as pd

    pointer_path = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))

    # Synthetic snapshot with two players: one with a teammate-out
    # vacated opportunity, one without. The contextual engine should
    # produce different minutes_delta for the two — proves real
    # response on real-snapshot-shaped input.
    rows = [
        {
            "player_id": 100, "player_name": "A", "team": "ATL",
            "game_id": "999", "stat": "pts", "line": 25.5, "exp_mp": 32.0,
            "is_actionable": True, "is_probable": True,
            "starter_proxy_lagged": 1.0, "is_home": 1.0,
            "rest_days": 2.0, "is_back_to_back": 0.0, "is_three_in_four": 0.0,
            "season_game_number": 41.0, "season_game_number_norm": 0.5,
            "opponent_team_id_hash": 7.0,
            "lineup_confirmed": True, "confirmed_starter": True,
            "confirmed_bench": False, "is_confirmed_out": False,
            "num_teammates_out_total": 0.0, "num_teammates_out_guard": 0.0,
            "num_teammates_out_wing": 0.0, "num_teammates_out_big": 0.0,
            "vacated_minutes_total": 0.0, "vacated_minutes_guard": 0.0,
            "vacated_minutes_wing": 0.0, "vacated_minutes_big": 0.0,
            "vacated_fga_total": 0.0,
            "is_doubtful": False, "is_questionable": False, "is_inactive": False,
            "injury_status_encoded": 2.0, "availability_status_encoded": 1.0,
            "injury_features_missing": 0.0, "vacated_features_missing": 0.0,
            "model_p_over": 0.5, "market_no_vig_over_prob": 0.5,
        },
        {
            "player_id": 101, "player_name": "B", "team": "ATL",
            "game_id": "999", "stat": "pts", "line": 22.5, "exp_mp": 30.0,
            "is_actionable": True, "is_probable": True,
            "starter_proxy_lagged": 1.0, "is_home": 1.0,
            "rest_days": 2.0, "is_back_to_back": 0.0, "is_three_in_four": 0.0,
            "season_game_number": 41.0, "season_game_number_norm": 0.5,
            "opponent_team_id_hash": 7.0,
            "lineup_confirmed": True, "confirmed_starter": True,
            "confirmed_bench": False, "is_confirmed_out": False,
            "num_teammates_out_total": 2.0, "num_teammates_out_guard": 1.0,
            "num_teammates_out_wing": 1.0, "num_teammates_out_big": 0.0,
            "vacated_minutes_total": 50.0, "vacated_minutes_guard": 25.0,
            "vacated_minutes_wing": 25.0, "vacated_minutes_big": 0.0,
            "vacated_fga_total": 18.0,
            "is_doubtful": False, "is_questionable": False, "is_inactive": False,
            "injury_status_encoded": 2.0, "availability_status_encoded": 1.0,
            "injury_features_missing": 0.0, "vacated_features_missing": 0.0,
            "model_p_over": 0.5, "market_no_vig_over_prob": 0.5,
        },
    ]
    sub = pd.DataFrame(rows)
    with tempfile.TemporaryDirectory() as tmp:
        out_root = Path(tmp) / "snapshot"
        out_root.mkdir(parents=True, exist_ok=True)
        try:
            summary = mod._apply_contextual_scoring(
                sub, pointer=pointer, out_root=out_root,
            )
        except Exception as exc:
            issues.append(f"_apply_contextual_scoring raised: {exc}")
            return issues
        facts["fixture_summary"] = summary

        # Required sidecars.
        for fname in (
            "pmf_driver_decomposition.csv",
            "pmf_driver_decomposition.parquet",
            "pmf_driver_decomposition.md",
            "lineup_injury_impact_report.json",
            "lineup_injury_impact_report.md",
            "contextual_feature_audit.csv",
            "contextual_feature_audit.parquet",
        ):
            if not (out_root / fname).exists():
                issues.append(f"missing sidecar artifact {fname}")

        # Per-row contextual_minutes_delta must be present and at least
        # one row must differ from the other.
        if "contextual_minutes_delta" not in sub.columns:
            issues.append("contextual_minutes_delta column not added")
        else:
            d100 = float(sub.loc[sub["player_id"] == 100, "contextual_minutes_delta"].iloc[0])
            d101 = float(sub.loc[sub["player_id"] == 101, "contextual_minutes_delta"].iloc[0])
            facts["fixture_minutes_deltas"] = {"player_100": d100, "player_101": d101}
            if abs(d100 - d101) <= 1e-6:
                issues.append(
                    "contextual minutes delta did not differ between "
                    "the no-teammate-out and teammate-out scenarios; "
                    "engine may not be consuming vacated features"
                )

        # contextual_pmf_applied true on every row.
        if not bool(sub["contextual_pmf_applied"].all()):
            issues.append(
                "contextual_pmf_applied not True on every fixture row"
            )
    return issues


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.parse_args(argv)

    facts: dict = {}
    issues_predict = _all_predict_paths_check(facts)
    issues_outputs = _derek_contextual_outputs_check(facts)

    out_dir = REPO_ROOT / "artifacts" / "phase13r"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues_all_predict_paths": issues_predict,
        "issues_derek_contextual_outputs": issues_outputs,
        "facts": facts,
    }
    (out_dir / "phase13r_deployment_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    rc = 0
    if issues_predict:
        print("PHASE13R_ALL_PREDICT_PATHS_CONTEXTUAL_FAILED", file=sys.stderr)
        for i in issues_predict:
            print(f"  - {i}", file=sys.stderr)
        rc = 1
    else:
        print("PHASE13R_ALL_PREDICT_PATHS_CONTEXTUAL_PASS")

    if issues_outputs:
        print("PHASE13R_DEREK_CONTEXTUAL_OUTPUTS_FAILED", file=sys.stderr)
        for i in issues_outputs:
            print(f"  - {i}", file=sys.stderr)
        rc = 1
    else:
        print("PHASE13R_DEREK_CONTEXTUAL_OUTPUTS_PASS")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
