# README for Derek — tonight's PMF delivery (2026-04-27, after 20:29 ET)

1. **Open `player_prop_pmfs_tonight_MODEL_ONLY.parquet` first.** That is
   the canonical file. The CSV and JSONL siblings are byte-equivalent.
2. `pmf_json` contains the full standalone-model PMF as a JSON object
   `{"k": prob, ...}` with `k` from `0` to `support_max`. Entries with
   probability ≤ 1e-9 are omitted.
3. `p_over_line` is the model probability of `stat > line` (over side),
   computed from `pmf_json`.
4. `market_fair_over_prob` is the reference de-vigged market probability
   for the same line, included for comparison only. It does NOT alter
   `pmf_json`.
5. `model_edge_vs_market = p_over_line - market_fair_over_prob`. Positive
   means the model is more bullish than the market at that line; negative
   means more bearish.
6. **No market-beating claim is made.** The standalone calibrated model
   did not beat the de-vigged closing market in the latest matched audit.
   See `MODEL_EVALUATION_SUMMARY.md` § "What is not proven".

The `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.*` files are a
separate reference bundle whose `pmf_json` IS market-tilted (CDF anchored
at the offered line). Do NOT use those to evaluate the standalone model.
