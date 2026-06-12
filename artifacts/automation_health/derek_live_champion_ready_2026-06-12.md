# Derek Live Champion Model Readiness — 2026-06-12

- generated_at_utc: 2026-06-12T20:34:30+00:00
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| champion_pointer_present | yes | artifacts/models/registry/champion_pointer.json |
| champion_pointer_rich_fields_present | yes | all rich fields present |
| trained_through_date_no_later_than_yesterday | yes | trained_through=2026-06-11 yesterday=2026-06-11 |
| calibrated_through_date_no_later_than_yesterday | yes | calibrated_through=2026-06-11 yesterday=2026-06-11 |
| calibrated_through_ge_trained_through | yes | trained=2026-06-11 calibrated=2026-06-11 |
| pointer_flag:leakage_checks_passed | yes | value=True |
| pointer_flag:no_future_rows_verified | yes | value=True |
| champion_not_dry_run_or_synthetic | yes | promotion_decision_id='phase13s-promotion-2026-06-11_direct_lineup_contextual-20260612T141731' |

## Facts

```json
{
  "calibrated_through_date": "2026-06-11",
  "champion_model_id": "challenger-2026-06-11",
  "champion_pointer_hash": "2e953f9c766e826017abf220c563a18d",
  "delivery_date_minus_one_utc": "2026-06-11",
  "trained_through_date": "2026-06-11"
}
```
