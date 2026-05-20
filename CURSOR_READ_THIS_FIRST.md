# READ THIS FIRST — NBA PMF Production Repair

You are Cursor Agent working in:

`/Users/josephshackelford/repos/nba-player-props-model-pmf-fix`

This is a high-stakes production repair. Work in phases. Do **not** make one giant unreviewable patch.

## Prime directive

Make `.github/workflows/nba_pmf_delivery.yml` the single coordinated production pipeline **without breaking the existing model**.

You must preserve:
- model-only PMFs
- role/stat calibration
- injury and lineup context
- Phase 8 calibration/diagnostics
- Phase 13O/P/Q/R/S chain
- after-game scoring
- Derek and Wizard of Odds deliveries
- CSV-size delivery contracts
- existing benchmark gates

## Non-negotiables

Do not touch:

`deliveries/*/derek_forward_feed/derek_unique_props_summary.csv`

Do not:
- fabricate PMFs
- fabricate odds
- fabricate BDL props
- fabricate injuries
- fabricate lineups
- fabricate player outcomes
- market-anchor `MODEL_ONLY` PMFs
- delete old workflows
- disable old workflows until the new workflow passes a full production day
- claim market superiority unless the mathematical gates pass

## Required work style

1. Inventory existing workflows and scripts first.
2. Reuse existing production entrypoints.
3. Do not invent script arguments. Inspect argparse or old workflows first.
4. Add tests before or alongside changes.
5. Run validation before commit.
6. If a market-superiority/calibration gate fails, do **not** fake success. Block promotion and write diagnostics.

## Success definition

Daily `deliveries/YYYY-MM-DD/` folders are populated by the new workflow only after contracts pass:
- canonical model-only PMFs present
- WoO exports present
- Derek outputs present
- after-game scoring present when outcomes are available
- calibration and market benchmark reports present
- user-facing CSVs are viewable or split/previewed
- no protected Derek unique summary mutation
