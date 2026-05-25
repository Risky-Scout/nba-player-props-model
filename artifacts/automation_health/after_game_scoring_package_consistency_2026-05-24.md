# After-Game Scoring Package Consistency — 2026-05-24

- generated_at_utc: 2026-05-25T11:11:44+00:00
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| after_game_scoring_artifact_exists | yes | deliveries/2026-05-24/after_game_scoring/after_game_scoring.{parquet,csv} |
| after_game_summary_md_exists | yes | deliveries/2026-05-24/after_game_scoring/after_game_summary.md |
| woo_after_game_clv_and_scoring_md_exists | yes | deliveries/2026-05-24/wizard_of_odds/after_game_clv_and_scoring.md |
| pmf_model_review_package_run_manifest_exists | yes | deliveries/2026-05-24/pmf_model_review_package/run_manifest.json |
| model_performance_md_not_stale_when_scored | yes | ok |
| pmf_review_manifest_matches_champion_pointer | yes | ok |
| expected_target_stats_coverage_exists | yes | deliveries/2026-05-24/after_game_scoring/expected_target_stats_coverage.json |
| expected_stats_scored_or_documented_blocked | yes | all_accounted=True missing_undocumented=[] |
| model_vs_market_scoring_exists | yes | deliveries/2026-05-24/after_game_scoring/model_vs_market_scoring.json |
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
    "champion_pointer_hash": "f1b07b5b90d474a4a6527c4a9252cba5"
  },
  "pmf_review_manifest": {
    "champion_model_id": "challenger-2026-04-30",
    "trained_through_date": "2026-04-30",
    "calibrated_through_date": "2026-04-30",
    "champion_pointer_hash": "f1b07b5b90d474a4a6527c4a9252cba5",
    "after_game_status": "scored",
    "scoring_status": "scored",
    "expected_target_stats": [
      "pts",
      "reb",
      "ast",
      "fg3m",
      "tov",
      "stl",
      "blk",
      "stocks",
      "pa",
      "pr",
      "pra"
    ],
    "scored_target_stats": [
      "pts",
      "reb",
      "ast",
      "fg3m",
      "tov",
      "stl",
      "blk",
      "stocks",
      "pa",
      "pr",
      "pra"
    ],
    "missing_target_stats": []
  },
  "expected_target_stats_coverage": {
    "expected_target_stats": [
      "pts",
      "reb",
      "ast",
      "fg3m",
      "tov",
      "stl",
      "blk",
      "stocks",
      "pa",
      "pr",
      "pra"
    ],
    "scored_target_stats": [
      "pts",
      "reb",
      "ast",
      "fg3m",
      "tov",
      "stl",
      "blk",
      "stocks",
      "pa",
      "pr",
      "pra"
    ],
    "missing_target_stats": [],
    "documented_blocked_target_stats": [],
    "all_accounted": true,
    "all_actually_scored": true
  },
  "model_vs_market": {
    "rows_total": null,
    "rows_paired": null,
    "minimum_sample_passed": null,
    "overall": null
  },
  "prediction_files_missing": [],
  "lineup_phase_executed_today": true
}
```
