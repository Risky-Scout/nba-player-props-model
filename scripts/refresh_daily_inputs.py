"""Refresh daily inputs and emit a freshness manifest.

Single orchestrator the daily runner calls before
`scripts/build_daily_pmf_delivery.py`. It does five things:

  1. Refreshes finalized BDL box scores into
     `data/player_game_stats.parquet` via
     `scripts/refresh_bdl_player_game_stats.py`. Only games whose BDL
     status is ``Final`` are ingested — partial / in-progress rows are
     dropped. Skipped when `--no-bdl-refresh` is passed.
  2. Fetches today's Dunks & Threes player / team predictions via
     `scripts/fetch_dunks_and_threes.py`. Skipped when `--no-dnt-fetch`
     is passed.
  3. Fetches today's NBA player-prop odds from the Odds API for the
     requested regions (default `us` and `us2`) via
     `scripts/oddsapi_nba_props.py live-snapshot`.
  4. Optionally re-runs the prediction export
     (`scripts/predict.py`) when `--refresh-predictions` is set.
     By default we leave the existing predictions alone — the CI
     pipeline produces them earlier in the morning.
  5. Inspects every input the delivery consumes (predictions,
     availability table, model artifacts, finals box-score parquet,
     odds snapshots, D&T pulls) and writes a single
     `data/freshness_manifest/{date}.json` capturing path / mtime /
     status for each.

The freshness manifest is an *input* to the delivery build, not a
delivery artifact. It is written under `data/` and intentionally NOT
staged (see `.gitignore` rules in the runbook).

This script never:
  - prints the API key,
  - mutates predictions when `--refresh-predictions` is unset,
  - fabricates injuries, lineups, or odds when an upstream input is
    missing — the manifest faithfully records what is actually present.

CLI:
    python scripts/refresh_daily_inputs.py \
        --date 2026-04-29 \
        [--regions us us2] \
        [--snapshot-type morning_7am] \
        [--max-events 20] \
        [--no-odds-fetch] \
        [--no-bdl-refresh] \
        [--no-dnt-fetch] \
        [--refresh-predictions]
"""
from __future__ import annotations

# Phase 14 audit tag: source-of-truth for the active calibration blend policy.
try:
    import sys as _phase14_sys
    from pathlib import Path as _phase14_Path
    _SRC = _phase14_Path(__file__).resolve().parent.parent / "src"
    if str(_SRC) not in _phase14_sys.path:
        _phase14_sys.path.insert(0, str(_SRC))
    from nba_props_model.calibration.pmf_calibration import (
        ROLE_AWARE_BLEND_POLICY as _ROLE_AWARE_BLEND_POLICY,
    )
except Exception:
    _ROLE_AWARE_BLEND_POLICY = None

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ODDS_PROCESSED_DIR = REPO_ROOT / "data" / "odds_api" / "processed"
FRESHNESS_DIR = REPO_ROOT / "data" / "freshness_manifest"
DNT_RAW_DIR = REPO_ROOT / "data" / "dunks_and_threes"

SUPPORTED_STATS = ("pts", "reb", "ast", "tov", "fg3m")


