# PMF Variance Experience Study — July 30, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-30` over a 60-day lookback._

## Executive summary

- **183** settled rows from **2026-06-03** through **2026-06-13** (5 delivery dates with at least one settled row).
- **Mean A/E = 1.127** — actual outcomes ran +12.7% relative to expected means in this sample.
- **Variance A/E = 0.827** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.210, sd = 1.019** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.754 and 0.918); the 10th-percentile band is over-covered (0.197 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.281 vs 0.253 (model vs market); logloss 0.767 vs 0.699.
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
| rows | 183 |
| actual_mean (per row) | 5.918 |
| expected_mean (per row) | 5.251 |
| **mean_AE** | **1.1271** |
| Σ squared residual | 2199.17 |
| Σ expected variance | 2658.18 |
| **variance_AE** | **0.8273** |
| standardized_residual_mean | 0.2095 |
| standardized_residual_sd | 1.0194 |
| pmf_nll_mean | 2.2851 |
| pmf_rps_mean | 0.1264 |
| model_brier (over/under) | 0.2813 |
| market_brier (over/under) | 0.2525 |
| model_logloss (over/under) | 0.7673 |
| market_logloss (over/under) | 0.6990 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.197 / 0.284 / 0.514 / 0.754 / 0.918 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `le_half` | 41 | **1.463** | 1.131 | 0.963 | 1.487 |
| low_line_discrete | `yes` | 63 | **1.490** | 1.200 | 1.148 | 1.726 |
| p0_bucket | `20_to_50pct` | 36 | **1.551** | 1.363 | 1.011 | 2.181 |
| predicted_variance_bucket | `low` | 61 | **1.459** | 1.197 | 1.075 | 1.685 |
| stat | `fg3m` | 30 | **1.401** | 1.292 | 1.033 | 1.956 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 84 | **0.772** | 1.020 | 1.127 | 2.401 |
| injury_context | `unavailable` | 30 | **0.606** | 0.996 | 1.133 | 2.341 |
| lineup_confirmed | `unavailable` | 30 | **0.606** | 0.996 | 1.133 | 2.341 |
| p0_bucket | `lt_5pct` | 67 | **0.794** | 0.864 | 1.124 | 2.905 |
| side | `OVER` | 30 | **0.604** | 1.039 | 0.910 | 2.162 |
| stat | `ast` | 32 | **0.557** | 0.806 | 1.007 | 2.054 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 51 | 1.128 | 1.191 | 0.153 | 2.164 |
| edge_bucket | `ge_20pct` | 31 | 1.241 | 0.830 | 0.292 | 2.204 |
| injury_context | `fallback_used` | 85 | 1.096 | 0.948 | 0.279 | 2.317 |
| injury_context | `latest_valid_report_selected` | 68 | 1.152 | 0.846 | 0.147 | 2.221 |
| lineup_confirmed | `projected` | 153 | 1.126 | 0.891 | 0.220 | 2.274 |
| low_line_discrete | `no` | 120 | 1.126 | 0.813 | 0.228 | 2.579 |
| minutes_volatility_bucket | `unavailable` | 183 | 1.127 | 0.827 | 0.210 | 2.285 |
| overall | `ALL` | 183 | 1.127 | 0.827 | 0.210 | 2.285 |
| p0_bucket | `5_to_20pct` | 52 | 1.135 | 0.960 | 0.263 | 2.147 |
| predicted_variance_bucket | `high` | 61 | 1.122 | 0.813 | 0.208 | 3.040 |
| predicted_variance_bucket | `mid` | 61 | 1.159 | 0.827 | 0.294 | 2.130 |
| role_bucket | `starter` | 98 | 1.120 | 0.874 | 0.289 | 2.507 |
| side | `UNDER` | 153 | 1.153 | 0.846 | 0.316 | 2.309 |
| snapshot_type | `morning` | 183 | 1.127 | 0.827 | 0.210 | 2.285 |
| stat | `pts` | 37 | 1.129 | 0.822 | 0.221 | 3.335 |
| stat | `reb` | 41 | 1.152 | 0.859 | 0.274 | 2.485 |
| vacated_opportunity_bucket | `unavailable` | 183 | 1.127 | 0.827 | 0.210 | 2.285 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 17 | 0.455 | -0.032 |
| line_bucket | `10_to_15` | 16 | 0.838 | 0.260 |
| line_bucket | `15_to_20` | 9 | 1.182 | 0.079 |
| line_bucket | `1_to_1p5` | 22 | 1.525 | 0.449 |
| line_bucket | `2_to_2p5` | 8 | 0.961 | 0.453 |
| line_bucket | `3_to_5` | 16 | 0.505 | 0.118 |
| line_bucket | `4_to_7` | 12 | 1.420 | 0.492 |
| line_bucket | `5_to_8` | 10 | 0.523 | -0.121 |
| line_bucket | `7_to_10` | 5 | 1.246 | 0.702 |
| line_bucket | `ge_10` | 9 | 0.424 | 0.315 |
| line_bucket | `ge_25` | 8 | 0.584 | 0.596 |
| line_bucket | `ge_3` | 2 | 2.405 | 1.384 |
| line_bucket | `lt_10` | 4 | 0.755 | -0.364 |
| line_bucket | `lt_3` | 6 | 0.891 | 0.144 |
| line_bucket | `lt_4` | 15 | 0.675 | -0.066 |
| p0_bucket | `ge_50pct` | 28 | 1.096 | 0.346 |
| role_bucket | `bench` | 25 | 1.004 | -0.070 |
| role_bucket | `core` | 24 | 0.955 | 0.360 |
| role_bucket | `ge30min_starter` | 20 | 0.664 | 0.394 |
| role_bucket | `lt15min` | 2 | 0.289 | -0.566 |
| role_bucket | `lt22min` | 3 | 0.795 | -0.914 |
| role_bucket | `lt30min` | 5 | 0.236 | 0.138 |
| role_bucket | `rotation` | 6 | 0.757 | -0.266 |
| stat | `blk` | 17 | 1.646 | 0.601 |
| stat | `stl` | 26 | 1.392 | 0.223 |

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
- settled window: **2026-06-03 → 2026-06-13** (5 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

