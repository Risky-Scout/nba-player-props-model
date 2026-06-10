# Reviewable Delivery Preview — 2026-06-10 — derek_game_snapshots

GitHub may refuse to render large CSV files. This file is intentionally small.

---

## `derek_game_snapshots/21716137/current_live/contextual_feature_audit.csv`

- bytes: `4,832`
- rows: `15`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
Mitchell Robinson,399,NYK,21716137
OG Anunoby,18,NYK,21716137
Landry Shamet,414,NYK,21716137
De'Aaron Fox,161,SAS,21716137
Stephon Castle,1028025261,SAS,21716137
Dylan Harper,1057262518,SAS,21716137
Keldon Johnson,666682,SAS,21716137
Mikal Bridges,61,NYK,21716137
Victor Wembanyama,56677822,SAS,21716137
Karl-Anthony Towns,447,NYK,21716137
Jalen Brunson,73,NYK,21716137
Josh Hart,202,NYK,21716137
Miles McBride,17896033,NYK,21716137
Devin Vassell,3547246,SAS,21716137
Julian Champagnie,38017649,SAS,21716137

```

---

## `derek_game_snapshots/21716137/current_live/contextual_feature_audit.parquet`

- bytes: `29,853`
- rows: `15`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
Mitchell Robinson,399,NYK,21716137
OG Anunoby,18,NYK,21716137
Landry Shamet,414,NYK,21716137
De'Aaron Fox,161,SAS,21716137
Stephon Castle,1028025261,SAS,21716137
Dylan Harper,1057262518,SAS,21716137
Keldon Johnson,666682,SAS,21716137
Mikal Bridges,61,NYK,21716137
Victor Wembanyama,56677822,SAS,21716137
Karl-Anthony Towns,447,NYK,21716137
Jalen Brunson,73,NYK,21716137
Josh Hart,202,NYK,21716137
Miles McBride,17896033,NYK,21716137
Devin Vassell,3547246,SAS,21716137
Julian Champagnie,38017649,SAS,21716137

```

---

## `derek_game_snapshots/21716137/current_live/derek_live_predictions.parquet`

- bytes: `39,191`
- rows: `35`
- columns: `47`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
Mitchell Robinson,399,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,4.5,-0.0531
Mitchell Robinson,399,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.1386
Mitchell Robinson,399,NYK,SAS,21716137,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0889
OG Anunoby,18,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,-0.0936
OG Anunoby,18,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1322
Landry Shamet,414,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0593
De'Aaron Fox,161,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,14.5,0.043
De'Aaron Fox,161,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1426
De'Aaron Fox,161,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0903
Stephon Castle,1028025261,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,-0.0319
Stephon Castle,1028025261,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1959
Stephon Castle,1028025261,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.0497
Dylan Harper,1057262518,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,13.5,-0.1036
Dylan Harper,1057262518,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1898
Dylan Harper,1057262518,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1328
Keldon Johnson,666682,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.1268
Keldon Johnson,666682,SAS,NYK,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2975
Keldon Johnson,666682,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.1371
Mikal Bridges,61,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.0775
Mikal Bridges,61,NYK,SAS,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0858
Mikal Bridges,61,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1402
Victor Wembanyama,56677822,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,27.5,-0.2116
Victor Wembanyama,56677822,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.2496
Victor Wembanyama,56677822,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1275
Karl-Anthony Towns,447,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.1646
Karl-Anthony Towns,447,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.0716
Jalen Brunson,73,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,27.5,-0.0901
Jalen Brunson,73,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.162
Josh Hart,202,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.5,-0.0422
Josh Hart,202,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.5,-0.1537

```

---

## `derek_game_snapshots/21716137/current_live/full_pmf_wide.csv`

- bytes: `41,966`
- rows: `35`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
Mitchell Robinson,399,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,4.5,-0.0531
Mitchell Robinson,399,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.1386
Mitchell Robinson,399,NYK,SAS,21716137,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0889
OG Anunoby,18,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,-0.0936
OG Anunoby,18,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1322
Landry Shamet,414,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0593
De'Aaron Fox,161,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,14.5,0.043
De'Aaron Fox,161,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1426
De'Aaron Fox,161,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0903
Stephon Castle,1028025261,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,-0.0319
Stephon Castle,1028025261,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1959
Stephon Castle,1028025261,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.0497
Dylan Harper,1057262518,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,13.5,-0.1036
Dylan Harper,1057262518,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1898
Dylan Harper,1057262518,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1328
Keldon Johnson,666682,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.1268
Keldon Johnson,666682,SAS,NYK,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2975
Keldon Johnson,666682,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.1371
Mikal Bridges,61,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.0775
Mikal Bridges,61,NYK,SAS,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0858
Mikal Bridges,61,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1402
Victor Wembanyama,56677822,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,27.5,-0.2116
Victor Wembanyama,56677822,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.2496
Victor Wembanyama,56677822,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1275
Karl-Anthony Towns,447,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.1646
Karl-Anthony Towns,447,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.0716
Jalen Brunson,73,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,27.5,-0.0901
Jalen Brunson,73,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.162
Josh Hart,202,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.5,-0.0422
Josh Hart,202,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.5,-0.1537

```

---

## `derek_game_snapshots/21716137/current_live/full_pmf_wide.parquet`

- bytes: `72,796`
- rows: `35`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
Mitchell Robinson,399,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,4.5,-0.0531
Mitchell Robinson,399,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.1386
Mitchell Robinson,399,NYK,SAS,21716137,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0889
OG Anunoby,18,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,-0.0936
OG Anunoby,18,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1322
Landry Shamet,414,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0593
De'Aaron Fox,161,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,14.5,0.043
De'Aaron Fox,161,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1426
De'Aaron Fox,161,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0903
Stephon Castle,1028025261,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,-0.0319
Stephon Castle,1028025261,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1959
Stephon Castle,1028025261,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.0497
Dylan Harper,1057262518,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,13.5,-0.1036
Dylan Harper,1057262518,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1898
Dylan Harper,1057262518,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1328
Keldon Johnson,666682,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.1268
Keldon Johnson,666682,SAS,NYK,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2975
Keldon Johnson,666682,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.1371
Mikal Bridges,61,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.0775
Mikal Bridges,61,NYK,SAS,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0858
Mikal Bridges,61,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1402
Victor Wembanyama,56677822,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,27.5,-0.2116
Victor Wembanyama,56677822,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.2496
Victor Wembanyama,56677822,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1275
Karl-Anthony Towns,447,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.1646
Karl-Anthony Towns,447,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.5,-0.0716
Jalen Brunson,73,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,27.5,-0.0901
Jalen Brunson,73,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.162
Josh Hart,202,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.5,-0.0422
Josh Hart,202,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.5,-0.1537

