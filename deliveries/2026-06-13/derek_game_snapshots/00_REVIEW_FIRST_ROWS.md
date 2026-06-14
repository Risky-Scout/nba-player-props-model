# Reviewable Delivery Preview — 2026-06-13 — derek_game_snapshots

GitHub may refuse to render large CSV files. This file is intentionally small.

---

## `derek_game_snapshots/21716138/current_live/after_game_scoring.csv`

- bytes: `2,551`
- rows: `41`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,stat,line
De'Aaron Fox,161,reb,3.5
De'Aaron Fox,161,ast,6.5
De'Aaron Fox,161,stl,1.5
Jose Alvarado,17896097,fg3m,0.5
Jose Alvarado,17896097,stl,0.5
Landry Shamet,414,fg3m,1.5
Landry Shamet,414,stl,0.5
Miles McBride,17896033,fg3m,0.5
Jalen Brunson,73,pts,28.5
Jalen Brunson,73,reb,3.5
Jalen Brunson,73,fg3m,2.5
Josh Hart,202,reb,8.5
Josh Hart,202,ast,4.5
Josh Hart,202,fg3m,1.5
Josh Hart,202,stl,1.5
Stephon Castle,1028025261,ast,6.5
Devin Vassell,3547246,pts,13.5
Devin Vassell,3547246,ast,2.5
Devin Vassell,3547246,fg3m,2.5
Mitchell Robinson,399,stl,0.5
Mitchell Robinson,399,blk,0.5
OG Anunoby,18,pts,17.5
OG Anunoby,18,fg3m,2.5
OG Anunoby,18,stl,1.5
Dylan Harper,1057262518,pts,14.5
Dylan Harper,1057262518,reb,5.5
Dylan Harper,1057262518,ast,3.5
Dylan Harper,1057262518,blk,0.5
Keldon Johnson,666682,reb,2.5
Keldon Johnson,666682,fg3m,0.5

```

---

## `derek_game_snapshots/21716138/current_live/contextual_feature_audit.csv`

- bytes: `4,828`
- rows: `15`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716138
Jose Alvarado,17896097,NYK,21716138
Landry Shamet,414,NYK,21716138
Miles McBride,17896033,NYK,21716138
Jalen Brunson,73,NYK,21716138
Josh Hart,202,NYK,21716138
Stephon Castle,1028025261,SAS,21716138
Devin Vassell,3547246,SAS,21716138
Mitchell Robinson,399,NYK,21716138
OG Anunoby,18,NYK,21716138
Dylan Harper,1057262518,SAS,21716138
Keldon Johnson,666682,SAS,21716138
Mikal Bridges,61,NYK,21716138
Victor Wembanyama,56677822,SAS,21716138
Karl-Anthony Towns,447,NYK,21716138

```

---

## `derek_game_snapshots/21716138/current_live/contextual_feature_audit.parquet`

- bytes: `29,845`
- rows: `15`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716138
Jose Alvarado,17896097,NYK,21716138
Landry Shamet,414,NYK,21716138
Miles McBride,17896033,NYK,21716138
Jalen Brunson,73,NYK,21716138
Josh Hart,202,NYK,21716138
Stephon Castle,1028025261,SAS,21716138
Devin Vassell,3547246,SAS,21716138
Mitchell Robinson,399,NYK,21716138
OG Anunoby,18,NYK,21716138
Dylan Harper,1057262518,SAS,21716138
Keldon Johnson,666682,SAS,21716138
Mikal Bridges,61,NYK,21716138
Victor Wembanyama,56677822,SAS,21716138
Karl-Anthony Towns,447,NYK,21716138

```

---

## `derek_game_snapshots/21716138/current_live/derek_live_predictions.parquet`

- bytes: `39,920`
- rows: `41`
- columns: `47`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1454
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0666
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1313
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.0889
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.2018
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,0.1445
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1071
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.255
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,28.5,-0.0967
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.127
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0875
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.5,-0.1253
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,-0.1148
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1331
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1826
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.1855
Devin Vassell,3547246,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.031
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1758
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0809
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.1231
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.1693
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1347
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1671
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,14.5,-0.2118
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1741
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.1074
Keldon Johnson,666682,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2969

```

---

## `derek_game_snapshots/21716138/current_live/full_pmf_wide.csv`

- bytes: `45,581`
- rows: `41`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1454
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0666
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1313
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.0889
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.2018
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,0.1445
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1071
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.255
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,28.5,-0.0967
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.127
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0875
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.5,-0.1253
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,-0.1148
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1331
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1826
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.1855
Devin Vassell,3547246,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.031
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1758
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0809
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.1231
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.1693
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1347
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1671
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,14.5,-0.2118
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1741
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.1074
Keldon Johnson,666682,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2969

```

---

## `derek_game_snapshots/21716138/current_live/full_pmf_wide.parquet`

- bytes: `73,523`
- rows: `41`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1454
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0666
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1313
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.0889
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.2018
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,0.1445
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1071
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.255
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,28.5,-0.0967
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.127
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0875
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.5,-0.1253
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,-0.1148
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1331
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1826
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.1855
Devin Vassell,3547246,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.031
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1758
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0809
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.1231
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.1693
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1347
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1671
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,14.5,-0.2118
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1741
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.1074
Keldon Johnson,666682,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2969

```

---

## `derek_game_snapshots/21716138/current_live/game_context.csv`

- bytes: `608`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,NYK,21716138
Jose Alvarado,17896097,NYK,SAS,21716138
Landry Shamet,414,NYK,SAS,21716138
Miles McBride,17896033,NYK,SAS,21716138
Jalen Brunson,73,NYK,SAS,21716138
Josh Hart,202,NYK,SAS,21716138
Stephon Castle,1028025261,SAS,NYK,21716138
Devin Vassell,3547246,SAS,NYK,21716138
Mitchell Robinson,399,NYK,SAS,21716138
OG Anunoby,18,NYK,SAS,21716138
Dylan Harper,1057262518,SAS,NYK,21716138
Keldon Johnson,666682,SAS,NYK,21716138
Mikal Bridges,61,NYK,SAS,21716138
Victor Wembanyama,56677822,SAS,NYK,21716138
Karl-Anthony Towns,447,NYK,SAS,21716138

```

---

## `derek_game_snapshots/21716138/current_live/game_context.parquet`

- bytes: `3,640`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,NYK,21716138
Jose Alvarado,17896097,NYK,SAS,21716138
Landry Shamet,414,NYK,SAS,21716138
Miles McBride,17896033,NYK,SAS,21716138
Jalen Brunson,73,NYK,SAS,21716138
Josh Hart,202,NYK,SAS,21716138
Stephon Castle,1028025261,SAS,NYK,21716138
Devin Vassell,3547246,SAS,NYK,21716138
Mitchell Robinson,399,NYK,SAS,21716138
OG Anunoby,18,NYK,SAS,21716138
Dylan Harper,1057262518,SAS,NYK,21716138
Keldon Johnson,666682,SAS,NYK,21716138
Mikal Bridges,61,NYK,SAS,21716138
Victor Wembanyama,56677822,SAS,NYK,21716138
Karl-Anthony Towns,447,NYK,SAS,21716138

```

---

## `derek_game_snapshots/21716138/current_live/injury_availability_context.csv`

- bytes: `597`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716138
Jose Alvarado,17896097,NYK,21716138
Landry Shamet,414,NYK,21716138
Miles McBride,17896033,NYK,21716138
Jalen Brunson,73,NYK,21716138
Josh Hart,202,NYK,21716138
Stephon Castle,1028025261,SAS,21716138
Devin Vassell,3547246,SAS,21716138
Mitchell Robinson,399,NYK,21716138
OG Anunoby,18,NYK,21716138
Dylan Harper,1057262518,SAS,21716138
Keldon Johnson,666682,SAS,21716138
Mikal Bridges,61,NYK,21716138
Victor Wembanyama,56677822,SAS,21716138
Karl-Anthony Towns,447,NYK,21716138

```

---

## `derek_game_snapshots/21716138/current_live/injury_availability_context.parquet`

- bytes: `3,842`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716138
Jose Alvarado,17896097,NYK,21716138
Landry Shamet,414,NYK,21716138
Miles McBride,17896033,NYK,21716138
Jalen Brunson,73,NYK,21716138
Josh Hart,202,NYK,21716138
Stephon Castle,1028025261,SAS,21716138
Devin Vassell,3547246,SAS,21716138
Mitchell Robinson,399,NYK,21716138
OG Anunoby,18,NYK,21716138
Dylan Harper,1057262518,SAS,21716138
Keldon Johnson,666682,SAS,21716138
Mikal Bridges,61,NYK,21716138
Victor Wembanyama,56677822,SAS,21716138
Karl-Anthony Towns,447,NYK,21716138

```

---

## `derek_game_snapshots/21716138/current_live/lineup_context.csv`

- bytes: `1,627`
- rows: `15`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21716138,reb
Jose Alvarado,17896097,NYK,21716138,fg3m
Landry Shamet,414,NYK,21716138,fg3m
Miles McBride,17896033,NYK,21716138,fg3m
Jalen Brunson,73,NYK,21716138,pts
Josh Hart,202,NYK,21716138,reb
Stephon Castle,1028025261,SAS,21716138,ast
Devin Vassell,3547246,SAS,21716138,pts
Mitchell Robinson,399,NYK,21716138,stl
OG Anunoby,18,NYK,21716138,pts
Dylan Harper,1057262518,SAS,21716138,pts
Keldon Johnson,666682,SAS,21716138,reb
Mikal Bridges,61,NYK,21716138,ast
Victor Wembanyama,56677822,SAS,21716138,pts
Karl-Anthony Towns,447,NYK,21716138,pts

```

---

## `derek_game_snapshots/21716138/current_live/lineup_context.parquet`

- bytes: `8,426`
- rows: `15`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21716138,reb
Jose Alvarado,17896097,NYK,21716138,fg3m
Landry Shamet,414,NYK,21716138,fg3m
Miles McBride,17896033,NYK,21716138,fg3m
Jalen Brunson,73,NYK,21716138,pts
Josh Hart,202,NYK,21716138,reb
Stephon Castle,1028025261,SAS,21716138,ast
Devin Vassell,3547246,SAS,21716138,pts
Mitchell Robinson,399,NYK,21716138,stl
OG Anunoby,18,NYK,21716138,pts
Dylan Harper,1057262518,SAS,21716138,pts
Keldon Johnson,666682,SAS,21716138,reb
Mikal Bridges,61,NYK,21716138,ast
Victor Wembanyama,56677822,SAS,21716138,pts
Karl-Anthony Towns,447,NYK,21716138,pts

```

---

## `derek_game_snapshots/21716138/current_live/market_comparison.csv`

- bytes: `61,208`
- rows: `41`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.396396396396398,0.0624,3.5,0.1454
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.54389828811693,0.0356,6.5,-0.0666
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0423957604239575,0.3686,1.5,-0.1313
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.9506,0.3848,0.5,0.0889
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.2756,0.7813,0.5,-0.2018
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.0799079907990805,0.0889,1.5,0.1445
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.4734,0.643,0.5,-0.1071
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4857,0.2101,0.5,0.255
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,25.91670853009143,0.0043,28.5,-0.0967
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.858445201362452,0.0669,3.5,0.127
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.108889111088891,0.1055,2.5,-0.0875
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.419555199358844,0.0197,8.5,-0.1253
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.016120957244417,0.0609,4.5,-0.1148
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.8152,0.1498,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.9629962996299628,0.4346,1.5,-0.1331
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.083633814102562,0.0436,6.5,-0.1826
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.096890672016048,0.022,13.5,-0.1855
Devin Vassell,3547246,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.3180180180180177,0.1664,2.5,-0.031
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.9956995699569955,0.1017,2.5,-0.1758
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.4046,0.6776,0.5,-0.0809
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.8737126287371264,0.3996,0.5,0.1231
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.42274872000803,0.007,17.5,-0.1693
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.0325,0.0965,2.5,-0.1347
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.9653000000000002,0.3989,1.5,-0.1671
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,11.814261357938015,0.017,14.5,-0.2118
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.819665565234807,0.0443,5.5,-0.1741
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.4648832782286347,0.1702,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.19001900190019,0.8336,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5016025641025643,0.1911,2.5,-0.1074
Keldon Johnson,666682,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4453,0.2111,0.5,0.2969

