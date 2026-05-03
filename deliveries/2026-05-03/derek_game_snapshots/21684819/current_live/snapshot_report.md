# Magic @ Pistons — Current-live PMF snapshot (post-tip stale baseline)

## Summary

- Matchup: **Magic @ Pistons** (Away: Magic, Home: Pistons)
- Snapshot: Current-live (post-tip stale baseline)
- Snapshot mode: `production_live_current`
- Props emitted: **33**
- PMFs recomputed: **True**
- Lineup status: BDL did not return confirmed starters at this timestamp; this is a baseline snapshot
- Injury status: Injury / availability inherited from the canonical predictions slate
- Edge status: See `market_comparison.csv` `edge_publish_status` column. Current-live without confirmed lineups is at most `WATCHLIST_NOT_CONFIRMED_LINEUP`.

## How to read this

- `model_prob` is the model's **win probability** under the sportsbook push-excluded convention. For decimal lines (e.g. `UNDER 8.5`), `model_prob = P(stat < 8.5)`. For integer lines (e.g. `UNDER 1.0`), `model_prob = P(stat < 1) / (1 − P(stat = 1))`.
- `market_prob` is the no-vig probability implied by the same side's American odds, after stripping the vig.
- `raw_edge = model_prob − market_prob`. `ev` uses the same push-excluded convention; integer-line rows also report a push-aware EV in the audit JSON.
- `edge_publish_status` filters which rows are eligible to show Derek as actionable: `PUBLISH_BLOCKER` > `REVIEW_LARGE_EDGE` > `REVIEW_PUSH_LINE` > `WATCHLIST_NOT_CONFIRMED_LINEUP` > `ACTIONABLE_REVIEWED`. Current-live without confirmed lineups is never higher than `WATCHLIST_NOT_CONFIRMED_LINEUP`.
- `calibration_support_status` reports whether the historical scoring corpus has enough settled rows in the same (stat, side, line bucket, edge bucket) to trust the edge: `CALIBRATION_SUPPORTED` (n ≥ 100) > `CALIBRATION_SAMPLE_LIMITED` (30 ≤ n < 100) > `CALIBRATION_SAMPLE_THIN` (n < 30) > `CALIBRATION_REVIEW_REQUIRED` (model worse than market by ≥ 0.05 logloss).
- `p0` is the modeled probability the player records exactly zero of this stat. PMF tail mass is summarized in `pmf_mean` / `pmf_variance`.

## Important caveats

- **BDL did not return confirmed lineup rows at this timestamp.** This snapshot is a best-available baseline; it does not directly reflect official starter status. The dispatcher will produce confirmed-lineup snapshots in the T-minus-25 and close-lock windows.
- **This run executed after the game tipped.** The PMFs are the canonical pre-tip slate scored by the contextual engine — no in-game data leaks in — but the timestamp is post-tip. The dispatcher refuses to regenerate current-live for already-tipped games going forward.
- Market odds are used for **edge only**, never as model features (`market_odds_used_as_features=False`).
- No post-tip data was used in any prediction (`no_post_tip_data_used=True`).

## Top edges (subject to publishability gates)

Sort: largest |raw_edge| first. `edge_publish_status` is the gate that determines whether a row is showable; rows without `ACTIONABLE_REVIEWED` are not for action.

| player_name | stat | side | line | model_prob | market_prob | raw_edge | ev | edge_publish_status | calibration_support_status | calibration_bucket_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jamal Cain | reb | UNDER | 3.500 | 0.754 | 0.557 | +0.197 | +0.348 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 156 |
| Jalen Suggs | blk | UNDER | 0.500 | 0.621 | 0.426 | +0.194 | +0.384 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Isaiah Stewart | reb | OVER | 3.500 | 0.617 | 0.423 | +0.194 | +0.443 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 156 |
| Desmond Bane | fg3m | UNDER | 2.500 | 0.699 | 0.506 | +0.193 | +0.398 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 78 |
| Tobias Harris | pts | UNDER | 17.500 | 0.673 | 0.483 | +0.190 | +0.346 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 383 |
| Cade Cunningham | pts | UNDER | 28.500 | 0.675 | 0.490 | +0.185 | +0.336 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 383 |
| Ausar Thompson | blk | OVER | 1.500 | 0.625 | 0.442 | +0.182 | +0.393 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Tobias Harris | blk | OVER | 0.500 | 0.647 | 0.468 | +0.180 | +0.347 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Anthony Black | pts | UNDER | 11.500 | 0.690 | 0.517 | +0.173 | +0.289 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 383 |
| Daniss Jenkins | ast | UNDER | 2.500 | 0.733 | 0.585 | +0.148 | +0.238 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 33 |
| Tobias Harris | stl | UNDER | 1.500 | 0.786 | 0.641 | +0.145 | +0.189 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Duncan Robinson | fg3m | UNDER | 2.500 | 0.686 | 0.544 | +0.142 | +0.198 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 78 |
| Jalen Suggs | ast | UNDER | 4.500 | 0.575 | 0.441 | +0.134 | +0.254 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 82 |
| Cade Cunningham | reb | OVER | 5.500 | 0.666 | 0.536 | +0.130 | +0.198 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 156 |
| Jalen Duren | stl | UNDER | 0.500 | 0.629 | 0.503 | +0.126 | +0.176 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Anthony Black | blk | UNDER | 0.500 | 0.635 | 0.512 | +0.123 | +0.187 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Cade Cunningham | ast | UNDER | 8.500 | 0.621 | 0.499 | +0.122 | +0.185 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 115 |
| Daniss Jenkins | fg3m | OVER | 0.500 | 0.612 | 0.495 | +0.117 | +0.143 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 11 |
| Daniss Jenkins | stl | UNDER | 0.500 | 0.647 | 0.544 | +0.104 | +0.113 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Tristan Da Silva | reb | UNDER | 2.500 | 0.584 | 0.483 | +0.101 | +0.169 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 23 |

## Technical audit details

- Game ID: `21684819`
- Away Team: Magic
- Home Team: Pistons
- Game start time UTC: `2026-05-03T19:40:00Z`
- Snapshot target time UTC: `2026-05-03T20:38:19Z`
- Actual run started at UTC: `2026-05-03T20:38:19Z`
- Snapshot validity status: `post_tip_stale_baseline`
- Champion model ID: `challenger-2026-04-30`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-04-30`
- Calibrated through date: `2026-04-30`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed_canonical_current`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
