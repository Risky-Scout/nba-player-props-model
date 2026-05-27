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
    "pts": "pts",
    "reb": "reb",
    "ast": "ast",
    "tov": "turnover",
    "fg3m": "fg3m",
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


def _pmf_from_json_like(x) -> np.ndarray | None:
    """Parse full PMF from pmf_json/pmf when available."""
    if x is None:
        return None
    try:
        if isinstance(x, str):
            d = json.loads(x)
        elif isinstance(x, dict):
            d = x
        else:
            return None
        if not d:
            return None
        max_k = max(int(k) for k in d.keys())
        pmf = np.zeros(max_k + 1, dtype=float)
        for k, v in d.items():
            pmf[int(k)] = float(v)
        pmf = np.clip(np.nan_to_num(pmf, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
        total = float(pmf.sum())
        return pmf / total if total > 0 else None
    except Exception:
        return None


def _pmf_from_row(row: pd.Series) -> np.ndarray:
    """Use full PMF when present; legacy p_ge ladder only as fallback."""
    for col in ("pmf_json", "pmf"):
        if col in row.index:
            pmf = _pmf_from_json_like(row.get(col))
            if pmf is not None:
                return pmf
    return _pmf_from_pge(row)

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
        pmf = _pmf_from_row(r)
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
    """Per-line scoring (one row per player×stat×line×book).

    Phase 13K: also records the market-side counterpart (market_logloss /
    market_brier from ``market_no_vig_over_prob``) so downstream model-vs-
    market deltas can be computed on the same aligned rows.
    """
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
            market_ll = market_brier = None
        else:
            y = 1 if outcome > line else 0
            p_model = (float(r["model_p_over"]) if pd.notna(r.get("model_p_over"))
                       else None)
            p_market = (float(r["market_no_vig_over_prob"])
                        if pd.notna(r.get("market_no_vig_over_prob"))
                        else None)
            over_real = bool(outcome > line)
            under_real = bool(outcome < line)
            ll = _logloss(p_model, y) if p_model is not None else None
            brier = _brier(p_model, y) if p_model is not None else None
            market_ll = _logloss(p_market, y) if p_market is not None else None
            market_brier = _brier(p_market, y) if p_market is not None else None
        rec = dict(r.drop(labels=["outcome"], errors="ignore"))
        rec["actual_outcome"] = outcome
        rec["over_realized"] = over_real
        rec["under_realized"] = under_real
        rec["is_push"] = push
        rec["model_logloss"] = ll
        rec["model_brier"] = brier
        # Phase 13K: market-side counterparts for paired comparison.
        rec["market_logloss"] = market_ll
        rec["market_brier"] = market_brier
        if ll is not None and market_ll is not None:
            rec["delta_logloss"] = ll - market_ll
        if brier is not None and market_brier is not None:
            rec["delta_brier"] = brier - market_brier
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


# ── Phase 13K helpers ─────────────────────────────────────────────────────

EXPECTED_TARGET_STATS = ("pts", "reb", "ast", "fg3m", "tov", "stl", "blk", "stocks", "pa", "pr", "pra")  # M8.1: mission canonical 11 (source: nba_props_model.targets.MISSION_REQUIRED_TARGETS_CANONICAL)

# Documented upstream blockers per stat. Used by Phase 13K
# expected_target_stats_coverage to record stats whose absence is a known,
# attributable upstream gap rather than a silent omission.
DOCUMENTED_STAT_BLOCKERS = {
    "tov": {
        "blocker_id": "phase11c_market_driven_prediction_layer",
        "blocker_summary": (
            "TOV PMFs are not emitted by the current prediction layer when "
            "no market line is offered, because predict.py is market-line-driven. "
            "Resolving this requires the Phase 11C player-stat-grid prediction "
            "refactor (emit one model-only PMF row per (player, eligible_stat) "
            "regardless of whether a market line is offered). Outcomes are "
            "available in data/player_game_stats.parquet under the 'turnover' "
            "column; the gap is upstream of after-game scoring."
        ),
        "outcome_source_column_present": "turnover",
        "remediation_phase": "phase11c",
    },
}

MIN_PAIRED_ROWS_FOR_MODEL_VS_MARKET = 20  # below this we report counts only
MIN_PAIRED_ROWS_FOR_BUCKET_BREAKDOWN = 30


def _aggregate_model_vs_market(market_scoring: pd.DataFrame) -> dict:
    """Compute model-vs-market realized deltas overall and by stat / role /
    edge / book on the rows that have BOTH a model and market probability
    AND a non-push outcome. Lower is better — negative delta favors model."""
    if market_scoring is None or market_scoring.empty:
        return {
            "rows_total": 0,
            "rows_paired": 0,
            "minimum_sample_passed": False,
            "overall": None,
            "by_stat": [],
            "by_role_bucket": [],
            "by_edge_bucket": [],
            "by_book": [],
            "note": "no market_scoring rows",
        }
    paired = market_scoring.dropna(subset=["model_logloss", "market_logloss"])
    paired = paired[~paired["is_push"].astype(bool, copy=False)] if "is_push" in paired.columns else paired
    out = {
        "rows_total": int(len(market_scoring)),
        "rows_paired": int(len(paired)),
        "minimum_sample_passed": bool(len(paired) >= MIN_PAIRED_ROWS_FOR_MODEL_VS_MARKET),
        "overall": None,
        "by_stat": [],
        "by_role_bucket": [],
        "by_edge_bucket": [],
        "by_book": [],
    }
    if paired.empty:
        return out

    def _block(sub: pd.DataFrame) -> dict:
        return {
            "n": int(len(sub)),
            "model_logloss": float(sub["model_logloss"].mean()),
            "market_logloss": float(sub["market_logloss"].mean()),
            "delta_logloss": float(
                (sub["model_logloss"] - sub["market_logloss"]).mean()
            ),
            "model_brier": float(sub["model_brier"].mean()),
            "market_brier": float(sub["market_brier"].mean()),
            "delta_brier": float(
                (sub["model_brier"] - sub["market_brier"]).mean()
            ),
        }

    out["overall"] = _block(paired)

    def _by(group_col: str) -> list:
        if group_col not in paired.columns:
            return []
        rows = []
        for k, sub in paired.groupby(group_col, dropna=False):
            if len(sub) < MIN_PAIRED_ROWS_FOR_BUCKET_BREAKDOWN:
                continue
            block = _block(sub)
            block[group_col] = (str(k) if not pd.isna(k) else "unknown")
            rows.append(block)
        return rows

    out["by_stat"] = _by("stat")
    out["by_role_bucket"] = _by("role_bucket")
    if "book" in paired.columns:
        out["by_book"] = _by("book")

    # Edge buckets — derived from model_p_over - market_no_vig_over_prob if available.
    if {"model_p_over", "market_no_vig_over_prob"}.issubset(paired.columns):
        try:
            edge = paired["model_p_over"] - paired["market_no_vig_over_prob"]
            buckets = pd.cut(
                edge,
                bins=[-1.0, -0.05, -0.02, 0.02, 0.05, 1.0],
                labels=["very_under", "under", "near_zero", "over", "very_over"],
            )
            paired = paired.assign(_edge_bucket=buckets.astype(str))
            for k, sub in paired.groupby("_edge_bucket"):
                if len(sub) < MIN_PAIRED_ROWS_FOR_BUCKET_BREAKDOWN:
                    continue
                block = _block(sub)
                block["edge_bucket"] = str(k)
                out["by_edge_bucket"].append(block)
        except Exception:
            pass

    return out


def _expected_target_stats_coverage(scoring: pd.DataFrame,
                                     canonical: pd.DataFrame,
                                     outcomes: pd.DataFrame) -> dict:
    """Record per-stat coverage status. PASS only if every expected stat is
    either actually scored or has a documented upstream blocker."""
    expected = list(EXPECTED_TARGET_STATS)
    scored_per_stat: dict[str, int] = {}
    if scoring is not None and not scoring.empty and "stat" in scoring.columns:
        for stat in expected:
            scored_per_stat[stat] = int((scoring["stat"] == stat).sum())
    canonical_per_stat: dict[str, int] = {}
    if canonical is not None and not canonical.empty and "stat" in canonical.columns:
        for stat in expected:
            canonical_per_stat[stat] = int((canonical["stat"] == stat).sum())
    outcomes_per_stat: dict[str, int] = {}
    if outcomes is not None and not outcomes.empty and "stat" in outcomes.columns:
        for stat in expected:
            outcomes_per_stat[stat] = int((outcomes["stat"] == stat).sum())

    scored_target_stats: list[str] = []
    missing_target_stats: list[str] = []
    documented_blocked_target_stats: list[dict] = []
    per_stat_records: list[dict] = []

    if outcomes is None or outcomes.empty:
        for stat in expected:
            per_stat_records.append({
                "stat": stat,
                "status": "pending_outcomes",
                "scored_rows": 0,
                "canonical_pmf_rows": canonical_per_stat.get(stat, 0),
                "outcome_rows": 0,
            })
        return {
            "expected_target_stats": expected,
            "scored_target_stats": [],
            "missing_target_stats": [],
            "documented_blocked_target_stats": [],
            "per_stat": per_stat_records,
            "all_accounted": True,
            "all_actually_scored": False,
            "pending_reason": "no_settled_outcomes",
            "source_columns_checked": ["pts", "reb", "ast", "fg3m", "turnover"],
            "tov_source_column": "turnover",
            "tov_rows_scored": 0,
        }
    for stat in expected:
        scored_n = scored_per_stat.get(stat, 0)
        canon_n = canonical_per_stat.get(stat, 0)
        out_n = outcomes_per_stat.get(stat, 0)
        if scored_n > 0:
            scored_target_stats.append(stat)
            per_stat_records.append({
                "stat": stat,
                "status": "scored",
                "scored_rows": scored_n,
                "canonical_pmf_rows": canon_n,
                "outcome_rows": out_n,
            })
        elif stat in DOCUMENTED_STAT_BLOCKERS:
            documented_blocked_target_stats.append({"stat": stat, **DOCUMENTED_STAT_BLOCKERS[stat]})
            per_stat_records.append({
                "stat": stat,
                "status": "documented_blocked",
                "scored_rows": 0,
                "canonical_pmf_rows": canon_n,
                "outcome_rows": out_n,
                **DOCUMENTED_STAT_BLOCKERS[stat],
            })
        else:
            missing_target_stats.append(stat)
            per_stat_records.append({
                "stat": stat,
                "status": "undocumented_missing",
                "scored_rows": 0,
                "canonical_pmf_rows": canon_n,
                "outcome_rows": out_n,
            })

    accounted = (len(scored_target_stats) + len(documented_blocked_target_stats)) == len(expected)
    return {
        "expected_target_stats": expected,
        "scored_target_stats": scored_target_stats,
        "missing_target_stats": missing_target_stats,
        "documented_blocked_target_stats": documented_blocked_target_stats,
        "per_stat": per_stat_records,
        "all_accounted": bool(accounted),
        "all_actually_scored": bool(len(scored_target_stats) == len(expected)),
        "source_columns_checked": ["pts", "reb", "ast", "fg3m", "turnover"],
        "tov_source_column": "turnover",
        "tov_rows_scored": scored_per_stat.get("tov", 0),
    }


def _read_champion_pointer() -> dict:
    pointer = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    if not pointer.exists():
        return {}
    try:
        return json.loads(pointer.read_text())
    except Exception:
        return {}


def _sha256_file_short(path: Path) -> str | None:
    if not path.exists():
        return None
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _write_pmf_review_run_manifest(*, delivery_date: str, derek_dir: Path,
                                     after_game_status: str,
                                     scoring: pd.DataFrame,
                                     coverage: dict) -> Path:
    """Phase 13K Part B: write pmf_model_review_package/run_manifest.json."""
    derek_dir.mkdir(parents=True, exist_ok=True)
    pointer = _read_champion_pointer()
    pointer_path = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    package_files = sorted(p.name for p in derek_dir.iterdir() if p.is_file())
    file_hashes: dict[str, str] = {}
    for name in package_files:
        if name.endswith((".csv", ".parquet", ".html", ".md", ".json")):
            sha = _sha256_file_short(derek_dir / name)
            if sha:
                file_hashes[name] = sha

    row_counts = {}
    for fname in ("after_game_scoring.parquet", "04_PROP_SUMMARY.parquet",
                   "05_FULL_PMF_WIDE.parquet", "06_OUTCOME_LEVEL_PROBABILITIES.parquet"):
        p = derek_dir / fname
        if p.exists():
            try:
                row_counts[fname] = int(len(pd.read_parquet(p, columns=[])))
            except Exception:
                pass

    now = _utc_now()
    manifest = {
        "schema_version": "1.0",
        "delivery_date": delivery_date,
        "package_type": "pmf_model_review_package",
        "model_source": "champion_pointer",
        "champion_model_id": pointer.get("champion_model_id") or pointer.get("model_version"),
        "champion_artifact_dir": pointer.get("champion_artifact_dir") or pointer.get("model_dir"),
        "trained_through_date": pointer.get("trained_through_date"),
        "calibrated_through_date": pointer.get("calibrated_through_date"),
        "training_run_id": pointer.get("training_run_id"),
        "calibration_run_id": pointer.get("calibration_run_id"),
        "validation_run_id": pointer.get("validation_run_id"),
        "promotion_decision_id": pointer.get("promotion_decision_id"),
        "champion_pointer_path": str(pointer_path.relative_to(REPO_ROOT)),
        "champion_pointer_hash": _sha256_file_short(pointer_path),
        "after_game_status": after_game_status,
        "scoring_status": ("scored" if scoring is not None and not scoring.empty
                            else "pending_outcomes"),
        "expected_target_stats": coverage["expected_target_stats"],
        "scored_target_stats": coverage["scored_target_stats"],
        "missing_target_stats": coverage["missing_target_stats"],
        "documented_blocked_target_stats": coverage["documented_blocked_target_stats"],
        "row_counts": row_counts,
        "file_hashes": file_hashes,
        "package_files": package_files,
        "generated_at_utc": now,
        "metadata_stamped_at_utc": now,
        "no_challenger_artifacts_used": True,
        "phase10d_overlays_in_use": False,
    }
    out = derek_dir / "run_manifest.json"
    tmp = out.with_suffix(out.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, default=str)
    tmp.replace(out)
    return out


def _write_expected_target_stats_coverage(*, after_game_dir: Path,
                                            coverage: dict,
                                            delivery_date: str) -> tuple[Path, Path]:
    after_game_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "delivery_date": delivery_date,
        "generated_at_utc": _utc_now(),
        **coverage,
        "blockers": [
            {
                "stat": rec["stat"],
                "blocker_id": rec.get("blocker_id"),
                "blocker_summary": rec.get("blocker_summary"),
                "remediation_phase": rec.get("remediation_phase"),
            }
            for rec in coverage["documented_blocked_target_stats"]
        ],
    }
    json_path = after_game_dir / "expected_target_stats_coverage.json"
    md_path = after_game_dir / "expected_target_stats_coverage.md"
    with json_path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True, default=str)

    md = [
        f"# Expected Target Stats Coverage — {delivery_date}",
        "",
        f"- expected_target_stats: {coverage['expected_target_stats']}",
        f"- scored_target_stats: {coverage['scored_target_stats']}",
        f"- documented_blocked_target_stats: "
        f"{[s['stat'] for s in coverage['documented_blocked_target_stats']]}",
        f"- missing_target_stats (undocumented): {coverage['missing_target_stats']}",
        f"- all_accounted: **{coverage['all_accounted']}**",
        f"- all_actually_scored: **{coverage['all_actually_scored']}**",
        f"- tov_source_column: `{coverage['tov_source_column']}`",
        f"- tov_rows_scored: {coverage['tov_rows_scored']}",
        "",
        "## Per stat",
        "",
        "| Stat | Status | Scored rows | Canonical PMF rows | Outcome rows | Blocker |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for rec in coverage["per_stat"]:
        blocker = rec.get("blocker_id") or ""
        md.append(
            f"| {rec['stat']} | {rec['status']} | {rec['scored_rows']} | "
            f"{rec['canonical_pmf_rows']} | {rec['outcome_rows']} | {blocker} |"
        )
    if coverage["documented_blocked_target_stats"]:
        md += ["", "## Documented blockers", ""]
        for rec in coverage["documented_blocked_target_stats"]:
            md += [
                f"### {rec['stat']} — `{rec['blocker_id']}`",
                "",
                rec["blocker_summary"],
                "",
                f"Outcome source column present: `{rec.get('outcome_source_column_present')}`. "
                f"Remediation phase: `{rec.get('remediation_phase')}`.",
                "",
            ]
    md_path.write_text("\n".join(md) + "\n")
    return json_path, md_path


def _write_model_vs_market_artifacts(*, after_game_dir: Path,
                                       agg: dict,
                                       market_scoring: pd.DataFrame,
                                       delivery_date: str) -> dict:
    """Write the model-vs-market summary JSON / CSV / MD."""
    after_game_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "delivery_date": delivery_date,
        "generated_at_utc": _utc_now(),
        "minimum_paired_rows_threshold": MIN_PAIRED_ROWS_FOR_MODEL_VS_MARKET,
        "minimum_bucket_rows_threshold": MIN_PAIRED_ROWS_FOR_BUCKET_BREAKDOWN,
        **agg,
    }
    json_path = after_game_dir / "model_vs_market_scoring.json"
    csv_path = after_game_dir / "model_vs_market_scoring.csv"
    md_path = after_game_dir / "model_vs_market_scoring.md"
    with json_path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True, default=str)

    # CSV: per-row paired data so analysts can reproduce.
    if market_scoring is not None and not market_scoring.empty:
        cols = [c for c in (
            "stat", "role_bucket", "book", "line", "player_id",
            "model_logloss", "market_logloss", "delta_logloss",
            "model_brier", "market_brier", "delta_brier",
            "model_p_over", "market_no_vig_over_prob",
            "actual_outcome", "is_push",
        ) if c in market_scoring.columns]
        market_scoring[cols].to_csv(csv_path, index=False)

    md = [f"# Model vs Market Realized Scoring — {delivery_date}", ""]
    overall = agg.get("overall")
    if overall:
        md += [
            f"- rows_paired: {agg['rows_paired']} (rows_total={agg['rows_total']})",
            f"- model_logloss: **{overall['model_logloss']:.4f}**",
            f"- market_logloss: **{overall['market_logloss']:.4f}**",
            f"- delta_logloss (model - market, lower is better): **{overall['delta_logloss']:+.4f}**",
            f"- model_brier: **{overall['model_brier']:.4f}**",
            f"- market_brier: **{overall['market_brier']:.4f}**",
            f"- delta_brier (model - market, lower is better): **{overall['delta_brier']:+.4f}**",
            "",
        ]
    else:
        md += [
            f"- rows_paired: {agg.get('rows_paired')} (rows_total={agg.get('rows_total')})",
            "- Overall: no paired model+market rows on this slate.",
            "",
        ]
    for label, key in (("By stat", "by_stat"), ("By role bucket", "by_role_bucket"),
                       ("By edge bucket", "by_edge_bucket"), ("By book", "by_book")):
        rows = agg.get(key) or []
        if not rows:
            continue
        md += [f"## {label}", "", "| Group | n | model_LL | market_LL | Δ_LL | model_Brier | market_Brier | Δ_Brier |",
               "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        gcol = key.replace("by_", "")
        for rec in rows:
            md.append(
                f"| {rec.get(gcol, '')} | {rec['n']} | {rec['model_logloss']:.4f} | "
                f"{rec['market_logloss']:.4f} | {rec['delta_logloss']:+.4f} | "
                f"{rec['model_brier']:.4f} | {rec['market_brier']:.4f} | "
                f"{rec['delta_brier']:+.4f} |"
            )
        md.append("")
    md_path.write_text("\n".join(md) + "\n")
    return {
        "json": json_path,
        "csv": csv_path,
        "md": md_path,
        "rows_paired": agg.get("rows_paired", 0),
        "minimum_sample_passed": agg.get("minimum_sample_passed", False),
    }


def _write_model_performance_md(*, derek_dir: Path,
                                  after_game_status: str,
                                  scoring: pd.DataFrame,
                                  market_scoring: pd.DataFrame,
                                  agg_mvm: dict,
                                  coverage: dict,
                                  clv: pd.DataFrame,
                                  delivery_date: str) -> Path:
    """Phase 13K Part C: rewrite MODEL_PERFORMANCE_AND_CALIBRATION.md."""
    derek_dir.mkdir(parents=True, exist_ok=True)
    pointer = _read_champion_pointer()
    md = [
        f"# Model Performance and Calibration — {delivery_date}",
        "",
        f"- champion_model_id: `{pointer.get('champion_model_id') or pointer.get('model_version')}`",
        f"- trained_through_date: `{pointer.get('trained_through_date')}`",
        f"- calibrated_through_date: `{pointer.get('calibrated_through_date')}`",
        f"- after_game_status: **{after_game_status}**",
        f"- expected_target_stats: {coverage['expected_target_stats']}",
        f"- scored_target_stats: {coverage['scored_target_stats']}",
        f"- documented_blocked_target_stats: "
        f"{[s['stat'] for s in coverage['documented_blocked_target_stats']]}",
        f"- missing_target_stats (undocumented): {coverage['missing_target_stats']}",
        "",
        "PMFs are model-only and are NOT market-anchored. Comparisons against",
        "market lines below use realized outcomes only.",
        "",
    ]
    if scoring is None or scoring.empty:
        md += [
            "## Status",
            "",
            f"`{after_game_status}` — no scored PMF rows for this delivery yet.",
            "Re-run after-game scoring once box-score finals land.",
            "",
        ]
    else:
        md += [
            "## Aggregate PMF metrics",
            "",
            f"- rows scored: {len(scoring):,}",
            f"- mean NLL: {float(scoring['pmf_nll'].mean()):.4f}",
            f"- mean RPS: {float(scoring['pmf_rps'].mean()):.4f}",
            f"- mean abs error: {float(scoring['mean_error'].abs().mean()):.4f}",
            f"- mean outcome_prob_assigned: "
            f"{float(scoring['outcome_prob_assigned'].mean()):.4f}",
            "",
            "## Per stat",
            "",
            "| Stat | n | NLL | RPS | abs_mean_error |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for stat, sub in scoring.groupby("stat"):
            md.append(
                f"| {stat} | {len(sub)} | {float(sub['pmf_nll'].mean()):.4f} | "
                f"{float(sub['pmf_rps'].mean()):.4f} | "
                f"{float(sub['mean_error'].abs().mean()):.4f} |"
            )
        md.append("")
        if "role_bucket" in scoring.columns:
            md += [
                "## Per role bucket", "",
                "| Role | n | NLL | RPS | abs_mean_error |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
            for role, sub in scoring.groupby("role_bucket", dropna=False):
                md.append(
                    f"| {role} | {len(sub)} | {float(sub['pmf_nll'].mean()):.4f} | "
                    f"{float(sub['pmf_rps'].mean()):.4f} | "
                    f"{float(sub['mean_error'].abs().mean()):.4f} |"
                )
            md.append("")

    md += ["## Market-line scoring (model only)", ""]
    if market_scoring is None or market_scoring.empty:
        md.append("- No market-line rows were scored for this delivery.")
    else:
        valid = market_scoring.dropna(subset=["model_logloss"])
        valid = valid[~valid["is_push"].astype(bool, copy=False)] if "is_push" in valid.columns else valid
        md += [
            f"- rows scored: {len(valid):,}",
            f"- mean model logloss at market lines: "
            f"{float(valid['model_logloss'].mean()):.4f}"
            if not valid.empty else "- no non-push market rows",
            f"- mean model Brier at market lines: "
            f"{float(valid['model_brier'].mean()):.4f}"
            if not valid.empty else "",
        ]
    md.append("")

    md += ["## Model vs market", ""]
    overall = agg_mvm.get("overall")
    if overall:
        md += [
            f"- rows_paired: {agg_mvm['rows_paired']} "
            f"(threshold for hard claim: {MIN_PAIRED_ROWS_FOR_MODEL_VS_MARKET})",
            f"- delta_logloss = model - market = "
            f"**{overall['delta_logloss']:+.4f}** (negative favors model)",
            f"- delta_brier   = model - market = "
            f"**{overall['delta_brier']:+.4f}** (negative favors model)",
        ]
    else:
        md += [
            f"- rows_paired: {agg_mvm.get('rows_paired', 0)} — "
            "no overall delta computed for this slate.",
        ]
    md.append("")

    if clv is not None and not clv.empty:
        md += [
            "## CLV summary",
            "",
            f"- CLV rows: {len(clv):,}",
            f"- mean model edge movement: "
            f"{float(clv['model_edge_movement'].mean()):.4f}",
            "",
        ]

    if coverage["documented_blocked_target_stats"]:
        md += ["## Stats blocked by upstream phases", ""]
        for rec in coverage["documented_blocked_target_stats"]:
            md += [
                f"### {rec['stat']} — `{rec['blocker_id']}` ({rec.get('remediation_phase', 'unknown')})",
                "",
                rec["blocker_summary"],
                "",
            ]

    out = derek_dir / "MODEL_PERFORMANCE_AND_CALIBRATION.md"
    out.write_text("\n".join(md) + "\n")
    return out


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
    _woo_pmf = woo_dir / "full_pmfs_wide.parquet"
    _canonical_fallback = REPO_ROOT / "deliveries" / delivery_date / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    if not _woo_pmf.exists() and _canonical_fallback.exists():
        print(f"  full_pmfs_wide.parquet missing; falling back to canonical_source for scoring")
        canonical = pd.read_parquet(_canonical_fallback)
    else:
        canonical = pd.read_parquet(_woo_pmf)
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
    # Build scoring+CLV merge so the _clv_and_scoring outputs actually
    # carry CLV columns (left-join on prop key; NaN where line not stable).
    if not clv.empty:
        _clv_cols = ["player_id", "stat", "line", "book",
                     "clv_close_minus_morning_p",
                     "clv_book_close_minus_morning_p",
                     "model_edge_movement",
                     "model_p_over_close", "model_p_over_morning",
                     "market_no_vig_over_prob_close",
                     "market_no_vig_over_prob_morning",
                     "edge_close", "edge_morning"]
        _clv_subset = clv[[c for c in _clv_cols if c in clv.columns]].copy()
        # Coerce `line` to numeric on both sides (scoring sometimes stores it
        # as object/string from upstream join; clv has it as float64).
        _clv_subset["line"] = pd.to_numeric(_clv_subset["line"], errors="coerce")
        _scoring_for_merge = scoring.copy()
        _scoring_for_merge["line"] = pd.to_numeric(
            _scoring_for_merge["line"], errors="coerce")
        scoring_with_clv = _scoring_for_merge.merge(
            _clv_subset,
            on=["player_id", "stat", "line", "book"],
            how="left")
    else:
        scoring_with_clv = scoring

    after_game_status = ("scored" if not scoring.empty
                         else "pending_outcomes")
    if not scoring.empty:
        _write(scoring, derek_dir / "after_game_scoring")
        _write(scoring_with_clv, woo_dir / "after_game_clv_and_scoring")
        _write(scoring, after_game_dir / "after_game_scoring")
        _write(scoring_with_clv, after_game_dir / "after_game_clv_and_scoring")
    # CLV lives at (player_id, stat, line, book) — different granularity
    # than PMF scoring at (player_id, stat). Write CLV as its own artifact
    # so the actual CLV rows are visible. The _clv_and_scoring left-join
    # above produces NaN CLV columns by design (scoring lacks line/book).
    if not clv.empty:
        _write(clv, woo_dir / "after_game_clv")
        _write(clv, after_game_dir / "after_game_clv")
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

    # ── Phase 13K artifacts ────────────────────────────────────────────────
    coverage = _expected_target_stats_coverage(scoring, canonical, outcomes)
    _write_expected_target_stats_coverage(
        after_game_dir=after_game_dir, coverage=coverage,
        delivery_date=delivery_date,
    )
    agg_mvm = _aggregate_model_vs_market(market_scoring)
    mvm_paths = _write_model_vs_market_artifacts(
        after_game_dir=after_game_dir, agg=agg_mvm,
        market_scoring=market_scoring, delivery_date=delivery_date,
    )
    _write_pmf_review_run_manifest(
        delivery_date=delivery_date, derek_dir=derek_dir,
        after_game_status=after_game_status, scoring=scoring,
        coverage=coverage,
    )
    _write_model_performance_md(
        derek_dir=derek_dir, after_game_status=after_game_status,
        scoring=scoring, market_scoring=market_scoring, agg_mvm=agg_mvm,
        coverage=coverage, clv=clv, delivery_date=delivery_date,
    )

    # ── Phase 13K PASS / FAIL lines ────────────────────────────────────────
    # Expected-target-stats coverage: PASS only if every expected stat is
    # either actually scored or has a documented upstream blocker.
    if coverage["all_actually_scored"]:
        print("EXPECTED_TARGET_STATS_SCORED_PASS")
    elif coverage["all_accounted"]:
        # Use the Option-B preferred pass line — clearer semantics.
        print("EXPECTED_TARGET_STATS_COVERAGE_ACCOUNTED_PASS")
        print(
            f"  scored_target_stats={coverage['scored_target_stats']} "
            f"documented_blocked_target_stats="
            f"{[s['stat'] for s in coverage['documented_blocked_target_stats']]}"
        )
    else:
        print("EXPECTED_TARGET_STATS_SCORED_FAILED", flush=True)
        print(
            f"  missing_target_stats (undocumented)={coverage['missing_target_stats']}"
        )
        print(
            f"  scored_target_stats={coverage['scored_target_stats']} "
            f"documented_blocked={[s['stat'] for s in coverage['documented_blocked_target_stats']]}"
        )
        return 3  # hard fail per Phase 13K Part D

    # Model-vs-market scoring: PASS when paired sample exists; FAILED only if
    # market_scoring rows exist but pairing or computation could not happen.
    if agg_mvm.get("rows_total", 0) == 0:
        # No market rows at all on this slate — neutral skip, no claim made.
        print("MODEL_VS_MARKET_SCORING_PASS")
        print("  rows_total=0 — no market-line rows to score on this slate")
    elif agg_mvm.get("overall") is None:
        print("MODEL_VS_MARKET_SCORING_FAILED")
        print(
            f"  rows_total={agg_mvm.get('rows_total')} but no paired model+market "
            f"rows could be computed (likely all rows were pushes or missing probabilities)"
        )
        return 4
    else:
        print("MODEL_VS_MARKET_SCORING_PASS")
        ov = agg_mvm["overall"]
        print(
            f"  rows_paired={agg_mvm['rows_paired']}  "
            f"delta_logloss={ov['delta_logloss']:+.4f}  "
            f"delta_brier={ov['delta_brier']:+.4f}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
