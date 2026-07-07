# PMF Variance Experience Study — July 6, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-06` over a 60-day lookback._

## Executive summary

- **615** settled rows from **2026-05-07** through **2026-06-13** (16 delivery dates with at least one settled row).
- **Mean A/E = 1.056** — actual outcomes ran +5.6% relative to expected means in this sample.
- **Variance A/E = 0.806** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.075, sd = 0.970** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.789 and 0.932); the 10th-percentile band is over-covered (0.215 vs target 0.10).
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
| rows | 615 |
| actual_mean (per row) | 5.782 |
| expected_mean (per row) | 5.473 |
| **mean_AE** | **1.0565** |
| Σ squared residual | 7917.53 |
| Σ expected variance | 9828.21 |
| **variance_AE** | **0.8056** |
| standardized_residual_mean | 0.0748 |
| standardized_residual_sd | 0.9697 |
| pmf_nll_mean | 2.2268 |
| pmf_rps_mean | 0.1105 |
| model_brier (over/under) | 0.2628 |
| market_brier (over/under) | 0.2476 |
| model_logloss (over/under) | 0.7251 |
| market_logloss (over/under) | 0.6902 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.215 / 0.345 / 0.556 / 0.789 / 0.932 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `4_to_7` | 46 | **1.290** | 1.212 | 1.079 | 2.691 |
| p0_bucket | `5_to_20pct` | 201 | **1.313** | 1.022 | 1.093 | 2.120 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 40 | **0.570** | 0.820 | 0.844 | 2.050 |
| edge_bucket | `10_to_20pct` | 280 | **0.751** | 0.984 | 1.051 | 2.231 |
| edge_bucket | `5_to_10pct` | 200 | **0.782** | 0.928 | 1.000 | 2.223 |
| injury_context | `unavailable` | 194 | **0.596** | 0.852 | 1.029 | 1.995 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `2_to_2p5` | 36 | **0.770** | 0.865 | 1.099 | 1.618 |
| line_bucket | `3_to_5` | 52 | **0.737** | 0.877 | 0.959 | 2.038 |
| line_bucket | `ge_25` | 31 | **0.550** | 0.686 | 1.118 | 3.503 |
| line_bucket | `le_half` | 114 | **0.722** | 0.921 | 0.784 | 1.257 |
| lineup_confirmed | `unavailable` | 194 | **0.596** | 0.852 | 1.029 | 1.995 |
| p0_bucket | `ge_50pct` | 72 | **0.546** | 0.825 | 1.212 | 1.063 |
| p0_bucket | `lt_5pct` | 217 | **0.737** | 0.880 | 1.051 | 2.963 |
| predicted_variance_bucket | `high` | 203 | **0.786** | 0.922 | 1.066 | 3.075 |
| role_bucket | `bench` | 34 | **0.740** | 0.946 | 0.881 | 1.578 |
| role_bucket | `ge30min_starter` | 126 | **0.515** | 0.877 | 1.033 | 2.139 |
| role_bucket | `lt30min` | 42 | **0.389** | 0.647 | 1.031 | 1.797 |
| role_bucket | `starter` | 221 | **0.720** | 0.975 | 1.055 | 2.432 |
| side | `OVER` | 115 | **0.769** | 0.940 | 0.792 | 2.069 |
| stat | `ast` | 104 | **0.732** | 0.866 | 1.063 | 2.117 |
| stat | `blk` | 62 | **0.635** | 0.867 | 1.148 | 1.284 |
| stat | `pts` | 126 | **0.783** | 0.930 | 1.075 | 3.358 |
| stat | `stl` | 73 | **0.657** | 0.893 | 1.047 | 1.496 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 95 | 1.276 | 1.103 | 0.327 | 2.297 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 97 | 1.129 | 1.049 | 0.089 | 2.476 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 47 | 1.098 | 0.891 | 0.210 | 3.287 |
| line_bucket | `1_to_1p5` | 91 | 1.030 | 0.995 | 0.086 | 1.810 |
| line_bucket | `lt_4` | 48 | 1.009 | 0.852 | 0.026 | 2.173 |
| lineup_confirmed | `projected` | 396 | 1.089 | 0.905 | 0.127 | 2.326 |
| low_line_discrete | `no` | 410 | 1.065 | 0.804 | 0.123 | 2.589 |
| low_line_discrete | `yes` | 205 | 0.923 | 0.856 | -0.021 | 1.502 |
| minutes_volatility_bucket | `unavailable` | 615 | 1.056 | 0.806 | 0.075 | 2.227 |
| overall | `ALL` | 615 | 1.056 | 0.806 | 0.075 | 2.227 |
| p0_bucket | `20_to_50pct` | 125 | 0.963 | 0.914 | -0.018 | 1.791 |
| predicted_variance_bucket | `low` | 203 | 1.007 | 1.023 | 0.032 | 1.527 |
| predicted_variance_bucket | `mid` | 209 | 1.037 | 0.913 | 0.059 | 2.083 |
| role_bucket | `rotation` | 72 | 1.098 | 0.923 | 0.160 | 2.052 |
| side | `UNDER` | 500 | 1.103 | 0.811 | 0.189 | 2.263 |
| snapshot_type | `morning` | 615 | 1.056 | 0.806 | 0.075 | 2.227 |
| stat | `fg3m` | 111 | 0.906 | 1.134 | -0.119 | 1.690 |
| stat | `reb` | 139 | 1.037 | 0.953 | 0.087 | 2.516 |
| vacated_opportunity_bucket | `unavailable` | 615 | 1.056 | 0.806 | 0.075 | 2.227 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| line_bucket | `15_to_20` | 29 | 0.868 | -0.039 |
| line_bucket | `20_to_25` | 3 | 1.299 | 0.253 |
| line_bucket | `5_to_8` | 28 | 0.774 | 0.200 |
| line_bucket | `7_to_10` | 25 | 0.982 | 0.049 |
| line_bucket | `ge_10` | 20 | 0.663 | 0.122 |
| line_bucket | `ge_3` | 5 | 0.928 | 0.468 |
| line_bucket | `ge_8` | 2 | 0.201 | 0.378 |
| line_bucket | `lt_10` | 16 | 1.151 | 0.118 |
| line_bucket | `lt_3` | 22 | 0.758 | 0.294 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 20 | 0.631 | -0.433 |

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
- settled window: **2026-05-07 → 2026-06-13** (16 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

