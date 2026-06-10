# Model performance & calibration — 2026-06-10

**after_game_status**: `pending_outcomes`

This file will be re-written by `scripts/score_daily_pmf_delivery_after_game.py` once box-score finals are loaded into `data/player_game_stats.parquet` for 2026-06-10.

## Rollup at delivery time

- delivery_date: `2026-06-10`
- props in delivery: **180**
- finality_status: `provisional`
- finality_blockers: lineup_unconfirmed
- model_version: `1e12786b#phase10c`

## What this file will contain after scoring

- props scored, PMF NLL, RPS, mean absolute error
- assigned probability to the realized outcome
- model logloss / Brier per (stat, role_bucket) where market lines exist
- CLV summary where morning and close snapshots both exist
- model vs market logloss / Brier comparison **only when directly measured** — no claims of market superiority otherwise