```

---

## `derek_game_snapshots/21716137/current_live/game_context.csv`

- bytes: `612`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
Mitchell Robinson,399,NYK,SAS,21716137
OG Anunoby,18,NYK,SAS,21716137
Landry Shamet,414,NYK,SAS,21716137
De'Aaron Fox,161,SAS,NYK,21716137
Stephon Castle,1028025261,SAS,NYK,21716137
Dylan Harper,1057262518,SAS,NYK,21716137
Keldon Johnson,666682,SAS,NYK,21716137
Mikal Bridges,61,NYK,SAS,21716137
Victor Wembanyama,56677822,SAS,NYK,21716137
Karl-Anthony Towns,447,NYK,SAS,21716137
Jalen Brunson,73,NYK,SAS,21716137
Josh Hart,202,NYK,SAS,21716137
Miles McBride,17896033,NYK,SAS,21716137
Devin Vassell,3547246,SAS,NYK,21716137
Julian Champagnie,38017649,SAS,NYK,21716137

```

---

## `derek_game_snapshots/21716137/current_live/game_context.parquet`

- bytes: `3,648`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
Mitchell Robinson,399,NYK,SAS,21716137
OG Anunoby,18,NYK,SAS,21716137
Landry Shamet,414,NYK,SAS,21716137
De'Aaron Fox,161,SAS,NYK,21716137
Stephon Castle,1028025261,SAS,NYK,21716137
Dylan Harper,1057262518,SAS,NYK,21716137
Keldon Johnson,666682,SAS,NYK,21716137
Mikal Bridges,61,NYK,SAS,21716137
Victor Wembanyama,56677822,SAS,NYK,21716137
Karl-Anthony Towns,447,NYK,SAS,21716137
Jalen Brunson,73,NYK,SAS,21716137
Josh Hart,202,NYK,SAS,21716137
Miles McBride,17896033,NYK,SAS,21716137
Devin Vassell,3547246,SAS,NYK,21716137
Julian Champagnie,38017649,SAS,NYK,21716137

```

---

## `derek_game_snapshots/21716137/current_live/injury_availability_context.csv`

- bytes: `601`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
Mitchell Robinson,399,NYK,21716137
OG Anunoby,18,NYK,21716137
Landry Shamet,414,NYK,21716137
De'Aaron Fox,161,SAS,21716137
Stephon Castle,1028025261,SAS,21716137
Dylan Harper,1057262518,SAS,21716137
Keldon Johnson,666682,SAS,21716137
Mikal Bridges,61,NYK,21716137
Victor Wembanyama,56677822,SAS,21716137
Karl-Anthony Towns,447,NYK,21716137
Jalen Brunson,73,NYK,21716137
Josh Hart,202,NYK,21716137
Miles McBride,17896033,NYK,21716137
Devin Vassell,3547246,SAS,21716137
Julian Champagnie,38017649,SAS,21716137

```

---

## `derek_game_snapshots/21716137/current_live/injury_availability_context.parquet`

- bytes: `3,850`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
Mitchell Robinson,399,NYK,21716137
OG Anunoby,18,NYK,21716137
Landry Shamet,414,NYK,21716137
De'Aaron Fox,161,SAS,21716137
Stephon Castle,1028025261,SAS,21716137
Dylan Harper,1057262518,SAS,21716137
Keldon Johnson,666682,SAS,21716137
Mikal Bridges,61,NYK,21716137
Victor Wembanyama,56677822,SAS,21716137
Karl-Anthony Towns,447,NYK,21716137
Jalen Brunson,73,NYK,21716137
Josh Hart,202,NYK,21716137
Miles McBride,17896033,NYK,21716137
Devin Vassell,3547246,SAS,21716137
Julian Champagnie,38017649,SAS,21716137

```

---

## `derek_game_snapshots/21716137/current_live/lineup_context.csv`

- bytes: `1,629`
- rows: `15`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
Mitchell Robinson,399,NYK,21716137,reb
OG Anunoby,18,NYK,21716137,pts
Landry Shamet,414,NYK,21716137,stl
De'Aaron Fox,161,SAS,21716137,pts
Stephon Castle,1028025261,SAS,21716137,pts
Dylan Harper,1057262518,SAS,21716137,pts
Keldon Johnson,666682,SAS,21716137,reb
Mikal Bridges,61,NYK,21716137,reb
Victor Wembanyama,56677822,SAS,21716137,pts
Karl-Anthony Towns,447,NYK,21716137,pts
Jalen Brunson,73,NYK,21716137,pts
Josh Hart,202,NYK,21716137,pts
Miles McBride,17896033,NYK,21716137,fg3m
Devin Vassell,3547246,SAS,21716137,pts
Julian Champagnie,38017649,SAS,21716137,pts

```

---

## `derek_game_snapshots/21716137/current_live/lineup_context.parquet`

- bytes: `8,427`
- rows: `15`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
Mitchell Robinson,399,NYK,21716137,reb
OG Anunoby,18,NYK,21716137,pts
Landry Shamet,414,NYK,21716137,stl
De'Aaron Fox,161,SAS,21716137,pts
Stephon Castle,1028025261,SAS,21716137,pts
Dylan Harper,1057262518,SAS,21716137,pts
Keldon Johnson,666682,SAS,21716137,reb
Mikal Bridges,61,NYK,21716137,reb
Victor Wembanyama,56677822,SAS,21716137,pts
Karl-Anthony Towns,447,NYK,21716137,pts
Jalen Brunson,73,NYK,21716137,pts
Josh Hart,202,NYK,21716137,pts
Miles McBride,17896033,NYK,21716137,fg3m
Devin Vassell,3547246,SAS,21716137,pts
Julian Champagnie,38017649,SAS,21716137,pts

```

---

## `derek_game_snapshots/21716137/current_live/market_comparison.csv`

- bytes: `51,079`
- rows: `35`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
Mitchell Robinson,399,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,4.4398,0.0713,4.5,-0.0531
Mitchell Robinson,399,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.4027,0.728,0.5,-0.1386
Mitchell Robinson,399,NYK,SAS,21716137,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5497,0.6221,0.5,-0.0889
OG Anunoby,18,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.108,0.0103,16.5,-0.0936
OG Anunoby,18,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.9922,0.4282,1.5,-0.1322
Landry Shamet,414,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5458,0.6065,0.5,-0.0593
De'Aaron Fox,161,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.3625,0.0119,14.5,0.043
De'Aaron Fox,161,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.1598,0.0669,3.5,0.1426
De'Aaron Fox,161,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.2471,0.0348,6.5,-0.0903
Stephon Castle,1028025261,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.8014,0.0101,16.5,-0.0319
Stephon Castle,1028025261,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.1428,0.0326,6.5,-0.1959
Stephon Castle,1028025261,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0601,0.3219,0.5,0.0497
Dylan Harper,1057262518,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.1103,0.0161,13.5,-0.1036
Dylan Harper,1057262518,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.0046,0.04,5.5,-0.1898
Dylan Harper,1057262518,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.6139,0.1468,3.5,-0.1328
Keldon Johnson,666682,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.4338,0.1767,2.5,-0.1268
Keldon Johnson,666682,SAS,NYK,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4607,0.2058,0.5,0.2975
Keldon Johnson,666682,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.3114,0.7742,0.5,-0.1371
Mikal Bridges,61,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.0127,0.057,3.5,0.0775
Mikal Bridges,61,NYK,SAS,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.6375,0.1251,2.5,-0.0858
Mikal Bridges,61,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0652,0.3026,1.5,-0.1402
Victor Wembanyama,56677822,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,22.2335,0.0052,27.5,-0.2116
Victor Wembanyama,56677822,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.6033,0.013,11.5,-0.2496
Victor Wembanyama,56677822,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.6076,0.122,3.5,-0.1275
Karl-Anthony Towns,447,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,14.4055,0.013,17.5,-0.1646
Karl-Anthony Towns,447,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.2916,0.0104,11.5,-0.0716
Jalen Brunson,73,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,24.923,0.0045,27.5,-0.0901
Jalen Brunson,73,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.7988,0.1604,2.5,-0.162
Josh Hart,202,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.4591,0.0266,10.5,-0.0422
Josh Hart,202,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,7.4828,0.0175,8.5,-0.1537

```

