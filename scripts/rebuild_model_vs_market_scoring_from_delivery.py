#!/usr/bin/env python3
import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd


def norm_col(c):
    return str(c).strip().lower()


def norm_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip()


def norm_stat(x):
    s = norm_text(x).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    mapping = {
        "points": "pts",
        "point": "pts",
        "pts": "pts",
        "rebounds": "reb",
        "rebound": "reb",
        "reb": "reb",
        "assists": "ast",
        "assist": "ast",
        "ast": "ast",
        "threes": "fg3m",
        "three_pointers": "fg3m",
        "three_point_made": "fg3m",
        "three_pointers_made": "fg3m",
        "3pm": "fg3m",
        "fg3m": "fg3m",
        "turnovers": "tov",
        "turnover": "tov",
        "tov": "tov",
        "steals": "stl",
        "steal": "stl",
        "stl": "stl",
        "blocks": "blk",
        "block": "blk",
        "blk": "blk",
        "stocks": "stocks",
        "pts_ast": "pa",
        "points_assists": "pa",
        "pa": "pa",
        "pts_reb": "pr",
        "points_rebounds": "pr",
        "pr": "pr",
        "reb_ast": "ra",
        "rebounds_assists": "ra",
        "ra": "ra",
        "pts_reb_ast": "pra",
        "points_rebounds_assists": "pra",
        "pra": "pra",
    }
    return mapping.get(s, s)


def pick(df, candidates, required=True, label="column"):
    cols = {norm_col(c): c for c in df.columns}
    for c in candidates:
        if norm_col(c) in cols:
            return cols[norm_col(c)]
    if required:
        raise SystemExit(f"FAIL: could not find {label}. candidates={candidates} available={list(df.columns)}")
    return None


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def american_to_prob(x):
    if pd.isna(x):
        return math.nan
    txt = str(x).replace("+", "").strip()
    if txt == "":
        return math.nan
    try:
        odds = float(txt)
    except Exception:
        return math.nan
    if odds > 0:
        return 100.0 / (odds + 100.0)
    if odds < 0:
        return abs(odds) / (abs(odds) + 100.0)
    return math.nan


def read_csv(path):
    if not path.exists():
        raise SystemExit(f"FAIL: missing source file: {path}")
    return pd.read_csv(path, low_memory=False)