```

---

## `derek_game_snapshots/21716138/current_live/market_comparison.parquet`

- bytes: `88,814`
- rows: `41`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.396396396396398,0.0624,3.5,0.1454
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.54389828811693,0.0356,6.5,-0.0666
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0423957604239575,0.3686,1.5,-0.1313
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.9506,0.3848,0.5,0.0889
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.2756,0.7813,0.5,-0.2018
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.0799079907990805,0.0889,1.5,0.1445
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.47340000000000004,0.643,0.5,-0.1071
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4857,0.2101,0.5,0.255
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,25.91670853009143,0.0043,28.5,-0.0967
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.8584452013624517,0.0669,3.5,0.127
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.108889111088891,0.1055,2.5,-0.0875
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.419555199358844,0.0197,8.5,-0.1253
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.016120957244417,0.0609,4.5,-0.1148
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.8151999999999997,0.1498,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.9629962996299629,0.4346,1.5,-0.1331
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.083633814102562,0.0436,6.5,-0.1826
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.096890672016048,0.022,13.5,-0.1855
Devin Vassell,3547246,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.3180180180180177,0.1664,2.5,-0.031
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.9956995699569955,0.1017,2.5,-0.1758
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.40460000000000007,0.6776,0.5,-0.0809
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.8737126287371264,0.3996,0.5,0.1231
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.42274872000803,0.007,17.5,-0.1693
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.0325,0.0965,2.5,-0.1347
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.9653000000000002,0.3989,1.5,-0.1671
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,11.814261357938017,0.017,14.5,-0.2118
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.819665565234807,0.0443,5.5,-0.1741
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.4648832782286347,0.1702,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.19001900190019,0.8336,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5016025641025643,0.1911,2.5,-0.1074
Keldon Johnson,666682,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4453,0.2111,0.5,0.2969

```

---

## `derek_game_snapshots/21716138/current_live/outcome_level_probabilities.csv`

- bytes: `103,141`
- rows: `564`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21716138,reb,0,0.0625,3.5,current_live
De'Aaron Fox,161,21716138,reb,1,0.0779,3.5,current_live
De'Aaron Fox,161,21716138,reb,2,0.1101,3.5,current_live
De'Aaron Fox,161,21716138,reb,3,0.1441,3.5,current_live
De'Aaron Fox,161,21716138,reb,4,0.1261,3.5,current_live
De'Aaron Fox,161,21716138,reb,5,0.1656,3.5,current_live
De'Aaron Fox,161,21716138,reb,6,0.1139,3.5,current_live
De'Aaron Fox,161,21716138,reb,7,0.0806,3.5,current_live
De'Aaron Fox,161,21716138,reb,8,0.0545,3.5,current_live
De'Aaron Fox,161,21716138,reb,9,0.0275,3.5,current_live
De'Aaron Fox,161,21716138,reb,10,0.0176,3.5,current_live
De'Aaron Fox,161,21716138,reb,11,0.0133,3.5,current_live
De'Aaron Fox,161,21716138,reb,12,0.0031,3.5,current_live
De'Aaron Fox,161,21716138,reb,13,0.0021,3.5,current_live
De'Aaron Fox,161,21716138,reb,14,0.0011,3.5,current_live
De'Aaron Fox,161,21716138,ast,0,0.0356,6.5,current_live
De'Aaron Fox,161,21716138,ast,1,0.0518,6.5,current_live
De'Aaron Fox,161,21716138,ast,2,0.059,6.5,current_live
De'Aaron Fox,161,21716138,ast,3,0.1013,6.5,current_live
De'Aaron Fox,161,21716138,ast,4,0.1183,6.5,current_live
De'Aaron Fox,161,21716138,ast,5,0.146,6.5,current_live
De'Aaron Fox,161,21716138,ast,6,0.1151,6.5,current_live
De'Aaron Fox,161,21716138,ast,7,0.1356,6.5,current_live
De'Aaron Fox,161,21716138,ast,8,0.0922,6.5,current_live
De'Aaron Fox,161,21716138,ast,9,0.061,6.5,current_live
De'Aaron Fox,161,21716138,ast,10,0.0335,6.5,current_live
De'Aaron Fox,161,21716138,ast,11,0.0246,6.5,current_live
De'Aaron Fox,161,21716138,ast,12,0.0129,6.5,current_live
De'Aaron Fox,161,21716138,ast,13,0.0067,6.5,current_live
De'Aaron Fox,161,21716138,ast,14,0.0035,6.5,current_live

```

---

## `derek_game_snapshots/21716138/current_live/outcome_level_probabilities.parquet`

- bytes: `19,112`
- rows: `564`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21716138,reb,0,0.06246246246246247,3.5,current_live
De'Aaron Fox,161,21716138,reb,1,0.07787787787787788,3.5,current_live
De'Aaron Fox,161,21716138,reb,2,0.11011011011011013,3.5,current_live
De'Aaron Fox,161,21716138,reb,3,0.14414414414414414,3.5,current_live
De'Aaron Fox,161,21716138,reb,4,0.12612612612612614,3.5,current_live
De'Aaron Fox,161,21716138,reb,5,0.16556556556556556,3.5,current_live
De'Aaron Fox,161,21716138,reb,6,0.11391391391391392,3.5,current_live
De'Aaron Fox,161,21716138,reb,7,0.0805805805805806,3.5,current_live
De'Aaron Fox,161,21716138,reb,8,0.05445445445445446,3.5,current_live
De'Aaron Fox,161,21716138,reb,9,0.02752752752752753,3.5,current_live
De'Aaron Fox,161,21716138,reb,10,0.017617617617617622,3.5,current_live
De'Aaron Fox,161,21716138,reb,11,0.013313313313313315,3.5,current_live
De'Aaron Fox,161,21716138,reb,12,0.003103103103103103,3.5,current_live
De'Aaron Fox,161,21716138,reb,13,0.002102102102102102,3.5,current_live
De'Aaron Fox,161,21716138,reb,14,0.0011011011011011014,3.5,current_live
De'Aaron Fox,161,21716138,ast,0,0.035639203123435784,6.5,current_live
De'Aaron Fox,161,21716138,ast,1,0.051756932625888485,6.5,current_live
De'Aaron Fox,161,21716138,ast,2,0.05896486134748224,6.5,current_live
De'Aaron Fox,161,21716138,ast,3,0.10131144258684553,6.5,current_live
De'Aaron Fox,161,21716138,ast,4,0.11833016317949746,6.5,current_live
De'Aaron Fox,161,21716138,ast,5,0.14596055661227353,6.5,current_live
De'Aaron Fox,161,21716138,ast,6,0.11512663930323358,6.5,current_live
De'Aaron Fox,161,21716138,ast,7,0.13564921413554912,6.5,current_live
De'Aaron Fox,161,21716138,ast,8,0.0922014215637201,6.5,current_live
De'Aaron Fox,161,21716138,ast,9,0.06096706377014717,6.5,current_live
De'Aaron Fox,161,21716138,ast,10,0.03353689057963761,6.5,current_live
De'Aaron Fox,161,21716138,ast,11,0.02462708979877866,6.5,current_live
De'Aaron Fox,161,21716138,ast,12,0.012914205626188809,6.5,current_live
De'Aaron Fox,161,21716138,ast,13,0.006707378115927521,6.5,current_live
De'Aaron Fox,161,21716138,ast,14,0.0035038542396636303,6.5,current_live

```

---

## `derek_game_snapshots/21716138/current_live/pmf_driver_decomposition.csv`

- bytes: `3,166`
- rows: `15`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21716138,reb,3.5
Jose Alvarado,17896097,NYK,21716138,fg3m,0.5
Landry Shamet,414,NYK,21716138,fg3m,1.5
Miles McBride,17896033,NYK,21716138,fg3m,0.5
Jalen Brunson,73,NYK,21716138,pts,28.5
Josh Hart,202,NYK,21716138,reb,8.5
Stephon Castle,1028025261,SAS,21716138,ast,6.5
Devin Vassell,3547246,SAS,21716138,pts,13.5
Mitchell Robinson,399,NYK,21716138,stl,0.5
OG Anunoby,18,NYK,21716138,pts,17.5
Dylan Harper,1057262518,SAS,21716138,pts,14.5
Keldon Johnson,666682,SAS,21716138,reb,2.5
Mikal Bridges,61,NYK,21716138,ast,2.5
Victor Wembanyama,56677822,SAS,21716138,pts,28.5
Karl-Anthony Towns,447,NYK,21716138,pts,16.5

```

---

## `derek_game_snapshots/21716138/current_live/pmf_driver_decomposition.parquet`

- bytes: `14,459`
- rows: `15`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21716138,reb,3.5
Jose Alvarado,17896097,NYK,21716138,fg3m,0.5
Landry Shamet,414,NYK,21716138,fg3m,1.5
Miles McBride,17896033,NYK,21716138,fg3m,0.5
Jalen Brunson,73,NYK,21716138,pts,28.5
Josh Hart,202,NYK,21716138,reb,8.5
Stephon Castle,1028025261,SAS,21716138,ast,6.5
Devin Vassell,3547246,SAS,21716138,pts,13.5
Mitchell Robinson,399,NYK,21716138,stl,0.5
OG Anunoby,18,NYK,21716138,pts,17.5
Dylan Harper,1057262518,SAS,21716138,pts,14.5
Keldon Johnson,666682,SAS,21716138,reb,2.5
Mikal Bridges,61,NYK,21716138,ast,2.5
Victor Wembanyama,56677822,SAS,21716138,pts,28.5
Karl-Anthony Towns,447,NYK,21716138,pts,16.5

```

---

## `derek_game_snapshots/21716138/current_live/prediction_input_audit.csv`

- bytes: `2,804`
- rows: `41`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716138,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716138,ast,6.5
De'Aaron Fox,161,SAS,NYK,21716138,stl,1.5
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,0.5
Jose Alvarado,17896097,NYK,SAS,21716138,stl,0.5
Landry Shamet,414,NYK,SAS,21716138,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716138,stl,0.5
Miles McBride,17896033,NYK,SAS,21716138,fg3m,0.5
Jalen Brunson,73,NYK,SAS,21716138,pts,28.5
Jalen Brunson,73,NYK,SAS,21716138,reb,3.5
Jalen Brunson,73,NYK,SAS,21716138,fg3m,2.5
Josh Hart,202,NYK,SAS,21716138,reb,8.5
Josh Hart,202,NYK,SAS,21716138,ast,4.5
Josh Hart,202,NYK,SAS,21716138,fg3m,1.5
Josh Hart,202,NYK,SAS,21716138,stl,1.5
Stephon Castle,1028025261,SAS,NYK,21716138,ast,6.5
Devin Vassell,3547246,SAS,NYK,21716138,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716138,ast,2.5
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,2.5
Mitchell Robinson,399,NYK,SAS,21716138,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716138,blk,0.5
OG Anunoby,18,NYK,SAS,21716138,pts,17.5
OG Anunoby,18,NYK,SAS,21716138,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716138,stl,1.5
Dylan Harper,1057262518,SAS,NYK,21716138,pts,14.5
Dylan Harper,1057262518,SAS,NYK,21716138,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716138,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716138,blk,0.5
Keldon Johnson,666682,SAS,NYK,21716138,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716138,fg3m,0.5

```

---

## `derek_game_snapshots/21716138/current_live/prediction_input_audit.parquet`

- bytes: `5,424`
- rows: `41`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716138,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716138,ast,6.5
De'Aaron Fox,161,SAS,NYK,21716138,stl,1.5
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,0.5
Jose Alvarado,17896097,NYK,SAS,21716138,stl,0.5
Landry Shamet,414,NYK,SAS,21716138,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716138,stl,0.5
Miles McBride,17896033,NYK,SAS,21716138,fg3m,0.5
Jalen Brunson,73,NYK,SAS,21716138,pts,28.5
Jalen Brunson,73,NYK,SAS,21716138,reb,3.5
Jalen Brunson,73,NYK,SAS,21716138,fg3m,2.5
Josh Hart,202,NYK,SAS,21716138,reb,8.5
Josh Hart,202,NYK,SAS,21716138,ast,4.5
Josh Hart,202,NYK,SAS,21716138,fg3m,1.5
Josh Hart,202,NYK,SAS,21716138,stl,1.5
Stephon Castle,1028025261,SAS,NYK,21716138,ast,6.5
Devin Vassell,3547246,SAS,NYK,21716138,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716138,ast,2.5
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,2.5
Mitchell Robinson,399,NYK,SAS,21716138,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716138,blk,0.5
OG Anunoby,18,NYK,SAS,21716138,pts,17.5
OG Anunoby,18,NYK,SAS,21716138,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716138,stl,1.5
Dylan Harper,1057262518,SAS,NYK,21716138,pts,14.5
Dylan Harper,1057262518,SAS,NYK,21716138,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716138,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716138,blk,0.5
Keldon Johnson,666682,SAS,NYK,21716138,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716138,fg3m,0.5

```