---

## `derek_game_snapshots/21716137/current_live/market_comparison.parquet`

- bytes: `87,330`
- rows: `35`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
Mitchell Robinson,399,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,4.439791624924867,0.0713,4.5,-0.0531
Mitchell Robinson,399,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.4027,0.728,0.5,-0.1386
Mitchell Robinson,399,NYK,SAS,21716137,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5497000000000002,0.6221,0.5,-0.0889
OG Anunoby,18,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.107956255643623,0.0103,16.5,-0.0936
OG Anunoby,18,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.992199219921992,0.4282,1.5,-0.1322
Landry Shamet,414,NYK,SAS,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5458,0.6065,0.5,-0.0593
De'Aaron Fox,161,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.362451108213822,0.0119,14.5,0.043
De'Aaron Fox,161,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.15978761771188,0.0669,3.5,0.1426
De'Aaron Fox,161,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.247095352564102,0.0348,6.5,-0.0903
Stephon Castle,1028025261,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.801364365971107,0.0101,16.5,-0.0319
Stephon Castle,1028025261,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.1428285256410255,0.0326,6.5,-0.1959
Stephon Castle,1028025261,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0601000000000003,0.3219,0.5,0.0497
Dylan Harper,1057262518,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.11030814011843,0.0161,13.5,-0.1036
Dylan Harper,1057262518,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.004607371794873,0.04,5.5,-0.1898
Dylan Harper,1057262518,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.6138752627890685,0.1468,3.5,-0.1328
Keldon Johnson,666682,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.433837523790444,0.1767,2.5,-0.1268
Keldon Johnson,666682,SAS,NYK,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4607,0.2058,0.5,0.2975
Keldon Johnson,666682,SAS,NYK,21716137,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.3114311431143114,0.7742,0.5,-0.1371
Mikal Bridges,61,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.012720352564102,0.057,3.5,0.0775
Mikal Bridges,61,NYK,SAS,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.637483722327958,0.1251,2.5,-0.0858
Mikal Bridges,61,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0652,0.3026,1.5,-0.1402
Victor Wembanyama,56677822,SAS,NYK,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,22.233510691697607,0.0052,27.5,-0.2116
Victor Wembanyama,56677822,SAS,NYK,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.60332732010423,0.013,11.5,-0.2496
Victor Wembanyama,56677822,SAS,NYK,21716137,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.607568325157673,0.122,3.5,-0.1275
Karl-Anthony Towns,447,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,14.40547862733293,0.013,17.5,-0.1646
Karl-Anthony Towns,447,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.291558050932425,0.0104,11.5,-0.0716
Jalen Brunson,73,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,24.923022811777706,0.0045,27.5,-0.0901
Jalen Brunson,73,NYK,SAS,21716137,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.7988000000000002,0.1604,2.5,-0.162
Josh Hart,202,NYK,SAS,21716137,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,10.459069020866774,0.0266,10.5,-0.0422
Josh Hart,202,NYK,SAS,21716137,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,7.482765531062122,0.0175,8.5,-0.1537

```

---

## `derek_game_snapshots/21716137/current_live/outcome_level_probabilities.csv`

- bytes: `119,943`
- rows: `655`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
Mitchell Robinson,399,21716137,reb,0,0.0714,4.5,current_live
Mitchell Robinson,399,21716137,reb,1,0.1076,4.5,current_live
Mitchell Robinson,399,21716137,reb,2,0.1165,4.5,current_live
Mitchell Robinson,399,21716137,reb,3,0.1368,4.5,current_live
Mitchell Robinson,399,21716137,reb,4,0.1286,4.5,current_live
Mitchell Robinson,399,21716137,reb,5,0.1383,4.5,current_live
Mitchell Robinson,399,21716137,reb,6,0.0815,4.5,current_live
Mitchell Robinson,399,21716137,reb,7,0.0641,4.5,current_live
Mitchell Robinson,399,21716137,reb,8,0.0516,4.5,current_live
Mitchell Robinson,399,21716137,reb,9,0.0328,4.5,current_live
Mitchell Robinson,399,21716137,reb,10,0.0176,4.5,current_live
Mitchell Robinson,399,21716137,reb,11,0.0203,4.5,current_live
Mitchell Robinson,399,21716137,reb,12,0.0126,4.5,current_live
Mitchell Robinson,399,21716137,reb,13,0.0084,4.5,current_live
Mitchell Robinson,399,21716137,reb,14,0.0055,4.5,current_live
Mitchell Robinson,399,21716137,reb,15,0.0023,4.5,current_live
Mitchell Robinson,399,21716137,reb,16,0.0016,4.5,current_live
Mitchell Robinson,399,21716137,reb,17,0.0012,4.5,current_live
Mitchell Robinson,399,21716137,reb,18,0.001,4.5,current_live
Mitchell Robinson,399,21716137,stl,0,0.728,0.5,current_live
Mitchell Robinson,399,21716137,stl,1,0.1733,0.5,current_live
Mitchell Robinson,399,21716137,stl,2,0.0733,0.5,current_live
Mitchell Robinson,399,21716137,stl,3,0.0188,0.5,current_live
Mitchell Robinson,399,21716137,stl,4,0.0066,0.5,current_live
Mitchell Robinson,399,21716137,blk,0,0.6221,0.5,current_live
Mitchell Robinson,399,21716137,blk,1,0.2421,0.5,current_live
Mitchell Robinson,399,21716137,blk,2,0.107,0.5,current_live
Mitchell Robinson,399,21716137,blk,3,0.0216,0.5,current_live
Mitchell Robinson,399,21716137,blk,4,0.0072,0.5,current_live
OG Anunoby,18,21716137,pts,0,0.0103,16.5,current_live

```

---

## `derek_game_snapshots/21716137/current_live/outcome_level_probabilities.parquet`

