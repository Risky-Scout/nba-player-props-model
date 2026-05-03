"""Phase 13Z polish — render Derek-facing Markdown reports with
team-name matchup labels (no game_id in visible headings).

Reads existing manifests, market_comparison parquets, and audit JSONs;
overwrites the corresponding Markdown files in place. Does NOT
modify any data, parquet, CSV, or non-Markdown manifest files.

Files rewritten:

    deliveries/<date>/README.md
    deliveries/<date>/derek_game_snapshots/README.md
    deliveries/<date>/derek_game_snapshots/<gid>/current_live/snapshot_report.md
    deliveries/<date>/derek_game_snapshots/<gid>/current_live/pmf_driver_decomposition.md
    deliveries/<date>/derek_game_snapshots/<gid>/current_live/lineup_injury_impact_report.md
    deliveries/<date>/derek_game_snapshots/<gid>/current_live/direct_lineup_impact_report.md
    deliveries/<date>/derek_game_snapshots/<gid>/<missed_type>/missed_snapshot_report.md
    artifacts/phase13z/near_tip_snapshot_root_cause_<date>.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.derek.team_labels import (  # noqa: E402
    parse_matchup_string,
    resolve_team_labels,
)


# ── Status labels ────────────────────────────────────────────────────


CURRENT_LIVE_STATUS_LABELS = {
    "post_tip_stale_baseline": "Available, stale baseline",
    "on_time_or_current_live": "Available",
    "late_but_pre_tip": "Available (late but pre-tip)",
}


def _status_for_current_live(manifest: dict) -> str:
    sv = manifest.get("snapshot_validity_status") or "on_time_or_current_live"
    return CURRENT_LIVE_STATUS_LABELS.get(sv, "Available")


def _status_for_near_tip(snap_dir: Path,
                          manifest: dict | None,
                          missed_marker: dict | None,
                          target_in_future: bool) -> str:
    if manifest:
        if manifest.get("actual_run_late"):
            return "Available (late but pre-tip)"
        return "Available"
    if missed_marker:
        return "Missed during setup window; documented, not backfilled"
    if target_in_future:
        return "Scheduled"
    return "Pending dispatch"


def _read_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _utc_iso(d: dt.datetime) -> str:
    return d.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(s):
    if not s:
        return None
    try:
        d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return None


# ── Per-game gather ──────────────────────────────────────────────────


def _gather_game(*, repo_root: Path, delivery_date: str, game_id: str,
                  now: dt.datetime) -> dict:
    snaps_root = (repo_root / "deliveries" / delivery_date
                   / "derek_game_snapshots" / game_id)
    labels = resolve_team_labels(
        repo_root=repo_root, delivery_date=delivery_date, game_id=game_id,
    ) or {
        "away": f"Away (game {game_id})",
        "home": f"Home (game {game_id})",
        "matchup": f"Game {game_id}",
        "away_full": "", "home_full": "",
    }
    g: dict = {"game_id": game_id, "labels": labels, "snapshots": {}}
    # Resolve game_start_time once (any snapshot folder will have it).
    game_gs_iso: str | None = None
    for snap_type in ("current_live", "t_minus_25", "close_lock"):
        for fname in ("snapshot_manifest.json", "missed_snapshot_manifest.json"):
            d = _read_json(snaps_root / snap_type / fname) or {}
            cand = d.get("game_start_time_utc")
            if cand:
                game_gs_iso = str(cand)
                break
        if game_gs_iso:
            break
    game_gs_dt = _parse_iso(game_gs_iso)
    snapshot_offsets = {"t_minus_25": 25, "close_lock": 5}
    for snap_type in ("current_live", "t_minus_25", "close_lock"):
        sd = snaps_root / snap_type
        manifest = _read_json(sd / "snapshot_manifest.json")
        missed = _read_json(sd / "missed_snapshot_manifest.json")
        gs_iso = (
            (manifest or {}).get("game_start_time_utc")
            or (missed or {}).get("game_start_time_utc")
            or game_gs_iso
        )
        # Derive the target if it's not in any manifest (pending case).
        target_iso = (
            (manifest or {}).get("snapshot_target_time_utc")
            or (missed or {}).get("snapshot_target_time_utc")
        )
        if not target_iso and game_gs_dt and snap_type in snapshot_offsets:
            target_dt_calc = game_gs_dt - dt.timedelta(
                minutes=snapshot_offsets[snap_type]
            )
            target_iso = _utc_iso(target_dt_calc)
        target_dt = _parse_iso(target_iso)
        in_future = bool(target_dt and target_dt > now)
        status = (
            _status_for_current_live(manifest)
            if (manifest and snap_type == "current_live")
            else _status_for_near_tip(sd, manifest, missed, in_future)
        )
        g["snapshots"][snap_type] = {
            "snap_dir": sd,
            "manifest": manifest,
            "missed_marker": missed,
            "target_iso": target_iso,
            "game_start_time_utc": gs_iso,
            "status": status,
        }
    return g


# ── Markdown writers ─────────────────────────────────────────────────


SNAPSHOT_TYPE_DISPLAY = {
    "current_live": "Current-live",
    "t_minus_25": "T-minus-25",
    "close_lock": "Close-lock",
}


def _write_top_readme(*, repo_root: Path, delivery_date: str,
                       games: list[dict], now: dt.datetime) -> None:
    out = repo_root / "deliveries" / delivery_date / "README.md"
    pretty_date = dt.datetime.strptime(delivery_date, "%Y-%m-%d").strftime(
        "%B %-d, %Y"
    )
    md = [
        f"# Derek PMF Delivery — {pretty_date}",
        "",
        f"Generated {_utc_iso(now)}.",
        "",
        "## What to open first",
        "",
        "1. **Derek snapshot index** — "
        f"[derek_game_snapshots/README.md](derek_game_snapshots/README.md)",
    ]
    rank = 2
    for g in games:
        cl = g["snapshots"].get("current_live") or {}
        if cl.get("manifest"):
            base = f"derek_game_snapshots/{g['game_id']}/current_live"
            md.append(
                f"{rank}. **Current-live for {g['labels']['matchup']}** — "
                f"[snapshot_report.md]({base}/snapshot_report.md)"
            )
            rank += 1
    md.append(
        f"{rank}. **Edge reasonability audit** — "
        "[../../artifacts/automation_health/derek_edge_root_cause_"
        f"{delivery_date}.md](../../artifacts/automation_health/"
        f"derek_edge_root_cause_{delivery_date}.md)"
    )
    rank += 1
    md.append(
        f"{rank}. **Edge calibration audit** — "
        "[../../artifacts/automation_health/derek_edge_calibration_"
        f"{delivery_date}.md](../../artifacts/automation_health/"
        f"derek_edge_calibration_{delivery_date}.md)"
    )
    rank += 1
    md.append(
        f"{rank}. **Daily model report** — "
        "see `artifacts/model_daily_reports/<trained_through_date>/"
        "daily_model_training_report.md`"
    )
    md.append("")

    md.append("## Snapshot status by game")
    md.append("")
    md.append("| Matchup | Current-live | T-minus-25 | Close-lock |")
    md.append("| --- | --- | --- | --- |")
    for g in games:
        row = [g["labels"]["matchup"]]
        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            row.append(g["snapshots"][snap_type]["status"])
        md.append("| " + " | ".join(row) + " |")
    md.append("")
    md.append(
        "Missed snapshots are documented rather than backfilled. "
        "This avoids creating fake pre-tip output after a game has "
        "started. Going forward the dispatcher's snapshot state "
        "machine prevents silent misses by classifying every "
        "(game, snapshot type) pair as one of: Available, Scheduled, "
        "Pending dispatch, Available (late but pre-tip), or Missed "
        "during setup window."
    )
    md.append("")

    md.append("## What each file means")
    md.append("")
    md.append(
        "- **snapshot_report.md** — plain-English executive summary of "
        "one snapshot: top edges, top contextual minutes deltas, "
        "driver attribution, publishability gates."
    )
    md.append(
        "- **market_comparison.csv** — per-prop model probability vs "
        "market no-vig probability, with the Phase 13X "
        "edge_publish_status / edge_reasonability_status columns. "
        "Edges marked `WATCHLIST` / `REVIEW` / `PUBLISH_BLOCKER` are "
        "not for action."
    )
    md.append(
        "- **full_pmf_wide.csv** — full per-prop PMF + market "
        "probabilities."
    )
    md.append(
        "- **outcome_level_probabilities.csv** — long-form "
        "(player, stat, k, p_k) view of the PMF."
    )
    md.append(
        "- **pmf_driver_decomposition.md** — per-row contextual "
        "minutes / rate deltas with Phase 13S driver attribution."
    )
    md.append(
        "- **lineup_injury_impact_report.md** — lineup confirmation, "
        "BDL injury fetch, and counts of confirmed starters / bench "
        "/ confirmed out."
    )
    md.append(
        "- **direct_lineup_impact_report.md** — Phase 13S direct-"
        "lineup driver attribution: starter / bench changes, lineup "
        "composition impact."
    )
    md.append(
        "- **missed_snapshot_report.md** — written when a near-tip "
        "snapshot was missed post-tip; explains the miss and links "
        "back to the audit trail."
    )
    md.append("")

    md.append("## PMF variance experience study")
    md.append("")
    md.append(
        f"- [pmf_variance_experience_{delivery_date}.md]("
        f"https://github.com/Risky-Scout/nba-player-props-model/blob/main/"
        f"artifacts/experience_studies/pmf_variance_experience_"
        f"{delivery_date}.md)"
    )
    md.append(
        "- This is an actuarial-style actual-to-expected study for "
        "settled rows. It checks PMF mean calibration, PMF variance "
        "calibration, quantile coverage, and model-vs-market scoring. "
        "In this first settled sample, PMF variance is reasonably close "
        "overall, but the model under-projects means and trails market "
        "on Brier/logloss, so this is a diagnostic and improvement "
        "report rather than a market-superiority claim."
    )
    md.append("")

    md.append("## Daily location going forward")
    md.append("")
    md.append("- Future daily delivery index: `deliveries/YYYY-MM-DD/README.md`")
    md.append(
        "- Future Derek snapshot index: "
        "`deliveries/YYYY-MM-DD/derek_game_snapshots/README.md`"
    )
    md.append(
        "- Future per-game snapshots: "
        "`deliveries/YYYY-MM-DD/derek_game_snapshots/<game_id>/"
        "{current_live,t_minus_25,close_lock}/`"
    )
    md.append("")
    out.write_text("\n".join(md) + "\n", encoding="utf-8")


def _write_snapshot_index(*, repo_root: Path, delivery_date: str,
                           games: list[dict], now: dt.datetime) -> None:
    out = (repo_root / "deliveries" / delivery_date
            / "derek_game_snapshots" / "README.md")
    pretty_date = dt.datetime.strptime(delivery_date, "%Y-%m-%d").strftime(
        "%B %-d, %Y"
    )
    md = [
        f"# Derek PMF Snapshots — {pretty_date}",
        "",
        f"Generated {_utc_iso(now)}.",
        "",
        "## Snapshot status",
        "",
        "| Matchup | Current-live | T-minus-25 | Close-lock |",
        "| --- | --- | --- | --- |",
    ]
    for g in games:
        cl = g["snapshots"]["current_live"]["status"]
        t25 = g["snapshots"]["t_minus_25"]["status"]
        cl_lock = g["snapshots"]["close_lock"]["status"]
        md.append(
            f"| {g['labels']['matchup']} | {cl} | {t25} | {cl_lock} |"
        )
    md.append("")
    md.append(
        "Each subfolder is `<game_id>/<snapshot_type>/`. Visible "
        "labels use team names; the numeric `game_id` is preserved "
        "in file paths and technical manifests for the audit trail."
    )
    md.append("")
    md.append("## Per-game files")
    md.append("")
    for g in games:
        md.append(f"### {g['labels']['matchup']}")
        md.append("")
        md.append(
            f"_Game ID `{g['game_id']}` (used in paths only). "
            f"Tip time UTC: `{(g['snapshots']['current_live'].get('game_start_time_utc') or '')}`._"
        )
        md.append("")
        cl = g["snapshots"]["current_live"]
        if cl.get("manifest"):
            base = f"{g['game_id']}/current_live"
            md.append(f"- **Current-live** ({cl['status']}):")
            md.append(f"  - [snapshot_report.md]({base}/snapshot_report.md)")
            md.append(f"  - [market_comparison.csv]({base}/market_comparison.csv)")
            md.append(f"  - [full_pmf_wide.csv]({base}/full_pmf_wide.csv)")
            md.append(
                f"  - [outcome_level_probabilities.csv]"
                f"({base}/outcome_level_probabilities.csv)"
            )
            md.append(
                f"  - [pmf_driver_decomposition.md]"
                f"({base}/pmf_driver_decomposition.md)"
            )
            md.append(
                f"  - [lineup_injury_impact_report.md]"
                f"({base}/lineup_injury_impact_report.md)"
            )
            md.append(
                f"  - [direct_lineup_impact_report.md]"
                f"({base}/direct_lineup_impact_report.md)"
            )
        for snap_type in ("t_minus_25", "close_lock"):
            data = g["snapshots"][snap_type]
            base = f"{g['game_id']}/{snap_type}"
            label = SNAPSHOT_TYPE_DISPLAY[snap_type]
            if data.get("manifest"):
                md.append(f"- **{label}** ({data['status']}):")
                md.append(
                    f"  - [snapshot_report.md]({base}/snapshot_report.md)"
                )
                md.append(
                    f"  - [market_comparison.csv]({base}/market_comparison.csv)"
                )
            elif data.get("missed_marker"):
                md.append(f"- **{label}** ({data['status']}):")
                md.append(
                    f"  - [missed_snapshot_report.md]"
                    f"({base}/missed_snapshot_report.md)"
                )
            else:
                md.append(f"- **{label}**: {data['status']}")
        md.append("")
    md.append("## PMF variance experience study")
    md.append("")
    md.append(
        f"- [pmf_variance_experience_{delivery_date}.md]("
        f"https://github.com/Risky-Scout/nba-player-props-model/blob/main/"
        f"artifacts/experience_studies/pmf_variance_experience_"
        f"{delivery_date}.md)"
    )
    md.append(
        "- Actuarial-style actual-to-expected diagnostic for settled "
        "rows. PMF variance is reasonably close overall but the model "
        "under-projects means and trails market on Brier/logloss in "
        "the current sample, so this is a diagnostic and improvement "
        "report rather than a market-superiority claim."
    )
    md.append("")
    out.write_text("\n".join(md) + "\n", encoding="utf-8")


def _format_status_summary(manifest: dict, labels: dict) -> list[str]:
    sv = manifest.get("snapshot_validity_status") or "on_time_or_current_live"
    snap_type_disp = SNAPSHOT_TYPE_DISPLAY.get(
        manifest.get("snapshot_type") or "", manifest.get("snapshot_type") or ""
    )
    if sv == "post_tip_stale_baseline":
        snap_label = f"{snap_type_disp} (post-tip stale baseline)"
    elif sv == "late_but_pre_tip":
        snap_label = f"{snap_type_disp} (late but pre-tip)"
    else:
        snap_label = snap_type_disp
    lineup_status = (
        "Confirmed starters" if manifest.get("lineup_confirmed")
        else "BDL did not return confirmed starters at this timestamp; "
             "this is a baseline snapshot"
    )
    if manifest.get("BDL_injury_fetch_status") == "ok":
        injury_status = "Live BDL injury / availability"
    else:
        injury_status = (
            "Injury / availability inherited from the canonical "
            "predictions slate"
        )
    edge = (
        "See `market_comparison.csv` `edge_publish_status` column. "
        "Current-live without confirmed lineups is at most "
        "`WATCHLIST_NOT_CONFIRMED_LINEUP`."
    )
    return [
        f"- Matchup: **{labels['matchup']}** "
        f"(Away: {labels['away']}, Home: {labels['home']})",
        f"- Snapshot: {snap_label}",
        f"- Snapshot mode: `{manifest.get('snapshot_mode')}`",
        f"- Props emitted: **{manifest.get('props_emitted')}**",
        f"- PMFs recomputed: **{manifest.get('pmfs_recomputed')}**",
        f"- Lineup status: {lineup_status}",
        f"- Injury status: {injury_status}",
        f"- Edge status: {edge}",
    ]


def _write_current_live_snapshot_report(*, snap_dir: Path,
                                          manifest: dict,
                                          labels: dict,
                                          delivery_date: str,
                                          game_id: str) -> None:
    sv = manifest.get("snapshot_validity_status") or "on_time_or_current_live"
    title_suffix = "Current-live PMF snapshot"
    if sv == "post_tip_stale_baseline":
        title_suffix = "Current-live PMF snapshot (post-tip stale baseline)"
    md = [
        f"# {labels['matchup']} — {title_suffix}",
        "",
        "## Summary",
        "",
        *_format_status_summary(manifest, labels),
        "",
        "## How to read this",
        "",
        "- `model_prob` is the model's **win probability** under the "
        "sportsbook push-excluded convention. For decimal lines (e.g. "
        "`UNDER 8.5`), `model_prob = P(stat < 8.5)`. For integer lines "
        "(e.g. `UNDER 1.0`), `model_prob = P(stat < 1) / (1 − P(stat = 1))`.",
        "- `market_prob` is the no-vig probability implied by the same "
        "side's American odds, after stripping the vig.",
        "- `raw_edge = model_prob − market_prob`. `ev` uses the same "
        "push-excluded convention; integer-line rows also report a "
        "push-aware EV in the audit JSON.",
        "- `edge_publish_status` filters which rows are eligible to "
        "show Derek as actionable: "
        "`PUBLISH_BLOCKER` > `REVIEW_LARGE_EDGE` > `REVIEW_PUSH_LINE` > "
        "`WATCHLIST_NOT_CONFIRMED_LINEUP` > `ACTIONABLE_REVIEWED`. "
        "Current-live without confirmed lineups is never higher than "
        "`WATCHLIST_NOT_CONFIRMED_LINEUP`.",
        "- `calibration_support_status` reports whether the historical "
        "scoring corpus has enough settled rows in the same "
        "(stat, side, line bucket, edge bucket) to trust the edge: "
        "`CALIBRATION_SUPPORTED` (n ≥ 100) > `CALIBRATION_SAMPLE_LIMITED` "
        "(30 ≤ n < 100) > `CALIBRATION_SAMPLE_THIN` (n < 30) > "
        "`CALIBRATION_REVIEW_REQUIRED` (model worse than market by "
        "≥ 0.05 logloss).",
        "- `p0` is the modeled probability the player records exactly "
        "zero of this stat. PMF tail mass is summarized in "
        "`pmf_mean` / `pmf_variance`.",
        "",
        "## Important caveats",
        "",
    ]
    if not manifest.get("lineup_confirmed"):
        md.append(
            "- **BDL did not return confirmed lineup rows at this "
            "timestamp.** This snapshot is a best-available baseline; "
            "it does not directly reflect official starter status. "
            "The dispatcher will produce confirmed-lineup snapshots "
            "in the T-minus-25 and close-lock windows."
        )
    if sv == "post_tip_stale_baseline":
        md.append(
            "- **This run executed after the game tipped.** The PMFs "
            "are the canonical pre-tip slate scored by the contextual "
            "engine — no in-game data leaks in — but the timestamp is "
            "post-tip. The dispatcher refuses to regenerate "
            "current-live for already-tipped games going forward."
        )
    md.append(
        "- Market odds are used for **edge only**, never as model "
        "features (`market_odds_used_as_features=False`)."
    )
    md.append(
        "- No post-tip data was used in any prediction "
        "(`no_post_tip_data_used=True`)."
    )
    md.append("")

    # Reuse the rich top-edge / push-line / driver tables already
    # produced by the Phase 13X appender. We re-derive them here from
    # market_comparison.parquet so this script stands alone.
    try:
        import pandas as pd
        df = pd.read_parquet(snap_dir / "market_comparison.parquet")
        md.append("## Top edges (subject to publishability gates)")
        md.append("")
        md.append(
            "Sort: largest |raw_edge| first. `edge_publish_status` is "
            "the gate that determines whether a row is showable; rows "
            "without `ACTIONABLE_REVIEWED` are not for action."
        )
        md.append("")
        cols = [c for c in (
            "player_name", "stat", "side", "line", "model_prob",
            "market_prob", "raw_edge", "ev", "edge_publish_status",
            "calibration_support_status", "calibration_bucket_n",
        ) if c in df.columns]
        if cols:
            top = df.copy()
            top["_abs"] = top["raw_edge"].abs()
            top = top.sort_values("_abs", ascending=False).head(20)[cols]
            md.append("| " + " | ".join(cols) + " |")
            md.append("| " + " | ".join(["---"] * len(cols)) + " |")
            for _, r in top.iterrows():
                row = []
                for c in cols:
                    v = r.get(c)
                    if isinstance(v, float):
                        row.append(
                            f"{v:+.3f}" if c in ("raw_edge", "ev")
                            else f"{v:.3f}"
                        )
                    else:
                        row.append(str(v))
                md.append("| " + " | ".join(row) + " |")
            md.append("")

        # Push-line audit.
        if "push_line" in df.columns:
            push_rows = df[df["push_line"] == True]  # noqa: E712
            if not push_rows.empty:
                md.append("## Push-line audit rows")
                md.append("")
                md.append(
                    "Integer lines where the model's probability of "
                    "exact-line outcomes is non-trivial. The displayed "
                    "`ev` uses the sportsbook push-excluded convention; "
                    "`ev_recomputed_pushinc` is the honest dollar-EV "
                    "with push paid as $0."
                )
                md.append("")
                pcols = [c for c in (
                    "player_name", "stat", "side", "line", "push_prob",
                    "ev", "ev_recomputed", "ev_recomputed_pushinc",
                    "edge_publish_status",
                ) if c in push_rows.columns]
                md.append("| " + " | ".join(pcols) + " |")
                md.append("| " + " | ".join(["---"] * len(pcols)) + " |")
                for _, r in push_rows.iterrows():
                    row = []
                    for c in pcols:
                        v = r.get(c)
                        if isinstance(v, float):
                            row.append(f"{v:+.3f}" if "ev" in c else f"{v:.3f}")
                        else:
                            row.append(str(v))
                    md.append("| " + " | ".join(row) + " |")
                md.append("")
    except Exception as exc:
        md.append(f"_Edge tables unavailable: {exc}_")
        md.append("")

    md.append("## Technical audit details")
    md.append("")
    md.append(f"- Game ID: `{game_id}`")
    md.append(f"- Away Team: {labels.get('away')}")
    md.append(f"- Home Team: {labels.get('home')}")
    md.append(f"- Game start time UTC: `{manifest.get('game_start_time_utc')}`")
    md.append(
        f"- Snapshot target time UTC: "
        f"`{manifest.get('snapshot_target_time_utc')}`"
    )
    md.append(
        f"- Actual run started at UTC: "
        f"`{manifest.get('actual_run_started_at_utc')}`"
    )
    md.append(
        f"- Snapshot validity status: `{manifest.get('snapshot_validity_status')}`"
    )
    md.append(f"- Champion model ID: `{manifest.get('champion_model_id')}`")
    md.append(f"- Feature set ID: `{manifest.get('feature_set_id')}`")
    md.append(f"- Trained through date: `{manifest.get('trained_through_date')}`")
    md.append(
        f"- Calibrated through date: `{manifest.get('calibrated_through_date')}`"
    )
    md.append(
        f"- Direct-lineup PMF driver: **{manifest.get('direct_lineup_pmf_driver')}**"
    )
    md.append(f"- Contextual PMF engine: **{manifest.get('contextual_pmf_engine')}**")
    md.append(f"- PMFs recomputed: **{manifest.get('pmfs_recomputed')}**")
    md.append(f"- PMF source: `{manifest.get('pmf_source')}`")
    md.append(
        f"- BDL lineup fetch status: `{manifest.get('BDL_lineup_fetch_status')}` "
        f"(rows={manifest.get('BDL_lineup_rows')})"
    )
    md.append(
        f"- BDL injury fetch status: `{manifest.get('BDL_injury_fetch_status')}` "
        f"(rows={manifest.get('BDL_injury_rows')})"
    )
    md.append(
        f"- market_odds_used_as_features: `{manifest.get('market_odds_used_as_features')}`"
    )
    md.append(
        f"- market_odds_used_for_edge_only: `{manifest.get('market_odds_used_for_edge_only')}`"
    )
    md.append(
        f"- no_post_tip_data_used: `{manifest.get('no_post_tip_data_used')}`"
    )

    (snap_dir / "snapshot_report.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )


def _write_pmf_decomp(*, snap_dir: Path, manifest: dict, labels: dict,
                       game_id: str) -> None:
    md = [
        f"# {labels['matchup']} — PMF driver decomposition",
        "",
        f"_Snapshot: `{manifest.get('snapshot_type')}` ({manifest.get('snapshot_validity_status')})._",
        "",
        "Per-row contextual deltas from the Phase 13S direct-lineup "
        "engine. Constant deltas across players are honest when BDL "
        "did not return confirmed lineups (the engine then sees the "
        "same lagged-proxy bucket on every row).",
        "",
    ]
    try:
        import pandas as pd
        decomp = snap_dir / "pmf_driver_decomposition.parquet"
        if decomp.exists():
            df = pd.read_parquet(decomp)
            cols = [c for c in (
                "player_name", "team", "exp_mp", "exp_mp_contextual",
                "contextual_minutes_delta", "contextual_pmf_mean_baseline",
                "contextual_pmf_mean_post",
            ) if c in df.columns]
            if cols:
                slim = df[cols].drop_duplicates(subset=["player_name"]).head(30) \
                    if "player_name" in df.columns else df[cols].head(30)
                md.append("## Per-player contextual deltas (top 30)")
                md.append("")
                md.append("| " + " | ".join(cols) + " |")
                md.append("| " + " | ".join(["---"] * len(cols)) + " |")
                for _, r in slim.iterrows():
                    row = []
                    for c in cols:
                        v = r.get(c)
                        row.append(
                            f"{v:.3f}" if isinstance(v, float) else str(v)
                        )
                    md.append("| " + " | ".join(row) + " |")
                md.append("")
    except Exception as exc:
        md.append(f"_Decomposition unavailable: {exc}_")
        md.append("")
    md.append("## Technical audit details")
    md.append("")
    md.append(f"- Game ID: `{game_id}`")
    md.append(f"- Feature set ID: `{manifest.get('feature_set_id')}`")
    md.append(f"- Contextual engine: **{manifest.get('contextual_pmf_engine')}**")
    md.append(
        f"- Contextual applied: **{manifest.get('contextual_pmf_applied')}**"
    )
    md.append(
        f"- Direct-lineup driver: **{manifest.get('direct_lineup_pmf_driver')}**"
    )
    (snap_dir / "pmf_driver_decomposition.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )


def _write_lineup_injury(*, snap_dir: Path, manifest: dict, labels: dict,
                          game_id: str) -> None:
    impact = _read_json(snap_dir / "lineup_injury_impact_report.json") or {}
    md = [
        f"# {labels['matchup']} — Lineup & injury impact",
        "",
        "## Summary",
        "",
        f"- Lineup confirmed: **{manifest.get('lineup_confirmed')}**",
        f"- BDL lineup fetch: `{manifest.get('BDL_lineup_fetch_status')}` "
        f"(rows={manifest.get('BDL_lineup_rows')})",
        f"- BDL injury fetch: `{manifest.get('BDL_injury_fetch_status')}` "
        f"(rows={manifest.get('BDL_injury_rows')})",
        f"- Official lineup context supplied: "
        f"**{manifest.get('official_lineup_context_supplied')}**",
        f"- Injury context supplied: "
        f"**{manifest.get('injury_context_supplied')}**",
        f"- Game context supplied: "
        f"**{manifest.get('game_context_supplied')}**",
        "",
    ]
    if not manifest.get("lineup_confirmed"):
        md.append(
            "BDL did not return confirmed lineup rows at this "
            "timestamp, so this snapshot is a best-available baseline. "
            "Rows therefore reflect lagged-proxy starter status, not "
            "live confirmation."
        )
        md.append("")
    md.append("## Counts")
    md.append("")
    md.append(
        f"- Confirmed starters: **{(impact.get('lineup_summary') or {}).get('confirmed_starters', 0)}**"
    )
    md.append(
        f"- Confirmed bench: **{(impact.get('lineup_summary') or {}).get('confirmed_benches', 0)}**"
    )
    md.append(
        f"- Confirmed out: **{(impact.get('injury_summary') or {}).get('confirmed_out', 0)}**"
    )
    md.append(
        f"- Non-actionable: **{(impact.get('injury_summary') or {}).get('non_actionable', 0)}**"
    )
    md.append("")
    md.append("## Technical audit details")
    md.append("")
    md.append(f"- Game ID: `{game_id}`")
    md.append(f"- Feature set ID: `{manifest.get('feature_set_id')}`")
    md.append(f"- Lineup blocker: `{manifest.get('lineup_blocker')}`")
    md.append(f"- Injury blocker: `{manifest.get('injury_blocker')}`")
    (snap_dir / "lineup_injury_impact_report.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )


def _write_direct_lineup(*, snap_dir: Path, manifest: dict, labels: dict,
                          game_id: str) -> None:
    impact = _read_json(snap_dir / "direct_lineup_impact_report.json") or {}
    rate_summary = impact.get("rate_delta_summary") or {}
    md = [
        f"# {labels['matchup']} — Direct lineup impact",
        "",
        "## Summary",
        "",
        f"- Feature set ID: `{manifest.get('feature_set_id')}`",
        f"- Direct-lineup PMF driver: "
        f"**{manifest.get('direct_lineup_pmf_driver')}**",
        f"- Direct-lineup features consumed: "
        f"**{manifest.get('direct_lineup_features_consumed')}**",
        f"- Lineup confirmed: **{manifest.get('lineup_confirmed')}**",
        "",
    ]
    if not manifest.get("lineup_confirmed"):
        md.append(
            "Without confirmed lineups, the direct-lineup features "
            "fall back to lagged starter proxies. Treat the deltas as "
            "a best-available baseline, not a confirmed projection."
        )
        md.append("")
    md.append("## Direct-lineup metrics")
    md.append("")
    md.append(
        f"- Rows scored: **{impact.get('rows_scored', 0)}**"
    )
    md.append(
        f"- Confirmed starters: **{impact.get('confirmed_starters', 0)}**"
    )
    md.append(
        f"- Confirmed bench: **{impact.get('confirmed_benches', 0)}**"
    )
    md.append(
        f"- Starter changed from projection: "
        f"**{impact.get('starter_changed_from_projection', 0)}**"
    )
    md.append(
        f"- Bench changed from projection: "
        f"**{impact.get('bench_changed_from_projection', 0)}**"
    )
    md.append(
        f"- Minutes-projection conflicts: "
        f"**{impact.get('minutes_projection_conflicts', 0)}**"
    )
    md.append(
        f"- Minutes-delta abs mean: "
        f"**{(impact.get('minutes_delta_abs_mean') or 0):.4f}**"
    )
    md.append(
        f"- Minutes-delta abs max: "
        f"**{(impact.get('minutes_delta_abs_max') or 0):.4f}**"
    )
    md.append("")
    if rate_summary:
        md.append("## Per-stat rate-delta summary")
        md.append("")
        md.append("| stat | abs_mean | abs_max | n |")
        md.append("| --- | ---: | ---: | ---: |")
        for stat, vals in sorted(rate_summary.items()):
            md.append(
                f"| {stat} | {vals.get('abs_mean', 0):.4f} | "
                f"{vals.get('abs_max', 0):.4f} | {vals.get('n', 0)} |"
            )
        md.append("")
    md.append("## Technical audit details")
    md.append("")
    md.append(f"- Game ID: `{game_id}`")
    md.append(f"- Champion model ID: `{manifest.get('champion_model_id')}`")
    (snap_dir / "direct_lineup_impact_report.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )


def _write_missed_report(*, snap_dir: Path, missed: dict, labels: dict,
                          snap_type: str, game_id: str) -> None:
    snap_label = SNAPSHOT_TYPE_DISPLAY.get(snap_type, snap_type)
    md = [
        f"# {labels['matchup']} — {snap_label} snapshot",
        "",
        "This near-tip snapshot was not generated before tip.",
        "",
        f"The target time was {25 if snap_type == 't_minus_25' else 5} "
        "minutes before tip. By the time the near-tip verification ran, "
        "the game had already started, so the system did not create a "
        "backfilled pre-tip PMF. That is intentional: creating a "
        "pre-tip snapshot after the game starts would risk using "
        "information that was not available at the time.",
        "",
        "The miss is documented here so the daily index and verifiers "
        "show the true status. Going forward, the dispatcher's "
        "snapshot state machine fires inside the cron window and "
        "recovers any miss before tip; only post-tip misses produce "
        "this report.",
        "",
        "## Technical audit details",
        "",
        f"- Game ID: `{game_id}`",
        f"- Away Team: {labels.get('away')}",
        f"- Home Team: {labels.get('home')}",
        f"- Snapshot type: `{snap_type}`",
        f"- Target time UTC: `{missed.get('snapshot_target_time_utc')}`",
        f"- Tip time UTC: `{missed.get('game_start_time_utc')}`",
        f"- Documented at UTC: `{missed.get('now_utc')}`",
        f"- Missed reason: `{missed.get('missed_reason')}`",
        f"- no_fake_pretip_snapshot: **{missed.get('no_fake_pretip_snapshot')}**",
        f"- production_fix_applied: **{missed.get('production_fix_applied')}**",
    ]
    (snap_dir / "missed_snapshot_report.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )


def _write_root_cause_audit(*, repo_root: Path, delivery_date: str,
                              games: list[dict], now: dt.datetime) -> None:
    """Rewrite the Phase 13Z root-cause audit Markdown with team-name
    columns. The JSON sidecar (with raw fields) stays unchanged."""
    out = (repo_root / "artifacts" / "phase13z"
            / f"near_tip_snapshot_root_cause_{delivery_date}.md")
    if not out.parent.exists():
        return
    json_path = (repo_root / "artifacts" / "phase13z"
                  / f"near_tip_snapshot_root_cause_{delivery_date}.json")
    payload = _read_json(json_path) or {}

    md = [
        f"# Near-tip snapshot root-cause audit — {delivery_date}",
        "",
        f"Generated {_utc_iso(now)}.",
        "",
        "## Per-(matchup, snapshot) state",
        "",
        "| Away | Home | Matchup | Snapshot | Tip Time UTC | "
        "Target Time UTC | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for g in games:
        labels = g["labels"]
        for snap_type in ("t_minus_25", "close_lock"):
            data = g["snapshots"][snap_type]
            label = SNAPSHOT_TYPE_DISPLAY[snap_type]
            tip = data.get("game_start_time_utc") or ""
            target = data.get("target_iso") or ""
            md.append(
                f"| {labels['away']} | {labels['home']} | "
                f"{labels['matchup']} | {label} | `{tip}` | "
                f"`{target}` | {data['status']} |"
            )
    md.append("")
    md.append("## Why missed snapshots are documented, not backfilled")
    md.append("")
    md.append(
        "The dispatcher's snapshot state machine refuses to create a "
        "pre-tip snapshot after a game has already tipped. That would "
        "risk capturing post-tip information into a manifest claimed "
        "as pre-tip. Instead, missed near-tip snapshots get a "
        "`missed_snapshot_manifest.json` + `missed_snapshot_report.md` "
        "marker so the daily index and verifiers can show the true "
        "status."
    )
    md.append("")
    answers = payload.get("answers") or {}
    if answers:
        md.append("## Audit answers")
        md.append("")
        for k, v in answers.items():
            md.append(f"### {k}")
            md.append("")
            if isinstance(v, list):
                for item in v:
                    md.append(f"- {item}")
            else:
                md.append(str(v))
            md.append("")
    out.write_text("\n".join(md) + "\n", encoding="utf-8")


# ── Main ─────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    now = dt.datetime.now(dt.timezone.utc)
    base = (REPO_ROOT / "deliveries" / args.delivery_date
             / "derek_game_snapshots")
    if not base.exists():
        print("PHASE13Z_POLISH_PENDING")
        print(f"  no derek_game_snapshots dir for {args.delivery_date}")
        return 0

    game_ids = sorted(
        d.name for d in base.iterdir() if d.is_dir() and d.name.isdigit()
    )
    games = [
        _gather_game(repo_root=REPO_ROOT, delivery_date=args.delivery_date,
                      game_id=gid, now=now)
        for gid in game_ids
    ]

    # Top-level + index READMEs.
    _write_top_readme(
        repo_root=REPO_ROOT, delivery_date=args.delivery_date,
        games=games, now=now,
    )
    _write_snapshot_index(
        repo_root=REPO_ROOT, delivery_date=args.delivery_date,
        games=games, now=now,
    )

    # Per-game per-snapshot files.
    for g in games:
        for snap_type, data in g["snapshots"].items():
            sd = data["snap_dir"]
            manifest = data["manifest"]
            missed = data["missed_marker"]
            if manifest:
                if snap_type == "current_live":
                    _write_current_live_snapshot_report(
                        snap_dir=sd, manifest=manifest, labels=g["labels"],
                        delivery_date=args.delivery_date,
                        game_id=g["game_id"],
                    )
                    _write_pmf_decomp(
                        snap_dir=sd, manifest=manifest, labels=g["labels"],
                        game_id=g["game_id"],
                    )
                    _write_lineup_injury(
                        snap_dir=sd, manifest=manifest, labels=g["labels"],
                        game_id=g["game_id"],
                    )
                    _write_direct_lineup(
                        snap_dir=sd, manifest=manifest, labels=g["labels"],
                        game_id=g["game_id"],
                    )
                else:
                    # Available T-minus-25 / close-lock snapshots use
                    # the same current-live writer template (same
                    # technical fields).
                    _write_current_live_snapshot_report(
                        snap_dir=sd, manifest=manifest, labels=g["labels"],
                        delivery_date=args.delivery_date,
                        game_id=g["game_id"],
                    )
            elif missed:
                _write_missed_report(
                    snap_dir=sd, missed=missed, labels=g["labels"],
                    snap_type=snap_type, game_id=g["game_id"],
                )

    # Phase 13Z root-cause audit MD with team-name columns.
    _write_root_cause_audit(
        repo_root=REPO_ROOT, delivery_date=args.delivery_date,
        games=games, now=now,
    )

    print("PHASE13Z_POLISH_REPORTS_PASS")
    print(
        f"  delivery_date={args.delivery_date} games={len(games)}  "
        + ", ".join(
            f"{g['game_id']}=`{g['labels']['matchup']}`" for g in games
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
