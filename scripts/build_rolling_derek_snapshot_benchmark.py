"""Phase 13M-bis Part L — rolling prospective benchmark for Derek snapshots.

Aggregates after-game snapshot scoring across a rolling window
(default 28 days, ending at ``--as-of-date``) and emits prospective
calibration / market-superiority metrics. Does NOT fabricate
superiority — when the sample is insufficient it reports
``DEREK_LIVE_SNAPSHOT_BENCHMARK_INSUFFICIENT_SAMPLE``.

Usage:
    python3 scripts/build_rolling_derek_snapshot_benchmark.py \\
        --as-of-date YYYY-MM-DD --window-days 28

Pass line:
    DEREK_LIVE_SNAPSHOT_BENCHMARK_PASS
Insufficient-sample line:
    DEREK_LIVE_SNAPSHOT_BENCHMARK_INSUFFICIENT_SAMPLE
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    git_commit,
    read_json,
    utcnow_iso,
    write_json_atomic,
)


DELIVERIES_DIR = REPO_ROOT / "deliveries"
ROLLUP_DIR = REPO_ROOT / "artifacts" / "derek_live_snapshots"

MIN_SAMPLE_ROWS = 200  # below this we refuse to claim performance


def _date_range(end: dt.date, days: int):
    return [end - dt.timedelta(days=i) for i in range(days)]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Rolling Derek snapshot benchmark.")
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--window-days", type=int, default=28)
    args = p.parse_args(argv)

    end = dt.date.fromisoformat(args.as_of_date)
    dates = _date_range(end, args.window_days)
    out_dir = ROLLUP_DIR / args.as_of_date
    out_dir.mkdir(parents=True, exist_ok=True)

    dates_included: list[str] = []
    dates_missing: list[str] = []
    rows_total = 0
    rows_by_snapshot_type: dict = {"t_minus_25": 0, "close_lock": 0}
    sums: dict = {}  # accumulator for per-snapshot-type metrics

    for d in sorted(dates):
        date_str = d.isoformat()
        agg_path = (
            DELIVERIES_DIR / date_str / "derek_game_snapshots"
            / "aggregate_snapshot_scoring.json"
        )
        if not agg_path.exists():
            dates_missing.append(date_str)
            continue
        try:
            agg = read_json(agg_path)
        except Exception:
            dates_missing.append(date_str)
            continue
        if agg.get("status") != "scored":
            dates_missing.append(date_str)
            continue
        dates_included.append(date_str)
        for gid, per_game in (agg.get("by_game") or {}).items():
            for stype, res in (per_game or {}).items():
                if not isinstance(res, dict) or not res.get("present") or res.get("blocker"):
                    continue
                matched = int(res.get("matched_rows") or 0)
                rows_total += matched
                if stype in rows_by_snapshot_type:
                    rows_by_snapshot_type[stype] += matched
                bucket = sums.setdefault(stype, {
                    "rows": 0, "nll_sum": 0.0,
                    "model_logloss_sum": 0.0, "market_logloss_sum": 0.0,
                    "n_logloss": 0,
                })
                bucket["rows"] += matched
                if res.get("mean_nll") is not None:
                    bucket["nll_sum"] += float(res["mean_nll"]) * matched
                if (res.get("model_logloss_vs_over") is not None
                        and res.get("market_logloss_vs_over") is not None):
                    bucket["model_logloss_sum"] += float(res["model_logloss_vs_over"]) * matched
                    bucket["market_logloss_sum"] += float(res["market_logloss_vs_over"]) * matched
                    bucket["n_logloss"] += matched

    rollup: dict = {
        "schema_version": "1.0",
        "as_of_date": args.as_of_date,
        "window_days": args.window_days,
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "dates_included": dates_included,
        "dates_missing": dates_missing,
        "rows_total": rows_total,
        "rows_by_snapshot_type": rows_by_snapshot_type,
        "minimum_sample_passed": rows_total >= MIN_SAMPLE_ROWS,
    }
    by_type: dict = {}
    for stype, bucket in sums.items():
        if bucket["rows"] == 0:
            continue
        by_type[stype] = {
            "rows": bucket["rows"],
            "mean_nll": (
                bucket["nll_sum"] / bucket["rows"]
                if bucket["rows"] else None
            ),
            "model_logloss_vs_over": (
                bucket["model_logloss_sum"] / bucket["n_logloss"]
                if bucket["n_logloss"] else None
            ),
            "market_logloss_vs_over": (
                bucket["market_logloss_sum"] / bucket["n_logloss"]
                if bucket["n_logloss"] else None
            ),
        }
        if (
            by_type[stype]["model_logloss_vs_over"] is not None
            and by_type[stype]["market_logloss_vs_over"] is not None
        ):
            by_type[stype]["delta_logloss_model_minus_market"] = (
                by_type[stype]["model_logloss_vs_over"]
                - by_type[stype]["market_logloss_vs_over"]
            )
    rollup["by_snapshot_type"] = by_type

    write_json_atomic(out_dir / "rolling_derek_snapshot_benchmark.json", rollup)
    md = [
        f"# Rolling Derek snapshot benchmark — as-of {args.as_of_date}",
        "",
        f"- window_days: {args.window_days}",
        f"- generated_at_utc: {rollup['generated_at_utc']}",
        f"- dates_included: {len(dates_included)}",
        f"- dates_missing: {len(dates_missing)}",
        f"- rows_total: {rows_total}",
        f"- minimum_sample_passed (>={MIN_SAMPLE_ROWS}): "
        f"**{rollup['minimum_sample_passed']}**",
        "",
        "## By snapshot type",
        "",
        "| snapshot_type | rows | mean_nll | model_logloss | market_logloss | Δ (model−market) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for stype, m in by_type.items():
        md.append(
            f"| {stype} | {m['rows']} | {m.get('mean_nll')} | "
            f"{m.get('model_logloss_vs_over')} | "
            f"{m.get('market_logloss_vs_over')} | "
            f"{m.get('delta_logloss_model_minus_market')} |"
        )
    (out_dir / "rolling_derek_snapshot_benchmark.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    if not rollup["minimum_sample_passed"]:
        print("DEREK_LIVE_SNAPSHOT_BENCHMARK_INSUFFICIENT_SAMPLE")
        print(
            f"  rows_total={rows_total} < min={MIN_SAMPLE_ROWS}; "
            f"dates_included={len(dates_included)}/{args.window_days}"
        )
        return 0
    print("DEREK_LIVE_SNAPSHOT_BENCHMARK_PASS")
    print(f"  rows_total={rows_total} dates_included={len(dates_included)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
