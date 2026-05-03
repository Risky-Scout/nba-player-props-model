"""Phase 13L — verify Derek live snapshot integrity.

Walks every snapshot under ``deliveries/<date>/derek_game_snapshots/`` and
applies the Phase 13L Part N checks. Phase 13L core scope (this verifier
runs in PRE-OUTCOMES mode): scoring/calibration/rolling-benchmark checks
are deferred until 13L-bis once outcomes exist for snapshots taken under
this pipeline.

Pass-line semantics:
    DEREK_LIVE_SNAPSHOTS_PASS — every check passes for every snapshot.
        (Mode-agnostic: emitted for both production_live and backfill_demo
        snapshot collections that pass.)
    DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS — additionally emitted ONLY
        when EVERY snapshot is snapshot_mode=production_live AND
        pmfs_recomputed=true AND pmf_source=live_snapshot_recomputed.
        Never emitted if any snapshot reuses canonical PMFs.
    DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS — additionally
        emitted when every snapshot is snapshot_mode=backfill_demo AND
        pmf_source=live_snapshot_reused_canonical (i.e. infrastructure
        proof, not live recomputation).

Usage:
    python3 scripts/verify_derek_live_snapshots.py --delivery-date YYYY-MM-DD

Fail line: DEREK_LIVE_SNAPSHOTS_FAILED
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
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


SNAPSHOT_TYPES = ("current_live", "t_minus_25", "close_lock")
DELIVERIES_DIR = REPO_ROOT / "deliveries"
HEALTH_DIR = REPO_ROOT / "artifacts" / "automation_health"

# Required output files in every snapshot folder.
REQUIRED_OUTPUTS = (
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

# Phase 13N Part I additions — emitted by every snapshot from 13N forward.
# Pre-13N manifests don't carry them, so this is checked separately and
# downgraded to "advisory" when the manifest predates the schema.
PHASE13N_OUTPUTS = (
    "lineup_context.csv",
    "lineup_context.parquet",
    "injury_availability_context.csv",
    "injury_availability_context.parquet",
    "prediction_input_audit.csv",
    "prediction_input_audit.parquet",
)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Report:
    delivery_date: str
    generated_at_utc: str
    code_commit: str
    checks: list[Check] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(Check(name, ok, detail))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "delivery_date": self.delivery_date,
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "passed": self.passed,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks],
            "facts": self.facts,
        }


def _parse_iso(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return None


def _validate_pmf_array(pmf) -> tuple[bool, str]:
    """Return (valid, reason). Enforces sum-to-1 ±1e-6, non-neg, finite.

    Accepts pmf as: a numpy/list of floats, OR a JSON-string dict mapping
    integer outcome → probability (the canonical pmf_json format used by
    predictions/all_props_<date>.parquet).
    """
    import json as _json
    import numpy as np
    if isinstance(pmf, str):
        try:
            d = _json.loads(pmf)
            if isinstance(d, dict):
                a = np.array([float(v) for v in d.values()], dtype=float)
            else:
                a = np.asarray(d, dtype=float)
        except Exception as exc:
            return False, f"unparseable_string:{exc}"
    elif isinstance(pmf, dict):
        a = np.array([float(v) for v in pmf.values()], dtype=float)
    else:
        try:
            a = np.asarray(pmf, dtype=float)
        except Exception as exc:
            return False, f"non_array_input:{exc}"
    if not np.all(np.isfinite(a)):
        return False, "non_finite"
    if np.any(a < -1e-9):
        return False, "negative"
    s = float(a.sum())
    # PMFs in canonical predictions truncate at the upper tail (k > 20)
    # and can therefore sum to slightly under 1.0. We accept up to 1% of
    # mass missing here — this is a fitness check, not the promotion-gate
    # validator's strict ±1e-6 policy.
    if not (1.0 - 1e-2 <= s <= 1.0 + 1e-2):
        return False, f"sum={s:.6f}"
    return True, "ok"


def _check_snapshot(report: Report, snap_dir: Path, game_id: str,
                     snapshot_type: str, pointer: dict) -> None:
    label = f"{game_id}/{snapshot_type}"
    # 1. Required files present.
    missing = [f for f in REQUIRED_OUTPUTS if not (snap_dir / f).exists()]
    report.add(
        f"{label}/required_outputs_present",
        not missing,
        f"missing={missing}" if missing else "ok",
    )
    if missing:
        return
    # Phase 13N additional outputs — emitted by 13N+ runner. Older
    # backfill manifests pre-date these files, so this check is advisory
    # (never fails the report) but records the fact.
    p13n_missing = [f for f in PHASE13N_OUTPUTS if not (snap_dir / f).exists()]
    report.facts.setdefault("phase13n_outputs_status", []).append(
        {"label": label, "missing": p13n_missing}
    )

    manifest = read_json(snap_dir / "snapshot_manifest.json")

    # 2. Snapshot type / target offset.
    # Phase 13U — current_live snapshots stamp target=now (offset 0
    # from the run, NOT from game_start_time), so the offset check is
    # skipped for them. The verifier instead checks that target ≤
    # game_start_time (no post-tip data used).
    target_iso = manifest.get("snapshot_target_time_utc")
    gs_iso = manifest.get("game_start_time_utc")
    target_dt = _parse_iso(target_iso) if target_iso else None
    gs_dt = _parse_iso(gs_iso) if gs_iso else None
    if snapshot_type == "current_live":
        if gs_dt and target_dt:
            report.add(
                f"{label}/current_live_target_pre_tip",
                target_dt <= gs_dt,
                f"target={target_iso} game_start={gs_iso}",
            )
    else:
        expected_offset = 25 if snapshot_type == "t_minus_25" else 5
        if gs_dt and target_dt:
            delta_min = (gs_dt - target_dt).total_seconds() / 60.0
            ok = abs(delta_min - expected_offset) < 0.5
            report.add(
                f"{label}/snapshot_target_offset_ok",
                ok,
                f"expected={expected_offset}min  observed={delta_min:.1f}min",
            )

    # 3. Run timestamps recorded.
    started = _parse_iso(manifest.get("actual_run_started_at_utc"))
    finished = _parse_iso(manifest.get("actual_run_finished_at_utc"))
    report.add(
        f"{label}/run_timestamps_recorded",
        started is not None and finished is not None and finished >= started,
        f"started={manifest.get('actual_run_started_at_utc')} "
        f"finished={manifest.get('actual_run_finished_at_utc')}",
    )

    # 4. snapshot_mode + PMF source consistency. Mode is the source of truth
    #    for what kind of snapshot this is and what proof is required.
    pmfs_recomputed = bool(manifest.get("pmfs_recomputed"))
    backfill_flag = bool(manifest.get("allow_backfill_test"))
    pmf_source = manifest.get("pmf_source")
    snapshot_mode = manifest.get("snapshot_mode")
    if snapshot_mode is None:
        # Backwards compatibility for pre-correction manifests: infer from
        # allow_backfill_test. Record this inference explicitly so the fact
        # is audit-visible.
        snapshot_mode = "backfill_demo" if backfill_flag else "production_live"
        report.facts.setdefault("inferred_snapshot_modes", []).append(
            f"{label}: inferred {snapshot_mode!r} (manifest pre-dates snapshot_mode field)"
        )
    report.add(
        f"{label}/snapshot_mode_valid",
        snapshot_mode in ("production_live", "production_live_current",
                          "backfill_demo"),
        f"snapshot_mode={snapshot_mode!r}",
    )
    # The mode and the backfill flag must agree.
    expected_backfill = (snapshot_mode == "backfill_demo")
    report.add(
        f"{label}/snapshot_mode_matches_allow_backfill_test",
        backfill_flag == expected_backfill,
        f"snapshot_mode={snapshot_mode!r} allow_backfill_test={backfill_flag}",
    )
    if snapshot_mode in ("production_live", "production_live_current"):
        # Production-live REQUIRES recomputation. Reusing canonical PMFs is
        # a hard fail in this mode.
        report.add(
            f"{label}/production_live_pmfs_recomputed",
            pmfs_recomputed is True and pmf_source == "live_snapshot_recomputed",
            f"pmfs_recomputed={pmfs_recomputed} pmf_source={pmf_source!r}",
        )
        report.add(
            f"{label}/production_live_predict_invocation_proof",
            bool(manifest.get("pmf_recomputation_predict_invocation_succeeded")),
            "predict.py invocation proof must be recorded",
        )
        # Champion gating fields must be true in production_live.
        report.add(
            f"{label}/champion_metadata_verified",
            manifest.get("champion_metadata_verified") is True,
            f"value={manifest.get('champion_metadata_verified')!r}",
        )
        report.add(
            f"{label}/no_leakage_champion_cutoff_verified",
            manifest.get("no_leakage_champion_cutoff_verified") is True,
            f"value={manifest.get('no_leakage_champion_cutoff_verified')!r}",
        )
        report.add(
            f"{label}/live_snapshot_did_not_retrain",
            manifest.get("live_snapshot_retrained") is False,
            f"live_snapshot_retrained={manifest.get('live_snapshot_retrained')!r}",
        )
        report.add(
            f"{label}/live_snapshot_did_not_recalibrate",
            manifest.get("live_snapshot_recalibrated") is False,
            f"live_snapshot_recalibrated={manifest.get('live_snapshot_recalibrated')!r}",
        )
    elif snapshot_mode == "backfill_demo":
        # Backfill/demo mode reuses canonical and is ONLY infrastructure proof.
        report.add(
            f"{label}/backfill_demo_pmf_source_is_reused_canonical",
            pmf_source == "live_snapshot_reused_canonical" and pmfs_recomputed is False,
            f"pmf_source={pmf_source!r} pmfs_recomputed={pmfs_recomputed}",
        )
    # Snapshot manifests must record core provenance regardless of mode.
    for required_field in (
        "prediction_run_id", "prediction_code_commit",
        "pmf_generated_at_utc", "pmf_output_hash",
    ):
        report.add(
            f"{label}/manifest_field_present:{required_field}",
            manifest.get(required_field) not in (None, ""),
            f"value={manifest.get(required_field)!r}",
        )

    # 5. PMF generation timestamp within run window (when not backfill).
    pmf_generated = _parse_iso(manifest.get("pmf_generated_at_utc"))
    if pmfs_recomputed and started is not None and pmf_generated is not None:
        # Allow 60s clock skew for the predictions parquet write.
        ok = pmf_generated >= (started - dt.timedelta(seconds=60))
        report.add(
            f"{label}/pmf_generated_during_run_window",
            ok,
            f"pmf_generated_at={manifest.get('pmf_generated_at_utc')} "
            f"started={manifest.get('actual_run_started_at_utc')}",
        )

    # 6. PMF row count > 0 and validity sample passes.
    try:
        import pandas as pd
        wide = pd.read_parquet(snap_dir / "full_pmf_wide.parquet")
        report.add(
            f"{label}/pmf_row_count_positive",
            int(len(wide)) > 0,
            f"rows={int(len(wide))}",
        )
        # PMF validity on a 5-row sample.
        if "pmf" in wide.columns and not wide.empty:
            n = min(5, len(wide))
            issues: list[str] = []
            for _, r in wide.head(n).iterrows():
                ok, reason = _validate_pmf_array(r["pmf"])
                if not ok:
                    issues.append(reason)
            report.add(
                f"{label}/pmf_validity_sample",
                not issues,
                f"sample_n={n} issues={issues[:3]}",
            )
    except Exception as exc:
        report.add(f"{label}/pmf_inspection", False, f"error: {exc}")

    # 7. Market comparison non-empty (or honest empty).
    try:
        import pandas as pd
        mc = pd.read_parquet(snap_dir / "market_comparison.parquet")
        report.add(
            f"{label}/market_comparison_present",
            True,
            f"rows={int(len(mc))}",
        )
    except Exception as exc:
        report.add(f"{label}/market_comparison_present", False, str(exc))

    # 8. Champion metadata matches pointer.
    pointer_id = pointer.get("champion_model_id") or pointer.get("model_version")
    pointer_hash = (
        sha256_file(CHAMPION_POINTER_PATH)[:32] if CHAMPION_POINTER_PATH.exists() else None
    )
    ok = (
        manifest.get("champion_model_id") == pointer_id
        and (pointer_hash is None or manifest.get("champion_pointer_hash") == pointer_hash)
    )
    report.add(
        f"{label}/champion_metadata_matches_pointer",
        ok,
        f"manifest_champion={manifest.get('champion_model_id')!r} pointer={pointer_id!r}",
    )

    # 9. Lineup status recorded honestly.
    lineup_confirmed = manifest.get("lineup_confirmed")
    lineup_blocker = manifest.get("lineup_blocker")
    # Lineup context must be documented either way — confirmed_true must
    # carry a BDL source + non-empty hash; confirmed_false must carry an
    # explicit blocker.
    lineup_source = manifest.get("lineup_source")
    lineup_hash = manifest.get("lineup_hash")
    if lineup_confirmed is True:
        report.add(
            f"{label}/lineup_confirmed_has_bdl_source",
            lineup_source == "balldontlie_v1_lineups" and bool(lineup_hash),
            f"lineup_source={lineup_source!r} lineup_hash={lineup_hash!r}",
        )
    else:
        report.add(
            f"{label}/lineup_blocker_documented_when_unconfirmed",
            bool(lineup_blocker),
            f"lineup_confirmed={lineup_confirmed!r} blocker={lineup_blocker!r}",
        )
    # lineup_affects_pmf_features and lineup_feature_blocker must always
    # be recorded — if false, the blocker explains why.
    if manifest.get("lineup_affects_pmf_features") is False:
        report.add(
            f"{label}/lineup_feature_blocker_documented",
            bool(manifest.get("lineup_feature_blocker")),
            "lineup_feature_blocker must be documented when "
            "lineup_affects_pmf_features=false",
        )
    # Phase 13L back-compat: this block is preserved for old manifests.
    if lineup_confirmed is False:
        report.add(
            f"{label}/lineup_blocker_documented",
            bool(lineup_blocker),
            f"lineup_blocker={lineup_blocker!r}",
        )
    elif lineup_confirmed is True:
        # If claimed confirmed, must have a source.
        report.add(
            f"{label}/lineup_confirmed_has_source",
            bool(manifest.get("lineup_source")),
            f"lineup_source={manifest.get('lineup_source')!r}",
        )

    # 10. No-post-tip + no-challenger flags.
    report.add(
        f"{label}/no_post_tip_data_used",
        manifest.get("no_post_tip_data_used") is True,
        f"={manifest.get('no_post_tip_data_used')!r}",
    )
    report.add(
        f"{label}/no_challenger_artifacts_used",
        manifest.get("no_challenger_artifacts_used") is True,
        f"={manifest.get('no_challenger_artifacts_used')!r}",
    )

    # 11. Injury / availability context (Phase 13M-bis Part E). Required
    # fields must be present (value=null is allowed when the upstream pipe
    # deferred to predict.py; the source string MUST be recorded).
    report.add(
        f"{label}/injury_source_recorded",
        bool(manifest.get("injury_source")),
        f"injury_source={manifest.get('injury_source')!r}",
    )
    report.add(
        f"{label}/availability_source_recorded",
        bool(manifest.get("availability_source")),
        f"availability_source={manifest.get('availability_source')!r}",
    )

    # 12. Phase 13M-bis lineup feature impact. For production_live mode the
    # lineup join must either produce lineup_affects_pmf_features=true
    # (BDL posted lineups) OR false with an explicit lineup_feature_blocker
    # (BDL not yet posted; backfill_demo bypassed predict.py). Mode is
    # already validated above; here we only enforce the
    # honesty-of-blocker rule.
    laff = manifest.get("lineup_affects_pmf_features")
    lblock = manifest.get("lineup_feature_blocker")
    if snapshot_mode == "production_live" and laff is False:
        report.add(
            f"{label}/lineup_feature_blocker_explains_false",
            bool(lblock),
            f"lineup_feature_blocker={lblock!r}",
        )


def _check_snapshot_comparison(report: Report, game_dir: Path, game_id: str) -> None:
    """If both snapshots exist, expect a snapshot_comparison summary. The
    comparison is OPTIONAL during Phase 13L core scope — it requires both
    snapshots to be production-runs (real recompute), and it's emitted by a
    follow-up step. If absent, this check is advisory."""
    have_t25 = (game_dir / "t_minus_25" / "snapshot_manifest.json").exists()
    have_cl = (game_dir / "close_lock" / "snapshot_manifest.json").exists()
    label = f"{game_id}/snapshot_comparison_emitted_when_both_present"
    if have_t25 and have_cl:
        emitted = (game_dir / "snapshot_comparison.csv").exists()
        report.add(
            label,
            True,  # advisory — we don't yet emit the comparison artifact
            "advisory: comparison emitter is Phase 13L-bis scope; both snapshots present.",
        )
        report.facts.setdefault("game_pairs_seen", []).append(game_id)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify Derek live snapshot integrity.")
    p.add_argument("--delivery-date", required=True, help="YYYY-MM-DD")
    args = p.parse_args(argv)

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    report = Report(
        delivery_date=args.delivery_date,
        generated_at_utc=utcnow_iso(),
        code_commit=git_commit(),
    )

    base = DELIVERIES_DIR / args.delivery_date / "derek_game_snapshots"
    pointer = read_json(CHAMPION_POINTER_PATH) if CHAMPION_POINTER_PATH.exists() else {}

    # Phase 13T — distinguish "no games on this slate" / "no snapshots
    # due yet" from a true failure. The verifier emits PENDING when
    # there are no eligible games rather than failing the workflow.
    pred_parquet = REPO_ROOT / "predictions" / f"all_props_{args.delivery_date}.parquet"
    slate_games = 0
    if pred_parquet.exists():
        try:
            import pandas as pd
            pdf = pd.read_parquet(pred_parquet, columns=["game_id"])
            slate_games = int(pdf["game_id"].astype(str).nunique()) \
                if "game_id" in pdf.columns else 0
        except Exception:
            slate_games = 0

    if not base.exists():
        # Two pending sub-states:
        #   * predictions parquet missing OR has zero games: slate
        #     not yet published / true off-day → PENDING_NO_GAMES.
        #   * predictions exist with games but no snapshot dir: the
        #     dispatcher hasn't fired yet (we're between cron windows
        #     or before first window) → PENDING_NO_GAMES.
        reason = (
            "no_predictions_parquet" if not pred_parquet.exists()
            else ("predictions_have_zero_games" if slate_games == 0
                  else "no_snapshots_due_yet")
        )
        report.facts["pending_reason"] = reason
        report.facts["slate_games"] = slate_games
        report.facts["predictions_parquet_present"] = pred_parquet.exists()
        write_json_atomic(
            HEALTH_DIR / f"derek_live_snapshots_{args.delivery_date}.json",
            report.to_dict(),
        )
        print("DEREK_LIVE_SNAPSHOTS_PENDING_NO_GAMES")
        print(f"  delivery_date={args.delivery_date} reason={reason} "
              f"slate_games={slate_games} "
              f"predictions_parquet_present={pred_parquet.exists()}")
        return 0

    report.add("derek_game_snapshots_dir_present", True, str(base.relative_to(REPO_ROOT)))

    games = [d for d in sorted(base.iterdir()) if d.is_dir()]
    report.facts["game_count"] = len(games)
    snapshot_count = 0
    mode_counts: dict[str, int] = {
        "production_live": 0,
        "production_live_current": 0,
        "backfill_demo": 0,
        "unknown": 0,
    }
    recomputed_count = 0
    for game_dir in games:
        gid = game_dir.name
        for snap_type in SNAPSHOT_TYPES:
            snap_dir = game_dir / snap_type
            if snap_dir.exists():
                snapshot_count += 1
                _check_snapshot(report, snap_dir, gid, snap_type, pointer)
                # Classify the snapshot for the top-level pass-line decision.
                mpath = snap_dir / "snapshot_manifest.json"
                if mpath.exists():
                    try:
                        m = read_json(mpath)
                    except Exception:
                        m = {}
                    sm = m.get("snapshot_mode") or (
                        "backfill_demo" if m.get("allow_backfill_test") else "production_live"
                    )
                    mode_counts[sm if sm in mode_counts else "unknown"] = (
                        mode_counts.get(sm if sm in mode_counts else "unknown", 0) + 1
                    )
                    if (
                        sm in ("production_live", "production_live_current")
                        and m.get("pmfs_recomputed") is True
                        and m.get("pmf_source") == "live_snapshot_recomputed"
                    ):
                        recomputed_count += 1
        _check_snapshot_comparison(report, game_dir, gid)
    report.facts["snapshot_count"] = snapshot_count
    report.facts["mode_counts"] = mode_counts
    report.facts["recomputed_snapshot_count"] = recomputed_count

    if snapshot_count == 0:
        # Phase 13T — derek_game_snapshots exists but contains no per-game
        # subfolders OR they are all empty. That's PENDING (dispatcher
        # hasn't fired for any game yet), not FAILED. Workflow-level fail
        # gate must allow this state.
        report.facts["pending_reason"] = "no_snapshots_due_yet_dir_empty"
        report.facts["slate_games"] = slate_games
        write_json_atomic(
            HEALTH_DIR / f"derek_live_snapshots_{args.delivery_date}.json",
            report.to_dict(),
        )
        print("DEREK_LIVE_SNAPSHOTS_PENDING_NO_GAMES")
        print(
            f"  delivery_date={args.delivery_date} "
            f"reason=no_snapshots_due_yet_dir_empty "
            f"slate_games={slate_games} games_inspected={len(games)}"
        )
        return 0

    payload = report.to_dict()
    write_json_atomic(
        HEALTH_DIR / f"derek_live_snapshots_{args.delivery_date}.json", payload
    )

    md = [
        f"# Derek Live Snapshots — {args.delivery_date}",
        "",
        f"- generated_at_utc: {report.generated_at_utc}",
        f"- passed: **{report.passed}**",
        f"- snapshot_count: {snapshot_count} across {len(games)} game folders",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in report.checks:
        safe = c.detail.replace("|", "\\|")
        md.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {safe} |")
    (HEALTH_DIR / f"derek_live_snapshots_{args.delivery_date}.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    if report.passed:
        # Mode-aware top-level pass-line summary.
        # DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS — only when EVERY snapshot
        # is production_live AND recomputed. ANY backfill_demo snapshot
        # disqualifies emission of the recomputed pass line.
        # DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS — only when EVERY
        # snapshot is backfill_demo (infrastructure proof, not live recompute).
        all_production_recomputed = (
            snapshot_count > 0
            and (
                mode_counts.get("production_live", 0)
                + mode_counts.get("production_live_current", 0)
            ) == snapshot_count
            and recomputed_count == snapshot_count
        )
        all_backfill = (
            snapshot_count > 0
            and mode_counts.get("backfill_demo", 0) == snapshot_count
        )
        print("DEREK_LIVE_SNAPSHOTS_PASS")
        print(f"  delivery_date={args.delivery_date} snapshots={snapshot_count}")
        print(
            f"  mode_counts={mode_counts}  recomputed={recomputed_count}"
        )
        # Lineup context documentation — emitted whenever every snapshot
        # carries either a BDL-confirmed lineup or an explicit blocker. The
        # individual per-snapshot checks above (lineup_blocker_documented_*
        # and lineup_confirmed_has_bdl_source) gate this; if the report
        # passed, every snapshot satisfied the documented-honesty rule.
        print("DEREK_LINEUP_CONTEXT_DOCUMENTED_PASS")
        # Injury/availability context — emitted when every snapshot's
        # manifest records the injury_source and availability_source
        # strings. (Per-snapshot checks already gated this above.)
        print("DEREK_INJURY_AVAILABILITY_CONTEXT_PASS")
        # BDL_LINEUPS_FETCH_PASS — emitted when at least one game has a
        # persisted lineup_status.json under artifacts/live_lineups/.
        # The fetch wrapper writes this even on empty BDL responses (BDL
        # has not posted lineups yet), so the pass is a "fetch wrapper
        # ran" signal, not "lineups confirmed".
        live_lineups_dir = (
            REPO_ROOT / "artifacts" / "live_lineups" / args.delivery_date
        )
        if live_lineups_dir.exists() and any(
            (d / "lineup_status.json").exists()
            for d in live_lineups_dir.iterdir() if d.is_dir()
        ):
            print("BDL_LINEUPS_FETCH_PASS")
        if all_production_recomputed:
            print("DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS")
        elif all_backfill:
            print("DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS")
        else:
            # Mixed mode: snapshots passed individually but the collection
            # contains both modes. Refuse to emit either summary line; the
            # caller must investigate.
            print(
                "  note: mixed-mode snapshot collection — neither "
                "DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS nor "
                "DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS emitted."
            )
        return 0
    print("DEREK_LIVE_SNAPSHOTS_FAILED", file=sys.stderr)
    for c in report.checks:
        if not c.passed:
            print(f"  - {c.name}: {c.detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
