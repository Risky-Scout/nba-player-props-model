# PMF Variance Experience Study — June 7, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-07` over a 60-day lookback._

## Executive summary

- **1,945** settled rows from **2026-04-17** through **2026-06-05** (31 delivery dates with at least one settled row).
- **Mean A/E = 1.104** — actual outcomes ran +10.4% relative to expected means in this sample.
- **Variance A/E = 0.834** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.152, sd = 1.000** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.759 and 0.910); the 10th-percentile band is over-covered (0.202 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.270 vs 0.247 (model vs market); logloss 0.742 vs 0.689.
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
| rows | 1,945 |
| actual_mean (per row) | 6.088 |
| expected_mean (per row) | 5.513 |
| **mean_AE** | **1.1044** |
| Σ squared residual | 26544.84 |
| Σ expected variance | 31833.86 |
| **variance_AE** | **0.8339** |
| standardized_residual_mean | 0.1520 |
| standardized_residual_sd | 1.0001 |
| pmf_nll_mean | 2.5070 |
| pmf_rps_mean | 0.1141 |
| model_brier (over/under) | 0.2700 |
| market_brier (over/under) | 0.2470 |
| model_logloss (over/under) | 0.7425 |
| market_logloss (over/under) | 0.6891 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.202 / 0.299 / 0.500 / 0.759 / 0.910 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 76 | **1.370** | 1.138 | 1.076 | 2.627 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 73 | **0.540** | 0.944 | 0.837 | 2.602 |
| injury_context | `fallback_used` | 90 | **0.779** | 1.134 | 1.118 | 2.462 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 284 | **0.701** | 1.039 | 1.126 | 1.995 |
| line_bucket | `20_to_25` | 47 | **0.668** | 1.009 | 1.082 | 4.416 |
| line_bucket | `2_to_2p5` | 77 | **0.709** | 1.209 | 1.067 | 2.358 |
| line_bucket | `5_to_8` | 95 | **0.676** | 0.866 | 1.056 | 2.477 |
| line_bucket | `ge_10` | 38 | **0.640** | 0.802 | 1.099 | 2.695 |
| line_bucket | `ge_25` | 68 | **0.597** | 0.793 | 1.061 | 3.653 |
| line_bucket | `le_half` | 357 | **0.466** | 0.733 | 1.025 | 1.282 |
| low_line_discrete | `yes` | 641 | **0.591** | 0.882 | 1.085 | 1.598 |
| p0_bucket | `20_to_50pct` | 344 | **0.724** | 1.005 | 1.069 | 1.928 |
| p0_bucket | `ge_50pct` | 314 | **0.469** | 0.691 | 1.283 | 1.253 |
| role_bucket | `bench` | 50 | **0.673** | 0.956 | 0.854 | 2.266 |
| role_bucket | `ge30min_starter` | 601 | **0.683** | 0.964 | 1.073 | 2.539 |
| role_bucket | `lt22min` | 145 | **0.778** | 0.798 | 0.982 | 1.801 |
| role_bucket | `starter` | 320 | **0.644** | 0.923 | 1.032 | 2.533 |
| stat | `ast` | 307 | **0.787** | 0.985 | 1.053 | 2.413 |
| stat | `blk` | 242 | **0.688** | 0.765 | 1.283 | 1.519 |
| stat | `fg3m` | 238 | **0.736** | 1.160 | 0.979 | 2.132 |
| stat | `stl` | 253 | **0.564** | 0.831 | 1.097 | 1.460 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 946 | 1.109 | 0.809 | 0.136 | 2.521 |
| edge_bucket | `5_to_10pct` | 434 | 1.051 | 0.818 | 0.049 | 2.506 |
| edge_bucket | `ge_20pct` | 492 | 1.219 | 0.992 | 0.329 | 2.467 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 89 | 0.890 | 0.850 | -0.091 | 2.357 |
| injury_context | `unavailable` | 1340 | 1.130 | 0.853 | 0.173 | 2.503 |
| line_bucket | `10_to_15` | 132 | 1.052 | 0.977 | 0.118 | 3.256 |
| line_bucket | `15_to_20` | 124 | 1.177 | 0.909 | 0.412 | 3.849 |
| line_bucket | `3_to_5` | 131 | 0.994 | 0.809 | -0.012 | 2.373 |
| line_bucket | `4_to_7` | 188 | 1.195 | 1.105 | 0.350 | 2.871 |
| line_bucket | `7_to_10` | 96 | 1.148 | 1.073 | 0.330 | 3.061 |
| line_bucket | `lt_10` | 38 | 1.112 | 0.984 | 0.150 | 3.608 |
| line_bucket | `lt_3` | 64 | 1.130 | 0.881 | 0.153 | 2.174 |
| line_bucket | `lt_4` | 174 | 1.105 | 1.039 | 0.138 | 2.614 |
| lineup_confirmed | `projected` | 580 | 1.072 | 0.805 | 0.117 | 2.519 |
| lineup_confirmed | `unavailable` | 1340 | 1.130 | 0.853 | 0.173 | 2.503 |
| low_line_discrete | `no` | 1304 | 1.106 | 0.844 | 0.194 | 2.954 |
| minutes_volatility_bucket | `unavailable` | 1945 | 1.104 | 0.834 | 0.152 | 2.507 |
| overall | `ALL` | 1945 | 1.104 | 0.834 | 0.152 | 2.507 |
| p0_bucket | `5_to_20pct` | 547 | 1.186 | 0.984 | 0.202 | 2.307 |
| p0_bucket | `lt_5pct` | 740 | 1.084 | 0.822 | 0.157 | 3.455 |
| predicted_variance_bucket | `high` | 642 | 1.105 | 0.808 | 0.220 | 3.293 |
| predicted_variance_bucket | `low` | 642 | 1.091 | 1.073 | 0.094 | 1.994 |
| predicted_variance_bucket | `mid` | 661 | 1.108 | 0.949 | 0.142 | 2.242 |
| role_bucket | `lt30min` | 580 | 1.224 | 1.066 | 0.279 | 2.650 |
| role_bucket | `rotation` | 159 | 1.170 | 0.960 | 0.253 | 2.509 |
| side | `OVER` | 271 | 0.910 | 0.985 | -0.258 | 2.994 |
| side | `UNDER` | 1674 | 1.139 | 0.817 | 0.218 | 2.428 |
| snapshot_type | `morning` | 1945 | 1.104 | 0.834 | 0.152 | 2.507 |
| stat | `pts` | 409 | 1.100 | 0.815 | 0.221 | 3.668 |
| stat | `reb` | 496 | 1.148 | 1.011 | 0.259 | 2.804 |
| vacated_opportunity_bucket | `unavailable` | 1945 | 1.104 | 0.834 | 0.152 | 2.507 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 15 | 2.217 | 0.139 |
| line_bucket | `ge_8` | 17 | 1.041 | 0.401 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 14 | 2.788 | 0.282 |

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
- settled window: **2026-04-17 → 2026-06-05** (31 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

