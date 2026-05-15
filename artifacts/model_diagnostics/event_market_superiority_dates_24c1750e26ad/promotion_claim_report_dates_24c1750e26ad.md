# Promotion Claim Report — dates_24c1750e26ad

**Overall promotion status:** `calibrated_but_not_more_accurate_than_market`
**Market superiority claim allowed:** NO
**Sign convention:** `event_logloss_delta = model − market` (NEGATIVE deltas mean the model is better)
**Promotion gate:** `mean(delta) + z·SE ≤ −tau` (tau=0.0, z=1.96, min_n=30)
**Input:** `artifacts/model_diagnostics/event_market_loss_rows_dates_24c1750e26ad.parquet`

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
| ast|bench | 177 | 0.07889173467037937 | 0.15225431799530767 | 0.035414131668874325 | `valid_pmf_not_event_market_superior` |
| ast|core | 2064 | -0.0021458750669237953 | -0.00015776285111178704 | -0.0010793052397947657 | `market_superior_event_accuracy_and_calibration` |
| ast|fringe | 35 | 0.6523921082036156 | 0.8904040226753347 | 0.24188706290246992 | `valid_pmf_not_event_market_superior` |
| ast|inactive_risk | 77 | -0.26271594810506943 | -0.14726048039677608 | -0.11169492068918659 | `market_superior_event_accuracy_and_calibration` |
| ast|rotation | 776 | 0.06879624228034008 | 0.0924813676202858 | 0.03181989911454154 | `valid_pmf_not_event_market_superior` |
| ast|starter | 2616 | -0.014187780108366955 | -0.009765634486506341 | -0.006474337631130046 | `market_superior_event_accuracy_and_calibration` |
| ast|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| blk|bench | 6 | 0.14092378965326882 | 0.14866670316995628 | 0.06817800297109355 | `valid_pmf_not_event_market_superior` |
| blk|core | 772 | 6.319467520029734 | 6.850357220702529 | 0.23145684756546453 | `valid_pmf_not_event_market_superior` |
| blk|inactive_risk | 17 | -0.35013447223576893 | -0.26798588213008223 | -0.14879820269130992 | `valid_pmf_not_event_market_superior` |
| blk|rotation | 220 | 2.120522544196451 | 2.6841549358425154 | 0.09407519630182153 | `valid_pmf_not_event_market_superior` |
| blk|starter | 730 | 0.07499662930959035 | 0.10705644037656048 | 0.03242807048199102 | `valid_pmf_not_event_market_superior` |
| blk|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| fg3m|bench | 495 | -0.02785216912390121 | 0.02909211508262358 | -0.0209583057720103 | `calibrated_but_not_more_accurate_than_market` |
| fg3m|core | 2021 | 0.0009876847894936692 | 0.0027723570855657438 | 0.00038802552496911805 | `valid_pmf_not_event_market_superior` |
| fg3m|fringe | 45 | 0.1050511698329546 | 0.26278567282671306 | 0.04086529084977191 | `valid_pmf_not_event_market_superior` |
| fg3m|inactive_risk | 75 | -0.07433169945447826 | 0.003551591558382111 | -0.025614002987125916 | `valid_pmf_not_event_market_superior` |
| fg3m|rotation | 994 | 0.013066547204880385 | 0.03445217660849434 | 0.002288915650284132 | `valid_pmf_not_event_market_superior` |
| fg3m|starter | 2289 | 0.0015256123789544826 | 0.006927076588173731 | 0.00037857387017159916 | `valid_pmf_not_event_market_superior` |
| fg3m|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pa|bench | 153 | -0.01369419370645695 | 0.05691466699471582 | -0.006594860689104694 | `valid_pmf_not_event_market_superior` |
| pa|core | 2287 | 0.02984248852179634 | 0.040415781608554885 | 0.013956055993669647 | `valid_pmf_not_event_market_superior` |
| pa|fringe | 36 | -0.20550654598347834 | 0.10125959190475742 | -0.12062220796194073 | `calibrated_but_not_more_accurate_than_market` |
| pa|inactive_risk | 68 | 0.3736236567852568 | 0.5662631020970607 | 0.14543077538631263 | `valid_pmf_not_event_market_superior` |
| pa|rotation | 760 | 0.029687473025689 | 0.05257410338938532 | 0.013738416788502536 | `valid_pmf_not_event_market_superior` |
| pa|starter | 3113 | -0.01040228862036541 | 0.0024804890790633694 | -0.006293211455054063 | `calibrated_but_not_more_accurate_than_market` |
| pa|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pr|bench | 604 | 0.01957217449539199 | 0.05119862505861145 | 0.0055656982996061255 | `valid_pmf_not_event_market_superior` |
| pr|core | 3259 | 0.038021468713951054 | 0.047054167708253644 | 0.01777084573023825 | `valid_pmf_not_event_market_superior` |
| pr|fringe | 56 | -0.31386926929127246 | -0.12233183963939259 | -0.13297558919198374 | `market_superior_event_accuracy_and_calibration` |
| pr|inactive_risk | 69 | 0.8027837948103171 | 0.985568571945396 | 0.29443431939179737 | `valid_pmf_not_event_market_superior` |
| pr|rotation | 1288 | 0.03719358021071979 | 0.05388723336284397 | 0.016483640998462595 | `valid_pmf_not_event_market_superior` |
| pr|starter | 3372 | -0.0005379347248661997 | 0.010157914093654054 | -0.0021212627834129756 | `valid_pmf_not_event_market_superior` |
| pr|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pra|bench | 448 | 0.0396314957123755 | 0.07762118722800965 | 0.01425224551142538 | `valid_pmf_not_event_market_superior` |
| pra|core | 3793 | 0.030944321118990065 | 0.03814817122281855 | 0.01441171705946881 | `valid_pmf_not_event_market_superior` |
| pra|fringe | 55 | -0.5117472906916656 | -0.4329736191107629 | -0.21300197116078673 | `market_superior_event_accuracy_and_calibration` |
| pra|inactive_risk | 91 | 0.45809957481196373 | 0.6375418539247699 | 0.17412215751257076 | `valid_pmf_not_event_market_superior` |
| pra|rotation | 1295 | 0.03612086127244718 | 0.05404096415314981 | 0.01630690683987649 | `valid_pmf_not_event_market_superior` |
| pra|starter | 4551 | -0.0011836813276937888 | 0.01064315964707475 | -0.0033885889534738425 | `valid_pmf_not_event_market_superior` |
| pra|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| pts|bench | 1472 | 0.006180057800499245 | 0.023205422625298545 | 0.00016323458949525215 | `valid_pmf_not_event_market_superior` |
| pts|core | 4922 | 0.01037652974698691 | 0.014406132709051486 | 0.004560082962466151 | `valid_pmf_not_event_market_superior` |
| pts|fringe | 110 | -0.28406785098440707 | -0.1659467916146133 | -0.12138994016919726 | `market_superior_event_accuracy_and_calibration` |
| pts|inactive_risk | 143 | 0.14187734522922837 | 0.19957824373871175 | 0.06858205601181896 | `valid_pmf_not_event_market_superior` |
| pts|rotation | 2319 | 0.004474248543200772 | 0.01530509372140498 | 0.0013641222503518564 | `valid_pmf_not_event_market_superior` |
| pts|starter | 5214 | -0.0029270321517639443 | 0.005900225073119842 | -0.0024712277242803014 | `valid_pmf_not_event_market_superior` |
| pts|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| ra|bench | 103 | 0.22684812606818922 | 0.3336307038495412 | 0.09461062328377956 | `valid_pmf_not_event_market_superior` |
| ra|core | 1817 | 0.023653545314464983 | 0.035952142523862585 | 0.01126001058958452 | `valid_pmf_not_event_market_superior` |
| ra|fringe | 29 | 0.1524135541834261 | 0.4165494935264725 | 0.059520918370166806 | `valid_pmf_not_event_market_superior` |
| ra|inactive_risk | 46 | 0.1638856417685943 | 0.42189426772299776 | 0.05939612444018645 | `valid_pmf_not_event_market_superior` |
| ra|rotation | 623 | 0.04861302987084502 | 0.07220060686157716 | 0.022211258461430475 | `valid_pmf_not_event_market_superior` |
| ra|starter | 2175 | 0.005084454703950661 | 0.01893273546006947 | 0.0014728693333066623 | `valid_pmf_not_event_market_superior` |
| ra|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| reb|bench | 793 | 0.06921842115894013 | 0.09154832098113337 | 0.030545602420890626 | `valid_pmf_not_event_market_superior` |
| reb|core | 3154 | 0.004555086520076728 | 0.009619270906089437 | 0.0021773934283161327 | `valid_pmf_not_event_market_superior` |
| reb|fringe | 69 | 0.005232867444601801 | 0.19076086129943004 | -0.006384005981639412 | `valid_pmf_not_event_market_superior` |
| reb|inactive_risk | 70 | 0.6305460357775853 | 0.7743546370780584 | 0.2618123044583655 | `valid_pmf_not_event_market_superior` |
| reb|rotation | 1483 | -0.002096794154040946 | 0.0001281685500315868 | -0.0009454628055606467 | `valid_pmf_not_event_market_superior` |
| reb|starter | 2828 | -0.004532182937402729 | 0.0033688384947019763 | -0.0022300691642930005 | `valid_pmf_not_event_market_superior` |
| reb|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| stl|bench | 1 | 0.040980519286260564 | None | 0.020238253867966183 | `valid_pmf_not_event_market_superior` |
| stl|core | 757 | 0.17016897469445572 | 0.21155182295018501 | 0.07597816585627692 | `valid_pmf_not_event_market_superior` |
| stl|fringe | 7 | 0.45517198420262134 | 0.49035779590927786 | 0.20174273070817333 | `valid_pmf_not_event_market_superior` |
| stl|inactive_risk | 18 | -0.012987741071777224 | 0.04609283181702868 | -0.00463706890027205 | `valid_pmf_not_event_market_superior` |
| stl|rotation | 294 | 0.14331576508571583 | 0.20202789712510708 | 0.06324944471955528 | `valid_pmf_not_event_market_superior` |
| stl|starter | 783 | 0.04383394582197991 | 0.07648215977583306 | 0.01834757047033 | `valid_pmf_not_event_market_superior` |
| stl|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| stocks|core | 391 | 7.274578054613936 | 8.159032125549023 | 0.21599951829182726 | `valid_pmf_not_event_market_superior` |
| stocks|inactive_risk | 6 | 0.1819409001252609 | 0.4906139765113552 | 0.07120079209527132 | `valid_pmf_not_event_market_superior` |
| stocks|rotation | 19 | 0.00473375105771312 | 0.14170733640023686 | 0.007927211551805096 | `valid_pmf_not_event_market_superior` |
| stocks|starter | 413 | 9.539555970385978 | 10.763803275907321 | 0.17991524814045756 | `valid_pmf_not_event_market_superior` |
| stocks|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
| tov|core | 8 | 0.1595564078496889 | 0.307508427893987 | 0.07822039210281741 | `valid_pmf_not_event_market_superior` |
| tov|inactive_risk | 1 | 0.723999656445811 | None | 0.32639782774421067 | `valid_pmf_not_event_market_superior` |
| tov|starter | 31 | 0.1355968582299189 | 0.23755291468647655 | 0.06394954905367453 | `valid_pmf_not_event_market_superior` |
| tov|nan | 0 | None | None | None | `valid_pmf_not_event_market_superior` |
