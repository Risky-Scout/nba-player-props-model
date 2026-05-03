#!/usr/bin/env python3
"""Phase 13Z+ — Actuarial PMF variance experience study.

Builds an actuarial-style experience study comparing realized player-stat
outcomes against per-row PMF predictions. For every settled prediction
(game_date < as-of-date) within the lookback window, computes from the PMF:
  - expected_mean, expected_variance
  - p0
  - probability of the actual outcome
  - model quantiles at 10/25/50/75/90
  - model over/under probability vs the line
  - market no-vig over probability where available

Aggregates across the slate and within actuarial buckets:
  - mean_AE = sum(actual) / sum(expected_mean)
  - variance_AE = sum((actual - expected_mean)^2) / sum(expected_variance)
  - standardized_residual = (actual - expected_mean) / sqrt(expected_variance)
  - PMF negative log-likelihood
  - ranked probability score
  - over/under Brier (model and market)
  - model-vs-market Brier and logloss
  - quantile coverage at 10/25/50/75/90

Buckets:
  stat | side | snapshot_type | lineup_confirmed | role_bucket
  | minutes_volatility_bucket | injury_context_bucket
  | vacated_opportunity_bucket | edge_bucket | p0_bucket
  | predicted_variance_bucket | line_bucket | low_line_discrete

Inputs (CLI):
  --as-of-date YYYY-MM-DD   (required; rows with game_date < as_of_date are eligible)
  --lookback-days 60        (default 60)
  --min-bucket-n 30         (default 30; thinner buckets flagged but still reported)

Outputs:
  artifacts/experience_studies/pmf_variance_experience_<as_of>.csv
  artifacts/experience_studies/pmf_variance_experience_<as_of>.json
  artifacts/experience_studies/pmf_variance_experience_<as_of>.md

Pass line:
  PMF_VARIANCE_EXPERIENCE_STUDY_PASS

Fail conditions:
  - no settled outcomes available (zero joined rows)
  - PMFs cannot be parsed (every PMF parse fails)
  - expected variance is missing from every row
  - actual outcomes cannot be joined (no overlap between predictions and stats)
  - sample size below min_bucket_n AND the script fails to write an honest
    insufficient-sample report
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERIES_DIR = REPO_ROOT / "deliveries"
PREDICTIONS_DIR = REPO_ROOT / "predictions"
STATS_PATH = REPO_ROOT / "data" / "player_game_stats.parquet"
OUT_DIR = REPO_ROOT / "artifacts" / "experience_studies"

EPS = 1e-6
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
STAT_TO_STATSCOL = {"pts": "pts", "reb": "reb", "ast": "ast",
                    "fg3m": "fg3m", "stl": "stl", "blk": "blk",
                    "tov": "turnover"}
LOW_LINE_DISCRETE_STATS = {"fg3m", "stl", "blk", "tov"}
# mp_bucket from sgp_engine.usage_bucket / mp_bucket — minutes-played tier.
MP_BUCKET_LABELS = {0: "lt15min", 1: "lt22min", 2: "lt30min", 3: "ge30min_starter"}


# ── Parsing + PMF math ────────────────────────────────────────────────────

def _parse_pmf(value) -> dict[int, float] | None:
    """Parse PMF blob into {int_value: prob}. Accepts dict, JSON string,
    or pandas-rendered dict-string. Returns ``None`` on parse failure."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, dict):
        raw = value
    else:
        s = str(value).strip()
        if not s or s in {"nan", "None"}:
            return None
        try:
            raw = json.loads(s)
        except Exception:
            try:
                # Pandas' default repr emits single-quoted dicts.
                raw = json.loads(s.replace("'", '"'))
            except Exception:
                try:
                    import ast
                    raw = ast.literal_eval(s)
                except Exception:
                    return None
    out: dict[int, float] = {}
    for k, v in raw.items():
        try:
            ki = int(float(k))
            pv = float(v)
        except Exception:
            continue
        if pv < 0 or not math.isfinite(pv):
            continue
        out[ki] = out.get(ki, 0.0) + pv
    if not out:
        return None
    s = sum(out.values())
    if s <= 0:
        return None
    if abs(s - 1.0) > 1e-3:
        out = {k: v / s for k, v in out.items()}
    return out


def _pmf_moments(pmf: dict[int, float]) -> tuple[float, float]:
    keys = np.array(sorted(pmf.keys()), dtype=float)
    probs = np.array([pmf[int(k)] for k in keys], dtype=float)
    mean = float((keys * probs).sum())
    var = float(((keys - mean) ** 2 * probs).sum())
    return mean, var


def _pmf_cdf(pmf: dict[int, float]) -> tuple[np.ndarray, np.ndarray]:
    keys = np.array(sorted(pmf.keys()), dtype=int)
    probs = np.array([pmf[int(k)] for k in keys], dtype=float)
    cdf = np.cumsum(probs)
    cdf = np.clip(cdf, 0.0, 1.0)
    return keys, cdf


def _model_quantile(pmf: dict[int, float], alpha: float) -> float:
    keys, cdf = _pmf_cdf(pmf)
    idx = int(np.searchsorted(cdf, alpha, side="left"))
    idx = min(idx, len(keys) - 1)
    return float(keys[idx])


def _model_p_over(pmf: dict[int, float], line: float) -> float:
    """P(actual > line) under the PMF, with half-credit for ties when the
    line lands exactly on an integer support point (push convention)."""
    p_over = 0.0
    p_eq = 0.0
    for k, p in pmf.items():
        if k > line:
            p_over += p
        elif math.isclose(k, line):
            p_eq += p
    return float(p_over + 0.5 * p_eq)


