# Derek/WoO Champion Dependency Verification

- generated_at_utc: 2026-05-01T11:37:42+00:00
- max_stale_days: 14
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| champion_pointer_present | yes | model_version='2026-03-09-v12' |
| champion_calibrators_present | yes | ok |
| champion_freshness | yes | age_days=0.55 max=14 |
| delivery_scripts_no_challenger_refs | yes | ok |
| delivery_scripts_reference_champion_path | yes | 4/6 delivery scripts reference champion path (via direct path or nba_props_model package import) |
| latest_delivery_after_champion_promotion | yes | delivery_generated_at=None promoted_at_utc='2026-04-30T22:30:59+00:00' (advisory) |
| delivery_records_champion_id | yes | pointer_model_version='2026-03-09-v12' delivery_records=['6aea017#phase10c'] format_match=False (format-alignment is a Phase 13H follow-up) |

## Facts

```
{
  "champion_model_version": "2026-03-09-v12",
  "champion_calibrator_version": "phase8-role-bucket",
  "champion_promoted_at_utc": "2026-04-30T22:30:59+00:00",
  "champion_model_dir": "artifacts/models",
  "champion_trained_through_date": null,
  "champion_calibrated_through_date": null,
  "champion_calibrator_sha_prefixes": {
    "pts": "cef39bbf256f2d63",
    "reb": "4b018db3bff8f827",
    "ast": "aa73d678b1512d33",
    "fg3m": "6fb662716667fed4",
    "tov": "5b9d732536e30e33"
  },
  "champion_age_days": 0.55,
  "delivery_scripts_with_champion_refs": [
    "build_daily_pmf_delivery.py",
    "run_daily_delivery_pipeline.py",
    "predict.py",
    "build_stat_grid_pmfs.py"
  ],
  "latest_delivery_date": "2026-04-30",
  "latest_delivery_generated_at": null,
  "delivery_manifest_id_fields": {
    "deliveries/2026-04-30/wizard_of_odds/run_manifest.json::model_version": "6aea017#phase10c"
  }
}
```