---

## `derek_game_snapshots/21716138/current_live/prop_summary.csv`

- bytes: `2,054`
- rows: `41`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716138,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716138,ast,6.5
De'Aaron Fox,161,SAS,NYK,21716138,stl,1.5
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,0.5
Jose Alvarado,17896097,NYK,SAS,21716138,stl,0.5
Landry Shamet,414,NYK,SAS,21716138,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716138,stl,0.5
Miles McBride,17896033,NYK,SAS,21716138,fg3m,0.5
Jalen Brunson,73,NYK,SAS,21716138,pts,28.5
Jalen Brunson,73,NYK,SAS,21716138,reb,3.5
Jalen Brunson,73,NYK,SAS,21716138,fg3m,2.5
Josh Hart,202,NYK,SAS,21716138,reb,8.5
Josh Hart,202,NYK,SAS,21716138,ast,4.5
Josh Hart,202,NYK,SAS,21716138,fg3m,1.5
Josh Hart,202,NYK,SAS,21716138,stl,1.5
Stephon Castle,1028025261,SAS,NYK,21716138,ast,6.5
Devin Vassell,3547246,SAS,NYK,21716138,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716138,ast,2.5
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,2.5
Mitchell Robinson,399,NYK,SAS,21716138,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716138,blk,0.5
OG Anunoby,18,NYK,SAS,21716138,pts,17.5
OG Anunoby,18,NYK,SAS,21716138,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716138,stl,1.5
Dylan Harper,1057262518,SAS,NYK,21716138,pts,14.5
Dylan Harper,1057262518,SAS,NYK,21716138,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716138,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716138,blk,0.5
Keldon Johnson,666682,SAS,NYK,21716138,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716138,fg3m,0.5

```

---

## `derek_game_snapshots/21716138/current_live/prop_summary.parquet`

- bytes: `4,833`
- rows: `41`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716138,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716138,ast,6.5
De'Aaron Fox,161,SAS,NYK,21716138,stl,1.5
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,0.5
Jose Alvarado,17896097,NYK,SAS,21716138,stl,0.5
Landry Shamet,414,NYK,SAS,21716138,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716138,stl,0.5
Miles McBride,17896033,NYK,SAS,21716138,fg3m,0.5
Jalen Brunson,73,NYK,SAS,21716138,pts,28.5
Jalen Brunson,73,NYK,SAS,21716138,reb,3.5
Jalen Brunson,73,NYK,SAS,21716138,fg3m,2.5
Josh Hart,202,NYK,SAS,21716138,reb,8.5
Josh Hart,202,NYK,SAS,21716138,ast,4.5
Josh Hart,202,NYK,SAS,21716138,fg3m,1.5
Josh Hart,202,NYK,SAS,21716138,stl,1.5
Stephon Castle,1028025261,SAS,NYK,21716138,ast,6.5
Devin Vassell,3547246,SAS,NYK,21716138,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716138,ast,2.5
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,2.5
Mitchell Robinson,399,NYK,SAS,21716138,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716138,blk,0.5
OG Anunoby,18,NYK,SAS,21716138,pts,17.5
OG Anunoby,18,NYK,SAS,21716138,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716138,stl,1.5
Dylan Harper,1057262518,SAS,NYK,21716138,pts,14.5
Dylan Harper,1057262518,SAS,NYK,21716138,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716138,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716138,blk,0.5
Keldon Johnson,666682,SAS,NYK,21716138,reb,2.5
Keldon Johnson,666682,SAS,NYK,21716138,fg3m,0.5

```

---

## `derek_game_snapshots/21716138/morning/full_pmf_wide.csv`

- bytes: `372,709`
- rows: `192`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,5.6455,5.6455,6,6,0.0032,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,1.9687,1.9687,2,2,0.0429,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,1.8093,1.8093,2,0,0.3945,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,1.2158,1.2158,1,1,0.1198,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,0.7894,0.7894,0,0,0.5091,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,0.3783,0.3783,0,0,0.7629,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.011,35.3676,0.05,1.1324,1.1324,1,0,0.3884,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.011,35.3676,0.05,18.4441,18.4441,18,18,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.011,35.3676,0.05,22.1209,22.1209,22,22,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.011,35.3676,0.05,7.6142,7.6142,8,8,0.0001,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.011,35.3676,0.05,24.0896,24.0896,24,24,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8643,32.6084,0.05,12.7882,12.7882,13,13,0.002,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8643,32.6084,0.05,3.8699,3.8699,4,4,0.0087,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8643,32.6084,0.05,2.7252,2.7252,3,2,0.0179,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8643,32.6084,0.05,1.1519,1.1519,1,0,0.4029,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8643,32.6084,0.05,1.2121,1.2121,1,1,0.1154,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8643,32.6084,0.05,0.6345,0.6345,0,0,0.5328,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8643,32.6084,0.05,0.323,0.323,0,0,0.7461,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8643,32.6084,0.05,0.9671,0.9671,1,0,0.3975,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8643,32.6084,0.05,15.5134,15.5134,15,15,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8643,32.6084,0.05,16.6581,16.6581,16,17,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8643,32.6084,0.05,6.5951,6.5951,7,6,0.0002,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8643,32.6084,0.05,19.3832,19.3832,19,19,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.855,36.7394,0.05,28.162,28.162,28,29,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.855,36.7394,0.05,4.0839,4.0839,4,4,0.0064,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.855,36.7394,0.05,6.1574,6.1574,6,7,0.0047,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.855,36.7394,0.05,2.3336,2.3336,2,0,0.4007,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.855,36.7394,0.05,1.5667,1.5667,2,2,0.1093,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.855,36.7394,0.05,0.7885,0.7885,0,0,0.5119,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/full_pmf_wide.parquet`

- bytes: `208,171`
- rows: `192`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,5.6454981938643405,5.645498193864341,6,6,0.0032005754669008793,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,1.9687142736627214,1.968714273662721,2,2,0.042927169955385806,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,1.809290866936096,1.809290866936096,2,0,0.39445679384557614,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,1.2157660999389404,1.2157660999389406,1,1,0.11981109260485748,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,0.789351087836143,0.789351087836143,0,0,0.5090554688063025,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,0.3782960586192103,0.37829605861921034,0,0,0.76291044282263,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.010982920291184,35.36755462857424,0.050000000000000044,1.132352543305043,1.132352543305043,1,0,0.38836373312829764,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.010982920291184,35.36755462857424,0.050000000000000044,18.4441181121687,18.444118112168706,18,18,2.8577101673994803e-05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.010982920291184,35.36755462857424,0.050000000000000044,22.120902032370317,22.120902032370314,22,22,2.130659221839629e-06,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.010982920291184,35.36755462857424,0.050000000000000044,7.614212467527063,7.614212467527062,8,8,0.00013739164702269231,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.010982920291184,35.36755462857424,0.050000000000000044,24.089616306033026,24.08961630603302,24,24,9.146317053291983e-08,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.864261317077787,32.60836927251124,0.050000000000000044,12.788183187260637,12.788183187260636,13,13,0.0020409813102744484,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.864261317077787,32.60836927251124,0.050000000000000044,3.8698742753095114,3.869874275309511,4,4,0.008714273375118252,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.864261317077787,32.60836927251124,0.050000000000000044,2.725184929078539,2.7251849290785386,3,2,0.017874650792295402,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.864261317077787,32.60836927251124,0.050000000000000044,1.1518630615235272,1.1518630615235272,1,0,0.4029384755331976,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.864261317077787,32.60836927251124,0.050000000000000044,1.212071288802766,1.2120712888027663,1,1,0.1154128886583441,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.864261317077787,32.60836927251124,0.050000000000000044,0.6345109263464038,0.6345109263464037,0,0,0.5327855875627525,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.864261317077787,32.60836927251124,0.050000000000000044,0.3229656110103885,0.3229656110103885,0,0,0.746128617607881,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.864261317077787,32.60836927251124,0.050000000000000044,0.9670932531496343,0.9670932531496343,1,0,0.3975265739295991,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.864261317077787,32.60836927251124,0.050000000000000044,15.51336811633917,15.513368116339176,15,15,3.6481828194757266e-05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.864261317077787,32.60836927251124,0.050000000000000044,16.658057462570135,16.658057462570135,16,17,1.778566909123859e-05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.864261317077787,32.60836927251124,0.050000000000000044,6.595059204388045,6.595059204388044,7,6,0.00015576459348883617,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mikal Bridges,61,NYK,SAS,21716138,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.864261317077787,32.60836927251124,0.050000000000000044,19.383242391648633,19.383242391648626,19,19,3.179126241132119e-07,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.85504390077265,36.73938616938365,0.050000000000000044,28.16202829526128,28.162028295261262,28,29,4.851400629890724e-05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.85504390077265,36.73938616938365,0.050000000000000044,4.083923128761348,4.0839231287613496,4,4,0.00635998272685019,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.85504390077265,36.73938616938365,0.050000000000000044,6.157415571801391,6.157415571801393,6,7,0.00472151354755727,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.85504390077265,36.73938616938365,0.050000000000000044,2.333560242774647,2.333560242774647,2,0,0.40065757022062526,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.85504390077265,36.73938616938365,0.050000000000000044,1.566656362742573,1.5666563627425727,2,2,0.10927590447850763,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.85504390077265,36.73938616938365,0.050000000000000044,0.788486765353584,0.7884867653535839,0,0,0.5119295080014331,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/market_comparison.csv`

