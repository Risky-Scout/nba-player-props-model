# Reviewable Delivery Preview — 2026-05-23 — derek_game_snapshots

GitHub may refuse to render large CSV files. This file is intentionally small.

---

## `derek_game_snapshots/21713899/morning/full_pmf_wide.csv`

- bytes: `432,769`
- rows: `180`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,reb,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,7.6263,7.6263,7,7,0.0068,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,ast,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,1.3578,1.3578,1,1,0.165,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,fg3m,core,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,1.3424,1.3424,0,0,0.8322,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,tov,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,1.3544,1.3544,1,2,0.1829,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,stl,core,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,0.474,0.474,0,0,0.707,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,blk,core,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,1.133,1.133,1,1,0.238,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,stocks,core,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.1469,29.3591,0.05,1.607,1.607,1,1,0.1683,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pa,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.1469,29.3591,0.05,14.3316,14.3316,14,14,0.0019,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.1469,29.3591,0.05,20.6,20.6,20,20,0.0001,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.1469,29.3591,0.05,8.9841,8.9841,9,8,0.0011,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pra,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.1469,29.3591,0.05,21.9579,21.9579,22,21,0.0,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.6513,34.7313,0.05,16.9764,16.9764,17,17,0.0013,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.6513,34.7313,0.05,6.4304,6.4304,6,6,0.0031,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.6513,34.7313,0.05,1.9324,1.9324,2,2,0.0535,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.6513,34.7313,0.05,2.1233,2.1233,2,1,0.1943,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.6513,34.7313,0.05,1.3273,1.3273,1,1,0.1282,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.6513,34.7313,0.05,0.8092,0.8092,0,0,0.5149,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.6513,34.7313,0.05,1.0619,1.0619,1,1,0.3245,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.6513,34.7313,0.05,1.8711,1.8711,1,1,0.1671,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.6513,34.7313,0.05,18.9088,18.9088,19,19,0.0001,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.6513,34.7313,0.05,23.4068,23.4068,23,23,0.0,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.6513,34.7313,0.05,8.3629,8.3629,8,8,0.0002,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.6513,34.7313,0.05,25.3392,25.3392,25,25,0.0,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.7506,34.1045,0.05,13.49,13.49,13,14,0.0025,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.7506,34.1045,0.05,3.4158,3.4158,3,3,0.0118,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.7506,34.1045,0.05,2.7386,2.7386,3,2,0.0298,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.7506,34.1045,0.05,1.161,1.161,1,1,0.3013,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.7506,34.1045,0.05,1.4083,1.4083,1,1,0.121,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.7506,34.1045,0.05,0.6993,0.6993,0,0,0.525,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z

