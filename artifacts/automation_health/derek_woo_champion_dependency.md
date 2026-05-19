# Derek/WoO Champion Dependency Verification

- generated_at_utc: 2026-05-19T19:17:12+00:00
- max_stale_days: 14
- fail_stale_days: 30
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| champion_pointer_present | yes | model_version='sim-2099-12-31' |
| champion_calibrators_present | yes | ok |
| champion_freshness | yes | age_days=0.86 max=14 |
| delivery_scripts_no_challenger_refs | yes | ok |
| delivery_scripts_reference_champion_path | yes | 5/6 delivery scripts reference champion path (via direct path or nba_props_model package import) |
| latest_delivery_after_champion_promotion | yes | delivery_generated_at=None promoted_at_utc='2026-05-18T22:40:27+00:00' (advisory) |
| delivery_records_champion_id_strict | yes | ok |
| delivery_does_not_use_stale_calibrators | yes | no per-stat hashes in pointer.data_hashes; deferred until first real promotion (advisory) |

## Facts

```
{
  "champion_model_version": "sim-2099-12-31",
  "champion_calibrator_version": "phase8-role-bucket",
  "champion_promoted_at_utc": "2026-05-18T22:40:27+00:00",
  "champion_model_dir": "artifacts/models",
  "champion_trained_through_date": "2099-12-31",
  "champion_calibrated_through_date": "2099-12-31",
  "champion_calibrator_sha_prefixes": {
    "pts": "4133ebd730cec6bf",
    "reb": "ef761e201f32102e",
    "ast": "95739abbefc7e55b",
    "fg3m": "57edf14dad60a827",
    "tov": "deedd3f0ed6faedd",
    "stl": "69a0f01a30bf81f5",
    "blk": "34f3b048d3e97119",
    "stocks": "f54ae753a28490c2",
    "pa": "2ced7ccd5383fdbe",
    "pr": "0d091c820124d5a6",
    "ra": "d8c6e66391adbc04",
    "pra": "49b237508620484b"
  },
  "champion_age_days": 0.86,
  "delivery_scripts_with_champion_refs": [
    "build_daily_pmf_delivery.py",
    "build_derek_forward_feed.py",
    "run_daily_delivery_pipeline.py",
    "predict.py",
    "build_stat_grid_pmfs.py"
  ],
  "latest_delivery_date": "2026-05-19",
  "latest_delivery_generated_at": null,
  "delivery_date_checked": "2026-05-18",
  "champion_pointer_hash": "dfd4615c99bf495666b0dbd3c4c12f32",
  "delivery_manifest_stamped": {
    "woo": {
      "path": "deliveries/2026-05-18/wizard_of_odds/run_manifest.json",
      "champion_model_id": "sim-2099-12-31",
      "trained_through_date": "2099-12-31",
      "calibrated_through_date": "2099-12-31",
      "champion_pointer_hash": "dfd4615c99bf495666b0dbd3c4c12f32",
      "model_source": "champion_pointer",
      "no_challenger_artifacts_used": true,
      "model_version": "ae210a4f#phase10c"
    },
    "derek": {
      "path": "deliveries/2026-05-18/derek_forward_feed/feed_manifest.json",
      "champion_model_id": "sim-2099-12-31",
      "trained_through_date": "2099-12-31",
      "calibrated_through_date": "2099-12-31",
      "champion_pointer_hash": "dfd4615c99bf495666b0dbd3c4c12f32",
      "model_source": "champion_pointer",
      "no_challenger_artifacts_used": true,
      "model_version": null
    }
  },
  "champion_calibrator_actual_sha_prefixes": {
    "pts": "4133ebd730cec6bf",
    "reb": "ef761e201f32102e",
    "ast": "95739abbefc7e55b",
    "fg3m": "57edf14dad60a827",
    "tov": "deedd3f0ed6faedd",
    "stl": "69a0f01a30bf81f5",
    "blk": "34f3b048d3e97119",
    "stocks": "f54ae753a28490c2",
    "pa": "2ced7ccd5383fdbe",
    "pr": "0d091c820124d5a6",
    "ra": "d8c6e66391adbc04",
    "pra": "49b237508620484b"
  }
}
```
