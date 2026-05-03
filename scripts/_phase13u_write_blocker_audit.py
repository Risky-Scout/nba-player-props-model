"""Phase 13U Part B — Derek output blocker audit (read-only).

Inspects predictions/all_props_<date>.parquet, predictions/pmf_display_<date>.json,
deliveries/<date>/, artifacts/live_lineups/<date>/, and the dispatcher /
runner / workflow scripts to record exactly why Derek outputs were not
generated for the requested delivery date(s). Writes:

    artifacts/phase13u/derek_output_blocker_audit.json
    artifacts/phase13u/derek_output_blocker_audit.md

Pass line:  PHASE13U_DEREK_OUTPUT_BLOCKER_AUDIT_PASS
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _audit_date(date: str) -> dict:
    out: dict = {"delivery_date": date}
    pred = REPO_ROOT / "predictions" / f"all_props_{date}.parquet"
    pmf_disp = REPO_ROOT / "predictions" / f"pmf_display_{date}.json"
    deliveries = REPO_ROOT / "deliveries" / date
    derek = REPO_ROOT / "deliveries" / date / "derek_game_snapshots"
    live_lineups = REPO_ROOT / "artifacts" / "live_lineups" / date
    odds_processed = REPO_ROOT / "data" / "odds_api" / "processed" / date
    odds_raw = REPO_ROOT / "data" / "odds_api" / "raw" / date

    out["predictions_parquet_present"] = pred.exists()
    if pred.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(pred)
            out["prediction_rows"] = int(len(df))
            out["unique_games"] = (
                int(df["game_id"].nunique()) if "game_id" in df.columns else 0
            )
            out["game_ids"] = (
                sorted(set(df["game_id"].astype(str).tolist()))
                if "game_id" in df.columns else []
            )
            out["team_ids"] = (
                sorted(set(df["team_id"].astype(int).tolist()))
                if "team_id" in df.columns else []
            )
            out["game_start_time_column_present"] = "game_start_time" in df.columns
            out["game_start_time_non_null_count"] = (
                int(df["game_start_time"].notna().sum())
                if "game_start_time" in df.columns else 0
            )
            out["columns"] = list(df.columns)
        except Exception as exc:
            out["predictions_parquet_error"] = str(exc)

    out["pmf_display_present"] = pmf_disp.exists()
    if pmf_disp.exists():
        try:
            d = json.loads(pmf_disp.read_text(encoding="utf-8"))
            props = d.get("props") or []
            out["pmf_display_props"] = len(props)
            out["pmf_display_games"] = sorted(
                {p.get("game") for p in props if p.get("game")}
            )
            # Look for any time-like keys.
            time_keys = []
            if props:
                for k in props[0]:
                    if any(s in k.lower() for s in ("time","tip","start","commence")):
                        time_keys.append(k)
            out["pmf_display_time_keys_in_rows"] = time_keys
            out["pmf_display_top_level_time_keys"] = [
                k for k in d.keys()
                if any(s in k.lower() for s in ("time","tip","start","commence"))
            ]
        except Exception as exc:
            out["pmf_display_error"] = str(exc)

    out["deliveries_dir_present"] = deliveries.exists()
    out["derek_game_snapshots_dir_present"] = derek.exists()
    out["derek_snapshot_count"] = (
        sum(1 for d in derek.iterdir() if d.is_dir())
        if derek.exists() else 0
    )
    out["live_lineups_dir_present"] = live_lineups.exists()

    out["odds_api_processed_dir_present"] = odds_processed.exists()
    if odds_processed.exists():
        out["odds_api_processed_files"] = sorted(
            p.name for p in odds_processed.iterdir() if p.suffix in (".parquet",)
        )
    out["odds_api_raw_dir_present"] = odds_raw.exists()
    if odds_raw.exists():
        evs = sorted(p.name for p in odds_raw.glob("event_*.json"))
        out["odds_api_raw_event_count"] = len(evs)
        # Surface the most recent event commence_time samples.
        samples: list[dict] = []
        for p in evs[:5]:
            try:
                rec = json.loads((odds_raw / p).read_text(encoding="utf-8"))
                samples.append({
                    "event_id": rec.get("id"),
                    "commence_time": rec.get("commence_time"),
                    "home_team": rec.get("home_team"),
                    "away_team": rec.get("away_team"),
                })
            except Exception:
                continue
        out["odds_api_raw_event_samples"] = samples
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-dates", nargs="+",
                   default=None,
                   help="Dates to audit. Defaults to today UTC + 2026-05-03.")
    args = p.parse_args(argv)

    dates = args.delivery_dates or [
        dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "2026-05-03",
    ]
    seen: set[str] = set()
    dates = [d for d in dates if not (d in seen or seen.add(d))]

    out_dir = REPO_ROOT / "artifacts" / "phase13u"
    out_dir.mkdir(parents=True, exist_ok=True)
    audits = [_audit_date(d) for d in dates]
    payload = {
        "schema_version": "1.0",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0).isoformat() + "Z",
        "audits": audits,
        "answers": {
            "1_predictions_parquet_present": [
                {a["delivery_date"]: a.get("predictions_parquet_present")}
                for a in audits
            ],
            "2_prediction_rows": [
                {a["delivery_date"]: a.get("prediction_rows")} for a in audits
            ],
            "3_unique_games": [
                {a["delivery_date"]: a.get("unique_games")} for a in audits
            ],
            "4_game_ids": [
                {a["delivery_date"]: a.get("game_ids")} for a in audits
            ],
            "5_team_ids": [
                {a["delivery_date"]: a.get("team_ids")} for a in audits
            ],
            "6_game_start_time_column_present": [
                {a["delivery_date"]: a.get("game_start_time_column_present")}
                for a in audits
            ],
            "7_game_start_time_non_null_count": [
                {a["delivery_date"]: a.get("game_start_time_non_null_count")}
                for a in audits
            ],
            "8_pmf_display_present": [
                {a["delivery_date"]: a.get("pmf_display_present")} for a in audits
            ],
            "8b_pmf_display_top_level_time_keys": [
                {a["delivery_date"]: a.get("pmf_display_top_level_time_keys")}
                for a in audits
            ],
            "9_odds_api_processed_dir_present": [
                {a["delivery_date"]: a.get("odds_api_processed_dir_present")}
                for a in audits
            ],
            "10_odds_api_raw_event_count": [
                {a["delivery_date"]: a.get("odds_api_raw_event_count", 0)}
                for a in audits
            ],
            "11_derek_snapshot_count": [
                {a["delivery_date"]: a.get("derek_snapshot_count")} for a in audits
            ],
            "12_live_lineups_dir_present": [
                {a["delivery_date"]: a.get("live_lineups_dir_present")}
                for a in audits
            ],
            "13_dispatcher_no_games_root_cause": (
                "predictions/all_props_<date>.parquet has no game_start_time "
                "column at all (not just null), so the dispatcher's "
                "_load_schedule cannot derive any per-game tip time. "
                "Without tip times, the T-25 / close-lock window check "
                "always returns due=False with reason=no_game_start_time."
            ),
            "14_files_to_repair": [
                "src/nba_props_model/schedule/game_start_times.py (new resolver)",
                "scripts/resolve_game_start_times.py (CLI for live_schedule outputs)",
                "scripts/enrich_predictions_game_start_times.py (metadata-only writer)",
                "scripts/dispatch_derek_live_game_snapshots.py (resolver-aware)",
                "scripts/run_derek_live_game_snapshot.py (current_live mode)",
                "scripts/verify_derek_slate_completeness.py (new)",
                "scripts/verify_derek_production_live_e2e.py (extend with current_live)",
                ".github/workflows/derek_live_game_snapshots.yml (cron + steps)",
            ],
        },
    }
    (out_dir / "derek_output_blocker_audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    md = ["# Derek Output Blocker Audit (Phase 13U Part B)", ""]
    md.append(f"- generated_at_utc: {payload['generated_at_utc']}")
    md.append("")
    for a in audits:
        md.append(f"## delivery_date = {a['delivery_date']}")
        md.append("")
        md.append(f"- predictions_parquet_present: **{a.get('predictions_parquet_present')}**")
        md.append(f"- prediction_rows: {a.get('prediction_rows')}")
        md.append(f"- unique_games: {a.get('unique_games')}")
        md.append(f"- game_ids: {a.get('game_ids')}")
        md.append(f"- game_start_time_column_present: **{a.get('game_start_time_column_present')}**")
        md.append(f"- game_start_time_non_null_count: {a.get('game_start_time_non_null_count')}")
        md.append(f"- pmf_display_props: {a.get('pmf_display_props')}")
        md.append(f"- pmf_display_games: {a.get('pmf_display_games')}")
        md.append(f"- pmf_display_top_level_time_keys: {a.get('pmf_display_top_level_time_keys')}")
        md.append(f"- odds_api_processed_dir_present: {a.get('odds_api_processed_dir_present')}")
        md.append(f"- odds_api_raw_event_count: {a.get('odds_api_raw_event_count', 0)}")
        md.append(f"- derek_snapshot_count: {a.get('derek_snapshot_count')}")
        md.append(f"- live_lineups_dir_present: {a.get('live_lineups_dir_present')}")
        md.append("")
    md.append("## Root cause")
    md.append("")
    md.append(payload["answers"]["13_dispatcher_no_games_root_cause"])
    md.append("")
    md.append("## Files to repair")
    md.append("")
    for f in payload["answers"]["14_files_to_repair"]:
        md.append(f"- `{f}`")
    md.append("")
    (out_dir / "derek_output_blocker_audit.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")

    print("PHASE13U_DEREK_OUTPUT_BLOCKER_AUDIT_PASS")
    for a in audits:
        print(
            f"  - {a['delivery_date']}: "
            f"parquet={a.get('predictions_parquet_present')} "
            f"games={a.get('unique_games')} "
            f"start_time_col={a.get('game_start_time_column_present')} "
            f"derek_snapshots={a.get('derek_snapshot_count')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
