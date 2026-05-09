# Calibration A/B Report (Phase 14 Step 1)

- Generated (UTC): 2026-05-09T02:06:08+00:00
- OOF: `/Users/josephshackelford/repos/nba-player-props-model-pmf-fix/data/oof_pmfs.parquet`
- Model dir: `/Users/josephshackelford/repos/nba-player-props-model-pmf-fix/artifacts/models`
- Rows scored per mode: 77,730

## Recommendation: **PROMOTE_ROLE_AWARE**

**Reason:** role_aware NLL 2.1855 beats legacy 2.1907 by +0.0053

## Overall metrics

| mode | n | NLL | RPS | p0_err | mean_bias |
|---|---:|---:|---:|---:|---:|
| raw | 77,730 | 2.2370 | 1.3717 | 0.2860 | -0.2169 |
| global_only | 77,730 | 2.1907 | 1.3459 | 0.2710 | -0.1295 |
| role_aware | 77,730 | 2.1855 | 1.3432 | 0.2709 | -0.1180 |

## By stat

| key | mode | n | NLL | NLL_delta_vs_legacy |
|---|---|---:|---:|---:|
| ast | raw | 15,546 | 1.8539 | +0.0519 |
| ast | global_only | 15,546 | 1.8020 | - |
| ast | role_aware | 15,546 | 1.7984 | -0.0036 |
| fg3m | raw | 15,546 | 2.5011 | +0.0587 |
| fg3m | global_only | 15,546 | 2.4424 | - |
| fg3m | role_aware | 15,546 | 2.4422 | -0.0002 |
| pts | raw | 15,546 | 3.0781 | +0.0094 |
| pts | global_only | 15,546 | 3.0687 | - |
| pts | role_aware | 15,546 | 3.0593 | -0.0094 |
| reb | raw | 15,546 | 2.2634 | +0.0494 |
| reb | global_only | 15,546 | 2.2140 | - |
| reb | role_aware | 15,546 | 2.2082 | -0.0058 |
| tov | raw | 15,546 | 1.4887 | +0.0622 |
| tov | global_only | 15,546 | 1.4264 | - |
| tov | role_aware | 15,546 | 1.4192 | -0.0072 |

## By role bucket

| key | mode | n | NLL | NLL_delta_vs_legacy |
|---|---|---:|---:|---:|
| bench | raw | 13,115 | 2.0954 | +0.0325 |
| bench | global_only | 13,115 | 2.0629 | - |
| bench | role_aware | 13,115 | 2.0604 | -0.0025 |
| core | raw | 21,080 | 2.2765 | +0.0534 |
| core | global_only | 21,080 | 2.2231 | - |
| core | role_aware | 21,080 | 2.2182 | -0.0049 |
| fringe | raw | 4,680 | 1.8794 | +0.0208 |
| fringe | global_only | 4,680 | 1.8586 | - |
| fringe | role_aware | 4,680 | 1.8468 | -0.0118 |
| inactive_risk | raw | 4,610 | 2.4864 | +0.0473 |
| inactive_risk | global_only | 4,610 | 2.4391 | - |
| inactive_risk | role_aware | 4,610 | 2.4261 | -0.0131 |
| rotation | raw | 18,590 | 2.1370 | +0.0459 |
| rotation | global_only | 18,590 | 2.0911 | - |
| rotation | role_aware | 18,590 | 2.0890 | -0.0021 |
| starter | raw | 15,655 | 2.4548 | +0.0561 |
| starter | global_only | 15,655 | 2.3987 | - |
| starter | role_aware | 15,655 | 2.3910 | -0.0076 |

## By line bin (predicted-median quartile proxy)

| key | mode | n | NLL | NLL_delta_vs_legacy |
|---|---|---:|---:|---:|
| high | raw | 834 | 3.2059 | +0.0479 |
| high | global_only | 834 | 3.1581 | - |
| high | role_aware | 834 | 3.1480 | -0.0100 |
| low | raw | 51,025 | 2.0437 | +0.0419 |
| low | global_only | 51,025 | 2.0018 | - |
| low | role_aware | 51,025 | 1.9965 | -0.0053 |
| mid_high | raw | 5,754 | 2.8867 | +0.0460 |
| mid_high | global_only | 5,754 | 2.8408 | - |
| mid_high | role_aware | 5,754 | 2.8332 | -0.0075 |
| mid_low | raw | 20,117 | 2.5015 | +0.0576 |
| mid_low | global_only | 20,117 | 2.4439 | - |
| mid_low | role_aware | 20,117 | 2.4397 | -0.0042 |

