# Diagnostics report — 2026-05-29

Full-universe out-of-sample, date-respecting walk-forward diagnostics.
All metrics computed on the held-out fold for the corresponding window.

## Stat: `ast__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 3.6072 | 1.0182 | 0.383 | 0.295 | 0.170 | 0.1543 | 0.0815 | 1.088 | -0.122 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 3.7199 | 1.0398 | 0.381 | 0.303 | 0.188 | 0.1553 | 0.0740 | 1.021 | -0.083 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 3.4961 | 0.9165 | 0.373 | 0.297 | 0.197 | 0.1576 | 0.0967 | 1.206 | -0.214 | +nan | +nan |

## Stat: `ast__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 1.7757 | 0.9119 | 0.501 | 0.277 | 0.029 | 0.1507 | 0.0301 | 1.051 | -0.035 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 1.7873 | 0.9401 | 0.518 | 0.288 | 0.032 | 0.1548 | 0.0308 | 0.983 | 0.015 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 1.5546 | 0.7496 | 0.523 | 0.273 | 0.053 | 0.1453 | 0.0524 | 1.122 | -0.035 | +nan | +nan |

## Stat: `blk__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 1.2164 | 0.4212 | 0.336 | 0.254 | 0.253 | 0.2788 | 0.3082 | 0.941 | -0.272 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 1.2521 | 0.4182 | 0.343 | 0.256 | 0.253 | 0.2742 | 0.3034 | 0.937 | -0.266 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 1.2943 | 0.4307 | 0.326 | 0.244 | 0.283 | 0.2740 | 0.3321 | 1.026 | -0.348 | +nan | +nan |

## Stat: `blk__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 0.8297 | 0.2874 | 0.515 | 0.291 | 0.026 | 0.1787 | 0.0317 | 0.904 | 0.048 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 0.8370 | 0.2975 | 0.519 | 0.296 | 0.038 | 0.1807 | 0.0385 | 0.922 | 0.054 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 0.7511 | 0.2672 | 0.477 | 0.284 | 0.047 | 0.1520 | 0.0334 | 1.018 | -0.034 | +nan | +nan |

## Stat: `fg3m__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 2.8616 | 0.7353 | 0.341 | 0.286 | 0.245 | 0.1806 | 0.1208 | 1.007 | -0.124 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 3.0220 | 0.7372 | 0.328 | 0.289 | 0.269 | 0.1736 | 0.1205 | 0.985 | -0.114 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 2.4783 | 0.6990 | 0.329 | 0.291 | 0.276 | 0.1629 | 0.1081 | 0.979 | -0.100 | +nan | +nan |

## Stat: `fg3m__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 2.5034 | 0.6194 | 0.481 | 0.316 | 0.062 | 0.1815 | 0.0717 | 0.792 | 0.040 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 2.5487 | 0.6141 | 0.476 | 0.320 | 0.080 | 0.1751 | 0.0661 | 0.776 | 0.040 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 2.5509 | 0.5508 | 0.481 | 0.315 | 0.063 | 0.1627 | 0.0515 | 0.828 | 0.031 | +nan | +nan |

## Stat: `pts__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 4.2693 | 3.2227 | 0.462 | 0.289 | 0.077 | 0.1510 | 0.0404 | 1.128 | -0.083 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 4.3586 | 3.2967 | 0.460 | 0.297 | 0.077 | 0.1578 | 0.0270 | 1.064 | -0.051 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 4.9075 | 2.9945 | 0.450 | 0.294 | 0.081 | 0.1182 | 0.0632 | 1.181 | -0.124 | +nan | +nan |

## Stat: `pts__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 3.0651 | 3.2015 | 0.519 | 0.291 | 0.044 | 0.1591 | 0.0298 | 1.040 | 0.010 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 3.1050 | 3.4200 | 0.528 | 0.304 | 0.064 | 0.1752 | 0.0416 | 0.924 | 0.074 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 2.8151 | 2.8664 | 0.504 | 0.286 | 0.020 | 0.1195 | 0.0484 | 1.134 | -0.056 | +nan | +nan |

