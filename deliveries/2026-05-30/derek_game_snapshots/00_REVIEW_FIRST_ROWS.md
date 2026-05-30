# Reviewable Delivery Preview — 2026-05-30 — derek_game_snapshots

GitHub may refuse to render large CSV files. This file is intentionally small.

---

## `derek_game_snapshots/21713534/current_live/contextual_feature_audit.csv`

- bytes: `5,360`
- rows: `17`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
Isaiah Joe,3547272,OKC,21713534
Chet Holmgren,38017685,OKC,21713534
De'Aaron Fox,161,SAS,21713534
Jaylin Williams,38017706,OKC,21713534
Stephon Castle,1028025261,SAS,21713534
Luguentz Dort,666541,OKC,21713534
Shai Gilgeous-Alexander,175,OKC,21713534
Dylan Harper,1057262518,SAS,21713534
Keldon Johnson,666682,SAS,21713534
Victor Wembanyama,56677822,SAS,21713534
Cason Wallace,56677833,OKC,21713534
Isaiah Hartenstein,201,OKC,21713534
Alex Caruso,89,OKC,21713534
Kenrich Williams,480,OKC,21713534
Jared McCain,1028027372,OKC,21713534
Devin Vassell,3547246,SAS,21713534
Julian Champagnie,38017649,SAS,21713534

```

---

## `derek_game_snapshots/21713534/current_live/contextual_feature_audit.parquet`

- bytes: `34,457`
- rows: `17`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
Isaiah Joe,3547272,OKC,21713534
Chet Holmgren,38017685,OKC,21713534
De'Aaron Fox,161,SAS,21713534
Jaylin Williams,38017706,OKC,21713534
Stephon Castle,1028025261,SAS,21713534
Luguentz Dort,666541,OKC,21713534
Shai Gilgeous-Alexander,175,OKC,21713534
Dylan Harper,1057262518,SAS,21713534
Keldon Johnson,666682,SAS,21713534
Victor Wembanyama,56677822,SAS,21713534
Cason Wallace,56677833,OKC,21713534
Isaiah Hartenstein,201,OKC,21713534
Alex Caruso,89,OKC,21713534
Kenrich Williams,480,OKC,21713534
Jared McCain,1028027372,OKC,21713534
Devin Vassell,3547246,SAS,21713534
Julian Champagnie,38017649,SAS,21713534

```

---

## `derek_game_snapshots/21713534/current_live/derek_live_predictions.parquet`

- bytes: `44,956`
- rows: `41`
- columns: `47`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
Isaiah Joe,3547272,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2121
Chet Holmgren,38017685,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,13.5,-0.0407
Chet Holmgren,38017685,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.5,-0.0995
De'Aaron Fox,161,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,0.101
De'Aaron Fox,161,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,0.1139
Jaylin Williams,38017706,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.0597
Jaylin Williams,38017706,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1721
Stephon Castle,1028025261,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,0.0377
Stephon Castle,1028025261,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0697
Stephon Castle,1028025261,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,0.1259
Luguentz Dort,666541,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.1129
Luguentz Dort,666541,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1646
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,30.5,-0.2684
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.5,-0.05
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1447
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.0652
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.229
Dylan Harper,1057262518,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5,-0.0517
Dylan Harper,1057262518,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.074
Dylan Harper,1057262518,SAS,OKC,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.0898
Keldon Johnson,666682,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.2279
Victor Wembanyama,56677822,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,26.5,-0.1754
Victor Wembanyama,56677822,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,12.5,-0.1687
Victor Wembanyama,56677822,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1627
Victor Wembanyama,56677822,SAS,OKC,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1243
Cason Wallace,56677833,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,3.5,-0.1011
Cason Wallace,56677833,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5,-0.1441
Cason Wallace,56677833,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.166
Isaiah Hartenstein,201,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.5,-0.126
Isaiah Hartenstein,201,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1994

```

---

## `derek_game_snapshots/21713534/current_live/full_pmf_wide.csv`

- bytes: `46,581`
- rows: `41`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
Isaiah Joe,3547272,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2121
Chet Holmgren,38017685,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,13.5,-0.0407
Chet Holmgren,38017685,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.5,-0.0995
De'Aaron Fox,161,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,0.101
De'Aaron Fox,161,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,0.1139
Jaylin Williams,38017706,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.0597
Jaylin Williams,38017706,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1721
Stephon Castle,1028025261,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,0.0377
Stephon Castle,1028025261,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0697
Stephon Castle,1028025261,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,0.1259
Luguentz Dort,666541,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.1129
Luguentz Dort,666541,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1646
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,30.5,-0.2684
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.5,-0.05
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1447
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.0652
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.229
Dylan Harper,1057262518,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5,-0.0517
Dylan Harper,1057262518,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.074
Dylan Harper,1057262518,SAS,OKC,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.0898
Keldon Johnson,666682,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.2279
Victor Wembanyama,56677822,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,26.5,-0.1754
Victor Wembanyama,56677822,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,12.5,-0.1687
Victor Wembanyama,56677822,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1627
Victor Wembanyama,56677822,SAS,OKC,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1243
Cason Wallace,56677833,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,3.5,-0.1011
Cason Wallace,56677833,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5,-0.1441
Cason Wallace,56677833,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.166
Isaiah Hartenstein,201,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.5,-0.126
Isaiah Hartenstein,201,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1994

```

---

## `derek_game_snapshots/21713534/current_live/full_pmf_wide.parquet`

- bytes: `84,073`
- rows: `41`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
Isaiah Joe,3547272,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,0.5,0.2121
Chet Holmgren,38017685,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,13.5,-0.0407
Chet Holmgren,38017685,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.5,-0.0995
De'Aaron Fox,161,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,0.101
De'Aaron Fox,161,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,0.1139
Jaylin Williams,38017706,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.0597
Jaylin Williams,38017706,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1721
Stephon Castle,1028025261,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.5,0.0377
Stephon Castle,1028025261,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.0697
Stephon Castle,1028025261,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,0.1259
Luguentz Dort,666541,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.1129
Luguentz Dort,666541,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1646
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,30.5,-0.2684
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.5,-0.05
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1447
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.0652
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.5,-0.229
Dylan Harper,1057262518,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5,-0.0517
Dylan Harper,1057262518,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.074
Dylan Harper,1057262518,SAS,OKC,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.0898
Keldon Johnson,666682,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.2279
Victor Wembanyama,56677822,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,26.5,-0.1754
Victor Wembanyama,56677822,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,12.5,-0.1687
Victor Wembanyama,56677822,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1627
Victor Wembanyama,56677822,SAS,OKC,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,-0.1243
Cason Wallace,56677833,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,3.5,-0.1011
Cason Wallace,56677833,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5,-0.1441
Cason Wallace,56677833,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.166
Isaiah Hartenstein,201,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.5,-0.126
Isaiah Hartenstein,201,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.1994