- bytes: `19,612`
- rows: `655`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
Mitchell Robinson,399,21716137,reb,0,0.07142857142857145,4.5,current_live
Mitchell Robinson,399,21716137,reb,1,0.1075936686034863,4.5,current_live
Mitchell Robinson,399,21716137,reb,2,0.11650971749148471,4.5,current_live
Mitchell Robinson,399,21716137,reb,3,0.1368463233820878,4.5,current_live
Mitchell Robinson,399,21716137,reb,4,0.12863153676617917,4.5,current_live
Mitchell Robinson,399,21716137,reb,5,0.13834902825085157,4.5,current_live
Mitchell Robinson,399,21716137,reb,6,0.08154678421158087,4.5,current_live
Mitchell Robinson,399,21716137,reb,7,0.06411540773392108,4.5,current_live
Mitchell Robinson,399,21716137,reb,8,0.051592867160889615,4.5,current_live
Mitchell Robinson,399,21716137,reb,9,0.0327589661390503,4.5,current_live
Mitchell Robinson,399,21716137,reb,10,0.0176317371268283,4.5,current_live
Mitchell Robinson,399,21716137,reb,11,0.020336605890603092,4.5,current_live
Mitchell Robinson,399,21716137,reb,12,0.012622720897615713,4.5,current_live
Mitchell Robinson,399,21716137,reb,13,0.008415147265077142,4.5,current_live
Mitchell Robinson,399,21716137,reb,14,0.005509917852133842,4.5,current_live
Mitchell Robinson,399,21716137,reb,15,0.002304147465437789,4.5,current_live
Mitchell Robinson,399,21716137,reb,16,0.0016028851933480271,4.5,current_live
Mitchell Robinson,399,21716137,reb,17,0.0012021638950110202,4.5,current_live
Mitchell Robinson,399,21716137,reb,18,0.0010018032458425168,4.5,current_live
Mitchell Robinson,399,21716137,stl,0,0.728,0.5,current_live
Mitchell Robinson,399,21716137,stl,1,0.1733,0.5,current_live
Mitchell Robinson,399,21716137,stl,2,0.0733,0.5,current_live
Mitchell Robinson,399,21716137,stl,3,0.0188,0.5,current_live
Mitchell Robinson,399,21716137,stl,4,0.0066,0.5,current_live
Mitchell Robinson,399,21716137,blk,0,0.6221000000000001,0.5,current_live
Mitchell Robinson,399,21716137,blk,1,0.24210000000000004,0.5,current_live
Mitchell Robinson,399,21716137,blk,2,0.10700000000000001,0.5,current_live
Mitchell Robinson,399,21716137,blk,3,0.021600000000000005,0.5,current_live
Mitchell Robinson,399,21716137,blk,4,0.007200000000000001,0.5,current_live
OG Anunoby,18,21716137,pts,0,0.010334102538376643,16.5,current_live

```

---

## `derek_game_snapshots/21716137/current_live/pmf_driver_decomposition.csv`

- bytes: `3,171`
- rows: `15`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
Mitchell Robinson,399,NYK,21716137,reb,4.5
OG Anunoby,18,NYK,21716137,pts,16.5
Landry Shamet,414,NYK,21716137,stl,0.5
De'Aaron Fox,161,SAS,21716137,pts,14.5
Stephon Castle,1028025261,SAS,21716137,pts,16.5
Dylan Harper,1057262518,SAS,21716137,pts,13.5
Keldon Johnson,666682,SAS,21716137,reb,2.5
Mikal Bridges,61,NYK,21716137,reb,3.5
Victor Wembanyama,56677822,SAS,21716137,pts,27.5
Karl-Anthony Towns,447,NYK,21716137,pts,17.5
Jalen Brunson,73,NYK,21716137,pts,27.5
Josh Hart,202,NYK,21716137,pts,10.5
Miles McBride,17896033,NYK,21716137,fg3m,0.5
Devin Vassell,3547246,SAS,21716137,pts,12.5
Julian Champagnie,38017649,SAS,21716137,pts,9.5

```

---

## `derek_game_snapshots/21716137/current_live/pmf_driver_decomposition.parquet`

- bytes: `14,465`
- rows: `15`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
Mitchell Robinson,399,NYK,21716137,reb,4.5
OG Anunoby,18,NYK,21716137,pts,16.5
Landry Shamet,414,NYK,21716137,stl,0.5
De'Aaron Fox,161,SAS,21716137,pts,14.5
Stephon Castle,1028025261,SAS,21716137,pts,16.5
Dylan Harper,1057262518,SAS,21716137,pts,13.5
Keldon Johnson,666682,SAS,21716137,reb,2.5
Mikal Bridges,61,NYK,21716137,reb,3.5
Victor Wembanyama,56677822,SAS,21716137,pts,27.5
Karl-Anthony Towns,447,NYK,21716137,pts,17.5
Jalen Brunson,73,NYK,21716137,pts,27.5
Josh Hart,202,NYK,21716137,pts,10.5
Miles McBride,17896033,NYK,21716137,fg3m,0.5
Devin Vassell,3547246,SAS,21716137,pts,12.5
Julian Champagnie,38017649,SAS,21716137,pts,9.5

```

---

## `derek_game_snapshots/21716137/current_live/prediction_input_audit.csv`

- bytes: `2,410`
- rows: `35`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
Mitchell Robinson,399,NYK,SAS,21716137,reb,4.5
Mitchell Robinson,399,NYK,SAS,21716137,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716137,blk,0.5
OG Anunoby,18,NYK,SAS,21716137,pts,16.5
OG Anunoby,18,NYK,SAS,21716137,stl,1.5
Landry Shamet,414,NYK,SAS,21716137,stl,0.5
De'Aaron Fox,161,SAS,NYK,21716137,pts,14.5
De'Aaron Fox,161,SAS,NYK,21716137,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716137,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716137,pts,16.5
Stephon Castle,1028025261,SAS,NYK,21716137,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716137,stl,0.5
Dylan Harper,1057262518,SAS,NYK,21716137,pts,13.5
Dylan Harper,1057262518,SAS,NYK,21716137,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716137,ast,3.5
Keldon Johnson,666682,SAS,NYK,21716137,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716137,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716137,stl,0.5
Mikal Bridges,61,NYK,SAS,21716137,reb,3.5
Mikal Bridges,61,NYK,SAS,21716137,ast,2.5
Mikal Bridges,61,NYK,SAS,21716137,fg3m,1.5
Victor Wembanyama,56677822,SAS,NYK,21716137,pts,27.5
Victor Wembanyama,56677822,SAS,NYK,21716137,reb,11.5
Victor Wembanyama,56677822,SAS,NYK,21716137,ast,3.5
Karl-Anthony Towns,447,NYK,SAS,21716137,pts,17.5
Karl-Anthony Towns,447,NYK,SAS,21716137,reb,11.5
Jalen Brunson,73,NYK,SAS,21716137,pts,27.5
Jalen Brunson,73,NYK,SAS,21716137,fg3m,2.5
Josh Hart,202,NYK,SAS,21716137,pts,10.5
Josh Hart,202,NYK,SAS,21716137,reb,8.5

```

---

## `derek_game_snapshots/21716137/current_live/prediction_input_audit.parquet`

