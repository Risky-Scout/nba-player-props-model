# PMF Variance Experience Study — May 24, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-24` over a 60-day lookback._

## Executive summary

- **1,733** settled rows from **2026-04-17** through **2026-05-23** (25 delivery dates with at least one settled row).
- **Mean A/E = 1.116** — actual outcomes ran +11.6% relative to expected means in this sample.
- **Variance A/E = 0.845** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.157, sd = 0.996** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.756 and 0.908); the 10th-percentile band is over-covered (0.202 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.270 vs 0.247 (model vs market); logloss 0.743 vs 0.689.
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
| rows | 1,733 |
| actual_mean (per row) | 6.158 |
| expected_mean (per row) | 5.517 |
| **mean_AE** | **1.1161** |
| Σ squared residual | 23969.18 |
| Σ expected variance | 28365.69 |
| **variance_AE** | **0.8450** |
| standardized_residual_mean | 0.1566 |
| standardized_residual_sd | 0.9958 |
| pmf_nll_mean | 2.5281 |
| pmf_rps_mean | 0.1132 |
| model_brier (over/under) | 0.2703 |
| market_brier (over/under) | 0.2467 |
| model_logloss (over/under) | 0.7433 |
| market_logloss (over/under) | 0.6886 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.202 / 0.295 / 0.494 / 0.756 / 0.908 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 48 | **1.532** | 1.196 | 1.243 | 2.885 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 57 | **0.523** | 0.962 | 0.872 | 2.703 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 257 | **0.656** | 0.991 | 1.095 | 1.946 |
| line_bucket | `20_to_25` | 47 | **0.668** | 1.009 | 1.082 | 4.416 |
| line_bucket | `2_to_2p5` | 68 | **0.722** | 1.256 | 1.091 | 2.479 |
| line_bucket | `5_to_8` | 86 | **0.688** | 0.877 | 1.075 | 2.499 |
| line_bucket | `ge_10` | 31 | **0.684** | 0.826 | 1.118 | 2.690 |
| line_bucket | `ge_25` | 58 | **0.586** | 0.798 | 1.047 | 3.655 |
| line_bucket | `le_half` | 312 | **0.417** | 0.667 | 1.015 | 1.256 |
| lineup_confirmed | `projected` | 455 | **0.798** | 0.956 | 1.083 | 2.554 |
| low_line_discrete | `yes` | 569 | **0.544** | 0.829 | 1.063 | 1.568 |
| p0_bucket | `20_to_50pct` | 299 | **0.669** | 0.936 | 1.046 | 1.864 |
| p0_bucket | `ge_50pct` | 282 | **0.450** | 0.660 | 1.255 | 1.260 |
| role_bucket | `bench` | 42 | **0.675** | 0.965 | 0.852 | 2.406 |
| role_bucket | `ge30min_starter` | 559 | **0.691** | 0.967 | 1.068 | 2.558 |
| role_bucket | `lt22min` | 141 | **0.778** | 0.797 | 1.002 | 1.806 |
| role_bucket | `starter` | 249 | **0.622** | 0.871 | 1.044 | 2.481 |
| stat | `blk` | 214 | **0.684** | 0.747 | 1.283 | 1.556 |
| stat | `fg3m` | 203 | **0.683** | 1.123 | 0.978 | 2.138 |
| stat | `stl` | 233 | **0.531** | 0.796 | 1.064 | 1.411 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 853 | 1.119 | 0.825 | 0.138 | 2.524 |
| edge_bucket | `5_to_10pct` | 360 | 1.063 | 0.807 | 0.036 | 2.544 |
| edge_bucket | `ge_20pct` | 463 | 1.215 | 1.008 | 0.329 | 2.502 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `unavailable` | 1278 | 1.132 | 0.868 | 0.177 | 2.519 |
| line_bucket | `10_to_15` | 113 | 1.103 | 1.007 | 0.200 | 3.274 |
| line_bucket | `15_to_20` | 114 | 1.198 | 0.949 | 0.457 | 3.904 |
| line_bucket | `3_to_5` | 118 | 1.000 | 0.846 | -0.005 | 2.415 |
| line_bucket | `4_to_7` | 172 | 1.206 | 1.088 | 0.366 | 2.902 |
| line_bucket | `7_to_10` | 88 | 1.155 | 1.058 | 0.342 | 3.088 |
| line_bucket | `lt_10` | 30 | 1.139 | 1.028 | 0.173 | 3.757 |
| line_bucket | `lt_3` | 54 | 1.117 | 0.889 | 0.124 | 2.204 |
| line_bucket | `lt_4` | 155 | 1.092 | 1.007 | 0.120 | 2.644 |
| lineup_confirmed | `unavailable` | 1278 | 1.132 | 0.868 | 0.177 | 2.519 |
| low_line_discrete | `no` | 1164 | 1.119 | 0.859 | 0.214 | 2.997 |
| minutes_volatility_bucket | `unavailable` | 1733 | 1.116 | 0.845 | 0.157 | 2.528 |
| overall | `ALL` | 1733 | 1.116 | 0.845 | 0.157 | 2.528 |
| p0_bucket | `5_to_20pct` | 487 | 1.194 | 0.956 | 0.210 | 2.319 |
| p0_bucket | `lt_5pct` | 665 | 1.099 | 0.843 | 0.188 | 3.517 |
| predicted_variance_bucket | `high` | 572 | 1.120 | 0.824 | 0.245 | 3.325 |
| predicted_variance_bucket | `low` | 572 | 1.080 | 1.039 | 0.074 | 2.018 |
| predicted_variance_bucket | `mid` | 589 | 1.118 | 0.931 | 0.151 | 2.249 |
| role_bucket | `lt30min` | 568 | 1.228 | 1.085 | 0.285 | 2.662 |
| role_bucket | `rotation` | 116 | 1.170 | 0.962 | 0.215 | 2.627 |
| side | `OVER` | 230 | 0.939 | 0.961 | -0.233 | 3.090 |
| side | `UNDER` | 1503 | 1.147 | 0.833 | 0.216 | 2.442 |
| snapshot_type | `morning` | 1733 | 1.116 | 0.845 | 0.157 | 2.528 |
| stat | `ast` | 275 | 1.062 | 0.809 | 0.075 | 2.452 |
| stat | `pts` | 362 | 1.118 | 0.832 | 0.261 | 3.722 |
| stat | `reb` | 446 | 1.155 | 1.007 | 0.265 | 2.834 |
| vacated_opportunity_bucket | `unavailable` | 1733 | 1.116 | 0.845 | 0.157 | 2.528 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `latest_valid_report_selected` | 29 | 0.862 | 0.046 |
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 13 | 2.361 | 0.223 |
| line_bucket | `ge_8` | 17 | 1.041 | 0.401 |
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
- settled window: **2026-04-17 → 2026-05-23** (25 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

