# Derek PMF Delivery — May 3, 2026

Generated 2026-05-03T23:36:31Z.

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
| Raptors @ Cavaliers | Available | Pending dispatch | Pending dispatch |
| Magic @ Pistons | Available, stale baseline | Missed during setup window; documented, not backfilled | Missed during setup window; documented, not backfilled |

Missed snapshots are documented rather than backfilled. This avoids creating fake pre-tip output after a game has started. Going forward the dispatcher's snapshot state machine prevents silent misses by classifying every (game, snapshot type) pair as one of: Available, Scheduled, Pending dispatch, Available (late but pre-tip), or Missed during setup window.

## Validated Derek files

Per snapshot folder (`derek_game_snapshots/<game_id>/<snapshot_type>/`):

- **snapshot_report.md** — plain-English summary of one snapshot: top edges, top contextual minutes deltas, driver attribution, publishability gates.
- **market_comparison.csv** — per-prop model probability vs market no-vig probability, with `edge_publish_status` / `edge_reasonability_status` columns. Rows marked `WATCHLIST` / `REVIEW` / `PUBLISH_BLOCKER` are not for action.
- **full_pmf_wide.csv** — full per-prop PMF + market probabilities, one row per (player, stat, side, line, book).
- **outcome_level_probabilities.csv** — long-form PMF view. The Phase 13AB repair (committed 2026-05-03) regenerated this file from the canonical PMF JSON: each prop's PMF now expands into one row per possible outcome `k`, with `p_k` summing to 1 per prop. The previous build had emitted a single `k=0, p_k=0.0` row per prop because the legacy `p_ge` ladder was no longer present in the upstream parquet. Verifier: `scripts/verify_derek_outcome_level_probabilities.py`.
- **pmf_driver_decomposition.md** — per-row contextual minutes / rate deltas with Phase 13S driver attribution.
- **lineup_injury_impact_report.md** — lineup confirmation, BDL injury fetch, counts of confirmed starters / bench / confirmed out.
- **direct_lineup_impact_report.md** — Phase 13S direct-lineup driver attribution: starter / bench changes, lineup composition impact.
- **missed_snapshot_report.md** — written when a near-tip snapshot was missed post-tip; explains the miss and links back to the audit trail.

Repaired long-form outcome files (live):

- https://github.com/Risky-Scout/nba-player-props-model/blob/main/deliveries/2026-05-03/derek_game_snapshots/21682000/current_live/outcome_level_probabilities.csv
- https://github.com/Risky-Scout/nba-player-props-model/blob/main/deliveries/2026-05-03/derek_game_snapshots/21684819/current_live/outcome_level_probabilities.csv

## Model status and calibration note

The 2026-05-03 package includes live-context PMF snapshots and a new actuarial-style PMF variance experience study. The experience study is based on **1,001** settled player-prop rows from **2026-04-17** through **2026-05-02**. It is a diagnostic review of settled morning/current rows, not a mature T-minus-25 or close-lock live-context sample yet — those snapshots have not accumulated enough joinable game stats to score meaningfully.

The first study is useful but mixed:

- **PMF variance is reasonably close overall.** Variance A/E = **0.913** (band 0.80–1.20 is the well-calibrated zone); standardized residual sd = **1.052** (target 1.00).
- **The model under-projects means.** Mean A/E = **1.144**; standardized residual mean = **0.211** — actuals ran ~14.4% above expected means in this sample.
- **The model trails the market on binary scoring in this sample.** Brier **0.278** (model) vs **0.246** (market); logloss **0.762** (model) vs **0.688** (market).

Read this as a recalibration roadmap, not a market-superiority claim. The verifier emits `PMF_VARIANCE_EXPERIENCE_STUDY_WARN` whenever the model trails the market on Brier — the WARN status is itself the audit trail.

**Next improvements (in priority order):**

1. Mean calibration — the +14.4% mean A/E bias points at the role-aware mean centering in the contextual stack.
2. Low-line discrete stat handling — fg3m / stl / blk / tov at lines ≤ 1.5 are the most miscalibrated bucket family.
3. fg3m dispersion — variance A/E = 2.01 means the PMF is materially too narrow on threes.
4. Bucket-level recalibration — high-p0 props and starter minutes are over-dispersed (variance A/E ≈ 0.50–0.75); they compress cleanly with isotonic.
5. More settled t_minus_25 / close_lock snapshots — the prospective live-context sample still needs to build.
6. Confirmed-lineup and injury-context experience tracking — Source A coverage will let us compare confirmed-lineup rows against projected rows once enough delivery dates accumulate.

## PMF variance experience study

- Latest study: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/pmf_variance_experience_2026-05-03.md
- Index: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/README.md
- Sample: 1,001 settled player-prop rows, 2026-04-17 → 2026-05-02, morning/current settled rows only.
- Headline: mean A/E = 1.144, variance A/E = 0.913, model Brier 0.278 vs market 0.246, model logloss 0.762 vs market 0.688.
- This is a diagnostic and improvement report. Do not claim market superiority from this sample.

## Daily location going forward

- Future daily delivery index: `deliveries/YYYY-MM-DD/README.md`
- Future Derek snapshot index: `deliveries/YYYY-MM-DD/derek_game_snapshots/README.md`
- Future per-game snapshots: `deliveries/YYYY-MM-DD/derek_game_snapshots/<game_id>/{current_live,t_minus_25,close_lock}/`

