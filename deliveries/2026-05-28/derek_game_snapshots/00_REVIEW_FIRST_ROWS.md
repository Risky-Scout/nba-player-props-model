# Reviewable Delivery Preview — 2026-05-28 — derek_game_snapshots

GitHub may refuse to render large CSV files. This file is intentionally small.

---

## `derek_game_snapshots/21713533/current_live/after_game_scoring.csv`

- bytes: `2,519`
- rows: `39`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,stat,line
De'Aaron Fox,161,pts,15.5
De'Aaron Fox,161,reb,3.5
Jalen Williams,38017703,pts,12.5
Jalen Williams,38017703,reb,3.5
Jalen Williams,38017703,ast,3.5
Isaiah Hartenstein,201,reb,8.5
Cason Wallace,56677833,pts,8.5
Cason Wallace,56677833,ast,2.5
Cason Wallace,56677833,fg3m,1.5
Jaylin Williams,38017706,reb,3.5
Jared McCain,1028027372,pts,13.5
Jared McCain,1028027372,stl,0.5
Stephon Castle,1028025261,reb,5.5
Stephon Castle,1028025261,ast,6.5
Devin Vassell,3547246,pts,13.5
Devin Vassell,3547246,reb,4.5
Devin Vassell,3547246,fg3m,2.5
Devin Vassell,3547246,stl,1.0
Shai Gilgeous-Alexander,175,pts,29.5
Shai Gilgeous-Alexander,175,fg3m,1.5
Luguentz Dort,666541,fg3m,1.5
Julian Champagnie,38017649,reb,5.5
Julian Champagnie,38017649,fg3m,2.5
Chet Holmgren,38017685,reb,7.5
Chet Holmgren,38017685,blk,1.5
Dylan Harper,1057262518,reb,3.5
Dylan Harper,1057262518,ast,2.5
Dylan Harper,1057262518,fg3m,0.5
Dylan Harper,1057262518,stl,0.5
Alex Caruso,89,pts,10.5

```

---

## `derek_game_snapshots/21713533/current_live/contextual_feature_audit.csv`

- bytes: `5,117`
- rows: `16`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21713533
Jalen Williams,38017703,OKC,21713533
Isaiah Hartenstein,201,OKC,21713533
Cason Wallace,56677833,OKC,21713533
Jaylin Williams,38017706,OKC,21713533
Jared McCain,1028027372,OKC,21713533
Stephon Castle,1028025261,SAS,21713533
Devin Vassell,3547246,SAS,21713533
Shai Gilgeous-Alexander,175,OKC,21713533
Luguentz Dort,666541,OKC,21713533
Julian Champagnie,38017649,SAS,21713533
Chet Holmgren,38017685,OKC,21713533
Dylan Harper,1057262518,SAS,21713533
Alex Caruso,89,OKC,21713533
Keldon Johnson,666682,SAS,21713533
Victor Wembanyama,56677822,SAS,21713533

```

---

## `derek_game_snapshots/21713533/current_live/contextual_feature_audit.parquet`

- bytes: `34,426`
- rows: `16`
- columns: `41`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21713533
Jalen Williams,38017703,OKC,21713533
Isaiah Hartenstein,201,OKC,21713533
Cason Wallace,56677833,OKC,21713533
Jaylin Williams,38017706,OKC,21713533
Jared McCain,1028027372,OKC,21713533
Stephon Castle,1028025261,SAS,21713533
Devin Vassell,3547246,SAS,21713533
Shai Gilgeous-Alexander,175,OKC,21713533
Luguentz Dort,666541,OKC,21713533
Julian Champagnie,38017649,SAS,21713533
Chet Holmgren,38017685,OKC,21713533
Dylan Harper,1057262518,SAS,21713533
Alex Caruso,89,OKC,21713533
Keldon Johnson,666682,SAS,21713533
Victor Wembanyama,56677822,SAS,21713533

```

---

## `derek_game_snapshots/21713533/current_live/derek_live_predictions.parquet`

- bytes: `45,291`
- rows: `39`
- columns: `47`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.5,0.0547
De'Aaron Fox,161,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.0786
Jalen Williams,38017703,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.5,0.0973
Jalen Williams,38017703,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,0.1405
Jalen Williams,38017703,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,0.1145
Isaiah Hartenstein,201,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.5,-0.0371
Cason Wallace,56677833,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.5,-0.0933
Cason Wallace,56677833,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.5,-0.1272
Cason Wallace,56677833,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.5,-0.1246
Jaylin Williams,38017706,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,3.5,-0.0913
Jared McCain,1028027372,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,13.5,-0.1382
Jared McCain,1028027372,OKC,SAS,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0665
Stephon Castle,1028025261,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.0655
Stephon Castle,1028025261,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1046
Devin Vassell,3547246,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.0543
Devin Vassell,3547246,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,0.0749
Devin Vassell,3547246,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1273
Devin Vassell,3547246,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0,0.1784
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,29.5,-0.1263
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1613
Luguentz Dort,666541,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.1104
Julian Champagnie,38017649,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.0707
Julian Champagnie,38017649,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.5,-0.081
Chet Holmgren,38017685,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,7.5,0.0302
Chet Holmgren,38017685,OKC,SAS,21713533,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.5,-0.182
Dylan Harper,1057262518,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,3.5,0.0814
Dylan Harper,1057262518,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5,-0.1201
Dylan Harper,1057262518,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.0795
Dylan Harper,1057262518,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.1161
Alex Caruso,89,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,10.5,-0.1604

```

---

## `derek_game_snapshots/21713533/current_live/full_pmf_wide.csv`

- bytes: `46,097`
- rows: `39`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.5,0.0547
De'Aaron Fox,161,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.0786
Jalen Williams,38017703,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.5,0.0973
Jalen Williams,38017703,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,0.1405
Jalen Williams,38017703,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,0.1145
Isaiah Hartenstein,201,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.5,-0.0371
Cason Wallace,56677833,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.5,-0.0933
Cason Wallace,56677833,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.5,-0.1272
Cason Wallace,56677833,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.5,-0.1246
Jaylin Williams,38017706,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,3.5,-0.0913
Jared McCain,1028027372,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,13.5,-0.1382
Jared McCain,1028027372,OKC,SAS,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0665
Stephon Castle,1028025261,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.0655
Stephon Castle,1028025261,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1046
Devin Vassell,3547246,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.0543
Devin Vassell,3547246,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,0.0749
Devin Vassell,3547246,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1273
Devin Vassell,3547246,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0,0.1784
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,29.5,-0.1263
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1613
Luguentz Dort,666541,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.1104
Julian Champagnie,38017649,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.0707
Julian Champagnie,38017649,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.5,-0.081
Chet Holmgren,38017685,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,7.5,0.0302
Chet Holmgren,38017685,OKC,SAS,21713533,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.5,-0.182
Dylan Harper,1057262518,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,3.5,0.0814
Dylan Harper,1057262518,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5,-0.1201
Dylan Harper,1057262518,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.0795
Dylan Harper,1057262518,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.1161
Alex Caruso,89,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,10.5,-0.1604

```

---

## `derek_game_snapshots/21713533/current_live/full_pmf_wide.parquet`

- bytes: `84,410`
- rows: `39`
- columns: `93`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,line,edge_over
De'Aaron Fox,161,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,15.5,0.0547
De'Aaron Fox,161,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,3.5,0.0786
Jalen Williams,38017703,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,12.5,0.0973
Jalen Williams,38017703,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,0.1405
Jalen Williams,38017703,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,3.5,0.1145
Isaiah Hartenstein,201,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.5,-0.0371
Cason Wallace,56677833,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.5,-0.0933
Cason Wallace,56677833,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.5,-0.1272
Cason Wallace,56677833,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.5,-0.1246
Jaylin Williams,38017706,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,3.5,-0.0913
Jared McCain,1028027372,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,13.5,-0.1382
Jared McCain,1028027372,OKC,SAS,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,-0.0665
Stephon Castle,1028025261,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.5,-0.0655
Stephon Castle,1028025261,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.5,-0.1046
Devin Vassell,3547246,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,13.5,-0.0543
Devin Vassell,3547246,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.5,0.0749
Devin Vassell,3547246,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.5,-0.1273
Devin Vassell,3547246,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.0,0.1784
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,29.5,-0.1263
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5,-0.1613
Luguentz Dort,666541,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.5,-0.1104
Julian Champagnie,38017649,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.5,-0.0707
Julian Champagnie,38017649,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.5,-0.081
Chet Holmgren,38017685,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,7.5,0.0302
Chet Holmgren,38017685,OKC,SAS,21713533,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.5,-0.182
Dylan Harper,1057262518,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,3.5,0.0814
Dylan Harper,1057262518,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.5,-0.1201
Dylan Harper,1057262518,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.0795
Dylan Harper,1057262518,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5,0.1161
Alex Caruso,89,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,10.5,-0.1604

```

---

## `derek_game_snapshots/21713533/current_live/game_context.csv`

- bytes: `687`
- rows: `16`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,OKC,21713533
Jalen Williams,38017703,OKC,SAS,21713533
Isaiah Hartenstein,201,OKC,SAS,21713533
Cason Wallace,56677833,OKC,SAS,21713533
Jaylin Williams,38017706,OKC,SAS,21713533
Jared McCain,1028027372,OKC,SAS,21713533
Stephon Castle,1028025261,SAS,OKC,21713533
Devin Vassell,3547246,SAS,OKC,21713533
Shai Gilgeous-Alexander,175,OKC,SAS,21713533
Luguentz Dort,666541,OKC,SAS,21713533
Julian Champagnie,38017649,SAS,OKC,21713533
Chet Holmgren,38017685,OKC,SAS,21713533
Dylan Harper,1057262518,SAS,OKC,21713533
Alex Caruso,89,OKC,SAS,21713533
Keldon Johnson,666682,SAS,OKC,21713533
Victor Wembanyama,56677822,SAS,OKC,21713533