```

---

## `derek_game_snapshots/21713534/current_live/game_context.csv`

- bytes: `720`
- rows: `17`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
Isaiah Joe,3547272,OKC,SAS,21713534
Chet Holmgren,38017685,OKC,SAS,21713534
De'Aaron Fox,161,SAS,OKC,21713534
Jaylin Williams,38017706,OKC,SAS,21713534
Stephon Castle,1028025261,SAS,OKC,21713534
Luguentz Dort,666541,OKC,SAS,21713534
Shai Gilgeous-Alexander,175,OKC,SAS,21713534
Dylan Harper,1057262518,SAS,OKC,21713534
Keldon Johnson,666682,SAS,OKC,21713534
Victor Wembanyama,56677822,SAS,OKC,21713534
Cason Wallace,56677833,OKC,SAS,21713534
Isaiah Hartenstein,201,OKC,SAS,21713534
Alex Caruso,89,OKC,SAS,21713534
Kenrich Williams,480,OKC,SAS,21713534
Jared McCain,1028027372,OKC,SAS,21713534
Devin Vassell,3547246,SAS,OKC,21713534
Julian Champagnie,38017649,SAS,OKC,21713534

```

---

## `derek_game_snapshots/21713534/current_live/game_context.parquet`

- bytes: `4,103`
- rows: `17`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
Isaiah Joe,3547272,OKC,SAS,21713534
Chet Holmgren,38017685,OKC,SAS,21713534
De'Aaron Fox,161,SAS,OKC,21713534
Jaylin Williams,38017706,OKC,SAS,21713534
Stephon Castle,1028025261,SAS,OKC,21713534
Luguentz Dort,666541,OKC,SAS,21713534
Shai Gilgeous-Alexander,175,OKC,SAS,21713534
Dylan Harper,1057262518,SAS,OKC,21713534
Keldon Johnson,666682,SAS,OKC,21713534
Victor Wembanyama,56677822,SAS,OKC,21713534
Cason Wallace,56677833,OKC,SAS,21713534
Isaiah Hartenstein,201,OKC,SAS,21713534
Alex Caruso,89,OKC,SAS,21713534
Kenrich Williams,480,OKC,SAS,21713534
Jared McCain,1028027372,OKC,SAS,21713534
Devin Vassell,3547246,SAS,OKC,21713534
Julian Champagnie,38017649,SAS,OKC,21713534

```

---

## `derek_game_snapshots/21713534/current_live/injury_availability_context.csv`

- bytes: `705`
- rows: `17`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
Isaiah Joe,3547272,OKC,21713534
Chet Holmgren,38017685,OKC,21713534
De'Aaron Fox,161,SAS,21713534
Jaylin Williams,38017706,OKC,21713534
Stephon Castle,1028025261,SAS,21713534
Luguentz Dort,666541,OKC,21713534
Shai Gilgeous-Alexander,175,OKC,21713534
Dylan Harper,1057262518,SAS,21713534
Keldon Johnson,666682,SAS,21713534
Victor Wembanyama,56677822,SAS,21713534
Cason Wallace,56677833,OKC,21713534
Isaiah Hartenstein,201,OKC,21713534
Alex Caruso,89,OKC,21713534
Kenrich Williams,480,OKC,21713534
Jared McCain,1028027372,OKC,21713534
Devin Vassell,3547246,SAS,21713534
Julian Champagnie,38017649,SAS,21713534

```

---

## `derek_game_snapshots/21713534/current_live/injury_availability_context.parquet`

- bytes: `4,355`
- rows: `17`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
Isaiah Joe,3547272,OKC,21713534
Chet Holmgren,38017685,OKC,21713534
De'Aaron Fox,161,SAS,21713534
Jaylin Williams,38017706,OKC,21713534
Stephon Castle,1028025261,SAS,21713534
Luguentz Dort,666541,OKC,21713534
Shai Gilgeous-Alexander,175,OKC,21713534
Dylan Harper,1057262518,SAS,21713534
Keldon Johnson,666682,SAS,21713534
Victor Wembanyama,56677822,SAS,21713534
Cason Wallace,56677833,OKC,21713534
Isaiah Hartenstein,201,OKC,21713534
Alex Caruso,89,OKC,21713534
Kenrich Williams,480,OKC,21713534
Jared McCain,1028027372,OKC,21713534
Devin Vassell,3547246,SAS,21713534
Julian Champagnie,38017649,SAS,21713534

```

---

## `derek_game_snapshots/21713534/current_live/lineup_context.csv`

- bytes: `1,857`
- rows: `17`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
Isaiah Joe,3547272,OKC,21713534,fg3m
Chet Holmgren,38017685,OKC,21713534,pts
De'Aaron Fox,161,SAS,21713534,pts
Jaylin Williams,38017706,OKC,21713534,fg3m
Stephon Castle,1028025261,SAS,21713534,pts
Luguentz Dort,666541,OKC,21713534,fg3m
Shai Gilgeous-Alexander,175,OKC,21713534,pts
Dylan Harper,1057262518,SAS,21713534,ast
Keldon Johnson,666682,SAS,21713534,fg3m
Victor Wembanyama,56677822,SAS,21713534,pts
Cason Wallace,56677833,OKC,21713534,reb
Isaiah Hartenstein,201,OKC,21713534,reb
Alex Caruso,89,OKC,21713534,pts
Kenrich Williams,480,OKC,21713534,fg3m
Jared McCain,1028027372,OKC,21713534,pts
Devin Vassell,3547246,SAS,21713534,pts
Julian Champagnie,38017649,SAS,21713534,blk

```

---

## `derek_game_snapshots/21713534/current_live/lineup_context.parquet`

- bytes: `9,584`
- rows: `17`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
Isaiah Joe,3547272,OKC,21713534,fg3m
Chet Holmgren,38017685,OKC,21713534,pts
De'Aaron Fox,161,SAS,21713534,pts
Jaylin Williams,38017706,OKC,21713534,fg3m
Stephon Castle,1028025261,SAS,21713534,pts
Luguentz Dort,666541,OKC,21713534,fg3m
Shai Gilgeous-Alexander,175,OKC,21713534,pts
Dylan Harper,1057262518,SAS,21713534,ast
Keldon Johnson,666682,SAS,21713534,fg3m
Victor Wembanyama,56677822,SAS,21713534,pts
Cason Wallace,56677833,OKC,21713534,reb
Isaiah Hartenstein,201,OKC,21713534,reb
Alex Caruso,89,OKC,21713534,pts
Kenrich Williams,480,OKC,21713534,fg3m
Jared McCain,1028027372,OKC,21713534,pts
Devin Vassell,3547246,SAS,21713534,pts
Julian Champagnie,38017649,SAS,21713534,blk