- bytes: `5,439`
- rows: `35`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
Mitchell Robinson,399,NYK,SAS,21716137,reb,4.5
Mitchell Robinson,399,NYK,SAS,21716137,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716137,blk,0.5
OG Anunoby,18,NYK,SAS,21716137,pts,16.5
OG Anunoby,18,NYK,SAS,21716137,stl,1.5
Landry Shamet,414,NYK,SAS,21716137,stl,0.5
De'Aaron Fox,161,SAS,NYK,21716137,pts,14.5
De'Aaron Fox,161,SAS,NYK,21716137,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716137,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716137,pts,16.5
Stephon Castle,1028025261,SAS,NYK,21716137,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716137,stl,0.5
Dylan Harper,1057262518,SAS,NYK,21716137,pts,13.5
Dylan Harper,1057262518,SAS,NYK,21716137,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716137,ast,3.5
Keldon Johnson,666682,SAS,NYK,21716137,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716137,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716137,stl,0.5
Mikal Bridges,61,NYK,SAS,21716137,reb,3.5
Mikal Bridges,61,NYK,SAS,21716137,ast,2.5
Mikal Bridges,61,NYK,SAS,21716137,fg3m,1.5
Victor Wembanyama,56677822,SAS,NYK,21716137,pts,27.5
Victor Wembanyama,56677822,SAS,NYK,21716137,reb,11.5
Victor Wembanyama,56677822,SAS,NYK,21716137,ast,3.5
Karl-Anthony Towns,447,NYK,SAS,21716137,pts,17.5
Karl-Anthony Towns,447,NYK,SAS,21716137,reb,11.5
Jalen Brunson,73,NYK,SAS,21716137,pts,27.5
Jalen Brunson,73,NYK,SAS,21716137,fg3m,2.5
Josh Hart,202,NYK,SAS,21716137,pts,10.5
Josh Hart,202,NYK,SAS,21716137,reb,8.5

```

---

## `derek_game_snapshots/21716137/current_live/prop_summary.csv`

- bytes: `1,768`
- rows: `35`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
Mitchell Robinson,399,NYK,SAS,21716137,reb,4.5
Mitchell Robinson,399,NYK,SAS,21716137,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716137,blk,0.5
OG Anunoby,18,NYK,SAS,21716137,pts,16.5
OG Anunoby,18,NYK,SAS,21716137,stl,1.5
Landry Shamet,414,NYK,SAS,21716137,stl,0.5
De'Aaron Fox,161,SAS,NYK,21716137,pts,14.5
De'Aaron Fox,161,SAS,NYK,21716137,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716137,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716137,pts,16.5
Stephon Castle,1028025261,SAS,NYK,21716137,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716137,stl,0.5
Dylan Harper,1057262518,SAS,NYK,21716137,pts,13.5
Dylan Harper,1057262518,SAS,NYK,21716137,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716137,ast,3.5
Keldon Johnson,666682,SAS,NYK,21716137,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716137,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716137,stl,0.5
Mikal Bridges,61,NYK,SAS,21716137,reb,3.5
Mikal Bridges,61,NYK,SAS,21716137,ast,2.5
Mikal Bridges,61,NYK,SAS,21716137,fg3m,1.5
Victor Wembanyama,56677822,SAS,NYK,21716137,pts,27.5
Victor Wembanyama,56677822,SAS,NYK,21716137,reb,11.5
Victor Wembanyama,56677822,SAS,NYK,21716137,ast,3.5
Karl-Anthony Towns,447,NYK,SAS,21716137,pts,17.5
Karl-Anthony Towns,447,NYK,SAS,21716137,reb,11.5
Jalen Brunson,73,NYK,SAS,21716137,pts,27.5
Jalen Brunson,73,NYK,SAS,21716137,fg3m,2.5
Josh Hart,202,NYK,SAS,21716137,pts,10.5
Josh Hart,202,NYK,SAS,21716137,reb,8.5

```

---

## `derek_game_snapshots/21716137/current_live/prop_summary.parquet`

- bytes: `4,848`
- rows: `35`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
Mitchell Robinson,399,NYK,SAS,21716137,reb,4.5
Mitchell Robinson,399,NYK,SAS,21716137,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716137,blk,0.5
OG Anunoby,18,NYK,SAS,21716137,pts,16.5
OG Anunoby,18,NYK,SAS,21716137,stl,1.5
Landry Shamet,414,NYK,SAS,21716137,stl,0.5
De'Aaron Fox,161,SAS,NYK,21716137,pts,14.5
De'Aaron Fox,161,SAS,NYK,21716137,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716137,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716137,pts,16.5
Stephon Castle,1028025261,SAS,NYK,21716137,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716137,stl,0.5
Dylan Harper,1057262518,SAS,NYK,21716137,pts,13.5
Dylan Harper,1057262518,SAS,NYK,21716137,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716137,ast,3.5
Keldon Johnson,666682,SAS,NYK,21716137,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716137,fg3m,0.5
Keldon Johnson,666682,SAS,NYK,21716137,stl,0.5
Mikal Bridges,61,NYK,SAS,21716137,reb,3.5
Mikal Bridges,61,NYK,SAS,21716137,ast,2.5
Mikal Bridges,61,NYK,SAS,21716137,fg3m,1.5
Victor Wembanyama,56677822,SAS,NYK,21716137,pts,27.5
Victor Wembanyama,56677822,SAS,NYK,21716137,reb,11.5
Victor Wembanyama,56677822,SAS,NYK,21716137,ast,3.5
Karl-Anthony Towns,447,NYK,SAS,21716137,pts,17.5
Karl-Anthony Towns,447,NYK,SAS,21716137,reb,11.5
Jalen Brunson,73,NYK,SAS,21716137,pts,27.5
Jalen Brunson,73,NYK,SAS,21716137,fg3m,2.5
Josh Hart,202,NYK,SAS,21716137,pts,10.5
Josh Hart,202,NYK,SAS,21716137,reb,8.5

```

---

## `derek_game_snapshots/21716137/morning/full_pmf_wide.csv`

- bytes: `354,837`
- rows: `180`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,6.0985,6.0985,6,6,0.0031,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,2.0825,2.0825,2,2,0.0452,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,1.4864,1.4864,1,0,0.4083,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,1.1822,1.1822,1,1,0.125,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,0.6318,0.6318,0,0,0.5665,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,0.3702,0.3702,0,0,0.756,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.8515,33.6713,0.05,1.002,1.002,1,0,0.4283,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.8515,33.6713,0.05,18.3861,18.3861,18,18,0.0001,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.8515,33.6713,0.05,22.4021,22.4021,22,22,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.8515,33.6713,0.05,8.181,8.181,8,8,0.0001,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.8515,33.6713,0.05,24.4846,24.4846,24,24,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.5847,33.3243,0.05,13.5084,13.5084,13,13,0.0025,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.5847,33.3243,0.05,4.182,4.182,4,4,0.0061,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.5847,33.3243,0.05,2.7824,2.7824,3,2,0.0147,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.5847,33.3243,0.05,1.1385,1.1385,1,0,0.4049,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.5847,33.3243,0.05,1.1429,1.1429,1,1,0.1234,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.5847,33.3243,0.05,0.6015,0.6015,0,0,0.5667,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.5847,33.3243,0.05,0.3299,0.3299,0,0,0.7621,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.5847,33.3243,0.05,0.9388,0.9388,1,0,0.4319,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.5847,33.3243,0.05,16.2908,16.2908,16,16,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.5847,33.3243,0.05,17.6904,17.6904,17,17,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.5847,33.3243,0.05,6.9644,6.9644,7,7,0.0001,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.5847,33.3243,0.05,20.4728,20.4728,20,20,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9745,36.0278,0.05,27.0935,27.0935,27,27,0.0001,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9745,36.0278,0.05,3.8918,3.8918,4,4,0.0065,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9745,36.0278,0.05,6.415,6.415,6,7,0.0045,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9745,36.0278,0.05,1.7289,1.7289,1,0,0.4074,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9745,36.0278,0.05,1.5093,1.5093,1,1,0.1203,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.9745,36.0278,0.05,0.7482,0.7482,0,0,0.537,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z

```

