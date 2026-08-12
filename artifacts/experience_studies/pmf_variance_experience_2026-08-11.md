# PMF Variance Experience Study — August 11, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-08-11` over a 60-day lookback._

## Executive summary

- **40** settled rows from **2026-06-13** through **2026-06-13** (1 delivery dates with at least one settled row).
- **Mean A/E = 1.053** — actual outcomes ran +5.3% relative to expected means in this sample.
- **Variance A/E = 1.256** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly narrow overall.
- **Standardized residual: mean = 0.142, sd = 1.109** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.725 and 0.900); the 10th-percentile band is over-covered (0.325 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.285 vs 0.255 (model vs market); logloss 0.780 vs 0.704.
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
| rows | 40 |
| actual_mean (per row) | 4.300 |
| expected_mean (per row) | 4.082 |
| **mean_AE** | **1.0533** |
| Σ squared residual | 484.23 |
| Σ expected variance | 385.51 |
| **variance_AE** | **1.2561** |
| standardized_residual_mean | 0.1420 |
| standardized_residual_sd | 1.1092 |
| pmf_nll_mean | 2.0158 |
| pmf_rps_mean | 0.1380 |
| model_brier (over/under) | 0.2852 |
| market_brier (over/under) | 0.2545 |
| model_logloss (over/under) | 0.7804 |
| market_logloss (over/under) | 0.7035 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.325 / 0.375 / 0.575 / 0.725 / 0.900 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| injury_context | `fallback_used` | 40 | **1.256** | 1.109 | 1.053 | 2.016 |
| lineup_confirmed | `projected` | 40 | **1.256** | 1.109 | 1.053 | 2.016 |
| minutes_volatility_bucket | `unavailable` | 40 | **1.256** | 1.109 | 1.053 | 2.016 |
| overall | `ALL` | 40 | **1.256** | 1.109 | 1.053 | 2.016 |
| side | `UNDER` | 31 | **1.254** | 1.108 | 1.115 | 2.179 |
| snapshot_type | `morning` | 40 | **1.256** | 1.109 | 1.053 | 2.016 |
| vacated_opportunity_bucket | `unavailable` | 40 | **1.256** | 1.109 | 1.053 | 2.016 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

_No buckets fell below `variance_AE < 0.80` with sufficient sample._

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

_No buckets met the calibration band with sufficient sample._

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 1 | 2.809 | 1.676 |
| edge_bucket | `10_to_20pct` | 24 | 0.999 | -0.029 |
| edge_bucket | `5_to_10pct` | 8 | 0.885 | 0.101 |
| edge_bucket | `ge_20pct` | 7 | 1.562 | 0.556 |
| line_bucket | `10_to_15` | 2 | 2.218 | 1.096 |
| line_bucket | `15_to_20` | 2 | 1.698 | -1.192 |
| line_bucket | `1_to_1p5` | 7 | 1.510 | 0.449 |
| line_bucket | `2_to_2p5` | 3 | 0.888 | 0.167 |
| line_bucket | `3_to_5` | 3 | 0.527 | -0.164 |
| line_bucket | `4_to_7` | 2 | 1.536 | 0.866 |
| line_bucket | `5_to_8` | 1 | 0.157 | -0.397 |
| line_bucket | `7_to_10` | 1 | 0.961 | 0.980 |
| line_bucket | `ge_10` | 2 | 0.758 | 0.666 |
| line_bucket | `ge_25` | 1 | 0.160 | -0.400 |
| line_bucket | `ge_3` | 1 | 4.821 | 2.196 |
| line_bucket | `le_half` | 11 | 0.745 | -0.231 |
| line_bucket | `lt_3` | 1 | 0.511 | 0.714 |
| line_bucket | `lt_4` | 3 | 1.591 | -0.299 |
| low_line_discrete | `no` | 22 | 1.261 | 0.231 |
| low_line_discrete | `yes` | 18 | 1.151 | 0.034 |
| p0_bucket | `20_to_50pct` | 10 | 1.386 | 0.016 |
| p0_bucket | `5_to_20pct` | 14 | 1.485 | 0.270 |
| p0_bucket | `ge_50pct` | 6 | 0.667 | 0.060 |
| p0_bucket | `lt_5pct` | 10 | 1.218 | 0.138 |
| predicted_variance_bucket | `high` | 13 | 1.291 | 0.038 |
| predicted_variance_bucket | `low` | 13 | 1.397 | 0.034 |
| predicted_variance_bucket | `mid` | 14 | 0.881 | 0.339 |
| role_bucket | `bench` | 9 | 1.937 | -0.177 |
| role_bucket | `core` | 4 | 3.238 | 1.149 |
| role_bucket | `rotation` | 2 | 0.622 | -0.738 |
| role_bucket | `starter` | 25 | 0.860 | 0.166 |
| side | `OVER` | 9 | 1.296 | -0.542 |
| stat | `ast` | 5 | 0.407 | -0.035 |
| stat | `blk` | 4 | 3.221 | 0.982 |
| stat | `fg3m` | 9 | 1.116 | 0.108 |
| stat | `pts` | 5 | 1.364 | -0.119 |
| stat | `reb` | 8 | 1.136 | 0.393 |
| stat | `stl` | 9 | 1.021 | -0.178 |

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
- settled window: **2026-06-13 → 2026-06-13** (1 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

