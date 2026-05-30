# Spurs @ Thunder — Current-live PMF snapshot

## Summary

- Matchup: **Spurs @ Thunder** (Away: Spurs, Home: Thunder)
- Snapshot: Current-live
- Snapshot mode: `production_live_current`
- Props emitted: **41**
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
| Julian Champagnie | blk | OVER | 0.500 | 0.636 | 0.338 | +0.298 | +0.780 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_THIN | 19 |
| Kenrich Williams | fg3m | OVER | 0.500 | 0.716 | 0.429 | +0.287 | +0.590 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| Shai Gilgeous-Alexander | pts | UNDER | 30.500 | 0.759 | 0.490 | +0.272 | +0.481 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 285 |
| Alex Caruso | fg3m | UNDER | 1.500 | 0.650 | 0.389 | +0.261 | +0.605 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 196 |
| Alex Caruso | pts | UNDER | 10.500 | 0.726 | 0.475 | +0.255 | +0.452 | PUBLISH_BLOCKER | CALIBRATION_SAMPLE_LIMITED | 61 |
| Shai Gilgeous-Alexander | blk | UNDER | 0.500 | 0.664 | 0.435 | +0.229 | +0.441 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_THIN | 19 |
| Keldon Johnson | fg3m | OVER | 0.500 | 0.807 | 0.579 | +0.228 | +0.321 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| Isaiah Joe | fg3m | OVER | 0.500 | 0.721 | 0.508 | +0.212 | +0.347 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| Alex Caruso | reb | UNDER | 3.500 | 0.721 | 0.512 | +0.210 | +0.377 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 221 |
| Jared McCain | pts | UNDER | 13.500 | 0.707 | 0.507 | +0.203 | +0.322 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 994 |
| Isaiah Hartenstein | blk | UNDER | 0.500 | 0.711 | 0.512 | +0.199 | +0.330 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 76 |
| Alex Caruso | ast | UNDER | 2.500 | 0.684 | 0.489 | +0.195 | +0.367 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 136 |
| Victor Wembanyama | pts | UNDER | 26.500 | 0.677 | 0.501 | +0.178 | +0.321 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 994 |
| Jaylin Williams | stl | UNDER | 0.500 | 0.770 | 0.598 | +0.172 | +0.206 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 82 |
| Victor Wembanyama | reb | UNDER | 12.500 | 0.654 | 0.486 | +0.170 | +0.296 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 30 |
| Cason Wallace | fg3m | UNDER | 1.500 | 0.661 | 0.495 | +0.166 | +0.322 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 283 |
| Luguentz Dort | stl | UNDER | 0.500 | 0.667 | 0.502 | +0.165 | +0.273 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 82 |
| Victor Wembanyama | ast | UNDER | 3.500 | 0.744 | 0.582 | +0.164 | +0.215 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 207 |
| Shai Gilgeous-Alexander | fg3m | UNDER | 1.500 | 0.681 | 0.536 | +0.145 | +0.225 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 283 |
| Cason Wallace | ast | UNDER | 2.500 | 0.606 | 0.462 | +0.145 | +0.272 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 136 |

## Technical audit details

- Game ID: `21713534`
- Away Team: Spurs
- Home Team: Thunder
- Game start time UTC: `2026-05-31T00:10:00Z`
- Snapshot target time UTC: `2026-05-30T21:12:56Z`
- Actual run started at UTC: `2026-05-30T21:12:56Z`
- Snapshot validity status: `on_time_or_current_live`
- Champion model ID: `challenger-2026-05-29`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-05-29`
- Calibrated through date: `2026-05-29`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
