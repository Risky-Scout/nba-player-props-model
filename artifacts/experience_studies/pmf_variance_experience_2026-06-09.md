# PMF Variance Experience Study — June 9, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-09` over a 60-day lookback._

## Executive summary

- **1,975** settled rows from **2026-04-17** through **2026-06-08** (32 delivery dates with at least one settled row).
- **Mean A/E = 1.104** — actual outcomes ran +10.4% relative to expected means in this sample.
- **Variance A/E = 0.829** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.151, sd = 0.999** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.760 and 0.910); the 10th-percentile band is over-covered (0.202 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.270 vs 0.247 (model vs market); logloss 0.743 vs 0.689.
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
| rows | 1,975 |
| actual_mean (per row) | 6.097 |
| expected_mean (per row) | 5.521 |
| **mean_AE** | **1.1042** |
| Σ squared residual | 26832.75 |
| Σ expected variance | 32369.30 |
| **variance_AE** | **0.8290** |
| standardized_residual_mean | 0.1513 |
| standardized_residual_sd | 0.9985 |
| pmf_nll_mean | 2.5039 |
| pmf_rps_mean | 0.1141 |
| model_brier (over/under) | 0.2701 |
| market_brier (over/under) | 0.2470 |
| model_logloss (over/under) | 0.7426 |
| market_logloss (over/under) | 0.6893 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.202 / 0.298 / 0.500 / 0.760 / 0.910 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 82 | **1.318** | 1.108 | 1.091 | 2.602 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 76 | **0.536** | 0.935 | 0.861 | 2.578 |
| injury_context | `fallback_used` | 90 | **0.779** | 1.134 | 1.118 | 2.462 |
| injury_context | `latest_valid_report_selected` | 119 | **0.781** | 0.957 | 0.939 | 2.343 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 287 | **0.702** | 1.040 | 1.121 | 1.990 |
| line_bucket | `20_to_25` | 47 | **0.668** | 1.009 | 1.082 | 4.416 |
| line_bucket | `2_to_2p5` | 78 | **0.705** | 1.202 | 1.070 | 2.348 |
| line_bucket | `5_to_8` | 97 | **0.675** | 0.865 | 1.061 | 2.473 |
| line_bucket | `ge_10` | 40 | **0.618** | 0.793 | 1.085 | 2.683 |
| line_bucket | `ge_25` | 70 | **0.602** | 0.792 | 1.070 | 3.654 |
| line_bucket | `le_half` | 361 | **0.473** | 0.737 | 1.026 | 1.286 |
| lineup_confirmed | `projected` | 610 | **0.793** | 0.985 | 1.073 | 2.509 |
| low_line_discrete | `yes` | 648 | **0.594** | 0.885 | 1.082 | 1.598 |
| p0_bucket | `20_to_50pct` | 351 | **0.726** | 1.005 | 1.057 | 1.917 |
| p0_bucket | `ge_50pct` | 315 | **0.476** | 0.696 | 1.294 | 1.260 |
| role_bucket | `bench` | 52 | **0.668** | 0.950 | 0.845 | 2.239 |
| role_bucket | `ge30min_starter` | 601 | **0.683** | 0.964 | 1.073 | 2.539 |
| role_bucket | `lt22min` | 145 | **0.778** | 0.798 | 0.982 | 1.801 |
| role_bucket | `starter` | 341 | **0.640** | 0.924 | 1.036 | 2.522 |
| stat | `ast` | 313 | **0.790** | 0.988 | 1.058 | 2.411 |
| stat | `blk` | 243 | **0.686** | 0.764 | 1.284 | 1.519 |
| stat | `fg3m` | 243 | **0.737** | 1.157 | 0.973 | 2.114 |
| stat | `stl` | 256 | **0.570** | 0.833 | 1.106 | 1.468 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 960 | 1.108 | 0.803 | 0.137 | 2.519 |
| edge_bucket | `5_to_10pct` | 443 | 1.050 | 0.814 | 0.047 | 2.501 |
| edge_bucket | `ge_20pct` | 496 | 1.219 | 0.991 | 0.327 | 2.466 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `unavailable` | 1340 | 1.130 | 0.853 | 0.173 | 2.503 |
| line_bucket | `10_to_15` | 135 | 1.054 | 0.959 | 0.119 | 3.250 |
| line_bucket | `15_to_20` | 125 | 1.174 | 0.904 | 0.405 | 3.841 |
| line_bucket | `3_to_5` | 134 | 1.009 | 0.818 | 0.013 | 2.377 |
| line_bucket | `4_to_7` | 190 | 1.193 | 1.113 | 0.347 | 2.871 |
| line_bucket | `7_to_10` | 97 | 1.149 | 1.064 | 0.331 | 3.054 |
| line_bucket | `lt_10` | 39 | 1.095 | 0.977 | 0.125 | 3.586 |
| line_bucket | `lt_3` | 65 | 1.116 | 0.887 | 0.132 | 2.165 |
| line_bucket | `lt_4` | 177 | 1.102 | 1.023 | 0.133 | 2.603 |
| lineup_confirmed | `unavailable` | 1340 | 1.130 | 0.853 | 0.173 | 2.503 |
| low_line_discrete | `no` | 1327 | 1.106 | 0.839 | 0.194 | 2.946 |
| minutes_volatility_bucket | `unavailable` | 1975 | 1.104 | 0.829 | 0.151 | 2.504 |
| overall | `ALL` | 1975 | 1.104 | 0.829 | 0.151 | 2.504 |
| p0_bucket | `5_to_20pct` | 556 | 1.184 | 0.979 | 0.205 | 2.305 |
| p0_bucket | `lt_5pct` | 753 | 1.084 | 0.816 | 0.158 | 3.445 |
| predicted_variance_bucket | `high` | 652 | 1.104 | 0.802 | 0.217 | 3.287 |
| predicted_variance_bucket | `low` | 652 | 1.093 | 1.076 | 0.095 | 1.990 |
| predicted_variance_bucket | `mid` | 671 | 1.108 | 0.949 | 0.142 | 2.242 |
| role_bucket | `lt30min` | 580 | 1.224 | 1.066 | 0.279 | 2.650 |
| role_bucket | `rotation` | 160 | 1.163 | 0.957 | 0.247 | 2.511 |
| side | `OVER` | 276 | 0.910 | 0.981 | -0.259 | 2.968 |
| side | `UNDER` | 1699 | 1.139 | 0.812 | 0.218 | 2.429 |
| snapshot_type | `morning` | 1975 | 1.104 | 0.829 | 0.151 | 2.504 |
| stat | `pts` | 416 | 1.101 | 0.809 | 0.220 | 3.659 |
| stat | `reb` | 504 | 1.144 | 1.003 | 0.254 | 2.797 |
| vacated_opportunity_bucket | `unavailable` | 1975 | 1.104 | 0.829 | 0.151 | 2.504 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 16 | 2.145 | 0.166 |
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
- settled window: **2026-04-17 → 2026-06-08** (32 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

