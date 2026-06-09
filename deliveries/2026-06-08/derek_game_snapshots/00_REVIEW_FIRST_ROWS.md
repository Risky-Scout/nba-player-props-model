# Reviewable Delivery Preview — 2026-06-08 — derek_game_snapshots

GitHub may refuse to render large CSV files. This file is intentionally small.

---

## `derek_game_snapshots/21716136/current_live/after_game_scoring.csv`

- bytes: `1,943`
- rows: `30`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,stat,line
De'Aaron Fox,161,reb,3.5
De'Aaron Fox,161,ast,5.5
Landry Shamet,414,pts,8.5
Jalen Brunson,73,pts,26.5
Josh Hart,202,reb,8.5
Josh Hart,202,ast,4.5
Stephon Castle,1028025261,ast,6.5
Stephon Castle,1028025261,stl,0.5
Devin Vassell,3547246,pts,13.5
Devin Vassell,3547246,ast,2.5
Julian Champagnie,38017649,pts,10.5
Julian Champagnie,38017649,reb,5.5
Julian Champagnie,38017649,fg3m,2.5
Dylan Harper,1057262518,pts,13.5
Dylan Harper,1057262518,reb,5.5
Dylan Harper,1057262518,ast,3.5
Dylan Harper,1057262518,fg3m,0.5
Keldon Johnson,666682,reb,2.5
Keldon Johnson,666682,fg3m,0.5
Mikal Bridges,61,reb,3.5
Mikal Bridges,61,fg3m,1.5
Victor Wembanyama,56677822,pts,27.5
Victor Wembanyama,56677822,reb,11.5
Victor Wembanyama,56677822,ast,3.5
Victor Wembanyama,56677822,stl,1.5
Victor Wembanyama,56677822,blk,3.5
Karl-Anthony Towns,447,pts,17.5
Karl-Anthony Towns,447,reb,11.5
Karl-Anthony Towns,447,fg3m,1.5
Karl-Anthony Towns,447,stl,0.5

```

---

## `derek_game_snapshots/21716136/current_live/contextual_feature_audit.csv`

- bytes: `4,092`
- rows: `12`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716136
Landry Shamet,414,NYK,21716136
Jalen Brunson,73,NYK,21716136
Josh Hart,202,NYK,21716136
Stephon Castle,1028025261,SAS,21716136
Devin Vassell,3547246,SAS,21716136
Julian Champagnie,38017649,SAS,21716136
Dylan Harper,1057262518,SAS,21716136
Keldon Johnson,666682,SAS,21716136
Mikal Bridges,61,NYK,21716136
Victor Wembanyama,56677822,SAS,21716136
Karl-Anthony Towns,447,NYK,21716136

```

---

## `derek_game_snapshots/21716136/current_live/contextual_feature_audit.parquet`

- bytes: `29,787`
- rows: `12`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716136
Landry Shamet,414,NYK,21716136
Jalen Brunson,73,NYK,21716136
Josh Hart,202,NYK,21716136
Stephon Castle,1028025261,SAS,21716136
Devin Vassell,3547246,SAS,21716136
Julian Champagnie,38017649,SAS,21716136
Dylan Harper,1057262518,SAS,21716136
Keldon Johnson,666682,SAS,21716136
Mikal Bridges,61,NYK,21716136
Victor Wembanyama,56677822,SAS,21716136
Karl-Anthony Towns,447,NYK,21716136

```

---

## `derek_game_snapshots/21716136/current_live/derek_live_predictions.parquet`

- bytes: `37,945`
- rows: `30`
- columns: `47`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1506
De'Aaron Fox,161,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.1342
Landry Shamet,414,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.5,-0.1017
Jalen Brunson,73,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,26.5,-0.0505
Josh Hart,202,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.5,-0.1172
Josh Hart,202,NYK,SAS,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.5,-0.1085
Stephon Castle,1028025261,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1475
Stephon Castle,1028025261,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.1312
Devin Vassell,3547246,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.1138
Devin Vassell,3547246,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1147
Julian Champagnie,38017649,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.5,-0.1163
Julian Champagnie,38017649,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.069
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0446
Dylan Harper,1057262518,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,13.5,-0.1324
Dylan Harper,1057262518,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.0757
Dylan Harper,1057262518,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1999
Dylan Harper,1057262518,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,0.0047
Keldon Johnson,666682,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.0994
Keldon Johnson,666682,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.257
Mikal Bridges,61,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.0751
Mikal Bridges,61,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1483
Victor Wembanyama,56677822,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,27.5,-0.2279
Victor Wembanyama,56677822,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.2223
Victor Wembanyama,56677822,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1647
Victor Wembanyama,56677822,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.096
Victor Wembanyama,56677822,SAS,NYK,21716136,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.3004
Karl-Anthony Towns,447,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.1634
Karl-Anthony Towns,447,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.0765
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.066
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.1557

```

---

## `derek_game_snapshots/21716136/current_live/full_pmf_wide.csv`

- bytes: `35,964`
- rows: `30`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1506
De'Aaron Fox,161,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.1342
Landry Shamet,414,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.5,-0.1017
Jalen Brunson,73,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,26.5,-0.0505
Josh Hart,202,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.5,-0.1172
Josh Hart,202,NYK,SAS,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.5,-0.1085
Stephon Castle,1028025261,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1475
Stephon Castle,1028025261,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.1312
Devin Vassell,3547246,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.1138
Devin Vassell,3547246,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1147
Julian Champagnie,38017649,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.5,-0.1163
Julian Champagnie,38017649,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.069
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0446
Dylan Harper,1057262518,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,13.5,-0.1324
Dylan Harper,1057262518,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.0757
Dylan Harper,1057262518,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1999
Dylan Harper,1057262518,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,0.0047
Keldon Johnson,666682,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.0994
Keldon Johnson,666682,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.257
Mikal Bridges,61,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.0751
Mikal Bridges,61,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1483
Victor Wembanyama,56677822,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,27.5,-0.2279
Victor Wembanyama,56677822,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.2223
Victor Wembanyama,56677822,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1647
Victor Wembanyama,56677822,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.096
Victor Wembanyama,56677822,SAS,NYK,21716136,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.3004
Karl-Anthony Towns,447,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.1634
Karl-Anthony Towns,447,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.0765
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.066
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.1557

```

---

## `derek_game_snapshots/21716136/current_live/full_pmf_wide.parquet`

- bytes: `71,552`
- rows: `30`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1506
De'Aaron Fox,161,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.1342
Landry Shamet,414,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.5,-0.1017
Jalen Brunson,73,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,26.5,-0.0505
Josh Hart,202,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.5,-0.1172
Josh Hart,202,NYK,SAS,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.5,-0.1085
Stephon Castle,1028025261,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1475
Stephon Castle,1028025261,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.1312
Devin Vassell,3547246,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.1138
Devin Vassell,3547246,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1147
Julian Champagnie,38017649,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.5,-0.1163
Julian Champagnie,38017649,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.069
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0446
Dylan Harper,1057262518,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,13.5,-0.1324
Dylan Harper,1057262518,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.0757
Dylan Harper,1057262518,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1999
Dylan Harper,1057262518,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,0.0047
Keldon Johnson,666682,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.0994
Keldon Johnson,666682,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.257
Mikal Bridges,61,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.0751
Mikal Bridges,61,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1483
Victor Wembanyama,56677822,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,27.5,-0.2279
Victor Wembanyama,56677822,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.2223
Victor Wembanyama,56677822,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1647
Victor Wembanyama,56677822,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.096
Victor Wembanyama,56677822,SAS,NYK,21716136,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.3004
Karl-Anthony Towns,447,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.1634
Karl-Anthony Towns,447,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.0765
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.066
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.1557

```

---

## `derek_game_snapshots/21716136/current_live/game_context.csv`

- bytes: `502`
- rows: `12`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,NYK,21716136
Landry Shamet,414,NYK,SAS,21716136
Jalen Brunson,73,NYK,SAS,21716136
Josh Hart,202,NYK,SAS,21716136
Stephon Castle,1028025261,SAS,NYK,21716136
Devin Vassell,3547246,SAS,NYK,21716136
Julian Champagnie,38017649,SAS,NYK,21716136
Dylan Harper,1057262518,SAS,NYK,21716136
Keldon Johnson,666682,SAS,NYK,21716136
Mikal Bridges,61,NYK,SAS,21716136
Victor Wembanyama,56677822,SAS,NYK,21716136
Karl-Anthony Towns,447,NYK,SAS,21716136

```

---

## `derek_game_snapshots/21716136/current_live/game_context.parquet`

- bytes: `3,582`
- rows: `12`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,NYK,21716136
Landry Shamet,414,NYK,SAS,21716136
Jalen Brunson,73,NYK,SAS,21716136
Josh Hart,202,NYK,SAS,21716136
Stephon Castle,1028025261,SAS,NYK,21716136
Devin Vassell,3547246,SAS,NYK,21716136
Julian Champagnie,38017649,SAS,NYK,21716136
Dylan Harper,1057262518,SAS,NYK,21716136
Keldon Johnson,666682,SAS,NYK,21716136
Mikal Bridges,61,NYK,SAS,21716136
Victor Wembanyama,56677822,SAS,NYK,21716136
Karl-Anthony Towns,447,NYK,SAS,21716136

```

