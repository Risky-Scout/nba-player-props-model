# Reviewable Delivery Preview — 2026-06-05 — derek_game_snapshots

GitHub may refuse to render large CSV files. This file is intentionally small.

---

## `derek_game_snapshots/21716135/current_live/contextual_feature_audit.csv`

- bytes: `4,825`
- rows: `15`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716135
Landry Shamet,414,NYK,21716135
Luke Kornet,261,SAS,21716135
Jalen Brunson,73,NYK,21716135
Josh Hart,202,NYK,21716135
Stephon Castle,1028025261,SAS,21716135
Devin Vassell,3547246,SAS,21716135
Mitchell Robinson,399,NYK,21716135
Julian Champagnie,38017649,SAS,21716135
OG Anunoby,18,NYK,21716135
Dylan Harper,1057262518,SAS,21716135
Keldon Johnson,666682,SAS,21716135
Mikal Bridges,61,NYK,21716135
Victor Wembanyama,56677822,SAS,21716135
Karl-Anthony Towns,447,NYK,21716135

```

---

## `derek_game_snapshots/21716135/current_live/contextual_feature_audit.parquet`

- bytes: `29,854`
- rows: `15`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716135
Landry Shamet,414,NYK,21716135
Luke Kornet,261,SAS,21716135
Jalen Brunson,73,NYK,21716135
Josh Hart,202,NYK,21716135
Stephon Castle,1028025261,SAS,21716135
Devin Vassell,3547246,SAS,21716135
Mitchell Robinson,399,NYK,21716135
Julian Champagnie,38017649,SAS,21716135
OG Anunoby,18,NYK,21716135
Dylan Harper,1057262518,SAS,21716135
Keldon Johnson,666682,SAS,21716135
Mikal Bridges,61,NYK,21716135
Victor Wembanyama,56677822,SAS,21716135
Karl-Anthony Towns,447,NYK,21716135

```

---

## `derek_game_snapshots/21716135/current_live/derek_live_predictions.parquet`

- bytes: `40,000`
- rows: `43`
- columns: `47`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.076
De'Aaron Fox,161,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.1682
Landry Shamet,414,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.1654
Landry Shamet,414,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0838
Luke Kornet,261,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.1087
Jalen Brunson,73,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.092
Jalen Brunson,73,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.1583
Josh Hart,202,NYK,SAS,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.0573
Josh Hart,202,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.5,-0.1545
Josh Hart,202,NYK,SAS,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,-0.1146
Josh Hart,202,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.0595
Josh Hart,202,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.0428
Stephon Castle,1028025261,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.2263
Devin Vassell,3547246,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,12.5,-0.1569
Devin Vassell,3547246,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1085
Devin Vassell,3547246,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.1109
Mitchell Robinson,399,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,5.5,-0.0906
Mitchell Robinson,399,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0991
Mitchell Robinson,399,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.2235
Julian Champagnie,38017649,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.5,-0.1671
Julian Champagnie,38017649,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1416
Julian Champagnie,38017649,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.5,-0.086
OG Anunoby,18,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,0.0818
OG Anunoby,18,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1703
OG Anunoby,18,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.1792
Dylan Harper,1057262518,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.5,-0.1402
Dylan Harper,1057262518,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1881
Dylan Harper,1057262518,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,0.0788
Keldon Johnson,666682,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.1236
Keldon Johnson,666682,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2274

```

---

## `derek_game_snapshots/21716135/current_live/full_pmf_wide.csv`

- bytes: `47,434`
- rows: `43`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.076
De'Aaron Fox,161,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.1682
Landry Shamet,414,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.1654
Landry Shamet,414,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0838
Luke Kornet,261,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.1087
Jalen Brunson,73,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.092
Jalen Brunson,73,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.1583
Josh Hart,202,NYK,SAS,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.0573
Josh Hart,202,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.5,-0.1545
Josh Hart,202,NYK,SAS,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,-0.1146
Josh Hart,202,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.0595
Josh Hart,202,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.0428
Stephon Castle,1028025261,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.2263
Devin Vassell,3547246,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,12.5,-0.1569
Devin Vassell,3547246,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1085
Devin Vassell,3547246,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.1109
Mitchell Robinson,399,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,5.5,-0.0906
Mitchell Robinson,399,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0991
Mitchell Robinson,399,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.2235
Julian Champagnie,38017649,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.5,-0.1671
Julian Champagnie,38017649,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1416
Julian Champagnie,38017649,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.5,-0.086
OG Anunoby,18,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,0.0818
OG Anunoby,18,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1703
OG Anunoby,18,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.1792
Dylan Harper,1057262518,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.5,-0.1402
Dylan Harper,1057262518,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1881
Dylan Harper,1057262518,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,0.0788
Keldon Johnson,666682,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.1236
Keldon Johnson,666682,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2274

```

---

## `derek_game_snapshots/21716135/current_live/full_pmf_wide.parquet`

- bytes: `73,603`
- rows: `43`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.076
De'Aaron Fox,161,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.1682
Landry Shamet,414,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.1654
Landry Shamet,414,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0838
Luke Kornet,261,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.1087
Jalen Brunson,73,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.092
Jalen Brunson,73,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.1583
Josh Hart,202,NYK,SAS,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.0573
Josh Hart,202,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.5,-0.1545
Josh Hart,202,NYK,SAS,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,-0.1146
Josh Hart,202,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.0595
Josh Hart,202,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.0428
Stephon Castle,1028025261,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.2263
Devin Vassell,3547246,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,12.5,-0.1569
Devin Vassell,3547246,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1085
Devin Vassell,3547246,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.1109
Mitchell Robinson,399,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,5.5,-0.0906
Mitchell Robinson,399,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0991
Mitchell Robinson,399,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.2235
Julian Champagnie,38017649,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.5,-0.1671
Julian Champagnie,38017649,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1416
Julian Champagnie,38017649,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.5,-0.086
OG Anunoby,18,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,0.0818
OG Anunoby,18,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1703
OG Anunoby,18,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.1792
Dylan Harper,1057262518,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.5,-0.1402
Dylan Harper,1057262518,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1881
Dylan Harper,1057262518,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,0.0788
Keldon Johnson,666682,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.1236
Keldon Johnson,666682,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2274

```

---

## `derek_game_snapshots/21716135/current_live/game_context.csv`

- bytes: `605`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,NYK,21716135
Landry Shamet,414,NYK,SAS,21716135
Luke Kornet,261,SAS,NYK,21716135
Jalen Brunson,73,NYK,SAS,21716135
Josh Hart,202,NYK,SAS,21716135
Stephon Castle,1028025261,SAS,NYK,21716135
Devin Vassell,3547246,SAS,NYK,21716135
Mitchell Robinson,399,NYK,SAS,21716135
Julian Champagnie,38017649,SAS,NYK,21716135
OG Anunoby,18,NYK,SAS,21716135
Dylan Harper,1057262518,SAS,NYK,21716135
Keldon Johnson,666682,SAS,NYK,21716135
Mikal Bridges,61,NYK,SAS,21716135
Victor Wembanyama,56677822,SAS,NYK,21716135
Karl-Anthony Towns,447,NYK,SAS,21716135

```