- bytes: `524,009`
- rows: `589`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,fanduel,0.372,-108,-120,0.4877,-0.1156,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,24.5,24.5,fanduel,0.0705,450,-750,0.1709,-0.1003,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,23.5,23.5,fanduel,0.095,360,-580,0.2031,-0.1081,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,22.5,22.5,fanduel,0.1177,280,-420,0.2457,-0.128,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,21.5,21.5,fanduel,0.16,225,-320,0.2877,-0.1277,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,20.5,20.5,fanduel,0.2101,182,-250,0.3318,-0.1216,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,19.5,19.5,fanduel,0.2584,146,-198,0.3796,-0.1212,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,18.5,18.5,fanduel,0.3126,116,-154,0.433,-0.1204,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,fanduel,0.372,-110,-122,0.488,-0.116,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,16.5,16.5,fanduel,0.4704,-140,106,0.5458,-0.0754,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,15.5,15.5,fanduel,0.5667,-186,138,0.6075,-0.0408,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,14.5,14.5,fanduel,0.6373,-235,178,0.661,-0.0238,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,13.5,13.5,fanduel,0.7177,-320,225,0.7123,0.0054,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,12.5,12.5,fanduel,0.7785,-440,290,0.7606,0.0179,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,11.5,11.5,fanduel,0.8374,-600,370,0.8011,0.0363,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,10.5,10.5,fanduel,0.8778,-900,490,0.8415,0.0363,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,williamhill_us,0.372,-112,-121,0.4911,-0.119,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,20.5,20.5,bovada,0.2101,185,-250,0.3294,-0.1193,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,19.5,19.5,bovada,0.2584,150,-200,0.375,-0.1166,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,18.5,18.5,bovada,0.3126,120,-160,0.4248,-0.1123,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,bovada,0.372,-105,-125,0.4797,-0.1076,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,16.5,16.5,bovada,0.4704,-130,100,0.5306,-0.0602,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,15.5,15.5,bovada,0.5667,-170,130,0.5915,-0.0248,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,14.5,14.5,bovada,0.6373,-230,170,0.653,-0.0157,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,betmgm,0.372,-105,-125,0.4797,-0.1076,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,18.5,18.5,betrivers,0.3126,106,-143,0.452,-0.1395,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,betrivers,0.372,-121,-113,0.5079,-0.1358,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,16.5,16.5,betrivers,0.4704,-155,114,0.5654,-0.0949,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,draftkings,0.372,-110,-115,0.4948,-0.1227,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,hardrockbet_az,0.372,-125,-105,0.5203,-0.1483,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/market_comparison.parquet`

- bytes: `147,017`
- rows: `2,837`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,17.5,17.5,fanduel,0.37204556153633334,-108,-120,0.4876847290640395,-0.11563916752770614,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,24.5,24.5,fanduel,0.07050839056636836,450,-750,0.1708542713567839,-0.10034588079041554,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,23.5,23.5,fanduel,0.09502865481384015,360,-580,0.20310633213859022,-0.10807767732475007,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,22.5,22.5,fanduel,0.1176972507147383,280,-420,0.24574669187145556,-0.12804944115671726,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,21.5,21.5,fanduel,0.15996207582122124,225,-320,0.28767123287671237,-0.12770915705549105,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,20.5,20.5,fanduel,0.21011386207896007,182,-250,0.3317535545023697,-0.12163969242340955,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,19.5,19.5,fanduel,0.2584130347644585,146,-198,0.37957915116930757,-0.12116611640484909,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,18.5,18.5,fanduel,0.3125729469583935,116,-154,0.4329742261011864,-0.12040127914279292,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,17.5,17.5,fanduel,0.37204556153633334,-110,-122,0.48800959232613905,-0.11596403078980572,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,16.5,16.5,fanduel,0.4704432855027731,-140,106,0.5457986373959123,-0.07535535189313913,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,15.5,15.5,fanduel,0.5667071646156825,-186,138,0.6075094691771422,-0.040802304561459835,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,14.5,14.5,fanduel,0.6372634174718839,-235,178,0.6610340989578064,-0.02377068148592254,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,13.5,13.5,fanduel,0.717720942961997,-320,225,0.7123287671232876,0.005392175838709212,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,12.5,12.5,fanduel,0.7785456147416251,-440,290,0.7606382978723404,0.017907316869284595,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,11.5,11.5,fanduel,0.8374463064190513,-600,370,0.8011363636363636,0.03630994278268751,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,10.5,10.5,fanduel,0.877816934877737,-900,490,0.8415213946117275,0.03629554026600956,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,17.5,17.5,williamhill_us,0.37204556153633334,-112,-121,0.49107213713197356,-0.11902657559564023,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,20.5,20.5,bovada,0.21011386207896007,185,-250,0.32941176470588235,-0.11929790262692219,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,19.5,19.5,bovada,0.2584130347644585,150,-200,0.375,-0.11658696523554152,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,18.5,18.5,bovada,0.3125729469583935,120,-160,0.4248366013071895,-0.11226365434879598,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,17.5,17.5,bovada,0.37204556153633334,-105,-125,0.4796954314720812,-0.10764986993574788,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,16.5,16.5,bovada,0.4704432855027731,-130,100,0.5306122448979592,-0.06016895939518607,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,15.5,15.5,bovada,0.5667071646156825,-170,130,0.5915279878971256,-0.024820823281443194,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,14.5,14.5,bovada,0.6372634174718839,-230,170,0.6529968454258674,-0.01573342795398358,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,17.5,17.5,betmgm,0.37204556153633334,-105,-125,0.4796954314720812,-0.10764986993574788,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,18.5,18.5,betrivers,0.3125729469583935,106,-143,0.4520257450053946,-0.13945279804700111,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,17.5,17.5,betrivers,0.37204556153633334,-121,-113,0.5078823946715012,-0.13583683313516787,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,16.5,16.5,betrivers,0.4704432855027731,-155,114,0.5653656042270325,-0.09492231872425938,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,17.5,17.5,draftkings,0.37204556153633334,-110,-115,0.4947698744769875,-0.12272431294065417,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.010982920291184,35.36755462857424,0.050000000000000044,16.47540383850598,16.47540383850598,16,17,0.0006657112896958961,17.5,17.5,hardrockbet_az,0.37204556153633334,-125,-105,0.5203045685279188,-0.1482590069915855,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/market_comparison_csv_parts/market_comparison_part_000.csv`

- bytes: `488,647`
- rows: `555`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,fanduel,0.372,-108,-120,0.4877,-0.1156,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,24.5,24.5,fanduel,0.0705,450,-750,0.1709,-0.1003,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,23.5,23.5,fanduel,0.095,360,-580,0.2031,-0.1081,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,22.5,22.5,fanduel,0.1177,280,-420,0.2457,-0.128,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,21.5,21.5,fanduel,0.16,225,-320,0.2877,-0.1277,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,20.5,20.5,fanduel,0.2101,182,-250,0.3318,-0.1216,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,19.5,19.5,fanduel,0.2584,146,-198,0.3796,-0.1212,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,18.5,18.5,fanduel,0.3126,116,-154,0.433,-0.1204,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,fanduel,0.372,-110,-122,0.488,-0.116,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,16.5,16.5,fanduel,0.4704,-140,106,0.5458,-0.0754,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,15.5,15.5,fanduel,0.5667,-186,138,0.6075,-0.0408,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,14.5,14.5,fanduel,0.6373,-235,178,0.661,-0.0238,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,13.5,13.5,fanduel,0.7177,-320,225,0.7123,0.0054,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,12.5,12.5,fanduel,0.7785,-440,290,0.7606,0.0179,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,11.5,11.5,fanduel,0.8374,-600,370,0.8011,0.0363,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,10.5,10.5,fanduel,0.8778,-900,490,0.8415,0.0363,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,williamhill_us,0.372,-112,-121,0.4911,-0.119,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,20.5,20.5,bovada,0.2101,185,-250,0.3294,-0.1193,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,19.5,19.5,bovada,0.2584,150,-200,0.375,-0.1166,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,18.5,18.5,bovada,0.3126,120,-160,0.4248,-0.1123,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,bovada,0.372,-105,-125,0.4797,-0.1076,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,16.5,16.5,bovada,0.4704,-130,100,0.5306,-0.0602,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,15.5,15.5,bovada,0.5667,-170,130,0.5915,-0.0248,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,14.5,14.5,bovada,0.6373,-230,170,0.653,-0.0157,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,betmgm,0.372,-105,-125,0.4797,-0.1076,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,18.5,18.5,betrivers,0.3126,106,-143,0.452,-0.1395,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,betrivers,0.372,-121,-113,0.5079,-0.1358,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,16.5,16.5,betrivers,0.4704,-155,114,0.5654,-0.0949,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,draftkings,0.372,-110,-115,0.4948,-0.1227,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
OG Anunoby,18,NYK,SAS,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.011,35.3676,0.05,16.4754,16.4754,16,17,0.0007,17.5,17.5,hardrockbet_az,0.372,-125,-105,0.5203,-0.1483,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/market_comparison_csv_parts/market_comparison_part_001.csv`

- bytes: `518,962`
- rows: `555`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Jalen Brunson,73,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,34.3194,34.3194,34,34,0.0,34.5,34.5,bovada,0.4844,-130,100,0.5306,-0.0462,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,34.3194,34.3194,34,34,0.0,33.5,33.5,bovada,0.5456,-160,120,0.5752,-0.0296,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,34.3194,34.3194,34,34,0.0,33.5,33.5,betmgm,0.5456,-125,-105,0.5203,0.0253,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,34.3194,34.3194,34,34,0.0,35.5,35.5,draftkings,0.424,-108,-122,0.4858,-0.0618,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,34.3194,34.3194,34,34,0.0,34.5,34.5,hardrockbet_az,0.4844,-120,-110,0.5101,-0.0257,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,34.3194,34.3194,34,34,0.0,34.5,34.5,hardrockbet,0.4844,-120,-110,0.5101,-0.0257,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,34.3194,34.3194,34,34,0.0,34.5,34.5,hardrockbet_fl,0.4844,-115,-115,0.5,-0.0156,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,34.3194,34.3194,34,34,0.0,34.5,34.5,espnbet,0.4844,-120,-110,0.5101,-0.0257,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,34.3194,34.3194,34,34,0.0,34.5,34.5,fliff,0.4844,-125,-115,0.5095,-0.025,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,31.5,31.5,fanduel,0.5438,-106,-120,0.4854,0.0584,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,23.5,23.5,fanduel,0.8895,-650,390,0.8094,0.0801,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,22.5,22.5,fanduel,0.9119,-850,470,0.8361,0.0759,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,24.5,24.5,fanduel,0.8634,-470,310,0.7717,0.0917,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,25.5,25.5,fanduel,0.832,-390,265,0.7439,0.0881,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,27.5,27.5,fanduel,0.7529,-250,182,0.6682,0.0847,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,40.5,40.5,fanduel,0.1175,470,-850,0.1639,-0.0464,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,39.5,39.5,fanduel,0.1448,390,-650,0.1906,-0.0458,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,38.5,38.5,fanduel,0.1795,320,-500,0.2222,-0.0427,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,37.5,37.5,fanduel,0.2185,280,-420,0.2457,-0.0273,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,36.5,36.5,fanduel,0.261,235,-340,0.2787,-0.0177,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,35.5,35.5,fanduel,0.3075,198,-275,0.3139,-0.0065,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,34.5,34.5,fanduel,0.3588,168,-230,0.3487,0.0101,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,33.5,33.5,fanduel,0.4146,138,-186,0.3925,0.0221,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,32.5,32.5,fanduel,0.4791,114,-152,0.4365,0.0426,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,31.5,31.5,fanduel,0.5438,-108,-122,0.4858,0.058,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,30.5,30.5,fanduel,0.6022,-132,100,0.5323,0.0699,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,29.5,29.5,fanduel,0.6563,-160,120,0.5752,0.0811,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,28.5,28.5,fanduel,0.7065,-200,148,0.6231,0.0834,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,26.5,26.5,fanduel,0.7948,-310,220,0.7076,0.0872,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Jalen Brunson,73,NYK,SAS,21716138,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,33.855,36.7394,0.05,32.246,32.246,32,32,0.0,32.5,32.5,bovada,0.4791,-105,-125,0.4797,-0.0006,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/market_comparison_csv_parts/market_comparison_part_002.csv`

