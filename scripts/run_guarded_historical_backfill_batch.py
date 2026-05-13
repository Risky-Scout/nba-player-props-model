#!/usr/bin/env python3
"""Guarded historical backfill: one date at a time with hard stop on pipeline failure."""
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
from odds_snapshot_selection import select_odds_pairs_parquet  # noqa: E402

VERIFY_STAT_GRID = REPO_ROOT / "scripts" / "verify_stat_grid_mission_stats_contract.py"

def _run(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _quotes_pairs_counts(day: str) -> tuple[int, int]:
    proc_dir = REPO_ROOT / "data" / "odds_api" / "processed" / day
    qn = pn = 0
    if not proc_dir.is_dir():
        return 0, 0
    for p in sorted(proc_dir.glob("odds_quotes_*.parquet")):
        try:
            qn = max(qn, int(len(pd.read_parquet(p))))
        except Exception:
            pass
    for p in sorted(proc_dir.glob("odds_pairs_*.parquet")):
        try:
            pn = max(pn, int(len(pd.read_parquet(p))))
        except Exception:
            pass
    return qn, pn


def _has_actuals(day: str) -> bool:
    pgs = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not pgs.is_file():
        return False
    bx = pd.read_parquet(pgs, columns=["game_date"])
    return int(bx["game_date"].astype(str).str.slice(0, 10).eq(day).sum()) > 0


def _inventory_row(day: str) -> dict | None:
    inv = REPO_ROOT / "artifacts" / "model_diagnostics" / "event_market_backtest_date_inventory.csv"
    if not inv.is_file():
        return None
    df = pd.read_csv(inv)
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    m = df[df["date"] == day]
    if m.empty:
        return None
    return m.iloc[0].to_dict()


def _eligible(row: dict | None) -> bool:
    if not row:
        return False
    v = row.get("eligible_for_event_market_backtest")
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "t", "yes")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", required=True)
    ap.add_argument("--end-date", required=True)
    ap.add_argument("--regions", default="us,us2")
    ap.add_argument("--snapshot-family", default="hist_lockday")
    ap.add_argument("--max-events", type=int, default=50)
    ap.add_argument("--lock-offset-minutes", type=int, default=5)
    ap.add_argument("--no-public-export", action="store_true", default=True)
    ap.add_argument("--stop-on-first-failed-date", action="store_true")
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit-dates", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        print("FATAL: pass --dry-run or --apply", file=sys.stderr)
        return 2

    py = sys.executable
    sd = date.fromisoformat(args.start_date.strip()[:10])
    ed = date.fromisoformat(args.end_date.strip()[:10])
    if sd > ed:
        print("FATAL start>end", file=sys.stderr)
        return 2

    substr = "hist_lockday" if args.snapshot_family == "hist_lockday" else "auto"
    regions = str(args.regions).strip()

    dates: list[str] = []
    cur = sd
    while cur <= ed:
        dates.append(cur.isoformat())
        cur += timedelta(days=1)
    if args.limit_dates is not None:
        dates = dates[: int(args.limit_dates)]

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / "guarded_historical_backfill_batch_plan.csv"
    res_path = out_dir / "guarded_historical_backfill_batch_results.csv"
    summ_path = out_dir / "guarded_historical_backfill_batch_summary.json"

    plan_rows: list[dict] = []
    result_rows: list[dict] = []

    for d in dates:
        inv_row = _inventory_row(d)
        el = _eligible(inv_row)
        p_pairs, meta = select_odds_pairs_parquet(REPO_ROOT, d, substr)
        has_proc = bool(p_pairs and p_pairs.is_file())
        qn, pn = _quotes_pairs_counts(d) if has_proc else (0, 0)
        has_act = _has_actuals(d)
        stat_grid = REPO_ROOT / "predictions" / f"stat_grid_{d}.parquet"
        canonical = (
            REPO_ROOT / "deliveries" / d / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
        )
        has_sg = stat_grid.is_file()
        has_can = canonical.is_file()
        need_fetch = not has_proc
        risk = "low" if has_act and (not has_proc) else ("medium" if has_act else "high")
        can_eligible = bool(has_act and (has_proc or True))
        plan_rows.append(
            {
                "date": d,
                "has_actuals": has_act,
                "has_stat_grid": has_sg,
                "has_canonical": has_can,
                "has_processed_odds": has_proc,
                "needs_historical_fetch": need_fetch,
                "processed_quotes_max": qn,
                "processed_pairs_max": pn,
                "inventory_eligible": el,
                "risk_level": risk,
                "can_be_made_eligible": can_eligible,
            }
        )

    pd.DataFrame(plan_rows).to_csv(plan_path, index=False)

    if args.dry_run:
        summ_path.write_text(
            json.dumps({"mode": "dry_run", "n_dates": len(dates), "plan_csv": str(plan_path)}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"GUARDED_HISTORICAL_BACKFILL_DRY_RUN plan={plan_path.relative_to(REPO_ROOT)}")
        return 0

    stopped: str | None = None
    for d in dates:
        inv_row = _inventory_row(d)
        need_force_delivery = bool(args.force)
        if args.skip_existing and _eligible(inv_row) and not args.force:
            sg_skip = REPO_ROOT / "predictions" / f"stat_grid_{d}.parquet"
            contract_ok = False
            vout_skip = ""
            if sg_skip.is_file():
                vrc_skip, vout_skip = _run([py, str(VERIFY_STAT_GRID), "--date", d])
                contract_ok = vrc_skip == 0
            if contract_ok:
                result_rows.append({"date": d, "step": "skip_eligible_inventory", "rc": 0, "tail": ""})
                continue
            print(
                "BAD_STAT_GRID_MISSION_STATS eligible_skip_overridden "
                f"(rebuilding stat_grid/canonical/delivery) date={d}",
                file=sys.stderr,
            )
            result_rows.append(
                {
                    "date": d,
                    "step": "eligible_but_stat_grid_contract_fail_override_force",
                    "rc": 0,
                    "tail": vout_skip[-2000:] if sg_skip.is_file() else "missing_stat_grid",
                }
            )
            need_force_delivery = True

        p_pairs, _meta = select_odds_pairs_parquet(REPO_ROOT, d, substr)
        has_proc = bool(p_pairs and p_pairs.is_file())
        if not has_proc or args.force:
            fetch_cmd = [
                py,
                str(REPO_ROOT / "scripts" / "oddsapi_nba_props.py"),
                "historical-lock-day",
                "--target-date",
                d,
                "--max-events",
                str(int(args.max_events)),
                "--regions",
                regions,
                "--lock-offset-minutes",
                str(int(args.lock_offset_minutes)),
            ]
            rc, out = _run(fetch_cmd)
            quota = "\n".join([ln for ln in out.splitlines() if "[quota]" in ln.lower()])
            result_rows.append(
                {
                    "date": d,
                    "step": "fetch_hist_lockday",
                    "rc": rc,
                    "quota_lines": quota,
                    "tail": out[-6000:],
                }
            )
            if rc != 0:
                stopped = f"{d}:fetch_hist_lockday_rc={rc}"
                break
            p_pairs2, _ = select_odds_pairs_parquet(REPO_ROOT, d, substr)
            has_proc = bool(p_pairs2 and p_pairs2.is_file())
        qn, pn = _quotes_pairs_counts(d)
        if qn <= 0 or pn <= 0:
            stopped = f"{d}:zero_quotes_or_pairs qn={qn} pn={pn}"
            result_rows.append({"date": d, "step": "guard_zero_pairs", "rc": 1, "tail": stopped})
            break

        if not _has_actuals(d):
            stopped = f"{d}:no_actuals"
            result_rows.append({"date": d, "step": "guard_no_actuals", "rc": 1, "tail": stopped})
            break

        build_cmd = [
            py,
            str(REPO_ROOT / "scripts" / "build_backtest_delivery_range.py"),
            "--start-date",
            d,
            "--end-date",
            d,
            "--no-public-export",
        ]
        if not need_force_delivery:
            build_cmd.append("--skip-existing")
        else:
            build_cmd.append("--force")
        rc, out = _run(build_cmd)
        result_rows.append({"date": d, "step": "build_backtest_delivery_range", "rc": rc, "tail": out[-6000:]})
        if rc != 0:
            stopped = f"{d}:build_backtest_delivery_range_rc={rc}"
            break

        vcmd_sg = [py, str(VERIFY_STAT_GRID), "--date", d]
        vrc_sg, vout_sg = _run(vcmd_sg)
        result_rows.append(
            {"date": d, "step": "verify_stat_grid_mission_stats_contract", "rc": vrc_sg, "tail": vout_sg[-2000:]}
        )
        if vrc_sg != 0:
            stopped = f"{d}:STAT_GRID_MISSION_STATS_CONTRACT_FAIL"
            break

        vcmd = [
            py,
            str(REPO_ROOT / "scripts" / "verify_canonical_model_only_rectangularity.py"),
            "--date",
            d,
        ]
        rc, out = _run(vcmd)
        result_rows.append({"date": d, "step": "verify_canonical_model_only_rectangularity", "rc": rc, "tail": out[-2000:]})
        if rc != 0:
            stopped = f"{d}:rectangularity_rc={rc}"
            break

        lcmd = [
            py,
            str(REPO_ROOT / "scripts" / "build_event_market_loss_rows.py"),
            "--as-of-date",
            d,
            "--snapshot-substr",
            "auto",
        ]
        rc, out = _run(lcmd)
        result_rows.append({"date": d, "step": "build_event_market_loss_rows", "rc": rc, "tail": out[-4000:]})
        if rc != 0:
            stopped = f"{d}:event_market_loss_rows_rc={rc}"
            break

    pd.DataFrame(result_rows).to_csv(res_path, index=False)
    summ = {
        "start_date": str(sd),
        "end_date": str(ed),
        "regions": regions,
        "stopped_reason": stopped,
        "n_result_steps": len(result_rows),
        "plan_csv": str(plan_path),
        "results_csv": str(res_path),
    }
    summ_path.write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8")
    print(f"GUARDED_HISTORICAL_BACKFILL_BATCH_DONE summary={summ_path.relative_to(REPO_ROOT)}")
    if stopped:
        print(f"STOPPED: {stopped}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
