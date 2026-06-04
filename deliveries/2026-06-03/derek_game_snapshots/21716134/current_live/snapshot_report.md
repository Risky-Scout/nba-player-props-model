# Knicks @ Spurs — Current-live PMF snapshot

## Summary

- Matchup: **Knicks @ Spurs** (Away: Knicks, Home: Spurs)
- Snapshot: Current-live
- Snapshot mode: `production_live_current`
- Props emitted: **29**
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
- Market odds are used for **edge only**, never as model features (`market_odds_used_as_features=False`).
- No post-tip data was used in any prediction (`no_post_tip_data_used=True`).

## Top edges (subject to publishability gates)

Sort: largest |raw_edge| first. `edge_publish_status` is the gate that determines whether a row is showable; rows without `ACTIONABLE_REVIEWED` are not for action.

| player_name | stat | side | line | model_prob | market_prob | raw_edge | ev | edge_publish_status | calibration_support_status | calibration_bucket_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | reb | UNDER | 11.500 | 0.769 | 0.484 | +0.287 | +0.546 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 53 |
| Karl-Anthony Towns | blk | UNDER | 0.500 | 0.686 | 0.404 | +0.282 | +0.715 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_THIN | 24 |
| Victor Wembanyama | pts | UNDER | 26.500 | 0.737 | 0.487 | +0.252 | +0.452 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 296 |
| Mitchell Robinson | blk | UNDER | 0.500 | 0.682 | 0.456 | +0.226 | +0.399 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_THIN | 24 |
| Stephon Castle | ast | UNDER | 6.500 | 0.677 | 0.468 | +0.210 | +0.401 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 97 |
| Julian Champagnie | reb | UNDER | 5.500 | 0.695 | 0.499 | +0.197 | +0.327 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 400 |
| Victor Wembanyama | stl | UNDER | 1.500 | 0.817 | 0.620 | +0.197 | +0.242 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 62 |
| Luke Kornet | reb | UNDER | 2.500 | 0.666 | 0.474 | +0.193 | +0.345 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 12 |
| Victor Wembanyama | ast | UNDER | 3.500 | 0.785 | 0.601 | +0.185 | +0.260 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 219 |
| Keldon Johnson | reb | UNDER | 3.500 | 0.760 | 0.579 | +0.183 | +0.274 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 400 |
| Stephon Castle | reb | UNDER | 4.500 | 0.608 | 0.443 | +0.166 | +0.326 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 400 |
| Karl-Anthony Towns | pts | UNDER | 16.500 | 0.654 | 0.491 | +0.165 | +0.277 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 1034 |
| Devin Vassell | pts | UNDER | 13.500 | 0.667 | 0.506 | +0.163 | +0.303 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 1034 |
| Karl-Anthony Towns | reb | UNDER | 11.500 | 0.647 | 0.502 | +0.146 | +0.294 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 30 |
| Josh Hart | reb | UNDER | 8.500 | 0.694 | 0.553 | +0.141 | +0.200 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 297 |
| Devin Vassell | reb | UNDER | 4.500 | 0.702 | 0.563 | +0.140 | +0.222 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 400 |
| Karl-Anthony Towns | ast | OVER | 3.500 | 0.698 | 0.566 | +0.131 | +0.179 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 219 |
| Dylan Harper | ast | UNDER | 2.500 | 0.590 | 0.459 | +0.131 | +0.268 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 148 |
| Devin Vassell | blk | UNDER | 0.500 | 0.695 | 0.566 | +0.129 | +0.158 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 77 |
| De'Aaron Fox | ast | UNDER | 5.500 | 0.566 | 0.458 | +0.109 | +0.190 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 219 |

## Technical audit details

- Game ID: `21716134`
- Away Team: Knicks
- Home Team: Spurs
- Game start time UTC: `2026-06-04T00:30:00Z`
- Snapshot target time UTC: `2026-06-03T22:34:15Z`
- Actual run started at UTC: `2026-06-03T22:34:15Z`
- Snapshot validity status: `on_time_or_current_live`
- Champion model ID: `challenger-2026-06-02`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-06-02`
- Calibrated through date: `2026-06-02`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