def _now_utc_iso() -> str:
    return (datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _file_mtime_iso_utc(path: Path) -> str | None:
    if not path.exists():
        return None
    return (datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            .isoformat().replace("+00:00", "Z"))


def _file_age_hours(path: Path) -> float | None:
    if not path.exists():
        return None
    return (datetime.now(timezone.utc).timestamp() - path.stat().st_mtime) / 3600.0


def _file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _classify_age(age_hours: float | None, *, fresh_h: float = 3.0,
                  stale_h: float = 12.0) -> str:
    if age_hours is None:
        return "unknown"
    if age_hours <= fresh_h:
        return "fresh"
    if age_hours <= stale_h:
        return "stale"
    return "very_stale"


# ── BDL refresh ──────────────────────────────────────────────────────────


def _run_bdl_refresh(*, date: str) -> dict:
    """Invoke `scripts/refresh_bdl_player_game_stats.py` once.

    Returns a status dict — never raises; failures are recorded so the
    freshness manifest reflects them. Default window is
    `[latest_in_parquet+1, --date]`. We pass an explicit `--end-date`
    so a stale clock cannot widen the window past the slate."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "refresh_bdl_player_game_stats.py"),
        "--end-date", date,
    ]
    started_at = _now_utc_iso()
    print("  → BDL refresh (player_game_stats)")
    try:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False,
                              capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return {"started_at_utc": started_at,
                "ended_at_utc": _now_utc_iso(),
                "exit_code": None, "status": "timeout",
                "stderr_tail": "subprocess timed out after 600s"}
    out_tail = (proc.stdout or "").splitlines()[-12:]
    err_tail = (proc.stderr or "").splitlines()[-6:]
    for ln in out_tail:
        print(f"    {ln}")
    # exit_code 0 = wrote, 1 = empty window or no rows, 2 = no key.
    if proc.returncode == 0:
        status = "ok"
    elif proc.returncode == 1:
        status = "no_new_finals"
    else:
        status = "fail"
    return {
        "started_at_utc": started_at,
        "ended_at_utc": _now_utc_iso(),
        "exit_code": int(proc.returncode),
        "status": status,
        "stdout_tail": out_tail,
        "stderr_tail": err_tail,
    }


# ── Dunks & Threes fetch ──────────────────────────────────────────────────


def _run_dnt_fetch(*, date: str) -> dict:
    """Invoke `scripts/fetch_dunks_and_threes.py` once."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "fetch_dunks_and_threes.py"),
        "--date", date,
    ]
    started_at = _now_utc_iso()
    print("  → Dunks & Threes fetch")
    try:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False,
                              capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return {"started_at_utc": started_at,
                "ended_at_utc": _now_utc_iso(),
                "exit_code": None, "status": "timeout",
                "stderr_tail": "subprocess timed out after 300s"}
    out_tail = (proc.stdout or "").splitlines()[-12:]
    err_tail = (proc.stderr or "").splitlines()[-6:]
    for ln in out_tail:
        print(f"    {ln}")
    status = "ok" if proc.returncode == 0 else "fail"
    return {
        "started_at_utc": started_at,
        "ended_at_utc": _now_utc_iso(),
        "exit_code": int(proc.returncode),
        "status": status,
        "stdout_tail": out_tail,
        "stderr_tail": err_tail,
    }


def _scan_dnt_for_date(date: str) -> dict:
    """Inspect `data/dunks_and_threes/{date}/` and report per-endpoint
    presence + row counts (read from each endpoint's JSON file)."""
    base = DNT_RAW_DIR / date
    summary: dict = {
        "path": str(base.relative_to(REPO_ROOT)) if base.exists() else None,
        "exists": base.exists(),
        "endpoints": [],
        "manifest": None,
    }
    if not base.exists():
        return summary
    for ep in ("epm", "team-epm", "game-predictions", "game-predictions-box"):
        fp = base / f"{ep}.json"
        entry = {
            "endpoint": ep,
            "path": str(fp.relative_to(REPO_ROOT)) if fp.exists() else None,
            "exists": fp.exists(),
            "mtime_utc": _file_mtime_iso_utc(fp),
            "rows": None,
        }
        if fp.exists():
            try:
                payload = json.loads(fp.read_text())
                if isinstance(payload, list):
                    entry["rows"] = len(payload)
                elif isinstance(payload, dict):
                    for k in ("data", "rows", "results"):
                        if isinstance(payload.get(k), list):
                            entry["rows"] = len(payload[k])
                            break
            except Exception as e:
                entry["error"] = repr(e)
        summary["endpoints"].append(entry)
    mp = base / "_fetch_manifest.json"
    if mp.exists():
        try:
            summary["manifest"] = json.loads(mp.read_text())
        except Exception:
            summary["manifest"] = {"error": "manifest decode failed"}
    return summary


# ── Odds fetch ────────────────────────────────────────────────────────────


def _run_live_snapshot(*, regions: str, snapshot_type: str,
                       max_events: int, dry_run: bool,
                       date: str) -> dict:
    """Invoke `scripts/oddsapi_nba_props.py live-snapshot` once.

    Returns a per-region status dict — never raises; failures are logged
    in the dict so the freshness manifest can record them.
    """
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "oddsapi_nba_props.py"),
        "live-snapshot",
        "--snapshot-type", snapshot_type,
        "--regions", regions,
        "--max-events", str(max_events),
        "--target-date", date,
    ]
    if dry_run:
        cmd.append("--dry-run")
    started_at = _now_utc_iso()
    print(f"  → live-snapshot regions={regions}")
    try:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False,
                              capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return {"regions": regions, "started_at_utc": started_at,
                "ended_at_utc": _now_utc_iso(),
                "exit_code": None, "status": "timeout",
                "stderr_tail": "subprocess timed out after 600s"}
    out_tail = (proc.stdout or "").splitlines()[-12:]
    err_tail = (proc.stderr or "").splitlines()[-12:]
    for ln in out_tail:
        print(f"    {ln}")
    status = "ok" if proc.returncode == 0 else "fail"
    return {
        "regions": regions,
        "started_at_utc": started_at,
        "ended_at_utc": _now_utc_iso(),
        "exit_code": int(proc.returncode),
        "status": status,
        "stdout_tail": out_tail,
        "stderr_tail": err_tail,
    }