---

## `derek_game_snapshots/21716135/current_live/game_context.parquet`

- bytes: `3,649`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,NYK,21716135
Landry Shamet,414,NYK,SAS,21716135
Luke Kornet,261,SAS,NYK,21716135
Jalen Brunson,73,NYK,SAS,21716135
Josh Hart,202,NYK,SAS,21716135
Stephon Castle,1028025261,SAS,NYK,21716135
Devin Vassell,3547246,SAS,NYK,21716135
Mitchell Robinson,399,NYK,SAS,21716135
Julian Champagnie,38017649,SAS,NYK,21716135
OG Anunoby,18,NYK,SAS,21716135
Dylan Harper,1057262518,SAS,NYK,21716135
Keldon Johnson,666682,SAS,NYK,21716135
Mikal Bridges,61,NYK,SAS,21716135
Victor Wembanyama,56677822,SAS,NYK,21716135
Karl-Anthony Towns,447,NYK,SAS,21716135

```

---

## `derek_game_snapshots/21716135/current_live/injury_availability_context.csv`

- bytes: `594`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716135
Landry Shamet,414,NYK,21716135
Luke Kornet,261,SAS,21716135
Jalen Brunson,73,NYK,21716135
Josh Hart,202,NYK,21716135
Stephon Castle,1028025261,SAS,21716135
Devin Vassell,3547246,SAS,21716135
Mitchell Robinson,399,NYK,21716135
Julian Champagnie,38017649,SAS,21716135
OG Anunoby,18,NYK,21716135
Dylan Harper,1057262518,SAS,21716135
Keldon Johnson,666682,SAS,21716135
Mikal Bridges,61,NYK,21716135
Victor Wembanyama,56677822,SAS,21716135
Karl-Anthony Towns,447,NYK,21716135

```

---

## `derek_game_snapshots/21716135/current_live/injury_availability_context.parquet`

- bytes: `3,851`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716135
Landry Shamet,414,NYK,21716135
Luke Kornet,261,SAS,21716135
Jalen Brunson,73,NYK,21716135
Josh Hart,202,NYK,21716135
Stephon Castle,1028025261,SAS,21716135
Devin Vassell,3547246,SAS,21716135
Mitchell Robinson,399,NYK,21716135
Julian Champagnie,38017649,SAS,21716135
OG Anunoby,18,NYK,21716135
Dylan Harper,1057262518,SAS,21716135
Keldon Johnson,666682,SAS,21716135
Mikal Bridges,61,NYK,21716135
Victor Wembanyama,56677822,SAS,21716135
Karl-Anthony Towns,447,NYK,21716135

```

---

## `derek_game_snapshots/21716135/current_live/lineup_context.csv`

- bytes: `1,623`
- rows: `15`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21716135,reb
Landry Shamet,414,NYK,21716135,fg3m
Luke Kornet,261,SAS,21716135,blk
Jalen Brunson,73,NYK,21716135,fg3m
Josh Hart,202,NYK,21716135,pts
Stephon Castle,1028025261,SAS,21716135,ast
Devin Vassell,3547246,SAS,21716135,pts
Mitchell Robinson,399,NYK,21716135,reb
Julian Champagnie,38017649,SAS,21716135,pts
OG Anunoby,18,NYK,21716135,reb
Dylan Harper,1057262518,SAS,21716135,pts
Keldon Johnson,666682,SAS,21716135,reb
Mikal Bridges,61,NYK,21716135,pts
Victor Wembanyama,56677822,SAS,21716135,pts
Karl-Anthony Towns,447,NYK,21716135,pts

```

---

## `derek_game_snapshots/21716135/current_live/lineup_context.parquet`

- bytes: `8,435`
- rows: `15`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21716135,reb
Landry Shamet,414,NYK,21716135,fg3m
Luke Kornet,261,SAS,21716135,blk
Jalen Brunson,73,NYK,21716135,fg3m
Josh Hart,202,NYK,21716135,pts
Stephon Castle,1028025261,SAS,21716135,ast
Devin Vassell,3547246,SAS,21716135,pts
Mitchell Robinson,399,NYK,21716135,reb
Julian Champagnie,38017649,SAS,21716135,pts
OG Anunoby,18,NYK,21716135,reb
Dylan Harper,1057262518,SAS,21716135,pts
Keldon Johnson,666682,SAS,21716135,reb
Mikal Bridges,61,NYK,21716135,pts
Victor Wembanyama,56677822,SAS,21716135,pts
Karl-Anthony Towns,447,NYK,21716135,pts

```

---

## `derek_game_snapshots/21716135/current_live/market_comparison.csv`

- bytes: `58,817`
- rows: `43`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.0122,0.0651,3.5,0.076
De'Aaron Fox,161,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.6815,0.0428,5.5,-0.1682
Landry Shamet,414,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.1809,0.227,1.5,-0.1654
Landry Shamet,414,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5483,0.6309,0.5,-0.0838
Luke Kornet,261,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.3671,0.7298,0.5,-0.1087
Jalen Brunson,73,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.898,0.1543,2.5,-0.092
Jalen Brunson,73,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.1985,0.2873,0.5,0.1583
Josh Hart,202,NYK,SAS,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.8267,0.0231,11.5,-0.0573
Josh Hart,202,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.5939,0.0171,8.5,-0.1545
Josh Hart,202,NYK,SAS,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.992,0.0578,4.5,-0.1146
Josh Hart,202,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.4527,0.2159,1.5,-0.0595
Josh Hart,202,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.2564,0.7917,0.5,-0.0428
Stephon Castle,1028025261,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.1635,0.0378,6.5,-0.2263
Devin Vassell,3547246,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.0003,0.0236,12.5,-0.1569
Devin Vassell,3547246,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.9841,0.2165,2.5,-0.1085
Devin Vassell,3547246,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.3028,0.7463,0.5,-0.1109
Mitchell Robinson,399,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,5.021,0.0475,5.5,-0.0906
Mitchell Robinson,399,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5184,0.6435,0.5,-0.0991
Mitchell Robinson,399,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.3648,0.7339,0.5,-0.2235
Julian Champagnie,38017649,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,9.4684,0.0247,10.5,-0.1671
Julian Champagnie,38017649,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.0718,0.0383,5.5,-0.1416
Julian Champagnie,38017649,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.2991,0.0774,2.5,-0.086
OG Anunoby,18,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.8064,0.0333,5.5,0.0818
OG Anunoby,18,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.567,0.1642,1.5,-0.1703
OG Anunoby,18,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.4945,0.6544,0.5,-0.1792
Dylan Harper,1057262518,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.4713,0.024,12.5,-0.1402
Dylan Harper,1057262518,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.2113,0.1816,3.5,-0.1881
Dylan Harper,1057262518,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.0361,0.3097,0.5,0.0788
Keldon Johnson,666682,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.2568,0.1973,2.5,-0.1236
Keldon Johnson,666682,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4459,0.2151,0.5,0.2274

```