---

## `derek_game_snapshots/21716136/current_live/injury_availability_context.csv`

- bytes: `497`
- rows: `12`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716136
Landry Shamet,414,NYK,21716136
Jalen Brunson,73,NYK,21716136
Josh Hart,202,NYK,21716136
Stephon Castle,1028025261,SAS,21716136
Devin Vassell,3547246,SAS,21716136
Julian Champagnie,38017649,SAS,21716136
Dylan Harper,1057262518,SAS,21716136
Keldon Johnson,666682,SAS,21716136
Mikal Bridges,61,NYK,21716136
Victor Wembanyama,56677822,SAS,21716136
Karl-Anthony Towns,447,NYK,21716136

```

---

## `derek_game_snapshots/21716136/current_live/injury_availability_context.parquet`

- bytes: `3,784`
- rows: `12`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716136
Landry Shamet,414,NYK,21716136
Jalen Brunson,73,NYK,21716136
Josh Hart,202,NYK,21716136
Stephon Castle,1028025261,SAS,21716136
Devin Vassell,3547246,SAS,21716136
Julian Champagnie,38017649,SAS,21716136
Dylan Harper,1057262518,SAS,21716136
Keldon Johnson,666682,SAS,21716136
Mikal Bridges,61,NYK,21716136
Victor Wembanyama,56677822,SAS,21716136
Karl-Anthony Towns,447,NYK,21716136

```

---

## `derek_game_snapshots/21716136/current_live/lineup_context.csv`

- bytes: `1,344`
- rows: `12`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21716136,reb
Landry Shamet,414,NYK,21716136,pts
Jalen Brunson,73,NYK,21716136,pts
Josh Hart,202,NYK,21716136,reb
Stephon Castle,1028025261,SAS,21716136,ast
Devin Vassell,3547246,SAS,21716136,pts
Julian Champagnie,38017649,SAS,21716136,pts
Dylan Harper,1057262518,SAS,21716136,pts
Keldon Johnson,666682,SAS,21716136,reb
Mikal Bridges,61,NYK,21716136,reb
Victor Wembanyama,56677822,SAS,21716136,pts
Karl-Anthony Towns,447,NYK,21716136,pts

```

---

## `derek_game_snapshots/21716136/current_live/lineup_context.parquet`

- bytes: `8,352`
- rows: `12`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21716136,reb
Landry Shamet,414,NYK,21716136,pts
Jalen Brunson,73,NYK,21716136,pts
Josh Hart,202,NYK,21716136,reb
Stephon Castle,1028025261,SAS,21716136,ast
Devin Vassell,3547246,SAS,21716136,pts
Julian Champagnie,38017649,SAS,21716136,pts
Dylan Harper,1057262518,SAS,21716136,pts
Keldon Johnson,666682,SAS,21716136,reb
Mikal Bridges,61,NYK,21716136,reb
Victor Wembanyama,56677822,SAS,21716136,pts
Karl-Anthony Towns,447,NYK,21716136,pts

```

---

## `derek_game_snapshots/21716136/current_live/market_comparison.csv`

- bytes: `47,250`
- rows: `30`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.370092147435897,0.0588,3.5,0.1506
De'Aaron Fox,161,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.83877755511022,0.0442,5.5,-0.1342
Landry Shamet,414,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,7.70133386821783,0.0824,8.5,-0.1017
Jalen Brunson,73,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,24.843894588613963,0.005,26.5,-0.0505
Josh Hart,202,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,7.320284341209451,0.0222,8.5,-0.1172
Josh Hart,202,NYK,SAS,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.04296875,0.0713,4.5,-0.1085
Stephon Castle,1028025261,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.081497797356828,0.037,6.5,-0.1475
Stephon Castle,1028025261,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.408340834083408,0.2451,0.5,0.1312
Devin Vassell,3547246,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.56096826034552,0.0201,13.5,-0.1138
Devin Vassell,3547246,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.044135308246598,0.2049,2.5,-0.1147
Julian Champagnie,38017649,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,9.35058279742765,0.0282,10.5,-0.1163
Julian Champagnie,38017649,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.037474949899798,0.0423,5.5,-0.069
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.261426142614261,0.0906,2.5,-0.0446
Dylan Harper,1057262518,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,11.529364521634374,0.0233,13.5,-0.1324
Dylan Harper,1057262518,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.92970862120757,0.0473,5.5,-0.0757
Dylan Harper,1057262518,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.2396114949434263,0.1989,3.5,-0.1999
Dylan Harper,1057262518,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.9772022797720228,0.3582,0.5,0.0047
Keldon Johnson,666682,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.538376753507013,0.1842,2.5,-0.0994
Keldon Johnson,666682,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.391939193919392,0.2312,0.5,0.257
Mikal Bridges,61,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.946414262820512,0.069,3.5,0.0751
Mikal Bridges,61,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.074907490749075,0.3006,1.5,-0.1483
Victor Wembanyama,56677822,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,22.00140731805387,0.0054,27.5,-0.2279
Victor Wembanyama,56677822,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,9.141912869303956,0.0142,11.5,-0.2223
Victor Wembanyama,56677822,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.312975570684822,0.1497,3.5,-0.1647
Victor Wembanyama,56677822,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.1489,0.3989,1.5,-0.096
Victor Wembanyama,56677822,SAS,NYK,21716136,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.1586,0.1375,3.5,-0.3004
Karl-Anthony Towns,447,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,14.922868061142395,0.0104,17.5,-0.1634
Karl-Anthony Towns,447,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.48186736125025,0.0117,11.5,-0.0765
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.1409,0.2871,1.5,-0.066
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.8369163083691631,0.6089,0.5,-0.1557

```

---

## `derek_game_snapshots/21716136/current_live/market_comparison.parquet`

- bytes: `85,893`
- rows: `30`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.370092147435897,0.0588,3.5,0.1506
De'Aaron Fox,161,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.83877755511022,0.0442,5.5,-0.1342
Landry Shamet,414,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,7.70133386821783,0.0824,8.5,-0.1017
Jalen Brunson,73,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,24.843894588613963,0.005,26.5,-0.0505
Josh Hart,202,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,7.320284341209451,0.0222,8.5,-0.1172
Josh Hart,202,NYK,SAS,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.04296875,0.0713,4.5,-0.1085
Stephon Castle,1028025261,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.081497797356828,0.037,6.5,-0.1475
Stephon Castle,1028025261,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.408340834083408,0.2451,0.5,0.1312
Devin Vassell,3547246,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.56096826034552,0.0201,13.5,-0.1138
Devin Vassell,3547246,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.044135308246598,0.2049,2.5,-0.1147
Julian Champagnie,38017649,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,9.35058279742765,0.0282,10.5,-0.1163
Julian Champagnie,38017649,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.037474949899798,0.0423,5.5,-0.069
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.2614261426142614,0.0906,2.5,-0.0446
Dylan Harper,1057262518,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,11.529364521634374,0.0233,13.5,-0.1324
Dylan Harper,1057262518,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.92970862120757,0.0473,5.5,-0.0757
Dylan Harper,1057262518,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.2396114949434263,0.1989,3.5,-0.1999
Dylan Harper,1057262518,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.9772022797720229,0.3582,0.5,0.0047
Keldon Johnson,666682,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.538376753507013,0.1842,2.5,-0.0994
Keldon Johnson,666682,SAS,NYK,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.391939193919392,0.2312,0.5,0.257
Mikal Bridges,61,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.9464142628205123,0.069,3.5,0.0751
Mikal Bridges,61,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.074907490749075,0.3006,1.5,-0.1483
Victor Wembanyama,56677822,SAS,NYK,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,22.00140731805387,0.0054,27.5,-0.2279
Victor Wembanyama,56677822,SAS,NYK,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,9.141912869303955,0.0142,11.5,-0.2223
Victor Wembanyama,56677822,SAS,NYK,21716136,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.312975570684822,0.1497,3.5,-0.1647
Victor Wembanyama,56677822,SAS,NYK,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.1489,0.3989,1.5,-0.096
Victor Wembanyama,56677822,SAS,NYK,21716136,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.1586,0.1375,3.5,-0.3004
Karl-Anthony Towns,447,NYK,SAS,21716136,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,14.922868061142397,0.0104,17.5,-0.1634
Karl-Anthony Towns,447,NYK,SAS,21716136,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.48186736125025,0.0117,11.5,-0.0765
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.1409,0.2871,1.5,-0.066
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.8369163083691631,0.6089,0.5,-0.1557

```

---

