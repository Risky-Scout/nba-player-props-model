#!/usr/bin/env python3
"""Phase 13AA — verify the PMF variance experience study artifacts.

Pass conditions:
  - the build script exists;
  - csv / json / md outputs exist for the requested as-of date;
  - rows_total > 0;
  - mean_AE present and finite;
  - variance_AE present and finite;
  - standardized residual mean + sd present;
  - model_brier and market_brier present when market data exists in the run;
  - model_logloss and market_logloss present when market data exists;
  - markdown contains an explicit "do not claim market superiority" caveat
    (or equivalent) when the model trails market on Brier;
  - markdown contains a `t_minus_25` / `close_lock` pending-or-thin-sample
    explanation when those buckets lack settled outcomes;
  - the experience study is linked from Derek delivery README, Derek
    snapshot index README, and the daily model report (when those files
    exist).

Outcomes emitted:
  PMF_VARIANCE_EXPERIENCE_STUDY_PASS    — all checks clean
  PMF_VARIANCE_EXPERIENCE_STUDY_WARN    — model trails market or buckets
                                          are thin, but the report says so
                                          honestly; or links missing in
                                          optional locations
  PMF_VARIANCE_EXPERIENCE_STUDY_FAILED  — missing files, invalid metrics,
                                          parse errors, or dishonest report
                                          language
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_finite_number(x) -> bool:
    if x is None:
        return False
    if isinstance(x, bool):
        return False
    try:
        f = float(x)
    except (TypeError, ValueError):
        return False
    return math.isfinite(f)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of-date", required=True)
    args = ap.parse_args(argv)

    failures: list[str] = []
    warnings: list[str] = []

    build_script = REPO_ROOT / "scripts" / "build_pmf_variance_experience_study.py"
    if not build_script.exists():
        failures.append(f"build script missing: {build_script.relative_to(REPO_ROOT)}")

    out_dir = REPO_ROOT / "artifacts" / "experience_studies"
    csv_path = out_dir / f"pmf_variance_experience_{args.as_of_date}.csv"
    json_path = out_dir / f"pmf_variance_experience_{args.as_of_date}.json"
    md_path = out_dir / f"pmf_variance_experience_{args.as_of_date}.md"

    for p in (csv_path, json_path, md_path):
        if not p.exists():
            failures.append(f"missing artifact: {p.relative_to(REPO_ROOT)}")

    payload: dict | None = None
    if json_path.exists():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            failures.append(f"json parse error: {e}")

    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""

    rows_total = 0
    overall: dict = {}
    market_present = False
    model_trails_market = False

    if payload is not None:
        rows_total = int(payload.get("row_count_settled", 0))
        if rows_total <= 0:
            failures.append(f"row_count_settled must be > 0; got {rows_total}")
        overall = payload.get("overall") or {}

        for k in ("mean_AE", "variance_AE", "std_residual_mean", "std_residual_sd"):
            if not _is_finite_number(overall.get(k)):
                failures.append(f"overall.{k} missing or non-finite: {overall.get(k)!r}")

        market_brier = overall.get("brier_over_market_mean")
        market_logloss = overall.get("logloss_over_market_mean")
        market_present = _is_finite_number(market_brier) or _is_finite_number(market_logloss)

        if market_present:
            for k in ("brier_over_model_mean", "brier_over_market_mean",
                      "logloss_over_model_mean", "logloss_over_market_mean"):
                if not _is_finite_number(overall.get(k)):
                    failures.append(f"overall.{k} missing while market data exists: "
                                    f"{overall.get(k)!r}")
            mb = overall.get("brier_over_model_mean")
            if (_is_finite_number(mb) and _is_finite_number(market_brier)
                    and float(mb) > float(market_brier)):
                model_trails_market = True

    if md_text:
        # Honest no-market-superiority caveat must appear when model trails.
        caveat_patterns = [
            r"do not claim market superiority",
            r"not\s+(?:a\s+)?(?:proof\s+of|claim(?:ing)?(?:\s+broad)?)\s+market\s+superiority",
            r"trails?\s+(?:the\s+)?market",
        ]
        has_caveat = any(re.search(p, md_text, flags=re.IGNORECASE) for p in caveat_patterns)
        if model_trails_market and not has_caveat:
            failures.append("markdown does not contain a no-market-superiority caveat "
                            "while the run shows the model trails market on Brier")

        # Snapshot pending / thin-sample language must appear; t_minus_25
        # and close_lock must be acknowledged.
        for needle in ("t_minus_25", "close_lock"):
            if needle not in md_text:
                failures.append(f"markdown missing reference to `{needle}` "
                                "(live-context limitation explanation required)")
        if not re.search(r"pending|insufficient|thin sample|not yet scored|fabricat",
                         md_text, flags=re.IGNORECASE):
            failures.append("markdown missing pending / insufficient-sample / thin-sample "
                            "explanation for live-snapshot scoring")

    # Link checks — Derek + daily model report.
    derek_readme = REPO_ROOT / "deliveries" / args.as_of_date / "README.md"
    derek_snapshot_readme = (REPO_ROOT / "deliveries" / args.as_of_date
                             / "derek_game_snapshots" / "README.md")
    expected_url_fragment = f"pmf_variance_experience_{args.as_of_date}.md"

    if derek_readme.exists():
        if expected_url_fragment not in derek_readme.read_text(encoding="utf-8"):
            failures.append(f"derek delivery README missing experience-study link: "
                            f"{derek_readme.relative_to(REPO_ROOT)}")
    else:
        warnings.append(f"derek delivery README absent for {args.as_of_date}; "
                        "link check skipped")

    if derek_snapshot_readme.exists():
        if expected_url_fragment not in derek_snapshot_readme.read_text(encoding="utf-8"):
            failures.append(f"derek snapshot README missing experience-study link: "
                            f"{derek_snapshot_readme.relative_to(REPO_ROOT)}")
    else:
        warnings.append(f"derek snapshot README absent for {args.as_of_date}; "
                        "link check skipped")

    # The daily model report is keyed on training-as-of-date which lags the
    # delivery date by 1+ days. Find the most recent daily model report
    # directory that has a markdown and check it has an experience-study
    # link.
    daily_root = REPO_ROOT / "artifacts" / "model_daily_reports"
    daily_dirs = sorted([p for p in daily_root.glob("*/daily_model_training_report.md")])
    if daily_dirs:
        latest_daily = daily_dirs[-1]
        if "pmf_variance_experience" not in latest_daily.read_text(encoding="utf-8"):
            warnings.append(f"latest daily model report missing experience-study link: "
                            f"{latest_daily.relative_to(REPO_ROOT)}")
    else:
        warnings.append("no daily_model_training_report.md found — link check skipped")

    if failures:
        for line in failures:
            print(f"  fail: {line}", file=sys.stderr)
        for line in warnings:
            print(f"  warn: {line}", file=sys.stderr)
        print("PMF_VARIANCE_EXPERIENCE_STUDY_FAILED  "
              f"as_of_date={args.as_of_date}  failures={len(failures)}  "
              f"warnings={len(warnings)}", file=sys.stderr)
        return 1

    if model_trails_market or warnings:
        for line in warnings:
            print(f"  warn: {line}")
        if model_trails_market:
            print("  warn: model trails market on Brier — caveat present, treated as honest WARN")
        print("PMF_VARIANCE_EXPERIENCE_STUDY_WARN  "
              f"as_of_date={args.as_of_date}  rows={rows_total}  "
              f"model_trails_market={model_trails_market}  "
              f"warnings={len(warnings)}")
        return 0

    print("PMF_VARIANCE_EXPERIENCE_STUDY_PASS  "
          f"as_of_date={args.as_of_date}  rows={rows_total}  "
          f"market_present={market_present}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