---

## `derek_game_snapshots/21716137/morning/full_pmf_wide.parquet`

- bytes: `203,924`
- rows: `180`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682827,16,16,0.001237947375268299,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,6.098457084250648,6.098457084250649,6,6,0.003144274037230362,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,2.082526495029054,2.0825264950290543,2,2,0.045162205828292556,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,1.4863628774245532,1.4863628774245532,1,0,0.4083350854857854,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,1.182249660895564,1.182249660895564,1,1,0.12497893477387226,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,0.631800084371469,0.6318000843714691,0,0,0.5665089018956692,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,0.3701967938749173,0.37019679387491733,0,0,0.756041347404668,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.851519370645025,33.671292856979264,0.050000000000000044,1.0019968782463862,1.0019968782463862,1,0,0.4283041535059406,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.851519370645025,33.671292856979264,0.050000000000000044,18.386127092711888,18.386127092711895,18,18,5.590843416646143e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.851519370645025,33.671292856979264,0.050000000000000044,22.402057681933456,22.402057681933456,22,22,3.892445791513586e-06,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.851519370645025,33.671292856979264,0.050000000000000044,8.180983579279687,8.180983579279689,8,8,0.00014200235124995408,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.851519370645025,33.671292856979264,0.050000000000000044,24.4845841769625,24.4845841769625,24,24,1.757914380118077e-07,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.58467790206813,33.32429149144187,0.050000000000000044,13.50838945538012,13.508389455380117,13,13,0.002497493229232919,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.58467790206813,33.32429149144187,0.050000000000000044,4.181961463680547,4.181961463680546,4,4,0.006066296463631078,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.58467790206813,33.32429149144187,0.050000000000000044,2.782436166565753,2.7824361665657524,3,2,0.01468979055628502,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.58467790206813,33.32429149144187,0.050000000000000044,1.1384826272853672,1.138482627285367,1,0,0.4048667330115218,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.58467790206813,33.32429149144187,0.050000000000000044,1.142875091532399,1.142875091532399,1,1,0.12343223933913561,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.58467790206813,33.32429149144187,0.050000000000000044,0.6014877847970497,0.6014877847970497,0,0,0.5667019044128909,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.58467790206813,33.32429149144187,0.050000000000000044,0.32989951112847105,0.32989951112847105,0,0,0.7621364281425416,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.58467790206813,33.32429149144187,0.050000000000000044,0.9387605614921863,0.9387605614921863,1,0,0.4319041652508167,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.58467790206813,33.32429149144187,0.050000000000000044,16.29082562194582,16.290825621945817,16,16,3.668765245317155e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.58467790206813,33.32429149144187,0.050000000000000044,17.6903509190606,17.690350919060602,17,17,1.5150534344438233e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.58467790206813,33.32429149144187,0.050000000000000044,6.964397630246297,6.964397630246298,7,7,8.911262450307302e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Mikal Bridges,61,NYK,SAS,21716137,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.58467790206813,33.32429149144187,0.050000000000000044,20.472787085626386,20.472787085626393,20,20,2.2255817633560055e-07,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97448711201221,36.02784744421177,0.050000000000000044,27.093506607314914,27.093506607314904,27,27,5.5583263964196936e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97448711201221,36.02784744421177,0.050000000000000044,3.8917693808027654,3.8917693808027662,4,4,0.006492679361214762,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97448711201221,36.02784744421177,0.050000000000000044,6.4150263767598625,6.415026376759862,6,7,0.00452173722878756,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97448711201221,36.02784744421177,0.050000000000000044,1.7288917511426243,1.728891751142624,1,0,0.4073504763598038,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97448711201221,36.02784744421177,0.050000000000000044,1.5093260483350808,1.5093260483350808,1,1,0.12033857013349455,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
Jalen Brunson,73,NYK,SAS,21716137,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.97448711201221,36.02784744421177,0.050000000000000044,0.748165698117875,0.748165698117875,0,0,0.5370238624541326,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z

```

---

## `derek_game_snapshots/21716137/morning/market_comparison.csv`

- bytes: `2,639,921`
- rows: `2,775`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,16.5,16.5,fanduel,0.4568,-104,-122,0.4812,-0.0244,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,14.5,14.5,fanduel,0.6246,-180,138,0.6047,0.0198,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,13.5,13.5,fanduel,0.709,-245,178,0.6638,0.0452,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,12.5,12.5,fanduel,0.7717,-330,230,0.7169,0.0548,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,11.5,11.5,fanduel,0.8278,-470,310,0.7717,0.0561,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,10.5,10.5,fanduel,0.8665,-650,390,0.8094,0.0571,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,15.5,15.5,fanduel,0.5557,-138,104,0.5419,0.0139,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,16.5,16.5,fanduel,0.4568,-106,-125,0.4808,-0.024,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,17.5,17.5,fanduel,0.3752,122,-162,0.4215,-0.0462,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,18.5,18.5,fanduel,0.3118,158,-215,0.3622,-0.0504,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,23.5,23.5,fanduel,0.0895,490,-900,0.1585,-0.069,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,22.5,22.5,fanduel,0.1107,390,-650,0.1906,-0.0799,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,21.5,21.5,fanduel,0.1464,310,-470,0.2283,-0.0818,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,20.5,20.5,fanduel,0.2032,240,-350,0.2744,-0.0712,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,19.5,19.5,fanduel,0.256,200,-270,0.3136,-0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,16.5,16.5,williamhill_us,0.4568,-112,-120,0.492,-0.0352,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,19.5,19.5,bovada,0.256,180,-245,0.3346,-0.0786,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,18.5,18.5,bovada,0.3118,145,-190,0.3839,-0.0721,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,17.5,17.5,bovada,0.3752,115,-150,0.4367,-0.0614,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,16.5,16.5,bovada,0.4568,-110,-120,0.4899,-0.0331,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,15.5,15.5,bovada,0.5557,-145,110,0.5541,0.0016,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,14.5,14.5,bovada,0.6246,-185,140,0.6091,0.0155,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,13.5,13.5,bovada,0.709,-245,180,0.6654,0.0436,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,16.5,16.5,betmgm,0.4568,-110,-120,0.4899,-0.0331,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,17.5,17.5,betrivers,0.3752,118,-165,0.4242,-0.049,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,16.5,16.5,betrivers,0.4568,-110,-124,0.4862,-0.0294,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,15.5,15.5,betrivers,0.5557,-141,104,0.5441,0.0116,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,16.5,16.5,draftkings,0.4568,-110,-116,0.4938,-0.037,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,16.5,16.5,hardrockbet_az,0.4568,-120,-110,0.5101,-0.0533,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.8515,33.6713,0.05,16.3036,16.3036,16,16,0.0012,16.5,16.5,hardrockbet,0.4568,-120,-110,0.5101,-0.0533,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z

```