## `derek_game_snapshots/21716136/current_live/outcome_level_probabilities.csv`

- bytes: `99,489`
- rows: `541`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21716136,reb,0,0.0589,3.5,current_live
De'Aaron Fox,161,21716136,reb,1,0.0907,3.5,current_live
De'Aaron Fox,161,21716136,reb,2,0.1264,3.5,current_live
De'Aaron Fox,161,21716136,reb,3,0.1266,3.5,current_live
De'Aaron Fox,161,21716136,reb,4,0.1511,3.5,current_live
De'Aaron Fox,161,21716136,reb,5,0.1244,3.5,current_live
De'Aaron Fox,161,21716136,reb,6,0.1031,3.5,current_live
De'Aaron Fox,161,21716136,reb,7,0.0954,3.5,current_live
De'Aaron Fox,161,21716136,reb,8,0.0548,3.5,current_live
De'Aaron Fox,161,21716136,reb,9,0.0292,3.5,current_live
De'Aaron Fox,161,21716136,reb,10,0.0168,3.5,current_live
De'Aaron Fox,161,21716136,reb,11,0.0122,3.5,current_live
De'Aaron Fox,161,21716136,reb,12,0.0054,3.5,current_live
De'Aaron Fox,161,21716136,reb,13,0.0035,3.5,current_live
De'Aaron Fox,161,21716136,reb,14,0.0014,3.5,current_live
De'Aaron Fox,161,21716136,ast,0,0.0443,5.5,current_live
De'Aaron Fox,161,21716136,ast,1,0.0667,5.5,current_live
De'Aaron Fox,161,21716136,ast,2,0.0834,5.5,current_live
De'Aaron Fox,161,21716136,ast,3,0.1293,5.5,current_live
De'Aaron Fox,161,21716136,ast,4,0.1542,5.5,current_live
De'Aaron Fox,161,21716136,ast,5,0.1398,5.5,current_live
De'Aaron Fox,161,21716136,ast,6,0.1285,5.5,current_live
De'Aaron Fox,161,21716136,ast,7,0.0883,5.5,current_live
De'Aaron Fox,161,21716136,ast,8,0.0737,5.5,current_live
De'Aaron Fox,161,21716136,ast,9,0.0408,5.5,current_live
De'Aaron Fox,161,21716136,ast,10,0.0255,5.5,current_live
De'Aaron Fox,161,21716136,ast,11,0.013,5.5,current_live
De'Aaron Fox,161,21716136,ast,12,0.0075,5.5,current_live
De'Aaron Fox,161,21716136,ast,13,0.0034,5.5,current_live
De'Aaron Fox,161,21716136,ast,14,0.0017,5.5,current_live

```

---

## `derek_game_snapshots/21716136/current_live/outcome_level_probabilities.parquet`

- bytes: `18,075`
- rows: `541`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21716136,reb,0,0.058894230769230775,3.5,current_live
De'Aaron Fox,161,21716136,reb,1,0.09074519230769232,3.5,current_live
De'Aaron Fox,161,21716136,reb,2,0.1264022435897436,3.5,current_live
De'Aaron Fox,161,21716136,reb,3,0.12660256410256412,3.5,current_live
De'Aaron Fox,161,21716136,reb,4,0.15114182692307696,3.5,current_live
De'Aaron Fox,161,21716136,reb,5,0.12439903846153849,3.5,current_live
De'Aaron Fox,161,21716136,reb,6,0.10306490384615387,3.5,current_live
De'Aaron Fox,161,21716136,reb,7,0.09535256410256412,3.5,current_live
De'Aaron Fox,161,21716136,reb,8,0.05478766025641026,3.5,current_live
De'Aaron Fox,161,21716136,reb,9,0.029246794871794875,3.5,current_live
De'Aaron Fox,161,21716136,reb,10,0.01682692307692308,3.5,current_live
De'Aaron Fox,161,21716136,reb,11,0.012219551282051285,3.5,current_live
De'Aaron Fox,161,21716136,reb,12,0.005408653846153847,3.5,current_live
De'Aaron Fox,161,21716136,reb,13,0.003505608974358975,3.5,current_live
De'Aaron Fox,161,21716136,reb,14,0.00140224358974359,3.5,current_live
De'Aaron Fox,161,21716136,ast,0,0.044288577154308624,5.5,current_live
De'Aaron Fox,161,21716136,ast,1,0.06673346693386775,5.5,current_live
De'Aaron Fox,161,21716136,ast,2,0.08336673346693388,5.5,current_live
De'Aaron Fox,161,21716136,ast,3,0.12925851703406815,5.5,current_live
De'Aaron Fox,161,21716136,ast,4,0.15420841683366737,5.5,current_live
De'Aaron Fox,161,21716136,ast,5,0.1397795591182365,5.5,current_live
De'Aaron Fox,161,21716136,ast,6,0.12845691382765534,5.5,current_live
De'Aaron Fox,161,21716136,ast,7,0.08827655310621244,5.5,current_live
De'Aaron Fox,161,21716136,ast,8,0.07374749498997997,5.5,current_live
De'Aaron Fox,161,21716136,ast,9,0.04078156312625251,5.5,current_live
De'Aaron Fox,161,21716136,ast,10,0.025450901803607217,5.5,current_live
De'Aaron Fox,161,21716136,ast,11,0.013026052104208418,5.5,current_live
De'Aaron Fox,161,21716136,ast,12,0.007515030060120241,5.5,current_live
De'Aaron Fox,161,21716136,ast,13,0.003406813627254509,5.5,current_live
De'Aaron Fox,161,21716136,ast,14,0.0017034068136272545,5.5,current_live

```

---

## `derek_game_snapshots/21716136/current_live/pmf_driver_decomposition.csv`

- bytes: `2,619`
- rows: `12`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21716136,reb,3.5
Landry Shamet,414,NYK,21716136,pts,8.5
Jalen Brunson,73,NYK,21716136,pts,26.5
Josh Hart,202,NYK,21716136,reb,8.5
Stephon Castle,1028025261,SAS,21716136,ast,6.5
Devin Vassell,3547246,SAS,21716136,pts,13.5
Julian Champagnie,38017649,SAS,21716136,pts,10.5
Dylan Harper,1057262518,SAS,21716136,pts,13.5
Keldon Johnson,666682,SAS,21716136,reb,2.5
Mikal Bridges,61,NYK,21716136,reb,3.5
Victor Wembanyama,56677822,SAS,21716136,pts,27.5
Karl-Anthony Towns,447,NYK,21716136,pts,17.5

```

---

## `derek_game_snapshots/21716136/current_live/pmf_driver_decomposition.parquet`

- bytes: `14,376`
- rows: `12`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21716136,reb,3.5
Landry Shamet,414,NYK,21716136,pts,8.5
Jalen Brunson,73,NYK,21716136,pts,26.5
Josh Hart,202,NYK,21716136,reb,8.5
Stephon Castle,1028025261,SAS,21716136,ast,6.5
Devin Vassell,3547246,SAS,21716136,pts,13.5
Julian Champagnie,38017649,SAS,21716136,pts,10.5
Dylan Harper,1057262518,SAS,21716136,pts,13.5
Keldon Johnson,666682,SAS,21716136,reb,2.5
Mikal Bridges,61,NYK,21716136,reb,3.5
Victor Wembanyama,56677822,SAS,21716136,pts,27.5
Karl-Anthony Towns,447,NYK,21716136,pts,17.5

```

---

## `derek_game_snapshots/21716136/current_live/prediction_input_audit.csv`

- bytes: `2,134`
- rows: `30`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716136,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716136,ast,5.5
Landry Shamet,414,NYK,SAS,21716136,pts,8.5
Jalen Brunson,73,NYK,SAS,21716136,pts,26.5
Josh Hart,202,NYK,SAS,21716136,reb,8.5
Josh Hart,202,NYK,SAS,21716136,ast,4.5
Stephon Castle,1028025261,SAS,NYK,21716136,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716136,stl,0.5
Devin Vassell,3547246,SAS,NYK,21716136,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716136,ast,2.5
Julian Champagnie,38017649,SAS,NYK,21716136,pts,10.5
Julian Champagnie,38017649,SAS,NYK,21716136,reb,5.5
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,2.5
Dylan Harper,1057262518,SAS,NYK,21716136,pts,13.5
Dylan Harper,1057262518,SAS,NYK,21716136,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716136,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716136,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716136,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716136,fg3m,0.5
Mikal Bridges,61,NYK,SAS,21716136,reb,3.5
Mikal Bridges,61,NYK,SAS,21716136,fg3m,1.5
Victor Wembanyama,56677822,SAS,NYK,21716136,pts,27.5
Victor Wembanyama,56677822,SAS,NYK,21716136,reb,11.5
Victor Wembanyama,56677822,SAS,NYK,21716136,ast,3.5
Victor Wembanyama,56677822,SAS,NYK,21716136,stl,1.5
Victor Wembanyama,56677822,SAS,NYK,21716136,blk,3.5
Karl-Anthony Towns,447,NYK,SAS,21716136,pts,17.5
Karl-Anthony Towns,447,NYK,SAS,21716136,reb,11.5
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,1.5
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,0.5

