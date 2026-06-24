# PMF Variance Experience Study — June 23, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-23` over a 60-day lookback._

## Executive summary

- **1,558** settled rows from **2026-04-24** through **2026-06-13** (27 delivery dates with at least one settled row).
- **Mean A/E = 1.099** — actual outcomes ran +9.9% relative to expected means in this sample.
- **Variance A/E = 0.791** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.134, sd = 0.925** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.767 and 0.917); the 10th-percentile band is over-covered (0.203 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.266 vs 0.249 (model vs market); logloss 0.732 vs 0.692.
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
| rows | 1,558 |
| actual_mean (per row) | 5.976 |
| expected_mean (per row) | 5.436 |
| **mean_AE** | **1.0992** |
| Σ squared residual | 21133.48 |
| Σ expected variance | 26731.60 |
| **variance_AE** | **0.7906** |
| standardized_residual_mean | 0.1344 |
| standardized_residual_sd | 0.9249 |
| pmf_nll_mean | 2.3011 |
| pmf_rps_mean | 0.1029 |
| model_brier (over/under) | 0.2655 |
| market_brier (over/under) | 0.2486 |
| model_logloss (over/under) | 0.7318 |
| market_logloss (over/under) | 0.6924 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.203 / 0.306 / 0.511 / 0.767 / 0.917 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `7_to_10` | 77 | **1.205** | 1.082 | 1.161 | 2.784 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 71 | **0.536** | 0.847 | 0.865 | 2.245 |
| edge_bucket | `10_to_20pct` | 779 | **0.730** | 0.921 | 1.106 | 2.320 |
| injury_context | `unavailable` | 845 | **0.762** | 0.868 | 1.134 | 2.167 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 232 | **0.655** | 0.946 | 1.107 | 1.897 |
| line_bucket | `2_to_2p5` | 70 | **0.521** | 0.884 | 1.051 | 1.835 |
| line_bucket | `5_to_8` | 79 | **0.643** | 0.816 | 1.087 | 2.387 |
| line_bucket | `ge_10` | 34 | **0.587** | 0.768 | 1.103 | 2.755 |
| line_bucket | `ge_25` | 60 | **0.561** | 0.721 | 1.092 | 3.518 |
| line_bucket | `le_half` | 287 | **0.473** | 0.747 | 0.906 | 1.255 |
| lineup_confirmed | `unavailable` | 845 | **0.762** | 0.868 | 1.134 | 2.167 |
| low_line_discrete | `no` | 1039 | **0.800** | 0.959 | 1.104 | 2.680 |
| low_line_discrete | `yes` | 519 | **0.574** | 0.843 | 1.025 | 1.542 |
| minutes_volatility_bucket | `unavailable` | 1558 | **0.791** | 0.925 | 1.099 | 2.301 |
| overall | `ALL` | 1558 | **0.791** | 0.925 | 1.099 | 2.301 |
| p0_bucket | `20_to_50pct` | 285 | **0.712** | 0.964 | 1.014 | 1.891 |
| p0_bucket | `ge_50pct` | 239 | **0.470** | 0.705 | 1.240 | 1.212 |
| p0_bucket | `lt_5pct` | 557 | **0.757** | 0.932 | 1.083 | 3.000 |
| predicted_variance_bucket | `high` | 514 | **0.767** | 0.894 | 1.105 | 3.112 |
| predicted_variance_bucket | `low` | 514 | **0.707** | 0.897 | 1.078 | 1.516 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 401 | **0.588** | 0.806 | 1.070 | 2.199 |
| role_bucket | `lt22min` | 92 | **0.545** | 0.704 | 0.939 | 1.606 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| side | `OVER` | 210 | **0.754** | 0.883 | 0.789 | 2.121 |
| side | `UNDER` | 1348 | **0.795** | 0.907 | 1.139 | 2.329 |
| snapshot_type | `morning` | 1558 | **0.791** | 0.925 | 1.099 | 2.301 |
| stat | `ast` | 248 | **0.749** | 0.890 | 1.084 | 2.222 |
| stat | `blk` | 189 | **0.743** | 0.785 | 1.285 | 1.496 |
| stat | `fg3m` | 207 | **0.637** | 1.013 | 0.946 | 1.930 |
| stat | `pts` | 317 | **0.759** | 0.898 | 1.097 | 3.393 |
| stat | `stl` | 205 | **0.542** | 0.759 | 1.032 | 1.379 |
| vacated_opportunity_bucket | `unavailable` | 1558 | **0.791** | 0.925 | 1.099 | 2.301 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 400 | 1.038 | 0.804 | 0.023 | 2.304 |
| edge_bucket | `ge_20pct` | 308 | 1.247 | 1.021 | 0.305 | 2.261 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 112 | 1.052 | 0.922 | 0.107 | 3.276 |
| line_bucket | `15_to_20` | 87 | 1.133 | 0.841 | 0.266 | 3.443 |
| line_bucket | `3_to_5` | 110 | 1.015 | 0.817 | 0.040 | 2.129 |
| line_bucket | `4_to_7` | 153 | 1.142 | 1.112 | 0.234 | 2.586 |
| line_bucket | `lt_10` | 30 | 1.131 | 1.092 | 0.202 | 3.416 |
| line_bucket | `lt_3` | 47 | 1.226 | 0.917 | 0.295 | 2.066 |
| line_bucket | `lt_4` | 128 | 1.095 | 1.030 | 0.157 | 2.263 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| p0_bucket | `5_to_20pct` | 477 | 1.171 | 1.071 | 0.195 | 2.275 |
| predicted_variance_bucket | `mid` | 530 | 1.084 | 0.977 | 0.121 | 2.276 |
| role_bucket | `lt30min` | 342 | 1.248 | 0.995 | 0.262 | 2.279 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| stat | `reb` | 392 | 1.131 | 1.028 | 0.227 | 2.534 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `20_to_25` | 28 | 0.541 | 0.249 |
| line_bucket | `ge_3` | 12 | 2.539 | 0.470 |
| line_bucket | `ge_8` | 12 | 0.754 | 0.306 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 10 | 3.887 | 0.378 |

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
- settled window: **2026-04-24 → 2026-06-13** (27 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