```

---

## `derek_game_snapshots/21713899/morning/full_pmf_wide.parquet`

- bytes: `281,547`
- rows: `180`
- columns: `69`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,reb,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,7.626302028775516,7.626302028775519,7,7,0.006800106064804134,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,ast,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,1.357822725917859,1.3578227259178588,1,1,0.1650419243359433,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,fg3m,core,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,1.3423938960419646,1.3423938960419637,0,0,0.8322007629947543,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,tov,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,1.3543598906814165,1.3543598906814163,1,2,0.1829188205314016,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,stl,core,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,0.47401570056783837,0.47401570056783837,0,0,0.7069506660355148,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,blk,core,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,1.1329744103796864,1.1329744103796862,1,1,0.2379967292071045,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,stocks,core,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.146949328262913,29.359060532512963,0.050000000000000044,1.6069901109475249,1.6069901109475253,1,1,0.1682519462272366,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pa,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.146949328262913,29.359060532512963,0.050000000000000044,14.33155104837784,14.331551048377836,14,14,0.0019215597520779698,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pr,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.146949328262913,29.359060532512963,0.050000000000000044,20.6000303512355,20.600030351235496,20,20,7.917267189269683e-05,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,ra,core,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.146949328262913,29.359060532512963,0.050000000000000044,8.984124754693376,8.984124754693374,9,8,0.0011223025906237933,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pra,core,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,27.146949328262913,29.359060532512963,0.050000000000000044,21.957853077153356,21.957853077153356,22,21,1.3066810123988934e-05,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.65126073182097,34.73130045956243,0.050000000000000044,16.976363594215268,16.976363594215265,17,17,0.0013203349274651074,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.65126073182097,34.73130045956243,0.050000000000000044,6.430448650761871,6.430448650761872,6,6,0.0030653452909192914,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.65126073182097,34.73130045956243,0.050000000000000044,1.932402807570281,1.9324028075702817,2,2,0.053468063847404615,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.65126073182097,34.73130045956243,0.050000000000000044,2.1232827901303732,2.1232827901303732,2,1,0.194307205306112,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.65126073182097,34.73130045956243,0.050000000000000044,1.327256781220861,1.3272567812208607,1,1,0.1282406849129527,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.65126073182097,34.73130045956243,0.050000000000000044,0.8091972883653819,0.809197288365382,0,0,0.5148764139079623,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,blk,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,31.65126073182097,34.73130045956243,0.050000000000000044,1.061861416389922,1.0618614163899223,1,1,0.3244516866717762,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,stocks,starter,"stat_grid:component_convolution_mean_coherent_v1+components[stl:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,blk:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.65126073182097,34.73130045956243,0.050000000000000044,1.8710587047553036,1.8710587047553033,1,1,0.16705252091995393,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,pa,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.65126073182097,34.73130045956243,0.050000000000000044,18.908766401785552,18.908766401785556,19,19,7.059575220166272e-05,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,pr,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.65126073182097,34.73130045956243,0.050000000000000044,23.40681224497714,23.40681224497715,23,23,4.047282452341431e-06,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,ra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.65126073182097,34.73130045956243,0.050000000000000044,8.362851458332154,8.362851458332155,8,8,0.00016389807772921382,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
OG Anunoby,18,NYK,CLE,21713899,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,31.65126073182097,34.73130045956243,0.050000000000000044,25.339215052547424,25.33921505254742,25,25,2.1640035657027197e-07,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.75057536382615,34.10450327009431,0.050000000000000044,13.490000708478425,13.490000708478423,13,14,0.002507716234462815,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,reb,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.75057536382615,34.10450327009431,0.050000000000000044,3.4157939151264363,3.4157939151264367,3,3,0.011756352536384853,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,ast,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.75057536382615,34.10450327009431,0.050000000000000044,2.738580674525832,2.7385806745258314,3,2,0.029818060527984344,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,fg3m,starter,stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.75057536382615,34.10450327009431,0.050000000000000044,1.1609815811508422,1.1609815811508422,1,1,0.3013196474392437,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,tov,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.75057536382615,34.10450327009431,0.050000000000000044,1.4083238869641628,1.4083238869641628,1,1,0.12095171420976011,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Mikal Bridges,61,NYK,CLE,21713899,stl,starter,stat_grid:hurdle_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1+sparse_hurdle_guarded,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,30.75057536382615,34.10450327009431,0.050000000000000044,0.6993347223304097,0.6993347223304098,0,0,0.5250372525507125,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z

```

---

## `derek_game_snapshots/21713899/morning/market_comparison.csv`

- bytes: `523,836`
- rows: `617`
- columns: `67`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,williamhill_us,0.5004,-112,-120,0.492,0.0083,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,9.5,9.5,bovada,0.6943,-280,205,0.6921,0.0022,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,10.5,10.5,bovada,0.6277,-200,150,0.625,0.0027,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,11.5,11.5,bovada,0.5642,-145,110,0.5541,0.0101,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,bovada,0.5004,-110,-120,0.4899,0.0105,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,13.5,13.5,bovada,0.4316,120,-160,0.4248,0.0068,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,14.5,14.5,bovada,0.3715,155,-210,0.3666,0.0048,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,15.5,15.5,bovada,0.3112,200,-275,0.3125,-0.0013,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,betonlineag,0.5004,-109,-119,0.4897,0.0106,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,betmgm,0.5004,-115,-115,0.5,0.0004,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,11.5,11.5,betrivers,0.5642,-162,117,0.573,-0.0088,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,betrivers,0.5004,-106,-129,0.4774,0.023,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,draftkings,0.5004,-108,-117,0.4906,0.0098,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,16.5,16.5,fanduel,0.2586,290,-440,0.2394,0.0193,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,17.5,17.5,fanduel,0.22,390,-650,0.1906,0.0294,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,15.5,15.5,fanduel,0.3112,225,-320,0.2877,0.0236,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,14.5,14.5,fanduel,0.3715,178,-245,0.3362,0.0352,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,fanduel,0.5004,100,-132,0.4677,0.0326,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,13.5,13.5,fanduel,0.4316,134,-180,0.3993,0.0323,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,6.5,6.5,fanduel,0.8479,-900,490,0.8415,0.0064,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,7.5,7.5,fanduel,0.8068,-550,350,0.792,0.0148,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,8.5,8.5,fanduel,0.7567,-380,260,0.7403,0.0165,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,9.5,9.5,fanduel,0.6943,-260,188,0.6753,0.0189,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,10.5,10.5,fanduel,0.6277,-188,140,0.6104,0.0174,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,11.5,11.5,fanduel,0.5642,-136,102,0.5379,0.0263,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,fanduel,0.5004,100,-132,0.4677,0.0326,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,fliff,0.5004,-115,-125,0.4905,0.0098,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,betparx,0.5004,-105,-127,0.4779,0.0224,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,11.5,11.5,betparx,0.5642,-162,117,0.573,-0.0088,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,13.5,13.5,espnbet,0.4316,130,-170,0.4085,0.0231,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z

