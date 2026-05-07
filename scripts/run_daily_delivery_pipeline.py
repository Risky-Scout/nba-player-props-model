"""Single orchestrator for the daily PMF delivery lifecycle.

Wraps `refresh_daily_inputs.py`, optionally `predict.py`,
`build_daily_pmf_delivery.py`, and `score_daily_pmf_delivery_after_game.py`
behind one CLI so the GitHub Actions workflow (and the on-call operator)
can invoke a full snapshot run with a single command.

Modes
-----
    woo_morning_monetization   first WoO public run of the day. Refresh inputs,
                               build canonical delivery (snapshot=morning), build
                               public WoO export with snapshot_type_label=
                               woo_morning_monetization and finality_status_override=
                               PROVISIONAL_EARLY_MARKET, refresh index. Never
                               touches Derek's evaluation feed.
    woo_afternoon_refresh      mid-afternoon WoO public refresh. Same as above
                               but with snapshot=pre_close and snapshot_type_label=
                               woo_afternoon_refresh. Never touches Derek's feed.
    derek_near_lineup          Derek's first evaluation-grade snapshot. Refresh
                               inputs, build delivery (snapshot=pre_close), build
                               Derek forward feed (--snapshot lineup), refresh
                               public WoO export with the lineup-aware snapshot.
    close_lock                 final lineup/market lock. Build delivery
                               (snapshot=close_lock), refresh Derek feed and WoO
                               public export.
    after_game                 skip odds fetch, run after-game scorer, refresh
                               Derek latest_available_snapshot pointer.
    morning                    legacy/backfill morning run; manual-only since
                               Phase 12D.
    pre_close                  alias for derek_near_lineup retained for
                               backwards compatibility.
    full_day                   morning → derek_near_lineup → close_lock →
                               after_game in sequence (manual full backfill).

Hard rules echoed from the spec:
- Never logs the API key (predict.py / refresh use os.environ directly).
- Never wires Phase 10D / 10D.2 TOV overlays.
- Never market-anchors model-only PMFs.
- Never fabricates predictions, injuries, lineups, role buckets, or odds.
- Never fabricates affiliate links — when config/wizardofodds_affiliate_links.json
  is missing or has no entry for a book, monetization_status=needs_affiliate_mapping
  and the URL fields stay blank.
- Never stages data/odds_api/, data/freshness_manifest/, artifacts/, logs.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

# Phase 12D — first publishable scheduled run is at earliest tipoff − 35
# minutes (default 22:25 UTC during NBA playoffs). Refreshes fire every
# 15 minutes through the slate. The cron schedule itself is the primary
# timing control; the gate below skips runs that have no game tipoff
# anywhere in [now − 15 min, now + 45 min] when schedule data is on
# disk. When schedule data is unavailable (e.g. fresh GitHub Actions
# runner before refresh_daily_inputs.py runs), the gate is permissive.
TIPOFF_WINDOW_PRE_MIN = 45
TIPOFF_WINDOW_POST_MIN = 15

REFRESH = REPO_ROOT / "scripts" / "refresh_daily_inputs.py"
BUILD = REPO_ROOT / "scripts" / "build_daily_pmf_delivery.py"
SCORE = REPO_ROOT / "scripts" / "score_daily_pmf_delivery_after_game.py"
PREDICT = REPO_ROOT / "src" / "nba_props_model" / "pipelines" / "predict.py"
STAT_GRID = REPO_ROOT / "scripts" / "build_stat_grid_pmfs.py"
CANONICAL_FROM_STAT_GRID = REPO_ROOT / "scripts" / "build_model_only_canonical_from_stat_grid.py"
INDEX = REPO_ROOT / "scripts" / "build_deliveries_index.py"
DEREK_FEED = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"
DEREK_GAME_SNAPSHOTS_FROM_DELIVERY = REPO_ROOT / "scripts" / "build_derek_game_snapshots_from_delivery.py"
WOO_EXPORT = REPO_ROOT / "scripts" / "publish_woo_public_export.py"
WOO_DASHBOARD = REPO_ROOT / "scripts" / "build_woo_dashboard.py"
CORRECTED_PMF_VERIFY = REPO_ROOT / "scripts" / "verify_corrected_pmf_delivery.py"


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
    cmd = [
        PYTHON, str(STAT_GRID), "--date", date,
        "--stats", "pts", "reb", "ast", "fg3m", "tov",
    ]
    return _run(cmd, allow_fail=True, label=f"stat_grid {date}")


def _canonical_model_only_path(date: str) -> Path:
    return (
        REPO_ROOT
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )


def _canonical_from_stat_grid(date: str) -> Path | None:
    """Build canonical MODEL_ONLY parquet from the PMF-only stat grid."""
    if not CANONICAL_FROM_STAT_GRID.exists():
        print(f" canonical_from_stat_grid: {CANONICAL_FROM_STAT_GRID} missing, skipping")
        return None

    cmd = [PYTHON, str(CANONICAL_FROM_STAT_GRID), "--date", date]
    rc = _run(cmd, allow_fail=True, label=f"canonical_from_stat_grid {date}")
    if rc != 0:
        return None

    p = _canonical_model_only_path(date)
    return p if p.exists() else None


def _build(
    date: str,
    *,
    snapshot: str,
    rebuild_canonical: bool,
    model_only_path: Path | None = None,
) -> int:
    cmd = [PYTHON, str(BUILD), "--date", date, "--snapshot", snapshot]

    if model_only_path is not None:
        cmd.extend(["--model-only", str(model_only_path)])
    elif rebuild_canonical:
        cmd.append("--rebuild-canonical")

    return _run(cmd, label=f"build {date} {snapshot}")


def _score(date: str) -> int:
    cmd = [PYTHON, str(SCORE), "--date", date]
    return _run(cmd, allow_fail=True, label=f"score {date}")



def _derek_game_snapshots_from_delivery(date: str, *, snapshot_type: str) -> int:
    """Build Derek per-game snapshots from corrected WoO PMF delivery.

    This prevents false no_games_today.json when the corrected PMF delivery
    has games, and guarantees Derek uses the same core PMF source as WoO.
    """
    if not DEREK_GAME_SNAPSHOTS_FROM_DELIVERY.exists():
        print(f"  derek game snapshots: {DEREK_GAME_SNAPSHOTS_FROM_DELIVERY} missing, skipping")
        return 0
    cmd = [
        PYTHON, str(DEREK_GAME_SNAPSHOTS_FROM_DELIVERY),
        "--date", date,
        "--snapshot-type", snapshot_type,
        "--force",
    ]
    return _run(cmd, allow_fail=False, label=f"derek game snapshots from delivery ({snapshot_type})")



def _refresh_index() -> int:
    if not INDEX.exists():
        return 0
    cmd = [PYTHON, str(INDEX)]
    return _run(cmd, allow_fail=True, label="refresh deliveries index")


def _derek_feed(date: str, *, snapshot: str) -> int:
    """Phase 12C: build Derek's forward-looking PMF feed for the date.

    `morning` snapshot is built whenever the canonical model_only.parquet
    exists. `lineup` snapshot is honestly skipped (with a status JSON)
    when no pre_close/close_lock package is on disk; the builder never
    fabricates a lineup snapshot."""
    if not DEREK_FEED.exists():
        return 0
    cmd = [PYTHON, str(DEREK_FEED), "--date", date, "--snapshot", snapshot]
    return _run(cmd, allow_fail=True, label=f"derek forward feed ({snapshot})")


def _woo_export(
    *,
    snapshot_type_label: str | None,
    finality_status_override: str | None,
    only_date: str | None = None,
) -> int:
    """Build the protected customer-facing Wizard of Odds public export.

    This intentionally uses publish_woo_public_export.py, not the legacy
    build_wizard_of_odds_public_export.py. The protected publisher sources
    from deliveries/{date}/wizard_of_odds/full_pmfs_wide.parquet, rejects
    stale broad PMF packages, and refuses empty affiliate exports by default.
    """
    if not WOO_EXPORT.exists():
        return 0

    if not only_date:
        sys.exit(
            "FATAL: protected WoO publisher requires --date; refusing all-date "
            "customer export from run_daily_delivery_pipeline.py"
        )

    if snapshot_type_label or finality_status_override:
        print(
            "  woo public export: legacy snapshot/finality labels are ignored; "
            "protected JSON inherits the dated delivery manifest."
        )

    rc = _run(
        [PYTHON, str(WOO_EXPORT), "--date", only_date],
        allow_fail=False,
        label=f"publish woo public JSON {only_date}",
    )

    if WOO_DASHBOARD.exists():
        _run(
            [PYTHON, str(WOO_DASHBOARD), "--date", only_date],
            allow_fail=False,
            label=f"build woo dashboard {only_date}",
        )

    return rc



def _verify_corrected_pmf_delivery(date: str) -> int:
    """Hard gate: Derek + WoO must both source the corrected core PMF delivery."""
    if not CORRECTED_PMF_VERIFY.exists():
        sys.exit(f"FATAL: corrected PMF verifier missing: {CORRECTED_PMF_VERIFY}")
    return _run(
        [PYTHON, str(CORRECTED_PMF_VERIFY), "--date", date],
        allow_fail=False,
        label=f"verify corrected PMF delivery {date}",
    )



def _load_tipoffs_utc(date: str) -> list[datetime]:
    """Best-effort load of today's tipoff times in UTC. Reads from
    `data/odds_api/processed/{date}/*.parquet` (commence_time_utc), then
    `data/historical_game_odds.parquet` (commence_time) as fallback.
    Returns an empty list if no schedule data is on disk."""
    try:
        import pandas as pd
    except ImportError:
        return []

    odds_dir = REPO_ROOT / "data" / "odds_api" / "processed" / date
    if odds_dir.exists():
        files = sorted(odds_dir.glob("*.parquet"))
        if files:
            try:
                df = pd.read_parquet(files[-1], columns=["commence_time_utc"])
                vals = pd.to_datetime(
                    df["commence_time_utc"].dropna().unique(),
                    utc=True, errors="coerce")
                return [v.to_pydatetime() for v in vals if v is not None]
            except Exception as e:  # pragma: no cover — defensive
                print(f"  [gate] could not read {files[-1].name}: {e!r}")

    fallback = REPO_ROOT / "data" / "historical_game_odds.parquet"
    if fallback.exists():
        try:
            df = pd.read_parquet(
                fallback, columns=["game_date", "commence_time"])
            df = df[df["game_date"].astype(str) == date]
            vals = pd.to_datetime(
                df["commence_time"].dropna().unique(),
                utc=True, errors="coerce")
            return [v.to_pydatetime() for v in vals if v is not None]
        except Exception as e:  # pragma: no cover — defensive
            print(f"  [gate] could not read historical_game_odds: {e!r}")

    return []


def _check_tipoff_window(
    date: str,
    *,
    mode: str,
    force: bool,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """Return (proceed, reason). Schedule-driven gate that suppresses
    blind rebuilds when no game tipoff is within [now − 15, now + 45]
    minutes for the date.

    The gate is opt-in by mode: it only applies to lineup-refresh modes
    (`pre_close`, `close_lock`). `morning`, `after_game`, and
    `full_day` always proceed. When schedule data isn't on disk yet
    (fresh CI checkout pre-refresh), the gate is permissive — the cron
    schedule is the primary timing control."""
    if force:
        return True, "force-run override"
    # WoO monetization runs and morning backfills are scheduled at fixed
    # clock times; they're intentionally allowed to fire ahead of any
    # game's tipoff. Only Derek's near-lineup / close-lock evaluation
    # snapshots are gated on the tipoff window.
    if mode in {
        "morning",
        "woo_morning_monetization",
        "woo_afternoon_refresh",
        "after_game",
        "full_day",
    }:
        return True, f"mode={mode} skips tipoff gate"

    tipoffs = _load_tipoffs_utc(date)
    if not tipoffs:
        return True, "no schedule data on disk; cron-only enforcement"

    now = now or datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=TIPOFF_WINDOW_POST_MIN)
    window_end = now + timedelta(minutes=TIPOFF_WINDOW_PRE_MIN)
    in_window = [t for t in tipoffs if window_start <= t <= window_end]
    if in_window:
        return (
            True,
            f"{len(in_window)} tipoff(s) in [-{TIPOFF_WINDOW_POST_MIN},"
            f"+{TIPOFF_WINDOW_PRE_MIN}] min window",
        )
    earliest = min(tipoffs)
    return (
        False,
        f"now={now.isoformat(timespec='seconds')} earliest_tipoff="
        f"{earliest.isoformat(timespec='seconds')} — no games in "
        f"[-{TIPOFF_WINDOW_POST_MIN},+{TIPOFF_WINDOW_PRE_MIN}] min "
        "window",
    )


# ── Mode dispatchers ──────────────────────────────────────────────────────


def run_morning(date: str, *, regions: list[str], rebuild_canonical: bool,
                  do_predict: bool) -> int:
    """Manual-only legacy backfill (Phase 12D retired the morning cron).
    Builds the canonical morning delivery and Derek's morning snapshot,
    but **does not** publish a WoO public export — the WoO monetization
    feed has its own scheduled lifecycle starting at 15:00 UTC."""
    if do_predict:
        _predict(date)
    _refresh(date, snapshot_type="morning_7am", no_odds_fetch=False,
              regions=regions)
    _stat_grid(date)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="morning", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _derek_feed(date, snapshot="morning")
    _derek_game_snapshots_from_delivery(date, snapshot_type="morning")
    _refresh_index()
    return 0


def run_woo_morning_monetization(
    date: str, *, regions: list[str], rebuild_canonical: bool,
    do_predict: bool,
) -> int:
    """Phase 12D-amend mode 1 — first WoO public run of the day.

    Builds the canonical morning delivery, then the public WoO export
    stamped with snapshot_type_public=woo_morning_monetization and
    finality_status_public=PROVISIONAL_EARLY_MARKET. Does not touch
    Derek's evaluation feed — that runs later, near lineup time."""
    if do_predict:
        _predict(date)
    _refresh(date, snapshot_type="morning_7am", no_odds_fetch=False,
              regions=regions)
    _stat_grid(date)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="morning", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _woo_export(
        snapshot_type_label="woo_morning_monetization",
        finality_status_override="PROVISIONAL_EARLY_MARKET",
        only_date=date,
    )
    _refresh_index()
    return 0


