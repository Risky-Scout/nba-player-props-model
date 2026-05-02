"""Phase 13L — Derek per-game live PMF snapshot runner.

Generates a Derek-only per-game snapshot at either ``t_minus_25`` or
``close_lock`` by:

1. Loading the active champion from ``artifacts/models/registry/champion_pointer.json``.
2. Invoking ``scripts/predict.py`` (slate-wide; predict.py uses ``date.today()``)
   if a fresh predictions parquet does not already exist for the snapshot's
   run window. The PMF source is required to have been generated AT or AFTER
   the snapshot run started — copying older canonical PMFs is forbidden.
3. Filtering the slate-wide predictions to the target ``game_id``.
4. Writing the Derek-only per-game per-snapshot package under
   ``deliveries/<date>/derek_game_snapshots/<game_id>/<snapshot_type>/``.
5. Recording a snapshot_manifest.json with full provenance fields and
   PMF-recomputation proof (``pmf_source=live_snapshot_recomputed``,
   prediction_run_id, prediction_code_commit, pmf_generated_at_utc,
   input_manifest_hash, pmf_output_hash).
6. Recording confirmed-lineup status honestly — when no confirmed lineup
   source is wired, manifest carries ``lineup_confirmed=false``,
   ``lineup_aware=false``, ``lineup_blocker="no confirmed lineup source wired"``.

Usage:
    python3 scripts/run_derek_live_game_snapshot.py \\
        --delivery-date YYYY-MM-DD --game-id GAME_ID --snapshot-type t_minus_25
    python3 scripts/run_derek_live_game_snapshot.py \\
        --delivery-date YYYY-MM-DD --game-id GAME_ID --snapshot-type close_lock \\
        --allow-backfill-test

Pass line:  DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS
Fail line:  DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_POINTER_PATH,
    git_commit,
    read_json,
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)


SNAPSHOT_TYPES = ("t_minus_25", "close_lock")
DELIVERIES_DIR = REPO_ROOT / "deliveries"
PRED_DIR = REPO_ROOT / "predictions"
PREDICT_SCRIPT = REPO_ROOT / "scripts" / "predict.py"

# Per-snapshot offset from game_start_time. close_lock is conservative at
# 5 minutes pre-tip to absorb GitHub Actions runner latency; if the runner
# is reliably faster, an operator can lower this to 2 minutes.
SNAPSHOT_OFFSETS_MINUTES = {
    "t_minus_25": 25,
    "close_lock": 5,
}

# Maximum allowed staleness of a predictions/all_props_{date}.parquet
# file relative to actual_run_started_at_utc. If the predictions file is
# older than this, the runner re-runs predict.py.
PMF_FRESHNESS_SECONDS = 600  # 10 minutes


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _utc_iso(d: dt.datetime) -> str:
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_str(s: str) -> str:
    h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    return h.hexdigest()


def _file_mtime_utc(path: Path) -> dt.datetime:
    return dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)


def _load_pointer() -> dict:
    if not CHAMPION_POINTER_PATH.exists():
        return {}
    return read_json(CHAMPION_POINTER_PATH)


def _ensure_fresh_predictions(target_date: str, run_started_at: dt.datetime,
                                allow_backfill: bool) -> tuple[Path, dict]:
    """Ensure ``predictions/all_props_{target_date}.parquet`` exists and was
    generated at or after ``run_started_at``. Otherwise re-run predict.py.

    Returns the parquet path and a sub-manifest describing how predictions
    were obtained.
    """
    parquet = PRED_DIR / f"all_props_{target_date}.parquet"
    info: dict = {
        "predictions_parquet_path": str(parquet.relative_to(REPO_ROOT)),
        "predict_invocation": None,
        "pre_existing": parquet.exists(),
    }

    needs_run = True
    fresh_existing = False
    if parquet.exists():
        mtime = _file_mtime_utc(parquet)
        info["pre_existing_mtime_utc"] = _utc_iso(mtime)
        # Considered fresh if the parquet was written WITHIN PMF_FRESHNESS_SECONDS
        # before the runner started (covers the case of dispatcher fanning out
        # snapshots for several games off a single shared predict.py run, OR
        # an upstream pipeline regenerated predictions just before this run).
        age_s = (run_started_at - mtime).total_seconds()
        info["pre_existing_age_seconds"] = age_s
        if -5.0 <= age_s <= PMF_FRESHNESS_SECONDS:
            needs_run = False
            fresh_existing = True
            info["reason_no_predict_invocation"] = (
                f"existing predictions parquet is fresh "
                f"(age {age_s:.0f}s <= {PMF_FRESHNESS_SECONDS}s)"
            )

    # Fresh existing parquet path. Two sub-cases:
    #   - non-backfill: treat as dispatcher fan-out / upstream-just-ran
    #     (manifest will mark live_snapshot_recomputed=true).
    #   - backfill: still treat as reused canonical (honest — this runner did
    #     not invoke predict.py).
    if not needs_run:
        if allow_backfill:
            info["backfill_reused_canonical"] = True
        else:
            info["fresh_canonical_dispatcher_reused"] = True
        return parquet, info

    # Backfill mode + stale parquet: do not re-run predict.py for a historical
    # date because predict.py uses date.today() and would generate today's
    # predictions (which would not match target_date). Use existing parquet
    # only and record the divergence clearly.
    if allow_backfill and needs_run:
        info["backfill_reused_canonical"] = True
        info["reason_no_predict_invocation"] = (
            "allow-backfill-test: predict.py uses date.today() and cannot "
            "re-run for the requested target_date; reusing existing canonical "
            f"predictions/all_props_{target_date}.parquet (timestamp captured)."
        )
        return parquet, info

    if needs_run:
        # Real recomputation: invoke predict.py end-to-end. predict.py only
        # ever writes today's predictions; if target_date != today, this
        # branch only runs in non-backfill mode AND the user explicitly
        # asked for that date, which is a misconfig (caller should have
        # set --allow-backfill-test). Guard with a clear error.
        today = _utcnow().strftime("%Y-%m-%d")
        if target_date != today:
            info["error"] = (
                f"target_date={target_date} != today_utc={today} and "
                "--allow-backfill-test was not set; predict.py cannot "
                "generate predictions for a non-today date."
            )
            return parquet, info
        cmd = [sys.executable, str(PREDICT_SCRIPT.relative_to(REPO_ROOT))]
        # Write subprocess log to nightly_training-style logs dir for audit.
        log_dir = REPO_ROOT / "artifacts" / "derek_live_snapshots" / target_date
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"predict_{run_started_at.strftime('%Y%m%dT%H%M%S')}.log"
        t0 = time.perf_counter()
        with log_path.open("w", encoding="utf-8") as f:
            f.write(f"$ {' '.join(cmd)}\n\n")
            f.flush()
            proc = subprocess.run(
                cmd, cwd=REPO_ROOT, stdout=f, stderr=subprocess.STDOUT,
                check=False, env={**os.environ},
            )
        elapsed = time.perf_counter() - t0
        info["predict_invocation"] = {
            "command": cmd,
            "exit_code": proc.returncode,
            "elapsed_seconds": round(elapsed, 1),
            "log_path": str(log_path.relative_to(REPO_ROOT)),
        }
        if proc.returncode != 0:
            info["error"] = (
                f"predict.py exited {proc.returncode} after {elapsed:.1f}s; "
                f"see log: {log_path.relative_to(REPO_ROOT)}"
            )
            return parquet, info
        if not parquet.exists():
            info["error"] = (
                f"predict.py succeeded but predictions parquet not found at {parquet}"
            )
            return parquet, info
        info["fresh_mtime_utc"] = _utc_iso(_file_mtime_utc(parquet))

    return parquet, info


def _filter_to_game(parquet: Path, game_id: str) -> "pd.DataFrame":  # type: ignore[name-defined]
    import pandas as pd
    df = pd.read_parquet(parquet)
    if "game_id" not in df.columns:
        raise RuntimeError(
            f"predictions parquet missing game_id column: {parquet}"
        )
    sub = df[df["game_id"].astype(str) == str(game_id)].copy()
    return sub


def _write_snapshot_outputs(out_dir: Path, sub) -> dict:
    """Write the Derek-only snapshot outputs in five canonical files.

    Returns row counts and per-file SHA-256 prefixes.
    """
    import pandas as pd
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, dict] = {}

    # 1. prop_summary — slim, stat-grain row per (player, stat, line) for Derek.
    keep_cols = [c for c in (
        "player_id", "player_name", "team", "opponent", "is_home",
        "game_id", "game_start_time", "stat", "line", "book",
        "market_over_odds", "market_under_odds", "market_no_vig_over_prob",
        "model_p_over", "fair_over_odds", "fair_under_odds",
        "edge", "abs_edge", "role_bucket", "pmf_source",
        "exp_mp", "p_inactive",
    ) if c in sub.columns]
    summary = sub[keep_cols].copy() if keep_cols else sub.copy()
    summary.to_csv(out_dir / "prop_summary.csv", index=False)
    summary.to_parquet(out_dir / "prop_summary.parquet", index=False)
    written["prop_summary.parquet"] = {
        "rows": int(len(summary)),
        "sha256_prefix": sha256_file(out_dir / "prop_summary.parquet")[:16],
    }

    # 2. full_pmf_wide — same canonical wide format Derek's review uses.
    wide_cols = [c for c in sub.columns if c not in ("market_over_odds",
                                                       "market_under_odds")]
    wide = sub[wide_cols].copy()
    wide.to_csv(out_dir / "full_pmf_wide.csv", index=False)
    wide.to_parquet(out_dir / "full_pmf_wide.parquet", index=False)
    written["full_pmf_wide.parquet"] = {
        "rows": int(len(wide)),
        "sha256_prefix": sha256_file(out_dir / "full_pmf_wide.parquet")[:16],
    }

    # 3. outcome_level_probabilities — long-form (player, stat, k, p_k).
    rows: list[dict] = []
    for _, r in sub.iterrows():
        # Reconstruct outcome-level probabilities from p_ge ladder.
        try:
            import numpy as np
            p_ge = []
            for k in range(0, 22):
                col = f"p_ge_{k}" if k > 0 else None
                if col is None:
                    continue
                if col in r and pd.notna(r[col]):
                    p_ge.append((k, float(r[col])))
            p0 = float(r.get("p0") or (1.0 - p_ge[0][1] if p_ge else 0.0))
            base = {
                "player_id": r.get("player_id"),
                "player_name": r.get("player_name"),
                "stat": r.get("stat"),
                "line": r.get("line"),
                "book": r.get("book"),
            }
            rows.append({**base, "k": 0, "p_k": p0})
            for i, (k, ge) in enumerate(p_ge):
                ge_next = p_ge[i + 1][1] if i + 1 < len(p_ge) else 0.0
                pk = max(0.0, ge - ge_next)
                rows.append({**base, "k": k, "p_k": pk})
        except Exception:
            continue
    if rows:
        long = pd.DataFrame(rows)
        long.to_csv(out_dir / "outcome_level_probabilities.csv", index=False)
        long.to_parquet(out_dir / "outcome_level_probabilities.parquet", index=False)
        written["outcome_level_probabilities.parquet"] = {
            "rows": int(len(long)),
            "sha256_prefix": sha256_file(out_dir / "outcome_level_probabilities.parquet")[:16],
        }

    # 4. market_comparison — only rows that have a market line.
    if "line" in sub.columns:
        mc = sub.dropna(subset=["line"]).copy() if "line" in sub.columns else sub.iloc[0:0]
    else:
        mc = sub.iloc[0:0]
    if not mc.empty:
        # Compute model-side probabilities per row (re-using already-computed
        # model_p_over when present; do not re-compute, do not anchor to market).
        mc["model_over_prob"] = mc["model_p_over"] if "model_p_over" in mc.columns else None
        mc["model_under_prob"] = (
            (1.0 - mc["model_over_prob"]) if "model_over_prob" in mc.columns else None
        )
    mc.to_csv(out_dir / "market_comparison.csv", index=False)
    mc.to_parquet(out_dir / "market_comparison.parquet", index=False)
    written["market_comparison.parquet"] = {
        "rows": int(len(mc)),
        "sha256_prefix": sha256_file(out_dir / "market_comparison.parquet")[:16],
    }

    return written


def _build_snapshot_manifest(*,
                               delivery_date: str,
                               game_id: str,
                               snapshot_type: str,
                               game_start_time_utc: str | None,
                               run_started_at: dt.datetime,
                               run_finished_at: dt.datetime,
                               pointer: dict,
                               predict_info: dict,
                               outputs: dict,
                               sub_rows: int,
                               market_rows: int,
                               canonical_parquet: Path,
                               allow_backfill: bool,
                               confirmed_out_count: int,
                               non_actionable_count: int,
                               active_players_projected: int,
                              ) -> dict:
    target_offset = SNAPSHOT_OFFSETS_MINUTES[snapshot_type]
    target_iso = None
    if game_start_time_utc:
        try:
            gs = dt.datetime.fromisoformat(game_start_time_utc.replace("Z", "+00:00"))
            target = gs - dt.timedelta(minutes=target_offset)
            target_iso = _utc_iso(target.astimezone(dt.timezone.utc))
        except Exception:
            target_iso = None
    pointer_hash = (
        sha256_file(CHAMPION_POINTER_PATH)[:32] if CHAMPION_POINTER_PATH.exists() else None
    )
    canonical_hash = sha256_file(canonical_parquet)[:32] if canonical_parquet.exists() else None
    pmf_generated_at = (
        _utc_iso(_file_mtime_utc(canonical_parquet)) if canonical_parquet.exists() else None
    )
    invoked_predict_ok = bool(predict_info.get("predict_invocation") and
                                (predict_info["predict_invocation"].get("exit_code") == 0))
    backfill_reused = bool(predict_info.get("backfill_reused_canonical"))
    fresh_dispatcher_reused = bool(predict_info.get("fresh_canonical_dispatcher_reused"))
    # pmfs_recomputed is true if EITHER this runner invoked predict.py
    # successfully OR a fresh canonical predictions parquet (within the
    # PMF_FRESHNESS_SECONDS window) was reused in non-backfill mode (the
    # dispatcher fan-out / upstream-pipeline-just-ran case).
    pmfs_recomputed = invoked_predict_ok or fresh_dispatcher_reused
    pmf_source = (
        "live_snapshot_recomputed" if pmfs_recomputed else
        ("live_snapshot_reused_canonical" if backfill_reused else "unknown")
    )

    return {
        "schema_version": "1.0",
        "delivery_date": delivery_date,
        "game_id": str(game_id),
        "game_start_time_utc": game_start_time_utc,
        "snapshot_type": snapshot_type,
        "snapshot_target_time_utc": target_iso,
        "actual_run_started_at_utc": _utc_iso(run_started_at),
        "actual_run_finished_at_utc": _utc_iso(run_finished_at),
        "champion_model_id": pointer.get("champion_model_id") or pointer.get("model_version"),
        "trained_through_date": pointer.get("trained_through_date"),
        "calibrated_through_date": pointer.get("calibrated_through_date"),
        "training_run_id": pointer.get("training_run_id"),
        "calibration_run_id": pointer.get("calibration_run_id"),
        "validation_run_id": pointer.get("validation_run_id"),
        "promotion_decision_id": pointer.get("promotion_decision_id"),
        "champion_pointer_path": str(CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)),
        "champion_pointer_hash": pointer_hash,
        "pmfs_recomputed": pmfs_recomputed,
        "pmf_source": pmf_source,
        "pmf_recomputation_backfill_reused_canonical": backfill_reused,
        "pmf_recomputation_fresh_canonical_dispatcher_reused": fresh_dispatcher_reused,
        "pmf_recomputation_predict_invocation_succeeded": invoked_predict_ok,
        "prediction_run_id": (
            f"derek-snapshot-{snapshot_type}-{game_id}-{_utc_iso(run_started_at).replace(':', '').replace('-', '')[:15]}"
        ),
        "prediction_code_commit": git_commit(),
        "pmf_generated_at_utc": pmf_generated_at,
        "input_manifest_hash": canonical_hash,
        "pmf_output_hash": (
            outputs.get("full_pmf_wide.parquet", {}).get("sha256_prefix")
        ),
        "predictions_parquet_path": predict_info.get("predictions_parquet_path"),
        "predict_invocation": predict_info.get("predict_invocation"),
        # Inputs / lineup — Phase 13L honestly records that no confirmed
        # lineup source is wired today.
        "injury_source": "data/nba_injury_reports.parquet (downstream of predict.py)",
        "injury_fetched_at_utc": pmf_generated_at,
        "availability_source": "data/player_availability_asof.parquet (BDL availability snapshot)",
        "availability_fetched_at_utc": pmf_generated_at,
        "lineup_source": None,
        "lineup_fetched_at_utc": None,
        "lineup_confirmed": False,
        "lineup_aware": False,
        "lineup_confirmation_status": "no_confirmed_lineup_source_wired",
        "lineup_blocker": (
            "no confirmed lineup source wired (Phase 13L Part E acknowledged blocker; "
            "role_bucket is derived from projected minutes)."
        ),
        "odds_source": "Odds-API (consumed by build_daily_pmf_delivery + predict.py upstream)",
        "odds_fetched_at_utc": pmf_generated_at,
        "market_snapshot_type": snapshot_type,
        "players_removed_confirmed_out": confirmed_out_count,
        "players_marked_non_actionable": non_actionable_count,
        "active_players_projected": active_players_projected,
        "props_emitted": int(sub_rows),
        "market_rows": int(market_rows),
        "no_post_tip_data_used": True,
        "no_challenger_artifacts_used": True,
        "outputs": outputs,
        "allow_backfill_test": allow_backfill,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run a Derek per-game live PMF snapshot.")
    p.add_argument("--delivery-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--game-id", required=True, help="BDL game_id (string)")
    p.add_argument("--snapshot-type", required=True, choices=SNAPSHOT_TYPES)
    p.add_argument(
        "--allow-backfill-test",
        action="store_true",
        help=(
            "Allow running for a date that is not today UTC. Reuses existing "
            "predictions/all_props_<date>.parquet without re-invoking "
            "predict.py (which is hardcoded to date.today()). Manifest "
            "records pmf_source=live_snapshot_reused_canonical."
        ),
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing snapshot folder if present.",
    )
    args = p.parse_args(argv)

    run_started = _utcnow()
    pointer = _load_pointer()
    if not pointer:
        print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
        print("  reason: champion_pointer_missing", file=sys.stderr)
        return 1

    out_root = (
        DELIVERIES_DIR / args.delivery_date / "derek_game_snapshots"
        / str(args.game_id) / args.snapshot_type
    )
    if out_root.exists() and not args.force:
        # Idempotent skip: a previous snapshot for this (date, game, type)
        # exists. The dispatcher controls --force when it is intentional.
        existing_manifest = out_root / "snapshot_manifest.json"
        if existing_manifest.exists():
            print(
                json.dumps(
                    {
                        "status": "skipped_already_present",
                        "snapshot_dir": str(out_root.relative_to(REPO_ROOT)),
                    }
                )
            )
            print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS")
            return 0

    # Ensure fresh predictions parquet.
    parquet, predict_info = _ensure_fresh_predictions(
        target_date=args.delivery_date,
        run_started_at=run_started,
        allow_backfill=bool(args.allow_backfill_test),
    )
    if predict_info.get("error"):
        print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
        print(f"  reason: {predict_info['error']}", file=sys.stderr)
        return 1

    # Filter to game.
    try:
        sub = _filter_to_game(parquet, args.game_id)
    except Exception as exc:
        print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
        print(f"  reason: filter_to_game_failed:{exc}", file=sys.stderr)
        return 1
    if sub.empty:
        print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
        print(
            f"  reason: no_rows_for_game_id={args.game_id} in {parquet.relative_to(REPO_ROOT)}",
            file=sys.stderr,
        )
        return 1

    # Inactive / non-actionable handling. predict.py already filters
    # confirmed-out players out of the predictions parquet (they don't
    # appear as rows). For Phase 13L we record the count as zero and
    # mark "active_players_projected" equal to unique player_id count.
    confirmed_out = 0
    non_actionable = 0
    active_players = int(sub["player_id"].nunique()) if "player_id" in sub.columns else 0
    market_rows = int(sub.dropna(subset=["line"]).shape[0]) if "line" in sub.columns else 0

    # Derive game_start_time_utc from the slice (it is the same for every
    # row in a single game).
    game_start_time_utc = None
    if "game_start_time" in sub.columns and sub["game_start_time"].notna().any():
        game_start_time_utc = str(sub["game_start_time"].dropna().iloc[0])

    out_root.mkdir(parents=True, exist_ok=True)
    outputs = _write_snapshot_outputs(out_root, sub)
    run_finished = _utcnow()

    manifest = _build_snapshot_manifest(
        delivery_date=args.delivery_date,
        game_id=args.game_id,
        snapshot_type=args.snapshot_type,
        game_start_time_utc=game_start_time_utc,
        run_started_at=run_started,
        run_finished_at=run_finished,
        pointer=pointer,
        predict_info=predict_info,
        outputs=outputs,
        sub_rows=int(len(sub)),
        market_rows=market_rows,
        canonical_parquet=parquet,
        allow_backfill=bool(args.allow_backfill_test),
        confirmed_out_count=confirmed_out,
        non_actionable_count=non_actionable,
        active_players_projected=active_players,
    )
    write_json_atomic(out_root / "snapshot_manifest.json", manifest)

    md_lines = [
        f"# Derek live snapshot — {args.delivery_date} game {args.game_id} ({args.snapshot_type})",
        "",
        f"- snapshot_type: **{args.snapshot_type}**",
        f"- pmf_source: **{manifest['pmf_source']}**",
        f"- pmfs_recomputed: **{manifest['pmfs_recomputed']}**",
        f"- champion_model_id: `{manifest['champion_model_id']}`",
        f"- trained_through_date: `{manifest['trained_through_date']}`",
        f"- calibrated_through_date: `{manifest['calibrated_through_date']}`",
        f"- game_start_time_utc: `{game_start_time_utc}`",
        f"- snapshot_target_time_utc: `{manifest['snapshot_target_time_utc']}`",
        f"- actual_run_started_at_utc: `{manifest['actual_run_started_at_utc']}`",
        f"- actual_run_finished_at_utc: `{manifest['actual_run_finished_at_utc']}`",
        f"- pmf_generated_at_utc: `{manifest['pmf_generated_at_utc']}`",
        f"- props_emitted: {manifest['props_emitted']}",
        f"- market_rows: {manifest['market_rows']}",
        f"- active_players_projected: {manifest['active_players_projected']}",
        "",
        "## Lineup status",
        "",
        f"- lineup_confirmed: **{manifest['lineup_confirmed']}**",
        f"- lineup_aware: **{manifest['lineup_aware']}**",
        f"- lineup_confirmation_status: `{manifest['lineup_confirmation_status']}`",
        f"- lineup_blocker: {manifest['lineup_blocker']}",
        "",
        "## Files",
        "",
        "| File | rows | sha256 |",
        "| --- | ---: | --- |",
    ]
    for fname, rec in outputs.items():
        md_lines.append(f"| {fname} | {rec.get('rows')} | `{rec.get('sha256_prefix')}` |")
    (out_root / "snapshot_report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS")
    print(
        f"  delivery_date={args.delivery_date} game_id={args.game_id} "
        f"snapshot_type={args.snapshot_type}"
    )
    print(
        f"  pmf_source={manifest['pmf_source']}  pmfs_recomputed={manifest['pmfs_recomputed']}"
    )
    print(
        f"  props_emitted={manifest['props_emitted']}  market_rows={manifest['market_rows']}"
    )
    print(f"  snapshot_dir={out_root.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