---

## `derek_game_snapshots/21716135/current_live/market_comparison.parquet`

- bytes: `88,844`
- rows: `43`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.012221999599278,0.0651,3.5,0.076
De'Aaron Fox,161,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.681522283425138,0.0428,5.5,-0.1682
Landry Shamet,414,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.1809,0.227,1.5,-0.1654
Landry Shamet,414,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5483,0.6309,0.5,-0.0838
Luke Kornet,261,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.3671,0.7298,0.5,-0.1087
Jalen Brunson,73,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.8980000000000001,0.1543,2.5,-0.092
Jalen Brunson,73,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.1985000000000001,0.2873,0.5,0.1583
Josh Hart,202,NYK,SAS,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.826684041700078,0.0231,11.5,-0.0573
Josh Hart,202,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.59390964639888,0.0171,8.5,-0.1545
Josh Hart,202,NYK,SAS,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.9919847710650225,0.0578,4.5,-0.1146
Josh Hart,202,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.4527,0.2159,1.5,-0.0595
Josh Hart,202,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.25635127025405086,0.7917,0.5,-0.0428
Stephon Castle,1028025261,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.1634615384615365,0.0378,6.5,-0.2263
Devin Vassell,3547246,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.000300721732161,0.0236,12.5,-0.1569
Devin Vassell,3547246,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.9840761141712568,0.2165,2.5,-0.1085
Devin Vassell,3547246,SAS,NYK,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.3028,0.7463,0.5,-0.1109
Mitchell Robinson,399,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,5.0210420841683385,0.0475,5.5,-0.0906
Mitchell Robinson,399,NYK,SAS,21716135,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5184,0.6435,0.5,-0.0991
Mitchell Robinson,399,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.36483648364836485,0.7339,0.5,-0.2235
Julian Champagnie,38017649,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,9.468439538384343,0.0247,10.5,-0.1671
Julian Champagnie,38017649,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.071750676420483,0.0383,5.5,-0.1416
Julian Champagnie,38017649,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.2990999999999997,0.0774,2.5,-0.086
OG Anunoby,18,NYK,SAS,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.806409614421631,0.0333,5.5,0.0818
OG Anunoby,18,NYK,SAS,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5670432956704332,0.1642,1.5,-0.1703
OG Anunoby,18,NYK,SAS,21716135,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.4945,0.6544,0.5,-0.1792
Dylan Harper,1057262518,SAS,NYK,21716135,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.471343972698985,0.024,12.5,-0.1402
Dylan Harper,1057262518,SAS,NYK,21716135,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.211332465712284,0.1816,3.5,-0.1881
Dylan Harper,1057262518,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.0361036103610362,0.3097,0.5,0.0788
Keldon Johnson,666682,SAS,NYK,21716135,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.256787897004308,0.1973,2.5,-0.1236
Keldon Johnson,666682,SAS,NYK,21716135,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4459,0.2151,0.5,0.2274

```

---

## `derek_game_snapshots/21716135/current_live/outcome_level_probabilities.csv`

- bytes: `104,924`
- rows: `573`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21716135,reb,0,0.0652,3.5,current_live
De'Aaron Fox,161,21716135,reb,1,0.1077,3.5,current_live
De'Aaron Fox,161,21716135,reb,2,0.1333,3.5,current_live
De'Aaron Fox,161,21716135,reb,3,0.1428,3.5,current_live
De'Aaron Fox,161,21716135,reb,4,0.1625,3.5,current_live
De'Aaron Fox,161,21716135,reb,5,0.129,3.5,current_live
De'Aaron Fox,161,21716135,reb,6,0.0932,3.5,current_live
De'Aaron Fox,161,21716135,reb,7,0.0732,3.5,current_live
De'Aaron Fox,161,21716135,reb,8,0.0405,3.5,current_live
De'Aaron Fox,161,21716135,reb,9,0.0247,3.5,current_live
De'Aaron Fox,161,21716135,reb,10,0.0163,3.5,current_live
De'Aaron Fox,161,21716135,reb,11,0.007,3.5,current_live
De'Aaron Fox,161,21716135,reb,12,0.0027,3.5,current_live
De'Aaron Fox,161,21716135,reb,13,0.0018,3.5,current_live
De'Aaron Fox,161,21716135,ast,0,0.0429,5.5,current_live
De'Aaron Fox,161,21716135,ast,1,0.0586,5.5,current_live
De'Aaron Fox,161,21716135,ast,2,0.0939,5.5,current_live
De'Aaron Fox,161,21716135,ast,3,0.1371,5.5,current_live
De'Aaron Fox,161,21716135,ast,4,0.1788,5.5,current_live
De'Aaron Fox,161,21716135,ast,5,0.1203,5.5,current_live
De'Aaron Fox,161,21716135,ast,6,0.1469,5.5,current_live
De'Aaron Fox,161,21716135,ast,7,0.093,5.5,current_live
De'Aaron Fox,161,21716135,ast,8,0.0536,5.5,current_live
De'Aaron Fox,161,21716135,ast,9,0.0366,5.5,current_live
De'Aaron Fox,161,21716135,ast,10,0.018,5.5,current_live
De'Aaron Fox,161,21716135,ast,11,0.012,5.5,current_live
De'Aaron Fox,161,21716135,ast,12,0.0049,5.5,current_live
De'Aaron Fox,161,21716135,ast,13,0.0022,5.5,current_live
De'Aaron Fox,161,21716135,ast,14,0.0012,5.5,current_live
Landry Shamet,414,21716135,fg3m,0,0.227,1.5,current_live

```

---

## `derek_game_snapshots/21716135/current_live/outcome_level_probabilities.parquet`