- bytes: `495,751`
- rows: `555`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,5.5,5.5,bovada,0.3535,165,-220,0.3544,-0.0009,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,4.5,4.5,bovada,0.5033,-115,-115,0.5,0.0033,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,3.5,3.5,bovada,0.6493,-240,175,0.66,-0.0107,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,4.5,4.5,hardrockbet_az,0.5033,-115,-115,0.5,0.0033,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,4.5,4.5,hardrockbet,0.5033,-115,-115,0.5,0.0033,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,4.5,4.5,hardrockbet_fl,0.5033,-115,-115,0.5,0.0033,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,4.5,4.5,rebet,0.5033,-106,-120,0.4854,0.0179,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,4.5,4.5,betparx,0.5033,-120,-112,0.508,-0.0047,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,4.5,4.5,fliff,0.5033,-120,-120,0.5,0.0033,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,5.5,5.5,espnbet,0.3535,150,-200,0.375,-0.0215,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,4.5,4.5,espnbet,0.5033,-105,-125,0.4797,0.0236,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,reb,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,4.5967,4.5967,5,5,0.0876,3.5,3.5,espnbet,0.6493,-190,140,0.6113,0.038,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,ast,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.5785,0.5785,1,0,0.4878,0.5,0.5,bovada,0.5122,190,-260,0.3232,0.189,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,ast,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.5785,0.5785,1,0,0.4878,0.5,0.5,draftkings,0.5122,198,-268,0.3154,0.1968,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,ast,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.5785,0.5785,1,0,0.4878,0.5,0.5,hardrockbet_az,0.5122,185,-240,0.332,0.1802,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,ast,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.5785,0.5785,1,0,0.4878,0.5,0.5,rebet,0.5122,174,-228,0.3443,0.1679,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,ast,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.5785,0.5785,1,0,0.4878,0.5,0.5,hardrockbet_fl,0.5122,185,-240,0.332,0.1802,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,ast,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.5785,0.5785,1,0,0.4878,0.5,0.5,hardrockbet,0.5122,185,-240,0.332,0.1802,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,ast,bench,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.5785,0.5785,1,0,0.4878,0.5,0.5,fliff,0.5122,180,-270,0.3286,0.1836,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,stl,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.3163,0.3163,0,0,0.7048,0.5,0.5,draftkings,0.2952,128,-171,0.4101,-0.1149,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,stl,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.3163,0.3163,0,0,0.7048,0.5,0.5,bovada,0.2952,125,-165,0.4165,-0.1213,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,stl,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.3163,0.3163,0,0,0.7048,0.5,0.5,hardrockbet,0.2952,120,-175,0.4167,-0.1215,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,stl,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.3163,0.3163,0,0,0.7048,0.5,0.5,hardrockbet_fl,0.2952,120,-175,0.4167,-0.1215,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,stl,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.3163,0.3163,0,0,0.7048,0.5,0.5,hardrockbet_az,0.2952,120,-175,0.4167,-0.1215,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,stl,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.3163,0.3163,0,0,0.7048,0.5,0.5,betparx,0.2952,130,-177,0.4049,-0.1097,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,blk,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.2847,0.2847,0,0,0.8082,0.5,0.5,bovada,0.1918,100,-130,0.4694,-0.2776,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,blk,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.2847,0.2847,0,0,0.8082,0.5,0.5,draftkings,0.1918,-101,-132,0.469,-0.2772,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,blk,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.2847,0.2847,0,0,0.8082,0.5,0.5,hardrockbet_az,0.1918,-105,-135,0.4713,-0.2796,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,blk,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.2847,0.2847,0,0,0.8082,0.5,0.5,hardrockbet_fl,0.1918,-105,-135,0.4713,-0.2796,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Mitchell Robinson,399,NYK,SAS,21716138,blk,bench,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:bench+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,14.4662,13.023,0.05,0.2847,0.2847,0,0,0.8082,0.5,0.5,betparx,0.1918,-109,-121,0.4878,-0.2961,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/market_comparison_csv_parts/market_comparison_part_003.csv`

- bytes: `493,384`
- rows: `555`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Devin Vassell,3547246,SAS,NYK,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,11.7404,11.7404,12,12,0.0022,14.5,14.5,hardrockbet_fl,0.271,-105,-125,0.4797,-0.2087,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,11.7404,11.7404,12,12,0.0022,12.5,12.5,espnbet,0.4044,-170,130,0.5915,-0.1871,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,11.7404,11.7404,12,12,0.0022,13.5,13.5,espnbet,0.3369,-125,-105,0.5203,-0.1834,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,11.7404,11.7404,12,12,0.0022,14.5,14.5,espnbet,0.271,100,-130,0.4694,-0.1983,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,11.7404,11.7404,12,12,0.0022,14.5,14.5,betparx,0.271,-103,-130,0.473,-0.202,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,11.7404,11.7404,12,12,0.0022,13.5,13.5,betparx,0.3369,-136,102,0.5379,-0.201,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,11.7404,11.7404,12,12,0.0022,13.5,13.5,fliff,0.3369,-130,-110,0.519,-0.1821,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,williamhill_us,0.6041,-150,112,0.5599,0.0442,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,fanduel,0.6041,-132,104,0.5372,0.0669,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,7.5,7.5,fanduel,0.0813,540,-1000,0.1467,-0.0654,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,6.5,6.5,fanduel,0.1639,290,-440,0.2394,-0.0754,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,5.5,5.5,fanduel,0.3301,158,-215,0.3622,-0.0321,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,fanduel,0.6041,-136,102,0.5379,0.0662,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,3.5,3.5,fanduel,0.8189,-310,220,0.7076,0.1114,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,betmgm,0.6041,-155,115,0.5665,0.0376,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,betrivers,0.6041,-152,112,0.5612,0.0429,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,draftkings,0.6041,-159,121,0.5757,0.0284,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,5.5,5.5,bovada,0.3301,120,-160,0.4248,-0.0947,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,bovada,0.6041,-160,120,0.5752,0.0289,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,hardrockbet_az,0.6041,-145,115,0.5599,0.0442,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,hardrockbet,0.6041,-145,115,0.5599,0.0442,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,hardrockbet_fl,0.6041,-145,115,0.5599,0.0442,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,rebet,0.6041,-141,111,0.5525,0.0516,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,5.5,5.5,espnbet,0.3301,125,-165,0.4165,-0.0864,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,espnbet,0.6041,-145,110,0.5541,0.05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,3.5,3.5,espnbet,0.8189,-325,225,0.7131,0.1058,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,betparx,0.6041,-152,114,0.5635,0.0406,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,4.9425,4.9425,5,5,0.0056,4.5,4.5,fliff,0.6041,-160,110,0.5638,0.0403,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,2.4832,2.4832,3,3,0.0265,2.5,2.5,bovada,0.5035,110,-145,0.4459,0.0576,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Devin Vassell,3547246,SAS,NYK,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.592,34.2326,0.05,2.4832,2.4832,3,3,0.0265,1.5,1.5,bovada,0.8217,-275,200,0.6875,0.1342,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/market_comparison_csv_parts/market_comparison_part_004.csv`

- bytes: `507,717`
- rows: `555`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,13.5,13.5,fanduel,0.0511,225,-320,0.2877,-0.2366,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,12.5,12.5,fanduel,0.1204,148,-200,0.3769,-0.2565,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,fanduel,0.1933,-108,-122,0.4858,-0.2925,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,10.5,10.5,fanduel,0.3115,-192,142,0.6141,-0.3026,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,9.5,9.5,fanduel,0.5056,-320,225,0.7123,-0.2067,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,8.5,8.5,fanduel,0.6918,-470,310,0.7717,-0.0799,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,williamhill_us,0.1933,-114,-117,0.497,-0.3037,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,fanduel,0.1933,-106,-120,0.4854,-0.2921,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,12.5,12.5,betmgm,0.1204,105,-145,0.4518,-0.3314,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,betrivers,0.1933,-117,-117,0.5,-0.3067,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,draftkings,0.1933,-117,-112,0.5051,-0.3118,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,13.5,13.5,bovada,0.0511,190,-260,0.3232,-0.2721,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,12.5,12.5,bovada,0.1204,125,-165,0.4165,-0.2961,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,bovada,0.1933,-120,-110,0.5101,-0.3168,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,10.5,10.5,bovada,0.3115,-185,140,0.6091,-0.2975,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,hardrockbet_az,0.1933,-120,-110,0.5101,-0.3168,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,hardrockbet,0.1933,-120,-110,0.5101,-0.3168,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,hardrockbet_fl,0.1933,-120,-110,0.5101,-0.3168,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,rebet,0.1933,-113,-113,0.5,-0.3067,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,betparx,0.1933,-115,-115,0.5,-0.3067,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,fliff,0.1933,-125,-115,0.5095,-0.3162,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,10.5,10.5,espnbet,0.3115,-170,130,0.5915,-0.28,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,11.5,11.5,espnbet,0.1933,-105,-125,0.4797,-0.2864,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,9.5652,9.5652,10,10,0.0018,12.5,12.5,espnbet,0.1204,135,-180,0.3983,-0.2779,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,2.8777,2.8777,3,3,0.0121,3.5,3.5,williamhill_us,0.3077,110,-145,0.4459,-0.1382,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,2.8777,2.8777,3,3,0.0121,3.5,3.5,bovada,0.3077,110,-145,0.4459,-0.1382,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,2.8777,2.8777,3,3,0.0121,2.5,2.5,bovada,0.6118,-220,165,0.6456,-0.0338,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,2.8777,2.8777,3,3,0.0121,3.5,3.5,betmgm,0.3077,105,-140,0.4554,-0.1477,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,2.8777,2.8777,3,3,0.0121,3.5,3.5,betrivers,0.3077,107,-148,0.4474,-0.1397,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Victor Wembanyama,56677822,SAS,NYK,21716138,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0583,36.2251,0.05,2.8777,2.8777,3,3,0.0121,3.5,3.5,draftkings,0.3077,112,-147,0.4421,-0.1344,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/market_comparison_csv_parts/market_comparison_part_005.csv`

- bytes: `67,850`
- rows: `62`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Dylan Harper,1057262518,SAS,NYK,21716138,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,18.3992,18.3992,18,17,0.0001,21.5,21.5,bovada,0.2961,-120,-110,0.5101,-0.2141,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,18.3992,18.3992,18,17,0.0001,20.5,20.5,bovada,0.3472,-150,115,0.5633,-0.2161,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,18.3992,18.3992,18,17,0.0001,21.5,21.5,draftkings,0.2961,-116,-113,0.5031,-0.207,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,18.3992,18.3992,18,17,0.0001,21.5,21.5,hardrockbet_az,0.2961,-115,-115,0.5,-0.2039,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,18.3992,18.3992,18,17,0.0001,21.5,21.5,hardrockbet,0.2961,-115,-115,0.5,-0.2039,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,18.3992,18.3992,18,17,0.0001,21.5,21.5,hardrockbet_fl,0.2961,-115,-115,0.5,-0.2039,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,18.3992,18.3992,18,17,0.0001,21.5,21.5,espnbet,0.2961,-105,-125,0.4797,-0.1836,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,18.3992,18.3992,18,17,0.0001,21.5,21.5,fliff,0.2961,-115,-125,0.4905,-0.1945,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,12.5,12.5,fanduel,0.0351,450,-800,0.1698,-0.1347,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,11.5,11.5,fanduel,0.0748,290,-440,0.2394,-0.1645,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,10.5,10.5,fanduel,0.1464,194,-270,0.3179,-0.1716,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,9.5,9.5,fanduel,0.2588,124,-166,0.417,-0.1583,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,8.5,8.5,fanduel,0.4063,-136,102,0.5379,-0.1316,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,7.5,7.5,fanduel,0.5717,-240,174,0.6592,-0.0875,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,6.5,6.5,fanduel,0.7281,-440,290,0.7606,-0.0325,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,5.5,5.5,fanduel,0.8518,-900,490,0.8415,0.0103,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,8.5,8.5,fanduel,0.4063,-132,104,0.5372,-0.1309,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,9.5,9.5,draftkings,0.2588,103,-136,0.4609,-0.2021,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,7.5,7.5,bovada,0.5717,-250,185,0.6706,-0.0989,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,9.5,9.5,bovada,0.2588,105,-135,0.4592,-0.2004,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,8.5,8.5,bovada,0.4063,-150,115,0.5633,-0.157,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,9.5,9.5,hardrockbet_az,0.2588,105,-140,0.4554,-0.1966,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,9.5,9.5,hardrockbet,0.2588,105,-140,0.4554,-0.1966,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,9.5,9.5,hardrockbet_fl,0.2588,105,-140,0.4554,-0.1966,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,8.5,8.5,fliff,0.4063,-150,100,0.5455,-0.1392,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,7.9889,7.9889,8,8,0.0005,8.5,8.5,espnbet,0.4063,-145,110,0.5541,-0.1479,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pra,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,21.1212,21.1212,21,20,0.0,32.5,32.5,fanduel,0.046,470,-850,0.1639,-0.1179,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pra,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,21.1212,21.1212,21,20,0.0,31.5,31.5,fanduel,0.0621,390,-650,0.1906,-0.1285,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pra,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,21.1212,21.1212,21,20,0.0,30.5,30.5,fanduel,0.0819,320,-490,0.2228,-0.1409,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z
Dylan Harper,1057262518,SAS,NYK,21716138,pra,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,24.9137,26.5139,0.05,21.1212,21.1212,21,20,0.0,29.5,29.5,fanduel,0.1056,270,-400,0.2525,-0.1469,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-06-13T22:59:51Z

```

---

## `derek_game_snapshots/21716138/morning/outcome_level_probabilities.csv`

- bytes: `524,114`
- rows: `6,294`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,21716138,pts,starter,0,0.0007,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,1,0.0009,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,2,0.0011,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,3,0.0018,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,4,0.0023,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,5,0.0059,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,6,0.0073,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,7,0.0138,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,8,0.0246,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,9,0.0305,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,10,0.0332,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,11,0.0404,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,12,0.0589,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,13,0.0608,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,14,0.0805,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,15,0.0706,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,16,0.0963,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,17,0.0984,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,18,0.0595,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,19,0.0542,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,20,0.0483,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,21,0.0502,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,22,0.0423,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,23,0.0227,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,24,0.0245,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,25,0.0161,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,26,0.007,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,27,0.0103,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,28,0.0088,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,29,0.0124,fallback_used,projected