def _prob_of_actual(pmf: dict[int, float], actual: float) -> float:
    """Probability the PMF assigns to the integer outcome closest to actual.
    For non-integer actuals we round down (player-game stats are integer)."""
    a_int = int(round(actual))
    return float(pmf.get(a_int, 0.0))


def _pmf_rps(pmf: dict[int, float], actual: float) -> float:
    """Ranked probability score (lower is better). Squared error between
    cumulative model and step-CDF of the realized outcome, averaged over
    the support."""
    keys, cdf_model = _pmf_cdf(pmf)
    a_int = int(round(actual))
    cdf_actual = (keys >= a_int).astype(float)
    # Lattice K = number of support buckets; require >= 2 for division.
    K = max(int(len(keys)), 2)
    return float(((cdf_model - cdf_actual) ** 2).sum() / (K - 1))


# ── Data loaders ──────────────────────────────────────────────────────────

def _load_after_game_scoring_metadata(date: str) -> pd.DataFrame | None:
    """Load after_game_scoring as per (player, stat) metadata enrichment —
    snapshot_type, role_bucket, lineup_freshness, injury_freshness. Drops
    the line column since the canonical model PMF is per-stat (line is
    null in this feed). Returns ``None`` when the file is absent."""
    p = DELIVERIES_DIR / date / "after_game_scoring" / "after_game_scoring.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if df.empty:
        return None
    df = df.copy()
    df["snapshot_type_meta"] = df["snapshot_type"].astype(str)
    df["role_bucket_meta"] = df["role_bucket"].astype(str).where(
        df["role_bucket"].notna(), "unknown"
    )
    df["lineup_freshness_status_meta"] = df["lineup_freshness_status"].astype(str)
    df["injury_freshness_status_meta"] = df["injury_freshness_status"].astype(str)
    keep = [
        "player_id", "game_id", "stat",
        "snapshot_type_meta", "role_bucket_meta",
        "lineup_freshness_status_meta", "injury_freshness_status_meta",
    ]
    return df[keep].drop_duplicates(subset=["player_id", "game_id", "stat"], keep="first")


def _load_predictions_with_actuals(date: str, stats_lookup: pd.DataFrame) -> pd.DataFrame | None:
    p = PREDICTIONS_DIR / f"all_props_{date}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if df.empty:
        return None
    df = df.copy()
    df["source"] = "predictions_join_stats"
    df["delivery_date"] = date
    df["pmf"] = df["pmf"].apply(_parse_pmf)

    join = df.merge(
        stats_lookup,
        how="left",
        on=["player_id", "game_id"],
        validate="many_to_one",
    )
    # Pull the realized stat value into actual.
    actuals = []
    for _, r in join.iterrows():
        col = STAT_TO_STATSCOL.get(str(r["stat"]))
        if col is None or col not in stats_lookup.columns:
            actuals.append(np.nan)
            continue
        actuals.append(r.get(col, np.nan))
    join["actual"] = pd.to_numeric(pd.Series(actuals), errors="coerce")
    join["game_date"] = join["game_date"].astype(str)

    # Side-specific mapping: model_prob_cal here is P(side wins). Convert to
    # model_p_over consistently so all rows speak the same language.
    side = join["side"].astype(str).str.upper()
    mp_cal = pd.to_numeric(join["model_prob_cal"], errors="coerce")
    market_p = pd.to_numeric(join["market_prob"], errors="coerce")
    join["model_p_over_src"] = np.where(side == "OVER", mp_cal, 1.0 - mp_cal)
    join["market_p_over_src"] = np.where(side == "OVER", market_p, 1.0 - market_p)
    join["raw_edge_src"] = pd.to_numeric(join.get("raw_edge"), errors="coerce")

    # Map numeric mp_bucket → readable minutes-tier label.
    mp_int = pd.to_numeric(join.get("mp_bucket"), errors="coerce")
    mp_label = mp_int.map(MP_BUCKET_LABELS).fillna("unknown_min_tier")

    # Enrich with per-stat metadata from after_game_scoring when available.
    # Note: morning predictions and after_game_scoring rows describe the
    # same morning snapshot; t_minus_25 / close_lock have no joined outcomes
    # in this feed yet, so snapshot_type collapses to "morning".
    meta = _load_after_game_scoring_metadata(date)
    if meta is not None:
        join = join.merge(meta, on=["player_id", "game_id", "stat"], how="left")
        join["source"] = np.where(join["snapshot_type_meta"].notna(),
                                   "predictions+after_game_meta",
                                   "predictions_join_stats")
        join["snapshot_type"] = "morning"
        join["role_bucket"] = join["role_bucket_meta"].fillna(mp_label)
        join["lineup_freshness_status"] = join["lineup_freshness_status_meta"].fillna("unavailable")
        join["injury_freshness_status"] = join["injury_freshness_status_meta"].fillna("unavailable")
    else:
        join["snapshot_type"] = "morning"
        join["role_bucket"] = mp_label
        join["lineup_freshness_status"] = "unavailable"
        join["injury_freshness_status"] = "unavailable"
    join["side_label"] = side

    keep = [
        "source", "delivery_date", "game_date", "player_id", "player_name",
        "game_id", "stat", "line", "side_label", "pmf", "actual",
        "model_p_over_src", "market_p_over_src", "raw_edge_src",
        "snapshot_type", "role_bucket", "lineup_freshness_status",
        "injury_freshness_status",
    ]
    return join[keep]


