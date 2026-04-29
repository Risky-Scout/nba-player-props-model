# 2026-04-28 — NOT_DELIVERABLE_READY

No delivery was produced for this date.

## Cause

`predictions/all_props_2026-04-28.parquet` does not exist. The upstream
prediction pipeline (`scripts/predict.py`) was not run for this date.
Per the Phase 11C strict rules, we do **not** fabricate predictions; the
date is recorded here as `NOT_DELIVERABLE_READY` rather than left silently
absent.

## Required to resolve

1. Run the prediction pipeline for 2026-04-28 (this requires
   `BDL_API_KEY` and the canonical training inputs):
   ```
   python3 src/nba_props_model/pipelines/predict.py --date 2026-04-28
   ```
2. Run the daily delivery wrapper:
   ```
   python3 scripts/run_daily_delivery_pipeline.py --date 2026-04-28 \
       --mode morning --rebuild-canonical
   ```
3. Re-run the deliveries index:
   ```
   python3 scripts/build_deliveries_index.py
   ```

## What is **not** in this folder (intentionally)

- No `pmf_model_review_package/` — would require fabricated PMFs.
- No `wizard_of_odds/` — would require fabricated PMFs.
- No `canonical_source/` — would require fabricated PMFs.
- No `after_game_scoring/` — no delivery to score against.

The smoke odds capture under `data/odds_api/processed/2026-04-28/`
exists but is intentionally not staged and is not joined to anything
without a prediction source.