```

---

## `derek_game_snapshots/21713899/morning/market_comparison.parquet`

- bytes: `141,687`
- rows: `2,464`
- columns: `67`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,williamhill_us,0.5003568697739306,-112,-120,0.4920127795527157,0.008344090221214961,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,9.5,9.5,bovada,0.6942663448190215,-280,205,0.6920583468395461,0.0022079979794752402,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,10.5,10.5,bovada,0.6277402421960266,-200,150,0.625,0.002740242196026532,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,11.5,11.5,bovada,0.5642023807933828,-145,110,0.554140127388535,0.010062253404847898,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,bovada,0.5003568697739306,-110,-120,0.48987854251012153,0.01047832726380915,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,13.5,13.5,bovada,0.4315948930309853,120,-160,0.4248366013071895,0.006758291723795995,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,14.5,14.5,bovada,0.3714577166459069,155,-210,0.3666469544648137,0.0048107621810932755,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,15.5,15.5,bovada,0.3112467922255753,200,-275,0.3125,-0.001253207774424614,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,betonlineag,0.5003568697739306,-109,-119,0.48974190636412124,0.010614963409809441,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,betmgm,0.5003568697739306,-115,-115,0.5,0.0003568697739306792,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,11.5,11.5,betrivers,0.5642023807933828,-162,117,0.5729699775075789,-0.008767596714196024,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,betrivers,0.5003568697739306,-106,-129,0.4773835745752045,0.022973295198726207,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,draftkings,0.5003568697739306,-108,-117,0.4905802562170309,0.009776613556899794,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,16.5,16.5,fanduel,0.25863918870933295,290,-440,0.23936170212765953,0.01927748658167347,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,17.5,17.5,fanduel,0.21996662373516662,390,-650,0.1905972045743329,0.029369419160833687,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,15.5,15.5,fanduel,0.3112467922255753,225,-320,0.28767123287671237,0.023575559348863018,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,14.5,14.5,fanduel,0.3714577166459069,178,-245,0.3362245395185654,0.035233177127341586,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,fanduel,0.5003568697739306,100,-132,0.4677419354838709,0.032614934290059794,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,13.5,13.5,fanduel,0.4315948930309853,134,-180,0.3993154592127781,0.03227943381820736,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,6.5,6.5,fanduel,0.8479015964765529,-900,490,0.8415213946117275,0.006380201864825463,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,7.5,7.5,fanduel,0.8067643121613757,-550,350,0.792,0.014764312161375526,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,8.5,8.5,fanduel,0.7567342238535982,-380,260,0.7402597402597403,0.016474483593857947,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,9.5,9.5,fanduel,0.6942663448190215,-260,188,0.6753246753246753,0.01894166949434606,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,10.5,10.5,fanduel,0.6277402421960266,-188,140,0.6103896103896104,0.01735063180641616,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,11.5,11.5,fanduel,0.5642023807933828,-136,102,0.5379072681704261,0.026295112622956807,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,fanduel,0.5003568697739306,100,-132,0.4677419354838709,0.032614934290059794,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,fliff,0.5003568697739306,-115,-125,0.490521327014218,0.009835542759712657,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,12.5,12.5,betparx,0.5003568697739306,-105,-127,0.47794265089231996,0.022414218881610715,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,11.5,11.5,betparx,0.5642023807933828,-162,117,0.5729699775075789,-0.008767596714196024,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.146949328262913,29.359060532512963,0.050000000000000044,12.973728322459982,12.973728322459982,13,13,0.011642858381647499,13.5,13.5,espnbet,0.4315948930309853,130,-170,0.40847201210287437,0.0231228809281111,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z

```

---

## `derek_game_snapshots/21713899/morning/market_comparison_csv_parts/market_comparison_part_000.csv`

