"""Phase 13S Parts I + J — deployment + Derek interpretability verifier.

Two coupled checks:

  1. PHASE13S_ALL_PREDICT_PATHS_DIRECT_CONTEXTUAL_PASS — every PMF
     estimation path either uses the Phase 13S contextual engine or
     records an exact blocker.

  2. PHASE13S_DEREK_INTERPRETABILITY_OUTPUTS_PASS — fixture test that
     ``_apply_contextual_scoring`` produces:

         pmf_driver_decomposition.{csv,parquet,md}
         lineup_injury_impact_report.{json,md}
         direct_lineup_impact_report.{json,md}
         contextual_feature_audit.{csv,parquet}
         snapshot_comparison.csv  (when prior snapshot is supplied)
         input_change_report.{json,md} (when prior snapshot is supplied)
         game_context.{csv,parquet}

     and writes a non-zero ``contextual_minutes_delta`` to a row
     where the synthetic input has BDL-confirmed starter status.
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
    "scripts/run_derek_live_game_snapshot.py": (
        "_apply_contextual_scoring",
        "load_contextual_engine",
        "phase13s_",
        "apply_direct_lineup_overlay",
        "pmf_driver_decomposition",
        "lineup_injury_impact_report",
        "direct_lineup_impact_report",
        "contextual_feature_audit",
        "contextual_blocker",
    ),
    "scripts/predict.py": (
        "PREDICT_DEREK_LIVE_ARGS_PASS",
    ),
    "src/nba_props_model/pipelines/predict.py": (
        "_join_lineup_context_into_rows",
        "build_injury_map",
    ),
    "src/nba_props_model/features/direct_lineup_context.py": (
        "DIRECT_LINEUP_FEATURE_SET_ID",
        "apply_direct_lineup_overlay",
        "STARTER_MIN_THRESHOLD",
    ),
    "src/nba_props_model/features/lineup_interactions.py": (
        "aggregate_team_lineup",
        "player_in_lineup_interactions",
    ),
    "scripts/build_daily_pmf_delivery.py": (
        "model_version",
    ),
}

FORBIDDEN_FEATURE_PATTERNS = (
    re.compile(r"model\.predict\([^)]*market_no_vig_over_prob"),
    re.compile(r"model\.predict\([^)]*closing_odds"),
    re.compile(r"model\.predict\([^)]*market_over_odds"),
    re.compile(r"model\.predict\([^)]*market_under_odds"),
)


def _scan(path: Path, must_contain):
    text = path.read_text(encoding="utf-8")
    missing = [t for t in must_contain if t not in text]
    bad = [pat.pattern for pat in FORBIDDEN_FEATURE_PATTERNS if pat.search(text)]
    return missing, bad


def _all_predict_paths(facts: dict) -> list[str]:
    issues: list[str] = []
    for rel, tokens in PATHS.items():
        path = REPO_ROOT / rel
        if not path.exists():
            issues.append(f"{rel}: missing")
            facts[rel] = {"present": False}
            continue
        missing, bad = _scan(path, tokens)
        facts[rel] = {
            "present": True,
            "missing_tokens": missing,
            "forbidden_market_patterns": bad,
        }
        if missing:
            issues.append(f"{rel}: missing tokens {missing}")
        if bad:
            issues.append(f"{rel}: market-feature pattern present {bad}")

    pointer_path = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    if not pointer_path.exists():
        issues.append("champion_pointer.json missing")
    else:
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        required_fields = (
            "feature_set_id",
            "direct_lineup_pmf_driver",
            "contextual_pmf_engine",
            "official_lineup_features_enabled",
            "injury_availability_features_enabled",
            "vacated_opportunity_features_enabled",
            "lineup_composition_features_enabled",
            "game_context_features_enabled",
            "direct_lineup_pmf_sensitivity_verified",
            "lineup_composition_pmf_sensitivity_verified",
            "actionability_sensitivity_verified",
            "market_only_edge_sensitivity_verified",
            "contextual_trained_through_date",
            "contextual_calibrated_through_date",
            "validation_report_path",
            "promotion_decision_id",
        )
        missing_fields = [f for f in required_fields if f not in pointer]
        facts["champion_pointer"] = {
            "feature_set_id": pointer.get("feature_set_id"),
            "missing_required_fields": missing_fields,
        }
        if missing_fields:
            issues.append(
                f"champion_pointer.json missing required fields: {missing_fields}"
            )
        if pointer.get("feature_set_id") != "phase13s_direct_lineup_injury_pmf_driver_v1":
            issues.append(
                f"champion_pointer.feature_set_id="
                f"{pointer.get('feature_set_id')!r} is not the Phase 13S "
                "direct-lineup driver"
            )
    return issues


def _derek_outputs(facts: dict) -> list[str]:
    issues: list[str] = []
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_phase13s_runner",
            REPO_ROOT / "scripts" / "run_derek_live_game_snapshot.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as exc:
        issues.append(f"cannot import Derek runner: {exc}")
        return issues
    if not hasattr(mod, "_apply_contextual_scoring"):
        issues.append("Derek runner missing _apply_contextual_scoring")
        return issues
    if not hasattr(mod, "_write_derek_phase13s_sidecars"):
        issues.append(
            "Derek runner missing _write_derek_phase13s_sidecars helper"
        )
        return issues

    import pandas as pd
    pointer_path = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))

    rows_a = [
        {"player_id": 100, "player_name": "A", "team": "ATL",
         "game_id": "999", "stat": "pts", "line": 25.5, "exp_mp": 30.0,
         "is_actionable": True, "is_probable": True,
         "current_starter": False, "confirmed_starter": False,
         "confirmed_bench": True, "lineup_confirmed": False,
         "is_home": 1.0, "rest_days": 2.0, "is_back_to_back": 0.0,
         "is_three_in_four": 0.0, "season_game_number": 41.0,
         "season_game_number_norm": 0.5, "opponent_team_id_hash": 7.0,
         "starter_proxy_lagged": 0.0, "model_p_over": 0.5,
         "market_no_vig_over_prob": 0.5,
         "is_confirmed_out": False, "is_inactive": False,
         "is_doubtful": False, "is_questionable": False,
         "injury_status_encoded": 2.0, "availability_status_encoded": 1.0,
         "injury_features_missing": 0.0,
         "num_teammates_out_total": 0.0, "vacated_minutes_total": 0.0,
         "vacated_features_missing": 0.0,
         "num_teammates_out_guard": 0.0, "num_teammates_out_wing": 0.0,
         "num_teammates_out_big": 0.0, "vacated_minutes_guard": 0.0,
         "vacated_minutes_wing": 0.0, "vacated_minutes_big": 0.0,
         "vacated_fga_total": 0.0},
        {"player_id": 101, "player_name": "B", "team": "ATL",
         "game_id": "999", "stat": "pts", "line": 22.5, "exp_mp": 32.0,
         "is_actionable": True, "is_probable": True,
         "current_starter": True, "confirmed_starter": True,
         "confirmed_bench": False, "lineup_confirmed": True,
         "is_home": 1.0, "rest_days": 2.0, "is_back_to_back": 0.0,
         "is_three_in_four": 0.0, "season_game_number": 41.0,
         "season_game_number_norm": 0.5, "opponent_team_id_hash": 7.0,
         "starter_proxy_lagged": 1.0, "model_p_over": 0.5,
         "market_no_vig_over_prob": 0.5,
         "is_confirmed_out": False, "is_inactive": False,
         "is_doubtful": False, "is_questionable": False,
         "injury_status_encoded": 2.0, "availability_status_encoded": 1.0,
         "injury_features_missing": 0.0,
         "num_teammates_out_total": 2.0, "vacated_minutes_total": 50.0,
         "vacated_features_missing": 0.0,
         "num_teammates_out_guard": 1.0, "num_teammates_out_wing": 1.0,
         "num_teammates_out_big": 0.0, "vacated_minutes_guard": 25.0,
         "vacated_minutes_wing": 25.0, "vacated_minutes_big": 0.0,
         "vacated_fga_total": 18.0},
    ]
    sub = pd.DataFrame(rows_a)
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
        try:
            mod._write_derek_phase13s_sidecars(
                sub, contextual_summary=summary, out_root=out_root,
                prior_snapshot_dir=None,
            )
        except Exception as exc:
            issues.append(f"_write_derek_phase13s_sidecars raised: {exc}")
            return issues
        facts["fixture_summary"] = summary

        required_files = (
            "pmf_driver_decomposition.csv",
            "pmf_driver_decomposition.parquet",
            "pmf_driver_decomposition.md",
            "lineup_injury_impact_report.json",
            "lineup_injury_impact_report.md",
            "direct_lineup_impact_report.json",
            "direct_lineup_impact_report.md",
            "contextual_feature_audit.csv",
            "contextual_feature_audit.parquet",
            "game_context.csv",
            "game_context.parquet",
            "input_change_report.json",
            "input_change_report.md",
        )
        for fname in required_files:
            if not (out_root / fname).exists():
                issues.append(f"missing sidecar artifact {fname}")

        if summary.get("feature_set_id") != "phase13s_direct_lineup_injury_pmf_driver_v1":
            issues.append(
                f"summary feature_set_id={summary.get('feature_set_id')!r} "
                "is not Phase 13S"
            )
        # Player A: bench / no vacated; Player B: confirmed starter +
        # vacated minutes. Their minutes deltas must differ.
        d100 = float(sub.loc[sub["player_id"] == 100, "contextual_minutes_delta"].iloc[0])
        d101 = float(sub.loc[sub["player_id"] == 101, "contextual_minutes_delta"].iloc[0])
        facts["fixture_minutes_deltas"] = {"player_100": d100, "player_101": d101}
        if abs(d100 - d101) <= 0.5:
            issues.append(
                "minutes_delta did not differ by > 0.5 min between bench and "
                "confirmed-starter rows in the snapshot fixture"
            )

    return issues


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.parse_args(argv)

    facts: dict = {}
    issues_predict = _all_predict_paths(facts)
    issues_outputs = _derek_outputs(facts)

    out_dir = REPO_ROOT / "artifacts" / "phase13s"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "issues_all_predict_paths": issues_predict,
        "issues_derek_interpretability_outputs": issues_outputs,
        "facts": facts,
    }
    (out_dir / "deployment_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    rc = 0
    if issues_predict:
        print("PHASE13S_ALL_PREDICT_PATHS_DIRECT_CONTEXTUAL_FAILED", file=sys.stderr)
        for i in issues_predict:
            print(f"  - {i}", file=sys.stderr)
        rc = 1
    else:
        print("PHASE13S_ALL_PREDICT_PATHS_DIRECT_CONTEXTUAL_PASS")

    if issues_outputs:
        print("PHASE13S_DEREK_INTERPRETABILITY_OUTPUTS_FAILED", file=sys.stderr)
        for i in issues_outputs:
            print(f"  - {i}", file=sys.stderr)
        rc = 1
    else:
        print("PHASE13S_DEREK_INTERPRETABILITY_OUTPUTS_PASS")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
