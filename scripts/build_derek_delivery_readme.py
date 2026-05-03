"""Phase 13W Part F — generate Derek-facing README files.

Writes:
    deliveries/<date>/README.md
    deliveries/<date>/derek_game_snapshots/README.md

Both READMEs are auto-generated from the existing snapshot folders +
manifests, so they stay in sync with what was actually emitted.

Pass line:  PHASE13W_DEREK_GITHUB_INDEX_PASS
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _utcnow_iso() -> str:
    return (dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0).isoformat() + "Z")


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    base = REPO_ROOT / "deliveries" / args.delivery_date
    derek = base / "derek_game_snapshots"
    if not derek.exists():
        print("PHASE13W_DEREK_GITHUB_INDEX_PENDING", file=sys.stderr)
        print(
            f"  reason=no derek_game_snapshots dir under deliveries/"
            f"{args.delivery_date}",
            file=sys.stderr,
        )
        return 0

    # Collect per-game manifest summaries. Phase 13Z — also resolve
    # per-(game, snapshot_type) state via the shared state machine so
    # the README shows explicit status (available / pending_not_due /
    # late_but_pre_tip / missed_post_tip / blocked).
    import datetime as _dt
    try:
        from nba_props_model.derek import classify_snapshot_state
    except Exception:
        classify_snapshot_state = None
    now = _dt.datetime.now(_dt.timezone.utc)

    games: list[dict] = []
    for game_dir in sorted(derek.iterdir()):
        if not game_dir.is_dir():
            continue
        per_game: dict = {"game_id": game_dir.name, "types": {}}
        # Try to resolve game_start_time from any present manifest.
        gs_iso = None
        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            mp = game_dir / snap_type / "snapshot_manifest.json"
            mm = game_dir / snap_type / "missed_snapshot_manifest.json"
            for cand in (mp, mm):
                if cand.exists():
                    try:
                        m = json.loads(cand.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    gs_iso = (
                        m.get("game_start_time_utc")
                        or m.get("game_start_time")
                    )
                    if gs_iso:
                        break
            if gs_iso:
                break

        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            sd = game_dir / snap_type
            mp = sd / "snapshot_manifest.json"
            mm = sd / "missed_snapshot_manifest.json"
            if mp.exists():
                try:
                    m = json.loads(mp.read_text(encoding="utf-8"))
                except Exception:
                    m = {}
                actual_run_late = m.get("actual_run_late") or False
                late_seconds = m.get("late_seconds") or 0
                status = (
                    "late_but_pre_tip" if actual_run_late else "available"
                )
                per_game["types"][snap_type] = {
                    "snapshot_mode": m.get("snapshot_mode"),
                    "lineup_confirmed": m.get("lineup_confirmed"),
                    "BDL_lineup_fetch_status": m.get("BDL_lineup_fetch_status"),
                    "BDL_injury_fetch_status": m.get("BDL_injury_fetch_status"),
                    "pmfs_recomputed": m.get("pmfs_recomputed"),
                    "feature_set_id": m.get("feature_set_id"),
                    "props_emitted": m.get("props_emitted"),
                    "game_start_time_utc": m.get("game_start_time_utc"),
                    "status": status,
                    "actual_run_late": actual_run_late,
                    "late_seconds": late_seconds,
                }
                continue
            if mm.exists():
                try:
                    m = json.loads(mm.read_text(encoding="utf-8"))
                except Exception:
                    m = {}
                per_game["types"][snap_type] = {
                    "status": "missed_post_tip",
                    "missed_reason": m.get("missed_reason"),
                    "snapshot_target_time_utc": m.get("snapshot_target_time_utc"),
                    "game_start_time_utc": m.get("game_start_time_utc"),
                    "no_fake_pretip_snapshot": m.get("no_fake_pretip_snapshot"),
                }
                continue
            # Neither present — derive state from the state machine.
            if classify_snapshot_state is not None and gs_iso:
                sr = classify_snapshot_state(
                    now_utc=now,
                    game_start_time_utc=gs_iso,
                    snapshot_type=snap_type,
                    snapshot_exists=False,
                )
                target_iso = (
                    sr.target_time_utc.replace(microsecond=0)
                    .isoformat().replace("+00:00", "Z")
                    if sr.target_time_utc else None
                )
                if sr.state == "NOT_DUE":
                    per_game["types"][snap_type] = {
                        "status": "pending_not_due",
                        "snapshot_target_time_utc": target_iso,
                    }
                elif sr.state == "DUE_WINDOW":
                    per_game["types"][snap_type] = {
                        "status": "due_window_pending_dispatch",
                        "snapshot_target_time_utc": target_iso,
                    }
                elif sr.state == "LATE_BUT_PRE_TIP":
                    per_game["types"][snap_type] = {
                        "status": "late_but_pre_tip_pending_dispatch",
                        "snapshot_target_time_utc": target_iso,
                    }
                elif sr.state == "MISSED_POST_TIP":
                    per_game["types"][snap_type] = {
                        "status": "missed_post_tip_no_marker",
                        "snapshot_target_time_utc": target_iso,
                    }
                else:
                    per_game["types"][snap_type] = {
                        "status": "blocked_invalid_no_start_time",
                    }
            else:
                per_game["types"][snap_type] = {"status": "blocked_no_state"}
        games.append(per_game)

    # ── deliveries/<date>/README.md ─────────────────────────────────
    readme = [
        f"# Derek delivery — {args.delivery_date}",
        "",
        f"- generated_at_utc: {_utcnow_iso()}",
        f"- delivery_date: **{args.delivery_date}**",
        f"- games: **{len(games)}**",
        "",
        "## ⚠️ Read this first — current_live is a watchlist baseline",
        "",
        "The **current_live** package is an early baseline / watchlist "
        "package. Because BDL did not return confirmed lineup rows at "
        "this timestamp, **current_live edges are not labeled as "
        "confirmed-lineup recommendations**. The **T-minus-25** and "
        "**close-lock** snapshots are the near-tip packages intended "
        "for confirmed-lineup evaluation; they fire automatically "
        "inside their per-game windows.",
        "",
        "Every Derek market_comparison row carries an "
        "`edge_publish_status` column — values include "
        "`PUBLISH_BLOCKER`, `REVIEW_LARGE_EDGE`, `REVIEW_PUSH_LINE`, "
        "`WATCHLIST_NOT_CONFIRMED_LINEUP`, `ACTIONABLE_REVIEWED`. "
        "Calibration support per (stat / side / line / edge bucket) is "
        "captured in `calibration_support_status` and "
        "`calibration_bucket_n`.",
        "",
        "## Phase 13X audit reports",
        "",
        f"- [Edge root-cause audit]"
        f"(../../artifacts/automation_health/derek_edge_root_cause_"
        f"{args.delivery_date}.md)",
        f"- [Edge calibration audit]"
        f"(../../artifacts/automation_health/derek_edge_calibration_"
        f"{args.delivery_date}.md)",
        "",
        "## What's in this delivery",
        "",
        "Per-game live snapshot folders under "
        "`derek_game_snapshots/<game_id>/<snapshot_type>/` containing:",
        "",
        "- `snapshot_manifest.json` — full provenance (champion, BDL fetch, "
        "no-leakage flags, market-odds invariants).",
        "- `snapshot_report.md` — human-readable executive summary, top "
        "edges, top deltas, driver explanation.",
        "- `prop_summary.{csv,parquet}` — slim per-prop view.",
        "- `full_pmf_wide.{csv,parquet}` — full per-prop PMF + market.",
        "- `outcome_level_probabilities.{csv,parquet}` — long-form k → p_k.",
        "- `market_comparison.{csv,parquet}` — model probs vs market probs.",
        "- `lineup_context.{csv,parquet}` — BDL lineup fields per player.",
        "- `injury_availability_context.{csv,parquet}` — injury / actionability.",
        "- `game_context.{csv,parquet}` — schedule / rest / opponent.",
        "- `contextual_feature_audit.{csv,parquet}` — per-row contextual features.",
        "- `prediction_input_audit.{csv,parquet}` — prediction frame audit trail.",
        "- `pmf_driver_decomposition.{csv,parquet,md}` — per-row contextual deltas.",
        "- `lineup_injury_impact_report.{json,md}` — lineup + injury impact summary.",
        "- `direct_lineup_impact_report.{json,md}` — Phase 13S direct-lineup driver attribution.",
        "- `input_change_report.{json,md}` — diff vs prior snapshot when present.",
        "- `snapshot_comparison.{csv,parquet,md}` — close-lock vs t_minus_25 comparison.",
        "",
        "## Snapshot type meanings",
        "",
        "- `current_live` — best-available pre-tip baseline. Generated any "
        "time the workflow runs while at least one game has not tipped. "
        "Uses the canonical predictions slate + the Phase 13S contextual "
        "engine. May be lineup-confirmed or baseline (BDL lineups not yet "
        "posted).",
        "- `t_minus_25` — production-live snapshot taken ~25 minutes before "
        "game tip. The dispatcher fires this exactly inside the per-game "
        "window.",
        "- `close_lock` — production-live snapshot ~5 minutes before tip. "
        "The dispatcher fires this inside the per-game window.",
        "",
        "## Per-game status",
        "",
    ]

    for g in games:
        readme.append(f"### Game {g['game_id']}")
        readme.append("")
        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            data = g["types"].get(snap_type) or {}
            base_dir = f"derek_game_snapshots/{g['game_id']}/{snap_type}"
            status = data.get("status") or "unknown"
            if status in ("available", "late_but_pre_tip"):
                tip = data.get("game_start_time_utc")
                late_note = (
                    f", actual_run_late=**True** ({data.get('late_seconds')}s late)"
                    if status == "late_but_pre_tip" else ""
                )
                readme.append(
                    f"- **{snap_type}**: status=**{status}**, "
                    f"snapshot_mode=`{data.get('snapshot_mode')}`, "
                    f"lineup_confirmed=**{data.get('lineup_confirmed')}**, "
                    f"pmfs_recomputed=**{data.get('pmfs_recomputed')}**, "
                    f"props_emitted={data.get('props_emitted')}, "
                    f"feature_set_id=`{data.get('feature_set_id')}`, "
                    f"game_start_time_utc=`{tip}`{late_note}"
                )
                readme.append(
                    f"  - [snapshot_report.md]({base_dir}/snapshot_report.md)"
                )
                readme.append(f"  - [prop_summary.csv]({base_dir}/prop_summary.csv)")
                readme.append(f"  - [full_pmf_wide.csv]({base_dir}/full_pmf_wide.csv)")
                readme.append(
                    f"  - [outcome_level_probabilities.csv]({base_dir}/outcome_level_probabilities.csv)"
                )
                readme.append(f"  - [market_comparison.csv]({base_dir}/market_comparison.csv)")
                readme.append(
                    f"  - [pmf_driver_decomposition.md]({base_dir}/pmf_driver_decomposition.md)"
                )
                readme.append(
                    f"  - [lineup_injury_impact_report.md]({base_dir}/lineup_injury_impact_report.md)"
                )
                readme.append(
                    f"  - [direct_lineup_impact_report.md]({base_dir}/direct_lineup_impact_report.md)"
                )
            elif status == "pending_not_due":
                readme.append(
                    f"- **{snap_type}**: status=**pending_not_due**, "
                    f"snapshot_target_time_utc="
                    f"`{data.get('snapshot_target_time_utc')}` (will fire "
                    "automatically inside the cron window)"
                )
            elif status in ("due_window_pending_dispatch",
                            "late_but_pre_tip_pending_dispatch"):
                readme.append(
                    f"- **{snap_type}**: status=**{status}**, "
                    f"snapshot_target_time_utc="
                    f"`{data.get('snapshot_target_time_utc')}` "
                    "(next dispatcher run will generate)"
                )
            elif status == "missed_post_tip":
                readme.append(
                    f"- **{snap_type}**: status=**missed_post_tip**, "
                    f"snapshot_target_time_utc="
                    f"`{data.get('snapshot_target_time_utc')}`, "
                    f"game_start_time_utc=`{data.get('game_start_time_utc')}`, "
                    f"missed_reason=`{data.get('missed_reason')}`, "
                    "no_fake_pretip_snapshot=**True**"
                )
                readme.append(
                    f"  - [missed_snapshot_report.md]({base_dir}/missed_snapshot_report.md)"
                )
                readme.append(
                    f"  - [missed_snapshot_manifest.json]({base_dir}/missed_snapshot_manifest.json)"
                )
            elif status == "missed_post_tip_no_marker":
                readme.append(
                    f"- **{snap_type}**: status=**missed_post_tip_no_marker** "
                    "(dispatcher will write the marker on next firing)"
                )
            else:
                readme.append(
                    f"- **{snap_type}**: status=**{status}**"
                )
        readme.append("")

    readme.append("## Daily model report")
    readme.append("")
    readme.append(
        "The daily model training / recalibration report — what was "
        "trained, recalibrated, validated, and promoted — is in:"
    )
    readme.append("")
    readme.append(
        "`artifacts/model_daily_reports/<trained_through_date>/daily_model_training_report.md`"
    )
    readme.append("")
    readme.append("## Aggregate scoring")
    readme.append("")
    readme.append(
        "Snapshot scoring summaries (when realized outcomes are available) "
        "are in:"
    )
    readme.append("")
    readme.append(
        f"`artifacts/automation_health/derek_live_snapshots_{args.delivery_date}.{{json,md}}`"
    )
    readme.append("")

    base.mkdir(parents=True, exist_ok=True)
    (base / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    # ── derek_game_snapshots/README.md ──────────────────────────────
    snap_readme = [
        f"# Derek game snapshots — {args.delivery_date}",
        "",
        f"- generated_at_utc: {_utcnow_iso()}",
        f"- games: **{len(games)}**",
        "",
        "Each subfolder is `<game_id>/<snapshot_type>/` and contains the "
        "full Phase 13S contextual snapshot fileset. See the parent "
        "[delivery README](../README.md) for snapshot-type definitions.",
        "",
        "## Index",
        "",
        "| game_id | current_live | t_minus_25 | close_lock |",
        "| --- | --- | --- | --- |",
    ]
    for g in games:
        cells: list[str] = []
        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            data = g["types"].get(snap_type) or {}
            status = data.get("status") or "unknown"
            if status in ("available", "late_but_pre_tip"):
                lc = "**confirmed**" if data.get("lineup_confirmed") else "baseline"
                pmfs = "✓" if data.get("pmfs_recomputed") else "—"
                tag = "available" if status == "available" else "late_but_pre_tip"
                cells.append(
                    f"[{tag} / {lc}]({g['game_id']}/{snap_type}/snapshot_report.md) "
                    f"({pmfs}, props={data.get('props_emitted')})"
                )
            elif status == "pending_not_due":
                cells.append(
                    f"pending_not_due (target={data.get('snapshot_target_time_utc')})"
                )
            elif status == "missed_post_tip":
                cells.append(
                    f"[missed_post_tip]({g['game_id']}/{snap_type}/missed_snapshot_report.md)"
                )
            else:
                cells.append(status)
        snap_readme.append(
            "| " + g["game_id"] + " | " + " | ".join(cells) + " |"
        )
    snap_readme.append("")
    derek.mkdir(parents=True, exist_ok=True)
    (derek / "README.md").write_text(
        "\n".join(snap_readme) + "\n", encoding="utf-8"
    )

    print("PHASE13W_DEREK_GITHUB_INDEX_PASS")
    print("PHASE13Z_DEREK_INDEX_STATUS_PASS")
    print(
        f"  delivery_date={args.delivery_date} games={len(games)} "
        f"readme={base.relative_to(REPO_ROOT)}/README.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
