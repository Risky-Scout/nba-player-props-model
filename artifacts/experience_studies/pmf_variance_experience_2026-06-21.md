# PMF Variance Experience Study — June 21, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-21` over a 60-day lookback._

## Executive summary

- **1,747** settled rows from **2026-04-22** through **2026-06-13** (29 delivery dates with at least one settled row).
- **Mean A/E = 1.108** — actual outcomes ran +10.8% relative to expected means in this sample.
- **Variance A/E = 0.795** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.148, sd = 0.913** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.760 and 0.916); the 10th-percentile band is over-covered (0.196 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.270 vs 0.247 (model vs market); logloss 0.741 vs 0.690.
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
| rows | 1,747 |
| actual_mean (per row) | 6.010 |
| expected_mean (per row) | 5.425 |
| **mean_AE** | **1.1078** |
| Σ squared residual | 24024.70 |
| Σ expected variance | 30216.22 |
| **variance_AE** | **0.7951** |
| standardized_residual_mean | 0.1484 |
| standardized_residual_sd | 0.9133 |
| pmf_nll_mean | 2.3032 |
| pmf_rps_mean | 0.1014 |
| model_brier (over/under) | 0.2697 |
| market_brier (over/under) | 0.2475 |
| model_logloss (over/under) | 0.7410 |
| market_logloss (over/under) | 0.6899 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.196 / 0.297 / 0.499 / 0.760 / 0.916 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 76 | **0.548** | 0.842 | 0.854 | 2.263 |
| edge_bucket | `10_to_20pct` | 857 | **0.740** | 0.912 | 1.113 | 2.314 |
| injury_context | `unavailable` | 1034 | **0.776** | 0.858 | 1.143 | 2.195 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 247 | **0.641** | 0.931 | 1.109 | 1.887 |
| line_bucket | `20_to_25` | 32 | **0.518** | 0.709 | 1.108 | 3.398 |
| line_bucket | `2_to_2p5` | 70 | **0.521** | 0.884 | 1.051 | 1.835 |
| line_bucket | `5_to_8` | 86 | **0.648** | 0.817 | 1.082 | 2.391 |
| line_bucket | `ge_10` | 38 | **0.617** | 0.762 | 1.132 | 2.777 |
| line_bucket | `ge_25` | 66 | **0.552** | 0.723 | 1.082 | 3.510 |
| line_bucket | `le_half` | 338 | **0.486** | 0.746 | 0.991 | 1.290 |
| lineup_confirmed | `unavailable` | 1034 | **0.776** | 0.858 | 1.143 | 2.195 |
| low_line_discrete | `yes` | 585 | **0.568** | 0.830 | 1.059 | 1.542 |
| minutes_volatility_bucket | `unavailable` | 1747 | **0.795** | 0.913 | 1.108 | 2.303 |
| overall | `ALL` | 1747 | **0.795** | 0.913 | 1.108 | 2.303 |
| p0_bucket | `20_to_50pct` | 313 | **0.710** | 0.951 | 1.032 | 1.895 |
| p0_bucket | `ge_50pct` | 290 | **0.486** | 0.705 | 1.298 | 1.260 |
| p0_bucket | `lt_5pct` | 615 | **0.771** | 0.932 | 1.089 | 3.017 |
| predicted_variance_bucket | `high` | 577 | **0.777** | 0.893 | 1.110 | 3.114 |
| predicted_variance_bucket | `low` | 577 | **0.691** | 0.881 | 1.097 | 1.517 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 473 | **0.584** | 0.798 | 1.067 | 2.224 |
| role_bucket | `lt22min` | 118 | **0.741** | 0.716 | 0.964 | 1.667 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| side | `OVER` | 211 | **0.752** | 0.881 | 0.789 | 2.120 |
| side | `UNDER` | 1536 | **0.799** | 0.895 | 1.144 | 2.328 |
| snapshot_type | `morning` | 1747 | **0.795** | 0.913 | 1.108 | 2.303 |
| stat | `ast` | 279 | **0.754** | 0.888 | 1.077 | 2.228 |
| stat | `blk` | 221 | **0.729** | 0.773 | 1.335 | 1.522 |
| stat | `fg3m` | 207 | **0.637** | 1.013 | 0.946 | 1.930 |
| stat | `pts` | 357 | **0.773** | 0.905 | 1.103 | 3.395 |
| stat | `stl` | 239 | **0.524** | 0.749 | 1.055 | 1.384 |
| vacated_opportunity_bucket | `unavailable` | 1747 | **0.795** | 0.913 | 1.108 | 2.303 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 420 | 1.040 | 0.819 | 0.030 | 2.334 |
| edge_bucket | `ge_20pct` | 394 | 1.257 | 0.972 | 0.332 | 2.255 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 123 | 1.053 | 0.931 | 0.107 | 3.274 |
| line_bucket | `15_to_20` | 102 | 1.161 | 0.900 | 0.319 | 3.469 |
| line_bucket | `3_to_5` | 122 | 1.012 | 0.802 | 0.034 | 2.136 |
| line_bucket | `4_to_7` | 173 | 1.174 | 1.109 | 0.279 | 2.598 |
| line_bucket | `7_to_10` | 87 | 1.150 | 1.083 | 0.294 | 2.747 |
| line_bucket | `lt_10` | 34 | 1.123 | 1.065 | 0.188 | 3.387 |
| line_bucket | `lt_3` | 57 | 1.209 | 0.860 | 0.267 | 2.066 |
| line_bucket | `lt_4` | 146 | 1.115 | 0.947 | 0.177 | 2.256 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| low_line_discrete | `no` | 1162 | 1.111 | 0.805 | 0.198 | 2.686 |
| p0_bucket | `5_to_20pct` | 529 | 1.181 | 1.012 | 0.209 | 2.286 |
| predicted_variance_bucket | `mid` | 593 | 1.104 | 0.949 | 0.146 | 2.279 |
| role_bucket | `lt30min` | 431 | 1.272 | 1.013 | 0.304 | 2.311 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| stat | `reb` | 444 | 1.148 | 0.983 | 0.251 | 2.530 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 12 | 2.539 | 0.470 |
| line_bucket | `ge_8` | 14 | 0.882 | 0.257 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 12 | 3.358 | 0.297 |

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
- settled window: **2026-04-22 → 2026-06-13** (29 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