- bytes: `19,270`
- rows: `573`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21716135,reb,0,0.06521739130434784,3.5,current_live
De'Aaron Fox,161,21716135,reb,1,0.10769384892807053,3.5,current_live
De'Aaron Fox,161,21716135,reb,2,0.13334001202163895,3.5,current_live
De'Aaron Fox,161,21716135,reb,3,0.1427569625325586,3.5,current_live
De'Aaron Fox,161,21716135,reb,4,0.1624924864756562,3.5,current_live
De'Aaron Fox,161,21716135,reb,5,0.12903225806451613,3.5,current_live
De'Aaron Fox,161,21716135,reb,6,0.09316770186335403,3.5,current_live
De'Aaron Fox,161,21716135,reb,7,0.07323181727108796,3.5,current_live
De'Aaron Fox,161,21716135,reb,8,0.04047285113203767,3.5,current_live
De'Aaron Fox,161,21716135,reb,9,0.024744540172310158,3.5,current_live
De'Aaron Fox,161,21716135,reb,10,0.01632939290723302,3.5,current_live
De'Aaron Fox,161,21716135,reb,11,0.007012622720897616,3.5,current_live
De'Aaron Fox,161,21716135,reb,12,0.0027048687637747947,3.5,current_live
De'Aaron Fox,161,21716135,reb,13,0.0018032458425165298,3.5,current_live
De'Aaron Fox,161,21716135,ast,0,0.04286429644466701,5.5,current_live
De'Aaron Fox,161,21716135,ast,1,0.05858788182273411,5.5,current_live
De'Aaron Fox,161,21716135,ast,2,0.09394091136705059,5.5,current_live
De'Aaron Fox,161,21716135,ast,3,0.13710565848773162,5.5,current_live
De'Aaron Fox,161,21716135,ast,4,0.17876815222834253,5.5,current_live
De'Aaron Fox,161,21716135,ast,5,0.12028042063094643,5.5,current_live
De'Aaron Fox,161,21716135,ast,6,0.1469203805708563,5.5,current_live
De'Aaron Fox,161,21716135,ast,7,0.09303955933900852,5.5,current_live
De'Aaron Fox,161,21716135,ast,8,0.053580370555833756,5.5,current_live
De'Aaron Fox,161,21716135,ast,9,0.03655483224837256,5.5,current_live
De'Aaron Fox,161,21716135,ast,10,0.018027040560841263,5.5,current_live
De'Aaron Fox,161,21716135,ast,11,0.012018027040560843,5.5,current_live
De'Aaron Fox,161,21716135,ast,12,0.0049073610415623446,5.5,current_live
De'Aaron Fox,161,21716135,ast,13,0.0022033049574361548,5.5,current_live
De'Aaron Fox,161,21716135,ast,14,0.0012018027040560841,5.5,current_live
Landry Shamet,414,21716135,fg3m,0,0.227,1.5,current_live

```

---

## `derek_game_snapshots/21716135/current_live/pmf_driver_decomposition.csv`

- bytes: `3,163`
- rows: `15`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21716135,reb,3.5
Landry Shamet,414,NYK,21716135,fg3m,1.5
Luke Kornet,261,SAS,21716135,blk,0.5
Jalen Brunson,73,NYK,21716135,fg3m,2.5
Josh Hart,202,NYK,21716135,pts,11.5
Stephon Castle,1028025261,SAS,21716135,ast,6.5
Devin Vassell,3547246,SAS,21716135,pts,12.5
Mitchell Robinson,399,NYK,21716135,reb,5.5
Julian Champagnie,38017649,SAS,21716135,pts,10.5
OG Anunoby,18,NYK,21716135,reb,5.5
Dylan Harper,1057262518,SAS,21716135,pts,12.5
Keldon Johnson,666682,SAS,21716135,reb,2.5
Mikal Bridges,61,NYK,21716135,pts,11.5
Victor Wembanyama,56677822,SAS,21716135,pts,27.5
Karl-Anthony Towns,447,NYK,21716135,pts,16.5

```

---

## `derek_game_snapshots/21716135/current_live/pmf_driver_decomposition.parquet`

- bytes: `14,466`
- rows: `15`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21716135,reb,3.5
Landry Shamet,414,NYK,21716135,fg3m,1.5
Luke Kornet,261,SAS,21716135,blk,0.5
Jalen Brunson,73,NYK,21716135,fg3m,2.5
Josh Hart,202,NYK,21716135,pts,11.5
Stephon Castle,1028025261,SAS,21716135,ast,6.5
Devin Vassell,3547246,SAS,21716135,pts,12.5
Mitchell Robinson,399,NYK,21716135,reb,5.5
Julian Champagnie,38017649,SAS,21716135,pts,10.5
OG Anunoby,18,NYK,21716135,reb,5.5
Dylan Harper,1057262518,SAS,21716135,pts,12.5
Keldon Johnson,666682,SAS,21716135,reb,2.5
Mikal Bridges,61,NYK,21716135,pts,11.5
Victor Wembanyama,56677822,SAS,21716135,pts,27.5
Karl-Anthony Towns,447,NYK,21716135,pts,16.5

```

---

## `derek_game_snapshots/21716135/current_live/prediction_input_audit.csv`

- bytes: `2,944`
- rows: `43`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716135,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716135,ast,5.5
Landry Shamet,414,NYK,SAS,21716135,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716135,stl,0.5
Luke Kornet,261,SAS,NYK,21716135,blk,0.5
Jalen Brunson,73,NYK,SAS,21716135,fg3m,2.5
Jalen Brunson,73,NYK,SAS,21716135,stl,0.5
Josh Hart,202,NYK,SAS,21716135,pts,11.5
Josh Hart,202,NYK,SAS,21716135,reb,8.5
Josh Hart,202,NYK,SAS,21716135,ast,4.5
Josh Hart,202,NYK,SAS,21716135,fg3m,1.5
Josh Hart,202,NYK,SAS,21716135,blk,0.5
Stephon Castle,1028025261,SAS,NYK,21716135,ast,6.5
Devin Vassell,3547246,SAS,NYK,21716135,pts,12.5
Devin Vassell,3547246,SAS,NYK,21716135,ast,2.5
Devin Vassell,3547246,SAS,NYK,21716135,blk,0.5
Mitchell Robinson,399,NYK,SAS,21716135,reb,5.5
Mitchell Robinson,399,NYK,SAS,21716135,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716135,blk,0.5
Julian Champagnie,38017649,SAS,NYK,21716135,pts,10.5
Julian Champagnie,38017649,SAS,NYK,21716135,reb,5.5
Julian Champagnie,38017649,SAS,NYK,21716135,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716135,reb,5.5
OG Anunoby,18,NYK,SAS,21716135,fg3m,1.5
OG Anunoby,18,NYK,SAS,21716135,blk,0.5
Dylan Harper,1057262518,SAS,NYK,21716135,pts,12.5
Dylan Harper,1057262518,SAS,NYK,21716135,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716135,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716135,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716135,fg3m,0.5

```

---

## `derek_game_snapshots/21716135/current_live/prediction_input_audit.parquet`

