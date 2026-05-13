#!/usr/bin/env python3
"""M8.6Q B8 — verifier requires N scored rows with ALL 9 fields non-null.

For overlap dates: matched-only is NOT sufficient. The verifier counts rows
where EVERY one of these is non-null and gates on >= --min-scored-rows:
  - model_prob_over
  - market_prob_over_no_vig
  - hit_result (or actual)
  - model_event_logloss
  - market_event_logloss
  - event_logloss_delta
  - model_brier
  - market_brier
  - brier_delta

Default --min-scored-rows is 50. Configurable.

Pass marker: M8_6Q_EVENT_MARKET_JOIN_AND_PROMOTION_GATE_PASS
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_OUTPUT_COLS = {
    "market_full_pmf","market_implied_pmf","market_pmf",
    "market_pmf_mean","market_pmf_variance","market_pmf_delta",
    "market_pmf_nll","market_rps","market_pit",
    "market_implied_full_pmf","market_implied_pmfs",
}
CLAIM_ALLOWED_ENUM = "market_superior_event_accuracy_and_calibration"
PROMOTION_ENUM = {
    "fail_same_sample_or_leakage_risk","fail_invalid_pmf",
    "valid_pmf_not_event_market_superior",
    "calibrated_but_not_more_accurate_than_market",
    "accurate_but_not_well_calibrated",
    CLAIM_ALLOWED_ENUM,
}
REQUIRED_NONNULL = (
    "model_prob_over", "market_prob_over_no_vig",
    "model_event_logloss", "market_event_logloss", "event_logloss_delta",
    "model_brier", "market_brier", "brier_delta",
)


def _fail(g, d):
    print(f"M8_6Q_EVENT_MARKET_JOIN_GATE_FAILED gate={g} detail={d}", file=sys.stderr)
    sys.exit(1)


def _run(cmd):
    print("  $", " ".join(cmd))
    return subprocess.run(cmd).returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of-date", required=True)
    ap.add_argument("--skip-builders", action="store_true")
    ap.add_argument("--min-scored-rows", type=int, default=50,
                    help="Minimum number of rows where ALL 9 required fields are non-null. "
                         "Default 50.")
    ap.add_argument("--require-scored-rows-on-overlap", action="store_true",
                    default=True,
                    help="If odds_pairs file exists for the date, require scored_rows >= min. "
                         "Default True.")
    args = ap.parse_args()
    date = args.as_of_date

    diag = REPO_ROOT / "artifacts" / "model_diagnostics"
    eml_path = diag / f"event_market_loss_rows_{date}.parquet"
    pcr_path = diag / f"promotion_claim_report_{date}.json"

    if not args.skip_builders:
        if not eml_path.exists():
            if _run([sys.executable, "scripts/build_event_market_loss_rows.py",
                     "--as-of-date", date]) != 0:
                _fail("G_BUILDER_EML_FAILED", "exit≠0")
        if not pcr_path.exists():
            if _run([sys.executable, "scripts/build_promotion_claim_report.py",
                     "--as-of-date", date]) != 0:
                _fail("G_BUILDER_PCR_FAILED", "exit≠0")

    if not eml_path.exists(): _fail("G1_EML_MISSING", str(eml_path))

    import pandas as pd
    eml = pd.read_parquet(eml_path)

    # B9 — forbidden columns
    leaked = [c for c in eml.columns if c.lower() in {x.lower() for x in FORBIDDEN_OUTPUT_COLS}]
    if leaked: _fail("G2_FORBIDDEN_COLS", str(leaked))

    # B8 — scored rows: ALL 9 required fields non-null
    if len(eml) > 0:
        # Use 'actual' OR 'hit_result' as the outcome indicator
        outcome_col = None
        for c in ("hit_result", "actual"):
            if c in eml.columns:
                outcome_col = c; break
        if outcome_col is None:
            _fail("G_NO_OUTCOME_COL",
                  "neither 'hit_result' nor 'actual' present in event_market_loss_rows parquet")
        mask = eml[outcome_col].notna()
        for c in REQUIRED_NONNULL:
            if c not in eml.columns:
                _fail("G_REQUIRED_COL_MISSING", f"column={c}")
            mask &= eml[c].notna()
        scored_rows = int(mask.sum())
    else:
        scored_rows = 0

    # G3 — odds_pairs presence on overlap dates → require scored rows
    odds_dir = REPO_ROOT / "data" / "odds_api" / "processed" / date
    odds_has_close_or_lock = bool(list(odds_dir.glob("odds_pairs_*close_or_lock*.parquet"))) \
        if odds_dir.exists() else False
    matched_count = int((eml["join_status"] == "matched").sum()) if "join_status" in eml.columns else 0

    if odds_has_close_or_lock and args.require_scored_rows_on_overlap:
        if scored_rows < args.min_scored_rows:
            pgs_path = REPO_ROOT / "data" / "player_game_stats.parquet"
            box_n = 0
            if pgs_path.exists():
                bg = pd.read_parquet(pgs_path, columns=["game_date"])
                box_n = int(bg["game_date"].astype(str).str.startswith(date).sum())
            if box_n <= 0:
                _fail(
                    "G3_ACTUALS_UNAVAILABLE_FOR_DATE",
                    f"date={date} odds_has_close_or_lock=True matched={matched_count} "
                    f"scored_rows={scored_rows} min_required={args.min_scored_rows} "
                    f"box_score_rows_in_player_game_stats={box_n} "
                    f"(cannot score event markets without finals in data/player_game_stats.parquet; "
                    f"run scripts/refresh_bdl_player_game_stats.py --start-date <day_after_max> "
                    f"--end-date <today>)",
                )
            _fail(
                "G3_INSUFFICIENT_SCORED_ROWS",
                f"date={date} odds_has_close_or_lock=True matched={matched_count} "
                f"scored_rows={scored_rows} min_required={args.min_scored_rows} "
                f"box_score_rows={box_n} "
                f"(B8: matched-only is insufficient; need all 9 fields non-null — "
                f"investigate scoring_blocker / joins / missing_two_way_odds)",
            )

    # G4 — promotion report
    if not pcr_path.exists(): _fail("G4_PCR_MISSING", str(pcr_path))
    pcr = json.loads(pcr_path.read_text())
    overall = pcr.get("overall_promotion_status")
    if overall not in PROMOTION_ENUM:
        _fail("G4_PCR_BAD_ENUM", f"overall={overall}")

    # G4b — sign convention declared
    if pcr.get("delta_sign_convention") != "model_minus_market_negative_better":
        _fail("G4b_BAD_SIGN_CONVENTION", str(pcr.get("delta_sign_convention")))

    # G5 — claim/enum consistency
    claim = bool(pcr.get("market_superiority_claim_allowed"))
    if claim and overall != CLAIM_ALLOWED_ENUM:
        _fail("G5_CLAIM_INCONSISTENT", f"claim=True overall={overall}")
    if (not claim) and overall == CLAIM_ALLOWED_ENUM:
        _fail("G5_CLAIM_INCONSISTENT", f"claim=False overall={overall}")

    print("M8_6Q_EVENT_MARKET_JOIN_AND_PROMOTION_GATE_PASS")
    print(f"  date={date} eml_rows={len(eml)} matched={matched_count} scored_rows={scored_rows}")
    print(f"  min_scored_rows={args.min_scored_rows} odds_has_close_or_lock={odds_has_close_or_lock}")
    print(f"  overall_promotion_status={overall} claim_allowed={claim}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
