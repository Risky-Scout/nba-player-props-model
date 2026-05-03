# Derek delivery — 2026-05-03

- generated_at_utc: 2026-05-03T19:29:07+00:00Z
- delivery_date: **2026-05-03**
- games: **2**

## ⚠️ Read this first — current_live is a watchlist baseline

The **current_live** package is an early baseline / watchlist package. Because BDL did not return confirmed lineup rows at this timestamp, **current_live edges are not labeled as confirmed-lineup recommendations**. The **T-minus-25** and **close-lock** snapshots are the near-tip packages intended for confirmed-lineup evaluation; they fire automatically inside their per-game windows.

Every Derek market_comparison row carries an `edge_publish_status` column — values include `PUBLISH_BLOCKER`, `REVIEW_LARGE_EDGE`, `REVIEW_PUSH_LINE`, `WATCHLIST_NOT_CONFIRMED_LINEUP`, `ACTIONABLE_REVIEWED`. Calibration support per (stat / side / line / edge bucket) is captured in `calibration_support_status` and `calibration_bucket_n`.

## Phase 13X audit reports

- [Edge root-cause audit](../../artifacts/automation_health/derek_edge_root_cause_2026-05-03.md)
- [Edge calibration audit](../../artifacts/automation_health/derek_edge_calibration_2026-05-03.md)

## What's in this delivery

Per-game live snapshot folders under `derek_game_snapshots/<game_id>/<snapshot_type>/` containing:

- `snapshot_manifest.json` — full provenance (champion, BDL fetch, no-leakage flags, market-odds invariants).
- `snapshot_report.md` — human-readable executive summary, top edges, top deltas, driver explanation.
- `prop_summary.{csv,parquet}` — slim per-prop view.
- `full_pmf_wide.{csv,parquet}` — full per-prop PMF + market.
- `outcome_level_probabilities.{csv,parquet}` — long-form k → p_k.
- `market_comparison.{csv,parquet}` — model probs vs market probs.
- `lineup_context.{csv,parquet}` — BDL lineup fields per player.
- `injury_availability_context.{csv,parquet}` — injury / actionability.
- `game_context.{csv,parquet}` — schedule / rest / opponent.
- `contextual_feature_audit.{csv,parquet}` — per-row contextual features.
- `prediction_input_audit.{csv,parquet}` — prediction frame audit trail.
- `pmf_driver_decomposition.{csv,parquet,md}` — per-row contextual deltas.
- `lineup_injury_impact_report.{json,md}` — lineup + injury impact summary.
- `direct_lineup_impact_report.{json,md}` — Phase 13S direct-lineup driver attribution.
- `input_change_report.{json,md}` — diff vs prior snapshot when present.
- `snapshot_comparison.{csv,parquet,md}` — close-lock vs t_minus_25 comparison.

## Snapshot type meanings

- `current_live` — best-available pre-tip baseline. Generated any time the workflow runs while at least one game has not tipped. Uses the canonical predictions slate + the Phase 13S contextual engine. May be lineup-confirmed or baseline (BDL lineups not yet posted).
- `t_minus_25` — production-live snapshot taken ~25 minutes before game tip. The dispatcher fires this exactly inside the per-game window.
- `close_lock` — production-live snapshot ~5 minutes before tip. The dispatcher fires this inside the per-game window.

## Per-game status

### Game 21682000

- **current_live**: snapshot_mode=`production_live_current`, lineup_confirmed=**False**, pmfs_recomputed=**True**, props_emitted=36, feature_set_id=`phase13s_direct_lineup_injury_pmf_driver_v1`, game_start_time_utc=`2026-05-03T23:40:00Z`
  - [snapshot_report.md](derek_game_snapshots/21682000/current_live/snapshot_report.md)
  - [prop_summary.csv](derek_game_snapshots/21682000/current_live/prop_summary.csv)
  - [full_pmf_wide.csv](derek_game_snapshots/21682000/current_live/full_pmf_wide.csv)
  - [outcome_level_probabilities.csv](derek_game_snapshots/21682000/current_live/outcome_level_probabilities.csv)
  - [market_comparison.csv](derek_game_snapshots/21682000/current_live/market_comparison.csv)
  - [pmf_driver_decomposition.md](derek_game_snapshots/21682000/current_live/pmf_driver_decomposition.md)
  - [lineup_injury_impact_report.md](derek_game_snapshots/21682000/current_live/lineup_injury_impact_report.md)
  - [direct_lineup_impact_report.md](derek_game_snapshots/21682000/current_live/direct_lineup_impact_report.md)
- **t_minus_25**: not generated (target window may be in the future or absent).
- **close_lock**: not generated (target window may be in the future or absent).

### Game 21684819

- **current_live**: snapshot_mode=`production_live_current`, lineup_confirmed=**False**, pmfs_recomputed=**True**, props_emitted=33, feature_set_id=`phase13s_direct_lineup_injury_pmf_driver_v1`, game_start_time_utc=`2026-05-03T19:40:00Z`
  - [snapshot_report.md](derek_game_snapshots/21684819/current_live/snapshot_report.md)
  - [prop_summary.csv](derek_game_snapshots/21684819/current_live/prop_summary.csv)
  - [full_pmf_wide.csv](derek_game_snapshots/21684819/current_live/full_pmf_wide.csv)
  - [outcome_level_probabilities.csv](derek_game_snapshots/21684819/current_live/outcome_level_probabilities.csv)
  - [market_comparison.csv](derek_game_snapshots/21684819/current_live/market_comparison.csv)
  - [pmf_driver_decomposition.md](derek_game_snapshots/21684819/current_live/pmf_driver_decomposition.md)
  - [lineup_injury_impact_report.md](derek_game_snapshots/21684819/current_live/lineup_injury_impact_report.md)
  - [direct_lineup_impact_report.md](derek_game_snapshots/21684819/current_live/direct_lineup_impact_report.md)
- **t_minus_25**: not generated (target window may be in the future or absent).
- **close_lock**: not generated (target window may be in the future or absent).

## Daily model report

The daily model training / recalibration report — what was trained, recalibrated, validated, and promoted — is in:

`artifacts/model_daily_reports/<trained_through_date>/daily_model_training_report.md`

## Aggregate scoring

Snapshot scoring summaries (when realized outcomes are available) are in:

`artifacts/automation_health/derek_live_snapshots_2026-05-03.{json,md}`

