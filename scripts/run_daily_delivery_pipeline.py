"""Single orchestrator for the daily PMF delivery lifecycle.

Wraps `refresh_daily_inputs.py`, optionally `predict.py`,
`build_availability_table.py` (slate-date merge preflight),
`verify_oddsapi_market_registry_contract.py`,
`verify_availability_freshness.py`, `build_stat_grid_pmfs.py`,
`build_daily_pmf_delivery.py`, and `score_daily_pmf_delivery_after_game.py`
behind one CLI so the GitHub Actions workflow (and the on-call operator)
can invoke a full snapshot run with a single command.

Modes
-----
    woo_morning_monetization   first WoO public run of the day. Refresh inputs,
                               build canonical delivery (snapshot=morning), build
                               Derek morning forward feed (expected-lineup stamp),
                               public WoO export with snapshot_type_label=
                               woo_morning_monetization and finality_status_override=
                               PROVISIONAL_EARLY_MARKET, refresh index.
    woo_afternoon_refresh      mid-afternoon WoO public refresh. Same as above
                               but with snapshot=pre_close and snapshot_type_label=
                               woo_afternoon_refresh. Never builds Derek forward feed.
    derek_pre_tipoff_refresh   Derek's first evaluation-grade snapshot, fired
                               in the pre-tipoff window (T-35 down to T-5) so
                               BDL confirmed lineups can flow in as soon as
                               they drop. Refresh inputs, build delivery
                               (snapshot=pre_close), build Derek forward feed
                               (--snapshot lineup), refresh public WoO export
                               with the lineup-aware snapshot.
                               (legacy alias accepted: derek_near_lineup)
    close_lock                 final lineup/market lock. Build delivery
                               (snapshot=close_lock), refresh Derek feed and WoO
                               public export.
    after_game                 skip odds fetch, run after-game scorer, refresh
                               Derek latest_available_snapshot pointer.
    morning                    legacy/backfill morning run; manual-only since
                               Phase 12D.
    pre_close                  alias for derek_pre_tipoff_refresh retained for
                               backwards compatibility.
    derek_near_lineup          legacy alias for derek_pre_tipoff_refresh.
    full_day                   morning → derek_pre_tipoff_refresh → close_lock →
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
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
_SRC = REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from nba_props_model.delivery.delivery_contract import (  # noqa: E402
    PIPELINE_MODE_BY_RUN_MODE,
    RunMode,
)

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
# Must use scripts/predict.py: pipelines/predict.py's __main__ calls main()
# without argv, so `--date` would be ignored when invoked as a file.
PREDICT = REPO_ROOT / "scripts" / "predict.py"
STAT_GRID = REPO_ROOT / "scripts" / "build_stat_grid_pmfs.py"
CANONICAL_FROM_STAT_GRID = REPO_ROOT / "scripts" / "build_model_only_canonical_from_stat_grid.py"
BUILD_AVAILABILITY = REPO_ROOT / "scripts" / "build_availability_table.py"
VERIFY_AVAILABILITY = REPO_ROOT / "scripts" / "verify_availability_freshness.py"
VERIFY_ODDSAPI_REGISTRY = REPO_ROOT / "scripts" / "verify_oddsapi_market_registry_contract.py"
INDEX = REPO_ROOT / "scripts" / "build_deliveries_index.py"
DEREK_FEED = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"
DEREK_GAME_SNAPSHOTS_FROM_DELIVERY = REPO_ROOT / "scripts" / "build_derek_game_snapshots_from_delivery.py"
WOO_EXPORT = REPO_ROOT / "scripts" / "publish_woo_public_export.py"
WOO_DASHBOARD = REPO_ROOT / "scripts" / "build_woo_dashboard.py"
CORRECTED_PMF_VERIFY = REPO_ROOT / "scripts" / "verify_corrected_pmf_delivery.py"
BUILD_EVENT_MARKET_LOSS = REPO_ROOT / "scripts" / "build_event_market_loss_rows.py"
BUILD_PROMOTION_CLAIM = REPO_ROOT / "scripts" / "build_promotion_claim_report.py"
BUILD_STAT_ROLE_SUPERIORITY = REPO_ROOT / "scripts" / "build_stat_role_market_superiority_report.py"
DIAGNOSE_MARKET_SUPERIORITY = REPO_ROOT / "scripts" / "diagnose_market_superiority_failures.py"
VERIFY_RA_ROLE_CALIBRATION = REPO_ROOT / "scripts" / "verify_ra_role_calibration_contract.py"
VERIFY_COMBO_ROLE_CALIBRATION = REPO_ROOT / "scripts" / "verify_combo_role_calibration_contract.py"
AUDIT_DAILY_DELIVERY = REPO_ROOT / "scripts" / "audit_daily_delivery_completeness.py"
VERIFY_DEREK_CONTRACT = REPO_ROOT / "scripts" / "verify_derek_forward_feed_contract.py"
AUDIT_INJURY_LINEUP = REPO_ROOT / "scripts" / "audit_injury_lineup_run_modes.py"
AUDIT_GITHUB_AUTOMATION = REPO_ROOT / "scripts" / "audit_github_delivery_automation.py"
BUILD_FEATURE_SNAPSHOT = REPO_ROOT / "scripts" / "build_player_prop_feature_snapshot.py"
FETCH_BDL_LINEUPS = REPO_ROOT / "scripts" / "fetch_bdl_game_lineups.py"


def _run(cmd: list[str], *, allow_fail: bool = False, label: str = "") -> int:
    """Inherit stdout/stderr so subprocess output is visible in CI logs.
    Returns the exit code; raises on non-zero unless allow_fail."""
    print(f"\n[$] {label or ' '.join(cmd)}")
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(REPO_ROOT / "src"))
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env)
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


def _preflight_before_stat_grid(date: str, *, availability_mode: str) -> int:
    """M8.6: rebuild today's availability slice, verify Odds API registry,
    then enforce availability freshness before PMF stat grid."""
    if FETCH_BDL_LINEUPS.exists():
        _run(
            [PYTHON, str(FETCH_BDL_LINEUPS), "--delivery-date", date],
            label=f"fetch_bdl_game_lineups --delivery-date {date}",
        )
    if BUILD_AVAILABILITY.exists():
        _run(
            [PYTHON, str(BUILD_AVAILABILITY), "--slate-date", date],
            label=f"build_availability_table --slate-date {date}",
        )
    if VERIFY_ODDSAPI_REGISTRY.exists():
        _run(
            [PYTHON, str(VERIFY_ODDSAPI_REGISTRY)],
            label="verify_oddsapi_market_registry_contract",
        )
    if VERIFY_AVAILABILITY.exists():
        _run(
            [
                PYTHON, str(VERIFY_AVAILABILITY),
                "--date", date,
                "--mode", availability_mode,
            ],
            label=f"verify_availability_freshness ({availability_mode})",
        )
    return 0


def _feature_snapshot(date: str, *, run_mode_stamp: str) -> Path | None:
    """Build feature snapshot for the run mode (best-effort)."""
    if not BUILD_FEATURE_SNAPSHOT.exists():
        return None
    out = REPO_ROOT / "data" / "features" / f"player_prop_features_{date}_{run_mode_stamp}.parquet"
    rc = _run(
        [
            PYTHON,
            str(BUILD_FEATURE_SNAPSHOT),
            "--date",
            date,
            "--run-mode",
            run_mode_stamp,
            "--out",
            str(out),
        ],
        allow_fail=True,
        label=f"feature_snapshot {date} {run_mode_stamp}",
    )
    if rc != 0:
        return None
    return out if out.is_file() else None


def _stat_grid(date: str, *, feature_snapshot_path: Path | None = None) -> int:
    """Phase 12 Part G: emit `predictions/stat_grid_{date}.parquet` so
    the canonical build can include TOV (and any other model-only stats
    BDL doesn't sell). Allowed to fail — the canonical build still works
    without TOV when this step is skipped.

    Default stats are the 12-stat mission grid from
    ``build_stat_grid_pmfs.DEFAULT_STATS`` (includes ``ra``).
    """
    if not STAT_GRID.exists():
        return 0
    cmd = [PYTHON, str(STAT_GRID), "--date", date]
    if feature_snapshot_path is not None and feature_snapshot_path.is_file():
        cmd.extend(["--feature-snapshot", str(feature_snapshot_path)])
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


def _ensure_after_game_scoring_pending_placeholder(date: str) -> None:
    """When the after-game scorer has not run, keep a rectangular delivery tree.

    ``verify_morning_delivery_completeness.py`` accepts this manifest instead of
    scored parquet/CSV (M8.6 morning automation contract).
    """
    after_game_dir = REPO_ROOT / "deliveries" / date / "after_game_scoring"
    if (after_game_dir / "after_game_scoring.parquet").exists():
        return
    if (after_game_dir / "after_game_scoring.csv").exists():
        return
    after_game_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "after_game_scoring_status": "pending_actuals",
        "delivery_date": date,
        "reason": (
            "Box-score outcomes not yet available; placeholder until "
            "scripts/score_daily_pmf_delivery_after_game.py runs."
        ),
    }
    (after_game_dir / "after_game_scoring_placeholder_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _derek_feed(date: str, *, snapshot: str, run_mode_stamp: str | None = None) -> int:
    """Phase 12C: build Derek's forward-looking PMF feed for the date.

    `morning` snapshot is built whenever the canonical model_only.parquet
    exists. `lineup` snapshot is honestly skipped (with a status JSON)
    when no pre_close/close_lock package is on disk; the builder never
    fabricates a lineup snapshot."""
    if not DEREK_FEED.exists():
        return 0
    cmd = [PYTHON, str(DEREK_FEED), "--date", date, "--snapshot", snapshot]
    if run_mode_stamp:
        cmd.extend(["--run-mode", run_mode_stamp])
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


def _m86_event_market_validation_bundle(date: str) -> int:
    """M8.6 — event-market loss rows, promotion report, stat-role superiority rollup.

    Best-effort (allow_fail): does not block the near-lineup publish when
    OOF↔market joins are incomplete; CI can run the same scripts with strict gates.
    """
    steps: list[tuple[Path, list[str]]] = [
        (BUILD_EVENT_MARKET_LOSS, ["--as-of-date", date]),
        (BUILD_PROMOTION_CLAIM, ["--as-of-date", date]),
        (BUILD_STAT_ROLE_SUPERIORITY, ["--date", date]),
        (DIAGNOSE_MARKET_SUPERIORITY, ["--date", date]),
        (VERIFY_RA_ROLE_CALIBRATION, ["--date", date]),
        (VERIFY_COMBO_ROLE_CALIBRATION, ["--date", date]),
    ]
    for path, extra in steps:
        if not path.exists():
            continue
        _run([PYTHON, str(path), *extra], allow_fail=True, label=path.name)
    return 0



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


# ── M8.8 verification + run-mode resolution ───────────────────────────────


LEGACY_MODE_TO_RUN_STAMP: dict[str, str] = {
    "woo_morning_monetization": "morning_expected",
    "woo_afternoon_refresh": "morning_expected",
    "derek_pre_tipoff_refresh": "t25",
    "derek_near_lineup": "t25",  # legacy alias
    "pre_close": "t25",  # legacy alias
    "close_lock": "t5",
    "after_game": "final_after_game",
    "morning": "morning_expected",
    "full_day": "unspecified",
}


def _predictions_or_stat_grid_exists(date: str) -> bool:
    p1 = REPO_ROOT / "predictions" / f"all_props_{date}.parquet"
    p2 = REPO_ROOT / "predictions" / f"stat_grid_{date}.parquet"
    return p1.is_file() or p2.is_file()


def _resolve_internal_pipeline_mode(args: argparse.Namespace) -> str:
    if getattr(args, "run_mode", None):
        return PIPELINE_MODE_BY_RUN_MODE[RunMode(args.run_mode)]
    m = getattr(args, "mode", None)
    if not m:
        sys.exit("FATAL: internal mode unresolved")
    return str(m)


def _resolve_run_mode_stamp(args: argparse.Namespace) -> str:
    if getattr(args, "run_mode", None):
        return str(args.run_mode)
    m = getattr(args, "mode", None)
    if m:
        return LEGACY_MODE_TO_RUN_STAMP.get(str(m), "unspecified")
    return "unspecified"


def _same_day_source_inputs_ok(date: str) -> tuple[bool, list[str]]:
    miss: list[str] = []
    canon = _canonical_model_only_path(date)
    if not canon.is_file():
        miss.append(str(canon.relative_to(REPO_ROOT)))
    if not _predictions_or_stat_grid_exists(date):
        miss.append("predictions/all_props_<date>.parquet_or_stat_grid_<date>.parquet")
    return (len(miss) == 0), miss


def _verify_m88_delivery_bundle(
    date: str,
    run_stamp: str,
    *,
    fail_on_missing: bool,
) -> int:
    """Run delivery completeness + Derek contract + injury-lineup + GitHub audits."""

    outd = REPO_ROOT / "artifacts" / "model_diagnostics" / "daily_delivery_completeness_last_run"
    prev = (datetime.strptime(date, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()
    active_mode_args: list[str] = []
    if run_stamp in {m.value for m in RunMode}:
        active_mode_args = ["--active-run-mode", run_stamp]
    steps: list[tuple[str, list[str]]] = [
        (
            "audit_daily_delivery_completeness",
            [
                PYTHON,
                str(AUDIT_DAILY_DELIVERY),
                "--start-date",
                date,
                "--end-date",
                date,
                "--out-dir",
                str(outd),
                "--include-current-if-present",
                "--run-mode",
                run_stamp,
            ],
        ),
        (
            "verify_derek_forward_feed_contract",
            [
                PYTHON,
                str(VERIFY_DEREK_CONTRACT),
                "--date",
                date,
                "--run-mode",
                run_stamp,
            ],
        ),
        (
            "audit_injury_lineup_run_modes",
            [
                PYTHON,
                str(AUDIT_INJURY_LINEUP),
                "--date",
                date,
                "--latest-completed-date",
                prev,
                *active_mode_args,
            ],
        ),
        ("audit_github_delivery_automation", [PYTHON, str(AUDIT_GITHUB_AUTOMATION)]),
    ]
    worst = 0
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(REPO_ROOT / "src"))
    for label, cmd in steps:
        if not Path(cmd[1]).exists():
            print(f"  [verify] skip missing script {cmd[1]}")
            continue
        print(f"\n[$] {label}")
        rc = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env).returncode
        if (
            rc != 0
            and run_stamp == "morning_expected"
            and label == "audit_daily_delivery_completeness"
        ):
            print(
                "  [verify] warning: audit_daily_delivery_completeness failed in morning mode; "
                "continuing as non-blocking provisional check"
            )
            rc = 0
        worst = max(worst, int(rc))
    if run_stamp == "morning_expected":
        ok, miss = _same_day_source_inputs_ok(date)
        if not ok:
            print("SAME_DAY_SOURCE_INPUTS_MISSING")
            for m in miss:
                print(f"  - {m}")
            if fail_on_missing:
                return max(worst, 3)
    if worst != 0 and fail_on_missing:
        sys.exit(worst)
    return worst


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
    _preflight_before_stat_grid(date, availability_mode="close_lock")
    fs = _feature_snapshot(date, run_mode_stamp="morning_expected")
    _stat_grid(date, feature_snapshot_path=fs)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="morning", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _derek_feed(date, snapshot="morning", run_mode_stamp="morning_expected")
    _derek_game_snapshots_from_delivery(date, snapshot_type="morning")
    _ensure_after_game_scoring_pending_placeholder(date)
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
    _preflight_before_stat_grid(date, availability_mode="close_lock")
    fs = _feature_snapshot(date, run_mode_stamp="morning_expected")
    _stat_grid(date, feature_snapshot_path=fs)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="morning", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _derek_feed(date, snapshot="morning", run_mode_stamp="morning_expected")
    _derek_game_snapshots_from_delivery(date, snapshot_type="morning")
    _woo_export(
        snapshot_type_label="woo_morning_monetization",
        finality_status_override="PROVISIONAL_EARLY_MARKET",
        only_date=date,
    )
    _ensure_after_game_scoring_pending_placeholder(date)
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
    _preflight_before_stat_grid(date, availability_mode="close_lock")
    fs = _feature_snapshot(date, run_mode_stamp="morning_expected")
    _stat_grid(date, feature_snapshot_path=fs)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="pre_close", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _woo_export(
        snapshot_type_label="woo_afternoon_refresh",
        finality_status_override="PROVISIONAL_EARLY_MARKET",
        only_date=date,
    )
    _ensure_after_game_scoring_pending_placeholder(date)
    _refresh_index()
    return 0


def run_derek_pre_tipoff_refresh(
    date: str, *, regions: list[str], rebuild_canonical: bool,
) -> int:
    """Phase 12D-amend mode 3 — Derek's first evaluation-grade snapshot.

    Fires during the pre-tipoff window (T-35 down to T-5) so BDL confirmed
    lineups can flow in as soon as they drop. Refreshes odds, rebuilds the
    canonical pre_close package, builds Derek's forward feed
    (`--snapshot lineup`), and re-publishes the WoO public export so the
    monetization feed picks up the lineup-aware data. The WoO export
    inherits the canonical run manifest's snapshot_type / finality_status
    (no override).

    Legacy callers can still use ``run_derek_near_lineup`` (a thin
    backward-compat shim defined immediately below)."""
    _refresh(date, snapshot_type="close_or_lock", no_odds_fetch=False,
              regions=regions)
    _preflight_before_stat_grid(date, availability_mode="close_lock")
    fs = _feature_snapshot(date, run_mode_stamp="t25")
    _stat_grid(date, feature_snapshot_path=fs)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="pre_close", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _derek_feed(date, snapshot="lineup", run_mode_stamp="t25")
    _derek_game_snapshots_from_delivery(date, snapshot_type="lineup")
    _woo_export(
        snapshot_type_label=None,
        finality_status_override=None,
        only_date=date,
    )
    _verify_corrected_pmf_delivery(date)
    _m86_event_market_validation_bundle(date)
    _ensure_after_game_scoring_pending_placeholder(date)
    _refresh_index()
    return 0


def run_derek_near_lineup(*args, **kwargs):
    """Backward-compat shim. Calls ``run_derek_pre_tipoff_refresh`` so
    legacy importers and CI scripts keep working unchanged. New code
    should call ``run_derek_pre_tipoff_refresh`` directly."""
    return run_derek_pre_tipoff_refresh(*args, **kwargs)


def run_close_lock(date: str, *, regions: list[str],
                     rebuild_canonical: bool) -> int:
    _refresh(date, snapshot_type="close_or_lock", no_odds_fetch=False,
              regions=regions)
    _preflight_before_stat_grid(date, availability_mode="close_lock")
    fs = _feature_snapshot(date, run_mode_stamp="t5")
    _stat_grid(date, feature_snapshot_path=fs)
    model_only_path = _canonical_from_stat_grid(date) if rebuild_canonical else None
    _build(date, snapshot="close_lock", rebuild_canonical=rebuild_canonical, model_only_path=model_only_path)
    _derek_feed(date, snapshot="lineup", run_mode_stamp="t5")
    _derek_game_snapshots_from_delivery(date, snapshot_type="close_lock")
    _woo_export(
        snapshot_type_label=None,
        finality_status_override=None,
        only_date=date,
    )
    _verify_corrected_pmf_delivery(date)
    _m86_event_market_validation_bundle(date)
    _ensure_after_game_scoring_pending_placeholder(date)
    _refresh_index()
    return 0


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _parquet_row_count(path: Path) -> int | None:
    """Return the row count of a parquet file, or None if unreadable.

    Uses pyarrow.parquet.read_metadata so we never materialise the whole
    table; this is cheap even on multi-GB feeds.
    """
    if not path.is_file():
        return None
    try:
        import pyarrow.parquet as pq
    except Exception:
        return None
    try:
        return int(pq.read_metadata(str(path)).num_rows)
    except Exception:
        return None


def _detect_no_games_day(date: str) -> tuple[bool, dict]:
    """Return (is_no_games, evidence) for ``date``.

    True only when *all* of the available upstream evidence points to a
    true no-game slate (i.e. predict.py was honest about producing zero
    rows, and the canonical core-PMF parquet matches). We never short-
    circuit when files are simply missing — that would mask real outages.

    Specifically the function returns True only when:

    * ``predictions/all_props_<date>.parquet`` exists AND has zero rows.
    * ``deliveries/<date>/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet``
      exists AND has zero rows.

    Either parquet being missing, unreadable, or non-empty causes this
    function to return False so the normal after-game flow continues
    (the operator will see the real failure mode if data is missing).
    """
    pred = REPO_ROOT / "predictions" / f"all_props_{date}.parquet"
    canon = (
        REPO_ROOT
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    pred_rows = _parquet_row_count(pred)
    canon_rows = _parquet_row_count(canon)
    evidence = {
        "delivery_date": date,
        "checked_at_utc": _now_utc_iso(),
        "predictions_parquet": {
            "path": str(pred.relative_to(REPO_ROOT)),
            "exists": pred.is_file(),
            "rows": pred_rows,
        },
        "canonical_model_only_parquet": {
            "path": str(canon.relative_to(REPO_ROOT)),
            "exists": canon.is_file(),
            "rows": canon_rows,
        },
    }
    is_no_games = (
        pred.is_file() and pred_rows == 0
        and canon.is_file() and canon_rows == 0
    )
    return is_no_games, evidence


def _emit_after_game_no_games_skip(date: str, evidence: dict) -> None:
    """Write Derek-folder status JSON and the slate-level sentinel that
    downstream verifiers consult to short-circuit cleanly on a true
    no-game day. Idempotent — safe to invoke multiple times."""
    base = REPO_ROOT / "deliveries" / date
    derek_dir = base / "derek_forward_feed"
    derek_dir.mkdir(parents=True, exist_ok=True)
    after_game_dir = base / "after_game_scoring"
    after_game_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "delivery_date": date,
        "status": "after_game_skipped_no_games_prev_day",
        "reason": (
            "Predictions parquet and canonical MODEL_ONLY parquet for this "
            "slate both report 0 rows; the after-game scorer has nothing to "
            "do. This is the honest no-game-day path, not a data outage."
        ),
        "evidence": evidence,
        "emitted_by": "scripts/run_daily_delivery_pipeline.py:run_after_game",
    }
    (derek_dir / "after_game_no_games_status.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (after_game_dir / "no_games_status.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (base / "no_games_today.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        f"::notice::DEREK_AFTER_GAME_VALID_SKIP date={date} "
        "reason=no_games_prev_day"
    )
    print(f"DEREK_AFTER_GAME_VALID_SKIP date={date} reason=no_games_prev_day")


def run_after_game(date: str) -> tuple[int, bool]:
    """Run the after-game flow for ``date``.

    Returns ``(exit_code, skip_verify)``. ``skip_verify=True`` tells
    ``main()`` to bypass the M8.8 verify bundle because this run is a
    valid no-game-day short-circuit (the verifier would otherwise red-
    flag the missing derek_forward_feed.parquet on a slate that had no
    games to score in the first place).
    """
    _refresh(date, snapshot_type="morning_7am", no_odds_fetch=True,
              regions=["us"])

    is_no_games, evidence = _detect_no_games_day(date)
    if is_no_games:
        _emit_after_game_no_games_skip(date, evidence)
        _refresh_index()
        return 0, True

    _score(date)
    # Preserve any existing forward-feed files; rebuild the snapshot
    # pointer so latest_available_snapshot reflects the freshest snapshot
    # on disk. If neither morning nor lineup sources exist this no-ops.
    _derek_feed(date, snapshot="both", run_mode_stamp="final_after_game")
    _refresh_index()
    return 0, False


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
    run_after_game(date)  # tuple return — full_day ignores skip_verify
    return 0


# ── Main ──────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--date",
        required=True,
        help="delivery calendar date YYYY-MM-DD (US/Eastern)",
    )
    mx = ap.add_mutually_exclusive_group(required=True)
    mx.add_argument(
        "--mode",
        choices=[
            "woo_morning_monetization",
            "woo_afternoon_refresh",
            "derek_pre_tipoff_refresh",
            "derek_near_lineup",
            "close_lock",
            "after_game",
            "full_day",
            "morning",
            "pre_close",
        ],
        help=(
            "legacy pipeline mode (Phase 12D). derek_near_lineup is a "
            "legacy alias for derek_pre_tipoff_refresh."
        ),
    )
    mx.add_argument(
        "--run-mode",
        dest="run_mode",
        choices=[m.value for m in RunMode],
        help="M8.8 consumer run mode (preferred). Maps to internal --mode.",
    )
    ap.add_argument("--regions", nargs="+", default=["us", "us2"])
    ap.add_argument(
        "--rebuild-canonical",
        action="store_true",
        help="passes through to build_daily_pmf_delivery.py",
    )
    ap.add_argument(
        "--predict",
        action="store_true",
        help="run scripts/predict.py before refresh in morning / full_day modes",
    )
    ap.add_argument(
        "--force-run",
        action="store_true",
        help="bypass the tipoff-window gate (Phase 12D)",
    )
    ap.add_argument(
        "--verify",
        action="store_true",
        help="run M8.8 delivery completeness + Derek contract + audits after pipeline",
    )
    ap.add_argument(
        "--fail-on-missing-delivery",
        action="store_true",
        help="non-zero exit if any verifier fails (implies --verify)",
    )
    args = ap.parse_args()
    if args.fail_on_missing_delivery:
        args.verify = True

    internal = _resolve_internal_pipeline_mode(args)
    stamp = _resolve_run_mode_stamp(args)

    print("=" * 72)
    print(
        f"daily delivery pipeline — date={args.date}  internal_mode={internal}  "
        f"run_mode_stamp={stamp}"
    )
    print(
        f"  regions={args.regions}  rebuild_canonical={args.rebuild_canonical}"
        f"  predict={args.predict}  force_run={args.force_run}  verify={args.verify}"
    )
    print(
        f"  started_at_utc={datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')}"
    )
    print("=" * 72)

    proceed, reason = _check_tipoff_window(
        args.date, mode=internal, force=args.force_run
    )
    print(f"[gate] proceed={proceed}  reason={reason}")
    if not proceed:
        print("No games in lineup-refresh window; nothing to publish.")
        return 0

    rc = 0
    if internal == "morning":
        rc = run_morning(
            args.date,
            regions=args.regions,
            rebuild_canonical=args.rebuild_canonical,
            do_predict=args.predict,
        )
    elif internal == "woo_morning_monetization":
        rc = run_woo_morning_monetization(
            args.date,
            regions=args.regions,
            rebuild_canonical=args.rebuild_canonical,
            do_predict=args.predict,
        )
    elif internal == "woo_afternoon_refresh":
        rc = run_woo_afternoon_refresh(
            args.date,
            regions=args.regions,
            rebuild_canonical=args.rebuild_canonical,
        )
    elif internal in {"derek_pre_tipoff_refresh", "derek_near_lineup", "pre_close"}:
        rc = run_derek_pre_tipoff_refresh(
            args.date,
            regions=args.regions,
            rebuild_canonical=args.rebuild_canonical,
        )
    elif internal == "close_lock":
        rc = run_close_lock(
            args.date,
            regions=args.regions,
            rebuild_canonical=args.rebuild_canonical,
        )
    elif internal == "after_game":
        rc, skip_verify = run_after_game(args.date)
        if skip_verify:
            args.verify = False
            args.fail_on_missing_delivery = False
    elif internal == "full_day":
        rc = run_full_day(
            args.date,
            regions=args.regions,
            rebuild_canonical=args.rebuild_canonical,
            do_predict=args.predict,
        )
    else:
        return 1

    if args.verify:
        vrc = _verify_m88_delivery_bundle(
            args.date,
            stamp,
            fail_on_missing=bool(args.fail_on_missing_delivery),
        )
        rc = max(rc, vrc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
