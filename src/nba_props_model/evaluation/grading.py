#!/usr/bin/env python3
"""
NBA Props Model — grading and CLV.

True CLV = model_prob - closing_fair_prob, where closing_fair_prob is loaded
from artifacts/graded/closing_lines_{date}.json (captured at 6 PM ET via
scripts/snapshot_closing_lines.py, post-injury-report).

If no closing snapshot exists for a date, falls back to
clv = model_prob - market_prob (pick-time 8 AM market price) and marks the
column clv_proxy=True to distinguish.
"""

from typing import Optional, Tuple

import argparse
import json
import logging
import sys
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Closing line loader for true CLV ──────────────────────────────────────────

def load_closing_lines(target_date: str) -> dict:
    """
    Load graded/closing_lines_{date}.json produced by snapshot_closing_lines.py.
    Returns dict: {(player_norm, stat, line): fair_over_prob}
    Returns {} if file doesn't exist (falls back to pick-time market_prob).

    The closing file is keyed by "{player_norm}|{stat}|{line}".
    We join to predictions by normalizing player names the same way.
    """
    import re
    closing_path = GRADED_DIR / f"closing_lines_{target_date}.json"
    if not closing_path.exists():
        return {}
    try:
        with open(closing_path) as f:
            raw = json.load(f)
        result = {}
        for key, rec in raw.items():
            parts = key.split("|")
            if len(parts) != 3:
                continue
            player_norm, stat, line_str = parts
            try:
                line = float(line_str)
            except ValueError:
                continue
            result[(player_norm, stat, line)] = {
                "fair_over_prob":  rec.get("fair_over_prob", 0.5),
                "fair_under_prob": rec.get("fair_under_prob", 0.5),
            }
        logger.info(f"Closing lines loaded: {len(result)} player-stat entries for {target_date}")
        return result
    except Exception as e:
        logger.warning(f"Could not load closing lines for {target_date}: {e}")
        return {}


def normalize_player_name(name: str) -> str:
    """Mirror the normalization in snapshot_closing_lines.py."""
    import re
    name = name.lower().strip()
    name = re.sub(r"[''`]", "", name)
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def lookup_closing_prob(
    closing_lines: dict,
    player_name: str,
    stat: str,
    line: float,
    side: str,
) -> Tuple[Optional[float], bool]:
    """
    Look up fair probability from closing lines for a given pick.
    Returns (fair_prob_for_bet_side, is_true_clv).
    is_true_clv=True  → matched closing snapshot (true CLV)
    is_true_clv=False → no closing data (falls back to market_prob)
    """
    player_norm = normalize_player_name(player_name)
    # Try exact line match first, then ±0.5 tolerance
    for tolerance in [0.0, 0.5]:
        for try_line in [line, line + 0.5, line - 0.5]:
            if abs(try_line - line) > tolerance + 0.01:
                continue
            rec = closing_lines.get((player_norm, stat, try_line))
            if rec:
                if side == "OVER":
                    return float(rec["fair_over_prob"]), True
                else:
                    return float(rec["fair_under_prob"]), True
    return None, False


from nba_props_model.paths import GRADED_DIR, PRED_DIR

PERF_LOG   = GRADED_DIR / "performance_log.csv"
CUM_REPORT = GRADED_DIR / "cumulative_report.json"

STATS = ["pts", "reb", "ast", "fg3m", "stl", "blk"]
STAT_DISPLAY = {"pts": "Points", "reb": "Rebounds", "ast": "Assists",
                "fg3m": "Threes", "stl": "Steals", "blk": "Blocks"}

