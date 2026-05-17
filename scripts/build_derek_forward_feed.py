"""Build Derek's forward-looking daily PMF feed.

Emits one row per (player, stat) for each available market line, plus a
model-only row for every PMF without a corresponding market quote. PMFs
are sourced from `deliveries/{date}/pmf_model_review_package/machine_readable/model_only.parquet`
(canonical, model-only, never market-anchored). Market lines are
sourced from `deliveries/{date}/wizard_of_odds/market_comparison.parquet`
as reference-only fields.

Outputs land under `deliveries/{date}/derek_forward_feed/` and never
fabricate predictions, lineups, role buckets, or odds. If a lineup
snapshot package is unavailable the builder writes
`lineup_snapshot_status.json` with an honest status code; it never
synthesises lineup data.

Phase 12C — `--snapshot {morning,lineup,both}` controls which snapshot
files are produced. The builder reads only existing on-disk packages
and the run manifest; any field that cannot be sourced from the
manifest is left null rather than imputed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEL_DIR = REPO_ROOT / "deliveries"
FRESH_DIR = REPO_ROOT / "data" / "freshness_manifest"

P_GE_KEYS = [f"p_ge_{i}" for i in range(1, 21)]

IDENTITY_COLS = [
    "snapshot_type",
    "snapshot_time_utc",
    "delivery_date",
    "game_id",
    "game_start_time_utc",
    "player_id",
    "player_name",
    "team",
    "opponent",
    "is_home",
    "stat",
]
PMF_COLS = (
    ["pmf_json", "pmf_mean", "mean", "median", "mode", "p0"]
    + P_GE_KEYS
    + [
        "model_version",
        "pmf_source",
        "calibration_source",
        "role_bucket",
        "role_source",
        "calibration_confidence",
        # M8.9 minutes-model + eligibility passthrough. The upstream
        # canonical model_only.parquet carries these columns produced
        # by the player-game eligibility gate
        # (src/nba_props_model/pipelines/player_game_eligibility.py)
        # plus the minutes builder
        # (scripts/build_minutes_predictions.py). Without listing them
        # here the morning_snapshot strips them and the downstream
        # unified feed cannot reproduce the upstream eligibility
        # contract.
        "minutes_mean",
        "minutes_q50",
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
        "minutes_source",
        "minutes_model_version",
    ]
)
MARKET_COLS = [
    "sportsbook",
    "book",
    "market_key",
    "line",
    "market_line",
    "p_over",
    "over_price_american",
    "under_price_american",
    "market_no_vig_over_prob",
    "market_no_vig_under_prob",
    "model_p_under",
    "fair_over_odds_american",
    "fair_under_odds_american",
    "edge",
    "edge_over",
    "edge_under",
    "market_snapshot_time_utc",
    "market_coverage_status",
]
QUALITY_COLS = [
    "finality_status",
    "finality_blocker_codes",
    "injury_freshness_status",
    "availability_freshness_status",
    "lineup_freshness_status",
    "role_freshness_status",
    "odds_freshness_status",
    "outcomes_freshness_status",
    "tov_status",
    "pmf_valid",
    "pmf_sum_error",
    # Row-level provenance fields propagated from
    # stat_grid → canonical MODEL_ONLY → market_comparison so the
    # per-snapshot feed can carry them too. Without these, the
    # unified ``derek_forward_feed.parquet`` (built from
    # ``morning_snapshot.parquet``) loses
    # ``lineup_last_updated_utc`` and
    # ``injury_report_fetched_at_utc`` and falls back to ``None``.
    "expected_lineup_status",
    "official_lineup_status",
    "lineup_source",
    "lineup_last_updated_utc",
    "injury_context_source",
    "injury_report_fetched_at_utc",
]

FEED_COLS = IDENTITY_COLS + PMF_COLS + MARKET_COLS + QUALITY_COLS


# ── Source-contract guard ──────────────────────────────────────────────
#
# Derek's forward feed must be built from the full, validated model PMF
# surface — i.e. canonical MODEL_ONLY (built from stat-grid) joined with
# market_comparison (built from canonical/stat-grid + market lines). It
# must NEVER source projection / probability / PMF / edge fields from
# the raw ``predictions/all_props_*.parquet`` snapshot or the
# pre-canonical slate universe seed (which is identity-only and predates
# stat-grid). The required source graph is:
#
#   feature_snapshot
#     → minutes_predictions / minutes_predictions_eligible
#     → stat_grid (12 mission stats)
#     → canonical MODEL_ONLY built from stat_grid
#     → market_comparison
#     → derek_forward_feed   ← this script
#
# The guard below renders ``DEREK_FORWARD_FEED_SOURCE_CONTRACT_PASS`` on
# legitimate inputs and ``DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION``
# with the offending substring on attempted regressions (and exits 2).

DEREK_FEED_MODEL_SOURCE_CONTRACT = "stat_grid_canonical_market_comparison"

DEREK_FEED_FORBIDDEN_SOURCE_SUBSTRINGS = (
    "predictions/all_props_",
    "precanonical_slate_universe_",
)


def _stat_grid_source_path(repo_root: Path, date: str) -> Path:
    return repo_root / "predictions" / f"stat_grid_{date}.parquet"


def _canonical_model_only_source_path(repo_root: Path, date: str) -> Path:
    return (
        repo_root
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )


def _assert_derek_feed_source_contract(
    *,
    date: str,
    model_only_path: Path,
    market_comparison_path: Path | None,
) -> dict:
    """Hard guard before any rows are emitted.

    ``model_only_path`` must point at the canonical-derived review
    package parquet under ``deliveries/<date>/pmf_model_review_package/
    machine_readable/model_only.parquet`` (which is dual-written from
    canonical MODEL_ONLY by ``build_daily_pmf_delivery.py``). The
    canonical MODEL_ONLY parquet itself MUST be the
    stat-grid-derived ``deliveries/<date>/canonical_source/
    player_prop_pmfs_tonight_MODEL_ONLY.parquet`` — its existence is
    confirmed here so callers cannot silently route Derek to a raw
    ``predictions/all_props_*.parquet`` shortcut.

    Returns the lineage descriptor that is stamped on the feed
    manifest so post-run forensics can prove the source contract was
    honored.

    Emits ``DEREK_FORWARD_FEED_SOURCE_CONTRACT_PASS`` on success and
    raises SystemExit(2) with
    ``DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION ...`` on any
    violation.
    """
    model_src = str(model_only_path)
    for bad in DEREK_FEED_FORBIDDEN_SOURCE_SUBSTRINGS:
        if bad in model_src:
            print(
                "DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION "
                f"date={date} field=model_source forbidden_substring={bad!r} "
                f"path={model_src}",
                file=sys.stderr,
            )
            raise SystemExit(2)
    if market_comparison_path is not None:
        mc_src = str(market_comparison_path)
        for bad in DEREK_FEED_FORBIDDEN_SOURCE_SUBSTRINGS:
            if bad in mc_src:
                print(
                    "DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION "
                    f"date={date} field=market_comparison_source "
                    f"forbidden_substring={bad!r} path={mc_src}",
                    file=sys.stderr,
                )
                raise SystemExit(2)

    canonical_path = _canonical_model_only_source_path(REPO_ROOT, date)
    stat_grid_path = _stat_grid_source_path(REPO_ROOT, date)

    if not canonical_path.is_file():
        print(
            "DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION "
            f"date={date} field=canonical_source "
            f"reason=canonical_MODEL_ONLY_missing path={canonical_path}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if not stat_grid_path.is_file():
        print(
            "DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION "
            f"date={date} field=stat_grid_source "
            f"reason=stat_grid_parquet_missing path={stat_grid_path}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(REPO_ROOT))
        except ValueError:
            return str(p)

    lineage = {
        "model_source_contract": DEREK_FEED_MODEL_SOURCE_CONTRACT,
        "model_source": _rel(model_only_path),
        "canonical_source": _rel(canonical_path),
        "stat_grid_source": _rel(stat_grid_path),
        "market_comparison_source": (
            _rel(market_comparison_path)
            if market_comparison_path is not None
            else None
        ),
    }
    print(
        "DEREK_FORWARD_FEED_SOURCE_CONTRACT_PASS "
        f"date={date} contract={DEREK_FEED_MODEL_SOURCE_CONTRACT} "
        f"model_source={lineage['model_source']} "
        f"canonical_source={lineage['canonical_source']} "
        f"stat_grid_source={lineage['stat_grid_source']} "
        f"market_comparison_source={lineage['market_comparison_source']}"
    )
    return lineage


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"  warning: could not parse {path}: {e!r}", file=sys.stderr)
        return None


def _coerce_blocker_codes(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, list):
        return ",".join(str(x) for x in v) if v else None
    return str(v)


def _role_source_from_freshness(role_freshness: Any) -> str | None:
    if not role_freshness or (isinstance(role_freshness, float) and math.isnan(role_freshness)):
        return None
    if role_freshness == "derived_from_projected_minutes":
        return "projected_minutes"
    if role_freshness == "missing":
        return None
    return str(role_freshness)


def _validate_pmf(pmf_json: Any) -> tuple[str, float]:
    """Return (pmf_valid, pmf_sum_error). pmf_valid is 'ok' if PMF sums to
    1 within 1e-6, has no negatives, and no non-finite values; otherwise
    one of {'invalid_negative', 'invalid_non_finite', 'invalid_sum'}."""
    if not pmf_json:
        return ("missing", float("nan"))
    try:
        d = json.loads(pmf_json) if isinstance(pmf_json, str) else dict(pmf_json)
    except Exception:
        return ("invalid_json", float("nan"))
    total = 0.0
    for v in d.values():
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            return ("invalid_non_finite", float("nan"))
        if v < 0:
            return ("invalid_negative", float(abs(1.0 - sum(d.values()))))
        total += float(v)
    err = abs(1.0 - total)
    if err > 1e-6:
        return ("invalid_sum", err)
    return ("ok", err)



BDL_PLAYER_PROPS_URL = "https://api.balldontlie.io/v2/odds/player_props"

# Authoritative BDL prop_type → internal stat key map.
#
# Source: https://docs.balldontlie.io/nba/api-reference/odds-player-props
# (Supported Prop Types table — over_under markets only).
#
# Notes per BDL docs (verified 2026-05-17):
#   • BDL does NOT publish a turnovers ("tov") prop_type — production
#     Derek summary therefore cannot expose a market_line for tov.
#   • BDL does NOT publish a stocks / blocks_steals / steals_blocks
#     combo prop_type — production Derek summary therefore cannot expose
#     a market_line for stocks. Stocks remains an internal model stat.
#   • First-quarter (``points_1q`` / ``rebounds_1q`` / ``assists_1q``),
#     first-3-minute, ``double_double``, ``triple_double`` and milestone
#     markets are intentionally excluded from this mapping per the
#     user contract (only main over_under lines for the 10 single+combo
#     stats below are eligible for the Derek summary).
BDL_PROP_TYPE_TO_STAT = {
    "points": "pts",
    "rebounds": "reb",
    "assists": "ast",
    "threes": "fg3m",
    "blocks": "blk",
    "steals": "stl",
    "points_rebounds": "pr",
    "points_assists": "pa",
    "rebounds_assists": "ra",
    "points_rebounds_assists": "pra",
}

# Stats that exist in the internal PMF surface but are NOT exposed by
# BDL as over_under prop_types — included here for documentation /
# guard tests so accidental future additions of "turnovers"/"stocks"
# trigger a verifier failure rather than silently fabricating lines.
BDL_UNSUPPORTED_INTERNAL_STATS = ("tov", "stocks")

# Canonical PMF column priority for the Derek BDL main-line summary.
#
# Upstream snapshots have shipped the final per-row PMF payload under
# different names across the M8.x line: ``pmf_json`` is the historical
# name on canonical MODEL_ONLY, ``pmf_active`` is what the M8.9 active-
# PMF promotion writes, and ``pmf`` is the legacy fallback used in some
# pre-M8.9 calibration outputs. The Derek forward-feed writer must be
# tolerant of all three so the BDL main-line summary builder always
# sees a real PMF column, regardless of which upstream produced the
# snapshot. The writer normalises whichever column it finds into
# ``pmf_json`` before calling ``_build_derek_bdl_main_line_summary``;
# the public ``derek_forward_feed.*`` files still drop ``pmf_json``
# (it is a private feed column) — only the in-memory ``out_df`` and
# the summary builder ever see it.
PMF_VALUE_COLUMN_PRIORITY: tuple[str, ...] = ("pmf_json", "pmf_active", "pmf")


def _pick_row_pmf_value(row_like: Any) -> Any:
    """Return the first non-empty PMF payload from a row-like object.

    Iterates :data:`PMF_VALUE_COLUMN_PRIORITY` in order and returns the
    first value that is neither ``None`` nor ``NaN``. ``row_like`` may
    be a ``pd.Series`` (as yielded by ``DataFrame.iterrows()``) or any
    mapping that supports ``.get(key)``. Returns ``None`` if no PMF
    payload is available.

    This is the single source of truth for "which upstream column
    carries the final PMF for this row" inside
    ``scripts/build_derek_forward_feed.py``.
    """
    try:
        getter = row_like.get
    except AttributeError:
        return None
    for col in PMF_VALUE_COLUMN_PRIORITY:
        try:
            v = getter(col)
        except Exception:
            continue
        if v is None:
            continue
        if isinstance(v, float) and math.isnan(v):
            continue
        return v
    return None


def _ensure_pmf_json_column(df: pd.DataFrame) -> pd.DataFrame:
    """Return ``df`` with a guaranteed ``pmf_json`` column.

    If ``pmf_json`` is missing entirely but a fallback PMF column
    (``pmf_active`` / ``pmf``) is present, this materialises ``pmf_json``
    from the first available fallback. If no PMF column is present at
    all, ``df`` is returned unchanged so the downstream builder still
    raises its explicit ``DEREK_BDL_SUMMARY_MISSING_REQUIRED_COLUMNS``
    error (better signal than silently writing an empty summary).

    Belt-and-suspenders alongside the per-row helper above: a future
    refactor that removes the ``pmf_json`` key from the row dict would
    otherwise re-introduce the production failure mode where the BDL
    summary builder sees no PMF column at all.
    """
    if df is None or df.empty:
        return df
    if "pmf_json" in df.columns:
        return df
    fallback = next(
        (c for c in PMF_VALUE_COLUMN_PRIORITY[1:] if c in df.columns),
        None,
    )
    if fallback is None:
        return df
    out = df.copy()
    out["pmf_json"] = out[fallback]
    print(
        "DEREK_BDL_SUMMARY_PMF_NORMALIZED "
        f"source_column={fallback} target_column=pmf_json"
    )
    return out

# Quarantined public column names — must not appear in any persisted
# public delivery output (CSV / Parquet / JSONL / JSON / HTML embed).
QUARANTINED_PUBLIC_COLUMNS: tuple[str, ...] = (
    "model_projected_mean",
    "model_probability_over_market_line",
    "model_prob_over_raw",
    "model_prob_over_active",
    "model_p_over",
)


def _drop_quarantined_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with the quarantined public columns removed.

    Public delivery writers MUST call this before persisting any CSV /
    Parquet / JSONL Derek output. Quarantined fields stay available on
    internal intermediate frames (so verifiers and audit scripts can
    still cross-check); they are only stripped at the writer boundary.
    """
    if df is None:
        return df
    cols = [c for c in QUARANTINED_PUBLIC_COLUMNS if c in df.columns]
    if not cols:
        return df
    return df.drop(columns=cols)


