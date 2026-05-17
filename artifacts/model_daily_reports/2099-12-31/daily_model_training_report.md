# Daily model training / recalibration report — 2099-12-31

- generated_at_utc: 2026-05-17T17:03:32+00:00Z

## Headline

- active_champion_model_id: `sim-2099-12-31`
- feature_set_id: `None`
- is_phase13s_direct_lineup_driver: **False**
- trained_through_date: `2099-12-31`
- calibrated_through_date: `2099-12-31`
- retraining_ran: **False**
- recalibration_ran: **False**
- no_leakage_passed: **False**
- validation_gates_passed: **False**
- challenger_promoted: **False**
- promotion_reason: `promotion_decision_missing_or_unparseable`

## Active champion (full pointer block)

- champion_model_id: `sim-2099-12-31`
- feature_set_id: `None`
- direct_lineup_pmf_driver: `None`
- contextual_pmf_engine: `None`
- trained_through_date: `2099-12-31`
- calibrated_through_date: `2099-12-31`
- training_run_id: `nightly-20991231`
- calibration_manifest_path: `artifacts/models/challengers/2099-12-31/calibration_manifest.json`
- train_manifest_path: `artifacts/models/challengers/2099-12-31/train_manifest.json`
- validation_report_path: `artifacts/models/challengers/2099-12-31/validation_report.json`
- promotion_decision_path: `artifacts/models/challengers/2099-12-31/promotion_decision.json`
- no_leakage_manifest_path: `None`
- promotion_decision_id: `promotion-2099-12-31-20260516T222858`

## Promotion status

- promoted: **False**
- decision_promote_field: `None`
- manifest_promoted_field: `None`
- champion_pointer_swapped_to_today: **False**
- expected_today_challenger_id: `challenger-2099-12-31`
- active_champion_model_id: `sim-2099-12-31`
- promotion_reason: `promotion_decision_missing_or_unparseable`

## Validation gates

- any_positive_improvement: **None**
- issues: None
- minutes_min_rel_improvement: `None`
- safe_noninferiority_threshold: `None`

## Per-target metrics (training-time validation)

| target | n_test | rel_improvement |
| --- | ---: | ---: |

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
  "blocker": "no after-game scoring summary found for as_of_date=2099-12-31"
}
```

## Rolling Derek benchmark

```json
{
  "outcome": "pending",
  "blocker": "no rolling Derek benchmark found for as_of_date=2099-12-31"
}
```

## Files to inspect

- champion_pointer: `artifacts/models/registry/champion_pointer.json`
- validation_report: `artifacts/models/challengers/2099-12-31/validation_report.json`
- Phase 13S sensitivity: `artifacts/phase13s/direct_lineup_pmf_sensitivity.json`
- Phase 13S no-leakage report: `artifacts/phase13s/no_leakage_report.json`
- Derek snapshot E2E: `artifacts/automation_health/derek_production_live_e2e_<date>.json`

## PMF variance experience study

- Latest study: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/pmf_variance_experience_2099-12-31.md
- This is an actuarial-style actual-to-expected study for settled rows. It checks PMF mean calibration, PMF variance calibration, quantile coverage, and model-vs-market scoring. In the first settled samples, PMF variance is reasonably close overall, but the model under-projects means and trails market on Brier/logloss, so this is a diagnostic and improvement report rather than a market-superiority claim.

## Pending items

PMF NLL / RPS / ECE / p0 calibration / mean bias / tail calibration are reported once nightly post-game scoring produces realized outcomes. The Phase 13S/13T after-game scoring writes DEREK_LIVE_SNAPSHOT_SCORING_PENDING when outcomes are not yet available.
