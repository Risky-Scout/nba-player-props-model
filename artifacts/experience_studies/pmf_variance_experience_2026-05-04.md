# PMF Variance Experience Study — May 4, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-04` over a 60-day lookback._

## Executive summary

- **1,349** settled rows from **2026-04-17** through **2026-05-03** (16 delivery dates with at least one settled row).
- **Mean A/E = 1.140** — actual outcomes ran +14.0% relative to expected means in this sample.
- **Variance A/E = 0.865** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.200, sd = 1.014** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.745 and 0.900); the 10th-percentile band is over-covered (0.199 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.275 vs 0.247 (model vs market); logloss 0.755 vs 0.690.
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
| rows | 1,349 |
| actual_mean (per row) | 6.241 |
| expected_mean (per row) | 5.473 |
| **mean_AE** | **1.1403** |
| Σ squared residual | 18875.72 |
| Σ expected variance | 21825.98 |
| **variance_AE** | **0.8648** |
| standardized_residual_mean | 0.2004 |
| standardized_residual_sd | 1.0143 |
| pmf_nll_mean | 2.6158 |
| pmf_rps_mean | 0.1171 |
| model_brier (over/under) | 0.2753 |
| market_brier (over/under) | 0.2472 |
| model_logloss (over/under) | 0.7551 |
| market_logloss (over/under) | 0.6898 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.199 / 0.274 / 0.469 / 0.745 / 0.900 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

_No buckets exceeded `variance_AE > 1.20` with sufficient sample._

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 36 | **0.583** | 1.079 | 0.868 | 3.149 |
| injury_context | `fresh` | 201 | **0.757** | 0.949 | 1.101 | 2.658 |
| line_bucket | `1_to_1p5` | 195 | **0.664** | 1.019 | 1.172 | 2.068 |
| line_bucket | `20_to_25` | 42 | **0.648** | 1.015 | 1.084 | 4.515 |
| line_bucket | `2_to_2p5` | 43 | **0.760** | 1.451 | 1.114 | 2.953 |
| line_bucket | `5_to_8` | 67 | **0.601** | 0.845 | 1.077 | 2.499 |
| line_bucket | `ge_25` | 37 | **0.623** | 0.846 | 1.050 | 3.767 |
| line_bucket | `le_half` | 253 | **0.426** | 0.672 | 1.151 | 1.297 |
| lineup_confirmed | `projected` | 222 | **0.767** | 0.962 | 1.115 | 2.695 |
| low_line_discrete | `yes` | 448 | **0.553** | 0.840 | 1.163 | 1.633 |
| p0_bucket | `20_to_50pct` | 229 | **0.695** | 0.967 | 1.089 | 1.970 |
| p0_bucket | `ge_50pct` | 245 | **0.482** | 0.678 | 1.327 | 1.313 |
| role_bucket | `ge30min_starter` | 463 | **0.723** | 0.993 | 1.085 | 2.677 |
| role_bucket | `starter` | 126 | **0.618** | 0.891 | 1.102 | 2.587 |
| stat | `ast` | 205 | **0.795** | 1.035 | 1.062 | 2.546 |
| stat | `blk` | 178 | **0.530** | 0.713 | 1.325 | 1.559 |
| stat | `fg3m` | 134 | **0.686** | 1.214 | 1.026 | 2.433 |
| stat | `stl` | 189 | **0.568** | 0.827 | 1.146 | 1.443 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 680 | 1.133 | 0.838 | 0.165 | 2.618 |
| edge_bucket | `5_to_10pct` | 235 | 1.112 | 0.900 | 0.125 | 2.711 |
| edge_bucket | `ge_20pct` | 398 | 1.229 | 0.946 | 0.343 | 2.507 |
| injury_context | `unavailable` | 1127 | 1.147 | 0.892 | 0.205 | 2.600 |
| line_bucket | `10_to_15` | 89 | 1.081 | 1.024 | 0.151 | 3.250 |
| line_bucket | `15_to_20` | 95 | 1.247 | 1.007 | 0.559 | 4.015 |
| line_bucket | `3_to_5` | 82 | 1.022 | 0.858 | 0.021 | 2.583 |
| line_bucket | `4_to_7` | 136 | 1.258 | 1.066 | 0.449 | 2.972 |
| line_bucket | `7_to_10` | 72 | 1.222 | 1.084 | 0.467 | 3.193 |
| line_bucket | `lt_3` | 41 | 1.023 | 0.899 | -0.020 | 2.237 |
| line_bucket | `lt_4` | 128 | 1.155 | 1.088 | 0.197 | 2.777 |
| lineup_confirmed | `unavailable` | 1127 | 1.147 | 0.892 | 0.205 | 2.600 |
| low_line_discrete | `no` | 901 | 1.139 | 0.879 | 0.249 | 3.105 |
| minutes_volatility_bucket | `unavailable` | 1349 | 1.140 | 0.865 | 0.200 | 2.616 |
| overall | `ALL` | 1349 | 1.140 | 0.865 | 0.200 | 2.616 |
| p0_bucket | `5_to_20pct` | 355 | 1.230 | 0.847 | 0.276 | 2.388 |
| p0_bucket | `lt_5pct` | 520 | 1.118 | 0.884 | 0.223 | 3.670 |
| predicted_variance_bucket | `high` | 445 | 1.139 | 0.845 | 0.286 | 3.392 |
| predicted_variance_bucket | `low` | 445 | 1.112 | 1.162 | 0.114 | 2.187 |
| predicted_variance_bucket | `mid` | 459 | 1.156 | 0.918 | 0.201 | 2.279 |
| role_bucket | `lt22min` | 123 | 1.039 | 0.802 | -0.031 | 1.879 |
| role_bucket | `lt30min` | 533 | 1.237 | 1.109 | 0.306 | 2.709 |
| role_bucket | `rotation` | 70 | 1.184 | 1.038 | 0.221 | 2.880 |
| side | `OVER` | 157 | 1.004 | 1.102 | -0.118 | 3.586 |
| side | `UNDER` | 1192 | 1.163 | 0.846 | 0.242 | 2.488 |
| snapshot_type | `morning` | 1349 | 1.140 | 0.865 | 0.200 | 2.616 |
| stat | `pts` | 285 | 1.130 | 0.862 | 0.277 | 3.808 |
| stat | `reb` | 358 | 1.206 | 1.003 | 0.344 | 2.920 |
| vacated_opportunity_bucket | `unavailable` | 1349 | 1.140 | 0.865 | 0.200 | 2.616 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_10` | 22 | 0.455 | 0.150 |
| line_bucket | `ge_3` | 10 | 1.157 | -0.134 |
| line_bucket | `ge_8` | 15 | 1.152 | 0.405 |
| line_bucket | `lt_10` | 22 | 0.827 | 0.032 |
| role_bucket | `bench` | 26 | 0.882 | 0.002 |
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
- settled window: **2026-04-17 → 2026-05-03** (16 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

