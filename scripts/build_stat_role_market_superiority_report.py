#!/usr/bin/env python3
"""M8.6 — aggregate event-market loss rows to stat × role segments.

Writes:
  artifacts/model_diagnostics/event_market_superiority_<date>/
    stat_role_market_superiority.csv
    stat_market_superiority.csv
    role_market_superiority.csv
    book_market_superiority.csv
    snapshot_market_superiority.csv
    summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from collections import Counter

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from event_market_date_selection import (  # noqa: E402
    model_only_calibration_claim_allowed,
    resolve_event_market_label,
)
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402

REQUIRED_STATS = [str(s).lower() for s in MISSION_REQUIRED_TARGETS_CANONICAL]
DEFAULT_MIN_SCORED = 100
DEFAULT_MIN_JOINED = 100


def _load_audit_final_reasons(label: str) -> dict[str, str]:
    p = (
        REPO_ROOT
        / "artifacts"
        / "model_diagnostics"
        / f"event_market_coverage_{label}"
        / "coverage_by_stat.json"
    )
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, str] = {}
    for row in data.get("stats", []):
        st = str(row.get("stat", "")).lower()
        out[st] = str(row.get("final_missing_reason") or row.get("missing_reason") or "")
    return out


def _finite_mean(s: pd.Series) -> float | None:
    x = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if x.empty:
        return None
    return float(x.mean())


def _precise_segment_failure_reason(
    sub: pd.DataFrame,
    *,
    min_scored: int,
    n_scored_core: int,
    n_market_joined: int,
    mb: float | None,
    mm: float | None,
    ml: float | None,
    mk: float | None,
    mr: float | None,
    mkr: float | None,
) -> str:
    """Replace vague 'model_metrics_missing_or_join_incomplete' with actionable codes."""
    core_cols = (
        "model_prob_over",
        "market_prob_over_no_vig",
        "hit_result",
        "model_brier",
        "market_brier",
        "model_event_logloss",
        "market_event_logloss",
    )
    missing_cols = [c for c in core_cols if c not in sub.columns]
    if missing_cols:
        return "join_incomplete"
    for col, reason in (
        ("model_prob_over", "missing_model_prob_over"),
        ("market_prob_over_no_vig", "missing_market_prob_over"),
        ("hit_result", "missing_actual_outcome"),
        ("model_brier", "missing_model_brier"),
        ("market_brier", "missing_market_brier"),
        ("model_event_logloss", "missing_model_logloss"),
        ("market_event_logloss", "missing_market_logloss"),
    ):
        if int(sub[col].notna().sum()) == 0 and len(sub) > 0:
            return reason
    if n_scored_core < min_scored:
        return "insufficient_scored_rows"
    if mb is None or mm is None or ml is None or mk is None:
        return "unknown_bug"
    if ml >= mk:
        return "model_logloss_not_better"
    if mb >= mm:
        return "model_brier_not_better"
    if mkr is not None and mr is not None and mr >= mkr:
        return "model_rps_not_better"
    return "unknown_bug"


def _agg_segment(sub: pd.DataFrame, *, min_scored: int, min_joined: int) -> dict:
    n_rows = int(len(sub))
    joined = sub[sub.get("join_status", pd.Series(["unknown"] * len(sub))) == "matched"]
    n_market_joined = int(len(joined))
    settled = sub[sub.get("settled", False) == True] if "settled" in sub.columns else sub.iloc[0:0]
    n_scored = int(len(settled))
    mask = pd.Series(True, index=sub.index)
    for c in (
        "model_event_logloss", "market_event_logloss", "model_brier", "market_brier",
    ):
        if c in sub.columns:
            mask &= sub[c].notna()
    n_scored_core = int(mask.sum())

    def _m(col):
        return _finite_mean(sub[col]) if col in sub.columns else None

    out = {
        "n_rows": n_rows,
        "n_scored": n_scored_core,
        "n_market_joined": n_market_joined,
        "n_books": int(sub["bookmaker_key"].nunique()) if "bookmaker_key" in sub.columns else 0,
        "n_players": int(sub["player_id"].nunique()) if "player_id" in sub.columns else 0,
        "n_games": int(sub["game_id"].nunique()) if "game_id" in sub.columns else 0,
        "model_brier_avg": _m("model_brier"),
        "market_brier_avg": _m("market_brier"),
        "model_logloss_avg": _m("model_event_logloss"),
        "market_logloss_avg": _m("market_event_logloss"),
        "model_rps_avg": _m("model_rps"),
        "market_rps_avg": _m("market_rps") if "market_rps" in sub.columns else None,
        "market_coverage_status": "covered" if n_market_joined else "none",
        "availability_freshness_status": "unknown",
        "failure_reason": "",
        "market_superiority_pass": False,
    }
    if n_scored_core < min_scored:
        out["failure_reason"] = "insufficient_scored_rows"
    elif n_market_joined < min_joined:
        out["failure_reason"] = "insufficient_market_overlap"
    else:
        out["failure_reason"] = ""

    mb, mm = out["model_brier_avg"], out["market_brier_avg"]
    ml, mk = out["model_logloss_avg"], out["market_logloss_avg"]
    out["brier_delta_model_minus_market"] = (mb - mm) if (mb is not None and mm is not None) else None
    out["logloss_delta_model_minus_market"] = (ml - mk) if (ml is not None and mk is not None) else None
    mr, mkr = out["model_rps_avg"], out["market_rps_avg"]
    out["rps_delta_model_minus_market"] = (mr - mkr) if (mr is not None and mkr is not None) else None
    out["rps_status"] = "unavailable_market_distribution" if mkr is None else "available"

    # Strict pass only when deltas strictly negative (model better) and samples sufficient.
    if (
        out["failure_reason"] == ""
        and mb is not None
        and mm is not None
        and ml is not None
        and mk is not None
        and mb < mm
        and ml < mk
    ):
        if mkr is None or (mr is not None and mr < mkr):
            out["market_superiority_pass"] = True
            out["failure_reason"] = ""
    if out["failure_reason"] == "" and not out["market_superiority_pass"]:
        out["failure_reason"] = _precise_segment_failure_reason(
            sub,
            min_scored=min_scored,
            n_scored_core=n_scored_core,
            n_market_joined=n_market_joined,
            mb=mb,
            mm=mm,
            ml=ml,
            mk=mk,
            mr=mr,
            mkr=mkr,
        )

    out["model_beats_market_brier"] = bool(mb is not None and mm is not None and mb < mm)
    out["model_beats_market_logloss"] = bool(ml is not None and mk is not None and ml < mk)
    out["model_beats_market_rps"] = bool(mkr is None or (mr is not None and mr < mkr))
    out["calibration_pass"] = False
    out["model_ece"] = None
    out["market_ece"] = None
    out["model_calibration_slope"] = None
    out["model_calibration_intercept"] = None
    out["market_calibration_slope"] = None
    out["market_calibration_intercept"] = None
    out["pit_ks"] = None
    out["mean_error"] = None
    out["variance_error"] = None
    out["p0_error"] = None
    out["model_better_calibrated"] = False
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--dates-file", default=None)
    ap.add_argument("--include-ineligible", action="store_true")
    ap.add_argument("--min-scored-rows", type=int, default=DEFAULT_MIN_SCORED)
    ap.add_argument("--min-market-joined-rows", type=int, default=DEFAULT_MIN_JOINED)
    ap.add_argument(
        "--event-calibration-model",
        default=None,
        help="Optional guarded event calibration JSON; merged into summary.json metadata.",
    )
    args = ap.parse_args()

    if args.event_calibration_model:
        p = Path(args.event_calibration_model)
        if not p.is_absolute():
            p = REPO_ROOT / p
        if not p.is_file():
            print(f"FATAL: --event-calibration-model not found: {p}", file=sys.stderr)
            return 2

    modes = sum(bool(x) for x in (args.date, (args.start_date and args.end_date), args.dates_file))
    if modes > 1:
        print("FATAL: use only one of --date, --start-date/--end-date, --dates-file", file=sys.stderr)
        return 2
    if modes == 0:
        print("FATAL: pass --date, --start-date/--end-date, or --dates-file", file=sys.stderr)
        return 2

    dates_used, label, meta = resolve_event_market_label(
        date=args.date,
        start_date=args.start_date,
        end_date=args.end_date,
        dates_file=args.dates_file,
        include_ineligible=args.include_ineligible,
    )

    eml_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    if not eml_path.exists():
        print(f"FATAL missing {eml_path}", file=sys.stderr)
        return 1
    eml = pd.read_parquet(eml_path)
    if "role_bucket" not in eml.columns:
        eml = eml.copy()
        eml["role_bucket"] = "unknown"

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_superiority_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    roles = sorted(set(eml["role_bucket"].astype(str).unique()) | {"unknown"})
    rows_sr = []
    for stat in REQUIRED_STATS:
        for role in roles:
            sub = eml[(eml["stat"].astype(str).str.lower() == stat) & (eml["role_bucket"].astype(str) == role)]
            agg = _agg_segment(
                sub,
                min_scored=args.min_scored_rows,
                min_joined=args.min_market_joined_rows,
            )
            rows_sr.append({
                "date": label,
                "stat": stat,
                "role_bucket": role,
                **agg,
                "market_superiority_eligible": agg["n_scored"] >= args.min_scored_rows
                and agg["n_market_joined"] >= args.min_market_joined_rows,
                "market_superiority_claim_allowed": False,
                "promotion_status": "no_market_superiority_claim",
            })

    df_sr = pd.DataFrame(rows_sr)
    df_sr.to_csv(out_dir / "stat_role_market_superiority.csv", index=False)

    # Rollups
    def _rollup(key):
        g = eml.groupby(eml[key].astype(str).str.lower(), dropna=False)
        out_rows = []
        for k, sub in g:
            agg = _agg_segment(
                sub,
                min_scored=args.min_scored_rows,
                min_joined=args.min_market_joined_rows,
            )
            out_rows.append({key: k, **agg})
        return pd.DataFrame(out_rows)

    _rollup("stat").to_csv(out_dir / "stat_market_superiority.csv", index=False)
    _rollup("role_bucket").to_csv(out_dir / "role_market_superiority.csv", index=False)
    if "bookmaker_key" in eml.columns:
        g = eml.groupby(eml["bookmaker_key"].astype(str), dropna=False)
        br = []
        for k, sub in g:
            br.append({"book": k, **_agg_segment(sub, min_scored=args.min_scored_rows, min_joined=args.min_market_joined_rows)})
        pd.DataFrame(br).to_csv(out_dir / "book_market_superiority.csv", index=False)
    else:
        pd.DataFrame(columns=["book"]).to_csv(out_dir / "book_market_superiority.csv", index=False)
    if "snapshot_type" in eml.columns:
        g = eml.groupby(eml["snapshot_type"].astype(str), dropna=False)
        sr = []
        for k, sub in g:
            sr.append({"snapshot_type": k, **_agg_segment(sub, min_scored=args.min_scored_rows, min_joined=args.min_market_joined_rows)})
        pd.DataFrame(sr).to_csv(out_dir / "snapshot_market_superiority.csv", index=False)
    else:
        pd.DataFrame(columns=["snapshot_type"]).to_csv(out_dir / "snapshot_market_superiority.csv", index=False)

    present_stats = set(eml["stat"].astype(str).str.lower().unique())
    missing_required = [s for s in REQUIRED_STATS if s not in present_stats]

    matched_eml = eml[eml.get("join_status", "") == "matched"] if "join_status" in eml.columns else eml.iloc[0:0]
    stats_with_matched = set(matched_eml["stat"].astype(str).str.lower().unique()) if len(matched_eml) else set()
    required_stats_without_event_market_coverage = [s for s in REQUIRED_STATS if s not in stats_with_matched]
    required_stats_with_event_market_coverage = [s for s in REQUIRED_STATS if s in stats_with_matched]

    audit_reasons = _load_audit_final_reasons(label)

    def _audit_bucket(reason: str) -> list[str]:
        return sorted({s for s, r in audit_reasons.items() if r == reason})

    no_offered = _audit_bucket("no_offered_market")
    not_requested = _audit_bucket("not_requested_from_odds_api")
    parser_dropped = _audit_bucket("processed_parser_dropped_market")
    join_failed = _audit_bucket("event_market_join_failed")

    n_pass = int(df_sr["market_superiority_pass"].sum()) if len(df_sr) else 0
    n_fail = int((~df_sr["market_superiority_pass"]).sum()) if len(df_sr) else 0
    elig = df_sr[df_sr["market_superiority_eligible"] == True]
    blocked_reasons = Counter(df_sr.loc[~df_sr["market_superiority_pass"], "failure_reason"].astype(str))

    global_ok = (
        len(elig) > 0
        and bool(elig["market_superiority_pass"].all())
        and not missing_required
        and len(required_stats_without_event_market_coverage) == 0
    )

    market_subset_stats = sorted(stats_with_matched & set(REQUIRED_STATS))
    sub_df = df_sr[df_sr["stat"].isin(market_subset_stats)]
    sub_elig = sub_df[sub_df["market_superiority_eligible"] == True]
    eligible_subset_claim = bool(
        len(sub_elig) > 0 and sub_elig["market_superiority_pass"].all()
    )

    model_cal_ok = model_only_calibration_claim_allowed(REPO_ROOT)

    claim_blockers: list[dict] = []
    if missing_required:
        claim_blockers.append(
            {"kind": "stats_absent_from_event_market_loss_rows", "stats": missing_required}
        )
    if required_stats_without_event_market_coverage:
        claim_blockers.append(
            {
                "kind": "stats_without_matched_market_join",
                "stats": required_stats_without_event_market_coverage,
            }
        )
    if len(elig) == 0:
        claim_blockers.append(
            {
                "kind": "no_eligible_stat_role_segments",
                "detail": f"need n_scored>={args.min_scored_rows} and n_market_joined>={args.min_market_joined_rows}",
            }
        )
    else:
        failed_elig = elig[~elig["market_superiority_pass"]]
        if len(failed_elig) > 0:
            claim_blockers.append(
                {
                    "kind": "eligible_segments_failed_market_superiority",
                    "count": int(len(failed_elig)),
                    "failure_reasons": failed_elig["failure_reason"].astype(str).value_counts().head(12).to_dict(),
                }
            )
    if not global_ok and not claim_blockers:
        claim_blockers.append({"kind": "global_superiority_gate_failed", "detail": "see segment metrics"})

    summary = {
        "date": label,
        "dates_used": dates_used,
        "date_range": {"start": meta.get("start_date"), "end": meta.get("end_date")}
        if meta.get("mode") == "date_range"
        else None,
        "dates_file_mode": meta.get("mode") == "dates_file",
        "dates_fingerprint": meta.get("dates_fingerprint"),
        "global_market_superiority_claim_allowed": global_ok,
        "eligible_market_subset_superiority_claim_allowed": eligible_subset_claim,
        "model_only_calibration_claim_allowed": model_cal_ok,
        "required_stats_total": len(REQUIRED_STATS),
        "required_stats_with_event_market_coverage": required_stats_with_event_market_coverage,
        "required_stats_without_event_market_coverage": required_stats_without_event_market_coverage,
        "no_offered_market_stats": no_offered,
        "not_requested_market_stats": not_requested,
        "parser_dropped_market_stats": parser_dropped,
        "join_failed_market_stats": join_failed,
        "insufficient_sample_stats": _audit_bucket("insufficient_scored_rows"),
        "eligible_segments_total": int(len(elig)),
        "eligible_segments_passed": int(elig["market_superiority_pass"].sum()) if len(elig) else 0,
        "eligible_segments_failed": int((~elig["market_superiority_pass"]).sum()) if len(elig) else 0,
        "blocked_segments_total": int(n_fail),
        "blocked_segment_reasons": dict(blocked_reasons),
        "claim_blockers": claim_blockers,
        "n_segments_total": int(len(df_sr)),
        "n_segments_passed": n_pass,
        "n_segments_failed": n_fail,
        "required_stats_missing_in_event_rows": missing_required,
        "min_scored_rows": args.min_scored_rows,
        "min_market_joined_rows": args.min_market_joined_rows,
    }
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from event_line_calibration import merge_event_calibration_report_meta  # noqa: E402

    summary.update(
        merge_event_calibration_report_meta(REPO_ROOT, label, args.event_calibration_model)
    )
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"STAT_ROLE_MARKET_SUPERIORITY_REPORT_PASS out={out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
