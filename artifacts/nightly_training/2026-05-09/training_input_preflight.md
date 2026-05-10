# Training Input Preflight — 2026-05-09

| Field | Value |
| --- | --- |
| Generated (UTC) | 2026-05-10T16:32:47+00:00 |
| Code commit | f166d1a6520c |
| All required inputs present | yes |
| Missing required | [] |
| Missing advisory | ['data/training_table.parquet'] |
| Outcome max date | 2026-05-09 |
| Rows on/before as_of_date | 84003 |

## Required inputs

- **data/oof_pmfs.parquet** — present (`data/oof_pmfs.parquet`)
- **data/player_game_stats.parquet** — present (`data/player_game_stats.parquet`)
- **champion_pointer** — present (`artifacts/models/registry/champion_pointer.json`)
- **champion_pmf_cal_role_pts** — present (`artifacts/models/pmf_cal_role_pts.pkl`)
- **champion_pmf_cal_role_reb** — present (`artifacts/models/pmf_cal_role_reb.pkl`)
- **champion_pmf_cal_role_ast** — present (`artifacts/models/pmf_cal_role_ast.pkl`)
- **champion_pmf_cal_role_fg3m** — present (`artifacts/models/pmf_cal_role_fg3m.pkl`)
- **champion_pmf_cal_role_tov** — present (`artifacts/models/pmf_cal_role_tov.pkl`)
- **champion_pmf_cal_role_stl** — present (`artifacts/models/pmf_cal_role_stl.pkl`)
- **champion_pmf_cal_role_blk** — present (`artifacts/models/pmf_cal_role_blk.pkl`)

## Advisory inputs

- data/training_table.parquet — missing (advisory)
- data/player_availability_asof.parquet — present
- data/advanced_stats.parquet — present
