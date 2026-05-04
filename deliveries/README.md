# Deliveries
_Index regenerated 2026-05-04T09:05:01Z by `scripts/build_deliveries_index.py`._

Each row links to the per-date Derek (`pmf_model_review_package/`), Wizard of Odds (`wizard_of_odds/`), and after-game (`after_game_scoring/`) packages.

Classification key: **FINAL_DELIVERABLE_READY** · **PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS** · **NOT_DELIVERABLE_READY**.

| date | classification | props | fair_odds | market_comparison | publishable_edges | market_coverage | injury_fresh | tov_status | forward_feed | morning_rows | lineup_status | latest_rows | after_game | model_version |
|---|---|---:|---:|---:|---:|---|---|---|---|---:|---|---:|---|---|
| **2026-04-27** | `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS` | 158 | 3229 | 346 | 312 | `full` | `very_stale` | `present` | `morning_present` | 464 | `pending_lineup_snapshot` | 464 | `pending_outcomes` | `113c7b5#phase10c` |
| **2026-04-28** | `NOT_DELIVERABLE_READY` | — | — | — | — | `—` | `—` | `—` | `absent` | — | `—` | — | `n/a` | `—` |
| **2026-04-29** | `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS` | 143 | 3001 | 1508 | 1442 | `full` | `very_stale` | `present` | `morning_present` | 1528 | `pending_lineup_snapshot` | 1528 | `scored` | `113c7b5#phase10c` |
| **2026-04-30** | `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS` | 97 | 2458 | 1382 | 1205 | `full` | `fresh` | `missing_from_prediction_source` | `lineup_present` | 1372 | `present` | 1372 | `scored` | `6aea017#phase10c` |
| **2026-05-01** | `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS` | 95 | 2519 | 1202 | 1142 | `full` | `fresh` | `missing_from_prediction_source` | `lineup_present` | 1199 | `present` | 1199 | `scored` | `f496f12#phase10c` |
| **2026-05-02** | `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS` | 29 | 660 | 421 | 315 | `full` | `fresh` | `missing_from_prediction_source` | `lineup_present` | 414 | `present` | 414 | `scored` | `04ee0aa#phase10c` |
| **2026-05-03** | `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS` | 69 | 1780 | 489 | 462 | `full` | `fresh` | `missing_from_prediction_source` | `lineup_present` | 524 | `present` | 524 | `scored` | `a9bdb1c#phase10c` |

## Per-date links

### 2026-04-27 — `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS`

_injury_very_stale, role_bucket_missing_

**Derek (PMF model review)**

- [01_START_HERE.html](2026-04-27/pmf_model_review_package/01_START_HERE.html)
- [03_PMF_DISTRIBUTION_VIEWER.html](2026-04-27/pmf_model_review_package/03_PMF_DISTRIBUTION_VIEWER.html)
- [04_PROP_SUMMARY.csv](2026-04-27/pmf_model_review_package/04_PROP_SUMMARY.csv)
- [05_FULL_PMF_WIDE.csv](2026-04-27/pmf_model_review_package/05_FULL_PMF_WIDE.csv)
- [06_OUTCOME_LEVEL_PROBABILITIES.csv](2026-04-27/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv)
- [machine_readable/model_only.parquet](2026-04-27/pmf_model_review_package/machine_readable/model_only.parquet)
- [MODEL_PERFORMANCE_AND_CALIBRATION.md](2026-04-27/pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md)

**Derek forward feed (PMF snapshots)** — morning rows=464 · lineup=pending_lineup_snapshot · latest→morning

- [FEED_README.md](2026-04-27/derek_forward_feed/FEED_README.md)
- [feed_manifest.json](2026-04-27/derek_forward_feed/feed_manifest.json)
- [morning_snapshot.csv](2026-04-27/derek_forward_feed/morning_snapshot.csv)
- [morning_snapshot.parquet](2026-04-27/derek_forward_feed/morning_snapshot.parquet)
- [morning_snapshot.jsonl](2026-04-27/derek_forward_feed/morning_snapshot.jsonl)
- [latest_available_snapshot.csv](2026-04-27/derek_forward_feed/latest_available_snapshot.csv)
- [latest_available_snapshot.parquet](2026-04-27/derek_forward_feed/latest_available_snapshot.parquet)
- [lineup_snapshot_status.json](2026-04-27/derek_forward_feed/lineup_snapshot_status.json)

