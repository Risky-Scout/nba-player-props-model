"""Atom-level PMF calibration + side-split market evaluation.

Read-only diagnostic against a single Phase 8 fold OOF parquet. Reports:

  1. Per-stat atom-level reliability: for every integer atom k, the mean
     predicted P(X=k) across the fold vs the empirical frequency
     1[outcome==k], plus atom_ece_pred_mass (primary), atom_ece_empirical,
     atom_brier (per-row multinomial), and atom_logloss.
  2. Side-split market comparison on matched half-point lines. The fold
     parquet carries no `line` column, so the line is supplied by the
     market join on (player_norm, game_date == snapshot_date, stat);
     integer market lines are dropped before the join, and any
     (player_id, game_id, stat) group that still has more than one
     surviving market line after the join is excluded rather than
     scored. Primary metric is the edge-selection split (rows bucketed
     by whichever side has the larger model - market edge); a secondary
     unconditional OVER/UNDER table is kept as a sanity check.
  3. Per (stat, line) line-neighborhood atom table.

Invocation:

    python scripts/diagnostics/exact_mass_and_side_split.py \\
        --fold-oof artifacts/fold_1.parquet \\
        --stats-df data/player_game_stats.parquet \\
        --closing-lines-dir artifacts/graded \\
        --output-dir artifacts/diagnostics/fold_1
"""
from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from datetime import datetime
from math import ceil
from pathlib import Path

import numpy as np
import pandas as pd


LOGLOSS_EPS = 1e-6
DEFAULT_STATS = ("pts", "reb", "ast", "tov", "fg3m")


# ── IO helpers ─────────────────────────────────────────────────────────────


def _die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _load_fold_oof(path: Path) -> pd.DataFrame:
    if not path.exists():
        _die(f"--fold-oof not found: {path}")
    df = pd.read_parquet(path)
    required = {"stat", "player_id", "game_id", "game_date", "outcome", "pmf",
                "fold_start", "fold_end"}
    missing = required - set(df.columns)
    if missing:
        _die(f"fold_oof missing columns: {sorted(missing)}")
    df = df.copy()
    df["stat"] = df["stat"].astype(str).str.lower()
    df["game_date"] = df["game_date"].astype(str).str.slice(0, 10)
    df["outcome"] = df["outcome"].astype(int)
    df["player_id"] = df["player_id"].astype(int)
    return df


def _validate_pmfs(df: pd.DataFrame) -> None:
    bad_sum = bad_neg = bad_mono = 0
    out_of_range = 0
    for row in df.itertuples(index=False):
        pmf = np.asarray(row.pmf, dtype=np.float64)
        if pmf.ndim != 1 or pmf.size == 0:
            bad_sum += 1
            continue
        s = float(pmf.sum())
        if not np.isfinite(s) or abs(s - 1.0) > 1e-6:
            bad_sum += 1
        if (pmf < 0).any():
            bad_neg += 1
        cdf = np.cumsum(pmf)
        if (np.diff(cdf) < -1e-9).any():
            bad_mono += 1
        if not (0 <= int(row.outcome) < pmf.size):
            out_of_range += 1
    n = len(df)
    if bad_sum:
        _die(f"{bad_sum}/{n} PMFs do not sum to 1.0 within 1e-6")
    if bad_neg:
        _die(f"{bad_neg}/{n} PMFs contain negative entries")
    if bad_mono:
        _die(f"{bad_mono}/{n} PMFs have non-monotone CDFs")
    in_range_frac = 1.0 - out_of_range / max(n, 1)
    if in_range_frac < 0.95:
        _die(
            f"only {100*in_range_frac:.2f}% of rows have outcome in "
            f"[0, len(pmf)-1] ({out_of_range} out of {n})"
        )
    if in_range_frac < 0.99:
        print(
            f"WARN: {100*(1-in_range_frac):.2f}% of rows have outcome outside "
            f"PMF support; these rows contribute 0 to the realized_onehot."
        )


def _load_player_name_map(stats_df_path: Path) -> dict[int, str]:
    if not stats_df_path.exists():
        _die(f"--stats-df not found: {stats_df_path}")
    sdf = pd.read_parquet(stats_df_path, columns=["player_id", "player_name"])
    sdf = sdf.dropna(subset=["player_id", "player_name"]).drop_duplicates("player_id")
    return {
        int(r.player_id): str(r.player_name).strip().lower()
        for r in sdf.itertuples(index=False)
    }


