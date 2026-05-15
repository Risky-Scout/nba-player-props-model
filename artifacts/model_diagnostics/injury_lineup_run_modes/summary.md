# Injury / lineup run-mode audit (2026-05-13)

- pass_all: `False`
- hard_failure_count: `1`
- total_findings: `1`

## Run modes
- morning_expected (2026-05-13): n_rows=0, official_lineup_available_any=False, stale_injury_rows=0, stale_lineup_rows=0
- t25 (2026-05-12): n_rows=32, official_lineup_available_any=False, stale_injury_rows=32, stale_lineup_rows=32
- t5 (2026-05-12): n_rows=32, official_lineup_available_any=False, stale_injury_rows=32, stale_lineup_rows=32
- final_after_game (2026-05-12): n_rows=32, official_lineup_available_any=False, stale_injury_rows=32, stale_lineup_rows=0

## Findings
- [fail] morning_expected SAME_DAY_SOURCE_INPUTS_MISSING: No injury/lineup feature rows were produced; canonical or source inputs are missing for this run mode/date.
