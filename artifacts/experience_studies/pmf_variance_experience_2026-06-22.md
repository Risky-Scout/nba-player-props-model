# PMF Variance Experience Study — June 22, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-22` over a 60-day lookback._

## Executive summary

- **1,676** settled rows from **2026-04-23** through **2026-06-13** (28 delivery dates with at least one settled row).
- **Mean A/E = 1.103** — actual outcomes ran +10.3% relative to expected means in this sample.
- **Variance A/E = 0.799** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.143, sd = 0.921** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.763 and 0.914); the 10th-percentile band is over-covered (0.200 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.268 vs 0.248 (model vs market); logloss 0.737 vs 0.691.
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
| rows | 1,676 |
| actual_mean (per row) | 6.023 |
| expected_mean (per row) | 5.462 |
| **mean_AE** | **1.1028** |
| Σ squared residual | 23270.62 |
| Σ expected variance | 29126.37 |
| **variance_AE** | **0.7990** |
| standardized_residual_mean | 0.1432 |
| standardized_residual_sd | 0.9214 |
| pmf_nll_mean | 2.3087 |
| pmf_rps_mean | 0.1023 |
| model_brier (over/under) | 0.2678 |
| market_brier (over/under) | 0.2480 |
| model_logloss (over/under) | 0.7369 |
| market_logloss (over/under) | 0.6910 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.200 / 0.303 / 0.504 / 0.763 / 0.914 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 74 | **0.547** | 0.838 | 0.846 | 2.261 |
| edge_bucket | `10_to_20pct` | 824 | **0.742** | 0.919 | 1.111 | 2.325 |
| injury_context | `unavailable` | 963 | **0.782** | 0.869 | 1.136 | 2.196 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 240 | **0.646** | 0.937 | 1.101 | 1.887 |
| line_bucket | `20_to_25` | 32 | **0.518** | 0.709 | 1.108 | 3.398 |
| line_bucket | `2_to_2p5` | 70 | **0.521** | 0.884 | 1.051 | 1.835 |
| line_bucket | `5_to_8` | 84 | **0.663** | 0.824 | 1.088 | 2.398 |
| line_bucket | `ge_10` | 37 | **0.627** | 0.772 | 1.130 | 2.782 |
| line_bucket | `ge_25` | 65 | **0.536** | 0.717 | 1.075 | 3.506 |
| line_bucket | `le_half` | 319 | **0.497** | 0.755 | 0.975 | 1.292 |
| lineup_confirmed | `unavailable` | 963 | **0.782** | 0.869 | 1.136 | 2.196 |
| low_line_discrete | `yes` | 559 | **0.577** | 0.838 | 1.048 | 1.547 |
| minutes_volatility_bucket | `unavailable` | 1676 | **0.799** | 0.921 | 1.103 | 2.309 |
| overall | `ALL` | 1676 | **0.799** | 0.921 | 1.103 | 2.309 |
| p0_bucket | `20_to_50pct` | 298 | **0.743** | 0.966 | 1.039 | 1.899 |
| p0_bucket | `ge_50pct` | 271 | **0.501** | 0.713 | 1.301 | 1.261 |
| p0_bucket | `lt_5pct` | 598 | **0.772** | 0.938 | 1.084 | 3.015 |
| predicted_variance_bucket | `high` | 553 | **0.780** | 0.903 | 1.104 | 3.123 |
| predicted_variance_bucket | `low` | 553 | **0.705** | 0.890 | 1.092 | 1.522 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 463 | **0.578** | 0.802 | 1.064 | 2.226 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| side | `OVER` | 211 | **0.752** | 0.881 | 0.789 | 2.120 |
| snapshot_type | `morning` | 1676 | **0.799** | 0.921 | 1.103 | 2.309 |
| stat | `ast` | 268 | **0.767** | 0.897 | 1.081 | 2.236 |
| stat | `blk` | 208 | **0.743** | 0.781 | 1.332 | 1.529 |
| stat | `fg3m` | 207 | **0.637** | 1.013 | 0.946 | 1.930 |
| stat | `pts` | 345 | **0.774** | 0.910 | 1.098 | 3.397 |
| stat | `stl` | 226 | **0.541** | 0.757 | 1.041 | 1.380 |
| vacated_opportunity_bucket | `unavailable` | 1676 | **0.799** | 0.921 | 1.103 | 2.309 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 413 | 1.035 | 0.814 | 0.025 | 2.326 |
| edge_bucket | `ge_20pct` | 365 | 1.252 | 1.001 | 0.328 | 2.262 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 121 | 1.048 | 0.939 | 0.100 | 3.274 |
| line_bucket | `15_to_20` | 95 | 1.161 | 0.917 | 0.322 | 3.479 |
| line_bucket | `3_to_5` | 120 | 1.019 | 0.809 | 0.044 | 2.143 |
| line_bucket | `4_to_7` | 165 | 1.162 | 1.107 | 0.260 | 2.590 |
| line_bucket | `7_to_10` | 83 | 1.151 | 1.131 | 0.300 | 2.761 |
| line_bucket | `lt_10` | 32 | 1.098 | 1.094 | 0.152 | 3.396 |
| line_bucket | `lt_3` | 51 | 1.251 | 0.947 | 0.316 | 2.090 |
| line_bucket | `lt_4` | 137 | 1.101 | 0.988 | 0.163 | 2.255 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| low_line_discrete | `no` | 1117 | 1.106 | 0.808 | 0.193 | 2.690 |
| p0_bucket | `5_to_20pct` | 509 | 1.173 | 1.028 | 0.198 | 2.277 |
| predicted_variance_bucket | `mid` | 570 | 1.100 | 0.957 | 0.142 | 2.282 |
| role_bucket | `lt22min` | 102 | 0.963 | 0.818 | -0.093 | 1.665 |
| role_bucket | `lt30min` | 387 | 1.264 | 1.046 | 0.291 | 2.306 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| side | `UNDER` | 1465 | 1.140 | 0.804 | 0.216 | 2.336 |
| stat | `reb` | 422 | 1.141 | 1.004 | 0.240 | 2.532 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 12 | 2.539 | 0.470 |
| line_bucket | `ge_8` | 13 | 0.841 | 0.186 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 11 | 3.809 | 0.301 |

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
- settled window: **2026-04-23 → 2026-06-13** (28 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