**Wizard of Odds**

- [README.md](2026-04-27/wizard_of_odds/README.md)
- [fair_odds_board.csv](2026-04-27/wizard_of_odds/fair_odds_board.csv)
- [full_pmfs_wide.csv](2026-04-27/wizard_of_odds/full_pmfs_wide.csv)
- [full_pmfs_outcome_level.csv](2026-04-27/wizard_of_odds/full_pmfs_outcome_level.csv)
- [market_comparison.csv](2026-04-27/wizard_of_odds/market_comparison.csv)
- [publishable_edges.csv](2026-04-27/wizard_of_odds/publishable_edges.csv)
- [run_manifest.json](2026-04-27/wizard_of_odds/run_manifest.json)

**After-game scoring** (`pending_outcomes`)

- [after_game_summary.md](2026-04-27/after_game_scoring/after_game_summary.md)
- ~~after_game_scoring.csv~~
- ~~calibration_by_stat.csv~~
- ~~calibration_by_role_bucket.csv~~
- ~~clv_by_stat.csv~~
- ~~clv_by_book.csv~~
- [after_game_status.json](2026-04-27/after_game_scoring/after_game_status.json)

### 2026-04-28 — `NOT_DELIVERABLE_READY`

_predictions/all_props_{date}.parquet missing — predict.py must run before this date can ship_

_No wizard_of_odds/ package on disk for this date._

See [`STATUS.md`](2026-04-28/STATUS.md) for the cause and the required-to-resolve checklist.

### 2026-04-29 — `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS`

_injury_very_stale, role_bucket_missing_

**Derek (PMF model review)**

- [01_START_HERE.html](2026-04-29/pmf_model_review_package/01_START_HERE.html)
- [03_PMF_DISTRIBUTION_VIEWER.html](2026-04-29/pmf_model_review_package/03_PMF_DISTRIBUTION_VIEWER.html)
- [04_PROP_SUMMARY.csv](2026-04-29/pmf_model_review_package/04_PROP_SUMMARY.csv)
- [05_FULL_PMF_WIDE.csv](2026-04-29/pmf_model_review_package/05_FULL_PMF_WIDE.csv)
- [06_OUTCOME_LEVEL_PROBABILITIES.csv](2026-04-29/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv)
- [machine_readable/model_only.parquet](2026-04-29/pmf_model_review_package/machine_readable/model_only.parquet)
- [MODEL_PERFORMANCE_AND_CALIBRATION.md](2026-04-29/pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md)

**Derek forward feed (PMF snapshots)** — morning rows=1528 · lineup=pending_lineup_snapshot · latest→morning

- [FEED_README.md](2026-04-29/derek_forward_feed/FEED_README.md)
- [feed_manifest.json](2026-04-29/derek_forward_feed/feed_manifest.json)
- [morning_snapshot.csv](2026-04-29/derek_forward_feed/morning_snapshot.csv)
- [morning_snapshot.parquet](2026-04-29/derek_forward_feed/morning_snapshot.parquet)
- [morning_snapshot.jsonl](2026-04-29/derek_forward_feed/morning_snapshot.jsonl)
- [latest_available_snapshot.csv](2026-04-29/derek_forward_feed/latest_available_snapshot.csv)
- [latest_available_snapshot.parquet](2026-04-29/derek_forward_feed/latest_available_snapshot.parquet)
- [lineup_snapshot_status.json](2026-04-29/derek_forward_feed/lineup_snapshot_status.json)

**Wizard of Odds**

- [README.md](2026-04-29/wizard_of_odds/README.md)
- [fair_odds_board.csv](2026-04-29/wizard_of_odds/fair_odds_board.csv)
- [full_pmfs_wide.csv](2026-04-29/wizard_of_odds/full_pmfs_wide.csv)
- [full_pmfs_outcome_level.csv](2026-04-29/wizard_of_odds/full_pmfs_outcome_level.csv)
- [market_comparison.csv](2026-04-29/wizard_of_odds/market_comparison.csv)
- [publishable_edges.csv](2026-04-29/wizard_of_odds/publishable_edges.csv)
- [run_manifest.json](2026-04-29/wizard_of_odds/run_manifest.json)