```

---

## `derek_game_snapshots/21716136/current_live/prediction_input_audit.parquet`

- bytes: `5,335`
- rows: `30`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716136,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716136,ast,5.5
Landry Shamet,414,NYK,SAS,21716136,pts,8.5
Jalen Brunson,73,NYK,SAS,21716136,pts,26.5
Josh Hart,202,NYK,SAS,21716136,reb,8.5
Josh Hart,202,NYK,SAS,21716136,ast,4.5
Stephon Castle,1028025261,SAS,NYK,21716136,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716136,stl,0.5
Devin Vassell,3547246,SAS,NYK,21716136,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716136,ast,2.5
Julian Champagnie,38017649,SAS,NYK,21716136,pts,10.5
Julian Champagnie,38017649,SAS,NYK,21716136,reb,5.5
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,2.5
Dylan Harper,1057262518,SAS,NYK,21716136,pts,13.5
Dylan Harper,1057262518,SAS,NYK,21716136,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716136,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716136,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716136,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716136,fg3m,0.5
Mikal Bridges,61,NYK,SAS,21716136,reb,3.5
Mikal Bridges,61,NYK,SAS,21716136,fg3m,1.5
Victor Wembanyama,56677822,SAS,NYK,21716136,pts,27.5
Victor Wembanyama,56677822,SAS,NYK,21716136,reb,11.5
Victor Wembanyama,56677822,SAS,NYK,21716136,ast,3.5
Victor Wembanyama,56677822,SAS,NYK,21716136,stl,1.5
Victor Wembanyama,56677822,SAS,NYK,21716136,blk,3.5
Karl-Anthony Towns,447,NYK,SAS,21716136,pts,17.5
Karl-Anthony Towns,447,NYK,SAS,21716136,reb,11.5
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,1.5
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,0.5

```

---

## `derek_game_snapshots/21716136/current_live/prop_summary.csv`

- bytes: `1,582`
- rows: `30`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716136,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716136,ast,5.5
Landry Shamet,414,NYK,SAS,21716136,pts,8.5
Jalen Brunson,73,NYK,SAS,21716136,pts,26.5
Josh Hart,202,NYK,SAS,21716136,reb,8.5
Josh Hart,202,NYK,SAS,21716136,ast,4.5
Stephon Castle,1028025261,SAS,NYK,21716136,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716136,stl,0.5
Devin Vassell,3547246,SAS,NYK,21716136,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716136,ast,2.5
Julian Champagnie,38017649,SAS,NYK,21716136,pts,10.5
Julian Champagnie,38017649,SAS,NYK,21716136,reb,5.5
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,2.5
Dylan Harper,1057262518,SAS,NYK,21716136,pts,13.5
Dylan Harper,1057262518,SAS,NYK,21716136,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716136,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716136,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716136,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716136,fg3m,0.5
Mikal Bridges,61,NYK,SAS,21716136,reb,3.5
Mikal Bridges,61,NYK,SAS,21716136,fg3m,1.5
Victor Wembanyama,56677822,SAS,NYK,21716136,pts,27.5
Victor Wembanyama,56677822,SAS,NYK,21716136,reb,11.5
Victor Wembanyama,56677822,SAS,NYK,21716136,ast,3.5
Victor Wembanyama,56677822,SAS,NYK,21716136,stl,1.5
Victor Wembanyama,56677822,SAS,NYK,21716136,blk,3.5
Karl-Anthony Towns,447,NYK,SAS,21716136,pts,17.5
Karl-Anthony Towns,447,NYK,SAS,21716136,reb,11.5
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,1.5
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,0.5

```

---

## `derek_game_snapshots/21716136/current_live/prop_summary.parquet`

- bytes: `4,744`
- rows: `30`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716136,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716136,ast,5.5
Landry Shamet,414,NYK,SAS,21716136,pts,8.5
Jalen Brunson,73,NYK,SAS,21716136,pts,26.5
Josh Hart,202,NYK,SAS,21716136,reb,8.5
Josh Hart,202,NYK,SAS,21716136,ast,4.5
Stephon Castle,1028025261,SAS,NYK,21716136,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716136,stl,0.5
Devin Vassell,3547246,SAS,NYK,21716136,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716136,ast,2.5
Julian Champagnie,38017649,SAS,NYK,21716136,pts,10.5
Julian Champagnie,38017649,SAS,NYK,21716136,reb,5.5
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,2.5
Dylan Harper,1057262518,SAS,NYK,21716136,pts,13.5
Dylan Harper,1057262518,SAS,NYK,21716136,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716136,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716136,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716136,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716136,fg3m,0.5
Mikal Bridges,61,NYK,SAS,21716136,reb,3.5
Mikal Bridges,61,NYK,SAS,21716136,fg3m,1.5
Victor Wembanyama,56677822,SAS,NYK,21716136,pts,27.5
Victor Wembanyama,56677822,SAS,NYK,21716136,reb,11.5
Victor Wembanyama,56677822,SAS,NYK,21716136,ast,3.5
Victor Wembanyama,56677822,SAS,NYK,21716136,stl,1.5
Victor Wembanyama,56677822,SAS,NYK,21716136,blk,3.5
Karl-Anthony Towns,447,NYK,SAS,21716136,pts,17.5
Karl-Anthony Towns,447,NYK,SAS,21716136,reb,11.5
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,1.5
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,0.5

```

---

## `derek_game_snapshots/21716136/morning/full_pmf_wide.csv`

- bytes: `287,086`
- rows: `144`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,4.1533,4.1533,4,4,0.0071,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,3.2197,3.2197,3,3,0.014,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,1.0973,1.0973,1,0,0.3963,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,1.1393,1.1393,1,1,0.1189,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,0.8079,0.8079,0,0,0.6235,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,0.3336,0.3336,0,0,0.774,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.438,33.4249,0.05,1.1373,1.1373,1,0,0.4826,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.438,33.4249,0.05,17.9204,17.9204,18,18,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.438,33.4249,0.05,18.854,18.854,19,19,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.438,33.4249,0.05,7.373,7.373,7,7,0.0001,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.438,33.4249,0.05,22.0737,22.0737,22,22,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9712,36.068,0.05,27.0745,27.0745,27,28,0.0001,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9712,36.068,0.05,3.8116,3.8116,4,4,0.007,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9712,36.068,0.05,6.6106,6.6106,7,6,0.0048,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9712,36.068,0.05,1.9861,1.9861,2,0,0.397,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9712,36.068,0.05,1.4866,1.4866,1,1,0.1133,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9712,36.068,0.05,0.6529,0.6529,0,0,0.6463,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9712,36.068,0.05,0.3044,0.3044,0,0,0.7609,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.9712,36.068,0.05,0.963,0.963,1,0,0.4917,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.9712,36.068,0.05,33.6851,33.6851,34,35,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.9712,36.068,0.05,30.886,30.886,31,32,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.9712,36.068,0.05,10.4221,10.4221,10,10,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.9712,36.068,0.05,37.4966,37.4966,38,38,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,17.0545,17.0545,17,18,0.0013,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,4.6076,4.6076,5,4,0.0054,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,5.1975,5.1975,5,5,0.006,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,1.4095,1.4095,1,0,0.3968,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,1.5038,1.5038,1,1,0.1155,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,0.5899,0.5899,0,0,0.6327,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z

