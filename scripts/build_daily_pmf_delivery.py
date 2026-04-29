"""Build the daily PMF delivery: Derek review package + Wizard of Odds package.

This is the single orchestrator for a delivery run on a given calendar
date. It does NOT recompute PMFs — it consumes the canonical model-only
PMF parquet that the production prediction pipeline already wrote, joins
optional Odds-API snapshots, and emits both deliverables described in
`docs/daily_pmf_delivery_spec.md`.

The current production model is Phase 10C (commit `b7949ed`). Phase 10D
and Phase 10D.2 TOV overlays did NOT pass independent validation and are
intentionally not consumed here — see
`docs/phase11_tov_structural_refit_plan.md`.

Usage
-----
    python scripts/build_daily_pmf_delivery.py \
        --date 2026-04-27 \
        --snapshot morning \
        [--predictions predictions/all_props_2026-04-27.parquet] \
        [--model-only deliveries/2026-04-27/live_after_2029_et/player_prop_pmfs_tonight_MODEL_ONLY.parquet] \
        [--odds-snapshot data/odds_api/processed/2026-04-27/odds_pairs_*.parquet] \
        [--no-odds-fetch]

Inputs (any of which the orchestrator may discover automatically):
  - The canonical MODEL_ONLY parquet emitted by the prediction pipeline
    (preferred), OR
  - A `predictions/all_props_{date}.parquet` (the orchestrator will run
    `scripts/export_live_pmf_slate.py` if that script's output is missing).
  - Optional Odds-API snapshot under `data/odds_api/processed/{date}/`.

Outputs:
  deliveries/{date}/pmf_model_review_package/
  deliveries/{date}/wizard_of_odds/
  deliveries/{date}/wizard_of_odds/run_manifest.json

Hard rules:
  - The model-only PMF is canonical. No market anchoring is applied.
  - Sparse / missing market does not drop a row.
  - Every emitted row carries the full schema in §2 of the delivery spec,
    including `tov_status="current_phase8"`.
  - Runner-side validation gates §7 are checked before writing
    `publishable_edges.*`.

This script makes no Odds-API call when ODDS_API_KEY is unset; in that
case `market_*` columns are null and `market_coverage_status="none"`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
warnings.filterwarnings("ignore")

# ── Constants pinned to the delivery spec ────────────────────────────────

SUPPORTED_STATS = ("pts", "reb", "ast", "tov", "fg3m")
ROLE_ORDER = ("inactive_risk", "fringe", "bench", "rotation", "core", "starter")
HIGH_CONF_ROLES = ("starter", "core", "rotation")
MED_CONF_ROLES = ("bench", "fringe")
LOW_CONF_ROLES = ("inactive_risk",)

P_GE_LADDER = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
PMF_VALID_OK = "ok"
TOV_STATUS_CURRENT = "current_phase8"
TOV_STATUS_REASON = ("Phase 10D/10D.2 overlay failed independent validation; "
                      "see docs/phase11_tov_structural_refit_plan.md")

CANONICAL_COLUMNS_BASE = [
    "player_name", "player_id", "team", "opponent", "is_home",
    "game_id", "game_start_time", "stat",
    "line", "book",
    "market_over_odds", "market_under_odds", "market_no_vig_over_prob",
    "pmf_source", "calibration_source", "role_bucket",
    "mean", "median", "mode", "p0",
    *[f"p_ge_{k}" for k in P_GE_LADDER],
    "model_p_over", "fair_over_odds_american", "fair_under_odds_american",
    "edge",
    "snapshot_type", "snapshot_time_utc",
    "model_version", "pipeline_run_id",
    "pmf_valid", "pmf_sum_error", "calibration_confidence",
    "market_coverage_status", "tov_status",
    "injury_freshness_status", "lineup_freshness_status",
]
# Columns that carry the full untruncated PMF so consumers can reconstruct
# exactly for stats whose support exceeds 20 (e.g. points). These are added
# to per-(player,stat) wide tables only — not to per-line tables.
WIDE_ONLY_COLUMNS = ["pmf_json"]


# ── Provenance ────────────────────────────────────────────────────────────


def _git_sha_short() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT), text=True, stderr=subprocess.DEVNULL).strip()
        return out
    except Exception:
        return "unknown"


def _model_version_string() -> str:
    return f"{_git_sha_short()}#phase10c"


def _file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_mtime_iso_utc(path: Path) -> str | None:
    if not path.exists():
        return None
    return (datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            .isoformat().replace("+00:00", "Z"))


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ── PMF math helpers ─────────────────────────────────────────────────────


def _pmf_to_array(pmf_obj, max_k: int = 21) -> np.ndarray:
    """Coerce a `pmf_json` cell or a list/ndarray to an ndarray of length
    >= max_k. Missing tail entries are zero-padded."""
    if isinstance(pmf_obj, str):
        try:
            d = json.loads(pmf_obj)
        except Exception:
            return np.zeros(max_k, dtype=float)
        if isinstance(d, dict):
            keys = [int(k) for k in d.keys()]
            K = max(keys) + 1 if keys else max_k
            a = np.zeros(max(K, max_k), dtype=float)
            for k, v in d.items():
                a[int(k)] = float(v)
            return a
        if isinstance(d, list):
            a = np.asarray(d, dtype=float)
        else:
            a = np.zeros(max_k, dtype=float)
    elif isinstance(pmf_obj, (list, tuple, np.ndarray)):
        a = np.asarray(pmf_obj, dtype=float).ravel()
    else:
        a = np.zeros(max_k, dtype=float)
    if len(a) < max_k:
        a = np.concatenate([a, np.zeros(max_k - len(a), dtype=float)])
    return a


def _pmf_summary(pmf_arr: np.ndarray) -> dict:
    arr = np.clip(pmf_arr, 0.0, None)
    s = arr.sum()
    pmf_sum_error = float(abs(s - 1.0))
    if s > 0 and np.isfinite(s):
        norm = arr / s
    else:
        norm = arr
    K = len(norm)
    ks = np.arange(K, dtype=float)
    mean = float((norm * ks).sum())
    cdf = np.cumsum(norm)
    median = int(np.searchsorted(cdf, 0.5))
    mode = int(np.argmax(norm))
    p0 = float(norm[0]) if K > 0 else float("nan")
    p_ge = {k: float(norm[k:].sum()) if k < K else 0.0 for k in P_GE_LADDER}
    finite = bool(np.all(np.isfinite(arr)))
    nonneg = bool(np.all(arr >= -1e-9))
    sum_ok = pmf_sum_error <= 1e-6 or pmf_sum_error <= 1e-6 + 1e-12
    if not finite:
        valid = "non_finite"
    elif not nonneg:
        valid = "negative_prob"
    elif not sum_ok:
        valid = "bad_shape"
    else:
        valid = PMF_VALID_OK
    out = {"mean": mean, "median": median, "mode": mode, "p0": p0,
           "pmf_valid": valid, "pmf_sum_error": pmf_sum_error}
    out.update({f"p_ge_{k}": v for k, v in p_ge.items()})
    return out


def _model_p_over_line(pmf_arr: np.ndarray, line: float | None) -> float | None:
    if line is None or not np.isfinite(line):
        return None
    arr = np.clip(pmf_arr, 0.0, None)
    s = arr.sum()
    if s <= 0 or not np.isfinite(s):
        return None
    arr = arr / s
    K = len(arr)
    ks = np.arange(K)
    p_over = float(arr[ks > line].sum())
    p_under = float(arr[ks < line].sum())
    denom = p_over + p_under
    if denom <= 0:
        return None
    return float(min(1.0, max(0.0, p_over / denom)))


def _prob_to_american(p: float | None) -> int | None:
    if p is None or not np.isfinite(p) or p <= 0.0 or p >= 1.0:
        return None
    if p >= 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def _calibration_confidence(role: str | None) -> str:
    if role in HIGH_CONF_ROLES:
        return "high"
    if role in MED_CONF_ROLES:
        return "medium"
    return "low"


# ── Source discovery ─────────────────────────────────────────────────────


def _find_model_only_parquet(date: str) -> Path | None:
    """Locate the canonical MODEL_ONLY parquet emitted by the prediction
    export. The legacy daily export uses
    `deliveries/{date}/live_after_2029_et/...` and recent ones may use
    additional named subfolders. We scan the per-date delivery folder."""
    base = REPO_ROOT / "deliveries" / date
    if not base.exists():
        return None
    candidates = sorted(base.rglob("player_prop_pmfs_tonight_MODEL_ONLY.parquet"))
    return candidates[-1] if candidates else None


def _find_odds_snapshot(date: str) -> Path | None:
    base = REPO_ROOT / "data" / "odds_api" / "processed" / date
    if not base.exists():
        return None
    pairs = sorted(base.glob("odds_pairs_*.parquet"))
    return pairs[-1] if pairs else None


def _injury_freshness(path: Path | None) -> str:
    if path is None or not path.exists():
        return "unknown"
    age_h = (datetime.now(timezone.utc).timestamp() - path.stat().st_mtime) / 3600.0
    if age_h <= 3.0:
        return "fresh"
    if age_h <= 12.0:
        return "stale"
    return "very_stale"


def _lineup_freshness_for_row(row: pd.Series) -> str:
    src = str(row.get("role_source") or "").lower()
    if "confirmed" in src:
        return "confirmed"
    if "projected" in src or "minutes_distribution" in src:
        return "projected"
    return "unknown"


def _market_coverage_status(books_seen: list[str]) -> str:
    n = len(books_seen)
    if n == 0:
        return "none"
    if n == 1:
        return "sparse"
    if n < 4:
        return "partial"
    return "full"


# ── Loaders ───────────────────────────────────────────────────────────────


def load_model_only(parquet_path: Path) -> pd.DataFrame:
    if not parquet_path.exists():
        raise SystemExit(f"MODEL_ONLY parquet missing: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    if "pmf_json" not in df.columns and "pmf_active" in df.columns:
        df = df.rename(columns={"pmf_active": "pmf_json"})
    if "pmf_json" not in df.columns:
        raise SystemExit("MODEL_ONLY parquet missing pmf_json")
    return df


def load_odds_snapshot(parquet_path: Path | None) -> pd.DataFrame:
    if parquet_path is None or not parquet_path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(parquet_path)
    if "market_stat" in df.columns:
        df = df[df["market_stat"].astype(str).isin(SUPPORTED_STATS)]
    return df


# ── Build canonical row frame from MODEL_ONLY ───────────────────────────


def build_canonical_rows(model_only: pd.DataFrame, *,
                          delivery_date: str, snapshot_type: str,
                          snapshot_time_utc: str, model_version: str,
                          pipeline_run_id: str,
                          injury_path: Path | None) -> pd.DataFrame:
    """Per (player, stat) one row with full PMF summary + provenance. The
    line/book/market fields are null at this stage; market join lands them."""
    rows = []
    inj_fresh = _injury_freshness(injury_path)
    for _, r in model_only.iterrows():
        pmf = _pmf_to_array(r.get("pmf_json"))
        smry = _pmf_summary(pmf)
        role = r.get("role_bucket")
        # Serialize the (already normalized) full PMF as a JSON dict so
        # consumers can reconstruct exactly even for stats with support > 20.
        s = float(pmf.sum())
        norm = pmf / s if s > 0 else pmf
        pmf_json_str = json.dumps({str(k): float(v) for k, v in enumerate(norm)
                                    if v > 0.0})
        rows.append({
            "pmf_json": pmf_json_str,
            "player_name": r.get("player_name"),
            "player_id": (int(r.get("player_id"))
                          if pd.notna(r.get("player_id")) else None),
            "team": r.get("team_abbr") or r.get("team"),
            "opponent": r.get("opponent"),
            "is_home": (bool(r.get("is_home"))
                        if pd.notna(r.get("is_home")) else None),
            "game_id": (int(r.get("game_id"))
                        if pd.notna(r.get("game_id")) else None),
            "game_start_time": r.get("game_start_et") or r.get("game_start_time"),
            "stat": r.get("stat"),
            "line": None, "book": None,
            "market_over_odds": None, "market_under_odds": None,
            "market_no_vig_over_prob": None,
            "pmf_source": (r.get("pmf_source")
                           or "phase10c_role_aware_active_conditioned"),
            "calibration_source": "phase8_role_aware_pmf_cal_v2",
            "role_bucket": role,
            "mean": smry["mean"], "median": smry["median"],
            "mode": smry["mode"], "p0": smry["p0"],
            **{f"p_ge_{k}": smry[f"p_ge_{k}"] for k in P_GE_LADDER},
            "model_p_over": None,
            "fair_over_odds_american": None, "fair_under_odds_american": None,
            "edge": None,
            "snapshot_type": snapshot_type,
            "snapshot_time_utc": snapshot_time_utc,
            "model_version": model_version,
            "pipeline_run_id": pipeline_run_id,
            "pmf_valid": smry["pmf_valid"],
            "pmf_sum_error": smry["pmf_sum_error"],
            "calibration_confidence": _calibration_confidence(role),
            "market_coverage_status": "none",
            "tov_status": TOV_STATUS_CURRENT,
            "injury_freshness_status": inj_fresh,
            "lineup_freshness_status": _lineup_freshness_for_row(r),
            "_pmf_arr": pmf,
        })
    df = pd.DataFrame(rows)
    return df


# ── Fair odds board (line grid) ──────────────────────────────────────────


def _line_grid_for_stat(stat: str) -> Iterable[float]:
    """Default line grid for fair-odds publishing when no book offers a line."""
    if stat == "pts":
        return [v + 0.5 for v in range(0, 60)]
    if stat == "reb":
        return [v + 0.5 for v in range(0, 22)]
    if stat == "ast":
        return [v + 0.5 for v in range(0, 18)]
    if stat == "tov":
        return [v + 0.5 for v in range(0, 8)]
    if stat == "fg3m":
        return [v + 0.5 for v in range(0, 9)]
    return [v + 0.5 for v in range(0, 20)]


def build_fair_odds_board(canonical: pd.DataFrame) -> pd.DataFrame:
    """One row per (player, stat, line) over a default line grid.
    Independent of any book — `book=null` everywhere."""
    rows = []
    for _, r in canonical.iterrows():
        pmf = r["_pmf_arr"]
        for line in _line_grid_for_stat(r["stat"]):
            p_over = _model_p_over_line(pmf, line)
            row = {c: r[c] for c in CANONICAL_COLUMNS_BASE if c in r.index}
            row["line"] = float(line)
            row["book"] = None
            row["market_over_odds"] = None
            row["market_under_odds"] = None
            row["market_no_vig_over_prob"] = None
            row["model_p_over"] = p_over
            row["fair_over_odds_american"] = _prob_to_american(p_over)
            row["fair_under_odds_american"] = _prob_to_american(
                1.0 - p_over) if p_over is not None else None
            row["edge"] = None
            rows.append(row)
    if not rows:
        return pd.DataFrame(columns=CANONICAL_COLUMNS_BASE)
    return pd.DataFrame(rows)[CANONICAL_COLUMNS_BASE]


# ── Market comparison (model joined to book offered lines) ──────────────


def build_market_comparison(canonical: pd.DataFrame, odds: pd.DataFrame
                              ) -> tuple[pd.DataFrame, list[str]]:
    if odds.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS_BASE), []

    needed = {"market_stat", "line", "bookmaker_key", "no_vig_over_prob",
              "over_price", "under_price"}
    missing = needed - set(odds.columns)
    if missing:
        # Tolerant: if the snapshot lacks expected columns, fall back to none.
        return pd.DataFrame(columns=CANONICAL_COLUMNS_BASE), []

    # Normalize player name to match canonical's player_name.
    odds = odds.copy()
    odds["__norm_player__"] = (odds.get("player_name", "")
                                .astype(str).str.lower().str.strip())
    canon = canonical.copy()
    canon["__norm_player__"] = canon["player_name"].astype(str).str.lower().str.strip()

    rows = []
    books_seen: set[str] = set()
    for _, c in canon.iterrows():
        sub = odds[(odds["__norm_player__"] == c["__norm_player__"])
                   & (odds["market_stat"].astype(str) == c["stat"])]
        for _, m in sub.iterrows():
            line = float(m["line"]) if pd.notna(m["line"]) else None
            if line is None:
                continue
            book = str(m["bookmaker_key"])
            books_seen.add(book)
            no_vig = (float(m["no_vig_over_prob"])
                       if pd.notna(m["no_vig_over_prob"]) else None)
            p_over = _model_p_over_line(c["_pmf_arr"], line)
            row = {col: c[col] for col in CANONICAL_COLUMNS_BASE if col in c.index}
            row["line"] = line
            row["book"] = book
            row["market_over_odds"] = (int(m["over_price"])
                                         if pd.notna(m["over_price"]) else None)
            row["market_under_odds"] = (int(m["under_price"])
                                          if pd.notna(m["under_price"]) else None)
            row["market_no_vig_over_prob"] = no_vig
            row["model_p_over"] = p_over
            row["fair_over_odds_american"] = _prob_to_american(p_over)
            row["fair_under_odds_american"] = _prob_to_american(
                1.0 - p_over) if p_over is not None else None
            row["edge"] = ((p_over - no_vig)
                           if (p_over is not None and no_vig is not None)
                           else None)
            rows.append(row)
    if not rows:
        return pd.DataFrame(columns=CANONICAL_COLUMNS_BASE), sorted(books_seen)
    df = pd.DataFrame(rows)[CANONICAL_COLUMNS_BASE]
    return df, sorted(books_seen)


def build_publishable_edges(market_comparison: pd.DataFrame, *,
                              edge_threshold: float = 0.04
                              ) -> pd.DataFrame:
    if market_comparison.empty:
        return market_comparison
    df = market_comparison.copy()
    cond = (df["edge"].abs() >= edge_threshold) & df["edge"].notna()
    cond = cond & (df["pmf_valid"] == PMF_VALID_OK)
    cond = cond & (df["snapshot_type"].isin(["morning", "pre_close"]))
    return df[cond].reset_index(drop=True)


# ── Outcome-level long format ────────────────────────────────────────────


def build_outcome_level(canonical: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in canonical.iterrows():
        pmf = r["_pmf_arr"]
        for k, p in enumerate(pmf):
            row = {col: r[col] for col in
                   ("player_name", "player_id", "team", "opponent", "is_home",
                    "game_id", "game_start_time", "stat", "role_bucket",
                    "pmf_source", "calibration_source",
                    "snapshot_type", "snapshot_time_utc",
                    "model_version", "pipeline_run_id",
                    "pmf_valid", "pmf_sum_error", "calibration_confidence",
                    "market_coverage_status", "tov_status",
                    "injury_freshness_status", "lineup_freshness_status")
                   if col in r.index}
            row["k"] = int(k)
            row["p_k"] = float(p)
            rows.append(row)
    return pd.DataFrame(rows)


# ── Validation gates ─────────────────────────────────────────────────────


def runner_validation_gates(df: pd.DataFrame, *, snapshot_type: str
                              ) -> tuple[bool, list[str]]:
    msgs: list[str] = []
    if df.empty:
        return True, msgs
    p_cols = [f"p_ge_{k}" for k in P_GE_LADDER]
    for c in ("p0", *p_cols):
        if c not in df.columns:
            msgs.append(f"missing column {c}")
    if "pmf_sum_error" in df.columns and (df["pmf_sum_error"].abs() > 1e-6).any():
        bad = int((df["pmf_sum_error"].abs() > 1e-6).sum())
        msgs.append(f"G_PMF_SUM violations: {bad} rows |Σp - 1| > 1e-6")
    if "pmf_valid" in df.columns and (df["pmf_valid"] != PMF_VALID_OK).any():
        bad = int((df["pmf_valid"] != PMF_VALID_OK).sum())
        msgs.append(f"G_PMF_NONNEG/G_PMF_FINITE violations: {bad} rows")
    for col in ("model_version", "pipeline_run_id"):
        if col not in df.columns or df[col].isna().any():
            msgs.append(f"G_PROVENANCE: column {col} has nulls")
    if "tov_status" in df.columns:
        tov_rows = df[df["stat"] == "tov"]
        if not tov_rows.empty and (tov_rows["tov_status"]
                                   != TOV_STATUS_CURRENT).any():
            msgs.append("G_TOV_OVERLAY_OFF: a TOV row has overlay status != current_phase8")
    if (snapshot_type != "after_game" and "snapshot_time_utc" in df.columns
            and "game_start_time" in df.columns):
        try:
            ssu = pd.to_datetime(df["snapshot_time_utc"], utc=True, errors="coerce")
            gst = pd.to_datetime(df["game_start_time"], utc=True, errors="coerce")
            bad = int(((ssu >= gst) & ssu.notna() & gst.notna()).sum())
            if bad:
                msgs.append(f"G_LEAKAGE: {bad} rows where snapshot >= game_start_time")
        except Exception as e:
            msgs.append(f"G_LEAKAGE check skipped: {e}")
    return (len(msgs) == 0), msgs


# ── Writers ──────────────────────────────────────────────────────────────


def _drop_pmf_arr(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in df.columns if c.startswith("_")],
                   errors="ignore")


def _write_csv_parquet(df: pd.DataFrame, base: Path) -> None:
    """Parquet keeps full numeric precision; CSV rounds for readability."""
    base.parent.mkdir(parents=True, exist_ok=True)
    df = _drop_pmf_arr(df)
    df.to_parquet(base.with_suffix(".parquet"), index=False)
    _csv_round(df).to_csv(base.with_suffix(".csv"), index=False)


def _write_jsonl(df: pd.DataFrame, base: Path) -> None:
    base.parent.mkdir(parents=True, exist_ok=True)
    df = _drop_pmf_arr(df)
    df.to_json(base.with_suffix(".jsonl"), orient="records", lines=True)


def _csv_round(df: pd.DataFrame) -> pd.DataFrame:
    """Round float columns for CSV output only. Probability/PMF columns get
    12 decimals (preserves down to 10⁻¹²); summary stats get 6 decimals."""
    out = df.copy()
    pmf_cols = (["p0", *(f"p_ge_{k}" for k in P_GE_LADDER), "p_k",
                  "model_p_over", "market_no_vig_over_prob", "edge",
                  "pmf_sum_error"])
    for c in out.columns:
        if not pd.api.types.is_float_dtype(out[c]):
            continue
        if c in pmf_cols:
            out[c] = out[c].round(12)
        else:
            out[c] = out[c].round(6)
    return out


# ── Derek package writer ─────────────────────────────────────────────────


def write_derek_package(canonical: pd.DataFrame,
                          outcome_long: pd.DataFrame, *,
                          delivery_date: str, pkg_dir: Path,
                          model_only_path: Path | None) -> None:
    """Layout per spec §1.1. The Derek package mirrors the canonical
    model-only PMF (no market joins). HTML viewers are placeholders here;
    the existing `scripts/build_pmf_review_package.py` produces the rich
    HTML for the previously-shipped late-slate package and is the model we
    align to."""
    pkg_dir.mkdir(parents=True, exist_ok=True)
    machine = pkg_dir / "machine_readable"
    machine.mkdir(parents=True, exist_ok=True)

    canon_clean = _drop_pmf_arr(canonical)
    # Parquet keeps full numeric precision; CSV is rounded for readability.
    canon_clean.to_parquet(machine / "model_only.parquet", index=False)
    canon_clean.to_json(machine / "model_only.jsonl",
                          orient="records", lines=True)
    _csv_round(canon_clean).to_csv(machine / "model_only.csv", index=False)

    # Numbered review files at package root.
    summary_cols = [c for c in CANONICAL_COLUMNS_BASE
                    if c in canon_clean.columns
                    and not c.startswith("p_ge_")]
    canon_clean[summary_cols].to_parquet(pkg_dir / "04_PROP_SUMMARY.parquet",
                                            index=False)
    _csv_round(canon_clean[summary_cols]).to_csv(pkg_dir / "04_PROP_SUMMARY.csv",
                                                    index=False)
    canon_clean.to_parquet(pkg_dir / "05_FULL_PMF_WIDE.parquet", index=False)
    _csv_round(canon_clean).to_csv(pkg_dir / "05_FULL_PMF_WIDE.csv", index=False)
    outcome_long.to_parquet(pkg_dir / "06_OUTCOME_LEVEL_PROBABILITIES.parquet",
                              index=False)
    _csv_round(outcome_long).to_csv(
        pkg_dir / "06_OUTCOME_LEVEL_PROBABILITIES.csv", index=False)

    _write_start_here(pkg_dir / "01_START_HERE.html",
                       delivery_date=delivery_date, n_rows=len(canon_clean))
    _write_overview(pkg_dir / "02_MODEL_REVIEW_OVERVIEW.html",
                     delivery_date=delivery_date, canonical=canon_clean,
                     model_only_path=model_only_path)
    _write_pmf_viewer(pkg_dir / "03_PMF_DISTRIBUTION_VIEWER.html",
                       canonical=canon_clean, delivery_date=delivery_date)

    (pkg_dir / "README.md").write_text(
        _readme_text(delivery_date=delivery_date, n_rows=len(canon_clean)))


_HTML_BASE_STYLE = """
body{font-family:system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#222}
h1{margin-top:0}h2{margin-top:1.6rem;border-bottom:1px solid #ccc;padding-bottom:0.2rem}
code{background:#f3f3f3;padding:0.1em 0.3em;border-radius:3px;font-size:0.95em}
.callout{background:#fff8d6;border-left:4px solid #d4a900;padding:0.6rem 1rem;margin:1rem 0}
.callout-warn{background:#ffe8e0;border-left:4px solid #c33;padding:0.6rem 1rem;margin:1rem 0}
.pmf-card{border:1px solid #ddd;border-radius:6px;padding:0.8rem 1rem;margin:0.8rem 0;background:#fafafa}
.pmf-head{display:flex;justify-content:space-between;font-weight:600}
.pmf-meta{color:#666;font-size:0.9em;margin:0.2rem 0 0.6rem}
.bars{display:flex;align-items:flex-end;gap:2px;height:90px;margin:0.4rem 0 0.2rem;background:#fff;border:1px solid #eee;padding:4px}
.bar{display:flex;flex-direction:column;align-items:center;min-width:14px;font-size:0.7em;color:#666}
.bar > .fill{background:#3b6;border-radius:1px 1px 0 0;width:100%}
.bar > .label{margin-top:2px}
table{border-collapse:collapse;margin:0.6rem 0}
th,td{padding:0.3rem 0.6rem;border:1px solid #ddd;text-align:left;font-size:0.92em}
th{background:#f0f0f0}
"""


def _readme_text(*, delivery_date: str, n_rows: int) -> str:
    return (
        f"# PMF Model Review Package — {delivery_date}\n\n"
        f"Generated by `scripts/build_daily_pmf_delivery.py`. "
        f"See `docs/daily_pmf_delivery_spec.md` for the row schema.\n\n"
        f"## What's in this package\n\n"
        f"- `01_START_HERE.html` — read first.\n"
        f"- `02_MODEL_REVIEW_OVERVIEW.html` — slate summary, model version, quality flags.\n"
        f"- `03_PMF_DISTRIBUTION_VIEWER.html` — visual histogram of every PMF.\n"
        f"- `04_PROP_SUMMARY.{{csv,parquet}}` — one row per (player, stat) with mean/median/mode/p0.\n"
        f"- `05_FULL_PMF_WIDE.{{csv,parquet}}` — `04_*` plus `pmf_json` and `p_ge_1 … p_ge_20`.\n"
        f"- `06_OUTCOME_LEVEL_PROBABILITIES.{{csv,parquet}}` — long form, one row per (player, stat, k).\n"
        f"- `machine_readable/` — exact same data, programmatic consumption.\n\n"
        f"Rows: **{n_rows}**.\n\n"
        f"## Hard guarantee — model-only, never anchored\n\n"
        f"PMFs in this package are the **canonical model-only PMFs**. They are "
        f"NOT market-anchored. No PMF probability has been adjusted to fit a "
        f"book line. Market data (when present at all) lives in the separate "
        f"Wizard of Odds package as a side-by-side reference; PMFs there are "
        f"identical to the PMFs here.\n\n"
        f"## TOV status\n\n"
        f"TOV PMFs (when emitted by the slate) are produced by the current "
        f"production Phase 8 calibrators. **No Phase 10D / 10D.2 TOV overlay "
        f"is applied** — those overlays did not pass independent validation. "
        f"See `docs/phase11_tov_structural_refit_plan.md` for the next move.\n"
    )


def _write_start_here(path: Path, *, delivery_date: str, n_rows: int) -> None:
    body = f"""
<p><b>Delivery date:</b> {delivery_date} &nbsp;&nbsp;
<b>Rows:</b> {n_rows}</p>

<div class="callout">
<b>Model-only, never anchored.</b> The PMFs in this package are the
canonical model output. No probability has been adjusted to fit any
book line. Market references live in a separate Wizard of Odds package.
</div>

<h2>How to view this package</h2>
<ol>
<li><b>02_MODEL_REVIEW_OVERVIEW.html</b> — opens in any browser. Shows the
slate, the model version, per-stat counts, and quality-flag rollup.</li>
<li><b>03_PMF_DISTRIBUTION_VIEWER.html</b> — opens in any browser. Renders
every PMF as a small histogram, grouped by stat. Use this to eyeball
shape, peak, and tail before consuming the numbers.</li>
<li><b>04_PROP_SUMMARY.csv</b> — opens in Excel / Google Sheets. One row
per (player, stat) with <code>mean</code>, <code>median</code>,
<code>mode</code>, <code>p0</code>, role, market context (if any).</li>
<li><b>05_FULL_PMF_WIDE.csv</b> — same rows, with <code>pmf_json</code>
(the full PMF as JSON) and the <code>p_ge_1 … p_ge_20</code> tail
ladder.</li>
<li><b>06_OUTCOME_LEVEL_PROBABILITIES.csv</b> — long format. One row per
(player, stat, k) with P(outcome=k). Useful for plotting tools.</li>
<li><b>machine_readable/model_only.parquet</b> — the same content as
<code>05_FULL_PMF_WIDE</code> in parquet form, full numeric precision.
This is the canonical artifact.</li>
</ol>

<h2>What's NOT in this package</h2>
<ul>
<li>No book lines, no edges, no recommendations. Those live in the
separate <code>wizard_of_odds/</code> package.</li>
<li>No backtests or claims of profitability.</li>
</ul>

<h2>TOV note</h2>
<div class="callout-warn">
TOV PMFs (when present in the slate) come from the current production
Phase 8 calibrators with <b>no Phase 10D / 10D.2 overlay</b>. Those
overlays failed independent validation. The structural refit plan lives
at <code>docs/phase11_tov_structural_refit_plan.md</code>.
</div>
"""
    path.write_text(_html_doc("START HERE — PMF Model Review", body))


def _write_overview(path: Path, *, delivery_date: str,
                     canonical: pd.DataFrame, model_only_path: Path | None
                     ) -> None:
    if canonical.empty:
        body = f"<p>No rows for {delivery_date}.</p>"
    else:
        per_stat = canonical["stat"].value_counts().sort_index().to_dict()
        per_role = canonical["role_bucket"].value_counts().to_dict()
        first = canonical.iloc[0]
        rows = "".join(
            f"<tr><td>{stat}</td><td>{n}</td></tr>"
            for stat, n in per_stat.items())
        role_rows = "".join(
            f"<tr><td>{role}</td><td>{n}</td></tr>"
            for role, n in per_role.items())
        valid_pct = float((canonical["pmf_valid"] == "ok").mean()) * 100
        sum_err = float(canonical["pmf_sum_error"].abs().max())
        cov = canonical["market_coverage_status"].value_counts().to_dict()
        cov_rows = "".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in cov.items())
        src = (str(model_only_path)
                if model_only_path else "predictions/all_props_*.parquet")
        body = f"""
<p><b>Delivery date:</b> {delivery_date} &nbsp;&nbsp;
<b>Rows:</b> {len(canonical)} &nbsp;&nbsp;
<b>Model version:</b> <code>{first.get('model_version')}</code></p>

<p><b>Source:</b> <code>{src}</code></p>

<h2>Per-stat coverage</h2>
<table><tr><th>stat</th><th>rows</th></tr>{rows}</table>

<h2>Per-role coverage</h2>
<table><tr><th>role</th><th>rows</th></tr>{role_rows}</table>

<h2>Quality rollup</h2>
<ul>
<li>PMF validity OK: <b>{valid_pct:.1f}%</b></li>
<li>max |Σp − 1|: <b>{sum_err:.2e}</b></li>
<li>Market coverage breakdown:
<table><tr><th>status</th><th>rows</th></tr>{cov_rows}</table></li>
</ul>

<div class="callout">PMFs are model-only. No market anchoring.</div>
"""
    path.write_text(_html_doc("Model Review Overview", body))


def _write_pmf_viewer(path: Path, *, canonical: pd.DataFrame,
                       delivery_date: str) -> None:
    """Render every PMF as a small inline SVG-free CSS bar chart."""
    if canonical.empty:
        body = "<p>No PMFs.</p>"
        path.write_text(_html_doc("PMF Distribution Viewer", body))
        return

    cards = []
    for _, r in canonical.iterrows():
        try:
            d = json.loads(r["pmf_json"])
            pmf = sorted(((int(k), float(v)) for k, v in d.items()),
                          key=lambda kv: kv[0])
        except Exception:
            pmf = []
        if not pmf:
            continue
        # Cap viewer at k=30 so the bars stay readable; tail mass is summarized
        max_k_show = min(30, max(k for k, _ in pmf))
        max_p = max((p for _, p in pmf if _ <= max_k_show), default=0.0) or 1.0
        bars = []
        for k in range(0, max_k_show + 1):
            p = next((v for kk, v in pmf if kk == k), 0.0)
            h = int(round(80 * (p / max_p))) if max_p > 0 else 0
            bars.append(
                f'<div class="bar"><div class="fill" style="height:{h}px" '
                f'title="P({k})={p:.4f}"></div>'
                f'<div class="label">{k}</div></div>')
        bars_html = "".join(bars)
        tail = sum(p for k, p in pmf if k > max_k_show)
        tail_html = (f' <span style="color:#888;font-size:0.85em">'
                      f'(tail k>{max_k_show}: {tail:.4f})</span>'
                      if tail > 1e-6 else '')
        cards.append(f"""
<div class="pmf-card">
  <div class="pmf-head">
    <span>{_escape(r['player_name'])} — {r['stat'].upper()}
    <span style="color:#888;font-weight:400">({r['team']} vs {r['opponent']})</span></span>
    <span>mean {float(r['mean']):.2f} &middot; median {int(r['median'])} &middot;
          mode {int(r['mode'])} &middot; p0 {float(r['p0']):.3f}</span>
  </div>
  <div class="pmf-meta">role: {r['role_bucket']} &middot;
       calibration: {r['calibration_confidence']} &middot;
       TOV status: {r['tov_status']}{tail_html}</div>
  <div class="bars">{bars_html}</div>
</div>""")

    body = (
        f"<p>Every PMF in the slate, grouped by stat. Bars are normalized "
        f"to the row's peak. Hover for exact P(outcome=k).</p>"
        f"<div class=\"callout\">Model-only PMFs. No market anchoring.</div>"
    )
    # Group cards by stat for readability.
    by_stat: dict[str, list[str]] = {}
    canon_indexed = canonical.reset_index(drop=True)
    for i, card in enumerate(cards):
        stat = str(canon_indexed.iloc[i]["stat"]).upper()
        by_stat.setdefault(stat, []).append(card)
    for stat in sorted(by_stat):
        body += f"<h2>{stat}</h2>" + "".join(by_stat[stat])
    path.write_text(_html_doc(
        f"PMF Distribution Viewer — {delivery_date}", body))


def _escape(s) -> str:
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                  .replace(">", "&gt;").replace('"', "&quot;"))


def _html_doc(title: str, body: str) -> str:
    return (f"<!doctype html><html><head><meta charset=utf-8>"
            f"<title>{_escape(title)}</title>"
            f"<style>{_HTML_BASE_STYLE}</style></head>"
            f"<body><h1>{_escape(title)}</h1>{body}</body></html>")


# ── Wizard of Odds package writer ───────────────────────────────────────


def write_woo_package(canonical: pd.DataFrame, fair_board: pd.DataFrame,
                       market_comp: pd.DataFrame, edges: pd.DataFrame,
                       outcome_long: pd.DataFrame, *,
                       pkg_dir: Path, manifest: dict) -> None:
    pkg_dir.mkdir(parents=True, exist_ok=True)

    _write_csv_parquet(fair_board, pkg_dir / "fair_odds_board")
    _write_jsonl(fair_board, pkg_dir / "fair_odds_board")

    canon_clean = _drop_pmf_arr(canonical)
    _write_csv_parquet(canon_clean, pkg_dir / "full_pmfs_wide")
    _write_csv_parquet(outcome_long, pkg_dir / "full_pmfs_outcome_level")

    if not market_comp.empty:
        _write_csv_parquet(market_comp, pkg_dir / "market_comparison")
    else:
        _write_csv_parquet(pd.DataFrame(columns=CANONICAL_COLUMNS_BASE),
                            pkg_dir / "market_comparison")
    if not edges.empty:
        _write_csv_parquet(edges, pkg_dir / "publishable_edges")
    else:
        _write_csv_parquet(pd.DataFrame(columns=CANONICAL_COLUMNS_BASE),
                            pkg_dir / "publishable_edges")

    (pkg_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str))


# ── Main orchestration ──────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True,
                     help="delivery calendar date YYYY-MM-DD (US/Eastern)")
    ap.add_argument("--snapshot", choices=("morning", "pre_close",
                                           "close_lock", "after_game"),
                     default="morning")
    ap.add_argument("--predictions", default=None,
                     help="path to predictions/all_props_{date}.parquet (optional)")
    ap.add_argument("--model-only", default=None,
                     help="path to canonical MODEL_ONLY parquet (optional; auto-discovered)")
    ap.add_argument("--odds-snapshot", default=None,
                     help="path to a single odds_pairs_*.parquet (optional)")
    ap.add_argument("--no-odds-fetch", action="store_true",
                     help="never make Odds-API HTTP calls (default: on)")
    ap.add_argument("--edge-threshold", type=float, default=0.04,
                     help="absolute edge threshold for publishable_edges")
    args = ap.parse_args()

    delivery_date = args.date
    snapshot_type = args.snapshot
    snapshot_time_utc = _now_utc_iso()
    pipeline_run_id = str(uuid.uuid4())
    model_version = _model_version_string()

    print("=" * 72)
    print(f"daily delivery — {delivery_date} — snapshot={snapshot_type}")
    print(f"  model_version={model_version}  run_id={pipeline_run_id}")
    print(f"  snapshot_time_utc={snapshot_time_utc}")
    print("=" * 72)

    # 1. Locate canonical MODEL_ONLY parquet.
    model_only_path = (Path(args.model_only) if args.model_only
                        else _find_model_only_parquet(delivery_date))
    if model_only_path is None:
        print(f"ERROR: no MODEL_ONLY parquet for {delivery_date}. "
              f"Run scripts/predict.py + scripts/export_live_pmf_slate.py first.")
        return 2
    print(f"  model_only: {model_only_path.relative_to(REPO_ROOT)}")
    model_only = load_model_only(model_only_path)
    print(f"  rows: {len(model_only):,}")

    # 2. Load Odds API snapshot (no HTTP calls; we only consume disk).
    odds_path = (Path(args.odds_snapshot) if args.odds_snapshot
                  else _find_odds_snapshot(delivery_date))
    if odds_path:
        print(f"  odds_snapshot: {odds_path.relative_to(REPO_ROOT)}")
    else:
        print("  odds_snapshot: <none>")
    odds = load_odds_snapshot(odds_path)

    # 3. Build canonical row frame.
    injury_path = REPO_ROOT / "data" / "player_availability_asof.parquet"
    canonical = build_canonical_rows(
        model_only, delivery_date=delivery_date,
        snapshot_type=snapshot_type, snapshot_time_utc=snapshot_time_utc,
        model_version=model_version, pipeline_run_id=pipeline_run_id,
        injury_path=injury_path)
    print(f"  canonical rows: {len(canonical)}")

    # 4. Build derived views.
    fair_board = build_fair_odds_board(canonical)
    market_comp, books_seen = build_market_comparison(canonical, odds)
    edges = build_publishable_edges(market_comp,
                                      edge_threshold=args.edge_threshold)
    outcome_long = build_outcome_level(canonical)

    # Apply market_coverage_status to every row.
    coverage = _market_coverage_status(books_seen)
    for df in (canonical, fair_board, market_comp, edges, outcome_long):
        if "market_coverage_status" in df.columns:
            df["market_coverage_status"] = (
                coverage if coverage != "none" else "none")

    # 5. Validation gates.
    ok_canon, msgs_canon = runner_validation_gates(
        canonical, snapshot_type=snapshot_type)
    ok_edges, msgs_edges = runner_validation_gates(
        edges, snapshot_type=snapshot_type)
    if not ok_canon:
        print("WARN: canonical-frame gate violations:")
        for m in msgs_canon:
            print(f"  - {m}")
    if not ok_edges:
        print("REFUSE TO PUBLISH publishable_edges:")
        for m in msgs_edges:
            print(f"  - {m}")
        edges = pd.DataFrame(columns=CANONICAL_COLUMNS_BASE)

    # 6. Write Derek package.
    derek_dir = REPO_ROOT / "deliveries" / delivery_date / "pmf_model_review_package"
    write_derek_package(canonical, outcome_long,
                          delivery_date=delivery_date, pkg_dir=derek_dir,
                          model_only_path=model_only_path)
    print(f"  wrote {derek_dir.relative_to(REPO_ROOT)}")

    # 7. Build manifest.
    quality_rollup = {
        "pmf_valid_ok_pct": float((canonical["pmf_valid"] == PMF_VALID_OK).mean())
                              if not canonical.empty else 1.0,
        "pmf_sum_error_max": float(canonical["pmf_sum_error"].abs().max())
                               if not canonical.empty else 0.0,
        "calibration_confidence":
            canonical["calibration_confidence"].value_counts().to_dict()
            if not canonical.empty else {},
        "market_coverage_status":
            canonical["market_coverage_status"].value_counts().to_dict()
            if not canonical.empty else {},
        "injury_freshness_status":
            canonical["injury_freshness_status"].value_counts().to_dict()
            if not canonical.empty else {},
        "lineup_freshness_status":
            canonical["lineup_freshness_status"].value_counts().to_dict()
            if not canonical.empty else {},
    }
    manifest = {
        "delivery_date": delivery_date,
        "pipeline_run_id": pipeline_run_id,
        "snapshot_type": snapshot_type,
        "snapshot_time_utc": snapshot_time_utc,
        "model_version": model_version,
        "phase8_calibration_source": "phase8_role_aware_pmf_cal_v2",
        "tov_overlay": "off",
        "tov_overlay_reason": TOV_STATUS_REASON,
        "sources": {
            "model_only_parquet": {
                "path": str(model_only_path.relative_to(REPO_ROOT)),
                "mtime_utc": _file_mtime_iso_utc(model_only_path),
                "sha256": _file_sha256(model_only_path),
            },
            "availability_table": {
                "path": (str(injury_path.relative_to(REPO_ROOT))
                         if injury_path.exists() else None),
                "mtime_utc": _file_mtime_iso_utc(injury_path),
                "freshness_status": _injury_freshness(injury_path),
            },
            "odds_snapshot": ({
                "path": str(odds_path.relative_to(REPO_ROOT)),
                "mtime_utc": _file_mtime_iso_utc(odds_path),
                "books_seen": books_seen,
                "coverage_status": coverage,
            } if odds_path else {
                "path": None, "mtime_utc": None, "books_seen": [],
                "coverage_status": "none",
            }),
        },
        "row_counts": {
            "fair_odds_board": int(len(fair_board)),
            "full_pmfs_wide": int(len(canonical)),
            "market_comparison": int(len(market_comp)),
            "publishable_edges": int(len(edges)),
        },
        "quality_rollup": quality_rollup,
        "warnings": [*msgs_canon, *msgs_edges],
        "no_odds_fetch": bool(args.no_odds_fetch),
    }

    # 8. Write Wizard of Odds package.
    woo_dir = REPO_ROOT / "deliveries" / delivery_date / "wizard_of_odds"
    write_woo_package(canonical, fair_board, market_comp, edges,
                       outcome_long, pkg_dir=woo_dir, manifest=manifest)
    print(f"  wrote {woo_dir.relative_to(REPO_ROOT)}")
    print(f"  publishable_edges: {len(edges)} rows "
          f"(edge ≥ {args.edge_threshold})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