```

---

## `derek_game_snapshots/21713533/current_live/game_context.parquet`

- bytes: `4,071`
- rows: `16`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id
De'Aaron Fox,161,SAS,OKC,21713533
Jalen Williams,38017703,OKC,SAS,21713533
Isaiah Hartenstein,201,OKC,SAS,21713533
Cason Wallace,56677833,OKC,SAS,21713533
Jaylin Williams,38017706,OKC,SAS,21713533
Jared McCain,1028027372,OKC,SAS,21713533
Stephon Castle,1028025261,SAS,OKC,21713533
Devin Vassell,3547246,SAS,OKC,21713533
Shai Gilgeous-Alexander,175,OKC,SAS,21713533
Luguentz Dort,666541,OKC,SAS,21713533
Julian Champagnie,38017649,SAS,OKC,21713533
Chet Holmgren,38017685,OKC,SAS,21713533
Dylan Harper,1057262518,SAS,OKC,21713533
Alex Caruso,89,OKC,SAS,21713533
Keldon Johnson,666682,SAS,OKC,21713533
Victor Wembanyama,56677822,SAS,OKC,21713533

```

---

## `derek_game_snapshots/21713533/current_live/injury_availability_context.csv`

- bytes: `674`
- rows: `16`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21713533
Jalen Williams,38017703,OKC,21713533
Isaiah Hartenstein,201,OKC,21713533
Cason Wallace,56677833,OKC,21713533
Jaylin Williams,38017706,OKC,21713533
Jared McCain,1028027372,OKC,21713533
Stephon Castle,1028025261,SAS,21713533
Devin Vassell,3547246,SAS,21713533
Shai Gilgeous-Alexander,175,OKC,21713533
Luguentz Dort,666541,OKC,21713533
Julian Champagnie,38017649,SAS,21713533
Chet Holmgren,38017685,OKC,21713533
Dylan Harper,1057262518,SAS,21713533
Alex Caruso,89,OKC,21713533
Keldon Johnson,666682,SAS,21713533
Victor Wembanyama,56677822,SAS,21713533

```

---

## `derek_game_snapshots/21713533/current_live/injury_availability_context.parquet`

- bytes: `4,324`
- rows: `16`
- columns: `5`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id
De'Aaron Fox,161,SAS,21713533
Jalen Williams,38017703,OKC,21713533
Isaiah Hartenstein,201,OKC,21713533
Cason Wallace,56677833,OKC,21713533
Jaylin Williams,38017706,OKC,21713533
Jared McCain,1028027372,OKC,21713533
Stephon Castle,1028025261,SAS,21713533
Devin Vassell,3547246,SAS,21713533
Shai Gilgeous-Alexander,175,OKC,21713533
Luguentz Dort,666541,OKC,21713533
Julian Champagnie,38017649,SAS,21713533
Chet Holmgren,38017685,OKC,21713533
Dylan Harper,1057262518,SAS,21713533
Alex Caruso,89,OKC,21713533
Keldon Johnson,666682,SAS,21713533
Victor Wembanyama,56677822,SAS,21713533

```

---

## `derek_game_snapshots/21713533/current_live/lineup_context.csv`

- bytes: `1,763`
- rows: `16`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21713533,pts
Jalen Williams,38017703,OKC,21713533,pts
Isaiah Hartenstein,201,OKC,21713533,reb
Cason Wallace,56677833,OKC,21713533,pts
Jaylin Williams,38017706,OKC,21713533,reb
Jared McCain,1028027372,OKC,21713533,pts
Stephon Castle,1028025261,SAS,21713533,reb
Devin Vassell,3547246,SAS,21713533,pts
Shai Gilgeous-Alexander,175,OKC,21713533,pts
Luguentz Dort,666541,OKC,21713533,fg3m
Julian Champagnie,38017649,SAS,21713533,reb
Chet Holmgren,38017685,OKC,21713533,reb
Dylan Harper,1057262518,SAS,21713533,reb
Alex Caruso,89,OKC,21713533,pts
Keldon Johnson,666682,SAS,21713533,fg3m
Victor Wembanyama,56677822,SAS,21713533,pts

```

---

## `derek_game_snapshots/21713533/current_live/lineup_context.parquet`

- bytes: `9,535`
- rows: `16`
- columns: `13`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat
De'Aaron Fox,161,SAS,21713533,pts
Jalen Williams,38017703,OKC,21713533,pts
Isaiah Hartenstein,201,OKC,21713533,reb
Cason Wallace,56677833,OKC,21713533,pts
Jaylin Williams,38017706,OKC,21713533,reb
Jared McCain,1028027372,OKC,21713533,pts
Stephon Castle,1028025261,SAS,21713533,reb
Devin Vassell,3547246,SAS,21713533,pts
Shai Gilgeous-Alexander,175,OKC,21713533,pts
Luguentz Dort,666541,OKC,21713533,fg3m
Julian Champagnie,38017649,SAS,21713533,reb
Chet Holmgren,38017685,OKC,21713533,reb
Dylan Harper,1057262518,SAS,21713533,reb
Alex Caruso,89,OKC,21713533,pts
Keldon Johnson,666682,SAS,21713533,fg3m
Victor Wembanyama,56677822,SAS,21713533,pts

```

---

## `derek_game_snapshots/21713533/current_live/market_comparison.csv`

- bytes: `60,457`
- rows: `39`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.904489304007225,0.0102,15.5,0.0547
De'Aaron Fox,161,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.492336972853852,0.0579,3.5,0.0786
Jalen Williams,38017703,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,15.767516562939168,0.0157,12.5,0.0973
Jalen Williams,38017703,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.625200320512819,0.0722,3.5,0.1405
Jalen Williams,38017703,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.218079775506114,0.0713,3.5,0.1145
Isaiah Hartenstein,201,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.004106981869176,0.0218,8.5,-0.0371
Cason Wallace,56677833,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,7.858647672552163,0.0434,8.5,-0.0933
Cason Wallace,56677833,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.139364793106904,0.2407,2.5,-0.1272
Cason Wallace,56677833,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.0652,0.325,1.5,-0.1246
Jaylin Williams,38017706,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,3.5937687838108587,0.1177,3.5,-0.0913
Jared McCain,1028027372,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,11.512320225284116,0.0472,13.5,-0.1382
Jared McCain,1028027372,OKC,SAS,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5273527352735273,0.6351,0.5,-0.0665
Stephon Castle,1028025261,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.044266399599398,0.0417,5.5,-0.0655
Stephon Castle,1028025261,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.292138207310967,0.0303,6.5,-0.1046
Devin Vassell,3547246,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,12.936891742751078,0.0186,13.5,-0.0543
Devin Vassell,3547246,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.976555455365193,0.0476,4.5,0.0749
Devin Vassell,3547246,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.2150784921507847,0.1073,2.5,-0.1273
Devin Vassell,3547246,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5194519451945192,0.2382,1.0,0.1784
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,26.076024569529743,0.0049,29.5,-0.1263
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.009099090090991,0.3268,1.5,-0.1613
Luguentz Dort,666541,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.9872987298729876,0.3288,1.5,-0.1104
Julian Champagnie,38017649,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.411552707978775,0.0463,5.5,-0.0707
Julian Champagnie,38017649,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.091590840915908,0.1242,2.5,-0.081
Chet Holmgren,38017685,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.162960737179489,0.0184,7.5,0.0302
Chet Holmgren,38017685,OKC,SAS,21713533,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.052905290529053,0.3933,1.5,-0.182
Dylan Harper,1057262518,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,4.582273410115173,0.0606,3.5,0.0814
Dylan Harper,1057262518,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.246266412749323,0.2075,2.5,-0.1201
Dylan Harper,1057262518,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.0098,0.3618,0.5,0.0795
Dylan Harper,1057262518,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.1779,0.2931,0.5,0.1161
Alex Caruso,89,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.545554886614488,0.0474,10.5,-0.1604

