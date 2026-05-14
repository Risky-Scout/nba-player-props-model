# Promotion Claim Report — 2026-05-12

**Overall promotion status:** `valid_pmf_not_event_market_superior`
**Market superiority claim allowed:** NO
**Sign convention:** `event_logloss_delta = model − market` (NEGATIVE deltas mean the model is better)
**Promotion gate:** `mean(delta) + z·SE ≤ −tau` (tau=0.0, z=1.96, min_n=30)
**Input:** `artifacts/model_diagnostics/event_market_loss_rows_2026-05-12.parquet`

## Forbidden public copy (do NOT use in marketing):
- `accurate`
- `well calibrated`
- `well-calibrated`
- `better than market`
- `profitable`
- `lock`
- `guaranteed`
- `sharp`
- `proven edge`

## Per-bucket statuses

| Bucket | n_settled | logloss_delta_mean | logloss_delta_upper95 | brier_delta_mean | Status |
|---|---|---|---|---|---|
| ast|core | 31 | -0.011951280113720536 | 0.0592352405792067 | -0.0067670598485559015 | `valid_pmf_not_event_market_superior` |
| ast|fringe | 4 | 1.4692359738184888 | None | 0.4665176740045946 | `valid_pmf_not_event_market_superior` |
| ast|inactive_risk | 20 | 0.2968518601410507 | 0.5711576166386536 | 0.12826582119467408 | `valid_pmf_not_event_market_superior` |
| ast|rotation | 15 | 0.010232117232060793 | 0.07432346848505533 | 0.0015993097006363735 | `valid_pmf_not_event_market_superior` |
| ast|starter | 39 | -0.02540775420821717 | 0.03161868572847075 | -0.011077443117885702 | `valid_pmf_not_event_market_superior` |
| ast|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| fg3m|core | 32 | -0.13807898384132644 | -0.08745231729759834 | -0.05894528927132282 | `market_superior_event_accuracy_and_calibration` |
| fg3m|fringe | 4 | -0.08204411123567151 | None | -0.039469804880502626 | `valid_pmf_not_event_market_superior` |
| fg3m|inactive_risk | 17 | -0.025405540183112134 | 0.14140022176799072 | -0.005415218415424007 | `valid_pmf_not_event_market_superior` |
| fg3m|rotation | 14 | 0.060352397073591524 | 0.18018623080427132 | 0.031407464681952074 | `valid_pmf_not_event_market_superior` |
| fg3m|starter | 30 | 0.20719336122150525 | 0.3271428967046487 | 0.09397263474120214 | `valid_pmf_not_event_market_superior` |
| fg3m|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pts|core | 45 | 0.13245156138385375 | 0.29342268943852834 | 0.054272514371737586 | `valid_pmf_not_event_market_superior` |
| pts|fringe | 9 | -0.5759838428028459 | -0.5342578606232333 | -0.23411675454542222 | `valid_pmf_not_event_market_superior` |
| pts|inactive_risk | 24 | 0.1861058970658347 | 0.43274707939083357 | 0.08373186086408962 | `valid_pmf_not_event_market_superior` |
| pts|rotation | 18 | -0.21795679691249825 | -0.14462564057473454 | -0.10388108813134483 | `valid_pmf_not_event_market_superior` |
| pts|starter | 46 | 0.18402963415195736 | 0.2920190502514283 | 0.08588063069698851 | `valid_pmf_not_event_market_superior` |
| pts|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| reb|core | 38 | 0.22754691742300556 | 0.3913158464998586 | 0.083518249963786 | `valid_pmf_not_event_market_superior` |
| reb|fringe | 8 | -0.4208928787417623 | -0.3151491577349996 | -0.1740893289153214 | `valid_pmf_not_event_market_superior` |
| reb|inactive_risk | 16 | 0.2518639801444936 | 0.6425812287166023 | 0.09166741668191208 | `valid_pmf_not_event_market_superior` |
| reb|rotation | 16 | 0.5417884229207813 | 0.5622110725386198 | 0.24753582836939575 | `valid_pmf_not_event_market_superior` |
| reb|starter | 40 | -0.02019120670636947 | 0.019356268993488374 | -0.009979089082909166 | `valid_pmf_not_event_market_superior` |
| reb|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
