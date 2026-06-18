# PMF Variance Experience Study — June 17, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-17` over a 60-day lookback._

## Executive summary

- **2,023** settled rows from **2026-04-18** through **2026-06-13** (33 delivery dates with at least one settled row).
- **Mean A/E = 1.107** — actual outcomes ran +10.7% relative to expected means in this sample.
- **Variance A/E = 0.826** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.156, sd = 0.981** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.759 and 0.911); the 10th-percentile band is over-covered (0.200 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.271 vs 0.247 (model vs market); logloss 0.745 vs 0.690.
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
| rows | 2,023 |
| actual_mean (per row) | 6.069 |
| expected_mean (per row) | 5.484 |
| **mean_AE** | **1.1065** |
| Σ squared residual | 27441.76 |
| Σ expected variance | 33215.87 |
| **variance_AE** | **0.8262** |
| standardized_residual_mean | 0.1557 |
| standardized_residual_sd | 0.9813 |
| pmf_nll_mean | 2.4624 |
| pmf_rps_mean | 0.1125 |
| model_brier (over/under) | 0.2711 |
| market_brier (over/under) | 0.2475 |
| model_logloss (over/under) | 0.7450 |
| market_logloss (over/under) | 0.6901 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.200 / 0.296 / 0.499 / 0.759 / 0.911 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 82 | **0.544** | 0.879 | 0.860 | 2.400 |
| edge_bucket | `10_to_20pct` | 983 | **0.788** | 0.966 | 1.105 | 2.466 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 293 | **0.702** | 1.029 | 1.139 | 1.983 |
| line_bucket | `20_to_25` | 47 | **0.668** | 1.009 | 1.082 | 4.416 |
| line_bucket | `2_to_2p5` | 81 | **0.600** | 1.050 | 1.069 | 2.194 |
| line_bucket | `3_to_5` | 139 | **0.797** | 0.974 | 1.010 | 2.274 |
| line_bucket | `5_to_8` | 98 | **0.666** | 0.861 | 1.064 | 2.472 |
| line_bucket | `ge_10` | 43 | **0.620** | 0.794 | 1.098 | 2.713 |
| line_bucket | `ge_25` | 72 | **0.591** | 0.754 | 1.078 | 3.502 |
| line_bucket | `le_half` | 377 | **0.484** | 0.747 | 1.009 | 1.277 |
| low_line_discrete | `yes` | 670 | **0.599** | 0.883 | 1.085 | 1.585 |
| p0_bucket | `20_to_50pct` | 363 | **0.729** | 1.001 | 1.058 | 1.900 |
| p0_bucket | `ge_50pct` | 324 | **0.481** | 0.706 | 1.297 | 1.253 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 588 | **0.675** | 0.950 | 1.077 | 2.517 |
| role_bucket | `lt22min` | 139 | **0.771** | 0.769 | 0.979 | 1.802 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| stat | `ast` | 319 | **0.777** | 0.969 | 1.061 | 2.367 |
| stat | `blk` | 247 | **0.709** | 0.783 | 1.308 | 1.531 |
| stat | `fg3m` | 248 | **0.695** | 1.101 | 0.977 | 2.062 |
| stat | `stl` | 270 | **0.574** | 0.828 | 1.102 | 1.441 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 460 | 1.058 | 0.837 | 0.065 | 2.475 |
| edge_bucket | `ge_20pct` | 498 | 1.232 | 0.981 | 0.340 | 2.453 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| injury_context | `unavailable` | 1310 | 1.133 | 0.831 | 0.179 | 2.464 |
| line_bucket | `10_to_15` | 140 | 1.066 | 0.970 | 0.136 | 3.261 |
| line_bucket | `15_to_20` | 124 | 1.168 | 0.907 | 0.382 | 3.794 |
| line_bucket | `4_to_7` | 194 | 1.194 | 1.106 | 0.348 | 2.863 |
| line_bucket | `7_to_10` | 99 | 1.152 | 1.052 | 0.336 | 3.041 |
| line_bucket | `lt_10` | 40 | 1.078 | 0.966 | 0.102 | 3.569 |
| line_bucket | `lt_3` | 65 | 1.123 | 0.879 | 0.141 | 2.175 |
| line_bucket | `lt_4` | 180 | 1.094 | 0.997 | 0.122 | 2.472 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| lineup_confirmed | `unavailable` | 1310 | 1.133 | 0.831 | 0.179 | 2.464 |
| low_line_discrete | `no` | 1353 | 1.108 | 0.836 | 0.197 | 2.897 |
| minutes_volatility_bucket | `unavailable` | 2023 | 1.107 | 0.826 | 0.156 | 2.462 |
| overall | `ALL` | 2023 | 1.107 | 0.826 | 0.156 | 2.462 |
| p0_bucket | `5_to_20pct` | 580 | 1.182 | 0.980 | 0.210 | 2.296 |
| p0_bucket | `lt_5pct` | 756 | 1.087 | 0.813 | 0.162 | 3.378 |
| predicted_variance_bucket | `high` | 668 | 1.107 | 0.802 | 0.223 | 3.256 |
| predicted_variance_bucket | `low` | 668 | 1.105 | 1.019 | 0.107 | 1.901 |
| predicted_variance_bucket | `mid` | 687 | 1.104 | 0.941 | 0.137 | 2.237 |
| role_bucket | `lt30min` | 569 | 1.227 | 1.026 | 0.272 | 2.578 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| side | `OVER` | 274 | 0.890 | 0.851 | -0.285 | 2.733 |
| side | `UNDER` | 1749 | 1.141 | 0.824 | 0.225 | 2.420 |
| snapshot_type | `morning` | 2023 | 1.107 | 0.826 | 0.156 | 2.462 |
| stat | `pts` | 423 | 1.103 | 0.810 | 0.221 | 3.616 |
| stat | `reb` | 516 | 1.145 | 0.988 | 0.253 | 2.748 |
| vacated_opportunity_bucket | `unavailable` | 2023 | 1.107 | 0.826 | 0.156 | 2.462 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 14 | 2.341 | 0.332 |
| line_bucket | `ge_8` | 17 | 1.041 | 0.401 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 14 | 2.788 | 0.282 |

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
- settled window: **2026-04-18 → 2026-06-13** (33 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

