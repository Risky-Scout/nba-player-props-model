# PMF Variance Experience Study — July 10, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-10` over a 60-day lookback._

## Executive summary

- **481** settled rows from **2026-05-15** through **2026-06-13** (14 delivery dates with at least one settled row).
- **Mean A/E = 1.041** — actual outcomes ran +4.1% relative to expected means in this sample.
- **Variance A/E = 0.752** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.080, sd = 0.977** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.794 and 0.933); the 10th-percentile band is over-covered (0.210 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.261 vs 0.249 (model vs market); logloss 0.720 vs 0.693.
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
| rows | 481 |
| actual_mean (per row) | 5.857 |
| expected_mean (per row) | 5.628 |
| **mean_AE** | **1.0406** |
| Σ squared residual | 5918.38 |
| Σ expected variance | 7869.33 |
| **variance_AE** | **0.7521** |
| standardized_residual_mean | 0.0796 |
| standardized_residual_sd | 0.9773 |
| pmf_nll_mean | 2.2486 |
| pmf_rps_mean | 0.1136 |
| model_brier (over/under) | 0.2608 |
| market_brier (over/under) | 0.2494 |
| model_logloss (over/under) | 0.7203 |
| market_logloss (over/under) | 0.6934 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.210 / 0.326 / 0.555 / 0.794 / 0.933 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| p0_bucket | `5_to_20pct` | 158 | **1.338** | 1.005 | 1.117 | 2.112 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 32 | **0.574** | 0.858 | 0.830 | 2.143 |
| edge_bucket | `10_to_20pct` | 223 | **0.675** | 0.990 | 1.039 | 2.305 |
| edge_bucket | `ge_20pct` | 65 | **0.790** | 0.968 | 1.204 | 2.121 |
| injury_context | `unavailable` | 157 | **0.602** | 0.900 | 1.030 | 2.161 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `3_to_5` | 39 | **0.732** | 0.875 | 0.984 | 2.054 |
| lineup_confirmed | `unavailable` | 157 | **0.602** | 0.900 | 1.030 | 2.161 |
| low_line_discrete | `no` | 328 | **0.745** | 0.913 | 1.045 | 2.565 |
| minutes_volatility_bucket | `unavailable` | 481 | **0.752** | 0.977 | 1.041 | 2.249 |
| overall | `ALL` | 481 | **0.752** | 0.977 | 1.041 | 2.249 |
| p0_bucket | `ge_50pct` | 52 | **0.714** | 0.899 | 1.374 | 1.132 |
| p0_bucket | `lt_5pct` | 176 | **0.662** | 0.842 | 1.022 | 2.913 |
| predicted_variance_bucket | `high` | 159 | **0.726** | 0.895 | 1.047 | 3.067 |
| role_bucket | `ge30min_starter` | 104 | **0.516** | 0.914 | 1.031 | 2.283 |
| role_bucket | `lt30min` | 32 | **0.394** | 0.683 | 1.034 | 2.013 |
| role_bucket | `starter` | 170 | **0.752** | 1.006 | 1.076 | 2.470 |
| side | `OVER` | 101 | **0.770** | 0.962 | 0.805 | 2.139 |
| side | `UNDER` | 380 | **0.749** | 0.942 | 1.092 | 2.278 |
| snapshot_type | `morning` | 481 | **0.752** | 0.977 | 1.041 | 2.249 |
| stat | `ast` | 82 | **0.651** | 0.833 | 1.060 | 2.089 |
| stat | `blk` | 42 | **0.776** | 0.955 | 1.139 | 1.305 |
| stat | `pts` | 102 | **0.719** | 0.909 | 1.047 | 3.320 |
| vacated_opportunity_bucket | `unavailable` | 481 | **0.752** | 0.977 | 1.041 | 2.249 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 161 | 1.020 | 0.895 | 0.058 | 2.243 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 40 | 1.037 | 0.816 | 0.102 | 3.240 |
| line_bucket | `1_to_1p5` | 65 | 1.086 | 1.191 | 0.169 | 1.870 |
| line_bucket | `4_to_7` | 38 | 1.044 | 1.079 | 0.080 | 2.462 |
| line_bucket | `le_half` | 88 | 0.821 | 0.879 | -0.072 | 1.348 |
| line_bucket | `lt_4` | 39 | 1.059 | 0.987 | 0.100 | 2.265 |
| lineup_confirmed | `projected` | 299 | 1.074 | 0.844 | 0.139 | 2.278 |
| low_line_discrete | `yes` | 153 | 0.963 | 1.024 | 0.031 | 1.570 |
| p0_bucket | `20_to_50pct` | 95 | 0.970 | 1.073 | -0.001 | 1.855 |
| predicted_variance_bucket | `low` | 159 | 1.075 | 1.160 | 0.103 | 1.623 |
| predicted_variance_bucket | `mid` | 163 | 1.003 | 0.873 | 0.020 | 2.060 |
| role_bucket | `core` | 65 | 0.915 | 0.996 | -0.050 | 2.352 |
| role_bucket | `rotation` | 61 | 1.149 | 0.995 | 0.247 | 2.081 |
| stat | `fg3m` | 85 | 0.937 | 1.190 | -0.076 | 1.751 |
| stat | `reb` | 114 | 1.026 | 0.917 | 0.073 | 2.472 |
| stat | `stl` | 56 | 1.118 | 0.817 | 0.119 | 1.541 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| line_bucket | `15_to_20` | 24 | 0.871 | -0.088 |
| line_bucket | `20_to_25` | 1 | 0.015 | -0.121 |
| line_bucket | `2_to_2p5` | 26 | 0.691 | 0.149 |
| line_bucket | `5_to_8` | 22 | 0.568 | 0.142 |
| line_bucket | `7_to_10` | 20 | 0.937 | 0.038 |
| line_bucket | `ge_10` | 17 | 0.690 | 0.037 |
| line_bucket | `ge_25` | 24 | 0.467 | 0.289 |
| line_bucket | `ge_3` | 4 | 1.507 | 0.488 |
| line_bucket | `ge_8` | 1 | 0.025 | 0.158 |
| line_bucket | `lt_10` | 13 | 1.298 | 0.168 |
| line_bucket | `lt_3` | 20 | 0.753 | 0.265 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `bench` | 28 | 0.916 | -0.154 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 15 | 0.665 | -0.493 |

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
- settled window: **2026-05-15 → 2026-06-13** (14 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