```

---

## `derek_game_snapshots/21716136/morning/full_pmf_wide.parquet`

- bytes: `171,194`
- rows: `144`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.70071426649782,15,15,0.0023717097946503386,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,4.153281051901045,4.153281051901045,4,4,0.007061611882382426,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,3.2197294618790506,3.2197294618790506,3,3,0.014030913639987624,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,1.0973305154254185,1.0973305154254183,1,0,0.3963349828331995,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,1.139327008930856,1.139327008930856,1,1,0.11885498137342292,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,0.8078984893418149,0.8078984893418147,0,0,0.623527911825196,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,0.33356259623826034,0.33356259623826034,0,0,0.7740380201679007,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.43802343603572,33.42492678412381,0.050000000000000044,1.137302017859568,1.137302017859568,1,0,0.48263431038860005,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.43802343603572,33.42492678412381,0.050000000000000044,17.920443728376796,17.920443728376785,18,18,3.327725530785174e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.43802343603572,33.42492678412381,0.050000000000000044,18.853995318398795,18.8539953183988,19,19,1.6748094067465632e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.43802343603572,33.42492678412381,0.050000000000000044,7.373010513780088,7.3730105137800885,7,7,9.908086648081832e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.43802343603572,33.42492678412381,0.050000000000000044,22.07372478027782,22.073724780277814,22,22,2.3499106149499952e-07,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97117745967532,36.068001041442216,0.050000000000000044,27.07446523793174,27.074465237931726,27,28,7.352836850588927e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97117745967532,36.068001041442216,0.050000000000000044,3.811552576808661,3.811552576808661,4,4,0.006972078597201647,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97117745967532,36.068001041442216,0.050000000000000044,6.610595493048416,6.6105954930484145,7,6,0.004834488956102641,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97117745967532,36.068001041442216,0.050000000000000044,1.98606520729651,1.9860652072965097,2,0,0.39695100841442077,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97117745967532,36.068001041442216,0.050000000000000044,1.4866075594779007,1.486607559477901,1,1,0.1132964024458426,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97117745967532,36.068001041442216,0.050000000000000044,0.6529189907218552,0.6529189907218552,0,0,0.6462984937750074,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97117745967532,36.068001041442216,0.050000000000000044,0.30444055918887425,0.30444055918887425,0,0,0.7608500923819775,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.97117745967532,36.068001041442216,0.050000000000000044,0.962975403292079,0.9629754032920791,1,0,0.4917362686950473,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.97117745967532,36.068001041442216,0.050000000000000044,33.68506073098014,33.68506073098013,34,35,3.5547208550196706e-07,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.97117745967532,36.068001041442216,0.050000000000000044,30.8860178147404,30.886017814740388,31,32,5.126455643470663e-07,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.97117745967532,36.068001041442216,0.050000000000000044,10.42214806985707,10.422148069857071,10,10,3.370643697925098e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Jalen Brunson,73,NYK,SAS,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.97117745967532,36.068001041442216,0.050000000000000044,37.49661330778876,37.496613307788735,38,38,2.4783793192308996e-09,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.001485586550007,34.33683051748481,0.050000000000000044,17.054483918489815,17.054483918489815,17,18,0.0012683755474865385,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.001485586550007,34.33683051748481,0.050000000000000044,4.607616471556697,4.607616471556697,5,4,0.00541441007308604,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.001485586550007,34.33683051748481,0.050000000000000044,5.197525629290567,5.197525629290567,5,5,0.005952049830284089,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.001485586550007,34.33683051748481,0.050000000000000044,1.4094861277852613,1.4094861277852613,1,0,0.3968085953285083,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.001485586550007,34.33683051748481,0.050000000000000044,1.5038078323521198,1.5038078323521193,1,1,0.11554585116105569,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.001485586550007,34.33683051748481,0.050000000000000044,0.5898894640052345,0.5898894640052346,0,0,0.6326921317949522,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z

```

---

## `derek_game_snapshots/21716136/morning/market_comparison.csv`

- bytes: `523,878`
- rows: `574`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,15.5,15.5,fanduel,0.4157,162,-220,0.357,0.0587,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,fanduel,0.5094,120,-160,0.4248,0.0846,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,fanduel,0.575,-112,-118,0.4939,0.081,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,12.5,12.5,fanduel,0.6324,-152,114,0.5635,0.069,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,11.5,11.5,fanduel,0.6852,-210,154,0.6324,0.0528,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,10.5,10.5,fanduel,0.7379,-290,205,0.694,0.0439,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,9.5,9.5,fanduel,0.7944,-420,280,0.7543,0.0401,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,8.5,8.5,fanduel,0.8368,-650,390,0.8094,0.0274,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,16.5,16.5,fanduel,0.3483,200,-280,0.3115,0.0368,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,17.5,17.5,fanduel,0.292,260,-380,0.2597,0.0323,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,williamhill_us,0.575,-127,-105,0.5221,0.0529,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,15.5,15.5,bovada,0.4157,120,-160,0.4248,-0.0091,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,bovada,0.5094,-105,-125,0.4797,0.0297,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,bovada,0.575,-135,105,0.5408,0.0342,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,12.5,12.5,bovada,0.6324,-180,135,0.6017,0.0307,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,11.5,11.5,bovada,0.6852,-245,180,0.6654,0.0199,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,16.5,16.5,bovada,0.3483,155,-210,0.3666,-0.0184,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,17.5,17.5,bovada,0.292,200,-275,0.3125,-0.0205,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,betmgm,0.575,-111,-118,0.4929,0.0821,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,betrivers,0.575,-107,-127,0.4802,0.0947,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,12.5,12.5,betrivers,0.6324,-143,106,0.548,0.0845,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,draftkings,0.5094,100,-127,0.4719,0.0375,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,fanduel,0.575,-111,-115,0.4958,0.0791,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,hardrockbet_az,0.575,-120,-110,0.5101,0.0648,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,hardrockbet,0.575,-120,-110,0.5101,0.0648,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,rebet,0.5094,100,-127,0.4719,0.0375,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,hardrockbet_fl,0.575,-120,-110,0.5101,0.0648,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,12.5,12.5,espnbet,0.6324,-160,120,0.5752,0.0573,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,espnbet,0.575,-110,-120,0.4899,0.0851,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,espnbet,0.5094,120,-160,0.4248,0.0846,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z

```

---

## `derek_game_snapshots/21716136/morning/market_comparison.parquet`

- bytes: `128,019`
- rows: `2,352`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,15.5,15.5,fanduel,0.4157135980572443,162,-220,0.35698348951361003,0.058730108543634196,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,14.5,14.5,fanduel,0.5094427084824357,120,-160,0.4248366013071895,0.08460610717524619,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,fanduel,0.5749597281699909,-112,-118,0.4939310568053083,0.08102867136468245,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,12.5,12.5,fanduel,0.6324387864854701,-152,114,0.563470066518847,0.06896871996662313,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,11.5,11.5,fanduel,0.685228025408754,-210,154,0.6324401233104102,0.05278790209834372,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,10.5,10.5,fanduel,0.7378828937625308,-290,205,0.6939976461357396,0.043885247626791135,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,9.5,9.5,fanduel,0.7943813691110273,-420,280,0.7542533081285445,0.04012806098248278,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,8.5,8.5,fanduel,0.836780570781727,-650,390,0.8094027954256671,0.027377775356059897,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,16.5,16.5,fanduel,0.34827467381671845,200,-280,0.31147540983606553,0.03679926398065292,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,17.5,17.5,fanduel,0.29200356951120693,260,-380,0.25974025974025977,0.03226330977094721,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,williamhill_us,0.5749597281699909,-127,-105,0.5220573491076799,0.05290237906231088,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,15.5,15.5,bovada,0.4157135980572443,120,-160,0.4248366013071895,-0.00912300324994525,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,14.5,14.5,bovada,0.5094427084824357,-105,-125,0.4796954314720812,0.029747277010354456,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,bovada,0.5749597281699909,-135,105,0.5407914020517831,0.03416832611820764,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,12.5,12.5,bovada,0.6324387864854701,-180,135,0.6017069701280228,0.030731816357447372,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,11.5,11.5,bovada,0.685228025408754,-245,180,0.6653734238603297,0.019854601548424222,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,16.5,16.5,bovada,0.34827467381671845,155,-210,0.3666469544648137,-0.018372280648095263,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,17.5,17.5,bovada,0.29200356951120693,200,-275,0.3125,-0.020496430488793016,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,betmgm,0.5749597281699909,-111,-118,0.4928711096627016,0.08208861850728916,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,betrivers,0.5749597281699909,-107,-127,0.4802285578710111,0.09473117029897965,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,12.5,12.5,betrivers,0.6324387864854701,-143,106,0.5479742549946055,0.08446453149086464,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,14.5,14.5,draftkings,0.5094427084824357,100,-127,0.47193347193347185,0.03750923654896382,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,fanduel,0.5749597281699909,-111,-115,0.4958445875753168,0.07911514059467395,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,hardrockbet_az,0.5749597281699909,-120,-110,0.5101214574898786,0.06483827068011216,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,hardrockbet,0.5749597281699909,-120,-110,0.5101214574898786,0.06483827068011216,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,14.5,14.5,rebet,0.5094427084824357,100,-127,0.47193347193347185,0.03750923654896382,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,hardrockbet_fl,0.5749597281699909,-120,-110,0.5101214574898786,0.06483827068011216,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,12.5,12.5,espnbet,0.6324387864854701,-160,120,0.5751633986928104,0.05727538779265973,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,13.5,13.5,espnbet,0.5749597281699909,-110,-120,0.48987854251012153,0.08508118565986922,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.43802343603572,33.42492678412381,0.050000000000000044,14.700714266497819,14.700714266497819,15,15,0.0023717097946503386,14.5,14.5,espnbet,0.5094427084824357,120,-160,0.4248366013071895,0.08460610717524619,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z

```

---

## `derek_game_snapshots/21716136/morning/market_comparison_csv_parts/market_comparison_part_000.csv`