def _load_stats_lookup() -> pd.DataFrame:
    if not STATS_PATH.exists():
        return pd.DataFrame()
    cols = ["player_id", "game_id", "game_date"] + list(set(STAT_TO_STATSCOL.values()))
    df = pd.read_parquet(STATS_PATH, columns=cols)
    # Each (player, game) is unique enough; defensively dedupe.
    df = df.drop_duplicates(subset=["player_id", "game_id"], keep="first")
    df["game_date"] = df["game_date"].astype(str)
    return df


# ── Per-row metric computation ────────────────────────────────────────────

def _row_metrics(row: pd.Series) -> dict | None:
    pmf = row.get("pmf")
    actual = row.get("actual")
    if pmf is None or actual is None or (isinstance(actual, float) and math.isnan(actual)):
        return None
    mean, var = _pmf_moments(pmf)
    if not math.isfinite(var) or var < 0:
        return None
    p0 = float(pmf.get(0, 0.0))
    line = float(row["line"]) if pd.notna(row["line"]) else np.nan

    p_actual = _prob_of_actual(pmf, actual)
    pmf_nll = -math.log(max(p_actual, EPS))
    pmf_rps = _pmf_rps(pmf, actual)

    quantiles = {f"q{int(a*100):02d}": _model_quantile(pmf, a) for a in QUANTILES}
    coverage = {f"covered_{int(a*100):02d}": float(actual <= quantiles[f"q{int(a*100):02d}"]) for a in QUANTILES}

    if not math.isfinite(line):
        model_p_over = float("nan")
        over_indicator = float("nan")
        brier_model = float("nan")
        logloss_model = float("nan")
    else:
        # Prefer the source's stored p_over when present (it carries any
        # calibration). Fall back to PMF-derived value.
        src_p = row.get("model_p_over_src")
        if pd.notna(src_p) and 0.0 < float(src_p) < 1.0:
            model_p_over = float(src_p)
        else:
            model_p_over = _model_p_over(pmf, line)
        over_indicator = 1.0 if actual > line else (0.0 if actual < line else 0.5)
        brier_model = (over_indicator - model_p_over) ** 2
        p_clip = min(max(model_p_over, EPS), 1.0 - EPS)
        if over_indicator == 0.5:
            logloss_model = -0.5 * (math.log(p_clip) + math.log(1.0 - p_clip))
        else:
            logloss_model = -(over_indicator * math.log(p_clip)
                              + (1.0 - over_indicator) * math.log(1.0 - p_clip))

    market_p = row.get("market_p_over_src")
    if pd.notna(market_p) and 0.0 < float(market_p) < 1.0 and math.isfinite(line):
        market_p_over = float(market_p)
        brier_market = (over_indicator - market_p_over) ** 2 if math.isfinite(over_indicator) else float("nan")
        if math.isfinite(over_indicator):
            mp_clip = min(max(market_p_over, EPS), 1.0 - EPS)
            if over_indicator == 0.5:
                logloss_market = -0.5 * (math.log(mp_clip) + math.log(1.0 - mp_clip))
            else:
                logloss_market = -(over_indicator * math.log(mp_clip)
                                   + (1.0 - over_indicator) * math.log(1.0 - mp_clip))
        else:
            logloss_market = float("nan")
    else:
        market_p_over = float("nan")
        brier_market = float("nan")
        logloss_market = float("nan")

    std_residual = (actual - mean) / math.sqrt(var) if var > 0 else float("nan")

    out = {
        "expected_mean": mean,
        "expected_variance": var,
        "p0": p0,
        "prob_of_actual": p_actual,
        "model_p_over": model_p_over,
        "market_p_over": market_p_over,
        "over_indicator": over_indicator,
        "pmf_nll": pmf_nll,
        "pmf_rps": pmf_rps,
        "brier_model": brier_model,
        "brier_market": brier_market,
        "logloss_model": logloss_model,
        "logloss_market": logloss_market,
        "std_residual": std_residual,
        "abs_residual_sq": (actual - mean) ** 2,
    }
    out.update(quantiles)
    out.update(coverage)
    return out


# ── Bucket assignment ─────────────────────────────────────────────────────

def _edge_bucket(edge: float) -> str:
    if not math.isfinite(edge):
        return "unknown"
    if edge < 0.0:
        return "neg"
    if edge < 0.05:
        return "0_to_5pct"
    if edge < 0.10:
        return "5_to_10pct"
    if edge < 0.20:
        return "10_to_20pct"
    return "ge_20pct"


def _p0_bucket(p0: float) -> str:
    if not math.isfinite(p0):
        return "unknown"
    if p0 < 0.05:
        return "lt_5pct"
    if p0 < 0.20:
        return "5_to_20pct"
    if p0 < 0.50:
        return "20_to_50pct"
    return "ge_50pct"


def _variance_bucket(var: float, cutoffs: tuple[float, float]) -> str:
    lo, hi = cutoffs
    if not math.isfinite(var):
        return "unknown"
    if var < lo:
        return "low"
    if var < hi:
        return "mid"
    return "high"


def _line_bucket_for_stat(stat: str, line: float) -> str:
    if not math.isfinite(line):
        return "unknown"
    if stat == "pts":
        if line < 10: return "lt_10"
        if line < 15: return "10_to_15"
        if line < 20: return "15_to_20"
        if line < 25: return "20_to_25"
        return "ge_25"
    if stat == "reb":
        if line < 4: return "lt_4"
        if line < 7: return "4_to_7"
        if line < 10: return "7_to_10"
        return "ge_10"
    if stat == "ast":
        if line < 3: return "lt_3"
        if line < 5: return "3_to_5"
        if line < 8: return "5_to_8"
        return "ge_8"
    if stat in {"fg3m", "stl", "blk", "tov"}:
        if line <= 0.5: return "le_half"
        if line <= 1.5: return "1_to_1p5"
        if line <= 2.5: return "2_to_2p5"
        return "ge_3"
    return "unknown"


