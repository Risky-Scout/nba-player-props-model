#!/usr/bin/env python3
"""Phase 13AM: Predictions readiness gate for daily_pmf_delivery.yml jobs.

The PMF Delivery workflow has crons that fire across the UTC day, including
windows that fire BEFORE the daily Daily-Pipeline predict cron at 13:00 UTC.
Before this gate existed, an early-morning delivery cron would crash on the
"Stage and commit" step because predictions/all_props_<date>.parquet (and
the matching display/singles JSONs) had not been produced yet for tonight's
slate. The crash surfaced as DELIVERY_CHAMPION_METADATA_STAMP_FAILED with a
missing deliveries/<date> directory — an opaque red failure that the
operator had to root-cause manually.

This gate centralizes the readiness check:

    1. Resolve the slate date (caller passes --date already resolved in
       America/New_York by the workflow).
    2. Check predictions/all_props_<date>.parquet, pmf_display_<date>.json,
       singles_<date>.json. If all three exist:
         - emit PREDICTIONS_READY
         - set should_proceed=true
         - exit 0 (job continues)
    3. If predictions are missing AND now (UTC) is before predict-cron-hour:
         - emit WAITING_FOR_PREDICTIONS_VALID_SKIP
         - set should_proceed=false
         - exit 0 GREEN (downstream steps gated `if: should_proceed=='true'`
           skip cleanly; job conclusion=success)
    4. If predictions are missing AND we are at/past the predict cron AND
       --no-run-predict is NOT passed (forward-looking modes):
         - invoke scripts/predict.py
         - if predict.py exits non-zero or still does not produce all
           three artifacts, fail loudly with PREDICT_PY_FAILED /
           PREDICT_OUTPUTS_MISSING and exit 1
         - on success, run scripts/verify_daily_prediction_outputs.py and
           continue with should_proceed=true
    5. If --no-run-predict is set (after-game mode for past slates):
         - emit WAITING_FOR_PREDICTIONS_VALID_SKIP if missing (no chance
           to regenerate a past slate's predictions from this workflow)
         - set should_proceed=false; exit 0

Hard rule: this gate must NEVER red-fail in cases (3) or (5). Only case
(4) — predictions are due AND predict.py was unable to produce them — is
allowed to fail the job, and it MUST do so visibly so the operator notices.

Output contract — exactly one of these tokens appears on stdout:

    PREDICTIONS_READY                       date=<DATE> mode=<MODE>
    WAITING_FOR_PREDICTIONS_VALID_SKIP      date=<DATE> mode=<MODE>
                                            reason=<early|past_slate|...>
    PREDICT_PY_FAILED                       date=<DATE> mode=<MODE>
    PREDICT_OUTPUTS_MISSING                 date=<DATE> mode=<MODE>

The gate also writes `should_proceed=true|false` to $GITHUB_OUTPUT so
downstream steps can gate themselves with
`if: steps.predict_gate.outputs.should_proceed == 'true'`.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path

from nba_props_model.data.bdl_client import get_games

REPO_ROOT = Path(__file__).resolve().parent.parent
PREDICTIONS_DIR = REPO_ROOT / "predictions"


def _emit_github_output(key: str, value: str) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        # Local invocation — print to stderr for operator inspection.
        print(f"[gate] would set {key}={value}", file=sys.stderr)
        return
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write(f"{key}={value}\n")


def _required_files(date: str) -> list[Path]:
    return [
        PREDICTIONS_DIR / f"all_props_{date}.parquet",
        PREDICTIONS_DIR / f"pmf_display_{date}.json",
        PREDICTIONS_DIR / f"singles_{date}.json",
    ]


def _missing(date: str) -> list[Path]:
    return [p for p in _required_files(date) if not p.exists()]


def _now_utc_hour() -> int:
    return _dt.datetime.now(_dt.timezone.utc).hour


def _now_utc() -> _dt.datetime:
    """Current UTC time as a timezone-aware datetime (date + hour)."""
    return _dt.datetime.now(_dt.timezone.utc)


def _emit(line: str) -> None:
    print(line, flush=True)


def _is_no_game_slate(date: str) -> bool:
    """Return True when BDL reports no games for the target slate date."""
    try:
        games = get_games(date)
        return len(games) == 0
    except Exception as exc:
        _emit(
            "::notice::no-game slate precheck unavailable; "
            f"continuing with readiness checks detail={exc}"
        )
        return False


def _proceed(date: str, mode: str) -> int:
    _emit(f"PREDICTIONS_READY date={date} mode={mode}")
    _emit_github_output("should_proceed", "true")
    return 0


def _valid_skip(date: str, mode: str, reason: str) -> int:
    _emit(
        f"WAITING_FOR_PREDICTIONS_VALID_SKIP date={date} mode={mode} reason={reason}"
    )
    _emit_github_output("should_proceed", "false")
    return 0


def _hard_fail(token: str, date: str, mode: str, detail: str = "") -> int:
    suffix = f" {detail}" if detail else ""
    _emit(f"::error::{token} date={date} mode={mode}{suffix}")
    _emit(f"{token} date={date} mode={mode}{suffix}")
    _emit_github_output("should_proceed", "false")
    return 1


def _run_predict_py(date: str) -> tuple[int, str]:
    """Invoke scripts/predict.py and stream its output. Return (rc, tail)."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "predict.py"),
        "--date",
        date,
    ]
    _emit(f"[gate] invoking {' '.join(cmd)}")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
            timeout=45 * 60,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, f"predict.py timed out after {exc.timeout}s"
    # Echo predict.py output verbatim so the operator audit trail in CI
    # captures everything (per Phase 13AM hard rule: surface stdout/stderr
    # when predict fails).
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    sys.stdout.flush()
    sys.stderr.flush()
    tail_src = proc.stderr or proc.stdout or ""
    tail = "\n".join(tail_src.splitlines()[-25:])
    return proc.returncode, tail


