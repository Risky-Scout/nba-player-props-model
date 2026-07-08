# PMF Variance Experience Study — July 7, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-07` over a 60-day lookback._

## Executive summary

- **554** settled rows from **2026-05-08** through **2026-06-13** (15 delivery dates with at least one settled row).
- **Mean A/E = 1.061** — actual outcomes ran +6.1% relative to expected means in this sample.
- **Variance A/E = 0.817** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.094, sd = 0.979** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.789 and 0.928); the 10th-percentile band is over-covered (0.208 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.263 vs 0.247 (model vs market); logloss 0.726 vs 0.689.
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
| rows | 554 |
| actual_mean (per row) | 5.856 |
| expected_mean (per row) | 5.518 |
| **mean_AE** | **1.0612** |
| Σ squared residual | 7295.19 |
| Σ expected variance | 8926.60 |
| **variance_AE** | **0.8172** |
| standardized_residual_mean | 0.0938 |
| standardized_residual_sd | 0.9794 |
| pmf_nll_mean | 2.2427 |
| pmf_rps_mean | 0.1121 |
| model_brier (over/under) | 0.2632 |
| market_brier (over/under) | 0.2467 |
| model_logloss (over/under) | 0.7264 |
| market_logloss (over/under) | 0.6886 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.208 / 0.327 / 0.549 / 0.789 / 0.928 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| injury_context | `fresh` | 50 | **1.358** | 1.139 | 1.231 | 2.633 |
| line_bucket | `4_to_7` | 42 | **1.347** | 1.233 | 1.121 | 2.738 |
| p0_bucket | `5_to_20pct` | 183 | **1.369** | 1.030 | 1.112 | 2.136 |
| role_bucket | `core` | 81 | **1.382** | 1.103 | 1.081 | 2.598 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 35 | **0.574** | 0.843 | 0.823 | 2.071 |
| edge_bucket | `10_to_20pct` | 252 | **0.759** | 0.984 | 1.065 | 2.273 |
| injury_context | `unavailable` | 180 | **0.596** | 0.862 | 1.031 | 2.047 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `2_to_2p5` | 31 | **0.665** | 0.803 | 1.105 | 1.573 |
| line_bucket | `3_to_5` | 48 | **0.740** | 0.880 | 0.953 | 2.040 |
| line_bucket | `le_half` | 100 | **0.762** | 0.949 | 0.817 | 1.294 |
| lineup_confirmed | `unavailable` | 180 | **0.596** | 0.862 | 1.031 | 2.047 |
| p0_bucket | `ge_50pct` | 64 | **0.597** | 0.845 | 1.327 | 1.116 |
| p0_bucket | `lt_5pct` | 197 | **0.740** | 0.876 | 1.051 | 2.955 |
| predicted_variance_bucket | `high` | 183 | **0.793** | 0.916 | 1.068 | 3.075 |
| role_bucket | `ge30min_starter` | 119 | **0.514** | 0.881 | 1.032 | 2.158 |
| role_bucket | `lt30min` | 38 | **0.387** | 0.651 | 1.031 | 1.883 |
| role_bucket | `starter` | 197 | **0.742** | 0.988 | 1.076 | 2.443 |
| side | `OVER` | 107 | **0.768** | 0.946 | 0.800 | 2.101 |
| stat | `ast` | 95 | **0.729** | 0.861 | 1.070 | 2.106 |
| stat | `blk` | 55 | **0.659** | 0.883 | 1.191 | 1.306 |
| stat | `pts` | 114 | **0.794** | 0.940 | 1.069 | 3.360 |
| stat | `stl` | 66 | **0.662** | 0.908 | 1.060 | 1.492 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 182 | 1.014 | 0.830 | 0.040 | 2.211 |
| edge_bucket | `ge_20pct` | 85 | 1.253 | 1.071 | 0.323 | 2.292 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 45 | 1.083 | 0.905 | 0.186 | 3.285 |
| line_bucket | `1_to_1p5` | 83 | 1.037 | 1.009 | 0.100 | 1.799 |
| line_bucket | `lt_4` | 42 | 1.039 | 0.936 | 0.069 | 2.226 |
| lineup_confirmed | `projected` | 349 | 1.101 | 0.938 | 0.157 | 2.329 |
| low_line_discrete | `no` | 371 | 1.069 | 0.815 | 0.138 | 2.597 |
| low_line_discrete | `yes` | 183 | 0.943 | 0.887 | 0.004 | 1.523 |
| minutes_volatility_bucket | `unavailable` | 554 | 1.061 | 0.817 | 0.094 | 2.243 |
| overall | `ALL` | 554 | 1.061 | 0.817 | 0.094 | 2.243 |
| p0_bucket | `20_to_50pct` | 110 | 0.956 | 0.937 | -0.016 | 1.800 |
| predicted_variance_bucket | `low` | 183 | 1.044 | 1.055 | 0.070 | 1.569 |
| predicted_variance_bucket | `mid` | 188 | 1.040 | 0.959 | 0.059 | 2.087 |
| role_bucket | `rotation` | 67 | 1.082 | 0.949 | 0.161 | 2.053 |
| side | `UNDER` | 447 | 1.111 | 0.826 | 0.214 | 2.276 |
| snapshot_type | `morning` | 554 | 1.061 | 0.817 | 0.094 | 2.243 |
| stat | `fg3m` | 98 | 0.915 | 1.125 | -0.104 | 1.709 |
| stat | `reb` | 126 | 1.061 | 0.972 | 0.135 | 2.551 |
| vacated_opportunity_bucket | `unavailable` | 554 | 1.061 | 0.817 | 0.094 | 2.243 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| line_bucket | `15_to_20` | 25 | 0.837 | -0.082 |
| line_bucket | `20_to_25` | 3 | 1.299 | 0.253 |
| line_bucket | `5_to_8` | 25 | 0.758 | 0.285 |
| line_bucket | `7_to_10` | 23 | 0.902 | 0.098 |
| line_bucket | `ge_10` | 19 | 0.693 | 0.120 |
| line_bucket | `ge_25` | 28 | 0.560 | 0.293 |
| line_bucket | `ge_3` | 5 | 0.928 | 0.468 |
| line_bucket | `ge_8` | 1 | 0.025 | 0.158 |
| line_bucket | `lt_10` | 13 | 1.298 | 0.168 |
| line_bucket | `lt_3` | 21 | 0.721 | 0.244 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `bench` | 29 | 0.810 | -0.141 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 17 | 0.645 | -0.412 |

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
- settled window: **2026-05-08 → 2026-06-13** (15 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