```

---

## `derek_game_snapshots/21713533/current_live/market_comparison.parquet`

- bytes: `101,343`
- rows: `39`
- columns: `111`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,cal_source,pmf_mean,p0,line,edge_over
De'Aaron Fox,161,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,16.904489304007225,0.0102,15.5,0.0547
De'Aaron Fox,161,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.492336972853852,0.0579,3.5,0.0786
Jalen Williams,38017703,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,15.767516562939168,0.0157,12.5,0.0973
Jalen Williams,38017703,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.625200320512819,0.0722,3.5,0.1405
Jalen Williams,38017703,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,4.218079775506114,0.0713,3.5,0.1145
Isaiah Hartenstein,201,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.004106981869176,0.0218,8.5,-0.0371
Cason Wallace,56677833,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,7.858647672552163,0.0434,8.5,-0.0933
Cason Wallace,56677833,OKC,SAS,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.1393647931069038,0.2407,2.5,-0.1272
Cason Wallace,56677833,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.0652000000000001,0.325,1.5,-0.1246
Jaylin Williams,38017706,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:bench,3.5937687838108587,0.1177,3.5,-0.0913
Jared McCain,1028027372,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,11.512320225284117,0.0472,13.5,-0.1382
Jared McCain,1028027372,OKC,SAS,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.5273527352735273,0.6351,0.5,-0.0665
Stephon Castle,1028025261,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,5.044266399599398,0.0417,5.5,-0.0655
Stephon Castle,1028025261,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,6.292138207310967,0.0303,6.5,-0.1046
Devin Vassell,3547246,SAS,OKC,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,12.936891742751078,0.0186,13.5,-0.0543
Devin Vassell,3547246,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,4.976555455365193,0.0476,4.5,0.0749
Devin Vassell,3547246,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,2.2150784921507847,0.1073,2.5,-0.1273
Devin Vassell,3547246,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.5194519451945192,0.2382,1.0,0.1784
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,26.076024569529746,0.0049,29.5,-0.1263
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:starter,1.009099090090991,0.3268,1.5,-0.1613
Luguentz Dort,666541,OKC,SAS,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,0.9872987298729876,0.3288,1.5,-0.1104
Julian Champagnie,38017649,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,5.411552707978775,0.0463,5.5,-0.0707
Julian Champagnie,38017649,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,2.091590840915908,0.1242,2.5,-0.081
Chet Holmgren,38017685,OKC,SAS,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,8.162960737179489,0.0184,7.5,0.0302
Chet Holmgren,38017685,OKC,SAS,21713533,blk,role_aware_pmf_cal_v1:monotone_inactive_global_v1:core,1.052905290529053,0.3933,1.5,-0.182
Dylan Harper,1057262518,SAS,OKC,21713533,reb,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,4.582273410115173,0.0606,3.5,0.0814
Dylan Harper,1057262518,SAS,OKC,21713533,ast,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,2.246266412749323,0.2075,2.5,-0.1201
Dylan Harper,1057262518,SAS,OKC,21713533,fg3m,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.0098,0.3618,0.5,0.0795
Dylan Harper,1057262518,SAS,OKC,21713533,stl,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,1.1779,0.2931,0.5,0.1161
Alex Caruso,89,OKC,SAS,21713533,pts,role_aware_pmf_cal_v1:monotone_inactive_global_v1:rotation,8.545554886614488,0.0474,10.5,-0.1604

```

---

## `derek_game_snapshots/21713533/current_live/outcome_level_probabilities.csv`

- bytes: `130,040`
- rows: `682`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21713533,pts,0,0.0102,15.5,current_live
De'Aaron Fox,161,21713533,pts,1,0.012,15.5,current_live
De'Aaron Fox,161,21713533,pts,2,0.011,15.5,current_live
De'Aaron Fox,161,21713533,pts,3,0.0159,15.5,current_live
De'Aaron Fox,161,21713533,pts,4,0.0168,15.5,current_live
De'Aaron Fox,161,21713533,pts,5,0.0159,15.5,current_live
De'Aaron Fox,161,21713533,pts,6,0.0187,15.5,current_live
De'Aaron Fox,161,21713533,pts,7,0.0232,15.5,current_live
De'Aaron Fox,161,21713533,pts,8,0.0285,15.5,current_live
De'Aaron Fox,161,21713533,pts,9,0.0275,15.5,current_live
De'Aaron Fox,161,21713533,pts,10,0.0351,15.5,current_live
De'Aaron Fox,161,21713533,pts,11,0.035,15.5,current_live
De'Aaron Fox,161,21713533,pts,12,0.0353,15.5,current_live
De'Aaron Fox,161,21713533,pts,13,0.046,15.5,current_live
De'Aaron Fox,161,21713533,pts,14,0.0481,15.5,current_live
De'Aaron Fox,161,21713533,pts,15,0.0539,15.5,current_live
De'Aaron Fox,161,21713533,pts,16,0.0501,15.5,current_live
De'Aaron Fox,161,21713533,pts,17,0.0533,15.5,current_live
De'Aaron Fox,161,21713533,pts,18,0.0556,15.5,current_live
De'Aaron Fox,161,21713533,pts,19,0.0516,15.5,current_live
De'Aaron Fox,161,21713533,pts,20,0.0476,15.5,current_live
De'Aaron Fox,161,21713533,pts,21,0.0382,15.5,current_live
De'Aaron Fox,161,21713533,pts,22,0.036,15.5,current_live
De'Aaron Fox,161,21713533,pts,23,0.0355,15.5,current_live
De'Aaron Fox,161,21713533,pts,24,0.0358,15.5,current_live
De'Aaron Fox,161,21713533,pts,25,0.0273,15.5,current_live
De'Aaron Fox,161,21713533,pts,26,0.0213,15.5,current_live
De'Aaron Fox,161,21713533,pts,27,0.0223,15.5,current_live
De'Aaron Fox,161,21713533,pts,28,0.0141,15.5,current_live
De'Aaron Fox,161,21713533,pts,29,0.0122,15.5,current_live

```

---

## `derek_game_snapshots/21713533/current_live/outcome_level_probabilities.parquet`

- bytes: `21,846`
- rows: `682`
- columns: `18`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,k,p_k,line,snapshot_type
De'Aaron Fox,161,21713533,pts,0,0.010244049412473637,15.5,current_live
De'Aaron Fox,161,21713533,pts,1,0.011951390981219242,15.5,current_live
De'Aaron Fox,161,21713533,pts,2,0.01104750426835392,15.5,current_live
De'Aaron Fox,161,21713533,pts,3,0.01586823340363563,15.5,current_live
De'Aaron Fox,161,21713533,pts,4,0.016772120116500953,15.5,current_live
De'Aaron Fox,161,21713533,pts,5,0.01586823340363563,15.5,current_live
De'Aaron Fox,161,21713533,pts,6,0.018680325399216626,15.5,current_live
De'Aaron Fox,161,21713533,pts,7,0.023199758963543232,15.5,current_live
De'Aaron Fox,161,21713533,pts,8,0.028522647383750124,15.5,current_live
De'Aaron Fox,161,21713533,pts,9,0.027518328813899765,15.5,current_live
De'Aaron Fox,161,21713533,pts,10,0.03505071808777744,15.5,current_live
De'Aaron Fox,161,21713533,pts,11,0.0349502862307924,15.5,current_live
De'Aaron Fox,161,21713533,pts,12,0.035251581801747506,15.5,current_live
De'Aaron Fox,161,21713533,pts,13,0.045997790499146325,15.5,current_live
De'Aaron Fox,161,21713533,pts,14,0.04810685949583207,15.5,current_live
De'Aaron Fox,161,21713533,pts,15,0.053931907200964135,15.5,current_live
De'Aaron Fox,161,21713533,pts,16,0.05011549663553278,15.5,current_live
De'Aaron Fox,161,21713533,pts,17,0.05332931605905392,15.5,current_live
De'Aaron Fox,161,21713533,pts,18,0.05563924876970974,15.5,current_live
De'Aaron Fox,161,21713533,pts,19,0.05162197449030832,15.5,current_live
De'Aaron Fox,161,21713533,pts,20,0.04760470021090689,15.5,current_live
De'Aaron Fox,161,21713533,pts,21,0.038164105654313545,15.5,current_live
De'Aaron Fox,161,21713533,pts,22,0.035954604800642755,15.5,current_live
De'Aaron Fox,161,21713533,pts,23,0.03545244551571758,15.5,current_live
De'Aaron Fox,161,21713533,pts,24,0.03575374108667269,15.5,current_live
De'Aaron Fox,161,21713533,pts,25,0.027317465099929692,15.5,current_live
De'Aaron Fox,161,21713533,pts,26,0.021291553680827555,15.5,current_live
De'Aaron Fox,161,21713533,pts,27,0.022295872250677914,15.5,current_live
De'Aaron Fox,161,21713533,pts,28,0.01406045997790499,15.5,current_live
De'Aaron Fox,161,21713533,pts,29,0.012152254695189312,15.5,current_live

```

---

## `derek_game_snapshots/21713533/current_live/pmf_driver_decomposition.csv`

- bytes: `3,391`
- rows: `16`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21713533,pts,15.5
Jalen Williams,38017703,OKC,21713533,pts,12.5
Isaiah Hartenstein,201,OKC,21713533,reb,8.5
Cason Wallace,56677833,OKC,21713533,pts,8.5
Jaylin Williams,38017706,OKC,21713533,reb,3.5
Jared McCain,1028027372,OKC,21713533,pts,13.5
Stephon Castle,1028025261,SAS,21713533,reb,5.5
Devin Vassell,3547246,SAS,21713533,pts,13.5
Shai Gilgeous-Alexander,175,OKC,21713533,pts,29.5
Luguentz Dort,666541,OKC,21713533,fg3m,1.5
Julian Champagnie,38017649,SAS,21713533,reb,5.5
Chet Holmgren,38017685,OKC,21713533,reb,7.5
Dylan Harper,1057262518,SAS,21713533,reb,3.5
Alex Caruso,89,OKC,21713533,pts,10.5
Keldon Johnson,666682,SAS,21713533,fg3m,0.5
Victor Wembanyama,56677822,SAS,21713533,pts,27.5

```

---

## `derek_game_snapshots/21713533/current_live/pmf_driver_decomposition.parquet`

- bytes: `16,590`
- rows: `16`
- columns: `21`

Compact first 30 rows:

```csv
player_name,player_id,team,game_id,stat,line
De'Aaron Fox,161,SAS,21713533,pts,15.5
Jalen Williams,38017703,OKC,21713533,pts,12.5
Isaiah Hartenstein,201,OKC,21713533,reb,8.5
Cason Wallace,56677833,OKC,21713533,pts,8.5
Jaylin Williams,38017706,OKC,21713533,reb,3.5
Jared McCain,1028027372,OKC,21713533,pts,13.5
Stephon Castle,1028025261,SAS,21713533,reb,5.5
Devin Vassell,3547246,SAS,21713533,pts,13.5
Shai Gilgeous-Alexander,175,OKC,21713533,pts,29.5
Luguentz Dort,666541,OKC,21713533,fg3m,1.5
Julian Champagnie,38017649,SAS,21713533,reb,5.5
Chet Holmgren,38017685,OKC,21713533,reb,7.5
Dylan Harper,1057262518,SAS,21713533,reb,3.5
Alex Caruso,89,OKC,21713533,pts,10.5
Keldon Johnson,666682,SAS,21713533,fg3m,0.5
Victor Wembanyama,56677822,SAS,21713533,pts,27.5