def _run_verifier(date: str) -> int:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "verify_daily_prediction_outputs.py"),
        "--date",
        date,
    ]
    _emit(f"[gate] invoking {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return proc.returncode


def _run_publish_nba_props_today(date: str) -> int:
    """Refresh predictions/nba_props_today.json for the slate date.

    Must run AFTER predict.py succeeds and BEFORE the verifier, so that
    verify_daily_prediction_outputs.py does not flag nba_props_today.json
    as stale.
    """
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "publish_nba_props_today.py"),
        "--date",
        date,
    ]
    _emit(f"[gate] invoking {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Slate date (YYYY-MM-DD).")
    parser.add_argument(
        "--predict-cron-hour-utc",
        type=int,
        default=13,
        help="Hour (UTC) at which the daily predict cron is scheduled.",
    )
    parser.add_argument(
        "--mode",
        required=True,
        help="Delivery mode (morning, derek_near_lineup, after_game, ...).",
    )
    parser.add_argument(
        "--no-run-predict",
        action="store_true",
        help=(
            "If set, do NOT invoke predict.py when predictions are missing. "
            "Used by the after-game job — there is no point regenerating a "
            "past slate's predictions from this workflow."
        ),
    )
    args = parser.parse_args()

    date = args.date
    mode = args.mode

    if _is_no_game_slate(date):
        return _valid_skip(date, mode, reason="no_games_slate")

    missing = _missing(date)
    if not missing:
        # Predictions exist — refresh nba_props_today.json from the dated
        # artifacts, then verify them before proceeding so we never hand
        # a corrupt parquet (or a stale today.json) to downstream delivery.
        publish_rc = _run_publish_nba_props_today(date)
        if publish_rc != 0:
            return _hard_fail(
                "PUBLISH_NBA_PROPS_TODAY_FAILED",
                date,
                mode,
                detail=f"publish_rc={publish_rc}",
            )
        verifier_rc = _run_verifier(date)
        if verifier_rc != 0:
            return _hard_fail(
                "PREDICT_OUTPUTS_VERIFIER_FAILED",
                date,
                mode,
                detail=f"verifier_rc={verifier_rc}",
            )
        return _proceed(date, mode)

    missing_names = ",".join(p.name for p in missing)
    _emit(f"[gate] predictions missing for {date} mode={mode} files={missing_names}")

    now_utc = _now_utc()
    now_hour = now_utc.hour
    today_utc = now_utc.date().isoformat()
    slate_date = date  # caller resolves this in America/New_York
    _emit(
        f"[gate] now_utc={now_utc.isoformat()} today_utc={today_utc} "
        f"slate_date={slate_date} predict_cron_hour_utc={args.predict_cron_hour_utc}"
    )

    # C1 fix: compare slate_date against today_utc to know whether the
    # predict cron has had a chance to fire FOR THIS SPECIFIC SLATE.
    # The previous logic compared only now_hour against predict_cron_hour_utc,
    # which silently fake-greened every cron firing between 00:00-13:00 UTC
    # for a past slate (slate_date < today_utc) because now_hour < 13 was
    # always true in that window.

    # Future slate: caller asked about a date we have not reached yet.
    if slate_date > today_utc:
        return _valid_skip(
            date,
            mode,
            reason=f"future_slate today_utc={today_utc}",
        )

    # Past slate: predict cron has already fired (or should have) for
    # this date. Forward-looking workflows must NOT try to regenerate
    # yesterday's predictions. Valid-skip with an honest reason.
    if slate_date < today_utc:
        return _valid_skip(
            date,
            mode,
            reason=f"past_slate today_utc={today_utc}",
        )

    # slate_date == today_utc from here on.

    # Still BEFORE today's predict cron has had a chance to fire — this
    # is an expected pre-tip firing; valid-skip green.
    if now_hour < args.predict_cron_hour_utc:
        return _valid_skip(
            date,
            mode,
            reason=f"before_predict_cron_now_utc_hour={now_hour}",
        )

    # --no-run-predict modes (after-game past slates, deploy at an
    # arbitrary time) never invoke predict.py themselves; they
    # valid-skip green and let the forward-looking pipeline regenerate
    # the slate's predictions.
    if args.no_run_predict:
        return _valid_skip(date, mode, reason="no_run_predict_mode")

    # We are at/past predict cron and predictions still don't exist:
    # invoke predict.py. Fail loudly if it cannot produce the artifacts.
    _emit(
        "::warning::predictions missing and predict cron should have fired; "
        f"invoking predict.py for slate={date} mode={mode}"
    )
    rc, tail = _run_predict_py(date)
    if rc != 0:
        return _hard_fail(
            "PREDICT_PY_FAILED",
            date,
            mode,
            detail=f"rc={rc} tail={tail!r}",
        )

    still_missing = _missing(date)
    if still_missing:
        return _hard_fail(
            "PREDICT_OUTPUTS_MISSING",
            date,
            mode,
            detail=f"missing={','.join(p.name for p in still_missing)}",
        )

    publish_rc = _run_publish_nba_props_today(date)
    if publish_rc != 0:
        return _hard_fail(
            "PUBLISH_NBA_PROPS_TODAY_FAILED",
            date,
            mode,
            detail=f"publish_rc={publish_rc}",
        )

    verifier_rc = _run_verifier(date)
    if verifier_rc != 0:
        return _hard_fail(
            "PREDICT_OUTPUTS_VERIFIER_FAILED",
            date,
            mode,
            detail=f"verifier_rc={verifier_rc}",
        )

    return _proceed(date, mode)


if __name__ == "__main__":
    sys.exit(main())