```

---

## `derek_game_snapshots/21713534/current_live/market_comparison.csv`

- bytes: `57,427`
- rows: `41`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
Isaiah Joe,3547272,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.116,0.2794,0.5,0.2121
Chet Holmgren,38017685,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.9276,0.0143,13.5,-0.0407
Chet Holmgren,38017685,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.9016,0.4949,1.5,-0.0995
De'Aaron Fox,161,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.7395,0.0129,13.5,0.101
De'Aaron Fox,161,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.8289,0.047,4.5,0.1139
Jaylin Williams,38017706,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.088,0.3161,1.5,-0.0597
Jaylin Williams,38017706,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.3303,0.7703,0.5,-0.1721
Stephon Castle,1028025261,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.2572,0.0119,16.5,0.0377
Stephon Castle,1028025261,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.392,0.0263,6.5,-0.0697
Stephon Castle,1028025261,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.8475,0.1672,1.5,0.1259
Luguentz Dort,666541,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.0197,0.329,1.5,-0.1129
Luguentz Dort,666541,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5649,0.6668,0.5,-0.1646
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,24.1919,0.0064,30.5,-0.2684
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.1334,0.0229,7.5,-0.05
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.1069,0.2757,1.5,-0.1447
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.3058,0.3063,1.5,-0.0652
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.4558,0.6641,0.5,-0.229
Dylan Harper,1057262518,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5436,0.1622,2.5,-0.0517
Dylan Harper,1057262518,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.0226,0.321,0.5,0.074
Dylan Harper,1057262518,SAS,OKC,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.1439,0.2894,0.5,0.0898
Keldon Johnson,666682,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5219,0.1932,0.5,0.2279
Victor Wembanyama,56677822,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,22.2715,0.0072,26.5,-0.1754
Victor Wembanyama,56677822,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.822,0.0096,12.5,-0.1687
Victor Wembanyama,56677822,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.6091,0.1078,3.5,-0.1627
Victor Wembanyama,56677822,SAS,OKC,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.92,0.0953,3.5,-0.1243
Cason Wallace,56677833,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,3.3752,0.0961,3.5,-0.1011
Cason Wallace,56677833,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.0978,0.2392,2.5,-0.1441
Cason Wallace,56677833,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.1614,0.2564,1.5,-0.166
Isaiah Hartenstein,201,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,7.2573,0.0224,8.5,-0.126
Isaiah Hartenstein,201,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.4011,0.7114,0.5,-0.1994

```

---

## `derek_game_snapshots/21713534/current_live/market_comparison.parquet`

- bytes: `101,111`
- rows: `41`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
Isaiah Joe,3547272,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,1.115988401159884,0.2794,0.5,0.2121
Chet Holmgren,38017685,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.927590011031997,0.0143,13.5,-0.0407
Chet Holmgren,38017685,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,0.9016000000000002,0.4949,1.5,-0.0995
De'Aaron Fox,161,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.73953628425173,0.0129,13.5,0.101
De'Aaron Fox,161,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.8288775408030435,0.047,4.5,0.1139
Jaylin Williams,38017706,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.088,0.3161,1.5,-0.0597
Jaylin Williams,38017706,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.3303330333033303,0.7703,0.5,-0.1721
Stephon Castle,1028025261,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,17.25716863845999,0.0119,16.5,0.0377
Stephon Castle,1028025261,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.391983967935872,0.0263,6.5,-0.0697
Stephon Castle,1028025261,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.8475000000000001,0.1672,1.5,0.1259
Luguentz Dort,666541,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.0196980301969802,0.329,1.5,-0.1129
Luguentz Dort,666541,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5649000000000002,0.6668,0.5,-0.1646
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,24.19194050849161,0.0064,30.5,-0.2684
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,7.133380098206236,0.0229,7.5,-0.05
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.106910691069107,0.2757,1.5,-0.1447
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.3058,0.3063,1.5,-0.0652
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,0.4557544245575442,0.6641,0.5,-0.229
Dylan Harper,1057262518,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5436066886953035,0.1622,2.5,-0.0517
Dylan Harper,1057262518,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.0226,0.321,0.5,0.074
Dylan Harper,1057262518,SAS,OKC,21713534,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.1438856114388563,0.2894,0.5,0.0898
Keldon Johnson,666682,SAS,OKC,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5219,0.1932,0.5,0.2279
Victor Wembanyama,56677822,SAS,OKC,21713534,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,22.27151320413697,0.0072,26.5,-0.1754
Victor Wembanyama,56677822,SAS,OKC,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,10.82199057833016,0.0096,12.5,-0.1687
Victor Wembanyama,56677822,SAS,OKC,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.6090526737432413,0.1078,3.5,-0.1627
Victor Wembanyama,56677822,SAS,OKC,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.9200000000000004,0.0953,3.5,-0.1243
Cason Wallace,56677833,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,3.3752253154416176,0.0961,3.5,-0.1011
Cason Wallace,56677833,OKC,SAS,21713534,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.0977880092082875,0.2392,2.5,-0.1441
Cason Wallace,56677833,OKC,SAS,21713534,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.1614,0.2564,1.5,-0.166
Isaiah Hartenstein,201,OKC,SAS,21713534,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,7.257314629258516,0.0224,8.5,-0.126
Isaiah Hartenstein,201,OKC,SAS,21713534,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.4011401140114011,0.7114,0.5,-0.1994

```

---

## `derek_game_snapshots/21713534/current_live/outcome_level_probabilities.csv`

- bytes: `114,950`
- rows: `599`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
Isaiah Joe,3547272,21713534,fg3m,0,0.2794,0.5,current_live
Isaiah Joe,3547272,21713534,fg3m,1,0.4034,0.5,current_live
Isaiah Joe,3547272,21713534,fg3m,2,0.2392,0.5,current_live
Isaiah Joe,3547272,21713534,fg3m,3,0.0781,0.5,current_live
Chet Holmgren,38017685,21713534,pts,0,0.0143,13.5,current_live
Chet Holmgren,38017685,21713534,pts,1,0.0163,13.5,current_live
Chet Holmgren,38017685,21713534,pts,2,0.0241,13.5,current_live
Chet Holmgren,38017685,21713534,pts,3,0.0191,13.5,current_live
Chet Holmgren,38017685,21713534,pts,4,0.0299,13.5,current_live
Chet Holmgren,38017685,21713534,pts,5,0.0314,13.5,current_live
Chet Holmgren,38017685,21713534,pts,6,0.0353,13.5,current_live
Chet Holmgren,38017685,21713534,pts,7,0.0477,13.5,current_live
Chet Holmgren,38017685,21713534,pts,8,0.0369,13.5,current_live
Chet Holmgren,38017685,21713534,pts,9,0.0624,13.5,current_live
Chet Holmgren,38017685,21713534,pts,10,0.0645,13.5,current_live
Chet Holmgren,38017685,21713534,pts,11,0.056,13.5,current_live
Chet Holmgren,38017685,21713534,pts,12,0.0705,13.5,current_live
Chet Holmgren,38017685,21713534,pts,13,0.0523,13.5,current_live
Chet Holmgren,38017685,21713534,pts,14,0.0679,13.5,current_live
Chet Holmgren,38017685,21713534,pts,15,0.0464,13.5,current_live
Chet Holmgren,38017685,21713534,pts,16,0.0479,13.5,current_live
Chet Holmgren,38017685,21713534,pts,17,0.044,13.5,current_live
Chet Holmgren,38017685,21713534,pts,18,0.0309,13.5,current_live
Chet Holmgren,38017685,21713534,pts,19,0.0266,13.5,current_live
Chet Holmgren,38017685,21713534,pts,20,0.0352,13.5,current_live
Chet Holmgren,38017685,21713534,pts,21,0.0325,13.5,current_live
Chet Holmgren,38017685,21713534,pts,22,0.0109,13.5,current_live
Chet Holmgren,38017685,21713534,pts,23,0.0141,13.5,current_live
Chet Holmgren,38017685,21713534,pts,24,0.0288,13.5,current_live
Chet Holmgren,38017685,21713534,pts,25,0.0213,13.5,current_live

```

---

## `derek_game_snapshots/21713534/current_live/outcome_level_probabilities.parquet`