def _populate_pmf_native_fields(rows: list[dict]) -> None:
    """In-place: stamp ``pmf_mean`` + ``market_line`` + ``p_over`` on each
    public feed row.

    Computes ``p_over`` directly as ``sum_{outcome > line} PMF[outcome]``
    against the row's own PMF surface. Does NOT copy or rename
    ``model_p_over`` / ``model_prob_over_*`` — those are quarantined.

    Rules:
      • ``pmf_mean`` = direct expectation from row PMF when a parseable
        PMF exists, else fall back to the upstream ``mean`` / existing
        ``pmf_mean`` value.
      • ``market_line`` = explicit ``market_line`` when present, else
        the row's existing ``line``.
      • ``p_over`` populated only when both a numeric line and a valid
        PMF exist; otherwise left as ``None``.
    """
    for row in rows:
        pmf_arr = _pmf_array_from_jsonish(row.get("pmf_json"))
        if pmf_arr is not None:
            row["pmf_mean"] = _pmf_direct_mean(pmf_arr)
        elif row.get("pmf_mean") is None:
            existing_mean = row.get("mean")
            row["pmf_mean"] = (
                float(existing_mean)
                if isinstance(existing_mean, (int, float))
                and existing_mean is not None
                and math.isfinite(float(existing_mean))
                else None
            )

        market_line = row.get("market_line")
        if market_line is None:
            market_line = row.get("line")
        row["market_line"] = (
            float(market_line)
            if isinstance(market_line, (int, float))
            and market_line is not None
            and math.isfinite(float(market_line))
            else None
        )

        if pmf_arr is not None and row["market_line"] is not None:
            row["p_over"] = _pmf_direct_p_over(pmf_arr, row["market_line"])
        else:
            row["p_over"] = None

BDL_STAT_TO_PROP_TYPE = {v: k for k, v in BDL_PROP_TYPE_TO_STAT.items()}

DEREK_UNIQUE_SUMMARY_COLS = [
    "player_name",
    "projected_minutes",
    "stat",
    "pmf_mean",
    "market_line",
    "p_over",
]


def _pmf_array_from_jsonish(x: Any) -> list[float] | None:
    if x is None:
        return None
    try:
        d = json.loads(x) if isinstance(x, str) else dict(x)
    except Exception:
        return None

    vals: dict[int, float] = {}
    for k, v in d.items():
        try:
            kk = int(float(k))
            vv = float(v)
        except Exception:
            continue
        if kk < 0 or not math.isfinite(vv):
            continue
        vals[kk] = max(0.0, vv)

    if not vals:
        return None

    arr = [0.0] * (max(vals) + 1)
    for k, v in vals.items():
        arr[k] = v

    s = sum(arr)
    if not math.isfinite(s) or s <= 0:
        return None

    return [v / s for v in arr]


def _pmf_direct_mean(pmf_arr: list[float]) -> float:
    return float(sum(i * p for i, p in enumerate(pmf_arr)))


def _pmf_direct_p_over(pmf_arr: list[float], line: Any) -> float | None:
    try:
        line_f = float(line)
    except Exception:
        return None
    return float(sum(p for i, p in enumerate(pmf_arr) if i > line_f))


def _float_or_none(v: Any) -> float | None:
    try:
        if v is None:
            return None
        f = float(v)
        if not math.isfinite(f):
            return None
        return f
    except Exception:
        return None