def _scan_processed_odds(date: str) -> list[dict]:
    """Enumerate every odds_pairs_*.parquet under
    data/odds_api/processed/{date}/ with mtime + bookmaker / stat coverage."""
    out: list[dict] = []
    base = ODDS_PROCESSED_DIR / date
    if not base.exists():
        return out
    try:
        import pandas as pd
    except Exception:
        pd = None  # type: ignore
    for fp in sorted(base.glob("odds_pairs_*.parquet")):
        entry = {
            "path": str(fp.relative_to(REPO_ROOT)),
            "mtime_utc": _file_mtime_iso_utc(fp),
            "bytes": fp.stat().st_size,
            "rows": None,
            "books": [],
            "stats": [],
        }
        if pd is not None:
            try:
                df = pd.read_parquet(fp,
                                       columns=["bookmaker_key", "market_stat"])
                entry["rows"] = int(len(df))
                entry["books"] = sorted(df["bookmaker_key"].dropna()
                                          .astype(str).unique().tolist())
                entry["stats"] = sorted(df["market_stat"].dropna()
                                          .astype(str).unique().tolist())
            except Exception as e:
                entry["read_error"] = repr(e)
        out.append(entry)
    return out


# ── Predictions / availability / finals / artifacts ──────────────────────


def _maybe_refresh_predictions(date: str) -> dict:
    """Optionally re-run `scripts/predict.py` for the given date."""
    target = REPO_ROOT / "predictions" / f"all_props_{date}.parquet"
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "predict.py"),
           "--date", date]
    started = _now_utc_iso()
    try:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False,
                              capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return {"started_at_utc": started, "ended_at_utc": _now_utc_iso(),
                "status": "timeout", "exit_code": None}
    return {
        "started_at_utc": started,
        "ended_at_utc": _now_utc_iso(),
        "exit_code": int(proc.returncode),
        "status": "ok" if proc.returncode == 0 else "fail",
        "stdout_tail": (proc.stdout or "").splitlines()[-12:],
        "stderr_tail": (proc.stderr or "").splitlines()[-12:],
        "predictions_exists": target.exists(),
    }


def _availability_status() -> dict:
    p = REPO_ROOT / "data" / "player_availability_asof.parquet"
    age = _file_age_hours(p)
    return {
        "path": str(p.relative_to(REPO_ROOT)) if p.exists() else None,
        "exists": p.exists(),
        "mtime_utc": _file_mtime_iso_utc(p),
        "age_hours": (round(age, 2) if age is not None else None),
        "freshness_status": _classify_age(age),
    }


def _predictions_status(date: str) -> dict:
    p = REPO_ROOT / "predictions" / f"all_props_{date}.parquet"
    age = _file_age_hours(p)
    stats_in_predictions: list[str] = []
    n_rows = None
    if p.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(p, columns=["stat"])
            stats_in_predictions = sorted(df["stat"].astype(str).unique().tolist())
            n_rows = int(len(df))
        except Exception:
            pass
    missing_stats = sorted(set(SUPPORTED_STATS) - set(stats_in_predictions))
    return {
        "path": str(p.relative_to(REPO_ROOT)),
        "exists": p.exists(),
        "mtime_utc": _file_mtime_iso_utc(p),
        "age_hours": (round(age, 2) if age is not None else None),
        "rows": n_rows,
        "stats_in_predictions": stats_in_predictions,
        "missing_supported_stats": missing_stats,
        "tov_status": ("present" if "tov" in stats_in_predictions
                       else "missing_from_prediction_source"),
    }


