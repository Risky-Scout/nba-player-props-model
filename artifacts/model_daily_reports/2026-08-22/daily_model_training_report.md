# Daily model training / recalibration report — 2026-08-22

- generated_at_utc: 2026-08-23T16:45:15+00:00Z

## Headline

- active_champion_model_id: `challenger-2026-08-22`
- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- is_phase13s_direct_lineup_driver: **True**
- trained_through_date: `2026-08-22`
- calibrated_through_date: `2026-08-22`
- retraining_ran: **True**
- recalibration_ran: **True**
- no_leakage_passed: **True**
- validation_gates_passed: **True**
- challenger_promoted: **True**
- promotion_reason: `None`

## Active champion (full pointer block)

- champion_model_id: `challenger-2026-08-22`
- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- direct_lineup_pmf_driver: `True`
- contextual_pmf_engine: `True`
- trained_through_date: `2026-08-22`
- calibrated_through_date: `2026-08-22`
- training_run_id: `nightly-20260523T042740`
- calibration_manifest_path: `artifacts/models/challengers/2026-05-22/calibration_manifest.json`
- train_manifest_path: `artifacts/models/challengers/2026-08-22_direct_lineup_contextual/train_manifest.json`
- validation_report_path: `artifacts/phase13s/validation_gates_report.json`
- promotion_decision_path: `artifacts/models/challengers/2026-08-22_direct_lineup_contextual/promotion_decision.json`
- no_leakage_manifest_path: `artifacts/models/challengers/2026-08-22_direct_lineup_contextual/no_leakage_manifest.json`
- promotion_decision_id: `phase13s-promotion-2026-08-22_direct_lineup_contextual-20260823T075526`

## Promotion status

- promoted: **True**
- decision_promote_field: `True`
- manifest_promoted_field: `True`
- champion_pointer_swapped_to_today: **True**
- expected_today_challenger_id: `challenger-2026-08-22`
- active_champion_model_id: `challenger-2026-08-22`
- promotion_reason: `None`
- decision_id: `phase13s-promotion-2026-08-22_direct_lineup_contextual-20260823T075526`
- decided_at_utc: `2026-08-23T07:55:26+00:00`

## Validation gates

- any_positive_improvement: **True**
- issues: []
- minutes_min_rel_improvement: `0.05`
- safe_noninferiority_threshold: `-0.005`

## Per-target metrics (training-time validation)

| target | n_test | rel_improvement |
| --- | ---: | ---: |
| ast | 15987 | +2.0814% |
| blk | 15987 | -0.0044% |
| fg3m | 15987 | +0.0400% |
| minutes | 16443 | +15.2291% |
| pts | 15987 | +0.3472% |
| reb | 15987 | -0.0285% |
| stl | 15987 | +0.0216% |
| tov | 15987 | +0.0924% |

## Sensitivity

- case_1_direct_lineup: {'abs_diff_minutes_delta': 2.8569507698959917, 'feature_vector_hash_post': 'c6ef2fe8edb7777a', 'feature_vector_hash_pre': '9c834bc334605ad9', 'feature_vectors_changed': True, 'minutes_delta_post': 3.9246101550977954, 'minutes_delta_pre': 1.0676593852018037, 'pmf_mean_post': 33.924610155097795, 'pmf_mean_pre': 31.067659385201804, 'pmf_mean_shift': 2.8569507698959917}
- case_2_lineup_composition: {'abs_diff_minutes_delta': 2.4511298398661854, 'minutes_delta_a': 3.969769591266317, 'minutes_delta_b': 1.5186397514001317, 'team_lineup_num_high_usage_players_a': 1.0, 'team_lineup_num_high_usage_players_b': 3.0}
- case_3_actionability: {'injury_lineup_conflict': True, 'is_actionable': False, 'is_confirmed_out': True}
- case_4_teammate_out: {'abs_diff_minutes_delta': 0.00010795232668137089, 'minutes_delta_loaded': 3.9696616389396358, 'minutes_delta_quiet': 3.969769591266317}
- case_5_market_only: {'delta_hash_m1': '3297fe279984ab68', 'delta_hash_m2': '3297fe279984ab68', 'feature_vectors_equal': True}
- case_6_no_change: {'delta_hash_a': '3297fe279984ab68', 'delta_hash_b': '3297fe279984ab68', 'feature_vectors_equal': True}

## After-game scoring

```json
{
  "outcome": "pending",
  "blocker": "no after-game scoring summary found for as_of_date=2026-08-22"
}
```

## Rolling Derek benchmark

```json
{
  "outcome": "pending",
  "blocker": "no rolling Derek benchmark found for as_of_date=2026-08-22"
}
```

## Files to inspect

- champion_pointer: `artifacts/models/registry/champion_pointer.json`
- contextual challenger dir: `artifacts/models/challengers/2026-08-22_direct_lineup_contextual`
- train_manifest: `artifacts/models/challengers/2026-08-22_direct_lineup_contextual/train_manifest.json`
- no_leakage_manifest: `artifacts/models/challengers/2026-08-22_direct_lineup_contextual/no_leakage_manifest.json`
- promotion_decision: `artifacts/models/challengers/2026-08-22_direct_lineup_contextual/promotion_decision.json`
- validation_report: `artifacts/phase13s/validation_gates_report.json`
- contextual_no_leakage_manifest: `artifacts/models/challengers/2026-08-22_direct_lineup_contextual/no_leakage_manifest.json`
- Phase 13S sensitivity: `artifacts/phase13s/direct_lineup_pmf_sensitivity.json`
- Phase 13S no-leakage report: `artifacts/phase13s/no_leakage_report.json`
- Derek snapshot E2E: `artifacts/automation_health/derek_production_live_e2e_<date>.json`

## PMF variance experience study

- Latest study: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/pmf_variance_experience_2026-08-22.md
- This is an actuarial-style actual-to-expected study for settled rows. It checks PMF mean calibration, PMF variance calibration, quantile coverage, and model-vs-market scoring. In the first settled samples, PMF variance is reasonably close overall, but the model under-projects means and trails market on Brier/logloss, so this is a diagnostic and improvement report rather than a market-superiority claim.

## Pending items

PMF NLL / RPS / ECE / p0 calibration / mean bias / tail calibration are reported once nightly post-game scoring produces realized outcomes. The Phase 13S/13T after-game scoring writes DEREK_LIVE_SNAPSHOT_SCORING_PENDING when outcomes are not yet available.
