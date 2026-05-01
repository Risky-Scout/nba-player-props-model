# Daily Training Readiness — 2026-04-28

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-01T03:57:06+00:00 |
| Code commit | 8371d0db98ee |
| Overall pass | yes |
| Blocking failed | 0 |
| Advisory failed | 1 |

## Checks

| Check | Severity | Pass | Detail |
| --- | --- | --- | --- |
| outcomes_through_as_of_date | blocking | yes | rows through 2026-04-28: 83480 |
| future_dates_present_advisory | advisory | yes | 17 rows have date > 2026-04-28; trainer must filter them out |
| required_stat_columns_present | advisory | yes | present=['ast', 'blk', 'fg3m', 'pts', 'reb', 'stl'] missing=['tov'] |
| no_impossible_stat_values | blocking | yes | ok |
| min_training_rows | blocking | yes | 83480 >= 5000 |
| min_per_stat_rows | advisory | yes | enough=['pts', 'reb', 'ast', 'fg3m', 'stl', 'blk'] thin=[] |
| no_duplicate_player_game_rows_on_date | blocking | yes | 0 duplicates on 2026-04-28 |
| odds_snapshots_for_date | advisory | yes | 2 parquet snapshot(s) for 2026-04-28 |
| freshness_manifest_for_date | advisory | NO | missing |
| no_promotion_lock_held | blocking | yes | ok |

## Counts

```
{
  "player_game_stats_total_rows": 83497,
  "player_game_stats_rows_through_as_of": 83480,
  "player_game_stats_rows_on_as_of_date": 80,
  "player_game_stats_rows_after_as_of": 17,
  "stat_columns_present": {
    "pts": "pts",
    "reb": "reb",
    "ast": "ast",
    "fg3m": "fg3m",
    "stl": "stl",
    "blk": "blk"
  },
  "per_stat_rows_through_as_of": {
    "pts": 83480,
    "reb": 83480,
    "ast": 83480,
    "fg3m": 83480,
    "stl": 83480,
    "blk": 83480
  },
  "odds_snapshot_files_on_date": 2
}
```