def run_woo_afternoon_refresh(
    date: str, *, regions: list[str], rebuild_canonical: bool,
) -> int:
    """Phase 12D-amend mode 2 — mid-afternoon WoO public refresh.

    Refreshes odds and rebuilds the canonical pre_close package, then
    re-publishes the WoO public export. Still tagged
    PROVISIONAL_EARLY_MARKET because lineups typically aren't confirmed
    yet. Does not touch Derek's evaluation feed."""
    _refresh(date, snapshot_type="close_or_lock", no_odds_fetch=False,
              regions=regions)
    _stat_grid(date)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="pre_close", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _woo_export(
        snapshot_type_label="woo_afternoon_refresh",
        finality_status_override="PROVISIONAL_EARLY_MARKET",
        only_date=date,
    )
    _refresh_index()
    return 0


def run_derek_near_lineup(
    date: str, *, regions: list[str], rebuild_canonical: bool,
) -> int:
    """Phase 12D-amend mode 3 — Derek's first evaluation-grade snapshot.

    Refreshes odds, rebuilds the canonical pre_close package, builds
    Derek's forward feed (`--snapshot lineup`), and re-publishes the
    WoO public export so the monetization feed picks up the
    lineup-aware data. The WoO export inherits the canonical run
    manifest's snapshot_type / finality_status (no override)."""
    _refresh(date, snapshot_type="close_or_lock", no_odds_fetch=False,
              regions=regions)
    _stat_grid(date)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="pre_close", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _derek_feed(date, snapshot="lineup")
    _derek_game_snapshots_from_delivery(date, snapshot_type="lineup")
    _woo_export(
        snapshot_type_label=None,
        finality_status_override=None,
        only_date=date,
    )
    _verify_corrected_pmf_delivery(date)
    _refresh_index()
    return 0


