"""Single orchestrator for the daily PMF delivery lifecycle.

Wraps `refresh_daily_inputs.py`, optionally `predict.py`,
`build_daily_pmf_delivery.py`, and `score_daily_pmf_delivery_after_game.py`
behind one CLI so the GitHub Actions workflow (and the on-call operator)
can invoke a full snapshot run with a single command.

Modes
-----
    morning      refresh inputs, run predictions if `--predict`, build delivery
                 with `--snapshot morning`, then refresh deliveries/README.md.
    pre_close    refresh inputs, build delivery with `--snapshot pre_close`,
                 refresh index. (No predict — predictions stay morning-of.)
    close_lock   refresh inputs (close_or_lock odds capture), build delivery
                 with `--snapshot close_lock`, refresh index.
    after_game   skip odds fetch, run after-game scorer, refresh index.
    full_day     morning → pre_close → close_lock → after_game in sequence.

Hard rules echoed from the spec:
- Never logs the API key (predict.py / refresh use os.environ directly).
- Never wires Phase 10D / 10D.2 TOV overlays.
- Never market-anchors model-only PMFs.
- Never fabricates predictions, injuries, lineups, role buckets, or odds.
- Never stages data/odds_api/, data/freshness_manifest/, artifacts/, logs.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

REFRESH = REPO_ROOT / "scripts" / "refresh_daily_inputs.py"
BUILD = REPO_ROOT / "scripts" / "build_daily_pmf_delivery.py"
SCORE = REPO_ROOT / "scripts" / "score_daily_pmf_delivery_after_game.py"
PREDICT = REPO_ROOT / "src" / "nba_props_model" / "pipelines" / "predict.py"
STAT_GRID = REPO_ROOT / "scripts" / "build_stat_grid_pmfs.py"
INDEX = REPO_ROOT / "scripts" / "build_deliveries_index.py"


def _run(cmd: list[str], *, allow_fail: bool = False, label: str = "") -> int:
    """Inherit stdout/stderr so subprocess output is visible in CI logs.
    Returns the exit code; raises on non-zero unless allow_fail."""
    print(f"\n[$] {label or ' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if res.returncode != 0 and not allow_fail:
        sys.exit(f"FATAL: step exited {res.returncode}: {label or cmd[0]}")
    return int(res.returncode)


# ── Per-mode steps ────────────────────────────────────────────────────────


def _refresh(date: str, *, snapshot_type: str, no_odds_fetch: bool,
              regions: list[str]) -> int:
    cmd = [PYTHON, str(REFRESH), "--date", date,
            "--regions", *regions,
            "--snapshot-type", snapshot_type]
    if no_odds_fetch:
        cmd.append("--no-odds-fetch")
    return _run(cmd, allow_fail=True, label=f"refresh ({snapshot_type})")


def _predict(date: str) -> int:
    """Optional predict.py invocation. Allowed to fail when BDL_API_KEY is
    unset — the wrapper still proceeds with whatever predictions are on
    disk so the rest of the pipeline can run."""
    if not PREDICT.exists():
        print(f"  predict: {PREDICT} not found, skipping")
        return 0
    cmd = [PYTHON, str(PREDICT), "--date", date]
    return _run(cmd, allow_fail=True, label=f"predict {date}")


def _stat_grid(date: str) -> int:
    """Phase 12 Part G: emit `predictions/stat_grid_{date}.parquet` so
    the canonical build can include TOV (and any other model-only stats
    BDL doesn't sell). Allowed to fail — the canonical build still works
    without TOV when this step is skipped."""
    if not STAT_GRID.exists():
        return 0
    cmd = [PYTHON, str(STAT_GRID), "--date", date]
    return _run(cmd, allow_fail=True, label=f"stat_grid {date}")


def _build(date: str, *, snapshot: str, rebuild_canonical: bool) -> int:
    cmd = [PYTHON, str(BUILD), "--date", date, "--snapshot", snapshot]
    if rebuild_canonical:
        cmd.append("--rebuild-canonical")
    return _run(cmd, label=f"build {date} {snapshot}")


def _score(date: str) -> int:
    cmd = [PYTHON, str(SCORE), "--date", date]
    return _run(cmd, allow_fail=True, label=f"score {date}")


def _refresh_index() -> int:
    if not INDEX.exists():
        return 0
    cmd = [PYTHON, str(INDEX)]
    return _run(cmd, allow_fail=True, label="refresh deliveries index")


# ── Mode dispatchers ──────────────────────────────────────────────────────


def run_morning(date: str, *, regions: list[str], rebuild_canonical: bool,
                  do_predict: bool) -> int:
    if do_predict:
        _predict(date)
    _refresh(date, snapshot_type="morning_7am", no_odds_fetch=False,
              regions=regions)
    _stat_grid(date)
    _build(date, snapshot="morning", rebuild_canonical=rebuild_canonical)
    _refresh_index()
    return 0


def run_pre_close(date: str, *, regions: list[str],
                    rebuild_canonical: bool) -> int:
    _refresh(date, snapshot_type="close_or_lock", no_odds_fetch=False,
              regions=regions)
    _stat_grid(date)
    _build(date, snapshot="pre_close", rebuild_canonical=rebuild_canonical)
    _refresh_index()
    return 0


def run_close_lock(date: str, *, regions: list[str],
                     rebuild_canonical: bool) -> int:
    _refresh(date, snapshot_type="close_or_lock", no_odds_fetch=False,
              regions=regions)
    _stat_grid(date)
    _build(date, snapshot="close_lock", rebuild_canonical=rebuild_canonical)
    _refresh_index()
    return 0


def run_after_game(date: str) -> int:
    _refresh(date, snapshot_type="morning_7am", no_odds_fetch=True,
              regions=["us"])
    _score(date)
    _refresh_index()
    return 0


def run_full_day(date: str, *, regions: list[str],
                   rebuild_canonical: bool, do_predict: bool) -> int:
    run_morning(date, regions=regions, rebuild_canonical=rebuild_canonical,
                  do_predict=do_predict)
    run_pre_close(date, regions=regions, rebuild_canonical=False)
    run_close_lock(date, regions=regions, rebuild_canonical=False)
    run_after_game(date)
    return 0


# ── Main ──────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True,
                     help="delivery calendar date YYYY-MM-DD (US/Eastern)")
    ap.add_argument("--mode", required=True,
                     choices=["morning", "pre_close", "close_lock",
                              "after_game", "full_day"])
    ap.add_argument("--regions", nargs="+", default=["us", "us2"])
    ap.add_argument("--rebuild-canonical", action="store_true",
                     help="passes through to build_daily_pmf_delivery.py")
    ap.add_argument("--predict", action="store_true",
                     help="run scripts/predict.py before refresh in "
                           "morning / full_day modes (requires BDL_API_KEY)")
    args = ap.parse_args()

    print("=" * 72)
    print(f"daily delivery pipeline — date={args.date}  mode={args.mode}")
    print(f"  regions={args.regions}  rebuild_canonical={args.rebuild_canonical}"
          f"  predict={args.predict}")
    print(f"  started_at_utc={datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')}")
    print("=" * 72)

    if args.mode == "morning":
        return run_morning(args.date, regions=args.regions,
                            rebuild_canonical=args.rebuild_canonical,
                            do_predict=args.predict)
    if args.mode == "pre_close":
        return run_pre_close(args.date, regions=args.regions,
                              rebuild_canonical=args.rebuild_canonical)
    if args.mode == "close_lock":
        return run_close_lock(args.date, regions=args.regions,
                                rebuild_canonical=args.rebuild_canonical)
    if args.mode == "after_game":
        return run_after_game(args.date)
    if args.mode == "full_day":
        return run_full_day(args.date, regions=args.regions,
                             rebuild_canonical=args.rebuild_canonical,
                             do_predict=args.predict)
    return 1


if __name__ == "__main__":
    sys.exit(main())
