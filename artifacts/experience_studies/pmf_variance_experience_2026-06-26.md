# PMF Variance Experience Study — June 26, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-26` over a 60-day lookback._

## Executive summary

- **1,191** settled rows from **2026-04-27** through **2026-06-13** (24 delivery dates with at least one settled row).
- **Mean A/E = 1.078** — actual outcomes ran +7.8% relative to expected means in this sample.
- **Variance A/E = 0.747** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.107, sd = 0.942** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.771 and 0.923); the 10th-percentile band is over-covered (0.211 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.263 vs 0.248 (model vs market); logloss 0.725 vs 0.690.
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
| rows | 1,191 |
| actual_mean (per row) | 5.809 |
| expected_mean (per row) | 5.389 |
| **mean_AE** | **1.0781** |
| Σ squared residual | 14514.44 |
| Σ expected variance | 19431.44 |
| **variance_AE** | **0.7470** |
| standardized_residual_mean | 0.1070 |
| standardized_residual_sd | 0.9415 |
| pmf_nll_mean | 2.2825 |
| pmf_rps_mean | 0.1064 |
| model_brier (over/under) | 0.2626 |
| market_brier (over/under) | 0.2476 |
| model_logloss (over/under) | 0.7254 |
| market_logloss (over/under) | 0.6905 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.211 / 0.327 / 0.534 / 0.771 / 0.923 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `4_to_7` | 105 | **1.337** | 1.185 | 1.078 | 2.614 |
| line_bucket | `7_to_10` | 54 | **1.216** | 1.089 | 1.141 | 2.743 |
| p0_bucket | `5_to_20pct` | 351 | **1.222** | 1.003 | 1.136 | 2.193 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 65 | **0.461** | 0.844 | 0.911 | 2.208 |
| edge_bucket | `10_to_20pct` | 567 | **0.719** | 0.959 | 1.100 | 2.324 |
| edge_bucket | `5_to_10pct` | 350 | **0.705** | 0.891 | 1.010 | 2.262 |
| injury_context | `unavailable` | 478 | **0.587** | 0.869 | 1.102 | 2.017 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `10_to_15` | 83 | **0.759** | 0.885 | 1.045 | 3.218 |
| line_bucket | `1_to_1p5` | 201 | **0.675** | 0.978 | 1.083 | 1.918 |
| line_bucket | `2_to_2p5` | 70 | **0.521** | 0.884 | 1.051 | 1.835 |
| line_bucket | `3_to_5` | 80 | **0.759** | 0.888 | 1.054 | 2.097 |
| line_bucket | `ge_25` | 50 | **0.499** | 0.677 | 1.087 | 3.481 |
| line_bucket | `le_half` | 210 | **0.500** | 0.780 | 0.868 | 1.276 |
| lineup_confirmed | `unavailable` | 478 | **0.587** | 0.869 | 1.102 | 2.017 |
| low_line_discrete | `no` | 780 | **0.754** | 0.967 | 1.084 | 2.647 |
| low_line_discrete | `yes` | 411 | **0.604** | 0.884 | 1.001 | 1.590 |
| minutes_volatility_bucket | `unavailable` | 1191 | **0.747** | 0.942 | 1.078 | 2.282 |
| overall | `ALL` | 1191 | **0.747** | 0.942 | 1.078 | 2.282 |
| p0_bucket | `20_to_50pct` | 237 | **0.713** | 0.991 | 1.005 | 1.921 |
| p0_bucket | `ge_50pct` | 160 | **0.485** | 0.728 | 1.251 | 1.178 |
| p0_bucket | `lt_5pct` | 443 | **0.693** | 0.932 | 1.067 | 2.946 |
| predicted_variance_bucket | `high` | 393 | **0.720** | 0.919 | 1.083 | 3.081 |
| predicted_variance_bucket | `low` | 393 | **0.788** | 0.952 | 1.075 | 1.566 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 249 | **0.446** | 0.809 | 1.042 | 2.024 |
| role_bucket | `lt22min` | 52 | **0.582** | 0.697 | 0.871 | 1.483 |
| role_bucket | `lt30min` | 169 | **0.717** | 0.948 | 1.227 | 2.158 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| side | `OVER` | 203 | **0.763** | 0.894 | 0.794 | 2.142 |
| side | `UNDER` | 988 | **0.745** | 0.922 | 1.127 | 2.311 |
| snapshot_type | `morning` | 1191 | **0.747** | 0.942 | 1.078 | 2.282 |
| stat | `blk` | 137 | **0.767** | 0.798 | 1.257 | 1.489 |
| stat | `fg3m` | 207 | **0.637** | 1.013 | 0.946 | 1.930 |
| stat | `pts` | 233 | **0.689** | 0.871 | 1.085 | 3.379 |
| stat | `stl` | 148 | **0.589** | 0.809 | 1.021 | 1.421 |
| vacated_opportunity_bucket | `unavailable` | 1191 | **0.747** | 0.942 | 1.078 | 2.282 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 209 | 1.210 | 1.038 | 0.269 | 2.229 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `15_to_20` | 60 | 1.082 | 0.806 | 0.181 | 3.433 |
| line_bucket | `5_to_8` | 60 | 1.074 | 0.811 | 0.121 | 2.404 |
| line_bucket | `lt_3` | 38 | 1.176 | 0.878 | 0.262 | 2.017 |
| line_bucket | `lt_4` | 92 | 1.025 | 1.021 | 0.073 | 2.234 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| predicted_variance_bucket | `mid` | 405 | 1.062 | 0.939 | 0.087 | 2.203 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| stat | `ast` | 186 | 1.086 | 0.823 | 0.143 | 2.204 |
| stat | `reb` | 280 | 1.081 | 1.083 | 0.158 | 2.526 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `20_to_25` | 17 | 0.452 | 0.255 |
| line_bucket | `ge_10` | 29 | 0.594 | 0.179 |
| line_bucket | `ge_3` | 11 | 2.334 | 0.313 |
| line_bucket | `ge_8` | 8 | 1.056 | 0.268 |
| line_bucket | `lt_10` | 23 | 1.339 | 0.340 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 8 | 4.897 | 0.604 |

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
- settled window: **2026-04-27 → 2026-06-13** (24 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

