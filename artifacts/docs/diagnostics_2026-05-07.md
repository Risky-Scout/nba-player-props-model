# Diagnostics report — 2026-05-07

Full-universe out-of-sample, date-respecting walk-forward diagnostics.
All metrics computed on the held-out fold for the corresponding window.

## Stat: `ast__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 3.5648 | 1.0161 | 0.382 | 0.297 | 0.178 | 0.1553 | 0.0665 | 1.075 | -0.101 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 3.7483 | 1.0295 | 0.385 | 0.298 | 0.167 | 0.1663 | 0.0840 | 1.028 | -0.097 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 3.5584 | 1.0165 | 0.382 | 0.296 | 0.176 | 0.1540 | 0.0821 | 1.089 | -0.123 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 1789 | 3.5244 | 1.0784 | 0.401 | 0.305 | 0.163 | 0.1726 | 0.0620 | 0.961 | -0.045 | +nan | +nan |

## Stat: `ast__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 1.7928 | 0.8990 | 0.511 | 0.271 | 0.041 | 0.1523 | 0.0232 | 1.087 | -0.019 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 1.8044 | 0.9158 | 0.518 | 0.274 | 0.045 | 0.1595 | 0.0146 | 1.044 | -0.015 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 1.7730 | 0.9109 | 0.520 | 0.272 | 0.047 | 0.1501 | 0.0214 | 1.084 | -0.029 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 1789 | 1.8983 | 1.0326 | 0.554 | 0.287 | 0.078 | 0.1764 | 0.0466 | 0.947 | 0.061 | +nan | +nan |

## Stat: `fg3m__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 3.1703 | 0.7423 | 0.333 | 0.287 | 0.253 | 0.1750 | 0.1319 | 1.034 | -0.148 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 3.2415 | 0.7493 | 0.331 | 0.286 | 0.267 | 0.1833 | 0.1312 | 1.000 | -0.131 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 3.0516 | 0.7400 | 0.337 | 0.287 | 0.250 | 0.1806 | 0.1204 | 1.008 | -0.124 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 3.1483 | 0.7474 | 0.326 | 0.290 | 0.273 | 0.1731 | 0.1199 | 0.993 | -0.117 | +nan | +nan |

## Stat: `fg3m__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 2.4416 | 0.6109 | 0.493 | 0.313 | 0.051 | 0.1656 | 0.0463 | 0.912 | 0.008 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 2.4832 | 0.6228 | 0.488 | 0.315 | 0.056 | 0.1799 | 0.0554 | 0.828 | 0.037 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 2.4886 | 0.6117 | 0.494 | 0.315 | 0.049 | 0.1772 | 0.0528 | 0.841 | 0.040 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 2637 | 2.5337 | 0.6074 | 0.492 | 0.316 | 0.062 | 0.1714 | 0.0448 | 0.825 | 0.041 | +nan | +nan |

## Stat: `pts__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 4.2530 | 3.1240 | 0.455 | 0.287 | 0.081 | 0.1472 | 0.0382 | 1.107 | -0.070 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 4.2010 | 3.2100 | 0.463 | 0.289 | 0.081 | 0.1632 | 0.0227 | 1.063 | -0.042 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 4.3329 | 3.2258 | 0.461 | 0.290 | 0.078 | 0.1514 | 0.0359 | 1.128 | -0.084 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 1789 | 4.1751 | 3.4900 | 0.482 | 0.296 | 0.077 | 0.1727 | 0.0312 | 0.995 | 0.002 | +nan | +nan |

## Stat: `pts__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 3.0152 | 3.0644 | 0.504 | 0.282 | 0.015 | 0.1534 | 0.0274 | 1.063 | -0.011 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 3.0343 | 3.1836 | 0.516 | 0.286 | 0.030 | 0.1734 | 0.0317 | 0.993 | 0.035 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 3.0526 | 3.2082 | 0.524 | 0.287 | 0.045 | 0.1593 | 0.0332 | 1.068 | 0.000 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 1789 | 3.2046 | 3.7130 | 0.563 | 0.300 | 0.107 | 0.1957 | 0.0722 | 0.868 | 0.123 | +nan | +nan |

## Stat: `reb__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 3.5759 | 1.3739 | 0.412 | 0.291 | 0.124 | 0.1728 | 0.0702 | 1.128 | -0.141 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 3.6118 | 1.3739 | 0.420 | 0.294 | 0.112 | 0.1832 | 0.0674 | 1.075 | -0.109 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 3.6083 | 1.3177 | 0.423 | 0.293 | 0.110 | 0.1738 | 0.0626 | 1.124 | -0.125 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 1789 | 3.6467 | 1.3981 | 0.435 | 0.300 | 0.096 | 0.1763 | 0.0416 | 1.112 | -0.084 | +nan | +nan |

