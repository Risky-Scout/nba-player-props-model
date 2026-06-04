"""Player-game eligibility gate.

Single source of truth for whether a (slate_date, game_id, player_id) is
eligible to receive a model PMF in tonight's delivery.

Eligibility rule:

    player_game_eligible = (
        has_current_market_line
    OR starter_probability    >= 0.50
    OR rotation_probability   >= 0.50
    OR minutes_mean           >= 12
    )

Non-goals:
    * Does NOT compute PMFs.
    * Does NOT fetch BDL/Odds inside this module (callers resolve market
      tables via ``load_keyed_current_market_signal``).
    * Does NOT mutate inputs (returns new frames unless noted).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


EMPTY_LINE_VALUES = {"", " ", "NA", "N/A", "nan", "None", None}
ROTATION_MINUTES_FLOOR = 12.0
STARTER_PROB_FLOOR = 0.50
ROTATION_PROB_FLOOR = 0.50

# Full market-evaluation columns (WoO-aligned names where applicable).
_MARKET_SUPERIORITY_COLUMNS = [
    "slate_date",
    "game_id",
    "player_id",
    "stat",
    "line",
    "book",
    "market_over_odds",
    "market_under_odds",
    "market_no_vig_over_prob",
    "snapshot_time_utc",
]


REQUIRED_MINUTES_COLUMNS = [
    "slate_date",
    "game_id",
    "player_id",
    "minutes_mean",
    "minutes_p10",
    "minutes_p50",
    "minutes_p90",
    "minutes_std",
    "rotation_probability",
    "starter_probability",
    "projected_role",
    "p_inactive_used",
]


def normalize_line_column(df: pd.DataFrame, line_col: str = "line") -> pd.DataFrame:
    df = df.copy()
    if line_col not in df.columns:
        df[line_col] = np.nan

    df[line_col] = df[line_col].replace(list(EMPTY_LINE_VALUES), np.nan)
    df[line_col] = pd.to_numeric(df[line_col], errors="coerce")
    return df


def require_minutes_contract(minutes: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_MINUTES_COLUMNS if c not in minutes.columns]
    if missing:
        raise RuntimeError(
            f"minutes_predictions missing required columns: {missing}"
        )

    dupes = minutes.duplicated(["slate_date", "game_id", "player_id"]).sum()
    if dupes:
        raise RuntimeError(
            f"minutes_predictions has duplicate slate_date/game_id/player_id rows: {dupes}"
        )


def build_current_market_player_signal(
    market_df: pd.DataFrame | None,
    *,
    slate_date: str,
    source_label: str | None = None,
) -> pd.DataFrame:
    """One row per (slate_date, game_id, player_id) with line presence.

    Empty input returns an empty frame with the contract output columns.
    Raises SystemExit with marker ``CURRENT_MARKET_SIGNAL_SCHEMA_MISSING_KEYS``
    when required identity columns are absent (never a raw pandas KeyError).
    """
    _empty_out = pd.DataFrame(
        columns=[
            "slate_date",
            "game_id",
            "player_id",
            "has_current_market_line",
            "current_market_line_count",
            "quoted_stats",
        ]
    )
    if market_df is None or market_df.empty:
        return _empty_out

    df = market_df.copy()
    label = source_label or "unknown"

    if "slate_date" not in df.columns:
        if "game_date" in df.columns:
            df["slate_date"] = df["game_date"].astype(str).str[:10]
        else:
            df["slate_date"] = str(slate_date)

    df["slate_date"] = df["slate_date"].astype(str).str[:10]
    df = df[df["slate_date"] == str(slate_date)]

    required_keys = ["slate_date", "game_id", "player_id"]
    missing_keys = [c for c in required_keys if c not in df.columns]
    if missing_keys:
        raise SystemExit(
            "CURRENT_MARKET_SIGNAL_SCHEMA_MISSING_KEYS "
            f"source_label={label!r} row_count={len(df)} missing={missing_keys} "
            f"present={list(df.columns)}"
        )

    n_null_gid = int(df["game_id"].isna().sum())
    n_null_pid = int(df["player_id"].isna().sum())
    if n_null_gid or n_null_pid:
        print(
            f"CURRENT_MARKET_SIGNAL_NULL_KEYS_DROPPED source_label={label!r} "
            f"dropped_game_id={n_null_gid} dropped_player_id={n_null_pid} "
            f"remaining_before_drop={len(df)}"
        )
        df = df.dropna(subset=["game_id", "player_id"])

    if df.empty:
        return _empty_out

    df = normalize_line_column(df, "line")
    df_lined = df.dropna(subset=["line"])

    if df_lined.empty:
        return _empty_out

    if "stat" not in df_lined.columns:
        df_lined = df_lined.copy()
        df_lined["stat"] = None

    out = (
        df_lined.groupby(["slate_date", "game_id", "player_id"], as_index=False)
        .agg(
            current_market_line_count=("line", "size"),
            quoted_stats=(
                "stat",
                lambda s: sorted(set(s.dropna().astype(str))),
            ),
        )
    )
    out["has_current_market_line"] = out["current_market_line_count"] > 0
    return out


def _log_candidate(
    path: str | None,
    exists: bool,
    rows_n: Any,
    columns: Any,
    missing_req: list[str],
    snap_min: Any,
    snap_max: Any,
    accepted: bool,
    rejection_reason: str | None,
) -> None:
    print(
        "CURRENT_MARKET_SIGNAL_CANDIDATE "
        f"path={path!r} exists={exists} rows={rows_n} columns={columns} "
        f"missing_required_keys={missing_req} "
        f"snapshot_time_utc_min={snap_min} snapshot_time_utc_max={snap_max} "
        f"accepted={accepted} rejection_reason={rejection_reason or 'none'}"
    )


def _normalize_odds_aliases(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "market_stat" in out.columns and "stat" not in out.columns:
        out = out.rename(columns={"market_stat": "stat"})
    for col, alt in (("player_id", "bdl_player_id"), ("game_id", "event_id")):
        if col not in out.columns and alt in out.columns:
            out[col] = out[alt]
    # predict.py uses over_odds / under_odds
    if "market_over_odds" not in out.columns and "over_odds" in out.columns:
        out["market_over_odds"] = out["over_odds"]
    if "market_under_odds" not in out.columns and "under_odds" in out.columns:
        out["market_under_odds"] = out["under_odds"]
    if "book" not in out.columns and "bet_vendor" in out.columns:
        out["book"] = out["bet_vendor"]
    if "market_no_vig_over_prob" not in out.columns and "market_prob" in out.columns:
        out["market_no_vig_over_prob"] = out["market_prob"]
    return out


def _snapshot_fresh_for_slate(df: pd.DataFrame, slate_date: str) -> tuple[bool, str]:
    snap_col = None
    for c in ("snapshot_time_utc", "market_snapshot_time_utc"):
        if c in df.columns:
            snap_col = c
            break
    if snap_col is None:
        return False, "missing_snapshot_timestamp"

    ts = pd.to_datetime(df[snap_col], utc=True, errors="coerce")
    if ts.isna().all():
        return False, "missing_snapshot_timestamp"
    vmax = ts.max()
    try:
        dmax = vmax.date().isoformat()
    except Exception:
        return False, "missing_snapshot_timestamp"
    if dmax != str(slate_date):
        return False, "stale_snapshot_time_utc"
    return True, "none"


def _market_eval_ready(df: pd.DataFrame) -> bool:
    cols = df.columns.to_list()
    for c in _MARKET_SUPERIORITY_COLUMNS:
        if c not in cols:
            return False
    if df.empty:
        return False
    # Require at least one non-null line and snapshot in sample
    if "line" in df.columns and df["line"].isna().all():
        return False
    if "snapshot_time_utc" in df.columns and df["snapshot_time_utc"].isna().all():
        return False
    return True


def load_keyed_current_market_signal(
    repo_root: Path,
    slate_date: str,
    *,
    current_run_market_comparison_path: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Resolve a keyed market table for eligibility (identity columns present).

    Tries candidates in order; returns the first accepted keyed frame.
    Diagnostics-only sources never set ``market_eval_available`` or keyed/fresh flags.
    accompanying dict reports manifest-style market evaluation readiness.
    """
    meta: dict[str, Any] = {
        "market_eval_available": False,
        "market_rows_keyed": False,
        "market_rows_fresh": False,
        "market_superiority_claim_allowed": False,
        "market_eval_blocker": "current_market_signal_missing_or_stale_keys",
        "current_market_signal_selected_path": None,
        "current_market_signal_tier": None,
        "market_eval_candidates": [],
    }

    slate_date = str(slate_date)

    candidates: list[tuple[str, Path | None, str]] = [
        ("all_props", repo_root / "predictions" / f"all_props_{slate_date}.parquet", "primary"),
        ("wizard_market_comparison", repo_root / "deliveries" / slate_date / "wizard_of_odds" / "market_comparison.parquet", "secondary"),
        ("odds_pairs_concat", None, "secondary"),
        ("canonical_diagnostic", repo_root / "deliveries" / slate_date / "canonical_source" / "all_props_model_only.parquet", "diagnostic"),
    ]

    if current_run_market_comparison_path is not None:
        candidates.insert(
            1,
            ("wizard_market_comparison_current_run", current_run_market_comparison_path, "secondary"),
        )

    def try_read_parquet(path: Path) -> pd.DataFrame | None:
        if not path.is_file():
            return None
        try:
            return pd.read_parquet(path)
        except Exception:
            return None

    def try_concat_odds() -> pd.DataFrame | None:
        odds_dir = repo_root / "data" / "odds_api" / "processed" / slate_date
        if not odds_dir.is_dir():
            return None
        frames: list[pd.DataFrame] = []
        paths = sorted(odds_dir.glob("odds_pairs_*.parquet"))
        if not paths:
            return None
        for op in paths:
            try:
                frames.append(pd.read_parquet(op))
            except Exception:
                continue
        if not frames:
            return None
        return pd.concat(frames, ignore_index=True)

    selected_df: pd.DataFrame | None = None

    for name, path, tier in candidates:
        rejection: str | None = None
        is_current_run_cmp = name == "wizard_market_comparison_current_run"
        df: pd.DataFrame | None = None
        path_str: str | None
        exists = False
        rows_n = "NA"
        cols: Any = "NA"
        missing_req: list[str] = []
        snap_min = "NA"
        snap_max = "NA"

        if name == "odds_pairs_concat":
            concat = try_concat_odds()
            if concat is None:
                path_str = str(
                    repo_root / "data" / "odds_api" / "processed" / slate_date
                )
                _log_candidate(path_str, False, "NA", "NA", [], "NA", "NA", False, "missing_dir_or_files")
                continue
            df = concat
            path_str = str(
                repo_root / "data" / "odds_api" / "processed" / slate_date
            )
            exists = True
        else:
            path_str = str(path) if path is not None else None
            if path is not None:
                df = try_read_parquet(path)
                exists = df is not None
            else:
                exists = False

        if df is None or df.empty:
            _log_candidate(
                path_str, exists, rows_n if not exists else "0", cols, [], "NA", "NA",
                False, "missing_file" if not exists else "empty_file",
            )
            continue

        df = _normalize_odds_aliases(df)
        rows_n = len(df)
        cols = list(df.columns)
        if "slate_date" not in df.columns:
            df = df.copy()
            df["slate_date"] = slate_date
        df["slate_date"] = df["slate_date"].astype(str).str[:10]

        required = ["slate_date", "game_id", "player_id"]
        missing_req = [c for c in required if c not in df.columns]
        if missing_req:
            _log_candidate(
                path_str, True, rows_n, cols, missing_req, "NA", "NA",
                False, "missing_required_identity_keys",
            )
            continue

        snap_min = snap_max = "NA"
        if "snapshot_time_utc" in df.columns:
            ts = pd.to_datetime(df["snapshot_time_utc"], utc=True, errors="coerce")
            if ts.notna().any():
                snap_min = str(ts.min())
                snap_max = str(ts.max())

        keyed_ok = True
        if bool(df["game_id"].isna().all()) or bool(df["player_id"].isna().all()):
            rejection = "null_identity_keys_only"
            keyed_ok = False

        diagnostics_only = tier == "diagnostic"
        freshness_ok = True
        freshness_reason = "none"

        # Reject stale *deliveries* WoO market_comparison for keyed use unless
        # this is an explicit same-run injection (CURRENT_RUN_* path).
        if (
            not diagnostics_only
            and name.startswith("wizard_market_comparison")
            and not is_current_run_cmp
        ):
            freshness_ok, freshness_reason = _snapshot_fresh_for_slate(df, slate_date)
            if tier == "secondary" and not freshness_ok:
                rejection = freshness_reason or "not_fresh_for_slate"
                keyed_ok = False
        elif name == "wizard_market_comparison_current_run":
            freshness_ok, freshness_reason = _snapshot_fresh_for_slate(df, slate_date)
        elif name == "odds_pairs_concat" and "snapshot_time_utc" in df.columns:
            freshness_ok, freshness_reason = _snapshot_fresh_for_slate(df, slate_date)
            # Keyed eligibility may still use odds_pairs; market_eval uses freshness below.

        meta["market_eval_candidates"].append(
            {
                "name": name,
                "path": path_str,
                "tier": tier,
                "accepted": keyed_ok and rejection is None,
                "rejection_reason": rejection or (None if keyed_ok else "unknown"),
            }
        )

        accepted = keyed_ok and rejection is None
        _log_candidate(
            path_str, True, rows_n, cols, missing_req, snap_min, snap_max,
            accepted, rejection if not accepted else "none",
        )

        if not accepted:
            continue

        # Unmappable: name-like rows only
        if "player_name" in df.columns and df["player_id"].isna().all():
            sample = df.head(5).to_dict("records")
            raise SystemExit(
                "CURRENT_MARKET_SIGNAL_UNMAPPABLE_KEYS "
                f"source={name!r} path={path_str!r} sample_rows={json.dumps(sample, default=str)[:2000]}"
            )

        selected_df = df
        meta["current_market_signal_selected_path"] = path_str
        meta["current_market_signal_tier"] = tier

        keyed = True
        mrows_fresh = bool(freshness_ok) if not diagnostics_only else False
        # Primary all_props from predict has no snapshot_time_utc — not
        # sufficient for market-superiority evaluation per contract.
        primary_no_snap = name == "all_props" and (
            "snapshot_time_utc" not in df.columns
            or bool(df["snapshot_time_utc"].isna().all())
        )
        eval_avail = False
        if diagnostics_only:
            meta["market_eval_blocker"] = "canonical_diagnostic_fallback_not_primary_market_evidence"
            eval_avail = False
        elif primary_no_snap:
            # all_props is the keyed eligibility source but lacks snapshot_time_utc.
            # Scan secondary market sources for market-evaluation metadata so that
            # a valid wizard_of_odds market_comparison can still set market_eval_available=True.
            secondary_paths = [
                ("wizard_market_comparison", repo_root / "deliveries" / slate_date / "wizard_of_odds" / "market_comparison.parquet"),
            ]
            if current_run_market_comparison_path is not None:
                secondary_paths.insert(0, ("wizard_market_comparison_current_run", current_run_market_comparison_path))
            _supplemental_eval_set = False
            for _sec_name, _sec_path in secondary_paths:
                _sec_df = try_read_parquet(_sec_path) if _sec_path.is_file() else None
                if _sec_df is None or _sec_df.empty:
                    continue
                _sec_df = _normalize_odds_aliases(_sec_df)
                # Ensure slate_date column present (market_comparison may not have it)
                if "slate_date" not in _sec_df.columns:
                    _sec_df = _sec_df.copy()
                    _sec_df["slate_date"] = slate_date
                _sec_fresh, _sec_reason = _snapshot_fresh_for_slate(_sec_df, slate_date)
                if _sec_fresh and _market_eval_ready(_sec_df):
                    meta["market_eval_blocker"] = "none"
                    eval_avail = True
                    mrows_fresh = True
                    meta["market_eval_candidates"].append({
                        "name": _sec_name + "_supplemental_eval",
                        "path": str(_sec_path),
                        "tier": "secondary",
                        "accepted": True,
                        "rejection_reason": None,
                    })
                    _supplemental_eval_set = True
                    break
            if not _supplemental_eval_set:
                meta["market_eval_blocker"] = "missing_snapshot_timestamp"
                eval_avail = False
                mrows_fresh = False
        elif _market_eval_ready(df) and freshness_ok:
            eval_avail = True
            meta["market_eval_blocker"] = "none"
        else:
            meta["market_eval_blocker"] = (
                "incomplete_superiority_columns_or_stale_snapshot"
                if freshness_ok
                else freshness_reason
            )

        meta["market_rows_keyed"] = keyed
        meta["market_rows_fresh"] = mrows_fresh
        meta["market_eval_available"] = eval_avail and not diagnostics_only
        meta["market_superiority_claim_allowed"] = bool(
            meta["market_eval_available"] and meta["market_rows_keyed"] and meta["market_rows_fresh"]
        )

        break

    if selected_df is None:
        return pd.DataFrame(), meta

    return selected_df, meta


