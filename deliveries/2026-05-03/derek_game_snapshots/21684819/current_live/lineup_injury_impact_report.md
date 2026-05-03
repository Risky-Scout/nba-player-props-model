# Magic @ Pistons — Lineup & injury impact

## Summary

- Lineup confirmed: **False**
- BDL lineup fetch: `no_rows_returned` (rows=0)
- BDL injury fetch: `deferred_to_predict_pipeline` (rows=0)
- Official lineup context supplied: **False**
- Injury context supplied: **True**
- Game context supplied: **True**

BDL did not return confirmed lineup rows at this timestamp, so this snapshot is a best-available baseline. Rows therefore reflect lagged-proxy starter status, not live confirmation.

## Counts

- Confirmed starters: **0**
- Confirmed bench: **0**
- Confirmed out: **0**
- Non-actionable: **0**

## Technical audit details

- Game ID: `21684819`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Lineup blocker: `no rows returned by BDL lineups endpoint (lineups not posted yet)`
- Injury blocker: `no rows returned by BDL lineups endpoint (lineups not posted yet)`
