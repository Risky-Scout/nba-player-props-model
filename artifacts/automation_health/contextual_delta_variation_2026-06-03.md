# Contextual delta variation audit — 2026-06-03

- snapshots: **3**
- bug_count: **0**

| game | type | rows | minutes_unique | min | max | mean | feature_variation | verdict |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 21716134 | current_live | 13 | 1 | 14.4470 | 14.4470 | 14.4470 | constant | **expected_baseline** |
| 21716134 | t_minus_25 | 13 | 1 | 14.4470 | 14.4470 | 14.4470 | constant | **expected_baseline** |
| 21716134 | close_lock | 13 | 1 | 14.4470 | 14.4470 | 14.4470 | constant | **expected_baseline** |

## Per-snapshot reason

- 21716134/current_live: no per-player feature variation visible in this snapshot — constant contextual_minutes_delta is the honest baseline; lineup_confirmed=False, BDL_lineup_rows=0
- 21716134/t_minus_25: no per-player feature variation visible in this snapshot — constant contextual_minutes_delta is the honest baseline; lineup_confirmed=False, BDL_lineup_rows=0
- 21716134/close_lock: no per-player feature variation visible in this snapshot — constant contextual_minutes_delta is the honest baseline; lineup_confirmed=False, BDL_lineup_rows=0
