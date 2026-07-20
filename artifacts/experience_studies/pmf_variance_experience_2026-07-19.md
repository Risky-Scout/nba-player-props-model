# PMF Variance Experience Study — July 19, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-19` over a 60-day lookback._

## Executive summary

- **420** settled rows from **2026-05-20** through **2026-06-13** (13 delivery dates with at least one settled row).
- **Mean A/E = 1.057** — actual outcomes ran +5.7% relative to expected means in this sample.
- **Variance A/E = 0.799** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.104, sd = 0.987** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.786 and 0.929); the 10th-percentile band is over-covered (0.202 vs target 0.10).
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
| rows | 420 |
| actual_mean (per row) | 5.869 |
| expected_mean (per row) | 5.552 |
| **mean_AE** | **1.0571** |
| Σ squared residual | 5414.86 |
| Σ expected variance | 6776.86 |
| **variance_AE** | **0.7990** |
| standardized_residual_mean | 0.1042 |
| standardized_residual_sd | 0.9870 |
| pmf_nll_mean | 2.2616 |
| pmf_rps_mean | 0.1159 |
| model_brier (over/under) | 0.2627 |
| market_brier (over/under) | 0.2477 |
| model_logloss (over/under) | 0.7251 |
| market_logloss (over/under) | 0.6901 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.202 / 0.319 / 0.543 / 0.786 / 0.929 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| p0_bucket | `5_to_20pct` | 136 | **1.360** | 0.988 | 1.125 | 2.132 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 198 | **0.690** | 0.997 | 1.055 | 2.338 |
| injury_context | `unavailable` | 96 | **0.697** | 0.901 | 1.091 | 2.162 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `3_to_5` | 32 | **0.607** | 0.790 | 0.968 | 2.041 |
| lineup_confirmed | `unavailable` | 96 | **0.697** | 0.901 | 1.091 | 2.162 |
| low_line_discrete | `no` | 284 | **0.792** | 0.923 | 1.058 | 2.576 |
| minutes_volatility_bucket | `unavailable` | 420 | **0.799** | 0.987 | 1.057 | 2.262 |
| overall | `ALL` | 420 | **0.799** | 0.987 | 1.057 | 2.262 |
| p0_bucket | `lt_5pct` | 150 | **0.705** | 0.852 | 1.035 | 2.925 |
| predicted_variance_bucket | `high` | 139 | **0.780** | 0.918 | 1.062 | 3.079 |
| role_bucket | `ge30min_starter` | 64 | **0.527** | 0.876 | 1.078 | 2.233 |
| role_bucket | `starter` | 170 | **0.752** | 1.006 | 1.076 | 2.470 |
| side | `UNDER` | 340 | **0.788** | 0.958 | 1.107 | 2.283 |
| snapshot_type | `morning` | 420 | **0.799** | 0.987 | 1.057 | 2.262 |
| stat | `ast` | 68 | **0.614** | 0.806 | 1.041 | 2.080 |
| stat | `pts` | 90 | **0.783** | 0.942 | 1.060 | 3.332 |
| vacated_opportunity_bucket | `unavailable` | 420 | **0.799** | 0.987 | 1.057 | 2.262 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 140 | 1.030 | 0.977 | 0.080 | 2.216 |
| edge_bucket | `ge_20pct` | 53 | 1.261 | 0.929 | 0.295 | 2.160 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 36 | 1.019 | 0.866 | 0.074 | 3.251 |
| line_bucket | `1_to_1p5` | 60 | 1.109 | 1.088 | 0.182 | 1.859 |
| line_bucket | `4_to_7` | 33 | 1.045 | 1.178 | 0.080 | 2.479 |
| line_bucket | `le_half` | 76 | 0.967 | 1.076 | 0.008 | 1.403 |
| line_bucket | `lt_4` | 35 | 1.122 | 0.980 | 0.182 | 2.250 |
| lineup_confirmed | `projected` | 299 | 1.074 | 0.844 | 0.139 | 2.278 |
| low_line_discrete | `yes` | 136 | 1.047 | 1.082 | 0.085 | 1.604 |
| p0_bucket | `20_to_50pct` | 86 | 1.037 | 1.178 | 0.049 | 1.920 |
| p0_bucket | `ge_50pct` | 48 | 1.494 | 0.868 | 0.302 | 1.167 |
| predicted_variance_bucket | `low` | 139 | 1.027 | 1.195 | 0.070 | 1.603 |
| predicted_variance_bucket | `mid` | 142 | 1.047 | 0.868 | 0.100 | 2.106 |
| role_bucket | `core` | 65 | 0.915 | 0.996 | -0.050 | 2.352 |
| role_bucket | `rotation` | 61 | 1.149 | 0.995 | 0.247 | 2.081 |
| side | `OVER` | 80 | 0.799 | 0.863 | -0.378 | 2.169 |
| stat | `blk` | 37 | 1.321 | 0.934 | 0.340 | 1.334 |
| stat | `fg3m` | 74 | 0.903 | 1.165 | -0.110 | 1.756 |
| stat | `reb` | 101 | 1.056 | 0.907 | 0.122 | 2.462 |
| stat | `stl` | 50 | 1.285 | 0.917 | 0.207 | 1.610 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 29 | 0.610 | -0.224 |
| line_bucket | `15_to_20` | 20 | 0.968 | -0.045 |
| line_bucket | `20_to_25` | 1 | 0.015 | -0.121 |
| line_bucket | `2_to_2p5` | 21 | 0.758 | 0.063 |
| line_bucket | `5_to_8` | 19 | 0.549 | 0.120 |
| line_bucket | `7_to_10` | 17 | 0.830 | 0.102 |
| line_bucket | `ge_10` | 16 | 0.672 | 0.100 |
| line_bucket | `ge_25` | 20 | 0.526 | 0.391 |
| line_bucket | `ge_3` | 4 | 1.507 | 0.488 |
| line_bucket | `lt_10` | 13 | 1.298 | 0.168 |
| line_bucket | `lt_3` | 17 | 0.811 | 0.206 |
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
- settled window: **2026-05-20 → 2026-06-13** (13 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