**After-game scoring** (`scored`)

- [after_game_summary.md](2026-04-29/after_game_scoring/after_game_summary.md)
- [after_game_scoring.csv](2026-04-29/after_game_scoring/after_game_scoring.csv)
- [calibration_by_stat.csv](2026-04-29/after_game_scoring/calibration_by_stat.csv)
- [calibration_by_role_bucket.csv](2026-04-29/after_game_scoring/calibration_by_role_bucket.csv)
- ~~clv_by_stat.csv~~
- ~~clv_by_book.csv~~
- [after_game_status.json](2026-04-29/after_game_scoring/after_game_status.json)

### 2026-04-30 — `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS`

_lineup_unconfirmed, missing_stats:tov_

**Derek (PMF model review)**

- [01_START_HERE.html](2026-04-30/pmf_model_review_package/01_START_HERE.html)
- [03_PMF_DISTRIBUTION_VIEWER.html](2026-04-30/pmf_model_review_package/03_PMF_DISTRIBUTION_VIEWER.html)
- [04_PROP_SUMMARY.csv](2026-04-30/pmf_model_review_package/04_PROP_SUMMARY.csv)
- [05_FULL_PMF_WIDE.csv](2026-04-30/pmf_model_review_package/05_FULL_PMF_WIDE.csv)
- [06_OUTCOME_LEVEL_PROBABILITIES.csv](2026-04-30/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv)
- [machine_readable/model_only.parquet](2026-04-30/pmf_model_review_package/machine_readable/model_only.parquet)
- [MODEL_PERFORMANCE_AND_CALIBRATION.md](2026-04-30/pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md)

**Derek forward feed (PMF snapshots)** — morning rows=1372 · lineup=present · latest→lineup

- [FEED_README.md](2026-04-30/derek_forward_feed/FEED_README.md)
- [feed_manifest.json](2026-04-30/derek_forward_feed/feed_manifest.json)
- [morning_snapshot.csv](2026-04-30/derek_forward_feed/morning_snapshot.csv)
- [morning_snapshot.parquet](2026-04-30/derek_forward_feed/morning_snapshot.parquet)
- [morning_snapshot.jsonl](2026-04-30/derek_forward_feed/morning_snapshot.jsonl)
- [latest_available_snapshot.csv](2026-04-30/derek_forward_feed/latest_available_snapshot.csv)
- [latest_available_snapshot.parquet](2026-04-30/derek_forward_feed/latest_available_snapshot.parquet)
- [lineup_snapshot.csv](2026-04-30/derek_forward_feed/lineup_snapshot.csv)
- [lineup_snapshot.parquet](2026-04-30/derek_forward_feed/lineup_snapshot.parquet)
- [lineup_snapshot.jsonl](2026-04-30/derek_forward_feed/lineup_snapshot.jsonl)
- [lineup_snapshot_status.json](2026-04-30/derek_forward_feed/lineup_snapshot_status.json)

**Wizard of Odds**

- [README.md](2026-04-30/wizard_of_odds/README.md)
- [fair_odds_board.csv](2026-04-30/wizard_of_odds/fair_odds_board.csv)
- [full_pmfs_wide.csv](2026-04-30/wizard_of_odds/full_pmfs_wide.csv)
- [full_pmfs_outcome_level.csv](2026-04-30/wizard_of_odds/full_pmfs_outcome_level.csv)
- [market_comparison.csv](2026-04-30/wizard_of_odds/market_comparison.csv)
- [publishable_edges.csv](2026-04-30/wizard_of_odds/publishable_edges.csv)
- [run_manifest.json](2026-04-30/wizard_of_odds/run_manifest.json)

**After-game scoring** (`scored`)

- [after_game_summary.md](2026-04-30/after_game_scoring/after_game_summary.md)
- [after_game_scoring.csv](2026-04-30/after_game_scoring/after_game_scoring.csv)
- [calibration_by_stat.csv](2026-04-30/after_game_scoring/calibration_by_stat.csv)
- [calibration_by_role_bucket.csv](2026-04-30/after_game_scoring/calibration_by_role_bucket.csv)
- ~~clv_by_stat.csv~~
- ~~clv_by_book.csv~~
- [after_game_status.json](2026-04-30/after_game_scoring/after_game_status.json)

### 2026-05-01 — `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS`