TIER_ORDER = {"ELITE": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def american_to_decimal(american: int) -> float:
    if american > 0:
        return 1.0 + american / 100.0
    else:
        return 1.0 + 100.0 / abs(american)


def compute_profit(result: str, bet_odds: int) -> float:
    if result == "HIT":
        return american_to_decimal(bet_odds) - 1.0
    elif result == "MISS":
        return -1.0
    else:
        return 0.0


def grade_single(pred: dict, actual_stat, closing_lines: dict = None) -> dict:
    """
    Grade a single prediction.

    CLV computation (priority order):
      1. True CLV  = model_prob - closing_fair_prob (from closing_lines snapshot)
      2. Proxy CLV = model_prob - market_prob        (pick-time 8 AM price)
      3. None      = no market reference available

    Column names:
      clv       — true CLV (closing snapshot available)
      clv_proxy — pick-time proxy CLV (fallback, less reliable)
    """
    p = dict(pred)

    if actual_stat is None:
        p["result"]    = "NO_ACTION"
        p["profit"]    = 0.0
        p["actual"]    = None
        p["clv"]       = None
        p["clv_proxy"] = None
        p["clv_is_true"] = False
        return p

    line     = float(p.get("line", 0))
    side     = p.get("side", "OVER")
    bet_odds = int(p.get("odds", p.get("bet_odds", -110)))
    model_p  = float(p.get("model_prob", 0.5))
    imp_over = float(p.get("market_prob", p.get("implied_prob_over", 0.5)))

    actual = float(actual_stat)
    p["actual"] = actual

    if actual > line:
        raw_result = "OVER"
    elif actual < line:
        raw_result = "UNDER"
    else:
        raw_result = "PUSH"

    if raw_result == "PUSH":
        p["result"] = "PUSH"
    elif raw_result == side:
        p["result"] = "HIT"
    else:
        p["result"] = "MISS"

    p["profit"] = compute_profit(p["result"], bet_odds)

    # ── CLV: attempt true CLV from closing snapshot, fallback to proxy ────────
    closing_fair_prob = None
    is_true_clv       = False

    if closing_lines:
        player_name = p.get("player_name", "")
        closing_fair_prob, is_true_clv = lookup_closing_prob(
            closing_lines, player_name, p.get("stat", ""), line, side
        )

    if is_true_clv and closing_fair_prob is not None:
        # True CLV: model vs post-injury-report closing market
        p["clv"]         = round(model_p - closing_fair_prob, 4)
        p["clv_proxy"]   = round(model_p - imp_over, 4)    # keep proxy too for comparison
        p["clv_is_true"] = True
    else:
        # Proxy CLV: model vs pick-time market (less reliable — books shade lines)
        if side == "OVER":
            p["clv_proxy"] = round(model_p - imp_over, 4)
        else:
            p["clv_proxy"] = round((1.0 - model_p) - (1.0 - imp_over), 4)
        p["clv"]         = p["clv_proxy"]   # best available
        p["clv_is_true"] = False

    return p


def fetch_actual_stats(target_date: str) -> dict:
    try:
        from nba_props_model.data.bdl_client import get_player_game_stats, parse_minutes
    except ImportError:
        logger.error("bdl_client.py not found. Cannot fetch actual stats.")
        return {}

    try:
        records = get_player_game_stats(start_date=target_date, end_date=target_date)
    except Exception as e:
        logger.error(f"BDL fetch failed: {e}")
        return {}

    result = {}
    for rec in records:
        pid = (rec.get("player") or {}).get("id")
        if not pid:
            continue
        m = parse_minutes(rec.get("min", "0"))
        if m < 1:
            continue
        pid = int(pid)
        result[(pid, "pts")]  = float(rec.get("pts")  or 0)
        result[(pid, "reb")]  = float(rec.get("reb")  or 0)
        result[(pid, "ast")]  = float(rec.get("ast")  or 0)
        result[(pid, "fg3m")] = float(rec.get("fg3m") or 0)
        result[(pid, "stl")]  = float(rec.get("stl")  or 0)
        result[(pid, "blk")]  = float(rec.get("blk")  or 0)

    logger.info(f"Fetched actuals: {len(records)} stat records → {len(result)} (player,stat) pairs")
    return result


def grade_date(target_date: str) -> pd.DataFrame:
    pred_path = PRED_DIR / f"singles_{target_date}.json"

    if not pred_path.exists():
        logger.error(f"No predictions found: {pred_path}")
        return pd.DataFrame()

    with open(pred_path) as f:
        raw = json.load(f)

    # ── FIX: handle both formats ──────────────────────────────────────────────
    # New format: {"date": "2026-03-08", "picks": [...]}
    # Legacy format: [...]
    if isinstance(raw, dict):
        preds = raw.get("picks", [])
    elif isinstance(raw, list):
        preds = raw
    else:
        logger.error(f"Unrecognised predictions format in {pred_path}")
        return pd.DataFrame()
    # ─────────────────────────────────────────────────────────────────────────

    if not preds:
        logger.warning("Predictions file is empty.")
        return pd.DataFrame()

    actuals = fetch_actual_stats(target_date)
    if not actuals:
        logger.warning("No actuals fetched — grading will mark all as NO_ACTION.")

    # Load closing lines for true CLV computation
    closing_lines = load_closing_lines(target_date)
    n_true_clv = 0

    graded = []
    for pred in preds:
        pid  = int(pred.get("player_id", 0))
        stat = pred.get("stat", "")
        actual_val = actuals.get((pid, stat))
        g = grade_single(pred, actual_val, closing_lines=closing_lines)
        if g.get("clv_is_true"):
            n_true_clv += 1
        graded.append(g)

    if closing_lines:
        logger.info(f"CLV: {n_true_clv}/{len(graded)} picks matched closing lines (true CLV)")
    else:
        logger.info(f"CLV: No closing snapshot for {target_date} — using pick-time proxy CLV")

    df = pd.DataFrame(graded)
    df["grade_date"] = target_date
    outpath = GRADED_DIR / f"graded_{target_date}.csv"
    df.to_csv(outpath, index=False)
    logger.info(f"Graded {len(df)} predictions → {outpath}")

    return df


def compute_metrics(df: pd.DataFrame, label: str = "") -> dict:
    active = df[df["result"].isin(["HIT", "MISS", "PUSH"])]
    bet    = active[active["result"].isin(["HIT", "MISS"])]

    if len(bet) == 0:
        return {"label": label, "n_bets": 0}

    n        = len(bet)
    hits     = (bet["result"] == "HIT").sum()
    hit_rate = hits / n
    profit   = float(bet["profit"].sum())
    roi      = profit / n

    # Prefer true CLV column; fallback to proxy
    clv_col  = "clv" if "clv" in bet.columns else "clv_proxy"
    clv_vals = bet[clv_col].dropna()
    mean_clv = float(clv_vals.mean()) if len(clv_vals) > 0 else 0.0
    pct_true_clv = float((bet.get("clv_is_true", pd.Series(False)).sum() / len(bet))) if "clv_is_true" in bet.columns else 0.0
    # Bug 10 fix: report true CLV and proxy CLV separately
    if "clv_is_true" in bet.columns:
        true_clv_vals  = bet[bet["clv_is_true"] == True][clv_col].dropna()
        proxy_clv_vals = bet[bet["clv_is_true"] == False][clv_col].dropna()
        mean_clv_true  = float(true_clv_vals.mean())  if len(true_clv_vals)  > 0 else None
        mean_clv_proxy = float(proxy_clv_vals.mean()) if len(proxy_clv_vals) > 0 else None
    else:
        mean_clv_true = mean_clv_proxy = None

    if "model_prob" in bet.columns and "side" in bet.columns:
        actual_p = (bet["result"] == "HIT").astype(float)  # Bug 4 fix: HIT=1, MISS=0 regardless of side
        model_p = bet["model_prob"].clip(0.01, 0.99)
        brier = float(((model_p - actual_p) ** 2).mean())
    else:
        brier = None

    cumulative = bet["profit"].cumsum().values
    peak = np.maximum.accumulate(cumulative)
    drawdown = peak - cumulative
    max_dd = float(drawdown.max()) if len(drawdown) > 0 else 0.0

    pnl = bet["profit"].values
    sharpe = (np.mean(pnl) / np.std(pnl) * np.sqrt(172)) if np.std(pnl) > 0 else 0.0  # ~172 NBA slate days

    # Issue 19: bootstrap CI on CLV
    if len(clv_vals) >= 30:
        import numpy as _np2
        _rng = _np2.random.default_rng(42)
        boot_means = [_rng.choice(clv_vals.values, size=len(clv_vals), replace=True).mean()
                      for _ in range(10000)]
        clv_ci_low  = round(float(_np2.percentile(boot_means, 2.5)), 4)
        clv_ci_high = round(float(_np2.percentile(boot_means, 97.5)), 4)
        clv_sig     = bool(clv_ci_low > 0)
    else:
        clv_ci_low = clv_ci_high = None
        clv_sig = False
    return {
        "label":    label,
        "n_bets":   int(n),
        "n_hits":   int(hits),
        "hit_rate": round(hit_rate, 4),
        "profit":   round(profit, 2),
        "roi":      round(roi, 4),
        "mean_clv": round(mean_clv, 4),
        "mean_clv_true_clv": round(mean_clv_true, 4) if mean_clv_true is not None else None,
        "mean_clv_proxy": round(mean_clv_proxy, 4) if mean_clv_proxy is not None else None,
        "clv_ci_95": [clv_ci_low, clv_ci_high],
        "clv_significant": clv_sig,
        "pct_true_clv": round(pct_true_clv, 3),
        "pct_true_clv": round(pct_true_clv, 3),
        "brier":    round(brier, 4) if brier is not None else None,
        "max_dd":   round(max_dd, 2),
        "sharpe":   round(sharpe, 3),
    }


def print_report(df: pd.DataFrame, date_label: str = ""):
    active = df[df["result"].isin(["HIT", "MISS", "PUSH"])].copy()
    bet    = active[active["result"] != "PUSH"].copy()

    total_m     = compute_metrics(bet, "TOTAL")
    n_no_action = (df["result"] == "NO_ACTION").sum()
    n_push      = (active["result"] == "PUSH").sum()

    print(f"\n{'='*72}")
    print(f"NBA Props Model GRADING REPORT — {date_label}")
    print(f"{'='*72}")
    print(f"  Predictions:  {len(df):4d}  |  Graded:  {len(active):4d}  |  NO_ACTION: {n_no_action}  |  PUSH: {n_push}")
    print(f"  {'-'*68}")

    if total_m["n_bets"] == 0:
        print("  No graded bets to report.\n")
        return

    print(f"  TOTAL    Bets: {total_m['n_bets']:3d}  Hit: {total_m['hit_rate']:.1%}  "
          f"ROI: {total_m['roi']:+.1%}  P&L: {total_m['profit']:+.2f}  "
          f"CLV: {total_m['mean_clv']:+.4f}  MaxDD: {total_m['max_dd']:.2f}")

    print(f"\n  {'-'*68}")
    print(f"  BY TIER:")
    for tier in ["ELITE", "HIGH", "MEDIUM", "LOW"]:
        sub = bet[bet["confidence"] == tier] if "confidence" in bet.columns else pd.DataFrame()
        if sub.empty: continue
        m = compute_metrics(sub, tier)
        clv_str = f"CLV: {m['mean_clv']:+.4f}" if m["n_bets"] > 0 else ""
        print(f"    {tier:8s} Bets: {m['n_bets']:3d}  Hit: {m['hit_rate']:.1%}  "
              f"ROI: {m['roi']:+.1%}  P&L: {m['profit']:+.2f}  {clv_str}")

    print(f"\n  {'-'*68}")
    print(f"  BY STAT:")
    for stat in STATS:
        sub = bet[bet["stat"] == stat] if "stat" in bet.columns else pd.DataFrame()
        if sub.empty: continue
        m = compute_metrics(sub, STAT_DISPLAY[stat])
        print(f"    {STAT_DISPLAY[stat]:10s} Bets: {m['n_bets']:3d}  Hit: {m['hit_rate']:.1%}  "
              f"ROI: {m['roi']:+.1%}  CLV: {m['mean_clv']:+.4f}")

    print(f"\n  {'-'*68}")
    print(f"  BY SIDE:")
    for side in ["OVER", "UNDER"]:
        sub = bet[bet["side"] == side] if "side" in bet.columns else pd.DataFrame()
        if sub.empty: continue
        m = compute_metrics(sub, side)
        print(f"    {side:6s}  Bets: {m['n_bets']:3d}  Hit: {m['hit_rate']:.1%}  ROI: {m['roi']:+.1%}")

    if "model_prob" in bet.columns:
        print(f"\n  {'-'*68}")
        print(f"  CALIBRATION (model_prob bucket → actual hit rate):")
        print(f"    {'Bucket':12s} {'N':>5}  {'Pred':>7}  {'Actual':>7}  {'Error':>7}")
        # Issue 18 fix: equal-mass (quantile-based) bins instead of equal-width
        try:
            prob_vals = bet["model_prob"].dropna()
            bin_edges = pd.qcut(prob_vals, q=8, retbins=True, duplicates="drop")[1]
            bin_pairs = list(zip(bin_edges[:-1], bin_edges[1:]))
        except Exception:
            bin_pairs = [(0.40,0.50),(0.50,0.55),(0.55,0.60),(0.60,0.65),(0.65,0.70),(0.70,1.0)]
        for lo, hi in bin_pairs:
            mask = (bet["model_prob"] >= lo) & (bet["model_prob"] < hi)
    clv_vals = bet["clv_proxy"].dropna()
    if len(clv_vals) > 0:
        print(f"\n  {'-'*68}")
        print(f"  CLV DISTRIBUTION:")
        print(f"    Mean: {clv_vals.mean():+.4f}  Std: {clv_vals.std():.4f}  "
              f"Positive: {(clv_vals > 0).mean():.1%}  "
              f"P10: {np.percentile(clv_vals,10):+.3f}  P90: {np.percentile(clv_vals,90):+.3f}")

    print(f"  {'-'*68}")
    print(f"  Brier Score: {total_m.get('brier','N/A')}  |  Sharpe: {total_m['sharpe']:.3f}  |  Max Drawdown: {total_m['max_dd']:.2f}u\n")


def update_performance_log(df: pd.DataFrame, target_date: str):
    active = df[df["result"].isin(["HIT", "MISS", "PUSH"])].copy()
    if active.empty:
        return

    if PERF_LOG.exists():
        existing = pd.read_csv(PERF_LOG)
        existing = existing[existing.get("grade_date", pd.Series(dtype=str)) != target_date] \
            if "grade_date" in existing.columns else existing
        combined = pd.concat([existing, active], ignore_index=True)
    else:
        combined = active

    combined.to_csv(PERF_LOG, index=False)
    logger.info(f"Performance log updated: {len(combined)} total rows across all dates")
    _rebuild_cumulative_report(combined)


def _rebuild_cumulative_report(log: pd.DataFrame):
    bet = log[log["result"].isin(["HIT", "MISS"])].copy()
    if bet.empty:
        return

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_dates":  int(log["grade_date"].nunique()) if "grade_date" in log.columns else 0,
        "overall":      compute_metrics(bet, "ALL_TIME"),
        "by_tier":      {},
        "by_stat":      {},
        "by_side":      {},
        "rolling_30":   {},
        "rolling_60":   {},
    }

    if "grade_date" in bet.columns:
        bet_sorted = bet.sort_values("grade_date")
        all_dates  = sorted(bet_sorted["grade_date"].unique())
        if len(all_dates) >= 1:
            for window, key in [(30, "rolling_30"), (60, "rolling_60")]:
                cutoff = (datetime.strptime(all_dates[-1], "%Y-%m-%d") - timedelta(days=window)).strftime("%Y-%m-%d")
                sub = bet_sorted[bet_sorted["grade_date"] >= cutoff]
                report[key] = compute_metrics(sub, f"last_{window}d")

    for tier in ["ELITE", "HIGH", "MEDIUM", "LOW"]:
        sub = bet[bet["confidence"] == tier] if "confidence" in bet.columns else pd.DataFrame()
        if not sub.empty:
            report["by_tier"][tier] = compute_metrics(sub, tier)

    for stat in STATS:
        sub = bet[bet["stat"] == stat] if "stat" in bet.columns else pd.DataFrame()
        if not sub.empty:
            report["by_stat"][stat] = compute_metrics(sub, STAT_DISPLAY[stat])

    for side in ["OVER", "UNDER"]:
        sub = bet[bet["side"] == side] if "side" in bet.columns else pd.DataFrame()
        if not sub.empty:
            report["by_side"][side] = compute_metrics(sub, side)

    with open(CUM_REPORT, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Cumulative report saved → {CUM_REPORT}")


def print_cumulative_report():
    if not CUM_REPORT.exists():
        print("No cumulative report found. Run grader first.")
        return
    if not PERF_LOG.exists():
        print("No performance log found.")
        return

    with open(CUM_REPORT) as f:
        report = json.load(f)

    log = pd.read_csv(PERF_LOG)
    bet = log[log["result"].isin(["HIT", "MISS"])].copy()

    print(f"\n{'='*72}")
    print(f"NBA Props Model CUMULATIVE PERFORMANCE REPORT")
    print(f"Generated: {report.get('generated_at','?')}  |  Dates: {report.get('total_dates',0)}")
    print(f"{'='*72}")

    def show_metrics(m):
        if not m or m.get("n_bets", 0) == 0:
            print("    (no data)")
            return
        print(f"    Bets: {m['n_bets']:4d}  Hit: {m['hit_rate']:.1%}  ROI: {m['roi']:+.1%}  "
              f"P&L: {m['profit']:+.2f}  CLV: {m['mean_clv']:+.4f}  MaxDD: {m['max_dd']:.2f}")

    print("\nALL TIME:"); show_metrics(report.get("overall", {}))

    for wkey in ["rolling_30", "rolling_60"]:
        r = report.get(wkey, {})
        if r.get("n_bets", 0) > 0:
            print(f"\n{wkey.upper().replace('_','')} BETS:"); show_metrics(r)

    print("\nBY TIER:")
    for tier in ["ELITE", "HIGH", "MEDIUM", "LOW"]:
        m = report.get("by_tier", {}).get(tier, {})
        if m.get("n_bets", 0) > 0:
            print(f"  {tier:8s}", end=""); show_metrics(m)

    print("\nBY STAT:")
    for stat in STATS:
        m = report.get("by_stat", {}).get(stat, {})
        if m.get("n_bets", 0) > 0:
            print(f"  {STAT_DISPLAY[stat]:10s}", end=""); show_metrics(m)

    print("\nBY SIDE:")
    for side in ["OVER", "UNDER"]:
        m = report.get("by_side", {}).get(side, {})
        if m.get("n_bets", 0) > 0:
            print(f"  {side:8s}", end=""); show_metrics(m)

    if "model_prob" in bet.columns:
        print(f"\n{'─'*72}")
        print("CALIBRATION (all-time):")
        print(f"  {'Bucket':12s} {'N':>5}  {'Pred':>7}  {'Actual':>7}  {'Error':>7}")
        for lo, hi in [(0.40,0.50),(0.50,0.55),(0.55,0.60),(0.60,0.65),(0.65,0.70),(0.70,1.0)]:
            mask = (bet["model_prob"] >= lo) & (bet["model_prob"] < hi)
            if mask.sum() < 5: continue
            pred_p = float(bet[mask]["model_prob"].mean())
            act_p  = float((bet[mask]["result"] == "HIT").mean())
            print(f"  {lo:.0%}-{hi:.0%}      {mask.sum():5d}  {pred_p:7.3f}  {act_p:7.3f}  {abs(pred_p-act_p):7.3f}")

    if len(bet) > 0:
        pnl_cum = bet.sort_values("grade_date")["profit"].cumsum().values if "grade_date" in bet.columns else bet["profit"].cumsum().values
        peak = np.maximum.accumulate(pnl_cum)
        dd   = (peak - pnl_cum)
        print(f"\n  Max Drawdown: {dd.max():.2f}u  |  Current P&L: {pnl_cum[-1]:+.2f}u")

    print(f"{'='*72}\n")


def main():
    parser = argparse.ArgumentParser(description="NBA Props Model Grading Script")
    parser.add_argument("--date",   type=str, default=None)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    if args.report:
        print_cumulative_report()
        return

    target = args.date or (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"{'='*72}\nNBA Props Model GRADING — {target}\n{'='*72}")

    graded_df = grade_date(target)

    if graded_df.empty:
        logger.warning("No graded data. Check predictions/ directory.")
        return

    print_report(graded_df, target)
    update_performance_log(graded_df, target)


if __name__ == "__main__":
    main()
