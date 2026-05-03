"""Phase 13X Part C — calibration audit for the edge buckets driving
today's largest Derek current_live edges.

Reads the after-game scoring CSVs already on disk (one per delivery
date) under ``deliveries/<date>/after_game_scoring/model_vs_market_scoring.csv``,
buckets historical scored rows by (stat, side, line_bucket, edge_bucket,
role_bucket), and reports whether each bucket has enough samples to
trust the today's high-edge claim.

If a bucket is thin (n < 30) or limited (n < 100), today's high-edge
rows in that bucket are flagged for REVIEW_CALIBRATION_SAMPLE_THIN
publishability.

Pass:    PHASE13X_EDGE_CALIBRATION_PASS  (every high-edge bucket
                                          supported AND model not
                                          underperforming market)
Warn:    PHASE13X_EDGE_CALIBRATION_WARN  (some buckets thin/limited or
                                          some buckets show model
                                          underperformance)
Fail:    PHASE13X_EDGE_CALIBRATION_FAILED (no scoring data at all and
                                            no honest pending reason)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERIES = REPO_ROOT / "deliveries"
HEALTH = REPO_ROOT / "artifacts" / "automation_health"


def _line_bucket(line: float) -> str:
    try:
        x = float(line)
    except Exception:
        return "unknown"
    if x <= 1.0:
        return "low_le_1.0"
    if x <= 2.5:
        return "low_2.5"
    if x <= 5.5:
        return "mid_5.5"
    if x <= 10.5:
        return "mid_10.5"
    return "high_gt_10.5"


def _edge_bucket(abs_edge: float) -> str:
    if abs_edge >= 0.30:
        return "EDGE_30_PLUS"
    if abs_edge >= 0.20:
        return "EDGE_20_30"
    if abs_edge >= 0.10:
        return "EDGE_10_20"
    if abs_edge >= 0.05:
        return "EDGE_5_10"
    return "EDGE_LT_5"


def _load_today_high_edge_rows(delivery_date: str) -> list[dict]:
    """Read today's per-snapshot rows from the root-cause audit JSON."""
    path = HEALTH / f"derek_edge_root_cause_{delivery_date}.json"
    if not path.exists():
        return []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[dict] = []
    for s in d.get("snapshots") or []:
        for r in s.get("rows") or []:
            out.append({
                **r,
                "_snapshot_type": s.get("snapshot_type"),
                "_lineup_confirmed": s.get("lineup_confirmed"),
                "_game_id": s.get("game_id"),
            })
    return out