def _load_closing_lines(
    closing_dir: Path, window_lo: str, window_hi: str,
) -> pd.DataFrame:
    if not closing_dir.exists():
        _die(f"--closing-lines-dir not found: {closing_dir}")
    paths = sorted(glob.glob(str(closing_dir / "closing_lines_*.json")))
    market_cols = [
        "snapshot_date", "player_norm", "stat", "line",
        "fair_over_prob", "fair_under_prob",
    ]
    rows: list[dict] = []
    for p in paths:
        snap_date = Path(p).stem.replace("closing_lines_", "")
        if snap_date < window_lo or snap_date > window_hi:
            continue
        try:
            with open(p) as f:
                data = json.load(f)
        except Exception as e:
            print(f"WARN: skipping unreadable closing file {p}: {e}")
            continue
        if not isinstance(data, dict):
            continue
        for v in data.values():
            if not isinstance(v, dict):
                continue
            if "line" not in v or "stat" not in v:
                continue
            try:
                line = float(v["line"])
            except (TypeError, ValueError):
                continue
            rows.append({
                "snapshot_date": snap_date,
                "player_norm": str(v.get("player_norm", "")).strip().lower(),
                "stat": str(v.get("stat", "")).strip().lower(),
                "line": line,
                "fair_over_prob": (float(v["fair_over_prob"])
                                   if v.get("fair_over_prob") is not None else np.nan),
                "fair_under_prob": (float(v["fair_under_prob"])
                                    if v.get("fair_under_prob") is not None else np.nan),
            })
    if not rows:
        # Return a typed empty frame so downstream code that does
        # market["stat"] or boolean-mask filters still sees the expected
        # columns (pd.DataFrame([]) would yield a zero-column frame).
        return pd.DataFrame({c: pd.Series(dtype="object") for c in market_cols})
    return pd.DataFrame(rows, columns=market_cols)


# ── metrics ────────────────────────────────────────────────────────────────


def _atom_metrics_for_stat(fold_stat: pd.DataFrame, min_atom_count: int) -> dict:
    pmfs = [np.asarray(r, dtype=np.float64) for r in fold_stat["pmf"].tolist()]
    max_k = max(p.size for p in pmfs)
    n = len(pmfs)
    P = np.zeros((n, max_k), dtype=np.float64)
    for i, p in enumerate(pmfs):
        P[i, : p.size] = p
    outcomes = fold_stat["outcome"].to_numpy().astype(int)
    realized = np.zeros((n, max_k), dtype=np.float64)
    valid_mask = (outcomes >= 0) & (outcomes < max_k)
    rows_idx = np.arange(n)[valid_mask]
    cols_idx = outcomes[valid_mask]
    realized[rows_idx, cols_idx] = 1.0

    predicted_mean = P.mean(axis=0)
    empirical_freq = realized.mean(axis=0)
    atom_counts = realized.sum(axis=0).astype(int)
    abs_dev = np.abs(predicted_mean - empirical_freq)

    # Two ECE variants per the spec.
    #   atom_ece_pred_mass weights by the model's mass at each atom so
    #     atoms the model thinks matter most dominate the score.
    #   atom_ece_empirical weights by realized frequency (= the older
    #     empirical-count-weighted form) for comparison.
    atom_ece_pred_mass = float(np.sum(predicted_mean * abs_dev))
    atom_ece_empirical = float(np.sum(empirical_freq * abs_dev))

    # Standard multinomial per-row Brier, averaged over rows.
    atom_brier = float(np.mean(np.sum((P - realized) ** 2, axis=1)))

    P_clip = np.clip(P, LOGLOSS_EPS, 1 - LOGLOSS_EPS)
    if len(rows_idx) > 0:
        realized_logprob = np.log(P_clip[rows_idx, cols_idx])
        atom_logloss = float(-np.mean(realized_logprob))
    else:
        atom_logloss = float("nan")

    # ── Distributional summary (reuses P, realized, outcomes) ─────────
    # Honest distribution-level sanity checks before any correction
    # layer: predicted vs realized mean, P(X=0), P(X<=1). No tilt, no
    # reweighting — just read the PMF as is.
    pred_mean = float(np.sum(P * np.arange(P.shape[1])[None, :], axis=1).mean())
    realized_mean = float(fold_stat["outcome"].mean())
    pred_p0 = float(P[:, 0].mean())
    realized_p0 = float((fold_stat["outcome"].to_numpy() == 0).mean())
    if P.shape[1] >= 2:
        pred_p_le1 = float((P[:, 0] + P[:, 1]).mean())
    else:
        pred_p_le1 = float(P[:, 0].mean())
    realized_p_le1 = float((fold_stat["outcome"].to_numpy() <= 1).mean())
    distributional_summary = {
        "n_rows": int(n),
        "pred_mean": pred_mean,
        "realized_mean": realized_mean,
        "pred_p0": pred_p0,
        "realized_p0": realized_p0,
        "pred_p_le1": pred_p_le1,
        "realized_p_le1": realized_p_le1,
    }

    reliability = [
        {
            "atom_value": int(k),
            "predicted_mean_prob": float(predicted_mean[k]),
            "empirical_freq": float(empirical_freq[k]),
            "count": int(atom_counts[k]),
            "abs_dev": float(abs_dev[k]),
        }
        for k in range(max_k)
        if int(atom_counts[k]) >= min_atom_count
    ]
    reliability.sort(key=lambda r: r["abs_dev"], reverse=True)

    return {
        "n_rows": int(n),
        "n_atoms": int(max_k),
        "atom_ece_pred_mass": atom_ece_pred_mass,
        "atom_ece_empirical": atom_ece_empirical,
        "atom_brier": atom_brier,
        "atom_logloss": atom_logloss,
        "distributional_summary": distributional_summary,
        "reliability": reliability,
    }


