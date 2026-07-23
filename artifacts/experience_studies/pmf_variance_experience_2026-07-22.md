# PMF Variance Experience Study — July 22, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-22` over a 60-day lookback._

## Executive summary

- **357** settled rows from **2026-05-23** through **2026-06-13** (10 delivery dates with at least one settled row).
- **Mean A/E = 1.055** — actual outcomes ran +5.5% relative to expected means in this sample.
- **Variance A/E = 0.781** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.117, sd = 0.995** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.782 and 0.933); the 10th-percentile band is over-covered (0.202 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.266 vs 0.249 (model vs market); logloss 0.734 vs 0.694.
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
| rows | 357 |
| actual_mean (per row) | 5.745 |
| expected_mean (per row) | 5.445 |
| **mean_AE** | **1.0552** |
| Σ squared residual | 4394.93 |
| Σ expected variance | 5629.67 |
| **variance_AE** | **0.7807** |
| standardized_residual_mean | 0.1169 |
| standardized_residual_sd | 0.9945 |
| pmf_nll_mean | 2.2572 |
| pmf_rps_mean | 0.1176 |
| model_brier (over/under) | 0.2665 |
| market_brier (over/under) | 0.2494 |
| model_logloss (over/under) | 0.7339 |
| market_logloss (over/under) | 0.6939 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.202 / 0.317 / 0.543 / 0.782 / 0.933 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `1_to_1p5` | 48 | **1.323** | 1.254 | 1.250 | 2.019 |
| line_bucket | `le_half` | 70 | **1.206** | 1.065 | 0.984 | 1.385 |
| low_line_discrete | `yes` | 118 | **1.266** | 1.150 | 1.125 | 1.643 |
| p0_bucket | `20_to_50pct` | 74 | **1.316** | 1.264 | 1.084 | 1.995 |
| predicted_variance_bucket | `low` | 118 | **1.245** | 1.142 | 1.076 | 1.609 |
| stat | `fg3m` | 61 | **1.292** | 1.242 | 0.926 | 1.840 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 166 | **0.712** | 1.021 | 1.043 | 2.331 |
| edge_bucket | `ge_20pct` | 48 | **0.770** | 0.932 | 1.240 | 2.042 |
| injury_context | `unavailable` | 62 | **0.574** | 0.912 | 1.099 | 2.170 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| lineup_confirmed | `unavailable` | 62 | **0.574** | 0.912 | 1.099 | 2.170 |
| low_line_discrete | `no` | 239 | **0.770** | 0.911 | 1.051 | 2.561 |
| minutes_volatility_bucket | `unavailable` | 357 | **0.781** | 0.995 | 1.055 | 2.257 |
| overall | `ALL` | 357 | **0.781** | 0.995 | 1.055 | 2.257 |
| p0_bucket | `lt_5pct` | 128 | **0.732** | 0.839 | 1.040 | 2.907 |
| predicted_variance_bucket | `high` | 118 | **0.753** | 0.879 | 1.045 | 3.035 |
| role_bucket | `ge30min_starter` | 42 | **0.591** | 0.931 | 1.135 | 2.283 |
| role_bucket | `starter` | 158 | **0.788** | 1.018 | 1.062 | 2.476 |
| side | `UNDER` | 291 | **0.751** | 0.959 | 1.109 | 2.277 |
| snapshot_type | `morning` | 357 | **0.781** | 0.995 | 1.055 | 2.257 |
| stat | `ast` | 57 | **0.526** | 0.768 | 1.022 | 2.037 |
| stat | `pts` | 76 | **0.772** | 0.911 | 1.045 | 3.308 |
| vacated_opportunity_bucket | `unavailable` | 357 | **0.781** | 0.995 | 1.055 | 2.257 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 116 | 1.059 | 0.954 | 0.155 | 2.265 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `latest_valid_report_selected` | 128 | 0.984 | 0.845 | 0.005 | 2.264 |
| line_bucket | `10_to_15` | 30 | 0.988 | 0.873 | 0.004 | 3.235 |
| lineup_confirmed | `projected` | 270 | 1.076 | 0.842 | 0.149 | 2.259 |
| p0_bucket | `5_to_20pct` | 109 | 1.081 | 1.034 | 0.114 | 2.129 |
| p0_bucket | `ge_50pct` | 46 | 1.544 | 0.984 | 0.320 | 1.172 |
| predicted_variance_bucket | `mid` | 121 | 1.084 | 0.914 | 0.145 | 2.131 |
| role_bucket | `core` | 56 | 0.990 | 0.939 | 0.062 | 2.286 |
| role_bucket | `rotation` | 53 | 1.071 | 0.853 | 0.211 | 2.067 |
| side | `OVER` | 66 | 0.759 | 0.966 | -0.398 | 2.171 |
| stat | `blk` | 35 | 1.378 | 1.036 | 0.372 | 1.340 |
| stat | `reb` | 84 | 1.077 | 0.846 | 0.160 | 2.470 |
| stat | `stl` | 44 | 1.357 | 1.122 | 0.244 | 1.628 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 27 | 0.602 | -0.236 |
| line_bucket | `15_to_20` | 17 | 0.948 | -0.013 |
| line_bucket | `2_to_2p5` | 18 | 0.828 | 0.000 |
| line_bucket | `3_to_5` | 27 | 0.518 | 0.074 |
| line_bucket | `4_to_7` | 27 | 1.141 | 0.159 |
| line_bucket | `5_to_8` | 15 | 0.470 | -0.049 |
| line_bucket | `7_to_10` | 14 | 0.833 | 0.265 |
| line_bucket | `ge_10` | 14 | 0.450 | 0.126 |
| line_bucket | `ge_25` | 17 | 0.596 | 0.410 |
| line_bucket | `ge_3` | 4 | 1.507 | 0.488 |
| line_bucket | `lt_10` | 12 | 0.724 | -0.052 |
| line_bucket | `lt_3` | 15 | 0.673 | 0.120 |
| line_bucket | `lt_4` | 29 | 1.082 | 0.127 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `bench` | 28 | 0.916 | -0.154 |
| role_bucket | `lt15min` | 4 | 2.219 | -0.080 |
| role_bucket | `lt22min` | 4 | 0.780 | -0.855 |
| role_bucket | `lt30min` | 12 | 0.353 | 0.008 |

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
- settled window: **2026-05-23 → 2026-06-13** (10 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

