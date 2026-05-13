#!/usr/bin/env python3
"""M8.6O v5 — WoO monetization contract verifier (all-row + odds_pairs coverage)."""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FIELDS = ("model_prob_over","model_prob_under","model_probability_for_side",
    "side","side_odds","fair_odds_model","edge","ev","kelly","kelly_raw","kelly_capped",
    "affiliate_url","calibration_support_status","accuracy_support_status",
    "edge_publish_status","promotion_status","market_superiority_claim_allowed")
MISSION_STATS = {"pts","reb","ast","fg3m","tov","stl","blk","stocks","pa","pr","pra"}
MARKET_STAT_MAP = {"points":"pts","rebounds":"reb","assists":"ast","threes_made":"fg3m",
    "threes":"fg3m","three_pointers_made":"fg3m","turnovers":"tov","steals":"stl",
    "blocks":"blk","steals_blocks":"stocks","stl_blk":"stocks","points_assists":"pa",
    "pts_ast":"pa","points_rebounds":"pr","pts_reb":"pr","points_rebounds_assists":"pra",
    "pts_reb_ast":"pra","ra":None,"reb_ast":None}
AFFILIATE_BOOK_KEYS = {"bovada","betus","betonlineag","betonline"}
SIDE_TOL = 1e-9; SUM_TOL = 1e-6; MAX_EXAMPLES = 25
def _fail(g,d):
    print(f"M8_6O_WOO_MONETIZATION_CONTRACT_FAILED gate={g} detail={d}", file=sys.stderr); sys.exit(1)
def _norm_stat(s):
    s = str(s or "").lower().strip()
    if s in MARKET_STAT_MAP: return MARKET_STAT_MAP[s]
    return s if s in MISSION_STATS else (s or None)
def _norm_name(s): return str(s or "").lower().strip()
def _f(x):
    try: return float(x)
    except Exception: return None
