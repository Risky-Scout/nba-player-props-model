# PMF Variance Experience Study — May 6, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-06` over a 60-day lookback._

## Executive summary

- **1,411** settled rows from **2026-04-17** through **2026-05-04** (17 delivery dates with at least one settled row).
- **Mean A/E = 1.133** — actual outcomes ran +13.3% relative to expected means in this sample.
- **Variance A/E = 0.856** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.191, sd = 1.011** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.747 and 0.901); the 10th-percentile band is over-covered (0.198 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.274 vs 0.247 (model vs market); logloss 0.752 vs 0.689.
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
| rows | 1,411 |
| actual_mean (per row) | 6.218 |
| expected_mean (per row) | 5.488 |
| **mean_AE** | **1.1330** |
| Σ squared residual | 19665.49 |
| Σ expected variance | 22965.32 |
| **variance_AE** | **0.8563** |
| standardized_residual_mean | 0.1912 |
| standardized_residual_sd | 1.0112 |
| pmf_nll_mean | 2.6035 |
| pmf_rps_mean | 0.1164 |
| model_brier (over/under) | 0.2740 |
| market_brier (over/under) | 0.2471 |
| model_logloss (over/under) | 0.7520 |
| market_logloss (over/under) | 0.6894 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.198 / 0.279 / 0.476 / 0.747 / 0.901 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

_No buckets exceeded `variance_AE > 1.20` with sufficient sample._

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 40 | **0.543** | 1.023 | 0.868 | 2.998 |
| injury_context | `fresh` | 249 | **0.733** | 0.930 | 1.076 | 2.618 |
| line_bucket | `1_to_1p5` | 203 | **0.643** | 1.004 | 1.169 | 2.047 |
| line_bucket | `20_to_25` | 44 | **0.616** | 0.994 | 1.079 | 4.454 |
| line_bucket | `2_to_2p5` | 46 | **0.737** | 1.416 | 1.102 | 2.900 |
| line_bucket | `5_to_8` | 70 | **0.609** | 0.852 | 1.054 | 2.491 |
| line_bucket | `ge_25` | 40 | **0.664** | 0.867 | 1.038 | 3.778 |
| line_bucket | `le_half` | 264 | **0.413** | 0.665 | 1.117 | 1.288 |
| lineup_confirmed | `projected` | 270 | **0.743** | 0.943 | 1.089 | 2.651 |
| low_line_discrete | `yes` | 467 | **0.535** | 0.830 | 1.148 | 1.618 |
| p0_bucket | `20_to_50pct` | 240 | **0.684** | 0.958 | 1.083 | 1.946 |
| p0_bucket | `ge_50pct` | 252 | **0.472** | 0.672 | 1.313 | 1.305 |
| role_bucket | `ge30min_starter` | 472 | **0.722** | 0.986 | 1.084 | 2.647 |
| role_bucket | `starter` | 154 | **0.603** | 0.875 | 1.063 | 2.562 |
| stat | `ast` | 214 | **0.795** | 1.030 | 1.056 | 2.531 |
| stat | `blk` | 185 | **0.734** | 0.759 | 1.365 | 1.612 |
| stat | `fg3m` | 144 | **0.644** | 1.180 | 1.031 | 2.391 |
| stat | `stl` | 196 | **0.557** | 0.820 | 1.113 | 1.425 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 710 | 1.131 | 0.830 | 0.166 | 2.614 |
| edge_bucket | `5_to_10pct` | 256 | 1.100 | 0.885 | 0.102 | 2.667 |
| edge_bucket | `ge_20pct` | 405 | 1.216 | 0.954 | 0.331 | 2.505 |
| injury_context | `unavailable` | 1141 | 1.147 | 0.895 | 0.203 | 2.592 |
| line_bucket | `10_to_15` | 91 | 1.078 | 0.997 | 0.147 | 3.240 |
| line_bucket | `15_to_20` | 99 | 1.234 | 0.972 | 0.531 | 3.981 |
| line_bucket | `3_to_5` | 86 | 1.028 | 0.845 | 0.031 | 2.558 |
| line_bucket | `4_to_7` | 145 | 1.244 | 1.062 | 0.428 | 2.935 |
| line_bucket | `7_to_10` | 74 | 1.205 | 1.074 | 0.432 | 3.170 |
| line_bucket | `lt_3` | 43 | 1.046 | 0.920 | 0.015 | 2.240 |
| line_bucket | `lt_4` | 133 | 1.133 | 1.070 | 0.166 | 2.738 |
| lineup_confirmed | `unavailable` | 1141 | 1.147 | 0.895 | 0.203 | 2.592 |
| low_line_discrete | `no` | 944 | 1.132 | 0.871 | 0.239 | 3.091 |
| minutes_volatility_bucket | `unavailable` | 1411 | 1.133 | 0.856 | 0.191 | 2.604 |
| overall | `ALL` | 1411 | 1.133 | 0.856 | 0.191 | 2.604 |
| p0_bucket | `5_to_20pct` | 372 | 1.225 | 0.860 | 0.268 | 2.397 |
| p0_bucket | `lt_5pct` | 547 | 1.111 | 0.872 | 0.210 | 3.631 |
| predicted_variance_bucket | `high` | 466 | 1.131 | 0.833 | 0.270 | 3.376 |
| predicted_variance_bucket | `low` | 466 | 1.113 | 1.123 | 0.113 | 2.159 |
| predicted_variance_bucket | `mid` | 479 | 1.148 | 0.935 | 0.191 | 2.285 |
| role_bucket | `bench` | 32 | 0.861 | 0.814 | -0.066 | 2.549 |
| role_bucket | `lt22min` | 124 | 1.037 | 0.801 | -0.035 | 1.867 |
| role_bucket | `lt30min` | 537 | 1.239 | 1.119 | 0.309 | 2.720 |
| role_bucket | `rotation` | 84 | 1.191 | 1.014 | 0.288 | 2.855 |
| side | `OVER` | 168 | 0.985 | 1.050 | -0.145 | 3.478 |
| side | `UNDER` | 1243 | 1.158 | 0.840 | 0.237 | 2.485 |
| snapshot_type | `morning` | 1411 | 1.133 | 0.856 | 0.191 | 2.604 |
| stat | `pts` | 297 | 1.123 | 0.847 | 0.266 | 3.791 |
| stat | `reb` | 375 | 1.194 | 1.006 | 0.323 | 2.891 |
| vacated_opportunity_bucket | `unavailable` | 1411 | 1.133 | 0.856 | 0.191 | 2.604 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_10` | 23 | 0.546 | 0.222 |
| line_bucket | `ge_3` | 12 | 2.705 | 0.209 |
| line_bucket | `ge_8` | 15 | 1.152 | 0.405 |
| line_bucket | `lt_10` | 23 | 0.887 | 0.095 |
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
- settled window: **2026-04-17 → 2026-05-04** (17 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

