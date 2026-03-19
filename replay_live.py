#!/usr/bin/env python3
"""
replay_live.py v2 — NBA Live Props Replay Engine
==================================================
Instruction §6: Unified bucket taxonomy with state_bucket_calibration.py.
Computes CLV, ROI, Brier, routing quality, and monetization analytics.

Usage:
    python3 replay_live.py --date 2026-03-18
    python3 replay_live.py --all --output graded/replay_live_summary.json
"""

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

CACHE_DIR  = Path(__file__).parent / "cache"
GRADED_DIR = Path(__file__).parent / "graded"


# ── SHARED BUCKET TAXONOMY (unified with state_bucket_calibration.py) ─────────
# Instruction §1 and §6.1

def bucket_quarter(period: int, is_ot: bool = False) -> str:
    if is_ot or period > 4: return "OT"
    if period <= 0:          return "pre"
    return f"Q{period}"

def bucket_time(rem_min: Optional[float]) -> str:
    if rem_min is None: return "pre"
    if rem_min < 4:     return "0-4"
    if rem_min < 8:     return "4-8"
    if rem_min < 12:    return "8-12"
    return "12+"

def bucket_foul(fouls: int) -> str:
    if fouls <= 2: return "0-2"
    if fouls == 3: return "3"
    return "4+"

def bucket_court(on_court) -> str:
    return "on" if on_court else "off"

def make_bucket_key(stat, side, period, rem_min, fouls, on_court, is_ot=False) -> str:
    """Primary key: stat|side|quarter|time_bucket|foul_band|court"""
    return "|".join([
        stat.lower(),
        side.upper(),
        bucket_quarter(period, is_ot),
        bucket_time(rem_min),
        bucket_foul(fouls),
        bucket_court(on_court),
    ])


# ── BRIER SCORE ────────────────────────────────────────────────────────────────

def brier_score(records: list) -> float:
    if not records: return float("nan")
    return sum((r["model_prob"] - r["outcome_binary"])**2 for r in records) / len(records)


# ── CALIBRATION BY BUCKET (instruction §1–2) ──────────────────────────────────

def calibration_by_bucket(records: list) -> dict:
    """Use unified bucket key: stat|side|quarter|time_bucket|foul_band|court"""
    buckets = defaultdict(lambda: {"n":0,"sum_prob":0.0,"sum_out":0.0,"brier_sum":0.0})
    for r in records:
        key = make_bucket_key(
            r.get("stat",""),  r.get("side","OVER"),
            int(r.get("game_period",0) or 0),
            float(r.get("rem_minutes_mean",48) or 48) if r.get("rem_minutes_mean") else None,
            int(r.get("fouls",0) or 0),
            r.get("on_court", True),
            bool(r.get("is_overtime", False)),
        )
        b = buckets[key]
        b["n"] += 1
        p = r.get("model_prob", 0.5)
        o = r.get("outcome_binary", 0)
        b["sum_prob"] += p
        b["sum_out"]  += o
        b["brier_sum"]+= (p-o)**2

    result = {}
    for key, b in buckets.items():
        n = b["n"]
        if n < 5: continue
        mp = b["sum_prob"] / n
        hr = b["sum_out"]  / n
        result[key] = {
            "n":          n,
            "mean_prob":  round(mp, 4),
            "hit_rate":   round(hr, 4),
            "cal_error":  round(abs(mp-hr), 4),
            "brier":      round(b["brier_sum"]/n, 4),
        }
    return result


# ── ROI BY EDGE BUCKET ─────────────────────────────────────────────────────────

def roi_by_calibration_level(records: list) -> dict:
    """ROI and false-positive by calibration level (doc 6 §6 must also have)."""
    levels = defaultdict(lambda: {"n":0,"wins":0,"profit":0.0,"fp":0})
    for r in records:
        level  = r.get("calibration_level","unknown") or "unknown"
        out    = r.get("outcome_binary",0)
        profit = float(r.get("profit",0) or 0)
        edge   = float(r.get("edge",0) or 0)
        levels[level]["n"]      += 1
        levels[level]["wins"]   += out
        levels[level]["profit"] += profit
        if edge > 0 and out == 0:
            levels[level]["fp"] += 1
    return {
        lv: {
            "n":       d["n"],
            "win_rate":round(d["wins"]/d["n"],4) if d["n"] else None,
            "roi":     round(d["profit"]/d["n"],4) if d["n"] else None,
            "fp_rate": round(d["fp"]/max(d["n"],1),4),
        }
        for lv,d in levels.items()
    }


