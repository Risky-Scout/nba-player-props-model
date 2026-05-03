# PMF Variance Experience Study — May 3, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-03` over a 60-day lookback._

## Executive summary

- **1,001** settled rows from **2026-04-17** through **2026-05-02** (15 delivery dates with at least one settled row).
- **Mean A/E = 1.144** — actual outcomes ran +14.4% relative to expected means in this sample.
- **Variance A/E = 0.913** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.211, sd = 1.052** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.746 and 0.899); the 10th-percentile band is over-covered (0.195 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.278 vs 0.246 (model vs market); logloss 0.762 vs 0.688.
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
| rows | 1,001 |
| actual_mean (per row) | 6.329 |
| expected_mean (per row) | 5.531 |
| **mean_AE** | **1.1443** |
| Σ squared residual | 14733.02 |
| Σ expected variance | 16141.00 |
| **variance_AE** | **0.9128** |
| standardized_residual_mean | 0.2106 |
| standardized_residual_sd | 1.0519 |
| pmf_nll_mean | 2.7125 |
| pmf_rps_mean | 0.1221 |
| model_brier (over/under) | 0.2782 |
| market_brier (over/under) | 0.2465 |
| model_logloss (over/under) | 0.7618 |
| market_logloss (over/under) | 0.6876 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.195 / 0.264 / 0.467 / 0.746 / 0.899 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| predicted_variance_bucket | `low` | 330 | **1.406** | 1.258 | 1.123 | 2.354 |
| side | `OVER` | 103 | **1.356** | 1.372 | 1.033 | 4.200 |
| stat | `fg3m` | 76 | **2.009** | 1.522 | 1.108 | 2.725 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `20_to_25` | 33 | **0.780** | 1.123 | 1.068 | 4.866 |
| line_bucket | `5_to_8` | 44 | **0.429** | 0.754 | 1.048 | 2.517 |
| line_bucket | `le_half` | 193 | **0.441** | 0.695 | 1.175 | 1.239 |
| low_line_discrete | `yes` | 320 | **0.629** | 0.902 | 1.200 | 1.606 |
| p0_bucket | `20_to_50pct` | 158 | **0.755** | 1.036 | 1.092 | 1.916 |
| p0_bucket | `5_to_20pct` | 278 | **0.751** | 0.927 | 1.234 | 2.424 |
| p0_bucket | `ge_50pct` | 190 | **0.504** | 0.695 | 1.350 | 1.334 |
| role_bucket | `ge30min_starter` | 398 | **0.750** | 1.024 | 1.084 | 2.797 |
| stat | `ast` | 158 | **0.724** | 1.034 | 1.040 | 2.599 |
| stat | `blk` | 131 | **0.595** | 0.753 | 1.344 | 1.537 |
| stat | `stl` | 140 | **0.554** | 0.854 | 1.184 | 1.460 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 499 | 1.116 | 0.847 | 0.150 | 2.712 |
| edge_bucket | `5_to_10pct` | 138 | 1.143 | 1.021 | 0.158 | 2.884 |
| edge_bucket | `ge_20pct` | 341 | 1.251 | 0.988 | 0.374 | 2.591 |
| injury_context | `unavailable` | 980 | 1.141 | 0.913 | 0.204 | 2.705 |
| line_bucket | `10_to_15` | 67 | 1.063 | 1.173 | 0.132 | 3.270 |
| line_bucket | `15_to_20` | 77 | 1.258 | 1.050 | 0.593 | 4.137 |
| line_bucket | `1_to_1p5` | 127 | 1.220 | 0.866 | 0.182 | 2.164 |
| line_bucket | `3_to_5` | 66 | 0.972 | 0.829 | -0.064 | 2.666 |
| line_bucket | `4_to_7` | 105 | 1.354 | 0.981 | 0.575 | 3.081 |
| line_bucket | `7_to_10` | 51 | 1.202 | 0.924 | 0.427 | 3.332 |
| line_bucket | `lt_3` | 36 | 1.059 | 0.841 | 0.001 | 2.254 |
| line_bucket | `lt_4` | 101 | 1.151 | 0.968 | 0.164 | 2.865 |
| lineup_confirmed | `unavailable` | 980 | 1.141 | 0.913 | 0.204 | 2.705 |
| low_line_discrete | `no` | 681 | 1.141 | 0.923 | 0.256 | 3.233 |
| minutes_volatility_bucket | `unavailable` | 1001 | 1.144 | 0.913 | 0.211 | 2.713 |
| overall | `ALL` | 1001 | 1.144 | 0.913 | 0.211 | 2.713 |
| p0_bucket | `lt_5pct` | 375 | 1.119 | 0.960 | 0.230 | 3.961 |
| predicted_variance_bucket | `high` | 331 | 1.142 | 0.904 | 0.304 | 3.433 |
| predicted_variance_bucket | `mid` | 340 | 1.161 | 0.863 | 0.202 | 2.359 |
| role_bucket | `lt22min` | 110 | 1.022 | 0.804 | -0.063 | 1.910 |
| role_bucket | `lt30min` | 465 | 1.230 | 1.131 | 0.311 | 2.826 |
| side | `UNDER` | 898 | 1.164 | 0.884 | 0.246 | 2.542 |
| snapshot_type | `morning` | 1001 | 1.144 | 0.913 | 0.211 | 2.713 |
| stat | `pts` | 221 | 1.123 | 0.940 | 0.266 | 3.903 |
| stat | `reb` | 275 | 1.237 | 0.908 | 0.371 | 3.016 |
| vacated_opportunity_bucket | `unavailable` | 1001 | 1.144 | 0.913 | 0.211 | 2.713 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 23 | 0.661 | -0.577 |
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `2_to_2p5` | 20 | 2.963 | 0.523 |
| line_bucket | `ge_10` | 18 | 0.541 | 0.185 |
| line_bucket | `ge_25` | 26 | 0.740 | 0.070 |
| line_bucket | `ge_3` | 7 | 1.716 | 0.150 |
| line_bucket | `ge_8` | 12 | 1.147 | 0.479 |
| line_bucket | `lt_10` | 18 | 0.404 | -0.187 |
| lineup_confirmed | `projected` | 21 | 0.902 | 0.518 |
| role_bucket | `bench` | 2 | 0.438 | 0.609 |
| role_bucket | `lt15min` | 7 | 0.245 | -0.016 |
| role_bucket | `rotation` | 17 | 0.862 | 0.392 |
| role_bucket | `starter` | 2 | 2.125 | 1.495 |

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
- settled window: **2026-04-17 → 2026-05-02** (15 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

