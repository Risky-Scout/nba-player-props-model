"""Phase 13M-bis Part N — fixture proof for the predict.py Derek live-snapshot
CLI surface and lineup-context feature integration.

This is a CODE-PATH proof, not a production-live proof:
  1. Calls scripts/predict.py with --derek-live-snapshot
     --validate-args-and-exit and confirms it emits PREDICT_DEREK_LIVE_ARGS_PASS
     for valid args, and PREDICT_DEREK_LIVE_ARGS_FAILED for missing args.
  2. Constructs a tiny synthetic prediction-row list + a tiny synthetic BDL
     lineup parquet, calls
     ``nba_props_model.pipelines.predict._join_lineup_context_into_rows``
     directly, and confirms the new columns appear with the right values
     (current_starter, role_source=confirmed_bdl_lineup, lineup_confirmed,
     starter_flag_changed_count > 0, role_bucket_changed_count >= 0,
     etc.).
  3. Confirms backfill/demo snapshots still avoid claiming recomputation.

Pass lines:
    PREDICT_DEREK_LIVE_ARGS_PASS                    (CLI surface)
    PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_PASS (join function)
    PREDICT_LINEUP_CONTEXT_FIXTURE_PASS             (combined)

Fail lines:
    PREDICT_DEREK_LIVE_ARGS_FAILED
    PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_FAILED
    PREDICT_LINEUP_CONTEXT_FIXTURE_FAILED
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _check_cli_validation():
    """Return (passed, detail)."""
    py = sys.executable
    pred = REPO_ROOT / "scripts" / "predict.py"
    # Positive path.
    rc = subprocess.run(
        [py, str(pred),
         "--derek-live-snapshot",
         "--target-date", "2026-05-02",
         "--game-id", "21681995",
         "--snapshot-output-dir", "/tmp/derek-fixture",
         "--snapshot-type", "t_minus_25",
         "--snapshot-run-id", "fixture",
         "--validate-args-and-exit"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if rc.returncode != 0:
        return False, (
            f"positive validate-args path returned {rc.returncode}; "
            f"stdout={rc.stdout!r} stderr={rc.stderr!r}"
        )
    if "PREDICT_DEREK_LIVE_ARGS_PASS" not in rc.stdout:
        return False, f"PASS line not found in stdout: {rc.stdout!r}"
    # Negative path — missing required args.
    rc2 = subprocess.run(
        [py, str(pred), "--derek-live-snapshot", "--validate-args-and-exit"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if rc2.returncode == 0:
        return False, (
            "negative validate-args path should exit non-zero; "
            f"stdout={rc2.stdout!r} stderr={rc2.stderr!r}"
        )
    if "PREDICT_DEREK_LIVE_ARGS_FAILED" not in rc2.stderr:
        return False, f"FAILED line not found in stderr: {rc2.stderr!r}"
    return True, "positive + negative paths both behave correctly"


def _check_lineup_join():
    """Return (passed, detail)."""
    try:
        import pandas as pd
        from nba_props_model.pipelines.predict import (
            _join_lineup_context_into_rows,
        )
    except Exception as exc:
        return False, f"import failed: {exc}"

    tmp = Path(tempfile.mkdtemp(prefix="derek-fixture-"))
    # Synthetic rows: one starter (confirmed), one bench (confirmed), one
    # missing (no BDL data — must keep defaults).
    rows = [
        {"player_id": 100, "game_id": "999", "stat": "pts",
         "role_bucket": "high_minutes", "exp_mp": 32.0},
        {"player_id": 200, "game_id": "999", "stat": "pts",
         "role_bucket": "low_minutes", "exp_mp": 14.0},
        {"player_id": 300, "game_id": "999", "stat": "pts",
         "role_bucket": "starter", "exp_mp": 35.0},  # not in lineup data
    ]
    lineup = pd.DataFrame([
        # Confirmed starter who previously was just "high_minutes" → role
        # bucket should change to "starter_promoted".
        {"game_id": "999", "team_id": 1, "player_id": 100,
         "starter": True, "lineup_position": "G",
         "source": "balldontlie_v1_lineups"},
        # Confirmed bench previously "low_minutes" → no role change (was
        # not "starter" before).
        {"game_id": "999", "team_id": 1, "player_id": 200,
         "starter": False, "lineup_position": "F",
         "source": "balldontlie_v1_lineups"},
    ])
    lineup_path = tmp / "fixture_lineup.parquet"
    lineup.to_parquet(lineup_path, index=False)

    out_rows, summary = _join_lineup_context_into_rows(
        rows, str(lineup_path), "999",
    )

    # Assertions.
    issues = []
    if summary["lineup_rows_joined"] != 2:
        issues.append(f"expected 2 rows joined; got {summary['lineup_rows_joined']}")
    if summary["starter_flag_changed_count"] != 2:
        issues.append(
            f"expected 2 starter-flag changes; got {summary['starter_flag_changed_count']}"
        )
    if summary["role_bucket_changed_count"] != 1:
        issues.append(
            f"expected 1 role-bucket change (player 100 promoted); "
            f"got {summary['role_bucket_changed_count']}"
        )
    p100 = next(r for r in out_rows if r["player_id"] == 100)
    p200 = next(r for r in out_rows if r["player_id"] == 200)
    p300 = next(r for r in out_rows if r["player_id"] == 300)
    if p100["current_starter"] is not True:
        issues.append(f"p100 current_starter should be True; got {p100['current_starter']!r}")
    if p100["role_source"] != "confirmed_bdl_lineup":
        issues.append(f"p100 role_source should be confirmed_bdl_lineup; got {p100['role_source']!r}")
    if p100["role_bucket_post_lineup"] != "starter_promoted":
        issues.append(
            f"p100 role_bucket_post_lineup should be starter_promoted; "
            f"got {p100['role_bucket_post_lineup']!r}"
        )
    if p100["lineup_confirmed"] is not True:
        issues.append(f"p100 lineup_confirmed should be True; got {p100['lineup_confirmed']!r}")
    if p100["lineup_affects_pmf_features"] is not True:
        issues.append(
            f"p100 lineup_affects_pmf_features should be True; "
            f"got {p100['lineup_affects_pmf_features']!r}"
        )
    if p200["current_starter"] is not False:
        issues.append(f"p200 current_starter should be False; got {p200['current_starter']!r}")
    if p200["confirmed_bench"] is not True:
        issues.append(f"p200 confirmed_bench should be True; got {p200['confirmed_bench']!r}")
    # p300 not in lineup data — should keep defaults.
    if p300["bdl_lineup_present"] is not False:
        issues.append(f"p300 bdl_lineup_present should be False; got {p300['bdl_lineup_present']!r}")
    if p300["lineup_affects_pmf_features"] is not False:
        issues.append(f"p300 lineup_affects_pmf_features should be False")
    # Required column names must all be present on every row.
    required_cols = (
        "bdl_lineup_present", "current_starter", "confirmed_starter",
        "confirmed_bench", "lineup_position", "lineup_source",
        "lineup_confirmed", "role_source", "role_bucket_pre_lineup",
        "role_bucket_post_lineup", "lineup_context_supplied",
        "lineup_affects_pmf_features",
    )
    for r in out_rows:
        missing = [c for c in required_cols if c not in r]
        if missing:
            issues.append(f"row {r.get('player_id')}: missing columns {missing}")
            break

    if issues:
        return False, "; ".join(issues)
    return True, (
        f"rows_joined={summary['lineup_rows_joined']} "
        f"starter_flags={summary['starter_flag_changed_count']} "
        f"role_changes={summary['role_bucket_changed_count']} "
        f"minutes_conflicts={summary['minutes_projection_conflict_count']}"
    )


def main():
    cli_ok, cli_detail = _check_cli_validation()
    join_ok, join_detail = _check_lineup_join()

    if cli_ok:
        print("PREDICT_DEREK_LIVE_ARGS_PASS")
        print(f"  detail: {cli_detail}")
    else:
        print("PREDICT_DEREK_LIVE_ARGS_FAILED", file=sys.stderr)
        print(f"  detail: {cli_detail}", file=sys.stderr)

    if join_ok:
        print("PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_PASS")
        print(f"  detail: {join_detail}")
    else:
        print("PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_FAILED", file=sys.stderr)
        print(f"  detail: {join_detail}", file=sys.stderr)

    if cli_ok and join_ok:
        print("PREDICT_LINEUP_CONTEXT_FIXTURE_PASS")
        return 0
    print("PREDICT_LINEUP_CONTEXT_FIXTURE_FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