- bytes: `5,427`
- rows: `43`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716135,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716135,ast,5.5
Landry Shamet,414,NYK,SAS,21716135,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716135,stl,0.5
Luke Kornet,261,SAS,NYK,21716135,blk,0.5
Jalen Brunson,73,NYK,SAS,21716135,fg3m,2.5
Jalen Brunson,73,NYK,SAS,21716135,stl,0.5
Josh Hart,202,NYK,SAS,21716135,pts,11.5
Josh Hart,202,NYK,SAS,21716135,reb,8.5
Josh Hart,202,NYK,SAS,21716135,ast,4.5
Josh Hart,202,NYK,SAS,21716135,fg3m,1.5
Josh Hart,202,NYK,SAS,21716135,blk,0.5
Stephon Castle,1028025261,SAS,NYK,21716135,ast,6.5
Devin Vassell,3547246,SAS,NYK,21716135,pts,12.5
Devin Vassell,3547246,SAS,NYK,21716135,ast,2.5
Devin Vassell,3547246,SAS,NYK,21716135,blk,0.5
Mitchell Robinson,399,NYK,SAS,21716135,reb,5.5
Mitchell Robinson,399,NYK,SAS,21716135,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716135,blk,0.5
Julian Champagnie,38017649,SAS,NYK,21716135,pts,10.5
Julian Champagnie,38017649,SAS,NYK,21716135,reb,5.5
Julian Champagnie,38017649,SAS,NYK,21716135,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716135,reb,5.5
OG Anunoby,18,NYK,SAS,21716135,fg3m,1.5
OG Anunoby,18,NYK,SAS,21716135,blk,0.5
Dylan Harper,1057262518,SAS,NYK,21716135,pts,12.5
Dylan Harper,1057262518,SAS,NYK,21716135,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716135,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716135,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716135,fg3m,0.5

```

---

## `derek_game_snapshots/21716135/current_live/prop_summary.csv`

- bytes: `2,158`
- rows: `43`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716135,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716135,ast,5.5
Landry Shamet,414,NYK,SAS,21716135,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716135,stl,0.5
Luke Kornet,261,SAS,NYK,21716135,blk,0.5
Jalen Brunson,73,NYK,SAS,21716135,fg3m,2.5
Jalen Brunson,73,NYK,SAS,21716135,stl,0.5
Josh Hart,202,NYK,SAS,21716135,pts,11.5
Josh Hart,202,NYK,SAS,21716135,reb,8.5
Josh Hart,202,NYK,SAS,21716135,ast,4.5
Josh Hart,202,NYK,SAS,21716135,fg3m,1.5
Josh Hart,202,NYK,SAS,21716135,blk,0.5
Stephon Castle,1028025261,SAS,NYK,21716135,ast,6.5
Devin Vassell,3547246,SAS,NYK,21716135,pts,12.5
Devin Vassell,3547246,SAS,NYK,21716135,ast,2.5
Devin Vassell,3547246,SAS,NYK,21716135,blk,0.5
Mitchell Robinson,399,NYK,SAS,21716135,reb,5.5
Mitchell Robinson,399,NYK,SAS,21716135,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716135,blk,0.5
Julian Champagnie,38017649,SAS,NYK,21716135,pts,10.5
Julian Champagnie,38017649,SAS,NYK,21716135,reb,5.5
Julian Champagnie,38017649,SAS,NYK,21716135,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716135,reb,5.5
OG Anunoby,18,NYK,SAS,21716135,fg3m,1.5
OG Anunoby,18,NYK,SAS,21716135,blk,0.5
Dylan Harper,1057262518,SAS,NYK,21716135,pts,12.5
Dylan Harper,1057262518,SAS,NYK,21716135,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716135,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716135,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716135,fg3m,0.5

```

---

## `derek_game_snapshots/21716135/current_live/prop_summary.parquet`

- bytes: `4,836`
- rows: `43`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716135,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716135,ast,5.5
Landry Shamet,414,NYK,SAS,21716135,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716135,stl,0.5
Luke Kornet,261,SAS,NYK,21716135,blk,0.5
Jalen Brunson,73,NYK,SAS,21716135,fg3m,2.5
Jalen Brunson,73,NYK,SAS,21716135,stl,0.5
Josh Hart,202,NYK,SAS,21716135,pts,11.5
Josh Hart,202,NYK,SAS,21716135,reb,8.5
Josh Hart,202,NYK,SAS,21716135,ast,4.5
Josh Hart,202,NYK,SAS,21716135,fg3m,1.5
Josh Hart,202,NYK,SAS,21716135,blk,0.5
Stephon Castle,1028025261,SAS,NYK,21716135,ast,6.5
Devin Vassell,3547246,SAS,NYK,21716135,pts,12.5
Devin Vassell,3547246,SAS,NYK,21716135,ast,2.5
Devin Vassell,3547246,SAS,NYK,21716135,blk,0.5
Mitchell Robinson,399,NYK,SAS,21716135,reb,5.5
Mitchell Robinson,399,NYK,SAS,21716135,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716135,blk,0.5
Julian Champagnie,38017649,SAS,NYK,21716135,pts,10.5
Julian Champagnie,38017649,SAS,NYK,21716135,reb,5.5
Julian Champagnie,38017649,SAS,NYK,21716135,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716135,reb,5.5
OG Anunoby,18,NYK,SAS,21716135,fg3m,1.5
OG Anunoby,18,NYK,SAS,21716135,blk,0.5
Dylan Harper,1057262518,SAS,NYK,21716135,pts,12.5
Dylan Harper,1057262518,SAS,NYK,21716135,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716135,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716135,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716135,fg3m,0.5

```

---

## `derek_game_snapshots/21716135/morning/full_pmf_wide.csv`

- bytes: `378,362`
- rows: `192`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,6.2868,6.2868,6,6,0.0029,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,1.9543,1.9543,2,2,0.0505,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,1.5099,1.5099,1,0,0.3687,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,1.1869,1.1869,1,1,0.1168,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,0.6669,0.6669,0,0,0.6472,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,0.3925,0.3925,0,0,0.7734,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.4699,33.3382,0.05,1.0594,1.0594,0,0,0.5005,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.4699,33.3382,0.05,18.0839,18.0839,18,18,0.0001,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.4699,33.3382,0.05,22.4163,22.4163,22,22,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.4699,33.3382,0.05,8.2411,8.2411,8,8,0.0001,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.4699,33.3382,0.05,24.3706,24.3706,24,24,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.7925,32.784,0.05,14.707,14.707,15,15,0.0023,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.7925,32.784,0.05,3.9999,3.9999,4,4,0.0073,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.7925,32.784,0.05,2.491,2.491,2,2,0.0224,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.7925,32.784,0.05,1.15,1.15,1,0,0.3917,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.7925,32.784,0.05,1.1428,1.1428,1,1,0.1158,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.7925,32.784,0.05,0.6527,0.6527,0,0,0.6377,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.7925,32.784,0.05,0.3375,0.3375,0,0,0.7773,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.7925,32.784,0.05,1.044,1.044,1,0,0.4957,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.7925,32.784,0.05,17.198,17.198,17,18,0.0001,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.7925,32.784,0.05,18.7069,18.7069,19,19,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.7925,32.784,0.05,6.4909,6.4909,6,6,0.0002,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.7925,32.784,0.05,21.1979,21.1979,21,21,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.864,36.0076,0.05,26.2798,26.2798,26,27,0.0001,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.864,36.0076,0.05,3.6121,3.6121,4,3,0.0086,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.864,36.0076,0.05,6.3696,6.3696,6,7,0.0042,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.864,36.0076,0.05,1.6948,1.6948,1,0,0.3697,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.864,36.0076,0.05,1.4102,1.4102,1,1,0.1152,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.864,36.0076,0.05,0.6351,0.6351,0,0,0.6321,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z

```