- bytes: `481,591`
- rows: `560`
- columns: `67`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,williamhill_us,0.5004,-112,-120,0.492,0.0083,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,9.5,9.5,bovada,0.6943,-280,205,0.6921,0.0022,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,10.5,10.5,bovada,0.6277,-200,150,0.625,0.0027,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,11.5,11.5,bovada,0.5642,-145,110,0.5541,0.0101,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,bovada,0.5004,-110,-120,0.4899,0.0105,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,13.5,13.5,bovada,0.4316,120,-160,0.4248,0.0068,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,14.5,14.5,bovada,0.3715,155,-210,0.3666,0.0048,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,15.5,15.5,bovada,0.3112,200,-275,0.3125,-0.0013,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,betonlineag,0.5004,-109,-119,0.4897,0.0106,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,betmgm,0.5004,-115,-115,0.5,0.0004,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,11.5,11.5,betrivers,0.5642,-162,117,0.573,-0.0088,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,betrivers,0.5004,-106,-129,0.4774,0.023,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,draftkings,0.5004,-108,-117,0.4906,0.0098,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,16.5,16.5,fanduel,0.2586,290,-440,0.2394,0.0193,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,17.5,17.5,fanduel,0.22,390,-650,0.1906,0.0294,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,15.5,15.5,fanduel,0.3112,225,-320,0.2877,0.0236,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,14.5,14.5,fanduel,0.3715,178,-245,0.3362,0.0352,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,fanduel,0.5004,100,-132,0.4677,0.0326,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,13.5,13.5,fanduel,0.4316,134,-180,0.3993,0.0323,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,6.5,6.5,fanduel,0.8479,-900,490,0.8415,0.0064,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,7.5,7.5,fanduel,0.8068,-550,350,0.792,0.0148,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,8.5,8.5,fanduel,0.7567,-380,260,0.7403,0.0165,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,9.5,9.5,fanduel,0.6943,-260,188,0.6753,0.0189,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,10.5,10.5,fanduel,0.6277,-188,140,0.6104,0.0174,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,11.5,11.5,fanduel,0.5642,-136,102,0.5379,0.0263,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,fanduel,0.5004,100,-132,0.4677,0.0326,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,fliff,0.5004,-115,-125,0.4905,0.0098,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,12.5,12.5,betparx,0.5004,-105,-127,0.4779,0.0224,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,11.5,11.5,betparx,0.5642,-162,117,0.573,-0.0088,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jarrett Allen,9,CLE,NYK,21713899,pts,core,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,27.1469,29.3591,0.05,12.9737,12.9737,13,13,0.0116,13.5,13.5,espnbet,0.4316,130,-170,0.4085,0.0231,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z

```

---

## `derek_game_snapshots/21713899/morning/market_comparison_csv_parts/market_comparison_part_001.csv`

- bytes: `43,054`
- rows: `57`
- columns: `67`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_source,calibration_source,cal_source,minutes_mean,minutes_q50,p_inactive_used,mean,pmf_mean,median,mode,p0,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,edge,injury_freshness_status,injury_context_source,expected_lineup_status,official_lineup_status,lineup_source,lineup_freshness_status,snapshot_type,snapshot_time_utc
Mikal Bridges,61,NYK,CLE,21713899,pra,starter,"stat_grid:component_convolution_mean_coherent_v1+components[pts:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,reb:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,ast:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+prior_combo[joint_sampler_v1+joint_combo_pmf_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1]+stat_grid_final_component_convolution_mean_coherent_v1",phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,phase8_pmf_cal,30.7506,34.1045,0.05,19.6444,19.6444,19,19,0.0,19.5,19.5,hardrockbet,0.4789,-130,100,0.5306,-0.0517,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,26.5,26.5,williamhill_us,0.4993,-121,-111,0.51,-0.0107,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,22.5,22.5,bovada,0.6971,-300,215,0.7026,-0.0055,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,23.5,23.5,bovada,0.6443,-230,170,0.653,-0.0087,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,24.5,24.5,bovada,0.5967,-185,140,0.6091,-0.0123,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,25.5,25.5,bovada,0.5511,-150,115,0.5633,-0.0122,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,26.5,26.5,bovada,0.4993,-125,-105,0.5203,-0.021,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,28.5,28.5,bovada,0.3713,115,-150,0.4367,-0.0654,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,29.5,29.5,bovada,0.321,140,-185,0.3909,-0.07,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,30.5,30.5,bovada,0.2882,165,-220,0.3544,-0.0662,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,31.5,31.5,bovada,0.2467,200,-275,0.3125,-0.0658,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,27.5,27.5,bovada,0.4197,-105,-125,0.4797,-0.06,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,26.5,26.5,betonlineag,0.4993,-125,-103,0.5227,-0.0234,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,27.5,27.5,betmgm,0.4197,-105,-125,0.4797,-0.06,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,25.5,25.5,betrivers,0.5511,-167,120,0.5791,-0.028,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,26.5,26.5,betrivers,0.4993,-132,-103,0.5286,-0.0293,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,27.5,27.5,betrivers,0.4197,-107,-127,0.4802,-0.0606,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,28.5,28.5,betrivers,0.3713,116,-159,0.4299,-0.0586,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,26.5,26.5,draftkings,0.4993,-124,-103,0.5218,-0.0225,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,26.5,26.5,fanduel,0.4993,-114,-114,0.5,-0.0007,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,19.5,19.5,fanduel,0.8259,-600,370,0.8011,0.0248,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,20.5,20.5,fanduel,0.79,-450,300,0.766,0.024,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,21.5,21.5,fanduel,0.7428,-350,240,0.7256,0.0172,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,22.5,22.5,fanduel,0.6971,-275,198,0.6861,0.0111,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,23.5,23.5,fanduel,0.6443,-225,164,0.6464,-0.0021,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,25.5,25.5,fanduel,0.5511,-138,104,0.5419,0.0092,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,26.5,26.5,fanduel,0.4993,-114,-114,0.5,-0.0007,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,18.5,18.5,fanduel,0.856,-750,430,0.8238,0.0322,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,27.5,27.5,fanduel,0.4197,108,-144,0.4489,-0.0293,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z
Jalen Brunson,73,NYK,CLE,21713899,pts,starter,stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:starter+monotone_pit_cdf_v1,phase8_role_aware_pmf_cal_v1+monotone_inactive_global_v1,role_aware_pmf_cal_v1,33.0744,36.1936,0.05,26.4884,26.4884,26,27,0.0004,29.5,29.5,fanduel,0.321,164,-225,0.3536,-0.0327,unknown,bdl_injuries_only,projected,not_available_yet,bdl_lineup_freshness_manifest,projected,morning,2026-05-23T16:11:19Z

```

