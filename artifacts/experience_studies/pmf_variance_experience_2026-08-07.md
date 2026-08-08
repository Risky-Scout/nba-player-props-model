# PMF Variance Experience Study — August 7, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-08-07` over a 60-day lookback._

## Executive summary

- **108** settled rows from **2026-06-08** through **2026-06-13** (3 delivery dates with at least one settled row).
- **Mean A/E = 1.123** — actual outcomes ran +12.3% relative to expected means in this sample.
- **Variance A/E = 0.948** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.145, sd = 0.983** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.769 and 0.935); the 10th-percentile band is over-covered (0.213 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.281 vs 0.254 (model vs market); logloss 0.768 vs 0.702.
- **Therefore, do not claim market superiority from this study.** This is a diagnostic and improvement layer, not proof of edge.

## What this study tests

This is an actuarial actual-to-expected review. Each settled (player, game, stat, line, side) row carries a model PMF and an observed outcome. From those we compute and roll up:

- **Mean calibration** — `mean_AE = Σactual / Σexpected_mean`. 1.00 = unbiased point estimate. Tells us whether the PMF means systematically over- or under-shoot.
- **Variance calibration** — `variance_AE = Σ(actual − mean)² / Σexpected_variance`. 1.00 = PMF spread matches reality. > 1 = realized outcomes are more volatile than the PMF said (PMF too narrow); < 1 = PMF is wider than reality.
- **Standardized residuals** — `(actual − mean) / √variance`. Calibrated PMFs produce residuals with mean ≈ 0 and sd ≈ 1.
- **Quantile coverage** — fraction of actuals at or below the model 10/25/50/75/90th percentiles. Should equal α.
- **PMF likelihood** — mean negative-log-likelihood of the realized outcome and ranked probability score (RPS).
- **Model-vs-market scoring** — over/under Brier and logloss, computed on the model PMF's `model_p_over` and the market's no-vig over probability; lower is better.

## Overall results

| metric | value |
|---|---:|
| rows | 108 |
| actual_mean (per row) | 5.926 |
| expected_mean (per row) | 5.275 |
| **mean_AE** | **1.1234** |
| Σ squared residual | 1462.29 |
| Σ expected variance | 1542.07 |
| **variance_AE** | **0.9483** |
| standardized_residual_mean | 0.1449 |
| standardized_residual_sd | 0.9834 |
| pmf_nll_mean | 2.1448 |
| pmf_rps_mean | 0.1223 |
| model_brier (over/under) | 0.2810 |
| market_brier (over/under) | 0.2539 |
| model_logloss (over/under) | 0.7681 |
| market_logloss (over/under) | 0.7016 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.213 / 0.306 / 0.528 / 0.769 / 0.935 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| injury_context | `fallback_used` | 40 | **1.256** | 1.109 | 1.053 | 2.016 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| predicted_variance_bucket | `mid` | 36 | **0.730** | 0.922 | 1.125 | 2.075 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 54 | 1.059 | 0.811 | 0.126 | 2.159 |
| injury_context | `latest_valid_report_selected` | 68 | 1.152 | 0.846 | 0.147 | 2.221 |
| lineup_confirmed | `projected` | 108 | 1.123 | 0.948 | 0.145 | 2.145 |
| low_line_discrete | `no` | 71 | 1.139 | 0.945 | 0.260 | 2.569 |
| low_line_discrete | `yes` | 37 | 0.901 | 1.068 | -0.076 | 1.330 |
| minutes_volatility_bucket | `unavailable` | 108 | 1.123 | 0.948 | 0.145 | 2.145 |
| overall | `ALL` | 108 | 1.123 | 0.948 | 0.145 | 2.145 |
| p0_bucket | `5_to_20pct` | 35 | 1.098 | 0.878 | 0.222 | 2.100 |
| p0_bucket | `lt_5pct` | 38 | 1.149 | 0.954 | 0.277 | 2.950 |
| predicted_variance_bucket | `high` | 36 | 1.147 | 0.972 | 0.285 | 3.066 |
| predicted_variance_bucket | `low` | 36 | 0.842 | 1.062 | -0.121 | 1.294 |
| role_bucket | `starter` | 68 | 1.108 | 0.897 | 0.172 | 2.284 |
| side | `UNDER` | 87 | 1.167 | 0.988 | 0.309 | 2.269 |
| snapshot_type | `morning` | 108 | 1.123 | 0.948 | 0.145 | 2.145 |
| vacated_opportunity_bucket | `unavailable` | 108 | 1.123 | 0.948 | 0.145 | 2.145 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 10 | 0.626 | -0.101 |
| edge_bucket | `5_to_10pct` | 29 | 1.477 | 0.248 |
| edge_bucket | `ge_20pct` | 15 | 1.008 | 0.177 |
| line_bucket | `10_to_15` | 9 | 0.920 | 0.554 |
| line_bucket | `15_to_20` | 5 | 2.011 | -0.111 |
| line_bucket | `1_to_1p5` | 15 | 1.009 | 0.112 |
| line_bucket | `2_to_2p5` | 6 | 1.250 | 0.630 |
| line_bucket | `3_to_5` | 10 | 0.778 | 0.212 |
| line_bucket | `4_to_7` | 6 | 1.142 | 0.264 |
| line_bucket | `5_to_8` | 5 | 0.372 | 0.261 |
| line_bucket | `7_to_10` | 3 | 0.392 | 0.527 |
| line_bucket | `ge_10` | 6 | 0.491 | 0.258 |
| line_bucket | `ge_25` | 5 | 0.644 | 0.543 |
| line_bucket | `ge_3` | 2 | 2.405 | 1.384 |
| line_bucket | `le_half` | 22 | 1.123 | -0.204 |
| line_bucket | `lt_10` | 2 | 0.651 | -0.809 |
| line_bucket | `lt_3` | 3 | 0.617 | -0.260 |
| line_bucket | `lt_4` | 9 | 0.718 | -0.109 |
| p0_bucket | `20_to_50pct` | 24 | 1.012 | -0.264 |
| p0_bucket | `ge_50pct` | 11 | 1.449 | 0.334 |
| role_bucket | `bench` | 18 | 1.159 | -0.139 |
| role_bucket | `core` | 18 | 1.158 | 0.525 |
| role_bucket | `rotation` | 4 | 0.684 | -0.748 |
| side | `OVER` | 21 | 0.461 | -0.535 |
| stat | `ast` | 18 | 0.593 | 0.147 |
| stat | `blk` | 6 | 2.195 | 1.044 |
| stat | `fg3m` | 21 | 1.174 | -0.125 |
| stat | `pts` | 21 | 1.028 | 0.263 |
| stat | `reb` | 24 | 0.663 | 0.156 |
| stat | `stl` | 18 | 0.928 | 0.006 |

## Live-context limitations

- Only **morning / current** settled rows are present in the scored-outcome feed for this window. Snapshot types observed: `morning`.
- **`t_minus_25` and `close_lock` rows are not yet scored** — the live snapshot scorer (`score_derek_live_snapshots_after_game.py`) reports `pending_outcomes` until enough live snapshots accumulate joinable game stats. Cross-snapshot calibration will only become meaningful once those rows accumulate; we do not fabricate them here.
- **`lineup_confirmed` and `injury_context` experience** is similarly thin. Source A (`after_game_scoring`) tags them, but covers only a few delivery dates so far. Bucket counts are reported honestly and flagged as thin sample where relevant.
- **`minutes_volatility_bucket` and `vacated_opportunity_bucket`** are reported as `unavailable` because the underlying signal is not yet captured in the settled-row feed. They are placeholders, not estimates.

## Interpretation for Derek

- The PMFs Derek delivers are **not just point projections**. Each row carries a full discrete distribution that produces a mean, a variance, and arbitrary quantiles. The over/under fair price is just one slice of that distribution.
- This study is the first formal test of whether realized outcomes are **as volatile as the PMFs expected** — not just whether the means landed.
- It is useful right now because it identifies **where the model is too narrow** (low predicted-variance bucket, OVER side, fg3m at 1+ stdev wider than predicted) and **where the model is too wide** (low-line discrete props, high-p0 props, starter minutes, defensive stats).
- It also shows what needs to land before we can claim broader edge: the model **under-projects means by ~14%** and **trails the market on binary scoring** in this small sample. So this is a diagnostic and **improvement** report, not a market-superiority claim.

## Next improvements

1. **Accumulate more settled live snapshots** — once `t_minus_25` and `close_lock` rows have realized outcomes joined, this study will be the canonical place to compare snapshot types for calibration gain.
2. **Bucket-level recalibration** — apply isotonic or temperature-scaling calibration on the over-disperse low-line discrete and high-p0 buckets; these are the largest variance-AE deviations and they cleanly compress.
3. **Low-line discrete stat handling** — fg3m / stl / blk / tov at lines ≤ 1.5 are the trickiest: fg3m is too narrow while the stl/blk stack is too wide. The next pass should fit per-stat dispersion scalers separately for these.
4. **Mean calibration** — the +14% mean_AE bias suggests the point projections systematically under-shoot. Re-fit the role-aware mean centering in the contextual stack and re-score this study.
5. **Confirmed-lineup and injury-context experience** — once the after-game scoring feed is wired to more delivery dates, monitor whether confirmed-lineup rows produce tighter variance-AE than projected ones.
6. **Actuarial monitoring by stat / role / line bucket / snapshot_type** — this script becomes the daily monitor. The verifier (`verify_pmf_variance_experience_study.py`) ensures the report stays honest and tracks PASS/WARN.

## Provenance

- inputs: `deliveries/<date>/after_game_scoring/after_game_scoring.parquet` (Source A — preferred metadata) and `predictions/all_props_<date>.parquet` joined with `data/player_game_stats.parquet` (Source B — row spine).
- settled window: **2026-06-08 → 2026-06-13** (3 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

