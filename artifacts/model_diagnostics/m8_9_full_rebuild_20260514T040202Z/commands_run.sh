#!/usr/bin/env bash
set -euo pipefail
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-04-27 --run-mode backtest --out data/features/player_prop_features_2026-04-27_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-04-27 --run-mode backtest --out data/features/injury_lineup_features_2026-04-27_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-04-27_backtest.parquet --out data/features/role_state_features_2026-04-27.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-04-27_backtest.parquet --out data/features/teammate_on_off_features_2026-04-27.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-04-27_backtest.parquet --out data/features/opponent_matchup_features_2026-04-27.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-04-27_backtest.parquet --out data/features/sparse_stat_features_2026-04-27.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-04-27_backtest.parquet --out data/features/combo_covariance_features_2026-04-27.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-04-27 --feature-snapshot data/features/player_prop_features_2026-04-27_backtest.parquet --out predictions/stat_grid_2026-04-27.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-04-27 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-04-28 --run-mode backtest --out data/features/player_prop_features_2026-04-28_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-04-28 --run-mode backtest --out data/features/injury_lineup_features_2026-04-28_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-04-28_backtest.parquet --out data/features/role_state_features_2026-04-28.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-04-28_backtest.parquet --out data/features/teammate_on_off_features_2026-04-28.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-04-28_backtest.parquet --out data/features/opponent_matchup_features_2026-04-28.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-04-28_backtest.parquet --out data/features/sparse_stat_features_2026-04-28.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-04-28_backtest.parquet --out data/features/combo_covariance_features_2026-04-28.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-04-28 --feature-snapshot data/features/player_prop_features_2026-04-28_backtest.parquet --out predictions/stat_grid_2026-04-28.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-04-28 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-04-29 --run-mode backtest --out data/features/player_prop_features_2026-04-29_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-04-29 --run-mode backtest --out data/features/injury_lineup_features_2026-04-29_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-04-29_backtest.parquet --out data/features/role_state_features_2026-04-29.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-04-29_backtest.parquet --out data/features/teammate_on_off_features_2026-04-29.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-04-29_backtest.parquet --out data/features/opponent_matchup_features_2026-04-29.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-04-29_backtest.parquet --out data/features/sparse_stat_features_2026-04-29.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-04-29_backtest.parquet --out data/features/combo_covariance_features_2026-04-29.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-04-29 --feature-snapshot data/features/player_prop_features_2026-04-29_backtest.parquet --out predictions/stat_grid_2026-04-29.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-04-29 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-04-30 --run-mode backtest --out data/features/player_prop_features_2026-04-30_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-04-30 --run-mode backtest --out data/features/injury_lineup_features_2026-04-30_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-04-30_backtest.parquet --out data/features/role_state_features_2026-04-30.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-04-30_backtest.parquet --out data/features/teammate_on_off_features_2026-04-30.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-04-30_backtest.parquet --out data/features/opponent_matchup_features_2026-04-30.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-04-30_backtest.parquet --out data/features/sparse_stat_features_2026-04-30.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-04-30_backtest.parquet --out data/features/combo_covariance_features_2026-04-30.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-04-30 --feature-snapshot data/features/player_prop_features_2026-04-30_backtest.parquet --out predictions/stat_grid_2026-04-30.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-04-30 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-01 --run-mode backtest --out data/features/player_prop_features_2026-05-01_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-01 --run-mode backtest --out data/features/injury_lineup_features_2026-05-01_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-01_backtest.parquet --out data/features/role_state_features_2026-05-01.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-01_backtest.parquet --out data/features/teammate_on_off_features_2026-05-01.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-01_backtest.parquet --out data/features/opponent_matchup_features_2026-05-01.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-01_backtest.parquet --out data/features/sparse_stat_features_2026-05-01.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-01_backtest.parquet --out data/features/combo_covariance_features_2026-05-01.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-01 --feature-snapshot data/features/player_prop_features_2026-05-01_backtest.parquet --out predictions/stat_grid_2026-05-01.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-01 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-02 --run-mode backtest --out data/features/player_prop_features_2026-05-02_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-02 --run-mode backtest --out data/features/injury_lineup_features_2026-05-02_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-02_backtest.parquet --out data/features/role_state_features_2026-05-02.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-02_backtest.parquet --out data/features/teammate_on_off_features_2026-05-02.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-02_backtest.parquet --out data/features/opponent_matchup_features_2026-05-02.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-02_backtest.parquet --out data/features/sparse_stat_features_2026-05-02.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-02_backtest.parquet --out data/features/combo_covariance_features_2026-05-02.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-02 --feature-snapshot data/features/player_prop_features_2026-05-02_backtest.parquet --out predictions/stat_grid_2026-05-02.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-02 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-03 --run-mode backtest --out data/features/player_prop_features_2026-05-03_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-03 --run-mode backtest --out data/features/injury_lineup_features_2026-05-03_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-03_backtest.parquet --out data/features/role_state_features_2026-05-03.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-03_backtest.parquet --out data/features/teammate_on_off_features_2026-05-03.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-03_backtest.parquet --out data/features/opponent_matchup_features_2026-05-03.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-03_backtest.parquet --out data/features/sparse_stat_features_2026-05-03.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-03_backtest.parquet --out data/features/combo_covariance_features_2026-05-03.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-03 --feature-snapshot data/features/player_prop_features_2026-05-03_backtest.parquet --out predictions/stat_grid_2026-05-03.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-03 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-04 --run-mode backtest --out data/features/player_prop_features_2026-05-04_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-04 --run-mode backtest --out data/features/injury_lineup_features_2026-05-04_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-04_backtest.parquet --out data/features/role_state_features_2026-05-04.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-04_backtest.parquet --out data/features/teammate_on_off_features_2026-05-04.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-04_backtest.parquet --out data/features/opponent_matchup_features_2026-05-04.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-04_backtest.parquet --out data/features/sparse_stat_features_2026-05-04.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-04_backtest.parquet --out data/features/combo_covariance_features_2026-05-04.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-04 --feature-snapshot data/features/player_prop_features_2026-05-04_backtest.parquet --out predictions/stat_grid_2026-05-04.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-04 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-05 --run-mode backtest --out data/features/player_prop_features_2026-05-05_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-05 --run-mode backtest --out data/features/injury_lineup_features_2026-05-05_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-05_backtest.parquet --out data/features/role_state_features_2026-05-05.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-05_backtest.parquet --out data/features/teammate_on_off_features_2026-05-05.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-05_backtest.parquet --out data/features/opponent_matchup_features_2026-05-05.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-05_backtest.parquet --out data/features/sparse_stat_features_2026-05-05.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-05_backtest.parquet --out data/features/combo_covariance_features_2026-05-05.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-05 --feature-snapshot data/features/player_prop_features_2026-05-05_backtest.parquet --out predictions/stat_grid_2026-05-05.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-05 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-06 --run-mode backtest --out data/features/player_prop_features_2026-05-06_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-06 --run-mode backtest --out data/features/injury_lineup_features_2026-05-06_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-06_backtest.parquet --out data/features/role_state_features_2026-05-06.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-06_backtest.parquet --out data/features/teammate_on_off_features_2026-05-06.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-06_backtest.parquet --out data/features/opponent_matchup_features_2026-05-06.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-06_backtest.parquet --out data/features/sparse_stat_features_2026-05-06.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-06_backtest.parquet --out data/features/combo_covariance_features_2026-05-06.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-06 --feature-snapshot data/features/player_prop_features_2026-05-06_backtest.parquet --out predictions/stat_grid_2026-05-06.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-06 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-07 --run-mode backtest --out data/features/player_prop_features_2026-05-07_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-07 --run-mode backtest --out data/features/injury_lineup_features_2026-05-07_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-07_backtest.parquet --out data/features/role_state_features_2026-05-07.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-07_backtest.parquet --out data/features/teammate_on_off_features_2026-05-07.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-07_backtest.parquet --out data/features/opponent_matchup_features_2026-05-07.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-07_backtest.parquet --out data/features/sparse_stat_features_2026-05-07.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-07_backtest.parquet --out data/features/combo_covariance_features_2026-05-07.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-07 --feature-snapshot data/features/player_prop_features_2026-05-07_backtest.parquet --out predictions/stat_grid_2026-05-07.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-07 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-08 --run-mode backtest --out data/features/player_prop_features_2026-05-08_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-08 --run-mode backtest --out data/features/injury_lineup_features_2026-05-08_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-08_backtest.parquet --out data/features/role_state_features_2026-05-08.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-08_backtest.parquet --out data/features/teammate_on_off_features_2026-05-08.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-08_backtest.parquet --out data/features/opponent_matchup_features_2026-05-08.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-08_backtest.parquet --out data/features/sparse_stat_features_2026-05-08.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-08_backtest.parquet --out data/features/combo_covariance_features_2026-05-08.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-08 --feature-snapshot data/features/player_prop_features_2026-05-08_backtest.parquet --out predictions/stat_grid_2026-05-08.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-08 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-09 --run-mode backtest --out data/features/player_prop_features_2026-05-09_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-09 --run-mode backtest --out data/features/injury_lineup_features_2026-05-09_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-09_backtest.parquet --out data/features/role_state_features_2026-05-09.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-09_backtest.parquet --out data/features/teammate_on_off_features_2026-05-09.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-09_backtest.parquet --out data/features/opponent_matchup_features_2026-05-09.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-09_backtest.parquet --out data/features/sparse_stat_features_2026-05-09.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-09_backtest.parquet --out data/features/combo_covariance_features_2026-05-09.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-09 --feature-snapshot data/features/player_prop_features_2026-05-09_backtest.parquet --out predictions/stat_grid_2026-05-09.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-09 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-10 --run-mode backtest --out data/features/player_prop_features_2026-05-10_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-10 --run-mode backtest --out data/features/injury_lineup_features_2026-05-10_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-10_backtest.parquet --out data/features/role_state_features_2026-05-10.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-10_backtest.parquet --out data/features/teammate_on_off_features_2026-05-10.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-10_backtest.parquet --out data/features/opponent_matchup_features_2026-05-10.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-10_backtest.parquet --out data/features/sparse_stat_features_2026-05-10.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-10_backtest.parquet --out data/features/combo_covariance_features_2026-05-10.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-10 --feature-snapshot data/features/player_prop_features_2026-05-10_backtest.parquet --out predictions/stat_grid_2026-05-10.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-10 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-11 --run-mode backtest --out data/features/player_prop_features_2026-05-11_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-11 --run-mode backtest --out data/features/injury_lineup_features_2026-05-11_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-11_backtest.parquet --out data/features/role_state_features_2026-05-11.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-11_backtest.parquet --out data/features/teammate_on_off_features_2026-05-11.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-11_backtest.parquet --out data/features/opponent_matchup_features_2026-05-11.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-11_backtest.parquet --out data/features/sparse_stat_features_2026-05-11.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-11_backtest.parquet --out data/features/combo_covariance_features_2026-05-11.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-11 --feature-snapshot data/features/player_prop_features_2026-05-11_backtest.parquet --out predictions/stat_grid_2026-05-11.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-11 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_player_prop_feature_snapshot.py --date 2026-05-12 --run-mode backtest --out data/features/player_prop_features_2026-05-12_backtest.parquet
python3 scripts/build_injury_lineup_features.py --date 2026-05-12 --run-mode backtest --out data/features/injury_lineup_features_2026-05-12_backtest.parquet
python3 scripts/predict_role_state_distribution.py --input data/features/player_prop_features_2026-05-12_backtest.parquet --out data/features/role_state_features_2026-05-12.parquet
python3 scripts/build_teammate_on_off_features.py --input data/features/player_prop_features_2026-05-12_backtest.parquet --out data/features/teammate_on_off_features_2026-05-12.parquet
python3 scripts/build_opponent_matchup_features.py --input data/features/player_prop_features_2026-05-12_backtest.parquet --out data/features/opponent_matchup_features_2026-05-12.parquet
python3 scripts/build_sparse_stat_features.py --input data/features/player_prop_features_2026-05-12_backtest.parquet --out data/features/sparse_stat_features_2026-05-12.parquet
python3 scripts/build_combo_covariance_features.py --input data/features/player_prop_features_2026-05-12_backtest.parquet --out data/features/combo_covariance_features_2026-05-12.parquet
python3 scripts/build_stat_grid_pmfs.py --date 2026-05-12 --feature-snapshot data/features/player_prop_features_2026-05-12_backtest.parquet --out predictions/stat_grid_2026-05-12.parquet
python3 scripts/build_daily_pmf_delivery.py --date 2026-05-12 --snapshot after_game --no-odds-fetch --rebuild-canonical
python3 scripts/build_event_market_loss_rows.py --dates-file artifacts/model_diagnostics/event_market_backtest_date_inventory.csv
python3 scripts/build_stat_role_market_superiority_report.py --dates-file artifacts/model_diagnostics/event_market_backtest_date_inventory.csv
python3 scripts/verify_market_superiority_math_contract.py --label dates_24c1750e26ad
python3 scripts/build_promotion_claim_report.py --dates-file artifacts/model_diagnostics/event_market_backtest_date_inventory.csv
