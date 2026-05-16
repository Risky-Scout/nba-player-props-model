# Daily Training Readiness — 2026-05-15

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-16T22:26:53+00:00 |
| Code commit | 9c3ff8d4c6ca |
| Overall pass | yes |
| Blocking failed | 0 |
| Advisory failed | 2 |

## Checks

| Check | Severity | Pass | Detail |
| --- | --- | --- | --- |
| outcomes_through_as_of_date | blocking | yes | rows through 2026-05-15: 84196 |
| future_dates_present_advisory | advisory | yes | 0 rows have date > 2026-05-15; trainer must filter them out |
| required_stat_columns_present | advisory | yes | present=['ast', 'blk', 'fg3m', 'pts', 'reb', 'stl'] missing=['tov'] |
| no_impossible_stat_values | blocking | yes | ok |
| min_training_rows | blocking | yes | 84196 >= 5000 |
| min_per_stat_rows | advisory | yes | enough=['pts', 'reb', 'ast', 'fg3m', 'stl', 'blk'] thin=[] |
| no_duplicate_player_game_rows_on_date | blocking | yes | 0 duplicates on 2026-05-15 |
| odds_snapshots_present | advisory | NO | data/odds_api/processed missing — market comparison will be skipped (advisory only) |
| freshness_manifest_present | advisory | NO | data/freshness_manifest/ missing (advisory) |
| no_promotion_lock_held | blocking | yes | ok |

## Counts

```
{
  "player_game_stats_total_rows": 84196,
  "player_game_stats_rows_through_as_of": 84196,
  "player_game_stats_rows_on_as_of_date": 54,
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
    "pts": 84196,
    "reb": 84196,
    "ast": 84196,
    "fg3m": 84196,
    "stl": 84196,
    "blk": 84196
  }
}
```
