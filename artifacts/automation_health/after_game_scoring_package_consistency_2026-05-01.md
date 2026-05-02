# After-Game Scoring Package Consistency — 2026-05-01

- generated_at_utc: 2026-05-02T08:09:43+00:00
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| after_game_scoring_artifact_exists | yes | deliveries/2026-05-01/after_game_scoring/after_game_scoring.{parquet,csv} |
| after_game_summary_md_exists | yes | deliveries/2026-05-01/after_game_scoring/after_game_summary.md |
| woo_after_game_clv_and_scoring_md_exists | yes | deliveries/2026-05-01/wizard_of_odds/after_game_clv_and_scoring.md |
| pmf_model_review_package_run_manifest_exists | yes | deliveries/2026-05-01/pmf_model_review_package/run_manifest.json |
| model_performance_md_not_stale_when_scored | yes | ok |
| pmf_review_manifest_matches_champion_pointer | yes | ok |
| expected_target_stats_coverage_exists | yes | deliveries/2026-05-01/after_game_scoring/expected_target_stats_coverage.json |
| expected_stats_scored_or_documented_blocked | yes | all_accounted=True missing_undocumented=[] |
| model_vs_market_scoring_exists | yes | deliveries/2026-05-01/after_game_scoring/model_vs_market_scoring.json |
| model_vs_market_section_visible | yes | found in MODEL_PERFORMANCE_AND_CALIBRATION.md or after_game_summary.md |
| no_prediction_files_destroyed | yes | all expected prediction files present |
| woo_manifest_matches_champion_pointer | yes | champion_model_id='challenger-2026-04-30' |
| derek_manifest_matches_champion_pointer | yes | champion_model_id='challenger-2026-04-30' |

## Facts

```
{
  "champion_pointer": {
    "champion_model_id": "challenger-2026-04-30",
    "trained_through_date": "2026-04-30",
    "calibrated_through_date": "2026-04-30",
    "champion_pointer_hash": "ce691fe085d0daee5c7eab9bf4066081"
  },
  "pmf_review_manifest": {
    "champion_model_id": "challenger-2026-04-30",
    "trained_through_date": "2026-04-30",
    "calibrated_through_date": "2026-04-30",
    "champion_pointer_hash": "ce691fe085d0daee5c7eab9bf4066081",
    "after_game_status": "scored",
    "scoring_status": "scored",
    "expected_target_stats": [
      "pts",
      "reb",
      "ast",
      "fg3m",
      "tov"
    ],
    "scored_target_stats": [
      "pts",
      "reb",
      "ast",
      "fg3m"
    ],
    "missing_target_stats": []
  },
  "expected_target_stats_coverage": {
    "expected_target_stats": [
      "pts",
      "reb",
      "ast",
      "fg3m",
      "tov"
    ],
    "scored_target_stats": [
      "pts",
      "reb",
      "ast",
      "fg3m"
    ],
    "missing_target_stats": [],
    "documented_blocked_target_stats": [
      "tov"
    ],
    "all_accounted": true,
    "all_actually_scored": false
  },
  "model_vs_market": {
    "rows_total": 1202,
    "rows_paired": 1202,
    "minimum_sample_passed": true,
    "overall": {
      "delta_brier": 0.01322563112080243,
      "delta_logloss": 0.028488900614722285,
      "market_brier": 0.23601795744796422,
      "market_logloss": 0.6642631878469255,
      "model_brier": 0.24924358856876663,
      "model_logloss": 0.6927520884616478,
      "n": 1202
    }
  },
  "prediction_files_missing": []
}
```