def _fetch_bdl_player_props_for_game_prop_type(
    *,
    game_id: int,
    prop_type: str,
    api_key: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor: Any = None
    page: Any = None
    seen_tokens: set[tuple[Any, Any]] = set()

    while True:
        params: dict[str, Any] = {
            "game_id": int(game_id),
            "prop_type": prop_type,
            "per_page": 100,
        }
        if cursor is not None:
            params["cursor"] = cursor
        if page is not None:
            params["page"] = page

        url = f"{BDL_PLAYER_PROPS_URL}?{urlencode(params)}"
        req = Request(url, headers={"Authorization": api_key})

        try:
            with urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                "BDL_PLAYER_PROPS_REQUEST_FAILED "
                f"game_id={game_id} prop_type={prop_type} "
                f"status={exc.code} body={body[:500]}"
            ) from exc

        data = payload.get("data", payload if isinstance(payload, list) else [])
        if isinstance(data, list):
            rows.extend(r for r in data if isinstance(r, dict))

        meta = payload.get("meta") if isinstance(payload, dict) else {}
        meta = meta or {}
        next_cursor = meta.get("next_cursor") or meta.get("nextCursor")
        next_page = meta.get("next_page") or meta.get("nextPage")

        token = (next_cursor, next_page)
        if token in seen_tokens:
            break
        seen_tokens.add(token)

        if next_cursor:
            cursor = next_cursor
            page = None
            time.sleep(0.05)
            continue
        if next_page:
            page = next_page
            cursor = None
            time.sleep(0.05)
            continue
        break

    return rows


