# README for Derek — tonight's PMF delivery (2026-04-27, after 20:29 ET)

## Recommended viewing order

1. Open **`DEREK_EXECUTIVE_SUMMARY.html`** — short visual landing page.
2. Open **`DEREK_PMF_MODEL_VIEWER.html`** — full dashboard, every PMF visually inspectable.
3. Use **`player_prop_pmfs_tonight_MODEL_ONLY.parquet`** as the canonical machine-readable model output.
4. Use **`player_prop_pmfs_tonight_MODEL_ONLY_SUMMARY.csv`** for one-row-per-prop summaries (mean, median, mode, p_over_line_model, edge vs market).
5. Use **`player_prop_pmfs_tonight_MODEL_ONLY_EXPANDED.csv`** for one-row-per-outcome probability audit.

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
