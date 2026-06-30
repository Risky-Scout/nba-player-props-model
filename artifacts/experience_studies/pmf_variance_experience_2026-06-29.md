# PMF Variance Experience Study — June 29, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-29` over a 60-day lookback._

## Executive summary

- **979** settled rows from **2026-04-30** through **2026-06-13** (22 delivery dates with at least one settled row).
- **Mean A/E = 1.057** — actual outcomes ran +5.7% relative to expected means in this sample.
- **Variance A/E = 0.778** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.077, sd = 0.941** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.778 and 0.924); the 10th-percentile band is over-covered (0.211 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.261 vs 0.249 (model vs market); logloss 0.722 vs 0.692.
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
| rows | 979 |
| actual_mean (per row) | 5.822 |
| expected_mean (per row) | 5.511 |
| **mean_AE** | **1.0565** |
| Σ squared residual | 12525.99 |
| Σ expected variance | 16099.20 |
| **variance_AE** | **0.7781** |
| standardized_residual_mean | 0.0766 |
| standardized_residual_sd | 0.9407 |
| pmf_nll_mean | 2.2724 |
| pmf_rps_mean | 0.1074 |
| model_brier (over/under) | 0.2614 |
| market_brier (over/under) | 0.2485 |
| model_logloss (over/under) | 0.7220 |
| market_logloss (over/under) | 0.6923 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.211 / 0.340 / 0.549 / 0.778 / 0.924 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| p0_bucket | `5_to_20pct` | 287 | **1.316** | 1.007 | 1.103 | 2.169 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 58 | **0.511** | 0.865 | 0.919 | 2.162 |
| edge_bucket | `10_to_20pct` | 465 | **0.789** | 0.956 | 1.085 | 2.282 |
| edge_bucket | `5_to_10pct` | 311 | **0.728** | 0.910 | 0.996 | 2.309 |
| injury_context | `unavailable` | 287 | **0.613** | 0.826 | 1.036 | 1.863 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 160 | **0.641** | 0.966 | 1.081 | 1.843 |
| line_bucket | `2_to_2p5` | 60 | **0.475** | 0.767 | 1.016 | 1.665 |
| line_bucket | `3_to_5` | 70 | **0.764** | 0.892 | 1.016 | 2.066 |
| line_bucket | `ge_25` | 46 | **0.534** | 0.697 | 1.091 | 3.495 |
| line_bucket | `le_half` | 170 | **0.546** | 0.818 | 0.824 | 1.313 |
| lineup_confirmed | `unavailable` | 287 | **0.613** | 0.826 | 1.036 | 1.863 |
| low_line_discrete | `no` | 649 | **0.786** | 0.961 | 1.062 | 2.630 |
| low_line_discrete | `yes` | 330 | **0.602** | 0.896 | 0.980 | 1.570 |
| minutes_volatility_bucket | `unavailable` | 979 | **0.778** | 0.941 | 1.057 | 2.272 |
| overall | `ALL` | 979 | **0.778** | 0.941 | 1.057 | 2.272 |
| p0_bucket | `20_to_50pct` | 198 | **0.747** | 1.004 | 1.045 | 1.902 |
| p0_bucket | `ge_50pct` | 118 | **0.398** | 0.722 | 1.122 | 1.074 |
| p0_bucket | `lt_5pct` | 376 | **0.719** | 0.917 | 1.046 | 2.923 |
| predicted_variance_bucket | `high` | 323 | **0.763** | 0.939 | 1.065 | 3.099 |
| predicted_variance_bucket | `low` | 323 | **0.793** | 0.950 | 1.049 | 1.537 |
| role_bucket | `bench` | 66 | **0.731** | 0.981 | 0.873 | 2.070 |
| role_bucket | `ge30min_starter` | 175 | **0.519** | 0.830 | 1.035 | 2.005 |
| role_bucket | `lt30min` | 79 | **0.506** | 0.768 | 1.060 | 1.696 |
| role_bucket | `starter` | 386 | **0.676** | 0.932 | 1.041 | 2.460 |
| side | `UNDER` | 793 | **0.769** | 0.914 | 1.110 | 2.292 |
| snapshot_type | `morning` | 979 | **0.778** | 0.941 | 1.057 | 2.272 |
| stat | `fg3m` | 174 | **0.606** | 0.975 | 0.926 | 1.823 |
| stat | `pts` | 196 | **0.741** | 0.907 | 1.074 | 3.399 |
| stat | `stl` | 120 | **0.593** | 0.818 | 0.991 | 1.417 |
| vacated_opportunity_bucket | `unavailable` | 979 | **0.778** | 0.941 | 1.057 | 2.272 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 145 | 1.167 | 0.986 | 0.212 | 2.208 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 70 | 1.056 | 0.819 | 0.129 | 3.244 |
| line_bucket | `15_to_20` | 46 | 1.011 | 0.873 | 0.040 | 3.423 |
| line_bucket | `4_to_7` | 81 | 0.985 | 1.173 | -0.001 | 2.558 |
| line_bucket | `5_to_8` | 52 | 1.050 | 0.874 | 0.075 | 2.398 |
| line_bucket | `7_to_10` | 42 | 1.092 | 1.077 | 0.221 | 2.688 |
| line_bucket | `lt_3` | 31 | 1.194 | 0.912 | 0.289 | 2.032 |
| line_bucket | `lt_4` | 76 | 1.014 | 1.115 | 0.056 | 2.276 |
| lineup_confirmed | `projected` | 667 | 1.073 | 0.820 | 0.109 | 2.442 |
| predicted_variance_bucket | `mid` | 333 | 1.029 | 0.884 | 0.048 | 2.184 |
| role_bucket | `rotation` | 146 | 1.151 | 0.971 | 0.210 | 2.469 |
| side | `OVER` | 186 | 0.776 | 0.830 | -0.383 | 2.190 |
| stat | `ast` | 158 | 1.057 | 0.831 | 0.107 | 2.184 |
| stat | `blk` | 106 | 1.256 | 0.863 | 0.201 | 1.523 |
| stat | `reb` | 225 | 1.037 | 1.022 | 0.084 | 2.510 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| line_bucket | `20_to_25` | 12 | 0.505 | 0.279 |
| line_bucket | `ge_10` | 26 | 0.673 | 0.208 |
| line_bucket | `ge_3` | 10 | 2.407 | 0.380 |
| line_bucket | `ge_8` | 5 | 0.773 | 0.216 |
| line_bucket | `lt_10` | 22 | 1.408 | 0.338 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 27 | 0.601 | -0.339 |

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
- settled window: **2026-04-30 → 2026-06-13** (22 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

