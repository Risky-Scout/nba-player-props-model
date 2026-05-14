# Promotion Claim Report — 2026-05-07_2026-05-12

**Overall promotion status:** `valid_pmf_not_event_market_superior`
**Market superiority claim allowed:** NO
**Sign convention:** `event_logloss_delta = model − market` (NEGATIVE deltas mean the model is better)
**Promotion gate:** `mean(delta) + z·SE ≤ −tau` (tau=0.0, z=1.96, min_n=30)
**Input:** `artifacts/model_diagnostics/event_market_loss_rows_2026-05-07_2026-05-12.parquet`

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
| ast|bench | 14 | 0.05099616717648953 | 0.14049245914213357 | 0.026169444079110697 | `valid_pmf_not_event_market_superior` |
| ast|core | 94 | 0.08165359766004888 | 0.1328551157883532 | 0.037589754241743906 | `valid_pmf_not_event_market_superior` |
| ast|fringe | 4 | 1.4692359738184888 | None | 0.4665176740045946 | `valid_pmf_not_event_market_superior` |
| ast|inactive_risk | 20 | 0.2968518601410507 | 0.5711576166386536 | 0.12826582119467408 | `valid_pmf_not_event_market_superior` |
| ast|rotation | 51 | 0.03172511247903825 | 0.1139263235524219 | 0.010601423923674216 | `valid_pmf_not_event_market_superior` |
| ast|starter | 97 | -0.04932840767316962 | 0.010443744053583476 | -0.02393137249108879 | `valid_pmf_not_event_market_superior` |
| ast|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| fg3m|bench | 23 | 0.3963799768359099 | 0.5785304485369832 | 0.16044453131274358 | `valid_pmf_not_event_market_superior` |
| fg3m|core | 77 | -0.03614713414761934 | 0.006144513508255775 | -0.014287321866643032 | `valid_pmf_not_event_market_superior` |
| fg3m|fringe | 9 | 0.0827844132460786 | 0.30207496257732036 | 0.024002441053300558 | `valid_pmf_not_event_market_superior` |
| fg3m|inactive_risk | 17 | -0.025405540183112134 | 0.14140022176799072 | -0.005415218415424007 | `valid_pmf_not_event_market_superior` |
| fg3m|rotation | 61 | -0.04795091272964312 | 0.0017116740595066668 | -0.017725609821695396 | `valid_pmf_not_event_market_superior` |
| fg3m|starter | 94 | 0.07312947760730618 | 0.13671001036789135 | 0.028874392629166554 | `valid_pmf_not_event_market_superior` |
| fg3m|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pts|bench | 43 | -0.019072287042485793 | 0.029653085895855413 | -0.0089605828709417 | `valid_pmf_not_event_market_superior` |
| pts|core | 140 | 0.15618880512486313 | 0.2207215881213886 | 0.07074877589257157 | `valid_pmf_not_event_market_superior` |
| pts|fringe | 12 | -0.3467884711156561 | -0.11017197979053125 | -0.13405464504786013 | `valid_pmf_not_event_market_superior` |
| pts|inactive_risk | 24 | 0.1861058970658347 | 0.43274707939083357 | 0.08373186086408962 | `valid_pmf_not_event_market_superior` |
| pts|rotation | 78 | -0.03641613545256016 | 0.019819616234081808 | -0.01672869381191419 | `valid_pmf_not_event_market_superior` |
| pts|starter | 125 | 0.12441007846008025 | 0.185272745706853 | 0.056458690574302424 | `valid_pmf_not_event_market_superior` |
| pts|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| reb|bench | 33 | -0.08921966525375448 | -0.007514135484618753 | -0.04359169276375405 | `market_superior_event_accuracy_and_calibration` |
| reb|core | 117 | 0.07595380295702106 | 0.15096704146945028 | 0.028056580072133273 | `valid_pmf_not_event_market_superior` |
| reb|fringe | 8 | -0.4208928787417623 | -0.3151491577349996 | -0.1740893289153214 | `valid_pmf_not_event_market_superior` |
| reb|inactive_risk | 16 | 0.2518639801444936 | 0.6425812287166023 | 0.09166741668191208 | `valid_pmf_not_event_market_superior` |
| reb|rotation | 67 | 0.14828870591553056 | 0.22298031057899798 | 0.06886744401355166 | `valid_pmf_not_event_market_superior` |
| reb|starter | 104 | -0.03130624651040763 | 0.00707831648065832 | -0.014562611472918848 | `valid_pmf_not_event_market_superior` |
| reb|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| tov|starter | 1 | 0.3234371927767852 | None | 0.15428110464571487 | `valid_pmf_not_event_market_superior` |
| tov|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
