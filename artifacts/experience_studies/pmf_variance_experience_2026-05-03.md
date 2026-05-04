# PMF Variance Experience Study — May 3, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-03` over a 60-day lookback._

## Executive summary

- **1,208** settled rows from **2026-04-17** through **2026-05-02** (15 delivery dates with at least one settled row).
- **Mean A/E = 1.135** — actual outcomes ran +13.5% relative to expected means in this sample.
- **Variance A/E = 0.886** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.194, sd = 1.026** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.749 and 0.902); the 10th-percentile band is over-covered (0.200 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.275 vs 0.247 (model vs market); logloss 0.754 vs 0.689.
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
| rows | 1,208 |
| actual_mean (per row) | 6.273 |
| expected_mean (per row) | 5.529 |
| **mean_AE** | **1.1345** |
| Σ squared residual | 17361.82 |
| Σ expected variance | 19605.96 |
| **variance_AE** | **0.8855** |
| standardized_residual_mean | 0.1939 |
| standardized_residual_sd | 1.0263 |
| pmf_nll_mean | 2.6394 |
| pmf_rps_mean | 0.1181 |
| model_brier (over/under) | 0.2749 |
| market_brier (over/under) | 0.2473 |
| model_logloss (over/under) | 0.7539 |
| market_logloss (over/under) | 0.6894 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.200 / 0.276 / 0.474 / 0.749 / 0.902 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| predicted_variance_bucket | `low` | 399 | **1.240** | 1.193 | 1.108 | 2.263 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 33 | **0.620** | 1.115 | 0.838 | 3.245 |
| injury_context | `fresh` | 155 | **0.769** | 0.958 | 1.086 | 2.553 |
| line_bucket | `1_to_1p5` | 168 | **0.673** | 1.047 | 1.176 | 2.043 |
| line_bucket | `20_to_25` | 38 | **0.701** | 1.058 | 1.078 | 4.647 |
| line_bucket | `5_to_8` | 59 | **0.583** | 0.845 | 1.064 | 2.511 |
| line_bucket | `ge_25` | 34 | **0.652** | 0.870 | 1.048 | 3.812 |
| line_bucket | `le_half` | 224 | **0.427** | 0.680 | 1.124 | 1.243 |
| lineup_confirmed | `projected` | 176 | **0.781** | 0.973 | 1.105 | 2.613 |
| low_line_discrete | `yes` | 392 | **0.554** | 0.857 | 1.155 | 1.586 |
| p0_bucket | `20_to_50pct` | 199 | **0.699** | 0.986 | 1.081 | 1.887 |
| p0_bucket | `ge_50pct` | 218 | **0.470** | 0.675 | 1.302 | 1.301 |
| role_bucket | `ge30min_starter` | 425 | **0.748** | 1.007 | 1.085 | 2.734 |
| role_bucket | `starter` | 104 | **0.665** | 0.908 | 1.104 | 2.618 |
| stat | `ast` | 188 | **0.776** | 1.031 | 1.039 | 2.554 |
| stat | `blk` | 156 | **0.566** | 0.732 | 1.339 | 1.575 |
| stat | `fg3m` | 113 | **0.786** | 1.292 | 1.003 | 2.364 |
| stat | `stl` | 167 | **0.545** | 0.828 | 1.142 | 1.422 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 601 | 1.124 | 0.857 | 0.150 | 2.637 |
| edge_bucket | `5_to_10pct` | 203 | 1.101 | 0.933 | 0.115 | 2.738 |
| edge_bucket | `ge_20pct` | 371 | 1.235 | 0.949 | 0.348 | 2.535 |
| injury_context | `unavailable` | 1032 | 1.141 | 0.910 | 0.197 | 2.644 |
| line_bucket | `10_to_15` | 80 | 1.055 | 1.075 | 0.114 | 3.253 |
| line_bucket | `15_to_20` | 86 | 1.245 | 1.049 | 0.562 | 4.073 |
| line_bucket | `2_to_2p5` | 34 | 1.126 | 0.996 | 0.295 | 3.260 |
| line_bucket | `3_to_5` | 75 | 0.997 | 0.845 | -0.020 | 2.609 |
| line_bucket | `4_to_7` | 123 | 1.263 | 0.987 | 0.447 | 2.983 |
| line_bucket | `7_to_10` | 63 | 1.245 | 1.028 | 0.511 | 3.247 |
| line_bucket | `lt_3` | 40 | 0.993 | 0.851 | -0.074 | 2.207 |
| line_bucket | `lt_4` | 117 | 1.185 | 1.081 | 0.229 | 2.838 |
| lineup_confirmed | `unavailable` | 1032 | 1.141 | 0.910 | 0.197 | 2.644 |
| low_line_discrete | `no` | 816 | 1.133 | 0.900 | 0.240 | 3.146 |
| minutes_volatility_bucket | `unavailable` | 1208 | 1.135 | 0.886 | 0.194 | 2.639 |
| overall | `ALL` | 1208 | 1.135 | 0.886 | 0.194 | 2.639 |
| p0_bucket | `5_to_20pct` | 324 | 1.222 | 0.839 | 0.265 | 2.408 |
| p0_bucket | `lt_5pct` | 467 | 1.113 | 0.911 | 0.218 | 3.745 |
| predicted_variance_bucket | `high` | 399 | 1.137 | 0.873 | 0.293 | 3.386 |
| predicted_variance_bucket | `mid` | 410 | 1.138 | 0.877 | 0.177 | 2.280 |
| role_bucket | `lt22min` | 114 | 1.023 | 0.801 | -0.057 | 1.893 |
| role_bucket | `lt30min` | 486 | 1.228 | 1.126 | 0.295 | 2.750 |
| role_bucket | `rotation` | 54 | 1.146 | 1.044 | 0.173 | 2.726 |
| side | `OVER` | 141 | 1.017 | 1.190 | -0.098 | 3.671 |
| side | `UNDER` | 1067 | 1.155 | 0.862 | 0.232 | 2.503 |
| snapshot_type | `morning` | 1208 | 1.135 | 0.886 | 0.194 | 2.639 |
| stat | `pts` | 259 | 1.120 | 0.899 | 0.259 | 3.857 |
| stat | `reb` | 325 | 1.219 | 0.950 | 0.361 | 2.951 |
| vacated_opportunity_bucket | `unavailable` | 1208 | 1.135 | 0.886 | 0.194 | 2.639 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_10` | 22 | 0.455 | 0.150 |
| line_bucket | `ge_3` | 10 | 1.157 | -0.134 |
| line_bucket | `ge_8` | 14 | 1.110 | 0.337 |
| line_bucket | `lt_10` | 21 | 0.790 | -0.027 |
| role_bucket | `bench` | 18 | 0.735 | 0.001 |
| role_bucket | `lt15min` | 7 | 0.245 | -0.016 |

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
- settled window: **2026-04-17 → 2026-05-02** (15 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

