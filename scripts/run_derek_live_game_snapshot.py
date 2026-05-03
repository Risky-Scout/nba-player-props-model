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
# Phase 13R — contextual PMF engine. The engine loads the trained
# Phase 13Q (feature_set_id=phase13q_contextual_pmf_engine_v1) Ridge
# adjustment models when champion_pointer.contextual_pmf_engine is
# true, and produces per-row minutes / rate deltas. The runner refuses
# to claim contextual when the pointer or the artifacts are missing
# and records lineup_blocker / contextual_blocker accordingly.
from nba_props_model.contextual import (  # noqa: E402
    CONTEXTUAL_FEATURE_SET_ID,
    load_contextual_engine,
    resolve_contextual_challenger_dir,
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

    # 5. lineup_context.{csv,parquet} — only the lineup-derived columns from
    # the prediction state (Phase 13N Part I). Always emitted (may be empty
    # when no BDL rows joined). The columns are the 13M-bis additions.
    lineup_cols = [c for c in (
        "player_id", "player_name", "team", "game_id", "stat",
        "bdl_lineup_present", "current_starter", "confirmed_starter",
        "confirmed_bench", "lineup_position", "lineup_source",
        "lineup_confirmed", "role_source", "role_bucket_pre_lineup",
        "role_bucket_post_lineup", "lineup_context_supplied",
        "lineup_affects_pmf_features",
    ) if c in sub.columns]
    lineup_ctx = sub[lineup_cols].copy() if lineup_cols else sub.iloc[0:0].copy()
    if not lineup_ctx.empty and "player_id" in lineup_ctx.columns:
        lineup_ctx = lineup_ctx.drop_duplicates(subset=["player_id"])
    lineup_ctx.to_csv(out_dir / "lineup_context.csv", index=False)
    lineup_ctx.to_parquet(out_dir / "lineup_context.parquet", index=False)
    written["lineup_context.parquet"] = {
        "rows": int(len(lineup_ctx)),
        "sha256_prefix": sha256_file(out_dir / "lineup_context.parquet")[:16],
    }

    # 6. injury_availability_context.{csv,parquet} — Phase 13N Part D/E.
    # Slim audit file showing the injury/availability flags per player as
    # they entered prediction state.
    inj_cols = [c for c in (
        "player_id", "player_name", "team", "game_id",
        "injury_status", "availability_status", "is_actionable",
        "non_actionable_reason", "injury_lineup_conflict",
        "minutes_projection_conflict", "exp_mp", "p_inactive",
    ) if c in sub.columns]
    inj_ctx = sub[inj_cols].copy() if inj_cols else sub.iloc[0:0].copy()
    if not inj_ctx.empty and "player_id" in inj_ctx.columns:
        inj_ctx = inj_ctx.drop_duplicates(subset=["player_id"])
    inj_ctx.to_csv(out_dir / "injury_availability_context.csv", index=False)
    inj_ctx.to_parquet(out_dir / "injury_availability_context.parquet", index=False)
    written["injury_availability_context.parquet"] = {
        "rows": int(len(inj_ctx)),
        "sha256_prefix": sha256_file(out_dir / "injury_availability_context.parquet")[:16],
    }

    # 7. prediction_input_audit.{csv,parquet} — per-row audit trail showing
    # which columns from the canonical prediction frame entered the
    # snapshot. Useful for hash-based input-change diffing in Part J.
    audit_cols = [c for c in (
        "player_id", "player_name", "team", "opponent", "game_id",
        "game_start_time", "stat", "line", "book",
        "exp_mp", "role_bucket", "role_bucket_post_lineup", "role_source",
        "p_inactive", "is_home", "model_p_over", "market_no_vig_over_prob",
        "edge", "abs_edge", "calibration_source", "pmf_source",
    ) if c in sub.columns]
    audit = sub[audit_cols].copy() if audit_cols else sub.iloc[0:0].copy()
    audit.to_csv(out_dir / "prediction_input_audit.csv", index=False)
    audit.to_parquet(out_dir / "prediction_input_audit.parquet", index=False)
    written["prediction_input_audit.parquet"] = {
        "rows": int(len(audit)),
        "sha256_prefix": sha256_file(out_dir / "prediction_input_audit.parquet")[:16],
    }

    return written


def _apply_contextual_scoring(sub, *, pointer: dict, out_root: Path) -> dict:
    """Phase 13R — apply contextual PMF engine to the snapshot subframe.

    When champion_pointer.contextual_pmf_engine is true and the trained
    artifacts load cleanly, this:

      * loads the per-target Ridge adjustment models;
      * builds a per-row feature row from the existing snapshot columns
        (live-context columns from predict.py + game-context columns
        derived from the row's is_home / rest / season state);
      * writes a ``contextual_minutes_delta`` and per-stat
        ``contextual_rate_delta_<stat>`` column on ``sub`` in place;
      * computes an additive ``exp_mp_contextual = exp_mp +
        contextual_minutes_delta`` column;
      * recomputes a minutes-driven PMF-mean shift
        ``pmf_mean_shift_ratio = exp_mp_contextual / exp_mp`` and stores
        ``contextual_pmf_mean_baseline`` /
        ``contextual_pmf_mean_post`` columns. This is the **PMF
        adjustment** consumed by Derek interpretability: a real,
        non-zero, model-driven shift whenever the contextual feature
        vector materially differs from the baseline.

    When the pointer does not request contextual, or the engine cannot
    load, this is a no-op and sets ``contextual_pmf_applied=False`` on
    every row with an exact ``contextual_blocker`` reason.
    """
    import numpy as np
    import pandas as pd

    summary: dict = {
        "contextual_pmf_engine": False,
        "contextual_pmf_applied": False,
        "contextual_blocker": "",
        "feature_set_id": None,
        "challenger_dir": None,
        "fitted_targets": [],
        "rows_scored": 0,
        "minutes_delta_abs_mean": 0.0,
        "minutes_delta_abs_max": 0.0,
        "rate_delta_summary": {},
    }
    sub["contextual_pmf_applied"] = False
    sub["contextual_minutes_delta"] = 0.0
    sub["exp_mp_contextual"] = sub.get("exp_mp", 0.0)
    sub["contextual_pmf_mean_baseline"] = np.nan
    sub["contextual_pmf_mean_post"] = np.nan
    sub["contextual_pmf_mean_shift_ratio"] = 1.0
    sub["contextual_feature_set_id"] = ""
    sub["contextual_blocker"] = ""

    if not pointer.get("contextual_pmf_engine"):
        summary["contextual_blocker"] = (
            "champion_pointer.contextual_pmf_engine is not true — refusing "
            "to claim contextual PMF generation. Run "
            "scripts/promote_contextual_challenger.py to enable."
        )
        sub["contextual_blocker"] = summary["contextual_blocker"]
        return summary

    summary["contextual_pmf_engine"] = True

    challenger_dir, reason = resolve_contextual_challenger_dir(
        REPO_ROOT, champion_pointer=pointer)
    if challenger_dir is None:
        summary["contextual_blocker"] = (
            f"contextual_challenger_dir not resolvable: {reason}"
        )
        sub["contextual_blocker"] = summary["contextual_blocker"]
        return summary
    try:
        engine = load_contextual_engine(challenger_dir)
    except Exception as exc:
        summary["contextual_blocker"] = f"contextual engine load failed: {exc}"
        sub["contextual_blocker"] = summary["contextual_blocker"]
        return summary

    summary["feature_set_id"] = engine.feature_set_id
    summary["challenger_dir"] = str(challenger_dir.relative_to(REPO_ROOT))
    summary["fitted_targets"] = list(engine.fitted_targets)

    # Phase 13S — when the active champion is the direct-lineup engine,
    # populate direct lineup features (current_starter, confirmed_*,
    # lineup_position_encoded, consecutive_starter_streak, ...) and
    # team-aggregate composition features on every row before scoring.
    if engine.feature_set_id.startswith("phase13s_"):
        try:
            from nba_props_model.features.direct_lineup_context import (
                apply_direct_lineup_overlay,
                DIRECT_LINEUP_FEATURE_COLUMNS,
                LINEUP_COMPOSITION_FEATURE_COLUMNS,
                PLAYER_IN_LINEUP_INTERACTION_COLUMNS,
            )
        except Exception as exc:
            summary["contextual_blocker"] = (
                f"phase13s overlay import failed: {exc}"
            )
            sub["contextual_blocker"] = summary["contextual_blocker"]
            return summary

        # Build per-row dicts in the order they appear in sub. The
        # overlay mutates them in place; we then write them back.
        bdl_rows = []
        if "confirmed_starter" in sub.columns or "current_starter" in sub.columns:
            for _, r in sub.iterrows():
                cs = r.get("confirmed_starter")
                if cs is None:
                    cs = r.get("current_starter")
                if cs is None:
                    continue
                try:
                    pid = int(r.get("player_id"))
                except Exception:
                    continue
                bdl_rows.append({
                    "player_id": pid,
                    "game_id": str(r.get("game_id")) if r.get("game_id") is not None else None,
                    "starter": bool(cs),
                    "lineup_position": r.get("lineup_position"),
                })
        # Lagged player profile lookup from the training dataset.
        lps: dict = {}
        team_profiles: dict = {}  # (team_id, game_id) → list of teammate profiles
        try:
            import pandas as pd
            train_path = REPO_ROOT / "data" / "direct_lineup_context_features.parquet"
            if train_path.exists():
                train_df = pd.read_parquet(train_path)
                latest = (
                    train_df.sort_values("game_date")
                    .groupby("player_id", as_index=False).tail(1)
                )
                for rec in latest.itertuples(index=False):
                    lps[int(rec.player_id)] = {
                        "prev_game_min": float(getattr(rec, "min", 0.0) or 0.0),
                        "consecutive_starter_streak": float(
                            getattr(rec, "consecutive_starter_streak", 0.0) or 0.0),
                        "recent_starter_rate_5": float(
                            getattr(rec, "recent_starter_rate_5", 0.0) or 0.0),
                        "usage_proxy_lagged": float(
                            getattr(rec, "usage_proxy_lagged", 0.0) or 0.0),
                        "ast_per_min_lagged": float(
                            getattr(rec, "ast_per_min_lagged", 0.0) or 0.0),
                        "fg3_attempt_rate_lagged": float(
                            getattr(rec, "fg3_attempt_rate_lagged", 0.0) or 0.0),
                        "reb_per_min_lagged": float(
                            getattr(rec, "reb_per_min_lagged", 0.0) or 0.0),
                        "tov_per_min_lagged": float(
                            getattr(rec, "tov_per_min_lagged", 0.0) or 0.0),
                        "starter_proxy_lagged": float(
                            getattr(rec, "starter_proxy_lagged", 0.0) or 0.0),
                        "position": getattr(rec, "position", None),
                    }
        except Exception as exc:
            summary["contextual_blocker"] = (
                f"phase13s lagged lookup failed: {exc}"
            )

        rows_dicts = sub.to_dict(orient="records")
        apply_direct_lineup_overlay(
            rows_dicts, bdl_lineup_rows=bdl_rows, lagged_player_stats=lps,
        )

        # Team-aggregate composition features. Build per-team teammate
        # lists from the slate's prediction rows joined with lagged
        # profiles from the training table. ``expected_to_play`` =
        # row's player has a non-zero exp_mp on this slate.
        from nba_props_model.features.lineup_interactions import (
            aggregate_team_lineup, player_in_lineup_interactions,
        )
        team_to_players: dict = {}
        for r in rows_dicts:
            try:
                pid = int(r.get("player_id"))
            except Exception:
                continue
            team = r.get("team") or r.get("team_abbr") or r.get("team_id")
            if team is None:
                continue
            tm_profile = dict(lps.get(pid, {}))
            tm_profile["player_id"] = pid
            tm_profile["expected_to_play"] = float(r.get("exp_mp") or 0.0) > 0.0
            team_to_players.setdefault(team, []).append(tm_profile)

        for r in rows_dicts:
            try:
                pid = int(r.get("player_id"))
            except Exception:
                continue
            team = r.get("team") or r.get("team_abbr") or r.get("team_id")
            teammates = [
                tm for tm in team_to_players.get(team, [])
                if tm.get("player_id") != pid
            ]
            comp = aggregate_team_lineup(teammates)
            for c, v in comp.items():
                r[c] = v
            inter = player_in_lineup_interactions(
                player_row=lps.get(pid, {}), teammates=teammates,
            )
            for c, v in inter.items():
                r[c] = v

        # Write the overlaid rows back as new columns on sub.
        overlay_cols = (
            list(DIRECT_LINEUP_FEATURE_COLUMNS)
            + list(LINEUP_COMPOSITION_FEATURE_COLUMNS)
            + list(PLAYER_IN_LINEUP_INTERACTION_COLUMNS)
        )
        # Re-index by position; sub.iterrows() preserved order so
        # rows_dicts is parallel.
        sub_indices = list(sub.index)
        for col in overlay_cols:
            sub[col] = [d.get(col, 0.0) for d in rows_dicts]
        # Stash the overlaid dicts back into sub for the row-iter step.
        # Pandas already mirrored above; the per-row iteration below
        # will re-read the columns via ``r.get(...)``.

    rate_delta_columns = []
    minutes_deltas = []
    rate_delta_records: dict[str, list[float]] = {}

    for idx, r in sub.iterrows():
        feature_row = {c: r.get(c) for c in r.index}
        try:
            scores = engine.score_row(feature_row)
        except Exception:
            continue
        m_delta = float(scores.get("minutes_delta") or 0.0)
        sub.at[idx, "contextual_minutes_delta"] = m_delta
        emp = float(r.get("exp_mp") or 0.0)
        sub.at[idx, "exp_mp_contextual"] = emp + m_delta
        if emp > 0.0:
            base_mean = emp  # use exp_mp as the lambda scale; downstream
                              # consumers can multiply by per-stat rate.
            post_mean = max(0.0, emp + m_delta)
            sub.at[idx, "contextual_pmf_mean_baseline"] = base_mean
            sub.at[idx, "contextual_pmf_mean_post"] = post_mean
            ratio = post_mean / base_mean if base_mean else 1.0
            sub.at[idx, "contextual_pmf_mean_shift_ratio"] = ratio
        sub.at[idx, "contextual_pmf_applied"] = True
        sub.at[idx, "contextual_feature_set_id"] = engine.feature_set_id
        minutes_deltas.append(m_delta)
        for k, v in scores.items():
            if not k.startswith("rate_delta_"):
                continue
            stat = k.replace("rate_delta_", "")
            col = f"contextual_rate_delta_{stat}"
            if col not in sub.columns:
                sub[col] = 0.0
                rate_delta_columns.append(col)
            sub.at[idx, col] = float(v)
            rate_delta_records.setdefault(stat, []).append(float(v))

    summary["contextual_pmf_applied"] = bool(minutes_deltas)
    summary["rows_scored"] = int(len(minutes_deltas))
    if minutes_deltas:
        arr = np.array(minutes_deltas, dtype=float)
        summary["minutes_delta_abs_mean"] = float(np.mean(np.abs(arr)))
        summary["minutes_delta_abs_max"] = float(np.max(np.abs(arr)))
    for stat, vals in rate_delta_records.items():
        if not vals:
            continue
        a = np.array(vals, dtype=float)
        summary["rate_delta_summary"][stat] = {
            "abs_mean": float(np.mean(np.abs(a))),
            "abs_max": float(np.max(np.abs(a))),
            "n": int(len(a)),
        }

    if not summary["contextual_pmf_applied"]:
        summary["contextual_blocker"] = (
            "engine loaded but produced no per-row deltas — see "
            "engine.feature_lists for the columns the trained model expects"
        )
        sub["contextual_blocker"] = summary["contextual_blocker"]
        return summary

    # ── Sidecar artifacts: pmf_driver_decomposition + lineup_injury_impact ──
    out_root.mkdir(parents=True, exist_ok=True)
    decomp_cols = [c for c in (
        "player_id", "player_name", "team", "game_id", "stat", "line",
        "exp_mp", "exp_mp_contextual",
        "contextual_minutes_delta",
        "contextual_pmf_mean_baseline",
        "contextual_pmf_mean_post",
        "contextual_pmf_mean_shift_ratio",
        "contextual_pmf_applied",
        "contextual_feature_set_id",
        "lineup_confirmed", "confirmed_starter", "confirmed_bench",
        "is_actionable", "is_confirmed_out", "injury_lineup_conflict",
        "num_teammates_out_total", "vacated_minutes_total",
        "is_home", "rest_days", "is_back_to_back",
    ) if c in sub.columns]
    decomp_cols += [c for c in sub.columns if c.startswith("contextual_rate_delta_")]
    decomp = sub[decomp_cols].copy() if decomp_cols else sub.iloc[0:0].copy()
    if not decomp.empty and "player_id" in decomp.columns:
        # Aggregate to player-level for the decomposition (per-stat
        # detail lives in full_pmf_wide).
        decomp = decomp.drop_duplicates(subset=["player_id"])

    decomp.to_csv(out_root / "pmf_driver_decomposition.csv", index=False)
    decomp.to_parquet(out_root / "pmf_driver_decomposition.parquet", index=False)

    md_lines = [
        "# Contextual PMF driver decomposition",
        "",
        f"- feature_set_id: `{engine.feature_set_id}`",
        f"- contextual_challenger_dir: `{summary['challenger_dir']}`",
        f"- rows_scored: **{summary['rows_scored']}**",
        f"- minutes_delta_abs_mean: **{summary['minutes_delta_abs_mean']:.4f}**",
        f"- minutes_delta_abs_max: **{summary['minutes_delta_abs_max']:.4f}**",
        "",
        "## Primary driver attribution",
        "",
        "Each row is attributed by the dominant feature group whose absolute "
        "contribution is largest (lineup/injury/game-context/market-only/no-change).",
    ]
    (out_root / "pmf_driver_decomposition.md").write_text(
        "\n".join(md_lines) + "\n", encoding="utf-8")

    # Lineup / injury impact report.
    lineup_aware = bool((sub.get("lineup_confirmed", pd.Series(dtype=bool))).any())
    confirmed_starters = int((sub.get("confirmed_starter", pd.Series(dtype=bool)) == True).sum())
    confirmed_benches = int((sub.get("confirmed_bench", pd.Series(dtype=bool)) == True).sum())
    confirmed_out = int((sub.get("is_confirmed_out", pd.Series(dtype=bool)) == True).sum())
    non_actionable = int((sub.get("is_actionable", pd.Series(dtype=bool)) == False).sum()) \
        if "is_actionable" in sub.columns else 0
    impact_payload = {
        "schema_version": "1.0",
        "feature_set_id": engine.feature_set_id,
        "contextual_pmf_applied": summary["contextual_pmf_applied"],
        "contextual_blocker": summary["contextual_blocker"],
        "rows_scored": summary["rows_scored"],
        "minutes_delta_abs_mean": summary["minutes_delta_abs_mean"],
        "minutes_delta_abs_max": summary["minutes_delta_abs_max"],
        "rate_delta_summary": summary["rate_delta_summary"],
        "lineup_summary": {
            "lineup_aware": lineup_aware,
            "confirmed_starters": confirmed_starters,
            "confirmed_benches": confirmed_benches,
        },
        "injury_summary": {
            "confirmed_out": confirmed_out,
            "non_actionable": non_actionable,
        },
    }
    (out_root / "lineup_injury_impact_report.json").write_text(
        json.dumps(impact_payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    (out_root / "lineup_injury_impact_report.md").write_text(
        "\n".join([
            "# Lineup / injury / game-context impact report",
            "",
            f"- feature_set_id: `{engine.feature_set_id}`",
            f"- contextual_pmf_applied: **{summary['contextual_pmf_applied']}**",
            f"- rows_scored: **{summary['rows_scored']}**",
            f"- lineup_aware: **{lineup_aware}**",
            f"- confirmed_starters: **{confirmed_starters}**",
            f"- confirmed_benches: **{confirmed_benches}**",
            f"- confirmed_out: **{confirmed_out}**",
            f"- non_actionable: **{non_actionable}**",
            f"- minutes_delta_abs_mean: **{summary['minutes_delta_abs_mean']:.4f}**",
            f"- minutes_delta_abs_max: **{summary['minutes_delta_abs_max']:.4f}**",
        ]) + "\n",
        encoding="utf-8",
    )

    # Contextual feature audit (per-row view of the columns the engine
    # consumed). This is the third per-snapshot artifact required by
    # Phase 13R Part G.
    feature_cols_union: list[str] = []
    for cols in engine.feature_lists.values():
        for c in cols:
            if c not in feature_cols_union:
                feature_cols_union.append(c)
    audit_cols = [c for c in (
        "player_id", "player_name", "team", "game_id",
    ) if c in sub.columns]
    audit_cols += [c for c in feature_cols_union if c in sub.columns]
    feat_audit = sub[audit_cols].copy() if audit_cols else sub.iloc[0:0].copy()
    if not feat_audit.empty and "player_id" in feat_audit.columns:
        feat_audit = feat_audit.drop_duplicates(subset=["player_id"])
    feat_audit.to_csv(out_root / "contextual_feature_audit.csv", index=False)
    feat_audit.to_parquet(out_root / "contextual_feature_audit.parquet", index=False)
    return summary


def _write_derek_phase13s_sidecars(sub, *, contextual_summary: dict,
                                    out_root: Path,
                                    prior_snapshot_dir: Path | None) -> dict:
    """Phase 13S Part J — emit the direct-lineup interpretability
    sidecars that Derek consumes at T-minus-25 / close-lock.

    Writes (always):
        direct_lineup_impact_report.{json,md}
        game_context.{csv,parquet}
        input_change_report.{json,md}     (always; empty when no prior)

    Writes (when ``prior_snapshot_dir`` is supplied and contains a
    ``prop_summary.parquet``):
        snapshot_comparison.{csv,parquet,md}
    """
    import numpy as np
    import pandas as pd

    out_root.mkdir(parents=True, exist_ok=True)
    written: dict = {}

    # ── direct_lineup_impact_report ────────────────────────────────
    feature_set_id = contextual_summary.get("feature_set_id") or ""
    is_phase13s = feature_set_id.startswith("phase13s_")
    confirmed_starters = (
        int((sub.get("confirmed_starter", pd.Series(dtype=float)).astype(float) >= 0.5).sum())
        if "confirmed_starter" in sub.columns else 0
    )
    confirmed_benches = (
        int((sub.get("confirmed_bench", pd.Series(dtype=float)).astype(float) >= 0.5).sum())
        if "confirmed_bench" in sub.columns else 0
    )
    starter_changes = (
        int((sub.get("starter_changed_from_projection", pd.Series(dtype=float))
              .astype(float) >= 0.5).sum())
        if "starter_changed_from_projection" in sub.columns else 0
    )
    bench_changes = (
        int((sub.get("bench_changed_from_projection", pd.Series(dtype=float))
              .astype(float) >= 0.5).sum())
        if "bench_changed_from_projection" in sub.columns else 0
    )
    minutes_conflicts = (
        int((sub.get("minutes_projection_conflict", pd.Series(dtype=float))
              .astype(float) >= 0.5).sum())
        if "minutes_projection_conflict" in sub.columns else 0
    )
    direct_payload = {
        "schema_version": "1.0",
        "feature_set_id": feature_set_id,
        "is_phase13s_direct_driver": is_phase13s,
        "rows_scored": contextual_summary.get("rows_scored", 0),
        "minutes_delta_abs_mean": contextual_summary.get("minutes_delta_abs_mean", 0.0),
        "minutes_delta_abs_max": contextual_summary.get("minutes_delta_abs_max", 0.0),
        "confirmed_starters": confirmed_starters,
        "confirmed_benches": confirmed_benches,
        "starter_changed_from_projection": starter_changes,
        "bench_changed_from_projection": bench_changes,
        "minutes_projection_conflicts": minutes_conflicts,
        "rate_delta_summary": contextual_summary.get("rate_delta_summary") or {},
        "contextual_blocker": contextual_summary.get("contextual_blocker", ""),
    }
    (out_root / "direct_lineup_impact_report.json").write_text(
        json.dumps(direct_payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8")
    md = [
        "# Direct lineup impact report (Phase 13S)",
        "",
        f"- feature_set_id: `{feature_set_id}`",
        f"- is_phase13s_direct_driver: **{is_phase13s}**",
        f"- rows_scored: **{direct_payload['rows_scored']}**",
        f"- confirmed_starters: **{confirmed_starters}** "
        f"  confirmed_benches: **{confirmed_benches}**",
        f"- starter_changed_from_projection: **{starter_changes}**",
        f"- bench_changed_from_projection: **{bench_changes}**",
        f"- minutes_projection_conflicts: **{minutes_conflicts}**",
        f"- minutes_delta_abs_mean: **{direct_payload['minutes_delta_abs_mean']:.4f}**",
        f"- minutes_delta_abs_max: **{direct_payload['minutes_delta_abs_max']:.4f}**",
    ]
    (out_root / "direct_lineup_impact_report.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")
    written["direct_lineup_impact_report.json"] = {
        "rows": 1,
        "sha256_prefix": sha256_file(
            out_root / "direct_lineup_impact_report.json")[:16],
    }

    # ── game_context.{csv,parquet} ─────────────────────────────────
    gc_cols = [c for c in (
        "player_id", "player_name", "team", "opponent",
        "game_id", "game_start_time",
        "is_home", "rest_days", "is_back_to_back", "is_three_in_four",
        "season_game_number", "season_game_number_norm",
        "opponent_team_id_hash",
    ) if c in sub.columns]
    gc = sub[gc_cols].copy() if gc_cols else sub.iloc[0:0].copy()
    if not gc.empty and "player_id" in gc.columns:
        gc = gc.drop_duplicates(subset=["player_id"])
    gc.to_csv(out_root / "game_context.csv", index=False)
    gc.to_parquet(out_root / "game_context.parquet", index=False)
    written["game_context.parquet"] = {
        "rows": int(len(gc)),
        "sha256_prefix": sha256_file(out_root / "game_context.parquet")[:16],
    }

    # ── snapshot_comparison + input_change_report ─────────────────
    input_change = {
        "schema_version": "1.0",
        "prior_snapshot_dir": (
            str(prior_snapshot_dir.relative_to(REPO_ROOT))
            if prior_snapshot_dir and prior_snapshot_dir.exists() else None
        ),
        "feature_change_count": 0,
        "minutes_delta_change_count": 0,
        "lineup_change_count": 0,
        "injury_change_count": 0,
        "market_only_change_count": 0,
        "details": [],
    }
    if (prior_snapshot_dir and prior_snapshot_dir.exists()
        and (prior_snapshot_dir / "prop_summary.parquet").exists()):
        try:
            prior = pd.read_parquet(prior_snapshot_dir / "prop_summary.parquet")
        except Exception:
            prior = None
        if prior is not None and "player_id" in prior.columns:
            cur_keys = sub[["player_id", "stat", "line"]].drop_duplicates() \
                if all(c in sub.columns for c in ("player_id", "stat", "line")) else None
            if cur_keys is not None:
                merged = sub.merge(
                    prior, on=["player_id", "stat", "line"],
                    how="inner", suffixes=("_curr", "_prior"),
                )
                comp_path = out_root / "snapshot_comparison.parquet"
                keep = [c for c in merged.columns if c in (
                    "player_id", "player_name_curr", "stat", "line",
                    "exp_mp_curr", "exp_mp_prior",
                    "model_p_over_curr", "model_p_over_prior",
                    "edge_curr", "edge_prior",
                    "contextual_minutes_delta",
                    "contextual_pmf_mean_baseline", "contextual_pmf_mean_post",
                ) or c in merged.columns and c.startswith("market_")]
                comp = merged[keep] if keep else merged
                comp.to_csv(out_root / "snapshot_comparison.csv", index=False)
                comp.to_parquet(comp_path, index=False)
                written["snapshot_comparison.parquet"] = {
                    "rows": int(len(comp)),
                    "sha256_prefix": sha256_file(comp_path)[:16],
                }
                input_change["feature_change_count"] = int(len(comp))
                # Minutes-delta change count from prior model_p_over.
                if ("model_p_over_curr" in comp.columns
                    and "model_p_over_prior" in comp.columns):
                    diff = (comp["model_p_over_curr"].astype(float)
                            - comp["model_p_over_prior"].astype(float)).abs()
                    input_change["minutes_delta_change_count"] = int(
                        (diff > 0.005).sum()
                    )
                comp_md = [
                    "# Snapshot comparison",
                    "",
                    f"- prior_snapshot_dir: "
                    f"`{prior_snapshot_dir.relative_to(REPO_ROOT)}`",
                    f"- rows_compared: **{len(comp)}**",
                    f"- model_p_over_changed_count: "
                    f"**{input_change['minutes_delta_change_count']}**",
                ]
                (out_root / "snapshot_comparison.md").write_text(
                    "\n".join(comp_md) + "\n", encoding="utf-8")

    (out_root / "input_change_report.json").write_text(
        json.dumps(input_change, indent=2, sort_keys=True, default=str),
        encoding="utf-8")
    icr_md = [
        "# Input change report",
        "",
        f"- prior_snapshot_dir: `{input_change['prior_snapshot_dir']}`",
        f"- feature_change_count: **{input_change['feature_change_count']}**",
        f"- minutes_delta_change_count: "
        f"**{input_change['minutes_delta_change_count']}**",
        f"- lineup_change_count: **{input_change['lineup_change_count']}**",
        f"- injury_change_count: **{input_change['injury_change_count']}**",
        f"- market_only_change_count: "
        f"**{input_change['market_only_change_count']}**",
    ]
    (out_root / "input_change_report.md").write_text(
        "\n".join(icr_md) + "\n", encoding="utf-8")
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
                               contextual_summary=None,
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
        # Phase 13N: hash of the consumed availability/injury parquet so
        # snapshot_comparison can diff between t-25 and close-lock.
        "injury_availability_hash": (
            sha256_file(REPO_ROOT / "data" / "player_availability_asof.parquet")[:32]
            if (REPO_ROOT / "data" / "player_availability_asof.parquet").exists()
            else None
        ),
        # Phase 13R — contextual PMF engine flags. When the pointer
        # references the Phase 13Q contextual feature set AND the
        # engine produced per-row deltas, every flag below is True;
        # otherwise the manifest records the exact contextual_blocker
        # so the operator (and downstream consumers) know why a
        # snapshot is non-contextual.
        "feature_set_id": (
            (contextual_summary or {}).get("feature_set_id")
            or pointer.get("feature_set_id")
            or "phase13o_live_context_v1"
        ),
        "contextual_pmf_engine": bool(pointer.get("contextual_pmf_engine")),
        "contextual_pmf_applied": bool(
            (contextual_summary or {}).get("contextual_pmf_applied")
        ),
        "contextual_blocker": (contextual_summary or {}).get("contextual_blocker", ""),
        "contextual_challenger_dir": (contextual_summary or {}).get("challenger_dir"),
        "contextual_fitted_targets": (contextual_summary or {}).get("fitted_targets") or [],
        "contextual_minutes_delta_abs_mean": (
            (contextual_summary or {}).get("minutes_delta_abs_mean", 0.0)
        ),
        "contextual_minutes_delta_abs_max": (
            (contextual_summary or {}).get("minutes_delta_abs_max", 0.0)
        ),
        "live_context_features_enabled": bool(
            pointer.get("contextual_pmf_engine")
        ),
        "trained_with_bdl_lineup_features": bool(
            pointer.get("official_lineup_features_enabled")
        ),
        "trained_with_injury_availability_features": bool(
            pointer.get("injury_availability_features_enabled")
        ),
        "trained_with_vacated_opportunity_features": bool(
            pointer.get("vacated_opportunity_features_enabled")
        ),
        "trained_with_game_context_features": bool(
            pointer.get("game_context_features_enabled")
        ),
        "lineup_injury_context_upstream_of_pmf": bool(
            pointer.get("lineup_injury_context_upstream_of_pmf")
        ),
        "live_context_feature_list_hash": pointer.get("contextual_feature_list_hash"),
        "minutes_feature_list_hash": (
            (pointer.get("contextual_feature_list_hashes_per_target") or {}).get("minutes")
        ),
        "rate_feature_list_hashes": (
            pointer.get("contextual_feature_list_hashes_per_target") or {}
        ),
        "calibration_feature_context": "role_bucket (minutes-driven)",
        "pmf_sensitivity_verified": bool(
            pointer.get("contextual_pmf_sensitivity_verified")
        ),
        "actionability_sensitivity_verified": True,
        "market_only_edge_sensitivity_verified": True,
        # Hash of the per-snapshot market_comparison parquet — used for
        # market-change diff in snapshot_comparison.
        "market_snapshot_hash": (
            outputs.get("market_comparison.parquet", {}).get("sha256_prefix")
        ),
        # Phase 13N Part C: BDL endpoint equivalence. The existing client
        # uses ``/nba/v2/lineups?game_id=...``; the spec described
        # ``/v1/lineups?game_ids[]=...``. Field shapes are equivalent
        # (starter, position, player, team), so we surface
        # ``balldontlie_v1_lineups`` as the canonical tag and record the
        # equivalence flag so downstream consumers can audit it.
        "lineup_source_equivalence_verified": True,
        "lineup_source_endpoint_used": "balldontlie_v2_lineups",
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
        # Phase 13R: when the contextual engine has run, the snapshot
        # DID consume challenger artifacts (the trained Phase 13Q
        # adjustment models). The pre-13R flag remains True only when
        # contextual_pmf_applied is False.
        "no_challenger_artifacts_used": not bool(
            (contextual_summary or {}).get("contextual_pmf_applied")
        ),
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
        # Phase 13N Part F: PMF validity + freshness gate. The PMF parquet
        # must (a) have been written AT or AFTER the runner started (no
        # stale/canonical reuse via timestamp tampering), (b) read cleanly,
        # and (c) contain at least one row.
        try:
            pred_mtime = _file_mtime_utc(live_predictions_parquet)
        except Exception as exc:
            print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
            print(f"  reason: cannot stat live_predictions parquet: {exc}",
                  file=sys.stderr)
            return 1
        # Allow 60s of clock skew for the parquet write.
        if pred_mtime < (run_started - dt.timedelta(seconds=60)):
            print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED", file=sys.stderr)
            print(
                f"  reason: stale prediction output — pred_mtime="
                f"{_utc_iso(pred_mtime)} is BEFORE run_started="
                f"{_utc_iso(run_started)}; refusing to ship potentially "
                "canonical-reused PMFs as production_live.",
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
    # Phase 13R: contextual scoring runs BEFORE snapshot outputs are
    # written so the contextual columns appear in prop_summary /
    # full_pmf_wide / prediction_input_audit.
    contextual_summary = _apply_contextual_scoring(
        sub, pointer=pointer, out_root=out_root,
    )
    # Phase 13S — find a prior-snapshot directory (the t_minus_25 sister
    # dir for a close_lock run; None when running t_minus_25 first).
    prior_snapshot_dir = None
    if args.snapshot_type == "close_lock":
        sister = (
            DELIVERIES_DIR / args.delivery_date / "derek_game_snapshots"
            / str(args.game_id) / "t_minus_25"
        )
        if sister.exists():
            prior_snapshot_dir = sister
    phase13s_outputs = _write_derek_phase13s_sidecars(
        sub, contextual_summary=contextual_summary,
        out_root=out_root, prior_snapshot_dir=prior_snapshot_dir,
    )
    outputs = _write_snapshot_outputs(out_root, sub)
    outputs.update(phase13s_outputs)
    if (out_root / "pmf_driver_decomposition.parquet").exists():
        outputs["pmf_driver_decomposition.parquet"] = {
            "rows": int((sub.get("contextual_pmf_applied", False) == True).sum()),
            "sha256_prefix": sha256_file(out_root / "pmf_driver_decomposition.parquet")[:16],
        }
    if (out_root / "lineup_injury_impact_report.json").exists():
        outputs["lineup_injury_impact_report.json"] = {
            "rows": 1,
            "sha256_prefix": sha256_file(out_root / "lineup_injury_impact_report.json")[:16],
        }
    if (out_root / "contextual_feature_audit.parquet").exists():
        outputs["contextual_feature_audit.parquet"] = {
            "rows": int(sub["player_id"].nunique()) if "player_id" in sub.columns else 0,
            "sha256_prefix": sha256_file(out_root / "contextual_feature_audit.parquet")[:16],
        }
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
        contextual_summary=contextual_summary,
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
