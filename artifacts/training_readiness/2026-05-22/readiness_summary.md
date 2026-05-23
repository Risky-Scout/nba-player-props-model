# Daily Training Readiness — 2026-05-22

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-23T19:45:22+00:00 |
| Code commit | c49e8f23dc3a |
| Overall pass | yes |
| Blocking failed | 0 |
| Advisory failed | 2 |

## Checks

| Check | Severity | Pass | Detail |
| --- | --- | --- | --- |
| outcomes_through_as_of_date | blocking | yes | rows through 2026-05-22: 84338 |
| future_dates_present_advisory | advisory | yes | 0 rows have date > 2026-05-22; trainer must filter them out |
| required_stat_columns_present | advisory | yes | present=['ast', 'blk', 'fg3m', 'pts', 'reb', 'stl'] missing=['tov'] |
| no_impossible_stat_values | blocking | yes | ok |
| min_training_rows | blocking | yes | 84338 >= 5000 |
| min_per_stat_rows | advisory | yes | enough=['pts', 'reb', 'ast', 'fg3m', 'stl', 'blk'] thin=[] |
| no_duplicate_player_game_rows_on_date | blocking | yes | 0 duplicates on 2026-05-22 |
| odds_snapshots_present | advisory | NO | data/odds_api/processed missing — market comparison will be skipped (advisory only) |
| freshness_manifest_present | advisory | NO | data/freshness_manifest/ missing (advisory) |
| no_promotion_lock_held | blocking | yes | ok |

## Counts

```
{
  "player_game_stats_total_rows": 84338,
  "player_game_stats_rows_through_as_of": 84338,
  "player_game_stats_rows_on_as_of_date": 28,
  "player_game_stats_rows_after_as_of": 0,
  "stat_columns_present": {
    "pts": "pts",
    "reb": "reb",
    "ast": "ast",
    "fg3m": "fg3m",
    "stl": "stl",
    "blk": "blk"
  },
  "per_stat_rows_through_as_of": {
    "pts": 84338,
    "reb": 84338,
    "ast": 84338,
    "fg3m": 84338,
    "stl": 84338,
    "blk": 84338
  }
}
```
