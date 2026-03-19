#!/usr/bin/env python3
"""
state_bucket_calibration.py v2 — Live State-Bucket Calibration
================================================================
Instruction §7: Production calibrator with fallback hierarchy and
bucket_brier exposed to live_props.php API.

Bucket hierarchy (instruction §7.2):
  1. Primary: stat|side|quarter|time_bucket|foul_band|court
  2. Fallback 1: stat|side
  3. Fallback 2: stat
  4. Global

Writes:
  graded/state_bucket_calibration.json  — calibrator params per bucket
  graded/state_bucket_meta.csv          — summary per bucket

Usage:
    python3 state_bucket_calibration.py
    python3 state_bucket_calibration.py --min-samples 20
"""

import argparse
import csv
import json
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

warnings.filterwarnings("ignore")

GRADED_DIR = Path(__file__).parent / "graded"
CACHE_DIR  = Path(__file__).parent / "cache"
MIN_SAMPLES_DEFAULT = 20


# ── SHARED BUCKET TAXONOMY (unified with replay_live.py §1) ──────────────────

def bucket_quarter(period: int, is_ot: bool = False) -> str:
    if is_ot or period > 4: return "OT"
    if period <= 0:          return "pre"
    return f"Q{period}"

def bucket_time(rem_min) -> str:
    if rem_min is None: return "pre"
    try: rem_min = float(rem_min)
    except: return "pre"
    if rem_min < 4:  return "0-4"
    if rem_min < 8:  return "4-8"
    if rem_min < 12: return "8-12"
    return "12+"

def bucket_foul(fouls: int) -> str:
    if fouls <= 2: return "0-2"
    if fouls == 3: return "3"
    return "4+"

def bucket_court(on_court) -> str:
    return "on" if on_court else "off"

def make_primary_key(stat, side, period, rem_min, fouls, on_court, is_ot=False) -> str:
    return "|".join([stat.lower(), side.upper(),
                     bucket_quarter(int(period or 0), is_ot),
                     bucket_time(rem_min),
                     bucket_foul(int(fouls or 0)),
                     bucket_court(on_court)])


# ── ISOTONIC CALIBRATOR ───────────────────────────────────────────────────────