---

## `derek_game_snapshots/21713899/morning/outcome_level_probabilities.csv`

- bytes: `524,223`
- rows: `7,227`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Jarrett Allen,9,21713899,pts,core,0,0.0116,unknown,projected
Jarrett Allen,9,21713899,pts,core,1,0.0074,unknown,projected
Jarrett Allen,9,21713899,pts,core,2,0.01,unknown,projected
Jarrett Allen,9,21713899,pts,core,3,0.0223,unknown,projected
Jarrett Allen,9,21713899,pts,core,4,0.0283,unknown,projected
Jarrett Allen,9,21713899,pts,core,5,0.031,unknown,projected
Jarrett Allen,9,21713899,pts,core,6,0.0415,unknown,projected
Jarrett Allen,9,21713899,pts,core,7,0.0411,unknown,projected
Jarrett Allen,9,21713899,pts,core,8,0.05,unknown,projected
Jarrett Allen,9,21713899,pts,core,9,0.0625,unknown,projected
Jarrett Allen,9,21713899,pts,core,10,0.0665,unknown,projected
Jarrett Allen,9,21713899,pts,core,11,0.0635,unknown,projected
Jarrett Allen,9,21713899,pts,core,12,0.0638,unknown,projected
Jarrett Allen,9,21713899,pts,core,13,0.0688,unknown,projected
Jarrett Allen,9,21713899,pts,core,14,0.0601,unknown,projected
Jarrett Allen,9,21713899,pts,core,15,0.0602,unknown,projected
Jarrett Allen,9,21713899,pts,core,16,0.0526,unknown,projected
Jarrett Allen,9,21713899,pts,core,17,0.0387,unknown,projected
Jarrett Allen,9,21713899,pts,core,18,0.0414,unknown,projected
Jarrett Allen,9,21713899,pts,core,19,0.0299,unknown,projected
Jarrett Allen,9,21713899,pts,core,20,0.0301,unknown,projected
Jarrett Allen,9,21713899,pts,core,21,0.0198,unknown,projected
Jarrett Allen,9,21713899,pts,core,22,0.0195,unknown,projected
Jarrett Allen,9,21713899,pts,core,23,0.0205,unknown,projected
Jarrett Allen,9,21713899,pts,core,24,0.0103,unknown,projected
Jarrett Allen,9,21713899,pts,core,25,0.0099,unknown,projected
Jarrett Allen,9,21713899,pts,core,26,0.0091,unknown,projected
Jarrett Allen,9,21713899,pts,core,27,0.0061,unknown,projected
Jarrett Allen,9,21713899,pts,core,28,0.0085,unknown,projected
Jarrett Allen,9,21713899,pts,core,29,0.0061,unknown,projected

