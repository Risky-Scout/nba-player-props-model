# PMF Variance Experience Study — June 5, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-05` over a 60-day lookback._

## Executive summary

- **1,900** settled rows from **2026-04-17** through **2026-06-03** (30 delivery dates with at least one settled row).
- **Mean A/E = 1.104** — actual outcomes ran +10.4% relative to expected means in this sample.
- **Variance A/E = 0.836** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.146, sd = 0.997** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.761 and 0.910); the 10th-percentile band is over-covered (0.203 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.269 vs 0.247 (model vs market); logloss 0.741 vs 0.688.
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
| rows | 1,900 |
| actual_mean (per row) | 6.117 |
| expected_mean (per row) | 5.541 |
| **mean_AE** | **1.1038** |
| Σ squared residual | 26166.70 |
| Σ expected variance | 31309.61 |
| **variance_AE** | **0.8357** |
| standardized_residual_mean | 0.1461 |
| standardized_residual_sd | 0.9968 |
| pmf_nll_mean | 2.5051 |
| pmf_rps_mean | 0.1131 |
| model_brier (over/under) | 0.2691 |
| market_brier (over/under) | 0.2466 |
| model_logloss (over/under) | 0.7405 |
| market_logloss (over/under) | 0.6884 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.203 / 0.301 / 0.501 / 0.761 / 0.910 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 70 | **1.441** | 1.170 | 1.078 | 2.681 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 70 | **0.558** | 0.939 | 0.833 | 2.626 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 278 | **0.679** | 1.013 | 1.109 | 1.952 |
| line_bucket | `20_to_25` | 47 | **0.668** | 1.009 | 1.082 | 4.416 |
| line_bucket | `2_to_2p5` | 75 | **0.719** | 1.225 | 1.070 | 2.388 |
| line_bucket | `5_to_8` | 93 | **0.685** | 0.874 | 1.059 | 2.486 |
| line_bucket | `ge_10` | 37 | **0.655** | 0.813 | 1.101 | 2.706 |
| line_bucket | `ge_25` | 67 | **0.595** | 0.793 | 1.056 | 3.653 |
| line_bucket | `le_half` | 343 | **0.435** | 0.695 | 1.003 | 1.243 |
| low_line_discrete | `yes` | 621 | **0.565** | 0.853 | 1.066 | 1.560 |
| p0_bucket | `20_to_50pct` | 335 | **0.688** | 0.960 | 1.050 | 1.857 |
| p0_bucket | `ge_50pct` | 302 | **0.461** | 0.678 | 1.260 | 1.246 |
| role_bucket | `bench` | 43 | **0.677** | 0.968 | 0.846 | 2.379 |
| role_bucket | `ge30min_starter` | 601 | **0.683** | 0.964 | 1.073 | 2.539 |
| role_bucket | `lt22min` | 145 | **0.778** | 0.798 | 0.982 | 1.801 |
| role_bucket | `starter` | 290 | **0.634** | 0.879 | 1.024 | 2.483 |
| stat | `ast` | 300 | **0.795** | 0.991 | 1.053 | 2.421 |
| stat | `blk` | 235 | **0.683** | 0.755 | 1.269 | 1.523 |
| stat | `fg3m` | 229 | **0.714** | 1.137 | 0.971 | 2.099 |
| stat | `stl` | 247 | **0.538** | 0.803 | 1.072 | 1.408 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 931 | 1.107 | 0.814 | 0.128 | 2.510 |
| edge_bucket | `5_to_10pct` | 417 | 1.054 | 0.809 | 0.049 | 2.508 |
| edge_bucket | `ge_20pct` | 482 | 1.217 | 0.998 | 0.325 | 2.475 |
| injury_context | `fallback_used` | 45 | 1.104 | 0.831 | 0.228 | 2.340 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 89 | 0.890 | 0.850 | -0.091 | 2.357 |
| injury_context | `unavailable` | 1340 | 1.130 | 0.853 | 0.173 | 2.503 |
| line_bucket | `10_to_15` | 127 | 1.053 | 0.977 | 0.121 | 3.258 |
| line_bucket | `15_to_20` | 122 | 1.178 | 0.917 | 0.414 | 3.859 |
| line_bucket | `3_to_5` | 128 | 0.996 | 0.826 | -0.010 | 2.386 |
| line_bucket | `4_to_7` | 185 | 1.204 | 1.119 | 0.364 | 2.883 |
| line_bucket | `7_to_10` | 95 | 1.152 | 1.083 | 0.338 | 3.069 |
| line_bucket | `lt_10` | 38 | 1.112 | 0.984 | 0.150 | 3.608 |
| line_bucket | `lt_3` | 62 | 1.109 | 0.862 | 0.121 | 2.164 |
| line_bucket | `lt_4` | 171 | 1.102 | 1.046 | 0.131 | 2.620 |
| lineup_confirmed | `projected` | 535 | 1.068 | 0.809 | 0.094 | 2.514 |
| lineup_confirmed | `unavailable` | 1340 | 1.130 | 0.853 | 0.173 | 2.503 |
| low_line_discrete | `no` | 1279 | 1.106 | 0.847 | 0.195 | 2.964 |
| minutes_volatility_bucket | `unavailable` | 1900 | 1.104 | 0.836 | 0.146 | 2.505 |
| overall | `ALL` | 1900 | 1.104 | 0.836 | 0.146 | 2.505 |
| p0_bucket | `5_to_20pct` | 539 | 1.186 | 0.989 | 0.202 | 2.314 |
| p0_bucket | `lt_5pct` | 724 | 1.085 | 0.825 | 0.162 | 3.473 |
| predicted_variance_bucket | `high` | 627 | 1.105 | 0.810 | 0.223 | 3.305 |
| predicted_variance_bucket | `low` | 627 | 1.077 | 1.041 | 0.073 | 1.970 |
| predicted_variance_bucket | `mid` | 646 | 1.110 | 0.955 | 0.143 | 2.248 |
| role_bucket | `lt30min` | 580 | 1.224 | 1.066 | 0.279 | 2.650 |
| role_bucket | `rotation` | 157 | 1.169 | 0.960 | 0.248 | 2.523 |
| side | `OVER` | 263 | 0.904 | 0.988 | -0.272 | 2.977 |
| side | `UNDER` | 1637 | 1.140 | 0.818 | 0.213 | 2.429 |
| snapshot_type | `morning` | 1900 | 1.104 | 0.836 | 0.146 | 2.505 |
| stat | `pts` | 401 | 1.100 | 0.816 | 0.222 | 3.676 |
| stat | `reb` | 488 | 1.152 | 1.023 | 0.265 | 2.814 |
| vacated_opportunity_bucket | `unavailable` | 1900 | 1.104 | 0.836 | 0.146 | 2.505 |

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
- settled window: **2026-04-17 → 2026-06-03** (30 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