_lineup_unconfirmed, missing_stats:tov_

**Derek (PMF model review)**

- [01_START_HERE.html](2026-05-01/pmf_model_review_package/01_START_HERE.html)
- [03_PMF_DISTRIBUTION_VIEWER.html](2026-05-01/pmf_model_review_package/03_PMF_DISTRIBUTION_VIEWER.html)
- [04_PROP_SUMMARY.csv](2026-05-01/pmf_model_review_package/04_PROP_SUMMARY.csv)
- [05_FULL_PMF_WIDE.csv](2026-05-01/pmf_model_review_package/05_FULL_PMF_WIDE.csv)
- [06_OUTCOME_LEVEL_PROBABILITIES.csv](2026-05-01/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv)
- [machine_readable/model_only.parquet](2026-05-01/pmf_model_review_package/machine_readable/model_only.parquet)
- [MODEL_PERFORMANCE_AND_CALIBRATION.md](2026-05-01/pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md)

**Derek forward feed (PMF snapshots)** — morning rows=1199 · lineup=present · latest→lineup

- [FEED_README.md](2026-05-01/derek_forward_feed/FEED_README.md)
- [feed_manifest.json](2026-05-01/derek_forward_feed/feed_manifest.json)
- [morning_snapshot.csv](2026-05-01/derek_forward_feed/morning_snapshot.csv)
- [morning_snapshot.parquet](2026-05-01/derek_forward_feed/morning_snapshot.parquet)
- [morning_snapshot.jsonl](2026-05-01/derek_forward_feed/morning_snapshot.jsonl)
- [latest_available_snapshot.csv](2026-05-01/derek_forward_feed/latest_available_snapshot.csv)
- [latest_available_snapshot.parquet](2026-05-01/derek_forward_feed/latest_available_snapshot.parquet)
- [lineup_snapshot.csv](2026-05-01/derek_forward_feed/lineup_snapshot.csv)
- [lineup_snapshot.parquet](2026-05-01/derek_forward_feed/lineup_snapshot.parquet)
- [lineup_snapshot.jsonl](2026-05-01/derek_forward_feed/lineup_snapshot.jsonl)
- [lineup_snapshot_status.json](2026-05-01/derek_forward_feed/lineup_snapshot_status.json)

**Wizard of Odds**

- [README.md](2026-05-01/wizard_of_odds/README.md)
- [fair_odds_board.csv](2026-05-01/wizard_of_odds/fair_odds_board.csv)
- [full_pmfs_wide.csv](2026-05-01/wizard_of_odds/full_pmfs_wide.csv)
- [full_pmfs_outcome_level.csv](2026-05-01/wizard_of_odds/full_pmfs_outcome_level.csv)
- [market_comparison.csv](2026-05-01/wizard_of_odds/market_comparison.csv)
- [publishable_edges.csv](2026-05-01/wizard_of_odds/publishable_edges.csv)
- [run_manifest.json](2026-05-01/wizard_of_odds/run_manifest.json)

**After-game scoring** (`scored`)

- [after_game_summary.md](2026-05-01/after_game_scoring/after_game_summary.md)
- [after_game_scoring.csv](2026-05-01/after_game_scoring/after_game_scoring.csv)
- [calibration_by_stat.csv](2026-05-01/after_game_scoring/calibration_by_stat.csv)
- [calibration_by_role_bucket.csv](2026-05-01/after_game_scoring/calibration_by_role_bucket.csv)
- ~~clv_by_stat.csv~~
- ~~clv_by_book.csv~~
- [after_game_status.json](2026-05-01/after_game_scoring/after_game_status.json)

### 2026-05-02 — `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS`

_lineup_unconfirmed, missing_stats:tov_

**Derek (PMF model review)**

- [01_START_HERE.html](2026-05-02/pmf_model_review_package/01_START_HERE.html)
- [03_PMF_DISTRIBUTION_VIEWER.html](2026-05-02/pmf_model_review_package/03_PMF_DISTRIBUTION_VIEWER.html)
- [04_PROP_SUMMARY.csv](2026-05-02/pmf_model_review_package/04_PROP_SUMMARY.csv)
- [05_FULL_PMF_WIDE.csv](2026-05-02/pmf_model_review_package/05_FULL_PMF_WIDE.csv)
- [06_OUTCOME_LEVEL_PROBABILITIES.csv](2026-05-02/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv)
- [machine_readable/model_only.parquet](2026-05-02/pmf_model_review_package/machine_readable/model_only.parquet)
- [MODEL_PERFORMANCE_AND_CALIBRATION.md](2026-05-02/pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md)

