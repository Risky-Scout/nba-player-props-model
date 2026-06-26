# Derek Live Champion Model Readiness — 2026-06-26

- generated_at_utc: 2026-06-26T06:21:57+00:00
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| champion_pointer_present | yes | artifacts/models/registry/champion_pointer.json |
| champion_pointer_rich_fields_present | yes | all rich fields present |
| trained_through_date_no_later_than_yesterday | yes | trained_through=2026-06-24 yesterday=2026-06-25 |
| calibrated_through_date_no_later_than_yesterday | yes | calibrated_through=2026-06-24 yesterday=2026-06-25 |
| calibrated_through_ge_trained_through | yes | trained=2026-06-24 calibrated=2026-06-24 |
| pointer_flag:leakage_checks_passed | yes | value=True |
| pointer_flag:no_future_rows_verified | yes | value=True |
| champion_not_dry_run_or_synthetic | yes | promotion_decision_id='phase13s-promotion-2026-06-24_direct_lineup_contextual-20260625T103851' |

## Facts

```json
{
  "calibrated_through_date": "2026-06-24",
  "champion_model_id": "challenger-2026-06-24",
  "champion_pointer_hash": "b031064ec8b9767e3537eda9080c09c0",
  "delivery_date_minus_one_utc": "2026-06-25",
  "trained_through_date": "2026-06-24"
}
```
