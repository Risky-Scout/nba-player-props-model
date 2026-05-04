# Derek PMF Delivery — May 3, 2026

Generated 2026-05-04T15:06:45Z.

## What to open first

1. **Derek snapshot index** — [derek_game_snapshots/README.md](derek_game_snapshots/README.md)
2. **Current-live for Raptors @ Cavaliers** — [snapshot_report.md](derek_game_snapshots/21682000/current_live/snapshot_report.md)
3. **Current-live for Magic @ Pistons** — [snapshot_report.md](derek_game_snapshots/21684819/current_live/snapshot_report.md)
4. **Edge reasonability audit** — [../../artifacts/automation_health/derek_edge_root_cause_2026-05-03.md](../../artifacts/automation_health/derek_edge_root_cause_2026-05-03.md)
5. **Edge calibration audit** — [../../artifacts/automation_health/derek_edge_calibration_2026-05-03.md](../../artifacts/automation_health/derek_edge_calibration_2026-05-03.md)
6. **Daily model report** — see `artifacts/model_daily_reports/<trained_through_date>/daily_model_training_report.md`

## Snapshot status by game

| Matchup | Current-live | T-minus-25 | Close-lock |
| --- | --- | --- | --- |
| Raptors @ Cavaliers | Available | Missed during setup window; documented, not backfilled | Missed during setup window; documented, not backfilled |
| Magic @ Pistons | Available, stale baseline | Missed during setup window; documented, not backfilled | Missed during setup window; documented, not backfilled |

Missed snapshots are documented rather than backfilled. This avoids creating fake pre-tip output after a game has started. Going forward the dispatcher's snapshot state machine prevents silent misses by classifying every (game, snapshot type) pair as one of: Available, Scheduled, Pending dispatch, Available (late but pre-tip), or Missed during setup window.

## What each file means

- **snapshot_report.md** — plain-English executive summary of one snapshot: top edges, top contextual minutes deltas, driver attribution, publishability gates.
- **market_comparison.csv** — per-prop model probability vs market no-vig probability, with the Phase 13X edge_publish_status / edge_reasonability_status columns. Edges marked `WATCHLIST` / `REVIEW` / `PUBLISH_BLOCKER` are not for action.
- **full_pmf_wide.csv** — full per-prop PMF + market probabilities.
- **outcome_level_probabilities.csv** — long-form (player, stat, k, p_k) view of the PMF.
- **pmf_driver_decomposition.md** — per-row contextual minutes / rate deltas with Phase 13S driver attribution.
- **lineup_injury_impact_report.md** — lineup confirmation, BDL injury fetch, and counts of confirmed starters / bench / confirmed out.
- **direct_lineup_impact_report.md** — Phase 13S direct-lineup driver attribution: starter / bench changes, lineup composition impact.
- **missed_snapshot_report.md** — written when a near-tip snapshot was missed post-tip; explains the miss and links back to the audit trail.

## PMF variance experience study

- [pmf_variance_experience_2026-05-03.md](https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/pmf_variance_experience_2026-05-03.md)
- This is an actuarial-style actual-to-expected study for settled rows. It checks PMF mean calibration, PMF variance calibration, quantile coverage, and model-vs-market scoring. In this first settled sample, PMF variance is reasonably close overall, but the model under-projects means and trails market on Brier/logloss, so this is a diagnostic and improvement report rather than a market-superiority claim.

## Daily location going forward

- Future daily delivery index: `deliveries/YYYY-MM-DD/README.md`
- Future Derek snapshot index: `deliveries/YYYY-MM-DD/derek_game_snapshots/README.md`
- Future per-game snapshots: `deliveries/YYYY-MM-DD/derek_game_snapshots/<game_id>/{current_live,t_minus_25,close_lock}/`