def _model_artifacts_status() -> dict:
    base = REPO_ROOT / "artifacts" / "models"
    pmf_files = [base / "pmf_cal_meta.json",
                 base / "pmf_cal_pts.pkl",
                 base / "pmf_cal_role_pts.pkl",
                 base / "pmf_cal_role_reb.pkl",
                 base / "pmf_cal_role_ast.pkl",
                 base / "pmf_cal_role_fg3m.pkl",
                 base / "pmf_cal_role_tov.pkl"]
    files = []
    for fp in pmf_files:
        files.append({
            "path": str(fp.relative_to(REPO_ROOT)),
            "exists": fp.exists(),
            "mtime_utc": _file_mtime_iso_utc(fp),
            "sha256": _file_sha256(fp),
        })
    all_present = all(f["exists"] for f in files)
    return {
        "files": files,
        "calibration_source": (
            f"phase8_role_aware_pmf_cal_v1+{_ROLE_AWARE_BLEND_POLICY}"
            if _ROLE_AWARE_BLEND_POLICY
            else "phase8_role_aware_pmf_cal_v1"
        ),
        "blend_policy": _ROLE_AWARE_BLEND_POLICY,
        "phase": "phase10c",
        "tov_overlay_status": "off",
        "tov_overlay_reason": ("Phase 10D/10D.2 overlay failed independent "
                               "validation; see "
                               "docs/phase11_tov_structural_refit_plan.md"),
        "all_present": bool(all_present),
    }


def _finals_status(date: str) -> dict:
    """Best-effort lookup for finalized box-score data for the given date.
    The after-game scoring script reads
    `data/player_game_stats.parquet` (season-to-date)."""
    pgs = REPO_ROOT / "data" / "player_game_stats.parquet"
    age = _file_age_hours(pgs)
    has_today_finals = False
    if pgs.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(pgs, columns=["game_date"]) if "game_date" \
                in pd.read_parquet(pgs).columns else None
            if df is not None and len(df):
                has_today_finals = bool((df["game_date"].astype(str) == date).any())
        except Exception:
            pass
    return {
        "path": str(pgs.relative_to(REPO_ROOT)) if pgs.exists() else None,
        "exists": pgs.exists(),
        "mtime_utc": _file_mtime_iso_utc(pgs),
        "age_hours": (round(age, 2) if age is not None else None),
        "has_finals_for_date": bool(has_today_finals),
        "finality_status": ("finals_present" if has_today_finals
                             else "finals_pending"),
    }


# ── Manifest ──────────────────────────────────────────────────────────────


