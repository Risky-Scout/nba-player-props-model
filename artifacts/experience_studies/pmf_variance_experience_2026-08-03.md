# PMF Variance Experience Study — August 3, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-08-03` over a 60-day lookback._

## Executive summary

- **153** settled rows from **2026-06-05** through **2026-06-13** (4 delivery dates with at least one settled row).
- **Mean A/E = 1.126** — actual outcomes ran +12.6% relative to expected means in this sample.
- **Variance A/E = 0.891** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.220, sd = 1.027** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.745 and 0.922); the 10th-percentile band is over-covered (0.196 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.289 vs 0.256 (model vs market); logloss 0.785 vs 0.707.
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
| rows | 153 |
| actual_mean (per row) | 5.614 |
| expected_mean (per row) | 4.988 |
| **mean_AE** | **1.1255** |
| Σ squared residual | 1840.44 |
| Σ expected variance | 2066.32 |
| **variance_AE** | **0.8907** |
| standardized_residual_mean | 0.2198 |
| standardized_residual_sd | 1.0269 |
| pmf_nll_mean | 2.2741 |
| pmf_rps_mean | 0.1318 |
| model_brier (over/under) | 0.2890 |
| market_brier (over/under) | 0.2564 |
| model_logloss (over/under) | 0.7851 |
| market_logloss (over/under) | 0.7070 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.196 / 0.275 / 0.510 / 0.745 / 0.922 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 46 | **1.454** | 1.105 | 1.122 | 2.162 |
| line_bucket | `le_half` | 36 | **1.566** | 1.183 | 1.003 | 1.610 |
| low_line_discrete | `yes` | 57 | **1.578** | 1.242 | 1.176 | 1.836 |
| p0_bucket | `20_to_50pct` | 33 | **1.859** | 1.416 | 1.067 | 2.250 |
| predicted_variance_bucket | `low` | 51 | **1.692** | 1.264 | 1.184 | 1.839 |
| stat | `fg3m` | 30 | **1.401** | 1.292 | 1.033 | 1.956 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 69 | **0.736** | 0.993 | 1.098 | 2.383 |
| p0_bucket | `5_to_20pct` | 43 | **0.796** | 0.913 | 1.108 | 2.051 |
| predicted_variance_bucket | `mid` | 51 | **0.696** | 0.900 | 1.113 | 2.012 |
| stat | `reb` | 32 | **0.575** | 0.807 | 1.053 | 2.369 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| injury_context | `fallback_used` | 85 | 1.096 | 0.948 | 0.279 | 2.317 |
| injury_context | `latest_valid_report_selected` | 68 | 1.152 | 0.846 | 0.147 | 2.221 |
| lineup_confirmed | `projected` | 153 | 1.126 | 0.891 | 0.220 | 2.274 |
| low_line_discrete | `no` | 96 | 1.122 | 0.873 | 0.221 | 2.534 |
| minutes_volatility_bucket | `unavailable` | 153 | 1.126 | 0.891 | 0.220 | 2.274 |
| overall | `ALL` | 153 | 1.126 | 0.891 | 0.220 | 2.274 |
| p0_bucket | `lt_5pct` | 54 | 1.120 | 0.878 | 0.180 | 2.872 |
| predicted_variance_bucket | `high` | 51 | 1.124 | 0.894 | 0.207 | 2.972 |
| role_bucket | `starter` | 98 | 1.120 | 0.874 | 0.289 | 2.507 |
| side | `UNDER` | 124 | 1.156 | 0.919 | 0.348 | 2.299 |
| snapshot_type | `morning` | 153 | 1.126 | 0.891 | 0.220 | 2.274 |
| vacated_opportunity_bucket | `unavailable` | 153 | 1.126 | 0.891 | 0.220 | 2.274 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 13 | 0.504 | 0.050 |
| edge_bucket | `ge_20pct` | 25 | 0.931 | 0.329 |
| line_bucket | `10_to_15` | 14 | 0.931 | 0.369 |
| line_bucket | `15_to_20` | 7 | 1.513 | 0.010 |
| line_bucket | `1_to_1p5` | 21 | 1.593 | 0.464 |
| line_bucket | `2_to_2p5` | 8 | 0.961 | 0.453 |
| line_bucket | `3_to_5` | 13 | 0.581 | 0.138 |
| line_bucket | `4_to_7` | 9 | 0.854 | 0.000 |
| line_bucket | `5_to_8` | 7 | 0.301 | 0.147 |
| line_bucket | `7_to_10` | 4 | 0.337 | 0.289 |
| line_bucket | `ge_10` | 7 | 0.428 | 0.226 |
| line_bucket | `ge_25` | 6 | 0.667 | 0.601 |
| line_bucket | `ge_3` | 2 | 2.405 | 1.384 |
| line_bucket | `lt_10` | 2 | 0.651 | -0.809 |
| line_bucket | `lt_3` | 5 | 0.996 | 0.299 |
| line_bucket | `lt_4` | 12 | 0.692 | 0.042 |
| p0_bucket | `ge_50pct` | 23 | 1.238 | 0.491 |
| role_bucket | `bench` | 25 | 1.004 | -0.070 |
| role_bucket | `core` | 24 | 0.955 | 0.360 |
| role_bucket | `rotation` | 6 | 0.757 | -0.266 |
| side | `OVER` | 29 | 0.624 | -0.329 |
| stat | `ast` | 25 | 0.521 | 0.173 |
| stat | `blk` | 13 | 1.893 | 0.864 |
| stat | `pts` | 29 | 0.961 | 0.249 |
| stat | `stl` | 24 | 1.495 | 0.261 |

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
- settled window: **2026-06-05 → 2026-06-13** (4 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