## Stat: `reb__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 2.1922 | 1.2999 | 0.507 | 0.273 | 0.041 | 0.1721 | 0.0287 | 1.093 | -0.033 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 2.1875 | 1.3198 | 0.512 | 0.277 | 0.037 | 0.1832 | 0.0213 | 1.034 | -0.004 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 2.1550 | 1.2691 | 0.522 | 0.273 | 0.053 | 0.1759 | 0.0274 | 1.085 | -0.015 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 1789 | 2.2629 | 1.4536 | 0.557 | 0.288 | 0.083 | 0.1984 | 0.0791 | 0.989 | 0.084 | +nan | +nan |

## Stat: `tov__legacy`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 2.0361 | 0.7102 | 0.369 | 0.282 | 0.199 | 0.2102 | 0.1522 | 1.027 | -0.166 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 2.0886 | 0.7178 | 0.382 | 0.288 | 0.176 | 0.2124 | 0.1311 | 1.038 | -0.150 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 2.0981 | 0.7036 | 0.371 | 0.285 | 0.197 | 0.2100 | 0.1412 | 1.029 | -0.155 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 1789 | 2.3913 | 0.7258 | 0.372 | 0.293 | 0.202 | 0.2125 | 0.1321 | 0.890 | -0.081 | +nan | +nan |

## Stat: `tov__new`

| fold_start | fold_end | n | log_score | CRPS | PIT mean | PIT std | PIT KS | Brier | ECE | cal slope | cal int | logloss lift | rho(edge→PnL) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-07 | 2026-02-04 | 4453 | 1.4060 | 0.5870 | 0.510 | 0.274 | 0.034 | 0.1768 | 0.0180 | 1.091 | -0.031 | +nan | +nan |
| 2026-02-04 | 2026-03-04 | 3447 | 1.4379 | 0.6109 | 0.522 | 0.276 | 0.050 | 0.1834 | 0.0228 | 1.094 | -0.020 | +nan | +nan |
| 2026-03-04 | 2026-04-01 | 4365 | 1.3798 | 0.5839 | 0.509 | 0.272 | 0.039 | 0.1791 | 0.0176 | 1.070 | -0.025 | +nan | +nan |
| 2026-04-01 | 2026-04-29 | 1789 | 1.4021 | 0.6072 | 0.514 | 0.288 | 0.035 | 0.1859 | 0.0322 | 0.941 | 0.030 | +nan | +nan |

---

## New PMF path vs legacy direct-total path — aggregate

| stat | metric | legacy | new | better |
|---|---|---:|---:|---|
| ast | log_score | 3.5990 | 1.8171 | new |
| ast | crps | 1.0352 | 0.9396 | new |
| ast | pit_ks | 0.1711 | 0.0528 | new |
| ast | brier | 0.1620 | 0.1596 | new |
| ast | ece | 0.0737 | 0.0265 | new |
| fg3m | log_score | 3.1529 | 2.4868 | new |
| fg3m | crps | 0.7448 | 0.6132 | new |
| fg3m | pit_ks | 0.2608 | 0.0547 | new |
| fg3m | brier | 0.1780 | 0.1735 | new |
| fg3m | ece | 0.1258 | 0.0498 | new |
| pts | log_score | 4.2405 | 3.0767 | new |
| pts | crps | 3.2625 | 3.2923 | legacy |
| pts | pit_ks | 0.0791 | 0.0492 | new |
| pts | brier | 0.1586 | 0.1704 | legacy |
| pts | ece | 0.0320 | 0.0411 | legacy |
| reb | log_score | 3.6107 | 2.1994 | new |
| reb | crps | 1.3659 | 1.3356 | new |
| reb | pit_ks | 0.1106 | 0.0533 | new |
| reb | brier | 0.1765 | 0.1824 | legacy |
| reb | ece | 0.0605 | 0.0391 | new |
| tov | log_score | 2.1535 | 1.4064 | new |
| tov | crps | 0.7144 | 0.5973 | new |
| tov | pit_ks | 0.1936 | 0.0395 | new |
| tov | brier | 0.2113 | 0.1813 | new |
| tov | ece | 0.1392 | 0.0226 | new |

## Per-stat verdict

- **ast**: new wins 5 / legacy wins 0 / ties 0. new path passes
- **fg3m**: new wins 5 / legacy wins 0 / ties 0. new path passes
- **pts**: new wins 2 / legacy wins 3 / ties 0. LEGACY still wins on this stat; do not activate bet selection yet
- **reb**: new wins 4 / legacy wins 1 / ties 0. new path passes
- **tov**: new wins 5 / legacy wins 0 / ties 0. new path passes

---

## Role-aware PMF diagnostics by stat × role_bucket

_Diagnostics use active-conditioned PMFs (`pmf_active`) when the OOF parquet carries that column; otherwise fall back to raw `pmf`. Calibrators are fit on the same source._

Evaluated role buckets: bench, core, fringe, inactive_risk, rotation, starter; rows: 71,118