def merge_delivery_manifest_market_signal_fields(
    manifest: dict[str, Any],
    repo_root: Path,
    slate_date: str,
) -> None:
    """Populate delivery-manifest market-evaluation booleans from the latest
    resolver artifact (artifacts/current_market_signal/{slate}.json).

    Keeps evaluations honest when the artifact is absent: no implicit success.
    """
    defaults = {
        "market_eval_available": False,
        "market_rows_keyed": False,
        "market_rows_fresh": False,
        "market_superiority_claim_allowed": False,
        "market_eval_blocker": "current_market_signal_missing_or_stale_keys",
    }
    marker = repo_root / "artifacts" / "current_market_signal" / f"{slate_date}.json"
    if not marker.is_file():
        for k, v in defaults.items():
            manifest.setdefault(k, v)
        return
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except Exception:
        for k, v in defaults.items():
            manifest.setdefault(k, v)
        return
    for k in defaults:
        if k in data:
            manifest[k] = data[k]
        else:
            manifest.setdefault(k, defaults[k])


def write_current_market_meta(
    repo_root: Path,
    slate_date: str,
    meta: dict[str, Any],
) -> None:
    """Persist resolver metadata for manifests (optional)."""
    out_dir = repo_root / "artifacts" / "current_market_signal"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(meta)
    payload["slate_date"] = slate_date
    (out_dir / f"{slate_date}.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def build_player_game_eligibility(
    player_games: pd.DataFrame,
    minutes_predictions: pd.DataFrame,
    current_market_signal: pd.DataFrame,
    *,
    slate_date: str,
) -> pd.DataFrame:
    require_minutes_contract(minutes_predictions)

    base = player_games.copy()
    if "slate_date" not in base.columns:
        base["slate_date"] = str(slate_date)
    base["slate_date"] = base["slate_date"].astype(str).str[:10]

    required_base = ["slate_date", "game_id", "player_id"]
    missing_base = [c for c in required_base if c not in base.columns]
    if missing_base:
        raise RuntimeError(f"player_games missing required keys: {missing_base}")

    m = minutes_predictions.copy()
    m["slate_date"] = m["slate_date"].astype(str).str[:10]

    sig = current_market_signal.copy()
    if sig.empty:
        sig = pd.DataFrame(
            columns=[
                "slate_date",
                "game_id",
                "player_id",
                "has_current_market_line",
                "current_market_line_count",
                "quoted_stats",
            ]
        )
    else:
        # Ensure optional columns exist for downstream merge.
        if "quoted_stats" not in sig.columns:
            sig["quoted_stats"] = None
        if "current_market_line_count" not in sig.columns:
            sig["current_market_line_count"] = 0

    if "slate_date" not in sig.columns:
        sig["slate_date"] = str(slate_date)
    sig["slate_date"] = sig["slate_date"].astype(str).str[:10]

    keep_cols = [
        "slate_date",
        "game_id",
        "player_id",
        "minutes_mean",
        "minutes_p10",
        "minutes_p50",
        "minutes_p90",
        "minutes_std",
        "rotation_probability",
        "starter_probability",
        "projected_role",
        "p_inactive_used",
        "minutes_source",
        "minutes_model_version",
    ]
    keep_cols = [c for c in keep_cols if c in m.columns]

    merge_sig_cols = [
        "slate_date",
        "game_id",
        "player_id",
        "has_current_market_line",
        "current_market_line_count",
        "quoted_stats",
    ]
    merge_sig_cols = [c for c in merge_sig_cols if c in sig.columns]

    out = (
        base.drop_duplicates(["slate_date", "game_id", "player_id"])
        .merge(
            m[keep_cols],
            on=["slate_date", "game_id", "player_id"],
            how="left",
            validate="one_to_one",
        )
        .merge(
            sig[merge_sig_cols],
            on=["slate_date", "game_id", "player_id"],
            how="left",
        )
    )

    out["has_current_market_line"] = out["has_current_market_line"].fillna(False)

    for c in ["minutes_mean", "rotation_probability", "starter_probability"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out["player_game_eligible"] = (
        out["has_current_market_line"]
        | out["starter_probability"].ge(STARTER_PROB_FLOOR).fillna(False)
        | out["rotation_probability"].ge(ROTATION_PROB_FLOOR).fillna(False)
        | out["minutes_mean"].ge(ROTATION_MINUTES_FLOOR).fillna(False)
    )

    out["eligibility_reason"] = np.select(
        [
            out["has_current_market_line"],
            out["starter_probability"].ge(STARTER_PROB_FLOOR).fillna(False),
            out["rotation_probability"].ge(ROTATION_PROB_FLOOR).fillna(False),
            out["minutes_mean"].ge(ROTATION_MINUTES_FLOOR).fillna(False),
        ],
        [
            "current_market_line",
            "starter_probability",
            "rotation_probability",
            "minutes_floor",
        ],
        default="not_eligible",
    )

    return out


def assert_no_ineligible_pmfs(df: pd.DataFrame, *, label: str) -> None:
    if "player_game_eligible" not in df.columns:
        raise RuntimeError(f"{label} missing player_game_eligible")
    bad = df["player_game_eligible"].astype(bool) == False
    if bad.any():
        sample = df.loc[
            bad,
            [
                c
                for c in [
                    "slate_date",
                    "game_id",
                    "player_id",
                    "player_name",
                    "stat",
                    "minutes_mean",
                    "rotation_probability",
                    "starter_probability",
                    "eligibility_reason",
                ]
                if c in df.columns
            ],
        ].head(25).to_dict("records")
        raise RuntimeError(
            f"{label} contains ineligible PMF rows: {int(bad.sum())}; sample={sample}"
        )