- bytes: `21,076`
- rows: `599`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
Isaiah Joe,3547272,21713534,fg3m,0,0.2793720627937206,0.5,current_live
Isaiah Joe,3547272,21713534,fg3m,1,0.40335966403359663,0.5,current_live
Isaiah Joe,3547272,21713534,fg3m,2,0.23917608239176083,0.5,current_live
Isaiah Joe,3547272,21713534,fg3m,3,0.07809219078092192,0.5,current_live
Chet Holmgren,38017685,21713534,pts,0,0.014341590612777058,13.5,current_live
Chet Holmgren,38017685,21713534,pts,1,0.016347407481696923,13.5,current_live
Chet Holmgren,38017685,21713534,pts,2,0.024069802427038416,13.5,current_live
Chet Holmgren,38017685,21713534,pts,3,0.019055260254738745,13.5,current_live
Chet Holmgren,38017685,21713534,pts,4,0.029886671346906035,13.5,current_live
Chet Holmgren,38017685,21713534,pts,5,0.031391033998595934,13.5,current_live
Chet Holmgren,38017685,21713534,pts,6,0.03530237689298968,13.5,current_live
Chet Holmgren,38017685,21713534,pts,7,0.04773844148029286,13.5,current_live
Chet Holmgren,38017685,21713534,pts,8,0.036907030388125574,13.5,current_live
Chet Holmgren,38017685,21713534,pts,9,0.062380904623407896,13.5,current_live
Chet Holmgren,38017685,21713534,pts,10,0.06448701233577375,13.5,current_live
Chet Holmgren,38017685,21713534,pts,11,0.05596229064286432,13.5,current_live
Chet Holmgren,38017685,21713534,pts,12,0.07050446294253336,13.5,current_live
Chet Holmgren,38017685,21713534,pts,13,0.05225152943536256,13.5,current_live
Chet Holmgren,38017685,21713534,pts,14,0.06789690101293754,13.5,current_live
Chet Holmgren,38017685,21713534,pts,15,0.04643466051549495,13.5,current_live
Chet Holmgren,38017685,21713534,pts,16,0.04793902316718485,13.5,current_live
Chet Holmgren,38017685,21713534,pts,17,0.04402768027279111,13.5,current_live
Chet Holmgren,38017685,21713534,pts,18,0.03088957978136597,13.5,current_live
Chet Holmgren,38017685,21713534,pts,19,0.026577073513188252,13.5,current_live
Chet Holmgren,38017685,21713534,pts,20,0.03520208604954368,13.5,current_live
Chet Holmgren,38017685,21713534,pts,21,0.03249423327650186,13.5,current_live
Chet Holmgren,38017685,21713534,pts,22,0.010931701935613282,13.5,current_live
Chet Holmgren,38017685,21713534,pts,23,0.01414100892588507,13.5,current_live
Chet Holmgren,38017685,21713534,pts,24,0.02878347206900011,13.5,current_live
Chet Holmgren,38017685,21713534,pts,25,0.0212616588105506,13.5,current_live

```

---

## `derek_game_snapshots/21713534/current_live/pmf_driver_decomposition.csv`

- bytes: `3,574`
- rows: `17`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
Isaiah Joe,3547272,OKC,21713534,fg3m,0.5
Chet Holmgren,38017685,OKC,21713534,pts,13.5
De'Aaron Fox,161,SAS,21713534,pts,13.5
Jaylin Williams,38017706,OKC,21713534,fg3m,1.5
Stephon Castle,1028025261,SAS,21713534,pts,16.5
Luguentz Dort,666541,OKC,21713534,fg3m,1.5
Shai Gilgeous-Alexander,175,OKC,21713534,pts,30.5
Dylan Harper,1057262518,SAS,21713534,ast,2.5
Keldon Johnson,666682,SAS,21713534,fg3m,0.5
Victor Wembanyama,56677822,SAS,21713534,pts,26.5
Cason Wallace,56677833,OKC,21713534,reb,3.5
Isaiah Hartenstein,201,OKC,21713534,reb,8.5
Alex Caruso,89,OKC,21713534,pts,10.5
Kenrich Williams,480,OKC,21713534,fg3m,0.5
Jared McCain,1028027372,OKC,21713534,pts,13.5
Devin Vassell,3547246,SAS,21713534,pts,12.5
Julian Champagnie,38017649,SAS,21713534,blk,0.5

```

---

## `derek_game_snapshots/21713534/current_live/pmf_driver_decomposition.parquet`

- bytes: `16,640`
- rows: `17`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
Isaiah Joe,3547272,OKC,21713534,fg3m,0.5
Chet Holmgren,38017685,OKC,21713534,pts,13.5
De'Aaron Fox,161,SAS,21713534,pts,13.5
Jaylin Williams,38017706,OKC,21713534,fg3m,1.5
Stephon Castle,1028025261,SAS,21713534,pts,16.5
Luguentz Dort,666541,OKC,21713534,fg3m,1.5
Shai Gilgeous-Alexander,175,OKC,21713534,pts,30.5
Dylan Harper,1057262518,SAS,21713534,ast,2.5
Keldon Johnson,666682,SAS,21713534,fg3m,0.5
Victor Wembanyama,56677822,SAS,21713534,pts,26.5
Cason Wallace,56677833,OKC,21713534,reb,3.5
Isaiah Hartenstein,201,OKC,21713534,reb,8.5
Alex Caruso,89,OKC,21713534,pts,10.5
Kenrich Williams,480,OKC,21713534,fg3m,0.5
Jared McCain,1028027372,OKC,21713534,pts,13.5
Devin Vassell,3547246,SAS,21713534,pts,12.5
Julian Champagnie,38017649,SAS,21713534,blk,0.5

```

---

## `derek_game_snapshots/21713534/current_live/prediction_input_audit.csv`

- bytes: `2,914`
- rows: `41`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
Isaiah Joe,3547272,OKC,SAS,21713534,fg3m,0.5
Chet Holmgren,38017685,OKC,SAS,21713534,pts,13.5
Chet Holmgren,38017685,OKC,SAS,21713534,blk,1.5
De'Aaron Fox,161,SAS,OKC,21713534,pts,13.5
De'Aaron Fox,161,SAS,OKC,21713534,reb,4.5
Jaylin Williams,38017706,OKC,SAS,21713534,fg3m,1.5
Jaylin Williams,38017706,OKC,SAS,21713534,stl,0.5
Stephon Castle,1028025261,SAS,OKC,21713534,pts,16.5
Stephon Castle,1028025261,SAS,OKC,21713534,ast,6.5
Stephon Castle,1028025261,SAS,OKC,21713534,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713534,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713534,stl,0.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,30.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,7.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,1.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,1.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,blk,0.5
Dylan Harper,1057262518,SAS,OKC,21713534,ast,2.5
Dylan Harper,1057262518,SAS,OKC,21713534,fg3m,0.5
Dylan Harper,1057262518,SAS,OKC,21713534,stl,0.5
Keldon Johnson,666682,SAS,OKC,21713534,fg3m,0.5
Victor Wembanyama,56677822,SAS,OKC,21713534,pts,26.5
Victor Wembanyama,56677822,SAS,OKC,21713534,reb,12.5
Victor Wembanyama,56677822,SAS,OKC,21713534,ast,3.5
Victor Wembanyama,56677822,SAS,OKC,21713534,blk,3.5
Cason Wallace,56677833,OKC,SAS,21713534,reb,3.5
Cason Wallace,56677833,OKC,SAS,21713534,ast,2.5
Cason Wallace,56677833,OKC,SAS,21713534,fg3m,1.5
Isaiah Hartenstein,201,OKC,SAS,21713534,reb,8.5
Isaiah Hartenstein,201,OKC,SAS,21713534,blk,0.5

```

