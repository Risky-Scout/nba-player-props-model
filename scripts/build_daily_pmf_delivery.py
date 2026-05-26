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
        [--model-only deliveries/2026-04-27/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet] \
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

# Phase 14 audit tag: source-of-truth for the active calibration blend policy.
# Imported lazily so module-level use sites get the current value without
# re-importing per call. Defensive try/except: if the import path is
# unavailable in any execution context, fall back to None so the existing
# hardcoded string is emitted unchanged.
try:
    import sys as _phase14_sys
    from pathlib import Path as _phase14_Path
    _SRC = _phase14_Path(__file__).resolve().parent.parent / "src"
    if str(_SRC) not in _phase14_sys.path:
        _phase14_sys.path.insert(0, str(_SRC))
    from nba_props_model.calibration.pmf_calibration import (
        ROLE_AWARE_BLEND_POLICY as _ROLE_AWARE_BLEND_POLICY,
    )
except Exception:
    _ROLE_AWARE_BLEND_POLICY = None

import argparse
import hashlib
import json
import math
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
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from delivery_model_only_paths import find_model_only_parquet_for_date  # noqa: E402
warnings.filterwarnings("ignore")

# ── Constants pinned to the delivery spec ────────────────────────────────

from nba_props_model.targets import (  # noqa: E402
    BASE_STATS_FULL,
    MISSION_REQUIRED_TARGETS_CANONICAL,
)
from nba_props_model.data.lineup_freshness import (  # noqa: E402
    LINEUP_SOURCE_DEFAULT,
    LineupFreshnessSnapshot,
    derive_lineup_metadata_for_row,
    load_bdl_lineup_freshness_snapshot,
)
from nba_props_model.data.injury_freshness import (  # noqa: E402
    classify_canonical_injury_freshness,
)

SUPPORTED_STATS = MISSION_REQUIRED_TARGETS_CANONICAL  # M8.1: 12-stat mission canonical (incl. ra)
ROLE_ORDER = ("inactive_risk", "fringe", "bench", "rotation", "core", "starter")
HIGH_CONF_ROLES = ("starter", "core", "rotation")
MED_CONF_ROLES = ("bench", "fringe")
LOW_CONF_ROLES = ("inactive_risk",)

# Deterministic mapping from `mp_bucket` (4-bucket projected-minutes
# feature emitted by predict.py via correlation/sgp_engine.mp_bucket()).
# Thresholds documented in src/nba_props_model/correlation/sgp_engine.py:
#   bucket 0 → mp_mean_last10 < 15  (fringe)
#   bucket 1 → 15 ≤ mp < 22         (bench)
#   bucket 2 → 22 ≤ mp < 30         (rotation)
#   bucket 3 → mp ≥ 30              (starter)
# This is ex-ante (10-game rolling mean of minutes played) and does not
# require lineup confirmation. We never derive `core` or `inactive_risk`
# from this signal — those tiers require usage data and confirmed lineup
# status which we do not have at the canonical-source layer.
MP_BUCKET_TO_ROLE = {
    0: "fringe",
    1: "bench",
    2: "rotation",
    3: "starter",
}
ROLE_SOURCE_DERIVED_FROM_MINUTES = "derived_from_projected_minutes"
ROLE_SOURCE_UNKNOWN = "unknown"

P_GE_LADDER = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
PMF_VALID_OK = "ok"
TOV_STATUS_CURRENT = "current_phase8"
TOV_STATUS_REASON = ("Phase 10D/10D.2 overlay failed independent validation; "
                      "see docs/phase11_tov_structural_refit_plan.md")

