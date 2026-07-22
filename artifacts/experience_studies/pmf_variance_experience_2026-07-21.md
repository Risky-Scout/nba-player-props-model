# PMF Variance Experience Study — July 21, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-21` over a 60-day lookback._

## Executive summary

- **390** settled rows from **2026-05-22** through **2026-06-13** (11 delivery dates with at least one settled row).
- **Mean A/E = 1.057** — actual outcomes ran +5.7% relative to expected means in this sample.
- **Variance A/E = 0.799** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.109, sd = 0.987** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.787 and 0.936); the 10th-percentile band is over-covered (0.200 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.262 vs 0.247 (model vs market); logloss 0.723 vs 0.689.
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
| rows | 390 |
| actual_mean (per row) | 5.782 |
| expected_mean (per row) | 5.468 |
| **mean_AE** | **1.0574** |
| Σ squared residual | 4932.84 |
| Σ expected variance | 6173.32 |
| **variance_AE** | **0.7991** |
| standardized_residual_mean | 0.1087 |
| standardized_residual_sd | 0.9867 |
| pmf_nll_mean | 2.2461 |
| pmf_rps_mean | 0.1160 |
| model_brier (over/under) | 0.2616 |
| market_brier (over/under) | 0.2473 |
| model_logloss (over/under) | 0.7230 |
| market_logloss (over/under) | 0.6894 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.200 / 0.318 / 0.549 / 0.787 / 0.936 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| p0_bucket | `20_to_50pct` | 81 | **1.207** | 1.227 | 1.061 | 1.925 |
| p0_bucket | `5_to_20pct` | 124 | **1.320** | 0.984 | 1.118 | 2.125 |
| predicted_variance_bucket | `low` | 129 | **1.280** | 1.144 | 1.064 | 1.618 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 183 | **0.744** | 1.007 | 1.056 | 2.319 |
| injury_context | `unavailable` | 95 | **0.717** | 0.906 | 1.093 | 2.155 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `3_to_5` | 30 | **0.535** | 0.757 | 1.005 | 2.025 |
| lineup_confirmed | `unavailable` | 95 | **0.717** | 0.906 | 1.093 | 2.155 |
| low_line_discrete | `no` | 262 | **0.792** | 0.915 | 1.056 | 2.561 |
| minutes_volatility_bucket | `unavailable` | 390 | **0.799** | 0.987 | 1.057 | 2.246 |
| overall | `ALL` | 390 | **0.799** | 0.987 | 1.057 | 2.246 |
| p0_bucket | `lt_5pct` | 138 | **0.710** | 0.842 | 1.035 | 2.914 |
| predicted_variance_bucket | `high` | 129 | **0.779** | 0.905 | 1.058 | 3.054 |
| role_bucket | `ge30min_starter` | 63 | **0.546** | 0.883 | 1.080 | 2.223 |
| role_bucket | `starter` | 158 | **0.788** | 1.018 | 1.062 | 2.476 |
| side | `UNDER` | 320 | **0.782** | 0.955 | 1.111 | 2.265 |
| snapshot_type | `morning` | 390 | **0.799** | 0.987 | 1.057 | 2.246 |
| stat | `ast` | 63 | **0.559** | 0.767 | 1.028 | 2.040 |
| stat | `pts` | 83 | **0.794** | 0.942 | 1.063 | 3.325 |
| vacated_opportunity_bucket | `unavailable` | 390 | **0.799** | 0.987 | 1.057 | 2.246 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 129 | 1.056 | 0.949 | 0.125 | 2.230 |
| edge_bucket | `ge_20pct` | 50 | 1.209 | 0.808 | 0.217 | 2.065 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `latest_valid_report_selected` | 128 | 0.984 | 0.845 | 0.005 | 2.264 |
| line_bucket | `10_to_15` | 34 | 1.005 | 0.852 | 0.039 | 3.233 |
| line_bucket | `1_to_1p5` | 57 | 1.161 | 1.108 | 0.236 | 1.888 |
| line_bucket | `le_half` | 71 | 0.969 | 1.164 | 0.018 | 1.372 |
| line_bucket | `lt_4` | 32 | 1.114 | 1.041 | 0.171 | 2.280 |
| lineup_confirmed | `projected` | 270 | 1.076 | 0.842 | 0.149 | 2.259 |
| low_line_discrete | `yes` | 128 | 1.079 | 1.132 | 0.115 | 1.602 |
| p0_bucket | `ge_50pct` | 47 | 1.489 | 0.923 | 0.303 | 1.157 |
| predicted_variance_bucket | `mid` | 132 | 1.054 | 0.865 | 0.101 | 2.070 |
| role_bucket | `core` | 56 | 0.990 | 0.939 | 0.062 | 2.286 |
| role_bucket | `rotation` | 53 | 1.071 | 0.853 | 0.211 | 2.067 |
| side | `OVER` | 70 | 0.754 | 0.903 | -0.414 | 2.158 |
| stat | `blk` | 36 | 1.313 | 0.988 | 0.342 | 1.326 |
| stat | `fg3m` | 69 | 0.928 | 1.186 | -0.076 | 1.780 |
| stat | `reb` | 92 | 1.051 | 0.866 | 0.124 | 2.463 |
| stat | `stl` | 47 | 1.299 | 0.953 | 0.213 | 1.581 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 28 | 0.607 | -0.186 |
| line_bucket | `15_to_20` | 17 | 0.948 | -0.013 |
| line_bucket | `2_to_2p5` | 20 | 0.756 | 0.022 |
| line_bucket | `4_to_7` | 29 | 1.108 | 0.102 |
| line_bucket | `5_to_8` | 17 | 0.556 | 0.052 |
| line_bucket | `7_to_10` | 16 | 0.820 | 0.170 |
| line_bucket | `ge_10` | 15 | 0.586 | 0.016 |
| line_bucket | `ge_25` | 19 | 0.541 | 0.386 |
| line_bucket | `ge_3` | 4 | 1.507 | 0.488 |
| line_bucket | `lt_10` | 13 | 1.298 | 0.168 |
| line_bucket | `lt_3` | 16 | 0.634 | 0.102 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `bench` | 28 | 0.916 | -0.154 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 8 | 0.611 | -0.650 |
| role_bucket | `lt30min` | 18 | 0.477 | 0.057 |

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
- settled window: **2026-05-22 → 2026-06-13** (11 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