```

---

## `derek_game_snapshots/21713533/current_live/prediction_input_audit.csv`

- bytes: `2,776`
- rows: `39`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,OKC,21713533,pts,15.5
De'Aaron Fox,161,SAS,OKC,21713533,reb,3.5
Jalen Williams,38017703,OKC,SAS,21713533,pts,12.5
Jalen Williams,38017703,OKC,SAS,21713533,reb,3.5
Jalen Williams,38017703,OKC,SAS,21713533,ast,3.5
Isaiah Hartenstein,201,OKC,SAS,21713533,reb,8.5
Cason Wallace,56677833,OKC,SAS,21713533,pts,8.5
Cason Wallace,56677833,OKC,SAS,21713533,ast,2.5
Cason Wallace,56677833,OKC,SAS,21713533,fg3m,1.5
Jaylin Williams,38017706,OKC,SAS,21713533,reb,3.5
Jared McCain,1028027372,OKC,SAS,21713533,pts,13.5
Jared McCain,1028027372,OKC,SAS,21713533,stl,0.5
Stephon Castle,1028025261,SAS,OKC,21713533,reb,5.5
Stephon Castle,1028025261,SAS,OKC,21713533,ast,6.5
Devin Vassell,3547246,SAS,OKC,21713533,pts,13.5
Devin Vassell,3547246,SAS,OKC,21713533,reb,4.5
Devin Vassell,3547246,SAS,OKC,21713533,fg3m,2.5
Devin Vassell,3547246,SAS,OKC,21713533,stl,1.0
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,29.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713533,fg3m,1.5
Julian Champagnie,38017649,SAS,OKC,21713533,reb,5.5
Julian Champagnie,38017649,SAS,OKC,21713533,fg3m,2.5
Chet Holmgren,38017685,OKC,SAS,21713533,reb,7.5
Chet Holmgren,38017685,OKC,SAS,21713533,blk,1.5
Dylan Harper,1057262518,SAS,OKC,21713533,reb,3.5
Dylan Harper,1057262518,SAS,OKC,21713533,ast,2.5
Dylan Harper,1057262518,SAS,OKC,21713533,fg3m,0.5
Dylan Harper,1057262518,SAS,OKC,21713533,stl,0.5
Alex Caruso,89,OKC,SAS,21713533,pts,10.5

```

---

## `derek_game_snapshots/21713533/current_live/prediction_input_audit.parquet`

- bytes: `6,079`
- rows: `39`
- columns: `8`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,OKC,21713533,pts,15.5
De'Aaron Fox,161,SAS,OKC,21713533,reb,3.5
Jalen Williams,38017703,OKC,SAS,21713533,pts,12.5
Jalen Williams,38017703,OKC,SAS,21713533,reb,3.5
Jalen Williams,38017703,OKC,SAS,21713533,ast,3.5
Isaiah Hartenstein,201,OKC,SAS,21713533,reb,8.5
Cason Wallace,56677833,OKC,SAS,21713533,pts,8.5
Cason Wallace,56677833,OKC,SAS,21713533,ast,2.5
Cason Wallace,56677833,OKC,SAS,21713533,fg3m,1.5
Jaylin Williams,38017706,OKC,SAS,21713533,reb,3.5
Jared McCain,1028027372,OKC,SAS,21713533,pts,13.5
Jared McCain,1028027372,OKC,SAS,21713533,stl,0.5
Stephon Castle,1028025261,SAS,OKC,21713533,reb,5.5
Stephon Castle,1028025261,SAS,OKC,21713533,ast,6.5
Devin Vassell,3547246,SAS,OKC,21713533,pts,13.5
Devin Vassell,3547246,SAS,OKC,21713533,reb,4.5
Devin Vassell,3547246,SAS,OKC,21713533,fg3m,2.5
Devin Vassell,3547246,SAS,OKC,21713533,stl,1.0
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,29.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713533,fg3m,1.5
Julian Champagnie,38017649,SAS,OKC,21713533,reb,5.5
Julian Champagnie,38017649,SAS,OKC,21713533,fg3m,2.5
Chet Holmgren,38017685,OKC,SAS,21713533,reb,7.5
Chet Holmgren,38017685,OKC,SAS,21713533,blk,1.5
Dylan Harper,1057262518,SAS,OKC,21713533,reb,3.5
Dylan Harper,1057262518,SAS,OKC,21713533,ast,2.5
Dylan Harper,1057262518,SAS,OKC,21713533,fg3m,0.5
Dylan Harper,1057262518,SAS,OKC,21713533,stl,0.5
Alex Caruso,89,OKC,SAS,21713533,pts,10.5

```

---

## `derek_game_snapshots/21713533/current_live/prop_summary.csv`

- bytes: `2,062`
- rows: `39`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,OKC,21713533,pts,15.5
De'Aaron Fox,161,SAS,OKC,21713533,reb,3.5
Jalen Williams,38017703,OKC,SAS,21713533,pts,12.5
Jalen Williams,38017703,OKC,SAS,21713533,reb,3.5
Jalen Williams,38017703,OKC,SAS,21713533,ast,3.5
Isaiah Hartenstein,201,OKC,SAS,21713533,reb,8.5
Cason Wallace,56677833,OKC,SAS,21713533,pts,8.5
Cason Wallace,56677833,OKC,SAS,21713533,ast,2.5
Cason Wallace,56677833,OKC,SAS,21713533,fg3m,1.5
Jaylin Williams,38017706,OKC,SAS,21713533,reb,3.5
Jared McCain,1028027372,OKC,SAS,21713533,pts,13.5
Jared McCain,1028027372,OKC,SAS,21713533,stl,0.5
Stephon Castle,1028025261,SAS,OKC,21713533,reb,5.5
Stephon Castle,1028025261,SAS,OKC,21713533,ast,6.5
Devin Vassell,3547246,SAS,OKC,21713533,pts,13.5
Devin Vassell,3547246,SAS,OKC,21713533,reb,4.5
Devin Vassell,3547246,SAS,OKC,21713533,fg3m,2.5
Devin Vassell,3547246,SAS,OKC,21713533,stl,1.0
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,29.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713533,fg3m,1.5
Julian Champagnie,38017649,SAS,OKC,21713533,reb,5.5
Julian Champagnie,38017649,SAS,OKC,21713533,fg3m,2.5
Chet Holmgren,38017685,OKC,SAS,21713533,reb,7.5
Chet Holmgren,38017685,OKC,SAS,21713533,blk,1.5
Dylan Harper,1057262518,SAS,OKC,21713533,reb,3.5
Dylan Harper,1057262518,SAS,OKC,21713533,ast,2.5
Dylan Harper,1057262518,SAS,OKC,21713533,fg3m,0.5
Dylan Harper,1057262518,SAS,OKC,21713533,stl,0.5
Alex Caruso,89,OKC,SAS,21713533,pts,10.5

```

---

## `derek_game_snapshots/21713533/current_live/prop_summary.parquet`

- bytes: `5,397`
- rows: `39`
- columns: `7`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,line
De'Aaron Fox,161,SAS,OKC,21713533,pts,15.5
De'Aaron Fox,161,SAS,OKC,21713533,reb,3.5
Jalen Williams,38017703,OKC,SAS,21713533,pts,12.5
Jalen Williams,38017703,OKC,SAS,21713533,reb,3.5
Jalen Williams,38017703,OKC,SAS,21713533,ast,3.5
Isaiah Hartenstein,201,OKC,SAS,21713533,reb,8.5
Cason Wallace,56677833,OKC,SAS,21713533,pts,8.5
Cason Wallace,56677833,OKC,SAS,21713533,ast,2.5
Cason Wallace,56677833,OKC,SAS,21713533,fg3m,1.5
Jaylin Williams,38017706,OKC,SAS,21713533,reb,3.5
Jared McCain,1028027372,OKC,SAS,21713533,pts,13.5
Jared McCain,1028027372,OKC,SAS,21713533,stl,0.5
Stephon Castle,1028025261,SAS,OKC,21713533,reb,5.5
Stephon Castle,1028025261,SAS,OKC,21713533,ast,6.5
Devin Vassell,3547246,SAS,OKC,21713533,pts,13.5
Devin Vassell,3547246,SAS,OKC,21713533,reb,4.5
Devin Vassell,3547246,SAS,OKC,21713533,fg3m,2.5
Devin Vassell,3547246,SAS,OKC,21713533,stl,1.0
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,29.5
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,1.5
Luguentz Dort,666541,OKC,SAS,21713533,fg3m,1.5
Julian Champagnie,38017649,SAS,OKC,21713533,reb,5.5
Julian Champagnie,38017649,SAS,OKC,21713533,fg3m,2.5
Chet Holmgren,38017685,OKC,SAS,21713533,reb,7.5
Chet Holmgren,38017685,OKC,SAS,21713533,blk,1.5
Dylan Harper,1057262518,SAS,OKC,21713533,reb,3.5
Dylan Harper,1057262518,SAS,OKC,21713533,ast,2.5
Dylan Harper,1057262518,SAS,OKC,21713533,fg3m,0.5
Dylan Harper,1057262518,SAS,OKC,21713533,stl,0.5
Alex Caruso,89,OKC,SAS,21713533,pts,10.5

