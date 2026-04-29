"""Aggregate OOF-vs-OddsAPI market evaluator across a date window.

Reuses the leakage-safe match logic from
`scripts/evaluate_oof_vs_oddsapi_market.py` and aggregates across the
specified date range. Intended for the Phase 9C multi-day controlled
backfill window (2026-03-18 → 2026-03-31).

Inputs:
  - /tmp/phase8_full_vectorized_success/artifacts_downloaded/fold-*-oof/fold_*.parquet
  - artifacts/market_manifest/oof_player_game_crosswalk.parquet
  - data/odds_api/processed/{YYYY-MM-DD}/odds_pairs_hist_lockday_*.parquet (one per date)

Outputs:
  artifacts/phase9_market_eval/aggregate_{from}_to_{to}/
    aggregate_matches.parquet / .csv
    aggregate_summary.md
    by_stat.csv
    by_book.csv
    by_main_vs_alternate.csv
    by_line_bucket.csv
    by_role_bucket.csv
    calibration_bins_model.csv
    calibration_bins_market.csv
    alternate_ladder_shape_eval.csv
    date_coverage.csv

All hard validation gates from the per-day evaluator are preserved.
Single-day datasets are aggregated as-is; the aggregator does NOT
manufacture matches.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
OOF_ROOT_DEFAULT = Path("/tmp/phase8_full_vectorized_success/artifacts_downloaded")
ODDS_PROCESSED_DEFAULT = REPO_ROOT / "data" / "odds_api" / "processed"
CROSSWALK_DEFAULT = REPO_ROOT / "artifacts" / "market_manifest" / "oof_player_game_crosswalk.parquet"
OUT_ROOT = REPO_ROOT / "artifacts" / "phase9_market_eval"

STAT_TO_MARKET = {
    "pts": ("player_points", "player_points_alternate"),
    "reb": ("player_rebounds", "player_rebounds_alternate"),
    "ast": ("player_assists", "player_assists_alternate"),
    "tov": ("player_turnovers", "player_turnovers_alternate"),
    "fg3m": ("player_threes", "player_threes_alternate"),
}


def _norm_name(s) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[\.\,\']", "", s.lower().strip())
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\b\.?", "", s)
    return re.sub(r"\s+", " ", s)


def _parse_pmf(pmf_obj) -> np.ndarray:
    if isinstance(pmf_obj, str):
        d = json.loads(pmf_obj)
        max_k = max(int(k) for k in d.keys())
        arr = np.zeros(max_k + 1, dtype=float)
        for k, p in d.items():
            arr[int(k)] = float(p)
    else:
        arr = np.asarray(pmf_obj, dtype=float)
    s = arr.sum()
    if s > 0:
        arr = arr / s
    return arr


def _p_over_line(pmf: np.ndarray, line: float) -> float:
    """Strict discrete-integer settlement of P(stat > line).

    For a discrete integer-valued stat with PMF over {0..K-1}:
      - half-point line: P(over) + P(under) = 1, no push.
      - whole-number line: push mass at k == line is excluded from the
        over/under denominator (sportsbook settlement convention).

    Normalizing by `(p_over + p_under)` makes both cases consistent and
    avoids the floating-point epsilon trap where `1 - sum(pmf[:k+1])`
    can return -2.22e-16 when the PMF is fully concentrated below the line.
    """
    arr = np.asarray(pmf, dtype=float)
    arr = np.clip(arr, 0.0, None)
    s = arr.sum()
    if s <= 0 or not np.isfinite(s):
        return float("nan")
    arr = arr / s
    values = np.arange(len(arr))
    p_over = float(arr[values > line].sum())
    p_under = float(arr[values < line].sum())
    denom = p_over + p_under
    if denom <= 0 or not np.isfinite(denom):
        return float("nan")
    p = p_over / denom
    # Tiny floating-point epsilon clamp ONLY (don't silently fix material errors).
    if -1e-12 <= p <= 1 + 1e-12:
        return min(1.0, max(0.0, p))
    return p


def _logloss(p: np.ndarray, y: np.ndarray) -> float:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def _md_table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_(no rows)_"
    cols = list(df.columns)
    def _fmt(v):
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            return ""
        if isinstance(v, float):
            return f"{v:.4f}"
        return str(v)
    head = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = ["| " + " | ".join(_fmt(r[c]) for c in cols) + " |"
            for _, r in df.iterrows()]
    return "\n".join([head, sep] + rows)


def _calibration_bins(p: np.ndarray, y: np.ndarray, n_bins: int = 10) -> tuple[pd.DataFrame, float]:
    edges = np.linspace(0, 1, n_bins + 1)
    rows = []
    ece = 0.0
    n_total = max(len(p), 1)
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        n = int(mask.sum())
        if n == 0:
            rows.append({"bin_lo": lo, "bin_hi": hi, "n": 0,
                         "mean_pred": np.nan, "empirical_over_rate": np.nan,
                         "abs_calibration_error": np.nan})
            continue
        mp = float(p[mask].mean())
        mo = float(y[mask].mean())
        rows.append({"bin_lo": lo, "bin_hi": hi, "n": n,
                     "mean_pred": mp, "empirical_over_rate": mo,
                     "abs_calibration_error": abs(mp - mo)})
        ece += abs(mp - mo) * n / n_total
    return pd.DataFrame(rows), ece


def _date_range(start: str, end: str) -> list[str]:
    d0 = date.fromisoformat(start); d1 = date.fromisoformat(end)
    out = []
    while d0 <= d1:
        out.append(d0.isoformat())
        d0 += timedelta(days=1)
    return out


def _load_oof_for_dates(oof_root: Path, dates: list[str]) -> pd.DataFrame:
    folds = sorted(oof_root.glob("fold-*-oof/fold_*.parquet"),
                   key=lambda p: int(p.parent.name.split("-")[1]))
    df = pd.concat([pd.read_parquet(p) for p in folds], ignore_index=True)
    df["game_date"] = df["game_date"].astype(str).str[:10]
    return df[df.game_date.isin(dates)].reset_index(drop=True)


def _load_pairs_for_dates(processed_dir: Path, dates: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load all odds_pairs_*.parquet for the dates. Return (pairs, coverage_df)."""
    frames = []
    cov = []
    for d in dates:
        day = processed_dir / d
        files = sorted(day.glob("odds_pairs_*.parquet")) if day.exists() else []
        rows = 0
        sources = []
        for fp in files:
            try:
                df = pd.read_parquet(fp)
                if df.empty:
                    continue
                df["__source_file"] = fp.name
                df["__source_date"] = d
                frames.append(df)
                rows += len(df)
                sources.append(fp.name)
            except Exception as e:
                print(f"  WARN: read failed for {fp}: {e}")
        cov.append({"date": d, "files": len(files),
                    "non_empty_files": len(sources),
                    "pair_rows": rows,
                    "source_filenames": "|".join(sources)})
    coverage = pd.DataFrame(cov)
    pairs = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return pairs, coverage


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from-date", required=True, help="YYYY-MM-DD inclusive")
    ap.add_argument("--to-date", required=True, help="YYYY-MM-DD inclusive")
    ap.add_argument("--oof-root", default=str(OOF_ROOT_DEFAULT))
    ap.add_argument("--processed-dir", default=str(ODDS_PROCESSED_DEFAULT))
    ap.add_argument("--crosswalk", default=str(CROSSWALK_DEFAULT))
    args = ap.parse_args()

    dates = _date_range(args.from_date, args.to_date)
    out_dir = OUT_ROOT / f"aggregate_{args.from_date}_to_{args.to_date}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"PHASE 9C AGGREGATE — {args.from_date} → {args.to_date}  ({len(dates)} dates)")
    print("=" * 72)

    # 1. OOF
    oof = _load_oof_for_dates(Path(args.oof_root), dates)
    print(f"\n[OOF] rows in window: {len(oof):,}; "
          f"games: {oof.game_id.nunique() if not oof.empty else 0}; "
          f"players: {oof.player_id.nunique() if not oof.empty else 0}")
    if oof.empty:
        print("  ERROR: no OOF rows in window — nothing to evaluate.")
        return 1

    # 2. Crosswalk
    if not Path(args.crosswalk).exists():
        print(f"  ERROR: crosswalk missing: {args.crosswalk}")
        return 1
    xw = pd.read_parquet(args.crosswalk)
    xw["normalized_player_name"] = xw["normalized_player_name"].astype(str)
    print(f"[CROSSWALK] rows: {len(xw):,}; "
          f"unique (game_id, player_id): {xw.drop_duplicates(['game_id','player_id']).shape[0]:,}")

    # 3. Pairs
    pairs, coverage = _load_pairs_for_dates(Path(args.processed_dir), dates)
    coverage.to_csv(out_dir / "date_coverage.csv", index=False)
    print(f"\n[ODDS] paired rows across window: {len(pairs):,}")
    print(coverage.to_string(index=False))
    if pairs.empty:
        print("  ERROR: no Odds API paired rows in window — cannot aggregate.")
        return 2

    # 4. Leakage filter
    leakage_violations = 0
    if "snapshot_time_utc" in pairs.columns and "commence_time_utc" in pairs.columns:
        bad = pairs["snapshot_time_utc"].astype(str) > pairs["commence_time_utc"].astype(str)
        leakage_violations = int(bad.sum())
        if leakage_violations:
            print(f"  WARN: dropping {leakage_violations} leakage rows")
            pairs = pairs[~bad].reset_index(drop=True)

    pairs["market_stat"] = pairs["market_stat"].astype(str)
    pairs["normalized_player_name"] = pairs["player_name"].map(_norm_name)
    pairs["commence_date"] = pairs["commence_time_utc"].astype(str).str[:10]
    print(f"[ODDS] post-leakage rows: {len(pairs):,}")

    # 5. Build OOF-named (dedupe crosswalk on game_id, player_id — name/team are stat-invariant)
    name_proj = (xw[["game_id", "player_id", "player_name",
                     "normalized_player_name", "team_abbr", "opponent_abbr"]]
                  .drop_duplicates(["game_id", "player_id"]))
    oof_keyed = oof.merge(name_proj, on=["game_id", "player_id"], how="left")
    if len(oof_keyed) != len(oof):
        raise SystemExit(
            f"INTERNAL: oof_keyed row count {len(oof_keyed)} != oof "
            f"row count {len(oof)} — name-projection dedupe failed"
        )
    oof_keyed["game_date"] = oof_keyed["game_date"].astype(str).str[:10]

    # 6. Strict join: (game_date, normalized_player_name, market_stat=stat)
    matches = pairs.merge(
        oof_keyed[["game_id", "player_id", "player_name", "normalized_player_name",
                   "team_abbr", "opponent_abbr",
                   "stat", "game_date", "outcome", "pmf", "pmf_active",
                   "role_bucket", "minutes_mean"]],
        left_on=["commence_date", "normalized_player_name", "market_stat"],
        right_on=["game_date", "normalized_player_name", "stat"], how="inner",
    )
    print(f"\n[MATCH] aggregated matched rows: {len(matches):,}")

    if not matches.empty:
        bad_stat = int((matches["market_stat"] != matches["stat"]).sum())
        if bad_stat:
            raise SystemExit(f"FAIL gate B: {bad_stat} matched rows have market_stat != stat")
    if len(pairs) and len(matches) > int(len(pairs) * 1.10):
        raise SystemExit(
            f"FAIL gate A: matched_rows ({len(matches)}) > pairs × 1.10 "
            f"({len(pairs) * 1.10:.1f})"
        )

    # 7. PMF + p_over computation + per-row gates
    pmf_sum_failures = 0
    pmf_neg_failures = 0
    pmf_nonfinite_failures = 0
    pov_oor = 0

    def _model_pov(row):
        nonlocal pmf_sum_failures, pmf_neg_failures, pmf_nonfinite_failures, pov_oor
        line = row.get("line")
        if line is None or (isinstance(line, float) and not np.isfinite(line)):
            return None
        src = row["pmf_active"] if row.get("pmf_active") is not None else row.get("pmf")
        if src is None:
            return None
        pmf = _parse_pmf(src)
        s = float(np.asarray(pmf, dtype=float).sum())
        if abs(s - 1.0) > 1e-6:
            pmf_sum_failures += 1
        if (np.asarray(pmf) < -1e-12).any():
            pmf_neg_failures += 1
        if not np.all(np.isfinite(pmf)):
            pmf_nonfinite_failures += 1
        pov = _p_over_line(pmf, float(line))
        if pov is None or not np.isfinite(pov) or pov < 0.0 or pov > 1.0:
            pov_oor += 1
            return None
        return pov

    matches["model_p_over_line"] = matches.apply(_model_pov, axis=1)

    # Hard gates summary
    print(f"\n[GATES — strict checks]")
    print(f"  pairs_after_leakage:                 {len(pairs):,}")
    print(f"  matched_rows:                        {len(matches):,}")
    print(f"  matched/pairs ratio:                 "
          f"{len(matches)/max(len(pairs),1):.2f}  (gate A: ≤ 1.10)")
    print(f"  market_stat == stat failures:         "
          f"{int((matches['market_stat'] != matches['stat']).sum()) if not matches.empty else 0}")
    print(f"  PMF sum failures:                    {pmf_sum_failures}")
    print(f"  PMF negative-prob failures:          {pmf_neg_failures}")
    print(f"  PMF non-finite failures:             {pmf_nonfinite_failures}")
    print(f"  model_p_over_line out-of-range:      {pov_oor}")
    print(f"  leakage violations dropped:          {leakage_violations}")
    if pmf_sum_failures or pmf_neg_failures or pmf_nonfinite_failures or pov_oor:
        raise SystemExit("FAIL: PMF or p_over validity gate violated.")

    matches["over_realized"] = (matches["outcome"].astype(int) > matches["line"].astype(float)).astype(int)
    matches["is_push"] = (matches["line"].astype(float).round() == matches["line"].astype(float)) \
                        & (matches["outcome"].astype(int) == matches["line"].astype(float).astype(int))
    matches["edge"] = matches["model_p_over_line"] - matches["no_vig_over_prob"]

    # 8. Save match-level table
    matches.to_parquet(out_dir / "aggregate_matches.parquet", index=False)
    matches.to_csv(out_dir / "aggregate_matches.csv", index=False)
    print(f"\n[OUTPUT] wrote {(out_dir / 'aggregate_matches.parquet').relative_to(REPO_ROOT)} "
          f"({len(matches)} rows)")

    # 9. Eval set + overall metrics
    eval_set = matches[~matches["is_push"]
                       & matches["model_p_over_line"].notna()
                       & matches["no_vig_over_prob"].notna()].copy()
    print(f"[SCORE] eval set (non-push, both probs finite): {len(eval_set):,} of {len(matches):,}")

    overall = {}
    if not eval_set.empty:
        y = eval_set["over_realized"].to_numpy().astype(int)
        pm = eval_set["model_p_over_line"].to_numpy().astype(float)
        pk = eval_set["no_vig_over_prob"].to_numpy().astype(float)
        overall = {
            "n_matched": int(len(matches)),
            "n_non_push": int(len(eval_set)),
            "model_logloss": _logloss(pm, y),
            "market_logloss": _logloss(pk, y),
            "model_brier": _brier(pm, y),
            "market_brier": _brier(pk, y),
            "obs_over_rate": float(y.mean()),
            "mean_p_model": float(pm.mean()),
            "mean_p_market": float(pk.mean()),
        }
        overall["d_logloss"] = overall["model_logloss"] - overall["market_logloss"]
        overall["d_brier"] = overall["model_brier"] - overall["market_brier"]

        print(f"\n[OVERALL]")
        for k, v in overall.items():
            print(f"  {k:>20s}: {v:.4f}" if isinstance(v, float) else f"  {k:>20s}: {v}")

    # 10. Stratifications
    def _by_group(group_col_or_func, label_col):
        rows = []
        if eval_set.empty:
            return pd.DataFrame()
        grouped = eval_set.groupby(group_col_or_func, dropna=False)
        for k, sub in grouped:
            if len(sub) < 5: continue
            y = sub["over_realized"].to_numpy().astype(int)
            pm = sub["model_p_over_line"].to_numpy().astype(float)
            pk = sub["no_vig_over_prob"].to_numpy().astype(float)
            rows.append({label_col: k, "n": int(len(sub)),
                         "model_logloss": _logloss(pm, y),
                         "market_logloss": _logloss(pk, y),
                         "model_brier": _brier(pm, y),
                         "market_brier": _brier(pk, y),
                         "obs_over_rate": float(y.mean()),
                         "mean_p_model": float(pm.mean()),
                         "mean_p_market": float(pk.mean())})
        df = pd.DataFrame(rows)
        if not df.empty:
            df["d_logloss"] = df["model_logloss"] - df["market_logloss"]
            df["d_brier"] = df["model_brier"] - df["market_brier"]
        return df

    by_stat = _by_group("stat", "stat")
    by_book = _by_group("bookmaker_key", "bookmaker_key")
    by_alt = pd.DataFrame()
    if "is_alternate" in eval_set.columns:
        by_alt = _by_group(eval_set["is_alternate"].astype(bool).map({True: "alternate", False: "main"}), "kind")
    by_date = _by_group("commence_date", "date")
    by_role = _by_group("role_bucket", "role_bucket")
    # Line bucket: by stat × decile of line within stat
    line_bucket_rows = []
    if not eval_set.empty:
        for stat_key, sub in eval_set.groupby("stat"):
            try:
                buckets = pd.qcut(sub["line"].astype(float),
                                  q=min(4, sub["line"].nunique()), duplicates="drop")
            except Exception:
                continue
            for q, g in sub.groupby(buckets, observed=True):
                if len(g) < 5: continue
                y = g["over_realized"].to_numpy().astype(int)
                pm = g["model_p_over_line"].to_numpy().astype(float)
                pk = g["no_vig_over_prob"].to_numpy().astype(float)
                line_bucket_rows.append({
                    "stat": stat_key, "line_bucket": str(q), "n": int(len(g)),
                    "model_logloss": _logloss(pm, y),
                    "market_logloss": _logloss(pk, y),
                    "model_brier": _brier(pm, y),
                    "market_brier": _brier(pk, y),
                    "obs_over_rate": float(y.mean()),
                })
    by_line = pd.DataFrame(line_bucket_rows)

    by_stat.to_csv(out_dir / "by_stat.csv", index=False)
    by_book.to_csv(out_dir / "by_book.csv", index=False)
    by_alt.to_csv(out_dir / "by_main_vs_alternate.csv", index=False)
    by_date.to_csv(out_dir / "by_date.csv", index=False)
    by_role.to_csv(out_dir / "by_role_bucket.csv", index=False)
    by_line.to_csv(out_dir / "by_line_bucket.csv", index=False)

    # Calibration bins (10)
    cal_model_df, ece_model = (pd.DataFrame(), float("nan"))
    cal_market_df, ece_market = (pd.DataFrame(), float("nan"))
    if not eval_set.empty:
        y = eval_set["over_realized"].to_numpy().astype(int)
        pm = eval_set["model_p_over_line"].to_numpy().astype(float)
        pk = eval_set["no_vig_over_prob"].to_numpy().astype(float)
        cal_model_df, ece_model = _calibration_bins(pm, y, n_bins=10)
        cal_market_df, ece_market = _calibration_bins(pk, y, n_bins=10)
    cal_model_df.to_csv(out_dir / "calibration_bins_model.csv", index=False)
    cal_market_df.to_csv(out_dir / "calibration_bins_market.csv", index=False)

    # Alternate-line ladder shape eval
    ladder_rows = []
    monot_violations_total = 0
    feasible_pmf_recon = 0
    if "is_alternate" in eval_set.columns:
        groups = eval_set.groupby(
            ["normalized_player_name", "stat", "bookmaker_key", "snapshot_time_utc"],
            dropna=False,
        )
        for (pname, stat_key, book, snap), g in groups:
            g_sorted = g.sort_values("line").reset_index(drop=True)
            if len(g_sorted) < 3:
                continue
            mkt = g_sorted["no_vig_over_prob"].to_numpy()
            mod = g_sorted["model_p_over_line"].to_numpy()
            err = np.abs(mod - mkt)
            mkt_violations = int(np.sum(np.diff(mkt) > 1e-9))
            mod_violations = int(np.sum(np.diff(mod) > 1e-9))
            monot_violations_total += max(mkt_violations, mod_violations)
            recon_ok = (mkt_violations == 0) and (g_sorted["line"].is_monotonic_increasing) \
                       and (len(g_sorted) >= 3)
            if recon_ok:
                feasible_pmf_recon += 1
            ladder_rows.append({
                "normalized_player_name": pname, "stat": stat_key,
                "bookmaker_key": book, "snapshot_time_utc": snap,
                "n_lines": int(len(g_sorted)),
                "min_line": float(g_sorted["line"].min()),
                "max_line": float(g_sorted["line"].max()),
                "mean_abs_diff_p_over": float(err.mean()),
                "median_abs_diff_p_over": float(np.median(err)),
                "max_abs_diff_p_over": float(err.max()),
                "model_monotonicity_violations": mod_violations,
                "market_monotonicity_violations": mkt_violations,
                "feasible_market_pmf_recon": bool(recon_ok),
            })
    ladder_df = pd.DataFrame(ladder_rows)
    ladder_df.to_csv(out_dir / "alternate_ladder_shape_eval.csv", index=False)

    # 11. aggregate_summary.md
    md = [
        f"# Phase 9C aggregate market eval — {args.from_date} → {args.to_date}",
        "",
        f"- Dates in window: **{len(dates)}**",
        f"- OOF rows in window: **{len(oof):,}**",
        f"- Odds paired rows post-leakage: **{len(pairs):,}**",
        f"- Matched rows: **{len(matches):,}**",
        f"- Non-push eval rows: **{len(eval_set):,}**",
        f"- Leakage violations dropped: **{leakage_violations}**",
        "",
    ]
    if overall:
        md += ["## Overall (non-push)", "",
               "| Metric | Model | Market (no-vig) | Δ(model − market) |",
               "|---|---:|---:|---:|",
               f"| logloss | {overall['model_logloss']:.4f} | "
               f"{overall['market_logloss']:.4f} | {overall['d_logloss']:+.4f} |",
               f"| Brier   | {overall['model_brier']:.4f} | "
               f"{overall['market_brier']:.4f} | {overall['d_brier']:+.4f} |",
               f"| mean predicted | {overall['mean_p_model']:.4f} | {overall['mean_p_market']:.4f} | "
               f"{overall['mean_p_model']-overall['mean_p_market']:+.4f} |",
               f"| obs over rate | — | — | {overall['obs_over_rate']:.4f} |",
               ""]
    md += ["## By stat", "", _md_table(by_stat), ""]
    md += ["## By book", "", _md_table(by_book), ""]
    md += ["## By main vs alternate", "", _md_table(by_alt), ""]
    md += ["## By line bucket", "", _md_table(by_line), ""]
    md += ["## By role_bucket", "", _md_table(by_role), ""]
    md += ["## By date", "", _md_table(by_date), ""]
    md += ["## Calibration (model)", "",
           f"ECE (10 bins, weighted): **{ece_model:.4f}**", "",
           _md_table(cal_model_df), ""]
    md += ["## Calibration (market no-vig)", "",
           f"ECE (10 bins, weighted): **{ece_market:.4f}**", "",
           _md_table(cal_market_df), ""]
    md += ["## Alternate-line ladder shape", "",
           f"- Ladder groups (≥3 lines): **{len(ladder_df)}**",
           (f"- Average ladder size: **{ladder_df.n_lines.mean():.2f}**"
            if not ladder_df.empty else "- Average ladder size: n/a"),
           (f"- Median |Δ p_over| across groups: **{ladder_df.median_abs_diff_p_over.median():.4f}**"
            if not ladder_df.empty else "- Median |Δ p_over|: n/a"),
           f"- Monotonicity violations (sum across groups): **{monot_violations_total}**",
           f"- Groups feasible for market-implied PMF recon: **{feasible_pmf_recon}** of {len(ladder_df)}",
           ""]
    md += [
        "## Honest framing",
        "",
        "This is a controlled multi-day diagnostic, not a market-beating",
        "claim. Numbers are computed leakage-safe (snapshot ≤ commence) and",
        "the join is strict on `(game_date, normalized_player_name, stat)`.",
        "Recommended next steps appear in the project's "
        "`docs/phase9_aggregate_market_eval_plan.md`.",
        "",
    ]
    (out_dir / "aggregate_summary.md").write_text("\n".join(md))
    print(f"\nWrote {(out_dir / 'aggregate_summary.md').relative_to(REPO_ROOT)}")

    # Final hard-gate check
    if len(matches) == 0:
        print("\nFAIL: aggregate matched rows = 0")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