## By role x line bin

| key | mode | n | NLL | NLL_delta_vs_legacy |
|---|---|---:|---:|---:|
| bench|low | raw | 12,643 | 2.0865 | +0.0303 |
| bench|low | global_only | 12,643 | 2.0563 | - |
| bench|low | role_aware | 12,643 | 2.0535 | -0.0027 |
| bench|mid_high | raw | 1 | 1.9981 | +0.2677 |
| bench|mid_high | global_only | 1 | 1.7304 | - |
| bench|mid_high | role_aware | 1 | 1.7034 | -0.0270 |
| bench|mid_low | raw | 471 | 2.3348 | +0.0934 |
| bench|mid_low | global_only | 471 | 2.2414 | - |
| bench|mid_low | role_aware | 471 | 2.2461 | +0.0047 |
| core|high | raw | 98 | 2.9283 | +0.0484 |
| core|high | global_only | 98 | 2.8799 | - |
| core|high | role_aware | 98 | 2.8808 | +0.0009 |
| core|low | raw | 10,905 | 1.9117 | +0.0557 |
| core|low | global_only | 10,905 | 1.8561 | - |
| core|low | role_aware | 10,905 | 1.8510 | -0.0051 |
| core|mid_high | raw | 1,532 | 2.8544 | +0.0544 |
| core|mid_high | global_only | 1,532 | 2.8000 | - |
| core|mid_high | role_aware | 1,532 | 2.7939 | -0.0061 |
| core|mid_low | raw | 8,545 | 2.6309 | +0.0504 |
| core|mid_low | global_only | 8,545 | 2.5805 | - |
| core|mid_low | role_aware | 8,545 | 2.5761 | -0.0044 |
| fringe|low | raw | 4,659 | 1.8789 | +0.0197 |
| fringe|low | global_only | 4,659 | 1.8593 | - |
| fringe|low | role_aware | 4,659 | 1.8470 | -0.0122 |
| fringe|mid_low | raw | 21 | 1.9915 | +0.2679 |
| fringe|mid_low | global_only | 21 | 1.7235 | - |
| fringe|mid_low | role_aware | 21 | 1.7974 | +0.0739 |
| inactive_risk|high | raw | 2 | 1.3956 | -0.0270 |
| inactive_risk|high | global_only | 2 | 1.4226 | - |
| inactive_risk|high | role_aware | 2 | 1.3389 | -0.0836 |
| inactive_risk|low | raw | 4,310 | 2.5007 | +0.0460 |
| inactive_risk|low | global_only | 4,310 | 2.4547 | - |
| inactive_risk|low | role_aware | 4,310 | 2.4392 | -0.0155 |
| inactive_risk|mid_high | raw | 41 | 2.0580 | +0.0536 |
| inactive_risk|mid_high | global_only | 41 | 2.0043 | - |
| inactive_risk|mid_high | role_aware | 41 | 2.0473 | +0.0429 |
| inactive_risk|mid_low | raw | 257 | 2.3231 | +0.0672 |
| inactive_risk|mid_low | global_only | 257 | 2.2559 | - |
| inactive_risk|mid_low | role_aware | 257 | 2.2745 | +0.0186 |
| rotation|low | raw | 15,119 | 2.0479 | +0.0430 |
| rotation|low | global_only | 15,119 | 2.0049 | - |
| rotation|low | role_aware | 15,119 | 2.0025 | -0.0024 |
| rotation|mid_high | raw | 208 | 2.6299 | +0.0848 |
| rotation|mid_high | global_only | 208 | 2.5451 | - |
| rotation|mid_high | role_aware | 208 | 2.5443 | -0.0007 |
| rotation|mid_low | raw | 3,263 | 2.5185 | +0.0571 |
| rotation|mid_low | global_only | 3,263 | 2.4614 | - |
| rotation|mid_low | role_aware | 3,263 | 2.4608 | -0.0006 |
| starter|high | raw | 734 | 3.2479 | +0.0480 |
| starter|high | global_only | 734 | 3.1999 | - |
| starter|high | role_aware | 734 | 3.1886 | -0.0113 |
| starter|low | raw | 3,389 | 1.9350 | +0.0615 |
| starter|low | global_only | 3,389 | 1.8735 | - |
| starter|low | role_aware | 3,389 | 1.8670 | -0.0065 |
| starter|mid_high | raw | 3,972 | 2.9214 | +0.0406 |
| starter|mid_high | global_only | 3,972 | 2.8809 | - |
| starter|mid_high | role_aware | 3,972 | 2.8719 | -0.0089 |
| starter|mid_low | raw | 7,560 | 2.3656 | +0.0627 |
| starter|mid_low | global_only | 7,560 | 2.3029 | - |
| starter|mid_low | role_aware | 7,560 | 2.2958 | -0.0071 |