**Derek forward feed (PMF snapshots)** — morning rows=414 · lineup=present · latest→lineup

- [FEED_README.md](2026-05-02/derek_forward_feed/FEED_README.md)
- [feed_manifest.json](2026-05-02/derek_forward_feed/feed_manifest.json)
- [morning_snapshot.csv](2026-05-02/derek_forward_feed/morning_snapshot.csv)
- [morning_snapshot.parquet](2026-05-02/derek_forward_feed/morning_snapshot.parquet)
- [morning_snapshot.jsonl](2026-05-02/derek_forward_feed/morning_snapshot.jsonl)
- [latest_available_snapshot.csv](2026-05-02/derek_forward_feed/latest_available_snapshot.csv)
- [latest_available_snapshot.parquet](2026-05-02/derek_forward_feed/latest_available_snapshot.parquet)
- [lineup_snapshot.csv](2026-05-02/derek_forward_feed/lineup_snapshot.csv)
- [lineup_snapshot.parquet](2026-05-02/derek_forward_feed/lineup_snapshot.parquet)
- [lineup_snapshot.jsonl](2026-05-02/derek_forward_feed/lineup_snapshot.jsonl)
- [lineup_snapshot_status.json](2026-05-02/derek_forward_feed/lineup_snapshot_status.json)

**Wizard of Odds**

- [README.md](2026-05-02/wizard_of_odds/README.md)
- [fair_odds_board.csv](2026-05-02/wizard_of_odds/fair_odds_board.csv)
- [full_pmfs_wide.csv](2026-05-02/wizard_of_odds/full_pmfs_wide.csv)
- [full_pmfs_outcome_level.csv](2026-05-02/wizard_of_odds/full_pmfs_outcome_level.csv)
- [market_comparison.csv](2026-05-02/wizard_of_odds/market_comparison.csv)
- [publishable_edges.csv](2026-05-02/wizard_of_odds/publishable_edges.csv)
- [run_manifest.json](2026-05-02/wizard_of_odds/run_manifest.json)

**After-game scoring** (`scored`)

- [after_game_summary.md](2026-05-02/after_game_scoring/after_game_summary.md)
- [after_game_scoring.csv](2026-05-02/after_game_scoring/after_game_scoring.csv)
- [calibration_by_stat.csv](2026-05-02/after_game_scoring/calibration_by_stat.csv)
- [calibration_by_role_bucket.csv](2026-05-02/after_game_scoring/calibration_by_role_bucket.csv)
- ~~clv_by_stat.csv~~
- ~~clv_by_book.csv~~
- [after_game_status.json](2026-05-02/after_game_scoring/after_game_status.json)

### 2026-05-03 — `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS`

_lineup_unconfirmed, missing_stats:tov_

**Derek (PMF model review)**

- [01_START_HERE.html](2026-05-03/pmf_model_review_package/01_START_HERE.html)
- [03_PMF_DISTRIBUTION_VIEWER.html](2026-05-03/pmf_model_review_package/03_PMF_DISTRIBUTION_VIEWER.html)
- [04_PROP_SUMMARY.csv](2026-05-03/pmf_model_review_package/04_PROP_SUMMARY.csv)
- [05_FULL_PMF_WIDE.csv](2026-05-03/pmf_model_review_package/05_FULL_PMF_WIDE.csv)
- [06_OUTCOME_LEVEL_PROBABILITIES.csv](2026-05-03/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv)
- [machine_readable/model_only.parquet](2026-05-03/pmf_model_review_package/machine_readable/model_only.parquet)
- [MODEL_PERFORMANCE_AND_CALIBRATION.md](2026-05-03/pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md)

**Derek forward feed (PMF snapshots)** — morning rows=524 · lineup=present · latest→lineup