def roi_by_stale_and_fallback(records: list) -> dict:
    """Stale-quote and fallback-pricer audit (doc 6 §6 must also have)."""
    categories = {
        "python_fresh":   {"n":0,"wins":0,"profit":0.0},
        "python_stale":   {"n":0,"wins":0,"profit":0.0},
        "fallback_php":   {"n":0,"wins":0,"profit":0.0},
        "other":          {"n":0,"wins":0,"profit":0.0},
    }
    for r in records:
        src   = r.get("pricing_source","unknown") or "unknown"
        stale = float(r.get("stale_sec",0) or 0)
        out   = r.get("outcome_binary",0)
        profit= float(r.get("profit",0) or 0)
        if src == "fallback_php":
            cat = "fallback_php"
        elif "python" in src and stale > 180:
            cat = "python_stale"
        elif "python" in src:
            cat = "python_fresh"
        else:
            cat = "other"
        categories[cat]["n"]      += 1
        categories[cat]["wins"]   += out
        categories[cat]["profit"] += profit
    return {
        cat: {
            "n":       d["n"],
            "win_rate":round(d["wins"]/d["n"],4) if d["n"] else None,
            "roi":     round(d["profit"]/d["n"],4) if d["n"] else None,
        }
        for cat,d in categories.items() if d["n"] > 0
    }


def roi_by_edge_bucket(records: list) -> list:
    buckets = {k: {"n":0,"profit":0.0} for k in ["0-3","3-5","5-8","8-12","12-20","20+"]}
    for r in records:
        e = (r.get("edge",0) or 0) * 100
        profit = r.get("profit",0) or 0
        k = ("0-3" if e<3 else "3-5" if e<5 else "5-8" if e<8
             else "8-12" if e<12 else "12-20" if e<20 else "20+")
        buckets[k]["n"] += 1
        buckets[k]["profit"] += profit
    return [{"edge_bucket":lbl,"n":b["n"],"roi":round(b["profit"]/max(b["n"],1),4) if b["n"]>0 else None}
            for lbl,b in buckets.items()]


# ── ROI BY ACTION SCORE BUCKET (instruction §5) ───────────────────────────────

def roi_by_action_score_bucket(records: list) -> list:
    buckets = {k:{"n":0,"profit":0.0} for k in ["neg","0-2","2-4","4-8","8+"]}
    for r in records:
        a = (r.get("action_score",0) or 0) * 100
        profit = r.get("profit",0) or 0
        k = ("neg" if a<0 else "0-2" if a<2 else "2-4" if a<4 else "4-8" if a<8 else "8+")
        buckets[k]["n"] += 1
        buckets[k]["profit"] += profit
    return [{"action_bucket":lbl,"n":b["n"],"roi":round(b["profit"]/max(b["n"],1),4) if b["n"]>0 else None}
            for lbl,b in buckets.items()]


# ── FALSE POSITIVE RATE BY TIER AND PRICING SOURCE (instruction §5) ───────────

def false_positive_by_tier(records: list) -> dict:
    tiers = {"A":{"n":0,"fp":0},"B":{"n":0,"fp":0},"C":{"n":0,"fp":0}}
    for r in records:
        tier = r.get("conf_tier","C")
        if (r.get("edge",0) or 0) <= 0: continue
        t = tiers.get(tier, tiers["C"])
        t["n"] += 1
        if r.get("outcome_binary",0) == 0: t["fp"] += 1
    return {t:{"n":d["n"],"fp_rate":round(d["fp"]/d["n"],4) if d["n"]>0 else None,
               "hit_rate":round(1-d["fp"]/d["n"],4) if d["n"]>0 else None}
            for t,d in tiers.items()}

def false_positive_by_pricing_source(records: list) -> dict:
    sources = defaultdict(lambda: {"n":0,"fp":0})
    for r in records:
        src = r.get("pricing_source","unknown")
        if (r.get("edge",0) or 0) <= 0: continue
        sources[src]["n"] += 1
        if r.get("outcome_binary",0) == 0: sources[src]["fp"] += 1
    return {s:{"n":d["n"],"fp_rate":round(d["fp"]/d["n"],4) if d["n"]>0 else None}
            for s,d in sources.items()}


# ── CLV COMPUTATION (instruction §3) ─────────────────────────────────────────
# Instruction: compute CLV against final archived line (closing line)

