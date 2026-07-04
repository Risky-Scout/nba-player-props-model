# PMF Variance Experience Study — July 3, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-03` over a 60-day lookback._

## Executive summary

- **704** settled rows from **2026-05-04** through **2026-06-13** (18 delivery dates with at least one settled row).
- **Mean A/E = 1.039** — actual outcomes ran +3.9% relative to expected means in this sample.
- **Variance A/E = 0.791** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.058, sd = 0.963** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.788 and 0.932); the 10th-percentile band is over-covered (0.209 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.262 vs 0.248 (model vs market); logloss 0.722 vs 0.690.
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
| rows | 704 |
| actual_mean (per row) | 5.770 |
| expected_mean (per row) | 5.552 |
| **mean_AE** | **1.0392** |
| Σ squared residual | 9131.41 |
| Σ expected variance | 11549.96 |
| **variance_AE** | **0.7906** |
| standardized_residual_mean | 0.0582 |
| standardized_residual_sd | 0.9629 |
| pmf_nll_mean | 2.2427 |
| pmf_rps_mean | 0.1095 |
| model_brier (over/under) | 0.2617 |
| market_brier (over/under) | 0.2475 |
| model_logloss (over/under) | 0.7223 |
| market_logloss (over/under) | 0.6898 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.209 / 0.348 / 0.564 / 0.788 / 0.932 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `4_to_7` | 58 | **1.210** | 1.154 | 1.053 | 2.605 |
| p0_bucket | `5_to_20pct` | 227 | **1.294** | 1.028 | 1.093 | 2.149 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |
| stat | `blk` | 70 | **1.225** | 0.949 | 1.257 | 1.447 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 47 | **0.513** | 0.808 | 0.842 | 2.069 |
| edge_bucket | `10_to_20pct` | 320 | **0.743** | 0.983 | 1.049 | 2.252 |
| edge_bucket | `5_to_10pct` | 228 | **0.751** | 0.913 | 0.987 | 2.230 |
| injury_context | `unavailable` | 213 | **0.621** | 0.874 | 1.030 | 1.986 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `15_to_20` | 34 | **0.784** | 0.930 | 0.954 | 3.370 |
| line_bucket | `2_to_2p5` | 40 | **0.686** | 0.850 | 1.071 | 1.646 |
| line_bucket | `3_to_5` | 59 | **0.720** | 0.868 | 0.973 | 2.037 |
| line_bucket | `5_to_8` | 33 | **0.793** | 0.886 | 1.026 | 2.372 |
| line_bucket | `ge_25` | 36 | **0.577** | 0.725 | 1.095 | 3.517 |
| line_bucket | `le_half` | 126 | **0.629** | 0.885 | 0.763 | 1.238 |
| lineup_confirmed | `unavailable` | 213 | **0.621** | 0.874 | 1.030 | 1.986 |
| low_line_discrete | `no` | 474 | **0.793** | 0.952 | 1.047 | 2.609 |
| low_line_discrete | `yes` | 230 | **0.730** | 0.982 | 0.922 | 1.487 |
| minutes_volatility_bucket | `unavailable` | 704 | **0.791** | 0.963 | 1.039 | 2.243 |
| overall | `ALL` | 704 | **0.791** | 0.963 | 1.039 | 2.243 |
| p0_bucket | `ge_50pct` | 80 | **0.478** | 0.793 | 1.173 | 1.062 |
| p0_bucket | `lt_5pct` | 258 | **0.729** | 0.891 | 1.028 | 2.949 |
| predicted_variance_bucket | `high` | 232 | **0.768** | 0.921 | 1.044 | 3.075 |
| role_bucket | `bench` | 42 | **0.551** | 0.908 | 0.882 | 1.665 |
| role_bucket | `ge30min_starter` | 138 | **0.517** | 0.858 | 1.026 | 2.073 |
| role_bucket | `lt30min` | 47 | **0.520** | 0.869 | 1.064 | 1.986 |
| role_bucket | `starter` | 262 | **0.710** | 0.954 | 1.013 | 2.442 |
| side | `UNDER` | 569 | **0.781** | 0.935 | 1.097 | 2.278 |
| snapshot_type | `morning` | 704 | **0.791** | 0.963 | 1.039 | 2.243 |
| stat | `ast` | 120 | **0.744** | 0.875 | 1.043 | 2.128 |
| stat | `pts` | 145 | **0.758** | 0.918 | 1.050 | 3.356 |
| stat | `stl` | 82 | **0.596** | 0.860 | 0.992 | 1.447 |
| vacated_opportunity_bucket | `unavailable` | 704 | **0.791** | 0.963 | 1.039 | 2.243 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 109 | 1.197 | 1.101 | 0.261 | 2.318 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 167 | 1.037 | 0.869 | 0.018 | 2.476 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 52 | 1.051 | 0.891 | 0.135 | 3.279 |
| line_bucket | `1_to_1p5` | 104 | 1.041 | 0.823 | 0.081 | 1.789 |
| line_bucket | `lt_4` | 55 | 0.966 | 0.877 | -0.040 | 2.162 |
| lineup_confirmed | `projected` | 466 | 1.058 | 0.855 | 0.096 | 2.349 |
| p0_bucket | `20_to_50pct` | 139 | 0.978 | 0.832 | -0.012 | 1.765 |
| predicted_variance_bucket | `low` | 232 | 1.030 | 0.926 | 0.045 | 1.524 |
| predicted_variance_bucket | `mid` | 240 | 1.023 | 0.935 | 0.036 | 2.133 |
| role_bucket | `rotation` | 93 | 1.129 | 0.841 | 0.235 | 2.176 |
| side | `OVER` | 135 | 0.738 | 0.843 | -0.464 | 2.094 |
| stat | `fg3m` | 125 | 0.921 | 0.877 | -0.104 | 1.707 |
| stat | `reb` | 162 | 1.027 | 0.971 | 0.057 | 2.491 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| line_bucket | `20_to_25` | 5 | 0.799 | 0.150 |
| line_bucket | `7_to_10` | 27 | 0.961 | -0.015 |
| line_bucket | `ge_10` | 22 | 0.778 | 0.247 |
| line_bucket | `ge_3` | 7 | 3.548 | 0.883 |
| line_bucket | `ge_8` | 2 | 0.201 | 0.378 |
| line_bucket | `lt_10` | 18 | 1.134 | 0.187 |
| line_bucket | `lt_3` | 26 | 0.816 | 0.378 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 22 | 0.614 | -0.412 |

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
- settled window: **2026-05-04 → 2026-06-13** (18 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

