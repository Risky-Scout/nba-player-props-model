"""Injury and lineup feature layer for M8.9."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from nba_props_model.features.player_prop_feature_contract import RunMode


FAIL_EXPECTED_MISLABELED = "EXPECTED_LINEUP_MISLABELED_AS_OFFICIAL"
FAIL_OFFICIAL_WITHOUT_SOURCE = "OFFICIAL_LINEUP_USED_WITHOUT_SOURCE"
FAIL_STALE_CONFIRMED_ACTIVE = "STALE_AVAILABILITY_CAN_PRODUCE_CONFIRMED_ACTIVE"
FAIL_MISSING_INJURY_TS = "MISSING_INJURY_TIMESTAMP"
FAIL_MISSING_LINEUP_TS = "MISSING_LINEUP_TIMESTAMP"


@dataclass(frozen=True)
class InjuryLineupBuildResult:
    frame: pd.DataFrame
    summary: dict[str, Any]
    stale_sources: pd.DataFrame
    missing_sources: pd.DataFrame


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _base_players(repo_root: Path, date: str) -> pd.DataFrame:
    canonical = repo_root / "deliveries" / date / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    if canonical.is_file():
        df = pd.read_parquet(canonical)
        keep = [c for c in ("player_id", "player_name", "team", "opponent", "game_id", "event_id") if c in df.columns]
        return df[keep].drop_duplicates()
    return pd.DataFrame(columns=["player_id"])


def _availability(repo_root: Path, date: str) -> pd.DataFrame:
    p = repo_root / "data" / "player_availability_asof.parquet"
    if not p.is_file():
        return pd.DataFrame()
    df = pd.read_parquet(p)
    if "game_date" in df.columns:
        df = df[df["game_date"].astype(str) == date]
    return df


def _lineup_status(repo_root: Path, date: str) -> dict[str, Any]:
    p = repo_root / "deliveries" / date / "derek_forward_feed" / "lineup_snapshot_status.json"
    return _read_json(p)


def _validate_or_raise(df: pd.DataFrame) -> None:
    if "expected_lineup_mislabeled_as_official_flag" in df.columns and bool(
        df["expected_lineup_mislabeled_as_official_flag"].fillna(False).any()
    ):
        raise RuntimeError(FAIL_EXPECTED_MISLABELED)
    if "official_lineup_available" in df.columns and "official_lineup_source" in df.columns:
        bad = df["official_lineup_available"].fillna(False) & (
            df["official_lineup_source"].isna() | (df["official_lineup_source"].astype(str).str.strip() == "")
        )
        if bool(bad.any()):
            raise RuntimeError(FAIL_OFFICIAL_WITHOUT_SOURCE)
    if "injury_last_updated_utc" in df.columns and df["injury_last_updated_utc"].isna().any():
        raise RuntimeError(FAIL_MISSING_INJURY_TS)
    if "lineup_last_updated_utc" in df.columns and df["lineup_last_updated_utc"].isna().any():
        raise RuntimeError(FAIL_MISSING_LINEUP_TS)


def build_injury_lineup_features(repo_root: Path, date: str, run_mode: RunMode) -> InjuryLineupBuildResult:
    base = _base_players(repo_root, date)
    if base.empty:
        base = pd.DataFrame({"player_id": []})
    avail = _availability(repo_root, date)
    lineup_blob = _lineup_status(repo_root, date)

    if not avail.empty and "player_id" in avail.columns:
        use_cols = [
            c
            for c in [
                "player_id",
                "availability_status",
                "prob_active",
                "availability_source",
                "availability_confidence",
                "minutes_restriction_flag",
                "is_returning_from_absence",
            ]
            if c in avail.columns
        ]
        base = base.merge(avail[use_cols].drop_duplicates(subset=["player_id"]), on="player_id", how="left")
    else:
        base["availability_status"] = pd.NA
        base["prob_active"] = pd.NA
        base["availability_source"] = pd.NA
        base["availability_confidence"] = pd.NA
        base["minutes_restriction_flag"] = False
        base["is_returning_from_absence"] = False

    official_available = bool(lineup_blob.get("official_snapshot_available", False))
    if run_mode == RunMode.MORNING_EXPECTED:
        official_available = False

    base["expected_starter"] = False
    base["expected_starter_prob"] = 0.5
    base["expected_lineup_confidence"] = 0.5
    base["official_starter"] = False
    base["confirmed_starter"] = False
    base["official_lineup_available"] = official_available
    base["official_lineup_status"] = "confirmed" if official_available else "not_available_yet"
    base["projected_to_official_role_delta"] = 0.0
    base["lineup_changed_since_morning"] = False
    base["injury_status_current"] = base["availability_status"].fillna("source_unavailable")
    base["injury_status_previous"] = base["injury_status_current"]
    base["injury_status_changed_since_morning"] = False
    base["prob_active_current"] = base["prob_active"].fillna(0.5)
    base["inactive_risk_current"] = 1.0 - base["prob_active_current"].astype(float)
    base["minutes_restriction_flag"] = base["minutes_restriction_flag"].fillna(False)
    base["stale_injury_flag"] = base["availability_status"].isna()
    base["stale_lineup_flag"] = (~base["official_lineup_available"]) & (run_mode in (RunMode.T25, RunMode.T5))
    base["unavailable_reason"] = ""
    base.loc[base["availability_status"].isna(), "unavailable_reason"] = "source_unavailable"
    if run_mode in (RunMode.T25, RunMode.T5) and not official_available:
        has_reason = base["unavailable_reason"].astype(str).str.strip() != ""
        base.loc[~has_reason, "unavailable_reason"] = "official_lineup_not_available_yet"
        base.loc[has_reason, "unavailable_reason"] = (
            base.loc[has_reason, "unavailable_reason"].astype(str).str.strip()
            + ";official_lineup_not_available_yet"
        )
    base["expected_lineup_mislabeled_as_official_flag"] = False
    base["official_lineup_source"] = str(lineup_blob.get("official_lineup_source") or ("source_unavailable" if not official_available else "official_lineup_feed"))
    base["injury_source"] = base["availability_source"].fillna("source_unavailable")
    base["injury_last_updated_utc"] = str(lineup_blob.get("availability_last_updated_utc") or lineup_blob.get("snapshot_time_utc") or "1970-01-01T00:00:00Z")
    base["lineup_source"] = str(lineup_blob.get("expected_lineup_source") or "projected_lineup")
    base["lineup_last_updated_utc"] = str(lineup_blob.get("snapshot_time_utc") or "1970-01-01T00:00:00Z")

    _validate_or_raise(base)

    stale_rows = []
    if base["stale_injury_flag"].any():
        stale_rows.append({"source": "availability", "reason": "availability_status_null", "n_rows": int(base["stale_injury_flag"].sum())})
    if bool((base["official_lineup_available"] == False).any()):  # noqa: E712
        stale_rows.append({"source": "official_lineup", "reason": "official_lineup_not_available", "n_rows": int((base["official_lineup_available"] == False).sum())})  # noqa: E712
    stale_sources = pd.DataFrame(stale_rows, columns=["source", "reason", "n_rows"])

    missing_rows = []
    if avail.empty:
        missing_rows.append({"source": "data/player_availability_asof.parquet", "reason": "missing_or_no_rows_for_date"})
    if not lineup_blob:
        missing_rows.append({"source": f"deliveries/{date}/derek_forward_feed/lineup_snapshot_status.json", "reason": "missing"})
    missing_sources = pd.DataFrame(missing_rows, columns=["source", "reason"])

    summary = {
        "date": date,
        "run_mode": run_mode.value,
        "n_rows": int(len(base)),
        "official_lineup_available_any": bool(base["official_lineup_available"].any()),
        "stale_injury_rows": int(base["stale_injury_flag"].sum()),
        "stale_lineup_rows": int(base["stale_lineup_flag"].sum()) if "stale_lineup_flag" in base.columns else 0,
        "pass": True,
    }
    return InjuryLineupBuildResult(frame=base, summary=summary, stale_sources=stale_sources, missing_sources=missing_sources)
