# Derek/WoO Champion Dependency Verification

- generated_at_utc: 2026-05-04T09:05:10+00:00
- max_stale_days: 14
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| champion_pointer_present | yes | model_version='challenger-2026-04-30' |
| champion_calibrators_present | yes | ok |
| champion_freshness | yes | age_days=2.84 max=14 |
| delivery_scripts_no_challenger_refs | yes | ok |
| delivery_scripts_reference_champion_path | yes | 4/6 delivery scripts reference champion path (via direct path or nba_props_model package import) |
| latest_delivery_after_champion_promotion | yes | delivery_generated_at=None promoted_at_utc='2026-05-01T12:48:39+00:00' (advisory) |
| delivery_records_champion_id_strict | yes | ok |
| delivery_does_not_use_stale_calibrators | yes | no per-stat hashes in pointer.data_hashes; deferred until first real promotion (advisory) |

## Facts

```
{
  "champion_model_version": "challenger-2026-04-30",
  "champion_calibrator_version": "phase8-role-bucket",
  "champion_promoted_at_utc": "2026-05-01T12:48:39+00:00",
  "champion_model_dir": "artifacts/models",
  "champion_trained_through_date": "2026-04-30",
  "champion_calibrated_through_date": "2026-04-30",
  "champion_calibrator_sha_prefixes": {
    "pts": "cef39bbf256f2d63",
    "reb": "4b018db3bff8f827",
    "ast": "aa73d678b1512d33",
    "fg3m": "6fb662716667fed4",
    "tov": "5b9d732536e30e33"
  },
  "champion_age_days": 2.84,
  "delivery_scripts_with_champion_refs": [
    "build_daily_pmf_delivery.py",
    "run_daily_delivery_pipeline.py",
    "predict.py",
    "build_stat_grid_pmfs.py"
  ],
  "latest_delivery_date": "2026-05-03",
  "latest_delivery_generated_at": null,
  "delivery_date_checked": "2026-05-03",
  "champion_pointer_hash": "125eb260dc642bd3b26878f8e407bffd",
  "delivery_manifest_stamped": {
    "woo": {
      "path": "deliveries/2026-05-03/wizard_of_odds/run_manifest.json",
      "champion_model_id": "challenger-2026-04-30",
      "trained_through_date": "2026-04-30",
      "calibrated_through_date": "2026-04-30",
      "champion_pointer_hash": "125eb260dc642bd3b26878f8e407bffd",
      "model_source": "champion_pointer",
      "no_challenger_artifacts_used": true,
      "model_version": "a9bdb1c#phase10c"
    },
    "derek": {
      "path": "deliveries/2026-05-03/derek_forward_feed/feed_manifest.json",
      "champion_model_id": "challenger-2026-04-30",
      "trained_through_date": "2026-04-30",
      "calibrated_through_date": "2026-04-30",
      "champion_pointer_hash": "125eb260dc642bd3b26878f8e407bffd",
      "model_source": "champion_pointer",
      "no_challenger_artifacts_used": true,
      "model_version": null
    }
  },
  "champion_calibrator_actual_sha_prefixes": {
    "pts": "cef39bbf256f2d63",
    "reb": "4b018db3bff8f827",
    "ast": "aa73d678b1512d33",
    "fg3m": "6fb662716667fed4",
    "tov": "5b9d732536e30e33"
  }
}
```
