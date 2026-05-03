# Raptors @ Cavaliers — Current-live PMF snapshot

## Summary

- Matchup: **Raptors @ Cavaliers** (Away: Raptors, Home: Cavaliers)
- Snapshot: Current-live
- Snapshot mode: `production_live_current`
- Props emitted: **36**
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
| Evan Mobley | blk | UNDER | 1.500 | 0.789 | 0.473 | +0.316 | +0.617 | PUBLISH_BLOCKER | CALIBRATION_SAMPLE_THIN | 0 |
| Donovan Mitchell | fg3m | UNDER | 2.500 | 0.735 | 0.479 | +0.257 | +0.529 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 69 |
| Scottie Barnes | ast | UNDER | 7.500 | 0.668 | 0.440 | +0.228 | +0.482 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 62 |
| Collin Murray-Boyles | pts | UNDER | 12.500 | 0.693 | 0.469 | +0.225 | +0.442 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 157 |
| Scottie Barnes | fg3m | UNDER | 1.000 | 0.746 | 0.526 | +0.220 | +0.978 | REVIEW_PUSH_LINE | CALIBRATION_SAMPLE_THIN | 7 |
| Jamal Shead | ast | UNDER | 5.500 | 0.668 | 0.467 | +0.201 | +0.430 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 67 |
| RJ Barrett | pts | UNDER | 23.500 | 0.708 | 0.508 | +0.200 | +0.334 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 383 |
| James Harden | blk | UNDER | 0.500 | 0.755 | 0.561 | +0.194 | +0.269 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Sandro Mamukelashvili | reb | OVER | 3.500 | 0.627 | 0.435 | +0.192 | +0.373 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 156 |
| Jamal Shead | pts | UNDER | 8.500 | 0.676 | 0.488 | +0.189 | +0.333 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 28 |
| Ja'Kobe Walter | reb | UNDER | 3.500 | 0.654 | 0.472 | +0.182 | +0.340 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 156 |
| Scottie Barnes | reb | UNDER | 6.500 | 0.624 | 0.446 | +0.178 | +0.310 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_REVIEW_REQUIRED | 147 |
| Donovan Mitchell | stl | UNDER | 1.500 | 0.789 | 0.612 | +0.178 | +0.283 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| James Harden | stl | UNDER | 1.500 | 0.790 | 0.615 | +0.175 | +0.284 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| James Harden | fg3m | UNDER | 2.500 | 0.624 | 0.451 | +0.173 | +0.342 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 78 |
| Donovan Mitchell | pts | UNDER | 25.500 | 0.676 | 0.505 | +0.171 | +0.264 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 383 |
| RJ Barrett | ast | UNDER | 3.500 | 0.655 | 0.486 | +0.170 | +0.297 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 82 |
| Sam Merrill | stl | UNDER | 0.500 | 0.701 | 0.556 | +0.145 | +0.175 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Scottie Barnes | blk | UNDER | 1.500 | 0.733 | 0.589 | +0.144 | +0.177 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 0 |
| Dennis Schroder | fg3m | OVER | 0.500 | 0.624 | 0.485 | +0.138 | +0.191 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 11 |

## Push-line audit rows

Integer lines where the model's probability of exact-line outcomes is non-trivial. The displayed `ev` uses the sportsbook push-excluded convention; `ev_recomputed_pushinc` is the honest dollar-EV with push paid as $0.

| player_name | stat | side | line | push_prob | ev | ev_recomputed | ev_recomputed_pushinc | edge_publish_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Scottie Barnes | fg3m | UNDER | 1.000 | 0.326 | +0.978 | +0.978 | +0.659 | REVIEW_PUSH_LINE |

## Technical audit details

- Game ID: `21682000`
- Away Team: Raptors
- Home Team: Cavaliers
- Game start time UTC: `2026-05-03T23:40:00Z`
- Snapshot target time UTC: `2026-05-03T20:54:06Z`
- Actual run started at UTC: `2026-05-03T20:54:06Z`
- Snapshot validity status: `on_time_or_current_live`
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