- [FEED_README.md](2026-05-03/derek_forward_feed/FEED_README.md)
- [feed_manifest.json](2026-05-03/derek_forward_feed/feed_manifest.json)
- [morning_snapshot.csv](2026-05-03/derek_forward_feed/morning_snapshot.csv)
- [morning_snapshot.parquet](2026-05-03/derek_forward_feed/morning_snapshot.parquet)
- [morning_snapshot.jsonl](2026-05-03/derek_forward_feed/morning_snapshot.jsonl)
- [latest_available_snapshot.csv](2026-05-03/derek_forward_feed/latest_available_snapshot.csv)
- [latest_available_snapshot.parquet](2026-05-03/derek_forward_feed/latest_available_snapshot.parquet)
- [lineup_snapshot.csv](2026-05-03/derek_forward_feed/lineup_snapshot.csv)
- [lineup_snapshot.parquet](2026-05-03/derek_forward_feed/lineup_snapshot.parquet)
- [lineup_snapshot.jsonl](2026-05-03/derek_forward_feed/lineup_snapshot.jsonl)
- [lineup_snapshot_status.json](2026-05-03/derek_forward_feed/lineup_snapshot_status.json)

**Wizard of Odds**

- [README.md](2026-05-03/wizard_of_odds/README.md)
- [fair_odds_board.csv](2026-05-03/wizard_of_odds/fair_odds_board.csv)
- [full_pmfs_wide.csv](2026-05-03/wizard_of_odds/full_pmfs_wide.csv)
- [full_pmfs_outcome_level.csv](2026-05-03/wizard_of_odds/full_pmfs_outcome_level.csv)
- [market_comparison.csv](2026-05-03/wizard_of_odds/market_comparison.csv)
- [publishable_edges.csv](2026-05-03/wizard_of_odds/publishable_edges.csv)
- [run_manifest.json](2026-05-03/wizard_of_odds/run_manifest.json)

**After-game scoring** (`scored`)

- [after_game_summary.md](2026-05-03/after_game_scoring/after_game_summary.md)
- [after_game_scoring.csv](2026-05-03/after_game_scoring/after_game_scoring.csv)
- [calibration_by_stat.csv](2026-05-03/after_game_scoring/calibration_by_stat.csv)
- [calibration_by_role_bucket.csv](2026-05-03/after_game_scoring/calibration_by_role_bucket.csv)
- ~~clv_by_stat.csv~~
- ~~clv_by_book.csv~~
- [after_game_status.json](2026-05-03/after_game_scoring/after_game_status.json)


## Schedule (Phase 12D-amend)

Derek's evaluation feed and WoO's monetization feed run on separate clocks.

**WoO monetization feed (public, affiliate-friendly):**

- 15:00 UTC / 11:00 AM ET — `woo_morning_monetization` (`finality_status_public=PROVISIONAL_EARLY_MARKET`)
- 18:00 UTC / 2:00 PM ET — `woo_afternoon_refresh`
- 20:00 UTC / 4:00 PM ET — `woo_afternoon_refresh`
- Refreshed automatically alongside every `derek_near_lineup` and `close_lock` run.

**Derek evaluation feed:**

- 22:25 UTC / 6:25 PM ET — `derek_near_lineup` first publishable evaluation snapshot (earliest tipoff − 35 min default during NBA playoffs).
- Every 15 min from 22:40 UTC through 03:10 UTC — `derek_near_lineup` refresh as lineups confirm.
- 03:25 UTC — `close_lock` final lineup/market lock.
- 06:30 UTC — `after_game` scoring (yesterday's slate).

- Derek should archive `derek_forward_feed/latest_available_snapshot.csv` after the near-lineup run.
- The morning cron was retired in Phase 12D; `morning` mode remains available manually via `workflow_dispatch` for backfills.
- Affiliate URLs in the public WoO export are never fabricated — absent mapping ⇒ `monetization_status=needs_affiliate_mapping`. See `docs/wizardofodds_public_export_runbook.md`.

## Honest framing

- All emitted PMFs are **model-only**; market columns are reference only.
- TOV PMFs (when emitted) come from Phase 8 calibrators — **no Phase 10D / 10D.2 overlay is wired into production**.
- Freshness, role provenance, and after-game scoring status are recorded verbatim from each delivery's `wizard_of_odds/run_manifest.json` — no fabrication.
- See `docs/daily_pmf_delivery_spec.md` for the row schema and validation contract, and `docs/daily_data_freshness_runbook.md` for the freshness manifest.