## Stat: `reb__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 3.6342 | 1.3184 | 0.424 | 0.291 | 0.106 | 0.1736 | 0.0633 | 1.125 | -0.126 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 3.9468 | 1.3646 | 0.419 | 0.299 | 0.118 | 0.1678 | 0.0515 | 1.141 | -0.111 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 4.4192 | 1.3445 | 0.393 | 0.301 | 0.167 | 0.1503 | 0.0747 | 1.118 | -0.128 | +nan | +nan |

## Stat: `reb__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 2.1595 | 1.2733 | 0.522 | 0.277 | 0.048 | 0.1764 | 0.0226 | 1.053 | -0.002 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 2.2032 | 1.3707 | 0.542 | 0.291 | 0.065 | 0.1832 | 0.0644 | 1.025 | 0.054 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 2.0324 | 1.2102 | 0.506 | 0.278 | 0.031 | 0.1470 | 0.0362 | 1.098 | -0.025 | +nan | +nan |

## Stat: `stl__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 1.3860 | 0.5450 | 0.341 | 0.265 | 0.246 | 0.2965 | 0.2675 | 1.581 | -0.704 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 1.3546 | 0.5447 | 0.343 | 0.267 | 0.251 | 0.3021 | 0.2769 | 1.464 | -0.621 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 1.3513 | 0.5611 | 0.332 | 0.263 | 0.281 | 0.3028 | 0.2995 | 1.678 | -0.799 | +nan | +nan |

## Stat: `stl__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 1.1708 | 0.4312 | 0.492 | 0.288 | 0.015 | 0.2204 | 0.0149 | 0.938 | 0.021 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 1.1648 | 0.4334 | 0.515 | 0.288 | 0.031 | 0.2211 | 0.0243 | 0.894 | 0.065 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 1.0908 | 0.4223 | 0.490 | 0.290 | 0.025 | 0.2036 | 0.0235 | 1.002 | -0.020 | +nan | +nan |

## Stat: `tov__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 1.9551 | 0.7039 | 0.370 | 0.284 | 0.197 | 0.2085 | 0.1389 | 1.050 | -0.163 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 1.8937 | 0.7162 | 0.363 | 0.284 | 0.222 | 0.2009 | 0.1354 | 1.003 | -0.137 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 2.5122 | 0.7426 | 0.349 | 0.288 | 0.246 | 0.1922 | 0.1537 | 0.901 | -0.108 | +nan | +nan |

## Stat: `tov__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 | 2026-04-01 | 4365 | 1.3922 | 0.5892 | 0.524 | 0.276 | 0.056 | 0.1804 | 0.0220 | 1.082 | -0.007 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 1.3684 | 0.5868 | 0.525 | 0.276 | 0.055 | 0.1740 | 0.0279 | 1.048 | 0.009 | +nan | +nan |
| 2026-04-29 | 2026-05-27 | 951 | 1.3073 | 0.5644 | 0.522 | 0.277 | 0.056 | 0.1518 | 0.0292 | 1.074 | -0.021 | +nan | +nan |

---

## New PMF path vs legacy direct-total path — aggregate

| stat | metric | legacy | new | better |
|---|---|---:|---:|---|
| ast | log_score | 3.6077 | 1.7059 | new |
| ast | crps | 0.9915 | 0.8672 | new |
| ast | pit_ks | 0.1849 | 0.0381 | new |
| ast | brier | 0.1557 | 0.1503 | new |
| ast | ece | 0.0840 | 0.0378 | new |
| blk | log_score | 1.2543 | 0.8059 | new |
| blk | crps | 0.4233 | 0.2840 | new |
| blk | pit_ks | 0.2630 | 0.0370 | new |
| blk | brier | 0.2757 | 0.1705 | new |
| blk | ece | 0.3146 | 0.0345 | new |
| fg3m | log_score | 2.7873 | 2.5343 | new |
| fg3m | crps | 0.7238 | 0.5948 | new |
| fg3m | pit_ks | 0.2634 | 0.0681 | new |
| fg3m | brier | 0.1724 | 0.1731 | legacy |
| fg3m | ece | 0.1165 | 0.0631 | new |
| pts | log_score | 4.5118 | 2.9951 | new |
| pts | crps | 3.1713 | 3.1626 | new |
| pts | pit_ks | 0.0784 | 0.0427 | new |
| pts | brier | 0.1423 | 0.1513 | legacy |
| pts | ece | 0.0435 | 0.0399 | new |
| reb | log_score | 4.0001 | 2.1317 | new |
| reb | crps | 1.3425 | 1.2847 | new |
| reb | pit_ks | 0.1303 | 0.0480 | new |
| reb | brier | 0.1639 | 0.1689 | legacy |
| reb | ece | 0.0632 | 0.0411 | new |
| stl | log_score | 1.3640 | 1.1421 | new |
| stl | crps | 0.5503 | 0.4290 | new |
| stl | pit_ks | 0.2594 | 0.0236 | new |
| stl | brier | 0.3005 | 0.2150 | new |
| stl | ece | 0.2813 | 0.0209 | new |
| tov | log_score | 2.1203 | 1.3560 | new |
| tov | crps | 0.7209 | 0.5801 | new |
| tov | pit_ks | 0.2220 | 0.0556 | new |
| tov | brier | 0.2005 | 0.1688 | new |
| tov | ece | 0.1427 | 0.0264 | new |

