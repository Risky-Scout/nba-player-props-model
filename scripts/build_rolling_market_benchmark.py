"""Phase 13K — build a rolling model-vs-market benchmark.

Aggregates per-slate after-game model-vs-market scoring artifacts across a
trailing window (default 28 days, ending on as_of_date inclusive). Used by
``scripts/validate_champion_vs_challenger.py`` to gate promotion on real,
multi-slate market evidence.

Usage:
    python3 scripts/build_rolling_market_benchmark.py --as-of-date YYYY-MM-DD
    python3 scripts/build_rolling_market_benchmark.py --as-of-date YYYY-MM-DD --window-days 28

Outputs:
    artifacts/market_benchmark/<as_of_date>/rolling_market_benchmark.json
    artifacts/market_benchmark/<as_of_date>/rolling_market_benchmark.md

Pass line:  ROLLING_MARKET_BENCHMARK_PASS
Fail line:  ROLLING_MARKET_BENCHMARK_FAILED  (non-fatal — the validator
            applies its own market gates with insufficient-sample handling)

Hard rules:
- Reads only from delivery dates ``<= as_of_date``. No future leakage.
- Aggregates rows where both `model_logloss` and `market_logloss` are
  populated AND the row is a non-push.
- Insufficient-sample is reported explicitly, never silently passed.
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
    parse_date,
    utcnow_iso,
    write_json_atomic,
)


DELIVERIES_DIR = REPO_ROOT / "deliveries"
BENCHMARK_DIR = REPO_ROOT / "artifacts" / "market_benchmark"

# Sample-size policy. The validator applies stricter thresholds for hard
# gates; this script reports the raw aggregations and a pass/fail signal
# based on whether the overall sample meets the floor used by the gate.
DEFAULT_WINDOW_DAYS = 28
MIN_OVERALL_ROWS = 500
MIN_BUCKET_ROWS = 50


def _list_dates_in_window(as_of: dt.date, window_days: int) -> list[dt.date]:
    return [as_of - dt.timedelta(days=i) for i in range(window_days)]


def _collect_rows_from_per_slate_json(date_dir: Path) -> dict | None:
    """Per-slate model_vs_market_scoring.json — overall + by_stat blocks."""
    p = date_dir / "after_game_scoring" / "model_vs_market_scoring.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def _collect_rows_from_per_slate_csv(date_dir: Path):
    """Per-slate model_vs_market_scoring.csv — full row-level paired data."""
    p = date_dir / "after_game_scoring" / "model_vs_market_scoring.csv"
    if not p.exists():
        return None
    try:
        import pandas as pd
        return pd.read_csv(p)
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build rolling model-vs-market benchmark.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD (inclusive end of window)")
    p.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS,
                   help=f"Trailing window size in days (default {DEFAULT_WINDOW_DAYS}).")
    p.add_argument("--min-overall-rows", type=int, default=MIN_OVERALL_ROWS)
    p.add_argument("--min-bucket-rows", type=int, default=MIN_BUCKET_ROWS)
    args = p.parse_args(argv)

    as_of = parse_date(args.as_of_date)
    window = _list_dates_in_window(as_of, args.window_days)
    out_dir = BENCHMARK_DIR / as_of.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import pandas as pd
    except ImportError:
        print("ROLLING_MARKET_BENCHMARK_FAILED", file=sys.stderr)
        print("  reason: pandas not installed", file=sys.stderr)
        return 1

    dates_included: list[str] = []
    dates_missing: list[str] = []
    per_slate_summaries: list[dict] = []
    row_frames: list = []
    for d in window:
        dd = DELIVERIES_DIR / d.isoformat()
        if not dd.exists():
            dates_missing.append(d.isoformat())
            continue
        summary = _collect_rows_from_per_slate_json(dd)
        rows_csv = _collect_rows_from_per_slate_csv(dd)
        if summary is None and rows_csv is None:
            dates_missing.append(d.isoformat())
            continue
        dates_included.append(d.isoformat())
        if summary is not None:
            per_slate_summaries.append({
                "date": d.isoformat(),
                "rows_total": summary.get("rows_total"),
                "rows_paired": summary.get("rows_paired"),
                "overall": summary.get("overall"),
            })
        if rows_csv is not None and not rows_csv.empty:
            rows_csv = rows_csv.assign(_slate_date=d.isoformat())
            row_frames.append(rows_csv)

    payload: dict = {
        "schema_version": "1.0",
        "as_of_date": as_of.isoformat(),
        "window_days": args.window_days,
        "window_start": (as_of - dt.timedelta(days=args.window_days - 1)).isoformat(),
        "window_end": as_of.isoformat(),
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "min_overall_rows": args.min_overall_rows,
        "min_bucket_rows": args.min_bucket_rows,
        "dates_included": dates_included,
        "dates_missing": dates_missing,
        "per_slate_summaries": per_slate_summaries,
        "rows_total": 0,
        "rows_non_push": 0,
        "model_logloss": None,
        "market_logloss": None,
        "delta_logloss": None,
        "model_brier": None,
        "market_brier": None,
        "delta_brier": None,
        "by_stat": [],
        "by_role_bucket": [],
        "by_edge_bucket": [],
        "minimum_sample_passed": False,
        "minimum_sample_passed_per_stat": {},
        "status": "insufficient_sample",
    }

    if not row_frames:
        # No CSVs — derive overall delta from the per-slate summaries
        # weighted by rows_paired. This is approximate but better than
        # nothing.
        if per_slate_summaries:
            tot_rows = sum((s.get("rows_paired") or 0) for s in per_slate_summaries)
            payload["rows_total"] = tot_rows
            payload["rows_non_push"] = tot_rows
            if tot_rows > 0:
                def _wmean(field):
                    num = sum(
                        (s.get("overall") or {}).get(field, 0.0) * (s.get("rows_paired") or 0)
                        for s in per_slate_summaries
                        if s.get("overall")
                    )
                    return float(num / tot_rows) if tot_rows else None
                payload["model_logloss"] = _wmean("model_logloss")
                payload["market_logloss"] = _wmean("market_logloss")
                payload["delta_logloss"] = _wmean("delta_logloss")
                payload["model_brier"] = _wmean("model_brier")
                payload["market_brier"] = _wmean("market_brier")
                payload["delta_brier"] = _wmean("delta_brier")
                payload["minimum_sample_passed"] = bool(tot_rows >= args.min_overall_rows)
                payload["status"] = ("ok" if payload["minimum_sample_passed"]
                                      else "insufficient_sample")
        write_json_atomic(out_dir / "rolling_market_benchmark.json", payload)
        _write_md(out_dir, payload)
        if payload["minimum_sample_passed"]:
            print("ROLLING_MARKET_BENCHMARK_PASS")
            print(
                f"  rows_total={payload['rows_total']} dates_included={len(dates_included)} "
                f"delta_logloss={payload['delta_logloss']:+.4f} "
                f"delta_brier={payload['delta_brier']:+.4f}"
            )
            return 0
        print("ROLLING_MARKET_BENCHMARK_FAILED", file=sys.stderr)
        print(
            f"  reason: insufficient_sample rows_total={payload['rows_total']} "
            f"min_required={args.min_overall_rows}",
            file=sys.stderr,
        )
        return 1

    df = pd.concat(row_frames, ignore_index=True)
    df = df.dropna(subset=["model_logloss", "market_logloss"])
    if "is_push" in df.columns:
        df = df[~df["is_push"].astype(bool, copy=False)]
    payload["rows_total"] = int(len(df))
    payload["rows_non_push"] = int(len(df))

    if df.empty:
        write_json_atomic(out_dir / "rolling_market_benchmark.json", payload)
        _write_md(out_dir, payload)
        print("ROLLING_MARKET_BENCHMARK_FAILED", file=sys.stderr)
        print("  reason: zero paired non-push rows in window", file=sys.stderr)
        return 1

    payload["model_logloss"] = float(df["model_logloss"].mean())
    payload["market_logloss"] = float(df["market_logloss"].mean())
    payload["delta_logloss"] = float((df["model_logloss"] - df["market_logloss"]).mean())
    payload["model_brier"] = float(df["model_brier"].mean())
    payload["market_brier"] = float(df["market_brier"].mean())
    payload["delta_brier"] = float((df["model_brier"] - df["market_brier"]).mean())

    def _by(group_col: str) -> list:
        if group_col not in df.columns:
            return []
        rows = []
        for k, sub in df.groupby(group_col, dropna=False):
            n = int(len(sub))
            rec = {
                group_col: (str(k) if k is not None else "unknown"),
                "n": n,
                "minimum_sample_passed": bool(n >= args.min_bucket_rows),
            }
            if n > 0:
                rec.update({
                    "model_logloss": float(sub["model_logloss"].mean()),
                    "market_logloss": float(sub["market_logloss"].mean()),
                    "delta_logloss": float((sub["model_logloss"] - sub["market_logloss"]).mean()),
                    "model_brier": float(sub["model_brier"].mean()),
                    "market_brier": float(sub["market_brier"].mean()),
                    "delta_brier": float((sub["model_brier"] - sub["market_brier"]).mean()),
                })
            rows.append(rec)
        return rows

    payload["by_stat"] = _by("stat")
    payload["by_role_bucket"] = _by("role_bucket")
    if "_edge_bucket" in df.columns:
        payload["by_edge_bucket"] = _by("_edge_bucket")
    payload["minimum_sample_passed"] = bool(payload["rows_total"] >= args.min_overall_rows)
    payload["minimum_sample_passed_per_stat"] = {
        rec["stat"]: rec["minimum_sample_passed"] for rec in payload["by_stat"]
    }
    payload["status"] = ("ok" if payload["minimum_sample_passed"] else "insufficient_sample")

    write_json_atomic(out_dir / "rolling_market_benchmark.json", payload)
    _write_md(out_dir, payload)

    if payload["minimum_sample_passed"]:
        print("ROLLING_MARKET_BENCHMARK_PASS")
        print(
            f"  rows_total={payload['rows_total']} dates_included={len(dates_included)} "
            f"delta_logloss={payload['delta_logloss']:+.4f} "
            f"delta_brier={payload['delta_brier']:+.4f}"
        )
        return 0
    print("ROLLING_MARKET_BENCHMARK_FAILED", file=sys.stderr)
    print(
        f"  reason: insufficient_sample rows_total={payload['rows_total']} "
        f"min_required={args.min_overall_rows} "
        f"dates_included={len(dates_included)} dates_missing={len(dates_missing)}",
        file=sys.stderr,
    )
    return 1


def _write_md(out_dir: Path, payload: dict) -> None:
    md = [
        f"# Rolling Model-vs-Market Benchmark — {payload['as_of_date']}",
        "",
        f"- window: {payload['window_start']} → {payload['window_end']} "
        f"({payload['window_days']} days)",
        f"- dates_included: {len(payload['dates_included'])}",
        f"- dates_missing: {len(payload['dates_missing'])}",
        f"- rows_total: {payload['rows_total']}",
        f"- rows_non_push: {payload['rows_non_push']}",
        f"- minimum_sample_passed: **{payload['minimum_sample_passed']}** "
        f"(min_overall_rows={payload['min_overall_rows']})",
        f"- status: **{payload['status']}**",
        "",
    ]
    if payload["model_logloss"] is not None:
        md += [
            f"- model_logloss: **{payload['model_logloss']:.4f}**",
            f"- market_logloss: **{payload['market_logloss']:.4f}**",
            f"- delta_logloss: **{payload['delta_logloss']:+.4f}** (negative favors model)",
            f"- model_brier: **{payload['model_brier']:.4f}**",
            f"- market_brier: **{payload['market_brier']:.4f}**",
            f"- delta_brier: **{payload['delta_brier']:+.4f}** (negative favors model)",
            "",
        ]
    if payload["by_stat"]:
        md += ["## By stat", "", "| stat | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier | sample_pass |",
               "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
        for r in payload["by_stat"]:
            md.append(
                f"| {r['stat']} | {r['n']} | "
                f"{(r.get('model_logloss') or 0.0):.4f} | "
                f"{(r.get('market_logloss') or 0.0):.4f} | "
                f"{(r.get('delta_logloss') or 0.0):+.4f} | "
                f"{(r.get('model_brier') or 0.0):.4f} | "
                f"{(r.get('market_brier') or 0.0):.4f} | "
                f"{(r.get('delta_brier') or 0.0):+.4f} | "
                f"{r['minimum_sample_passed']} |"
            )
        md.append("")
    if payload["dates_missing"]:
        md += ["## Dates missing", "", *(f"- {d}" for d in payload["dates_missing"][:10]), ""]
    (out_dir / "rolling_market_benchmark.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