```

---

## `derek_game_snapshots/21716138/morning/outcome_level_probabilities.parquet`

- bytes: `72,158`
- rows: `6,294`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,21716138,pts,starter,0,0.0006657112896958958,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,1,0.0009239400548960338,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,2,0.0011309501868589469,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,3,0.0018122514524228227,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,4,0.0022878987546347054,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,5,0.0059176394905488434,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,6,0.007303223770885862,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,7,0.013828015198371402,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,8,0.024582803059193206,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,9,0.030547177761280034,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,10,0.033183454103475236,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,11,0.04037062845868582,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,12,0.05890069167742618,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,13,0.06082467177962807,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,14,0.08045752549011302,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,15,0.07055625285620137,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,16,0.0962638791129092,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,17,0.09839772396643978,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,18,0.05947261457793987,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,19,0.05415991219393495,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,20,0.048299172685498326,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,21,0.05015178625773882,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,22,0.04226482510648301,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,23,0.022668595900898154,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,24,0.02452026424747177,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,25,0.01607409459779409,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,26,0.007028625964464484,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,27,0.01031325176746259,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,28,0.008844728501762216,fallback_used,projected
OG Anunoby,18,21716138,pts,starter,29,0.012352880324289082,fallback_used,projected

```

---

## `derek_game_snapshots/21716138/morning/prop_summary.csv`

- bytes: `27,355`
- rows: `192`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,NYK,SAS,21716138,pts,starter,16.4754,17.5,17.5,betmgm,0.372,-105.0,-125.0,0.4797,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,reb,starter,5.6455,5.5,5.5,betmgm,0.5592,115.0,-150.0,0.4367,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,ast,starter,1.9687,1.5,1.5,betmgm,0.6536,-110.0,-120.0,0.4899,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,fg3m,starter,1.8093,2.5,2.5,betmgm,0.3269,110.0,-150.0,0.4425,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,tov,starter,1.2158,,,,,,,,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,stl,starter,0.7894,1.5,1.5,betparx,0.1766,128.0,-167.0,0.4122,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,blk,starter,0.3783,0.5,0.5,betmgm,0.2371,-175.0,130.0,0.5941,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,stocks,starter,1.1324,2.5,2.5,betparx,0.1477,133.0,-180.0,0.4003,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,pa,starter,18.4441,19.5,19.5,betmgm,0.3841,-120.0,-110.0,0.5101,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,pr,starter,22.1209,23.5,23.5,betmgm,0.3716,-115.0,-115.0,0.5,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,ra,starter,7.6142,6.5,6.5,betmgm,0.716,-130.0,100.0,0.5306,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,pra,starter,24.0896,24.5,24.5,betparx,0.4462,-125.0,-106.0,0.5192,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,pts,starter,12.7882,11.5,11.5,betmgm,0.5868,-105.0,-125.0,0.4797,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,reb,starter,3.8699,3.5,3.5,betmgm,0.5897,100.0,-135.0,0.4653,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,ast,starter,2.7252,2.5,2.5,betmgm,0.5408,-140.0,105.0,0.5446,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,fg3m,starter,1.1519,1.5,1.5,betmgm,0.3588,140.0,-190.0,0.3887,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,tov,starter,1.2121,,,,,,,,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,stl,starter,0.6345,0.5,0.5,betparx,0.4672,-245.0,175.0,0.6613,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,blk,starter,0.323,0.5,0.5,betmgm,0.2539,135.0,-190.0,0.3938,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,stocks,starter,0.9671,1.5,1.5,betparx,0.2466,-110.0,-121.0,0.4889,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,pa,starter,15.5134,13.5,13.5,betmgm,0.639,-125.0,-105.0,0.5203,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,pr,starter,16.6581,14.5,14.5,betmgm,0.6464,-115.0,-118.0,0.497,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,ra,starter,6.5951,5.5,5.5,betmgm,0.7118,-155.0,120.0,0.5721,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,pra,starter,19.3832,17.5,17.5,betmgm,0.623,-110.0,-120.0,0.4899,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,pts,starter,28.162,28.5,28.5,betmgm,0.4732,-120.0,-111.0,0.509,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,reb,starter,4.0839,3.5,3.5,betmgm,0.6874,105.0,-145.0,0.4518,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,ast,starter,6.1574,6.5,6.5,betmgm,0.4479,120.0,-160.0,0.4248,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,fg3m,starter,2.3336,2.5,2.5,betmgm,0.402,100.0,-135.0,0.4653,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,tov,starter,1.5667,,,,,,,,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,stl,starter,0.7885,0.5,0.5,betparx,0.4881,-220.0,160.0,0.6413,fallback_used,projected

```

---

## `derek_game_snapshots/21716138/morning/prop_summary.parquet`

- bytes: `17,705`
- rows: `192`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
OG Anunoby,18,NYK,SAS,21716138,pts,starter,16.47540383850598,17.5,17.5,betmgm,0.37204556153633334,-105.0,-125.0,0.4796954314720812,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,reb,starter,5.645498193864341,5.5,5.5,betmgm,0.5592444699224676,115.0,-150.0,0.43668122270742354,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,ast,starter,1.968714273662721,1.5,1.5,betmgm,0.653624338604333,-110.0,-120.0,0.48987854251012153,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,fg3m,starter,1.809290866936096,2.5,2.5,betmgm,0.32688759554912034,110.0,-150.0,0.4424778761061947,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,tov,starter,1.2157660999389406,,,,,,,,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,stl,starter,0.789351087836143,1.5,1.5,betparx,0.17655845796623654,128.0,-167.0,0.4121896998888477,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,blk,starter,0.37829605861921034,0.5,0.5,betmgm,0.23708955717737007,-175.0,130.0,0.5940959409594095,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,stocks,starter,1.132352543305043,2.5,2.5,betparx,0.14773024508882052,133.0,-180.0,0.40034315127251924,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,pa,starter,18.444118112168706,19.5,19.5,betmgm,0.3840549703566131,-120.0,-110.0,0.5101214574898786,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,pr,starter,22.120902032370314,23.5,23.5,betmgm,0.3716460159573306,-115.0,-115.0,0.5,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,ra,starter,7.614212467527062,6.5,6.5,betmgm,0.7159784895355367,-130.0,100.0,0.5306122448979592,fallback_used,projected
OG Anunoby,18,NYK,SAS,21716138,pra,starter,24.08961630603302,24.5,24.5,betparx,0.4461640733841429,-125.0,-106.0,0.5191532258064516,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,pts,starter,12.788183187260636,11.5,11.5,betmgm,0.5868062891462038,-105.0,-125.0,0.4796954314720812,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,reb,starter,3.869874275309511,3.5,3.5,betmgm,0.5897229957831313,100.0,-135.0,0.4653465346534653,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,ast,starter,2.7251849290785386,2.5,2.5,betmgm,0.5407719605801181,-140.0,105.0,0.5445920303605313,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,fg3m,starter,1.1518630615235272,1.5,1.5,betmgm,0.3587978092804277,140.0,-190.0,0.38873994638069703,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,tov,starter,1.2120712888027663,,,,,,,,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,stl,starter,0.6345109263464037,0.5,0.5,betparx,0.4672144124372476,-245.0,175.0,0.6613496932515337,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,blk,starter,0.3229656110103885,0.5,0.5,betmgm,0.2538713823921189,135.0,-190.0,0.3937542430414121,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,stocks,starter,0.9670932531496343,1.5,1.5,betparx,0.24661937348698484,-110.0,-121.0,0.48893805309734506,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,pa,starter,15.513368116339176,13.5,13.5,betmgm,0.6390114600307079,-125.0,-105.0,0.5203045685279188,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,pr,starter,16.658057462570135,14.5,14.5,betmgm,0.6463712402488537,-115.0,-118.0,0.4970261697065821,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,ra,starter,6.595059204388044,5.5,5.5,betmgm,0.7117979333928561,-155.0,120.0,0.5721476510067114,fallback_used,projected
Mikal Bridges,61,NYK,SAS,21716138,pra,starter,19.383242391648626,17.5,17.5,betmgm,0.622959060819506,-110.0,-120.0,0.48987854251012153,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,pts,starter,28.162028295261262,28.5,28.5,betmgm,0.4731755436740117,-120.0,-111.0,0.5090470446320868,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,reb,starter,4.0839231287613496,3.5,3.5,betmgm,0.6874113500581212,105.0,-145.0,0.45182111572153066,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,ast,starter,6.157415571801393,6.5,6.5,betmgm,0.44792547471230876,120.0,-160.0,0.4248366013071895,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,fg3m,starter,2.333560242774647,2.5,2.5,betmgm,0.401951790723046,100.0,-135.0,0.4653465346534653,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,tov,starter,1.5666563627425727,,,,,,,,fallback_used,projected
Jalen Brunson,73,NYK,SAS,21716138,stl,starter,0.7884867653535839,0.5,0.5,betparx,0.48807049199856695,-220.0,160.0,0.641255605381166,fallback_used,projected

```

---

## `derek_game_snapshots/21716138/t_minus_25/after_game_scoring.csv`

- bytes: `2,618`
- rows: `42`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,stat,line
De'Aaron Fox,161,reb,3.5
De'Aaron Fox,161,ast,6.5
De'Aaron Fox,161,stl,1.5
Jose Alvarado,17896097,fg3m,0.5
Jose Alvarado,17896097,stl,0.5
Landry Shamet,414,fg3m,1.5
Landry Shamet,414,stl,0.5
Miles McBride,17896033,fg3m,0.5
Jalen Brunson,73,pts,28.5
Jalen Brunson,73,reb,3.5
Jalen Brunson,73,fg3m,2.5
Josh Hart,202,reb,8.5
Josh Hart,202,ast,4.5
Josh Hart,202,fg3m,1.5
Josh Hart,202,stl,1.5
Stephon Castle,1028025261,pts,16.5
Stephon Castle,1028025261,ast,6.5
Stephon Castle,1028025261,stl,0.5
Devin Vassell,3547246,pts,13.5
Devin Vassell,3547246,fg3m,2.5
Mitchell Robinson,399,stl,0.5
Mitchell Robinson,399,blk,0.5
OG Anunoby,18,pts,17.5
OG Anunoby,18,fg3m,2.5
OG Anunoby,18,stl,1.5
Dylan Harper,1057262518,pts,15.5
Dylan Harper,1057262518,reb,5.5
Dylan Harper,1057262518,ast,3.5
Dylan Harper,1057262518,blk,0.5
Keldon Johnson,666682,reb,2.5

```

---

## `derek_game_snapshots/21716138/t_minus_25/contextual_feature_audit.csv`

- bytes: `3,568`
- rows: `15`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716138
Jose Alvarado,17896097,NYK,21716138
Landry Shamet,414,NYK,21716138
Miles McBride,17896033,NYK,21716138
Jalen Brunson,73,NYK,21716138
Josh Hart,202,NYK,21716138
Stephon Castle,1028025261,SAS,21716138
Devin Vassell,3547246,SAS,21716138
Mitchell Robinson,399,NYK,21716138
OG Anunoby,18,NYK,21716138
Dylan Harper,1057262518,SAS,21716138
Keldon Johnson,666682,SAS,21716138
Mikal Bridges,61,NYK,21716138
Victor Wembanyama,56677822,SAS,21716138
Karl-Anthony Towns,447,NYK,21716138

```

---

## `derek_game_snapshots/21716138/t_minus_25/contextual_feature_audit.parquet`

- bytes: `29,845`
- rows: `15`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716138
Jose Alvarado,17896097,NYK,21716138
Landry Shamet,414,NYK,21716138
Miles McBride,17896033,NYK,21716138
Jalen Brunson,73,NYK,21716138
Josh Hart,202,NYK,21716138
Stephon Castle,1028025261,SAS,21716138
Devin Vassell,3547246,SAS,21716138
Mitchell Robinson,399,NYK,21716138
OG Anunoby,18,NYK,21716138
Dylan Harper,1057262518,SAS,21716138
Keldon Johnson,666682,SAS,21716138
Mikal Bridges,61,NYK,21716138
Victor Wembanyama,56677822,SAS,21716138
Karl-Anthony Towns,447,NYK,21716138