---

## `derek_game_snapshots/21716135/morning/full_pmf_wide.parquet`

- bytes: `212,643`
- rows: `192`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072272,16,16,0.0015402785823751034,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,6.286757263430152,6.286757263430153,6,6,0.0028618359663884355,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,1.9543282902093586,1.9543282902093582,2,2,0.05048511935716426,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,1.509884546755963,1.509884546755963,1,0,0.36869421948612224,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,1.186944914146279,1.1869449141462787,1,1,0.11677677626453606,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,0.6668570409518642,0.666857040951864,0,0,0.6472253806875063,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,0.3925362692222983,0.39253626922229834,0,0,0.7733589865305006,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.469908380500705,33.33820903857685,0.050000000000000044,1.0593933101741624,1.0593933101741624,0,0,0.5005375644653074,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.469908380500705,33.33820903857685,0.050000000000000044,18.0838555452816,18.083855545281587,18,18,7.776114807449092e-05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.469908380500705,33.33820903857685,0.050000000000000044,22.41628451850242,22.416284518502415,22,22,4.408024645298865e-06,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.469908380500705,33.33820903857685,0.050000000000000044,8.241085553639504,8.241085553639508,8,8,0.00014448013034374575,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.469908380500705,33.33820903857685,0.050000000000000044,24.370612808711726,24.370612808711712,24,24,2.22539650347235e-07,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.792468565351026,32.784041322361986,0.050000000000000044,14.706955487465326,14.706955487465324,15,15,0.0022942195417340635,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.792468565351026,32.784041322361986,0.050000000000000044,3.999927000726594,3.9999270007265952,4,4,0.007273837723459671,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.792468565351026,32.784041322361986,0.050000000000000044,2.491009154652596,2.491009154652596,2,2,0.02237243832689663,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.792468565351026,32.784041322361986,0.050000000000000044,1.1499603392725075,1.1499603392725075,1,0,0.39167187415131655,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.792468565351026,32.784041322361986,0.050000000000000044,1.1428230730755933,1.1428230730755933,1,1,0.11584960408675604,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.792468565351026,32.784041322361986,0.050000000000000044,0.652707507934642,0.652707507934642,0,0,0.6377363191191203,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.792468565351026,32.784041322361986,0.050000000000000044,0.3374507297425667,0.3374507297425666,0,0,0.7773366565880138,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.792468565351026,32.784041322361986,0.050000000000000044,1.0440384673637766,1.0440384673637766,1,0,0.4957358180888035,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.792468565351026,32.784041322361986,0.050000000000000044,17.19796464211786,17.197964642117878,17,18,5.132728520580644e-05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.792468565351026,32.784041322361986,0.050000000000000044,18.70688248819186,18.706882488191866,19,19,1.6687780648563602e-05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.792468565351026,32.784041322361986,0.050000000000000044,6.490936155379188,6.490936155379188,6,6,0.0001627334858679557,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Mikal Bridges,61,NYK,SAS,21716135,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.792468565351026,32.784041322361986,0.050000000000000044,21.197891642844464,21.197891642844475,21,21,3.7334634337276815e-07,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.863995131522344,36.0075895571501,0.050000000000000044,26.279787996444114,26.27978799644411,26,27,7.684956412012756e-05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.863995131522344,36.0075895571501,0.050000000000000044,3.612061552750179,3.612061552750179,4,3,0.00864008354505715,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.863995131522344,36.0075895571501,0.050000000000000044,6.369599140195987,6.369599140195989,6,7,0.004165561394352655,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.863995131522344,36.0075895571501,0.050000000000000044,1.6948196641364817,1.6948196641364814,1,0,0.3697473938742532,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.863995131522344,36.0075895571501,0.050000000000000044,1.4102168078435917,1.4102168078435913,1,1,0.11517803411987959,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
Jalen Brunson,73,NYK,SAS,21716135,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.863995131522344,36.0075895571501,0.050000000000000044,0.6350819458519261,0.6350819458519261,0,0,0.6320808364113999,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z

```

---

## `derek_game_snapshots/21716135/morning/market_comparison.csv`

- bytes: `2,607,886`
- rows: `2,782`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,fanduel,0.6003,-113,-113,0.5,0.1003,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,21.5,21.5,fanduel,0.1766,450,-800,0.1698,0.0068,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,20.5,20.5,fanduel,0.2205,370,-600,0.1989,0.0217,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,19.5,19.5,fanduel,0.2722,300,-450,0.234,0.0382,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,18.5,18.5,fanduel,0.316,230,-330,0.2831,0.0329,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,17.5,17.5,fanduel,0.3738,188,-260,0.3247,0.0491,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,16.5,16.5,fanduel,0.4567,146,-198,0.3796,0.0771,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,fanduel,0.6003,-113,-114,0.499,0.1014,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,13.5,13.5,fanduel,0.6627,-154,116,0.567,0.0956,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,12.5,12.5,fanduel,0.7169,-200,148,0.6231,0.0938,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,11.5,11.5,fanduel,0.7702,-270,194,0.6821,0.0881,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,10.5,10.5,fanduel,0.8292,-360,250,0.7326,0.0967,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,9.5,9.5,fanduel,0.866,-480,320,0.7766,0.0894,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,15.5,15.5,fanduel,0.5403,116,-154,0.433,0.1073,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,williamhill_us,0.6003,-125,-108,0.5169,0.0834,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,17.5,17.5,bovada,0.3738,170,-230,0.347,0.0268,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,16.5,16.5,bovada,0.4567,135,-180,0.3983,0.0584,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,15.5,15.5,bovada,0.5403,110,-145,0.4459,0.0944,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,bovada,0.6003,-120,-110,0.5101,0.0902,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,13.5,13.5,bovada,0.6627,-160,120,0.5752,0.0875,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,12.5,12.5,bovada,0.7169,-210,155,0.6334,0.0836,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,11.5,11.5,bovada,0.7702,-290,210,0.6974,0.0728,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,betmgm,0.6003,-120,-110,0.5101,0.0902,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,15.5,15.5,betrivers,0.5403,106,-143,0.452,0.0882,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,betrivers,0.6003,-124,-110,0.5138,0.0865,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,13.5,13.5,betrivers,0.6627,-167,120,0.5791,0.0835,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,draftkings,0.6003,-116,-110,0.5062,0.0941,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,hardrockbet_az,0.6003,-120,-110,0.5101,0.0902,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,hardrockbet,0.6003,-120,-110,0.5101,0.0902,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.4699,33.3382,0.05,16.1295,16.1295,16,16,0.0015,14.5,14.5,rebet,0.6003,-114,-112,0.5021,0.0983,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z

```

