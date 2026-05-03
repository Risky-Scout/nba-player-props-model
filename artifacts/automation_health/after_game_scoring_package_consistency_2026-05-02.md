# After-Game Scoring Package Consistency — 2026-05-02

- generated_at_utc: 2026-05-03T08:21:10+00:00
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| after_game_scoring_artifact_exists | yes | deliveries/2026-05-02/after_game_scoring/after_game_scoring.{parquet,csv} |
| after_game_summary_md_exists | yes | deliveries/2026-05-02/after_game_scoring/after_game_summary.md |
| woo_after_game_clv_and_scoring_md_exists | yes | deliveries/2026-05-02/wizard_of_odds/after_game_clv_and_scoring.md |
| pmf_model_review_package_run_manifest_exists | yes | deliveries/2026-05-02/pmf_model_review_package/run_manifest.json |
| model_performance_md_not_stale_when_scored | yes | ok |
| pmf_review_manifest_matches_champion_pointer | yes | ok |
| expected_target_stats_coverage_exists | yes | deliveries/2026-05-02/after_game_scoring/expected_target_stats_coverage.json |
| expected_stats_scored_or_documented_blocked | yes | all_accounted=True missing_undocumented=[] |
| model_vs_market_scoring_exists | yes | deliveries/2026-05-02/after_game_scoring/model_vs_market_scoring.json |
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
    "champion_pointer_hash": "9dc24f5d531ca31ee053e4a1ec6267a0"
  },
  "pmf_review_manifest": {
    "champion_model_id": "challenger-2026-04-30",
    "trained_through_date": "2026-04-30",
    "calibrated_through_date": "2026-04-30",
    "champion_pointer_hash": "9dc24f5d531ca31ee053e4a1ec6267a0",
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
    "rows_total": 406,
    "rows_paired": 406,
    "minimum_sample_passed": true,
    "overall": {
      "delta_brier": 0.05552741851279544,
      "delta_logloss": 0.13676583058275626,
      "market_brier": 0.23703766005352775,
      "market_logloss": 0.6661274089055593,
      "model_brier": 0.2925650785663232,
      "model_logloss": 0.8028932394883157,
      "n": 406
    }
  },
  "prediction_files_missing": []
}
```
