# Deliveries
_Index regenerated 2026-04-29T23:19:02Z by `scripts/build_deliveries_index.py`._

Each row links to the per-date Derek (`pmf_model_review_package/`), Wizard of Odds (`wizard_of_odds/`), and after-game (`after_game_scoring/`) packages.

Classification key: **FINAL_DELIVERABLE_READY** · **PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS** · **NOT_DELIVERABLE_READY**.

| date | classification | props | fair_odds | market_comparison | publishable_edges | market_coverage | injury_fresh | tov_status | after_game | model_version |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| **2026-04-27** | `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS` | 114 | 2877 | 346 | 312 | `full` | `very_stale` | `missing_from_prediction_source` | `pending_outcomes` | `bb723eb#phase10c` |
| **2026-04-28** | `NOT_DELIVERABLE_READY` | — | — | — | — | `—` | `—` | `—` | `n/a` | `—` |
| **2026-04-29** | `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS` | 104 | 2689 | 1314 | 1239 | `full` | `fresh` | `missing_from_prediction_source` | `pending_outcomes` | `113c7b5#phase10c` |

## Per-date links

### 2026-04-27 — `PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS`

_injury_very_stale, lineup_unconfirmed, missing_stats:tov_

**Derek (PMF model review)**

- [01_START_HERE.html](2026-04-27/pmf_model_review_package/01_START_HERE.html)
- [03_PMF_DISTRIBUTION_VIEWER.html](2026-04-27/pmf_model_review_package/03_PMF_DISTRIBUTION_VIEWER.html)
- [04_PROP_SUMMARY.csv](2026-04-27/pmf_model_review_package/04_PROP_SUMMARY.csv)
- [05_FULL_PMF_WIDE.csv](2026-04-27/pmf_model_review_package/05_FULL_PMF_WIDE.csv)
- [06_OUTCOME_LEVEL_PROBABILITIES.csv](2026-04-27/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv)
- [machine_readable/model_only.parquet](2026-04-27/pmf_model_review_package/machine_readable/model_only.parquet)
- [MODEL_PERFORMANCE_AND_CALIBRATION.md](2026-04-27/pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md)

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

_lineup_unconfirmed, missing_stats:tov_

**Derek (PMF model review)**

- [01_START_HERE.html](2026-04-29/pmf_model_review_package/01_START_HERE.html)
- [03_PMF_DISTRIBUTION_VIEWER.html](2026-04-29/pmf_model_review_package/03_PMF_DISTRIBUTION_VIEWER.html)
- [04_PROP_SUMMARY.csv](2026-04-29/pmf_model_review_package/04_PROP_SUMMARY.csv)
- [05_FULL_PMF_WIDE.csv](2026-04-29/pmf_model_review_package/05_FULL_PMF_WIDE.csv)
- [06_OUTCOME_LEVEL_PROBABILITIES.csv](2026-04-29/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv)
- [machine_readable/model_only.parquet](2026-04-29/pmf_model_review_package/machine_readable/model_only.parquet)
- [MODEL_PERFORMANCE_AND_CALIBRATION.md](2026-04-29/pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md)

**Wizard of Odds**

- [README.md](2026-04-29/wizard_of_odds/README.md)
- [fair_odds_board.csv](2026-04-29/wizard_of_odds/fair_odds_board.csv)
- [full_pmfs_wide.csv](2026-04-29/wizard_of_odds/full_pmfs_wide.csv)
- [full_pmfs_outcome_level.csv](2026-04-29/wizard_of_odds/full_pmfs_outcome_level.csv)
- [market_comparison.csv](2026-04-29/wizard_of_odds/market_comparison.csv)
- [publishable_edges.csv](2026-04-29/wizard_of_odds/publishable_edges.csv)
- [run_manifest.json](2026-04-29/wizard_of_odds/run_manifest.json)

**After-game scoring** (`pending_outcomes`)

- [after_game_summary.md](2026-04-29/after_game_scoring/after_game_summary.md)
- ~~after_game_scoring.csv~~
- ~~calibration_by_stat.csv~~
- ~~calibration_by_role_bucket.csv~~
- ~~clv_by_stat.csv~~
- ~~clv_by_book.csv~~
- [after_game_status.json](2026-04-29/after_game_scoring/after_game_status.json)


## Honest framing

- All emitted PMFs are **model-only**; market columns are reference only.
- TOV PMFs (when emitted) come from Phase 8 calibrators — **no Phase 10D / 10D.2 overlay is wired into production**.
- Freshness, role provenance, and after-game scoring status are recorded verbatim from each delivery's `wizard_of_odds/run_manifest.json` — no fabrication.
- See `docs/daily_pmf_delivery_spec.md` for the row schema and validation contract, and `docs/daily_data_freshness_runbook.md` for the freshness manifest.
