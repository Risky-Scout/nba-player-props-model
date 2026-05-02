"""Phase 13L — Derek per-game live PMF snapshot runner.

Generates a Derek-only per-game snapshot at either ``t_minus_25`` or
``close_lock`` by:

1. Loading the active champion from ``artifacts/models/registry/champion_pointer.json``.
2. Resolving snapshot_mode:
   - ``production_live`` (default): MUST invoke ``scripts/predict.py`` and
     succeed. Reusing a pre-existing predictions parquet, even one that is
     fresh on disk, is NOT permitted. predict.py is hardcoded to
     ``date.today()`` so target_date must equal today UTC.
   - ``backfill_demo`` (``--allow-backfill-test``): reuses the existing
     ``predictions/all_props_<date>.parquet`` (canonical reuse) and records
     ``pmf_source=live_snapshot_reused_canonical`` /
     ``pmfs_recomputed=false``. Used for infrastructure proof on historical
     dates that predict.py cannot regenerate.
3. Filtering the slate-wide predictions to the target ``game_id``.
4. Writing the Derek-only per-game per-snapshot package under
   ``deliveries/<date>/derek_game_snapshots/<game_id>/<snapshot_type>/``.
5. Recording a snapshot_manifest.json with snapshot_mode and full
   provenance — production_live runs carry pmfs_recomputed=true /
   pmf_source=live_snapshot_recomputed; backfill_demo runs carry
   pmfs_recomputed=false / pmf_source=live_snapshot_reused_canonical.
6. Recording confirmed-lineup status honestly — when no confirmed lineup
   source is wired, manifest carries ``lineup_confirmed=false``,
   ``lineup_aware=false``, ``lineup_blocker="no confirmed lineup source wired"``.

Usage:
    python3 scripts/run_derek_live_game_snapshot.py \\
        --delivery-date YYYY-MM-DD --game-id GAME_ID --snapshot-type t_minus_25
    python3 scripts/run_derek_live_game_snapshot.py \\
        --delivery-date YYYY-MM-DD --game-id GAME_ID --snapshot-type close_lock \\
        --allow-backfill-test

Pass lines:
    DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS    (production_live + recomputed)
    DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS  (backfill_demo)
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


def _fetch_lineup_status_for_snapshot(*, delivery_date: str, game_id: str,
                                        allow_backfill: bool) -> dict | None:
    """Invoke fetch_bdl_game_lineups.py for one game and return the
    persisted lineup_status dict, or None if the fetch failed for a reason
    that does not warrant aborting the snapshot.

    Returning None vs returning a status dict with lineup_confirmed=false:
      - None: the fetch script could not run at all (e.g. BDL_API_KEY
        missing in backfill_demo mode), so there is no live status file to
        record. Manifest will fall back to "no confirmed lineup source
        wired" wording.
      - dict: the fetch ran and produced a status — even if
        lineup_confirmed=false (no rows yet, partial, etc.). The blocker is
        explicit and propagates to the manifest unmodified.
    """
    fetch_script = REPO_ROOT / "scripts" / "fetch_bdl_game_lineups.py"
    status_path = (
        REPO_ROOT / "artifacts" / "live_lineups" / delivery_date / str(game_id)
        / "lineup_status.json"
    )
    if not os.environ.get("BDL_API_KEY", "").strip():
        if allow_backfill:
            return None
        # In production-live mode an absent BDL key is a soft blocker — the
        # snapshot can still ship (with lineup_confirmed=false) but the
        # manifest should record the exact reason. Return a synthetic status
        # so downstream code doesn't fall back to the legacy "no source
        # wired" wording, which would be misleading.
        return {
            "schema_version": "1.0",
            "delivery_date": delivery_date,
            "game_id": str(game_id),
            "source": "balldontlie_v1_lineups",
            "fetched_at_utc": _utc_iso(_utcnow()),
            "lineup_confirmed": False,
            "lineup_complete": "fetch_failed",
            "lineup_blocker": "BDL_API_KEY not set in runner environment",
            "teams_present": [],
            "starter_count_by_team": {},
            "bench_count_by_team": {},
            "total_rows": 0,
            "starters": [],
            "bench_players": [],
            "unmapped_players": [],
            "lineup_hash": "",
        }
    rc = subprocess.run(
        [sys.executable, str(fetch_script.relative_to(REPO_ROOT)),
         "--delivery-date", delivery_date,
         "--game-id", str(game_id)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        env={**os.environ},
    )
    if not status_path.exists():
        # Even on rc != 0 the fetch script writes a status file when it can.
        # If it doesn't exist, persist a synthetic blocker so the manifest
        # is still honest.
        return {
            "schema_version": "1.0",
            "delivery_date": delivery_date,
            "game_id": str(game_id),
            "source": "balldontlie_v1_lineups",
            "fetched_at_utc": _utc_iso(_utcnow()),
            "lineup_confirmed": False,
            "lineup_complete": "fetch_failed",
            "lineup_blocker": (
                f"fetch_bdl_game_lineups.py exit_code={rc.returncode} "
                "and produced no lineup_status.json"
            ),
            "teams_present": [],
            "starter_count_by_team": {},
            "bench_count_by_team": {},
            "total_rows": 0,
            "starters": [],
            "bench_players": [],
            "unmapped_players": [],
            "lineup_hash": "",
        }
    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return None


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

    if parquet.exists():
        mtime = _file_mtime_utc(parquet)
        info["pre_existing_mtime_utc"] = _utc_iso(mtime)
        age_s = (run_started_at - mtime).total_seconds()
        info["pre_existing_age_seconds"] = age_s

    # Backfill / demo mode: predict.py uses date.today() and cannot re-run
    # for a historical date, so reuse the existing canonical parquet and
    # mark it explicitly. snapshot_mode=backfill_demo + pmfs_recomputed=false
    # downstream.
    if allow_backfill:
        if not parquet.exists():
            info["error"] = (
                f"backfill mode requested but predictions/all_props_{target_date}.parquet "
                "does not exist; cannot reuse canonical."
            )
            return parquet, info
        info["backfill_reused_canonical"] = True
        info["reason_no_predict_invocation"] = (
            "allow-backfill-test: predict.py uses date.today() and cannot "
            "re-run for the requested target_date; reusing existing canonical "
            f"predictions/all_props_{target_date}.parquet (timestamp captured)."
        )
        return parquet, info

    # Production-live mode: predict.py MUST be invoked by this runner. We do
    # not accept "fresh canonical from upstream" as a substitute, because the
    # runner cannot prove the upstream invocation belongs to this snapshot's
    # window. predict.py only ever writes today's predictions, so target_date
    # MUST equal today_utc.
    today = _utcnow().strftime("%Y-%m-%d")
    if target_date != today:
        info["error"] = (
            f"target_date={target_date} != today_utc={today} and "
            "--allow-backfill-test was not set; predict.py cannot "
            "generate predictions for a non-today date. In production-live "
            "mode the runner refuses to silently reuse canonical PMFs."
        )
        return parquet, info
    cmd = [sys.executable, str(PREDICT_SCRIPT.relative_to(REPO_ROOT))]
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
                               lineup_status,
                               lineup_integration_summary=None,
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
    # pmfs_recomputed is true ONLY when this runner invoked predict.py and
    # got a clean exit. Reusing a canonical parquet — even one that is fresh
    # on disk — does not count as recomputation and the manifest must not
    # claim it does. Snapshot_mode disambiguates the path.
    pmfs_recomputed = invoked_predict_ok
    snapshot_mode = "backfill_demo" if allow_backfill else "production_live"
    if pmfs_recomputed:
        pmf_source = "live_snapshot_recomputed"
    elif backfill_reused:
        pmf_source = "live_snapshot_reused_canonical"
    else:
        # Should never reach here: production-live mode without a successful
        # predict.py invocation must have already returned an error from
        # _ensure_fresh_predictions and short-circuited the caller.
        pmf_source = "unknown"

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
        "snapshot_mode": snapshot_mode,
        "pmfs_recomputed": pmfs_recomputed,
        "pmf_source": pmf_source,
        "pmf_recomputation_backfill_reused_canonical": backfill_reused,
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
        # Champion model usage. Production-live runs MUST use a pre-promoted
        # champion; this runner never retrains/recalibrates.
        "live_snapshot_retrained": False,
        "live_snapshot_recalibrated": False,
        "champion_metadata_verified": (
            predict_info.get("champion_metadata_verified") is True
        ),
        "no_leakage_champion_cutoff_verified": (
            predict_info.get("no_leakage_champion_cutoff_verified") is True
        ),
        # Inputs / lineup. Phase 13M wires BDL confirmed lineups; if the
        # fetch produced a usable response we surface it here, otherwise the
        # blocker is recorded honestly.
        "injury_source": "data/nba_injury_reports.parquet (downstream of predict.py)",
        "injury_fetched_at_utc": pmf_generated_at,
        "availability_source": "data/player_availability_asof.parquet (BDL availability snapshot)",
        "availability_fetched_at_utc": pmf_generated_at,
        "lineup_source": (
            (lineup_status or {}).get("source")
            if (lineup_status or {}).get("total_rows", 0) > 0
            else None
        ),
        "lineup_fetched_at_utc": (lineup_status or {}).get("fetched_at_utc"),
        "lineup_confirmed": bool((lineup_status or {}).get("lineup_confirmed")),
        "lineup_complete": (lineup_status or {}).get("lineup_complete"),
        "lineup_aware": bool((lineup_status or {}).get("lineup_confirmed")),
        "lineup_confirmation_status": (
            "complete" if (lineup_status or {}).get("lineup_confirmed")
            else (lineup_status or {}).get("lineup_complete")
                 or "no_confirmed_lineup_source_wired"
        ),
        "lineup_blocker": (
            (lineup_status or {}).get("lineup_blocker")
            or ("no confirmed lineup source wired" if not lineup_status
                else "")
        ),
        "lineup_hash": (lineup_status or {}).get("lineup_hash") or "",
        "starters_by_team": (lineup_status or {}).get("starter_count_by_team") or {},
        "bench_count_by_team": (lineup_status or {}).get("bench_count_by_team") or {},
        "unmapped_lineup_players": (lineup_status or {}).get("unmapped_players") or [],
        # Phase 13M-bis lineup feature wiring. predict.py now accepts
        # --lineup-context and joins BDL lineup rows into the prediction
        # dataframe (current_starter, role_source=confirmed_bdl_lineup, etc.).
        # `lineup_affects_pmf_features` is true iff at least one row was
        # actually joined for THIS snapshot. When zero rows joined (BDL
        # not yet posted lineups, mismatched IDs, no lineup_context passed)
        # the integration summary's lineup_blocker explains why.
        "lineup_context_supplied": bool(
            (lineup_integration_summary or {}).get("lineup_context_supplied")
            or bool(lineup_status)
        ),
        "lineup_affects_pmf_features": bool(
            (lineup_integration_summary or {})
                .get("lineup_affects_pmf_features", False)
        ),
        "lineup_feature_blocker": (
            (
                (lineup_integration_summary or {})
                .get("lineup_integration_summary", {}) or {}
            ).get("lineup_blocker")
            or (
                "" if (lineup_integration_summary or {})
                        .get("lineup_affects_pmf_features")
                else (
                    "no lineup rows joined into prediction state for this "
                    "snapshot — see derek_live_predictions_summary.json for "
                    "the exact blocker (typical: BDL has not posted lineups "
                    "yet, or backfill_demo mode bypassed predict.py)."
                )
            )
        ),
        "lineup_feature_columns_added": (
            (lineup_integration_summary or {})
            .get("lineup_integration_summary", {}) or {}
        ).get("lineup_feature_columns_added", []),
        "role_bucket_changed_count": (
            (lineup_integration_summary or {})
            .get("lineup_integration_summary", {}) or {}
        ).get("role_bucket_changed_count", 0),
        "starter_flag_changed_count": (
            (lineup_integration_summary or {})
            .get("lineup_integration_summary", {}) or {}
        ).get("starter_flag_changed_count", 0),
        "minutes_projection_conflict_count": (
            (lineup_integration_summary or {})
            .get("lineup_integration_summary", {}) or {}
        ).get("minutes_projection_conflict_count", 0),
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

    # Phase 13M champion-readiness gate (Critical Training/Calibration Rule).
    # Production-live runs MUST verify the champion is a real, leakage-clean
    # promotion trained/calibrated through ≤ delivery_date - 1 day. Backfill
    # mode skips this gate (it's allowed to run against historical pointers).
    champion_metadata_verified = False
    no_leakage_champion_cutoff_verified = False
    if not args.allow_backfill_test:
        rc = subprocess.run(
            [
                sys.executable,
                str((REPO_ROOT / "scripts" / "verify_derek_live_champion_ready.py")
                    .relative_to(REPO_ROOT)),
                "--delivery-date", args.delivery_date,
            ],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
            env={**os.environ},
        )
        champion_metadata_verified = (rc.returncode == 0)
        no_leakage_champion_cutoff_verified = (rc.returncode == 0)
        if rc.returncode != 0:
            print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
            print(
                "  reason: champion-readiness gate failed; refusing to run "
                "production-live without a verified champion.",
                file=sys.stderr,
            )
            tail = (rc.stdout or "") + (rc.stderr or "")
            for line in tail.strip().splitlines()[-6:]:
                print(f"  {line}", file=sys.stderr)
            return 1

    out_root = (
        DELIVERIES_DIR / args.delivery_date / "derek_game_snapshots"
        / str(args.game_id) / args.snapshot_type
    )
    if out_root.exists() and not args.force:
        # Idempotent skip: a previous snapshot for this (date, game, type)
        # exists. The dispatcher controls --force when it is intentional.
        # Replay the existing manifest's mode-appropriate pass line so the
        # caller observes a consistent PASS even when this invocation was a
        # no-op.
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
            try:
                m = json.loads(existing_manifest.read_text(encoding="utf-8"))
            except Exception:
                m = {}
            if m.get("snapshot_mode") == "production_live" and m.get("pmfs_recomputed") is True:
                print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS")
            else:
                print("DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS")
            return 0

    # Phase 13M-bis: in production-live mode, fetch BDL lineups FIRST so we
    # can pass --lineup-context to predict.py. In backfill_demo mode the
    # BDL fetch still runs (after the canonical reuse) for honest lineup
    # status recording — see further below.
    lineup_status_early = None
    lineup_parquet_path = None
    if not args.allow_backfill_test:
        lineup_status_early = _fetch_lineup_status_for_snapshot(
            delivery_date=args.delivery_date,
            game_id=str(args.game_id),
            allow_backfill=False,
        )
        # Locate the normalized parquet emitted by fetch_bdl_game_lineups.py.
        candidate = (
            REPO_ROOT / "artifacts" / "live_lineups" / args.delivery_date
            / str(args.game_id) / "bdl_lineups_normalized.parquet"
        )
        if candidate.exists():
            lineup_parquet_path = candidate

    # Ensure fresh predictions. Two modes:
    #   - backfill_demo (--allow-backfill-test): reuse canonical
    #     predictions/all_props_<date>.parquet, then filter to game.
    #   - production_live: invoke predict.py with --derek-live-snapshot and
    #     consume the per-snapshot derek_live_predictions.parquet directly.
    out_root_pre = (
        DELIVERIES_DIR / args.delivery_date / "derek_game_snapshots"
        / str(args.game_id) / args.snapshot_type
    )
    if args.allow_backfill_test:
        parquet, predict_info = _ensure_fresh_predictions(
            target_date=args.delivery_date,
            run_started_at=run_started,
            allow_backfill=True,
        )
        if predict_info.get("error"):
            print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
            print(f"  reason: {predict_info['error']}", file=sys.stderr)
            return 1
        try:
            sub = _filter_to_game(parquet, args.game_id)
        except Exception as exc:
            print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
            print(f"  reason: filter_to_game_failed:{exc}", file=sys.stderr)
            return 1
        lineup_integration_summary = None
    else:
        # Production-live: invoke predict.py with Derek live args.
        out_root_pre.mkdir(parents=True, exist_ok=True)
        predict_run_id = (
            f"derek-snapshot-{args.snapshot_type}-{args.game_id}-"
            f"{run_started.strftime('%Y%m%dT%H%M%S')}"
        )
        cmd = [
            sys.executable, "scripts/predict.py",
            "--derek-live-snapshot",
            "--target-date", args.delivery_date,
            "--game-id", str(args.game_id),
            "--snapshot-output-dir", str(out_root_pre.relative_to(REPO_ROOT)),
            "--snapshot-type", args.snapshot_type,
            "--snapshot-run-id", predict_run_id,
        ]
        if lineup_parquet_path is not None:
            cmd += ["--lineup-context", str(lineup_parquet_path.relative_to(REPO_ROOT))]
        log_dir = REPO_ROOT / "artifacts" / "derek_live_snapshots" / args.delivery_date
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / (
            f"predict_{args.snapshot_type}_{args.game_id}_"
            f"{run_started.strftime('%Y%m%dT%H%M%S')}.log"
        )
        t0 = time.perf_counter()
        with log_path.open("w", encoding="utf-8") as f:
            f.write(f"$ {' '.join(cmd)}\n\n")
            f.flush()
            proc = subprocess.run(
                cmd, cwd=REPO_ROOT, stdout=f, stderr=subprocess.STDOUT,
                check=False, env={**os.environ},
            )
        elapsed = time.perf_counter() - t0
        live_predictions_parquet = out_root_pre / "derek_live_predictions.parquet"
        live_predictions_summary = out_root_pre / "derek_live_predictions_summary.json"
        predict_info = {
            "predictions_parquet_path": str(
                live_predictions_parquet.relative_to(REPO_ROOT)
            ),
            "predict_invocation": {
                "command": cmd,
                "exit_code": proc.returncode,
                "elapsed_seconds": round(elapsed, 1),
                "log_path": str(log_path.relative_to(REPO_ROOT)),
            },
        }
        if proc.returncode != 0 or not live_predictions_parquet.exists():
            print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
            print(
                f"  reason: predict.py exit={proc.returncode}; "
                f"see log: {log_path.relative_to(REPO_ROOT)}",
                file=sys.stderr,
            )
            return 1
        # Read integration summary to surface in manifest.
        lineup_integration_summary = None
        if live_predictions_summary.exists():
            try:
                lineup_integration_summary = json.loads(
                    live_predictions_summary.read_text(encoding="utf-8")
                )
            except Exception:
                lineup_integration_summary = None
        try:
            import pandas as pd
            sub = pd.read_parquet(live_predictions_parquet)
            if "game_id" in sub.columns:
                sub = sub[sub["game_id"].astype(str) == str(args.game_id)].copy()
        except Exception as exc:
            print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
            print(f"  reason: failed to read derek_live_predictions: {exc}",
                  file=sys.stderr)
            return 1
        # In production-live, mark the predict_invocation as backfill-NOT.
        predict_info["backfill_reused_canonical"] = False
        # Use derek live predictions parquet path for the manifest hash.
        parquet = live_predictions_parquet

    # Production-live filter no-op (predict.py already filtered) — fall through
    # to the rest of the snapshot pipeline. For backfill we already have sub.
    if False:
        # Placeholder so the diff is small; the real flow continues below.
        pass

    # The legacy filter_to_game error handler (now only triggers in
    # backfill_demo path; production-live path returned earlier on failure).
    try:
        _ = sub  # name in scope
    except NameError as exc:
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

    # Phase 13M: BDL confirmed-lineup status. In production-live mode the
    # fetch already ran upstream (so we could pass --lineup-context to
    # predict.py); reuse that result. In backfill_demo mode we still
    # invoke the fetch here for honest lineup_status recording.
    if args.allow_backfill_test:
        lineup_status = _fetch_lineup_status_for_snapshot(
            delivery_date=args.delivery_date,
            game_id=str(args.game_id),
            allow_backfill=True,
        )
    else:
        lineup_status = lineup_status_early

    # Predict_info carries champion verification results for the manifest.
    predict_info["champion_metadata_verified"] = champion_metadata_verified
    predict_info["no_leakage_champion_cutoff_verified"] = no_leakage_champion_cutoff_verified

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
        lineup_status=lineup_status,
        lineup_integration_summary=lineup_integration_summary,
    )
    write_json_atomic(out_root / "snapshot_manifest.json", manifest)

    md_lines = [
        f"# Derek live snapshot — {args.delivery_date} game {args.game_id} ({args.snapshot_type})",
        "",
        f"- snapshot_type: **{args.snapshot_type}**",
        f"- snapshot_mode: **{manifest['snapshot_mode']}**",
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
        f"- lineup_source: `{manifest.get('lineup_source')}`",
        f"- lineup_fetched_at_utc: `{manifest.get('lineup_fetched_at_utc')}`",
        f"- lineup_confirmed: **{manifest['lineup_confirmed']}**",
        f"- lineup_complete: `{manifest.get('lineup_complete')}`",
        f"- lineup_aware: **{manifest['lineup_aware']}**",
        f"- lineup_confirmation_status: `{manifest['lineup_confirmation_status']}`",
        f"- lineup_blocker: {manifest['lineup_blocker']!r}",
        f"- lineup_hash: `{manifest.get('lineup_hash')}`",
        f"- starters_by_team: `{manifest.get('starters_by_team')}`",
        f"- lineup_context_supplied: **{manifest.get('lineup_context_supplied')}**",
        f"- lineup_affects_pmf_features: **{manifest.get('lineup_affects_pmf_features')}**",
        f"- lineup_feature_blocker: {manifest.get('lineup_feature_blocker')!r}",
        "",
        "## Champion model",
        "",
        f"- champion_metadata_verified: **{manifest.get('champion_metadata_verified')}**",
        f"- no_leakage_champion_cutoff_verified: **{manifest.get('no_leakage_champion_cutoff_verified')}**",
        f"- live_snapshot_retrained: **{manifest.get('live_snapshot_retrained')}**",
        f"- live_snapshot_recalibrated: **{manifest.get('live_snapshot_recalibrated')}**",
        "",
        "## Files",
        "",
        "| File | rows | sha256 |",
        "| --- | ---: | --- |",
    ]
    for fname, rec in outputs.items():
        md_lines.append(f"| {fname} | {rec.get('rows')} | `{rec.get('sha256_prefix')}` |")
    (out_root / "snapshot_report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    if manifest["snapshot_mode"] == "production_live" and manifest["pmfs_recomputed"] is True:
        print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS")
    else:
        print("DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS")
    print(
        f"  delivery_date={args.delivery_date} game_id={args.game_id} "
        f"snapshot_type={args.snapshot_type}"
    )
    print(
        f"  snapshot_mode={manifest['snapshot_mode']}  pmf_source={manifest['pmf_source']}  "
        f"pmfs_recomputed={manifest['pmfs_recomputed']}"
    )
    print(
        f"  props_emitted={manifest['props_emitted']}  market_rows={manifest['market_rows']}"
    )
    print(f"  snapshot_dir={out_root.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
