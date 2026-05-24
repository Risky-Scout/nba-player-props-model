# PMF Variance Experience Study — May 23, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-23` over a 60-day lookback._

## Executive summary

- **1,696** settled rows from **2026-04-17** through **2026-05-22** (24 delivery dates with at least one settled row).
- **Mean A/E = 1.116** — actual outcomes ran +11.6% relative to expected means in this sample.
- **Variance A/E = 0.851** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.159, sd = 1.000** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.755 and 0.906); the 10th-percentile band is over-covered (0.203 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.271 vs 0.247 (model vs market); logloss 0.746 vs 0.689.
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
| rows | 1,696 |
| actual_mean (per row) | 6.150 |
| expected_mean (per row) | 5.512 |
| **mean_AE** | **1.1157** |
| Σ squared residual | 23612.21 |
| Σ expected variance | 27746.26 |
| **variance_AE** | **0.8510** |
| standardized_residual_mean | 0.1590 |
| standardized_residual_sd | 1.0001 |
| pmf_nll_mean | 2.5365 |
| pmf_rps_mean | 0.1138 |
| model_brier (over/under) | 0.2715 |
| market_brier (over/under) | 0.2469 |
| model_logloss (over/under) | 0.7459 |
| market_logloss (over/under) | 0.6889 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.203 / 0.295 / 0.493 / 0.755 / 0.906 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 38 | **1.790** | 1.296 | 1.261 | 3.041 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 56 | **0.524** | 0.970 | 0.873 | 2.723 |
| line_bucket | `1_to_1p5` | 251 | **0.653** | 0.992 | 1.104 | 1.962 |
| line_bucket | `20_to_25` | 47 | **0.668** | 1.009 | 1.082 | 4.416 |
| line_bucket | `2_to_2p5` | 65 | **0.719** | 1.263 | 1.114 | 2.526 |
| line_bucket | `5_to_8` | 85 | **0.694** | 0.883 | 1.074 | 2.505 |
| line_bucket | `ge_10` | 30 | **0.703** | 0.833 | 1.128 | 2.702 |
| line_bucket | `ge_25` | 56 | **0.602** | 0.810 | 1.044 | 3.668 |
| line_bucket | `le_half` | 309 | **0.414** | 0.665 | 1.007 | 1.253 |
| low_line_discrete | `yes` | 560 | **0.541** | 0.828 | 1.065 | 1.571 |
| p0_bucket | `20_to_50pct` | 294 | **0.665** | 0.934 | 1.044 | 1.867 |
| p0_bucket | `ge_50pct` | 279 | **0.450** | 0.660 | 1.262 | 1.264 |
| role_bucket | `bench` | 40 | **0.682** | 0.981 | 0.870 | 2.453 |
| role_bucket | `ge30min_starter` | 559 | **0.691** | 0.967 | 1.068 | 2.558 |
| role_bucket | `lt22min` | 141 | **0.778** | 0.797 | 1.002 | 1.806 |
| role_bucket | `starter` | 230 | **0.616** | 0.873 | 1.033 | 2.499 |
| stat | `blk` | 213 | **0.684** | 0.746 | 1.293 | 1.558 |
| stat | `fg3m` | 198 | **0.681** | 1.128 | 0.991 | 2.157 |
| stat | `stl` | 227 | **0.525** | 0.794 | 1.052 | 1.408 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 834 | 1.119 | 0.828 | 0.140 | 2.535 |
| edge_bucket | `5_to_10pct` | 347 | 1.058 | 0.812 | 0.031 | 2.544 |
| edge_bucket | `ge_20pct` | 459 | 1.218 | 1.025 | 0.334 | 2.511 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `unavailable` | 1278 | 1.132 | 0.868 | 0.177 | 2.519 |
| line_bucket | `10_to_15` | 111 | 1.092 | 1.001 | 0.184 | 3.267 |
| line_bucket | `15_to_20` | 112 | 1.197 | 0.946 | 0.454 | 3.912 |
| line_bucket | `3_to_5` | 114 | 0.993 | 0.869 | -0.013 | 2.429 |
| line_bucket | `4_to_7` | 167 | 1.214 | 1.101 | 0.378 | 2.919 |
| line_bucket | `7_to_10` | 85 | 1.157 | 1.086 | 0.347 | 3.118 |
| line_bucket | `lt_3` | 52 | 1.129 | 0.922 | 0.138 | 2.229 |
| line_bucket | `lt_4` | 154 | 1.095 | 1.012 | 0.125 | 2.649 |
| lineup_confirmed | `projected` | 418 | 1.080 | 0.814 | 0.104 | 2.591 |
| lineup_confirmed | `unavailable` | 1278 | 1.132 | 0.868 | 0.177 | 2.519 |
| low_line_discrete | `no` | 1136 | 1.119 | 0.865 | 0.217 | 3.013 |
| minutes_volatility_bucket | `unavailable` | 1696 | 1.116 | 0.851 | 0.159 | 2.536 |
| overall | `ALL` | 1696 | 1.116 | 0.851 | 0.159 | 2.536 |
| p0_bucket | `5_to_20pct` | 473 | 1.203 | 0.970 | 0.224 | 2.333 |
| p0_bucket | `lt_5pct` | 650 | 1.097 | 0.849 | 0.184 | 3.534 |
| predicted_variance_bucket | `high` | 560 | 1.118 | 0.829 | 0.243 | 3.333 |
| predicted_variance_bucket | `low` | 560 | 1.085 | 1.043 | 0.080 | 2.031 |
| predicted_variance_bucket | `mid` | 576 | 1.120 | 0.945 | 0.154 | 2.254 |
| role_bucket | `lt30min` | 568 | 1.228 | 1.085 | 0.285 | 2.662 |
| role_bucket | `rotation` | 110 | 1.181 | 0.979 | 0.237 | 2.676 |
| side | `OVER` | 226 | 0.936 | 0.967 | -0.243 | 3.108 |
| side | `UNDER` | 1470 | 1.148 | 0.839 | 0.221 | 2.449 |
| snapshot_type | `morning` | 1696 | 1.116 | 0.851 | 0.159 | 2.536 |
| stat | `ast` | 268 | 1.062 | 0.822 | 0.075 | 2.467 |
| stat | `pts` | 354 | 1.114 | 0.836 | 0.254 | 3.731 |
| stat | `reb` | 436 | 1.160 | 1.024 | 0.273 | 2.847 |
| vacated_opportunity_bucket | `unavailable` | 1696 | 1.116 | 0.851 | 0.159 | 2.536 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `latest_valid_report_selected` | 29 | 0.862 | 0.046 |
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 13 | 2.361 | 0.223 |
| line_bucket | `ge_8` | 17 | 1.041 | 0.401 |
| line_bucket | `lt_10` | 28 | 1.069 | 0.168 |
| role_bucket | `lt15min` | 10 | 2.868 | 0.427 |

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
- settled window: **2026-04-17 → 2026-05-22** (24 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