---

## `derek_game_snapshots/21716137/morning/market_comparison.parquet`

- bytes: `143,886`
- rows: `2,775`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,16.5,16.5,fanduel,0.45681008492629277,-104,-122,0.48124062031015497,-0.02443053538386214,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,14.5,14.5,fanduel,0.6245721180535362,-180,138,0.6047430830039526,0.019829035049583554,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,13.5,13.5,fanduel,0.7090203643353399,-245,178,0.6637754604814345,0.04524490385390534,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,12.5,12.5,fanduel,0.771670573150736,-330,230,0.716919025674786,0.05475154747594979,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,11.5,11.5,fanduel,0.8278279912964145,-470,310,0.7717260712855426,0.056101920010871775,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,10.5,10.5,fanduel,0.8664731574000625,-650,390,0.8094027954256671,0.0570703619743953,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,15.5,15.5,fanduel,0.5557497998824137,-138,104,0.5418848167539267,0.013864983128487052,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,16.5,16.5,fanduel,0.45681008492629277,-106,-125,0.4808467741935484,-0.02403668926725555,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,17.5,17.5,fanduel,0.3752437344314373,122,-162,0.421465800141561,-0.04622206571012366,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,18.5,18.5,fanduel,0.31179010294040105,158,-215,0.3621938599517075,-0.050403757011306394,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,23.5,23.5,fanduel,0.08950200865552338,490,-900,0.1584786053882726,-0.0689765967327492,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,22.5,22.5,fanduel,0.11070824134081976,390,-650,0.1905972045743329,-0.07988896323351312,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,21.5,21.5,fanduel,0.1464455211122891,310,-470,0.2282739287144573,-0.08182840760216828,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,20.5,20.5,fanduel,0.2032384858424167,240,-350,0.27439024390243905,-0.07115175806002239,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,19.5,19.5,fanduel,0.2560290711856754,200,-270,0.3135593220338983,-0.05753025084822283,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,16.5,16.5,williamhill_us,0.45681008492629277,-112,-120,0.4920127795527157,-0.03520269462642289,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,19.5,19.5,bovada,0.2560290711856754,180,-245,0.3346265761396702,-0.0785975049539947,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,18.5,18.5,bovada,0.31179010294040105,145,-190,0.3838517538054269,-0.0720616508650258,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,17.5,17.5,bovada,0.3752437344314373,115,-150,0.43668122270742354,-0.06143748827598622,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,16.5,16.5,bovada,0.45681008492629277,-110,-120,0.48987854251012153,-0.0330684575838287,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,15.5,15.5,bovada,0.5557497998824137,-145,110,0.554140127388535,0.0016096724938787776,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,14.5,14.5,bovada,0.6245721180535362,-185,140,0.6090534979423868,0.01551862011114935,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,13.5,13.5,bovada,0.7090203643353399,-245,180,0.6653734238603297,0.043646940475010165,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,16.5,16.5,betmgm,0.45681008492629277,-110,-120,0.48987854251012153,-0.0330684575838287,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,17.5,17.5,betrivers,0.3752437344314373,118,-165,0.42420361773651355,-0.048959883305076224,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,16.5,16.5,betrivers,0.45681008492629277,-110,-124,0.4861878453038673,-0.029377760377574502,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,15.5,15.5,betrivers,0.5557497998824137,-141,104,0.544113196125908,0.01163660375650577,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,16.5,16.5,draftkings,0.45681008492629277,-110,-116,0.4937655860349127,-0.03695550110861989,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,16.5,16.5,hardrockbet_az,0.45681008492629277,-120,-110,0.5101214574898786,-0.05331137256358576,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z
OG Anunoby,18,NYK,SAS,21716137,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.851519370645025,33.671292856979264,0.050000000000000044,16.303600597682838,16.303600597682838,16,16,0.001237947375268299,16.5,16.5,hardrockbet,0.45681008492629277,-120,-110,0.5101214574898786,-0.05331137256358576,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-10T23:27:36Z

```

---

## `derek_game_snapshots/21716137/morning/outcome_level_probabilities.csv`

- bytes: `586,082`
- rows: `5,996`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,21716137,pts,starter,0,0.0012,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,1,0.0005,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,2,0.0015,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,3,0.002,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,4,0.0044,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,5,0.0072,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,6,0.013,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,7,0.014,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,8,0.0259,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,9,0.0281,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,10,0.0356,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,11,0.0386,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,12,0.0562,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,13,0.0627,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,14,0.0844,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,15,0.0688,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,16,0.0989,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,17,0.0816,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,18,0.0635,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,19,0.0558,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,20,0.0528,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,21,0.0568,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,22,0.0357,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,23,0.0212,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,24,0.0205,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,25,0.0172,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,26,0.0068,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,27,0.0099,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,28,0.0094,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,29,0.0109,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21716137/morning/outcome_level_probabilities.parquet`