```

---

## `derek_game_snapshots/21713533/morning/full_pmf_wide.csv`

- bytes: `342,022`
- rows: `168`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,reb,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,3.5112,3.5112,3,3,0.0496,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,ast,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,2.3355,2.3355,2,2,0.1449,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,fg3m,rotation,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,0.9241,0.9241,0,0,0.6426,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,tov,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,0.8282,0.8282,1,1,0.3501,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,stl,rotation,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,1.4206,1.4206,1,1,0.1029,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,blk,rotation,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,0.2793,0.2793,0,0,0.7948,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,stocks,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6614,20.1453,0.05,1.6999,1.6999,1,1,0.0818,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pa,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6614,20.1453,0.05,11.9957,11.9957,11,10,0.0047,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pr,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6614,20.1453,0.05,13.1713,13.1713,13,12,0.0016,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,ra,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6614,20.1453,0.05,5.8467,5.8467,6,6,0.0072,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pra,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.6614,20.1453,0.05,15.5068,15.5068,15,14,0.0002,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8328,32.6013,0.05,18.3923,18.3923,18,19,0.0011,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8328,32.6013,0.05,4.6895,4.6895,5,5,0.006,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8328,32.6013,0.05,6.1171,6.1171,6,6,0.0058,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8328,32.6013,0.05,1.7402,1.7402,1,1,0.226,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8328,32.6013,0.05,2.3533,2.3533,2,2,0.0797,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8328,32.6013,0.05,0.6647,0.6647,0,0,0.5389,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.8328,32.6013,0.05,0.2339,0.2339,0,0,0.8123,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8328,32.6013,0.05,0.8987,0.8987,1,0,0.4377,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8328,32.6013,0.05,24.5094,24.5094,24,24,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8328,32.6013,0.05,23.0818,23.0818,23,23,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8328,32.6013,0.05,10.8066,10.8066,11,11,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.8328,32.6013,0.05,29.1989,29.1989,29,29,0.0,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.0647,35.2109,0.05,28.358,28.358,28,28,0.0001,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.0647,35.2109,0.05,4.4988,4.4988,4,4,0.0046,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.0647,35.2109,0.05,8.4152,8.4152,8,9,0.0041,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.0647,35.2109,0.05,1.4257,1.4257,1,1,0.3097,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.0647,35.2109,0.05,2.9389,2.9389,3,3,0.0608,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.0647,35.2109,0.05,0.745,0.745,0,0,0.535,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z

```

---

## `derek_game_snapshots/21713533/morning/full_pmf_wide.parquet`

- bytes: `210,110`
- rows: `168`
- columns: `70`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,reb,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,3.511155937637162,3.511155937637162,3,3,0.04958629725521377,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,ast,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,2.335505396886386,2.3355053968863855,2,2,0.14491007045953241,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,fg3m,rotation,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,0.9240923844308195,0.9240923844308196,0,0,0.6426185772141156,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,tov,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,0.8282313495879146,0.8282313495879147,1,1,0.35005518469115027,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,stl,rotation,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,1.4205536958712344,1.4205536958712341,1,1,0.10286306553028067,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,blk,rotation,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,0.2793058116961172,0.2793058116961172,0,0,0.7947604478969069,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,stocks,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.66144330386411,20.145296856111514,0.050000000000000044,1.6998595075673517,1.6998595075673517,1,1,0.08175149603289475,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pa,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.66144330386411,20.145296856111514,0.050000000000000044,11.995666977432382,11.995666977432384,11,10,0.00465608508297654,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pr,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.66144330386411,20.145296856111514,0.050000000000000044,13.171317518183157,13.171317518183155,13,12,0.0015932503395926258,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,ra,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.66144330386411,20.145296856111514,0.050000000000000044,5.8466613345235166,5.8466613345235166,6,6,0.00718555382908035,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pra,rotation,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,20.66144330386411,20.145296856111514,0.050000000000000044,15.506822915069502,15.506822915069506,15,14,0.0002308780189700415,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.832835253330774,32.60130732037619,0.050000000000000044,18.392320498224503,18.3923204982245,18,19,0.0011259825860457753,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.832835253330774,32.60130732037619,0.050000000000000044,4.689526811738876,4.689526811738876,5,5,0.005955064618471946,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.832835253330774,32.60130732037619,0.050000000000000044,6.1170814359552175,6.1170814359552175,6,6,0.005798434451337963,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.832835253330774,32.60130732037619,0.050000000000000044,1.740190831007218,1.740190831007218,1,1,0.22602930800641674,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.832835253330774,32.60130732037619,0.050000000000000044,2.353294810552616,2.353294810552617,2,2,0.07972283205781037,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.832835253330774,32.60130732037619,0.050000000000000044,0.6647089604975196,0.6647089604975196,0,0,0.5388550592322852,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,29.832835253330774,32.60130732037619,0.050000000000000044,0.23394986512222554,0.23394986512222551,0,0,0.8122826789323478,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.832835253330774,32.60130732037619,0.050000000000000044,0.8986588256197452,0.898658825619745,1,0,0.4377026310694495,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.832835253330774,32.60130732037619,0.050000000000000044,24.509401934179724,24.509401934179706,24,24,6.5289362185344365e-06,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.832835253330774,32.60130732037619,0.050000000000000044,23.081847309963354,23.08184730996335,23,23,6.705299059176743e-06,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.832835253330774,32.60130732037619,0.050000000000000044,10.806608247694076,10.80660824769407,11,11,3.453005184369153e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
De'Aaron Fox,161,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,29.832835253330774,32.60130732037619,0.050000000000000044,29.198928745918582,29.19892874591858,29,29,3.888023707125446e-08,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.06468459714189,35.2108786950857,0.050000000000000044,28.35801160039275,28.358011600392746,28,28,7.443402870106976e-05,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.06468459714189,35.2108786950857,0.050000000000000044,4.4987571588535,4.498757158853499,4,4,0.004565563820361744,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.06468459714189,35.2108786950857,0.050000000000000044,8.415162817878887,8.415162817878887,8,9,0.004113770543504276,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.06468459714189,35.2108786950857,0.050000000000000044,1.4256664463698425,1.4256664463698423,1,1,0.30973629519598844,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.06468459714189,35.2108786950857,0.050000000000000044,2.9389238711707586,2.9389238711707586,3,3,0.06083945509441636,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,32.06468459714189,35.2108786950857,0.050000000000000044,0.7449818584301016,0.7449818584301016,0,0,0.5349895965305181,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z

```

---

## `derek_game_snapshots/21713533/morning/market_comparison.csv`

- bytes: `524,283`
- rows: `572`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,13.5,13.5,fanduel,0.247,194,-270,0.3179,-0.0709,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,12.5,12.5,fanduel,0.2905,154,-210,0.3676,-0.0771,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,11.5,11.5,fanduel,0.3403,124,-166,0.417,-0.0768,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,fanduel,0.3968,-106,-125,0.4808,-0.0841,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,fanduel,0.4636,-140,108,0.5482,-0.0846,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,8.5,8.5,fanduel,0.5355,-192,142,0.6141,-0.0786,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,7.5,7.5,fanduel,0.608,-260,188,0.6753,-0.0673,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,6.5,6.5,fanduel,0.6652,-340,235,0.7213,-0.0562,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,5.5,5.5,fanduel,0.7338,-500,320,0.7778,-0.0439,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,4.5,4.5,fanduel,0.8065,-850,470,0.8361,-0.0295,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,williamhill_us,0.3968,-113,-118,0.495,-0.0982,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,13.5,13.5,bovada,0.247,190,-260,0.3232,-0.0762,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,12.5,12.5,bovada,0.2905,145,-190,0.3839,-0.0934,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,11.5,11.5,bovada,0.3403,110,-145,0.4459,-0.1056,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,bovada,0.3968,-120,-110,0.5101,-0.1134,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,bovada,0.4636,-165,125,0.5835,-0.1199,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,8.5,8.5,bovada,0.5355,-230,170,0.653,-0.1175,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,betmgm,0.4636,-120,-110,0.5101,-0.0465,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,betrivers,0.3968,-103,-132,0.4714,-0.0746,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,betrivers,0.4636,-143,106,0.548,-0.0844,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,draftkings,0.3968,-115,-111,0.5042,-0.1074,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,fanduel,0.3968,-104,-122,0.4812,-0.0845,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,hardrockbet_az,0.3968,-120,-110,0.5101,-0.1134,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,hardrockbet,0.3968,-120,-110,0.5101,-0.1134,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,rebet,0.3968,-107,-119,0.4875,-0.0908,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,hardrockbet_fl,0.3968,-120,-110,0.5101,-0.1134,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,espnbet,0.4636,-145,110,0.5541,-0.0905,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,espnbet,0.3968,-105,-125,0.4797,-0.0829,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,11.5,11.5,espnbet,0.3403,120,-160,0.4248,-0.0846,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,betparx,0.3968,-103,-132,0.4714,-0.0746,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z

```

---

## `derek_game_snapshots/21713533/morning/market_comparison.parquet`

