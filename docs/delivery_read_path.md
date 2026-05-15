# Delivery read path (minutes + PMFs)

Use this map when integrating daily outputs. Replace `{date}` with the slate (e.g. `2026-05-15`).

## Canonical model / market envelope (trust when manifest passes)

- **Primary**: `deliveries/{date}/canonical_source/all_props_model_only.parquet`  
  One row per **player × game × stat × role_bucket** that survived publication/eligibility gates. Columns include **`minutes_mean`**, **`line`**, market fields (**`market_fair_over_prob`**, **`market_source`**, **`market_offered_odds`**), **`pmf_source`**, **`pmf_active`**, **`support_min`** / **`support_max`**, **`stat`**, ids (**`player_id`**, **`game_id`**, **`team_id`**). Treat as SOT **only after** root `deliveries/{date}/manifest.json` has **`status`** success (e.g. `"passed"`); if it **`failed`**, read for debugging only.

- Root manifest: **`deliveries/{date}/manifest.json`** — **`status`**, **`failures`**, and **`notes`** (row counts) are authoritative for publishability.

- **Absent rows**: canonically joined rows exclude ineligible/out-of-scope player-games **by design**; do not expect full roster coverage.

## Minutes (two scopes)

| Scope | Path |
|-------|------|
| **Universe / roster-wide** | `artifacts/minutes_predictions/{date}/minutes_predictions.parquet` |
| **Publication-eligible slice** | `artifacts/minutes_predictions/{date}/minutes_predictions_eligible.parquet` |

The eligible slice is narrower than the roster universe. CI and validators may require **both** files to exist **before** PMF pipelines run.

A **`manifest.json`** beside the parquet (if present) carries run metadata; use it alongside row-count checks.

## P > line (tails vs booked line)

- Booked **`line`** is on **`all_props_model_only.parquet`** and on the richer review export below.

- For **numeric over tails** (**`model_p_over`**) and **`p_ge_<k>`** ladders (`k` aligns with discrete outcome support), use:  
  **`deliveries/{date}/pmf_model_review_package/machine_readable/model_only.parquet`** — join on **`game_id`**, **`player_id`**, **`stat`**, **`line`** / **`book`**, **`role_bucket`** as needed.

- **`pmf_json`** in that machine-readable row carries full discrete masses when tails are insufficient.

Other exports (`wizard_of_odds/full_pmfs_*.parquet`, `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet`) are downstream or channel-specific; use when your downstream contract references them.