| stat | role_bucket | n | log_score | CRPS | PIT mean | PIT std | PIT KS | ECE |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ast | bench | 2259 | 1.4542 | 0.6744 | 0.5238 | 0.2816 | 0.0479 | 0.0268 |
| ast | core | 3983 | 1.9688 | 1.0470 | 0.5177 | 0.2714 | 0.0462 | 0.0248 |
| ast | fringe | 899 | 1.1832 | 0.5292 | 0.5144 | 0.2894 | 0.0370 | 0.0608 |
| ast | inactive_risk | 967 | 1.7783 | 0.8289 | 0.5478 | 0.2884 | 0.0708 | 0.0681 |
| ast | rotation | 3626 | 1.7584 | 0.8592 | 0.5292 | 0.2725 | 0.0624 | 0.0141 |
| ast | starter | 2320 | 2.1776 | 1.2488 | 0.4992 | 0.2664 | 0.0424 | 0.0386 |
| fg3m | bench | 2478 | 2.9954 | 0.4811 | 0.4992 | 0.3168 | 0.0787 | 0.1345 |
| fg3m | core | 4172 | 2.2813 | 0.7201 | 0.4941 | 0.3135 | 0.0453 | 0.0425 |
| fg3m | fringe | 978 | 3.0043 | 0.3312 | 0.4914 | 0.3256 | 0.0913 | 0.1836 |
| fg3m | inactive_risk | 999 | 3.2132 | 0.4807 | 0.4992 | 0.3180 | 0.0881 | 0.1457 |
| fg3m | rotation | 3835 | 2.2167 | 0.5722 | 0.4802 | 0.3136 | 0.0659 | 0.0531 |
| fg3m | starter | 2440 | 2.2077 | 0.7969 | 0.4945 | 0.3103 | 0.0404 | 0.0242 |
| pts | bench | 2259 | 2.7385 | 2.6633 | 0.5196 | 0.2973 | 0.0393 | 0.0373 |
| pts | core | 3983 | 3.2499 | 3.5790 | 0.5162 | 0.2839 | 0.0298 | 0.0217 |
| pts | fringe | 899 | 2.2219 | 2.0160 | 0.5067 | 0.3060 | 0.0418 | 0.0301 |
| pts | inactive_risk | 967 | 2.9971 | 2.7306 | 0.5444 | 0.2891 | 0.0802 | 0.0823 |
| pts | rotation | 3626 | 3.0176 | 3.0012 | 0.5319 | 0.2875 | 0.0533 | 0.0497 |
| pts | starter | 2320 | 3.4377 | 4.1636 | 0.5036 | 0.2770 | 0.0273 | 0.0203 |
| reb | bench | 2259 | 2.0603 | 1.2539 | 0.5225 | 0.2851 | 0.0404 | 0.0319 |
| reb | core | 3983 | 2.2757 | 1.3902 | 0.5201 | 0.2731 | 0.0509 | 0.0217 |
| reb | fringe | 899 | 1.7249 | 0.9684 | 0.5272 | 0.2908 | 0.0502 | 0.0437 |
| reb | inactive_risk | 967 | 2.1788 | 1.1820 | 0.5442 | 0.2830 | 0.0677 | 0.0734 |
| reb | rotation | 3626 | 2.1860 | 1.2940 | 0.5238 | 0.2756 | 0.0489 | 0.0294 |
| reb | starter | 2320 | 2.3513 | 1.4663 | 0.4949 | 0.2703 | 0.0335 | 0.0213 |
| tov | bench | 2259 | 1.1209 | 0.4445 | 0.5225 | 0.2842 | 0.0456 | 0.0551 |
| tov | core | 3983 | 1.5440 | 0.6688 | 0.5034 | 0.2688 | 0.0370 | 0.0266 |
| tov | fringe | 899 | 0.9354 | 0.3557 | 0.5253 | 0.2949 | 0.0592 | 0.0496 |
| tov | inactive_risk | 967 | 1.3932 | 0.5032 | 0.5491 | 0.2778 | 0.0886 | 0.0475 |
| tov | rotation | 3626 | 1.3148 | 0.5416 | 0.5100 | 0.2765 | 0.0357 | 0.0255 |
| tov | starter | 2320 | 1.7721 | 0.8261 | 0.5042 | 0.2645 | 0.0536 | 0.0277 |

---

## Market evaluation status

**Market-relative evaluation unavailable: no matched de-vigged market probabilities found.**

The `logloss lift` column in the per-stat tables above is emitted as `nan` because real opening-line de-vigged over/under probabilities are not currently joined onto the OOF rows. The previous code path silently substituted a constant 0.5 baseline, which produced a misleading non-zero lift. This report now flags the gap explicitly.

`market_eval_available = false`

Wiring real market data requires joining `data/opening_lines_*.json` to the OOF parquet by `(player_name, game_date, stat, line)`; the helpers `devigged_main_line` / `market_implied_cdf_from_alt_lines` in `src/nba_props_model/evaluation/market_baseline.py` are ready to consume that join.