def _overall_status(odds_status: str, predictions_exists: bool,
                    artifacts_ok: bool) -> str:
    if not predictions_exists or not artifacts_ok:
        return "not_ready"
    if odds_status == "ok":
        return "ready"
    return "partial"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True,
                     help="delivery calendar date YYYY-MM-DD (US/Eastern)")
    ap.add_argument("--regions", nargs="+", default=["us", "us2"],
                     help="Odds API region groups to fetch (default: us us2)")
    ap.add_argument("--snapshot-type", default="morning_7am",
                     choices=["morning_7am", "close_or_lock", "live", "smoke"])
    ap.add_argument("--max-events", type=int, default=20)
    ap.add_argument("--no-odds-fetch", action="store_true",
                     help="Skip the live odds fetch entirely")
    ap.add_argument("--no-bdl-refresh", action="store_true",
                     help="Skip the BDL player_game_stats refresh")
    ap.add_argument("--no-dnt-fetch", action="store_true",
                     help="Skip the Dunks & Threes fetch")
    ap.add_argument("--refresh-predictions", action="store_true",
                     help="Re-run scripts/predict.py for --date")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    delivery_date: str = args.date
    print("=" * 72)
    print(f"refresh_daily_inputs — {delivery_date}")
    print(f"  regions={args.regions}  snapshot_type={args.snapshot_type}  "
          f"max_events={args.max_events}")
    print("=" * 72)

    # 1. BDL refresh — pull finalized box scores into player_game_stats.
    bdl_refresh_summary: dict | None = None
    if args.no_bdl_refresh:
        print("  bdl-refresh: SKIPPED (--no-bdl-refresh)")
        bdl_refresh_summary = {"status": "skipped"}
    elif not os.environ.get("BDL_API_KEY", "").strip():
        print("  WARN: BDL_API_KEY unset; skipping BDL refresh.")
        bdl_refresh_summary = {"status": "skipped:no_api_key"}
    else:
        bdl_refresh_summary = _run_bdl_refresh(date=delivery_date)

    # 2. Dunks & Threes fetch.
    dnt_run: dict | None = None
    if args.no_dnt_fetch:
        print("  dnt-fetch: SKIPPED (--no-dnt-fetch)")
        dnt_run = {"status": "skipped"}
    elif not (os.environ.get("DUNKS_AND_THREES_API_KEY", "").strip()
              or os.environ.get("DUNKS_API_KEY", "").strip()):
        print("  WARN: DUNKS_*_API_KEY unset; skipping D&T fetch.")
        dnt_run = {"status": "skipped:no_api_key"}
    else:
        dnt_run = _run_dnt_fetch(date=delivery_date)

    # 3. Odds fetch (one call per region group).
    odds_runs: list[dict] = []
    if args.no_odds_fetch:
        print("  odds-fetch: SKIPPED (--no-odds-fetch)")
        odds_status_summary = "skipped"
    else:
        if not os.environ.get("ODDS_API_KEY", "").strip():
            print("  WARN: ODDS_API_KEY unset; skipping odds fetch.")
            odds_status_summary = "skipped:no_api_key"
        else:
            for region in args.regions:
                odds_runs.append(_run_live_snapshot(
                    regions=region, snapshot_type=args.snapshot_type,
                    max_events=args.max_events, dry_run=args.dry_run,
                    date=delivery_date))
            ok_count = sum(1 for r in odds_runs if r.get("status") == "ok")
            if ok_count == len(odds_runs) and odds_runs:
                odds_status_summary = "ok"
            elif ok_count == 0:
                odds_status_summary = "fail"
            else:
                odds_status_summary = "partial"

    # 4. Optional predictions refresh.
    predictions_refresh: dict | None = None
    if args.refresh_predictions:
        print("  refreshing predictions (scripts/predict.py)")
        predictions_refresh = _maybe_refresh_predictions(delivery_date)

    # 5. Status sweep.
    pred_status = _predictions_status(delivery_date)
    avail_status = _availability_status()
    artifacts = _model_artifacts_status()
    finals = _finals_status(delivery_date)
    odds_files = _scan_processed_odds(delivery_date)
    dnt_status = _scan_dnt_for_date(delivery_date)

    # Aggregate book / stat coverage across all per-region snapshots.
    seen_books: set[str] = set()
    seen_stats: set[str] = set()
    total_rows = 0
    for f in odds_files:
        for b in f.get("books", []) or []:
            seen_books.add(str(b))
        for s in f.get("stats", []) or []:
            seen_stats.add(str(s))
        total_rows += int(f.get("rows") or 0)
    market_coverage_status = (
        "none" if not seen_books else
        "sparse" if len(seen_books) < 2 else
        "partial" if len(seen_books) < 4 else "full"
    )

    overall = _overall_status(
        odds_status_summary, pred_status["exists"], artifacts["all_present"])

    manifest = {
        "delivery_date": delivery_date,
        "built_at_utc": _now_utc_iso(),
        "schema_version": 1,
        "snapshot_type": args.snapshot_type,
        "regions_requested": list(args.regions),
        "odds": {
            "status": odds_status_summary,
            "runs": odds_runs,
            "files": odds_files,
            "books_seen": sorted(seen_books),
            "stats_seen": sorted(seen_stats),
            "total_rows": int(total_rows),
            "market_coverage_status": market_coverage_status,
        },
        "predictions": pred_status,
        "predictions_refresh": predictions_refresh,
        "availability_table": avail_status,
        "model_artifacts": artifacts,
        "finals": finals,
        "bdl_refresh": bdl_refresh_summary,
        "dunks_and_threes": {
            "fetch_run": dnt_run,
            "files": dnt_status,
        },
        "overall_status": overall,
        "tov_status": pred_status["tov_status"],
    }

    FRESHNESS_DIR.mkdir(parents=True, exist_ok=True)
    out = FRESHNESS_DIR / f"{delivery_date}.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    print()
    print(f"wrote {out.relative_to(REPO_ROOT)}")
    print(f"  overall_status         : {overall}")
    print(f"  bdl_refresh.status     : "
          f"{(bdl_refresh_summary or {}).get('status')}")
    print(f"  dnt.status             : "
          f"{(dnt_run or {}).get('status')}")
    print(f"  odds.status            : {odds_status_summary}")
    print(f"  odds.books_seen        : {sorted(seen_books)}")
    print(f"  odds.market_coverage   : {market_coverage_status}")
    print(f"  predictions.exists     : {pred_status['exists']}")
    print(f"  predictions.tov_status : {pred_status['tov_status']}")
    print(f"  availability.freshness : {avail_status['freshness_status']}")
    print(f"  artifacts.all_present  : {artifacts['all_present']}")
    print(f"  finals.finality_status : {finals['finality_status']}")
    return 0 if overall != "not_ready" else 1


if __name__ == "__main__":
    sys.exit(main())