---

## `derek_game_snapshots/21713534/current_live/prediction_input_audit.parquet`

- bytes: `6,120`
- rows: `41`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
Isaiah Joe,3547272,OKC,SAS,21713534,fg3m,0.5
Chet Holmgren,38017685,OKC,SAS,21713534,pts,13.5
Chet Holmgren,38017685,OKC,SAS,21713534,blk,1.5
De'Aaron Fox,161,SAS,OKC,21713534,pts,13.5
De'Aaron Fox,161,SAS,OKC,21713534,reb,4.5
Jaylin Williams,38017706,OKC,SAS,21713534,fg3m,1.5
Jaylin Williams,38017706,OKC,SAS,21713534,stl,0.5
Stephon Castle,1028025261,SAS,OKC,21713534,pts,16.5
Stephon Castle,1028025261,SAS,OKC,21713534,ast,6.5
Stephon Castle,1028025261,SAS,OKC,21713534,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713534,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713534,stl,0.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,30.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,7.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,1.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,1.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,blk,0.5
Dylan Harper,1057262518,SAS,OKC,21713534,ast,2.5
Dylan Harper,1057262518,SAS,OKC,21713534,fg3m,0.5
Dylan Harper,1057262518,SAS,OKC,21713534,stl,0.5
Keldon Johnson,666682,SAS,OKC,21713534,fg3m,0.5
Victor Wembanyama,56677822,SAS,OKC,21713534,pts,26.5
Victor Wembanyama,56677822,SAS,OKC,21713534,reb,12.5
Victor Wembanyama,56677822,SAS,OKC,21713534,ast,3.5
Victor Wembanyama,56677822,SAS,OKC,21713534,blk,3.5
Cason Wallace,56677833,OKC,SAS,21713534,reb,3.5
Cason Wallace,56677833,OKC,SAS,21713534,ast,2.5
Cason Wallace,56677833,OKC,SAS,21713534,fg3m,1.5
Isaiah Hartenstein,201,OKC,SAS,21713534,reb,8.5
Isaiah Hartenstein,201,OKC,SAS,21713534,blk,0.5

```

---

## `derek_game_snapshots/21713534/current_live/prop_summary.csv`

- bytes: `2,164`
- rows: `41`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
Isaiah Joe,3547272,OKC,SAS,21713534,fg3m,0.5
Chet Holmgren,38017685,OKC,SAS,21713534,pts,13.5
Chet Holmgren,38017685,OKC,SAS,21713534,blk,1.5
De'Aaron Fox,161,SAS,OKC,21713534,pts,13.5
De'Aaron Fox,161,SAS,OKC,21713534,reb,4.5
Jaylin Williams,38017706,OKC,SAS,21713534,fg3m,1.5
Jaylin Williams,38017706,OKC,SAS,21713534,stl,0.5
Stephon Castle,1028025261,SAS,OKC,21713534,pts,16.5
Stephon Castle,1028025261,SAS,OKC,21713534,ast,6.5
Stephon Castle,1028025261,SAS,OKC,21713534,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713534,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713534,stl,0.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,30.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,7.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,1.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,1.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,blk,0.5
Dylan Harper,1057262518,SAS,OKC,21713534,ast,2.5
Dylan Harper,1057262518,SAS,OKC,21713534,fg3m,0.5
Dylan Harper,1057262518,SAS,OKC,21713534,stl,0.5
Keldon Johnson,666682,SAS,OKC,21713534,fg3m,0.5
Victor Wembanyama,56677822,SAS,OKC,21713534,pts,26.5
Victor Wembanyama,56677822,SAS,OKC,21713534,reb,12.5
Victor Wembanyama,56677822,SAS,OKC,21713534,ast,3.5
Victor Wembanyama,56677822,SAS,OKC,21713534,blk,3.5
Cason Wallace,56677833,OKC,SAS,21713534,reb,3.5
Cason Wallace,56677833,OKC,SAS,21713534,ast,2.5
Cason Wallace,56677833,OKC,SAS,21713534,fg3m,1.5
Isaiah Hartenstein,201,OKC,SAS,21713534,reb,8.5
Isaiah Hartenstein,201,OKC,SAS,21713534,blk,0.5

```

---

## `derek_game_snapshots/21713534/current_live/prop_summary.parquet`

- bytes: `5,438`
- rows: `41`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
Isaiah Joe,3547272,OKC,SAS,21713534,fg3m,0.5
Chet Holmgren,38017685,OKC,SAS,21713534,pts,13.5
Chet Holmgren,38017685,OKC,SAS,21713534,blk,1.5
De'Aaron Fox,161,SAS,OKC,21713534,pts,13.5
De'Aaron Fox,161,SAS,OKC,21713534,reb,4.5
Jaylin Williams,38017706,OKC,SAS,21713534,fg3m,1.5
Jaylin Williams,38017706,OKC,SAS,21713534,stl,0.5
Stephon Castle,1028025261,SAS,OKC,21713534,pts,16.5
Stephon Castle,1028025261,SAS,OKC,21713534,ast,6.5
Stephon Castle,1028025261,SAS,OKC,21713534,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713534,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713534,stl,0.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,30.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,7.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,1.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,1.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,blk,0.5
Dylan Harper,1057262518,SAS,OKC,21713534,ast,2.5
Dylan Harper,1057262518,SAS,OKC,21713534,fg3m,0.5
Dylan Harper,1057262518,SAS,OKC,21713534,stl,0.5
Keldon Johnson,666682,SAS,OKC,21713534,fg3m,0.5
Victor Wembanyama,56677822,SAS,OKC,21713534,pts,26.5
Victor Wembanyama,56677822,SAS,OKC,21713534,reb,12.5
Victor Wembanyama,56677822,SAS,OKC,21713534,ast,3.5
Victor Wembanyama,56677822,SAS,OKC,21713534,blk,3.5
Cason Wallace,56677833,OKC,SAS,21713534,reb,3.5
Cason Wallace,56677833,OKC,SAS,21713534,ast,2.5
Cason Wallace,56677833,OKC,SAS,21713534,fg3m,1.5
Isaiah Hartenstein,201,OKC,SAS,21713534,reb,8.5
Isaiah Hartenstein,201,OKC,SAS,21713534,blk,0.5