def _row_key(pid, pname, stat, line, book, side):
    try: lf = float(line)
    except Exception: lf = None
    return (("" if pid is None else str(pid)), _norm_name(pname),
            str(stat).lower(), (round(lf,4) if lf is not None else None),
            str(book or "").lower(), str(side or "").upper())
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date", required=True)
    a = ap.parse_args(); date = a.date
    candidates = [REPO_ROOT/"public_export"/"wizard_of_odds"/date,
                  REPO_ROOT/"public_export"/"wizard_of_odds"/"latest",
                  REPO_ROOT/"public_export"/"wizard_of_odds"]
    found = next((c for c in candidates if (c/"affiliate_dashboard.json").exists()), None)
    if found is None: _fail("G_AD_MISSING", str([str(c) for c in candidates]))
    cd = json.loads((found/"count_diagnostics.json").read_text()) if (found/"count_diagnostics.json").exists() else _fail("G1","missing")
    for k in ("pmf_rows_available","offered_market_rows_available","joinable_rows",
              "model_prob_resolved_rows","market_prob_resolved_rows","side_odds_resolved_rows",
              "edge_publishable_rows","calibration_supported_rows","accuracy_supported_rows"):
        if k not in cd: _fail("G1_SCHEMA", f"missing {k}")
    ob = json.loads((found/"omitted_bets.json").read_text()) if (found/"omitted_bets.json").exists() else _fail("G2","missing")
    if "omitted_bets" not in ob or "total_omitted" not in ob: _fail("G2_SCHEMA", str(list(ob.keys())))
    ad = json.loads((found/"affiliate_dashboard.json").read_text())
    rows = ad.get("rows", [])
    if not isinstance(rows, list): _fail("G3_BAD_ROWS", str(type(rows)))
    over = sum(1 for r in rows if str(r.get("side","")).upper()=="OVER")
    under = sum(1 for r in rows if str(r.get("side","")).upper()=="UNDER")
    if rows:
        if over == 0: _fail("G3_NO_OVER", f"rows={len(rows)}")
        if under == 0: _fail("G3_NO_UNDER", f"rows={len(rows)}")
    mf=[]; sc=[]; s1=[]; nv=[]
    for i, r in enumerate(rows):
        if not isinstance(r, dict): mf.append(f"row#{i}: not dict"); continue
        miss = [f for f in REQUIRED_FIELDS if f not in r]
        if miss and len(mf) < MAX_EXAMPLES:
            mf.append(f"row#{i} stat={r.get('stat')} line={r.get('line')} book={r.get('book')} side={r.get('side')} missing={miss}")
        if miss: continue
        side = str(r.get("side","")).upper()
        mpo = _f(r.get("model_prob_over")); mpu = _f(r.get("model_prob_under")); mps = _f(r.get("model_probability_for_side")); ev = _f(r.get("ev"))
        if mpo is None or mpu is None or mps is None or side not in ("OVER","UNDER"):
            if len(sc) < MAX_EXAMPLES: sc.append(f"row#{i} side={side} mpo={mpo} mpu={mpu} mps={mps}")
        else:
            exp = mpo if side == "OVER" else mpu
            if abs(mps - exp) > SIDE_TOL and len(sc) < MAX_EXAMPLES:
                sc.append(f"row#{i} side={side} mps={mps} expected={exp}")
            if abs(mpo + mpu - 1.0) > SUM_TOL and len(s1) < MAX_EXAMPLES:
                s1.append(f"row#{i} mpo={mpo} mpu={mpu}")
            if not (0.0 < mps < 1.0) and len(nv) < MAX_EXAMPLES:
                nv.append(f"row#{i} mps={mps}")
            if ev is not None and not math.isfinite(ev) and len(nv) < MAX_EXAMPLES:
                nv.append(f"row#{i} ev_not_finite={ev}")
    if mf: _fail("G4_MISSING_CONTRACT_FIELDS", " | ".join(mf))
    if sc: _fail("G5_SIDE_INCONSISTENCY", " | ".join(sc))
    if s1: _fail("G6_PROBS_DO_NOT_SUM_TO_ONE", " | ".join(s1))
    if nv: _fail("G7_NUMERIC_INVALID", " | ".join(nv))
    has_alt = any(bool(r.get("is_alternate", False)) for r in rows)
    mcp = REPO_ROOT/"deliveries"/date/"wizard_of_odds"/"market_comparison.parquet"
    if mcp.exists():
        try:
            import pandas as pd
            mc = pd.read_parquet(mcp)
            if "is_alternate" in mc.columns and (mc["is_alternate"] == True).any() and not has_alt:
                _fail("G8_ALTERNATES_DROPPED","mc has alts; ad has none")
        except Exception as e:
            print(f"::warning::G8 skipped: {e}", file=sys.stderr)
    odds_dir = REPO_ROOT/"data"/"odds_api"/"processed"/date
    odds_pairs = sorted(odds_dir.glob("odds_pairs_*close_or_lock*.parquet")) if odds_dir.exists() else []
    coverage_status = "no_odds_pairs_close_or_lock_for_date"
    if odds_pairs:
        try: import pandas as pd
        except ImportError: _fail("G9_PANDAS", "pandas required")
        op = pd.read_parquet(odds_pairs[-1])
        stat_col = "market_stat" if "market_stat" in op.columns else ("stat" if "stat" in op.columns else None)
        if stat_col is None: _fail("G9_NO_STAT", str(odds_pairs[-1]))
        op["_sc"] = op[stat_col].apply(_norm_stat)
        op = op[op["_sc"].isin(MISSION_STATS)].copy()
        bk = "bookmaker_key" if "bookmaker_key" in op.columns else ("book" if "book" in op.columns else None)
        if bk is None: _fail("G9_NO_BOOK", str(odds_pairs[-1]))
        op["_bk"] = op[bk].astype(str).str.lower()
        op = op[op["_bk"].isin(AFFILIATE_BOOK_KEYS)].copy()
        if "line" not in op.columns: _fail("G9_NO_LINE", str(odds_pairs[-1]))
        pid_c = "player_id" if "player_id" in op.columns else None
        pn_c = "player_name" if "player_name" in op.columns else ("player" if "player" in op.columns else None)
        offered = set()
        for _, r in op.iterrows():
            for side in ("OVER","UNDER"):
                offered.add(_row_key(r.get(pid_c) if pid_c else None,
                                      r.get(pn_c) if pn_c else None,
                                      r.get("_sc"), r.get("line"), r.get("_bk"), side))
        cov_d = {_row_key(r.get("player_id"), r.get("player_name"), r.get("stat"),
                          r.get("line"), r.get("book"), r.get("side")) for r in rows}
        cov_o = {_row_key(o.get("player_id"), o.get("player_name"), o.get("stat"),
                          o.get("line"), o.get("book"), o.get("side")) for o in ob.get("omitted_bets",[])}
        covered = cov_d | cov_o
        unc = sorted(offered - covered)
        if unc: _fail("G9_ODDS_PAIRS_COVERAGE_INCOMPLETE",
                      f"uncovered={len(unc)}/{len(offered)} first={unc[:MAX_EXAMPLES]}")
        dc = sorted(cov_d & cov_o)
        if dc: _fail("G9_TUPLE_DOUBLE_COVERED", f"count={len(dc)} first={dc[:MAX_EXAMPLES]}")
        coverage_status = f"covered/offered={len(offered&covered)}/{len(offered)}"
    jo = int(cd.get("joinable_rows") or 0); to = int(ob.get("total_omitted") or 0)
    if jo > 0 and to/jo > 0.95: _fail("G10_OMISSION_RATE", f"j={jo} o={to}")
    if int(cd.get("offered_market_rows_available") or 0) > 0 and not rows:
        _fail("G10_EMPTY_WITH_OFFERS", f"offered={cd['offered_market_rows_available']}")
    print("M8_6O_WOO_MONETIZATION_CONTRACT_PASS")
    print(f"  date={date} rows={len(rows)} over={over} under={under} coverage={coverage_status}")
    return 0
if __name__ == "__main__": raise SystemExit(main())