```

---

## `derek_game_snapshots/21716138/t_minus_25/derek_live_predictions.parquet`

- bytes: `40,086`
- rows: `42`
- columns: `47`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1529
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0671
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1296
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.0838
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.2024
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,0.1579
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0953
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2725
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,28.5,-0.0878
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1325
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0842
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.5,-0.1251
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,-0.1057
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1338
Stephon Castle,1028025261,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,-0.0409
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1623
Stephon Castle,1028025261,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.0827
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.1818
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1709
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0845
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.1258
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.164
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1336
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1665
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,15.5,-0.2194
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1825
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.0958

```

---

## `derek_game_snapshots/21716138/t_minus_25/full_pmf_wide.csv`

- bytes: `47,201`
- rows: `42`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1529
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0671
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1296
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.0838
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.2024
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,0.1579
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0953
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2725
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,28.5,-0.0878
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1325
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0842
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.5,-0.1251
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,-0.1057
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1338
Stephon Castle,1028025261,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,-0.0409
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1623
Stephon Castle,1028025261,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.0827
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.1818
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1709
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0845
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.1258
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.164
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1336
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1665
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,15.5,-0.2194
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1825
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.0958

```

---

## `derek_game_snapshots/21716138/t_minus_25/full_pmf_wide.parquet`

- bytes: `73,689`
- rows: `42`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1529
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0671
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1296
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.0838
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.2024
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,0.1579
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0953
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2725
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,28.5,-0.0878
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.1325
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.0842
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,8.5,-0.1251
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,-0.1057
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1338
Stephon Castle,1028025261,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,-0.0409
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1623
Stephon Castle,1028025261,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,0.0827
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.1818
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1709
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,-0.0845
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.1258
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.5,-0.164
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1336
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1665
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,15.5,-0.2194
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.1825
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5,-0.0958

```

---

## `derek_game_snapshots/21716138/t_minus_25/game_context.csv`

- bytes: `608`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,NYK,21716138
Jose Alvarado,17896097,NYK,SAS,21716138
Landry Shamet,414,NYK,SAS,21716138
Miles McBride,17896033,NYK,SAS,21716138
Jalen Brunson,73,NYK,SAS,21716138
Josh Hart,202,NYK,SAS,21716138
Stephon Castle,1028025261,SAS,NYK,21716138
Devin Vassell,3547246,SAS,NYK,21716138
Mitchell Robinson,399,NYK,SAS,21716138
OG Anunoby,18,NYK,SAS,21716138
Dylan Harper,1057262518,SAS,NYK,21716138
Keldon Johnson,666682,SAS,NYK,21716138
Mikal Bridges,61,NYK,SAS,21716138
Victor Wembanyama,56677822,SAS,NYK,21716138
Karl-Anthony Towns,447,NYK,SAS,21716138

```

---

## `derek_game_snapshots/21716138/t_minus_25/game_context.parquet`

- bytes: `3,640`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,NYK,21716138
Jose Alvarado,17896097,NYK,SAS,21716138
Landry Shamet,414,NYK,SAS,21716138
Miles McBride,17896033,NYK,SAS,21716138
Jalen Brunson,73,NYK,SAS,21716138
Josh Hart,202,NYK,SAS,21716138
Stephon Castle,1028025261,SAS,NYK,21716138
Devin Vassell,3547246,SAS,NYK,21716138
Mitchell Robinson,399,NYK,SAS,21716138
OG Anunoby,18,NYK,SAS,21716138
Dylan Harper,1057262518,SAS,NYK,21716138
Keldon Johnson,666682,SAS,NYK,21716138
Mikal Bridges,61,NYK,SAS,21716138
Victor Wembanyama,56677822,SAS,NYK,21716138
Karl-Anthony Towns,447,NYK,SAS,21716138

```

---

## `derek_game_snapshots/21716138/t_minus_25/injury_availability_context.csv`

- bytes: `597`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716138
Jose Alvarado,17896097,NYK,21716138
Landry Shamet,414,NYK,21716138
Miles McBride,17896033,NYK,21716138
Jalen Brunson,73,NYK,21716138
Josh Hart,202,NYK,21716138
Stephon Castle,1028025261,SAS,21716138
Devin Vassell,3547246,SAS,21716138
Mitchell Robinson,399,NYK,21716138
OG Anunoby,18,NYK,21716138
Dylan Harper,1057262518,SAS,21716138
Keldon Johnson,666682,SAS,21716138
Mikal Bridges,61,NYK,21716138
Victor Wembanyama,56677822,SAS,21716138
Karl-Anthony Towns,447,NYK,21716138

```

---

## `derek_game_snapshots/21716138/t_minus_25/injury_availability_context.parquet`

- bytes: `3,842`
- rows: `15`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21716138
Jose Alvarado,17896097,NYK,21716138
Landry Shamet,414,NYK,21716138
Miles McBride,17896033,NYK,21716138
Jalen Brunson,73,NYK,21716138
Josh Hart,202,NYK,21716138
Stephon Castle,1028025261,SAS,21716138
Devin Vassell,3547246,SAS,21716138
Mitchell Robinson,399,NYK,21716138
OG Anunoby,18,NYK,21716138
Dylan Harper,1057262518,SAS,21716138
Keldon Johnson,666682,SAS,21716138
Mikal Bridges,61,NYK,21716138
Victor Wembanyama,56677822,SAS,21716138
Karl-Anthony Towns,447,NYK,21716138

```

---

## `derek_game_snapshots/21716138/t_minus_25/lineup_context.csv`

- bytes: `1,492`
- rows: `15`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21716138,reb
Jose Alvarado,17896097,NYK,21716138,fg3m
Landry Shamet,414,NYK,21716138,fg3m
Miles McBride,17896033,NYK,21716138,fg3m
Jalen Brunson,73,NYK,21716138,pts
Josh Hart,202,NYK,21716138,reb
Stephon Castle,1028025261,SAS,21716138,pts
Devin Vassell,3547246,SAS,21716138,pts
Mitchell Robinson,399,NYK,21716138,stl
OG Anunoby,18,NYK,21716138,pts
Dylan Harper,1057262518,SAS,21716138,pts
Keldon Johnson,666682,SAS,21716138,reb
Mikal Bridges,61,NYK,21716138,ast
Victor Wembanyama,56677822,SAS,21716138,pts
Karl-Anthony Towns,447,NYK,21716138,pts

```

---

## `derek_game_snapshots/21716138/t_minus_25/lineup_context.parquet`

- bytes: `8,426`
- rows: `15`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21716138,reb
Jose Alvarado,17896097,NYK,21716138,fg3m
Landry Shamet,414,NYK,21716138,fg3m
Miles McBride,17896033,NYK,21716138,fg3m
Jalen Brunson,73,NYK,21716138,pts
Josh Hart,202,NYK,21716138,reb
Stephon Castle,1028025261,SAS,21716138,pts
Devin Vassell,3547246,SAS,21716138,pts
Mitchell Robinson,399,NYK,21716138,stl
OG Anunoby,18,NYK,21716138,pts
Dylan Harper,1057262518,SAS,21716138,pts
Keldon Johnson,666682,SAS,21716138,reb
Mikal Bridges,61,NYK,21716138,ast
Victor Wembanyama,56677822,SAS,21716138,pts
Karl-Anthony Towns,447,NYK,21716138,pts

```

---

## `derek_game_snapshots/21716138/t_minus_25/market_comparison.csv`

- bytes: `60,668`
- rows: `42`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.414314314314315,0.0587,3.5,0.1529
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.564141110442976,0.0359,6.5,-0.0671
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0423957604239575,0.3686,1.5,-0.1296
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.9506,0.3848,0.5,0.0838
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.2756,0.7813,0.5,-0.2024
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.0799079907990805,0.0889,1.5,0.1579
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.4734,0.643,0.5,-0.0953
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4857,0.2101,0.5,0.2725
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,25.96763168476077,0.0044,28.5,-0.0878
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.864991993594876,0.065,3.5,0.1325
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.108889111088891,0.1055,2.5,-0.0842
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.418252855139252,0.0188,8.5,-0.1251
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.005607850991389,0.0576,4.5,-0.1057
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.8152,0.1498,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.9629962996299628,0.4346,1.5,-0.1338
Stephon Castle,1028025261,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.757423756019262,0.0097,16.5,-0.0409
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.09325853951718,0.043,6.5,-0.1623
Stephon Castle,1028025261,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.14021402140214,0.2832,0.5,0.0827
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.081344032096286,0.0223,13.5,-0.1818
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.9956995699569955,0.1017,2.5,-0.1709
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.4046,0.6776,0.5,-0.0845
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.8737126287371264,0.3996,0.5,0.1258
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.37922729553437,0.0087,17.5,-0.164
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.0325,0.0965,2.5,-0.1336
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.9653000000000002,0.3989,1.5,-0.1665
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,11.781905813836731,0.0186,15.5,-0.2194
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.7855854049719335,0.0443,5.5,-0.1825
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.4981483335001498,0.1698,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.19001900190019,0.8336,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5029556156697725,0.1887,2.5,-0.0958

```

---

## `derek_game_snapshots/21716138/t_minus_25/market_comparison.parquet`

- bytes: `88,877`
- rows: `42`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.414314314314315,0.0587,3.5,0.1529
De'Aaron Fox,161,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.564141110442976,0.0359,6.5,-0.0671
De'Aaron Fox,161,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0423957604239575,0.3686,1.5,-0.1296
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.9506,0.3848,0.5,0.0838
Jose Alvarado,17896097,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.2756,0.7813,0.5,-0.2024
Landry Shamet,414,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.0799079907990805,0.0889,1.5,0.1579
Landry Shamet,414,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.47340000000000004,0.643,0.5,-0.0953
Miles McBride,17896033,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.4857,0.2101,0.5,0.2725
Jalen Brunson,73,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,25.96763168476077,0.0044,28.5,-0.0878
Jalen Brunson,73,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.8649919935948756,0.065,3.5,0.1325
Jalen Brunson,73,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.108889111088891,0.1055,2.5,-0.0842
Josh Hart,202,NYK,SAS,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.418252855139252,0.0188,8.5,-0.1251
Josh Hart,202,NYK,SAS,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.005607850991389,0.0576,4.5,-0.1057
Josh Hart,202,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.8151999999999997,0.1498,1.5,0.1251
Josh Hart,202,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.9629962996299629,0.4346,1.5,-0.1338
Stephon Castle,1028025261,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.757423756019262,0.0097,16.5,-0.0409
Stephon Castle,1028025261,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.09325853951718,0.043,6.5,-0.1623
Stephon Castle,1028025261,SAS,NYK,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.1402140214021401,0.2832,0.5,0.0827
Devin Vassell,3547246,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,11.081344032096286,0.0223,13.5,-0.1818
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.9956995699569955,0.1017,2.5,-0.1709
Mitchell Robinson,399,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.40460000000000007,0.6776,0.5,-0.0845
Mitchell Robinson,399,NYK,SAS,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.8737126287371264,0.3996,0.5,0.1258
OG Anunoby,18,NYK,SAS,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.37922729553437,0.0087,17.5,-0.164
OG Anunoby,18,NYK,SAS,21716138,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.0325,0.0965,2.5,-0.1336
OG Anunoby,18,NYK,SAS,21716138,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.9653000000000002,0.3989,1.5,-0.1665
Dylan Harper,1057262518,SAS,NYK,21716138,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,11.781905813836731,0.0186,15.5,-0.2194
Dylan Harper,1057262518,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.7855854049719335,0.0443,5.5,-0.1825
Dylan Harper,1057262518,SAS,NYK,21716138,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.4981483335001498,0.1698,3.5,-0.1605
Dylan Harper,1057262518,SAS,NYK,21716138,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.19001900190019,0.8336,0.5,-0.1055
Keldon Johnson,666682,SAS,NYK,21716138,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,2.5029556156697725,0.1887,2.5,-0.0958

```

---

## `derek_game_snapshots/21716138/t_minus_25/outcome_level_probabilities.csv`