## Per-stat verdict

- **ast**: new wins 5 / legacy wins 0 / ties 0. new path passes
- **blk**: new wins 5 / legacy wins 0 / ties 0. new path passes
- **fg3m**: new wins 4 / legacy wins 1 / ties 0. new path passes
- **pts**: new wins 4 / legacy wins 1 / ties 0. new path passes
- **reb**: new wins 4 / legacy wins 1 / ties 0. new path passes
- **stl**: new wins 5 / legacy wins 0 / ties 0. new path passes
- **tov**: new wins 5 / legacy wins 0 / ties 0. new path passes

---

## Role-aware PMF diagnostics by stat × role_bucket

_Diagnostics use active-conditioned PMFs (`pmf_active`) when the OOF parquet carries that column; otherwise fall back to raw `pmf`. Calibrators are fit on the same source._

Evaluated role buckets: bench, core, fringe, inactive_risk, rotation, starter; rows: 55,671

| stat | role_bucket | n | log_score | CRPS | PIT mean | PIT std | PIT KS | ECE |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ast | bench | 1379 | 1.4156 | 0.6504 | 0.5234 | 0.2897 | 0.0407 | 0.0333 |
| ast | core | 2098 | 1.9619 | 1.0375 | 0.4913 | 0.2703 | 0.0453 | 0.0421 |
| ast | fringe | 607 | 1.1559 | 0.5068 | 0.5307 | 0.2871 | 0.0655 | 0.0552 |
| ast | inactive_risk | 593 | 1.4245 | 0.7092 | 0.5493 | 0.2975 | 0.0750 | 0.0764 |
| ast | rotation | 1940 | 1.7494 | 0.8528 | 0.5047 | 0.2782 | 0.0336 | 0.0155 |
| ast | starter | 1336 | 2.1964 | 1.2845 | 0.4995 | 0.2756 | 0.0325 | 0.0290 |
| blk | bench | 1379 | 0.6801 | 0.2324 | 0.5059 | 0.2982 | 0.0361 | 0.0351 |
| blk | core | 2098 | 0.9497 | 0.3409 | 0.5098 | 0.3009 | 0.0359 | 0.0421 |
| blk | fringe | 607 | 0.4443 | 0.1326 | 0.4854 | 0.2853 | 0.0342 | 0.0396 |
| blk | inactive_risk | 593 | 0.6554 | 0.2161 | 0.5089 | 0.2953 | 0.0358 | 0.0351 |
| blk | rotation | 1940 | 0.8959 | 0.3068 | 0.5280 | 0.2960 | 0.0540 | 0.0510 |
| blk | starter | 1336 | 0.9105 | 0.3394 | 0.5002 | 0.2916 | 0.0117 | 0.0203 |
| fg3m | bench | 1379 | 2.8483 | 0.4979 | 0.4812 | 0.3187 | 0.0753 | 0.1432 |
| fg3m | core | 2098 | 2.3715 | 0.7227 | 0.4794 | 0.3158 | 0.0675 | 0.0698 |
| fg3m | fringe | 607 | 2.7764 | 0.3108 | 0.4702 | 0.3196 | 0.1008 | 0.1970 |
| fg3m | inactive_risk | 593 | 3.5709 | 0.4507 | 0.5325 | 0.3176 | 0.1079 | 0.1756 |
| fg3m | rotation | 1940 | 2.2699 | 0.5924 | 0.4671 | 0.3143 | 0.0821 | 0.0826 |
| fg3m | starter | 1336 | 2.2190 | 0.7776 | 0.4871 | 0.3069 | 0.0493 | 0.0252 |
| pts | bench | 1379 | 2.7701 | 2.6901 | 0.5187 | 0.3066 | 0.0550 | 0.0452 |
| pts | core | 2098 | 3.2934 | 3.7334 | 0.5185 | 0.2873 | 0.0389 | 0.0263 |
| pts | fringe | 607 | 2.2391 | 1.8863 | 0.4766 | 0.3145 | 0.1196 | 0.0120 |
| pts | inactive_risk | 593 | 2.7586 | 2.4976 | 0.5393 | 0.3120 | 0.1084 | 0.0839 |
| pts | rotation | 1940 | 3.0635 | 3.1274 | 0.5361 | 0.2895 | 0.0632 | 0.0441 |
| pts | starter | 1336 | 3.4255 | 4.1044 | 0.5136 | 0.2781 | 0.0317 | 0.0301 |
| reb | bench | 1379 | 2.0479 | 1.2253 | 0.5319 | 0.2890 | 0.0491 | 0.0417 |
| reb | core | 2098 | 2.2795 | 1.3794 | 0.5182 | 0.2733 | 0.0517 | 0.0291 |
| reb | fringe | 607 | 1.6741 | 0.9294 | 0.5176 | 0.2964 | 0.0382 | 0.0437 |
| reb | inactive_risk | 593 | 1.8700 | 1.0604 | 0.5707 | 0.2937 | 0.1177 | 0.0967 |
| reb | rotation | 1940 | 2.1919 | 1.2946 | 0.5305 | 0.2832 | 0.0497 | 0.0419 |
| reb | starter | 1336 | 2.3842 | 1.5234 | 0.5126 | 0.2769 | 0.0392 | 0.0192 |
| stl | bench | 1379 | 0.9437 | 0.3394 | 0.5049 | 0.2875 | 0.0224 | 0.0353 |
| stl | core | 2098 | 1.3208 | 0.5090 | 0.4928 | 0.2857 | 0.0185 | 0.0262 |
| stl | fringe | 607 | 0.7129 | 0.2316 | 0.4934 | 0.2873 | 0.0221 | 0.0426 |
| stl | inactive_risk | 593 | 0.8307 | 0.2865 | 0.5010 | 0.2849 | 0.0363 | 0.0229 |
| stl | rotation | 1940 | 1.1836 | 0.4279 | 0.5073 | 0.2876 | 0.0246 | 0.0365 |
| stl | starter | 1336 | 1.4412 | 0.5615 | 0.4981 | 0.2938 | 0.0278 | 0.0243 |
| tov | bench | 1379 | 1.0960 | 0.4332 | 0.5294 | 0.2824 | 0.0610 | 0.0634 |
| tov | core | 2098 | 1.5583 | 0.6762 | 0.5335 | 0.2671 | 0.0866 | 0.0436 |
| tov | fringe | 607 | 0.8685 | 0.3292 | 0.5236 | 0.2947 | 0.0497 | 0.0335 |
| tov | inactive_risk | 593 | 1.1039 | 0.4421 | 0.5601 | 0.2873 | 0.0927 | 0.1075 |
| tov | rotation | 1940 | 1.3315 | 0.5515 | 0.5181 | 0.2766 | 0.0506 | 0.0210 |
| tov | starter | 1336 | 1.7837 | 0.8292 | 0.5094 | 0.2585 | 0.0688 | 0.0440 |

---

## Market evaluation status

**Market-relative evaluation unavailable: no matched de-vigged market probabilities found.**

The `logloss lift` column in the per-stat tables above is emitted as `nan` because real opening-line de-vigged over/under probabilities are not currently joined onto the OOF rows. The previous code path silently substituted a constant 0.5 baseline, which produced a misleading non-zero lift. This report now flags the gap explicitly.

`market_eval_available = false`

Wiring real market data requires joining `data/opening_lines_*.json` to the OOF parquet by `(player_name, game_date, stat, line)`; the helpers `devigged_main_line` / `market_implied_cdf_from_alt_lines` in `src/nba_props_model/evaluation/market_baseline.py` are ready to consume that join.
