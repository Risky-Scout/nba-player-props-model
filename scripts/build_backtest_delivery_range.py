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

VERIFY_STAT_GRID = REPO_ROOT / "scripts" / "verify_stat_grid_mission_stats_contract.py"
DIAGNOSE_STAT_GRID = REPO_ROOT / "scripts" / "diagnose_stat_grid_integrity.py"
BUILD_STAT_GRID = REPO_ROOT / "scripts" / "build_stat_grid_pmfs.py"
MISSION_STATS_ARGS = list(MISSION_REQUIRED_TARGETS_CANONICAL)


def _run(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def _verify_stat_grid_contract(py: str, d: str) -> tuple[int, str]:
    cmd = [py, str(VERIFY_STAT_GRID), "--date", d]
    rc, out = _run(cmd)
    return rc, out


def _diagnose_before_rebuild(py: str, d: str) -> tuple[int, str]:
    cmd = [
        py,
        str(DIAGNOSE_STAT_GRID),
        "--date",
        d,
        "--require-mission-stats",
    ]
    return _run(cmd)


def _build_stat_grid_mission(py: str, d: str) -> tuple[int, str]:
    cmd = [
        py,
        str(BUILD_STAT_GRID),
        "--date",
        d,
        "--stats",
        *MISSION_STATS_ARGS,
    ]
    return _run(cmd)


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

    exit_code = 0

    for d in dates:
        stat_grid = REPO_ROOT / "predictions" / f"stat_grid_{d}.parquet"
        canonical = (
            REPO_ROOT
            / "deliveries"
            / d
            / "canonical_source"
            / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
        )

        contract_rc: int | None = None
        contract_out = ""
        if stat_grid.exists():
            contract_rc, contract_out = _verify_stat_grid_contract(py, d)
            if contract_rc == 0:
                sys.stdout.write(contract_out)
                if not contract_out.endswith("\n"):
                    sys.stdout.write("\n")
            else:
                print("BAD_STAT_GRID_MISSION_STATS", d, file=sys.stderr)
                sys.stderr.write(contract_out[-4000:])

        if (
            args.skip_existing
            and stat_grid.exists()
            and canonical.exists()
            and contract_rc == 0
        ):
            report["dates_skipped"].append({"date": d, "reason": "stat_grid_and_canonical_exist_contract_ok"})
            try:
                sg = pd.read_parquet(stat_grid, columns=["stat"])
                report["stat_counts_per_date"][d] = (
                    sg["stat"].astype(str).str.lower().value_counts().to_dict()
                )
            except Exception:
                report["stat_counts_per_date"][d] = {}
            continue

        if stat_grid.exists() and contract_rc != 0:
            if not args.force:
                report["failures"].append(
                    {
                        "date": d,
                        "stage": "BAD_STAT_GRID_MISSION_STATS",
                        "log": {"rc": contract_rc, "tail": contract_out[-4000:]},
                    }
                )
                exit_code = 1
                break

            drc, dout = _diagnose_before_rebuild(py, d)
            report.setdefault("stat_grid_diagnostics", []).append(
                {"date": d, "diagnose_rc": drc, "tail": dout[-2000:]}
            )

        step_log: list[dict] = []

        def _step(script: str, extra: list[str]) -> bool:
            cmd = [py, str(REPO_ROOT / "scripts" / script), "--date", d, *extra]
            rc, out = _run(cmd)
            step_log.append({"script": script, "cmd": cmd, "rc": rc, "tail": out[-4000:]})
            return rc == 0

        rebuild_sg = (not stat_grid.exists()) or args.force or (stat_grid.exists() and contract_rc != 0)
        ok = True
        if rebuild_sg:
            brc, bout = _build_stat_grid_mission(py, d)
            step_log.append(
                {
                    "script": "build_stat_grid_pmfs.py (mission explicit)",
                    "cmd": [py, str(BUILD_STAT_GRID), "--date", d, "--stats", *MISSION_STATS_ARGS],
                    "rc": brc,
                    "tail": bout[-4000:],
                }
            )
            ok = brc == 0
        if not ok:
            report["failures"].append({"date": d, "stage": "build_stat_grid_pmfs", "log": step_log[-1]})
            exit_code = 1
            break

        vrc, vout = _verify_stat_grid_contract(py, d)
        if vrc != 0:
            print("BAD_STAT_GRID_MISSION_STATS post_rebuild", d, file=sys.stderr)
            sys.stderr.write(vout[-4000:])
            report["failures"].append(
                {
                    "date": d,
                    "stage": "verify_stat_grid_mission_stats_contract_post_build",
                    "log": {"rc": vrc, "tail": vout[-4000:]},
                }
            )
            exit_code = 1
            break
        sys.stdout.write(vout)
        if not vout.endswith("\n"):
            sys.stdout.write("\n")

        rebuild_canonical = rebuild_sg or args.force or not canonical.exists()
        if rebuild_canonical:
            ok = _step("build_model_only_canonical_from_stat_grid.py", [])
        else:
            ok = True
        if not ok:
            report["failures"].append(
                {
                    "date": d,
                    "stage": "build_model_only_canonical_from_stat_grid",
                    "log": step_log[-1],
                }
            )
            exit_code = 1
            break

        ok = _step(
            "build_daily_pmf_delivery.py",
            [
                "--snapshot",
                "pre_close",
                "--no-odds-fetch",
                "--model-only",
                str(canonical),
            ],
        )
        if not ok:
            report["failures"].append(
                {"date": d, "stage": "build_daily_pmf_delivery", "log": step_log[-1]}
            )
            exit_code = 1
            break

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
    tag = "BACKTEST_DELIVERY_RANGE_FAIL" if exit_code != 0 else "BACKTEST_DELIVERY_RANGE_PASS"
    print(f"{tag} wrote {out_path.relative_to(REPO_ROOT)} failures={len(report['failures'])}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