## By stat x role

| key | mode | n | NLL | NLL_delta_vs_legacy |
|---|---|---:|---:|---:|
| ast|bench | raw | 2,623 | 1.4436 | +0.0375 |
| ast|bench | global_only | 2,623 | 1.4061 | - |
| ast|bench | role_aware | 2,623 | 1.4073 | +0.0012 |
| ast|core | raw | 4,216 | 2.0074 | +0.0576 |
| ast|core | global_only | 4,216 | 1.9498 | - |
| ast|core | role_aware | 4,216 | 1.9460 | -0.0038 |
| ast|fringe | raw | 936 | 1.1615 | +0.0211 |
| ast|fringe | global_only | 936 | 1.1404 | - |
| ast|fringe | role_aware | 936 | 1.1471 | +0.0067 |
| ast|inactive_risk | raw | 922 | 2.0929 | +0.0502 |
| ast|inactive_risk | global_only | 922 | 2.0426 | - |
| ast|inactive_risk | role_aware | 922 | 2.0221 | -0.0206 |
| ast|rotation | raw | 3,718 | 1.7635 | +0.0504 |
| ast|rotation | global_only | 3,718 | 1.7131 | - |
| ast|rotation | role_aware | 3,718 | 1.7135 | +0.0004 |
| ast|starter | raw | 3,131 | 2.2349 | +0.0676 |
| ast|starter | global_only | 3,131 | 2.1673 | - |
| ast|starter | role_aware | 3,131 | 2.1568 | -0.0104 |
| fg3m|bench | raw | 2,623 | 3.1481 | +0.0459 |
| fg3m|bench | global_only | 2,623 | 3.1022 | - |
| fg3m|bench | role_aware | 2,623 | 3.1030 | +0.0008 |
| fg3m|core | raw | 4,216 | 2.1625 | +0.0658 |
| fg3m|core | global_only | 4,216 | 2.0967 | - |
| fg3m|core | role_aware | 4,216 | 2.0957 | -0.0010 |
| fg3m|fringe | raw | 936 | 3.2978 | +0.0418 |
| fg3m|fringe | global_only | 936 | 3.2560 | - |
| fg3m|fringe | role_aware | 936 | 3.2600 | +0.0040 |
| fg3m|inactive_risk | raw | 922 | 2.6907 | +0.0390 |
| fg3m|inactive_risk | global_only | 922 | 2.6516 | - |
| fg3m|inactive_risk | role_aware | 922 | 2.6642 | +0.0126 |
| fg3m|rotation | raw | 3,718 | 2.3505 | +0.0583 |
| fg3m|rotation | global_only | 3,718 | 2.2922 | - |
| fg3m|rotation | role_aware | 3,718 | 2.2886 | -0.0036 |
| fg3m|starter | raw | 3,131 | 2.3001 | +0.0711 |
| fg3m|starter | global_only | 3,131 | 2.2290 | - |
| fg3m|starter | role_aware | 3,131 | 2.2278 | -0.0012 |
| pts|bench | raw | 2,623 | 2.6815 | +0.0037 |
| pts|bench | global_only | 2,623 | 2.6777 | - |
| pts|bench | role_aware | 2,623 | 2.6630 | -0.0147 |
| pts|core | raw | 4,216 | 3.2426 | +0.0103 |
| pts|core | global_only | 4,216 | 3.2323 | - |
| pts|core | role_aware | 4,216 | 3.2269 | -0.0054 |
| pts|fringe | raw | 936 | 2.2504 | -0.0066 |
| pts|fringe | global_only | 936 | 2.2571 | - |
| pts|fringe | role_aware | 936 | 2.2019 | -0.0551 |
| pts|inactive_risk | raw | 922 | 3.3461 | +0.0359 |
| pts|inactive_risk | global_only | 922 | 3.3102 | - |
| pts|inactive_risk | role_aware | 922 | 3.3172 | +0.0070 |
| pts|rotation | raw | 3,718 | 2.9883 | +0.0086 |
| pts|rotation | global_only | 3,718 | 2.9798 | - |
| pts|rotation | role_aware | 3,718 | 2.9772 | -0.0025 |
| pts|starter | raw | 3,131 | 3.4639 | +0.0108 |
| pts|starter | global_only | 3,131 | 3.4531 | - |
| pts|starter | role_aware | 3,131 | 3.4435 | -0.0096 |
| reb|bench | raw | 2,623 | 2.0674 | +0.0271 |
| reb|bench | global_only | 2,623 | 2.0403 | - |
| reb|bench | role_aware | 2,623 | 2.0419 | +0.0016 |
| reb|core | raw | 4,216 | 2.3466 | +0.0595 |
| reb|core | global_only | 4,216 | 2.2871 | - |
| reb|core | role_aware | 4,216 | 2.2823 | -0.0048 |
| reb|fringe | raw | 936 | 1.7268 | +0.0179 |
| reb|fringe | global_only | 936 | 1.7089 | - |
| reb|fringe | role_aware | 936 | 1.7059 | -0.0030 |
| reb|inactive_risk | raw | 922 | 2.6220 | +0.0434 |
| reb|inactive_risk | global_only | 922 | 2.5786 | - |
| reb|inactive_risk | role_aware | 922 | 2.5246 | -0.0540 |
| reb|rotation | raw | 3,718 | 2.2217 | +0.0485 |
| reb|rotation | global_only | 3,718 | 2.1732 | - |
| reb|rotation | role_aware | 3,718 | 2.1732 | +0.0000 |
| reb|starter | raw | 3,131 | 2.4201 | +0.0669 |
| reb|starter | global_only | 3,131 | 2.3531 | - |
| reb|starter | role_aware | 3,131 | 2.3462 | -0.0070 |
| tov|bench | raw | 2,623 | 1.1366 | +0.0484 |
| tov|bench | global_only | 2,623 | 1.0882 | - |
| tov|bench | role_aware | 2,623 | 1.0869 | -0.0013 |
| tov|core | raw | 4,216 | 1.6234 | +0.0739 |
| tov|core | global_only | 4,216 | 1.5495 | - |
| tov|core | role_aware | 4,216 | 1.5401 | -0.0094 |
| tov|fringe | raw | 936 | 0.9606 | +0.0298 |
| tov|fringe | global_only | 936 | 0.9309 | - |
| tov|fringe | role_aware | 936 | 0.9191 | -0.0117 |
| tov|inactive_risk | raw | 922 | 1.6804 | +0.0677 |
| tov|inactive_risk | global_only | 922 | 1.6127 | - |
| tov|inactive_risk | role_aware | 922 | 1.6022 | -0.0105 |
| tov|rotation | raw | 3,718 | 1.3612 | +0.0639 |
| tov|rotation | global_only | 3,718 | 1.2973 | - |
| tov|rotation | role_aware | 3,718 | 1.2927 | -0.0046 |
| tov|starter | raw | 3,131 | 1.8549 | +0.0642 |
| tov|starter | global_only | 3,131 | 1.7907 | - |
| tov|starter | role_aware | 3,131 | 1.7807 | -0.0100 |

## Thresholds applied
- starter regression: > 0.005 NLL
- low-volume bucket bleed: > 0.02 NLL
- overall improvement: < -0.001 NLL
- min n for conclusion: 500

## Evidence
```json
{
  "overall_delta": -0.005258748279104886,
  "starter_delta": -0.007644636846144692,
  "n_total": 77730,
  "vs_raw_delta": -0.051581341646226075
}
```