def run_close_lock(date: str, *, regions: list[str],
                     rebuild_canonical: bool) -> int:
    _refresh(date, snapshot_type="close_or_lock", no_odds_fetch=False,
              regions=regions)
    _stat_grid(date)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="close_lock", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _derek_feed(date, snapshot="lineup")
    _derek_game_snapshots_from_delivery(date, snapshot_type="close_lock")
    _woo_export(
        snapshot_type_label=None,
        finality_status_override=None,
        only_date=date,
    )
    _verify_corrected_pmf_delivery(date)
    _refresh_index()
    return 0


def run_after_game(date: str) -> int:
    _refresh(date, snapshot_type="morning_7am", no_odds_fetch=True,
              regions=["us"])
    _score(date)
    # Preserve any existing forward-feed files; rebuild the snapshot
    # pointer so latest_available_snapshot reflects the freshest snapshot
    # on disk. If neither morning nor lineup sources exist this no-ops.
    _derek_feed(date, snapshot="both")
    _refresh_index()
    return 0


def run_full_day(date: str, *, regions: list[str],
                   rebuild_canonical: bool, do_predict: bool) -> int:
    run_woo_morning_monetization(
        date, regions=regions, rebuild_canonical=rebuild_canonical,
        do_predict=do_predict,
    )
    run_woo_afternoon_refresh(
        date, regions=regions, rebuild_canonical=False,
    )
    run_derek_near_lineup(
        date, regions=regions, rebuild_canonical=False,
    )
    run_close_lock(date, regions=regions, rebuild_canonical=False)
    run_after_game(date)
    return 0


