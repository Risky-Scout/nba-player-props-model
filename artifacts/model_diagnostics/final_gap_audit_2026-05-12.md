# Final gap audit — 2026-05-12

Machine-readable twin: `final_gap_audit_2026-05-12.json`.

## Summary

| Area | Status |
|------|--------|
| 12-stat delivery + RA in outputs | Verified (Phase A gate) |
| RA combo OOF + `pmf_cal_role_ra.pkl` | **Complete** (rebuilt `oof_combo_pmfs`, ran `fit_combo_pmf_calibrators`) |
| Event-market join (odds ↔ model PMF) | **Patched** — canonical fallback + name→`player_id` map; **466** matched rows for 2026-05-12 |
| Scored event rows (G3 gate) | **Blocked locally** — `player_game_stats` has **no** rows for `2026-05-12` (max date **2026-05-09**), so `scored_all_fields=0` |
| Phase D–F (full feature registry, minutes GBM, sparse hurdle, monotone CDF) | **Missing / not implemented** — see JSON items 12–20 |
| Phase G source recalibration optimizer | **Started** — long-running; verify scripts not re-run in this session |

## Critical blockers for market superiority proof

1. **No local box scores** for slate `2026-05-12` → cannot produce binary `hit_result` / logloss / Brier on outcomes for that date.
2. **Insufficient stat-role sample** in superiority report until (1) is fixed and joins remain stable.

Do **not** claim `MARKET_SUPERIORITY_BY_STAT_ROLE_CONTRACT_PASS` until the strict verifier prints it.
