# Contextual delta variation audit — 2026-05-03

- snapshots: **2**
- bug_count: **0**

| game | type | rows | minutes_unique | min | max | mean | feature_variation | verdict |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 21682000 | current_live | 14 | 1 | 15.3781 | 15.3781 | 15.3781 | constant | **expected_baseline** |
| 21684819 | current_live | 14 | 1 | 15.3781 | 15.3781 | 15.3781 | constant | **expected_baseline** |

## Per-snapshot reason

- 21682000/current_live: no per-player feature variation visible in this snapshot — constant contextual_minutes_delta is the honest baseline; lineup_confirmed=False, BDL_lineup_rows=0
- 21684819/current_live: no per-player feature variation visible in this snapshot — constant contextual_minutes_delta is the honest baseline; lineup_confirmed=False, BDL_lineup_rows=0
