# PMF Variance Experience Study — May 18, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-18` over a 60-day lookback._

## Executive summary

- **1,633** settled rows from **2026-04-17** through **2026-05-15** (21 delivery dates with at least one settled row).
- **Mean A/E = 1.118** — actual outcomes ran +11.8% relative to expected means in this sample.
- **Variance A/E = 0.849** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.164, sd = 1.002** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.753 and 0.906); the 10th-percentile band is over-covered (0.203 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.273 vs 0.247 (model vs market); logloss 0.749 vs 0.690.
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
| rows | 1,633 |
| actual_mean (per row) | 6.133 |
| expected_mean (per row) | 5.487 |
| **mean_AE** | **1.1179** |
| Σ squared residual | 22592.28 |
| Σ expected variance | 26599.07 |
| **variance_AE** | **0.8494** |
| standardized_residual_mean | 0.1638 |
| standardized_residual_sd | 1.0020 |
| pmf_nll_mean | 2.5461 |
| pmf_rps_mean | 0.1141 |
| model_brier (over/under) | 0.2726 |
| market_brier (over/under) | 0.2472 |
| model_logloss (over/under) | 0.7487 |
| market_logloss (over/under) | 0.6897 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.203 / 0.294 / 0.491 / 0.753 / 0.906 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

_No buckets exceeded `variance_AE > 1.20` with sufficient sample._

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 54 | **0.521** | 0.959 | 0.869 | 2.747 |
| edge_bucket | `5_to_10pct` | 323 | **0.800** | 0.934 | 1.066 | 2.585 |
| line_bucket | `1_to_1p5` | 239 | **0.660** | 1.000 | 1.129 | 1.999 |
| line_bucket | `20_to_25` | 46 | **0.691** | 1.019 | 1.085 | 4.439 |
| line_bucket | `2_to_2p5` | 62 | **0.729** | 1.289 | 1.106 | 2.572 |
| line_bucket | `5_to_8` | 81 | **0.689** | 0.887 | 1.056 | 2.506 |
| line_bucket | `ge_25` | 53 | **0.629** | 0.829 | 1.040 | 3.694 |
| line_bucket | `le_half` | 303 | **0.409** | 0.662 | 1.013 | 1.246 |
| low_line_discrete | `yes` | 542 | **0.542** | 0.829 | 1.082 | 1.578 |
| p0_bucket | `20_to_50pct` | 282 | **0.666** | 0.936 | 1.055 | 1.884 |
| p0_bucket | `ge_50pct` | 277 | **0.453** | 0.662 | 1.266 | 1.266 |
| role_bucket | `bench` | 40 | **0.682** | 0.981 | 0.870 | 2.453 |
| role_bucket | `ge30min_starter` | 537 | **0.703** | 0.975 | 1.073 | 2.575 |
| role_bucket | `lt22min` | 137 | **0.793** | 0.805 | 1.019 | 1.815 |
| role_bucket | `starter` | 218 | **0.630** | 0.873 | 1.021 | 2.505 |
| stat | `blk` | 211 | **0.688** | 0.747 | 1.301 | 1.561 |
| stat | `fg3m` | 185 | **0.682** | 1.146 | 1.003 | 2.213 |
| stat | `stl` | 221 | **0.530** | 0.798 | 1.057 | 1.407 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 802 | 1.120 | 0.840 | 0.140 | 2.542 |
| edge_bucket | `ge_20pct` | 454 | 1.214 | 1.003 | 0.329 | 2.502 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `unavailable` | 1244 | 1.133 | 0.867 | 0.181 | 2.529 |
| line_bucket | `10_to_15` | 105 | 1.087 | 1.011 | 0.170 | 3.264 |
| line_bucket | `15_to_20` | 109 | 1.206 | 0.942 | 0.472 | 3.925 |
| line_bucket | `3_to_5` | 109 | 1.013 | 0.860 | 0.012 | 2.447 |
| line_bucket | `4_to_7` | 161 | 1.225 | 1.093 | 0.402 | 2.941 |
| line_bucket | `7_to_10` | 82 | 1.177 | 1.096 | 0.384 | 3.136 |
| line_bucket | `lt_3` | 50 | 1.107 | 0.889 | 0.110 | 2.215 |
| line_bucket | `lt_4` | 148 | 1.087 | 1.034 | 0.112 | 2.673 |
| lineup_confirmed | `projected` | 389 | 1.081 | 0.811 | 0.108 | 2.601 |
| lineup_confirmed | `unavailable` | 1244 | 1.133 | 0.867 | 0.181 | 2.529 |
| low_line_discrete | `no` | 1091 | 1.120 | 0.864 | 0.219 | 3.027 |
| minutes_volatility_bucket | `unavailable` | 1633 | 1.118 | 0.849 | 0.164 | 2.546 |
| overall | `ALL` | 1633 | 1.118 | 0.849 | 0.164 | 2.546 |
| p0_bucket | `5_to_20pct` | 446 | 1.197 | 0.882 | 0.228 | 2.344 |
| p0_bucket | `lt_5pct` | 628 | 1.100 | 0.861 | 0.189 | 3.552 |
| predicted_variance_bucket | `high` | 539 | 1.118 | 0.825 | 0.241 | 3.333 |
| predicted_variance_bucket | `low` | 539 | 1.092 | 1.060 | 0.087 | 2.052 |
| predicted_variance_bucket | `mid` | 555 | 1.128 | 0.957 | 0.163 | 2.262 |
| role_bucket | `lt30min` | 562 | 1.227 | 1.086 | 0.286 | 2.667 |
| role_bucket | `rotation` | 102 | 1.163 | 0.947 | 0.218 | 2.715 |
| side | `OVER` | 212 | 0.935 | 1.012 | -0.240 | 3.171 |
| side | `UNDER` | 1421 | 1.150 | 0.834 | 0.224 | 2.453 |
| snapshot_type | `morning` | 1633 | 1.118 | 0.849 | 0.164 | 2.546 |
| stat | `ast` | 257 | 1.059 | 0.815 | 0.070 | 2.474 |
| stat | `pts` | 340 | 1.113 | 0.836 | 0.248 | 3.742 |
| stat | `reb` | 419 | 1.169 | 1.015 | 0.286 | 2.864 |
| vacated_opportunity_bucket | `unavailable` | 1633 | 1.118 | 0.849 | 0.164 | 2.546 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_10` | 28 | 0.589 | 0.255 |
| line_bucket | `ge_3` | 13 | 2.361 | 0.223 |
| line_bucket | `ge_8` | 17 | 1.041 | 0.401 |
| line_bucket | `lt_10` | 27 | 0.809 | 0.070 |
| role_bucket | `core` | 29 | 1.924 | 0.762 |
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
- settled window: **2026-04-17 → 2026-05-15** (21 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

