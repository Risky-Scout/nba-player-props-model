#!/usr/bin/env python3
"""Plan / build missing stat_grid + canonical + daily PMF inputs for backtest dates.

Modes:
  A) Legacy inventory CSV (dates marked ineligible but have odds+actuals).
  B) Explicit --start-date/--end-date with optional historical Odds API fetch
     (credit-safe: --dry-run never calls the network; --estimate-credits is labeled).

Does not publish public_export. Respects --skip-existing unless --force.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from odds_snapshot_selection import select_odds_pairs_parquet  # noqa: E402


def _as_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "t", "yes")


def _validate_iso_date(s: str) -> str:
    t = str(s).strip()
    if t == "YYYY-MM-DD" or re.fullmatch(r"\d{4}-\d{2}-\d{2}", t) is None:
        print("BUILD_MISSING_INVALID_DATE", t, file=sys.stderr)
        sys.exit(2)
    try:
        date.fromisoformat(t)
    except ValueError:
        print("BUILD_MISSING_INVALID_DATE", t, file=sys.stderr)
        sys.exit(2)
    return t


def _run(py: str, cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _quotes_pairs_counts(day: str) -> tuple[int, int]:
    proc_dir = REPO_ROOT / "data" / "odds_api" / "processed" / day
    qn = pn = 0
    for pat in ("odds_quotes_*.parquet", "odds_quotes_hist_lockday_*.parquet"):
        for p in sorted(proc_dir.glob(pat)) if proc_dir.is_dir() else []:
            try:
                qn = max(qn, int(len(pd.read_parquet(p))))
            except Exception:
                pass
    for p in sorted(proc_dir.glob("odds_pairs_*.parquet")) if proc_dir.is_dir() else []:
        try:
            pn = max(pn, int(len(pd.read_parquet(p))))
        except Exception:
            pass
    return qn, pn


def _estimate_hist_lockday_requests(day: str, max_events: int) -> dict:
    """Upper-bound style estimate from raw hist_events JSON when present."""
    raw = REPO_ROOT / "data" / "odds_api" / "raw" / day
    n_ev = None
    if raw.is_dir():
        for p in sorted(raw.glob("hist_events_*.json")):
            try:
                blob = json.loads(p.read_text(encoding="utf-8"))
                n_ev = len(blob.get("data") or []) if isinstance(blob, dict) else None
                if n_ev is not None:
                    break
            except Exception:
                continue
    capped = min(int(max_events), int(n_ev or max_events))
    note = (
        "request_count_estimate_not_guaranteed_credits; "
        "historical-lock-day uses 1 events-list call + 1 call per selected event."
    )
    if n_ev is None:
        return {
            "events_inferred": None,
            "estimated_api_requests": 1 + capped,
            "note": note + " events_inferred_unavailable_without_hist_events_json.",
        }
    return {
        "events_inferred": int(n_ev),
        "estimated_api_requests": 1 + capped,
        "note": note,
    }


def _has_actuals_for_date(day: str) -> bool:
    pgs = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not pgs.is_file():
        return False
    bx = pd.read_parquet(pgs, columns=["game_date"])
    return int(bx["game_date"].astype(str).str.slice(0, 10).eq(day).sum()) > 0


def _snapshot_substr_for_family(fam: str) -> str:
    fam = str(fam or "hist_lockday").lower().strip()
    if fam in ("hist_lockday", "hist_slate", "close_or_lock", "auto"):
        return fam
    return "auto"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--inventory",
        type=Path,
        default=None,
        help="Optional inventory CSV (legacy mode). Default when no start/end.",
    )
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--fetch-historical-odds", action="store_true")
    ap.add_argument("--snapshot-family", default="hist_lockday")
    ap.add_argument("--max-events", type=int, default=50)
    ap.add_argument("--regions", default="us,us2")
    ap.add_argument("--lock-offset-minutes", type=int, default=5)
    ap.add_argument("--estimate-credits", action="store_true")
    ap.add_argument("--limit-dates", type=int, default=None)
    ap.add_argument("--no-public-export", action="store_true", default=True)
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        print("FATAL: pass --dry-run or --apply", file=sys.stderr)
        return 2
    if args.estimate_credits and args.apply:
        print("FATAL: --estimate-credits is incompatible with --apply", file=sys.stderr)
        return 2

    inv_default = (
        REPO_ROOT / "artifacts" / "model_diagnostics" / "event_market_backtest_date_inventory.csv"
    )
    use_range = bool(args.start_date and args.end_date)
    sd = ed = ""
    if use_range:
        sd = _validate_iso_date(args.start_date)
        ed = _validate_iso_date(args.end_date)
        if sd > ed:
            print("FATAL: start-date > end-date", file=sys.stderr)
            return 2
    elif args.start_date or args.end_date:
        print("FATAL: pass both --start-date and --end-date", file=sys.stderr)
        return 2
    else:
        inv_path = args.inventory or inv_default
        if not inv_path.is_file():
            print(f"MISSING {inv_path}", file=sys.stderr)
            return 2

    py = sys.executable
    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / "historical_backfill_plan.csv"
    res_path = out_dir / "historical_backfill_results.csv"
    summ_path = out_dir / "historical_backfill_summary.json"

    plan_rows: list[dict] = []
    result_rows: list[dict] = []
    substr = _snapshot_substr_for_family(args.snapshot_family)

    if use_range:
        cur = date.fromisoformat(sd)
        end_d = date.fromisoformat(ed)
        dates: list[str] = []
        while cur <= end_d:
            dates.append(cur.isoformat())
            cur += timedelta(days=1)
        if args.limit_dates is not None:
            dates = dates[: int(args.limit_dates)]

        for d in dates:
            fetch_cmd = [
                py,
                str(REPO_ROOT / "scripts" / "oddsapi_nba_props.py"),
                "historical-lock-day",
                "--target-date",
                d,
                "--max-events",
                str(int(args.max_events)),
                "--regions",
                str(args.regions),
                "--lock-offset-minutes",
                str(int(args.lock_offset_minutes)),
            ]
            p_pairs, meta = select_odds_pairs_parquet(REPO_ROOT, d, substr)
            has_proc = bool(p_pairs and p_pairs.is_file())
            qn, pn = _quotes_pairs_counts(d) if has_proc else (0, 0)
            raw_day = REPO_ROOT / "data" / "odds_api" / "raw" / d
            has_raw_events = raw_day.is_dir() and any(raw_day.glob("hist_events_*.json"))
            has_raw_event_odds = raw_day.is_dir() and any(
                fn.name.startswith("hist_event_") and "_lock_" in fn.name
                for fn in raw_day.glob("*.json")
            )
            has_act = _has_actuals_for_date(d)
            stat_grid = REPO_ROOT / "predictions" / f"stat_grid_{d}.parquet"
            canonical = (
                REPO_ROOT
                / "deliveries"
                / d
                / "canonical_source"
                / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
            )
            has_sg = stat_grid.is_file()
            has_can = canonical.is_file()
            need_fetch = args.fetch_historical_odds and not has_proc
            if args.estimate_credits or args.fetch_historical_odds:
                est = _estimate_hist_lockday_requests(d, args.max_events)
            else:
                est = {"note": "estimate_skipped"}

            build_cmd = [
                py,
                str(REPO_ROOT / "scripts" / "build_backtest_delivery_range.py"),
                "--start-date",
                d,
                "--end-date",
                d,
                "--no-public-export",
            ]
            if not args.force:
                build_cmd.append("--skip-existing")
            else:
                build_cmd.append("--force")

            blockers: list[str] = []
            if not has_proc:
                if need_fetch:
                    blockers.append("no_processed_odds")
                    if args.dry_run or args.estimate_credits:
                        blockers.append("would_fetch_hist_lockday_odds_api")
                else:
                    blockers.append("no_processed_odds")
            elif qn <= 0 or pn <= 0:
                blockers.append("empty_processed_quotes_or_pairs")
            if has_proc and not has_raw_events:
                blockers.append("missing_raw_hist_events_list")
            if has_proc and not has_raw_event_odds:
                blockers.append("missing_raw_hist_event_odds_json")
            if not has_act:
                blockers.append("no_actuals")
            if has_sg and has_can and not args.force:
                blockers.append("skip_existing_stat_grid_and_canonical")
            elif has_proc and has_act and (not has_sg or not has_can):
                pass  # buildable
            elif has_proc and has_act and has_sg and has_can and args.force:
                pass
            blocker = ";".join(blockers) if blockers else "ready"

            deliv = REPO_ROOT / "deliveries" / d / "canonical_source" / "manifest.json"
            has_delivery_manifest = deliv.is_file()
            can_eligible = bool(has_act and (has_proc or need_fetch))
            if not has_act:
                risk = "high"
            elif not has_proc and need_fetch:
                risk = "low"
            elif not has_sg or not has_can:
                risk = "medium"
            else:
                risk = "low"

            plan_rows.append(
                {
                    "date": d,
                    "snapshot_substr": substr,
                    "need_fetch_hist_lockday": bool(need_fetch),
                    "needs_historical_fetch": bool(need_fetch),
                    "has_processed_pairs_file": has_proc,
                    "processed_quotes_rows_max": qn,
                    "processed_pairs_rows_max": pn,
                    "has_raw_hist_events": has_raw_events,
                    "has_raw_hist_event_lock_odds": has_raw_event_odds,
                    "has_actuals": has_act,
                    "has_stat_grid": has_sg,
                    "has_canonical_delivery": has_can,
                    "has_delivery_manifest": has_delivery_manifest,
                    "can_be_made_eligible": can_eligible,
                    "risk_level": risk,
                    "blocker": blocker,
                    "fetch_command": json.dumps(fetch_cmd),
                    "build_command": json.dumps(build_cmd),
                    "odds_snapshot_meta": json.dumps(meta, sort_keys=True),
                    **(
                        {f"estimate_{k}": v for k, v in est.items()}
                        if isinstance(est, dict)
                        else {}
                    ),
                }
            )

            if args.apply and args.fetch_historical_odds and need_fetch:
                rc, out = _run(py, fetch_cmd)
                quota_lines = "\n".join([ln for ln in out.splitlines() if "[quota]" in ln])
                result_rows.append(
                    {
                        "date": d,
                        "step": "fetch_hist_lockday",
                        "rc": rc,
                        "quota_lines": quota_lines,
                        "tail": out[-4000:],
                    }
                )
                if rc != 0:
                    continue
                p_pairs, meta = select_odds_pairs_parquet(REPO_ROOT, d, substr)
                has_proc = bool(p_pairs and p_pairs.is_file())
                qn, pn = _quotes_pairs_counts(d) if has_proc else (0, 0)
            if args.apply and not _has_actuals_for_date(d) and os.environ.get("BDL_API_KEY", "").strip():
                brc, bout = _run(
                    py,
                    [
                        py,
                        str(REPO_ROOT / "scripts" / "refresh_bdl_player_game_stats.py"),
                        "--start-date",
                        d,
                        "--end-date",
                        d,
                    ],
                )
                result_rows.append(
                    {"date": d, "step": "refresh_bdl_player_game_stats", "rc": brc, "tail": bout[-4000:]}
                )
            has_act2 = _has_actuals_for_date(d)
            if args.apply and has_act2:
                p_pairs2, _ = select_odds_pairs_parquet(REPO_ROOT, d, substr)
                if not p_pairs2 or not p_pairs2.is_file():
                    result_rows.append({"date": d, "step": "skip_build", "rc": 0, "tail": "no_processed_pairs"})
                    continue
                q2, p2 = _quotes_pairs_counts(d)
                if q2 <= 0 or p2 <= 0:
                    result_rows.append({"date": d, "step": "skip_build", "rc": 0, "tail": "empty_quotes_or_pairs"})
                    continue
                has_sg2 = stat_grid.is_file()
                has_can2 = canonical.is_file()
                if has_sg2 and has_can2 and not args.force:
                    continue
                brc2, bout2 = _run(py, build_cmd)
                result_rows.append(
                    {"date": d, "step": "build_backtest_delivery_range", "rc": brc2, "tail": bout2[-4000:]}
                )

    else:
        inv_path = args.inventory or inv_default
        df = pd.read_csv(inv_path)
        for _, r in df.iterrows():
            row = r.to_dict()
            if _as_bool(row.get("eligible_for_event_market_backtest", False)):
                continue
            d = str(row.get("date", "")).strip()[:10]
            if not d:
                continue
            has_proc = _as_bool(row.get("has_processed_odds", False))
            has_act = _as_bool(row.get("has_player_game_stats", False))
            has_sg = _as_bool(row.get("has_stat_grid", False))
            has_can = _as_bool(row.get("has_canonical_delivery", False))
            if not (has_proc and has_act):
                continue
            if not args.force and has_sg and has_can:
                continue
            cmd = [
                py,
                str(REPO_ROOT / "scripts" / "build_backtest_delivery_range.py"),
                "--start-date",
                d,
                "--end-date",
                d,
                "--no-public-export",
            ]
            if not args.force:
                cmd.append("--skip-existing")
            if args.force:
                cmd.append("--force")
            plan_rows.append({"date": d, "mode": "inventory", "cmd": json.dumps(cmd)})

        if args.dry_run:
            print(json.dumps({"planned_dates": [p["date"] for p in plan_rows], "n": len(plan_rows)}, indent=2))
            return 0

        failures: list[dict] = []
        for p in plan_rows:
            rc, out = _run(py, json.loads(p["cmd"]))
            if rc != 0:
                failures.append({"date": p["date"], "rc": rc, "tail": out[-4000:]})
        rep = REPO_ROOT / "artifacts" / "model_diagnostics" / "build_missing_backtest_inputs_report.json"
        rep.write_text(json.dumps({"built": [p["date"] for p in plan_rows], "failures": failures}, indent=2) + "\n")
        print(f"BUILD_MISSING_BACKTEST_INPUTS_APPLY_DONE n={len(plan_rows)} failures={len(failures)}")
        return 1 if failures else 0

    if use_range and args.dry_run:
        print("=== HISTORICAL_BACKFILL_DRY_RUN_PLAN_JSON ===")
        print(json.dumps(plan_rows, indent=2, default=str))

    pd.DataFrame(plan_rows).to_csv(plan_path, index=False)
    if result_rows:
        pd.DataFrame(result_rows).to_csv(res_path, index=False)
    else:
        res_path.write_text("", encoding="utf-8")
    summ_path.write_text(
        json.dumps(
            {
                "mode": "date_range",
                "dry_run": bool(args.dry_run),
                "apply": bool(args.apply),
                "fetch_historical_odds": bool(args.fetch_historical_odds),
                "snapshot_family": args.snapshot_family,
                "snapshot_substr_resolved": substr,
                "n_plan_rows": len(plan_rows),
                "estimate_only": bool(args.estimate_credits),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"HISTORICAL_BACKFILL_PLAN wrote {plan_path.relative_to(REPO_ROOT)} n={len(plan_rows)}")
    if args.estimate_credits:
        print("HISTORICAL_BACKFILL_CREDIT_ESTIMATE_MODE see estimate_* columns in plan (request counts).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