CANONICAL_COLUMNS_BASE = [
    "player_name", "player_id", "team", "opponent", "is_home",
    "game_id", "game_start_time", "stat",
    "line", "market_line", "book",
    "market_over_odds", "market_under_odds", "market_no_vig_over_prob",
    "pmf_source", "calibration_source", "cal_source", "role_bucket",
    "role_source", "minutes_mean", "minutes_q50", "p_inactive_used",
    "mean", "pmf_mean", "median", "mode", "p0",
    *[f"p_ge_{k}" for k in P_GE_LADDER],
    # ``model_p_over`` is the legacy conditional probability retained
    # for internal canonical_source forensics. It is QUARANTINED from
    # public WoO outputs (the public writer strips it via
    # ``_sanitize_public_columns`` before persisting). ``p_over``
    # holds the PMF-native direct tail probability
    # ``P(stat > line)`` and IS the public-facing column.
    "model_p_over", "p_over",
    "fair_over_odds_american", "fair_under_odds_american",
    "edge",
    "snapshot_type", "snapshot_time_utc",
    "model_version", "pipeline_run_id",
    "pmf_valid", "pmf_sum_error", "calibration_confidence",
    "market_coverage_status", "tov_status",
    "injury_freshness_status", "lineup_freshness_status",
    "role_freshness_status",
    # Row-level provenance for the row-level injury/lineup freshness
    # rollups in deliveries/<DATE>/manifest.json. These fields must
    # propagate from stat_grid -> canonical MODEL_ONLY ->
    # market_comparison -> Derek's feed so each downstream consumer
    # can reason about freshness from row evidence rather than file
    # mtimes.
    "injury_context_source",
    "injury_report_fetched_at_utc",
    "expected_lineup_status",
    "official_lineup_status",
    "lineup_source",
    "lineup_last_updated_utc",
    # line_source distinguishes actual sportsbook-offered lines from
    # synthetic model-grid sweep rows. Values:
    #   "market_offered"  — a real book offered this line
    #   "model_grid"      — generated by _line_grid_for_stat for fair-odds board
    # Do NOT flag extreme p_over values (0.99, 0.0) as corruption when
    # line_source == "model_grid"; those are expected tail probabilities.
    "line_source",
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


# ── Direct PMF expectation + tail probability (public-output names) ──
#
# These helpers compute the PMF-native ``pmf_mean`` and ``p_over``
# fields that public delivery outputs must expose. They are
# intentionally distinct from ``_model_p_over_line`` above:
#
#   * ``_pmf_direct_mean``: ``E[X] = sum_k k * P[k]`` after
#     normalising the PMF so its mass sums to 1.
#   * ``_pmf_direct_p_over``: RAW tail probability
#     ``P(stat > line) = sum_{k > line} P[k]`` (NOT the conditional
#     renormalisation used by ``_model_p_over_line``).
#
# The public column rule is: ``p_over`` ALWAYS means
# ``P(stat > line)`` computed directly from the final stat-grid PMF
# surface. Never alias ``model_p_over`` or ``model_prob_over_*`` into
# ``p_over``.
def _pmf_direct_mean(pmf_arr: np.ndarray) -> float | None:
    arr = np.clip(np.asarray(pmf_arr, dtype=float), 0.0, None)
    s = arr.sum()
    if s <= 0 or not np.isfinite(s):
        return None
    arr = arr / s
    return float((arr * np.arange(len(arr), dtype=float)).sum())


def _pmf_direct_p_over(
    pmf_arr: np.ndarray, line: float | None
) -> float | None:
    if line is None or not np.isfinite(line):
        return None
    arr = np.clip(np.asarray(pmf_arr, dtype=float), 0.0, None)
    s = arr.sum()
    if s <= 0 or not np.isfinite(s):
        return None
    arr = arr / s
    ks = np.arange(len(arr), dtype=float)
    return float(arr[ks > float(line)].sum())


# Quarantined public column names — the public WoO writer strips
# these from every persisted CSV / Parquet / JSONL artifact it owns.
# Internal canonical_source files keep the diagnostic names so
# downstream forensics + verifiers still see the legacy probabilities;
# the strip happens only at the public writer boundary.
QUARANTINED_PUBLIC_COLUMNS: tuple[str, ...] = (
    "model_projected_mean",
    "model_probability_over_market_line",
    "model_prob_over_raw",
    "model_prob_over_active",
    "model_p_over",
)


def _sanitize_public_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop quarantined public columns from a WoO-bound frame."""
    if df is None or df.empty:
        return df
    cols = [c for c in QUARANTINED_PUBLIC_COLUMNS if c in df.columns]
    if not cols:
        return df
    return df.drop(columns=cols)


# Fair American odds are written to Parquet; reject magnitudes that overflow
# int64 or pyarrow's pandas bridge (extreme tail lines where p is interior
# but implied price is astronomically large — treat as non-publishable).
_FAIR_AMERICAN_ODDS_MAX_ABS = 9_000_000_000_000_000  # < 2**63-1, with margin


def _prob_to_american(p: float | None) -> int | None:
    """Convert a naked win probability to fair American odds.

    Defined only on the open interval (0, 1). For ``p <= 0``, ``p >= 1``,
    non-finite ``p``, or when the implied price overflows IEEE floats,
    returns ``None`` (fair odds are infinite or undefined — never clip
    ``p`` to fake finite prices).

    Convention: ``p >= 0.5`` → negative American; ``p < 0.5`` → positive.
    """
    if p is None:
        return None
    try:
        if pd.isna(p):
            return None
    except TypeError:
        pass
    try:
        pf = float(p)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(pf) or pf <= 0.0 or pf >= 1.0:
        return None
    if pf >= 0.5:
        raw = -100.0 * pf / (1.0 - pf)
    else:
        raw = 100.0 * (1.0 - pf) / pf
    if not math.isfinite(raw):
        return None
    try:
        out = int(round(raw))
    except (OverflowError, ValueError):
        return None
    if abs(out) > _FAIR_AMERICAN_ODDS_MAX_ABS:
        return None
    return out


def _prob_is_degenerate_boundary(p: float | None) -> bool:
    """True when ``p`` is a finite probability on the closed boundary {0, 1}."""
    if p is None:
        return False
    try:
        if pd.isna(p):
            return False
    except TypeError:
        pass
    try:
        x = float(p)
    except (TypeError, ValueError):
        return False
    return bool(math.isfinite(x) and (x <= 0.0 or x >= 1.0))


def _validate_fair_american_odds_columns(df: pd.DataFrame, *, label: str) -> None:
    """Assert fair American columns are null or finite integers (no inf)."""
    if df is None or df.empty:
        return
    for col in ("fair_over_odds_american", "fair_under_odds_american"):
        if col not in df.columns:
            continue
        for i, v in enumerate(df[col].tolist()):
            if v is None:
                continue
            try:
                if pd.isna(v):
                    continue
            except TypeError:
                pass
            try:
                fv = float(v)
            except (TypeError, ValueError) as e:
                raise AssertionError(
                    f"{label}: {col} row {i} non-numeric value {v!r}"
                ) from e
            if not math.isfinite(fv):
                raise AssertionError(
                    f"{label}: {col} row {i} non-finite value {v!r}"
                )
            if abs(fv - round(fv)) > 1e-6:
                raise AssertionError(
                    f"{label}: {col} row {i} expected integer American odds, got {v!r}"
                )


def _clean_optional_meta(v):
    """Return None for missing metadata values, otherwise original value."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, str) and v.strip().lower() in {"", "none", "nan", "<na>"}:
        return None
    return v


def _clean_optional_float(v) -> float | None:
    v = _clean_optional_meta(v)
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


def _derive_cal_source(row) -> str | None:
    """Derive a stable calibration-source label from explicit metadata or pmf_source.

    Examples:
      stat_grid:pmf_sim_v1+role_aware_pmf_cal_v1:core
        -> role_aware_pmf_cal_v1
      stat_grid:fg3m_hurdle_v1+role_aware_pmf_cal_v1:bench
        -> role_aware_pmf_cal_v1
    """
    for col in ("cal_source", "calibration_source"):
        v = _clean_optional_meta(row.get(col))
        if v is not None:
            return str(v)

    src = str(_clean_optional_meta(row.get("pmf_source")) or "")
    if not src:
        return None

    parts = src.split(":")
    middle = parts[1] if len(parts) >= 2 else src
    tokens = [t for t in middle.split("+") if t]
    cal_tokens = [t for t in tokens if "cal" in t.lower()]
    return "+".join(cal_tokens) if cal_tokens else None


def _repo_rel(path: Path | str | None) -> str | None:
    """Return repo-relative path when possible; tolerate relative input paths."""
    if path is None:
        return None
    q = Path(path)
    try:
        return str(q.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(q)


def _calibration_confidence(role: str | None) -> str:
    if role in HIGH_CONF_ROLES:
        return "high"
    if role in MED_CONF_ROLES:
        return "medium"
    return "low"


# ── Canonical model-only build from predictions/all_props_*.parquet ──────


NBA_TEAM_NAME_TO_ABBR = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE", "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU",
    "Indiana Pacers": "IND", "LA Clippers": "LAC",
    "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM", "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS", "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}


def _team_id_to_abbr_map() -> dict[int, str]:
    p = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not p.exists():
        return {}
    df = pd.read_parquet(p, columns=["team_id", "team_abbr"]).drop_duplicates()
    return dict(zip(df["team_id"].astype(int), df["team_abbr"].astype(str)))


def _normalize_pmf_json_string(s) -> str | None:
    """Take a PMF JSON dict-string with possibly imprecise sums; return a
    new JSON dict-string normalized to sum exactly 1 (to float64 precision)."""
    if not isinstance(s, str):
        return None
    try:
        d = {int(k): float(v) for k, v in json.loads(s).items()}
    except Exception:
        return None
    if not d:
        return None
    K = max(d.keys()) + 1
    arr = np.zeros(K, dtype=float)
    for k, v in d.items():
        arr[k] = max(0.0, float(v))
    s_total = arr.sum()
    if s_total <= 0 or not np.isfinite(s_total):
        return None
    arr = arr / s_total
    return json.dumps({str(k): float(v) for k, v in enumerate(arr) if v > 0.0})


def _parse_game_string(g) -> tuple[str | None, str | None]:
    """\"Houston Rockets @ Los Angeles Lakers\" → (\"HOU\", \"LAL\")."""
    if not isinstance(g, str) or " @ " not in g:
        return None, None
    away_name, home_name = g.split(" @ ", 1)
    return (NBA_TEAM_NAME_TO_ABBR.get(away_name.strip()),
            NBA_TEAM_NAME_TO_ABBR.get(home_name.strip()))


def _odds_commence_lookup(date: str) -> dict[int, str]:
    """Return {game_id → commence_time_utc} from any odds_pairs file for
    {date}, if available. Used to populate game_start_time when the
    prediction file lacks it."""
    base = REPO_ROOT / "data" / "odds_api" / "processed" / date
    if not base.exists():
        return {}
    out: dict[int, str] = {}
    for fp in sorted(base.glob("odds_pairs_*.parquet")):
        try:
            cols = ["game_id", "commence_time_utc"]
            df = pd.read_parquet(fp, columns=cols)
            for _, r in df.iterrows():
                gid = r.get("game_id")
                ct = r.get("commence_time_utc")
                if pd.notna(gid) and pd.notna(ct):
                    out.setdefault(int(gid), str(ct))
        except Exception:
            continue
    return out


def _stat_grid_rows(date: str, stat_grid_path: Path | None = None) -> list[dict]:
    """If ``stat_grid_path`` (or default ``predictions/stat_grid_{date}.parquet``)
    exists, return its rows as canonical-schema dicts. These rows carry
    model-only PMFs for stats whose markets BDL does not sell — most
    importantly TOV. Returns [] when the file is absent so merge callers
    can fall back."""
    p = Path(stat_grid_path) if stat_grid_path is not None else (
        REPO_ROOT / "predictions" / f"stat_grid_{date}.parquet"
    )
    if not p.exists():
        return []
    grid = pd.read_parquet(p)
    if grid.empty:
        return []

    ta_map = _team_id_to_abbr_map()
    commence_map = _odds_commence_lookup(date)

    out: list[dict] = []
    for _, r in grid.iterrows():
        away_abbr, home_abbr = _parse_game_string(r.get("game"))
        team_abbr = (ta_map.get(int(r["team_id"]))
                     if pd.notna(r.get("team_id")) else None)
        if team_abbr is not None and home_abbr is not None:
            is_home = (team_abbr == home_abbr)
            opponent = away_abbr if is_home else home_abbr
        else:
            is_home, opponent = bool(r.get("is_home", False)), None
        gid = int(r["game_id"]) if pd.notna(r.get("game_id")) else None
        out.append({
            "player_id": int(r["player_id"]) if pd.notna(r.get("player_id")) else None,
            "player_name": r.get("player_name"),
            "team_abbr": team_abbr,
            "team_id": int(r["team_id"]) if pd.notna(r.get("team_id")) else None,
            "opponent": opponent,
            "is_home": is_home,
            "game_id": gid,
            "game": r.get("game"),
            "game_start_et": commence_map.get(gid) if gid is not None else None,
            "stat": r.get("stat"),
            "role_bucket": (r.get("role_bucket")
                            if pd.notna(r.get("role_bucket")) else None),
            "hard_role_bucket": (r.get("hard_role_bucket")
                                  if pd.notna(r.get("hard_role_bucket"))
                                  else (r.get("role_bucket") if pd.notna(r.get("role_bucket")) else None)),
            "role_mixture_enabled": (
                bool(r.get("role_mixture_enabled"))
                if pd.notna(r.get("role_mixture_enabled"))
                else None
            ),
            "role_mixture_weights_json": (
                r.get("role_mixture_weights_json")
                if pd.notna(r.get("role_mixture_weights_json"))
                else None
            ),
            "role_entropy": (r.get("role_entropy")
                              if pd.notna(r.get("role_entropy")) else None),
            "role_bucket_confidence": (
                r.get("role_bucket_confidence")
                if pd.notna(r.get("role_bucket_confidence"))
                else None
            ),
            "role_source": (r.get("role_source")
                            if pd.notna(r.get("role_source"))
                            else "phase12_stat_grid"),
            "mp_bucket": (r.get("mp_bucket")
                          if pd.notna(r.get("mp_bucket")) else None),
            "usage_bucket": (r.get("usage_bucket")
                             if pd.notna(r.get("usage_bucket")) else None),
            "minutes_mean": (r.get("minutes_mean")
                             if pd.notna(r.get("minutes_mean")) else None),
            "minutes_q50": (r.get("minutes_q50")
                            if pd.notna(r.get("minutes_q50")) else None),
            "p_inactive_used": (r.get("p_inactive_used")
                                if pd.notna(r.get("p_inactive_used")) else None),
            "injury_freshness_status": (
                r.get("injury_freshness_status")
                if pd.notna(r.get("injury_freshness_status")) else None
            ),
            "injury_context_source": (
                r.get("injury_context_source")
                if pd.notna(r.get("injury_context_source")) else None
            ),
            "injury_report_fetched_at_utc": (
                r.get("injury_report_fetched_at_utc")
                if pd.notna(r.get("injury_report_fetched_at_utc")) else None
            ),
            "expected_lineup_status": (
                r.get("expected_lineup_status")
                if pd.notna(r.get("expected_lineup_status"))
                else None
            ),
            "official_lineup_status": (
                r.get("official_lineup_status")
                if pd.notna(r.get("official_lineup_status"))
                else None
            ),
            "lineup_source": (
                r.get("lineup_source")
                if pd.notna(r.get("lineup_source"))
                else None
            ),
            "lineup_last_updated_utc": (
                r.get("lineup_last_updated_utc")
                if pd.notna(r.get("lineup_last_updated_utc"))
                else None
            ),
            "lineup_freshness_status": (
                r.get("lineup_freshness_status")
                if pd.notna(r.get("lineup_freshness_status"))
                else None
            ),
            "projected_minutes": (
                r.get("projected_minutes")
                if pd.notna(r.get("projected_minutes"))
                else None
            ),
            "minutes_q10": (r.get("minutes_q10") if pd.notna(r.get("minutes_q10")) else None),
            "minutes_q90": (r.get("minutes_q90") if pd.notna(r.get("minutes_q90")) else None),
            "support_min": 0,
            "support_max": (int(r["support_max"])
                              if pd.notna(r.get("support_max")) else None),
            "line": None,
            "market_fair_over_prob": None,
            "market_source": None,
            "market_offered_side": "MODEL_ONLY",
            "market_offered_odds": None,
            "pmf_source": f"stat_grid:{r.get('model_version','phase8_pmf_cal')}",
            "pmf_active": _normalize_pmf_json_string(r.get("pmf")),
        })
    return out


def build_canonical_from_predictions(predictions_path: Path, *,
                                       date: str,
                                       canonical_dir: Path) -> Path:
    """Read predictions/all_props_{date}.parquet, normalize into the
    canonical MODEL_ONLY schema, and write parquet/jsonl/csv under
    canonical_dir. Returns the parquet path.

    The predictions file emits one row per (player, stat, side); we keep
    the first PMF per (player, stat) since both sides share the PMF.

    Phase 12 Part G: when `predictions/stat_grid_{date}.parquet` exists,
    its model-only rows (TOV in particular) are appended after the
    market-driven rows so the canonical includes stats that BDL does
    not sell as markets. Stat-grid rows are tagged
    `pmf_source="stat_grid:..."` and `market_offered_side="MODEL_ONLY"`.
    """
    if not predictions_path.exists():
        raise SystemExit(f"predictions parquet missing: {predictions_path}")
    src = pd.read_parquet(predictions_path)
    if "pmf" not in src.columns:
        raise SystemExit("predictions parquet missing 'pmf' column")
    src = src.drop_duplicates(["player_id", "stat"], keep="first").reset_index(drop=True)

    ta_map = _team_id_to_abbr_map()
    commence_map = _odds_commence_lookup(date)

    rows = []
    for _, r in src.iterrows():
        away_abbr, home_abbr = _parse_game_string(r.get("game"))
        team_abbr = (ta_map.get(int(r["team_id"]))
                     if pd.notna(r.get("team_id")) else None)
        if team_abbr is not None and home_abbr is not None:
            is_home = (team_abbr == home_abbr)
            opponent = away_abbr if is_home else home_abbr
        else:
            is_home, opponent = None, None
        gid = int(r["game_id"]) if pd.notna(r.get("game_id")) else None
        # Derive role_bucket from the projected-minutes feature emitted
        # by predict.py. Never fabricate when the feature is absent.
        mp_b = r.get("mp_bucket")
        if pd.notna(mp_b):
            try:
                mp_b_int = int(mp_b)
                role_bucket = MP_BUCKET_TO_ROLE.get(mp_b_int)
                role_source = (ROLE_SOURCE_DERIVED_FROM_MINUTES
                               if role_bucket else ROLE_SOURCE_UNKNOWN)
            except (TypeError, ValueError):
                role_bucket, role_source = None, ROLE_SOURCE_UNKNOWN
        else:
            role_bucket, role_source = None, ROLE_SOURCE_UNKNOWN
        minutes_q50 = _clean_optional_float(r.get("q50"))
        if minutes_q50 is None:
            minutes_q50 = _clean_optional_float(r.get("projected_minutes"))
        if minutes_q50 is None:
            minutes_q50 = 0.0
        minutes_mean = _clean_optional_float(r.get("minutes_mean"))
        if minutes_mean is None:
            minutes_mean = minutes_q50
        rows.append({
            "player_id": int(r["player_id"]) if pd.notna(r.get("player_id")) else None,
            "player_name": r.get("player_name"),
            "team_abbr": team_abbr,
            "team_id": int(r["team_id"]) if pd.notna(r.get("team_id")) else None,
            "opponent": opponent,
            "is_home": is_home,
            "game_id": gid,
            "game": r.get("game"),
            "game_start_et": commence_map.get(gid) if gid is not None else None,
            "stat": r.get("stat"),
            "role_bucket": role_bucket,
            "hard_role_bucket": role_bucket,
            "role_mixture_enabled": None,
            "role_mixture_weights_json": None,
            "role_entropy": None,
            "role_bucket_confidence": None,
            "role_source": role_source,
            "mp_bucket": (int(mp_b) if pd.notna(mp_b) else None),
            "usage_bucket": (int(r.get("usage_bucket"))
                              if pd.notna(r.get("usage_bucket")) else None),
            "minutes_mean": minutes_mean,
            "minutes_q50": minutes_q50,
            "p_inactive_used": 0.0,
            "slate_date": str(date),
            "minutes_p10": None,
            "minutes_p50": minutes_q50,
            "minutes_p90": None,
            "minutes_std": None,
            "rotation_probability": None,
            "starter_probability": None,
            "projected_role": None,
            "player_game_eligible": None,
            "eligibility_reason": None,
            "has_current_market_line": False,
            "minutes_source": None,
            "minutes_model_version": None,
            "expected_lineup_status": None,
            "official_lineup_status": None,
            "projected_minutes": None,
            "minutes_q10": None,
            "minutes_q90": None,
            "support_min": 0,
            "support_max": None,
            "line": r.get("line"),
            "market_fair_over_prob": r.get("mkt_true_over"),
            "market_source": r.get("bet_vendor"),
            "market_offered_side": r.get("side"),
            "market_offered_odds": r.get("odds"),
            "pmf_source": (f"predict.py:{r.get('cal_source','phase8_pmf_cal')}"
                            if r.get("cal_applied") else "predict.py:raw"),
            "pmf_active": _normalize_pmf_json_string(r.get("pmf")),
        })

    # Phase 12 Part G: append model-only stat-grid rows (e.g. TOV) when
    # predictions/stat_grid_{date}.parquet is present. We dedupe so a
    # market row is never overwritten by a model-only row for the same
    # (player_id, stat).
    grid_rows = _stat_grid_rows(date)
    seen_keys = {(r["player_id"], r["stat"]) for r in rows}
    appended_stats: set[str] = set()
    appended = 0
    for gr in grid_rows:
        key = (gr["player_id"], gr["stat"])
        if key in seen_keys:
            continue
        rows.append(gr)
        seen_keys.add(key)
        appended += 1
        appended_stats.add(str(gr["stat"]))
    if appended:
        print(f"  + appended {appended} stat-grid model-only rows "
              f"(stats: {sorted(appended_stats)})")

    df = pd.DataFrame(rows)
    # M8.6 — drop incomplete (player, game) pairs so production MODEL_ONLY
    # always has equal counts per mission stat (same gate as stat_grid path).
    from build_model_only_canonical_from_stat_grid import _enforce_complete_stat_grid

    df = _enforce_complete_stat_grid(df)
    canonical_dir.mkdir(parents=True, exist_ok=True)
    pq_path = canonical_dir / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    df.to_parquet(pq_path, index=False)
    df.to_json(canonical_dir / "player_prop_pmfs_tonight_MODEL_ONLY.jsonl",
                orient="records", lines=True)
    df.to_csv(canonical_dir / "player_prop_pmfs_tonight_MODEL_ONLY.csv",
                index=False)
    # Compatibility aliases expected by the delivery completeness contract.
    df.to_parquet(canonical_dir / "all_props_model_only.parquet", index=False)
    df.to_json(canonical_dir / "all_props_model_only.jsonl",
               orient="records", lines=True)
    df.to_csv(canonical_dir / "all_props_model_only.csv", index=False)
    (canonical_dir / "manifest.json").write_text(
        json.dumps(
            {
                "delivery_date": date,
                "source_predictions": _repo_rel(predictions_path),
                "model_only_rows": int(len(df)),
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return pq_path


# ── Source discovery ─────────────────────────────────────────────────────


def _find_model_only_parquet(date: str) -> Path | None:
    """Locate MODEL_ONLY parquet under ``deliveries/{date}/``.

    Prefer ``canonical_source/`` (stat_grid-backed rectangular canonical).
    If absent, fall back to legacy rglob discovery (lexicographic last),
    emitting a warning when multiple candidates exist.
    """
    chosen, _cands, warn = find_model_only_parquet_for_date(REPO_ROOT, date)
    if warn:
        print(warn)
    return chosen


def _find_odds_snapshot(date: str) -> Path | None:
    base = REPO_ROOT / "data" / "odds_api" / "processed" / date
    if not base.exists():
        return None
    pairs = sorted(base.glob("odds_pairs_*.parquet"))
    return pairs[-1] if pairs else None


def _list_odds_pair_files(date: str) -> list[Path]:
    base = REPO_ROOT / "data" / "odds_api" / "processed" / date
    if not base.exists():
        return []
    return sorted(base.glob("odds_pairs_*.parquet"))


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def _find_freshness_manifest(date: str) -> Path | None:
    p = REPO_ROOT / "data" / "freshness_manifest" / f"{date}.json"
    return p if p.exists() else None


def _load_freshness_manifest(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"WARN: failed to read freshness manifest {path}: {e}")
        return None


def _load_bdl_lineup_context(
    delivery_date: str,
) -> tuple[
    dict[tuple[str, int], dict[str, Any]],
    dict[str, dict[str, Any]],
    LineupFreshnessSnapshot,
]:
    """Load per-player and per-game BDL lineup context from
    ``artifacts/live_lineups/<delivery_date>/``.

    Thin wrapper around
    :func:`nba_props_model.data.lineup_freshness.load_bdl_lineup_freshness_snapshot`
    so the legacy tuple-shape callers in ``build_daily_pmf_delivery``
    keep working. The third tuple slot is the snapshot dataclass —
    callers that need ``manifest_last_updated_utc`` should read it
    from there.
    """
    snapshot = load_bdl_lineup_freshness_snapshot(REPO_ROOT, delivery_date)
    return snapshot.player_lookup, snapshot.game_lookup, snapshot


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
    official = str(row.get("official_lineup_status") or "").lower().strip()
    expected = str(row.get("expected_lineup_status") or "").lower().strip()
    if official in {"confirmed", "official_confirmed", "available"}:
        return "confirmed"
    if official in {"projected", "partial"}:
        return "projected"
    if expected in {"projected", "expected_probable"}:
        return "projected"
    src = str(row.get("role_source") or "").lower()
    if "confirmed" in src:
        return "confirmed"
    if ("projected" in src or "minutes_distribution" in src
            or "derived_from_projected_minutes" in src):
        return "projected"
    return "unknown"


def _role_freshness_for_row(row: pd.Series) -> str:
    """Row-level flag describing the provenance of `role_bucket`.

    Distinct from `lineup_freshness_status` (which uses the spec
    vocabulary `confirmed | projected | unknown`). The role-freshness
    flag records *which signal* produced `role_bucket`:

      - `confirmed_lineup`        — confirmed starter / rotation list
      - `derived_from_projected_minutes` — from `mp_bucket`
      - `missing`                 — `role_bucket is null`
    """
    if not row.get("role_bucket"):
        return "missing"
    src = str(row.get("role_source") or "").lower()
    if "confirmed" in src:
        return "confirmed_lineup"
    if "derived_from_projected_minutes" in src:
        return ROLE_SOURCE_DERIVED_FROM_MINUTES
    return "missing"


def _market_coverage_status(books_seen: list[str]) -> str:
    n = len(books_seen)
    if n == 0:
        return "none"
    if n == 1:
        return "sparse"
    if n < 4:
        return "partial"
    return "full"



PRODUCTION_TARGET_STATS = MISSION_REQUIRED_TARGETS_CANONICAL  # M8.1: 11-stat mission canonical (was 7-stat BASE_STATS_FULL pre-M8.1, 5-stat literal pre-M4A2)
PRODUCTION_TARGET_STAT_SET = set(PRODUCTION_TARGET_STATS)

# Stat-grid / MODEL_ONLY parquet must carry these for production + daily validation.
MODEL_ONLY_ELIGIBILITY_MINUTES_COLUMNS = [
    "minutes_mean",
    "minutes_p10",
    "minutes_p50",
    "minutes_p90",
    "minutes_std",
    "p_inactive_used",
    "rotation_probability",
    "starter_probability",
    "projected_role",
    "player_game_eligible",
    "eligibility_reason",
    "has_current_market_line",
]

MODEL_ONLY_PUBLISH_ID_STAT_COLUMNS = [
    "slate_date",
    "game_id",
    "player_id",
    "stat",
]


def _validate_eligibility_contract_for_model_only(df: pd.DataFrame, path: Path) -> None:
    """M8.9 root-cause rewire: model_only must carry eligibility + minutes
    columns AND must not contain ineligible / deep-bench rows.

    Set NBA_ALLOW_LEGACY_NO_ELIGIBILITY=1 to skip while migrating; the
    flag exists only so partial-environment backfills can produce a
    canonical even before the upstream pipeline is re-run.
    """
    if os.environ.get("NBA_ALLOW_LEGACY_NO_ELIGIBILITY", "").strip() == "1":
        return

    required_cols = list(MODEL_ONLY_ELIGIBILITY_MINUTES_COLUMNS)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise SystemExit(
            "MODEL_ONLY_SCHEMA_MISSING_COLUMNS "
            f"path={path} missing={missing} present={list(df.columns)}"
        )

    bad_eligible = df["player_game_eligible"].astype(bool).eq(False)
    if bool(bad_eligible.any()):
        sample = (
            df.loc[
                bad_eligible,
                [
                    c
                    for c in (
                        "slate_date",
                        "game_id",
                        "player_id",
                        "stat",
                        "player_name",
                        "player_game_eligible",
                    )
                    if c in df.columns
                ],
            ]
            .head(15)
            .to_dict("records")
        )
        raise SystemExit(
            "MODEL_ONLY_INELIGIBLE_ROWS_PRESENT "
            f"count={int(bad_eligible.sum())} sample_rows={sample}"
        )

    for col in ("minutes_mean", "rotation_probability", "starter_probability"):
        if df[col].isna().any():
            raise SystemExit(
                "FATAL: production MODEL_ONLY has null " + col
                + "; every eligible row must carry the upstream minutes summary."
            )

    deep_bench = (
        ~df["has_current_market_line"].fillna(False).astype(bool)
        & (df["minutes_mean"] < 12.0)
        & (df["rotation_probability"] < 0.50)
        & (df["starter_probability"] < 0.50)
    )
    if bool(deep_bench.any()):
        sample = df.loc[
            deep_bench,
            [c for c in ("player_name", "stat", "minutes_mean",
                          "rotation_probability", "starter_probability")
             if c in df.columns],
        ].head(10).to_dict("records")
        raise SystemExit(
            "FATAL: production MODEL_ONLY still contains deep-bench no-line "
            "PMFs (upstream eligibility gate should have removed them). "
            "Sample: " + str(sample)
        )


def _validate_production_model_only(df: pd.DataFrame, path: Path) -> None:
    """Block stale all_props/broader sparse-stat canonical PMFs in production.

    Research mode can opt out with NBA_ALLOW_RESEARCH_PMF_STATS=1.
    """
    if os.environ.get("NBA_ALLOW_RESEARCH_PMF_STATS", "").strip() == "1":
        return

    if "stat" not in df.columns:
        raise SystemExit(f"MODEL_ONLY parquet missing stat column: {path}")

    # No-game slates are valid: allow an empty canonical MODEL_ONLY table.
    # Downstream writers still emit full package files with explicit empty rows.
    if df.empty:
        return

    stats = set(df["stat"].astype(str).str.lower())
    extra = sorted(stats - PRODUCTION_TARGET_STAT_SET)
    missing = sorted(PRODUCTION_TARGET_STAT_SET - stats)
    if extra or missing:
        raise SystemExit(
            "FATAL: production MODEL_ONLY stat set mismatch for "
            f"{path}: expected={list(PRODUCTION_TARGET_STATS)} "
            f"missing={missing} extra={extra}. "
            "Regenerate from predictions/stat_grid_{date}.parquet; "
            "do not use stale all_props canonical."
        )

    counts = df["stat"].astype(str).str.lower().value_counts()
    if counts.empty or counts.min() != counts.max():
        raise SystemExit(
            "FATAL: production MODEL_ONLY stat counts are uneven for "
            f"{path}: {counts.sort_index().to_dict()}. "
            "This usually means stale market-row/all_props PMFs contaminated the delivery."
        )

    if "role_bucket" not in df.columns:
        raise SystemExit(f"FATAL: production MODEL_ONLY missing role_bucket: {path}")

    missing_roles = df["role_bucket"].isna() | (
        df["role_bucket"].astype(str).str.lower().isin(["", "none", "nan", "unknown"])
    )
    if bool(missing_roles.any()):
        raise SystemExit(
            "FATAL: production MODEL_ONLY has missing role_bucket rows: "
            f"{int(missing_roles.sum())}/{len(df)} in {path}. "
            "Role-aware calibration cannot be trusted until stat_grid emits role metadata."
        )

    _validate_eligibility_contract_for_model_only(df, path)


# ── Loaders ───────────────────────────────────────────────────────────────


def load_model_only(parquet_path: Path) -> pd.DataFrame:
    if not parquet_path.exists():
        raise SystemExit(f"MODEL_ONLY parquet missing: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    if "pmf_json" not in df.columns and "pmf_active" in df.columns:
        df = df.rename(columns={"pmf_active": "pmf_json"})
    if "pmf_json" not in df.columns:
        raise SystemExit("MODEL_ONLY parquet missing pmf_json")
    _validate_production_model_only(df, parquet_path)
    return df


def load_odds_snapshot(parquet_path: Path | None,
                         *, all_paths: list[Path] | None = None
                         ) -> pd.DataFrame:
    """Load one or many odds_pairs_*.parquet files. When `all_paths` is
    supplied (e.g. multi-region capture in one date directory), every
    file is concatenated and de-duplicated to the freshest quote per
    (event, book, market, player, line)."""
    paths: list[Path] = []
    if all_paths:
        paths = [p for p in all_paths if p and p.exists()]
    elif parquet_path is not None and parquet_path.exists():
        paths = [parquet_path]
    if not paths:
        return pd.DataFrame()
    frames = []
    for p in paths:
        try:
            frames.append(pd.read_parquet(p))
        except Exception as e:
            print(f"  WARN: failed to read {p}: {e}")
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    if "market_stat" in df.columns:
        df = df[df["market_stat"].astype(str).isin(SUPPORTED_STATS)]
    if not df.empty and "snapshot_time_utc" in df.columns:
        # Keep the freshest quote per book/market/player/line.
        keys = [c for c in ("event_id", "bookmaker_key", "market_key",
                              "player_name", "line")
                 if c in df.columns]
        if keys:
            df = (df.sort_values("snapshot_time_utc")
                    .drop_duplicates(subset=keys, keep="last")
                    .reset_index(drop=True))
    return df


# ── Build canonical row frame from MODEL_ONLY ───────────────────────────


def build_canonical_rows(model_only: pd.DataFrame, *,
                          delivery_date: str, snapshot_type: str,
                          snapshot_time_utc: str, model_version: str,
                          pipeline_run_id: str,
                          injury_path: Path | None,
                          bdl_lineup_players: dict[tuple[str, int], dict[str, Any]] | None = None,
                          bdl_lineup_games: dict[str, dict[str, Any]] | None = None,
                          bdl_lineup_snapshot: "LineupFreshnessSnapshot | None" = None) -> pd.DataFrame:
    """Per (player, stat) one row with full PMF summary + provenance. The
    line/book/market fields are null at this stage; market join lands them."""
    rows = []
    inj_fresh = _injury_freshness(injury_path)
    for _, r in model_only.iterrows():
        minutes_q50 = _clean_optional_float(r.get("minutes_q50"))
        if minutes_q50 is None:
            minutes_q50 = _clean_optional_float(r.get("projected_minutes"))
        if minutes_q50 is None:
            minutes_q50 = 0.0
        minutes_mean = _clean_optional_float(r.get("minutes_mean"))
        if minutes_mean is None:
            minutes_mean = minutes_q50
        p_inactive_used = _clean_optional_float(r.get("p_inactive_used"))
        if p_inactive_used is None:
            p_inactive_used = 0.0
        role_source = _clean_optional_meta(r.get("role_source")) or ROLE_SOURCE_UNKNOWN
        gid = int(r.get("game_id")) if pd.notna(r.get("game_id")) else None
        pid = int(r.get("player_id")) if pd.notna(r.get("player_id")) else None
        expected_lineup_status = (
            _clean_optional_meta(r.get("expected_lineup_status")) or "projected"
        )
        official_lineup_status = (
            _clean_optional_meta(r.get("official_lineup_status")) or "not_available_yet"
        )
        lineup_source_val = (
            _clean_optional_meta(r.get("lineup_source")) or LINEUP_SOURCE_DEFAULT
        )
        lineup_last_updated_utc_val = (
            _clean_optional_meta(r.get("lineup_last_updated_utc")) or None
        )
        # Pre-tipoff / close-lock are the only modes allowed to
        # promote ``official_lineup_status`` to ``"confirmed"``. The
        # morning / forced-manual paths intentionally hold the line
        # at ``"projected"`` even when BDL reports
        # ``lineup_confirmed=True``.
        allow_official_confirmation = snapshot_type in (
            "pre_tipoff", "close_lock", "after_game",
        )
        if gid is not None and bdl_lineup_games:
            game_key = str(gid)
            game_ctx = bdl_lineup_games.get(game_key)
            player_ctx = (
                bdl_lineup_players.get((game_key, pid))
                if (bdl_lineup_players and pid is not None)
                else None
            )
            if game_ctx:
                expected_lineup_status = "projected"
                snapshot_fetched = game_ctx.get("fetched_at_utc")
                if isinstance(snapshot_fetched, str) and snapshot_fetched.strip():
                    lineup_last_updated_utc_val = snapshot_fetched.strip()
                if game_ctx.get("confirmed") and allow_official_confirmation:
                    official_lineup_status = "confirmed"
                    if player_ctx and bool(player_ctx.get("starter")):
                        role_source = "confirmed_bdl_lineup"
                elif game_ctx.get("confirmed"):
                    official_lineup_status = "projected"
                    if role_source == ROLE_SOURCE_UNKNOWN:
                        role_source = "projected_bdl_lineup"
                elif game_ctx.get("has_rows"):
                    official_lineup_status = "projected"
                    if role_source == ROLE_SOURCE_UNKNOWN:
                        role_source = "projected_bdl_lineup"
        cal_source = _derive_cal_source(r) or "phase8_pmf_cal"
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
            "game_id": gid,
            "game_start_time": r.get("game_start_et") or r.get("game_start_time"),
            "stat": r.get("stat"),
            "line": None, "book": None,
            "market_over_odds": None, "market_under_odds": None,
            "market_no_vig_over_prob": None,
            "pmf_source": (r.get("pmf_source")
                           or "phase10c_role_aware_active_conditioned"),
            "calibration_source": (
                f"phase8_role_aware_pmf_cal_v1+{_ROLE_AWARE_BLEND_POLICY}"
                if _ROLE_AWARE_BLEND_POLICY
                else "phase8_role_aware_pmf_cal_v1"
            ),
            "role_bucket": role,
            "role_source": role_source,
            "minutes_mean": minutes_mean,
            "minutes_q50": minutes_q50,
            "p_inactive_used": p_inactive_used,
            # M8.9: canonical eligibility/minutes-summary columns.
            "slate_date": (r.get("slate_date") if pd.notna(r.get("slate_date")) else str(delivery_date)),
            "minutes_p10": _clean_optional_float(r.get("minutes_p10")),
            "minutes_p50": _clean_optional_float(r.get("minutes_p50") if r.get("minutes_p50") is not None else minutes_q50),
            "minutes_p90": _clean_optional_float(r.get("minutes_p90")),
            "minutes_std": _clean_optional_float(r.get("minutes_std")),
            "rotation_probability": _clean_optional_float(r.get("rotation_probability")),
            "starter_probability": _clean_optional_float(r.get("starter_probability")),
            "projected_role": _clean_optional_meta(r.get("projected_role")),
            "player_game_eligible": (bool(r.get("player_game_eligible")) if pd.notna(r.get("player_game_eligible")) else None),
            "eligibility_reason": _clean_optional_meta(r.get("eligibility_reason")),
            "has_current_market_line": (bool(r.get("has_current_market_line")) if pd.notna(r.get("has_current_market_line")) else False),
            "minutes_source": _clean_optional_meta(r.get("minutes_source")),
            "minutes_model_version": _clean_optional_meta(r.get("minutes_model_version")),
            "cal_source": cal_source,
            "mean": smry["mean"], "median": smry["median"],
            "mode": smry["mode"], "p0": smry["p0"],
            # ``pmf_mean`` is the PMF-native public expectation field
            # for downstream WoO/Derek consumers. ``_pmf_summary``
            # already computes ``mean`` from the normalised PMF (i.e.
            # the direct expectation) so we duplicate the value
            # under the public name. This is the same number — the
            # rename exists so consumers can rely on a single public
            # contract column.
            "pmf_mean": smry["mean"],
            **{f"p_ge_{k}": smry[f"p_ge_{k}"] for k in P_GE_LADDER},
            "model_p_over": None,
            # Pre-line row: no offered line yet, so the direct PMF
            # tail probability is undefined. Populated downstream by
            # ``build_fair_odds_board`` (per grid line) and
            # ``build_market_comparison`` (per offered book line).
            "p_over": None,
            "market_line": None,
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
            "injury_freshness_status": (
                r.get("injury_freshness_status")
                if pd.notna(r.get("injury_freshness_status")) else inj_fresh
            ),
            # Row-level injury provenance — preserved end-to-end so
            # the canonical delivery quality rollup can decide
            # freshness from row-level evidence rather than file
            # mtime.
            "injury_context_source": (
                _clean_optional_meta(r.get("injury_context_source"))
                if pd.notna(r.get("injury_context_source")) else None
            ),
            "injury_report_fetched_at_utc": (
                _clean_optional_meta(r.get("injury_report_fetched_at_utc"))
                if pd.notna(r.get("injury_report_fetched_at_utc")) else None
            ),
            "expected_lineup_status": expected_lineup_status,
            "official_lineup_status": official_lineup_status,
            "lineup_source": lineup_source_val,
            "lineup_last_updated_utc": lineup_last_updated_utc_val,
            "lineup_freshness_status": _lineup_freshness_for_row(pd.Series({
                "official_lineup_status": official_lineup_status,
                "expected_lineup_status": expected_lineup_status,
                "role_source": role_source,
            })),
            "role_freshness_status": _role_freshness_for_row(pd.Series({
                "role_bucket": role,
                "role_source": role_source,
            })),
            "_pmf_arr": pmf,
        })
    if not rows:
        empty_cols = list(dict.fromkeys(CANONICAL_COLUMNS_BASE + ["pmf_json", "_pmf_arr"]))
        return pd.DataFrame(columns=empty_cols)
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


def build_fair_odds_board(canonical: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """One row per (player, stat, line) over a default line grid.
    Independent of any book — `book=null` everywhere."""
    rows = []
    fair_over_odds_null_count = 0
    fair_under_odds_null_count = 0
    zero_or_one_prob_count = 0
    for _, r in canonical.iterrows():
        pmf = r["_pmf_arr"]
        for line in _line_grid_for_stat(r["stat"]):
            p_over = _model_p_over_line(pmf, line)
            if _prob_is_degenerate_boundary(p_over):
                zero_or_one_prob_count += 1

            p_under: float | None = None
            if p_over is not None:
                try:
                    if pd.isna(p_over):
                        p_under = None
                    else:
                        po = float(p_over)
                        if math.isfinite(po):
                            p_under = 1.0 - po
                except (TypeError, ValueError):
                    p_under = None

            fo = _prob_to_american(p_over)
            fu = _prob_to_american(p_under) if p_under is not None else None
            if fo is None:
                fair_over_odds_null_count += 1
            if fu is None:
                fair_under_odds_null_count += 1

            row = {c: r[c] for c in CANONICAL_COLUMNS_BASE if c in r.index}
            row["line"] = float(line)
            row["market_line"] = float(line)
            row["book"] = None
            row["market_over_odds"] = None
            row["market_under_odds"] = None
            row["market_no_vig_over_prob"] = None
            row["model_p_over"] = p_over
            # Direct PMF tail probability for this grid line.
            # Computed from the row's pmf_arr — NEVER a rename of
            # the conditional ``model_p_over``.
            row["p_over"] = _pmf_direct_p_over(pmf, line)
            row["fair_over_odds_american"] = fo
            row["fair_under_odds_american"] = fu
            row["edge"] = None
            # Mark as synthetic model-grid row so diagnostics do not
            # confuse extreme tail p_over (0.99 at line=0.5, 0.001 at
            # line=59.5) with actual sportsbook-line corruption.
            row["line_source"] = "model_grid"
            rows.append(row)
    diag = {
        "fair_over_odds_null_count": int(fair_over_odds_null_count),
        "fair_under_odds_null_count": int(fair_under_odds_null_count),
        "zero_or_one_prob_count": int(zero_or_one_prob_count),
    }
    if not rows:
        return pd.DataFrame(columns=CANONICAL_COLUMNS_BASE), diag
    df = pd.DataFrame(rows)[CANONICAL_COLUMNS_BASE]
    return df, diag


# ── Market comparison (model joined to book offered lines) ──────────────


def build_market_comparison(canonical: pd.DataFrame, odds: pd.DataFrame
                              ) -> tuple[pd.DataFrame, list[str]]:
    if odds.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS_BASE), []

    needed = {"market_stat", "line", "bookmaker_key", "no_vig_over_prob",
              "over_odds_american", "under_odds_american"}
    missing = needed - set(odds.columns)
    if missing:
        # Tolerant: if the snapshot lacks expected columns, fall back to none.
        print(f"  WARN: odds snapshot missing columns {sorted(missing)}; "
              f"market_comparison will be empty")
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
            p_over_direct = _pmf_direct_p_over(c["_pmf_arr"], line)
            row = {col: c[col] for col in CANONICAL_COLUMNS_BASE if col in c.index}
            row["line"] = line
            row["market_line"] = line
            row["book"] = book
            row["market_over_odds"] = (int(m["over_odds_american"])
                                         if pd.notna(m["over_odds_american"]) else None)
            row["market_under_odds"] = (int(m["under_odds_american"])
                                          if pd.notna(m["under_odds_american"]) else None)
            row["market_no_vig_over_prob"] = no_vig
            row["model_p_over"] = p_over
            # Direct PMF tail probability against the offered market line.
            # NEVER reuse ``model_p_over`` here — that field is
            # conditional and is quarantined from public outputs.
            row["p_over"] = p_over_direct
            row["fair_over_odds_american"] = _prob_to_american(p_over)
            pu = None
            if p_over is not None:
                try:
                    if pd.isna(p_over):
                        pu = None
                    else:
                        po = float(p_over)
                        if math.isfinite(po):
                            pu = 1.0 - po
                except (TypeError, ValueError):
                    pu = None
            row["fair_under_odds_american"] = _prob_to_american(pu)
            row["edge"] = ((p_over - no_vig)
                           if (p_over is not None and no_vig is not None)
                           else None)
            # Mark as actual sportsbook-offered line so diagnostics can
            # distinguish these from synthetic model-grid sweep rows.
            row["line_source"] = "market_offered"
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
                    "injury_freshness_status", "lineup_freshness_status",
                    "role_freshness_status")
                   if col in r.index}
            row["k"] = int(k)
            row["p_k"] = float(p)
            rows.append(row)
    if not rows:
        base_cols = [c for c in canonical.columns if c != "_pmf_arr"]
        return pd.DataFrame(columns=base_cols + ["k", "p_k"])
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
    """Parquet keeps full numeric precision; CSV rounds for readability.

    Write-then-readback: writes to a temp path, reads back to verify
    row count and readability, then atomically renames to final path.
    """
    base.parent.mkdir(parents=True, exist_ok=True)
    df = _drop_pmf_arr(df)
    pq_final = base.with_suffix(".parquet")
    pq_tmp = base.with_suffix(".parquet.tmp")
    try:
        df.to_parquet(pq_tmp, index=False)
        import pyarrow.parquet as _pq_rb
        _rb = _pq_rb.read_table(str(pq_tmp))
        if _rb.num_rows != len(df):
            raise RuntimeError(
                f"PARQUET_READBACK_FAIL  path={pq_tmp}"
                f"  written={len(df)}  read_back={_rb.num_rows}"
            )
        pq_tmp.rename(pq_final)
    except Exception as _e:
        if pq_tmp.exists():
            pq_tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"PARQUET_WRITE_READBACK_ERROR  path={pq_final}  error={_e}"
        ) from _e
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


def _run_status_block(*, delivery_date: str, snapshot_type: str,
                       model_version: str, finality_status: str,
                       finality_blockers: list[dict],
                       n_rows: int, n_books: int,
                       coverage: str, role_rollup: dict,
                       injury_freshness: str) -> str:
    """One concise run-status block consumed by README + START_HERE.

    Lists the CLIENT-FACING summary in plain English plus a tight
    bulleted blocker section. Long required-to-resolve text lives only
    in run_manifest.json.
    """
    if finality_status == "final":
        banner = ("status: <b>FINAL</b> &middot; ready for client use")
    else:
        banner = (f"status: <b>PROVISIONAL</b> &middot; "
                  f"safe to use, with the caveats below")
    role_summary = (
        ", ".join(f"{k}: {v}" for k, v in (role_rollup or {}).items())
        or "no role signal")
    blocker_lines = []
    for b in finality_blockers:
        blocker_lines.append(f"- <code>{b['code']}</code> — {b['detail']}")
    blockers_html = ("\n".join(blocker_lines)
                       if blocker_lines else "- (no blockers)")
    return (
        f"<b>Run status — {delivery_date} — snapshot {snapshot_type}</b><br>\n"
        f"{banner}<br>\n"
        f"props: <b>{n_rows}</b> &middot; books: <b>{n_books}</b> "
        f"&middot; market coverage: <b>{coverage}</b> &middot; "
        f"injury freshness: <b>{injury_freshness}</b><br>\n"
        f"role provenance: {role_summary}<br>\n"
        f"model: <code>{model_version}</code>\n"
        f"<br><br>\n"
        f"<b>Caveats</b> (full detail in <code>wizard_of_odds/run_manifest.json</code>):<br>\n"
        f"{blockers_html}\n"
    )


def _run_status_block_md(*, delivery_date: str, snapshot_type: str,
                           model_version: str, finality_status: str,
                           finality_blockers: list[dict],
                           n_rows: int, n_books: int, coverage: str,
                           role_rollup: dict,
                           injury_freshness: str) -> str:
    role_summary = (
        ", ".join(f"`{k}`: {v}" for k, v in (role_rollup or {}).items())
        or "no role signal")
    blocker_md = "\n".join(
        f"- `{b['code']}` — {b['detail']}"
        for b in finality_blockers) or "- _no blockers_"
    banner = ("**FINAL** — ready for client use" if finality_status == "final"
              else "**PROVISIONAL** — safe to use, with the caveats below")
    return (
        f"## Run status — {delivery_date} — snapshot `{snapshot_type}`\n\n"
        f"{banner}\n\n"
        f"- props: **{n_rows}**\n"
        f"- books: **{n_books}**\n"
        f"- market coverage: **{coverage}**\n"
        f"- injury freshness: **{injury_freshness}**\n"
        f"- role provenance: {role_summary}\n"
        f"- model: `{model_version}`\n\n"
        f"### Caveats\n\n"
        f"Full detail (including the `required_to_resolve` field for each "
        f"blocker) is in `wizard_of_odds/run_manifest.json`.\n\n"
        f"{blocker_md}\n"
    )


def write_derek_package(canonical: pd.DataFrame,
                          outcome_long: pd.DataFrame, *,
                          delivery_date: str, pkg_dir: Path,
                          model_only_path: Path | None,
                          run_status_html: str = "",
                          run_status_md: str = "") -> None:
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
                       delivery_date=delivery_date, n_rows=len(canon_clean),
                       run_status_html=run_status_html)
    _write_overview(pkg_dir / "02_MODEL_REVIEW_OVERVIEW.html",
                     delivery_date=delivery_date, canonical=canon_clean,
                     model_only_path=model_only_path)
    _write_pmf_viewer(pkg_dir / "03_PMF_DISTRIBUTION_VIEWER.html",
                       canonical=canon_clean, delivery_date=delivery_date)

    (pkg_dir / "README.md").write_text(
        _readme_text(delivery_date=delivery_date, n_rows=len(canon_clean),
                      run_status_md=run_status_md))


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