class IsotonicCalibrator:
    def __init__(self):
        self.x_knots = None
        self.y_knots = None
        self.fitted   = False
        self.level    = "identity"  # full_bucket | stat_side | stat | global | identity

    def fit(self, probs: np.ndarray, outcomes: np.ndarray, level: str = "full_bucket") -> "IsotonicCalibrator":
        if len(probs) < 5:
            self.fitted = False
            return self
        order   = np.argsort(probs)
        probs_s = probs[order]
        outs_s  = outcomes[order]
        n_bins  = min(10, max(2, len(probs) // 5))
        edges   = np.unique(np.percentile(probs_s, np.linspace(0, 100, n_bins + 1)))
        xs, ys  = [], []
        for i in range(len(edges) - 1):
            m = (probs_s >= edges[i]) & (probs_s <= edges[i+1])
            if m.sum() < 3: continue
            xs.append(probs_s[m].mean())
            ys.append(outs_s[m].mean())
        if len(xs) < 2:
            self.fitted = False
            return self
        ys = self._pava(np.array(ys))
        self.x_knots = np.concatenate([[0.0], xs, [1.0]]).tolist()
        self.y_knots = np.concatenate([[ys[0]], ys, [ys[-1]]]).tolist()
        self.fitted  = True
        self.level   = level
        return self

    def predict(self, p: float) -> float:
        if not self.fitted: return p
        return float(np.interp(p, self.x_knots, self.y_knots))

    def to_dict(self, n: int, brier: float, mean_prob: float, hit_rate: float) -> dict:
        """Instruction §7.3: return full metadata dict."""
        return {
            "fitted":    self.fitted,
            "level":     self.level,
            "n":         n,
            "brier":     round(brier, 4),
            "mean_prob": round(mean_prob, 4),
            "hit_rate":  round(hit_rate, 4),
            "x_knots":   self.x_knots,
            "y_knots":   self.y_knots,
        }

    @staticmethod
    def _pava(y: np.ndarray) -> np.ndarray:
        y = y.copy()
        i = 0
        while i < len(y) - 1:
            if y[i] > y[i+1]:
                pool = y[i:i+2].mean()
                y[i:i+2] = pool
                if i > 0: i -= 1
            else: i += 1
        return y


# ── RESOLVE CALIBRATION KEY (instruction §7.5) ───────────────────────────────

def resolve_calibration_key(
    stat: str, side: str, period: int, rem_min, fouls: int,
    on_court: bool, meta: dict, is_ot: bool = False
) -> tuple:
    """
    Returns best available (key, metadata_dict) for this state bucket.
    Falls back through: full_bucket → stat_side → stat → global
    """
    primary = make_primary_key(stat, side, period, rem_min, fouls, on_court, is_ot)
    if primary in meta:
        return primary, meta[primary]

    # Fallback 1: stat|side
    fb1 = f"{stat.lower()}|{side.upper()}"
    if fb1 in meta:
        row = {**meta[fb1], "level": "stat_side"}
        return fb1, row

    # Fallback 2: stat
    fb2 = stat.lower()
    if fb2 in meta:
        row = {**meta[fb2], "level": "stat"}
        return fb2, row

    # Fallback 3: global
    if "__global__" in meta:
        row = {**meta["__global__"], "level": "global"}
        return "__global__", row

    # Identity (no calibration data)
    return primary, {"fitted": False, "level": "identity", "n": 0,
                     "brier": 0.25, "mean_prob": 0.5, "hit_rate": 0.5}


# ── LOAD DATA ──────────────────────────────────────────────────────────────────

def load_graded_with_state() -> list:
    log = GRADED_DIR / "performance_log.csv"
    if not log.exists(): return []
    rows = []
    with open(log, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("outcome"): continue
            try:
                rows.append({
                    "stat":        row.get("stat","").lower(),
                    "side":        row.get("side","OVER").upper(),
                    "outcome_bin": 1 if row.get("outcome")=="win" else 0,
                    "model_prob":  float(row.get("model_prob",0.5) or 0.5),
                    "game_period": int(row.get("game_period",0) or 0),
                    "rem_minutes": row.get("rem_minutes_mean"),
                    "fouls":       int(row.get("fouls",0) or 0),
                    "on_court":    (row.get("on_court","true").lower() in ("true","1","yes")),
                    "is_ot":       (row.get("is_overtime","false").lower() in ("true","1")),
                    "pricing_source": row.get("pricing_source","unknown"),
                    "action_score":   float(row.get("action_score",0) or 0),
                    "edge":           float(row.get("edge",0) or 0),
                    # Include IDs for quote archive join (doc 6 §7 must do now)
                    "player_id":   str(row.get("player_id","") or ""),
                    "player":      row.get("player","").lower(),
                    "game_status": row.get("game_status","pre-game"),
                    "date_str":    row.get("date",""),
                })
            except: continue

    # Enrich from quote archive if available
    archives = sorted(CACHE_DIR.glob("quote_archive_*.ndjson"))
    qmap = {}
    # doc 6 §7 must also: build multi-key map for reliable join
    for arc in archives:
        try:
            with open(arc) as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        q = json.loads(line)
                        player_raw  = q.get("player","") or ""
                        player_norm = player_raw.lower().replace(" ","").replace(".","").replace("'","")
                        stat  = (q.get("stat","")  or "").lower()
                        side  = (q.get("side","")  or "").upper()
                        pid   = str(q.get("player_id","") or "")

                        # Store under multiple keys for priority join
                        if pid:
                            qmap[(pid, stat, side)] = q
                        qmap[(player_norm, stat, side)] = q
                        qmap[("", stat, side)] = q  # loose fallback
                    except: continue
        except: continue

    # doc 6 §7 must do now: multi-key join — player_id > player_norm > loose stat
    for row in rows:
        player_norm = row["player"].lower().replace(" ","").replace(".","").replace("'","")
        pid = str(row.get("player_id","") or "")
        stat = row["stat"]; side = row["side"]

        best_q = None
        if pid:
            best_q = qmap.get((pid, stat, side))
        if best_q is None:
            best_q = qmap.get((player_norm, stat, side))
        # Loose fallback only if player_norm matches archive record
        if best_q is None:
            cand = qmap.get(("", stat, side))
            if cand:
                arch_norm = cand.get("player_norm") or (
                    (cand.get("player","") or "").lower().replace(" ","").replace(".","").replace("'",""))
                best_q = cand if arch_norm == player_norm else None

        if best_q:
            row["game_period"] = int(best_q.get("game_period", row["game_period"]) or 0)
            row["rem_minutes"] = best_q.get("rem_minutes_mean", row["rem_minutes"])
            row["fouls"]       = int(best_q.get("fouls", row["fouls"]) or 0)
            row["on_court"]    = bool(best_q.get("on_court", row["on_court"]))
            row["model_prob"]  = float(best_q.get("model_prob", row["model_prob"]) or 0.5)
            row["is_live"]     = best_q.get("game_status","pre-game") != "pre-game"
            row["action_score"]= float(best_q.get("action_score",0) or 0)
        else:
            row.setdefault("is_live", False)
            row.setdefault("action_score", 0.0)
    return rows


# ── FIT ALL CALIBRATORS ────────────────────────────────────────────────────────

def fit_all_calibrators(rows: list, min_samples: int) -> tuple:
    import math as _math
    # doc 6 §7 must also: separate live and pregame inventories
    # Live calibration learns only from live states; pregame from all
    live_rows    = [r for r in rows if r.get("is_live", False)]
    pregame_rows = [r for r in rows if not r.get("is_live", False)]
    print(f"  Live rows: {len(live_rows)} | Pregame rows: {len(pregame_rows)}", flush=True)

    # Group by primary key — live-only for live buckets
    bucket_data = defaultdict(lambda: {"probs":[],"outs":[],"weights":[]})
    for row in live_rows:  # live calibration uses live rows only
        key = make_primary_key(row["stat"], row["side"], row["game_period"],
                               row["rem_minutes"], row["fouls"], row["on_court"], row.get("is_ot",False))
        # doc 6 §7 must also: recency weighting (more recent rows weighted higher)
        # Simple proxy: action_score as quality weight; default to 1.0
        w = max(0.5, float(row.get("action_score", 0)) * 10 + 1.0)
        bucket_data[key]["probs"].append(row["model_prob"])
        bucket_data[key]["outs"].append(row["outcome_bin"])
        bucket_data[key]["weights"].append(w)

    # Fallback levels use ALL rows (live + pregame for robustness)
    stat_side_data = defaultdict(lambda: {"probs":[],"outs":[],"dates":[]})
    stat_data      = defaultdict(lambda: {"probs":[],"outs":[]})
    global_data    = {"probs":[],"outs":[]}
    for row in rows:
        fb1 = f"{row['stat'].lower()}|{row['side'].upper()}"
        fb2 = row["stat"].lower()
        stat_side_data[fb1]["probs"].append(row["model_prob"])
        stat_side_data[fb1]["outs"].append(row["outcome_bin"])
        stat_side_data[fb1]["dates"].append(row.get("date_str",""))
        stat_data[fb2]["probs"].append(row["model_prob"])
        stat_data[fb2]["outs"].append(row["outcome_bin"])
        stat_data[fb2]["dates"].append(row.get("date_str",""))
        global_data["probs"].append(row["model_prob"])
        global_data["outs"].append(row["outcome_bin"])
        global_data["dates"].append(row.get("date_str",""))

    calibrators = {}
    report_rows = []

    def _fit_bucket(key, probs, outs, level, dates=None):
        # Recency weighting: more recent observations get higher weight (doc 6 §7)
        p = np.array(probs)
        o = np.array(outs)
        if dates:
            import datetime as _dt
            today = _dt.date.today()
            weights = []
            for d in dates:
                try:
                    age = (today - _dt.date.fromisoformat(str(d))).days if d else 90
                except: age = 90
                weights.append(max(0.1, 1.0 - age / 180.0))  # decay over 180 days
            w = np.array(weights)
            # Apply weights by repeating samples proportionally (simple approach)
            w_norm = (w / w.sum() * len(w)).astype(int).clip(1, 5)
            p = np.repeat(p, w_norm)
            o = np.repeat(o, w_norm)
        n = len(p)
        cal = IsotonicCalibrator()
        if n >= min_samples:
            cal.fit(p, o, level)
        mean_p  = p.mean() if n > 0 else float("nan")
        hit_r   = o.mean() if n > 0 else float("nan")
        brier   = ((p-o)**2).mean() if n > 0 else 0.25
        cal_err = abs(mean_p - hit_r) if n > 0 else float("nan")
        d = cal.to_dict(n, float(brier), float(mean_p), float(hit_r))
        calibrators[key] = d
        report_rows.append({**d, "bucket_key":key, "cal_error":round(cal_err,4) if not math.isnan(cal_err) else None})

    import math
    # Primary buckets
    for key, data in bucket_data.items():
        _fit_bucket(key, data["probs"], data["outs"], "full_bucket", data.get("dates",[]))
    # Fallback stat|side
    for key, data in stat_side_data.items():
        _fit_bucket(key, data["probs"], data["outs"], "stat_side", data.get("dates",[]))
    # Fallback stat
    for key, data in stat_data.items():
        _fit_bucket(key, data["probs"], data["outs"], "stat", data.get("dates",[]))
    # Global fallback (instruction §7.2: identity only at global if nothing else)
    if global_data["probs"]:
        _fit_bucket("__global__", global_data["probs"], global_data["outs"], "global", global_data.get("dates",[]))
    else:
        calibrators["__global__"] = {"fitted":False,"level":"identity","n":0,
                                      "brier":0.25,"mean_prob":0.5,"hit_rate":0.5}

    return calibrators, report_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-samples", type=int, default=MIN_SAMPLES_DEFAULT)
    parser.add_argument("--output-dir", default=str(GRADED_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading graded data…")
    rows = load_graded_with_state()
    print(f"  {len(rows)} graded rows")

    if not rows:
        print("No graded data. Will accumulate after games grade.")
        # Write empty calibration file so API doesn't crash
        (out_dir/"state_bucket_calibration.json").write_text(json.dumps({"__global__":{
            "fitted":False,"level":"identity","n":0,"brier":0.25,"x_knots":None,"y_knots":None}}))
        return

    print(f"Fitting calibrators (min_samples={args.min_samples})…")
    cals, report = fit_all_calibrators(rows, args.min_samples)

    cal_path = out_dir / "state_bucket_calibration.json"
    with open(cal_path,"w") as f:
        json.dump(cals, f, indent=2)
    print(f"  Calibrators → {cal_path}")

    meta_path = out_dir / "state_bucket_meta.csv"
    if report:
        import math as _math
        fieldnames = ["bucket_key","level","n","brier","mean_prob","hit_rate","cal_error","fitted"]
        with open(meta_path,"w",newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(report)
    print(f"  Meta → {meta_path}")

    fitted_n    = sum(1 for r in report if r.get("fitted"))
    briers      = [r["brier"] for r in report if r.get("brier") is not None]
    mean_brier  = sum(briers)/len(briers) if briers else 0
    print(f"\nSummary: {len(report)} buckets | {fitted_n} fitted | mean Brier={mean_brier:.4f}")

    # Top errors
    errs = sorted([r for r in report if r.get("cal_error") is not None],
                  key=lambda x: x.get("cal_error",0) or 0, reverse=True)[:5]
    for r in errs:
        print(f"  {r['bucket_key']}: cal_error={r['cal_error']} n={r['n']}")


if __name__ == "__main__":
    main()
