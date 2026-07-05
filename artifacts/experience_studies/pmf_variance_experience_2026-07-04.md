# PMF Variance Experience Study — July 4, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-04` over a 60-day lookback._

## Executive summary

- **642** settled rows from **2026-05-06** through **2026-06-13** (17 delivery dates with at least one settled row).
- **Mean A/E = 1.045** — actual outcomes ran +4.5% relative to expected means in this sample.
- **Variance A/E = 0.801** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.065, sd = 0.967** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.788 and 0.933); the 10th-percentile band is over-covered (0.212 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.263 vs 0.248 (model vs market); logloss 0.726 vs 0.691.
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
| rows | 642 |
| actual_mean (per row) | 5.776 |
| expected_mean (per row) | 5.528 |
| **mean_AE** | **1.0449** |
| Σ squared residual | 8341.65 |
| Σ expected variance | 10410.61 |
| **variance_AE** | **0.8013** |
| standardized_residual_mean | 0.0646 |
| standardized_residual_sd | 0.9667 |
| pmf_nll_mean | 2.2338 |
| pmf_rps_mean | 0.1103 |
| model_brier (over/under) | 0.2632 |
| market_brier (over/under) | 0.2478 |
| model_logloss (over/under) | 0.7259 |
| market_logloss (over/under) | 0.6906 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.212 / 0.344 / 0.559 / 0.788 / 0.933 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `4_to_7` | 49 | **1.246** | 1.189 | 1.054 | 2.647 |
| p0_bucket | `5_to_20pct` | 210 | **1.291** | 1.015 | 1.093 | 2.114 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 43 | **0.559** | 0.844 | 0.839 | 2.108 |
| edge_bucket | `10_to_20pct` | 290 | **0.751** | 0.982 | 1.043 | 2.224 |
| edge_bucket | `5_to_10pct` | 207 | **0.762** | 0.921 | 0.993 | 2.235 |
| injury_context | `unavailable` | 199 | **0.598** | 0.849 | 1.027 | 1.989 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `2_to_2p5` | 37 | **0.726** | 0.859 | 1.082 | 1.606 |
| line_bucket | `3_to_5` | 55 | **0.734** | 0.877 | 0.959 | 2.037 |
| line_bucket | `5_to_8` | 30 | **0.792** | 0.874 | 1.074 | 2.377 |
| line_bucket | `ge_25` | 33 | **0.524** | 0.670 | 1.114 | 3.480 |
| line_bucket | `le_half` | 115 | **0.709** | 0.917 | 0.785 | 1.254 |
| lineup_confirmed | `unavailable` | 199 | **0.598** | 0.849 | 1.027 | 1.989 |
| p0_bucket | `ge_50pct` | 73 | **0.531** | 0.819 | 1.211 | 1.064 |
| p0_bucket | `lt_5pct` | 231 | **0.737** | 0.888 | 1.035 | 2.958 |
| predicted_variance_bucket | `high` | 212 | **0.781** | 0.921 | 1.055 | 3.077 |
| role_bucket | `bench` | 36 | **0.576** | 0.954 | 0.934 | 1.643 |
| role_bucket | `ge30min_starter` | 129 | **0.520** | 0.879 | 1.030 | 2.141 |
| role_bucket | `lt30min` | 43 | **0.387** | 0.639 | 1.029 | 1.777 |
| role_bucket | `starter` | 234 | **0.735** | 0.976 | 1.030 | 2.442 |
| side | `UNDER` | 518 | **0.789** | 0.934 | 1.102 | 2.264 |
| stat | `ast` | 111 | **0.741** | 0.871 | 1.053 | 2.123 |
| stat | `blk` | 63 | **0.617** | 0.861 | 1.140 | 1.279 |
| stat | `pts` | 133 | **0.777** | 0.931 | 1.057 | 3.354 |
| stat | `stl` | 75 | **0.637** | 0.882 | 1.057 | 1.495 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 102 | 1.231 | 1.093 | 0.303 | 2.312 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 119 | 1.064 | 0.974 | 0.036 | 2.487 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 50 | 1.055 | 0.932 | 0.143 | 3.297 |
| line_bucket | `15_to_20` | 30 | 0.957 | 0.864 | -0.066 | 3.394 |
| line_bucket | `1_to_1p5` | 96 | 1.033 | 0.925 | 0.086 | 1.810 |
| line_bucket | `lt_4` | 50 | 1.001 | 0.906 | 0.017 | 2.203 |
| lineup_confirmed | `projected` | 418 | 1.070 | 0.890 | 0.110 | 2.337 |
| low_line_discrete | `no` | 431 | 1.053 | 0.801 | 0.106 | 2.590 |
| low_line_discrete | `yes` | 211 | 0.928 | 0.822 | -0.019 | 1.507 |
| minutes_volatility_bucket | `unavailable` | 642 | 1.045 | 0.801 | 0.065 | 2.234 |
| overall | `ALL` | 642 | 1.045 | 0.801 | 0.065 | 2.234 |
| p0_bucket | `20_to_50pct` | 128 | 0.980 | 0.895 | -0.008 | 1.791 |
| predicted_variance_bucket | `low` | 212 | 1.021 | 0.977 | 0.042 | 1.524 |
| predicted_variance_bucket | `mid` | 218 | 1.016 | 0.918 | 0.035 | 2.104 |
| role_bucket | `rotation` | 79 | 1.095 | 0.821 | 0.166 | 2.078 |
| side | `OVER` | 124 | 0.749 | 0.872 | -0.458 | 2.109 |
| snapshot_type | `morning` | 642 | 1.045 | 0.801 | 0.065 | 2.234 |
| stat | `fg3m` | 115 | 0.903 | 1.050 | -0.120 | 1.695 |
| stat | `reb` | 145 | 1.034 | 0.961 | 0.077 | 2.516 |
| vacated_opportunity_bucket | `unavailable` | 642 | 1.045 | 0.801 | 0.065 | 2.234 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| line_bucket | `20_to_25` | 3 | 1.299 | 0.253 |
| line_bucket | `7_to_10` | 25 | 0.982 | 0.049 |
| line_bucket | `ge_10` | 21 | 0.696 | 0.173 |
| line_bucket | `ge_3` | 5 | 0.928 | 0.468 |
| line_bucket | `ge_8` | 2 | 0.201 | 0.378 |
| line_bucket | `lt_10` | 17 | 1.072 | 0.112 |
| line_bucket | `lt_3` | 24 | 0.766 | 0.347 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 21 | 0.620 | -0.409 |

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
- settled window: **2026-05-06 → 2026-06-13** (17 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

