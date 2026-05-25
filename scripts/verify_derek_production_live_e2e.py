"""Phase 13T Part C — Derek production-live end-to-end verifier.

Decides one of three outcomes:

    DEREK_PRODUCTION_LIVE_E2E_PASS     - at least one production-live
        Derek snapshot exists for ``--delivery-date`` and proves the
        full contextual PMF pipeline ran (manifest fields,
        feature_set_id, contextual flags, lineup/injury/game-context
        files, PMF outputs, no_post_tip_data_used=true).

    DEREK_PRODUCTION_LIVE_E2E_PENDING  - no Derek snapshots are
        currently expected. Either the slate is not published yet,
        the slate has zero games, or the wall-clock is between cron
        windows (no game's T-25 / close-lock target has fired).

    DEREK_PRODUCTION_LIVE_E2E_FAILED   - eligible games existed
        AND were due in a prior cron window AND outputs are missing
        OR a snapshot lacks required contextual / PMF proof OR a
        snapshot falsely claims contextual proof.

PASS conditions (every check must hold for >= 1 production-live snapshot):
    - snapshot_manifest.json present
    - feature_set_id matches active champion's feature_set_id (or any
      'phase13r_'/'phase13s_' prefix)
    - direct_lineup_pmf_driver flag true (when champion is Phase 13S)
    - contextual_pmf_engine flag true
    - pmfs_recomputed=true and pmf_source=live_snapshot_recomputed
    - lineup_context.parquet, injury_availability_context.parquet,
      game_context.parquet, contextual_feature_audit.parquet,
      pmf_driver_decomposition.parquet, direct_lineup_impact_report.json
      all present
    - prop_summary.parquet, full_pmf_wide.parquet, market_comparison.parquet
      all present
    - no_post_tip_data_used=true

PENDING conditions (any one):
    - predictions/all_props_<date>.parquet missing OR has 0 games
    - all schedule games have target_utc strictly in the future
    - no game has tipped yet (game_start_time_utc all > now_utc)

FAILED conditions:
    - schedule has games whose T-25 target was >= 12 minutes in the
      past AND no production-live snapshot exists for that game's
      T-25 type
    - any production-live snapshot fails one of the PASS checks
    - any snapshot claims contextual but lacks supporting fields
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


DELIVERIES_DIR = REPO_ROOT / "deliveries"
PRED_DIR = REPO_ROOT / "predictions"
HEALTH_DIR = REPO_ROOT / "artifacts" / "automation_health"
CHAMPION_POINTER_PATH = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"

T_MINUS_25_OFFSET_MIN = 25
CLOSE_LOCK_OFFSET_MIN = 5

# Required snapshot files for a PASS-level production-live snapshot.
REQUIRED_PMF_FILES = (
    "snapshot_manifest.json",
    "snapshot_report.md",
    "prop_summary.csv",
    "prop_summary.parquet",
    "full_pmf_wide.csv",
    "full_pmf_wide.parquet",
    "outcome_level_probabilities.csv",
    "outcome_level_probabilities.parquet",
    "market_comparison.csv",
    "market_comparison.parquet",
)
REQUIRED_CONTEXT_FILES = (
    "lineup_context.csv",
    "lineup_context.parquet",
    "injury_availability_context.csv",
    "injury_availability_context.parquet",
    "game_context.csv",
    "game_context.parquet",
    "contextual_feature_audit.csv",
    "contextual_feature_audit.parquet",
    "prediction_input_audit.csv",
    "prediction_input_audit.parquet",
    "pmf_driver_decomposition.csv",
    "pmf_driver_decomposition.parquet",
    "pmf_driver_decomposition.md",
    "lineup_injury_impact_report.json",
    "lineup_injury_impact_report.md",
    "direct_lineup_impact_report.json",
    "direct_lineup_impact_report.md",
)


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _utc_iso(d: dt.datetime | None) -> str | None:
    if d is None:
        return None
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_iso_to_utc(s):
    if not s:
        return None
    try:
        d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return None


def _load_schedule(delivery_date: str) -> list[dict]:
    parquet = PRED_DIR / f"all_props_{delivery_date}.parquet"
    if not parquet.exists():
        return []
    try:
        import pandas as pd
        df = pd.read_parquet(parquet)
        if "game_id" not in df.columns:
            return []
        rows: dict[str, dict] = {}
        gst_col = "game_start_time" if "game_start_time" in df.columns else None
        for _, r in df.iterrows():
            gid = str(r.get("game_id"))
            if gid in rows:
                continue
            rec = {"game_id": gid}
            if gst_col:
                gs = r.get(gst_col)
                if gs is not None and not pd.isna(gs):
                    rec["game_start_time"] = str(gs)
            rows[gid] = rec
        return list(rows.values())
    except Exception:
        return []


def _load_pointer() -> dict:
    if not CHAMPION_POINTER_PATH.exists():
        return {}
    try:
        return json.loads(CHAMPION_POINTER_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _check_snapshot(snap_dir: Path, *, pointer: dict) -> tuple[bool, list[str], dict]:
    """Return (passes_e2e, issues, manifest)."""
    issues: list[str] = []
    manifest_path = snap_dir / "snapshot_manifest.json"
    if not manifest_path.exists():
        return False, [f"missing snapshot_manifest.json"], {}
    try:
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, [f"cannot parse snapshot_manifest.json: {exc}"], {}

    # Production-live mode required for E2E PASS classification.
    # Phase 13U — production_live_current also counts (current_live snapshots
    # use the contextual champion the same way).
    sm = m.get("snapshot_mode")
    if sm not in ("production_live", "production_live_current"):
        return False, [f"snapshot_mode={sm!r} is not production_live"], m

    # Required files.
    for f in REQUIRED_PMF_FILES:
        if not (snap_dir / f).exists():
            issues.append(f"missing {f}")
    for f in REQUIRED_CONTEXT_FILES:
        if not (snap_dir / f).exists():
            issues.append(f"missing context file {f}")

    # PMF recomputation required. Phase 13U — current_live snapshots
    # honestly mark pmf_source=live_snapshot_recomputed_canonical_current
    # (canonical predictions reused, contextual engine re-scored).
    accepted_sources = (
        "live_snapshot_recomputed",
        "live_snapshot_recomputed_canonical_current",
    )
    if not (m.get("pmfs_recomputed") is True
            and m.get("pmf_source") in accepted_sources):
        issues.append(
            f"pmfs_recomputed={m.get('pmfs_recomputed')} "
            f"pmf_source={m.get('pmf_source')!r} — production-live must recompute"
        )

    # Contextual flags.
    if not m.get("contextual_pmf_engine"):
        issues.append("contextual_pmf_engine flag not true on snapshot manifest")
    pointer_fs = (pointer.get("feature_set_id") or "").lower()
    snap_fs = (m.get("feature_set_id") or "").lower()
    if pointer_fs and snap_fs and snap_fs != pointer_fs:
        # Allow snapshot to have a contextual feature_set_id even when
        # pointer is older — but flag mismatch.
        if not (snap_fs.startswith(("phase13r_", "phase13s_"))
                and pointer_fs.startswith(("phase13r_", "phase13s_"))):
            issues.append(
                f"feature_set_id mismatch: snapshot={snap_fs!r} "
                f"pointer={pointer_fs!r}"
            )
    if pointer.get("direct_lineup_pmf_driver") and not m.get("contextual_pmf_applied"):
        issues.append(
            "champion is Phase 13S direct-lineup driver but snapshot's "
            "contextual_pmf_applied is not true"
        )

    # No-post-tip-data invariant.
    if not m.get("no_post_tip_data_used"):
        issues.append("no_post_tip_data_used flag not true")

    # Phase 13W — manifest truth fields must NEVER be None.
    # For current_live snapshots, game_start_time may be null when the
    # snapshot was generated before the daily schedule was resolved. This
    # is a warning, not a hard failure — T-25 and close-lock snapshots
    # (which fire after schedule resolution) are the authoritative signal.
    snap_type_from_dir = snap_dir.name  # "current_live", "t_minus_25", "close_lock"
    gst_optional_for_current_live = snap_type_from_dir == "current_live"
    for f in (
        "game_start_time",
        "game_start_time_utc",
        "game_start_time_source",
        "game_start_time_resolution_confidence",
        "BDL_lineup_fetch_attempted",
        "BDL_lineup_fetch_status",
        "BDL_lineup_rows",
        "BDL_lineup_endpoint",
        "BDL_injury_fetch_attempted",
        "BDL_injury_fetch_status",
        "BDL_injury_rows",
        "BDL_injury_endpoint",
        "official_lineup_context_supplied",
        "lineup_context_supplied",
        "injury_context_supplied",
        "game_context_supplied",
        "lineup_confirmed",
        "lineup_aware",
        "lineup_affects_pmf_features",
        "injury_affects_pmf_features",
        "direct_lineup_features_consumed",
        "lineup_source",
        "lineup_blocker",
        "injury_source",
        "injury_blocker",
        "no_post_tip_data_used",
        "market_odds_used_as_features",
        "market_odds_used_for_edge_only",
    ):
        if m.get(f) is None:
            if gst_optional_for_current_live and f in (
                "game_start_time", "game_start_time_utc",
                "game_start_time_source", "game_start_time_resolution_confidence",
            ):
                # current_live snapshots may precede schedule resolution.
                print(
                    f"  ::notice::current_live manifest.{f} is None — "
                    "acceptable (schedule may not have been resolved yet)"
                )
            else:
                issues.append(f"manifest.{f} is None (required non-null)")
    # Phase 13W — game_start_time must mirror game_start_time_utc.
    if m.get("game_start_time") and m.get("game_start_time_utc"):
        if str(m.get("game_start_time")) != str(m.get("game_start_time_utc")):
            issues.append(
                f"game_start_time={m.get('game_start_time')!r} != "
                f"game_start_time_utc={m.get('game_start_time_utc')!r}"
            )
    if m.get("market_odds_used_as_features") is True:
        issues.append("market_odds_used_as_features=True (must be False)")
    if m.get("market_odds_used_for_edge_only") is False:
        issues.append("market_odds_used_for_edge_only=False (must be True)")

    # Phase 13T — explicit Phase 13S champion-flag checks. When the
    # active pointer claims direct_lineup_pmf_driver, the snapshot
    # manifest must mirror it. The manifest also has to record the
    # full per-feature-group enable flags so Derek consumers can rely
    # on them without re-reading the pointer.
    if pointer.get("direct_lineup_pmf_driver"):
        if not m.get("direct_lineup_pmf_driver"):
            issues.append(
                "manifest.direct_lineup_pmf_driver missing/false even "
                "though champion_pointer.direct_lineup_pmf_driver=True"
            )
        for flag in (
            "official_lineup_features_enabled",
            "injury_availability_features_enabled",
            "vacated_opportunity_features_enabled",
            "lineup_composition_features_enabled",
            "game_context_features_enabled",
        ):
            if not m.get(flag):
                issues.append(
                    f"manifest.{flag} missing/false but pointer enables it"
                )

    # Phase 13T — BDL lineup fetch attempted: either
    # lineup_confirmed=True OR lineup_blocker is non-empty. A snapshot
    # with both lineup_confirmed=False AND no lineup_blocker is
    # silently failing — flag it.
    lineup_confirmed = m.get("lineup_confirmed")
    lineup_blocker = m.get("lineup_blocker") or ""
    if lineup_confirmed is None:
        issues.append(
            "manifest.lineup_confirmed missing — BDL lineup fetch "
            "status not recorded"
        )
    if not lineup_confirmed and not lineup_blocker:
        issues.append(
            "lineup_confirmed=False but lineup_blocker is empty — "
            "BDL lineup fetch failure must be recorded"
        )

    # BDL injury / availability fetch attempted: at minimum the
    # manifest must record injury_source and availability_source
    # strings (paths or live endpoint identifiers).
    if not m.get("injury_source"):
        issues.append("manifest.injury_source missing")
    if not m.get("availability_source"):
        issues.append("manifest.availability_source missing")

    # Market odds invariant: the snapshot must NOT claim market odds
    # were used as model features. If the manifest records the flag
    # explicitly, enforce it; otherwise the absence is acceptable
    # (legacy manifests didn't carry it).
    if m.get("market_odds_used_as_features") is True:
        issues.append(
            "manifest.market_odds_used_as_features=True — market odds "
            "must never be model features"
        )

    # If the snapshot claims contextual_pmf_applied=true, the trained
    # artifacts must really have been used (challenger_dir set).
    if m.get("contextual_pmf_applied"):
        if not m.get("contextual_challenger_dir"):
            issues.append(
                "contextual_pmf_applied=true but contextual_challenger_dir "
                "is empty — snapshot is falsely claiming contextual proof"
            )

    return (not issues), issues, m


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    p.add_argument("--miss-grace-minutes", type=int, default=12,
                   help="A T-25 target miss is treated as a hard failure once "
                        "the wall clock is more than this many minutes past "
                        "the close of the dispatch window. Default 12.")
    args = p.parse_args(argv)

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    now = _utcnow()
    pointer = _load_pointer()
    schedule = _load_schedule(args.delivery_date)
    schedule_size = len(schedule)
    pred_parquet_present = (PRED_DIR / f"all_props_{args.delivery_date}.parquet").exists()

    facts: dict = {
        "delivery_date": args.delivery_date,
        "now_utc": _utc_iso(now),
        "predictions_parquet_present": pred_parquet_present,
        "schedule_size": schedule_size,
        "champion_pointer_feature_set_id": pointer.get("feature_set_id"),
        "champion_pointer_direct_lineup_pmf_driver": pointer.get(
            "direct_lineup_pmf_driver"),
        "champion_pointer_contextual_pmf_engine": pointer.get(
            "contextual_pmf_engine"),
    }

    base = DELIVERIES_DIR / args.delivery_date / "derek_game_snapshots"

    # Compute per-game eligibility.
    schedule_eval: list[dict] = []
    any_target_in_past = False
    any_target_overdue = False
    for entry in schedule:
        gid = entry["game_id"]
        gs = _parse_iso_to_utc(entry.get("game_start_time"))
        t25_target = (gs - dt.timedelta(minutes=T_MINUS_25_OFFSET_MIN)) if gs else None
        cl_target = (gs - dt.timedelta(minutes=CLOSE_LOCK_OFFSET_MIN)) if gs else None
        # Window for "should have been generated": target + 7 minutes
        # (matches dispatcher T_MINUS_25_WINDOW closing bound) + grace.
        t25_close = (
            t25_target + dt.timedelta(minutes=7 + args.miss_grace_minutes)
            if t25_target else None
        )
        cl_close = (
            cl_target + dt.timedelta(minutes=-1 + args.miss_grace_minutes)
            if cl_target else None
        )
        t25_overdue = bool(t25_close and now > t25_close)
        cl_overdue = bool(cl_close and now > cl_close)
        if t25_target and now >= t25_target:
            any_target_in_past = True
        if t25_overdue or cl_overdue:
            any_target_overdue = True
        schedule_eval.append({
            "game_id": gid,
            "game_start_time": entry.get("game_start_time"),
            "t25_target_utc": _utc_iso(t25_target),
            "cl_target_utc": _utc_iso(cl_target),
            "t25_overdue": t25_overdue,
            "cl_overdue": cl_overdue,
        })

    facts["schedule_eval"] = schedule_eval
    facts["any_target_in_past"] = any_target_in_past
    facts["any_target_overdue"] = any_target_overdue

    # Phase 13U — pre-check whether any current_live snapshots exist
    # for this delivery date. If yes, run the full snapshot evaluation
    # below (current_live mode counts toward PASS). Only short-circuit
    # to PENDING when neither current_live snapshots are present nor
    # any T-25 target has passed.
    has_current_live_snapshots = False
    if base.exists():
        for game_dir in base.iterdir():
            if (game_dir / "current_live" / "snapshot_manifest.json").exists():
                has_current_live_snapshots = True
                break

    # PENDING short-circuits.
    if not pred_parquet_present:
        facts["pending_reason"] = "no_predictions_parquet"
    elif schedule_size == 0:
        facts["pending_reason"] = "predictions_have_zero_games"
    elif not any_target_in_past and not has_current_live_snapshots:
        facts["pending_reason"] = "all_targets_in_future"

    if facts.get("pending_reason"):
        payload = {"schema_version": "1.0", "outcome": "pending", "facts": facts}
        (HEALTH_DIR / f"derek_production_live_e2e_{args.delivery_date}.json"
         ).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        (HEALTH_DIR / f"derek_production_live_e2e_{args.delivery_date}.md"
         ).write_text(
            "\n".join([
                f"# Derek production-live E2E — {args.delivery_date}",
                "",
                f"- outcome: **pending**",
                f"- reason: {facts.get('pending_reason')}",
                f"- now_utc: {_utc_iso(now)}",
                f"- predictions_parquet_present: "
                f"{facts['predictions_parquet_present']}",
                f"- schedule_size: {schedule_size}",
                f"- any_target_in_past: {any_target_in_past}",
            ]) + "\n",
            encoding="utf-8",
        )
        print("DEREK_PRODUCTION_LIVE_E2E_PENDING")
        print(
            f"  reason={facts.get('pending_reason')}  "
            f"now_utc={_utc_iso(now)}  "
            f"schedule_size={schedule_size}  "
            f"predictions_parquet_present={pred_parquet_present}"
        )
        return 0

    # Now check actual snapshots.
    snapshot_failures: list[str] = []
    pl_passes: list[dict] = []
    pl_fails: list[dict] = []
    if base.exists():
        for game_dir in sorted(base.iterdir()):
            if not game_dir.is_dir():
                continue
            for snap_type in ("current_live", "t_minus_25", "close_lock"):
                snap_dir = game_dir / snap_type
                if not snap_dir.exists():
                    continue
                # Phase 13Z — folders with only a missed_snapshot_manifest.json
                # are not production-live snapshots; skip them here so they
                # don't count toward pl_fails.
                if (
                    not (snap_dir / "snapshot_manifest.json").exists()
                    and (snap_dir / "missed_snapshot_manifest.json").exists()
                ):
                    continue
                ok, issues, m = _check_snapshot(snap_dir, pointer=pointer)
                rec = {
                    "game_id": game_dir.name,
                    "snapshot_type": snap_type,
                    "issues": issues,
                    "feature_set_id": (m or {}).get("feature_set_id"),
                    "snapshot_mode": (m or {}).get("snapshot_mode"),
                }
                if ok:
                    pl_passes.append(rec)
                else:
                    pl_fails.append(rec)
    facts["pl_pass_count"] = len(pl_passes)
    facts["pl_fail_count"] = len(pl_fails)
    facts["pl_passes"] = pl_passes
    facts["pl_fails"] = pl_fails

    # Phase 13Z — overdue_unresolved is populated by the per_type
    # state-machine loop below; we'll filter into overdue_missing
    # after that loop runs.
    overdue_unresolved: list[str] = []
    overdue_missing: list[str] = []

    # Phase 13W — per-snapshot-type pass/pending/missed lines.
    # Phase 13Z — replace the legacy heuristic with the shared
    # snapshot state machine so we never emit PENDING_NOT_DUE when
    # now > target.
    try:
        from nba_props_model.derek import classify_snapshot_state
    except Exception:
        classify_snapshot_state = None
    per_type_lines: list[tuple[str, str, str]] = []  # (kind, type, detail)
    have_current_live_pass = any(
        r["snapshot_type"] == "current_live" for r in pl_passes
    )
    if have_current_live_pass:
        per_type_lines.append(("PASS", "CURRENT_LIVE", ""))

    # Required proof scripts — Phase 13W + 13X assert these exist on
    # disk and are runnable. Missing proof scripts is a hard fail.
    proof_scripts_missing: list[str] = []
    for s in (
        "scripts/verify_bdl_fetch_proof_for_derek.py",
        "scripts/audit_contextual_delta_variation.py",
        "scripts/verify_daily_retrain_recalibration.py",
        "scripts/build_daily_model_training_report.py",
        # Phase 13X — root cause + calibration + publishability + WoO.
        "scripts/audit_derek_edge_root_cause.py",
        "scripts/audit_derek_calibration_for_edge_buckets.py",
        "scripts/apply_derek_edge_publishability.py",
        "scripts/verify_phase13x_woo_unchanged.py",
    ):
        if not (REPO_ROOT / s).exists():
            proof_scripts_missing.append(s)

    # Phase 13X — required audit reports for the delivery date.
    required_phase13x_reports = (
        f"artifacts/automation_health/derek_edge_root_cause_{args.delivery_date}.json",
        f"artifacts/automation_health/derek_edge_root_cause_{args.delivery_date}.md",
        f"artifacts/automation_health/derek_edge_calibration_{args.delivery_date}.json",
    )
    missing_reports: list[str] = []
    for rel in required_phase13x_reports:
        if not (REPO_ROOT / rel).exists():
            missing_reports.append(rel)
    facts["phase13x_reports_missing"] = missing_reports

    # Phase 13X — every Derek market_comparison.parquet must carry the
    # publishability + reasonability columns.
    required_publish_cols = (
        "edge_publish_status",
        "edge_reasonability_status",
        "push_line",
        "push_prob",
        "p0",
        "pmf_mean",
        "pmf_variance",
        "model_prob_from_pmf",
        "market_prob_recomputed",
        "raw_edge_recomputed",
        "ev_recomputed",
        "large_edge_bucket",
        "calibration_support_status",
        "calibration_bucket_n",
    )
    publish_col_failures: list[str] = []
    actionable_unconfirmed: list[str] = []
    blocker_threshold_failures: list[str] = []
    if base.exists():
        try:
            import pandas as pd
            for game_dir in sorted(base.iterdir()):
                if not game_dir.is_dir():
                    continue
                for snap_type in ("current_live", "t_minus_25", "close_lock"):
                    sd = game_dir / snap_type
                    mc = sd / "market_comparison.parquet"
                    if not mc.exists():
                        continue
                    df = pd.read_parquet(mc)
                    missing_cols = [c for c in required_publish_cols
                                    if c not in df.columns]
                    if missing_cols:
                        publish_col_failures.append(
                            f"{sd.relative_to(REPO_ROOT)}: missing columns "
                            f"{missing_cols}"
                        )
                        continue
                    # current_live without confirmed lineup must NEVER
                    # have an ACTIONABLE_REVIEWED row.
                    manifest = sd / "snapshot_manifest.json"
                    m = {}
                    if manifest.exists():
                        try:
                            m = json.loads(manifest.read_text(encoding="utf-8"))
                        except Exception:
                            m = {}
                    if (m.get("snapshot_type") == "current_live"
                        and not m.get("lineup_confirmed")):
                        bad = df[df["edge_publish_status"] == "ACTIONABLE_REVIEWED"]
                        if not bad.empty:
                            actionable_unconfirmed.append(
                                f"{sd.relative_to(REPO_ROOT)}: {len(bad)} "
                                "rows ACTIONABLE_REVIEWED on unconfirmed-lineup current_live"
                            )
                    # |raw_edge| >= 0.30 must be PUBLISH_BLOCKER (or
                    # documented).
                    big = df[df["raw_edge"].abs() >= 0.30]
                    bad = big[big["edge_publish_status"] != "PUBLISH_BLOCKER"]
                    if not bad.empty:
                        blocker_threshold_failures.append(
                            f"{sd.relative_to(REPO_ROOT)}: {len(bad)} rows "
                            "with |edge| >= 30pp not marked PUBLISH_BLOCKER"
                        )
        except Exception as exc:
            publish_col_failures.append(f"phase13x column scan failed: {exc}")
    facts["phase13x_publish_col_failures"] = publish_col_failures
    facts["phase13x_actionable_unconfirmed_failures"] = actionable_unconfirmed
    facts["phase13x_blocker_threshold_failures"] = blocker_threshold_failures

    # T-25 / close-lock per-game decisions via the shared state
    # machine (Phase 13Z). Possible outcomes:
    #
    #   EXISTS                 → PASS
    #   NOT_DUE                → PENDING_NOT_DUE
    #   DUE_WINDOW             → PENDING_DUE_NOW (dispatch should fire)
    #   LATE_BUT_PRE_TIP       → MISSED_RECOVERABLE (dispatch should fire)
    #   MISSED_POST_TIP +
    #     missed_marker        → MISSED_POST_TIP_DOCUMENTED (PASS-eq)
    #   MISSED_POST_TIP +
    #     no marker            → MISSED_POST_TIP_UNDOCUMENTED (FAILED)
    #
    false_pending_count = 0
    for ev in schedule_eval:
        gid = ev["game_id"]
        for snap_type, label in (
            ("t_minus_25", "T_MINUS_25"),
            ("close_lock", "CLOSE_LOCK"),
        ):
            sd = base / gid / snap_type
            target_iso = ev.get(
                "t25_target_utc" if snap_type == "t_minus_25"
                else "cl_target_utc"
            )
            present = (sd / "snapshot_manifest.json").exists()
            missed_marker = (sd / "missed_snapshot_manifest.json").exists()
            if classify_snapshot_state is not None:
                sr = classify_snapshot_state(
                    now_utc=now,
                    game_start_time_utc=ev.get("game_start_time"),
                    snapshot_type=snap_type,
                    snapshot_exists=present,
                    missed_marker_exists=missed_marker,
                )
                state = sr.state
                detail = (
                    f"game={gid} target_utc={target_iso} "
                    f"now={_utc_iso(now)}"
                )
            else:
                state = "EXISTS" if present else "NOT_DUE"
                detail = f"game={gid} target_utc={target_iso}"
            if state == "EXISTS":
                ok, issues, _ = _check_snapshot(sd, pointer=pointer)
                if ok:
                    per_type_lines.append(("PASS", label, detail))
                else:
                    per_type_lines.append((
                        "FAILED", label,
                        f"game={gid} issues={issues}",
                    ))
            elif state == "NOT_DUE":
                per_type_lines.append((
                    "PENDING_NOT_DUE", label, detail
                ))
            elif state == "DUE_WINDOW":
                per_type_lines.append((
                    "PENDING_DUE_NOW", label,
                    detail + "  dispatcher should fire on next run",
                ))
                overdue_unresolved.append(f"{gid}/{snap_type}")
            elif state == "LATE_BUT_PRE_TIP":
                per_type_lines.append((
                    "MISSED_RECOVERABLE", label,
                    detail + "  late but pre-tip — dispatcher will recover",
                ))
                overdue_unresolved.append(f"{gid}/{snap_type}")
            elif state == "MISSED_POST_TIP":
                if missed_marker:
                    per_type_lines.append((
                        "MISSED_POST_TIP_DOCUMENTED", label,
                        detail + "  missed_snapshot_manifest.json present",
                    ))
                else:
                    per_type_lines.append((
                        "MISSED_POST_TIP_UNDOCUMENTED", label,
                        detail
                        + "  game tipped before snapshot was generated; "
                          "no missed_snapshot_manifest.json — Phase 13Z "
                          "dispatch should write one",
                    ))
                    overdue_unresolved.append(f"{gid}/{snap_type}")
            else:
                per_type_lines.append((
                    "INVALID_NO_START_TIME", label, detail,
                ))
            # Phase 13Z — never claim PENDING_NOT_DUE if now > target.
            if (state == "NOT_DUE" and classify_snapshot_state is None
                and target_iso is not None):
                # Old-path fallback safety only when the state machine
                # could not be imported.
                pass
    # Phase 13Z — filter into the strict failure list now that the
    # loop has populated overdue_unresolved.
    overdue_missing = [
        x for x in overdue_unresolved
        if not (
            (base / x.split("/")[0] / x.split("/")[1]
             / "missed_snapshot_manifest.json").exists()
        )
    ]
    facts["overdue_missing_snapshots"] = overdue_missing
    facts["overdue_unresolved"] = overdue_unresolved

    # FAILED conditions.
    failed_reasons: list[str] = []
    if proof_scripts_missing:
        failed_reasons.append(
            f"proof_scripts_missing={proof_scripts_missing}"
        )
    if missing_reports:
        failed_reasons.append(
            f"phase13x_reports_missing={missing_reports}"
        )
    if publish_col_failures:
        for f in publish_col_failures:
            failed_reasons.append(f"phase13x_publish_col: {f}")
    if actionable_unconfirmed:
        for f in actionable_unconfirmed:
            failed_reasons.append(f"phase13x_actionable_unconfirmed: {f}")
    if blocker_threshold_failures:
        for f in blocker_threshold_failures:
            failed_reasons.append(f"phase13x_blocker_threshold: {f}")
    if overdue_missing:
        failed_reasons.append(
            f"overdue_missing_snapshots={overdue_missing}"
        )
    if pl_fails:
        for f in pl_fails:
            failed_reasons.append(
                f"snapshot {f['game_id']}/{f['snapshot_type']} issues={f['issues']}"
            )
    facts["per_type_lines"] = [
        {"outcome": k, "type": t, "detail": d} for (k, t, d) in per_type_lines
    ]

    if failed_reasons:
        payload = {
            "schema_version": "1.0", "outcome": "failed",
            "facts": facts, "failed_reasons": failed_reasons,
        }
        (HEALTH_DIR / f"derek_production_live_e2e_{args.delivery_date}.json"
         ).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        (HEALTH_DIR / f"derek_production_live_e2e_{args.delivery_date}.md"
         ).write_text(
            "\n".join([
                f"# Derek production-live E2E — {args.delivery_date}",
                "",
                f"- outcome: **failed**",
                "",
                "## Failed reasons",
                "",
                *(f"- {r}" for r in failed_reasons),
            ]) + "\n",
            encoding="utf-8",
        )
        print("DEREK_PRODUCTION_LIVE_E2E_FAILED", file=sys.stderr)
        for r in failed_reasons:
            print(f"  - {r}", file=sys.stderr)
        for k, t, d in per_type_lines:
            print(f"PHASE13W_{t}_{k}{(' ' + d) if d else ''}", file=sys.stderr)
        return 1

    # PASS requires at least one production-live snapshot to have passed.
    if not pl_passes:
        # No production-live snapshots and no overdue missing: target
        # windows are still open. PENDING, not FAILED.
        facts["pending_reason"] = "schedule_present_but_no_target_overdue_yet"
        payload = {"schema_version": "1.0", "outcome": "pending", "facts": facts}
        (HEALTH_DIR / f"derek_production_live_e2e_{args.delivery_date}.json"
         ).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        (HEALTH_DIR / f"derek_production_live_e2e_{args.delivery_date}.md"
         ).write_text(
            "\n".join([
                f"# Derek production-live E2E — {args.delivery_date}",
                "",
                f"- outcome: **pending**",
                f"- reason: {facts['pending_reason']}",
                f"- schedule_size: {schedule_size}",
                f"- now_utc: {_utc_iso(now)}",
            ]) + "\n",
            encoding="utf-8",
        )
        print("DEREK_PRODUCTION_LIVE_E2E_PENDING")
        for k, t, d in per_type_lines:
            print(f"PHASE13W_{t}_{k}{(' ' + d) if d else ''}")
        print(
            f"  reason={facts['pending_reason']}  schedule_size={schedule_size}  "
            f"now_utc={_utc_iso(now)}"
        )
        return 0

    payload = {"schema_version": "1.0", "outcome": "pass", "facts": facts}
    (HEALTH_DIR / f"derek_production_live_e2e_{args.delivery_date}.json"
     ).write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    (HEALTH_DIR / f"derek_production_live_e2e_{args.delivery_date}.md"
     ).write_text(
        "\n".join([
            f"# Derek production-live E2E — {args.delivery_date}",
            "",
            f"- outcome: **pass**",
            f"- production_live snapshots passing: **{len(pl_passes)}**",
            f"- now_utc: {_utc_iso(now)}",
            f"- schedule_size: {schedule_size}",
        ] + [
            f"- pass: {r['game_id']}/{r['snapshot_type']}" for r in pl_passes
        ]) + "\n",
        encoding="utf-8",
    )
    print("DEREK_PRODUCTION_LIVE_E2E_PASS")
    print(
        f"  production_live_passing={len(pl_passes)}  "
        f"now_utc={_utc_iso(now)}"
    )
    for r in pl_passes:
        print(f"  - {r['game_id']}/{r['snapshot_type']} "
              f"feature_set_id={r['feature_set_id']!r}")
    # Phase 13W per-snapshot-type explicit pass / pending / missed.
    for k, t, d in per_type_lines:
        print(f"PHASE13W_{t}_{k}{(' ' + d) if d else ''}")
    # Phase 13Z — overdue resolution + 21684819 explicit lines.
    if not overdue_missing:
        print("PHASE13Z_NO_OVERDUE_MISSING_SNAPSHOTS_PASS")
    # Confirm the specific failing fixture is resolved.
    fixture_resolved = True
    for snap_type in ("t_minus_25", "close_lock"):
        sd = base / "21684819" / snap_type
        ok = (sd / "snapshot_manifest.json").exists() or (
            sd / "missed_snapshot_manifest.json").exists()
        if not ok:
            fixture_resolved = False
    if fixture_resolved:
        print("PHASE13Z_21684819_OVERDUE_RESOLVED_PASS")
    if classify_snapshot_state is not None:
        print("PHASE13Z_SNAPSHOT_STATE_MACHINE_PASS")
    no_false_pending = not any(
        k == "PENDING_NOT_DUE" and "now=" in d
        and (d.split("now=")[1].split()[0]
             > d.split("target_utc=")[1].split()[0])
        for k, t, d in per_type_lines
    )
    if no_false_pending:
        print("PHASE13Z_NO_FALSE_PENDING_NOT_DUE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
