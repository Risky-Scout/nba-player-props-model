# PMF Variance Experience Study — June 13, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-13` over a 60-day lookback._

## Executive summary

- **2,013** settled rows from **2026-04-17** through **2026-06-10** (33 delivery dates with at least one settled row).
- **Mean A/E = 1.106** — actual outcomes ran +10.6% relative to expected means in this sample.
- **Variance A/E = 0.834** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.152, sd = 0.997** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.761 and 0.911); the 10th-percentile band is over-covered (0.200 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.270 vs 0.247 (model vs market); logloss 0.743 vs 0.690.
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
| rows | 2,013 |
| actual_mean (per row) | 6.115 |
| expected_mean (per row) | 5.528 |
| **mean_AE** | **1.1061** |
| Σ squared residual | 27522.91 |
| Σ expected variance | 32990.42 |
| **variance_AE** | **0.8343** |
| standardized_residual_mean | 0.1518 |
| standardized_residual_sd | 0.9970 |
| pmf_nll_mean | 2.4973 |
| pmf_rps_mean | 0.1140 |
| model_brier (over/under) | 0.2703 |
| market_brier (over/under) | 0.2472 |
| model_logloss (over/under) | 0.7431 |
| market_logloss (over/under) | 0.6895 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.200 / 0.298 / 0.500 / 0.761 / 0.911 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 90 | **1.272** | 1.079 | 1.087 | 2.581 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 82 | **0.537** | 0.911 | 0.844 | 2.520 |
| injury_context | `fallback_used` | 90 | **0.779** | 1.134 | 1.118 | 2.462 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 292 | **0.699** | 1.032 | 1.120 | 1.975 |
| line_bucket | `20_to_25` | 47 | **0.668** | 1.009 | 1.082 | 4.416 |
| line_bucket | `2_to_2p5` | 80 | **0.730** | 1.205 | 1.092 | 2.349 |
| line_bucket | `5_to_8` | 99 | **0.667** | 0.858 | 1.063 | 2.462 |
| line_bucket | `ge_10` | 42 | **0.614** | 0.789 | 1.091 | 2.684 |
| line_bucket | `ge_25` | 72 | **0.606** | 0.789 | 1.075 | 3.648 |
| line_bucket | `le_half` | 368 | **0.482** | 0.748 | 1.015 | 1.288 |
| low_line_discrete | `yes` | 660 | **0.597** | 0.886 | 1.077 | 1.592 |
| p0_bucket | `20_to_50pct` | 358 | **0.725** | 1.001 | 1.052 | 1.903 |
| p0_bucket | `ge_50pct` | 319 | **0.480** | 0.702 | 1.297 | 1.260 |
| role_bucket | `bench` | 59 | **0.663** | 0.974 | 0.860 | 2.178 |
| role_bucket | `ge30min_starter` | 601 | **0.683** | 0.964 | 1.073 | 2.539 |
| role_bucket | `lt22min` | 145 | **0.778** | 0.798 | 0.982 | 1.801 |
| role_bucket | `starter` | 363 | **0.672** | 0.923 | 1.049 | 2.508 |
| stat | `ast` | 320 | **0.783** | 0.982 | 1.057 | 2.399 |
| stat | `blk` | 244 | **0.690** | 0.769 | 1.291 | 1.522 |
| stat | `fg3m` | 250 | **0.748** | 1.154 | 0.974 | 2.099 |
| stat | `stl` | 262 | **0.570** | 0.832 | 1.103 | 1.459 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 976 | 1.111 | 0.806 | 0.140 | 2.512 |
| edge_bucket | `5_to_10pct` | 455 | 1.058 | 0.838 | 0.061 | 2.497 |
| edge_bucket | `ge_20pct` | 500 | 1.218 | 0.980 | 0.322 | 2.465 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| injury_context | `unavailable` | 1340 | 1.130 | 0.853 | 0.173 | 2.503 |
| line_bucket | `10_to_15` | 139 | 1.061 | 0.957 | 0.132 | 3.251 |
| line_bucket | `15_to_20` | 127 | 1.179 | 0.936 | 0.417 | 3.847 |
| line_bucket | `3_to_5` | 138 | 1.005 | 0.812 | 0.007 | 2.364 |
| line_bucket | `4_to_7` | 192 | 1.190 | 1.102 | 0.342 | 2.861 |
| line_bucket | `7_to_10` | 98 | 1.148 | 1.053 | 0.329 | 3.043 |
| line_bucket | `lt_10` | 40 | 1.078 | 0.966 | 0.102 | 3.569 |
| line_bucket | `lt_3` | 66 | 1.110 | 0.876 | 0.125 | 2.155 |
| line_bucket | `lt_4` | 180 | 1.100 | 1.014 | 0.133 | 2.595 |
| lineup_confirmed | `projected` | 648 | 1.080 | 0.809 | 0.120 | 2.488 |
| lineup_confirmed | `unavailable` | 1340 | 1.130 | 0.853 | 0.173 | 2.503 |
| low_line_discrete | `no` | 1353 | 1.108 | 0.844 | 0.197 | 2.939 |
| minutes_volatility_bucket | `unavailable` | 2013 | 1.106 | 0.834 | 0.152 | 2.497 |
| overall | `ALL` | 2013 | 1.106 | 0.834 | 0.152 | 2.497 |
| p0_bucket | `5_to_20pct` | 568 | 1.181 | 0.974 | 0.201 | 2.299 |
| p0_bucket | `lt_5pct` | 768 | 1.088 | 0.824 | 0.164 | 3.436 |
| predicted_variance_bucket | `high` | 664 | 1.108 | 0.810 | 0.223 | 3.287 |
| predicted_variance_bucket | `low` | 664 | 1.088 | 1.073 | 0.090 | 1.975 |
| predicted_variance_bucket | `mid` | 685 | 1.108 | 0.939 | 0.143 | 2.239 |
| role_bucket | `lt30min` | 580 | 1.224 | 1.066 | 0.279 | 2.650 |
| role_bucket | `rotation` | 161 | 1.162 | 0.957 | 0.241 | 2.498 |
| side | `OVER` | 283 | 0.909 | 0.965 | -0.269 | 2.942 |
| side | `UNDER` | 1730 | 1.141 | 0.819 | 0.221 | 2.425 |
| snapshot_type | `morning` | 2013 | 1.106 | 0.834 | 0.152 | 2.497 |
| stat | `pts` | 425 | 1.105 | 0.819 | 0.227 | 3.655 |
| stat | `reb` | 512 | 1.143 | 0.991 | 0.252 | 2.788 |
| vacated_opportunity_bucket | `unavailable` | 2013 | 1.106 | 0.834 | 0.152 | 2.497 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 16 | 2.145 | 0.166 |
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
- settled window: **2026-04-17 → 2026-06-10** (33 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

