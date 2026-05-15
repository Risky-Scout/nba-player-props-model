# Constant probability diagnosis

Window `2026-04-01` .. `2026-05-12`

## Counts by stat
stat
blk       520
stl       520
stocks    520

## Counts by role_bucket
role_bucket
bench    1560

## Largest group n = 520

  source   stat role_bucket   n            probability_type  constant_prob_value source_pmf_column model_version calibration_stage source_recalibration_stage  ref_line fold_start   fold_end  example_player_id  example_game_id example_game_date     suspected_cause
base_oof    blk       bench 520 model_over_prob_median_line                  0.0        pmf_active                  oof_fold_chunk                                  0.5 2026-04-29 2026-05-10                356         21681991        2026-04-29 bug_same_pmf_reused
base_oof    stl       bench 520 model_over_prob_median_line                  0.0        pmf_active                  oof_fold_chunk                                  0.5 2026-04-29 2026-05-10                356         21681991        2026-04-29 bug_same_pmf_reused
base_oof stocks       bench 520 model_over_prob_median_line                  0.0        pmf_active                  oof_fold_chunk                                  1.5 2026-04-29 2026-05-10                356         21681991        2026-04-29 bug_same_pmf_reused