- bytes: `69,186`
- rows: `5,996`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,21716137,pts,starter,0,0.0012379473752682987,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,1,0.000455043254988176,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,2,0.0015270864151141867,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,3,0.0020220564999787003,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,4,0.0044397509210647255,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,5,0.007191241090255357,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,6,0.013041633054651763,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,7,0.014014363862874645,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,8,0.025907496672246125,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,9,0.028091228736339804,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,10,0.03559899471715583,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,11,0.038645166103647974,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,12,0.05615741814567852,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,13,0.06265020881539597,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,14,0.08444824628180368,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,15,0.06882231817112239,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,16,0.09893971495612092,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,17,0.08156635049485553,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,18,0.0634536314910362,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,19,0.055761031754725646,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,20,0.052790585343258756,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,21,0.05679296473012759,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,22,0.03573727977146926,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,23,0.02120623268529638,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,24,0.020525479059475087,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,25,0.017233675571971734,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,26,0.006759268002942924,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,27,0.009902904154171312,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,28,0.009400167793399916,latest_valid_report_selected,projected
OG Anunoby,18,21716137,pts,starter,29,0.010854843752550043,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21716137/morning/prop_summary.csv`

- bytes: `28,449`
- rows: `180`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,NYK,SAS,21716137,pts,starter,16.3036,16.5,16.5,betmgm,0.4568,-110.0,-120.0,0.4899,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,reb,starter,6.0985,5.5,5.5,betmgm,0.6326,-105.0,-125.0,0.4797,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,ast,starter,2.0825,1.5,1.5,betmgm,0.6834,-135.0,100.0,0.5347,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,fg3m,starter,1.4864,2.5,2.5,betmgm,0.2707,125.0,-165.0,0.4165,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,tov,starter,1.1822,,,,,,,,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,stl,starter,0.6318,1.5,1.5,betparx,0.1365,135.0,-182.0,0.3974,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,blk,starter,0.3702,0.5,0.5,betmgm,0.244,-165.0,120.0,0.578,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,stocks,starter,1.002,2.5,2.5,betparx,0.115,140.0,-190.0,0.3887,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,pa,starter,18.3861,18.5,18.5,betmgm,0.4696,-120.0,-110.0,0.5101,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,pr,starter,22.4021,22.5,22.5,betmgm,0.4747,120.0,-160.0,0.4248,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,ra,starter,8.181,7.5,7.5,betmgm,0.6262,105.0,-140.0,0.4554,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,pra,starter,24.4846,23.5,23.5,betparx,0.557,-122.0,-109.0,0.5131,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,pts,starter,13.5084,11.5,11.5,betmgm,0.6185,-135.0,100.0,0.5347,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,reb,starter,4.182,3.5,3.5,betmgm,0.6823,-120.0,-110.0,0.5101,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,ast,starter,2.7824,2.5,2.5,betmgm,0.5686,-165.0,125.0,0.5835,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,fg3m,starter,1.1385,1.5,1.5,betmgm,0.3547,110.0,-150.0,0.4425,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,tov,starter,1.1429,,,,,,,,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,stl,starter,0.6015,0.5,0.5,betparx,0.4333,-230.0,170.0,0.653,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,blk,starter,0.3299,0.5,0.5,betmgm,0.2379,105.0,-150.0,0.4484,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,stocks,starter,0.9388,1.5,1.5,betparx,0.2412,104.0,-137.0,0.4589,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,pa,starter,16.2908,14.5,14.5,betmgm,0.6053,-130.0,-105.0,0.5246,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,pr,starter,17.6904,15.5,15.5,betmgm,0.6301,-120.0,-110.0,0.5101,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,ra,starter,6.9644,6.5,6.5,betmgm,0.5879,-110.0,-120.0,0.4899,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,pra,starter,20.4728,18.5,18.5,betmgm,0.6132,-120.0,-110.0,0.5101,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,pts,starter,27.0935,27.5,27.5,betparx,0.4713,-117.0,-114.0,0.503,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,reb,starter,3.8918,3.5,3.5,betmgm,0.6212,115.0,-155.0,0.4335,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,ast,starter,6.415,5.5,5.5,betparx,0.6837,-143.0,108.0,0.5504,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,fg3m,starter,1.7289,2.5,2.5,betmgm,0.3173,105.0,-140.0,0.4554,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,tov,starter,1.5093,,,,,,,,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,stl,starter,0.7482,0.5,0.5,betparx,0.463,-210.0,155.0,0.6334,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21716137/morning/prop_summary.parquet`

- bytes: `17,496`
- rows: `180`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,NYK,SAS,21716137,pts,starter,16.303600597682827,16.5,16.5,betmgm,0.45681008492629277,-110.0,-120.0,0.48987854251012153,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,reb,starter,6.098457084250649,5.5,5.5,betmgm,0.6325925748320248,-105.0,-125.0,0.4796954314720812,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,ast,starter,2.0825264950290543,1.5,1.5,betmgm,0.6833576119511588,-135.0,100.0,0.5346534653465347,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,fg3m,starter,1.4863628774245532,2.5,2.5,betmgm,0.2707044241024781,125.0,-165.0,0.4165029469548134,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,tov,starter,1.182249660895564,,,,,,,,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,stl,starter,0.6318000843714691,1.5,1.5,betparx,0.13647670917602076,135.0,-182.0,0.3973509933774834,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,blk,starter,0.37019679387491733,0.5,0.5,betmgm,0.24395865259533206,-165.0,120.0,0.5780254777070064,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,stocks,starter,1.0019968782463862,2.5,2.5,betparx,0.11497209086646688,140.0,-190.0,0.38873994638069703,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,pa,starter,18.386127092711895,18.5,18.5,betmgm,0.4696290277599639,-120.0,-110.0,0.5101214574898786,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,pr,starter,22.402057681933456,22.5,22.5,betmgm,0.47469691069341746,120.0,-160.0,0.4248366013071895,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,ra,starter,8.180983579279689,7.5,7.5,betmgm,0.6262299164703704,105.0,-140.0,0.4554079696394686,latest_valid_report_selected,projected
OG Anunoby,18,NYK,SAS,21716137,pra,starter,24.4845841769625,23.5,23.5,betparx,0.5569639796792346,-122.0,-109.0,0.5130795235028978,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,pts,starter,13.508389455380117,11.5,11.5,betmgm,0.618533573710885,-135.0,100.0,0.5346534653465347,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,reb,starter,4.181961463680546,3.5,3.5,betmgm,0.6822633608724904,-120.0,-110.0,0.5101214574898786,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,ast,starter,2.7824361665657524,2.5,2.5,betmgm,0.5686307455098203,-165.0,125.0,0.5834970530451867,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,fg3m,starter,1.138482627285367,1.5,1.5,betmgm,0.35471382480551206,110.0,-150.0,0.4424778761061947,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,tov,starter,1.142875091532399,,,,,,,,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,stl,starter,0.6014877847970497,0.5,0.5,betparx,0.43329809558710897,-230.0,170.0,0.6529968454258674,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,blk,starter,0.32989951112847105,0.5,0.5,betmgm,0.23786357185745846,105.0,-150.0,0.44843049327354256,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,stocks,starter,0.9387605614921863,1.5,1.5,betparx,0.24115083812817106,104.0,-137.0,0.4588754646840148,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,pa,starter,16.290825621945817,14.5,14.5,betmgm,0.6052639311879293,-130.0,-105.0,0.5246062992125985,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,pr,starter,17.690350919060602,15.5,15.5,betmgm,0.6300624200822209,-120.0,-110.0,0.5101214574898786,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,ra,starter,6.964397630246298,6.5,6.5,betmgm,0.5879169696541322,-110.0,-120.0,0.48987854251012153,latest_valid_report_selected,projected
Mikal Bridges,61,NYK,SAS,21716137,pra,starter,20.472787085626393,18.5,18.5,betmgm,0.6131558738042221,-120.0,-110.0,0.5101214574898786,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,pts,starter,27.093506607314904,27.5,27.5,betparx,0.4712924977196742,-117.0,-114.0,0.5030135004821601,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,reb,starter,3.8917693808027662,3.5,3.5,betmgm,0.6212336909566281,115.0,-155.0,0.43348916277093075,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,ast,starter,6.415026376759862,5.5,5.5,betparx,0.6836786359377166,-143.0,108.0,0.5503663681444749,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,fg3m,starter,1.728891751142624,2.5,2.5,betmgm,0.31734293842238964,105.0,-140.0,0.4554079696394686,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,tov,starter,1.5093260483350808,,,,,,,,latest_valid_report_selected,projected
Jalen Brunson,73,NYK,SAS,21716137,stl,starter,0.748165698117875,0.5,0.5,betparx,0.46297613754586736,-210.0,155.0,0.6333530455351862,latest_valid_report_selected,projected

```
