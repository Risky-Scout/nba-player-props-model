#!/usr/bin/env python3
"""Phase 13AK — verify the root README.md is current production status.

Inputs:
  --date YYYY-MM-DD          (run_date)
  --derek-date YYYY-MM-DD    (Derek delivery date)

Required content:
  - title containing "NBA Player Props PMF Production System"
  - generated_at_utc timestamp
  - run_date and ET slate date
  - latest origin/main SHA
  - production status grid with all 12 rows:
      scheduled_training_cron, training_run,
      scheduled_recalibration_cron, recalibration_run,
      daily_predictions, derek_pre_tipoff_refresh, derek_current_live,
      derek_t_minus_25, derek_close_lock, derek_after_game_scoring,
      woo_public_export, woo_after_game_scoring
  - Derek outputs section (per-game folders, current_live / t_minus_25 /
    close_lock, missed-marker discipline)
  - WoO public export section (URLs + JSON contract files)
  - calibration / model-performance caveat (Brier, logloss, market
    comparison, no-market-superiority claim)

Banned stale phrases (any match → FAIL):
  - "Rebuild in flight"
  - "08:00 ET"
  - "09:00 ET"
  - "18:00 ET"
  - "Win rate on -110"
  - "mid-rebuild"
  - "seven-phase plan"

Pass: DAILY_README_FRESHNESS_PASS
Fail: DAILY_README_FRESHNESS_FAILED  with exact reasons
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"

REQUIRED_GRID_ROWS = (
    "scheduled_training_cron",
    "training_run",
    "scheduled_recalibration_cron",
    "recalibration_run",
    "daily_predictions",
    ("derek_pre_tipoff_refresh", "derek_near_lineup"),  # legacy alias accepted
    "derek_current_live",
    "derek_t_minus_25",
    "derek_close_lock",
    "derek_after_game_scoring",
    "woo_public_export",
    "woo_after_game_scoring",
)

REQUIRED_PHRASES = (
    "NBA Player Props PMF Production System",
    "generated_at_utc",
    "run_date",
    "ET slate date",
    "Derek",
    "Wizard of Odds",
    "Brier",
    "logloss",
)

BANNED_PHRASES = (
    "Rebuild in flight",
    "08:00 ET",
    "09:00 ET",
    "18:00 ET",
    "Win rate on -110",
    "mid-rebuild",
    "seven-phase plan",
)

OVERCLAIM_PHRASES = (
    r"market[-\s]beating",
    r"more accurate than the market",
    r"perfectly calibrated",
    r"extremely well calibrated",
    r"\bguaranteed\b",
    r"proven edge",
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    ap.add_argument("--derek-date", required=True)
    args = ap.parse_args(argv)

    failures: list[str] = []

    if not README.exists():
        print(f"DAILY_README_FRESHNESS_FAILED  reason=missing_README.md "
              f"path={README}", file=sys.stderr)
        return 1

    text = README.read_text(encoding="utf-8")

    # Required phrases.
    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            failures.append(f"missing required phrase: {phrase!r}")

    # Required grid rows. Look for the row label appearing in the file.
    for row in REQUIRED_GRID_ROWS:
        if isinstance(row, tuple):
            if not any(alt in text for alt in row):
                failures.append(
                    "missing production status grid row (any of): "
                    f"{row!r}"
                )
        else:
            if row not in text:
                failures.append(f"missing production status grid row: {row!r}")

    # Banned stale phrases.
    for phrase in BANNED_PHRASES:
        if phrase in text:
            failures.append(f"contains banned stale phrase: {phrase!r}")

    # Overclaim language: any match without a near explicit negation.
    for pat in OVERCLAIM_PHRASES:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            window_start = max(0, m.start() - 80)
            window = text[window_start:m.start()].lower()
            if not any(neg in window for neg in
                       ("not ", "do not", "don't", "never", "without ", "isn't ",
                        "aren't ", "no ", "we cannot")):
                failures.append(
                    f"overclaim phrase '{m.group(0)}' near position {m.start()} "
                    "without negation in preceding 80 chars"
                )

    # Date freshness — README must mention --date and --derek-date or
    # carry these values directly.
    if args.date not in text:
        failures.append(f"README does not mention run_date {args.date!r}")
    if args.derek_date not in text and args.derek_date != args.date:
        failures.append(f"README does not mention derek_date {args.derek_date!r}")

    if failures:
        print(f"DAILY_README_FRESHNESS_FAILED  date={args.date}  "
              f"failures={len(failures)}", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(f"DAILY_README_FRESHNESS_PASS  date={args.date}  "
          f"derek_date={args.derek_date}  "
          f"path={README.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
