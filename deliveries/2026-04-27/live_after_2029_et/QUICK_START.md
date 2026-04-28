# Quick Start — PMF Model Review Package (2026-04-27 late NBA slate)

## Recommended viewing order

1. Open **`START_HERE.html`** — landing page with all entry points.
2. Open **`PMF_MODEL_REVIEW_OVERVIEW.html`** — short visual overview with example PMFs and calibration evidence.
3. Open **`PMF_DISTRIBUTION_VIEWER.html`** — full dashboard, every PMF visually inspectable.
4. Use **`player_prop_pmfs_tonight_MODEL_ONLY.parquet`** as the canonical machine-readable model output.
5. Use **`player_prop_pmfs_tonight_MODEL_ONLY_SUMMARY.csv`** for one-row-per-prop summaries (mean, median, mode, p_over_line_model, edge vs market).
6. Use **`player_prop_pmfs_tonight_MODEL_ONLY_EXPANDED.csv`** for one-row-per-outcome probability audit.
7. Use **`player_prop_pmfs_tonight_MODEL_ONLY_WIDE.csv`** for the easiest spreadsheet viewing of the full PMFs (one column per outcome).

The MODEL_ONLY files are the **standalone model**. The
`player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.*` files are NOT
for evaluating the standalone model — their `pmf_json` is market-tilted
(CDF anchored at the offered line). Market columns in any file are
**comparison references only** and do not modify model PMFs.

## Reading any MODEL_ONLY row

1. `pmf_json` contains the full standalone-model PMF as a JSON object
   `{"k": prob, ...}` with `k` from `0` to `support_max`. Entries with
   probability ≤ 1e-9 are omitted.
2. `p_over_line` is the model probability of `stat > line` (over side),
   computed from `pmf_json`.
3. `market_fair_over_prob` is the reference de-vigged market probability
   for the same line, included for comparison only. It does NOT alter
   `pmf_json`.
4. `model_edge_vs_market = p_over_line - market_fair_over_prob`. Positive
   means the model is more bullish than the market at that line; negative
   means more bearish.
5. **No market-beating claim is made.** The standalone calibrated model
   did not beat the de-vigged closing market in the latest matched audit.
   See `MODEL_EVALUATION_SUMMARY.md` § "What is not proven".
