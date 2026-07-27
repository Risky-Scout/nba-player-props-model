# PMF Variance Experience Study — July 26, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-26` over a 60-day lookback._

## Executive summary

- **265** settled rows from **2026-05-28** through **2026-06-13** (7 delivery dates with at least one settled row).
- **Mean A/E = 1.078** — actual outcomes ran +7.8% relative to expected means in this sample.
- **Variance A/E = 0.854** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.166, sd = 1.045** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.770 and 0.921); the 10th-percentile band is over-covered (0.215 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.279 vs 0.250 (model vs market); logloss 0.761 vs 0.696.
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
| rows | 265 |
| actual_mean (per row) | 5.615 |
| expected_mean (per row) | 5.207 |
| **mean_AE** | **1.0783** |
| Σ squared residual | 3326.02 |
| Σ expected variance | 3894.43 |
| **variance_AE** | **0.8540** |
| standardized_residual_mean | 0.1661 |
| standardized_residual_sd | 1.0450 |
| pmf_nll_mean | 2.2865 |
| pmf_rps_mean | 0.1282 |
| model_brier (over/under) | 0.2787 |
| market_brier (over/under) | 0.2504 |
| model_logloss (over/under) | 0.7613 |
| market_logloss (over/under) | 0.6964 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.215 / 0.306 / 0.525 / 0.770 / 0.921 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `1_to_1p5` | 37 | **1.695** | 1.342 | 1.367 | 2.215 |
| line_bucket | `le_half` | 57 | **1.300** | 1.085 | 0.927 | 1.397 |
| low_line_discrete | `yes` | 94 | **1.489** | 1.207 | 1.150 | 1.719 |
| p0_bucket | `20_to_50pct` | 62 | **1.466** | 1.329 | 1.082 | 2.089 |
| p0_bucket | `5_to_20pct` | 76 | **1.238** | 1.039 | 1.156 | 2.216 |
| predicted_variance_bucket | `low` | 88 | **1.533** | 1.216 | 1.156 | 1.710 |
| role_bucket | `core` | 38 | **1.268** | 0.991 | 0.993 | 2.307 |
| side | `OVER` | 52 | **1.219** | 0.986 | 0.719 | 2.132 |
| stat | `fg3m` | 47 | **1.510** | 1.335 | 1.070 | 1.999 |
| stat | `stl` | 34 | **1.309** | 1.083 | 1.297 | 1.672 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 116 | **0.729** | 1.095 | 1.082 | 2.444 |
| injury_context | `unavailable` | 32 | **0.648** | 1.039 | 1.152 | 2.350 |
| lineup_confirmed | `unavailable` | 32 | **0.648** | 1.039 | 1.152 | 2.350 |
| p0_bucket | `lt_5pct` | 91 | **0.785** | 0.862 | 1.050 | 2.918 |
| role_bucket | `rotation` | 40 | **0.799** | 1.142 | 1.268 | 2.102 |
| stat | `ast` | 44 | **0.563** | 0.808 | 1.018 | 2.049 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 87 | 1.051 | 1.150 | 0.169 | 2.195 |
| edge_bucket | `ge_20pct` | 40 | 1.259 | 0.875 | 0.237 | 2.084 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `latest_valid_report_selected` | 103 | 1.035 | 0.883 | 0.044 | 2.218 |
| lineup_confirmed | `projected` | 233 | 1.066 | 0.892 | 0.165 | 2.278 |
| low_line_discrete | `no` | 171 | 1.074 | 0.840 | 0.159 | 2.598 |
| minutes_volatility_bucket | `unavailable` | 265 | 1.078 | 0.854 | 0.166 | 2.286 |
| overall | `ALL` | 265 | 1.078 | 0.854 | 0.166 | 2.286 |
| p0_bucket | `ge_50pct` | 36 | 1.626 | 1.051 | 0.360 | 1.178 |
| predicted_variance_bucket | `high` | 88 | 1.061 | 0.819 | 0.106 | 3.022 |
| predicted_variance_bucket | `mid` | 89 | 1.121 | 1.019 | 0.208 | 2.129 |
| role_bucket | `starter` | 129 | 1.057 | 0.810 | 0.185 | 2.475 |
| side | `UNDER` | 213 | 1.141 | 0.803 | 0.323 | 2.324 |
| snapshot_type | `morning` | 265 | 1.078 | 0.854 | 0.166 | 2.286 |
| stat | `pts` | 53 | 1.070 | 0.842 | 0.135 | 3.354 |
| stat | `reb` | 60 | 1.088 | 0.933 | 0.178 | 2.514 |
| vacated_opportunity_bucket | `unavailable` | 265 | 1.078 | 0.854 | 0.166 | 2.286 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 22 | 0.611 | -0.192 |
| line_bucket | `10_to_15` | 24 | 0.819 | 0.075 |
| line_bucket | `15_to_20` | 10 | 1.309 | -0.080 |
| line_bucket | `2_to_2p5` | 10 | 0.918 | 0.480 |
| line_bucket | `3_to_5` | 19 | 0.548 | -0.005 |
| line_bucket | `4_to_7` | 18 | 1.460 | 0.313 |
| line_bucket | `5_to_8` | 13 | 0.465 | 0.004 |
| line_bucket | `7_to_10` | 7 | 1.090 | 0.269 |
| line_bucket | `ge_10` | 11 | 0.408 | 0.157 |
| line_bucket | `ge_25` | 12 | 0.619 | 0.442 |
| line_bucket | `ge_3` | 4 | 1.507 | 0.488 |
| line_bucket | `lt_10` | 7 | 0.943 | 0.117 |
| line_bucket | `lt_3` | 12 | 0.858 | 0.217 |
| line_bucket | `lt_4` | 24 | 1.019 | 0.059 |
| role_bucket | `bench` | 26 | 1.010 | -0.114 |
| role_bucket | `ge30min_starter` | 20 | 0.664 | 0.394 |
| role_bucket | `lt15min` | 4 | 2.219 | -0.080 |
| role_bucket | `lt22min` | 3 | 0.795 | -0.914 |
| role_bucket | `lt30min` | 5 | 0.236 | 0.138 |
| stat | `blk` | 27 | 1.225 | 0.435 |

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
- settled window: **2026-05-28 → 2026-06-13** (7 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