- bytes: `141,495`
- rows: `2,489`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,13.5,13.5,fanduel,0.2469993833853228,194,-270,0.31792404193160334,-0.0709246585462806,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,12.5,12.5,fanduel,0.29045387430110164,154,-210,0.3675598766895898,-0.07710600238848797,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,11.5,11.5,fanduel,0.3402684060743299,124,-166,0.4170324846356453,-0.07676407856131523,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,fanduel,0.39676248506705764,-106,-125,0.4808467741935484,-0.08408428912649063,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,9.5,9.5,fanduel,0.46359851619331355,-140,108,0.5481927710843374,-0.08459425489102373,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,8.5,8.5,fanduel,0.5354955503039253,-192,142,0.6140833157115669,-0.07858776540764156,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,7.5,7.5,fanduel,0.6079811330180461,-260,188,0.6753246753246753,-0.0673435423066292,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,6.5,6.5,fanduel,0.6651727723210704,-340,235,0.7213426219126029,-0.056169849591532484,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,5.5,5.5,fanduel,0.7338464993323638,-500,320,0.7777777777777778,-0.04393127844541389,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,4.5,4.5,fanduel,0.8065229248858093,-850,470,0.8360655737704918,-0.02954264888468261,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,williamhill_us,0.39676248506705764,-113,-118,0.4949766918501849,-0.09821420678312714,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,13.5,13.5,bovada,0.2469993833853228,190,-260,0.32315978456014366,-0.07616040117482092,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,12.5,12.5,bovada,0.29045387430110164,145,-190,0.3838517538054269,-0.0933978795043251,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,11.5,11.5,bovada,0.3402684060743299,110,-145,0.4458598726114649,-0.10559146653713486,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,bovada,0.39676248506705764,-120,-110,0.5101214574898786,-0.11335897242282084,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,9.5,9.5,bovada,0.46359851619331355,-165,125,0.5834970530451867,-0.11989853685187307,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,8.5,8.5,bovada,0.5354955503039253,-230,170,0.6529968454258674,-0.11750129512194207,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,9.5,9.5,betmgm,0.46359851619331355,-120,-110,0.5101214574898786,-0.046522941296564924,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,betrivers,0.39676248506705764,-103,-132,0.471395881006865,-0.07463339593980728,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,9.5,9.5,betrivers,0.46359851619331355,-143,106,0.5479742549946055,-0.08437573880129184,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,draftkings,0.39676248506705764,-115,-111,0.5041554124246831,-0.10739292735762535,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,fanduel,0.39676248506705764,-104,-122,0.48124062031015497,-0.08447813524309722,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,hardrockbet_az,0.39676248506705764,-120,-110,0.5101214574898786,-0.11335897242282084,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,hardrockbet,0.39676248506705764,-120,-110,0.5101214574898786,-0.11335897242282084,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,rebet,0.39676248506705764,-107,-119,0.487517163899638,-0.09075467883258026,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,hardrockbet_fl,0.39676248506705764,-120,-110,0.5101214574898786,-0.11335897242282084,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,9.5,9.5,espnbet,0.46359851619331355,-145,110,0.554140127388535,-0.09054161119522136,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,espnbet,0.39676248506705764,-105,-125,0.4796954314720812,-0.08293294640502347,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,11.5,11.5,espnbet,0.3402684060743299,120,-160,0.4248366013071895,-0.08456819523285941,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.66144330386411,20.145296856111514,0.050000000000000044,9.660161580545996,9.660161580545996,9,5,0.03213085928542695,10.5,10.5,betparx,0.39676248506705764,-103,-132,0.471395881006865,-0.07463339593980728,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z

```

---

## `derek_game_snapshots/21713533/morning/market_comparison_csv_parts/market_comparison_part_000.csv`

- bytes: `492,039`
- rows: `542`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,13.5,13.5,fanduel,0.247,194,-270,0.3179,-0.0709,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,12.5,12.5,fanduel,0.2905,154,-210,0.3676,-0.0771,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,11.5,11.5,fanduel,0.3403,124,-166,0.417,-0.0768,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,fanduel,0.3968,-106,-125,0.4808,-0.0841,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,fanduel,0.4636,-140,108,0.5482,-0.0846,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,8.5,8.5,fanduel,0.5355,-192,142,0.6141,-0.0786,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,7.5,7.5,fanduel,0.608,-260,188,0.6753,-0.0673,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,6.5,6.5,fanduel,0.6652,-340,235,0.7213,-0.0562,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,5.5,5.5,fanduel,0.7338,-500,320,0.7778,-0.0439,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,4.5,4.5,fanduel,0.8065,-850,470,0.8361,-0.0295,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,williamhill_us,0.3968,-113,-118,0.495,-0.0982,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,13.5,13.5,bovada,0.247,190,-260,0.3232,-0.0762,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,12.5,12.5,bovada,0.2905,145,-190,0.3839,-0.0934,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,11.5,11.5,bovada,0.3403,110,-145,0.4459,-0.1056,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,bovada,0.3968,-120,-110,0.5101,-0.1134,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,bovada,0.4636,-165,125,0.5835,-0.1199,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,8.5,8.5,bovada,0.5355,-230,170,0.653,-0.1175,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,betmgm,0.4636,-120,-110,0.5101,-0.0465,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,betrivers,0.3968,-103,-132,0.4714,-0.0746,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,betrivers,0.4636,-143,106,0.548,-0.0844,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,draftkings,0.3968,-115,-111,0.5042,-0.1074,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,fanduel,0.3968,-104,-122,0.4812,-0.0845,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,hardrockbet_az,0.3968,-120,-110,0.5101,-0.1134,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,hardrockbet,0.3968,-120,-110,0.5101,-0.1134,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,rebet,0.3968,-107,-119,0.4875,-0.0908,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,hardrockbet_fl,0.3968,-120,-110,0.5101,-0.1134,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,9.5,9.5,espnbet,0.4636,-145,110,0.5541,-0.0905,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,espnbet,0.3968,-105,-125,0.4797,-0.0829,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,11.5,11.5,espnbet,0.3403,120,-160,0.4248,-0.0846,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:rotation+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,20.6614,20.1453,0.05,9.6602,9.6602,9,5,0.0321,10.5,10.5,betparx,0.3968,-103,-132,0.4714,-0.0746,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z

```

---

## `derek_game_snapshots/21713533/morning/market_comparison_csv_parts/market_comparison_part_001.csv`

- bytes: `509,225`
- rows: `542`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,1.2136,1.2136,1,0,0.3684,2.5,2.5,hardrockbet,0.1553,130,-190,0.3989,-0.2436,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,1.2136,1.2136,1,0,0.3684,2.5,2.5,hardrockbet_fl,0.1553,130,-190,0.3989,-0.2436,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,1.2136,1.2136,1,0,0.3684,2.5,2.5,betparx,0.1553,138,-186,0.3925,-0.2372,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,37.5,37.5,fanduel,0.4526,-120,-110,0.5101,-0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,37.5,37.5,fanduel,0.4526,-118,-110,0.5082,-0.0556,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,38.5,38.5,bovada,0.3983,-105,-125,0.4797,-0.0814,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,37.5,37.5,bovada,0.4526,-125,-105,0.5203,-0.0677,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,36.5,36.5,bovada,0.5076,-145,110,0.5541,-0.0465,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,37.5,37.5,betmgm,0.4526,-115,-118,0.497,-0.0444,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,38.5,38.5,draftkings,0.3983,-107,-123,0.4838,-0.0855,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,37.5,37.5,hardrockbet_az,0.4526,-120,-110,0.5101,-0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,37.5,37.5,hardrockbet,0.4526,-120,-110,0.5101,-0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,37.5,37.5,hardrockbet_fl,0.4526,-120,-110,0.5101,-0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,37.5,37.5,espnbet,0.4526,-120,-110,0.5101,-0.0575,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,36.7732,36.7732,37,37,0.0,37.5,37.5,fliff,0.4526,-125,-115,0.5095,-0.0569,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,33.5,33.5,fanduel,0.4547,-113,-113,0.5,-0.0453,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,33.5,33.5,fanduel,0.4547,-114,-114,0.5,-0.0453,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,33.5,33.5,betmgm,0.4547,-105,-125,0.4797,-0.025,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,34.5,34.5,draftkings,0.3971,-106,-124,0.4817,-0.0847,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,34.5,34.5,bovada,0.3971,-105,-125,0.4797,-0.0826,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,33.5,33.5,bovada,0.4547,-125,-105,0.5203,-0.0656,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,32.5,32.5,bovada,0.5142,-150,115,0.5633,-0.0492,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,33.5,33.5,hardrockbet_az,0.4547,-115,-115,0.5,-0.0453,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,33.5,33.5,hardrockbet,0.4547,-115,-115,0.5,-0.0453,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,33.5,33.5,hardrockbet_fl,0.4547,-115,-115,0.5,-0.0453,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,33.5,33.5,espnbet,0.4547,-115,-115,0.5,-0.0453,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,32.8568,32.8568,33,33,0.0,33.5,33.5,fliff,0.4547,-120,-120,0.5,-0.0453,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,12.9139,12.9139,13,13,0.0,11.5,11.5,fanduel,0.7027,104,-138,0.4581,0.2446,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,12.9139,12.9139,13,13,0.0,12.5,12.5,fanduel,0.5648,102,-130,0.4669,0.0979,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,32.0647,35.2109,0.05,12.9139,12.9139,13,13,0.0,11.5,11.5,betmgm,0.7027,-145,105,0.5482,0.1545,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z

