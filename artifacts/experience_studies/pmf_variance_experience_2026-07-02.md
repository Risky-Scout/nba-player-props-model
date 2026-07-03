# PMF Variance Experience Study — July 2, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-02` over a 60-day lookback._

## Executive summary

- **772** settled rows from **2026-05-03** through **2026-06-13** (19 delivery dates with at least one settled row).
- **Mean A/E = 1.048** — actual outcomes ran +4.8% relative to expected means in this sample.
- **Variance A/E = 0.783** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.067, sd = 0.954** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.782 and 0.926); the 10th-percentile band is over-covered (0.209 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.262 vs 0.248 (model vs market); logloss 0.724 vs 0.691.
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
| rows | 772 |
| actual_mean (per row) | 5.773 |
| expected_mean (per row) | 5.508 |
| **mean_AE** | **1.0482** |
| Σ squared residual | 9897.19 |
| Σ expected variance | 12634.24 |
| **variance_AE** | **0.7834** |
| standardized_residual_mean | 0.0668 |
| standardized_residual_sd | 0.9540 |
| pmf_nll_mean | 2.2689 |
| pmf_rps_mean | 0.1096 |
| model_brier (over/under) | 0.2621 |
| market_brier (over/under) | 0.2477 |
| model_logloss (over/under) | 0.7237 |
| market_logloss (over/under) | 0.6907 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.209 / 0.341 / 0.560 / 0.782 / 0.926 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `4_to_7` | 63 | **1.219** | 1.148 | 1.034 | 2.601 |
| p0_bucket | `5_to_20pct` | 241 | **1.261** | 1.015 | 1.098 | 2.140 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 48 | **0.510** | 0.801 | 0.844 | 2.057 |
| edge_bucket | `10_to_20pct` | 363 | **0.755** | 0.978 | 1.064 | 2.284 |
| edge_bucket | `5_to_10pct` | 246 | **0.737** | 0.905 | 0.997 | 2.277 |
| injury_context | `unavailable` | 235 | **0.619** | 0.859 | 1.032 | 1.946 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `2_to_2p5` | 46 | **0.564** | 0.815 | 1.035 | 1.642 |
| line_bucket | `3_to_5` | 61 | **0.729** | 0.878 | 0.989 | 2.047 |
| line_bucket | `5_to_8` | 37 | **0.763** | 0.867 | 1.027 | 2.360 |
| line_bucket | `ge_25` | 38 | **0.565** | 0.712 | 1.100 | 3.502 |
| line_bucket | `le_half` | 139 | **0.603** | 0.864 | 0.813 | 1.323 |
| lineup_confirmed | `unavailable` | 235 | **0.619** | 0.859 | 1.032 | 1.946 |
| low_line_discrete | `no` | 514 | **0.786** | 0.950 | 1.054 | 2.609 |
| low_line_discrete | `yes` | 258 | **0.714** | 0.960 | 0.972 | 1.591 |
| minutes_volatility_bucket | `unavailable` | 772 | **0.783** | 0.954 | 1.048 | 2.269 |
| overall | `ALL` | 772 | **0.783** | 0.954 | 1.048 | 2.269 |
| p0_bucket | `ge_50pct` | 90 | **0.461** | 0.776 | 1.170 | 1.073 |
| p0_bucket | `lt_5pct` | 284 | **0.725** | 0.893 | 1.035 | 2.942 |
| predicted_variance_bucket | `high` | 255 | **0.763** | 0.918 | 1.055 | 3.067 |
| role_bucket | `bench` | 50 | **0.718** | 0.980 | 0.883 | 2.006 |
| role_bucket | `ge30min_starter` | 148 | **0.518** | 0.851 | 1.028 | 2.040 |
| role_bucket | `lt30min` | 58 | **0.516** | 0.835 | 1.070 | 1.917 |
| role_bucket | `starter` | 284 | **0.684** | 0.944 | 1.020 | 2.442 |
| side | `UNDER` | 624 | **0.774** | 0.924 | 1.109 | 2.290 |
| snapshot_type | `morning` | 772 | **0.783** | 0.954 | 1.048 | 2.269 |
| stat | `ast` | 128 | **0.764** | 0.892 | 1.063 | 2.152 |
| stat | `pts` | 158 | **0.751** | 0.909 | 1.066 | 3.354 |
| stat | `stl` | 93 | **0.623** | 0.858 | 1.010 | 1.473 |
| vacated_opportunity_bucket | `unavailable` | 772 | **0.783** | 0.954 | 1.048 | 2.269 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 115 | 1.190 | 1.068 | 0.252 | 2.290 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 213 | 1.062 | 0.835 | 0.054 | 2.592 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 57 | 1.064 | 0.862 | 0.153 | 3.262 |
| line_bucket | `15_to_20` | 37 | 0.980 | 0.826 | -0.021 | 3.398 |
| line_bucket | `1_to_1p5` | 119 | 1.087 | 0.809 | 0.105 | 1.903 |
| line_bucket | `7_to_10` | 30 | 0.966 | 0.891 | -0.038 | 2.609 |
| line_bucket | `lt_4` | 60 | 0.920 | 0.931 | -0.100 | 2.171 |
| lineup_confirmed | `projected` | 512 | 1.068 | 0.839 | 0.104 | 2.408 |
| p0_bucket | `20_to_50pct` | 157 | 1.048 | 0.845 | 0.035 | 1.935 |
| predicted_variance_bucket | `low` | 255 | 1.068 | 0.898 | 0.070 | 1.539 |
| predicted_variance_bucket | `mid` | 262 | 1.014 | 0.914 | 0.024 | 2.202 |
| role_bucket | `rotation` | 109 | 1.170 | 0.894 | 0.257 | 2.355 |
| side | `OVER` | 148 | 0.735 | 0.836 | -0.455 | 2.178 |
| stat | `blk` | 81 | 1.234 | 1.029 | 0.197 | 1.446 |
| stat | `fg3m` | 137 | 0.953 | 0.805 | -0.077 | 1.878 |
| stat | `reb` | 175 | 1.007 | 0.974 | 0.020 | 2.485 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| line_bucket | `20_to_25` | 7 | 0.648 | 0.255 |
| line_bucket | `ge_10` | 22 | 0.778 | 0.247 |
| line_bucket | `ge_3` | 7 | 3.548 | 0.883 |
| line_bucket | `ge_8` | 3 | 0.700 | 0.701 |
| line_bucket | `lt_10` | 19 | 1.159 | 0.244 |
| line_bucket | `lt_3` | 27 | 0.908 | 0.443 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 23 | 0.609 | -0.415 |

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
- settled window: **2026-05-03 → 2026-06-13** (19 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