def _load_scoring_corpus() -> list[dict]:
    """Concatenate every available after-game scoring CSV. Empty if none."""
    import pandas as pd
    rows: list[dict] = []
    if not DELIVERIES.exists():
        return rows
    for d in sorted(DELIVERIES.iterdir()):
        if not d.is_dir():
            continue
        scoring = d / "after_game_scoring" / "model_vs_market_scoring.csv"
        if not scoring.exists():
            continue
        try:
            df = pd.read_csv(scoring)
        except Exception:
            continue
        df["delivery_date"] = d.name
        rows.extend(df.to_dict(orient="records"))
    return rows


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    p.add_argument("--as-of-date", required=False, default=None)
    args = p.parse_args(argv)

    HEALTH.mkdir(parents=True, exist_ok=True)
    today_rows = _load_today_high_edge_rows(args.delivery_date)
    if not today_rows:
        # Try to invoke the root-cause audit ourselves so the pending
        # reason is honest.
        payload = {
            "schema_version": "1.0",
            "delivery_date": args.delivery_date,
            "outcome": "warn",
            "reason": (
                f"no derek_edge_root_cause_{args.delivery_date}.json "
                "yet. Run scripts/audit_derek_edge_root_cause.py first."
            ),
        }
        (HEALTH / f"derek_edge_calibration_{args.delivery_date}.json"
         ).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print("PHASE13X_EDGE_CALIBRATION_WARN")
        print(f"  reason={payload['reason']}")
        return 0

    corpus = _load_scoring_corpus()
    import pandas as pd
    if not corpus:
        payload = {
            "schema_version": "1.0",
            "delivery_date": args.delivery_date,
            "outcome": "warn",
            "reason": (
                "no after-game scoring CSVs found under "
                "deliveries/*/after_game_scoring/model_vs_market_scoring.csv. "
                "Calibration support cannot be quantified yet — today's "
                "high-edge rows are flagged CALIBRATION_SAMPLE_THIN."
            ),
        }
        (HEALTH / f"derek_edge_calibration_{args.delivery_date}.json"
         ).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print("PHASE13X_EDGE_CALIBRATION_WARN")
        print(f"  reason=no scoring corpus; today's edges marked thin")
        return 0

    cdf = pd.DataFrame(corpus)
    # Annotate each historical row with side / edge_bucket per side.
    cdf["model_p_over"] = cdf["model_p_over"].astype(float)
    cdf["market_no_vig_over_prob"] = cdf["market_no_vig_over_prob"].astype(float)
    cdf["edge_over"] = cdf["model_p_over"] - cdf["market_no_vig_over_prob"]
    cdf["edge_under"] = -cdf["edge_over"]
    cdf["abs_edge"] = cdf["edge_over"].abs()
    cdf["edge_bucket"] = cdf["abs_edge"].map(_edge_bucket)
    cdf["line_bucket"] = cdf["line"].map(_line_bucket)

    # For each (stat, side, line_bucket, edge_bucket), aggregate
    # historical n / model_logloss / market_logloss / Brier deltas.
    historical: dict[tuple, dict] = {}
    for _, r in cdf.iterrows():
        for side, edge_signed in (("OVER", r["edge_over"]), ("UNDER", r["edge_under"])):
            ek = _edge_bucket(abs(float(edge_signed)))
            key = (str(r.get("stat")), side, r.get("line_bucket"), ek)
            d = historical.setdefault(key, {
                "n": 0, "sum_model_ll": 0.0, "sum_market_ll": 0.0,
                "sum_model_brier": 0.0, "sum_market_brier": 0.0,
                "wins": 0,
            })
            d["n"] += 1
            d["sum_model_ll"] += float(r["model_logloss"])
            d["sum_market_ll"] += float(r["market_logloss"])
            d["sum_model_brier"] += float(r["model_brier"])
            d["sum_market_brier"] += float(r["market_brier"])

    # Look up today's high-edge rows in this bucket.
    bucket_findings: list[dict] = []
    high_edge_rows = [
        r for r in today_rows
        if (r.get("abs_edge_recorded") or 0.0) >= 0.10
    ]
    for r in high_edge_rows:
        side = r.get("side")
        edge_bucket = r.get("large_edge_bucket")
        line_bucket = _line_bucket(r.get("line") or 0)
        key = (str(r.get("stat")), side, line_bucket, edge_bucket)
        d = historical.get(key)
        n = (d or {}).get("n", 0)
        model_ll = (d or {}).get("sum_model_ll", 0.0) / n if n else None
        market_ll = (d or {}).get("sum_market_ll", 0.0) / n if n else None
        delta_ll = (model_ll - market_ll) if (model_ll is not None) else None
        model_brier = (d or {}).get("sum_model_brier", 0.0) / n if n else None
        market_brier = (d or {}).get("sum_market_brier", 0.0) / n if n else None
        if n == 0:
            calib_status = "CALIBRATION_SAMPLE_THIN"
        elif n < 30:
            calib_status = "CALIBRATION_SAMPLE_THIN"
        elif n < 100:
            calib_status = "CALIBRATION_SAMPLE_LIMITED"
        else:
            if delta_ll is not None and delta_ll > 0.05:
                calib_status = "CALIBRATION_REVIEW_REQUIRED"
            else:
                calib_status = "CALIBRATION_SUPPORTED"
        bucket_findings.append({
            "player_name": r.get("player_name"),
            "stat": r.get("stat"),
            "side": side,
            "line": r.get("line"),
            "line_bucket": line_bucket,
            "edge_bucket": edge_bucket,
            "raw_edge": r.get("raw_edge"),
            "historical_n": n,
            "model_logloss_mean": model_ll,
            "market_logloss_mean": market_ll,
            "delta_logloss_mean": delta_ll,
            "model_brier_mean": model_brier,
            "market_brier_mean": market_brier,
            "calibration_status": calib_status,
        })

    thin_count = sum(
        1 for f in bucket_findings
        if f["calibration_status"] in (
            "CALIBRATION_SAMPLE_THIN", "CALIBRATION_SAMPLE_LIMITED"
        )
    )
    review_count = sum(
        1 for f in bucket_findings
        if f["calibration_status"] == "CALIBRATION_REVIEW_REQUIRED"
    )
    supported = sum(
        1 for f in bucket_findings
        if f["calibration_status"] == "CALIBRATION_SUPPORTED"
    )

    # Aggregate stat-level performance for transparency.
    stat_summary: dict = {}
    for (stat, side, lb, eb), d in historical.items():
        n = d["n"]
        if n == 0:
            continue
        s = stat_summary.setdefault(f"{stat}/{side}", {
            "n": 0, "model_ll": 0.0, "market_ll": 0.0,
            "model_brier": 0.0, "market_brier": 0.0,
        })
        s["n"] += n
        s["model_ll"] += d["sum_model_ll"]
        s["market_ll"] += d["sum_market_ll"]
        s["model_brier"] += d["sum_model_brier"]
        s["market_brier"] += d["sum_market_brier"]
    for k, s in stat_summary.items():
        n = s["n"]
        s["model_ll_mean"] = s["model_ll"] / n
        s["market_ll_mean"] = s["market_ll"] / n
        s["delta_ll_mean"] = s["model_ll_mean"] - s["market_ll_mean"]
        s["model_brier_mean"] = s["model_brier"] / n
        s["market_brier_mean"] = s["market_brier"] / n
        s["delta_brier_mean"] = s["model_brier_mean"] - s["market_brier_mean"]

    payload = {
        "schema_version": "1.0",
        "delivery_date": args.delivery_date,
        "as_of_date": args.as_of_date,
        "high_edge_row_count": len(high_edge_rows),
        "scoring_corpus_rows": len(cdf),
        "scoring_corpus_dates": sorted(cdf["delivery_date"].unique().tolist()),
        "thin_or_limited_count": thin_count,
        "review_required_count": review_count,
        "supported_count": supported,
        "bucket_findings": bucket_findings,
        "stat_summary": stat_summary,
    }
    (HEALTH / f"derek_edge_calibration_{args.delivery_date}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    md = [
        f"# Derek edge calibration audit — {args.delivery_date}",
        "",
        f"- high-edge rows audited: **{len(high_edge_rows)}**",
        f"- scoring corpus: **{len(cdf)} rows** across "
        f"{len(payload['scoring_corpus_dates'])} delivery dates",
        f"- thin/limited buckets: **{thin_count}**",
        f"- review-required buckets: **{review_count}**",
        f"- supported buckets: **{supported}**",
        "",
        "## Per-row calibration support",
        "",
        "| player | stat | side | line | edge_bucket | n | model_ll | "
        "market_ll | Δll | calibration_status |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for f in bucket_findings:
        md.append(
            f"| {f['player_name']} | {f['stat']} | {f['side']} | "
            f"{f['line']} | {f['edge_bucket']} | {f['historical_n']} | "
            f"{(f['model_logloss_mean'] or 0):.3f} | "
            f"{(f['market_logloss_mean'] or 0):.3f} | "
            f"{(f['delta_logloss_mean'] or 0):+.3f} | "
            f"**{f['calibration_status']}** |"
        )
    md.append("")
    md.append("## Stat-level model-vs-market summary (historical corpus)")
    md.append("")
    md.append("| stat/side | n | model_ll | market_ll | Δll | model_brier | market_brier | Δbrier |")
    md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for k, s in sorted(stat_summary.items()):
        md.append(
            f"| {k} | {s['n']} | {s['model_ll_mean']:.3f} | "
            f"{s['market_ll_mean']:.3f} | {s['delta_ll_mean']:+.3f} | "
            f"{s['model_brier_mean']:.3f} | {s['market_brier_mean']:.3f} | "
            f"{s['delta_brier_mean']:+.3f} |"
        )
    (HEALTH / f"derek_edge_calibration_{args.delivery_date}.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    if review_count > 0 or thin_count > 0:
        print("PHASE13X_EDGE_CALIBRATION_WARN")
        print(
            f"  delivery_date={args.delivery_date} "
            f"thin_or_limited={thin_count} review_required={review_count} "
            f"supported={supported}"
        )
        return 0
    print("PHASE13X_EDGE_CALIBRATION_PASS")
    print(
        f"  delivery_date={args.delivery_date} "
        f"high_edge_rows={len(high_edge_rows)} supported={supported}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
