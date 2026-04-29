"""Score a daily PMF delivery after games are final.

Reads the day's delivery (Derek package + Wizard of Odds package) and the
realized outcomes, then emits scoring artifacts:

  deliveries/YYYY-MM-DD/pmf_model_review_package/
    after_game_scoring.csv
    after_game_scoring.parquet
    after_game_summary.md

  deliveries/YYYY-MM-DD/wizard_of_odds/
    after_game_clv_and_scoring.csv
    after_game_clv_and_scoring.parquet
    after_game_clv_and_scoring.md

  deliveries/YYYY-MM-DD/wizard_of_odds/
    calibration_by_stat.csv
    calibration_by_role_bucket.csv
    clv_by_stat.csv
    clv_by_book.csv

Inputs:
  - deliveries/{date}/wizard_of_odds/full_pmfs_wide.parquet  (canonical PMFs)
  - deliveries/{date}/wizard_of_odds/market_comparison.parquet  (per-line market join)
  - --outcomes path/to/outcomes_{date}.parquet  (player_id, stat, outcome) OR
    --use-stats-table (pull from data/player_game_stats.parquet)
  - --close-snapshot path/to/wizard_of_odds@close_lock if present (else inferred)

Hard rules:
  - Score the canonical model-only PMF, not any market-anchored variant.
  - Walk-forward / point-in-time only — the scorer never modifies PMFs.
  - Sparse market does not drop rows; rows without `line` are still scored
    on PMF metrics (NLL, RPS, mean error, outcome-prob assigned).

This script makes no Odds-API call.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent

P_GE_COLS = [f"p_ge_{k}" for k in range(1, 21)]


# ── Outcome loading ─────────────────────────────────────────────────────


STAT_TO_WIDE_COL = {
    "pts": "pts", "reb": "reb", "ast": "ast",
    "tov": "turnover", "fg3m": "fg3m",
}


def load_outcomes(args, delivery_date: str) -> pd.DataFrame:
    """Return long-form DataFrame with columns: player_id, stat, outcome.

    Accepts either:
      - long format with (player_id, stat, outcome), or
      - wide format with (player_id, game_date, pts/reb/ast/turnover/fg3m).

    Preferred path: an explicit parquet via --outcomes.
    Fallback: derive from data/player_game_stats.parquet for the date.
    """
    if args.outcomes:
        path = Path(args.outcomes)
        df = pd.read_parquet(path)
    else:
        path = REPO_ROOT / "data" / "player_game_stats.parquet"
        if not path.exists():
            raise SystemExit(f"no outcomes source: {path} missing and "
                              f"--outcomes not supplied")
        df = pd.read_parquet(path)
    if "game_date" in df.columns:
        df = df[df["game_date"].astype(str).str[:10] == delivery_date]
    if {"player_id", "stat", "outcome"}.issubset(df.columns):
        out = df[["player_id", "stat", "outcome"]].copy()
    else:
        # Wide → long melt over the supported stat columns.
        keep = [c for c in df.columns if c in STAT_TO_WIDE_COL.values()
                or c == "player_id"]
        if "player_id" not in keep:
            raise SystemExit("outcomes table has no player_id column")
        sub = df[keep].copy()
        rows = []
        for stat, wide_col in STAT_TO_WIDE_COL.items():
            if wide_col not in sub.columns:
                continue
            vals = sub[["player_id", wide_col]].dropna()
            for _, r in vals.iterrows():
                rows.append({"player_id": r["player_id"], "stat": stat,
                             "outcome": int(r[wide_col])})
        out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["player_id"] = out["player_id"].astype("Int64")
    out["stat"] = out["stat"].astype(str)
    out["outcome"] = out["outcome"].astype(int)
    return out[["player_id", "stat", "outcome"]]


# ── PMF reconstruction from p_ge ladder ─────────────────────────────────


def _pmf_from_pge(row: pd.Series, max_k: int = 21) -> np.ndarray:
    """Reconstruct PMF from p0 + p_ge_1 ... p_ge_20.

    p_k = p_ge_k - p_ge_(k+1) for k >= 1
    p_0 = 1 - p_ge_1
    """
    pmf = np.zeros(max_k, dtype=float)
    p0 = float(row.get("p0") or 0.0)
    pmf[0] = p0
    for k in range(1, max_k):
        pk_col = f"p_ge_{k}"
        pk1_col = f"p_ge_{k + 1}"
        a = float(row.get(pk_col) or 0.0)
        b = float(row.get(pk1_col) or 0.0) if pk1_col in row.index else 0.0
        pmf[k] = max(0.0, a - b)
    s = pmf.sum()
    if s > 0:
        pmf = pmf / s
    return pmf


def _pmf_nll(pmf: np.ndarray, outcome: int) -> float:
    o = max(0, min(int(outcome), len(pmf) - 1))
    return float(-np.log(max(pmf[o], 1e-12)))


def _pmf_rps(pmf: np.ndarray, outcome: int) -> float:
    K = len(pmf)
    cdf = np.cumsum(pmf)
    Y = np.zeros(K, dtype=float)
    Y[max(0, min(int(outcome), K - 1))] = 1.0
    Yc = np.cumsum(Y)
    return float(((cdf - Yc) ** 2).sum() / max(K - 1, 1))


def _pmf_mean(pmf: np.ndarray) -> float:
    K = len(pmf)
    return float((pmf * np.arange(K, dtype=float)).sum())


def _logloss(p: float, y: int) -> float:
    p = float(min(1.0 - 1e-9, max(1e-9, p)))
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _brier(p: float, y: int) -> float:
    return float((p - y) ** 2)


# ── Scoring ──────────────────────────────────────────────────────────────


def score_pmf_rows(canonical: pd.DataFrame, outcomes: pd.DataFrame
                    ) -> pd.DataFrame:
    """Per-row PMF scoring (one row per player×stat)."""
    if canonical.empty or outcomes.empty:
        return pd.DataFrame()
    df = canonical.merge(outcomes, on=["player_id", "stat"], how="left")
    rows = []
    for _, r in df.iterrows():
        if pd.isna(r.get("outcome")):
            continue
        pmf = _pmf_from_pge(r)
        outcome = int(r["outcome"])
        rec = dict(r.drop(labels=["outcome"], errors="ignore"))
        rec["actual_outcome"] = outcome
        rec["pmf_nll"] = _pmf_nll(pmf, outcome)
        rec["pmf_rps"] = _pmf_rps(pmf, outcome)
        rec["pmf_mean"] = _pmf_mean(pmf)
        rec["mean_error"] = float(rec["pmf_mean"] - outcome)
        rec["outcome_prob_assigned"] = (float(pmf[outcome])
                                         if 0 <= outcome < len(pmf) else 0.0)
        rows.append(rec)
    return pd.DataFrame(rows)


def score_market_rows(market_comp: pd.DataFrame, outcomes: pd.DataFrame
                       ) -> pd.DataFrame:
    """Per-line scoring (one row per player×stat×line×book)."""
    if market_comp.empty or outcomes.empty:
        return pd.DataFrame()
    df = market_comp.merge(outcomes, on=["player_id", "stat"], how="left")
    rows = []
    for _, r in df.iterrows():
        if pd.isna(r.get("outcome")) or pd.isna(r.get("line")):
            continue
        outcome = int(r["outcome"])
        line = float(r["line"])
        push = (line == int(line)) and (outcome == int(line))
        if push:
            over_real = under_real = None
            ll = brier = None
        else:
            y = 1 if outcome > line else 0
            p = (float(r["model_p_over"]) if pd.notna(r.get("model_p_over"))
                 else None)
            over_real = bool(outcome > line)
            under_real = bool(outcome < line)
            ll = _logloss(p, y) if p is not None else None
            brier = _brier(p, y) if p is not None else None
        rec = dict(r.drop(labels=["outcome"], errors="ignore"))
        rec["actual_outcome"] = outcome
        rec["over_realized"] = over_real
        rec["under_realized"] = under_real
        rec["is_push"] = push
        rec["model_logloss"] = ll
        rec["model_brier"] = brier
        rows.append(rec)
    return pd.DataFrame(rows)


def compute_clv(market_comp_morning: pd.DataFrame,
                  market_comp_close: pd.DataFrame) -> pd.DataFrame:
    """CLV per (player, stat, line, book): change in model and market
    no-vig probabilities from morning → close."""
    if market_comp_morning.empty or market_comp_close.empty:
        return pd.DataFrame()
    on = ["player_id", "stat", "line", "book"]
    morning = market_comp_morning[on + ["model_p_over",
                                          "market_no_vig_over_prob",
                                          "edge"]].copy()
    morning.columns = on + ["model_p_over_morning",
                              "market_no_vig_over_prob_morning",
                              "edge_morning"]
    close = market_comp_close[on + ["model_p_over",
                                      "market_no_vig_over_prob",
                                      "edge"]].copy()
    close.columns = on + ["model_p_over_close",
                            "market_no_vig_over_prob_close",
                            "edge_close"]
    df = morning.merge(close, on=on, how="inner")
    df["clv_close_minus_morning_p"] = (df["model_p_over_close"]
                                          - df["market_no_vig_over_prob_morning"])
    df["clv_book_close_minus_morning_p"] = (df["market_no_vig_over_prob_close"]
                                              - df["market_no_vig_over_prob_morning"])
    df["model_edge_movement"] = df["edge_close"] - df["edge_morning"]
    return df


# ── Aggregations ─────────────────────────────────────────────────────────


def _agg_calibration_by(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if df.empty or group_col not in df.columns:
        return pd.DataFrame()
    rows = []
    for k, sub in df.groupby(group_col, dropna=False):
        if sub.empty:
            continue
        rows.append({
            group_col: k, "n": int(len(sub)),
            "nll_mean": float(sub["pmf_nll"].mean()),
            "rps_mean": float(sub["pmf_rps"].mean()),
            "mean_error": float(sub["mean_error"].mean()),
            "abs_mean_error": float(sub["mean_error"].abs().mean()),
            "outcome_prob_assigned_mean": float(sub["outcome_prob_assigned"].mean()),
        })
    return pd.DataFrame(rows)


def _agg_clv_by(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if df.empty or group_col not in df.columns:
        return pd.DataFrame()
    rows = []
    for k, sub in df.groupby(group_col, dropna=False):
        if sub.empty:
            continue
        rows.append({
            group_col: k, "n": int(len(sub)),
            "clv_close_minus_morning_p_mean":
                float(sub["clv_close_minus_morning_p"].mean()),
            "clv_book_close_minus_morning_p_mean":
                float(sub["clv_book_close_minus_morning_p"].mean()),
            "model_edge_movement_mean":
                float(sub["model_edge_movement"].mean()),
        })
    return pd.DataFrame(rows)


# ── Writers ──────────────────────────────────────────────────────────────


def _write(df: pd.DataFrame, base: Path) -> None:
    base.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(base.with_suffix(".csv"), index=False)
    df.to_parquet(base.with_suffix(".parquet"), index=False)


def write_summary_md(scoring: pd.DataFrame, market_scoring: pd.DataFrame,
                      clv: pd.DataFrame, *, path: Path,
                      delivery_date: str) -> None:
    lines = [f"# After-game scoring — {delivery_date}", ""]
    if scoring.empty:
        lines += ["No scored PMF rows.", ""]
    else:
        lines += [
            "## Aggregate PMF metrics",
            "",
            f"- n = {len(scoring):,}",
            f"- NLL mean = {scoring['pmf_nll'].mean():.4f}",
            f"- RPS mean = {scoring['pmf_rps'].mean():.4f}",
            f"- mean error = {scoring['mean_error'].mean():+.4f}",
            f"- |mean error| = {scoring['mean_error'].abs().mean():.4f}",
            f"- outcome prob assigned mean = "
            f"{scoring['outcome_prob_assigned'].mean():.4f}",
            "",
            "## Per-stat",
            "",
            "| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for stat, sub in scoring.groupby("stat"):
            lines.append(
                f"| {stat} | {len(sub):,} | "
                f"{sub['pmf_nll'].mean():.4f} | "
                f"{sub['pmf_rps'].mean():.4f} | "
                f"{sub['mean_error'].mean():+.4f} | "
                f"{sub['mean_error'].abs().mean():.4f} | "
                f"{sub['outcome_prob_assigned'].mean():.4f} |")
        lines += ["", "## Per-role bucket", "",
                   "| role | n | NLL | RPS | mean_err | |mean_err| |",
                   "|---|---:|---:|---:|---:|---:|"]
        for role, sub in scoring.groupby("role_bucket"):
            lines.append(
                f"| {role} | {len(sub):,} | "
                f"{sub['pmf_nll'].mean():.4f} | "
                f"{sub['pmf_rps'].mean():.4f} | "
                f"{sub['mean_error'].mean():+.4f} | "
                f"{sub['mean_error'].abs().mean():.4f} |")
    if not market_scoring.empty:
        lines += ["", "## Market-line scoring (non-push rows)", ""]
        nonpush = market_scoring[market_scoring["is_push"] == False]
        if not nonpush.empty:
            lines += [
                f"- non-push rows = {len(nonpush):,}",
                f"- model logloss = {nonpush['model_logloss'].mean():.4f}",
                f"- model brier  = {nonpush['model_brier'].mean():.4f}",
                "",
            ]
    if not clv.empty:
        lines += [
            "## CLV (close − morning)",
            "",
            f"- joined rows = {len(clv):,}",
            f"- mean model close − morning market p = "
            f"{clv['clv_close_minus_morning_p'].mean():+.4f}",
            f"- mean book close − morning market p = "
            f"{clv['clv_book_close_minus_morning_p'].mean():+.4f}",
            f"- mean model edge movement = "
            f"{clv['model_edge_movement'].mean():+.4f}",
            "",
        ]
    lines += [
        "## Honest framing", "",
        "Scoring is on the canonical model-only PMF (no market anchoring). "
        "TOV PMFs are scored as emitted by the production Phase 8 calibrators "
        "with no Phase 10D / 10D.2 overlay applied. The structural TOV refit "
        "plan is in `docs/phase11_tov_structural_refit_plan.md`.",
        "",
    ]
    path.write_text("\n".join(lines))


# ── Main ──────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True)
    ap.add_argument("--outcomes", default=None,
                     help="parquet with player_id, stat, outcome (optional)")
    ap.add_argument("--close-snapshot", default=None,
                     help="path to a previously-written market_comparison.parquet "
                          "from the close_lock snapshot")
    ap.add_argument("--morning-snapshot", default=None,
                     help="path to a previously-written market_comparison.parquet "
                          "from the morning snapshot")
    args = ap.parse_args()

    delivery_date = args.date
    woo_dir = REPO_ROOT / "deliveries" / delivery_date / "wizard_of_odds"
    derek_dir = REPO_ROOT / "deliveries" / delivery_date / "pmf_model_review_package"
    after_game_dir = (REPO_ROOT / "deliveries" / delivery_date
                       / "after_game_scoring")
    if not woo_dir.exists():
        print(f"ERROR: WoO package missing for {delivery_date}: {woo_dir}")
        return 2
    after_game_dir.mkdir(parents=True, exist_ok=True)

    print(f"scoring delivery {delivery_date} …")
    canonical = pd.read_parquet(woo_dir / "full_pmfs_wide.parquet")
    market_comp = pd.read_parquet(woo_dir / "market_comparison.parquet")
    print(f"  canonical rows: {len(canonical):,}")
    print(f"  market_comparison rows: {len(market_comp):,}")

    outcomes = load_outcomes(args, delivery_date)
    print(f"  outcomes rows: {len(outcomes):,}")

    scoring = score_pmf_rows(canonical, outcomes)
    market_scoring = score_market_rows(market_comp, outcomes)
    print(f"  scored PMF rows: {len(scoring):,}")
    print(f"  scored market rows: {len(market_scoring):,}")

    # Optional CLV: needs morning + close snapshots.
    morning_path = (Path(args.morning_snapshot) if args.morning_snapshot
                     else woo_dir / "market_comparison.parquet")
    close_path = (Path(args.close_snapshot) if args.close_snapshot
                   else woo_dir / "market_comparison_close_lock.parquet")
    clv = pd.DataFrame()
    if morning_path.exists() and close_path.exists() and morning_path != close_path:
        try:
            mm = pd.read_parquet(morning_path)
            cm = pd.read_parquet(close_path)
            clv = compute_clv(mm, cm)
            print(f"  CLV rows: {len(clv):,}")
        except Exception as e:
            print(f"  CLV skipped: {e}")
    else:
        print("  CLV skipped (need both morning + close snapshots)")

    # Aggregations.
    cal_by_stat = _agg_calibration_by(scoring, "stat")
    cal_by_role = _agg_calibration_by(scoring, "role_bucket")
    clv_by_stat = _agg_clv_by(clv, "stat") if not clv.empty else pd.DataFrame()
    clv_by_book = _agg_clv_by(clv, "book") if not clv.empty else pd.DataFrame()

    # Writers — Phase 11C layout: every artifact also lives under
    # `after_game_scoring/`, and a status indicator is always written
    # so the deliveries index can detect `pending_outcomes`.
    after_game_status = ("scored" if not scoring.empty
                         else "pending_outcomes")
    if not scoring.empty:
        _write(scoring, derek_dir / "after_game_scoring")
        _write(scoring, woo_dir / "after_game_clv_and_scoring")
        _write(scoring, after_game_dir / "after_game_scoring")
        _write(scoring, after_game_dir / "after_game_clv_and_scoring")
    summary_path = derek_dir / "after_game_summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    write_summary_md(scoring, market_scoring, clv,
                      path=summary_path, delivery_date=delivery_date)
    write_summary_md(scoring, market_scoring, clv,
                      path=woo_dir / "after_game_clv_and_scoring.md",
                      delivery_date=delivery_date)
    # Mirror the same summary into the `after_game_scoring/` folder.
    write_summary_md(scoring, market_scoring, clv,
                      path=after_game_dir / "after_game_summary.md",
                      delivery_date=delivery_date)
    write_summary_md(scoring, market_scoring, clv,
                      path=after_game_dir / "after_game_clv_and_scoring.md",
                      delivery_date=delivery_date)

    for fname, df in (("calibration_by_stat.csv", cal_by_stat),
                       ("calibration_by_role_bucket.csv", cal_by_role),
                       ("clv_by_stat.csv", clv_by_stat),
                       ("clv_by_book.csv", clv_by_book)):
        if not df.empty:
            df.to_csv(woo_dir / fname, index=False)
            df.to_csv(after_game_dir / fname, index=False)

    # Status indicator — always written so the deliveries index does not
    # have to special-case the absence of any scoring file.
    status_payload = {
        "after_game_status": after_game_status,
        "delivery_date": delivery_date,
        "scored_at_utc": (datetime.now(timezone.utc)
                            .isoformat(timespec="seconds")
                            .replace("+00:00", "Z")),
        "n_scored_pmf_rows": int(len(scoring)),
        "n_scored_market_rows": int(len(market_scoring)),
        "n_clv_rows": int(len(clv)),
        "outcomes_source": (str(args.outcomes) if args.outcomes
                              else "data/player_game_stats.parquet"),
        "reason": (None if not scoring.empty else
                    "outcomes table has no rows for this delivery date; "
                    "rerun once box-score finals land"),
    }
    (after_game_dir / "after_game_status.json").write_text(
        json.dumps(status_payload, indent=2, default=str))

    # Append a short post-mortem to the manifest.
    manifest_path = woo_dir / "run_manifest.json"
    if manifest_path.exists():
        try:
            mf = json.loads(manifest_path.read_text())
        except Exception:
            mf = {}
        mf.setdefault("after_game", {})
        mf["after_game"].update({
            "status": after_game_status,
            "scored_at_utc": datetime.now(timezone.utc)
                              .isoformat(timespec="seconds")
                              .replace("+00:00", "Z"),
            "n_scored_pmf_rows": int(len(scoring)),
            "n_scored_market_rows": int(len(market_scoring)),
            "n_clv_rows": int(len(clv)),
            "nll_mean": (float(scoring["pmf_nll"].mean())
                         if not scoring.empty else None),
            "rps_mean": (float(scoring["pmf_rps"].mean())
                         if not scoring.empty else None),
            "abs_mean_error": (float(scoring["mean_error"].abs().mean())
                               if not scoring.empty else None),
        })
        manifest_path.write_text(json.dumps(mf, indent=2, default=str))

    print(f"  wrote {summary_path.relative_to(REPO_ROOT)}")
    print(f"  wrote {(woo_dir / 'after_game_clv_and_scoring.md').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