def _brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2)) if len(p) else float("nan")


def _logloss(p: np.ndarray, y: np.ndarray) -> float:
    if not len(p):
        return float("nan")
    pc = np.clip(p, LOGLOSS_EPS, 1 - LOGLOSS_EPS)
    return float(-np.mean(y * np.log(pc) + (1 - y) * np.log(1 - pc)))


def _pct_improvement(model_v: float, market_v: float) -> float:
    if not (np.isfinite(model_v) and np.isfinite(market_v)) or market_v == 0:
        return float("nan")
    return 100.0 * (market_v - model_v) / abs(market_v)


def _side_metrics_unconditional(matched: pd.DataFrame) -> dict:
    """Sanity-check block: Brier / log-loss vs de-vigged market, computed
    for OVER and UNDER over ALL matched rows (not bucketed by chosen side).
    """
    if matched.empty:
        nan = float("nan")
        return {"n_matched": 0} | {
            k: nan for k in (
                "brier_model_over", "brier_market_over",
                "logloss_model_over", "logloss_market_over",
                "brier_model_under", "brier_market_under",
                "logloss_model_under", "logloss_market_under",
                "over_brier_improvement_pct", "under_brier_improvement_pct",
                "over_logloss_improvement_pct", "under_logloss_improvement_pct",
                "asymmetry_gap_pct",
            )
        }
    y_over = matched["realized_over"].to_numpy().astype(int)
    y_under = matched["realized_under"].to_numpy().astype(int)
    m_over = matched["model_p_over"].to_numpy()
    k_over = matched["fair_over_prob"].to_numpy()
    m_under = matched["model_p_under"].to_numpy()
    k_under = matched["fair_under_prob"].to_numpy()
    out = {
        "n_matched": int(len(matched)),
        "brier_model_over": _brier(m_over, y_over),
        "brier_market_over": _brier(k_over, y_over),
        "logloss_model_over": _logloss(m_over, y_over),
        "logloss_market_over": _logloss(k_over, y_over),
        "brier_model_under": _brier(m_under, y_under),
        "brier_market_under": _brier(k_under, y_under),
        "logloss_model_under": _logloss(m_under, y_under),
        "logloss_market_under": _logloss(k_under, y_under),
    }
    out["over_brier_improvement_pct"] = _pct_improvement(
        out["brier_model_over"], out["brier_market_over"]
    )
    out["under_brier_improvement_pct"] = _pct_improvement(
        out["brier_model_under"], out["brier_market_under"]
    )
    out["over_logloss_improvement_pct"] = _pct_improvement(
        out["logloss_model_over"], out["logloss_market_over"]
    )
    out["under_logloss_improvement_pct"] = _pct_improvement(
        out["logloss_model_under"], out["logloss_market_under"]
    )
    out["asymmetry_gap_pct"] = (
        float(abs(out["over_brier_improvement_pct"] - out["under_brier_improvement_pct"]))
        if np.isfinite(out["over_brier_improvement_pct"])
           and np.isfinite(out["under_brier_improvement_pct"])
        else float("nan")
    )
    return out


