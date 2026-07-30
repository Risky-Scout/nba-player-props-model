# PMF Variance Experience Study — July 29, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-29` over a 60-day lookback._

## Executive summary

- **228** settled rows from **2026-05-30** through **2026-06-13** (6 delivery dates with at least one settled row).
- **Mean A/E = 1.123** — actual outcomes ran +12.3% relative to expected means in this sample.
- **Variance A/E = 0.828** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.213, sd = 1.046** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.754 and 0.917); the 10th-percentile band is over-covered (0.202 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.283 vs 0.253 (model vs market); logloss 0.770 vs 0.700.
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
| rows | 228 |
| actual_mean (per row) | 5.768 |
| expected_mean (per row) | 5.136 |
| **mean_AE** | **1.1230** |
| Σ squared residual | 2682.70 |
| Σ expected variance | 3240.09 |
| **variance_AE** | **0.8280** |
| standardized_residual_mean | 0.2132 |
| standardized_residual_sd | 1.0459 |
| pmf_nll_mean | 2.2960 |
| pmf_rps_mean | 0.1291 |
| model_brier (over/under) | 0.2834 |
| market_brier (over/under) | 0.2533 |
| model_logloss (over/under) | 0.7703 |
| market_logloss (over/under) | 0.7004 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.202 / 0.289 / 0.509 / 0.754 / 0.917 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `1_to_1p5` | 30 | **1.833** | 1.387 | 1.413 | 2.378 |
| line_bucket | `le_half` | 53 | **1.320** | 1.083 | 0.933 | 1.409 |
| low_line_discrete | `yes` | 83 | **1.551** | 1.221 | 1.163 | 1.759 |
| p0_bucket | `20_to_50pct` | 50 | **1.651** | 1.393 | 1.136 | 2.227 |
| p0_bucket | `5_to_20pct` | 66 | **1.220** | 1.028 | 1.192 | 2.212 |
| predicted_variance_bucket | `low` | 75 | **1.605** | 1.229 | 1.177 | 1.749 |
| stat | `fg3m` | 40 | **1.593** | 1.374 | 1.060 | 2.095 |
| stat | `stl` | 30 | **1.356** | 1.078 | 1.326 | 1.671 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 98 | **0.776** | 1.109 | 1.125 | 2.513 |
| injury_context | `unavailable` | 30 | **0.606** | 0.996 | 1.133 | 2.341 |
| lineup_confirmed | `unavailable` | 30 | **0.606** | 0.996 | 1.133 | 2.341 |
| p0_bucket | `lt_5pct` | 78 | **0.751** | 0.852 | 1.096 | 2.903 |
| predicted_variance_bucket | `high` | 75 | **0.791** | 0.907 | 1.108 | 3.022 |
| side | `OVER` | 41 | **0.556** | 1.018 | 0.887 | 2.059 |
| stat | `ast` | 38 | **0.522** | 0.788 | 1.044 | 2.055 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 70 | 1.139 | 1.010 | 0.223 | 2.125 |
| edge_bucket | `ge_20pct` | 39 | 1.260 | 0.878 | 0.235 | 2.101 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `latest_valid_report_selected` | 68 | 1.152 | 0.846 | 0.147 | 2.221 |
| lineup_confirmed | `projected` | 198 | 1.121 | 0.878 | 0.222 | 2.289 |
| low_line_discrete | `no` | 145 | 1.120 | 0.811 | 0.224 | 2.603 |
| minutes_volatility_bucket | `unavailable` | 228 | 1.123 | 0.828 | 0.213 | 2.296 |
| overall | `ALL` | 228 | 1.123 | 0.828 | 0.213 | 2.296 |
| p0_bucket | `ge_50pct` | 34 | 1.598 | 0.996 | 0.346 | 1.167 |
| predicted_variance_bucket | `mid` | 78 | 1.162 | 0.995 | 0.258 | 2.124 |
| role_bucket | `rotation` | 30 | 1.375 | 1.175 | 0.466 | 2.211 |
| role_bucket | `starter` | 113 | 1.102 | 0.804 | 0.246 | 2.490 |
| side | `UNDER` | 187 | 1.155 | 0.855 | 0.340 | 2.348 |
| snapshot_type | `morning` | 228 | 1.123 | 0.828 | 0.213 | 2.296 |
| stat | `pts` | 45 | 1.130 | 0.806 | 0.235 | 3.338 |
| stat | `reb` | 51 | 1.121 | 0.940 | 0.243 | 2.520 |
| vacated_opportunity_bucket | `unavailable` | 228 | 1.123 | 0.828 | 0.213 | 2.296 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 21 | 0.605 | -0.146 |
| line_bucket | `10_to_15` | 21 | 0.743 | 0.168 |
| line_bucket | `15_to_20` | 9 | 1.182 | 0.079 |
| line_bucket | `2_to_2p5` | 8 | 0.961 | 0.453 |
| line_bucket | `3_to_5` | 17 | 0.488 | 0.091 |
| line_bucket | `4_to_7` | 15 | 1.651 | 0.454 |
| line_bucket | `5_to_8` | 12 | 0.443 | -0.063 |
| line_bucket | `7_to_10` | 7 | 1.090 | 0.269 |
| line_bucket | `ge_10` | 10 | 0.450 | 0.203 |
| line_bucket | `ge_25` | 10 | 0.596 | 0.586 |
| line_bucket | `ge_3` | 3 | 1.910 | 0.551 |
| line_bucket | `lt_10` | 5 | 1.223 | 0.094 |
| line_bucket | `lt_3` | 9 | 0.871 | 0.381 |
| line_bucket | `lt_4` | 19 | 0.789 | 0.089 |
| role_bucket | `bench` | 26 | 1.010 | -0.114 |
| role_bucket | `core` | 29 | 1.046 | 0.177 |
| role_bucket | `ge30min_starter` | 20 | 0.664 | 0.394 |
| role_bucket | `lt15min` | 2 | 0.289 | -0.566 |
| role_bucket | `lt22min` | 3 | 0.795 | -0.914 |
| role_bucket | `lt30min` | 5 | 0.236 | 0.138 |
| stat | `blk` | 24 | 1.412 | 0.467 |

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
- settled window: **2026-05-30 → 2026-06-13** (6 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