- bytes: `480,325`
- rows: `532`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,15.5,15.5,fanduel,0.4157,162,-220,0.357,0.0587,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,fanduel,0.5094,120,-160,0.4248,0.0846,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,fanduel,0.575,-112,-118,0.4939,0.081,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,12.5,12.5,fanduel,0.6324,-152,114,0.5635,0.069,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,11.5,11.5,fanduel,0.6852,-210,154,0.6324,0.0528,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,10.5,10.5,fanduel,0.7379,-290,205,0.694,0.0439,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,9.5,9.5,fanduel,0.7944,-420,280,0.7543,0.0401,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,8.5,8.5,fanduel,0.8368,-650,390,0.8094,0.0274,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,16.5,16.5,fanduel,0.3483,200,-280,0.3115,0.0368,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,17.5,17.5,fanduel,0.292,260,-380,0.2597,0.0323,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,williamhill_us,0.575,-127,-105,0.5221,0.0529,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,15.5,15.5,bovada,0.4157,120,-160,0.4248,-0.0091,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,bovada,0.5094,-105,-125,0.4797,0.0297,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,bovada,0.575,-135,105,0.5408,0.0342,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,12.5,12.5,bovada,0.6324,-180,135,0.6017,0.0307,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,11.5,11.5,bovada,0.6852,-245,180,0.6654,0.0199,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,16.5,16.5,bovada,0.3483,155,-210,0.3666,-0.0184,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,17.5,17.5,bovada,0.292,200,-275,0.3125,-0.0205,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,betmgm,0.575,-111,-118,0.4929,0.0821,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,betrivers,0.575,-107,-127,0.4802,0.0947,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,12.5,12.5,betrivers,0.6324,-143,106,0.548,0.0845,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,draftkings,0.5094,100,-127,0.4719,0.0375,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,fanduel,0.575,-111,-115,0.4958,0.0791,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,hardrockbet_az,0.575,-120,-110,0.5101,0.0648,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,hardrockbet,0.575,-120,-110,0.5101,0.0648,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,rebet,0.5094,100,-127,0.4719,0.0375,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,hardrockbet_fl,0.575,-120,-110,0.5101,0.0648,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,12.5,12.5,espnbet,0.6324,-160,120,0.5752,0.0573,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,13.5,13.5,espnbet,0.575,-110,-120,0.4899,0.0851,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.438,33.4249,0.05,14.7007,14.7007,15,15,0.0024,14.5,14.5,espnbet,0.5094,120,-160,0.4248,0.0846,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z

```

---

## `derek_game_snapshots/21716136/morning/market_comparison_csv_parts/market_comparison_part_001.csv`

- bytes: `493,476`
- rows: `532`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
De'Aaron Fox,161,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,0.3683,0.3683,0,0,0.7664,0.5,0.5,draftkings,0.2336,359,-518,0.2063,0.0273,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,0.3683,0.3683,0,0,0.7664,0.5,0.5,hardrockbet_az,0.2336,300,-525,0.2294,0.0043,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,0.3683,0.3683,0,0,0.7664,0.5,0.5,hardrockbet_fl,0.2336,300,-525,0.2294,0.0043,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.0015,34.3368,0.05,0.3683,0.3683,0,0,0.7664,0.5,0.5,hardrockbet,0.2336,300,-525,0.2294,0.0043,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,0.982,0.982,1,0,0.4849,1.5,1.5,draftkings,0.2509,141,-189,0.3882,-0.1373,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,0.982,0.982,1,0,0.4849,1.5,1.5,hardrockbet_az,0.2509,130,-185,0.4011,-0.1502,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,0.982,0.982,1,0,0.4849,1.5,1.5,hardrockbet,0.2509,130,-185,0.4011,-0.1502,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,0.982,0.982,1,0,0.4849,1.5,1.5,hardrockbet_fl,0.2509,130,-185,0.4011,-0.1502,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,28.5,28.5,fanduel,0.1523,490,-900,0.1585,-0.0062,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,27.5,27.5,fanduel,0.1942,400,-670,0.1869,0.0073,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,26.5,26.5,fanduel,0.2422,320,-500,0.2222,0.0199,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,25.5,25.5,fanduel,0.2957,270,-400,0.2525,0.0432,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,24.5,24.5,fanduel,0.3553,220,-310,0.2924,0.0629,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,23.5,23.5,fanduel,0.4206,178,-245,0.3362,0.0844,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,22.5,22.5,fanduel,0.4889,136,-182,0.3963,0.0926,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,21.5,21.5,fanduel,0.5561,108,-144,0.4489,0.1071,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,20.5,20.5,fanduel,0.6182,-118,-112,0.5061,0.1121,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,19.5,19.5,fanduel,0.6738,-154,116,0.567,0.1068,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,18.5,18.5,fanduel,0.7244,-200,148,0.6231,0.1013,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,16.5,16.5,fanduel,0.8124,-340,235,0.7213,0.0911,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,15.5,15.5,fanduel,0.8499,-470,310,0.7717,0.0782,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,14.5,14.5,fanduel,0.8826,-670,400,0.8131,0.0695,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,17.5,17.5,fanduel,0.7706,-260,188,0.6753,0.0953,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,20.5,20.5,fanduel,0.6182,-118,-112,0.5061,0.1121,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,21.5,21.5,bovada,0.5561,105,-135,0.4592,0.0969,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,20.5,20.5,bovada,0.6182,-120,-110,0.5101,0.1081,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,19.5,19.5,bovada,0.6738,-150,115,0.5633,0.1105,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,20.5,20.5,betmgm,0.6182,-115,-115,0.5,0.1182,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,20.5,20.5,draftkings,0.6182,-118,-112,0.5061,0.1121,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
De'Aaron Fox,161,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.0015,34.3368,0.05,22.252,22.252,22,23,0.0,20.5,20.5,hardrockbet_az,0.6182,-120,-110,0.5101,0.1081,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z

```

---

## `derek_game_snapshots/21716136/morning/market_comparison_csv_parts/market_comparison_part_002.csv`

- bytes: `493,447`
- rows: `532`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,1.131,1.131,1,0,0.3973,1.5,1.5,hardrockbet,0.3622,125,-160,0.4194,-0.0572,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,1.131,1.131,1,0,0.3973,1.5,1.5,hardrockbet_fl,0.3622,125,-160,0.4194,-0.0572,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,1.131,1.131,1,0,0.3973,1.5,1.5,rebet,0.3622,130,-166,0.4106,-0.0485,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,1.131,1.131,1,0,0.3973,1.5,1.5,hardrockbet_az,0.3622,125,-160,0.4194,-0.0572,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,1.131,1.131,1,0,0.3973,1.5,1.5,betparx,0.3622,120,-162,0.4237,-0.0615,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,1.131,1.131,1,0,0.3973,1.5,1.5,fliff,0.3622,115,-165,0.4276,-0.0654,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,1.131,1.131,1,0,0.3973,0.5,0.5,espnbet,0.6027,-400,260,0.7423,-0.1395,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,1.131,1.131,1,0,0.3973,2.5,2.5,espnbet,0.1661,400,-750,0.1848,-0.0187,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,1.131,1.131,1,0,0.3973,1.5,1.5,espnbet,0.3622,135,-180,0.3983,-0.0361,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.6318,0.6318,0,0,0.6336,0.5,0.5,fanduel,0.3664,-146,110,0.5548,-0.1885,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.6318,0.6318,0,0,0.6336,0.5,0.5,draftkings,0.3664,-135,102,0.5371,-0.1708,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.6318,0.6318,0,0,0.6336,0.5,0.5,bovada,0.3664,-135,105,0.5408,-0.1744,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.6318,0.6318,0,0,0.6336,0.5,0.5,hardrockbet,0.3664,-145,100,0.5421,-0.1757,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.6318,0.6318,0,0,0.6336,0.5,0.5,hardrockbet_fl,0.3664,-145,100,0.5421,-0.1757,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.6318,0.6318,0,0,0.6336,0.5,0.5,hardrockbet_az,0.3664,-145,100,0.5421,-0.1757,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.6318,0.6318,0,0,0.6336,0.5,0.5,betparx,0.3664,-143,108,0.5504,-0.184,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.6318,0.6318,0,0,0.6336,0.5,0.5,fliff,0.3664,-140,-105,0.5325,-0.1661,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.4076,0.4076,0,0,0.783,0.5,0.5,bovada,0.217,-135,105,0.5408,-0.3238,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.4076,0.4076,0,0,0.783,0.5,0.5,betmgm,0.217,-160,120,0.5752,-0.3581,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.4076,0.4076,0,0,0.783,0.5,0.5,draftkings,0.217,-136,102,0.5379,-0.3209,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.4076,0.4076,0,0,0.783,0.5,0.5,fanduel,0.217,-146,110,0.5548,-0.3378,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.4076,0.4076,0,0,0.783,0.5,0.5,hardrockbet_az,0.217,-155,110,0.5607,-0.3437,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.4076,0.4076,0,0,0.783,0.5,0.5,hardrockbet_fl,0.217,-155,110,0.5607,-0.3437,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.4076,0.4076,0,0,0.783,0.5,0.5,betparx,0.217,-180,133,0.5997,-0.3826,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.4076,0.4076,0,0,0.783,0.5,0.5,hardrockbet,0.217,-155,110,0.5607,-0.3437,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.2975,31.9331,0.05,0.4076,0.4076,0,0,0.783,0.5,0.5,fliff,0.217,-160,110,0.5638,-0.3467,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.2975,31.9331,0.05,1.0657,1.0657,1,0,0.4961,1.5,1.5,draftkings,0.2855,-111,-119,0.4919,-0.2064,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.2975,31.9331,0.05,1.0657,1.0657,1,0,0.4961,1.5,1.5,hardrockbet_az,0.2855,-120,-120,0.5,-0.2145,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.2975,31.9331,0.05,1.0657,1.0657,1,0,0.4961,1.5,1.5,hardrockbet,0.2855,-120,-120,0.5,-0.2145,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Karl-Anthony Towns,447,NYK,SAS,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.2975,31.9331,0.05,1.0657,1.0657,1,0,0.4961,1.5,1.5,hardrockbet_fl,0.2855,-120,-120,0.5,-0.2145,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z

