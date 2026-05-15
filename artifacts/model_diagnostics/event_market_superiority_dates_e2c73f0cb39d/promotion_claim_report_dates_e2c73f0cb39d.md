# Promotion Claim Report — dates_e2c73f0cb39d

**Overall promotion status:** `valid_pmf_not_event_market_superior`
**Market superiority claim allowed:** NO
**Sign convention:** `event_logloss_delta = model − market` (NEGATIVE deltas mean the model is better)
**Promotion gate:** `mean(delta) + z·SE ≤ −tau` (tau=0.0, z=1.96, min_n=30)
**Input:** `artifacts/model_diagnostics/event_market_loss_rows_dates_e2c73f0cb39d.parquet`

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
| ast|core | 194 | 0.015859927003604217 | 0.056649192244496084 | 0.006771309085103988 | `valid_pmf_not_event_market_superior` |
| ast|fringe | 4 | 1.4692359738184888 | None | 0.4665176740045946 | `valid_pmf_not_event_market_superior` |
| ast|inactive_risk | 20 | 0.2968518601410507 | 0.5711576166386536 | 0.12826582119467408 | `valid_pmf_not_event_market_superior` |
| ast|rotation | 81 | 0.10521315702748636 | 0.17610022287221408 | 0.045943676707503926 | `valid_pmf_not_event_market_superior` |
| ast|starter | 193 | 0.00316366702876744 | 0.05344948460017914 | 0.0018265674006798414 | `valid_pmf_not_event_market_superior` |
| ast|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| blk|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| fg3m|bench | 23 | 0.3963799768359099 | 0.5785304485369832 | 0.16044453131274358 | `valid_pmf_not_event_market_superior` |
| fg3m|core | 174 | 0.019632315371738335 | 0.05892868894973806 | 0.008755242412420695 | `valid_pmf_not_event_market_superior` |
| fg3m|fringe | 11 | 0.12482693166866023 | 0.31076308726273194 | 0.047916387419713914 | `valid_pmf_not_event_market_superior` |
| fg3m|inactive_risk | 17 | -0.025405540183112134 | 0.14140022176799072 | -0.005415218415424007 | `valid_pmf_not_event_market_superior` |
| fg3m|rotation | 96 | 0.004903320472864985 | 0.05703078090566103 | 0.008829091280132033 | `valid_pmf_not_event_market_superior` |
| fg3m|starter | 181 | 0.03592496837917551 | 0.07977124027916363 | 0.01138728693010015 | `valid_pmf_not_event_market_superior` |
| fg3m|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pa|core | 140 | -0.039408267816282844 | 0.01865366567252571 | -0.01543117448501663 | `valid_pmf_not_event_market_superior` |
| pa|fringe | 1 | -0.5616641415876213 | None | -0.22243394697518615 | `valid_pmf_not_event_market_superior` |
| pa|rotation | 39 | 0.032720517870476314 | 0.12621497628183148 | 0.01565816332045032 | `valid_pmf_not_event_market_superior` |
| pa|starter | 150 | 0.08167087444374291 | 0.1426497603251428 | 0.04017841709222858 | `valid_pmf_not_event_market_superior` |
| pa|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pr|bench | 5 | 0.0056752303088611015 | 0.09773201549790292 | 0.001589565301955792 | `valid_pmf_not_event_market_superior` |
| pr|core | 219 | -0.012287347425382834 | 0.028829633800816063 | -0.0038318848277268222 | `valid_pmf_not_event_market_superior` |
| pr|fringe | 7 | -0.4684930434203096 | 0.011291236663220239 | -0.1794703345940749 | `valid_pmf_not_event_market_superior` |
| pr|rotation | 59 | 0.05913308326574985 | 0.12055799710995505 | 0.02664986657113816 | `valid_pmf_not_event_market_superior` |
| pr|starter | 173 | 0.08476028040940557 | 0.1392962637222019 | 0.03949394119275409 | `valid_pmf_not_event_market_superior` |
| pr|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pra|bench | 5 | -0.05003800697171882 | 0.07621301431689823 | -0.02481868301986786 | `valid_pmf_not_event_market_superior` |
| pra|core | 217 | -0.01588468763341626 | 0.03045310670165883 | -0.007583467246698289 | `valid_pmf_not_event_market_superior` |
| pra|fringe | 4 | -0.37167775863774893 | None | -0.13191917619465676 | `valid_pmf_not_event_market_superior` |
| pra|rotation | 73 | 0.023521900301397624 | 0.09406129354270842 | 0.011524669301012218 | `valid_pmf_not_event_market_superior` |
| pra|starter | 226 | 0.06582143339499202 | 0.12159831271328861 | 0.03002080145941057 | `valid_pmf_not_event_market_superior` |
| pra|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pts|bench | 69 | 0.01716613806787755 | 0.050909234882796583 | 0.008460267170776744 | `valid_pmf_not_event_market_superior` |
| pts|core | 431 | 0.0500052769255567 | 0.08123337131764019 | 0.02354172244073476 | `valid_pmf_not_event_market_superior` |
| pts|fringe | 36 | -0.2853718620927879 | -0.09715524826064323 | -0.1141379356707046 | `market_superior_event_accuracy_and_calibration` |
| pts|inactive_risk | 24 | 0.1861058970658347 | 0.43274707939083357 | 0.08373186086408962 | `valid_pmf_not_event_market_superior` |
| pts|rotation | 183 | -0.04676995578171317 | -0.013678709535527134 | -0.021946053243993572 | `market_superior_event_accuracy_and_calibration` |
| pts|starter | 348 | 0.11724065754353168 | 0.1526943510480429 | 0.05411028086356383 | `valid_pmf_not_event_market_superior` |
| pts|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| ra|core | 106 | 0.014887076341998194 | 0.08937406783490644 | 0.01103463656537447 | `valid_pmf_not_event_market_superior` |
| ra|fringe | 1 | -0.7026858078732089 | None | -0.2736037591735384 | `valid_pmf_not_event_market_superior` |
| ra|rotation | 28 | 0.1932005318382101 | 0.30295755818007464 | 0.08887008116930258 | `valid_pmf_not_event_market_superior` |
| ra|starter | 94 | -0.015980652108997708 | 0.07130330048176416 | -0.008395763776205187 | `valid_pmf_not_event_market_superior` |
| ra|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| reb|bench | 40 | -0.07890785670630818 | -0.010572204595951248 | -0.038553209568229815 | `market_superior_event_accuracy_and_calibration` |
| reb|core | 274 | 0.022141799045465798 | 0.06404038795877269 | 0.007284610865933804 | `valid_pmf_not_event_market_superior` |
| reb|fringe | 25 | 0.1255470711590982 | 0.5119062261004328 | 0.042812411715028045 | `valid_pmf_not_event_market_superior` |
| reb|inactive_risk | 16 | 0.2518639801444936 | 0.6425812287166023 | 0.09166741668191208 | `valid_pmf_not_event_market_superior` |
| reb|rotation | 112 | 0.12534462958381007 | 0.17590137089242788 | 0.05913402231075553 | `valid_pmf_not_event_market_superior` |
| reb|starter | 211 | -0.021779170148513726 | 0.0166872381391262 | -0.012733172292398029 | `valid_pmf_not_event_market_superior` |
| reb|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| stl|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| tov|starter | 1 | 0.3234371927767852 | None | 0.15428110464571487 | `valid_pmf_not_event_market_superior` |
| tov|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