# ── Main ──────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True,
                     help="delivery calendar date YYYY-MM-DD (US/Eastern)")
    ap.add_argument(
        "--mode",
        required=True,
        choices=[
            "woo_morning_monetization",
            "woo_afternoon_refresh",
            "derek_near_lineup",
            "close_lock",
            "after_game",
            "full_day",
            # legacy aliases
            "morning",
            "pre_close",
        ],
    )
    ap.add_argument("--regions", nargs="+", default=["us", "us2"])
    ap.add_argument("--rebuild-canonical", action="store_true",
                     help="passes through to build_daily_pmf_delivery.py")
    ap.add_argument("--predict", action="store_true",
                     help="run scripts/predict.py before refresh in "
                           "morning / full_day modes (requires BDL_API_KEY)")
    ap.add_argument("--force-run", action="store_true",
                     help="bypass the tipoff-window gate (Phase 12D); used "
                           "for manual backfills outside the lineup window")
    args = ap.parse_args()

    print("=" * 72)
    print(f"daily delivery pipeline — date={args.date}  mode={args.mode}")
    print(f"  regions={args.regions}  rebuild_canonical={args.rebuild_canonical}"
          f"  predict={args.predict}  force_run={args.force_run}")
    print(f"  started_at_utc={datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')}")
    print("=" * 72)

    proceed, reason = _check_tipoff_window(
        args.date, mode=args.mode, force=args.force_run)
    print(f"[gate] proceed={proceed}  reason={reason}")
    if not proceed:
        print("No games in lineup-refresh window; nothing to publish.")
        return 0

    if args.mode == "morning":
        return run_morning(args.date, regions=args.regions,
                            rebuild_canonical=args.rebuild_canonical,
                            do_predict=args.predict)
    if args.mode == "woo_morning_monetization":
        return run_woo_morning_monetization(
            args.date, regions=args.regions,
            rebuild_canonical=args.rebuild_canonical,
            do_predict=args.predict,
        )
    if args.mode == "woo_afternoon_refresh":
        return run_woo_afternoon_refresh(
            args.date, regions=args.regions,
            rebuild_canonical=args.rebuild_canonical,
        )
    # `pre_close` is retained as an alias for `derek_near_lineup` so
    # existing CI configs and operators don't break mid-flight.
    if args.mode in {"derek_near_lineup", "pre_close"}:
        return run_derek_near_lineup(
            args.date, regions=args.regions,
            rebuild_canonical=args.rebuild_canonical,
        )
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