---

## `derek_game_snapshots/21716135/morning/market_comparison.parquet`

- bytes: `145,295`
- rows: `2,782`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,fanduel,0.6003302933881183,-113,-113,0.5,0.10033029338811827,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,21.5,21.5,fanduel,0.17658775259964038,450,-800,0.16981132075471697,0.0067764318449234084,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,20.5,20.5,fanduel,0.22051413099956613,370,-600,0.19886363636363638,0.02165049463592969,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,19.5,19.5,fanduel,0.27221087260301086,300,-450,0.23404255319148934,0.03816831941152146,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,18.5,18.5,fanduel,0.31599014383291596,230,-330,0.28308097432521395,0.03290916950770195,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,17.5,17.5,fanduel,0.37379177939369,188,-260,0.3246753246753247,0.04911645471836529,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,16.5,16.5,fanduel,0.45670579015876633,146,-198,0.37957915116930757,0.0771266389894587,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,fanduel,0.6003302933881183,-113,-114,0.49896830637173983,0.10136198701637844,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,13.5,13.5,fanduel,0.6626739589587165,-154,116,0.5670257738988136,0.09564818505990291,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,12.5,12.5,fanduel,0.716920170337286,-200,148,0.6231155778894473,0.09380459244783868,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,11.5,11.5,fanduel,0.7702090069564765,-270,194,0.6820759580683966,0.08813304888808005,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,10.5,10.5,fanduel,0.8292447825558638,-360,250,0.7325581395348837,0.09668664302098018,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,9.5,9.5,fanduel,0.8660105350412568,-480,320,0.7765793528505394,0.08943118219071744,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,15.5,15.5,fanduel,0.5402653207193285,116,-154,0.4329742261011864,0.10729109461814201,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,williamhill_us,0.6003302933881183,-125,-108,0.5168986083499005,0.08343168503821774,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,17.5,17.5,bovada,0.37379177939369,170,-230,0.34700315457413244,0.026788624819557516,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,16.5,16.5,bovada,0.45670579015876633,135,-180,0.3982930298719772,0.0584127602867891,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,15.5,15.5,bovada,0.5402653207193285,110,-145,0.4458598726114649,0.0944054481078635,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,bovada,0.6003302933881183,-120,-110,0.5101214574898786,0.09020883589823969,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,13.5,13.5,bovada,0.6626739589587165,-160,120,0.5751633986928104,0.08751056026590609,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,12.5,12.5,bovada,0.716920170337286,-210,155,0.6333530455351862,0.08356712480209971,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,11.5,11.5,bovada,0.7702090069564765,-290,210,0.6974398758727697,0.07276913108370697,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,betmgm,0.6003302933881183,-120,-110,0.5101214574898786,0.09020883589823969,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,15.5,15.5,betrivers,0.5402653207193285,106,-143,0.4520257450053946,0.08823957571393382,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,betrivers,0.6003302933881183,-124,-110,0.5138121546961325,0.08651813869198577,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,13.5,13.5,betrivers,0.6626739589587165,-167,120,0.5791298865069356,0.08354407245178086,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,draftkings,0.6003302933881183,-116,-110,0.5062344139650873,0.09409587942303099,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,hardrockbet_az,0.6003302933881183,-120,-110,0.5101214574898786,0.09020883589823969,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,hardrockbet,0.6003302933881183,-120,-110,0.5101214574898786,0.09020883589823969,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z
OG Anunoby,18,NYK,SAS,21716135,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.469908380500705,33.33820903857685,0.050000000000000044,16.129527255072265,16.129527255072265,16,16,0.0015402785823751034,14.5,14.5,rebet,0.6003302933881183,-114,-112,0.5020774472328402,0.09825284615527807,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-05T22:58:24Z

```

---

## `derek_game_snapshots/21716135/morning/outcome_level_probabilities.csv`

- bytes: `537,055`
- rows: `6,481`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,21716135,pts,starter,0,0.0015,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,1,0.0007,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,2,0.0022,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,3,0.004,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,4,0.007,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,5,0.0127,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,6,0.0128,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,7,0.0278,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,8,0.0313,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,9,0.0341,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,10,0.0368,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,11,0.059,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,12,0.0533,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,13,0.0542,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,14,0.0623,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,15,0.0601,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,16,0.0836,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,17,0.0829,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,18,0.0578,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,19,0.0438,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,20,0.0517,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,21,0.0439,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,22,0.0434,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,23,0.0321,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,24,0.019,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,25,0.0166,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,26,0.0166,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,27,0.01,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,28,0.0047,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,29,0.0085,fallback_used,projected

```

---

## `derek_game_snapshots/21716135/morning/outcome_level_probabilities.parquet`

- bytes: `73,789`
- rows: `6,481`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,21716135,pts,starter,0,0.0015402785823751036,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,1,0.0006609923411888556,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,2,0.00217071002723797,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,3,0.003971699562713425,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,4,0.006969018298404973,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,5,0.012684830700347888,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,6,0.012796286991846526,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,7,0.027825229059655697,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,8,0.03125158618894907,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,9,0.03411883320602372,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,10,0.036765752485392926,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,11,0.05903577559938724,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,12,0.053288836619190684,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,13,0.05424621137856939,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,14,0.062343665570598256,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,15,0.060064972668789844,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,16,0.08355953056056216,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,17,0.08291401076507635,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,18,0.05780163556077409,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,19,0.043779271229905055,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,20,0.051696741603444764,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,21,0.043926378399925706,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,22,0.04343721294347962,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,23,0.03211007523669554,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,24,0.01897558975698524,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,25,0.01658338186162882,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,26,0.01660335099816816,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,27,0.010013910598772801,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,28,0.004683515168299648,fallback_used,projected
OG Anunoby,18,21716135,pts,starter,29,0.008521965051810387,fallback_used,projected