```

---

## `derek_game_snapshots/21713899/morning/outcome_level_probabilities.parquet`

- bytes: `96,869`
- rows: `8,822`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Jarrett Allen,9,21713899,pts,core,0,0.011642858381647497,unknown,projected
Jarrett Allen,9,21713899,pts,core,1,0.007358920057903901,unknown,projected
Jarrett Allen,9,21713899,pts,core,2,0.010006929362493113,unknown,projected
Jarrett Allen,9,21713899,pts,core,3,0.022302307057614473,unknown,projected
Jarrett Allen,9,21713899,pts,core,4,0.028337651761704327,unknown,projected
Jarrett Allen,9,21713899,pts,core,5,0.03099757060041502,unknown,projected
Jarrett Allen,9,21713899,pts,core,6,0.041452166301668786,unknown,projected
Jarrett Allen,9,21713899,pts,core,7,0.04113728431517721,unknown,projected
Jarrett Allen,9,21713899,pts,core,8,0.05003008830777745,unknown,projected
Jarrett Allen,9,21713899,pts,core,9,0.062467879034576845,unknown,projected
Jarrett Allen,9,21713899,pts,core,10,0.06652610262299483,unknown,projected
Jarrett Allen,9,21713899,pts,core,11,0.06353786140264368,unknown,projected
Jarrett Allen,9,21713899,pts,core,12,0.06384551101945217,unknown,projected
Jarrett Allen,9,21713899,pts,core,13,0.0687619767429452,unknown,projected
Jarrett Allen,9,21713899,pts,core,14,0.0601371763850785,unknown,projected
Jarrett Allen,9,21713899,pts,core,15,0.06021092442033157,unknown,projected
Jarrett Allen,9,21713899,pts,core,16,0.052607603516242364,unknown,projected
Jarrett Allen,9,21713899,pts,core,17,0.038672564974166365,unknown,projected
Jarrett Allen,9,21713899,pts,core,18,0.041400172624856624,unknown,projected
Jarrett Allen,9,21713899,pts,core,19,0.029916518059884538,unknown,projected
Jarrett Allen,9,21713899,pts,core,20,0.03014880667314987,unknown,projected
Jarrett Allen,9,21713899,pts,core,21,0.019835611572039127,unknown,projected
Jarrett Allen,9,21713899,pts,core,22,0.019489231233025883,unknown,projected
Jarrett Allen,9,21713899,pts,core,23,0.020502688313093983,unknown,projected
Jarrett Allen,9,21713899,pts,core,24,0.010273459881833372,unknown,projected
Jarrett Allen,9,21713899,pts,core,25,0.009880638578536381,unknown,projected
Jarrett Allen,9,21713899,pts,core,26,0.009117118849173723,unknown,projected
Jarrett Allen,9,21713899,pts,core,27,0.006069978741056472,unknown,projected
Jarrett Allen,9,21713899,pts,core,28,0.00849782016982316,unknown,projected
Jarrett Allen,9,21713899,pts,core,29,0.00614514112466704,unknown,projected

```

---

## `derek_game_snapshots/21713899/morning/outcome_level_probabilities_csv_parts/outcome_level_probabilities_part_000.csv`

- bytes: `450,753`
- rows: `6,220`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Jarrett Allen,9,21713899,pts,core,0,0.0116,unknown,projected
Jarrett Allen,9,21713899,pts,core,1,0.0074,unknown,projected
Jarrett Allen,9,21713899,pts,core,2,0.01,unknown,projected
Jarrett Allen,9,21713899,pts,core,3,0.0223,unknown,projected
Jarrett Allen,9,21713899,pts,core,4,0.0283,unknown,projected
Jarrett Allen,9,21713899,pts,core,5,0.031,unknown,projected
Jarrett Allen,9,21713899,pts,core,6,0.0415,unknown,projected
Jarrett Allen,9,21713899,pts,core,7,0.0411,unknown,projected
Jarrett Allen,9,21713899,pts,core,8,0.05,unknown,projected
Jarrett Allen,9,21713899,pts,core,9,0.0625,unknown,projected
Jarrett Allen,9,21713899,pts,core,10,0.0665,unknown,projected
Jarrett Allen,9,21713899,pts,core,11,0.0635,unknown,projected
Jarrett Allen,9,21713899,pts,core,12,0.0638,unknown,projected
Jarrett Allen,9,21713899,pts,core,13,0.0688,unknown,projected
Jarrett Allen,9,21713899,pts,core,14,0.0601,unknown,projected
Jarrett Allen,9,21713899,pts,core,15,0.0602,unknown,projected
Jarrett Allen,9,21713899,pts,core,16,0.0526,unknown,projected
Jarrett Allen,9,21713899,pts,core,17,0.0387,unknown,projected
Jarrett Allen,9,21713899,pts,core,18,0.0414,unknown,projected
Jarrett Allen,9,21713899,pts,core,19,0.0299,unknown,projected
Jarrett Allen,9,21713899,pts,core,20,0.0301,unknown,projected
Jarrett Allen,9,21713899,pts,core,21,0.0198,unknown,projected
Jarrett Allen,9,21713899,pts,core,22,0.0195,unknown,projected
Jarrett Allen,9,21713899,pts,core,23,0.0205,unknown,projected
Jarrett Allen,9,21713899,pts,core,24,0.0103,unknown,projected
Jarrett Allen,9,21713899,pts,core,25,0.0099,unknown,projected
Jarrett Allen,9,21713899,pts,core,26,0.0091,unknown,projected
Jarrett Allen,9,21713899,pts,core,27,0.0061,unknown,projected
Jarrett Allen,9,21713899,pts,core,28,0.0085,unknown,projected
Jarrett Allen,9,21713899,pts,core,29,0.0061,unknown,projected

