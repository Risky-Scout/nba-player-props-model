# Derek Live Champion Model Readiness — 2026-07-18

- generated_at_utc: 2026-07-18T21:29:54+00:00
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| champion_pointer_present | yes | artifacts/models/registry/champion_pointer.json |
| champion_pointer_rich_fields_present | yes | all rich fields present |
| trained_through_date_no_later_than_yesterday | yes | trained_through=2026-07-17 yesterday=2026-07-17 |
| calibrated_through_date_no_later_than_yesterday | yes | calibrated_through=2026-07-17 yesterday=2026-07-17 |
| calibrated_through_ge_trained_through | yes | trained=2026-07-17 calibrated=2026-07-17 |
| pointer_flag:leakage_checks_passed | yes | value=True |
| pointer_flag:no_future_rows_verified | yes | value=True |
| champion_not_dry_run_or_synthetic | yes | promotion_decision_id='phase13s-promotion-2026-07-17_direct_lineup_contextual-20260718T092512' |

## Facts

```json
{
  "calibrated_through_date": "2026-07-17",
  "champion_model_id": "challenger-2026-07-17",
  "champion_pointer_hash": "002cb269bcb920291fd16199c7103b1f",
  "delivery_date_minus_one_utc": "2026-07-17",
  "trained_through_date": "2026-07-17"
}
```
