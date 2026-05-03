"""Phase 13S Part F — direct lineup PMF sensitivity proof.

Six controlled scenarios against the **trained** Phase 13S
challenger artifacts. Failure on the direct-lineup case fails the
phase — the explicit goal of 13S is making official lineup changes
direct trained PMF drivers.

Per-case pass lines:
    PHASE13S_DIRECT_LINEUP_FEATURE_VECTOR_SENSITIVITY_PASS
    PHASE13S_DIRECT_LINEUP_PMF_SENSITIVITY_PASS
    PHASE13S_LINEUP_COMPOSITION_PMF_SENSITIVITY_PASS
    PHASE13S_ACTIONABILITY_SENSITIVITY_PASS
    PHASE13S_MARKET_ONLY_EDGE_SENSITIVITY_PASS
    PHASE13S_NO_INPUT_STABILITY_PASS

If the direct case fails:
    PHASE13S_DIRECT_LINEUP_PMF_DRIVER_FAILED
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _vec_hash(rows, cols):
    payload = []
    for r in rows:
        payload.append("|".join(f"{c}={r.get(c)!r}" for c in cols))
    return hashlib.sha256("\n".join(payload).encode("utf-8")).hexdigest()[:16]


def _delta_hash(deltas):
    payload = "|".join(f"{k}={v:.6f}" for k, v in sorted(deltas.items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _find_phase13s_dir() -> Path | None:
    root = REPO_ROOT / "artifacts" / "models" / "challengers"
    if not root.exists():
        return None
    cands = sorted(d for d in root.iterdir()
                    if d.is_dir() and d.name.endswith("_direct_lineup_contextual"))
    return cands[-1] if cands else None


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--challenger-dir", default=None)
    args = p.parse_args(argv)

    issues_per_case: dict[str, list[str]] = {
        "case_1_direct_lineup": [],
        "case_2_lineup_composition": [],
        "case_3_actionability": [],
        "case_4_teammate_out": [],
        "case_5_market_only": [],
        "case_6_no_change": [],
    }
    case_results: dict = {}

    try:
        from nba_props_model.contextual import load_contextual_engine
        from nba_props_model.features.direct_lineup_context import (
            DIRECT_LINEUP_FEATURE_COLUMNS,
            DIRECT_LINEUP_FEATURE_SET_ID,
            LINEUP_COMPOSITION_FEATURE_COLUMNS,
            PLAYER_IN_LINEUP_INTERACTION_COLUMNS,
            apply_direct_lineup_overlay,
        )
        from nba_props_model.features import live_context as lc
    except Exception as exc:
        print("PHASE13S_DIRECT_LINEUP_PMF_DRIVER_FAILED", file=sys.stderr)
        print(f"  reason: cannot import contextual modules: {exc}",
              file=sys.stderr)
        return 1

    challenger_dir = Path(args.challenger_dir) if args.challenger_dir else _find_phase13s_dir()
    if challenger_dir is None or not challenger_dir.exists():
        print("PHASE13S_DIRECT_LINEUP_PMF_DRIVER_FAILED", file=sys.stderr)
        print("  reason: no <date>_direct_lineup_contextual dir found",
              file=sys.stderr)
        return 1
    try:
        engine = load_contextual_engine(challenger_dir)
    except Exception as exc:
        print("PHASE13S_DIRECT_LINEUP_PMF_DRIVER_FAILED", file=sys.stderr)
        print(f"  reason: engine load failed: {exc}", file=sys.stderr)
        return 1
    if engine.feature_set_id != DIRECT_LINEUP_FEATURE_SET_ID:
        print("PHASE13S_DIRECT_LINEUP_PMF_DRIVER_FAILED", file=sys.stderr)
        print(f"  reason: wrong feature_set_id={engine.feature_set_id!r}",
              file=sys.stderr)
        return 1

    feature_cols_for_hash = (
        list(lc.LINEUP_FEATURE_COLUMNS)
        + list(lc.INJURY_FEATURE_COLUMNS)
        + list(lc.VACATED_OPPORTUNITY_FEATURE_COLUMNS)
        + list(DIRECT_LINEUP_FEATURE_COLUMNS)
        + list(LINEUP_COMPOSITION_FEATURE_COLUMNS)
        + list(PLAYER_IN_LINEUP_INTERACTION_COLUMNS)
        + ["is_home", "rest_days", "is_back_to_back", "is_three_in_four",
           "season_game_number", "season_game_number_norm",
           "opponent_team_id_hash", "starter_proxy_lagged"]
    )

    base_row = {
        "player_id": 100, "game_id": "999", "stat": "pts", "line": 25.5,
        "exp_mp": 30.0, "is_home": 1.0, "rest_days": 2.0,
        "is_back_to_back": 0.0, "is_three_in_four": 0.0,
        "season_game_number": 41.0, "season_game_number_norm": 0.5,
        "opponent_team_id_hash": 7.0, "starter_proxy_lagged": 1.0,
        "model_p_over": 0.5, "market_no_vig_over_prob": 0.5,
        "is_actionable": True, "is_probable": True,
        "is_confirmed_out": False, "is_inactive": False,
        "is_doubtful": False, "is_questionable": False,
        "injury_status_encoded": 2.0, "availability_status_encoded": 1.0,
        "injury_features_missing": 0.0,
        "num_teammates_out_total": 0.0, "num_teammates_out_guard": 0.0,
        "num_teammates_out_wing": 0.0, "num_teammates_out_big": 0.0,
        "vacated_minutes_total": 0.0, "vacated_minutes_guard": 0.0,
        "vacated_minutes_wing": 0.0, "vacated_minutes_big": 0.0,
        "vacated_fga_total": 0.0, "vacated_features_missing": 0.0,
        # Lineup composition baseline (typical NBA team).
        "team_confirmed_starters_count": 4.0,
        "team_confirmed_bench_count": 4.0,
        "team_lineup_num_guards": 2.0,
        "team_lineup_num_wings": 2.0,
        "team_lineup_num_bigs": 2.0,
        "team_lineup_num_high_usage_players": 1.0,
        "team_lineup_num_primary_ballhandlers": 1.0,
        "team_lineup_num_shooters": 2.0,
        "team_lineup_num_rebounders": 2.0,
        "team_lineup_usage_competition_proxy": 3.0,
        "team_lineup_rebound_competition_proxy": 1.5,
        "team_lineup_assist_creation_proxy": 1.0,
        "team_lineup_spacing_proxy": 0.4,
        "team_lineup_turnover_pressure_proxy": 0.3,
        "player_confirmed_with_high_usage_count": 1.0,
        "player_confirmed_with_primary_ballhandler_count": 1.0,
        "player_confirmed_with_big_count": 1.0,
        "player_confirmed_with_shooter_count": 2.0,
        "player_usage_competition_proxy": 0.45,
        "player_rebound_competition_proxy": 0.20,
        "player_assist_target_quality_proxy": 0.18,
        "player_spacing_support_proxy": 0.25,
        "player_onball_burden_proxy": 0.10,
    }

    starter_lineup = [{"game_id": "999", "team_id": 1, "player_id": 100,
                       "starter": True, "lineup_position": "G",
                       "source": "balldontlie_v1_lineups"}]
    bench_lineup = [{"game_id": "999", "team_id": 1, "player_id": 100,
                     "starter": False, "lineup_position": "G",
                     "source": "balldontlie_v1_lineups"}]
    lps = {100: {"prev_game_min": 12.0, "consecutive_starter_streak": 0.0,
                 "recent_starter_rate_5": 0.2}}

    # ── CASE 1: confirmed starter change (BENCH → STARTER) ─────────
    rows_pre = [deepcopy(base_row)]
    rows_post = [deepcopy(base_row)]
    apply_direct_lineup_overlay(rows_pre, bdl_lineup_rows=bench_lineup,
                                  lagged_player_stats=lps)
    apply_direct_lineup_overlay(rows_post, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    # Inject injury defaults via live_context.
    lc.build_live_context_features(rows_pre, bdl_lineup_rows=bench_lineup,
                                     injury_rows=[], availability_rows=[])
    lc.build_live_context_features(rows_post, bdl_lineup_rows=starter_lineup,
                                     injury_rows=[], availability_rows=[])
    # Re-apply overlay AFTER live_context to ensure direct-lineup wins.
    apply_direct_lineup_overlay(rows_pre, bdl_lineup_rows=bench_lineup,
                                  lagged_player_stats=lps)
    apply_direct_lineup_overlay(rows_post, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    h_pre = _vec_hash(rows_pre, feature_cols_for_hash)
    h_post = _vec_hash(rows_post, feature_cols_for_hash)
    deltas_pre = engine.score_row(rows_pre[0])
    deltas_post = engine.score_row(rows_post[0])
    pmf_mean_pre = max(0.0, base_row["exp_mp"] + (deltas_pre.get("minutes_delta") or 0.0))
    pmf_mean_post = max(0.0, base_row["exp_mp"] + (deltas_post.get("minutes_delta") or 0.0))
    case_results["case_1_direct_lineup"] = {
        "feature_vector_hash_pre": h_pre,
        "feature_vector_hash_post": h_post,
        "feature_vectors_changed": h_pre != h_post,
        "minutes_delta_pre": deltas_pre.get("minutes_delta"),
        "minutes_delta_post": deltas_post.get("minutes_delta"),
        "abs_diff_minutes_delta": abs(
            (deltas_post.get("minutes_delta") or 0.0)
            - (deltas_pre.get("minutes_delta") or 0.0)
        ),
        "pmf_mean_pre": pmf_mean_pre,
        "pmf_mean_post": pmf_mean_post,
        "pmf_mean_shift": pmf_mean_post - pmf_mean_pre,
    }
    if h_pre == h_post:
        issues_per_case["case_1_direct_lineup"].append(
            "feature vector unchanged when current_starter flipped"
        )
    if abs(
        (deltas_post.get("minutes_delta") or 0.0)
        - (deltas_pre.get("minutes_delta") or 0.0)
    ) <= 0.5:
        issues_per_case["case_1_direct_lineup"].append(
            "trained minutes adjustment moved by <= 0.5 minute when "
            "current_starter flipped from bench to starter — direct "
            "lineup is NOT a trained PMF driver"
        )

    # ── CASE 2: lineup composition change (same player remains active) ──
    rows_a = [deepcopy(base_row)]
    rows_b = [deepcopy(base_row)]
    rows_b[0]["team_lineup_num_high_usage_players"] = 3.0
    rows_b[0]["team_lineup_usage_competition_proxy"] = 5.0
    rows_b[0]["player_confirmed_with_high_usage_count"] = 3.0
    rows_b[0]["player_usage_competition_proxy"] = 0.85
    apply_direct_lineup_overlay(rows_a, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    apply_direct_lineup_overlay(rows_b, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    da = engine.score_row(rows_a[0])
    db = engine.score_row(rows_b[0])
    case_results["case_2_lineup_composition"] = {
        "team_lineup_num_high_usage_players_a": rows_a[0]["team_lineup_num_high_usage_players"],
        "team_lineup_num_high_usage_players_b": rows_b[0]["team_lineup_num_high_usage_players"],
        "minutes_delta_a": da.get("minutes_delta"),
        "minutes_delta_b": db.get("minutes_delta"),
        "abs_diff_minutes_delta": abs(
            (db.get("minutes_delta") or 0.0)
            - (da.get("minutes_delta") or 0.0)
        ),
    }
    if abs(
        (db.get("minutes_delta") or 0.0)
        - (da.get("minutes_delta") or 0.0)
    ) <= 1e-6:
        issues_per_case["case_2_lineup_composition"].append(
            "trained model did not respond to lineup composition change"
        )

    # ── CASE 3: player ruled out → not actionable ──────────────────
    rows_inj = [deepcopy(base_row)]
    apply_direct_lineup_overlay(rows_inj, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    lc.build_live_context_features(rows_inj, bdl_lineup_rows=starter_lineup,
                                     injury_rows=[{"player_id": 100, "current_status": "out"}],
                                     availability_rows=[])
    apply_direct_lineup_overlay(rows_inj, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    case_results["case_3_actionability"] = {
        "is_actionable": rows_inj[0].get("is_actionable"),
        "is_confirmed_out": rows_inj[0].get("is_confirmed_out"),
        "injury_lineup_conflict": rows_inj[0].get("injury_lineup_conflict"),
    }
    if rows_inj[0].get("is_actionable"):
        issues_per_case["case_3_actionability"].append(
            "out-status row remained actionable"
        )

    # ── CASE 4: teammate late injury ───────────────────────────────
    rows_q = [deepcopy(base_row)]
    rows_l = [deepcopy(base_row)]
    apply_direct_lineup_overlay(rows_q, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    apply_direct_lineup_overlay(rows_l, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    rows_l[0]["num_teammates_out_total"] = 2.0
    rows_l[0]["num_teammates_out_guard"] = 1.0
    rows_l[0]["num_teammates_out_wing"] = 1.0
    rows_l[0]["vacated_minutes_total"] = 50.0
    rows_l[0]["vacated_minutes_guard"] = 25.0
    rows_l[0]["vacated_minutes_wing"] = 25.0
    rows_l[0]["vacated_fga_total"] = 18.0
    dq = engine.score_row(rows_q[0])
    dl = engine.score_row(rows_l[0])
    case_results["case_4_teammate_out"] = {
        "minutes_delta_quiet": dq.get("minutes_delta"),
        "minutes_delta_loaded": dl.get("minutes_delta"),
        "abs_diff_minutes_delta": abs(
            (dl.get("minutes_delta") or 0.0)
            - (dq.get("minutes_delta") or 0.0)
        ),
    }
    if abs(
        (dl.get("minutes_delta") or 0.0)
        - (dq.get("minutes_delta") or 0.0)
    ) <= 1e-6:
        issues_per_case["case_4_teammate_out"].append(
            "trained model did not respond to teammate-out vacated opportunity"
        )

    # ── CASE 5: market-only ────────────────────────────────────────
    rows_m1 = [deepcopy(base_row)]
    rows_m2 = [deepcopy(base_row)]
    rows_m2[0]["market_no_vig_over_prob"] = 0.6
    apply_direct_lineup_overlay(rows_m1, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    apply_direct_lineup_overlay(rows_m2, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    h_m1 = _vec_hash(rows_m1, feature_cols_for_hash)
    h_m2 = _vec_hash(rows_m2, feature_cols_for_hash)
    dm1 = engine.score_row(rows_m1[0])
    dm2 = engine.score_row(rows_m2[0])
    case_results["case_5_market_only"] = {
        "feature_vectors_equal": h_m1 == h_m2,
        "delta_hash_m1": _delta_hash(dm1),
        "delta_hash_m2": _delta_hash(dm2),
    }
    if h_m1 != h_m2:
        issues_per_case["case_5_market_only"].append(
            "market change leaked into feature vector"
        )
    if _delta_hash(dm1) != _delta_hash(dm2):
        issues_per_case["case_5_market_only"].append(
            "market change altered trained-model deltas"
        )

    # ── CASE 6: no input change ────────────────────────────────────
    rows_a6 = [deepcopy(base_row)]
    rows_b6 = [deepcopy(base_row)]
    apply_direct_lineup_overlay(rows_a6, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    apply_direct_lineup_overlay(rows_b6, bdl_lineup_rows=starter_lineup,
                                  lagged_player_stats=lps)
    h_a6 = _vec_hash(rows_a6, feature_cols_for_hash)
    h_b6 = _vec_hash(rows_b6, feature_cols_for_hash)
    da6 = engine.score_row(rows_a6[0])
    db6 = engine.score_row(rows_b6[0])
    case_results["case_6_no_change"] = {
        "feature_vectors_equal": h_a6 == h_b6,
        "delta_hash_a": _delta_hash(da6),
        "delta_hash_b": _delta_hash(db6),
    }
    if h_a6 != h_b6:
        issues_per_case["case_6_no_change"].append(
            "identical inputs produced different feature vectors"
        )
    if _delta_hash(da6) != _delta_hash(db6):
        issues_per_case["case_6_no_change"].append(
            "identical inputs produced different deltas"
        )

    out_dir = REPO_ROOT / "artifacts" / "phase13s"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "feature_set_id": engine.feature_set_id,
        "challenger_dir": str(challenger_dir.relative_to(REPO_ROOT)),
        "issues_per_case": issues_per_case,
        "case_results": case_results,
    }
    (out_dir / "direct_lineup_pmf_sensitivity.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    any_failure = False

    def _emit(case_keys, pass_line, fail_line):
        nonlocal any_failure
        case_issues = []
        for k in case_keys:
            case_issues.extend(issues_per_case.get(k, []))
        if case_issues:
            any_failure = True
            print(fail_line, file=sys.stderr)
            for i in case_issues:
                print(f"  - {i}", file=sys.stderr)
        else:
            print(pass_line)

    _emit(("case_1_direct_lineup", "case_5_market_only", "case_6_no_change"),
          "PHASE13S_DIRECT_LINEUP_FEATURE_VECTOR_SENSITIVITY_PASS",
          "PHASE13S_DIRECT_LINEUP_FEATURE_VECTOR_SENSITIVITY_FAILED")
    _emit(("case_1_direct_lineup",),
          "PHASE13S_DIRECT_LINEUP_PMF_SENSITIVITY_PASS",
          "PHASE13S_DIRECT_LINEUP_PMF_DRIVER_FAILED")
    _emit(("case_2_lineup_composition",),
          "PHASE13S_LINEUP_COMPOSITION_PMF_SENSITIVITY_PASS",
          "PHASE13S_LINEUP_COMPOSITION_PMF_SENSITIVITY_FAILED")
    _emit(("case_3_actionability",),
          "PHASE13S_ACTIONABILITY_SENSITIVITY_PASS",
          "PHASE13S_ACTIONABILITY_SENSITIVITY_FAILED")
    _emit(("case_5_market_only",),
          "PHASE13S_MARKET_ONLY_EDGE_SENSITIVITY_PASS",
          "PHASE13S_MARKET_ONLY_EDGE_SENSITIVITY_FAILED")
    _emit(("case_6_no_change",),
          "PHASE13S_NO_INPUT_STABILITY_PASS",
          "PHASE13S_NO_INPUT_STABILITY_FAILED")

    if any_failure:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