```

---

## `derek_game_snapshots/21716136/morning/market_comparison_csv_parts/market_comparison_part_003.csv`

- bytes: `500,105`
- rows: `532`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,2.5,2.5,bovada,0.4093,-110,-120,0.4899,-0.0806,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,2.5,2.5,hardrockbet,0.4093,-105,-125,0.4797,-0.0704,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,2.5,2.5,hardrockbet_fl,0.4093,-105,-125,0.4797,-0.0704,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,2.5,2.5,rebet,0.4093,106,-134,0.4588,-0.0495,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,2.5,2.5,hardrockbet_az,0.4093,-105,-125,0.4797,-0.0704,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,2.5,2.5,betparx,0.4093,106,-141,0.4535,-0.0442,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,2.5,2.5,fliff,0.4093,-110,-130,0.481,-0.0717,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,1.5,1.5,espnbet,0.5141,-285,210,0.6965,-0.1824,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,2.5,2.5,espnbet,0.4093,110,-145,0.4459,-0.0366,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,2.0827,2.0827,2,0,0.4009,3.5,3.5,espnbet,0.2726,250,-375,0.2657,0.0069,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.5776,0.5776,0,0,0.6337,0.5,0.5,draftkings,0.3663,-134,101,0.5351,-0.1688,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.5776,0.5776,0,0,0.6337,0.5,0.5,bovada,0.3663,-135,105,0.5408,-0.1745,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.5776,0.5776,0,0,0.6337,0.5,0.5,hardrockbet,0.3663,-145,100,0.5421,-0.1757,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.5776,0.5776,0,0,0.6337,0.5,0.5,hardrockbet_fl,0.3663,-145,100,0.5421,-0.1757,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.5776,0.5776,0,0,0.6337,0.5,0.5,hardrockbet_az,0.3663,-145,100,0.5421,-0.1757,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.5776,0.5776,0,0,0.6337,0.5,0.5,betparx,0.3663,-143,108,0.5504,-0.184,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.4081,0.4081,0,0,0.7786,0.5,0.5,bovada,0.2214,120,-160,0.4248,-0.2035,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.4081,0.4081,0,0,0.7786,0.5,0.5,betmgm,0.2214,125,-175,0.4112,-0.1899,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.4081,0.4081,0,0,0.7786,0.5,0.5,draftkings,0.2214,118,-157,0.4289,-0.2075,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.4081,0.4081,0,0,0.7786,0.5,0.5,hardrockbet_az,0.2214,125,-180,0.4088,-0.1874,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.4081,0.4081,0,0,0.7786,0.5,0.5,hardrockbet_fl,0.2214,125,-175,0.4112,-0.1899,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.4081,0.4081,0,0,0.7786,0.5,0.5,betparx,0.2214,123,-165,0.4187,-0.1973,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.4852,30.8107,0.05,0.4081,0.4081,0,0,0.7786,0.5,0.5,hardrockbet,0.2214,125,-175,0.4112,-0.1899,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.4852,30.8107,0.05,1.0164,1.0164,1,0,0.4934,1.5,1.5,draftkings,0.2724,138,-184,0.3934,-0.121,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.4852,30.8107,0.05,1.0164,1.0164,1,0,0.4934,1.5,1.5,hardrockbet_az,0.2724,140,-200,0.3846,-0.1122,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.4852,30.8107,0.05,1.0164,1.0164,1,0,0.4934,1.5,1.5,hardrockbet,0.2724,140,-200,0.3846,-0.1122,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.4852,30.8107,0.05,1.0164,1.0164,1,0,0.4934,1.5,1.5,hardrockbet_fl,0.2724,140,-200,0.3846,-0.1122,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.4852,30.8107,0.05,1.0164,1.0164,1,0,0.4934,1.5,1.5,betparx,0.2724,138,-186,0.3925,-0.1201,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.4852,30.8107,0.05,11.2036,11.2036,11,11,0.0004,11.5,11.5,fanduel,0.4333,-114,-114,0.5,-0.0667,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Julian Champagnie,38017649,SAS,NYK,21716136,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.4852,30.8107,0.05,11.2036,11.2036,11,11,0.0004,12.5,12.5,bovada,0.3456,105,-135,0.4592,-0.1136,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z

```

---

## `derek_game_snapshots/21716136/morning/market_comparison_csv_parts/market_comparison_part_004.csv`

- bytes: `213,288`
- rows: `224`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,22.5,22.5,fanduel,0.8008,-310,220,0.7076,0.0933,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,27.5,27.5,betmgm,0.5372,-110,-118,0.4918,0.0454,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,27.5,27.5,betrivers,0.5372,102,-139,0.4598,0.0774,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,26.5,26.5,betrivers,0.5977,-124,-110,0.5138,0.0839,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,25.5,25.5,betrivers,0.655,-157,115,0.5677,0.0873,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,26.5,26.5,draftkings,0.5977,-123,-107,0.5162,0.0815,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,26.5,26.5,bovada,0.5977,-125,-105,0.5203,0.0774,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,25.5,25.5,bovada,0.655,-150,115,0.5633,0.0917,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,24.5,24.5,bovada,0.7082,-185,140,0.6091,0.0991,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,27.5,27.5,bovada,0.5372,-105,-125,0.4797,0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,28.5,28.5,bovada,0.475,115,-150,0.4367,0.0384,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,27.5,27.5,hardrockbet_az,0.5372,-105,-125,0.4797,0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,27.5,27.5,hardrockbet,0.5372,-105,-125,0.4797,0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,27.5,27.5,hardrockbet_fl,0.5372,-105,-125,0.4797,0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,26.5,26.5,betparx,0.5977,-122,-109,0.5131,0.0847,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,26.5,26.5,espnbet,0.5977,-120,-110,0.5101,0.0876,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,25.5,25.5,betparx,0.655,-157,115,0.5677,0.0873,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,27.5,27.5,betparx,0.5372,104,-137,0.4589,0.0784,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Stephon Castle,1028025261,SAS,NYK,21716136,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.5556,32.0244,0.05,28.2182,28.2182,28,28,0.0,27.5,27.5,fliff,0.5372,-115,-130,0.4862,0.051,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,7.5,7.5,fanduel,0.8142,-800,450,0.8302,-0.016,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,8.5,8.5,fanduel,0.7633,-500,320,0.7778,-0.0145,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,9.5,9.5,fanduel,0.705,-360,250,0.7326,-0.0276,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,10.5,10.5,fanduel,0.6394,-270,194,0.6821,-0.0427,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,17.5,17.5,fanduel,0.2213,260,-380,0.2597,-0.0384,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,16.5,16.5,fanduel,0.2679,200,-280,0.3115,-0.0436,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,15.5,15.5,fanduel,0.3198,162,-220,0.357,-0.0372,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,14.5,14.5,fanduel,0.381,122,-162,0.4215,-0.0405,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,13.5,13.5,fanduel,0.4377,-106,-125,0.4808,-0.0431,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,12.5,12.5,fanduel,0.505,-144,108,0.5511,-0.0461,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z
Dylan Harper,1057262518,SAS,NYK,21716136,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,24.9364,26.3932,0.05,12.946,12.946,13,11,0.0105,11.5,11.5,fanduel,0.5706,-194,144,0.6169,-0.0462,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-08T23:43:42Z

```

---

## `derek_game_snapshots/21716136/morning/outcome_level_probabilities.csv`

- bytes: `481,011`
- rows: `4,893`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Mikal Bridges,61,21716136,pts,starter,0,0.0024,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,1,0.0027,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,2,0.0061,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,3,0.0118,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,4,0.0148,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,5,0.0232,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,6,0.0324,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,7,0.0311,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,8,0.0387,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,9,0.0424,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,10,0.0565,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,11,0.0527,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,12,0.0528,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,13,0.0575,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,14,0.0655,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,15,0.0937,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,16,0.0674,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,17,0.0563,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,18,0.0511,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,19,0.0395,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,20,0.0451,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,21,0.0378,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,22,0.0184,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,23,0.0161,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,24,0.0169,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,25,0.0136,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,26,0.009,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,27,0.0075,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,28,0.0055,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,29,0.0078,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21716136/morning/outcome_level_probabilities.parquet`