def _matched_distributional_summary(matched: pd.DataFrame) -> dict:
    """Matched-rows distribution summary (post-join).

    Computes mean model P(over line) vs realized P(over line) across all
    matched rows, plus an optional int-line-bucketed view for buckets
    with >= 20 rows. Called only when len(matched) > 0.
    """
    out = {
        "n_matched": int(len(matched)),
        "mean_model_p_over": float(matched["model_p_over"].mean()),
        "mean_realized_p_over": float(matched["realized_over"].mean()),
    }
    bucket_rows: list[dict] = []
    for line_bucket, grp in matched.groupby(matched["line"].astype(float).apply(int)):
        if len(grp) < 20:
            continue
        bucket_rows.append({
            "line_bucket": int(line_bucket),
            "n_rows": int(len(grp)),
            "mean_model_p_over": float(grp["model_p_over"].mean()),
            "mean_realized_p_over": float(grp["realized_over"].mean()),
        })
    if bucket_rows:
        bucket_rows.sort(key=lambda r: r["line_bucket"])
        out["by_line_bucket"] = bucket_rows
    return out


def _edge_selection_metrics(matched: pd.DataFrame) -> dict:
    """Primary side-split metric.

    For each matched row pick whichever side has the larger model - market
    edge (ties go OVER). Aggregate Brier / log-loss for the chosen-side
    probability against the realized chosen-side indicator, per bucket.
    """
    if matched.empty:
        return {
            "n_rows": 0, "n_over_picked": 0, "n_under_picked": 0,
            "over": {"n_rows": 0}, "under": {"n_rows": 0},
        }
    edge_over = matched["model_p_over"].to_numpy() - matched["fair_over_prob"].to_numpy()
    edge_under = matched["model_p_under"].to_numpy() - matched["fair_under_prob"].to_numpy()
    pick_over = edge_over >= edge_under

    def _bucket(mask: np.ndarray, side: str) -> dict:
        if not mask.any():
            return {
                "n_rows": 0, "brier_model": float("nan"), "brier_market": float("nan"),
                "logloss_model": float("nan"), "logloss_market": float("nan"),
                "rel_brier_improvement_pct": float("nan"),
                "rel_logloss_improvement_pct": float("nan"),
            }
        sub = matched.loc[mask]
        if side == "over":
            y = sub["realized_over"].to_numpy().astype(int)
            m = sub["model_p_over"].to_numpy()
            k = sub["fair_over_prob"].to_numpy()
        else:
            y = sub["realized_under"].to_numpy().astype(int)
            m = sub["model_p_under"].to_numpy()
            k = sub["fair_under_prob"].to_numpy()
        b_m = _brier(m, y); b_k = _brier(k, y)
        l_m = _logloss(m, y); l_k = _logloss(k, y)
        return {
            "n_rows": int(mask.sum()),
            "brier_model": b_m,
            "brier_market": b_k,
            "logloss_model": l_m,
            "logloss_market": l_k,
            "rel_brier_improvement_pct": _pct_improvement(b_m, b_k),
            "rel_logloss_improvement_pct": _pct_improvement(l_m, l_k),
        }

    return {
        "n_rows": int(len(matched)),
        "n_over_picked": int(pick_over.sum()),
        "n_under_picked": int((~pick_over).sum()),
        "over": _bucket(pick_over, "over"),
        "under": _bucket(~pick_over, "under"),
    }


# ── core pipeline ──────────────────────────────────────────────────────────


