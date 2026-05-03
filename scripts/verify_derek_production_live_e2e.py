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

    # Compute "expected snapshots overdue but missing" — the strictest
    # FAILED signal: a game whose T-25 closed > grace_minutes ago and no
    # production-live snapshot exists at all.
    overdue_missing: list[str] = []
    for ev in schedule_eval:
        gid = ev["game_id"]
        for snap_type, overdue_key in (
            ("t_minus_25", "t25_overdue"),
            ("close_lock", "cl_overdue"),
        ):
            if not ev.get(overdue_key):
                continue
            sd = base / gid / snap_type
            if not (sd / "snapshot_manifest.json").exists():
                overdue_missing.append(f"{gid}/{snap_type}")
    facts["overdue_missing_snapshots"] = overdue_missing

    # FAILED conditions.
    failed_reasons: list[str] = []
    if overdue_missing:
        failed_reasons.append(
            f"overdue_missing_snapshots={overdue_missing}"
        )
    if pl_fails:
        for f in pl_fails:
            failed_reasons.append(
                f"snapshot {f['game_id']}/{f['snapshot_type']} issues={f['issues']}"
            )

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