```

---

## `derek_game_snapshots/21713899/morning/outcome_level_probabilities_csv_parts/outcome_level_probabilities_part_001.csv`

- bytes: `73,608`
- rows: `1,007`
- columns: `11`

Compact first 30 rows:

```csv
player_name,player_id,game_id,stat,role_bucket,k,p_k,injury_freshness_status,lineup_freshness_status
Max Strus,666908,21713899,pa,core,74,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,75,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,76,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,77,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,78,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,79,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,80,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,81,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,82,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,83,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,84,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,85,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,86,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,87,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,88,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,89,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,90,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,91,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,92,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,93,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,94,0.0,unknown,projected
Max Strus,666908,21713899,pa,core,95,0.0,unknown,projected
Max Strus,666908,21713899,pr,core,0,0.0003,unknown,projected
Max Strus,666908,21713899,pr,core,1,0.001,unknown,projected
Max Strus,666908,21713899,pr,core,2,0.003,unknown,projected
Max Strus,666908,21713899,pr,core,3,0.0075,unknown,projected
Max Strus,666908,21713899,pr,core,4,0.0148,unknown,projected
Max Strus,666908,21713899,pr,core,5,0.0228,unknown,projected
Max Strus,666908,21713899,pr,core,6,0.0324,unknown,projected
Max Strus,666908,21713899,pr,core,7,0.0407,unknown,projected

```

---

## `derek_game_snapshots/21713899/morning/prop_summary.csv`

- bytes: `23,568`
- rows: `180`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
Jarrett Allen,9,CLE,NYK,21713899,pts,core,12.9737,12.5,12.5,betmgm,0.5004,-115.0,-115.0,0.5,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,reb,core,7.6263,8.5,8.5,betmgm,0.3449,125.0,-165.0,0.4165,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,ast,core,1.3578,1.5,1.5,betmgm,0.3846,110.0,-150.0,0.4425,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,fg3m,core,1.3424,,,,,,,,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,tov,core,1.3544,,,,,,,,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,stl,core,0.474,0.5,0.5,betparx,0.293,-177.0,130.0,0.5951,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,blk,core,1.133,1.5,1.5,betmgm,0.2089,130.0,-185.0,0.4011,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,stocks,core,1.607,2.5,2.5,betparx,0.1779,128.0,-175.0,0.408,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,pa,core,14.3316,13.5,13.5,betmgm,0.5224,-125.0,-105.0,0.5203,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,pr,core,20.6,20.5,20.5,betmgm,0.4784,-125.0,-105.0,0.5203,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,ra,core,8.9841,9.5,9.5,betmgm,0.4092,-110.0,-118.0,0.4918,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,pra,core,21.9579,22.5,22.5,betmgm,0.4411,-110.0,-125.0,0.4853,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,pts,starter,16.9764,14.5,14.5,betmgm,0.6475,-120.0,-110.0,0.5101,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,reb,starter,6.4304,4.5,4.5,betmgm,0.8356,-150.0,110.0,0.5575,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,ast,starter,1.9324,1.5,1.5,betmgm,0.632,-115.0,-115.0,0.5,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,fg3m,starter,2.1233,2.5,2.5,betonlineag,0.3125,144.0,-189.0,0.3853,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,tov,starter,1.3273,,,,,,,,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,stl,starter,0.8092,1.5,1.5,betparx,0.1996,175.0,-240.0,0.34,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,blk,starter,1.0619,0.5,0.5,betmgm,0.6755,-165.0,120.0,0.578,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,stocks,starter,1.8711,1.5,1.5,betparx,0.4863,-190.0,140.0,0.6113,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,pa,starter,18.9088,16.5,16.5,betmgm,0.647,-115.0,-115.0,0.5,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,pr,starter,23.4068,19.5,19.5,bovada,0.7305,-130.0,100.0,0.5306,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,ra,starter,8.3629,6.5,6.5,betmgm,0.7969,-110.0,-118.0,0.4918,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,pra,starter,25.3392,21.5,21.5,betmgm,0.7239,-120.0,-110.0,0.5101,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,pts,starter,13.49,13.5,13.5,betmgm,0.4729,-115.0,-115.0,0.5,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,reb,starter,3.4158,3.5,3.5,betmgm,0.4539,115.0,-155.0,0.4335,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,ast,starter,2.7386,2.5,2.5,betmgm,0.5464,-105.0,-125.0,0.4797,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,fg3m,starter,1.161,1.5,1.5,betmgm,0.3349,-110.0,-120.0,0.4899,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,tov,starter,1.4083,,,,,,,,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,stl,starter,0.6993,1.5,1.5,betparx,0.1371,148.0,-200.0,0.3769,unknown,projected

```