```

---

## `derek_game_snapshots/21716135/morning/prop_summary.csv`

- bytes: `27,235`
- rows: `192`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,NYK,SAS,21716135,pts,starter,16.1295,14.5,14.5,betmgm,0.6003,-120.0,-110.0,0.5101,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,reb,starter,6.2868,5.5,5.5,betmgm,0.6494,110.0,-150.0,0.4425,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,ast,starter,1.9543,1.5,1.5,betmgm,0.6497,100.0,-135.0,0.4653,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,fg3m,starter,1.5099,2.5,2.5,betparx,0.2806,143.0,-195.0,0.3837,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,tov,starter,1.1869,,,,,,,,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,stl,starter,0.6669,1.5,1.5,betparx,0.197,170.0,-235.0,0.3455,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,blk,starter,0.3925,0.5,0.5,betmgm,0.2266,-135.0,-105.0,0.5287,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,stocks,starter,1.0594,1.5,1.5,betparx,0.306,-175.0,128.0,0.592,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,pa,starter,18.0839,16.5,16.5,betmgm,0.5967,-118.0,-110.0,0.5082,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,pr,starter,22.4163,19.5,19.5,bovada,0.6701,-125.0,-105.0,0.5203,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,ra,starter,8.2411,6.5,6.5,betmgm,0.7779,-125.0,-105.0,0.5203,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,pra,starter,24.3706,21.5,21.5,betmgm,0.665,-125.0,-105.0,0.5203,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,pts,starter,14.707,11.5,11.5,betparx,0.6826,-127.0,-105.0,0.5221,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,reb,starter,3.9999,3.5,3.5,betparx,0.6225,133.0,-180.0,0.4003,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,ast,starter,2.491,2.5,2.5,betmgm,0.4453,-118.0,-111.0,0.5071,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,fg3m,starter,1.15,1.5,1.5,betmgm,0.3505,145.0,-200.0,0.3797,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,tov,starter,1.1428,,,,,,,,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,stl,starter,0.6527,1.5,1.5,betparx,0.1803,160.0,-215.0,0.3604,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,blk,starter,0.3375,0.5,0.5,betmgm,0.2227,150.0,-210.0,0.3713,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,stocks,starter,1.044,1.5,1.5,betparx,0.2717,-120.0,-110.0,0.5101,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,pa,starter,17.198,14.5,14.5,betmgm,0.6543,-110.0,-120.0,0.4899,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,pr,starter,18.7069,15.5,15.5,bovada,0.6798,-105.0,-125.0,0.4797,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,ra,starter,6.4909,5.5,5.5,betmgm,0.687,-120.0,-110.0,0.5101,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,pra,starter,21.1979,17.5,17.5,betmgm,0.7032,-120.0,-110.0,0.5101,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,pts,starter,26.2798,25.5,25.5,betmgm,0.5553,-125.0,-105.0,0.5203,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,reb,starter,3.6121,2.5,2.5,betmgm,0.7782,-145.0,110.0,0.5541,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,ast,starter,6.3696,6.5,6.5,betmgm,0.4825,110.0,-145.0,0.4459,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,fg3m,starter,1.6948,2.5,2.5,betparx,0.3015,135.0,-182.0,0.3974,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,tov,starter,1.4102,,,,,,,,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,stl,starter,0.6351,0.5,0.5,betparx,0.3679,-157.0,117.0,0.57,fallback_used,projected

```

---

## `derek_game_snapshots/21716135/morning/prop_summary.parquet`

- bytes: `17,544`
- rows: `192`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,NYK,SAS,21716135,pts,starter,16.129527255072272,14.5,14.5,betmgm,0.6003302933881183,-120.0,-110.0,0.5101214574898786,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,reb,starter,6.286757263430153,5.5,5.5,betmgm,0.6494459442914128,110.0,-150.0,0.4424778761061947,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,ast,starter,1.9543282902093582,1.5,1.5,betmgm,0.6496633686863287,100.0,-135.0,0.4653465346534653,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,fg3m,starter,1.509884546755963,2.5,2.5,betparx,0.28055877085577713,143.0,-195.0,0.38368992651362427,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,tov,starter,1.1869449141462787,,,,,,,,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,stl,starter,0.666857040951864,1.5,1.5,betparx,0.19701900283978338,170.0,-235.0,0.34553893759669935,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,blk,starter,0.39253626922229834,0.5,0.5,betmgm,0.22664101346949933,-135.0,-105.0,0.5286532951289399,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,stocks,starter,1.0593933101741624,1.5,1.5,betparx,0.30601322709539425,-175.0,128.0,0.5919881305637983,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,pa,starter,18.083855545281587,16.5,16.5,betmgm,0.5966508816447841,-118.0,-110.0,0.5082034454470877,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,pr,starter,22.416284518502415,19.5,19.5,bovada,0.6700848416932795,-125.0,-105.0,0.5203045685279188,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,ra,starter,8.241085553639508,6.5,6.5,betmgm,0.7779435920398364,-125.0,-105.0,0.5203045685279188,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716135,pra,starter,24.370612808711712,21.5,21.5,betmgm,0.6649691113279136,-125.0,-105.0,0.5203045685279188,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,pts,starter,14.706955487465324,11.5,11.5,betparx,0.6825772493030254,-127.0,-105.0,0.5220573491076799,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,reb,starter,3.9999270007265952,3.5,3.5,betparx,0.6225021181491561,133.0,-180.0,0.40034315127251924,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,ast,starter,2.491009154652596,2.5,2.5,betmgm,0.4453356508284254,-118.0,-111.0,0.5071288903372982,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,fg3m,starter,1.1499603392725075,1.5,1.5,betmgm,0.35047353601555764,145.0,-200.0,0.37974683544303806,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,tov,starter,1.1428230730755933,,,,,,,,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,stl,starter,0.652707507934642,1.5,1.5,betparx,0.18032541555382176,160.0,-215.0,0.36041189931350115,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,blk,starter,0.3374507297425666,0.5,0.5,betmgm,0.22266334341198626,150.0,-210.0,0.37125748502994016,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,stocks,starter,1.0440384673637766,1.5,1.5,betparx,0.2716675628677003,-120.0,-110.0,0.5101214574898786,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,pa,starter,17.197964642117878,14.5,14.5,betmgm,0.6542559905809943,-110.0,-120.0,0.48987854251012153,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,pr,starter,18.706882488191866,15.5,15.5,bovada,0.6798386057993253,-105.0,-125.0,0.4796954314720812,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,ra,starter,6.490936155379188,5.5,5.5,betmgm,0.6870412781314683,-120.0,-110.0,0.5101214574898786,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716135,pra,starter,21.197891642844475,17.5,17.5,betmgm,0.7032132494348081,-120.0,-110.0,0.5101214574898786,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,pts,starter,26.27978799644411,25.5,25.5,betmgm,0.5552797754364085,-125.0,-105.0,0.5203045685279188,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,reb,starter,3.612061552750179,2.5,2.5,betmgm,0.7782375296590914,-145.0,110.0,0.554140127388535,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,ast,starter,6.369599140195989,6.5,6.5,betmgm,0.48247881844245116,110.0,-145.0,0.4458598726114649,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,fg3m,starter,1.6948196641364814,2.5,2.5,betparx,0.3014637300383104,135.0,-182.0,0.3973509933774834,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,tov,starter,1.4102168078435913,,,,,,,,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716135,stl,starter,0.6350819458519261,0.5,0.5,betparx,0.3679191635886001,-157.0,117.0,0.5700112098244909,fallback_used,projected

```
