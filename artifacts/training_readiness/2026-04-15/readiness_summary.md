# Daily Training Readiness — 2026-04-15

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-01T02:42:50+00:00 |
| Code commit | d120889c1b2f |
| Overall pass | yes |
| Blocking failed | 0 |
| Advisory failed | 2 |

## Checks

| Check | Severity | Pass | Detail |
| --- | --- | --- | --- |
| outcomes_through_as_of_date | blocking | yes | rows through 2026-04-15: 82627 |
| future_dates_present_advisory | advisory | yes | 870 rows have date > 2026-04-15; trainer must filter them out |
| required_stat_columns_present | advisory | yes | present=['ast', 'blk', 'fg3m', 'pts', 'reb', 'stl'] missing=['tov'] |
| no_impossible_stat_values | blocking | yes | ok |
| min_training_rows | blocking | yes | 82627 >= 5000 |
| min_per_stat_rows | advisory | yes | enough=['pts', 'reb', 'ast', 'fg3m', 'stl', 'blk'] thin=[] |
| no_duplicate_player_game_rows_on_date | blocking | yes | 0 duplicates on 2026-04-15 |
| odds_snapshots_for_date | advisory | NO | 0 parquet snapshot(s) for 2026-04-15 |
| freshness_manifest_for_date | advisory | NO | missing |
| no_promotion_lock_held | blocking | yes | ok |

## Counts

```
{
  "player_game_stats_total_rows": 83497,
  "player_game_stats_rows_through_as_of": 82627,
  "player_game_stats_rows_on_as_of_date": 34,
  "player_game_stats_rows_after_as_of": 870,
  "stat_columns_present": {
    "pts": "pts",
    "reb": "reb",
    "ast": "ast",
    "fg3m": "fg3m",
    "stl": "stl",
    "blk": "blk"
  },
  "per_stat_rows_through_as_of": {
    "pts": 82627,
    "reb": 82627,
    "ast": 82627,
    "fg3m": 82627,
    "stl": 82627,
    "blk": 82627
  },
  "odds_snapshot_files_on_date": 0
}
```
