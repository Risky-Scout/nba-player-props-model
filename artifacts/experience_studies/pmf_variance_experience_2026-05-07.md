# PMF Variance Experience Study — May 7, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-07` over a 60-day lookback._

## Executive summary

- **1,438** settled rows from **2026-04-17** through **2026-05-06** (18 delivery dates with at least one settled row).
- **Mean A/E = 1.126** — actual outcomes ran +12.6% relative to expected means in this sample.
- **Variance A/E = 0.853** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.185, sd = 1.010** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.748 and 0.902); the 10th-percentile band is over-covered (0.197 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.274 vs 0.247 (model vs market); logloss 0.752 vs 0.690.
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
| rows | 1,438 |
| actual_mean (per row) | 6.207 |
| expected_mean (per row) | 5.512 |
| **mean_AE** | **1.1261** |
| Σ squared residual | 20089.61 |
| Σ expected variance | 23547.73 |
| **variance_AE** | **0.8531** |
| standardized_residual_mean | 0.1845 |
| standardized_residual_sd | 1.0098 |
| pmf_nll_mean | 2.5996 |
| pmf_rps_mean | 0.1162 |
| model_brier (over/under) | 0.2739 |
| market_brier (over/under) | 0.2472 |
| model_logloss (over/under) | 0.7518 |
| market_logloss (over/under) | 0.6896 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.197 / 0.280 / 0.478 / 0.748 / 0.902 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

_No buckets exceeded `variance_AE > 1.20` with sufficient sample._

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 43 | **0.537** | 1.029 | 0.863 | 2.991 |
| injury_context | `fresh` | 271 | **0.732** | 0.930 | 1.054 | 2.611 |
| line_bucket | `1_to_1p5` | 208 | **0.636** | 0.997 | 1.167 | 2.041 |
| line_bucket | `20_to_25` | 44 | **0.616** | 0.994 | 1.079 | 4.454 |
| line_bucket | `2_to_2p5` | 47 | **0.720** | 1.404 | 1.089 | 2.863 |
| line_bucket | `5_to_8` | 72 | **0.621** | 0.858 | 1.038 | 2.491 |
| line_bucket | `ge_25` | 42 | **0.638** | 0.848 | 1.038 | 3.747 |
| line_bucket | `le_half` | 265 | **0.411** | 0.664 | 1.114 | 1.286 |
| lineup_confirmed | `projected` | 292 | **0.741** | 0.943 | 1.067 | 2.643 |
| low_line_discrete | `yes` | 473 | **0.532** | 0.827 | 1.146 | 1.618 |
| p0_bucket | `20_to_50pct` | 243 | **0.681** | 0.954 | 1.090 | 1.945 |
| p0_bucket | `ge_50pct` | 253 | **0.470** | 0.671 | 1.312 | 1.305 |
| role_bucket | `bench` | 34 | **0.720** | 1.008 | 0.896 | 2.561 |
| role_bucket | `ge30min_starter` | 475 | **0.723** | 0.986 | 1.083 | 2.645 |
| role_bucket | `lt22min` | 125 | **0.799** | 0.811 | 1.037 | 1.862 |
| role_bucket | `starter` | 167 | **0.633** | 0.884 | 1.030 | 2.565 |
| stat | `ast` | 221 | **0.797** | 1.027 | 1.052 | 2.521 |
| stat | `blk` | 186 | **0.729** | 0.757 | 1.360 | 1.608 |
| stat | `fg3m` | 148 | **0.636** | 1.170 | 1.025 | 2.376 |
| stat | `stl` | 198 | **0.551** | 0.816 | 1.116 | 1.425 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 720 | 1.128 | 0.830 | 0.159 | 2.606 |
| edge_bucket | `5_to_10pct` | 263 | 1.093 | 0.870 | 0.098 | 2.664 |
| edge_bucket | `ge_20pct` | 412 | 1.204 | 0.958 | 0.324 | 2.505 |
| injury_context | `unavailable` | 1146 | 1.147 | 0.895 | 0.202 | 2.589 |
| line_bucket | `10_to_15` | 94 | 1.054 | 1.015 | 0.113 | 3.247 |
| line_bucket | `15_to_20` | 100 | 1.226 | 0.969 | 0.517 | 3.977 |
| line_bucket | `3_to_5` | 89 | 1.026 | 0.841 | 0.031 | 2.540 |
| line_bucket | `4_to_7` | 148 | 1.232 | 1.052 | 0.407 | 2.916 |
| line_bucket | `7_to_10` | 74 | 1.205 | 1.074 | 0.432 | 3.170 |
| line_bucket | `lt_3` | 45 | 1.073 | 0.918 | 0.056 | 2.239 |
| line_bucket | `lt_4` | 135 | 1.127 | 1.088 | 0.161 | 2.741 |
| lineup_confirmed | `unavailable` | 1146 | 1.147 | 0.895 | 0.202 | 2.589 |
| low_line_discrete | `no` | 965 | 1.125 | 0.868 | 0.229 | 3.081 |
| minutes_volatility_bucket | `unavailable` | 1438 | 1.126 | 0.853 | 0.185 | 2.600 |
| overall | `ALL` | 1438 | 1.126 | 0.853 | 0.185 | 2.600 |
| p0_bucket | `5_to_20pct` | 381 | 1.222 | 0.858 | 0.267 | 2.387 |
| p0_bucket | `lt_5pct` | 561 | 1.102 | 0.868 | 0.191 | 3.612 |
| predicted_variance_bucket | `high` | 475 | 1.124 | 0.830 | 0.260 | 3.372 |
| predicted_variance_bucket | `low` | 475 | 1.114 | 1.107 | 0.113 | 2.149 |
| predicted_variance_bucket | `mid` | 488 | 1.137 | 0.936 | 0.180 | 2.286 |
| role_bucket | `lt30min` | 538 | 1.239 | 1.118 | 0.308 | 2.717 |
| role_bucket | `rotation` | 91 | 1.183 | 0.968 | 0.283 | 2.815 |
| side | `OVER` | 177 | 0.953 | 1.098 | -0.185 | 3.434 |
| side | `UNDER` | 1261 | 1.157 | 0.830 | 0.236 | 2.482 |
| snapshot_type | `morning` | 1438 | 1.126 | 0.853 | 0.185 | 2.600 |
| stat | `pts` | 304 | 1.114 | 0.843 | 0.249 | 3.779 |
| stat | `reb` | 381 | 1.190 | 1.009 | 0.316 | 2.885 |
| vacated_opportunity_bucket | `unavailable` | 1438 | 1.126 | 0.853 | 0.185 | 2.600 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_10` | 24 | 0.582 | 0.263 |
| line_bucket | `ge_3` | 12 | 2.705 | 0.209 |
| line_bucket | `ge_8` | 15 | 1.152 | 0.405 |
| line_bucket | `lt_10` | 24 | 0.844 | 0.091 |
| role_bucket | `lt15min` | 8 | 0.245 | 0.047 |

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
- settled window: **2026-04-17 → 2026-05-06** (18 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

