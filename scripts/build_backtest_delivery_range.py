#!/usr/bin/env python3
"""Build stat_grid + canonical + daily PMF delivery for backtest-eligible dates (no public export)."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))
from event_market_date_selection import dates_fingerprint  # noqa: E402
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402


def _run(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--dates-file", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--no-public-export", action="store_true", default=True)
    args = ap.parse_args()

    dates: list[str] = []
    if args.dates_file:
        df = pd.read_csv(Path(args.dates_file))
        if "date" not in df.columns:
            print("FATAL: dates-file missing date column", file=sys.stderr)
            return 2
        if "eligible_for_event_market_backtest" in df.columns:
            ev = df["eligible_for_event_market_backtest"]
            if ev.dtype == object:
                ev = ev.astype(str).str.lower().isin(("1", "true", "t", "yes"))
            df = df[ev == True]  # noqa: E712
        dates = sorted(df["date"].astype(str).str.slice(0, 10).unique().tolist())
    elif args.start_date and args.end_date:
        s = date.fromisoformat(args.start_date)
        e = date.fromisoformat(args.end_date)
        while s <= e:
            dates.append(s.isoformat())
            s += timedelta(days=1)
    else:
        print("FATAL: pass --dates-file or --start-date and --end-date", file=sys.stderr)
        return 2

    py = sys.executable
    report: dict = {
        "dates_attempted": dates,
        "dates_built": [],
        "dates_skipped": [],
        "failures": [],
        "stat_counts_per_date": {},
        "all_twelve_mission_stats_per_date": {},
    }

    for d in dates:
        stat_grid = REPO_ROOT / "predictions" / f"stat_grid_{d}.parquet"
        canonical = (
            REPO_ROOT
            / "deliveries"
            / d
            / "canonical_source"
            / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
        )
        if args.skip_existing and stat_grid.exists() and canonical.exists():
            report["dates_skipped"].append({"date": d, "reason": "stat_grid_and_canonical_exist"})
            try:
                sg = pd.read_parquet(stat_grid, columns=["stat"])
                report["stat_counts_per_date"][d] = (
                    sg["stat"].astype(str).str.lower().value_counts().to_dict()
                )
            except Exception:
                report["stat_counts_per_date"][d] = {}
            continue

        step_log: list[dict] = []

        def _step(script: str, extra: list[str]) -> bool:
            cmd = [py, str(REPO_ROOT / "scripts" / script), "--date", d, *extra]
            rc, out = _run(cmd)
            step_log.append({"script": script, "cmd": cmd, "rc": rc, "tail": out[-4000:]})
            return rc == 0

        ok = True
        if args.force or not stat_grid.exists():
            ok = _step("build_stat_grid_pmfs.py", [])
        if not ok:
            report["failures"].append(
                {"date": d, "stage": "build_stat_grid_pmfs", "log": step_log[-1]}
            )
            continue

        if args.force or not canonical.exists():
            ok = _step("build_model_only_canonical_from_stat_grid.py", [])
        if not ok:
            report["failures"].append(
                {
                    "date": d,
                    "stage": "build_model_only_canonical_from_stat_grid",
                    "log": step_log[-1],
                }
            )
            continue

        ok = _step(
            "build_daily_pmf_delivery.py",
            ["--snapshot", "pre_close", "--no-odds-fetch", "--rebuild-canonical"],
        )
        if not ok:
            report["failures"].append(
                {"date": d, "stage": "build_daily_pmf_delivery", "log": step_log[-1]}
            )
            continue

        report["dates_built"].append(d)
        try:
            sg = pd.read_parquet(stat_grid, columns=["stat"])
            vc = sg["stat"].astype(str).str.lower().value_counts()
            report["stat_counts_per_date"][d] = vc.to_dict()
            need = {str(x).lower() for x in MISSION_REQUIRED_TARGETS_CANONICAL}
            have = set(vc.index.astype(str))
            report["all_twelve_mission_stats_per_date"][d] = bool(need <= have)
        except Exception as ex:
            report["stat_counts_per_date"][d] = {"error": str(ex)}
            report["all_twelve_mission_stats_per_date"][d] = False

    if args.dates_file and dates:
        report_label = f"dates_{dates_fingerprint(dates)}"
    elif dates:
        report_label = f"{dates[0]}_{dates[-1]}"
    else:
        report_label = "empty"
    out_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"backtest_delivery_range_{report_label}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"BACKTEST_DELIVERY_RANGE_PASS wrote {out_path.relative_to(REPO_ROOT)} failures={len(report['failures'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
