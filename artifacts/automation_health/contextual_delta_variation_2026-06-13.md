# Contextual delta variation audit — 2026-06-13

- snapshots: **2**
- bug_count: **0**

| game | type | rows | minutes_unique | min | max | mean | feature_variation | verdict |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 21716138 | current_live | 15 | 1 | 14.4424 | 14.4424 | 14.4424 | constant | **expected_baseline** |
| 21716138 | t_minus_25 | 15 | 1 | 14.4424 | 14.4424 | 14.4424 | constant | **expected_baseline** |

## Per-snapshot reason

- 21716138/current_live: no per-player feature variation visible in this snapshot — constant contextual_minutes_delta is the honest baseline; lineup_confirmed=False, BDL_lineup_rows=0
- 21716138/t_minus_25: no per-player feature variation visible in this snapshot — constant contextual_minutes_delta is the honest baseline; lineup_confirmed=False, BDL_lineup_rows=0
