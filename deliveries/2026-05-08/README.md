# Derek PMF Delivery — May 8, 2026

Generated 2026-05-09T00:08:44Z.

## What to open first

1. **Derek snapshot index** — [derek_game_snapshots/README.md](derek_game_snapshots/README.md)
2. **Edge reasonability audit** — [../../artifacts/automation_health/derek_edge_root_cause_2026-05-08.md](../../artifacts/automation_health/derek_edge_root_cause_2026-05-08.md)
3. **Edge calibration audit** — [../../artifacts/automation_health/derek_edge_calibration_2026-05-08.md](../../artifacts/automation_health/derek_edge_calibration_2026-05-08.md)
4. **Daily model report** — see `artifacts/model_daily_reports/<trained_through_date>/daily_model_training_report.md`

## Snapshot status by game

| Matchup | Current-live | T-minus-25 | Close-lock |
| --- | --- | --- | --- |
| Spurs @ Timberwolves | Pending dispatch | Pending dispatch | Pending dispatch |
| Knicks @ 76ers | Pending dispatch | Missed during setup window; documented, not backfilled | Missed during setup window; documented, not backfilled |

Missed snapshots are documented rather than backfilled. This avoids creating fake pre-tip output after a game has started. Going forward the dispatcher's snapshot state machine prevents silent misses by classifying every (game, snapshot type) pair as one of: Available, Scheduled, Pending dispatch, Available (late but pre-tip), or Missed during setup window.

## Validated Derek files

Per snapshot folder (`derek_game_snapshots/<game_id>/<snapshot_type>/`):

- **snapshot_report.md** — plain-English summary of one snapshot: top edges, top contextual minutes deltas, driver attribution, publishability gates.
- **market_comparison.csv** — per-prop model probability vs market no-vig probability, with `edge_publish_status` / `edge_reasonability_status` columns. Rows marked `WATCHLIST` / `REVIEW` / `PUBLISH_BLOCKER` are not for action.
- **full_pmf_wide.csv** — full per-prop PMF + market probabilities, one row per (player, stat, side, line, book).
- **outcome_level_probabilities.csv** — long-form PMF view. Phase 13AB regenerated this file from the canonical PMF JSON: each prop's PMF expands into one row per possible outcome `k`, with `p_k` summing to 1 per prop. Verifier: `scripts/verify_derek_outcome_level_probabilities.py`.
- **pmf_driver_decomposition.md** — per-row contextual minutes / rate deltas with Phase 13S driver attribution.
- **lineup_injury_impact_report.md** — lineup confirmation, BDL injury fetch, counts of confirmed starters / bench / confirmed out.
- **direct_lineup_impact_report.md** — Phase 13S direct-lineup driver attribution: starter / bench changes, lineup composition impact.
- **missed_snapshot_report.md** — written when a near-tip snapshot was missed post-tip; explains the miss and links back to the audit trail.

## Model status and calibration note

The 2026-05-08 package includes live-context PMF snapshots and a new actuarial-style PMF variance experience study. The experience study is based on the trailing 60-day settled sample of player-prop rows. It is a diagnostic review of settled morning / current rows, not a mature T-minus-25 or close-lock live-context sample yet — those snapshots have not accumulated enough joinable game stats to score meaningfully.

The first study is useful but mixed: PMF variance is reasonably close overall (variance A/E in the 0.80–1.20 well-calibrated band, standardized residual sd near 1.00), but the model under-projects means (mean A/E above 1.0) and trails the market on binary scoring in this sample (Brier and logloss both higher than the market no-vig baseline). Read this as a recalibration roadmap, not a market-superiority claim.

**Next improvements (in priority order):**

1. Mean calibration — the mean A/E bias points at the role-aware mean centering in the contextual stack.
2. Low-line discrete stat handling — fg3m / stl / blk / tov at lines ≤ 1.5 are the most miscalibrated bucket family.
3. fg3m dispersion — variance A/E above 2 means the PMF is materially too narrow on threes.
4. Bucket-level recalibration — high-p0 props and starter minutes are over-dispersed; they compress cleanly with isotonic.
5. More settled t_minus_25 / close_lock snapshots — the prospective live-context sample still needs to build.
6. Confirmed-lineup and injury-context experience tracking — Source A coverage will let us compare confirmed-lineup rows against projected rows once enough delivery dates accumulate.

## PMF variance experience study

- Latest study: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/pmf_variance_experience_2026-05-08.md
- Index: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/README.md
- Sample: trailing 60-day window of settled player-prop rows, morning / current settled rows only. Headline metrics — mean A/E, variance A/E, model Brier vs market Brier, model logloss vs market logloss — are reported in the linked study.
- This is a diagnostic and improvement report. Do not claim market superiority from this sample.

## Daily location going forward

- Future daily delivery index: `deliveries/YYYY-MM-DD/README.md`
- Future Derek snapshot index: `deliveries/YYYY-MM-DD/derek_game_snapshots/README.md`
- Future per-game snapshots: `deliveries/YYYY-MM-DD/derek_game_snapshots/<game_id>/{current_live,t_minus_25,close_lock}/`