def _match_market(
    fold: pd.DataFrame,
    player_name_map: dict[int, str],
    market: pd.DataFrame,
    stat: str,
) -> tuple[pd.DataFrame, int, int, int, int]:
    """Attach each matched market line to a fold row.

    Policy:
      - join on (player_norm, game_date == snapshot_date, stat) only; the
        fold parquet has no `line` column, so the market side supplies
        the line for every matched pair.
      - integer market lines are dropped up front (half-point lines only).
      - if multiple market lines survive the join for the same
        (player_id, game_id, stat), the whole group is excluded rather
        than scored — we do not pick which market line to attribute.
      - exact-line pushes on matched rows (outcome == line) are excluded
        from side metrics.

    Return (matched, n_fold_rows, n_unmatched, n_dupes_excluded,
    n_integer_line_excluded).
    """
    fold_stat = fold[fold["stat"] == stat].copy()
    fold_stat["player_norm"] = fold_stat["player_id"].map(player_name_map)
    fold_stat = fold_stat.dropna(subset=["player_norm"])

    market_stat = market[market["stat"] == stat].copy()
    # Half-point-only policy is applied to the market side here; the fold
    # parquet has no line to compare.
    int_line_mask = np.isclose(
        market_stat["line"].to_numpy() - np.round(market_stat["line"].to_numpy()),
        0.0, atol=1e-9,
    )
    n_integer_excluded = int(int_line_mask.sum())
    if n_integer_excluded:
        print(f"  {stat}: excluded {n_integer_excluded} integer-line market rows")
    market_stat = market_stat.loc[~int_line_mask].copy()

    merged = fold_stat.merge(
        market_stat,
        left_on=["player_norm", "game_date", "stat"],
        right_on=["player_norm", "snapshot_date", "stat"],
        how="inner",
        suffixes=("", "_mkt"),
    )
    # Defensive half-point check post-join — the pre-join mask already
    # drops integer lines, so this is a no-op unless upstream behavior
    # changes. The intent is: under no circumstance does a matched row
    # carry an integer line into the Brier / log-loss computation.
    keep_half = ~np.isclose(
        merged["line"].to_numpy() - np.round(merged["line"].to_numpy()),
        0.0, atol=1e-9,
    )
    merged = merged.loc[keep_half].copy()

    key_cols = ["player_id", "game_id", "stat"]
    group_sizes = merged.groupby(key_cols).size()
    dupe_keys = group_sizes[group_sizes > 1].index
    n_dupes_excluded = int(len(dupe_keys))
    if n_dupes_excluded:
        print(
            f"  {stat}: excluded {n_dupes_excluded} (player_id, game_id, stat) "
            f"groups with multiple market lines after the join"
        )
        dupe_set = set(dupe_keys.tolist())
        merged["_dupe"] = merged[key_cols].apply(
            lambda r: (r["player_id"], r["game_id"], r["stat"]) in dupe_set, axis=1,
        )
        merged = merged[~merged["_dupe"]].drop(columns=["_dupe"])

    def _split(row):
        pmf = np.asarray(row["pmf"], dtype=np.float64)
        ln = float(row["line"])
        p_over = float(pmf[ceil(ln):].sum()) if ceil(ln) < pmf.size else 0.0
        return pd.Series({"model_p_over": p_over, "model_p_under": 1.0 - p_over})

    if not merged.empty:
        split = merged.apply(_split, axis=1)
        merged = pd.concat([merged, split], axis=1)
        merged["realized_over"] = (merged["outcome"] > merged["line"]).astype(int)
        merged["realized_under"] = (merged["outcome"] < merged["line"]).astype(int)
        push_mask = (merged["outcome"] == merged["line"])
        if push_mask.any():
            n_push = int(push_mask.sum())
            print(
                f"  {stat}: {n_push} matched rows hit the exact line (push); "
                f"excluding from side metrics"
            )
            merged = merged.loc[~push_mask].copy()
        assert (
            ((merged["realized_over"] + merged["realized_under"]) == 1).all()
        ), "half-point side split must cover the whole outcome space"

    n_fold_rows = int(len(fold_stat))
    n_matched = int(len(merged))
    n_unmatched = int(n_fold_rows - n_matched - n_dupes_excluded)
    return merged, n_fold_rows, n_unmatched, n_dupes_excluded, n_integer_excluded


