# Daily Training Readiness — 2026-04-30

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-01T12:47:07+00:00 |
| Code commit | 1b057af9df36 |
| Overall pass | yes |
| Blocking failed | 0 |
| Advisory failed | 2 |

## Checks

| Check | Severity | Pass | Detail |
| --- | --- | --- | --- |
| outcomes_through_as_of_date | blocking | yes | rows through 2026-04-30: 83568 |
| future_dates_present_advisory | advisory | yes | 0 rows have date > 2026-04-30; trainer must filter them out |
| required_stat_columns_present | advisory | yes | present=['ast', 'blk', 'fg3m', 'pts', 'reb', 'stl'] missing=['tov'] |
| no_impossible_stat_values | blocking | yes | ok |
| min_training_rows | blocking | yes | 83568 >= 5000 |
| min_per_stat_rows | advisory | yes | enough=['pts', 'reb', 'ast', 'fg3m', 'stl', 'blk'] thin=[] |
| no_duplicate_player_game_rows_on_date | blocking | yes | 0 duplicates on 2026-04-30 |
| odds_snapshots_present | advisory | NO | data/odds_api/processed missing — market comparison will be skipped (advisory only) |
| freshness_manifest_present | advisory | NO | data/freshness_manifest/ missing (advisory) |
| no_promotion_lock_held | blocking | yes | ok |

## Counts

```
{
  "player_game_stats_total_rows": 83568,
  "player_game_stats_rows_through_as_of": 83568,
  "player_game_stats_rows_on_as_of_date": 71,
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
    "pts": 83568,
    "reb": 83568,
    "ast": 83568,
    "fg3m": 83568,
    "stl": 83568,
    "blk": 83568
  }
}
```