```

---

## `derek_game_snapshots/21713534/morning/full_pmf_wide.csv`

- bytes: `379,569`
- rows: `192`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,reb,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,2.9721,2.9721,3,3,0.0408,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,ast,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,2.0574,2.0574,2,2,0.1435,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,fg3m,rotation,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,0.8148,0.8148,1,0,0.4787,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,tov,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,0.7821,0.7821,1,1,0.3539,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,stl,rotation,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,1.287,1.287,1,1,0.2129,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,blk,rotation,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,0.3495,0.3495,0,0,0.7547,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,stocks,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6203,19.9662,0.05,1.6187,1.6187,1,1,0.1607,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pa,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6203,19.9662,0.05,10.851,10.851,10,9,0.0066,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pr,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6203,19.9662,0.05,11.7657,11.7657,11,10,0.0019,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,ra,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6203,19.9662,0.05,5.0295,5.0295,5,5,0.0059,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pra,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6203,19.9662,0.05,13.8231,13.8231,13,12,0.0003,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.9649,31.3201,0.05,16.99,16.99,17,17,0.0019,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.9649,31.3201,0.05,5.1632,5.1632,5,5,0.0048,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.9649,31.3201,0.05,6.2528,6.2528,7,7,0.0048,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.9649,31.3201,0.05,1.7107,1.7107,1,1,0.2161,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.9649,31.3201,0.05,2.3036,2.3036,2,2,0.0871,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.9649,31.3201,0.05,0.6636,0.6636,0,0,0.5194,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.9649,31.3201,0.05,0.2572,0.2572,0,0,0.783,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9649,31.3201,0.05,0.9208,0.9208,1,0,0.4067,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9649,31.3201,0.05,23.2427,23.2427,23,24,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9649,31.3201,0.05,22.1532,22.1532,22,22,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9649,31.3201,0.05,11.4159,11.4159,11,12,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9649,31.3201,0.05,28.4059,28.4059,28,28,0.0,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.1291,33.92,0.05,26.1502,26.1502,26,26,0.0001,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.1291,33.92,0.05,4.162,4.162,4,4,0.0061,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.1291,33.92,0.05,7.6895,7.6895,8,8,0.004,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.1291,33.92,0.05,1.1914,1.1914,1,1,0.2893,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.1291,33.92,0.05,2.9232,2.9232,3,3,0.0539,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.1291,33.92,0.05,0.7751,0.7751,0,0,0.5207,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z

```

---

## `derek_game_snapshots/21713534/morning/full_pmf_wide.parquet`

- bytes: `227,890`
- rows: `192`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,reb,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,2.9720830356760395,2.9720830356760395,3,3,0.040830852930116526,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,ast,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,2.057405562645986,2.0574055626459855,2,2,0.14353956075927518,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,fg3m,rotation,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,0.8148091464593784,0.8148091464593784,1,0,0.4786812183680804,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,tov,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,0.7821258341729249,0.7821258341729248,1,1,0.3539368325306847,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,stl,rotation,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,1.2869755076797516,1.2869755076797518,1,1,0.21287975369683268,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,blk,rotation,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,0.3494678091162397,0.34946780911623965,0,0,0.7547163553974978,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,stocks,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.62033227400498,19.96622200645924,0.050000000000000044,1.6186618932742745,1.6186618932742747,1,1,0.16066383184799057,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pa,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.62033227400498,19.96622200645924,0.050000000000000044,10.851026728236757,10.851026728236755,10,9,0.006604221490829682,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pr,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.62033227400498,19.96622200645924,0.050000000000000044,11.765704201266809,11.765704201266812,11,10,0.0018786179571930804,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,ra,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.62033227400498,19.96622200645924,0.050000000000000044,5.02948859832202,5.029488598322018,5,5,0.005860842695015491,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pra,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.62033227400498,19.96622200645924,0.050000000000000044,13.823109763912775,13.823109763912777,13,12,0.00026965599640998175,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.964921676365634,31.320073990530062,0.050000000000000044,16.9899988344321,16.989998834432104,17,17,0.0018505787115850295,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.964921676365634,31.320073990530062,0.050000000000000044,5.163157127136888,5.163157127136889,5,5,0.004764582804936277,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.964921676365634,31.320073990530062,0.050000000000000044,6.25275066681706,6.252750666817059,7,7,0.004836683237830696,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.964921676365634,31.320073990530062,0.050000000000000044,1.7106914300447564,1.7106914300447564,1,1,0.21611833686437912,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.964921676365634,31.320073990530062,0.050000000000000044,2.303601684692972,2.3036016846929717,2,2,0.08711050637143292,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.964921676365634,31.320073990530062,0.050000000000000044,0.663601996126987,0.6636019961269868,0,0,0.519359905661563,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,28.964921676365634,31.320073990530062,0.050000000000000044,0.2571954882245488,0.2571954882245488,0,0,0.7829880058191172,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.964921676365634,31.320073990530062,0.050000000000000044,0.9207974843515357,0.9207974843515356,1,0,0.4066525768363519,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.964921676365634,31.320073990530062,0.050000000000000044,23.242749501249136,23.242749501249133,23,24,8.95066303460964e-06,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.964921676365634,31.320073990530062,0.050000000000000044,22.153155961568952,22.153155961568984,22,22,8.817235508399165e-06,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.964921676365634,31.320073990530062,0.050000000000000044,11.415907793953926,11.415907793953927,11,12,2.304477778789166e-05,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
De'Aaron Fox,161,SAS,OKC,21713534,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.964921676365634,31.320073990530062,0.050000000000000044,28.40590662838599,28.405906628385996,28,28,4.264617518747986e-08,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.129144295789906,33.91998872629533,0.050000000000000044,26.15015525342752,26.150155253427503,26,26,0.0001411920340978078,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.129144295789906,33.91998872629533,0.050000000000000044,4.161988441536009,4.161988441536009,4,4,0.0060564516079388685,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.129144295789906,33.91998872629533,0.050000000000000044,7.689534365768694,7.689534365768692,8,8,0.004031556894299636,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.129144295789906,33.91998872629533,0.050000000000000044,1.1914203574203133,1.1914203574203133,1,1,0.2893286057478454,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.129144295789906,33.91998872629533,0.050000000000000044,2.9231939502253663,2.9231939502253668,3,3,0.05394819060861963,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.129144295789906,33.91998872629533,0.050000000000000044,0.7750636083320372,0.7750636083320371,0,0,0.5206836976760881,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z

```

---

## `derek_game_snapshots/21713534/morning/market_comparison.csv`

- bytes: `2,636,212`
- rows: `2,777`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,14.5,14.5,fanduel,0.1449,235,-320,0.2815,-0.1367,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,12.5,12.5,fanduel,0.2253,138,-186,0.3925,-0.1672,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,fanduel,0.2781,102,-136,0.4621,-0.184,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,10.5,10.5,fanduel,0.3399,-132,100,0.5323,-0.1923,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,9.5,9.5,fanduel,0.3999,-174,134,0.5977,-0.1978,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,8.5,8.5,fanduel,0.4742,-245,178,0.6638,-0.1895,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,7.5,7.5,fanduel,0.5574,-350,240,0.7256,-0.1683,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,6.5,6.5,fanduel,0.6381,-500,320,0.7778,-0.1396,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,5.5,5.5,fanduel,0.7108,-800,450,0.8302,-0.1194,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,13.5,13.5,fanduel,0.1814,178,-245,0.3362,-0.1548,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,10.5,10.5,fanduel,0.3399,-128,100,0.5289,-0.189,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,williamhill_us,0.2781,-115,-113,0.502,-0.2239,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,13.5,13.5,bovada,0.1814,150,-200,0.375,-0.1936,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,12.5,12.5,bovada,0.2253,115,-150,0.4367,-0.2114,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,bovada,0.2781,-115,-115,0.5,-0.2219,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,10.5,10.5,bovada,0.3399,-150,115,0.5633,-0.2234,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,9.5,9.5,bovada,0.3999,-215,160,0.6396,-0.2397,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,14.5,14.5,bovada,0.1449,190,-260,0.3232,-0.1783,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,betmgm,0.2781,-111,-120,0.491,-0.2128,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,betrivers,0.2781,105,-143,0.4532,-0.1751,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,10.5,10.5,betrivers,0.3399,-129,-106,0.5226,-0.1827,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,draftkings,0.2781,-110,-116,0.4938,-0.2157,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,hardrockbet_az,0.2781,-115,-115,0.5,-0.2219,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,hardrockbet,0.2781,-115,-115,0.5,-0.2219,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,rebet,0.2781,100,-127,0.4719,-0.1938,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,hardrockbet_fl,0.2781,-115,-115,0.5,-0.2219,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,9.5,9.5,espnbet,0.3999,-180,135,0.6017,-0.2018,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,10.5,10.5,espnbet,0.3399,-125,-105,0.5203,-0.1804,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,espnbet,0.2781,100,-130,0.4694,-0.1913,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6203,19.9662,0.05,8.7936,8.7936,8,8,0.046,11.5,11.5,betparx,0.2781,107,-143,0.4508,-0.1727,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z

```