- bytes: `113,428`
- rows: `596`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21716138,reb,0,0.0587587587587587,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,1,0.0793793793793793,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,2,0.1091091091091091,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,3,0.141041041041041,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,4,0.1291291291291291,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,5,0.1698698698698698,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,6,0.1108108108108108,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,7,0.0824824824824824,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,8,0.054054054054054,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,9,0.0286286286286286,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,10,0.0184184184184184,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,11,0.0124124124124124,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,12,0.0031031031031031,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,13,0.0018018018018018,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,14,0.001001001001001,3.5,t_minus_25
De'Aaron Fox,161,21716138,ast,0,0.035979154139106,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,1,0.0518139907797153,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,2,0.0579274403688113,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,3,0.0995189416716777,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,4,0.1209661254760473,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,5,0.1426137502505512,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,6,0.1155542192824213,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,7,0.132992583684105,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,8,0.0937061535377831,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,9,0.0609340549208258,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,10,0.0358789336540388,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,11,0.0254560032070555,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,12,0.0138304269392663,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,13,0.007516536380036,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,14,0.0035077169773501,6.5,t_minus_25

```

---

## `derek_game_snapshots/21716138/t_minus_25/outcome_level_probabilities.parquet`

- bytes: `19,416`
- rows: `596`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21716138,reb,0,0.05875875875875876,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,1,0.07937937937937938,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,2,0.1091091091091091,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,3,0.14104104104104104,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,4,0.12912912912912913,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,5,0.16986986986986985,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,6,0.11081081081081082,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,7,0.08248248248248248,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,8,0.05405405405405405,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,9,0.028628628628628628,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,10,0.018418418418418417,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,11,0.012412412412412413,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,12,0.003103103103103103,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,13,0.0018018018018018018,3.5,t_minus_25
De'Aaron Fox,161,21716138,reb,14,0.001001001001001001,3.5,t_minus_25
De'Aaron Fox,161,21716138,ast,0,0.03597915413910604,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,1,0.05181399077971538,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,2,0.05792744036881139,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,3,0.0995189416716777,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,4,0.12096612547604732,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,5,0.14261375025055123,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,6,0.11555421928242134,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,7,0.13299258368410505,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,8,0.09370615353778314,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,9,0.06093405492082582,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,10,0.03587893365403889,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,11,0.025456003207055523,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,12,0.013830426939266387,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,13,0.00751653638003608,6.5,t_minus_25
De'Aaron Fox,161,21716138,ast,14,0.003507716977350171,6.5,t_minus_25

```

---

## `derek_game_snapshots/21716138/t_minus_25/pmf_driver_decomposition.csv`

- bytes: `4,547`
- rows: `15`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21716138,reb,3.5
Jose Alvarado,17896097,NYK,21716138,fg3m,0.5
Landry Shamet,414,NYK,21716138,fg3m,1.5
Miles McBride,17896033,NYK,21716138,fg3m,0.5
Jalen Brunson,73,NYK,21716138,pts,28.5
Josh Hart,202,NYK,21716138,reb,8.5
Stephon Castle,1028025261,SAS,21716138,pts,16.5
Devin Vassell,3547246,SAS,21716138,pts,13.5
Mitchell Robinson,399,NYK,21716138,stl,0.5
OG Anunoby,18,NYK,21716138,pts,17.5
Dylan Harper,1057262518,SAS,21716138,pts,15.5
Keldon Johnson,666682,SAS,21716138,reb,2.5
Mikal Bridges,61,NYK,21716138,ast,2.5
Victor Wembanyama,56677822,SAS,21716138,pts,28.5
Karl-Anthony Towns,447,NYK,21716138,pts,16.5

```

---

## `derek_game_snapshots/21716138/t_minus_25/pmf_driver_decomposition.parquet`

- bytes: `14,457`
- rows: `15`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21716138,reb,3.5
Jose Alvarado,17896097,NYK,21716138,fg3m,0.5
Landry Shamet,414,NYK,21716138,fg3m,1.5
Miles McBride,17896033,NYK,21716138,fg3m,0.5
Jalen Brunson,73,NYK,21716138,pts,28.5
Josh Hart,202,NYK,21716138,reb,8.5
Stephon Castle,1028025261,SAS,21716138,pts,16.5
Devin Vassell,3547246,SAS,21716138,pts,13.5
Mitchell Robinson,399,NYK,21716138,stl,0.5
OG Anunoby,18,NYK,21716138,pts,17.5
Dylan Harper,1057262518,SAS,21716138,pts,15.5
Keldon Johnson,666682,SAS,21716138,reb,2.5
Mikal Bridges,61,NYK,21716138,ast,2.5
Victor Wembanyama,56677822,SAS,21716138,pts,28.5
Karl-Anthony Towns,447,NYK,21716138,pts,16.5

```

---

## `derek_game_snapshots/21716138/t_minus_25/prediction_input_audit.csv`

- bytes: `2,755`
- rows: `42`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716138,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716138,ast,6.5
De'Aaron Fox,161,SAS,NYK,21716138,stl,1.5
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,0.5
Jose Alvarado,17896097,NYK,SAS,21716138,stl,0.5
Landry Shamet,414,NYK,SAS,21716138,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716138,stl,0.5
Miles McBride,17896033,NYK,SAS,21716138,fg3m,0.5
Jalen Brunson,73,NYK,SAS,21716138,pts,28.5
Jalen Brunson,73,NYK,SAS,21716138,reb,3.5
Jalen Brunson,73,NYK,SAS,21716138,fg3m,2.5
Josh Hart,202,NYK,SAS,21716138,reb,8.5
Josh Hart,202,NYK,SAS,21716138,ast,4.5
Josh Hart,202,NYK,SAS,21716138,fg3m,1.5
Josh Hart,202,NYK,SAS,21716138,stl,1.5
Stephon Castle,1028025261,SAS,NYK,21716138,pts,16.5
Stephon Castle,1028025261,SAS,NYK,21716138,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716138,stl,0.5
Devin Vassell,3547246,SAS,NYK,21716138,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,2.5
Mitchell Robinson,399,NYK,SAS,21716138,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716138,blk,0.5
OG Anunoby,18,NYK,SAS,21716138,pts,17.5
OG Anunoby,18,NYK,SAS,21716138,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716138,stl,1.5
Dylan Harper,1057262518,SAS,NYK,21716138,pts,15.5
Dylan Harper,1057262518,SAS,NYK,21716138,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716138,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716138,blk,0.5
Keldon Johnson,666682,SAS,NYK,21716138,reb,2.5

```

---

## `derek_game_snapshots/21716138/t_minus_25/prediction_input_audit.parquet`

- bytes: `5,426`
- rows: `42`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716138,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716138,ast,6.5
De'Aaron Fox,161,SAS,NYK,21716138,stl,1.5
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,0.5
Jose Alvarado,17896097,NYK,SAS,21716138,stl,0.5
Landry Shamet,414,NYK,SAS,21716138,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716138,stl,0.5
Miles McBride,17896033,NYK,SAS,21716138,fg3m,0.5
Jalen Brunson,73,NYK,SAS,21716138,pts,28.5
Jalen Brunson,73,NYK,SAS,21716138,reb,3.5
Jalen Brunson,73,NYK,SAS,21716138,fg3m,2.5
Josh Hart,202,NYK,SAS,21716138,reb,8.5
Josh Hart,202,NYK,SAS,21716138,ast,4.5
Josh Hart,202,NYK,SAS,21716138,fg3m,1.5
Josh Hart,202,NYK,SAS,21716138,stl,1.5
Stephon Castle,1028025261,SAS,NYK,21716138,pts,16.5
Stephon Castle,1028025261,SAS,NYK,21716138,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716138,stl,0.5
Devin Vassell,3547246,SAS,NYK,21716138,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,2.5
Mitchell Robinson,399,NYK,SAS,21716138,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716138,blk,0.5
OG Anunoby,18,NYK,SAS,21716138,pts,17.5
OG Anunoby,18,NYK,SAS,21716138,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716138,stl,1.5
Dylan Harper,1057262518,SAS,NYK,21716138,pts,15.5
Dylan Harper,1057262518,SAS,NYK,21716138,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716138,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716138,blk,0.5
Keldon Johnson,666682,SAS,NYK,21716138,reb,2.5

```

---

## `derek_game_snapshots/21716138/t_minus_25/prop_summary.csv`

- bytes: `1,987`
- rows: `42`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716138,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716138,ast,6.5
De'Aaron Fox,161,SAS,NYK,21716138,stl,1.5
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,0.5
Jose Alvarado,17896097,NYK,SAS,21716138,stl,0.5
Landry Shamet,414,NYK,SAS,21716138,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716138,stl,0.5
Miles McBride,17896033,NYK,SAS,21716138,fg3m,0.5
Jalen Brunson,73,NYK,SAS,21716138,pts,28.5
Jalen Brunson,73,NYK,SAS,21716138,reb,3.5
Jalen Brunson,73,NYK,SAS,21716138,fg3m,2.5
Josh Hart,202,NYK,SAS,21716138,reb,8.5
Josh Hart,202,NYK,SAS,21716138,ast,4.5
Josh Hart,202,NYK,SAS,21716138,fg3m,1.5
Josh Hart,202,NYK,SAS,21716138,stl,1.5
Stephon Castle,1028025261,SAS,NYK,21716138,pts,16.5
Stephon Castle,1028025261,SAS,NYK,21716138,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716138,stl,0.5
Devin Vassell,3547246,SAS,NYK,21716138,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,2.5
Mitchell Robinson,399,NYK,SAS,21716138,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716138,blk,0.5
OG Anunoby,18,NYK,SAS,21716138,pts,17.5
OG Anunoby,18,NYK,SAS,21716138,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716138,stl,1.5
Dylan Harper,1057262518,SAS,NYK,21716138,pts,15.5
Dylan Harper,1057262518,SAS,NYK,21716138,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716138,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716138,blk,0.5
Keldon Johnson,666682,SAS,NYK,21716138,reb,2.5

```

---

## `derek_game_snapshots/21716138/t_minus_25/prop_summary.parquet`

- bytes: `4,835`
- rows: `42`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,NYK,21716138,reb,3.5
De'Aaron Fox,161,SAS,NYK,21716138,ast,6.5
De'Aaron Fox,161,SAS,NYK,21716138,stl,1.5
Jose Alvarado,17896097,NYK,SAS,21716138,fg3m,0.5
Jose Alvarado,17896097,NYK,SAS,21716138,stl,0.5
Landry Shamet,414,NYK,SAS,21716138,fg3m,1.5
Landry Shamet,414,NYK,SAS,21716138,stl,0.5
Miles McBride,17896033,NYK,SAS,21716138,fg3m,0.5
Jalen Brunson,73,NYK,SAS,21716138,pts,28.5
Jalen Brunson,73,NYK,SAS,21716138,reb,3.5
Jalen Brunson,73,NYK,SAS,21716138,fg3m,2.5
Josh Hart,202,NYK,SAS,21716138,reb,8.5
Josh Hart,202,NYK,SAS,21716138,ast,4.5
Josh Hart,202,NYK,SAS,21716138,fg3m,1.5
Josh Hart,202,NYK,SAS,21716138,stl,1.5
Stephon Castle,1028025261,SAS,NYK,21716138,pts,16.5
Stephon Castle,1028025261,SAS,NYK,21716138,ast,6.5
Stephon Castle,1028025261,SAS,NYK,21716138,stl,0.5
Devin Vassell,3547246,SAS,NYK,21716138,pts,13.5
Devin Vassell,3547246,SAS,NYK,21716138,fg3m,2.5
Mitchell Robinson,399,NYK,SAS,21716138,stl,0.5
Mitchell Robinson,399,NYK,SAS,21716138,blk,0.5
OG Anunoby,18,NYK,SAS,21716138,pts,17.5
OG Anunoby,18,NYK,SAS,21716138,fg3m,2.5
OG Anunoby,18,NYK,SAS,21716138,stl,1.5
Dylan Harper,1057262518,SAS,NYK,21716138,pts,15.5
Dylan Harper,1057262518,SAS,NYK,21716138,reb,5.5
Dylan Harper,1057262518,SAS,NYK,21716138,ast,3.5
Dylan Harper,1057262518,SAS,NYK,21716138,blk,0.5
Keldon Johnson,666682,SAS,NYK,21716138,reb,2.5

```

---

## `derek_game_snapshots/aggregate_snapshot_scoring.csv`

- bytes: `319`
- rows: `2`
- columns: `7`

Compact first 30 rows:

```csv
game_id,snapshot_type
21716138,current_live
21716138,t_minus_25

```
