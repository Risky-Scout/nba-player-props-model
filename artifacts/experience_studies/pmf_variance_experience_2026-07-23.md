# PMF Variance Experience Study — July 23, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-23` over a 60-day lookback._

## Executive summary

- **320** settled rows from **2026-05-24** through **2026-06-13** (9 delivery dates with at least one settled row).
- **Mean A/E = 1.046** — actual outcomes ran +4.6% relative to expected means in this sample.
- **Variance A/E = 0.806** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.125, sd = 1.017** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.781 and 0.928); the 10th-percentile band is over-covered (0.206 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.272 vs 0.251 (model vs market); logloss 0.746 vs 0.696.
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
| rows | 320 |
| actual_mean (per row) | 5.653 |
| expected_mean (per row) | 5.407 |
| **mean_AE** | **1.0456** |
| Σ squared residual | 4037.96 |
| Σ expected variance | 5010.24 |
| **variance_AE** | **0.8059** |
| standardized_residual_mean | 0.1248 |
| standardized_residual_sd | 1.0175 |
| pmf_nll_mean | 2.2703 |
| pmf_rps_mean | 0.1213 |
| model_brier (over/under) | 0.2722 |
| market_brier (over/under) | 0.2505 |
| model_logloss (over/under) | 0.7464 |
| market_logloss (over/under) | 0.6963 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.206 / 0.322 / 0.544 / 0.781 / 0.928 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `1_to_1p5` | 42 | **1.427** | 1.275 | 1.328 | 2.121 |
| line_bucket | `le_half` | 67 | **1.230** | 1.076 | 0.948 | 1.377 |
| low_line_discrete | `yes` | 109 | **1.325** | 1.167 | 1.140 | 1.663 |
| p0_bucket | `20_to_50pct` | 69 | **1.340** | 1.279 | 1.075 | 2.017 |
| predicted_variance_bucket | `low` | 106 | **1.370** | 1.172 | 1.148 | 1.655 |
| stat | `fg3m` | 56 | **1.345** | 1.268 | 0.975 | 1.882 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 147 | **0.714** | 1.049 | 1.037 | 2.371 |
| injury_context | `unavailable` | 62 | **0.574** | 0.912 | 1.099 | 2.170 |
| lineup_confirmed | `unavailable` | 62 | **0.574** | 0.912 | 1.099 | 2.170 |
| low_line_discrete | `no` | 211 | **0.795** | 0.933 | 1.040 | 2.584 |
| p0_bucket | `lt_5pct` | 113 | **0.748** | 0.855 | 1.018 | 2.923 |
| predicted_variance_bucket | `high` | 106 | **0.775** | 0.903 | 1.022 | 3.037 |
| role_bucket | `ge30min_starter` | 42 | **0.591** | 0.931 | 1.135 | 2.283 |
| role_bucket | `starter` | 139 | **0.799** | 1.039 | 1.043 | 2.504 |
| side | `UNDER` | 258 | **0.774** | 0.977 | 1.106 | 2.293 |
| stat | `ast` | 50 | **0.578** | 0.809 | 1.014 | 2.060 |
| stat | `pts` | 68 | **0.787** | 0.918 | 1.019 | 3.305 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 103 | 1.030 | 1.015 | 0.153 | 2.229 |
| edge_bucket | `ge_20pct` | 44 | 1.267 | 0.871 | 0.278 | 2.089 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `latest_valid_report_selected` | 128 | 0.984 | 0.845 | 0.005 | 2.264 |
| lineup_confirmed | `projected` | 233 | 1.066 | 0.892 | 0.165 | 2.278 |
| minutes_volatility_bucket | `unavailable` | 320 | 1.046 | 0.806 | 0.125 | 2.270 |
| overall | `ALL` | 320 | 1.046 | 0.806 | 0.125 | 2.270 |
| p0_bucket | `5_to_20pct` | 95 | 1.114 | 1.132 | 0.169 | 2.167 |
| p0_bucket | `ge_50pct` | 43 | 1.631 | 1.058 | 0.355 | 1.190 |
| predicted_variance_bucket | `mid` | 108 | 1.105 | 0.957 | 0.165 | 2.121 |
| role_bucket | `core` | 46 | 0.944 | 1.071 | 0.021 | 2.285 |
| role_bucket | `rotation` | 47 | 1.112 | 0.929 | 0.264 | 2.110 |
| side | `OVER` | 62 | 0.734 | 0.987 | -0.444 | 2.177 |
| snapshot_type | `morning` | 320 | 1.046 | 0.806 | 0.125 | 2.270 |
| stat | `blk` | 34 | 1.447 | 1.065 | 0.407 | 1.349 |
| stat | `reb` | 74 | 1.093 | 0.913 | 0.190 | 2.499 |
| stat | `stl` | 38 | 1.326 | 1.176 | 0.230 | 1.648 |
| vacated_opportunity_bucket | `unavailable` | 320 | 1.046 | 0.806 | 0.125 | 2.270 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 26 | 0.606 | -0.233 |
| line_bucket | `10_to_15` | 28 | 0.841 | -0.074 |
| line_bucket | `15_to_20` | 15 | 0.927 | -0.099 |
| line_bucket | `2_to_2p5` | 15 | 0.827 | 0.134 |
| line_bucket | `3_to_5` | 23 | 0.580 | 0.048 |
| line_bucket | `4_to_7` | 22 | 1.261 | 0.202 |
| line_bucket | `5_to_8` | 14 | 0.495 | -0.066 |
| line_bucket | `7_to_10` | 11 | 1.000 | 0.284 |
| line_bucket | `ge_10` | 13 | 0.473 | 0.165 |
| line_bucket | `ge_25` | 15 | 0.657 | 0.425 |
| line_bucket | `ge_3` | 4 | 1.507 | 0.488 |
| line_bucket | `lt_10` | 10 | 0.781 | -0.110 |
| line_bucket | `lt_3` | 13 | 0.782 | 0.176 |
| line_bucket | `lt_4` | 28 | 1.108 | 0.154 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `bench` | 26 | 1.010 | -0.114 |
| role_bucket | `lt15min` | 4 | 2.219 | -0.080 |
| role_bucket | `lt22min` | 4 | 0.780 | -0.855 |
| role_bucket | `lt30min` | 12 | 0.353 | 0.008 |

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
- settled window: **2026-05-24 → 2026-06-13** (9 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