- bytes: `57,913`
- rows: `4,893`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Mikal Bridges,61,21716136,pts,starter,0,0.002371709794650338,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,1,0.002662407536434192,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,2,0.00609821590749926,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,3,0.011799251177681007,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,4,0.014820548950408787,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,5,0.02319696954934912,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,6,0.03244646044264081,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,7,0.031141573841797016,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,8,0.038682292017812585,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,9,0.042399201670699646,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,10,0.05649847534849655,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,11,0.05265486835377678,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,12,0.05278923892328371,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,13,0.057479058315479385,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,14,0.06551701968755508,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,15,0.09372911042519148,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,16,0.06743892424052579,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,17,0.05627110430551142,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,18,0.05111709752544763,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,19,0.03951320736755628,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,20,0.04513514399375934,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,21,0.03779965858932782,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,22,0.01841364517305991,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,23,0.01608605098485294,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,24,0.016868443555679766,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,25,0.013562567524078225,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,26,0.00903988664187622,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,27,0.00745325970222836,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,28,0.005534613085197335,latest_valid_report_selected,projected
Mikal Bridges,61,21716136,pts,starter,29,0.007757494424591459,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21716136/morning/prop_summary.csv`

- bytes: `23,015`
- rows: `144`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,14.7007,13.5,13.5,betmgm,0.575,-111.0,-118.0,0.4929,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,reb,starter,4.1533,3.5,3.5,betmgm,0.6618,100.0,-135.0,0.4653,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,ast,starter,3.2197,2.5,2.5,betmgm,0.6758,-160.0,120.0,0.5752,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,fg3m,starter,1.0973,1.5,1.5,betmgm,0.3348,110.0,-150.0,0.4425,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,tov,starter,1.1393,,,,,,,,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,stl,starter,0.8079,1.5,1.5,betparx,0.215,155.0,-210.0,0.3666,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,blk,starter,0.3336,0.5,0.5,betmgm,0.226,135.0,-190.0,0.3938,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,stocks,starter,1.1373,1.5,1.5,betparx,0.2963,-127.0,-105.0,0.5221,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,pa,starter,17.9204,16.5,16.5,betmgm,0.5803,-105.0,-130.0,0.4754,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,pr,starter,18.854,17.5,17.5,bovada,0.5735,-115.0,-115.0,0.5,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,ra,starter,7.373,6.5,6.5,betmgm,0.6511,-110.0,-120.0,0.4899,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,pra,starter,22.0737,20.5,20.5,betparx,0.5831,102.0,-136.0,0.4621,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,pts,starter,27.0745,26.5,26.5,betmgm,0.5542,-125.0,-105.0,0.5203,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,reb,starter,3.8116,3.5,3.5,betparx,0.5717,133.0,-180.0,0.4003,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,ast,starter,6.6106,5.5,5.5,betparx,0.7125,-143.0,108.0,0.5504,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,fg3m,starter,1.9861,2.5,2.5,betmgm,0.371,115.0,-155.0,0.4335,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,tov,starter,1.4866,,,,,,,,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,stl,starter,0.6529,0.5,0.5,betparx,0.3537,-175.0,130.0,0.5941,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,blk,starter,0.3044,0.5,0.5,betmgm,0.2391,475.0,-1000.0,0.1606,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,stocks,starter,0.963,,,,,,,,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,pa,starter,33.6851,32.5,32.5,betmgm,0.5703,-125.0,-105.0,0.5203,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,pr,starter,30.886,29.5,29.5,betmgm,0.5852,-115.0,-115.0,0.5,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,ra,starter,10.4221,9.5,9.5,betmgm,0.6455,105.0,-140.0,0.4554,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,pra,starter,37.4966,35.5,35.5,betparx,0.606,-114.0,-117.0,0.497,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,pts,starter,17.0545,14.5,14.5,betmgm,0.6724,-115.0,-115.0,0.5,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,reb,starter,4.6076,3.5,3.5,betmgm,0.7466,100.0,-135.0,0.4653,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,ast,starter,5.1975,5.5,5.5,betmgm,0.4287,-125.0,-105.0,0.5203,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,fg3m,starter,1.4095,1.5,1.5,betmgm,0.4219,125.0,-165.0,0.4165,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,tov,starter,1.5038,,,,,,,,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,stl,starter,0.5899,0.5,0.5,betparx,0.3673,-250.0,185.0,0.6706,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21716136/morning/prop_summary.parquet`

- bytes: `16,541`
- rows: `144`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
Mikal Bridges,61,NYK,SAS,21716136,pts,starter,14.70071426649782,13.5,13.5,betmgm,0.5749597281699909,-111.0,-118.0,0.4928711096627016,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,reb,starter,4.153281051901045,3.5,3.5,betmgm,0.6617737654668412,100.0,-135.0,0.4653465346534653,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,ast,starter,3.2197294618790506,2.5,2.5,betmgm,0.6757914069103628,-160.0,120.0,0.5751633986928104,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,fg3m,starter,1.0973305154254183,1.5,1.5,betmgm,0.3347946261427721,110.0,-150.0,0.4424778761061947,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,tov,starter,1.139327008930856,,,,,,,,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,stl,starter,0.8078984893418147,1.5,1.5,betparx,0.21502066340161136,155.0,-210.0,0.3666469544648137,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,blk,starter,0.33356259623826034,0.5,0.5,betmgm,0.22596197983209937,135.0,-190.0,0.3937542430414121,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,stocks,starter,1.137302017859568,1.5,1.5,betparx,0.2963369183260614,-127.0,-105.0,0.5220573491076799,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,pa,starter,17.920443728376785,16.5,16.5,betmgm,0.5802990906468282,-105.0,-130.0,0.4753937007874017,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,pr,starter,18.8539953183988,17.5,17.5,bovada,0.5734955003423368,-115.0,-115.0,0.5,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,ra,starter,7.3730105137800885,6.5,6.5,betmgm,0.6511278419311965,-110.0,-120.0,0.48987854251012153,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716136,pra,starter,22.073724780277814,20.5,20.5,betparx,0.5830825849562601,102.0,-136.0,0.46209273182957394,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,pts,starter,27.074465237931726,26.5,26.5,betmgm,0.5541599455549537,-125.0,-105.0,0.5203045685279188,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,reb,starter,3.811552576808661,3.5,3.5,betparx,0.5717427258409282,133.0,-180.0,0.40034315127251924,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,ast,starter,6.6105954930484145,5.5,5.5,betparx,0.7124596993146193,-143.0,108.0,0.5503663681444749,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,fg3m,starter,1.9860652072965097,2.5,2.5,betmgm,0.37098365353928486,115.0,-155.0,0.43348916277093075,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,tov,starter,1.486607559477901,,,,,,,,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,stl,starter,0.6529189907218552,0.5,0.5,betparx,0.3537015062249928,-175.0,130.0,0.5940959409594095,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,blk,starter,0.30444055918887425,0.5,0.5,betmgm,0.2391499076180225,475.0,-1000.0,0.16058394160583941,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,stocks,starter,0.9629754032920791,,,,,,,,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,pa,starter,33.68506073098013,32.5,32.5,betmgm,0.570342983228567,-125.0,-105.0,0.5203045685279188,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,pr,starter,30.886017814740388,29.5,29.5,betmgm,0.5852369432532993,-115.0,-115.0,0.5,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,ra,starter,10.422148069857071,9.5,9.5,betmgm,0.645547780258048,105.0,-140.0,0.4554079696394686,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716136,pra,starter,37.496613307788735,35.5,35.5,betparx,0.6060002557850189,-114.0,-117.0,0.4969864995178399,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,pts,starter,17.054483918489815,14.5,14.5,betmgm,0.6724227190779515,-115.0,-115.0,0.5,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,reb,starter,4.607616471556697,3.5,3.5,betmgm,0.7466133413726206,100.0,-135.0,0.4653465346534653,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,ast,starter,5.197525629290567,5.5,5.5,betmgm,0.42871489033219995,-125.0,-105.0,0.5203045685279188,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,fg3m,starter,1.4094861277852613,1.5,1.5,betmgm,0.4218778076918537,125.0,-165.0,0.4165029469548134,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,tov,starter,1.5038078323521193,,,,,,,,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,NYK,21716136,stl,starter,0.5898894640052346,0.5,0.5,betparx,0.3673078682050478,-250.0,185.0,0.6705882352941177,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/aggregate_snapshot_scoring.csv`

- bytes: `204`
- rows: `1`
- columns: `7`

Compact first 30 rows:

```csv
game_id,snapshot_type
21716136,current_live

```
