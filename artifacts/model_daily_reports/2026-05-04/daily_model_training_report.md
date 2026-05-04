# Daily model training / recalibration report — 2026-05-04

- generated_at_utc: 2026-05-04T15:58:05+00:00Z
- status: **HALTED_PENDING_UPSTREAM_DATA**
- halted_reason: `previous_day_data_not_ready`

## Why training did not run

The strict previous-day-ET resolver halted before any training step ran. `data/player_game_stats.parquet` only contains realized stats through **2026-04-29**, so the previous-day target (**2026-05-03**) has zero settled rows. This is the correct safe behavior — the workflow refuses to retrain on stale upstream data.

This is not a code bug. The fix is upstream: BDL needs to finish backfilling 2026-04-30, 2026-05-01, 2026-05-02, and 2026-05-03 settled game stats. The next nightly cron (09:30 UTC) will re-attempt the resolver automatically.

## Active champion (unchanged)

- champion_model_id: `challenger-2026-04-30`
- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`
- promoted: **False** (no new training, no promotion)

The 2026-04-30 champion remains the active model for predictions / Derek snapshots / WoO output. No model artifacts were modified by this halted run.

## Halted workflow run

- run id: `25316091911`
- url: https://github.com/Risky-Scout/nba-player-props-model/actions/runs/25316091911
- conclusion: failure (intentional fail-loud signal — workflow halted on safe-default)
- is_correct_safe_behavior: **True**

## Promotion status

- promoted: **False**
- decision: `halted_pending_upstream_data`
- decided_at_utc: `2026-05-04T15:58:05+00:00`
- champion pointer: unchanged (`challenger-2026-04-30`)

## Validation gates

Skipped — no training run produced a validation report.

## Per-target metrics

Skipped — no training run.

## Sensitivity

Skipped — no training run.

## After-game scoring

Pending — `data/player_game_stats.parquet` settled-stats backfill required.

## Pending items

PMF NLL / RPS / ECE / p0 calibration / mean bias / tail calibration are reported once nightly post-game scoring produces realized outcomes. Currently blocked on BDL settled-stats backfill for 2026-04-30 → 2026-05-03.

## PMF variance experience study

- Latest as-of-2026-05-03 study: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/pmf_variance_experience_2026-05-03.md
- Index: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/README.md
- Sample: 1,001 settled player-prop rows, 2026-04-17 → 2026-05-02, morning / current settled rows only.
- Headline: mean A/E = 1.144 (actuals ran ~14.4% above expected means); variance A/E = 0.913 (reasonably close overall, slightly wide); standardized residual mean 0.211, sd 1.052; model Brier 0.278 vs market 0.246; model logloss 0.762 vs market 0.688.
- This study currently covers settled morning / current rows only; T-minus-25 and close-lock scoring will become meaningful after more live snapshots settle. The prospective live-context sample still needs to build.
- This is a diagnostic and improvement report. Do not claim market superiority from this sample.
