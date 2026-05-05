# Daily automation health — 2026-05-04

_Generated 2026-05-05T01:04:50+00:00._

## Overall: **OVERALL_WARN**

- summary: one or more sections pending honest upstream data

## 1. Nightly training / recalibration — `NO_PROMOTE_PASS`

- **status:** `NO_PROMOTE_PASS`
- **run_date:** `2026-05-04`
- **prediction_date:** `2026-05-04`
- **training_cutoff_date:** `2026-05-03`
- **required_outcomes_through:** `2026-05-03`
- **settled_outcomes_max_date:** `2026-05-03`
- **training_cutoff_satisfied_by_settled_outcomes:** `True`
- **completed_cutoff_training_dir:** `artifacts/models/challengers/2026-05-03`
- **promoted:** `None`
- **promotion_reason:** `gate_failed:promotion_clock_safe`
- **halted_reason:** `promotion_clock_cutoff`
- **halted_workflow_run_url:** `None`
- **champion_model_id:** `challenger-2026-04-30`
- **trained_through_date:** `2026-04-30`
- **calibrated_through_date:** `2026-04-30`
- **daily_report_md_path:** `artifacts/model_daily_reports/2026-05-03/daily_model_training_report.md`
- **readiness_report_path:** `artifacts/training_readiness/2026-05-03/readiness_report.json`
- **same_day_run_status:** `halted_pending_upstream_data`
- **same_day_run_classified_as:** `historical_failed_attempt`
- **root_cause:** training completed for cutoff=2026-05-03 but promotion withheld: gate_failed:promotion_clock_safe. champion pointer unchanged.

_Training artifacts are keyed by latest settled outcome date (training_cutoff_date), not by slate / run date. Same-day outcomes (e.g. tonight's games) may still be pending for postgame scoring; that does not affect today's training status._

## 2. Daily prediction generation — `PASS`

- **status:** `PASS`
- **verifier_pass_line:** `DAILY_PREDICTION_OUTPUTS_PASS  date=2026-05-04  parquet_rows=65  singles=8  pmf_display=8  today_count=65`
- **all_props_rows:** `65`
- **all_props_games:** `2`
- **singles_count:** `8`
- **pmf_display_count:** `8`
- **today_count:** `65`
- **today_date:** `2026-05-04`

## 3. Derek snapshots — `PENDING`

- **status:** `PENDING`
- **delivery_date:** `2026-05-04`
- **current_live_count:** `0`
- **t_minus_25_missed:** `1`
- **t_minus_25_present:** `0`
- **close_lock_missed:** `0`
- **close_lock_present:** `0`
- **root_cause:** one or more Derek verifiers reported PENDING (no game due / no game tipped); honest pre-tip state, not a failure

- DEREK_LIVE_SNAPSHOTS: `DEREK_LIVE_SNAPSHOTS_PENDING_NO_GAMES`
- DEREK_PRODUCTION_LIVE_E2E: `DEREK_PRODUCTION_LIVE_E2E_PENDING`
- DEREK_OUTCOME_LEVEL_PROBABILITIES: `DEREK_OUTCOME_LEVEL_PROBABILITIES_PASS  delivery_date=2026-05-04  ok=0  skipped=1`

## 4. Wizard of Odds — `PASS`

- **status:** `PASS`
- **verifier_pass_line:** `WOO_NBA_PROPS_PAGE_PASS  date=2026-05-04  count=65  games=2  date=2026-05-04`
- **html_path:** `predictions/nba-props.html`
- **data_path:** `predictions/nba_props_today.json`
- **html_size_bytes:** `39614`
- **blank_page_prevention:** `True`

## 5. After-game scoring — `PENDING`

- **status:** `PENDING`
- **latest_settled_date:** `2026-05-03`
- **outcomes_available:** `False`
- **scoring_report_path:** `None`
- **root_cause:** settled stats only through 2026-05-03; after-game scoring for 2026-05-04 pending upstream backfill

