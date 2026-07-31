# Derek Live Champion Model Readiness — 2026-07-31

- generated_at_utc: 2026-07-31T18:08:43+00:00
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| champion_pointer_present | yes | artifacts/models/registry/champion_pointer.json |
| champion_pointer_rich_fields_present | yes | all rich fields present |
| trained_through_date_no_later_than_yesterday | yes | trained_through=2026-07-30 yesterday=2026-07-30 |
| calibrated_through_date_no_later_than_yesterday | yes | calibrated_through=2026-07-30 yesterday=2026-07-30 |
| calibrated_through_ge_trained_through | yes | trained=2026-07-30 calibrated=2026-07-30 |
| pointer_flag:leakage_checks_passed | yes | value=True |
| pointer_flag:no_future_rows_verified | yes | value=True |
| champion_not_dry_run_or_synthetic | yes | promotion_decision_id='phase13s-promotion-2026-07-30_direct_lineup_contextual-20260731T101949' |

## Facts

```json
{
  "calibrated_through_date": "2026-07-30",
  "champion_model_id": "challenger-2026-07-30",
  "champion_pointer_hash": "6707cda3d94ec4f7d2a51c0ba39b9ce8",
  "delivery_date_minus_one_utc": "2026-07-30",
  "trained_through_date": "2026-07-30"
}
```