```

---

## `derek_game_snapshots/21713533/morning/market_comparison_csv_parts/market_comparison_part_002.csv`

- bytes: `493,029`
- rows: `542`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,6.5,6.5,fanduel,0.8101,-330,230,0.7169,0.0931,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,5.5,5.5,fanduel,0.8524,-550,350,0.792,0.0604,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,13.5,13.5,fanduel,0.403,240,-350,0.2744,0.1286,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,9.5,9.5,fanduel,0.6449,-120,-106,0.5146,0.1303,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,9.5,9.5,williamhill_us,0.6449,-127,-105,0.5221,0.1228,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,fanduel,0.5886,-108,-122,0.4858,0.1028,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,7.5,7.5,bovada,0.7543,-240,175,0.66,0.0943,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,8.5,8.5,bovada,0.6995,-165,125,0.5835,0.116,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,bovada,0.5886,115,-150,0.4367,0.1519,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,12.5,12.5,bovada,0.4615,200,-275,0.3125,0.149,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,11.5,11.5,bovada,0.5182,150,-200,0.375,0.1432,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,9.5,9.5,bovada,0.6449,-120,-110,0.5101,0.1348,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,betmgm,0.5886,-105,-125,0.4797,0.1089,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,betrivers,0.5886,100,-136,0.4646,0.124,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,9.5,9.5,betrivers,0.6449,-132,-104,0.5274,0.1175,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,9.5,9.5,draftkings,0.6449,-118,-108,0.5104,0.1345,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,hardrockbet_az,0.5886,-110,-120,0.4899,0.0987,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,hardrockbet,0.5886,-110,-120,0.4899,0.0987,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,9.5,9.5,rebet,0.6449,-133,104,0.538,0.1069,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,hardrockbet_fl,0.5886,-110,-120,0.4899,0.0987,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,8.5,8.5,espnbet,0.6995,-190,140,0.6113,0.0882,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,9.5,9.5,espnbet,0.6449,-130,100,0.5306,0.1143,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,espnbet,0.5886,-105,-125,0.4797,0.1089,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,9.5,9.5,betparx,0.6449,-132,100,0.5323,0.1126,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,betparx,0.5886,102,-136,0.4621,0.1265,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,12.5882,12.5882,12,11,0.0129,10.5,10.5,fliff,0.5886,-110,-130,0.481,0.1076,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,reb,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,6.0068,6.0068,6,6,0.0082,5.5,5.5,williamhill_us,0.5801,-125,-110,0.5147,0.0654,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,reb,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,6.0068,6.0068,6,6,0.0082,5.5,5.5,fanduel,0.5801,-112,-118,0.4939,0.0862,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,reb,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,6.0068,6.0068,6,6,0.0082,5.5,5.5,fanduel,0.5801,-113,-113,0.5,0.0801,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Julian Champagnie,38017649,SAS,OKC,21713533,reb,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.4443,30.0678,0.05,6.0068,6.0068,6,6,0.0082,7.5,7.5,fanduel,0.2537,300,-450,0.234,0.0196,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z

```

---

## `derek_game_snapshots/21713533/morning/market_comparison_csv_parts/market_comparison_part_003.csv`

- bytes: `502,480`
- rows: `542`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Victor Wembanyama,56677822,SAS,OKC,21713533,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,24.9632,24.9632,25,25,0.0001,26.5,26.5,espnbet,0.3909,-160,120,0.5752,-0.1842,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,24.9632,24.9632,25,25,0.0001,26.5,26.5,betparx,0.3909,-150,110,0.5575,-0.1666,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,24.9632,24.9632,25,25,0.0001,27.5,27.5,betparx,0.342,-120,-110,0.5101,-0.1681,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,24.9632,24.9632,25,25,0.0001,28.5,28.5,betparx,0.3018,104,-137,0.4589,-0.1571,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,24.9632,24.9632,25,25,0.0001,28.5,28.5,fliff,0.3018,-115,-125,0.4905,-0.1888,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,williamhill_us,0.4536,-125,-110,0.5147,-0.0611,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,13.5,13.5,fanduel,0.3262,100,-132,0.4677,-0.1415,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,fanduel,0.4536,-125,-102,0.5239,-0.0702,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,16.5,16.5,fanduel,0.0957,430,-750,0.1762,-0.0804,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,15.5,15.5,fanduel,0.158,300,-440,0.2348,-0.0767,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,13.5,13.5,fanduel,0.3262,126,-162,0.4171,-0.0909,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,fanduel,0.4536,-128,-104,0.5241,-0.0704,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,11.5,11.5,fanduel,0.6304,-205,154,0.6306,-0.0002,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,10.5,10.5,fanduel,0.7493,-340,235,0.7213,0.0279,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,9.5,9.5,fanduel,0.8402,-620,390,0.8084,0.0318,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,14.5,14.5,fanduel,0.2319,188,-260,0.3247,-0.0928,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,13.5,13.5,betmgm,0.3262,115,-155,0.4335,-0.1073,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,betrivers,0.4536,-132,-104,0.5274,-0.0738,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,fanatics,0.4536,-115,-115,0.5,-0.0464,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,draftkings,0.4536,-120,-109,0.5112,-0.0576,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,14.5,14.5,bovada,0.2319,175,-240,0.34,-0.1081,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,13.5,13.5,bovada,0.3262,120,-160,0.4248,-0.0986,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,bovada,0.4536,-125,-105,0.5203,-0.0667,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,11.5,11.5,bovada,0.6304,-190,145,0.6161,0.0142,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,hardrockbet_az,0.4536,-130,100,0.5306,-0.077,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,hardrockbet,0.4536,-130,100,0.5306,-0.077,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,hardrockbet_fl,0.4536,-130,100,0.5306,-0.077,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,rebet,0.4536,-119,-107,0.5125,-0.0588,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,betparx,0.4536,-132,100,0.5323,-0.0786,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Victor Wembanyama,56677822,SAS,OKC,21713533,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.7275,35.1016,0.05,12.3604,12.3604,12,12,0.0016,12.5,12.5,fliff,0.4536,-135,-110,0.5231,-0.0694,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z

```

---

## `derek_game_snapshots/21713533/morning/market_comparison_csv_parts/market_comparison_part_004.csv`

- bytes: `307,605`
- rows: `321`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,34.5,34.5,fanduel,0.2706,230,-330,0.2831,-0.0125,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,33.5,33.5,fanduel,0.3217,188,-260,0.3247,-0.003,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,32.5,32.5,fanduel,0.3772,154,-210,0.3676,0.0096,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,31.5,31.5,fanduel,0.4357,126,-168,0.4138,0.0219,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,30.5,30.5,fanduel,0.4959,104,-138,0.4581,0.0378,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,fanduel,0.5562,-118,-112,0.5061,0.0502,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,28.5,28.5,fanduel,0.615,-152,114,0.5635,0.0516,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,27.5,27.5,fanduel,0.671,-192,142,0.6141,0.0569,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,26.5,26.5,fanduel,0.7231,-240,174,0.6592,0.0639,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,25.5,25.5,fanduel,0.7704,-300,210,0.6992,0.0712,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,24.5,24.5,fanduel,0.8126,-400,270,0.7475,0.0651,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,23.5,23.5,fanduel,0.8494,-500,320,0.7778,0.0716,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,22.5,22.5,fanduel,0.8809,-700,410,0.8169,0.064,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,betmgm,0.5562,-120,-110,0.5101,0.0461,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,30.5,30.5,betrivers,0.4959,-103,-134,0.4698,0.0262,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,betrivers,0.5562,-127,-107,0.5198,0.0365,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,28.5,28.5,betrivers,0.615,-165,118,0.5758,0.0392,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,draftkings,0.5562,-121,-109,0.5122,0.0441,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,31.5,31.5,bovada,0.4357,120,-160,0.4248,0.0109,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,30.5,30.5,bovada,0.4959,100,-130,0.4694,0.0266,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,bovada,0.5562,-120,-110,0.5101,0.0461,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,27.5,27.5,bovada,0.671,-170,130,0.5915,0.0795,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,28.5,28.5,bovada,0.615,-145,110,0.5541,0.0609,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,hardrockbet_az,0.5562,-120,-110,0.5101,0.0461,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,hardrockbet,0.5562,-120,-110,0.5101,0.0461,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,hardrockbet_fl,0.5562,-120,-110,0.5101,0.0461,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,30.5,30.5,betparx,0.4959,100,-134,0.4661,0.0298,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,espnbet,0.5562,-120,-110,0.5101,0.0461,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,28.5,28.5,betparx,0.615,-165,118,0.5758,0.0392,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z
Stephon Castle,1028025261,SAS,OKC,21713533,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,28.9303,31.0388,0.05,30.6024,30.6024,30,30,0.0,29.5,29.5,betparx,0.5562,-127,-106,0.5209,0.0353,latest_valid_report_selected,bdl_plus_nba_official,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-28T23:09:49Z

```

---

## `derek_game_snapshots/21713533/morning/outcome_level_probabilities.csv`

- bytes: `524,198`
- rows: `5,281`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Alex Caruso,89,21713533,pts,rotation,0,0.0321,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,1,0.0423,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,2,0.0277,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,3,0.0379,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,4,0.0535,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,5,0.0727,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,6,0.0687,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,7,0.0572,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,8,0.0725,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,9,0.0719,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,10,0.0668,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,11,0.0565,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,12,0.0498,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,13,0.0435,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,14,0.0388,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,15,0.0457,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,16,0.037,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,17,0.025,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,18,0.0175,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,19,0.0227,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,20,0.0109,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,21,0.0111,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,22,0.0128,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,23,0.0075,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,24,0.0078,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,25,0.0029,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,26,0.0012,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,27,0.002,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,28,0.0006,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,29,0.0004,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21713533/morning/outcome_level_probabilities.parquet`

- bytes: `69,341`
- rows: `5,931`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Alex Caruso,89,21713533,pts,rotation,0,0.032130859285426944,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,1,0.042289111299515014,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,2,0.027655132632304544,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,3,0.037889290913127156,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,4,0.053512680983816986,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,5,0.07267642555344549,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,6,0.06867372701129336,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,7,0.05719163930302425,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,8,0.07248558271412073,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,9,0.07189703411061175,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,10,0.06683603112625591,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,11,0.056494078992727674,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,12,0.04981453177322826,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,13,0.04345449091577903,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,14,0.038814329208104494,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,15,0.045715291381323526,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,16,0.037007341078441565,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,17,0.024951722684589756,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,18,0.017540389072665603,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,19,0.02272148533651392,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,20,0.010869291893356609,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,21,0.01105041213190506,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,22,0.012785774700412304,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,23,0.007493605836100857,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,24,0.0078016977547789535,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,25,0.002889329690409694,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,26,0.001214180181170691,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,27,0.0020429773847559164,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,28,0.0006115361490855356,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,29,0.00038811773333467743,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21713533/morning/outcome_level_probabilities_csv_parts/outcome_level_probabilities_part_000.csv`