def _build_derek_bdl_main_line_summary(out_df: pd.DataFrame) -> pd.DataFrame:
    """Build Derek's one-row-per-player/stat BDL main-line summary.

    This intentionally does not use WoO alternate-line rows and does not use
    model_prob_over_* fields. p_over is computed directly from the PMF.
    """
    if out_df.empty:
        return pd.DataFrame(columns=DEREK_UNIQUE_SUMMARY_COLS)

    api_key = os.environ.get("BDL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("BDL_API_KEY not set; cannot build Derek BDL main-line summary")

    required = {"game_id", "player_id", "player_name", "stat"}
    missing = sorted(c for c in required if c not in out_df.columns)
    if missing:
        raise RuntimeError(f"DEREK_BDL_SUMMARY_MISSING_REQUIRED_COLUMNS: {missing}")

    pmf_value_col = next(
        (c for c in ("pmf_json", "pmf_active", "pmf") if c in out_df.columns),
        None,
    )
    if pmf_value_col is None:
        raise RuntimeError(
            "DEREK_BDL_SUMMARY_MISSING_REQUIRED_COLUMNS: "
            "one of pmf_json, pmf_active, pmf is required"
        )

    base = out_df.copy()
    base["stat"] = base["stat"].astype(str).str.lower()
    base = base[base["stat"].isin(BDL_STAT_TO_PROP_TYPE)].copy()

    if base.empty:
        return pd.DataFrame(columns=DEREK_UNIQUE_SUMMARY_COLS)

    # The Derek public feed schema added ``market_line`` (and ``p_over``)
    # to ``out_df`` as PMF-native public columns. Those collide with the
    # ``market_line`` column produced by the BDL consensus join below
    # (pandas would suffix them to ``market_line_x`` / ``market_line_y``,
    # silently dropping the row-level BDL line and yielding an empty
    # summary). Drop the pre-existing public ``market_line`` /
    # ``p_over`` from ``base`` so the BDL-derived ``market_line`` survives
    # the merge unambiguously and the loop below can read it back as
    # ``r.get("market_line")`` to compute the direct PMF tail probability.
    for collision_col in ("market_line", "p_over"):
        if collision_col in base.columns:
            base = base.drop(columns=[collision_col])

    base = (
        base.sort_values(["player_name", "stat"], kind="mergesort")
            .drop_duplicates(["game_id", "player_id", "stat"], keep="first")
            .copy()
    )

    game_ids = sorted(int(x) for x in base["game_id"].dropna().unique())

    bdl_records: list[dict[str, Any]] = []
    for gid in game_ids:
        for prop_type, stat in BDL_PROP_TYPE_TO_STAT.items():
            recs = _fetch_bdl_player_props_for_game_prop_type(
                game_id=gid,
                prop_type=prop_type,
                api_key=api_key,
            )
            print(
                "BDL_PLAYER_PROPS_FETCH "
                f"game_id={gid} prop_type={prop_type} rows={len(recs)}"
            )
            for rec in recs:
                market = rec.get("market") or {}
                if isinstance(market, str):
                    try:
                        market = json.loads(market)
                    except Exception:
                        market = {}

                if str(market.get("type") or "").lower() != "over_under":
                    continue

                line = _float_or_none(rec.get("line_value"))
                if line is None:
                    continue

                bdl_records.append(
                    {
                        "game_id": rec.get("game_id"),
                        "player_id": rec.get("player_id"),
                        "stat": stat,
                        "market_line": line,
                        "vendor": rec.get("vendor"),
                        "updated_at": rec.get("updated_at"),
                    }
                )

    bdl = pd.DataFrame(bdl_records)
    if bdl.empty:
        raise RuntimeError("BDL_PLAYER_PROPS_EMPTY: no over_under player props returned")

    line_counts = (
        bdl.groupby(["game_id", "player_id", "stat", "market_line"])
           .agg(vendor_count=("vendor", "nunique"), row_count=("market_line", "size"))
           .reset_index()
    )

    selected = (
        line_counts.sort_values(
            ["game_id", "player_id", "stat", "vendor_count", "row_count", "market_line"],
            ascending=[True, True, True, False, False, True],
        )
        .groupby(["game_id", "player_id", "stat"], as_index=False)
        .head(1)
        .reset_index(drop=True)
    )

    joined = base.merge(
        selected[["game_id", "player_id", "stat", "market_line"]],
        on=["game_id", "player_id", "stat"],
        how="inner",
    )

    rows: list[dict[str, Any]] = []
    for _, r in joined.iterrows():
        pmf_arr = _pmf_array_from_jsonish(r.get(pmf_value_col))
        if pmf_arr is None:
            continue

        p_over = _pmf_direct_p_over(pmf_arr, r.get("market_line"))
        if p_over is None:
            continue

        projected_minutes = (
            _float_or_none(r.get("projected_minutes"))
            or _float_or_none(r.get("minutes_mean"))
            or _float_or_none(r.get("minutes_q50"))
            or _float_or_none(r.get("minutes_p50"))
        )

        rows.append(
            {
                "player_name": r.get("player_name"),
                "projected_minutes": projected_minutes,
                "stat": r.get("stat"),
                "pmf_mean": _pmf_direct_mean(pmf_arr),
                "market_line": float(r.get("market_line")),
                "p_over": p_over,
            }
        )

    summary = pd.DataFrame(rows, columns=DEREK_UNIQUE_SUMMARY_COLS)

    if summary.empty:
        raise RuntimeError("DEREK_BDL_SUMMARY_EMPTY_AFTER_JOIN")

    dupes = summary.groupby(["player_name", "stat"]).size().reset_index(name="n")
    dupes = dupes[dupes["n"] > 1]
    if not dupes.empty:
        raise RuntimeError(
            "DEREK_BDL_SUMMARY_DUPLICATE_PLAYER_STAT_ROWS:\n"
            + dupes.to_string(index=False)
        )

    # Public CSV rounding contract: ``projected_minutes``, ``pmf_mean``,
    # ``market_line`` and ``p_over`` are rounded to 4 decimals on the
    # persisted ``derek_unique_props_summary.csv``. Internal math
    # (E[X], tail probability) stays full-precision; the rounding is
    # applied only at the public output boundary so the summary stays
    # eyeball-friendly without leaking float64 trailing digits.
    for col in ("projected_minutes", "pmf_mean", "market_line", "p_over"):
        if col in summary.columns:
            summary[col] = pd.to_numeric(summary[col], errors="coerce").round(4)

    return summary.sort_values(["player_name", "stat"], kind="mergesort").reset_index(drop=True)


def _market_key_for_stat(stat: str) -> str:
    return f"player_{stat}_over_under"


def _none_if_nan(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _maybe_rel(p: Path, root: Path) -> str:
    """Best-effort relative-to-root path; falls back to absolute."""
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def _clean_optional_str(v: Any) -> str | None:
    """Coerce a maybe-null/maybe-NaN value to a clean optional string.

    Returns ``None`` for ``None``, NaN floats, empty / whitespace-only
    strings, or the literal strings ``"nan"`` / ``"none"``.
    """
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).strip()
    if not s or s.lower() in {"nan", "none"}:
        return None
    return s


def _row_template() -> dict:
    return {c: None for c in FEED_COLS}


def _populate_identity_pmf_quality(
    row: dict,
    mo_row: pd.Series,
    *,
    snapshot_type: str,
    snapshot_time_utc: str,
    delivery_date: str,
    finality_status: str | None,
    finality_blocker_codes: str | None,
    availability_freshness_status: str | None,
    odds_freshness_status: str | None,
    outcomes_freshness_status: str | None,
) -> None:
    pmf_json = mo_row.get("pmf_json")
    pmf_valid, pmf_sum_error = _validate_pmf(pmf_json)

    role_freshness = _none_if_nan(mo_row.get("role_freshness_status"))

    # Public-facing PMF expectation: compute directly from the row PMF
    # whenever a parseable PMF exists; otherwise fall back to the
    # upstream ``mean`` summary stat. Never reference
    # ``model_projected_mean`` (quarantined).
    pmf_arr_for_mean = _pmf_array_from_jsonish(pmf_json)
    if pmf_arr_for_mean is not None:
        pmf_mean_value: float | None = _pmf_direct_mean(pmf_arr_for_mean)
    else:
        upstream_mean = _none_if_nan(mo_row.get("mean"))
        pmf_mean_value = (
            float(upstream_mean) if isinstance(upstream_mean, (int, float)) else None
        )

    row.update(
        {
            "snapshot_type": snapshot_type,
            "snapshot_time_utc": snapshot_time_utc,
            "delivery_date": delivery_date,
            "game_id": _none_if_nan(mo_row.get("game_id")),
            "game_start_time_utc": _none_if_nan(mo_row.get("game_start_time")),
            "player_id": _none_if_nan(mo_row.get("player_id")),
            "player_name": _none_if_nan(mo_row.get("player_name")),
            "team": _none_if_nan(mo_row.get("team")),
            "opponent": _none_if_nan(mo_row.get("opponent")),
            "is_home": _none_if_nan(mo_row.get("is_home")),
            "stat": _none_if_nan(mo_row.get("stat")),
            "pmf_json": pmf_json,
            "pmf_mean": pmf_mean_value,
            "mean": _none_if_nan(mo_row.get("mean")),
            "median": _none_if_nan(mo_row.get("median")),
            "mode": _none_if_nan(mo_row.get("mode")),
            "p0": _none_if_nan(mo_row.get("p0")),
            **{k: _none_if_nan(mo_row.get(k)) for k in P_GE_KEYS},
            "model_version": _none_if_nan(mo_row.get("model_version")),
            "pmf_source": _none_if_nan(mo_row.get("pmf_source")),
            "calibration_source": _none_if_nan(mo_row.get("calibration_source")),
            "role_bucket": _none_if_nan(mo_row.get("role_bucket")),
            "role_source": _role_source_from_freshness(role_freshness),
            "calibration_confidence": _none_if_nan(mo_row.get("calibration_confidence")),
            # M8.9 minutes-model + eligibility passthrough.
            "minutes_mean": _none_if_nan(mo_row.get("minutes_mean")),
            "minutes_q50": _none_if_nan(mo_row.get("minutes_q50")),
            "minutes_p10": _none_if_nan(mo_row.get("minutes_p10")),
            "minutes_p50": _none_if_nan(mo_row.get("minutes_p50")),
            "minutes_p90": _none_if_nan(mo_row.get("minutes_p90")),
            "minutes_std": _none_if_nan(mo_row.get("minutes_std")),
            "p_inactive_used": _none_if_nan(mo_row.get("p_inactive_used")),
            "rotation_probability": _none_if_nan(
                mo_row.get("rotation_probability")
            ),
            "starter_probability": _none_if_nan(
                mo_row.get("starter_probability")
            ),
            "projected_role": _none_if_nan(mo_row.get("projected_role")),
            "player_game_eligible": _none_if_nan(
                mo_row.get("player_game_eligible")
            ),
            "eligibility_reason": _none_if_nan(
                mo_row.get("eligibility_reason")
            ),
            "has_current_market_line": _none_if_nan(
                mo_row.get("has_current_market_line")
            ),
            "minutes_source": _none_if_nan(mo_row.get("minutes_source")),
            "minutes_model_version": _none_if_nan(
                mo_row.get("minutes_model_version")
            ),
            "finality_status": finality_status,
            "finality_blocker_codes": finality_blocker_codes,
            "injury_freshness_status": _none_if_nan(mo_row.get("injury_freshness_status")),
            "availability_freshness_status": availability_freshness_status,
            "lineup_freshness_status": _none_if_nan(mo_row.get("lineup_freshness_status")),
            "role_freshness_status": role_freshness,
            "odds_freshness_status": odds_freshness_status,
            "outcomes_freshness_status": outcomes_freshness_status,
            "tov_status": _none_if_nan(mo_row.get("tov_status")),
            "pmf_valid": pmf_valid,
            "pmf_sum_error": pmf_sum_error,
            # Row-level provenance — surfaces ``lineup_source``,
            # ``lineup_last_updated_utc``,
            # ``injury_context_source`` and
            # ``injury_report_fetched_at_utc`` onto every per-snapshot
            # row so morning_snapshot.parquet (and therefore the
            # unified Derek feed read from it) carry them.
            "expected_lineup_status": _none_if_nan(
                mo_row.get("expected_lineup_status")
            ),
            "official_lineup_status": _none_if_nan(
                mo_row.get("official_lineup_status")
            ),
            "lineup_source": _none_if_nan(mo_row.get("lineup_source")),
            "lineup_last_updated_utc": _none_if_nan(
                mo_row.get("lineup_last_updated_utc")
            ),
            "injury_context_source": _none_if_nan(
                mo_row.get("injury_context_source")
            ),
            "injury_report_fetched_at_utc": _none_if_nan(
                mo_row.get("injury_report_fetched_at_utc")
            ),
        }
    )


def _populate_market(
    row: dict,
    mc_row: pd.Series | None,
    *,
    market_snapshot_time_utc: str | None,
) -> None:
    if mc_row is None:
        # Model-only row — leave market fields blank but stamp coverage.
        row["market_key"] = _market_key_for_stat(str(row["stat"]))
        row["market_coverage_status"] = "no_market"
        row["market_line"] = None
        row["p_over"] = None
        # No line on a model-only row -> no p_over to compute. Do not
        # impute. ``model_p_over`` and ``model_p_under`` are not
        # exposed on public outputs (model_p_over is quarantined and
        # model_p_under is left at its template default so as not to
        # imply a real probability without a market line).
        return

    line = _none_if_nan(mc_row.get("line"))
    book = _none_if_nan(mc_row.get("book"))
    over_price = _none_if_nan(mc_row.get("market_over_odds"))
    under_price = _none_if_nan(mc_row.get("market_under_odds"))
    no_vig_over = _none_if_nan(mc_row.get("market_no_vig_over_prob"))
    no_vig_under = (
        None if no_vig_over is None else max(0.0, min(1.0, 1.0 - float(no_vig_over)))
    )
    # Direct PMF tail probability against the offered market line.
    # Prefer the canonical/stat-grid PMF carried on the row (set by
    # ``_populate_identity_pmf_quality`` from ``mo_row.pmf_json``)
    # because market_comparison strips ``pmf_json`` to keep the
    # comparison frame slim. We NEVER reuse ``model_p_over`` —
    # that field is conditional (renormalised against the at-line
    # atom) and is quarantined from public outputs.
    pmf_arr_for_market = _pmf_array_from_jsonish(row.get("pmf_json"))
    if pmf_arr_for_market is None:
        pmf_arr_for_market = _pmf_array_from_jsonish(mc_row.get("pmf_json"))
    if pmf_arr_for_market is not None and line is not None:
        p_over_direct = _pmf_direct_p_over(pmf_arr_for_market, line)
    else:
        p_over_direct = None
    model_p_under = (
        None
        if p_over_direct is None
        else max(0.0, min(1.0, 1.0 - float(p_over_direct)))
    )
    edge_over = _none_if_nan(mc_row.get("edge"))
    edge_under = None if edge_over is None else -float(edge_over)

    row.update(
        {
            "sportsbook": book,
            "book": book,
            "market_key": _market_key_for_stat(str(row["stat"])),
            "line": line,
            "market_line": line,
            "p_over": p_over_direct,
            "over_price_american": over_price,
            "under_price_american": under_price,
            "market_no_vig_over_prob": no_vig_over,
            "market_no_vig_under_prob": no_vig_under,
            "model_p_under": model_p_under,
            "fair_over_odds_american": _none_if_nan(mc_row.get("fair_over_odds_american")),
            "fair_under_odds_american": _none_if_nan(mc_row.get("fair_under_odds_american")),
            "edge": edge_over,
            "edge_over": edge_over,
            "edge_under": edge_under,
            "market_snapshot_time_utc": market_snapshot_time_utc,
            "market_coverage_status": _none_if_nan(mc_row.get("market_coverage_status"))
            or "full",
        }
    )


def build_rows(
    *,
    model_only: pd.DataFrame,
    market_comparison: pd.DataFrame | None,
    snapshot_type: str,
    snapshot_time_utc: str,
    delivery_date: str,
    finality_status: str | None,
    finality_blocker_codes: str | None,
    availability_freshness_status: str | None,
    odds_freshness_status: str | None,
    outcomes_freshness_status: str | None,
    market_snapshot_time_utc: str | None,
) -> list[dict]:
    """Assemble one row per (player, stat, book, line) where market exists,
    plus one model-only row for every (player, stat) without a market match."""
    rows: list[dict] = []
    mc_keys: set[tuple] = set()
    if market_comparison is not None and not market_comparison.empty:
        # Dedup market_comparison by (player_id, stat, book, line) so one
        # repeated quote doesn't double-count.
        mc = market_comparison.drop_duplicates(
            subset=["player_id", "stat", "book", "line"], keep="first"
        ).copy()
        mc_lookup = mc.set_index(["player_id", "stat"], drop=False)
        mc_keys = set(zip(mc["player_id"], mc["stat"]))
    else:
        mc_lookup = None

    for _, mo_row in model_only.iterrows():
        key = (mo_row.get("player_id"), mo_row.get("stat"))
        market_matches: list[pd.Series] = []
        if mc_lookup is not None and key in mc_keys:
            try:
                sub = mc_lookup.loc[[key]]
                # When .loc[[key]] returns a DataFrame iterate rows; when it
                # returns a single Series wrap it.
                if isinstance(sub, pd.DataFrame):
                    market_matches = [r for _, r in sub.iterrows()]
                else:
                    market_matches = [sub]
            except KeyError:
                market_matches = []
        if market_matches:
            for mc_row in market_matches:
                row = _row_template()
                _populate_identity_pmf_quality(
                    row,
                    mo_row,
                    snapshot_type=snapshot_type,
                    snapshot_time_utc=snapshot_time_utc,
                    delivery_date=delivery_date,
                    finality_status=finality_status,
                    finality_blocker_codes=finality_blocker_codes,
                    availability_freshness_status=availability_freshness_status,
                    odds_freshness_status=odds_freshness_status,
                    outcomes_freshness_status=outcomes_freshness_status,
                )
                _populate_market(
                    row,
                    mc_row,
                    market_snapshot_time_utc=market_snapshot_time_utc,
                )
                rows.append(row)
        else:
            row = _row_template()
            _populate_identity_pmf_quality(
                row,
                mo_row,
                snapshot_type=snapshot_type,
                snapshot_time_utc=snapshot_time_utc,
                delivery_date=delivery_date,
                finality_status=finality_status,
                finality_blocker_codes=finality_blocker_codes,
                availability_freshness_status=availability_freshness_status,
                odds_freshness_status=odds_freshness_status,
                outcomes_freshness_status=outcomes_freshness_status,
            )
            _populate_market(
                row,
                None,
                market_snapshot_time_utc=market_snapshot_time_utc,
            )
            rows.append(row)
    return rows


def write_feed_files(
    *,
    rows: list[dict],
    out_dir: Path,
    basename: str,
    write_jsonl: bool,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=FEED_COLS)
    df = _drop_quarantined_columns(df)

    csv_path = out_dir / f"{basename}.csv"
    parquet_path = out_dir / f"{basename}.parquet"
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    df.to_parquet(parquet_path, index=False)

    written = {"csv": str(csv_path.relative_to(REPO_ROOT)),
               "parquet": str(parquet_path.relative_to(REPO_ROOT)),
               "rows": len(df)}

    if write_jsonl:
        jsonl_path = out_dir / f"{basename}.jsonl"
        with jsonl_path.open("w") as f:
            for r in rows:
                # Ensure JSON-safe (no NaN / inf) and strip quarantined keys.
                clean = {
                    k: (None if isinstance(v, float) and not math.isfinite(v) else v)
                    for k, v in r.items()
                    if k not in QUARANTINED_PUBLIC_COLUMNS
                }
                f.write(json.dumps(clean, default=str) + "\n")
        written["jsonl"] = str(jsonl_path.relative_to(REPO_ROOT))

    return written


def write_latest_available(
    *,
    rows: list[dict],
    out_dir: Path,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=FEED_COLS)
    df = _drop_quarantined_columns(df)
    csv_path = out_dir / "latest_available_snapshot.csv"
    parquet_path = out_dir / "latest_available_snapshot.parquet"
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    df.to_parquet(parquet_path, index=False)
    return {
        "csv": str(csv_path.relative_to(REPO_ROOT)),
        "parquet": str(parquet_path.relative_to(REPO_ROOT)),
        "rows": len(df),
    }


def write_feed_readme(out_dir: Path, *, delivery_date: str, manifests: dict) -> Path:
    p = out_dir / "FEED_README.md"
    morning = manifests.get("morning", {})
    lineup = manifests.get("lineup", {})
    lineup_status = manifests.get("lineup_status", {})
    text = []
    text.append(f"# Derek forward feed — {delivery_date}\n\n")
    text.append(
        "This package is the forward-looking PMF feed for the dated slate. "
        "All PMFs are **model-only** and were never market-anchored. "
        "Market columns are reference-only.\n\n"
    )
    text.append("## Files Derek should archive daily\n\n")
    text.append(
        "Open these in order. Archive the entire `derek_forward_feed/` "
        "folder per date.\n\n"
    )
    text.append("- `feed_manifest.json` — provenance, row counts, finality.\n")
    text.append("- `morning_snapshot.csv` — pre-lineup snapshot (canonical).\n")
    text.append("- `morning_snapshot.parquet` — same data, columnar.\n")
    text.append("- `morning_snapshot.jsonl` — same data, one JSON record per line.\n")
    text.append(
        "- `latest_available_snapshot.csv` / `.parquet` — convenience pointer "
        "to the freshest snapshot on disk for this date "
        "(lineup_snapshot when available, else morning_snapshot).\n"
    )
    text.append(
        "- `lineup_snapshot.{csv,parquet,jsonl}` — official-lineup / near-tip "
        "snapshot when produced.\n"
    )
    text.append(
        "- `lineup_snapshot_status.json` — present only when no lineup snapshot "
        "package exists yet; documents the honest reason.\n\n"
    )
    text.append("## Snapshot summary\n\n")
    if morning:
        text.append(
            f"- **morning** rows: {morning.get('rows', '—')}  "
            f"snapshot_time_utc: `{morning.get('snapshot_time_utc', '—')}`\n"
        )
    else:
        text.append("- **morning**: not produced\n")
    if lineup:
        text.append(
            f"- **lineup**  rows: {lineup.get('rows', '—')}  "
            f"snapshot_time_utc: `{lineup.get('snapshot_time_utc', '—')}`\n"
        )
    elif lineup_status:
        text.append(
            f"- **lineup**: not available — status `{lineup_status.get('status')}`\n"
        )
    else:
        text.append("- **lineup**: not requested\n")
    text.append("\n## Schema (per row)\n\n")
    text.append(
        "Identity, model PMF, market reference, quality/finality. The full "
        "column list is documented in the feed_manifest.json `schema` block.\n"
    )
    text.append(
        "- One row per (player, stat, book, line) where a market quote exists.\n"
    )
    text.append(
        "- One model-only row per (player, stat) where no market exists "
        "(book and line blank).\n"
    )
    text.append(
        "- TOV PMFs (when present in canonical) appear as model-only rows.\n\n"
    )
    text.append("## Hard rules\n\n")
    text.append(
        "- PMFs are sourced from `pmf_model_review_package/machine_readable/"
        "model_only.parquet` — the canonical model-only file.\n"
    )
    text.append(
        "- Market fields come from `wizard_of_odds/market_comparison.parquet`. "
        "Market is reference-only; PMFs are never market-anchored.\n"
    )
    text.append(
        "- Phase 10D / 10D.2 TOV overlays are **not** wired in. TOV PMFs "
        "(when emitted) come from Phase 8 calibrators; see the run manifest's "
        "`tov_overlay` and `tov_status`.\n"
    )
    text.append(
        "- After-game outcomes are scored separately under "
        "`deliveries/{date}/after_game_scoring/` once finals are available.\n"
    )
    p.write_text("".join(text))
    return p


def _git_sha_short() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def _discrete_pmf_stats(pmf_json: Any) -> tuple[float | None, float | None, float | None, float | None, float | None]:
    """Return (mean, variance, p10, p50, p90) from a sparse PMF dict."""

    if pmf_json is None or (isinstance(pmf_json, float) and math.isnan(pmf_json)):
        return None, None, None, None, None
    try:
        d = json.loads(pmf_json) if isinstance(pmf_json, str) else dict(pmf_json)
    except Exception:
        return None, None, None, None, None
    if not d:
        return None, None, None, None, None
    ks: list[int] = []
    ps: list[float] = []
    for k, v in d.items():
        try:
            kk = int(k)
            vv = float(v)
        except Exception:
            continue
        if math.isfinite(vv) and vv > 0:
            ks.append(kk)
            ps.append(vv)
    if not ks:
        return None, None, None, None, None
    s = sum(ps)
    if s <= 0:
        return None, None, None, None, None
    ps = [p / s for p in ps]
    mean = float(sum(k * p for k, p in zip(ks, ps)))
    ex2 = float(sum((k * k) * p for k, p in zip(ks, ps)))
    var = max(ex2 - mean * mean, 0.0)
    pairs = sorted(zip(ks, ps), key=lambda x: x[0])
    cdf = 0.0
    qvals = {0.1: None, 0.5: None, 0.9: None}
    for k, p in pairs:
        cdf += p
        for thr in (0.1, 0.5, 0.9):
            if qvals[thr] is None and cdf >= thr - 1e-12:
                qvals[thr] = float(k)
    return mean, var, qvals[0.1], qvals[0.5], qvals[0.9]


def write_m88_unified_feed(
    *,
    date: str,
    out_dir: Path,
    df: pd.DataFrame | None,
    run_mode: str,
    lineup_status: dict | None,
) -> dict | None:
    """Emit ``derek_forward_feed.{parquet,csv,jsonl}`` + ``manifest.json`` (M8.8)."""

    if df is None or df.empty:
        skip = {
            "delivery_date": date,
            "unified_feed_status": "skipped_no_rows",
            "reason": "No latest snapshot dataframe on disk for this run.",
            "checked_at_utc": _now_utc_iso(),
        }
        (out_dir / "derek_forward_feed_unified_skip.json").write_text(
            json.dumps(skip, indent=2) + "\n", encoding="utf-8"
        )
        return None

    stamp_path = out_dir / "feed_manifest.champion_stamp.json"
    stamp = _read_json(stamp_path) or {}
    model_hash = str(stamp.get("champion_model_id") or stamp.get("calibration_run_id") or "")

    official = "not_available_yet"
    unavail_parts: list[str] = []
    if isinstance(lineup_status, dict):
        st = str(lineup_status.get("status") or "")
        if st == "confirmed_lineup_snapshot":
            official = "confirmed_bdl_or_equivalent"
        elif st == "near_tip_projected_lineup_snapshot":
            official = "projected_near_tip_not_bdl_confirmed"
            unavail_parts.append(lineup_status.get("reason") or st)
        elif st == "pending_lineup_snapshot":
            official = "not_available_yet"
            unavail_parts.append(lineup_status.get("reason") or st)

    run_id = str(uuid.uuid4())
    gen_at = _now_utc_iso()
    run_date = gen_at[:10]
    pipe_ver = _git_sha_short()
    has_min_mean = "minutes_mean" in df.columns
    has_min_q50 = "minutes_q50" in df.columns

    rows_out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        # Resolve the row's final PMF payload from the canonical priority
        # ``pmf_json`` → ``pmf_active`` → ``pmf`` so the downstream BDL
        # main-line summary builder always sees a real PMF column on
        # ``out_df``, regardless of which upstream snapshot produced the
        # row. The normalised value is stamped into the row dict under
        # ``pmf_json`` below — public ``derek_forward_feed.*`` writers
        # still strip ``pmf_json`` from the persisted files.
        pmf_json = _pick_row_pmf_value(r)
        pmean, pvar, p10, p50, p90 = _discrete_pmf_stats(pmf_json)

        # Direct PMF tail probability for the unified Derek feed.
        # Computed straight from the row PMF against the row's offered
        # line; never reuses the quarantined ``model_p_over`` /
        # ``model_prob_over_*`` fields.
        line_value = r.get("line")
        try:
            line_for_p_over = (
                float(line_value)
                if line_value is not None
                and not (isinstance(line_value, float) and math.isnan(line_value))
                else None
            )
        except (TypeError, ValueError):
            line_for_p_over = None
        pmf_arr_row = _pmf_array_from_jsonish(pmf_json)
        if pmf_arr_row is not None and line_for_p_over is not None:
            p_over_value: float | None = _pmf_direct_p_over(
                pmf_arr_row, line_for_p_over
            )
        else:
            p_over_value = None
        # M8.8 — use the real predict_minutes-derived p_inactive_used when
        # present (a continuous probability in [0, 1]). Fall back to the
        # legacy role-string binary when minutes_model output is missing.
        p_inact = r.get("p_inactive_used")
        if (
            p_inact is None
            or (isinstance(p_inact, float) and math.isnan(p_inact))
        ):
            role = str(r.get("role_bucket") or "")
            inactive = 1.0 if role == "inactive_risk" else 0.0
        else:
            try:
                inactive = float(p_inact)
            except Exception:
                role = str(r.get("role_bucket") or "")
                inactive = 1.0 if role == "inactive_risk" else 0.0
        mkt = str(r.get("market_coverage_status") or "unknown")
        if mkt in {"", "none", "nan"}:
            mkt_status = "no_offered_market" if r.get("line") is None or (isinstance(r.get("line"), float) and math.isnan(r.get("line"))) else "missing_raw_snapshot"
        else:
            mkt_status = mkt
        fair_o = r.get("fair_over_odds_american")
        fair_u = r.get("fair_under_odds_american")
        inj = str(r.get("injury_freshness_status") or "unknown")
        lin_f = str(r.get("lineup_freshness_status") or "unknown")
        stale_inj = "stale" in inj.lower()
        stale_lin = "stale" in lin_f.lower()
        u_reason = None
        if unavail_parts:
            u_reason = "; ".join(unavail_parts)[:2000]
        if p10 is None or p50 is None:
            u_reason = (u_reason + " | " if u_reason else "") + "pmf_quantiles_derived_from_sparse_pmf_json"

        mu = r.get("model_p_under")
        mu_f = (
            float(mu)
            if mu is not None and not (isinstance(mu, float) and math.isnan(mu))
            else None
        )
        row = {
            "game_date": str(r.get("delivery_date") or date),
            "run_date": run_date,
            "run_id": run_id,
            "run_mode": run_mode,
            "generated_at_utc": gen_at,
            "pipeline_version": pipe_ver,
            "model_version": str(r.get("model_version") or ""),
            "model_artifact_hash": model_hash,
            "source_data_asof_utc": str(r.get("snapshot_time_utc") or gen_at),
            "player_id": r.get("player_id"),
            "player_name": r.get("player_name"),
            "team": r.get("team"),
            "opponent": r.get("opponent"),
            "game_id": r.get("game_id"),
            "event_id": None,
            "stat": r.get("stat"),
            "line": r.get("line"),
            "role_bucket": r.get("role_bucket"),
            "hard_role_bucket": r.get("role_bucket"),
            "role_mixture_enabled": bool(r.get("role_mixture_enabled", True)),
            "role_mixture_weights_json": r.get("role_mixture_weights_json"),
            "role_entropy": r.get("role_entropy"),
            "role_bucket_confidence": r.get("role_bucket_confidence"),
            "projected_minutes": r.get("minutes_mean") if has_min_mean else None,
            "minutes_q10": None,
            "minutes_q50": r.get("minutes_q50") if has_min_q50 else None,
            "minutes_q90": None,
            "inactive_risk": inactive,
            "expected_lineup_status": (
                _clean_optional_str(r.get("expected_lineup_status"))
                or lin_f
            ),
            "official_lineup_status": (
                _clean_optional_str(r.get("official_lineup_status"))
                or official
            ),
            "injury_status": inj,
            "injury_source": (
                _clean_optional_str(r.get("injury_context_source"))
                or "bdl_availability_freshness_manifest"
            ),
            # Surface the row-level injury timestamp stamped by
            # stat_grid (``injury_report_fetched_at_utc``) rather
            # than the hardcoded ``None`` historically emitted here.
            "injury_last_updated_utc": (
                _clean_optional_str(r.get("injury_report_fetched_at_utc"))
                or None
            ),
            "lineup_source": (
                _clean_optional_str(r.get("lineup_source"))
                or "bdl_lineup_freshness_manifest"
            ),
            # Surface the row-level ``lineup_last_updated_utc`` from
            # the freshness manifest (set when
            # ``artifacts/live_lineups/<DATE>/<GAME>/lineup_status.json``
            # exists) rather than the hardcoded ``None``.
            "lineup_last_updated_utc": (
                _clean_optional_str(r.get("lineup_last_updated_utc"))
                or None
            ),
            "stale_injury_flag": stale_inj,
            "stale_lineup_flag": stale_lin,
            "market_line": line_for_p_over,
            "p_over": p_over_value,
            # In-memory only: ``pmf_json`` is propagated onto the row so
            # the BDL main-line summary builder can compute
            # ``pmf_mean`` and ``p_over`` directly from the row PMF.
            # It is stripped from the persisted derek_forward_feed.*
            # public files below (preserves the historical Derek feed
            # schema where ``pmf_json`` is NOT a public column).
            "pmf_json": pmf_json,
            "model_prob_under_active": mu_f,
            "fair_over_odds": fair_o,
            "fair_under_odds": fair_u,
            "pmf_mean": pmean if pmean is not None else r.get("mean"),
            "pmf_variance": pvar,
            "pmf_p10": p10,
            "pmf_p50": p50 if p50 is not None else r.get("median"),
            "pmf_p90": p90,
            "market_prob_over": r.get("market_no_vig_over_prob"),
            "no_vig_market_prob_over": r.get("market_no_vig_over_prob"),
            "edge": r.get("edge"),
            "market_status": mkt_status,
            "delivery_status": "ready",
            "unavailable_reason": u_reason,
            "calculation_source": "build_derek_forward_feed:v1_model_only_plus_market_reference",
            "calculation_status": "ok",
        }
        rows_out.append(row)

    out_df = pd.DataFrame(rows_out)

    # M8.9 — defensive publication guard.
    #
    # The PRIMARY player-universe gate is upstream projected
    # rotation/minutes eligibility (the M8.9 player-game eligibility
    # gate enforced by
    # src/nba_props_model/pipelines/player_game_eligibility.py before
    # PMFs are computed). This Derek filter is a defensive publication
    # guard only. It should rarely drop rows after canonical is fixed.
    # If it drops many rows, upstream validation
    # (scripts/validate_daily_pmf_delivery.py) should fail.
    #
    # Preferred path: respect the upstream `player_game_eligible` column
    # whenever it is present on every row of the latest snapshot. Any
    # row reaching this point with `player_game_eligible == False`
    # means upstream validation slipped; we still drop it for safety
    # but emit a loud WARN so the operator knows to fix the canonical
    # pipeline rather than rely on this guard.
    #
    # Legacy fallback (used only when the eligibility column is absent
    # from the snapshot — e.g. running against a pre-M8.9 canonical
    # rebuild): use the prior market-quoted-player heuristic so the
    # forward feed remains usable. This fallback must NEVER be the
    # primary mechanism — if it is firing in production, something
    # upstream is broken.
    rotation_filter_dropped_rows = 0
    rotation_filter_dropped_players: list[str] = []
    filter_strategy = "noop"
    if not out_df.empty:
        has_elig_col = (
            "player_game_eligible" in out_df.columns
            and out_df["player_game_eligible"].notna().all()
        )
        if has_elig_col:
            filter_strategy = "upstream_player_game_eligible"
            eligible_mask = out_df["player_game_eligible"].astype(bool)
            before_rows = len(out_df)
            dropped_df = out_df.loc[~eligible_mask].copy()
            out_df = out_df.loc[eligible_mask].copy()
            rotation_filter_dropped_rows = before_rows - len(out_df)
            if rotation_filter_dropped_rows > 0:
                rotation_filter_dropped_players = sorted(
                    str(p) for p in dropped_df["player_name"].dropna().unique()
                )
                print(
                    "  WARN: Derek defensive filter dropped "
                    f"{rotation_filter_dropped_rows} upstream-ineligible "
                    "rows; canonical validation should have prevented "
                    "this. Players: "
                    f"{', '.join(rotation_filter_dropped_players[:10])}"
                    f"{'...' if len(rotation_filter_dropped_players) > 10 else ''}"
                )
        elif "player_id" in out_df.columns and "line" in out_df.columns:
            # Legacy safeguard only — keep behaviour identical to M8.8
            # for snapshots produced before the M8.9 eligibility gate.
            filter_strategy = "legacy_market_quoted_player_fallback"
            has_line = out_df["line"].notna()
            market_quoted_players = set(
                out_df.loc[has_line, "player_id"].unique()
            )
            rotation_mask = has_line | out_df["player_id"].isin(
                market_quoted_players
            )
            before_rows = len(out_df)
            dropped_df = out_df.loc[~rotation_mask].copy()
            out_df = out_df.loc[rotation_mask].copy()
            rotation_filter_dropped_rows = before_rows - len(out_df)
            if rotation_filter_dropped_rows > 0:
                rotation_filter_dropped_players = sorted(
                    str(p) for p in dropped_df["player_name"].dropna().unique()
                )
                print(
                    "  legacy bench-filter (no upstream eligibility "
                    f"column): dropped {rotation_filter_dropped_rows} "
                    "model-only rows for "
                    f"{len(rotation_filter_dropped_players)} non-quoted "
                    "players. "
                    f"Dropped: {', '.join(rotation_filter_dropped_players[:10])}"
                    f"{'...' if len(rotation_filter_dropped_players) > 10 else ''}"
                )

    pq_out = out_dir / "derek_forward_feed.parquet"
    csv_out = out_dir / "derek_forward_feed.csv"
    jl_out = out_dir / "derek_forward_feed.jsonl"
    # Public Derek feed schema historically did NOT include the raw
    # ``pmf_json`` column. We carry it on the in-memory ``out_df``
    # purely so the summary builder below can compute ``pmf_mean``
    # / ``p_over`` directly from the row PMF; strip it (along with
    # any quarantined column) before persisting.
    _DEREK_FEED_PRIVATE_COLUMNS = ("pmf_json",)
    out_df_public = _drop_quarantined_columns(out_df).drop(
        columns=[c for c in _DEREK_FEED_PRIVATE_COLUMNS if c in out_df.columns],
        errors="ignore",
    )
    out_df_public.to_parquet(pq_out, index=False)
    out_df_public.to_csv(csv_out, index=False, quoting=csv.QUOTE_MINIMAL)
    with jl_out.open("w", encoding="utf-8") as f:
        for rec in rows_out:
            clean = {
                k: v for k, v in rec.items()
                if k not in QUARANTINED_PUBLIC_COLUMNS
                and k not in _DEREK_FEED_PRIVATE_COLUMNS
            }
            f.write(json.dumps(clean, default=str) + "\n")

    # Unique props summary — Derek's boss-facing at-a-glance view.
    #
    # Contract:
    #   one row per player/stat using BDL's normal over_under main prop line.
    #
    # This summary intentionally does NOT use WoO alternate-line rows and does
    # NOT expose or copy model_prob_over_* fields. p_over is computed directly
    # from the row PMF against the selected BDL market_line.
    #
    # Defensive normalisation: although the row builder above stamps
    # ``pmf_json`` onto every row dict from the canonical
    # ``pmf_json`` → ``pmf_active`` → ``pmf`` priority, we re-assert at
    # the dataframe boundary so a future refactor that drops the key
    # from the row literal still produces a usable summary (instead of
    # silently writing an empty file or surfacing
    # ``DEREK_BDL_SUMMARY_MISSING_REQUIRED_COLUMNS`` during the morning
    # delivery window).
    out_df_for_summary = _ensure_pmf_json_column(out_df)
    summary_csv_out = out_dir / "derek_unique_props_summary.csv"
    summary_df = _build_derek_bdl_main_line_summary(out_df_for_summary)
    summary_df.to_csv(summary_csv_out, index=False, quoting=csv.QUOTE_MINIMAL)
    try:
        _summary_rel = str(summary_csv_out.relative_to(REPO_ROOT))
    except ValueError:
        _summary_rel = str(summary_csv_out)
    print(
        "DEREK_UNIQUE_PROPS_SUMMARY_WRITTEN "
        f"path={_summary_rel} "
        f"rows={len(summary_df)} "
        f"columns={list(summary_df.columns)}"
    )
    man = {
        "delivery_date": date,
        "run_mode": run_mode,
        "generated_at_utc": gen_at,
        "row_count": int(len(out_df)),
        "schema": "m88_derek_unified_v1",
        "lineup_status": lineup_status,
        "rotation_bench_filter": {
            "policy": "defensive_publication_guard_only",
            "strategy": filter_strategy,
            "rows_dropped": int(rotation_filter_dropped_rows),
            "players_dropped_count": int(len(rotation_filter_dropped_players)),
            "players_dropped": rotation_filter_dropped_players,
            "rationale": (
                "Primary player-universe gate is upstream projected "
                "rotation/minutes eligibility (M8.9). This filter is a "
                "defensive publication guard only. If it drops many rows, "
                "scripts/validate_daily_pmf_delivery.py upstream should "
                "have failed first."
            ),
        },
        "files": {
            "parquet": _maybe_rel(pq_out, REPO_ROOT),
            "csv": _maybe_rel(csv_out, REPO_ROOT),
            "jsonl": _maybe_rel(jl_out, REPO_ROOT),
            "unique_props_summary_csv": _maybe_rel(summary_csv_out, REPO_ROOT),
        },
        "unique_props_summary": {
            "path": _maybe_rel(summary_csv_out, REPO_ROOT),
            "row_count": int(len(summary_df)),
            "columns": DEREK_UNIQUE_SUMMARY_COLS,
            "column_lineage": {
                "pmf_mean": "direct_expectation_from_pmf_json",
                "p_over": "direct_pmf_tail_probability_gt_market_line",
                "market_line": "bdl_player_props_line_value_over_under_consensus",
            },
            "dedupe_keys": ["player_name", "stat"],
            "market_line_source": "bdl_player_props_over_under",
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(man, indent=2, default=str) + "\n", encoding="utf-8")
    return man


def build_snapshot(
    *,
    date: str,
    snapshot_label: str,
    snapshot_type_value: str,
    out_dir: Path,
    write_jsonl: bool = True,
) -> dict | None:
    """Build a single snapshot (`morning` or `lineup`). Returns the
    feed_manifest entry for this snapshot, or None if the inputs are
    missing."""
    base = DEL_DIR / date
    review_pkg = base / "pmf_model_review_package" / "machine_readable"
    woo = base / "wizard_of_odds"
    model_only_path = review_pkg / "model_only.parquet"
    market_comparison_path = woo / "market_comparison.parquet"
    run_manifest_path = woo / "run_manifest.json"
    freshness_path = FRESH_DIR / f"{date}.json"

    if not model_only_path.exists():
        print(
            f"  [{snapshot_label}] missing {model_only_path.relative_to(REPO_ROOT)}; "
            "no source PMFs",
            file=sys.stderr,
        )
        return None

    model_only = pd.read_parquet(model_only_path)
    market_comparison = (
        pd.read_parquet(market_comparison_path)
        if market_comparison_path.exists()
        else None
    )
    run_manifest = _read_json(run_manifest_path) or {}
    freshness_manifest = _read_json(freshness_path) or {}

    # Stamp the snapshot_type for this snapshot (overrides whatever was
    # baked into model_only by the upstream build for the morning row).
    finality_status = run_manifest.get("finality_status")
    finality_blocker_codes = _coerce_blocker_codes(
        run_manifest.get("finality_blocker_codes")
    )
    snapshot_time_utc = run_manifest.get("snapshot_time_utc") or _now_utc_iso()
    market_snapshot_time_utc = (
        run_manifest.get("sources", {}).get("odds_snapshot", {}).get("mtime_utc")
    )
    availability_freshness_status = freshness_manifest.get(
        "availability_freshness_status"
    )
    odds_freshness_status = (
        freshness_manifest.get("odds", {}).get("status")
        if isinstance(freshness_manifest.get("odds"), dict)
        else None
    )
    outcomes_freshness_status = (
        freshness_manifest.get("finals", {}).get("finality_status")
        if isinstance(freshness_manifest.get("finals"), dict)
        else None
    )

    rows = build_rows(
        model_only=model_only,
        market_comparison=market_comparison,
        snapshot_type=snapshot_type_value,
        snapshot_time_utc=snapshot_time_utc,
        delivery_date=date,
        finality_status=finality_status,
        finality_blocker_codes=finality_blocker_codes,
        availability_freshness_status=availability_freshness_status,
        odds_freshness_status=odds_freshness_status,
        outcomes_freshness_status=outcomes_freshness_status,
        market_snapshot_time_utc=market_snapshot_time_utc,
    )

    written = write_feed_files(
        rows=rows,
        out_dir=out_dir,
        basename=f"{snapshot_label}_snapshot",
        write_jsonl=write_jsonl,
    )

    return {
        "snapshot_type": snapshot_type_value,
        "snapshot_time_utc": snapshot_time_utc,
        "rows": len(rows),
        "model_only_rows_used": len(model_only),
        "market_rows_referenced": (
            0 if market_comparison is None else int(len(market_comparison))
        ),
        "files": written,
        "model_only_source": str(model_only_path.relative_to(REPO_ROOT)),
        "market_comparison_source": (
            str(market_comparison_path.relative_to(REPO_ROOT))
            if market_comparison_path.exists()
            else None
        ),
        "run_manifest_source": (
            str(run_manifest_path.relative_to(REPO_ROOT))
            if run_manifest_path.exists()
            else None
        ),
        "freshness_manifest_source": (
            str(freshness_path.relative_to(REPO_ROOT))
            if freshness_path.exists()
            else None
        ),
        "rows_with_market": sum(1 for r in rows if r.get("line") is not None),
        "rows_model_only": sum(1 for r in rows if r.get("line") is None),
        "tov_rows": sum(1 for r in rows if r.get("stat") == "tov"),
    }


def _lineup_snapshot_present(date: str) -> bool:
    """True only when an upstream lineup-locked package exists. We do not
    fabricate a lineup snapshot from morning data."""
    base = DEL_DIR / date
    woo = base / "wizard_of_odds"
    rm = _read_json(woo / "run_manifest.json")
    if not isinstance(rm, dict):
        return False
    return rm.get("snapshot_type") in {"pre_close", "close_lock", "lineup"}


def _resolve_lineup_snapshot_type(date: str) -> tuple[str, str | None]:
    """Phase 12D — when the upstream wizard_of_odds package is a
    pre_close / close_lock build but BDL has not yet posted confirmed
    lineups, the Derek snapshot should be labelled `near_tip` (with the
    honest lineup_freshness_status), not `lineup`. Returns (snapshot_type,
    lineup_freshness_rollup_summary)."""
    base = DEL_DIR / date
    rm = _read_json(base / "wizard_of_odds" / "run_manifest.json") or {}
    qr = rm.get("quality_rollup") or {}
    rollup = qr.get("lineup_freshness_status") or {}
    if not isinstance(rollup, dict):
        return ("near_tip", None)
    statuses = set(rollup.keys())
    summary = ",".join(f"{k}={v}" for k, v in rollup.items())
    if "confirmed_bdl" in statuses or "confirmed" in statuses:
        return ("lineup", summary)
    return ("near_tip", summary)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True, help="delivery date YYYY-MM-DD")
    ap.add_argument(
        "--run-mode",
        default="unspecified",
        help="M8.8 stamp for unified Derek feed (morning_expected|t25|t5|final_after_game|backtest|unspecified).",
    )
    ap.add_argument(
        "--snapshot",
        choices=["morning", "lineup", "both"],
        default="both",
        help="which snapshot to build",
    )
    args = ap.parse_args()

    out_dir = DEL_DIR / args.date / "derek_forward_feed"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"derek forward feed — date={args.date}  snapshot={args.snapshot}")
    print(f"  out_dir={out_dir.relative_to(REPO_ROOT)}")
    print("=" * 72)

    # Hard source-contract guard: refuse to build Derek's evaluation
    # feed off a raw predictions/all_props snapshot or off the
    # identity-only pre-canonical seed. Both Derek inputs must be
    # downstream of stat_grid → canonical MODEL_ONLY → market_comparison.
    base = DEL_DIR / args.date
    review_pkg_model_only = base / "pmf_model_review_package" / "machine_readable" / "model_only.parquet"
    market_comparison_for_guard = base / "wizard_of_odds" / "market_comparison.parquet"
    source_lineage = _assert_derek_feed_source_contract(
        date=args.date,
        model_only_path=review_pkg_model_only,
        market_comparison_path=market_comparison_for_guard if market_comparison_for_guard.exists() else None,
    )

    morning_entry: dict | None = None
    lineup_entry: dict | None = None
    lineup_status_payload: dict | None = None
    latest_rows: list[dict] | None = None
    latest_label = None

    if args.snapshot in {"morning", "both"}:
        morning_entry = build_snapshot(
            date=args.date,
            snapshot_label="morning",
            snapshot_type_value="morning",
            out_dir=out_dir,
        )
        if morning_entry is None:
            print(
                "  morning: cannot build — model_only.parquet missing for this date",
                file=sys.stderr,
            )
            blocker = (
                f"# Derek forward feed blocker — {args.date}\n\n"
                "morning snapshot could not be built because\n"
                f"`deliveries/{args.date}/pmf_model_review_package/machine_readable/"
                "model_only.parquet` is missing. Run `predict.py` and "
                "`build_daily_pmf_delivery.py` for this date first.\n"
            )
            (DEL_DIR / "DEREK_FORWARD_FEED_BLOCKERS.md").write_text(blocker)
            return 2

    # M8.8 lineup-status freshness guard.
    # When --snapshot morning runs (no lineup phase today yet) the lineup
    # snapshot is intentionally not built — BDL hasn't published confirmed
    # lineups in the morning window. Without this block, the prior day's
    # lineup_snapshot_status.json would remain on disk and downstream
    # readers would see a checked_at_utc from yesterday plus a manifest
    # with lineup_status:null and no way to distinguish "scheduled later"
    # from "build failed".
    # The block always rewrites lineup_snapshot_status.json with today's
    # timestamp and a meaningful "pending_pre_tipoff_run" sentinel, and
    # populates lineup_status_payload so the feed_manifest.lineup_status
    # field carries the same sentinel instead of a bare null.
    if args.snapshot == "morning":
        lineup_status_payload = {
            "status": "pending_pre_tipoff_run",
            "reason": (
                f"Morning-only forward-feed run for {args.date}. "
                "BDL confirmed lineups are not yet available; the lineup "
                "snapshot will be produced by the later "
                "derek_pre_tipoff_refresh / close_lock runs. "
                "Re-check after the pre-tipoff window."
            ),
            "snapshot_mode_running": "morning",
            "lineup_phase_executed_today": False,
            "checked_at_utc": _now_utc_iso(),
            "schema_version": "lineup_snapshot_status.v2",
        }
        (out_dir / "lineup_snapshot_status.json").write_text(
            json.dumps(lineup_status_payload, indent=2)
        )
        print(
            "  lineup: morning-only run — wrote fresh "
            "lineup_snapshot_status.json (pending_pre_tipoff_run, "
            "no fabrication)"
        )

    if args.snapshot in {"lineup", "both"}:
        if _lineup_snapshot_present(args.date):
            snapshot_type_value, lineup_rollup = _resolve_lineup_snapshot_type(
                args.date)
            lineup_entry = build_snapshot(
                date=args.date,
                snapshot_label="lineup",
                snapshot_type_value=snapshot_type_value,
                out_dir=out_dir,
            )
            # Always write a status file alongside the lineup snapshot so
            # Derek can see at a glance whether lineups were confirmed.
            lineup_status_payload = {
                "status": (
                    "confirmed_lineup_snapshot"
                    if snapshot_type_value == "lineup"
                    else "near_tip_projected_lineup_snapshot"
                ),
                "snapshot_type_emitted": snapshot_type_value,
                "lineup_freshness_rollup": lineup_rollup,
                "reason": (
                    "Confirmed BDL lineup data was present in the upstream "
                    "wizard_of_odds package."
                    if snapshot_type_value == "lineup"
                    else "Upstream wizard_of_odds package contains projected "
                    "(not BDL-confirmed) lineup data; snapshot labelled "
                    "near_tip to keep Derek's archive honest."
                ),
                "checked_at_utc": _now_utc_iso(),
            }
            (out_dir / "lineup_snapshot_status.json").write_text(
                json.dumps(lineup_status_payload, indent=2)
            )
            print(
                f"  lineup: emitted as snapshot_type={snapshot_type_value!r}"
            )
        else:
            lineup_status_payload = {
                "status": "pending_lineup_snapshot",
                "reason": (
                    "No pre_close/close_lock/lineup snapshot is on disk for "
                    f"deliveries/{args.date}/wizard_of_odds/. The current "
                    "wizard_of_odds/run_manifest.json snapshot_type is "
                    "'morning'. Run scripts/run_daily_delivery_pipeline.py "
                    f"--date {args.date} --mode pre_close (or close_lock) "
                    "to produce a lineup-aware delivery."
                ),
                "checked_at_utc": _now_utc_iso(),
            }
            (out_dir / "lineup_snapshot_status.json").write_text(
                json.dumps(lineup_status_payload, indent=2)
            )
            print(
                "  lineup: not present — wrote lineup_snapshot_status.json "
                "(no fabrication)"
            )

    # latest_available_snapshot — copy of the most recent snapshot we
    # actually produced. Read the rows back from the snapshot files we
    # just wrote (avoids re-running build_rows).
    if lineup_entry is not None:
        latest_label = "lineup"
        latest_rows_df = pd.read_parquet(out_dir / "lineup_snapshot.parquet")
    elif morning_entry is not None:
        latest_label = "morning"
        latest_rows_df = pd.read_parquet(out_dir / "morning_snapshot.parquet")
    else:
        latest_rows_df = None

    latest_files = None
    if latest_rows_df is not None:
        # Re-emit rather than copy so the file modification time reflects
        # this run.
        latest_files = write_latest_available(
            rows=latest_rows_df.to_dict(orient="records"),
            out_dir=out_dir,
        )

    feed_manifest = {
        "delivery_date": args.date,
        "built_at_utc": _now_utc_iso(),
        "snapshot": args.snapshot,
        "morning": morning_entry,
        "lineup": lineup_entry,
        "lineup_status": lineup_status_payload,
        "latest_available_snapshot": {
            "points_to": latest_label,
            "files": latest_files,
        },
        "schema": {
            "columns": FEED_COLS,
            "identity": IDENTITY_COLS,
            "pmf": PMF_COLS,
            "market": MARKET_COLS,
            "quality": QUALITY_COLS,
        },
        "rules": {
            "pmf_source": "model_only.parquet (canonical)",
            "market_source": "market_comparison.parquet (reference-only)",
            "no_market_anchoring": True,
            "tov_overlay_phase10d": "off",
        },
        "model_source_contract": source_lineage["model_source_contract"],
        "model_source": source_lineage["model_source"],
        "canonical_source": source_lineage["canonical_source"],
        "stat_grid_source": source_lineage["stat_grid_source"],
        "market_comparison_source": source_lineage["market_comparison_source"],
    }
    (out_dir / "feed_manifest.json").write_text(json.dumps(feed_manifest, indent=2, default=str))
    write_feed_readme(
        out_dir,
        delivery_date=args.date,
        manifests={
            "morning": morning_entry,
            "lineup": lineup_entry,
            "lineup_status": lineup_status_payload,
        },
    )

    write_m88_unified_feed(
        date=args.date,
        out_dir=out_dir,
        df=latest_rows_df,
        run_mode=str(args.run_mode),
        lineup_status=lineup_status_payload,
    )

    print("\nfeed manifest summary:")
    if morning_entry:
        print(
            f"  morning rows={morning_entry['rows']}  "
            f"with_market={morning_entry['rows_with_market']}  "
            f"model_only={morning_entry['rows_model_only']}  "
            f"tov={morning_entry['tov_rows']}"
        )
    if lineup_entry:
        print(
            f"  lineup  rows={lineup_entry['rows']}  "
            f"with_market={lineup_entry['rows_with_market']}  "
            f"model_only={lineup_entry['rows_model_only']}  "
            f"tov={lineup_entry['tov_rows']}"
        )
    elif lineup_status_payload:
        print(f"  lineup  status={lineup_status_payload['status']}")
    if latest_files:
        print(
            f"  latest_available -> {latest_label}  rows={latest_files['rows']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