def _readme_text(*, delivery_date: str, n_rows: int,
                   run_status_md: str = "") -> str:
    return (
        f"# PMF Model Review Package — {delivery_date}\n\n"
        + (run_status_md + "\n---\n\n" if run_status_md else "")
        + f"Generated by `scripts/build_daily_pmf_delivery.py`. "
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


def _write_start_here(path: Path, *, delivery_date: str, n_rows: int,
                       run_status_html: str = "") -> None:
    status_box = (f'<div class="callout">{run_status_html}</div>'
                  if run_status_html else "")
    body = f"""
<p><b>Delivery date:</b> {delivery_date} &nbsp;&nbsp;
<b>Rows:</b> {n_rows}</p>

{status_box}

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
                       pkg_dir: Path, manifest: dict,
                       run_status_md: str = "") -> None:
    # Guard: refuse to overwrite a complete WoO delivery with an empty/degraded
    # candidate. A complete delivery is defined as having fair_odds_board.parquet
    # with at least 1 row. If the candidate fair_board is empty while an existing
    # complete delivery is present, abort.
    _existing_fob = pkg_dir / "fair_odds_board.parquet"
    if _existing_fob.exists() and len(fair_board) == 0:
        try:
            import pyarrow.parquet as _pq
            _existing_rows = _pq.read_table(str(_existing_fob)).num_rows
            if _existing_rows > 0:
                print(
                    f"WOO_DELIVERY_REFUSED_TO_OVERWRITE_COMPLETE_WITH_EMPTY"
                    f"  pkg_dir={pkg_dir}"
                    f"  existing_fair_odds_rows={_existing_rows}"
                    f"  candidate_fair_odds_rows=0"
                    f"  reason=preserving_complete_delivery"
                )
                raise RuntimeError(
                    f"FATAL: write_woo_package refused to overwrite complete WoO delivery"
                    f" ({_existing_rows} fair_odds rows) with empty candidate at {pkg_dir}"
                )
        except RuntimeError:
            raise
        except Exception as _e:
            print(f"WOO_OVERWRITE_GUARD_CHECK_ERROR  {_e}")

    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize all WoO public outputs by stripping the quarantined
    # public column names (the conditional / legacy probability
    # fields). The internal ``canonical_source`` copies of these
    # frames keep the legacy columns for forensics; only the public
    # ``deliveries/<date>/wizard_of_odds/`` artifacts are stripped.
    _write_csv_parquet(_sanitize_public_columns(fair_board),
                        pkg_dir / "fair_odds_board")
    _write_jsonl(_sanitize_public_columns(fair_board),
                  pkg_dir / "fair_odds_board")

    canon_clean = _sanitize_public_columns(_drop_pmf_arr(canonical))
    _write_csv_parquet(canon_clean, pkg_dir / "full_pmfs_wide")
    # ``full_pmfs_outcome_level`` is long-form (k, p_k) and has no
    # row-level offered line — ``p_over`` does not apply. Keep the
    # outcome distribution columns intact per the public sanitation
    # contract.
    _write_csv_parquet(outcome_long, pkg_dir / "full_pmfs_outcome_level")

    if not market_comp.empty:
        _write_csv_parquet(_sanitize_public_columns(market_comp),
                            pkg_dir / "market_comparison")
    else:
        _write_csv_parquet(
            pd.DataFrame(columns=[
                c for c in CANONICAL_COLUMNS_BASE
                if c not in QUARANTINED_PUBLIC_COLUMNS
            ]),
            pkg_dir / "market_comparison",
        )
    if not edges.empty:
        _write_csv_parquet(_sanitize_public_columns(edges),
                            pkg_dir / "publishable_edges")
    else:
        _write_csv_parquet(
            pd.DataFrame(columns=[
                c for c in CANONICAL_COLUMNS_BASE
                if c not in QUARANTINED_PUBLIC_COLUMNS
            ]),
            pkg_dir / "publishable_edges",
        )

    (pkg_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str))

    cd = manifest.get("count_diagnostics")
    if cd is not None:
        (pkg_dir / "count_diagnostics.json").write_text(
            json.dumps(cd, indent=2, default=str))

    (pkg_dir / "README.md").write_text(
        _woo_readme_text(manifest=manifest, run_status_md=run_status_md))


def _woo_readme_text(*, manifest: dict, run_status_md: str = "") -> str:
    odds = manifest.get("sources", {}).get("odds_snapshot", {}) or {}
    fm = manifest.get("freshness_manifest", {}) or {}
    rc = manifest.get("row_counts", {}) or {}
    ag = manifest.get("after_game", {}) or {
        "status": "pending_outcomes",
        "reason": "scoring runner has not yet been invoked for this delivery",
    }
    delivery_date = manifest.get("delivery_date", "?")
    return (
        f"# Wizard of Odds — {delivery_date}\n\n"
        + (run_status_md + "\n---\n\n" if run_status_md else "")
        + "## Files\n\n"
          "| file | role |\n"
          "|---|---|\n"
          "| `fair_odds_board.{csv,parquet,jsonl}` | one row per (player, stat, line) "
          "with the model's fair over/under American odds. Independent of any book. |\n"
          "| `full_pmfs_wide.{csv,parquet}` | one row per (player, stat) with `pmf_json`, `mean`, `median`, `mode`, `p0`, `p_ge_1 … p_ge_20`. |\n"
          "| `full_pmfs_outcome_level.{csv,parquet}` | long form: one row per (player, stat, k) with `P(outcome=k)`. |\n"
          "| `market_comparison.{csv,parquet}` | one row per (player, stat, line, book) joining the model fair odds to the book's offered odds and no-vig probability. |\n"
          "| `publishable_edges.{csv,parquet}` | subset of `market_comparison` filtered by `\\|edge\\| ≥ threshold` and quality flags. |\n"
          "| `run_manifest.json` | sources, snapshot lifecycle, quality rollup, model version, finality status, and the freshness manifest passthrough. |\n"
          "| `count_diagnostics.json` | fair-odds board null-odds / degenerate-probability counters (see `count_diagnostics` in the manifest). |\n"
          "| `after_game_clv_and_scoring.{csv,parquet,md}` | post-tip CLV + scoring artifacts (added by `scripts/score_daily_pmf_delivery_after_game.py`). |\n\n"
          "## Run summary\n\n"
        + f"- **finality_status**: `{manifest.get('finality_status')}`\n"
          f"- **finality_blockers**: `{manifest.get('finality_blocker_codes') or []}`\n"
          f"- **market_coverage_status**: `{odds.get('coverage_status')}`\n"
          f"- **odds.fetch_status**: `{odds.get('fetch_status')}`\n"
          f"- **books_seen**: `{len(odds.get('books_seen', []) or [])}`\n"
          f"- **freshness.overall_status**: `{fm.get('overall_status')}`\n"
          f"- **availability_freshness_status**: `{fm.get('availability_freshness_status')}`\n"
          f"- **role_freshness_status (rollup)**: `{fm.get('role_freshness_status_rollup') or {}}`\n"
          f"- **tov_status**: `{manifest.get('tov_status')}`\n"
          f"- **row counts**: fair_odds_board={rc.get('fair_odds_board')}, full_pmfs_wide={rc.get('full_pmfs_wide')}, market_comparison={rc.get('market_comparison')}, publishable_edges={rc.get('publishable_edges')}\n"
          f"- **fair_odds_board diagnostics**: `{manifest.get('count_diagnostics', {}).get('fair_odds_board', {})}`\n"
          f"- **after-game scoring**: `{ag.get('status')}`"
        + (f" — {ag.get('reason')}" if ag.get('reason') else "")
        + "\n\n## Hard rules echoed in this package\n\n"
          "- **Model-only PMFs are canonical.** Market columns are reference only; no probability has been adjusted to fit a book line.\n"
          "- **TOV PMFs (when present) come from Phase 8 calibrators with no Phase 10D / 10D.2 overlay** — those overlays did not pass independent validation.\n"
          "- **Sparse market coverage does not drop a row** — every model-only row is emitted; market joins are best-effort.\n"
          "- **Provenance** — `model_version` and `pipeline_run_id` are present on every row and reproduced verbatim in `run_manifest.json`.\n\n"
          "See `docs/daily_pmf_delivery_spec.md` for the full row schema and §7 validation gates, and `docs/daily_data_freshness_runbook.md` for the freshness manifest contract.\n"
    )


def _write_model_performance_stub(*, pkg_dir: Path, delivery_date: str,
                                    n_rows: int, manifest: dict) -> None:
    """Emit a `MODEL_PERFORMANCE_AND_CALIBRATION.md` for the Derek package.

    When outcomes are not yet available, the file is a *stub* recording
    that scoring is pending. The after-game runner overwrites it when it
    posts metrics. We never fabricate outcome metrics here.
    """
    blockers = ", ".join(manifest.get("finality_blocker_codes") or []) \
                or "_none_"
    text = (
        f"# Model performance & calibration — {delivery_date}\n\n"
        f"**after_game_status**: `pending_outcomes`\n\n"
        f"This file will be re-written by "
        f"`scripts/score_daily_pmf_delivery_after_game.py` once box-score "
        f"finals are loaded into `data/player_game_stats.parquet` for "
        f"{delivery_date}.\n\n"
        f"## Rollup at delivery time\n\n"
        f"- delivery_date: `{delivery_date}`\n"
        f"- props in delivery: **{n_rows}**\n"
        f"- finality_status: `{manifest.get('finality_status')}`\n"
        f"- finality_blockers: {blockers}\n"
        f"- model_version: `{manifest.get('model_version')}`\n\n"
        f"## What this file will contain after scoring\n\n"
        f"- props scored, PMF NLL, RPS, mean absolute error\n"
        f"- assigned probability to the realized outcome\n"
        f"- model logloss / Brier per (stat, role_bucket) where market "
        f"lines exist\n"
        f"- CLV summary where morning and close snapshots both exist\n"
        f"- model vs market logloss / Brier comparison **only when "
        f"directly measured** — no claims of market superiority "
        f"otherwise\n"
    )
    (pkg_dir / "MODEL_PERFORMANCE_AND_CALIBRATION.md").write_text(text)


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
    ap.add_argument("--freshness-manifest", default=None,
                     help="path to data/freshness_manifest/{date}.json "
                           "(optional; auto-discovered)")
    ap.add_argument("--rebuild-canonical", action="store_true",
                     help="force rebuild deliveries/{date}/canonical_source/* "
                           "from predictions/all_props_{date}.parquet even "
                           "when an existing canonical parquet is on disk")
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

    # 1. Locate canonical MODEL_ONLY parquet — three fallbacks:
    #    (a) explicit --model-only path
    #    (b) a previously-built MODEL_ONLY parquet under deliveries/{date}/
    #    (c) build one on the fly from predictions/all_props_{date}.parquet
    canonical_built = False
    model_only_path: Path | None = None
    if args.model_only:
        model_only_path = Path(args.model_only).resolve()
    elif (found := _find_model_only_parquet(delivery_date)) is not None \
            and not args.rebuild_canonical:
        model_only_path = found.resolve()
    else:
        preds_path = (Path(args.predictions).resolve() if args.predictions
                      else (REPO_ROOT / "predictions"
                            / f"all_props_{delivery_date}.parquet").resolve())
        if preds_path.exists():
            canonical_dir = (REPO_ROOT / "deliveries" / delivery_date
                              / "canonical_source")
            label = ("rebuilding canonical" if args.rebuild_canonical
                     else "building canonical")
            print(f"  {label} from {preds_path.relative_to(REPO_ROOT)} …")
            model_only_path = build_canonical_from_predictions(
                preds_path, date=delivery_date,
                canonical_dir=canonical_dir).resolve()
            canonical_built = True
        else:
            print(f"ERROR: no MODEL_ONLY parquet for {delivery_date} and "
                  f"no predictions/all_props_{delivery_date}.parquet to "
                  f"build from. Run scripts/predict.py first.")
            return 2
    try:
        rel_path = model_only_path.relative_to(REPO_ROOT)
    except ValueError:
        rel_path = model_only_path
    print(f"  model_only: {rel_path}"
          + ("  (auto-built)" if canonical_built else ""))
    model_only = load_model_only(model_only_path)
    print(f"  rows: {len(model_only):,}")

    # 2. Load Odds API snapshot (no HTTP calls; we only consume disk).
    if args.odds_snapshot:
        odds_path: Path | None = Path(args.odds_snapshot)
        odds_pair_files = [odds_path]
    else:
        odds_pair_files = _list_odds_pair_files(delivery_date)
        odds_path = odds_pair_files[-1] if odds_pair_files else None
    if odds_pair_files:
        for fp in odds_pair_files:
            print(f"  odds_snapshot: {_display_path(fp)}")
    else:
        print("  odds_snapshot: <none>")
    odds = load_odds_snapshot(odds_path, all_paths=odds_pair_files)

    # 2b. Freshness manifest (input — written by refresh_daily_inputs.py).
    fm_path = (Path(args.freshness_manifest)
               if args.freshness_manifest
               else _find_freshness_manifest(delivery_date))
    freshness_manifest = _load_freshness_manifest(fm_path)
    if freshness_manifest is not None:
        try:
            rel_fm = fm_path.relative_to(REPO_ROOT)
        except ValueError:
            rel_fm = fm_path
        print(f"  freshness_manifest: {rel_fm}  "
              f"(overall={freshness_manifest.get('overall_status')})")
    else:
        print("  freshness_manifest: <none>")

    # 3. Build canonical row frame.
    injury_path = REPO_ROOT / "data" / "player_availability_asof.parquet"
    (
        bdl_lineup_players,
        bdl_lineup_games,
        bdl_lineup_snapshot,
    ) = _load_bdl_lineup_context(delivery_date)
    if bdl_lineup_snapshot.has_any_rows:
        print(
            "  bdl lineup snapshot: "
            f"games={len(bdl_lineup_snapshot.game_lookup)} "
            f"manifest_last_updated_utc="
            f"{bdl_lineup_snapshot.manifest_last_updated_utc}"
        )
    canonical = build_canonical_rows(
        model_only, delivery_date=delivery_date,
        snapshot_type=snapshot_type, snapshot_time_utc=snapshot_time_utc,
        model_version=model_version, pipeline_run_id=pipeline_run_id,
        injury_path=injury_path,
        bdl_lineup_players=bdl_lineup_players,
        bdl_lineup_games=bdl_lineup_games,
        bdl_lineup_snapshot=bdl_lineup_snapshot,
    )
    print(f"  canonical rows: {len(canonical)}")

    # 4. Build derived views.
    fair_board, fair_board_diag = build_fair_odds_board(canonical)
    print(f"  fair_odds_board rows: {len(fair_board):,}  diagnostics: {fair_board_diag}")
    _validate_fair_american_odds_columns(fair_board, label="fair_odds_board")
    market_comp, books_seen = build_market_comparison(canonical, odds)
    _validate_fair_american_odds_columns(market_comp, label="market_comparison")
    edges = build_publishable_edges(market_comp,
                                      edge_threshold=args.edge_threshold)
    outcome_long = build_outcome_level(canonical)

    _validate_fair_american_odds_columns(edges, label="publishable_edges")

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

    # 6. Write Derek package.  (run_status block needs the manifest values
    #    that step 7 computes; we build the manifest first, then write.)
    derek_dir = REPO_ROOT / "deliveries" / delivery_date / "pmf_model_review_package"

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
        "role_freshness_status":
            canonical["role_freshness_status"].value_counts().to_dict()
            if not canonical.empty and "role_freshness_status" in canonical.columns
            else {},
    }
    # Target-stats completeness: expected vs in delivery.
    expected_stats = list(SUPPORTED_STATS)  # M8.1: mission canonical 11
    in_delivery_stats = sorted(canonical["stat"].astype(str).unique().tolist())
    missing_stats = sorted(set(expected_stats) - set(in_delivery_stats))
    extra_stats = sorted(set(in_delivery_stats) - set(expected_stats))
    tov_status_field = ("present" if "tov" in in_delivery_stats
                        else "missing_from_prediction_source")

    # Odds-fetch status: explicit signal even when the runner is disk-only.
    if args.no_odds_fetch:
        odds_fetch_status = "skipped:no_odds_fetch_flag"
    elif odds_path:
        odds_fetch_status = "consumed_from_disk"
    else:
        odds_fetch_status = "skipped:no_disk_snapshot"

    # Finality status — does this delivery have everything it needs to ship?
    # Each blocker is a stable string code with an explicit meaning.
    finality_blockers: list[dict] = []

    market_counts = quality_rollup.get("market_coverage_status", {})
    market_none = int(market_counts.get("none", 0) or market_counts.get("None", 0) or 0)
    if market_none:
        finality_blockers.append({
            "code": "market_coverage_none",
            "detail": f"{market_none} rows have no market coverage.",
            "required_to_resolve": "Attach a valid odds snapshot for this delivery date.",
        })

    # Row-level injury freshness verdict. The legacy rollup compared
    # ``injury_freshness_status`` against the literal string "fresh",
    # which is a *file mtime* taxonomy emitted by ``_injury_freshness``
    # — it ignored the actual statuses written by the NBA fetcher
    # (``latest_valid_report_selected`` / ``fallback_used``) and never
    # consulted the row-level ``injury_report_fetched_at_utc``
    # timestamps. The new ``classify_canonical_injury_freshness``
    # helper makes the rollup a strict function of row-level evidence.
    if not canonical.empty:
        injury_verdict = classify_canonical_injury_freshness(
            statuses=canonical.get(
                "injury_freshness_status", pd.Series(dtype="object")
            ).tolist(),
            fetched_at_values=canonical.get(
                "injury_report_fetched_at_utc",
                pd.Series([None] * len(canonical), dtype="object"),
            ).tolist(),
        )
    else:
        injury_verdict = classify_canonical_injury_freshness(
            statuses=[], fetched_at_values=[]
        )
    if not injury_verdict.is_fresh_overall:
        finality_blockers.append({
            "code": "injury_very_stale",
            "detail": injury_verdict.to_manifest_detail(),
            "required_to_resolve": (
                "Wait for the NBA official injury report to be published "
                "for the slate, or regenerate stat-grid PMFs in the "
                "Python 3.11 environment with nbainjuries available. "
                "File mtime alone is no longer accepted; canonical rows "
                "must carry a row-level injury_freshness_status of "
                "latest_valid_report_selected/fallback_used/fresh."
            ),
        })

    if missing_stats or extra_stats:
        finality_blockers.append({
            "code": "target_stats_mismatch",
            "detail": (
                f"missing={missing_stats}; "
                f"extra_relative_to_supported={extra_stats}"
            ),
            "required_to_resolve": (
                "Regenerate production PMFs so delivery stats match "
                "MISSION_REQUIRED_TARGETS_CANONICAL (12 stats incl. ra)."
            ),
        })

    lineup_counts = quality_rollup.get("lineup_freshness_status", {})
    lineup_has_confirmed = any(
        str(k).lower() == "confirmed" and int(v) > 0
        for k, v in lineup_counts.items()
    )
    if snapshot_type != "after_game" and not lineup_has_confirmed:
        finality_blockers.append({
            "code": "lineup_unconfirmed",
            "detail": (
                "No confirmed-lineup rows were present. This is acceptable "
                "for morning/provisional outputs but not final lock outputs."
            ),
            "required_to_resolve": (
                "Regenerate near lock after official lineups are available."
            ),
        })

    role_counts = quality_rollup.get("role_freshness_status", {})
    role_missing = int(role_counts.get("missing", 0) or role_counts.get("None", 0) or 0)
    if role_missing:
        finality_blockers.append({
            "code": "role_bucket_missing",
            "detail": f"{role_missing} rows have missing role_bucket.",
            "required_to_resolve": (
                "Regenerate stat-grid PMFs with role/minutes metadata."
            ),
        })

    finality_status = "final" if not finality_blockers else "provisional"
    finality_blocker_codes = [b["code"] for b in finality_blockers]

    manifest = {
        "delivery_date": delivery_date,
        "pipeline_run_id": pipeline_run_id,
        "snapshot_type": snapshot_type,
        "snapshot_time_utc": snapshot_time_utc,
        "model_version": model_version,
        "phase8_calibration_source": (
            f"phase8_role_aware_pmf_cal_v1+{_ROLE_AWARE_BLEND_POLICY}"
            if _ROLE_AWARE_BLEND_POLICY
            else "phase8_role_aware_pmf_cal_v1"
        ),
        "phase8_blend_policy": _ROLE_AWARE_BLEND_POLICY,
        "finality_status": finality_status,
        "finality_blocker_codes": finality_blocker_codes,
        "finality_blockers": finality_blockers,
        "tov_overlay": "off",
        "tov_overlay_reason": TOV_STATUS_REASON,
        "tov_status": tov_status_field,
        "target_stats": {
            "expected": expected_stats,
            "in_delivery": in_delivery_stats,
            "missing": missing_stats,
            "extra_relative_to_supported": extra_stats,
        },
        "sources": {
            "model_only_parquet": {
                "path": _repo_rel(model_only_path),
                "mtime_utc": _file_mtime_iso_utc(model_only_path),
                "sha256": _file_sha256(model_only_path),
                "auto_built_from_predictions": bool(canonical_built),
            },
            "predictions_parquet": ({
                "path": str(
                    (REPO_ROOT / "predictions"
                     / f"all_props_{delivery_date}.parquet")
                    .relative_to(REPO_ROOT)),
                "mtime_utc": _file_mtime_iso_utc(
                    REPO_ROOT / "predictions"
                    / f"all_props_{delivery_date}.parquet"),
            }),
            "availability_table": {
                "path": (str(injury_path.relative_to(REPO_ROOT))
                         if injury_path.exists() else None),
                "mtime_utc": _file_mtime_iso_utc(injury_path),
                "freshness_status": _injury_freshness(injury_path),
            },
            "odds_snapshot": ({
                "path": _repo_rel(odds_path),
                "mtime_utc": _file_mtime_iso_utc(odds_path),
                "books_seen": books_seen,
                "coverage_status": coverage,
                "fetch_status": odds_fetch_status,
            } if odds_path else {
                "path": None, "mtime_utc": None, "books_seen": [],
                "coverage_status": "none",
                "fetch_status": odds_fetch_status,
            }),
        },
        "row_counts": {
            "fair_odds_board": int(len(fair_board)),
            "full_pmfs_wide": int(len(canonical)),
            "market_comparison": int(len(market_comp)),
            "publishable_edges": int(len(edges)),
        },
        "count_diagnostics": {
            "fair_odds_board": fair_board_diag,
        },
        "quality_rollup": quality_rollup,
        "warnings": [*msgs_canon, *msgs_edges],
        "no_odds_fetch": bool(args.no_odds_fetch),
        "freshness_manifest": ({
            "path": _display_path(fm_path)
                     if fm_path is not None else None,
            "built_at_utc": freshness_manifest.get("built_at_utc"),
            "overall_status": freshness_manifest.get("overall_status"),
            "odds_status": freshness_manifest.get("odds", {}).get("status"),
            "regions_requested":
                freshness_manifest.get("regions_requested"),
            "books_seen": freshness_manifest.get("odds", {}).get("books_seen"),
            "tov_status": freshness_manifest.get("tov_status"),
            "predictions_mtime_utc":
                freshness_manifest.get("predictions", {}).get("mtime_utc"),
            "availability_freshness_status":
                (freshness_manifest.get("availability_table", {})
                 .get("freshness_status")),
            "finals_finality_status":
                freshness_manifest.get("finals", {}).get("finality_status"),
            "role_freshness_status_rollup":
                quality_rollup.get("role_freshness_status"),
        } if freshness_manifest is not None else {
            "path": None, "overall_status": "missing",
            "odds_status": odds_fetch_status,
            "regions_requested": None,
            "books_seen": books_seen,
            "tov_status": tov_status_field,
            "predictions_mtime_utc":
                _file_mtime_iso_utc(REPO_ROOT / "predictions"
                                      / f"all_props_{delivery_date}.parquet"),
            "availability_freshness_status":
                _injury_freshness(injury_path),
            "finals_finality_status": "unknown",
            "role_freshness_status_rollup":
                quality_rollup.get("role_freshness_status"),
        }),
    }

    # 7b. Build run-status block now that the manifest is finalised, then
    #     write the Derek package with that block embedded.
    injury_rollup = (canonical["injury_freshness_status"]
                       .value_counts().to_dict()
                       if not canonical.empty else {})
    injury_summary = max(injury_rollup, key=injury_rollup.get,
                          default="unknown")
    run_status_html = _run_status_block(
        delivery_date=delivery_date, snapshot_type=snapshot_type,
        model_version=model_version, finality_status=finality_status,
        finality_blockers=finality_blockers,
        n_rows=int(len(canonical)),
        n_books=len(books_seen),
        coverage=coverage,
        role_rollup=quality_rollup.get("role_freshness_status", {}),
        injury_freshness=injury_summary)
    run_status_md = _run_status_block_md(
        delivery_date=delivery_date, snapshot_type=snapshot_type,
        model_version=model_version, finality_status=finality_status,
        finality_blockers=finality_blockers,
        n_rows=int(len(canonical)),
        n_books=len(books_seen),
        coverage=coverage,
        role_rollup=quality_rollup.get("role_freshness_status", {}),
        injury_freshness=injury_summary)

    write_derek_package(canonical, outcome_long,
                          delivery_date=delivery_date, pkg_dir=derek_dir,
                          model_only_path=model_only_path,
                          run_status_html=run_status_html,
                          run_status_md=run_status_md)
    _write_model_performance_stub(
        pkg_dir=derek_dir, delivery_date=delivery_date,
        n_rows=int(len(canonical)), manifest=manifest)
    print(f"  wrote {derek_dir.relative_to(REPO_ROOT)}")

    # 8. Write Wizard of Odds package.
    woo_dir = REPO_ROOT / "deliveries" / delivery_date / "wizard_of_odds"
    write_woo_package(canonical, fair_board, market_comp, edges,
                       outcome_long, pkg_dir=woo_dir, manifest=manifest,
                       run_status_md=run_status_md)
    print(f"  wrote {woo_dir.relative_to(REPO_ROOT)}")
    print(f"  publishable_edges: {len(edges)} rows "
          f"(edge ≥ {args.edge_threshold})")
    print(f"  finality_status: {finality_status} "
          f"(blockers: {finality_blocker_codes or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