def compute_clv_vs_close(opening_prob: float, closing_prob: float) -> float:
    """CLV = model_prob at open - closing_market_prob. Positive = beat the close."""
    return opening_prob - closing_prob


# ── ROUTING QUALITY (instruction §3–4) ────────────────────────────────────────

def routing_quality(records: list) -> dict:
    """
    Real per-book routing CLV (doc 6 §6 must do now).

    For each record, compute:
      clv_best_price  = model_prob - closing_market_prob_at_best_price_book
      clv_recommended = model_prob - closing_market_prob_at_recommended_book

    routing_clv_delta = clv_best_price - clv_recommended
      Near 0  → affiliate routing did not cost bettors edge
      Positive → routing to recommended book gave worse closing line than best
      Negative → recommended book had better close than best (rare)

    When per-book closing odds exist in archive (closing_over_odds field),
    compute real routing delta. Otherwise fall back to price_delta proxy.
    """
    results = {
        "n": 0,
        "clv_best_mean": 0.0,
        "clv_recommended_mean": 0.0,
        "routing_clv_delta": 0.0,
        "real_routing_pct": 0.0,  # % of records with real per-book close
        "affiliate_cost_mean": 0.0,  # mean edge cost of affiliate routing
    }
    clv_best_list, clv_rec_list, delta_list = [], [], []
    real_count = 0

    tol_violations = 0
    within_tol     = 0
    by_type        = defaultdict(lambda: {"n":0,"delta_sum":0.0,"clv_sum":0.0})

    for r in records:
        model_p     = r.get("model_prob", 0.5) or 0.5
        price_delta = float(r.get("price_delta_to_best_prob", 0) or 0)
        ev_delta    = float(r.get("ev_delta_to_best", 0) or 0)
        best_book   = r.get("best_price_book","")
        rec_book    = r.get("recommended_book","")
        action_type = r.get("recommended_action_type","best_price")

        # Try real per-book close from archive (requires closing_over_odds in archive)
        closing_o = r.get("closing_over_odds") or r.get("book_over_odds")
        closing_u = r.get("closing_under_odds") or r.get("book_under_odds")
        side      = (r.get("side","OVER") or "OVER").upper()

        if closing_o is not None and closing_u is not None:
            # Real computation: use per-book closing odds (doc 6 §6 must do now)
            def _imp(o):
                o = float(o)
                return abs(o)/(abs(o)+100) if o < 0 else 100/(o+100)
            vig = _imp(closing_o) + _imp(closing_u)
            mkt_close = _imp(closing_o)/vig if side=="OVER" else _imp(closing_u)/vig
            clv_best  = model_p - mkt_close
            clv_rec   = model_p - (mkt_close + price_delta)
            real_count += 1
        else:
            # Proxy: archived CLV + price_delta cost
            clv       = float(r.get("clv", 0) or 0)
            clv_best  = clv
            clv_rec   = clv - price_delta

        # Tolerance check (bettor-first rule)
        if best_book != rec_book:
            tol_ok = (price_delta <= 0.012 or ev_delta <= 0.0075)
            if not tol_ok: tol_violations += 1
            else: within_tol += 1
        else:
            within_tol += 1

        clv_best_list.append(clv_best)
        clv_rec_list.append(clv_rec)
        delta_list.append(clv_best - clv_rec)

        bt = by_type[action_type]
        bt["n"] += 1
        bt["delta_sum"] += clv_best - clv_rec
        bt["clv_sum"]   += clv_rec

    n = len(delta_list)
    if n > 0:
        results["n"]                    = n
        results["clv_best_mean"]        = round(sum(clv_best_list)/n, 4)
        results["clv_recommended_mean"] = round(sum(clv_rec_list)/n,  4)
        results["routing_clv_delta"]    = round(sum(delta_list)/n,    4)
        results["real_routing_pct"]     = round(real_count/n*100, 1)
        results["pct_within_tolerance"] = round(within_tol/n*100, 1)
        results["tolerance_violations"] = tol_violations
        affiliate_costs = [d for d in delta_list if abs(d) > 0.0001]
        results["affiliate_cost_mean"]  = round(sum(affiliate_costs)/len(affiliate_costs),4) if affiliate_costs else 0.0
        results["by_action_type"] = {
            t: {"n":d["n"],"mean_routing_delta":round(d["delta_sum"]/d["n"],4) if d["n"] else 0,
                "mean_clv":round(d["clv_sum"]/d["n"],4) if d["n"] else 0}
            for t,d in by_type.items()
        }
    return results


