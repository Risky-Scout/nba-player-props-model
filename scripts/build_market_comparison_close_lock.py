"""Build market_comparison_close_lock.parquet from closing_lines JSON."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from nba_props_model.markets.oddsapi_markets import stat_for_market_key


def american_to_decimal(o):
    if o is None or pd.isna(o):
        return None
    o = float(o)
    if o > 0:
        return 1.0 + o / 100.0
    if o < 0:
        return 1.0 - 100.0 / o
    return None


def devig_two_way(over_o, under_o):
    do = american_to_decimal(over_o)
    du = american_to_decimal(under_o)
    if do is None or du is None or do <= 1 or du <= 1:
        return None
    p_o = 1.0 / do
    p_u = 1.0 / du
    t = p_o + p_u
    return p_o / t if t > 0 else None


def parse_closing_lines(path):
    with open(path) as f:
        data = json.load(f)
    captured_at = data.get("captured_at", "")
    raw = []
    for game in data.get("games", []):
        for book in game.get("bookmakers", []):
            book_key = book.get("key") or book.get("title")
            for market in book.get("markets", []):
                stat = stat_for_market_key(str(market.get("key") or ""))
                if stat is None:
                    continue
                for outcome in market.get("outcomes", []):
                    side = outcome.get("name")
                    if side not in ("Over", "Under"):
                        continue
                    raw.append({"player_name": outcome.get("description"),
                                "stat": stat, "line": outcome.get("point"),
                                "book": book_key, "side": side,
                                "price": outcome.get("price")})
    if not raw:
        return pd.DataFrame(), captured_at
    df = pd.DataFrame(raw)
    pv = df.pivot_table(index=["player_name", "stat", "line", "book"],
                         columns="side", values="price",
                         aggfunc="first").reset_index()
    pv.columns.name = None
    pv = pv.rename(columns={"Over": "over_odds", "Under": "under_odds"})
    return pv, captured_at


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    d = args.date
    closing_path = REPO_ROOT / "artifacts" / "graded" / f"closing_lines_{d}.json"
    morning_path = REPO_ROOT / "deliveries" / d / "wizard_of_odds" / "market_comparison.parquet"
    out_path = REPO_ROOT / "deliveries" / d / "wizard_of_odds" / "market_comparison_close_lock.parquet"
    if not closing_path.exists():
        print(f"NO_CLOSING_LINES {closing_path}")
        return 0
    if not morning_path.exists():
        print(f"NO_MORNING_MARKET_COMP {morning_path}")
        return 0
    closing, captured_at = parse_closing_lines(closing_path)
    if closing.empty:
        print("EMPTY_CLOSING_LINES")
        return 0
    print(f"closing rows: {len(closing)}")
    morning = pd.read_parquet(morning_path)
    print(f"morning rows: {len(morning)}")
    merged = morning.merge(
        closing[["player_name", "stat", "line", "book", "over_odds", "under_odds"]],
        on=["player_name", "stat", "line", "book"], how="inner")
    if merged.empty:
        print("NO_MATCHES")
        return 0
    print(f"matched rows: {len(merged)}")
    merged["market_over_odds"] = merged["over_odds"].astype("Int64")
    merged["market_under_odds"] = merged["under_odds"].astype("Int64")
    merged["market_no_vig_over_prob"] = merged.apply(
        lambda r: devig_two_way(r["over_odds"], r["under_odds"]), axis=1)
    merged["edge"] = merged["model_p_over"] - merged["market_no_vig_over_prob"]
    merged["snapshot_type"] = "close_lock"
    if captured_at:
        merged["snapshot_time_utc"] = captured_at
    out = merged.drop(columns=["over_odds", "under_odds"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_path, index=False)
    em = out["edge"].mean()
    print(f"WROTE rows={len(out)} edge_mean={em:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