---

## `derek_game_snapshots/21713534/morning/market_comparison.parquet`

- bytes: `153,016`
- rows: `2,777`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,14.5,14.5,fanduel,0.14485037117756674,235,-320,0.28150134048257375,-0.136650969305007,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,12.5,12.5,fanduel,0.22525346354583245,138,-186,0.3924905308228578,-0.1672370672770253,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,fanduel,0.2781074344250865,102,-136,0.46209273182957394,-0.18398529740448727,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,10.5,10.5,fanduel,0.3399162125420959,-132,100,0.532258064516129,-0.19234185197403297,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,9.5,9.5,fanduel,0.3999316742552203,-174,134,0.5977450231957249,-0.1978133489405044,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,8.5,8.5,fanduel,0.47423475355937805,-245,178,0.6637754604814345,-0.18954070692205632,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,7.5,7.5,fanduel,0.5573551665896229,-350,240,0.7256097560975611,-0.16825458950793815,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,6.5,6.5,fanduel,0.6381440362512917,-500,320,0.7777777777777778,-0.13963374152648622,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,5.5,5.5,fanduel,0.7107712380091472,-800,450,0.830188679245283,-0.11941744123613574,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,13.5,13.5,fanduel,0.1813812186940034,178,-245,0.3362245395185654,-0.154843320824562,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,10.5,10.5,fanduel,0.3399162125420959,-128,100,0.5289256198347108,-0.18900940729261473,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,williamhill_us,0.2781074344250865,-115,-113,0.502049600327936,-0.22394216590284932,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,13.5,13.5,bovada,0.1813812186940034,150,-200,0.375,-0.1936187813059966,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,12.5,12.5,bovada,0.22525346354583245,115,-150,0.43668122270742354,-0.21142775916159107,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,bovada,0.2781074344250865,-115,-115,0.5,-0.22189256557491333,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,10.5,10.5,bovada,0.3399162125420959,-150,115,0.5633187772925764,-0.22340256475048037,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,9.5,9.5,bovada,0.3999316742552203,-215,160,0.6395881006864989,-0.23965642643127838,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,14.5,14.5,bovada,0.14485037117756674,190,-260,0.32315978456014366,-0.17830941338257691,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,betmgm,0.2781074344250865,-111,-120,0.49095295536791317,-0.2128455209428265,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,betrivers,0.2781074344250865,105,-143,0.4532313718175883,-0.17512393739250165,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,10.5,10.5,betrivers,0.3399162125420959,-129,-106,0.5226164254247954,-0.18270021288269933,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,draftkings,0.2781074344250865,-110,-116,0.4937655860349127,-0.21565815160982604,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,hardrockbet_az,0.2781074344250865,-115,-115,0.5,-0.22189256557491333,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,hardrockbet,0.2781074344250865,-115,-115,0.5,-0.22189256557491333,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,rebet,0.2781074344250865,100,-127,0.47193347193347185,-0.19382603750838517,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,hardrockbet_fl,0.2781074344250865,-115,-115,0.5,-0.22189256557491333,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,9.5,9.5,espnbet,0.3999316742552203,-180,135,0.6017069701280228,-0.2017752958728023,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,10.5,10.5,espnbet,0.3399162125420959,-125,-105,0.5203045685279188,-0.1803883559858228,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,espnbet,0.2781074344250865,100,-130,0.4693877551020409,-0.19128032067695422,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.62033227400498,19.96622200645924,0.050000000000000044,8.793621165590771,8.793621165590771,8,8,0.046009765223577456,11.5,11.5,betparx,0.2781074344250865,107,-143,0.45082651527800965,-0.17271908085292298,fallback_used,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-30T22:47:50Z

```

---

## `derek_game_snapshots/21713534/morning/outcome_level_probabilities.csv`

- bytes: `558,526`
- rows: `6,501`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Alex Caruso,89,21713534,pts,rotation,0,0.046,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,1,0.0372,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,2,0.0386,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,3,0.0361,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,4,0.0538,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,5,0.0775,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,6,0.0726,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,7,0.0808,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,8,0.0831,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,9,0.0743,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,10,0.06,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,11,0.0618,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,12,0.0529,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,13,0.0439,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,14,0.0365,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,15,0.037,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,16,0.0174,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,17,0.0256,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,18,0.0163,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,19,0.0146,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,20,0.0065,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,21,0.0071,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,22,0.0026,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,23,0.0072,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,24,0.0039,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,25,0.0023,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,26,0.0009,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,27,0.0002,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,28,0.0003,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,29,0.0006,fallback_used,projected

```

---

## `derek_game_snapshots/21713534/morning/outcome_level_probabilities.parquet`

- bytes: `75,149`
- rows: `6,501`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Alex Caruso,89,21713534,pts,rotation,0,0.04600976522357745,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,1,0.037200459419124185,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,2,0.03863794954524219,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,3,0.03608384709682035,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,4,0.05377470512790045,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,5,0.07752203557818822,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,6,0.07262720175785556,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,7,0.08078886966166868,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,8,0.08312041303024473,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,9,0.07430307930415772,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,10,0.06001546171312441,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,11,0.0618087781170094,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,12,0.05285397087925415,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,13,0.043872244851829084,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,14,0.03653084751643666,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,15,0.0369794645150094,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,16,0.017397054491099198,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,17,0.02556795378782027,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,18,0.016293053674203428,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,19,0.014565141096067552,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,20,0.006547030352269181,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,21,0.007103146825930806,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,22,0.002563918838942279,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,23,0.007182504388110656,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,24,0.003938257506230312,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,25,0.00231166790221755,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,26,0.0009138232678368318,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,27,0.000189758044795183,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,28,0.00028794667376510395,fallback_used,projected
Alex Caruso,89,21713534,pts,rotation,29,0.0005944113779791856,fallback_used,projected