---

## `derek_game_snapshots/21713899/morning/prop_summary.parquet`

- bytes: `18,627`
- rows: `180`
- columns: `19`

Compact first 30 rows:

```csv
player_name,player_id,team,opponent,game_id,stat,role_bucket,pmf_mean,line,market_line,book,p_over,market_over_odds,market_under_odds,market_no_vig_over_prob,injury_freshness_status,lineup_freshness_status
Jarrett Allen,9,CLE,NYK,21713899,pts,core,12.973728322459982,12.5,12.5,betmgm,0.5003568697739306,-115.0,-115.0,0.5,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,reb,core,7.626302028775519,8.5,8.5,betmgm,0.3449452261113303,125.0,-165.0,0.4165029469548134,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,ast,core,1.3578227259178588,1.5,1.5,betmgm,0.3846470706660485,110.0,-150.0,0.4424778761061947,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,fg3m,core,1.3423938960419637,,,,,,,,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,tov,core,1.3543598906814163,,,,,,,,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,stl,core,0.47401570056783837,0.5,0.5,betparx,0.2930493339644851,-177.0,130.0,0.5950884373629587,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,blk,core,1.1329744103796862,1.5,1.5,betmgm,0.20891164680040106,130.0,-185.0,0.40112596762843067,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,stocks,core,1.6069901109475253,2.5,2.5,betparx,0.17788199815123107,128.0,-175.0,0.40801186943620177,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,pa,core,14.331551048377836,13.5,13.5,betmgm,0.5223956937096729,-125.0,-105.0,0.5203045685279188,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,pr,core,20.600030351235496,20.5,20.5,betmgm,0.478391636846338,-125.0,-105.0,0.5203045685279188,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,ra,core,8.984124754693374,9.5,9.5,betmgm,0.4092176140890091,-110.0,-118.0,0.49179655455291227,unknown,projected
Jarrett Allen,9,CLE,NYK,21713899,pra,core,21.957853077153356,22.5,22.5,betmgm,0.44107817051583453,-110.0,-125.0,0.48529411764705876,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,pts,starter,16.976363594215265,14.5,14.5,betmgm,0.6475021548695368,-120.0,-110.0,0.5101214574898786,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,reb,starter,6.430448650761872,4.5,4.5,betmgm,0.8356190945519744,-150.0,110.0,0.5575221238938053,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,ast,starter,1.9324028075702817,1.5,1.5,betmgm,0.6320269757453569,-115.0,-115.0,0.5,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,fg3m,starter,2.1232827901303732,2.5,2.5,betonlineag,0.3125042449848454,144.0,-189.0,0.3852511464220966,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,tov,starter,1.3272567812208607,,,,,,,,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,stl,starter,0.809197288365382,1.5,1.5,betparx,0.19959052746672112,175.0,-240.0,0.33999999999999997,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,blk,starter,1.0618614163899223,0.5,0.5,betmgm,0.6755483133282238,-165.0,120.0,0.5780254777070064,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,stocks,starter,1.8710587047553033,1.5,1.5,betparx,0.48629319718974634,-190.0,140.0,0.6112600536193029,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,pa,starter,18.908766401785556,16.5,16.5,betmgm,0.6470095766335497,-115.0,-115.0,0.5,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,pr,starter,23.40681224497715,19.5,19.5,bovada,0.7304697681869886,-130.0,100.0,0.5306122448979592,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,ra,starter,8.362851458332155,6.5,6.5,betmgm,0.796941384587428,-110.0,-118.0,0.49179655455291227,unknown,projected
OG Anunoby,18,NYK,CLE,21713899,pra,starter,25.33921505254742,21.5,21.5,betmgm,0.723877004469168,-120.0,-110.0,0.5101214574898786,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,pts,starter,13.490000708478423,13.5,13.5,betmgm,0.47288849359046886,-115.0,-115.0,0.5,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,reb,starter,3.4157939151264367,3.5,3.5,betmgm,0.45389761008247514,115.0,-155.0,0.43348916277093075,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,ast,starter,2.7385806745258314,2.5,2.5,betmgm,0.5464396933622886,-105.0,-125.0,0.4796954314720812,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,fg3m,starter,1.1609815811508422,1.5,1.5,betmgm,0.3348943803761771,-110.0,-120.0,0.48987854251012153,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,tov,starter,1.4083238869641628,,,,,,,,unknown,projected
Mikal Bridges,61,NYK,CLE,21713899,stl,starter,0.6993347223304098,1.5,1.5,betparx,0.1371057667999764,148.0,-200.0,0.3768844221105528,unknown,projected

```