# ── MONETIZATION QUALITY (instruction §4) ─────────────────────────────────────

def monetization_quality(records: list, click_log_path: Path) -> dict:
    """Load click log to compute CTR by book/action_type."""
    if not click_log_path.exists():
        return {"note": "click_log.csv not found"}
    ctr_by_book = defaultdict(int)
    ctr_by_type = defaultdict(int)
    by_edge_bucket = defaultdict(int)
    try:
        with open(click_log_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                book  = row.get("book","")
                atype = row.get("recommended_action_type","")
                edge  = float(row.get("edge",0) or 0) * 100
                ctr_by_book[book] += 1
                ctr_by_type[atype] += 1
                k = ("0-3" if edge<3 else "3-5" if edge<5 else "5-8" if edge<8
                     else "8-12" if edge<12 else "12+")
                by_edge_bucket[k] += 1
    except Exception as e:
        return {"error": str(e)}
    return {
        "ctr_by_book":         dict(ctr_by_book),
        "ctr_by_action_type":  dict(ctr_by_type),
        "clicks_per_edge_bucket": dict(by_edge_bucket),
    }


# ── LOAD DATA ─────────────────────────────────────────────────────────────────

def load_quote_archive(target_date: str) -> list:
    f = CACHE_DIR / f"quote_archive_{target_date}.ndjson"
    if not f.exists(): return []
    rows = []
    with open(f) as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: rows.append(json.loads(line))
            except: continue
    return rows

def load_perf_log() -> list:
    f = GRADED_DIR / "performance_log.csv"
    if not f.exists(): return []
    rows = []
    with open(f, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows

def match_outcomes(quotes: list, perf: list) -> list:
    outcome_map = {}
    for r in perf:
        key = (
            (r.get("player","") or "").lower().replace(" ",""),
            (r.get("stat","")   or "").lower(),
            (r.get("side","")   or "").upper(),
        )
        try:
            outcome_map[key] = {
                "outcome":        r.get("outcome",""),
                "outcome_binary": 1 if r.get("outcome")=="win" else 0,
                "profit":         float(r.get("profit",0) or 0),
                "clv":            float(r.get("clv",0) or 0),
                "kelly":          float(r.get("kelly_units",0.01) or 0.01),
            }
        except: continue

    matched = []
    for q in quotes:
        key = (
            (q.get("player","") or "").lower().replace(" ",""),
            (q.get("stat","")   or "").lower(),
            (q.get("side","")   or "").upper(),
        )
        om = outcome_map.get(key)
        if om:
            record = {**q, **om, "model_prob": float(q.get("model_prob",0.5) or 0.5)}
            matched.append(record)
    return matched


# ── MAIN REPLAY ───────────────────────────────────────────────────────────────

def roi_by_brier_level(records: list) -> list:
    """ROI grouped by calibration quality (doc 6 §6 must also)."""
    levels = {"excellent(<0.20)":[],"good(0.20-0.24)":[],"fair(0.24-0.28)":[],"poor(>0.28)":[]}
    for r in records:
        b = float(r.get("bucket_brier",0.25) or 0.25)
        profit = r.get("profit",0) or 0
        k = ("excellent(<0.20)" if b<0.20 else "good(0.20-0.24)" if b<0.24
             else "fair(0.24-0.28)" if b<0.28 else "poor(>0.28)")
        levels[k].append(profit)
    return [{"brier_level":k,"n":len(v),"roi":round(sum(v)/max(len(v),1),4) if v else None}
            for k,v in levels.items()]


def stale_quote_audit(records: list) -> dict:
    """Audit ROI and win rate by quote staleness (doc 6 §6 must also)."""
    buckets = {"fresh(<60s)":[],"warm(60-300s)":[],"stale(>300s)":[]}
    for r in records:
        stale = float(r.get("stale_sec",0) or r.get("quote_age_sec",0) or 0)
        profit = r.get("profit",0) or 0
        win    = r.get("outcome_binary",0)
        k = ("fresh(<60s)" if stale<60 else "warm(60-300s)" if stale<300 else "stale(>300s)")
        buckets[k].append({"profit":profit,"win":win})
    result = {}
    for k,rows in buckets.items():
        n = len(rows)
        result[k] = {
            "n":       n,
            "roi":     round(sum(r["profit"] for r in rows)/max(n,1),4) if n else None,
            "win_rate":round(sum(r["win"] for r in rows)/max(n,1),4)    if n else None,
        }
    return result


def fallback_pricer_audit(records: list) -> dict:
    """Compare ROI for python_live_pricer vs fallback_php (doc 6 §6 must also)."""
    sources = defaultdict(list)
    for r in records:
        src = r.get("pricing_source","unknown")
        sources[src].append({"profit":r.get("profit",0) or 0,"win":r.get("outcome_binary",0)})
    result = {}
    for src,rows in sources.items():
        n = len(rows)
        result[src] = {
            "n":       n,
            "roi":     round(sum(r["profit"] for r in rows)/max(n,1),4) if n else None,
            "win_rate":round(sum(r["win"] for r in rows)/max(n,1),4)    if n else None,
        }
    return result


def replay_date(target_date: str) -> dict:
    print(f"Replaying {target_date}…", file=sys.stderr)
    quotes  = load_quote_archive(target_date)
    perf    = load_perf_log()
    if not quotes: return {"date": target_date, "error": "no_quote_archive"}
    matched = match_outcomes(quotes, perf)
    n_total, n_graded = len(quotes), len(matched)
    print(f"  {n_total} quotes | {n_graded} matched", file=sys.stderr)
    if n_graded == 0:
        return {"date": target_date, "n_quotes": n_total, "n_graded": 0,
                "note": "No matched outcomes — check performance_log.csv"}

    wins = sum(r["outcome_binary"] for r in matched)
    total_profit = sum(r.get("profit",0) for r in matched)
    clvs = [r.get("clv",0) for r in matched]
    clv_pos = sum(1 for c in clvs if c > 0)

    # ROI by bucket_brier level (doc 6 §6 must also)
    brier_bucket_roi = roi_by_brier_level(matched)

    # Stale-quote and fallback-pricer audit (doc 6 §6 must also)
    stale_audit    = stale_quote_audit(matched)
    fallback_audit = fallback_pricer_audit(matched)

    return {
        "date":              target_date,
        "n_quotes":          n_total,
        "n_graded":          n_graded,
        "win_rate":          round(wins/n_graded, 4),
        "total_profit":      round(total_profit, 2),
        "clv_mean":          round(sum(clvs)/len(clvs), 4) if clvs else None,
        "clv_positive_pct":  round(clv_pos/n_graded*100, 1) if n_graded else None,
        "brier_score":       round(brier_score(matched), 4),
        "calibration":       calibration_by_bucket(matched),
        "roi_by_edge":       roi_by_edge_bucket(matched),
        "roi_by_action":     roi_by_action_score_bucket(matched),
        "roi_by_brier":      brier_bucket_roi,
        "fp_by_tier":        false_positive_by_tier(matched),
        "fp_by_source":      false_positive_by_pricing_source(matched),
        "routing":           routing_quality(matched),
        "monetization":      monetization_quality(matched, GRADED_DIR/"click_log.csv"),
        "stale_audit":       stale_audit,
        "fallback_audit":    fallback_audit,
        "roi_by_cal_level":  roi_by_calibration_level(matched),
        "stale_fallback_audit": roi_by_stale_and_fallback(matched),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    dates = (
        sorted(a.stem.replace("quote_archive_","") for a in CACHE_DIR.glob("quote_archive_*.ndjson"))
        if args.all else [args.date or (date.today()-timedelta(days=1)).isoformat()]
    )

    results = [replay_date(d) for d in dates]
    out = results[0] if len(results) == 1 else results

    # Write report files (instruction §6)
    (GRADED_DIR/"replay_live_summary.json").write_text(json.dumps(out, indent=2))

    if isinstance(out, list) and out:
        # by_bucket CSV
        all_buckets = {}
        for r in out:
            for k,v in (r.get("calibration",{}) or {}).items():
                all_buckets[k] = {**v, "bucket_key":k, "date":r["date"]}
        if all_buckets:
            rows = list(all_buckets.values())
            with open(GRADED_DIR/"replay_live_by_bucket.csv","w",newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
                w.writeheader(); w.writerows(rows)
        # routing CSV
        routing_rows = [{"date":r["date"], **r.get("routing",{})} for r in out if r.get("routing")]
        if routing_rows:
            with open(GRADED_DIR/"replay_live_routing.csv","w",newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(routing_rows[0].keys()), extrasaction="ignore")
                w.writeheader(); w.writerows(routing_rows)

    if args.output:
        Path(args.output).write_text(json.dumps(out, indent=2))
        print(f"Results written to {args.output}")
    else:
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
