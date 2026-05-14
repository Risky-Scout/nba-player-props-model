#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import pandas as pd

FORBIDDEN = ("ladder","p_ge","survival","cdf","cumulative","reconstructed","threshold")

def fail(msg): raise SystemExit(f"M8_6M_DEREK_OUTPUT_SCHEMA_FAIL: {msg}")

def parse_pmf(x):
    if x is None: fail("missing PMF")
    if isinstance(x, str): x = json.loads(x)
    if isinstance(x, list): return {i: float(v) for i, v in enumerate(x)}
    if isinstance(x, dict):
        bad = {str(k).lower() for k in x} & set(FORBIDDEN)
        if bad: fail(f"forbidden PMF keys: {sorted(bad)}")
        if "atom_pmf" in x: return parse_pmf(x["atom_pmf"])
        if "support" in x and "probs" in x: return {int(k): float(v) for k, v in zip(x["support"], x["probs"])}
        return {int(float(k)): float(v) for k, v in x.items()}
    fail(f"unsupported PMF type {type(x).__name__}")

def validate(x, ctx):
    atoms = parse_pmf(x)
    vals = list(atoms.values())
    if not vals: fail(f"{ctx}: empty PMF")
    if any(not math.isfinite(v) for v in vals): fail(f"{ctx}: non-finite PMF")
    if any(v < -1e-12 for v in vals): fail(f"{ctx}: negative PMF")
    if abs(sum(vals)-1) > 1e-6: fail(f"{ctx}: PMF sum={sum(vals)}")

def load(path):
    if path.suffix == ".parquet": return pd.read_parquet(path)
    if path.suffix == ".csv": return pd.read_csv(path)
    if path.suffix == ".jsonl": return pd.read_json(path, lines=True)
    if path.suffix == ".json":
        obj = json.loads(path.read_text())
        if isinstance(obj, list): return pd.DataFrame(obj)
        for k in ("rows","data","props"):
            if isinstance(obj.get(k), list): return pd.DataFrame(obj[k])
        return pd.DataFrame([obj])
    raise ValueError(path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    args = ap.parse_args()
    if args.date:
        roots = [
            Path("deliveries") / args.date / "derek_forward_feed",
            Path("deliveries") / args.date / "derek_game_snapshots",
        ]
    else:
        roots = [Path("deliveries")]
    files = []
    for r in roots:
        if r.exists(): files += [p for p in r.rglob("*") if p.suffix in (".parquet",".csv",".json",".jsonl")]
    if not files:
        print("M8_6M_DEREK_OUTPUT_SCHEMA_SKIP no Derek output files found yet")
        return 0
    checked = 0
    for f in files:
        try: df = load(f)
        except Exception: continue
        if df.empty: continue
        bad = [c for c in df.columns if "kelly" in c.lower()]
        if bad: fail(f"{f}: Derek has Kelly columns {bad}")
        cols = {c.lower(): c for c in df.columns}
        pmf_col = next((cols[c] for c in ("model_full_pmf","pmf","pmf_json","pmf_active") if c in cols), None)
        if not pmf_col: continue
        for i, v in df[pmf_col].head(500).items():
            validate(v, f"{f}:{i}")
            checked += 1
    if checked == 0: fail("no Derek rows with atom PMF found")
    print(f"M8_6M_DEREK_OUTPUT_SCHEMA_PASS pmfs_checked={checked}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
