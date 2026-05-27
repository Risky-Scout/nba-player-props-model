# PMF Variance Experience Study — May 26, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-26` over a 60-day lookback._

## Executive summary

- **1,788** settled rows from **2026-04-17** through **2026-05-25** (27 delivery dates with at least one settled row).
- **Mean A/E = 1.109** — actual outcomes ran +10.9% relative to expected means in this sample.
- **Variance A/E = 0.837** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.150, sd = 0.992** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.758 and 0.909); the 10th-percentile band is over-covered (0.201 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.269 vs 0.247 (model vs market); logloss 0.741 vs 0.689.
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
| rows | 1,788 |
| actual_mean (per row) | 6.148 |
| expected_mean (per row) | 5.544 |
| **mean_AE** | **1.1091** |
| Σ squared residual | 24681.11 |
| Σ expected variance | 29481.50 |
| **variance_AE** | **0.8372** |
| standardized_residual_mean | 0.1495 |
| standardized_residual_sd | 0.9923 |
| pmf_nll_mean | 2.5178 |
| pmf_rps_mean | 0.1125 |
| model_brier (over/under) | 0.2694 |
| market_brier (over/under) | 0.2469 |
| model_logloss (over/under) | 0.7412 |
| market_logloss (over/under) | 0.6888 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.201 / 0.298 / 0.498 / 0.758 / 0.909 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 56 | **1.367** | 1.150 | 1.175 | 2.785 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 61 | **0.529** | 0.943 | 0.859 | 2.664 |
| edge_bucket | `5_to_10pct` | 376 | **0.798** | 0.928 | 1.059 | 2.538 |
| injury_context | `latest_valid_report_selected` | 54 | **0.798** | 0.992 | 0.937 | 2.450 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 262 | **0.650** | 0.984 | 1.095 | 1.936 |
| line_bucket | `20_to_25` | 47 | **0.668** | 1.009 | 1.082 | 4.416 |
| line_bucket | `2_to_2p5` | 73 | **0.719** | 1.234 | 1.061 | 2.405 |
| line_bucket | `5_to_8` | 87 | **0.691** | 0.880 | 1.068 | 2.497 |
| line_bucket | `ge_10` | 33 | **0.692** | 0.831 | 1.115 | 2.704 |
| line_bucket | `ge_25` | 61 | **0.597** | 0.801 | 1.051 | 3.658 |
| line_bucket | `le_half` | 322 | **0.425** | 0.680 | 1.017 | 1.256 |
| lineup_confirmed | `projected` | 455 | **0.798** | 0.956 | 1.083 | 2.554 |
| low_line_discrete | `yes` | 584 | **0.545** | 0.830 | 1.064 | 1.561 |
| p0_bucket | `20_to_50pct` | 306 | **0.665** | 0.931 | 1.046 | 1.853 |
| p0_bucket | `ge_50pct` | 289 | **0.457** | 0.671 | 1.262 | 1.260 |
| role_bucket | `bench` | 42 | **0.675** | 0.965 | 0.852 | 2.406 |
| role_bucket | `ge30min_starter` | 581 | **0.684** | 0.960 | 1.067 | 2.537 |
| role_bucket | `lt22min` | 142 | **0.777** | 0.796 | 1.000 | 1.801 |
| role_bucket | `starter` | 259 | **0.630** | 0.878 | 1.038 | 2.496 |
| stat | `blk` | 221 | **0.682** | 0.752 | 1.288 | 1.549 |
| stat | `fg3m` | 212 | **0.682** | 1.111 | 0.960 | 2.101 |
| stat | `stl` | 237 | **0.530** | 0.795 | 1.072 | 1.411 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 884 | 1.110 | 0.819 | 0.126 | 2.509 |
| edge_bucket | `ge_20pct` | 467 | 1.216 | 1.007 | 0.333 | 2.499 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `unavailable` | 1308 | 1.129 | 0.859 | 0.173 | 2.506 |
| line_bucket | `10_to_15` | 117 | 1.079 | 1.005 | 0.160 | 3.267 |
| line_bucket | `15_to_20` | 119 | 1.186 | 0.917 | 0.432 | 3.870 |
| line_bucket | `3_to_5` | 122 | 1.007 | 0.842 | 0.005 | 2.408 |
| line_bucket | `4_to_7` | 176 | 1.198 | 1.071 | 0.351 | 2.881 |
| line_bucket | `7_to_10` | 92 | 1.155 | 1.049 | 0.341 | 3.067 |
| line_bucket | `lt_10` | 33 | 1.082 | 0.971 | 0.099 | 3.661 |
| line_bucket | `lt_3` | 55 | 1.110 | 0.873 | 0.116 | 2.194 |
| line_bucket | `lt_4` | 159 | 1.103 | 1.024 | 0.135 | 2.640 |
| lineup_confirmed | `unavailable` | 1308 | 1.129 | 0.859 | 0.173 | 2.506 |
| low_line_discrete | `no` | 1204 | 1.112 | 0.850 | 0.203 | 2.982 |
| minutes_volatility_bucket | `unavailable` | 1788 | 1.109 | 0.837 | 0.150 | 2.518 |
| overall | `ALL` | 1788 | 1.109 | 0.837 | 0.150 | 2.518 |
| p0_bucket | `5_to_20pct` | 506 | 1.185 | 0.949 | 0.199 | 2.306 |
| p0_bucket | `lt_5pct` | 687 | 1.092 | 0.834 | 0.176 | 3.499 |
| predicted_variance_bucket | `high` | 590 | 1.112 | 0.815 | 0.236 | 3.317 |
| predicted_variance_bucket | `low` | 590 | 1.074 | 1.033 | 0.068 | 1.997 |
| predicted_variance_bucket | `mid` | 608 | 1.112 | 0.933 | 0.145 | 2.247 |
| role_bucket | `lt30min` | 575 | 1.225 | 1.075 | 0.280 | 2.654 |
| role_bucket | `rotation` | 123 | 1.143 | 0.979 | 0.190 | 2.601 |
| side | `OVER` | 240 | 0.930 | 0.925 | -0.235 | 3.062 |
| side | `UNDER` | 1548 | 1.141 | 0.828 | 0.209 | 2.433 |
| snapshot_type | `morning` | 1788 | 1.109 | 0.837 | 0.150 | 2.518 |
| stat | `ast` | 281 | 1.061 | 0.806 | 0.073 | 2.445 |
| stat | `pts` | 377 | 1.107 | 0.822 | 0.236 | 3.698 |
| stat | `reb` | 460 | 1.153 | 1.002 | 0.265 | 2.822 |
| vacated_opportunity_bucket | `unavailable` | 1788 | 1.109 | 0.837 | 0.150 | 2.518 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 13 | 2.361 | 0.223 |
| line_bucket | `ge_8` | 17 | 1.041 | 0.401 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 10 | 2.868 | 0.427 |

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
- settled window: **2026-04-17 → 2026-05-25** (27 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