def simple_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._\n"

    cols = [str(c) for c in df.columns]
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")

    for _, row in df.iterrows():
        vals = []
        for c in df.columns:
            v = row[c]
            if pd.isna(v):
                vals.append("")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    date = args.date
    root = Path("deliveries") / date

    market_path = root / "wizard_of_odds" / "market_comparison.csv"
    pmf_path = root / "wizard_of_odds" / "full_pmfs_outcome_level.csv"
    actuals_path = root / "after_game_scoring" / "after_game_scoring.csv"
    out_dir = root / "after_game_scoring"
    out_dir.mkdir(parents=True, exist_ok=True)

    market = read_csv(market_path)
    pmf = read_csv(pmf_path)
    actuals = read_csv(actuals_path)

    print(f"market rows: {len(market):,} from {market_path}")
    print(f"pmf rows: {len(pmf):,} from {pmf_path}")
    print(f"actual rows: {len(actuals):,} from {actuals_path}")

    m_player = pick(market, ["player_id", "player_name", "player"], label="market player")
    m_stat = pick(market, ["stat", "stat_key", "market", "prop_type"], label="market stat")
    m_line = pick(market, ["line", "market_line", "threshold"], label="market line")
    m_book = pick(market, ["book", "sportsbook", "bookmaker"], required=False, label="market book")
    m_side = pick(market, ["side", "bet_side"], required=False, label="market side")
    m_odds = pick(market, ["side_odds", "odds", "price", "american_odds"], required=False, label="side odds")
    m_over_odds = pick(market, ["market_over_odds", "over_odds"], required=False, label="over odds")
    m_under_odds = pick(market, ["market_under_odds", "under_odds"], required=False, label="under odds")
    m_nv_over = pick(market, ["market_no_vig_over_prob", "no_vig_over_prob"], required=False, label="no-vig over prob")

    p_player = pick(pmf, ["player_id", "player_name", "player"], label="pmf player")
    p_stat = pick(pmf, ["stat", "stat_key", "market", "prop_type"], label="pmf stat")
    p_k = pick(pmf, ["k", "outcome", "stat_value", "value"], label="pmf outcome k")
    p_prob = pick(pmf, ["p_k", "prob", "probability", "pmf_prob", "p", "model_prob"], label="pmf probability")

    a_player = pick(actuals, ["player_id", "player_name", "player"], label="actual player")
    a_stat = pick(actuals, ["stat", "stat_key", "market", "prop_type"], label="actual stat")
    a_actual = pick(actuals, ["actual_outcome", "actual", "actual_value", "k_actual", "outcome"], label="actual value")

    market = market.copy()
    pmf = pmf.copy()
    actuals = actuals.copy()

    market["_player_key"] = market[m_player].map(norm_text)
    market["_stat"] = market[m_stat].map(norm_stat)
    market["_line"] = to_num(market[m_line])

    pmf["_player_key"] = pmf[p_player].map(norm_text)
    pmf["_stat"] = pmf[p_stat].map(norm_stat)
    pmf["_k"] = to_num(pmf[p_k])
    pmf["_prob"] = to_num(pmf[p_prob])

    actuals["_player_key"] = actuals[a_player].map(norm_text)
    actuals["_stat"] = actuals[a_stat].map(norm_stat)
    actuals["_actual"] = to_num(actuals[a_actual])

    pmf = pmf.dropna(subset=["_player_key", "_stat", "_k", "_prob"])
    actuals = actuals.dropna(subset=["_player_key", "_stat", "_actual"])

    actual_lookup = (
        actuals.sort_values(["_player_key", "_stat"])
        .drop_duplicates(["_player_key", "_stat"])
        .set_index(["_player_key", "_stat"])["_actual"]
        .to_dict()
    )

    # Build market offers.
    offers = []

    if m_side and m_odds:
        tmp = market.dropna(subset=["_player_key", "_stat", "_line"]).copy()
        tmp["_side"] = tmp[m_side].astype(str).str.lower().str.strip()
        tmp["_odds"] = tmp[m_odds]

        group_cols = ["_player_key", "_stat", "_line"]
        if m_book:
            tmp["_book"] = tmp[m_book].map(norm_text)
            group_cols.append("_book")
        else:
            tmp["_book"] = ""

        for keys, g in tmp.groupby(group_cols, dropna=False):
            row = g.iloc[0].to_dict()
            over = g[g["_side"].str.contains("over", na=False)]
            under = g[g["_side"].str.contains("under", na=False)]
            row["_market_over_odds"] = over["_odds"].iloc[0] if len(over) else None
            row["_market_under_odds"] = under["_odds"].iloc[0] if len(under) else None
            offers.append(row)
    else:
        tmp = market.dropna(subset=["_player_key", "_stat", "_line"]).copy()
        if m_book:
            tmp["_book"] = tmp[m_book].map(norm_text)
        else:
            tmp["_book"] = ""
        tmp["_market_over_odds"] = tmp[m_over_odds] if m_over_odds else None
        tmp["_market_under_odds"] = tmp[m_under_odds] if m_under_odds else None
        offers = tmp.to_dict(orient="records")

    rows = []
    pmf_groups = {
        key: g[["_k", "_prob"]].copy()
        for key, g in pmf.groupby(["_player_key", "_stat"], dropna=False)
    }

    for row in offers:
        player_key = norm_text(row.get("_player_key"))
        stat = norm_stat(row.get("_stat"))
        line = row.get("_line")

        if pd.isna(line):
            continue

        actual = actual_lookup.get((player_key, stat))
        dist = pmf_groups.get((player_key, stat))

        if actual is None or dist is None or dist.empty:
            continue

        over_odds = row.get("_market_over_odds")
        under_odds = row.get("_market_under_odds")

        p_over_market = math.nan
        if m_nv_over and row.get(m_nv_over) not in [None, ""]:
            p_over_market = pd.to_numeric(pd.Series([row.get(m_nv_over)]), errors="coerce").iloc[0]

        if pd.isna(p_over_market):
            imp_over = american_to_prob(over_odds)
            imp_under = american_to_prob(under_odds)
            if not pd.isna(imp_over) and not pd.isna(imp_under) and (imp_over + imp_under) > 0:
                p_over_market = imp_over / (imp_over + imp_under)

        p_over = float(dist.loc[dist["_k"] > line, "_prob"].sum())
        p_under = float(dist.loc[dist["_k"] < line, "_prob"].sum())
        p_push = float(dist.loc[dist["_k"] == line, "_prob"].sum())

        if actual > line:
            result = "over"
            model_result_prob = p_over
        elif actual < line:
            result = "under"
            model_result_prob = p_under
        else:
            result = "push"
            model_result_prob = p_push

        out = {
            "date": date,
            "book": row.get("_book", ""),
            "player_key": player_key,
            "player_name": row.get("player_name", row.get("player", player_key)),
            "player_id": row.get("player_id", ""),
            "team": row.get("team", ""),
            "opponent": row.get("opponent", ""),
            "stat": stat,
            "line": float(line),
            "actual": float(actual),
            "result": result,
            "model_p_over": p_over,
            "model_p_under": p_under,
            "model_p_push": p_push,
            "model_result_prob": model_result_prob,
            "market_over_odds": over_odds,
            "market_under_odds": under_odds,
            "market_no_vig_over_prob": p_over_market,
            "edge_over": p_over - p_over_market if not pd.isna(p_over_market) else math.nan,
        }
        rows.append(out)

    scored = pd.DataFrame(rows)

    if scored.empty:
        raise SystemExit(
            "FAIL: rebuilt model-vs-market still produced zero rows. "
            f"market_cols={list(market.columns)} pmf_cols={list(pmf.columns)} actual_cols={list(actuals.columns)}"
        )

    scored_csv = out_dir / "model_vs_market_scoring.csv"
    scored_parquet = out_dir / "model_vs_market_scoring.parquet"
    scored_json = out_dir / "model_vs_market_scoring.json"
    scored_md = out_dir / "model_vs_market_scoring.md"

    scored.to_csv(scored_csv, index=False)
    scored.to_parquet(scored_parquet, index=False)

    summary = {
        "date": date,
        "status": "pass",
        "source": "rebuilt_from_delivery_market_pmf_actuals",
        "rows": int(len(scored)),
        "non_push_rows": int((scored["result"] != "push").sum()),
        "push_rows": int((scored["result"] == "push").sum()),
        "stats": scored["stat"].value_counts().sort_index().to_dict(),
        "books": scored["book"].value_counts().head(30).to_dict(),
    }

    scored_json.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    by_stat = scored.groupby("stat").size().reset_index(name="rows").sort_values("stat")
    scored_md.write_text(
        "# Model vs Market Scoring\n\n"
        f"- date: `{date}`\n"
        "- status: `pass`\n"
        "- source: `rebuilt_from_delivery_market_pmf_actuals`\n"
        f"- rows: `{len(scored)}`\n"
        f"- non-push rows: `{summary['non_push_rows']}`\n"
        f"- push rows: `{summary['push_rows']}`\n\n"
        "## Rows by stat\n\n"
        + simple_markdown_table(by_stat)
        + "\n"
    )

    for p in [
        out_dir / "model_vs_market_scoring_blocked.md",
        out_dir / "model_vs_market_scoring_blocked.json",
    ]:
        if p.exists():
            p.unlink()

    print("MODEL_VS_MARKET_REBUILD_PASS")
    print(f"rows={len(scored):,}")
    print(f"non_push_rows={summary['non_push_rows']:,}")
    print(f"push_rows={summary['push_rows']:,}")
    print(f"wrote {scored_csv}")
    print(f"wrote {scored_parquet}")
    print(f"wrote {scored_json}")
    print(f"wrote {scored_md}")


if __name__ == "__main__":
    main()