def _line_neighborhood_table(
    matched: pd.DataFrame, stat: str, line_neighborhood: int, min_rows: int = 20,
) -> pd.DataFrame:
    if matched.empty:
        return pd.DataFrame()
    out_rows: list[dict] = []
    for line_val, group in matched.groupby("line"):
        if len(group) < min_rows:
            continue
        pmfs = [np.asarray(r, dtype=np.float64) for r in group["pmf"].tolist()]
        max_k = max(p.size for p in pmfs)
        P = np.zeros((len(pmfs), max_k), dtype=np.float64)
        for i, p in enumerate(pmfs):
            P[i, : p.size] = p
        outcomes = group["outcome"].to_numpy().astype(int)
        for offset in range(-line_neighborhood, line_neighborhood + 1):
            atom_value = int(round(float(line_val) + offset))
            if not (0 <= atom_value < max_k):
                continue
            predicted = float(P[:, atom_value].mean())
            empirical = float(np.mean(outcomes == atom_value))
            count = int(np.sum(outcomes == atom_value))
            out_rows.append({
                "stat": stat, "line": float(line_val), "offset": int(offset),
                "atom_value": atom_value, "predicted": predicted,
                "empirical": empirical, "count": count,
                "deviation": predicted - empirical,
            })
    return pd.DataFrame(out_rows)