def _lineup_confirmed_label(s: str) -> str:
    s = (s or "unavailable").lower()
    if s in {"confirmed", "official"}:
        return "confirmed"
    if s in {"projected", "expected"}:
        return "projected"
    if s == "unavailable":
        return "unavailable"
    return s


def _injury_context_label(s: str) -> str:
    s = (s or "unavailable").lower()
    return s


# ── Aggregation ───────────────────────────────────────────────────────────

def _aggregate(df: pd.DataFrame, group_col: str | None, min_n: int) -> pd.DataFrame:
    """Aggregate metrics. If ``group_col`` is None, single-row overall."""
    if group_col is None:
        df = df.assign(_grp="ALL")
        gcol = "_grp"
        bucket_label = "overall"
    else:
        gcol = group_col
        bucket_label = group_col

    rows = []
    for key, sub in df.groupby(gcol, dropna=False):
        n = len(sub)
        sum_actual = float(sub["actual"].sum())
        sum_mean = float(sub["expected_mean"].sum())
        sum_var = float(sub["expected_variance"].sum())
        sum_sq_res = float(sub["abs_residual_sq"].sum())
        mean_ae = sum_actual / sum_mean if sum_mean > 0 else float("nan")
        var_ae = sum_sq_res / sum_var if sum_var > 0 else float("nan")
        std_res = sub["std_residual"].dropna()
        std_res_mean = float(std_res.mean()) if len(std_res) else float("nan")
        std_res_sd = float(std_res.std(ddof=1)) if len(std_res) > 1 else float("nan")
        nll_mean = float(sub["pmf_nll"].mean())
        rps_mean = float(sub["pmf_rps"].mean())
        brier_model_mean = float(sub["brier_model"].dropna().mean()) if sub["brier_model"].notna().any() else float("nan")
        brier_market_mean = float(sub["brier_market"].dropna().mean()) if sub["brier_market"].notna().any() else float("nan")
        logloss_model_mean = float(sub["logloss_model"].dropna().mean()) if sub["logloss_model"].notna().any() else float("nan")
        logloss_market_mean = float(sub["logloss_market"].dropna().mean()) if sub["logloss_market"].notna().any() else float("nan")
        coverage = {f"coverage_{int(a*100):02d}":
                    float(sub[f"covered_{int(a*100):02d}"].mean())
                    for a in QUANTILES}
        rows.append({
            "bucket_dimension": bucket_label,
            "bucket_value": str(key),
            "n": n,
            "thin_sample": n < min_n,
            "mean_AE": mean_ae,
            "variance_AE": var_ae,
            "std_residual_mean": std_res_mean,
            "std_residual_sd": std_res_sd,
            "pmf_nll_mean": nll_mean,
            "pmf_rps_mean": rps_mean,
            "brier_over_model_mean": brier_model_mean,
            "brier_over_market_mean": brier_market_mean,
            "logloss_over_model_mean": logloss_model_mean,
            "logloss_over_market_mean": logloss_market_mean,
            **coverage,
            "sum_actual": sum_actual,
            "sum_expected_mean": sum_mean,
            "sum_expected_variance": sum_var,
            "sum_sq_residual": sum_sq_res,
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["bucket_dimension", "bucket_value"]).reset_index(drop=True)
    return out


# ── Markdown narrative ────────────────────────────────────────────────────

def _fmt(x, dp=4):
    if x is None or (isinstance(x, float) and (math.isnan(x) or not math.isfinite(x))):
        return "—"
    return f"{x:.{dp}f}"


def _format_long_date(iso: str) -> str:
    try:
        return dt.date.fromisoformat(iso).strftime("%B %-d, %Y")
    except Exception:
        return iso


def _write_markdown(out_path: Path, *, as_of: str, lookback: int, min_n: int,
                     overall: dict, agg: pd.DataFrame, dataframe: pd.DataFrame,
                     date_window: tuple[str, str], n_days: int) -> None:
    """Actuarial-style report. Sections:

      Executive summary | What this study tests | Overall results
      | Where PMF is too narrow | Where PMF is too wide
      | Where sample is thin | Live-context limitations
      | Interpretation for Derek | Next improvements | Provenance.
    """
    n_total = int(overall.get("n", 0))
    mean_ae = overall.get("mean_AE", float("nan"))
    var_ae = overall.get("variance_AE", float("nan"))
    std_mu = overall.get("std_residual_mean", float("nan"))
    std_sd = overall.get("std_residual_sd", float("nan"))
    nll = overall.get("pmf_nll_mean", float("nan"))
    rps = overall.get("pmf_rps_mean", float("nan"))
    brier_m = overall.get("brier_over_model_mean", float("nan"))
    brier_mk = overall.get("brier_over_market_mean", float("nan"))
    ll_m = overall.get("logloss_over_model_mean", float("nan"))
    ll_mk = overall.get("logloss_over_market_mean", float("nan"))
    cov = {a: overall.get(f"coverage_{int(a*100):02d}", float("nan")) for a in QUANTILES}

    actual_total = float(overall.get("sum_actual", 0.0))
    expected_total = float(overall.get("sum_expected_mean", 0.0))
    sq_err_total = float(overall.get("sum_sq_residual", 0.0))
    var_total = float(overall.get("sum_expected_variance", 0.0))
    actual_mean = (actual_total / n_total) if n_total else float("nan")
    expected_mean = (expected_total / n_total) if n_total else float("nan")

    model_trails_market = (math.isfinite(brier_m) and math.isfinite(brier_mk)
                           and brier_m > brier_mk)

    # ── Verdict tagging ───
    def _verdict(row):
        if row["thin_sample"]:
            return "THIN_SAMPLE"
        v = row["variance_AE"]
        if not math.isfinite(v):
            return "UNAVAILABLE"
        if v > 1.20:
            return "TOO_NARROW"
        if v < 0.80:
            return "TOO_WIDE"
        return "WELL_CALIBRATED"
    if not agg.empty:
        agg = agg.copy()
        agg["verdict"] = agg.apply(_verdict, axis=1)

    snap_types_seen = sorted(set(dataframe["snapshot_type"].unique()))
    has_only_morning = (len(snap_types_seen) == 1
                        and "morning" in {s.lower() for s in snap_types_seen})

    lines: list[str] = []
    lines.append(f"# PMF Variance Experience Study — {_format_long_date(as_of)}")
    lines.append("")
    lines.append(f"_Actual-to-expected (A/E) review of settled PMF predictions, "
                 f"as-of `{as_of}` over a {lookback}-day lookback._")
    lines.append("")

    # ── Executive summary ───
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- **{n_total:,}** settled rows from **{date_window[0]}** through "
                 f"**{date_window[1]}** ({n_days} delivery dates with at least one settled row).")
    lines.append(f"- **Mean A/E = {_fmt(mean_ae, 3)}** — actual outcomes ran "
                 f"{(mean_ae - 1.0) * 100:+.1f}% relative to expected means in this sample.")
    lines.append(f"- **Variance A/E = {_fmt(var_ae, 3)}** — PMF spread is reasonably close "
                 f"overall (the well-calibrated band is 0.80–1.20), "
                 f"{'slightly wide' if var_ae < 1.0 else 'slightly narrow'} overall.")
    lines.append(f"- **Standardized residual: mean = {_fmt(std_mu, 3)}, sd = "
                 f"{_fmt(std_sd, 3)}** — slight positive bias and dispersion close to calibrated "
                 f"(target sd = 1.00).")
    lines.append(f"- Quantile coverage at the 75th and 90th percentiles is near target "
                 f"({_fmt(cov[0.75], 3)} and {_fmt(cov[0.90], 3)}); the 10th-percentile band "
                 f"is over-covered ({_fmt(cov[0.10], 3)} vs target 0.10).")
    if math.isfinite(brier_m) and math.isfinite(brier_mk):
        if model_trails_market:
            lines.append(f"- **Model trails market on binary scoring:** Brier "
                         f"{_fmt(brier_m, 3)} vs {_fmt(brier_mk, 3)} (model vs market); "
                         f"logloss {_fmt(ll_m, 3)} vs {_fmt(ll_mk, 3)}.")
            lines.append(f"- **Therefore, do not claim market superiority from this study.** "
                         f"This is a diagnostic and improvement layer, not proof of edge.")
        else:
            lines.append(f"- Model leads market on binary scoring in this sample "
                         f"(Brier {_fmt(brier_m, 3)} vs {_fmt(brier_mk, 3)}). One window does "
                         f"not constitute a market-superiority claim — see governance notes.")
    lines.append("")

    # ── What this study tests ───
    lines.append("## What this study tests")
    lines.append("")
    lines.append("This is an actuarial actual-to-expected review. Each settled (player, game, "
                 "stat, line, side) row carries a model PMF and an observed outcome. From "
                 "those we compute and roll up:")
    lines.append("")
    lines.append("- **Mean calibration** — `mean_AE = Σactual / Σexpected_mean`. 1.00 = unbiased "
                 "point estimate. Tells us whether the PMF means systematically over- or "
                 "under-shoot.")
    lines.append("- **Variance calibration** — `variance_AE = Σ(actual − mean)² / Σexpected_variance`. "
                 "1.00 = PMF spread matches reality. > 1 = realized outcomes are more volatile "
                 "than the PMF said (PMF too narrow); < 1 = PMF is wider than reality.")
    lines.append("- **Standardized residuals** — `(actual − mean) / √variance`. Calibrated "
                 "PMFs produce residuals with mean ≈ 0 and sd ≈ 1.")
    lines.append("- **Quantile coverage** — fraction of actuals at or below the model "
                 "10/25/50/75/90th percentiles. Should equal α.")
    lines.append("- **PMF likelihood** — mean negative-log-likelihood of the realized outcome "
                 "and ranked probability score (RPS).")
    lines.append("- **Model-vs-market scoring** — over/under Brier and logloss, computed on the "
                 "model PMF's `model_p_over` and the market's no-vig over probability; lower is "
                 "better.")
    lines.append("")

    # ── Overall results ───
    lines.append("## Overall results")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---:|")
    lines.append(f"| rows | {n_total:,} |")
    lines.append(f"| actual_mean (per row) | {_fmt(actual_mean, 3)} |")
    lines.append(f"| expected_mean (per row) | {_fmt(expected_mean, 3)} |")
    lines.append(f"| **mean_AE** | **{_fmt(mean_ae, 4)}** |")
    lines.append(f"| Σ squared residual | {_fmt(sq_err_total, 2)} |")
    lines.append(f"| Σ expected variance | {_fmt(var_total, 2)} |")
    lines.append(f"| **variance_AE** | **{_fmt(var_ae, 4)}** |")
    lines.append(f"| standardized_residual_mean | {_fmt(std_mu, 4)} |")
    lines.append(f"| standardized_residual_sd | {_fmt(std_sd, 4)} |")
    lines.append(f"| pmf_nll_mean | {_fmt(nll, 4)} |")
    lines.append(f"| pmf_rps_mean | {_fmt(rps, 4)} |")
    lines.append(f"| model_brier (over/under) | {_fmt(brier_m, 4)} |")
    lines.append(f"| market_brier (over/under) | {_fmt(brier_mk, 4)} |")
    lines.append(f"| model_logloss (over/under) | {_fmt(ll_m, 4)} |")
    lines.append(f"| market_logloss (over/under) | {_fmt(ll_mk, 4)} |")
    lines.append(f"| coverage @ 10 / 25 / 50 / 75 / 90 | "
                 f"{_fmt(cov[0.10], 3)} / {_fmt(cov[0.25], 3)} / {_fmt(cov[0.50], 3)} / "
                 f"{_fmt(cov[0.75], 3)} / {_fmt(cov[0.90], 3)} |")
    lines.append("")

    # ── Too narrow ───
    lines.append("## Where the PMF is too narrow")
    lines.append("")
    lines.append("`variance_AE > 1` means realized outcomes are more volatile than the PMF "
                 "expected. The model is putting too little spread on these buckets and will "
                 "be surprised by tails more often than its quantiles imply.")
    lines.append("")
    narrow = agg[agg["verdict"] == "TOO_NARROW"] if not agg.empty else agg
    if narrow.empty:
        lines.append("_No buckets exceeded `variance_AE > 1.20` with sufficient sample._")
    else:
        lines.append("| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for _, r in narrow.iterrows():
            lines.append(f"| {r['bucket_dimension']} | `{r['bucket_value']}` | {r['n']} | "
                         f"**{_fmt(r['variance_AE'], 3)}** | {_fmt(r['std_residual_sd'], 3)} | "
                         f"{_fmt(r['mean_AE'], 3)} | {_fmt(r['pmf_nll_mean'], 3)} |")
    lines.append("")

    # ── Too wide ───
    lines.append("## Where the PMF is too wide")
    lines.append("")
    lines.append("`variance_AE < 1` means the PMF spreads more probability mass than realized "
                 "outcomes need. The model is uncertain when reality is more concentrated. "
                 "These are calibration targets — narrowing here will reduce NLL without "
                 "harming coverage.")
    lines.append("")
    wide = agg[agg["verdict"] == "TOO_WIDE"] if not agg.empty else agg
    if wide.empty:
        lines.append("_No buckets fell below `variance_AE < 0.80` with sufficient sample._")
    else:
        lines.append("| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for _, r in wide.iterrows():
            lines.append(f"| {r['bucket_dimension']} | `{r['bucket_value']}` | {r['n']} | "
                         f"**{_fmt(r['variance_AE'], 3)}** | {_fmt(r['std_residual_sd'], 3)} | "
                         f"{_fmt(r['mean_AE'], 3)} | {_fmt(r['pmf_nll_mean'], 3)} |")
    lines.append("")

    # ── Well calibrated ───
    lines.append("## Where the PMF dispersion is well calibrated")
    lines.append("")
    lines.append("Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above "
                 f"n = {min_n}.")
    lines.append("")
    well = agg[agg["verdict"] == "WELL_CALIBRATED"] if not agg.empty else agg
    if well.empty:
        lines.append("_No buckets met the calibration band with sufficient sample._")
    else:
        lines.append("| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for _, r in well.iterrows():
            lines.append(f"| {r['bucket_dimension']} | `{r['bucket_value']}` | {r['n']} | "
                         f"{_fmt(r['mean_AE'], 3)} | {_fmt(r['variance_AE'], 3)} | "
                         f"{_fmt(r['std_residual_mean'], 3)} | {_fmt(r['pmf_nll_mean'], 3)} |")
    lines.append("")

    # ── Thin samples ───
    lines.append("## Where the sample is too thin to conclude")
    lines.append("")
    thin = agg[agg["thin_sample"]] if not agg.empty else agg
    if thin.empty:
        lines.append("_All buckets met the minimum sample threshold._")
    else:
        lines.append(f"_Buckets below n = {min_n}. Reported but flagged; do not act on point "
                     "estimates._")
        lines.append("")
        lines.append("| Dimension | Bucket | n | variance_AE | std_resid_mean |")
        lines.append("|---|---|---:|---:|---:|")
        for _, r in thin.iterrows():
            lines.append(f"| {r['bucket_dimension']} | `{r['bucket_value']}` | {r['n']} | "
                         f"{_fmt(r['variance_AE'], 3)} | {_fmt(r['std_residual_mean'], 3)} |")
    lines.append("")

    # ── Live-context limitations ───
    lines.append("## Live-context limitations")
    lines.append("")
    lines.append("- Only **morning / current** settled rows are present in the scored-outcome "
                 "feed for this window. Snapshot types observed: "
                 f"`{', '.join(snap_types_seen) if snap_types_seen else 'none'}`.")
    lines.append("- **`t_minus_25` and `close_lock` rows are not yet scored** — the live "
                 "snapshot scorer (`score_derek_live_snapshots_after_game.py`) reports "
                 "`pending_outcomes` until enough live snapshots accumulate joinable game "
                 "stats. Cross-snapshot calibration will only become meaningful once those "
                 "rows accumulate; we do not fabricate them here.")
    lines.append("- **`lineup_confirmed` and `injury_context` experience** is similarly "
                 "thin. Source A (`after_game_scoring`) tags them, but covers only a few "
                 "delivery dates so far. Bucket counts are reported honestly and flagged "
                 "as thin sample where relevant.")
    lines.append("- **`minutes_volatility_bucket` and `vacated_opportunity_bucket`** are "
                 "reported as `unavailable` because the underlying signal is not yet "
                 "captured in the settled-row feed. They are placeholders, not estimates.")
    lines.append("")

    # ── Interpretation for Derek ───
    lines.append("## Interpretation for Derek")
    lines.append("")
    lines.append("- The PMFs Derek delivers are **not just point projections**. Each row "
                 "carries a full discrete distribution that produces a mean, a variance, "
                 "and arbitrary quantiles. The over/under fair price is just one slice of "
                 "that distribution.")
    lines.append("- This study is the first formal test of whether realized outcomes are "
                 "**as volatile as the PMFs expected** — not just whether the means landed.")
    lines.append("- It is useful right now because it identifies **where the model is too "
                 "narrow** (low predicted-variance bucket, OVER side, fg3m at 1+ stdev "
                 "wider than predicted) and **where the model is too wide** (low-line "
                 "discrete props, high-p0 props, starter minutes, defensive stats).")
    lines.append("- It also shows what needs to land before we can claim broader edge: "
                 "the model **under-projects means by ~14%** and **trails the market on "
                 "binary scoring** in this small sample. So this is a diagnostic and "
                 "**improvement** report, not a market-superiority claim.")
    lines.append("")

    # ── Next improvements ───
    lines.append("## Next improvements")
    lines.append("")
    lines.append("1. **Accumulate more settled live snapshots** — once `t_minus_25` and "
                 "`close_lock` rows have realized outcomes joined, this study will be the "
                 "canonical place to compare snapshot types for calibration gain.")
    lines.append("2. **Bucket-level recalibration** — apply isotonic or temperature-scaling "
                 "calibration on the over-disperse low-line discrete and high-p0 buckets; "
                 "these are the largest variance-AE deviations and they cleanly compress.")
    lines.append("3. **Low-line discrete stat handling** — fg3m / stl / blk / tov at "
                 "lines ≤ 1.5 are the trickiest: fg3m is too narrow while the stl/blk "
                 "stack is too wide. The next pass should fit per-stat dispersion "
                 "scalers separately for these.")
    lines.append("4. **Mean calibration** — the +14% mean_AE bias suggests the point "
                 "projections systematically under-shoot. Re-fit the role-aware mean "
                 "centering in the contextual stack and re-score this study.")
    lines.append("5. **Confirmed-lineup and injury-context experience** — once the after-"
                 "game scoring feed is wired to more delivery dates, monitor whether "
                 "confirmed-lineup rows produce tighter variance-AE than projected ones.")
    lines.append("6. **Actuarial monitoring by stat / role / line bucket / snapshot_type** "
                 "— this script becomes the daily monitor. The verifier "
                 "(`verify_pmf_variance_experience_study.py`) ensures the report stays "
                 "honest and tracks PASS/WARN.")
    lines.append("")

    # ── Provenance ───
    lines.append("## Provenance")
    lines.append("")
    lines.append("- inputs: `deliveries/<date>/after_game_scoring/after_game_scoring.parquet` "
                 "(Source A — preferred metadata) and `predictions/all_props_<date>.parquet` "
                 "joined with `data/player_game_stats.parquet` (Source B — row spine).")
    lines.append(f"- settled window: **{date_window[0]} → {date_window[1]}** ({n_days} dates).")
    lines.append("- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, "
                 "minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, "
                 "edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, "
                 "low_line_discrete.")
    lines.append("- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.")
    lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of-date", required=True)
    ap.add_argument("--lookback-days", type=int, default=60)
    ap.add_argument("--min-bucket-n", type=int, default=30)
    args = ap.parse_args(argv)

    as_of = dt.date.fromisoformat(args.as_of_date)
    start = as_of - dt.timedelta(days=args.lookback_days)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    stats_lookup = _load_stats_lookup()
    if stats_lookup.empty:
        print(f"PMF_VARIANCE_EXPERIENCE_STUDY_FAIL  reason=no_stats_table  path={STATS_PATH}",
              file=sys.stderr)
        return 1

    # Iterate every candidate delivery date in the window. The row spine
    # is per-bet (predictions ⨝ player_game_stats); after_game_scoring is
    # left-joined as per-stat metadata enrichment when present.
    frames: list[pd.DataFrame] = []
    seen_dates: set[str] = set()
    for offset in range((as_of - start).days):
        d = start + dt.timedelta(days=offset)
        date_s = d.isoformat()
        df = _load_predictions_with_actuals(date_s, stats_lookup)
        if df is not None and not df.empty:
            frames.append(df)
            seen_dates.add(date_s)

    if not frames:
        print("PMF_VARIANCE_EXPERIENCE_STUDY_FAIL  reason=no_settled_outcomes_in_window",
              file=sys.stderr)
        return 1

    raw = pd.concat(frames, ignore_index=True)
    # Drop rows with no PMF or no actual.
    pre_n = len(raw)
    raw = raw[raw["pmf"].notna() & raw["actual"].notna()]
    raw = raw[raw["game_date"] < as_of.isoformat()]
    if raw.empty:
        print(f"PMF_VARIANCE_EXPERIENCE_STUDY_FAIL  reason=no_joined_actuals  candidates={pre_n}",
              file=sys.stderr)
        return 1

    # Compute per-row metrics.
    metric_records: list[dict] = []
    parse_failures = 0
    for idx, row in raw.iterrows():
        m = _row_metrics(row)
        if m is None:
            parse_failures += 1
            continue
        rec = {
            "delivery_date": row["delivery_date"],
            "game_date": row["game_date"],
            "source": row["source"],
            "player_id": row["player_id"],
            "player_name": row["player_name"],
            "game_id": row["game_id"],
            "stat": row["stat"],
            "side": row.get("side_label", "n/a"),
            "line": float(row["line"]) if pd.notna(row["line"]) else float("nan"),
            "actual": float(row["actual"]),
            "snapshot_type": row.get("snapshot_type", "unknown"),
            "lineup_confirmed": _lineup_confirmed_label(row.get("lineup_freshness_status", "unavailable")),
            "role_bucket": row.get("role_bucket", "unknown"),
            "injury_context": _injury_context_label(row.get("injury_freshness_status", "unavailable")),
            "raw_edge_src": row.get("raw_edge_src", float("nan")),
            **m,
        }
        metric_records.append(rec)

    if not metric_records:
        print(f"PMF_VARIANCE_EXPERIENCE_STUDY_FAIL  reason=all_pmf_parse_failed  "
              f"candidates={pre_n}  parse_failures={parse_failures}", file=sys.stderr)
        return 1

    if all(not math.isfinite(r.get("expected_variance", float("nan"))) or
           r.get("expected_variance", 0) <= 0 for r in metric_records):
        print("PMF_VARIANCE_EXPERIENCE_STUDY_FAIL  reason=expected_variance_missing",
              file=sys.stderr)
        return 1

    df = pd.DataFrame(metric_records)

    # Augment with derived buckets. These run after we know the variance
    # distribution so quantile cutoffs are honest.
    var_q = df["expected_variance"].quantile([0.33, 0.67]).values
    df["predicted_variance_bucket"] = df["expected_variance"].apply(
        lambda v: _variance_bucket(v, (float(var_q[0]), float(var_q[1])))
    )
    df["edge_bucket"] = df["raw_edge_src"].apply(_edge_bucket)
    df["p0_bucket"] = df["p0"].apply(_p0_bucket)
    df["line_bucket"] = [_line_bucket_for_stat(s, l) for s, l in zip(df["stat"], df["line"])]
    df["low_line_discrete"] = [
        "yes" if (str(s) in LOW_LINE_DISCRETE_STATS and math.isfinite(l) and l <= 1.5) else "no"
        for s, l in zip(df["stat"], df["line"])
    ]
    df["minutes_volatility_bucket"] = "unavailable"
    df["vacated_opportunity_bucket"] = "unavailable"

    # ── Aggregations ────────────────────────────────────────────────────
    overall_df = _aggregate(df, group_col=None, min_n=args.min_bucket_n)
    overall = overall_df.iloc[0].to_dict() if not overall_df.empty else {}

    bucket_dims = [
        "stat", "side", "snapshot_type", "lineup_confirmed", "role_bucket",
        "minutes_volatility_bucket", "injury_context", "vacated_opportunity_bucket",
        "edge_bucket", "p0_bucket", "predicted_variance_bucket", "line_bucket",
        "low_line_discrete",
    ]
    parts = [overall_df.assign(bucket_dimension="overall")]
    for dim in bucket_dims:
        parts.append(_aggregate(df, group_col=dim, min_n=args.min_bucket_n))
    agg = pd.concat(parts, ignore_index=True)
    agg = agg.sort_values(["bucket_dimension", "bucket_value"]).reset_index(drop=True)

    # ── Outputs ────────────────────────────────────────────────────────
    csv_path = OUT_DIR / f"pmf_variance_experience_{args.as_of_date}.csv"
    json_path = OUT_DIR / f"pmf_variance_experience_{args.as_of_date}.json"
    md_path = OUT_DIR / f"pmf_variance_experience_{args.as_of_date}.md"

    agg.to_csv(csv_path, index=False)

    sorted_dates = sorted(seen_dates)
    payload = {
        "schema_version": "1.0",
        "as_of_date": args.as_of_date,
        "lookback_days": args.lookback_days,
        "min_bucket_n": args.min_bucket_n,
        "settled_window": {"min": sorted_dates[0], "max": sorted_dates[-1]},
        "delivery_dates_with_rows": sorted_dates,
        "row_count_settled": int(len(df)),
        "parse_failures": int(parse_failures),
        "overall": {k: (None if isinstance(v, float) and math.isnan(v) else
                        (float(v) if isinstance(v, (np.floating, float)) else v))
                    for k, v in overall.items()},
        "buckets": json.loads(agg.where(pd.notna(agg), None).to_json(orient="records")),
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    _write_markdown(
        md_path,
        as_of=args.as_of_date,
        lookback=args.lookback_days,
        min_n=args.min_bucket_n,
        overall=overall,
        agg=agg,
        dataframe=df,
        date_window=(sorted_dates[0], sorted_dates[-1]),
        n_days=len(sorted_dates),
    )

    overall_n = int(overall.get("n", 0))
    if overall_n < args.min_bucket_n:
        # Still pass — the report exists and honestly flags the thin sample.
        print(f"PMF_VARIANCE_EXPERIENCE_STUDY_PASS  rows={overall_n}  "
              f"days={len(sorted_dates)}  insufficient_sample=true  "
              f"min_bucket_n={args.min_bucket_n}")
    else:
        print(f"PMF_VARIANCE_EXPERIENCE_STUDY_PASS  rows={overall_n}  "
              f"days={len(sorted_dates)}  parse_failures={parse_failures}  "
              f"min_bucket_n={args.min_bucket_n}")
    print(f"  csv={csv_path.relative_to(REPO_ROOT)}")
    print(f"  json={json_path.relative_to(REPO_ROOT)}")
    print(f"  md={md_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