```

---

## `derek_game_snapshots/21713534/morning/prop_summary.csv`

- bytes: `27,926`
- rows: `192`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,8.7936,11.5,11.5,betmgm,0.2781,-111.0,-120.0,0.491,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,reb,rotation,2.9721,3.5,3.5,betmgm,0.3022,-120.0,-110.0,0.5101,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,ast,rotation,2.0574,2.5,2.5,betmgm,0.3632,-135.0,100.0,0.5347,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,fg3m,rotation,0.8148,2.5,2.5,betmgm,0.0968,145.0,-200.0,0.3797,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,tov,rotation,0.7821,,,,,,,,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,stl,rotation,1.287,1.5,1.5,betparx,0.3431,-109.0,-122.0,0.4869,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,blk,rotation,0.3495,0.5,0.5,betparx,0.2453,125.0,-167.0,0.4154,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,stocks,rotation,1.6187,2.5,2.5,betparx,0.2247,150.0,-205.0,0.3731,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,pa,rotation,10.851,13.5,13.5,bovada,0.2873,-135.0,105.0,0.5408,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,pr,rotation,11.7657,14.5,14.5,bovada,0.284,-130.0,100.0,0.5306,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,ra,rotation,5.0295,6.5,6.5,bovada,0.216,115.0,-150.0,0.4367,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,pra,rotation,13.8231,17.5,17.5,betparx,0.2407,100.0,-132.0,0.4677,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,pts,starter,16.99,13.5,13.5,betmgm,0.7052,-130.0,-105.0,0.5246,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,reb,starter,5.1632,4.5,4.5,betmgm,0.6677,115.0,-150.0,0.4367,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,ast,starter,6.2528,5.5,5.5,betmgm,0.6438,-140.0,105.0,0.5446,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,fg3m,starter,1.7107,1.5,1.5,betmgm,0.4609,120.0,-160.0,0.4248,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,tov,starter,2.3036,,,,,,,,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,stl,starter,0.6636,1.5,1.5,bovada,0.1316,170.0,-230.0,0.347,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,blk,starter,0.2572,0.5,0.5,betmgm,0.217,290.0,-450.0,0.2386,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,stocks,starter,0.9208,1.5,1.5,draftkings,0.224,122.0,-162.0,0.4215,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,pa,starter,23.2427,19.5,19.5,betmgm,0.7134,-118.0,-115.0,0.503,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,pr,starter,22.1532,17.5,17.5,bovada,0.7617,-125.0,-105.0,0.5203,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,ra,starter,11.4159,10.5,10.5,bovada,0.6468,105.0,-135.0,0.4592,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,pra,starter,28.4059,23.5,23.5,betmgm,0.7658,-135.0,100.0,0.5347,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,starter,26.1502,30.5,30.5,betparx,0.241,-112.0,-120.0,0.492,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,reb,starter,4.162,3.5,3.5,betmgm,0.7069,-140.0,105.0,0.5446,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,starter,7.6895,7.5,7.5,betmgm,0.5587,-135.0,100.0,0.5347,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,starter,1.1914,1.5,1.5,betmgm,0.3577,-105.0,-125.0,0.4797,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,tov,starter,2.9232,,,,,,,,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,starter,0.7751,1.5,1.5,betparx,0.2123,125.0,-167.0,0.4154,fallback_used,projected

```

---

## `derek_game_snapshots/21713534/morning/prop_summary.parquet`

- bytes: `19,243`
- rows: `192`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
Alex Caruso,89,OKC,SAS,21713534,pts,rotation,8.793621165590771,11.5,11.5,betmgm,0.2781074344250865,-111.0,-120.0,0.49095295536791317,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,reb,rotation,2.9720830356760395,3.5,3.5,betmgm,0.30224363174407465,-120.0,-110.0,0.5101214574898786,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,ast,rotation,2.0574055626459855,2.5,2.5,betmgm,0.3632298901189042,-135.0,100.0,0.5346534653465347,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,fg3m,rotation,0.8148091464593784,2.5,2.5,betmgm,0.0967862009009817,145.0,-200.0,0.37974683544303806,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,tov,rotation,0.7821258341729248,,,,,,,,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,stl,rotation,1.2869755076797518,1.5,1.5,betparx,0.3430603800069888,-109.0,-122.0,0.4869204764971024,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,blk,rotation,0.34946780911623965,0.5,0.5,betparx,0.24528364460250227,125.0,-167.0,0.41540256709451573,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,stocks,rotation,1.6186618932742747,2.5,2.5,betparx,0.2246663385255783,150.0,-205.0,0.3730886850152905,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,pa,rotation,10.851026728236755,13.5,13.5,bovada,0.28727313445744057,-135.0,105.0,0.5407914020517831,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,pr,rotation,11.765704201266812,14.5,14.5,bovada,0.2839977055258303,-130.0,100.0,0.5306122448979592,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,ra,rotation,5.029488598322018,6.5,6.5,bovada,0.21595872380796363,115.0,-150.0,0.43668122270742354,fallback_used,projected
Alex Caruso,89,OKC,SAS,21713534,pra,rotation,13.823109763912777,17.5,17.5,betparx,0.24065920384297865,100.0,-132.0,0.4677419354838709,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,pts,starter,16.989998834432104,13.5,13.5,betmgm,0.7052146590580136,-130.0,-105.0,0.5246062992125985,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,reb,starter,5.163157127136889,4.5,4.5,betmgm,0.6676669006165612,115.0,-150.0,0.43668122270742354,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,ast,starter,6.252750666817059,5.5,5.5,betmgm,0.6437549417875212,-140.0,105.0,0.5445920303605313,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,fg3m,starter,1.7106914300447564,1.5,1.5,betmgm,0.46089252816042614,120.0,-160.0,0.4248366013071895,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,tov,starter,2.3036016846929717,,,,,,,,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,stl,starter,0.6636019961269868,1.5,1.5,bovada,0.13164221297906256,170.0,-230.0,0.34700315457413244,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,blk,starter,0.2571954882245488,0.5,0.5,betmgm,0.21701199418088285,290.0,-450.0,0.23861171366594355,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,stocks,starter,0.9207974843515356,1.5,1.5,draftkings,0.22404035252162005,122.0,-162.0,0.421465800141561,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,pa,starter,23.242749501249133,19.5,19.5,betmgm,0.71344694206858,-118.0,-115.0,0.5029738302934179,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,pr,starter,22.153155961568984,17.5,17.5,bovada,0.7617435998830112,-125.0,-105.0,0.5203045685279188,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,ra,starter,11.415907793953927,10.5,10.5,bovada,0.6468084934620476,105.0,-135.0,0.4592085979482169,fallback_used,projected
De'Aaron Fox,161,SAS,OKC,21713534,pra,starter,28.405906628385996,23.5,23.5,betmgm,0.7657818654618894,-135.0,100.0,0.5346534653465347,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,pts,starter,26.150155253427503,30.5,30.5,betparx,0.24103139389917863,-112.0,-120.0,0.4920127795527157,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,reb,starter,4.161988441536009,3.5,3.5,betmgm,0.7069088640348401,-140.0,105.0,0.5445920303605313,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,ast,starter,7.689534365768692,7.5,7.5,betmgm,0.5587453721030684,-135.0,100.0,0.5346534653465347,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,fg3m,starter,1.1914203574203133,1.5,1.5,betmgm,0.35770737951141396,-105.0,-125.0,0.4796954314720812,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,tov,starter,2.9231939502253668,,,,,,,,fallback_used,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713534,stl,starter,0.7750636083320371,1.5,1.5,betparx,0.21227309794111224,125.0,-167.0,0.41540256709451573,fallback_used,projected

```
