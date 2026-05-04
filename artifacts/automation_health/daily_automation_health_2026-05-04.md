# Daily automation health — 2026-05-04

_Generated 2026-05-04T16:29:46+00:00._

## Overall: **OVERALL_WARN**

- summary: one or more sections pending honest upstream data

## 1. Nightly training / recalibration — `SKIPPED_WITH_REASON`

- **status:** `SKIPPED_WITH_REASON`
- **halted_reason:** `previous_day_data_not_ready`
- **halted_workflow_run_url:** `https://github.com/Risky-Scout/nba-player-props-model/actions/runs/25316091911`
- **champion_model_id:** `challenger-2026-04-30`
- **trained_through_date:** `2026-04-30`
- **calibrated_through_date:** `2026-04-30`
- **daily_report_md_path:** `artifacts/model_daily_reports/2026-05-04/daily_model_training_report.md`
- **readiness_report_path:** `artifacts/training_readiness/2026-05-04/readiness_report.json`
- **root_cause:** Strict resolver halted: previous-day-ET data not ready in data/player_game_stats.parquet. Correct safe behavior. Training will resume automatically when BDL backfills settled stats. champion pointer unchanged.

## 2. Daily prediction generation — `PASS`

- **status:** `PASS`
- **verifier_pass_line:** `DAILY_PREDICTION_OUTPUTS_PASS  date=2026-05-04  parquet_rows=65  singles=8  pmf_display=8  today_count=65`
- **all_props_rows:** `65`
- **all_props_games:** `2`
- **singles_count:** `8`
- **pmf_display_count:** `8`
- **today_count:** `65`
- **today_date:** `2026-05-04`

## 3. Derek snapshots — `PASS`

- **status:** `PASS`
- **delivery_date:** `2026-05-03`
- **current_live_count:** `2`
- **t_minus_25_missed:** `2`
- **t_minus_25_present:** `0`
- **close_lock_missed:** `2`
- **close_lock_present:** `0`

- DEREK_LIVE_SNAPSHOTS: `DEREK_LIVE_SNAPSHOTS_PASS`
- DEREK_PRODUCTION_LIVE_E2E: `DEREK_PRODUCTION_LIVE_E2E_PASS`
- DEREK_OUTCOME_LEVEL_PROBABILITIES: `DEREK_OUTCOME_LEVEL_PROBABILITIES_PASS  delivery_date=2026-05-03  ok=2  skipped=4`

## 4. Wizard of Odds — `PASS`

- **status:** `PASS`
- **verifier_pass_line:** `WOO_NBA_PROPS_PAGE_PASS  date=2026-05-04  count=65  games=2  date=2026-05-04`
- **html_path:** `predictions/nba-props.html`
- **data_path:** `predictions/nba_props_today.json`
- **html_size_bytes:** `39614`
- **blank_page_prevention:** `True`

## 5. After-game scoring — `PENDING`

- **status:** `PENDING`
- **latest_settled_date:** `2026-04-29`
- **outcomes_available:** `False`
- **scoring_report_path:** `None`
- **root_cause:** settled stats only through 2026-04-29; after-game scoring for 2026-05-04 pending upstream backfill

