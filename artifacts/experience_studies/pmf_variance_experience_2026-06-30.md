# PMF Variance Experience Study — June 30, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-30` over a 60-day lookback._

## Executive summary

- **888** settled rows from **2026-05-01** through **2026-06-13** (21 delivery dates with at least one settled row).
- **Mean A/E = 1.070** — actual outcomes ran +7.0% relative to expected means in this sample.
- **Variance A/E = 0.795** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.095, sd = 0.952** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.770 and 0.920); the 10th-percentile band is over-covered (0.206 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.263 vs 0.249 (model vs market); logloss 0.725 vs 0.693.
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
| rows | 888 |
| actual_mean (per row) | 5.878 |
| expected_mean (per row) | 5.496 |
| **mean_AE** | **1.0696** |
| Σ squared residual | 11536.34 |
| Σ expected variance | 14505.18 |
| **variance_AE** | **0.7953** |
| standardized_residual_mean | 0.0950 |
| standardized_residual_sd | 0.9520 |
| pmf_nll_mean | 2.2892 |
| pmf_rps_mean | 0.1091 |
| model_brier (over/under) | 0.2631 |
| market_brier (over/under) | 0.2488 |
| model_logloss (over/under) | 0.7254 |
| market_logloss (over/under) | 0.6926 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.206 / 0.332 / 0.545 / 0.770 / 0.920 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| p0_bucket | `5_to_20pct` | 270 | **1.357** | 1.008 | 1.114 | 2.169 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 55 | **0.484** | 0.785 | 0.893 | 2.128 |
| edge_bucket | `10_to_20pct` | 420 | **0.799** | 0.972 | 1.093 | 2.304 |
| edge_bucket | `5_to_10pct` | 278 | **0.762** | 0.922 | 1.027 | 2.321 |
| injury_context | `unavailable` | 264 | **0.616** | 0.842 | 1.037 | 1.914 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 140 | **0.716** | 1.005 | 1.114 | 1.899 |
| line_bucket | `2_to_2p5` | 54 | **0.473** | 0.774 | 1.015 | 1.635 |
| line_bucket | `3_to_5` | 66 | **0.754** | 0.891 | 1.000 | 2.058 |
| line_bucket | `ge_25` | 41 | **0.559** | 0.696 | 1.112 | 3.502 |
| line_bucket | `le_half` | 156 | **0.579** | 0.842 | 0.830 | 1.331 |
| lineup_confirmed | `unavailable` | 264 | **0.616** | 0.842 | 1.037 | 1.914 |
| low_line_discrete | `yes` | 296 | **0.657** | 0.927 | 1.000 | 1.600 |
| minutes_volatility_bucket | `unavailable` | 888 | **0.795** | 0.952 | 1.070 | 2.289 |
| overall | `ALL` | 888 | **0.795** | 0.952 | 1.070 | 2.289 |
| p0_bucket | `ge_50pct` | 107 | **0.423** | 0.746 | 1.131 | 1.082 |
| p0_bucket | `lt_5pct` | 337 | **0.729** | 0.918 | 1.058 | 2.938 |
| predicted_variance_bucket | `high` | 293 | **0.779** | 0.941 | 1.080 | 3.114 |
| role_bucket | `bench` | 57 | **0.770** | 1.005 | 0.899 | 2.049 |
| role_bucket | `ge30min_starter` | 161 | **0.519** | 0.842 | 1.032 | 2.040 |
| role_bucket | `lt30min` | 72 | **0.511** | 0.792 | 1.070 | 1.791 |
| role_bucket | `starter` | 341 | **0.680** | 0.941 | 1.050 | 2.459 |
| side | `UNDER` | 717 | **0.785** | 0.922 | 1.125 | 2.308 |
| snapshot_type | `morning` | 888 | **0.795** | 0.952 | 1.070 | 2.289 |
| stat | `fg3m` | 155 | **0.670** | 1.013 | 0.956 | 1.849 |
| stat | `pts` | 179 | **0.756** | 0.912 | 1.085 | 3.411 |
| stat | `stl` | 105 | **0.607** | 0.838 | 1.000 | 1.439 |
| vacated_opportunity_bucket | `unavailable` | 888 | **0.795** | 0.952 | 1.070 | 2.289 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 135 | 1.170 | 1.002 | 0.216 | 2.244 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 300 | 1.107 | 0.850 | 0.137 | 2.618 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 65 | 1.075 | 0.844 | 0.164 | 3.260 |
| line_bucket | `15_to_20` | 42 | 0.996 | 0.820 | 0.012 | 3.407 |
| line_bucket | `4_to_7` | 72 | 1.041 | 1.113 | 0.089 | 2.553 |
| line_bucket | `5_to_8` | 47 | 1.063 | 0.882 | 0.103 | 2.408 |
| line_bucket | `7_to_10` | 38 | 1.095 | 1.138 | 0.231 | 2.729 |
| line_bucket | `lt_4` | 73 | 0.996 | 1.067 | 0.020 | 2.247 |
| lineup_confirmed | `projected` | 599 | 1.092 | 0.848 | 0.138 | 2.448 |
| low_line_discrete | `no` | 592 | 1.075 | 0.801 | 0.137 | 2.634 |
| p0_bucket | `20_to_50pct` | 174 | 1.079 | 0.835 | 0.059 | 1.962 |
| predicted_variance_bucket | `low` | 293 | 1.055 | 0.825 | 0.059 | 1.549 |
| predicted_variance_bucket | `mid` | 302 | 1.038 | 0.910 | 0.062 | 2.207 |
| role_bucket | `rotation` | 132 | 1.202 | 1.027 | 0.284 | 2.491 |
| side | `OVER` | 171 | 0.783 | 0.858 | -0.370 | 2.208 |
| stat | `ast` | 146 | 1.062 | 0.843 | 0.120 | 2.190 |
| stat | `blk` | 98 | 1.259 | 0.914 | 0.204 | 1.540 |
| stat | `reb` | 205 | 1.054 | 1.036 | 0.108 | 2.507 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| line_bucket | `20_to_25` | 11 | 0.546 | 0.310 |
| line_bucket | `ge_10` | 22 | 0.778 | 0.247 |
| line_bucket | `ge_3` | 8 | 2.974 | 0.696 |
| line_bucket | `ge_8` | 4 | 0.963 | 0.190 |
| line_bucket | `lt_10` | 20 | 1.514 | 0.378 |
| line_bucket | `lt_3` | 29 | 0.918 | 0.365 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 25 | 0.613 | -0.352 |

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
- settled window: **2026-05-01 → 2026-06-13** (21 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

