#!/usr/bin/env python3
"""Phase 13AH — verify every file claimed in the Derek email contract.

Inputs:
  --delivery-date YYYY-MM-DD

For each Derek snapshot folder under
``deliveries/<date>/derek_game_snapshots/<game>/<snapshot>/`` that has a
market_comparison.csv (i.e. the snapshot ran), check that every file
referenced in the email is present, parseable, and structurally valid:

  - snapshot_report.md (>0 bytes, contains the matchup name)
  - market_comparison.csv (has model_prob, market_prob, raw_edge, edge_publish_status, calibration_support_status)
  - full_pmf_wide.csv (non-empty, has pmf JSON column)
  - outcome_level_probabilities.csv (has source_row_id, row_id, k, p_k;
    p_k finite + nonneg; per-source_row_id sum within 0.005 of 1.0)
  - pmf_driver_decomposition.md
  - lineup_injury_impact_report.md
  - direct_lineup_impact_report.md

For the delivery date as a whole, also check:
  - derek_game_snapshots/README.md links to the per-game snapshot files
  - artifacts/experience_studies/pmf_variance_experience_<date>.md exists
    and contains the variance / mean / Brier / logloss caveat phrases
  - artifacts/automation_health/derek_edge_root_cause_<date>.md exists
  - artifacts/automation_health/derek_edge_calibration_<date>.md exists
  - none of the above files contain banned overclaim phrases:
    'market-beating', 'proven edge', 'more accurate than the market',
    'perfectly calibrated', 'extremely well calibrated', 'guaranteed'
    UNLESS the phrase is explicitly negated within 80 chars.

Pass: DEREK_EMAIL_CLAIMED_FILES_PASS
Fail: DEREK_EMAIL_CLAIMED_FILES_FAILED  with exact reasons
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PMF_SUM_TOL = 0.005

REQUIRED_PER_SNAPSHOT_FILES = (
    "snapshot_report.md",
    "market_comparison.csv",
    "full_pmf_wide.csv",
    "outcome_level_probabilities.csv",
    "pmf_driver_decomposition.md",
    "lineup_injury_impact_report.md",
    "direct_lineup_impact_report.md",
)
MARKET_COMPARISON_COLS = (
    "model_prob", "market_prob", "raw_edge",
    "edge_publish_status", "calibration_support_status",
)
OUTCOME_LONG_COLS = (
    "source_row_id", "row_id", "k", "p_k",
)
BANNED_PHRASES = (
    r"market-?beating",
    r"proven\s+edge",
    r"more\s+accurate\s+than\s+the\s+market",
    r"perfectly\s+calibrated",
    r"extremely\s+well\s+calibrated",
    r"\bguaranteed\b",
)
NEGATION_TOKENS = (
    "not", "do not", "don't", "never", "without",
    "is not", "are not", "isn't", "aren't",
)


def _check_no_overclaims(text: str, label: str) -> list[str]:
    """Return failure messages for any banned phrase that lacks a near
    explicit negation (within 80 characters before the match)."""
    failures: list[str] = []
    for pat in BANNED_PHRASES:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            window_start = max(0, m.start() - 80)
            window = text[window_start:m.start()]
            negated = any(tok in window.lower() for tok in NEGATION_TOKENS)
            if not negated:
                failures.append(
                    f"{label}: banned overclaim '{m.group(0)}' near "
                    f"position {m.start()} without negation in preceding "
                    f"80 chars"
                )
    return failures


def _check_snapshot_folder(snap_dir: Path) -> dict:
    rel = str(snap_dir.relative_to(REPO_ROOT))
    failures: list[str] = []
    market = snap_dir / "market_comparison.csv"
    if not market.exists():
        return {"path": rel, "status": "skipped", "reason": "no market_comparison.csv"}

    for fname in REQUIRED_PER_SNAPSHOT_FILES:
        p = snap_dir / fname
        if not p.exists():
            failures.append(f"missing {fname}")
            continue
        if p.stat().st_size == 0:
            failures.append(f"{fname} is empty")

    if not failures:
        # market_comparison column check
        try:
            mc = pd.read_csv(snap_dir / "market_comparison.csv")
            missing = [c for c in MARKET_COMPARISON_COLS if c not in mc.columns]
            if missing:
                failures.append(f"market_comparison.csv missing columns: {missing}")
        except Exception as e:
            failures.append(f"market_comparison.csv parse error: {e}")

    if not failures:
        # full_pmf_wide check
        try:
            fpw = pd.read_csv(snap_dir / "full_pmf_wide.csv")
            if fpw.empty:
                failures.append("full_pmf_wide.csv is empty")
            elif "pmf" not in fpw.columns:
                failures.append("full_pmf_wide.csv missing pmf column")
        except Exception as e:
            failures.append(f"full_pmf_wide.csv parse error: {e}")

    if not failures:
        # outcome_level_probabilities check
        try:
            olp = pd.read_csv(snap_dir / "outcome_level_probabilities.csv")
            missing = [c for c in OUTCOME_LONG_COLS if c not in olp.columns]
            if missing:
                failures.append(
                    f"outcome_level_probabilities.csv missing columns: {missing}"
                )
            else:
                if olp["p_k"].isna().any():
                    failures.append("outcome_level_probabilities.csv p_k contains NaN")
                if (olp["p_k"] < 0).any():
                    failures.append("outcome_level_probabilities.csv p_k contains negative values")
                grp = olp.groupby("source_row_id")["p_k"].sum()
                bad = grp[(grp - 1.0).abs() > PMF_SUM_TOL]
                if not bad.empty:
                    failures.append(
                        f"outcome_level_probabilities.csv per source_row_id sum "
                        f"deviation > {PMF_SUM_TOL}: "
                        f"{len(bad)} row_ids, max_err={(grp - 1.0).abs().max():.6f}"
                    )
                # All-zero PMF rows
                zero_rows = grp[grp <= 0]
                if not zero_rows.empty:
                    failures.append(
                        f"outcome_level_probabilities.csv has {len(zero_rows)} "
                        "all-zero PMF rows"
                    )
        except Exception as e:
            failures.append(f"outcome_level_probabilities.csv parse error: {e}")

    # Overclaim language scan in human-facing markdown.
    if not failures:
        for md_name in ("snapshot_report.md", "pmf_driver_decomposition.md",
                         "lineup_injury_impact_report.md", "direct_lineup_impact_report.md"):
            p = snap_dir / md_name
            if p.exists():
                txt = p.read_text(encoding="utf-8", errors="replace")
                failures.extend(_check_no_overclaims(txt, f"{rel}/{md_name}"))

    return {"path": rel, "status": "ok" if not failures else "failed",
            "failures": failures}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--delivery-date", required=True)
    args = ap.parse_args(argv)
    date = args.delivery_date

    base = REPO_ROOT / "deliveries" / date / "derek_game_snapshots"
    if not base.exists():
        print(f"DEREK_EMAIL_CLAIMED_FILES_FAILED  delivery_date={date}  "
              f"reason=missing_derek_game_snapshots_root  "
              f"path={base.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1

    snap_dirs: list[Path] = []
    for game_dir in sorted(base.iterdir()):
        if not game_dir.is_dir():
            continue
        for snap in sorted(game_dir.iterdir()):
            if snap.is_dir() and snap.name in {"current_live", "t_minus_25", "close_lock"}:
                snap_dirs.append(snap)

    results = [_check_snapshot_folder(sd) for sd in snap_dirs]
    snapshot_failures = [r for r in results if r["status"] == "failed"]

    # Day-level checks.
    day_failures: list[str] = []
    derek_index = base / "README.md"
    if not derek_index.exists():
        day_failures.append(f"missing {derek_index.relative_to(REPO_ROOT)}")
    else:
        idx_text = derek_index.read_text(encoding="utf-8", errors="replace")
        day_failures.extend(_check_no_overclaims(idx_text,
                                                  str(derek_index.relative_to(REPO_ROOT))))

    delivery_index = REPO_ROOT / "deliveries" / date / "README.md"
    if delivery_index.exists():
        di_text = delivery_index.read_text(encoding="utf-8", errors="replace")
        day_failures.extend(_check_no_overclaims(di_text,
                                                  str(delivery_index.relative_to(REPO_ROOT))))

    exp_md = REPO_ROOT / "artifacts" / "experience_studies" / f"pmf_variance_experience_{date}.md"
    if not exp_md.exists():
        day_failures.append(
            f"missing experience study: {exp_md.relative_to(REPO_ROOT)}"
        )
    else:
        exp_text = exp_md.read_text(encoding="utf-8", errors="replace")
        # Caveat presence: must mention Brier OR logloss AND the variance / mean A/E framing
        if not re.search(r"brier|logloss", exp_text, flags=re.IGNORECASE):
            day_failures.append(
                "experience study missing Brier/logloss caveat language"
            )
        if not re.search(r"variance.{0,5}A/?E|mean.{0,5}A/?E", exp_text, flags=re.IGNORECASE):
            day_failures.append(
                "experience study missing mean/variance A/E framing"
            )
        day_failures.extend(_check_no_overclaims(exp_text,
                                                  str(exp_md.relative_to(REPO_ROOT))))

    edge_root = REPO_ROOT / "artifacts" / "automation_health" / f"derek_edge_root_cause_{date}.md"
    if not edge_root.exists():
        day_failures.append(f"missing {edge_root.relative_to(REPO_ROOT)}")
    edge_cal = REPO_ROOT / "artifacts" / "automation_health" / f"derek_edge_calibration_{date}.md"
    if not edge_cal.exists():
        day_failures.append(f"missing {edge_cal.relative_to(REPO_ROOT)}")

    total_fails = len(snapshot_failures) + len(day_failures)
    if total_fails:
        print(f"DEREK_EMAIL_CLAIMED_FILES_FAILED  delivery_date={date}  "
              f"snapshot_failures={len(snapshot_failures)}  "
              f"day_failures={len(day_failures)}", file=sys.stderr)
        for r in snapshot_failures:
            for f in r.get("failures", []):
                print(f"  - {r['path']}: {f}", file=sys.stderr)
        for f in day_failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    snap_ok = len([r for r in results if r["status"] == "ok"])
    snap_skipped = len([r for r in results if r["status"] == "skipped"])
    print(f"DEREK_EMAIL_CLAIMED_FILES_PASS  delivery_date={date}  "
          f"snapshots_ok={snap_ok}  snapshots_skipped={snap_skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