- bytes: `455,000`
- rows: `4,610`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Alex Caruso,89,21713533,pts,rotation,0,0.0321,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,1,0.0423,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,2,0.0277,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,3,0.0379,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,4,0.0535,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,5,0.0727,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,6,0.0687,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,7,0.0572,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,8,0.0725,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,9,0.0719,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,10,0.0668,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,11,0.0565,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,12,0.0498,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,13,0.0435,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,14,0.0388,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,15,0.0457,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,16,0.037,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,17,0.025,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,18,0.0175,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,19,0.0227,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,20,0.0109,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,21,0.0111,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,22,0.0128,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,23,0.0075,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,24,0.0078,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,25,0.0029,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,26,0.0012,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,27,0.002,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,28,0.0006,latest_valid_report_selected,projected
Alex Caruso,89,21713533,pts,rotation,29,0.0004,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21713533/morning/outcome_level_probabilities_csv_parts/outcome_level_probabilities_part_001.csv`

- bytes: `135,790`
- rows: `1,321`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Stephon Castle,1028025261,21713533,pts,starter,3,0.0029,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,4,0.0038,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,5,0.0061,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,6,0.0099,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,7,0.0103,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,8,0.017,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,9,0.023,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,10,0.0263,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,11,0.028,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,12,0.0301,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,13,0.045,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,14,0.0493,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,15,0.0613,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,16,0.0623,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,17,0.0537,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,18,0.0616,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,19,0.0889,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,20,0.0614,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,21,0.054,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,22,0.0546,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,23,0.0441,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,24,0.0504,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,25,0.0348,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,26,0.0161,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,27,0.0213,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,28,0.0177,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,29,0.0077,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,30,0.0109,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,31,0.0098,latest_valid_report_selected,projected
Stephon Castle,1028025261,21713533,pts,starter,32,0.004,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21713533/morning/prop_summary.csv`

- bytes: `27,061`
- rows: `168`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,9.6602,10.5,10.5,betparx,0.3968,-103.0,-132.0,0.4714,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,reb,rotation,3.5112,3.5,3.5,betmgm,0.4883,105.0,-145.0,0.4518,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,ast,rotation,2.3355,2.5,2.5,betmgm,0.4381,120.0,-160.0,0.4248,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,fg3m,rotation,0.9241,1.5,1.5,betmgm,0.2806,-150.0,110.0,0.5575,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,tov,rotation,0.8282,,,,,,,,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,stl,rotation,1.4206,1.5,1.5,betparx,0.3829,-110.0,-120.0,0.4899,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,blk,rotation,0.2793,0.5,0.5,betparx,0.2052,123.0,-165.0,0.4187,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,stocks,rotation,1.6999,2.5,2.5,betparx,0.2152,148.0,-200.0,0.3769,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,pa,rotation,11.9957,12.5,12.5,bovada,0.426,-125.0,-105.0,0.5203,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,pr,rotation,13.1713,13.5,13.5,bovada,0.4389,-125.0,-105.0,0.5203,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,ra,rotation,5.8467,5.5,5.5,bovada,0.5452,-115.0,-115.0,0.5,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,pra,rotation,15.5068,16.5,16.5,betparx,0.4041,106.0,-143.0,0.452,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,pts,starter,18.3923,15.5,15.5,betparx,0.6909,-120.0,-112.0,0.508,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,reb,starter,4.6895,3.5,3.5,betmgm,0.7616,-140.0,105.0,0.5446,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,ast,starter,6.1171,5.5,5.5,betmgm,0.6131,-140.0,105.0,0.5446,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,fg3m,starter,1.7402,1.5,1.5,betmgm,0.4963,-105.0,-125.0,0.4797,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,tov,starter,2.3533,,,,,,,,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,stl,starter,0.6647,0.5,0.5,fanduel,0.4611,-245.0,178.0,0.6638,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,blk,starter,0.2339,0.5,0.5,betmgm,0.1877,240.0,-375.0,0.2714,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,stocks,starter,0.8987,1.5,1.5,draftkings,0.2351,122.0,-163.0,0.4209,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,pa,starter,24.5094,21.5,21.5,betmgm,0.6856,-120.0,-110.0,0.5101,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,pr,starter,23.0818,19.5,19.5,betmgm,0.7199,-118.0,-110.0,0.5082,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,ra,starter,10.8066,9.5,9.5,betmgm,0.6897,-110.0,-120.0,0.4899,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,pra,starter,29.1989,25.5,25.5,betmgm,0.7156,-120.0,-110.0,0.5101,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,starter,28.358,29.5,29.5,betparx,0.4163,-109.0,-121.0,0.4878,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,reb,starter,4.4988,3.5,3.5,betmgm,0.7675,-145.0,110.0,0.5541,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,ast,starter,8.4152,7.5,7.5,betmgm,0.6469,-150.0,110.0,0.5575,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,starter,1.4257,1.5,1.5,betmgm,0.3262,105.0,-140.0,0.4554,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,tov,starter,2.9389,,,,,,,,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,stl,starter,0.745,1.5,1.5,betparx,0.2021,123.0,-165.0,0.4187,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/21713533/morning/prop_summary.parquet`

- bytes: `18,862`
- rows: `168`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
Alex Caruso,89,OKC,SAS,21713533,pts,rotation,9.660161580545996,10.5,10.5,betparx,0.39676248506705764,-103.0,-132.0,0.471395881006865,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,reb,rotation,3.511155937637162,3.5,3.5,betmgm,0.488265940770978,105.0,-145.0,0.45182111572153066,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,ast,rotation,2.3355053968863855,2.5,2.5,betmgm,0.438103193317112,120.0,-160.0,0.4248366013071895,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,fg3m,rotation,0.9240923844308196,1.5,1.5,betmgm,0.2805551644570535,-150.0,110.0,0.5575221238938053,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,tov,rotation,0.8282313495879147,,,,,,,,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,stl,rotation,1.4205536958712341,1.5,1.5,betparx,0.3828923655949239,-110.0,-120.0,0.48987854251012153,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,blk,rotation,0.2793058116961172,0.5,0.5,betparx,0.20523955210309316,123.0,-165.0,0.4186744608578877,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,stocks,rotation,1.6998595075673517,2.5,2.5,betparx,0.21521184753246772,148.0,-200.0,0.3768844221105528,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,pa,rotation,11.995666977432384,12.5,12.5,bovada,0.4260463113129193,-125.0,-105.0,0.5203045685279188,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,pr,rotation,13.171317518183155,13.5,13.5,bovada,0.43885212434469223,-125.0,-105.0,0.5203045685279188,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,ra,rotation,5.8466613345235166,5.5,5.5,bovada,0.5451864402566828,-115.0,-115.0,0.5,latest_valid_report_selected,projected
Alex Caruso,89,OKC,SAS,21713533,pra,rotation,15.506822915069506,16.5,16.5,betparx,0.4040982965700308,106.0,-143.0,0.4520257450053946,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,pts,starter,18.3923204982245,15.5,15.5,betparx,0.6908979244687576,-120.0,-112.0,0.5079872204472844,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,reb,starter,4.689526811738876,3.5,3.5,betmgm,0.7615712986100498,-140.0,105.0,0.5445920303605313,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,ast,starter,6.1170814359552175,5.5,5.5,betmgm,0.6130764894493721,-140.0,105.0,0.5445920303605313,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,fg3m,starter,1.740190831007218,1.5,1.5,betmgm,0.49627071725310246,-105.0,-125.0,0.4796954314720812,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,tov,starter,2.353294810552617,,,,,,,,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,stl,starter,0.6647089604975196,0.5,0.5,fanduel,0.4611449407677149,-245.0,178.0,0.6637754604814345,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,blk,starter,0.23394986512222551,0.5,0.5,betmgm,0.18771732106765227,240.0,-375.0,0.2714285714285714,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,stocks,starter,0.898658825619745,1.5,1.5,draftkings,0.235082111173934,122.0,-163.0,0.42089428031879145,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,pa,starter,24.509401934179706,21.5,21.5,betmgm,0.6855571769486106,-120.0,-110.0,0.5101214574898786,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,pr,starter,23.08184730996335,19.5,19.5,betmgm,0.7198732761093932,-118.0,-110.0,0.5082034454470877,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,ra,starter,10.80660824769407,9.5,9.5,betmgm,0.6896664072192736,-110.0,-120.0,0.48987854251012153,latest_valid_report_selected,projected
De'Aaron Fox,161,SAS,OKC,21713533,pra,starter,29.19892874591858,25.5,25.5,betmgm,0.7155795237136118,-120.0,-110.0,0.5101214574898786,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,pts,starter,28.358011600392746,29.5,29.5,betparx,0.4163193934698515,-109.0,-121.0,0.48784883956417835,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,reb,starter,4.498757158853499,3.5,3.5,betmgm,0.7674601880412054,-145.0,110.0,0.554140127388535,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,ast,starter,8.415162817878887,7.5,7.5,betmgm,0.6469213101330898,-150.0,110.0,0.5575221238938053,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,fg3m,starter,1.4256664463698423,1.5,1.5,betmgm,0.3261775188334889,105.0,-140.0,0.4554079696394686,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,tov,starter,2.9389238711707586,,,,,,,,latest_valid_report_selected,projected
Shai Gilgeous-Alexander,175,OKC,SAS,21713533,stl,starter,0.7449818584301016,1.5,1.5,betparx,0.20211557285731316,123.0,-165.0,0.4186744608578877,latest_valid_report_selected,projected

```

---

## `derek_game_snapshots/aggregate_snapshot_scoring.csv`

- bytes: `203`
- rows: `1`
- columns: `7`

Compact first 30 rows:

```csv
game_id,snapshot_type
21713533,current_live

```