# ── main ───────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold-oof", required=True, type=Path)
    ap.add_argument("--stats-df", required=True, type=Path)
    ap.add_argument("--closing-lines-dir", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--stats", nargs="+", default=list(DEFAULT_STATS))
    ap.add_argument("--min-atom-count", type=int, default=20)
    ap.add_argument("--line-neighborhood", type=int, default=3)
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    fold = _load_fold_oof(args.fold_oof)
    print(f"Loaded fold OOF: {len(fold):,} rows")
    print(f"  stats present: {sorted(fold['stat'].unique())}")
    for s in sorted(fold["stat"].unique()):
        print(f"    {s}: {int((fold['stat']==s).sum()):,} rows")
    print(
        f"  game_date range: {fold['game_date'].min()} -> {fold['game_date'].max()}"
    )

    _validate_pmfs(fold)

    player_name_map = _load_player_name_map(args.stats_df)
    print(f"Loaded player_id → player_name_lower for {len(player_name_map):,} players")

    fold_start = str(fold["fold_start"].min())
    fold_end = str(fold["fold_end"].max())
    market = _load_closing_lines(
        args.closing_lines_dir, window_lo=fold_start[:10], window_hi=fold_end[:10],
    )
    print(
        f"Loaded closing-lines market rows: {len(market):,} "
        f"(window {fold_start[:10]} -> {fold_end[:10]})"
    )

    selected_stats = [s.lower() for s in args.stats]
    report = {
        "metadata": {
            "git_sha": _git_sha(),
            "run_timestamp": datetime.utcnow().isoformat() + "Z",
            "fold_start": fold_start,
            "fold_end": fold_end,
            "n_rows": int(len(fold)),
            "stats_requested": selected_stats,
            "min_atom_count": int(args.min_atom_count),
            "line_neighborhood": int(args.line_neighborhood),
        },
        "per_stat": {},
    }

    n_matched_total = 0
    for stat in selected_stats:
        fold_stat = fold[fold["stat"] == stat]
        if fold_stat.empty:
            print(f"\n[{stat}] no fold rows; skipping")
            continue

        atom_report = _atom_metrics_for_stat(fold_stat, args.min_atom_count)

        matched, n_fold_rows, n_unmatched, n_dupes, n_int = _match_market(
            fold, player_name_map, market, stat,
        )
        n_matched_total += len(matched)
        sanity = _side_metrics_unconditional(matched)
        edge = _edge_selection_metrics(matched)

        # Matched-rows distributional summary is attached to the same
        # distributional_summary dict emitted by _atom_metrics_for_stat.
        # When no matched rows exist (expected for TOV / any stat without
        # closing-line coverage) the atom-level fields still land; the
        # matched-side block is simply absent.
        if len(matched) > 0:
            atom_report["distributional_summary"]["matched"] = (
                _matched_distributional_summary(matched)
            )

        nbhd = _line_neighborhood_table(
            matched, stat=stat, line_neighborhood=args.line_neighborhood,
        )
        nbhd_path = args.output_dir / f"{stat}_line_neighborhood.csv"
        if not nbhd.empty:
            nbhd.to_csv(nbhd_path, index=False)

        report["per_stat"][stat] = {
            "atom": atom_report,
            "match_counts": {
                "fold_rows_with_player_name": int(n_fold_rows),
                "matched_rows": int(len(matched)),
                "unmatched_rows": int(n_unmatched),
                "duplicates_excluded": int(n_dupes),
                "integer_line_market_rows_excluded": int(n_int),
            },
            "side_sanity": sanity,
            "edge_selection": edge,
            "line_neighborhood_csv": (
                str(nbhd_path.relative_to(args.output_dir)) if not nbhd.empty else None
            ),
        }

        # ── stdout summary ──
        print(f"\n[{stat}]")
        print(
            f"  atom_ece_pred_mass={atom_report['atom_ece_pred_mass']:.4f}  "
            f"atom_brier={atom_report['atom_brier']:.4f}  "
            f"atom_logloss={atom_report['atom_logloss']:.4f}  "
            f"n_rows={atom_report['n_rows']}"
        )
        _dist = atom_report["distributional_summary"]
        print(
            f"  DIST  pred_mean={_dist['pred_mean']:.2f} "
            f"realized_mean={_dist['realized_mean']:.2f}  "
            f"pred_p0={_dist['pred_p0']:.3f} "
            f"realized_p0={_dist['realized_p0']:.3f}  "
            f"pred_p_le1={_dist['pred_p_le1']:.3f} "
            f"realized_p_le1={_dist['realized_p_le1']:.3f}"
        )
        _dmatch = _dist.get("matched")
        if _dmatch is not None:
            print(
                f"  DIST-MATCHED  mean_model_p_over={_dmatch['mean_model_p_over']:.3f}  "
                f"mean_realized_p_over={_dmatch['mean_realized_p_over']:.3f}  "
                f"n_matched={_dmatch['n_matched']}"
            )
        print(
            f"  matched={len(matched):,}  unmatched={n_unmatched:,}  "
            f"duplicates_excluded={n_dupes}  integer_lines_excluded={n_int}"
        )
        if sanity["n_matched"] > 0:
            # Sanity-check unconditional OVER/UNDER line.
            print(
                f"  SANITY  OVER  brier m={sanity['brier_model_over']:.4f} k={sanity['brier_market_over']:.4f}  "
                f"ll m={sanity['logloss_model_over']:.4f} k={sanity['logloss_market_over']:.4f}"
            )
            print(
                f"  SANITY  UNDER brier m={sanity['brier_model_under']:.4f} k={sanity['brier_market_under']:.4f}  "
                f"ll m={sanity['logloss_model_under']:.4f} k={sanity['logloss_market_under']:.4f}"
            )
            # Primary edge-selection line.
            print(
                f"  EDGE-SEL  n_over_picked={edge['n_over_picked']}  "
                f"n_under_picked={edge['n_under_picked']}"
            )
            print(
                f"  EDGE-SEL  OVER  n={edge['over']['n_rows']}  "
                f"brier m={edge['over']['brier_model']:.4f} k={edge['over']['brier_market']:.4f}  "
                f"rel_brier_imp={edge['over']['rel_brier_improvement_pct']:+.2f}%  "
                f"rel_ll_imp={edge['over']['rel_logloss_improvement_pct']:+.2f}%"
            )
            print(
                f"  EDGE-SEL  UNDER n={edge['under']['n_rows']}  "
                f"brier m={edge['under']['brier_model']:.4f} k={edge['under']['brier_market']:.4f}  "
                f"rel_brier_imp={edge['under']['rel_brier_improvement_pct']:+.2f}%  "
                f"rel_ll_imp={edge['under']['rel_logloss_improvement_pct']:+.2f}%"
            )
        print("  top 5 worst-deviation atoms (count >= 20):")
        for entry in atom_report["reliability"][:5]:
            print(
                f"    atom={entry['atom_value']:>3}  pred={entry['predicted_mean_prob']:.4f}  "
                f"emp={entry['empirical_freq']:.4f}  n={entry['count']:>5}  "
                f"dev={entry['abs_dev']:+.4f}"
            )

    report["metadata"]["n_matched_for_market"] = int(n_matched_total)

    out_json = args.output_dir / "exact_mass_and_side_split.json"
    out_json.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nWrote {out_json}")


if __name__ == "__main__":
    main()
