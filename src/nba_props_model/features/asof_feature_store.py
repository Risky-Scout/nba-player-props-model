"""As-of-safe feature snapshot builder for M8.9."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from nba_props_model.features.player_prop_feature_contract import (
    FEATURE_CONTRACT_VERSION,
    RunMode,
    feature_families,
)
from nba_props_model.features.projected_starters import (
    ProjectedStarterConfig,
    build_projected_starter_frame,
)


class MissingSourceInputsError(RuntimeError):
    """Raised when a required source for same-day snapshot is absent."""


@dataclass(frozen=True)
class SnapshotResult:
    snapshot: pd.DataFrame
    metadata: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_base_universe(
    repo_root: Path,
    date: str,
    *,
    precanonical_seed_path: Path | None = None,
) -> pd.DataFrame:
    """Resolve the base universe for the feature snapshot.

    Precedence is strict:

      1. Canonical MODEL_ONLY parquet/csv under
         ``deliveries/<date>/canonical_source/`` — the production
         source. Always preferred when present.
      2. Pre-canonical slate universe seed, when supplied explicitly
         by the caller AND canonical MODEL_ONLY is not yet on disk.
         The seed only carries identity columns (player_id / game_id /
         slate_date / team / opponent / is_home / game_start_*); it is
         deliberately devoid of PMFs, model probabilities, market
         edges, and any downstream model surface — so it can never
         leak into Derek's evaluation feed or canonical delivery.
      3. Empty DataFrame fallthrough — :func:`build_feature_snapshot`
         maps that to ``SAME_DAY_SOURCE_INPUTS_MISSING``.

    The seed is intentionally NOT a general fallback. Callers must
    pass the path explicitly (i.e. the orchestrator's pre-canonical
    step) — generic callers will never accidentally pick it up.
    """
    root = repo_root / "deliveries" / date / "canonical_source"
    pq = root / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    csv = root / "player_prop_pmfs_tonight_MODEL_ONLY.csv"
    if pq.is_file():
        return pd.read_parquet(pq)
    if csv.is_file():
        return pd.read_csv(csv)
    if precanonical_seed_path is not None and precanonical_seed_path.is_file():
        return pd.read_parquet(precanonical_seed_path)
    return pd.DataFrame()


def _load_availability(repo_root: Path, date: str) -> pd.DataFrame:
    p = repo_root / "data" / "player_availability_asof.parquet"
    if not p.is_file():
        return pd.DataFrame()
    df = pd.read_parquet(p)
    if "game_date" in df.columns:
        df = df[df["game_date"].astype(str) == date]
    return df


def _load_lineup_status(repo_root: Path, date: str) -> dict[str, Any]:
    p = repo_root / "deliveries" / date / "derek_forward_feed" / "lineup_snapshot_status.json"
    return _read_json(p)


def _add_family_placeholders(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for fam in feature_families():
        for feat in fam.features:
            if feat.name not in out.columns:
                out[feat.name] = pd.NA
        if fam.unavailable_status_column not in out.columns:
            out[fam.unavailable_status_column] = "source_unavailable"
        if fam.unavailable_reason_column not in out.columns:
            out[fam.unavailable_reason_column] = "source_unavailable"
    return out


def _populate_identity(df: pd.DataFrame, date: str, run_mode: RunMode, run_id: str, generated_at_utc: str) -> pd.DataFrame:
    out = df.copy()
    defaults = {
        "game_date": date,
        "run_date": date,
        "run_id": run_id,
        "run_mode": run_mode.value,
        "generated_at_utc": generated_at_utc,
        "source_data_asof_utc": generated_at_utc,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "feature_snapshot_id": f"{date}_{run_mode.value}_{uuid.uuid4().hex[:12]}",
    }
    for col, val in defaults.items():
        if col not in out.columns:
            out[col] = val
        else:
            out[col] = out[col].fillna(val)
    if "event_id" not in out.columns:
        out["event_id"] = pd.NA
    if "model_version" not in out.columns:
        out["model_version"] = "unknown"
    return out


AVAILABILITY_CONFIDENCE_NUMERIC_ALIASES: tuple[str, ...] = (
    "availability_confidence_score",
    "confidence_score",
)
AVAILABILITY_CONFIDENCE_PERMISSIVE_ALIASES: tuple[str, ...] = (
    "confidence",
)
# Backwards-compat union for tests that iterate "all known names".
AVAILABILITY_CONFIDENCE_ALIASES: tuple[str, ...] = (
    "availability_confidence",
    *AVAILABILITY_CONFIDENCE_NUMERIC_ALIASES,
    *AVAILABILITY_CONFIDENCE_PERMISSIVE_ALIASES,
)

# Categorical tier strings sometimes appear in source feeds. Map them to
# stable numeric points so downstream ``availability_confidence`` is always
# a float and the original tier label survives in ``availability_confidence_tier``.
AVAILABILITY_CONFIDENCE_TIER_MAP: dict[str, float] = {
    "HIGH": 0.9,
    "HIGH_CONFIDENCE": 0.9,
    "MEDIUM": 0.7,
    "MED": 0.7,
    "MODERATE": 0.7,
    "LOW": 0.5,
    "LOW_CONFIDENCE": 0.5,
    "UNKNOWN": 0.5,
    "NONE": 0.5,
    "": 0.5,
}

_AVAILABILITY_COLUMN_DEFAULTS: dict[str, Any] = {
    "availability_status": "source_unavailable",
    "prob_active": 0.5,
    "availability_confidence": 0.5,
    "availability_source": "player_availability_asof",
    "minutes_restriction_flag": False,
    "num_teammates_out_total": 0,
    "teammate_out_count_guard": 0,
    "teammate_out_count_wing": 0,
    "teammate_out_count_big": 0,
    "is_returning_from_absence": False,
}


def _coalesce_availability_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """Build the canonical ``availability_confidence`` column.

    Priority:
      1. Existing ``availability_confidence`` — kept as-is (may be numeric
         or tier strings; numeric coercion happens later).
      2. Numeric-named score aliases (``availability_confidence_score``,
         ``confidence_score``) — only adopted when the values coerce to
         numbers. A score column carrying tier labels is refused.
      3. Generic ``confidence`` column — accepted as-is (may be numeric or
         categorical tier strings).
    """
    if "availability_confidence" in df.columns:
        return df
    for alias in AVAILABILITY_CONFIDENCE_NUMERIC_ALIASES:
        if alias in df.columns:
            numeric = pd.to_numeric(df[alias], errors="coerce")
            if numeric.notna().any() and float(numeric.notna().mean()) >= 0.5:
                return df.rename(columns={alias: "availability_confidence"})
    for alias in AVAILABILITY_CONFIDENCE_PERMISSIVE_ALIASES:
        if alias in df.columns:
            return df.rename(columns={alias: "availability_confidence"})
    return df


def _coerce_availability_confidence_to_numeric(out: pd.DataFrame) -> None:
    """In-place: split tier strings out into ``availability_confidence_tier``
    and force ``availability_confidence`` to ``float64``.

    Rules:
      * Numeric values pass through.
      * Tier strings (``HIGH``/``MEDIUM``/``MED``/``LOW``/etc.) get preserved
        upper-cased in ``availability_confidence_tier`` and mapped via
        :data:`AVAILABILITY_CONFIDENCE_TIER_MAP`.
      * Unknown / null / unmapped values fall back to 0.5.
      * Pre-existing non-null entries in ``availability_confidence_tier``
        take priority over freshly inferred labels (caller-supplied wins).
    """
    s = out["availability_confidence"]
    numeric_direct = pd.to_numeric(s, errors="coerce")
    s_str_upper = s.astype("string").str.upper().str.strip()
    inferred_tier = s_str_upper.where(numeric_direct.isna(), other=pd.NA)
    tier_numeric = inferred_tier.map(AVAILABILITY_CONFIDENCE_TIER_MAP)
    final_numeric = (
        numeric_direct.fillna(tier_numeric).fillna(0.5).astype("float64")
    )
    out["availability_confidence"] = final_numeric
    if "availability_confidence_tier" in out.columns:
        existing = out["availability_confidence_tier"].astype("string")
        out["availability_confidence_tier"] = existing.where(
            existing.notna() & (existing.str.len() > 0), other=inferred_tier
        ).astype("object")
    else:
        out["availability_confidence_tier"] = inferred_tier.astype("object")


def _apply_availability_defaults(df: pd.DataFrame) -> list[str]:
    """Insert any missing or fully-null availability columns.

    Returns the list of column names that were defaulted (either missing
    outright, or present but entirely null after the merge — which is
    the same effective signal: there was no source row). Never raises on
    missing columns.
    """
    defaulted: list[str] = []
    for col, default in _AVAILABILITY_COLUMN_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
            defaulted.append(col)
            continue
        if len(df) > 0 and bool(df[col].isna().all()):
            df[col] = default
            defaulted.append(col)
    return defaulted


def _populate_availability(snapshot: pd.DataFrame, avail: pd.DataFrame) -> pd.DataFrame:
    out = snapshot.copy()
    keyless = (
        avail.empty
        or "player_id" not in out.columns
        or "player_id" not in avail.columns
    )
    if not keyless:
        avail = _coalesce_availability_confidence(avail)
        cols = [
            c
            for c in ("player_id", *_AVAILABILITY_COLUMN_DEFAULTS.keys(), "days_since_last_played")
            if c in avail.columns
        ]
        av = avail[cols].drop_duplicates(subset=["player_id"])
        overlap = [c for c in av.columns if c != "player_id" and c in out.columns]
        if overlap:
            out = out.drop(columns=overlap)
        out = out.merge(av, on="player_id", how="left")

    defaulted = _apply_availability_defaults(out)
    if "availability_confidence" in defaulted:
        print(
            "AVAILABILITY_CONFIDENCE_DEFAULTED "
            f"rows={len(out)} defaulted_rows={len(out)} "
            f"reason=column_missing_or_all_null_after_merge"
        )
    if defaulted:
        print(
            "AVAILABILITY_FEATURE_SCHEMA_MISSING "
            f"rows={len(out)} missing={defaulted} "
            f"present={[c for c in _AVAILABILITY_COLUMN_DEFAULTS if c not in defaulted]}"
        )

    out["injury_status_current"] = out["availability_status"].fillna("source_unavailable")
    out["injury_status_previous"] = out["injury_status_current"]
    out["injury_status_changed_since_morning"] = False
    out["injury_source"] = out["availability_source"].fillna("player_availability_asof")
    out["injury_report_asof_utc"] = out.get("source_data_asof_utc")
    out["injury_last_updated_utc"] = out.get("source_data_asof_utc")
    out["injury_freshness_minutes"] = 0
    out["injury_freshness_status"] = "fresh"
    out["stale_injury_flag"] = False
    out["prob_active_current"] = out["prob_active"].fillna(0.5)
    out["prob_active_previous"] = out["prob_active_current"]
    out["prob_active_delta_since_morning"] = 0.0
    out["inactive_risk_current"] = 1.0 - out["prob_active_current"].astype(float)
    out["inactive_risk_reason"] = "availability_model"
    out["has_injury_data"] = out["availability_status"].notna()
    _coerce_availability_confidence_to_numeric(out)
    out["minutes_restriction_flag"] = out["minutes_restriction_flag"].fillna(False)
    out["returning_from_injury_flag"] = out["is_returning_from_absence"].fillna(False)
    out["first_game_back_flag"] = out["returning_from_injury_flag"]
    out["probable_flag"] = out["injury_status_current"].astype(str).str.contains("prob", case=False, na=False)
    out["questionable_flag"] = out["injury_status_current"].astype(str).str.contains("questionable", case=False, na=False)
    out["doubtful_flag"] = out["injury_status_current"].astype(str).str.contains("doubtful", case=False, na=False)
    out["out_flag"] = out["injury_status_current"].astype(str).str.contains("out", case=False, na=False)
    out["rest_flag"] = out["injury_status_current"].astype(str).str.contains("rest", case=False, na=False)
    out["personal_absence_flag"] = out["injury_status_current"].astype(str).str.contains("personal", case=False, na=False)
    out["coach_dnp_risk_flag"] = False
    out["num_teammates_out_total"] = out["num_teammates_out_total"].fillna(0)
    out["num_teammates_inactive"] = out["num_teammates_out_total"]
    out["teammate_out_count_guard"] = out["teammate_out_count_guard"].fillna(0)
    out["teammate_out_count_wing"] = out["teammate_out_count_wing"].fillna(0)
    out["teammate_out_count_big"] = out["teammate_out_count_big"].fillna(0)
    out["injury_freshness_status"] = out["injury_status_current"].where(out["has_injury_data"], "source_unavailable")
    return out


def _populate_lineup(
    snapshot: pd.DataFrame,
    run_mode: RunMode,
    status_blob: dict[str, Any],
    repo_root: Path | None = None,
    date: str | None = None,
) -> pd.DataFrame:
    out = snapshot.copy()
    has_official = bool(status_blob.get("official_snapshot_available", False))
    expected_status = str(status_blob.get("expected_lineup_status") or "expected_probable")
    official_status = str(status_blob.get("official_lineup_status") or "not_available_yet")
    out["expected_lineup_available"] = True
    out["expected_lineup_asof_utc"] = out["source_data_asof_utc"]
    out["expected_lineup_last_updated_utc"] = out["source_data_asof_utc"]
    out["expected_lineup_freshness_minutes"] = 0
    out["expected_lineup_freshness_status"] = "fresh"

    projected_prior_used = False
    if repo_root is not None and date is not None and "player_id" in out.columns and "team_id" in out.columns:
        eligible_cols = ["player_id", "team_id"]
        if "prob_active_current" in out.columns:
            eligible_cols.append("prob_active_current")
        elif "prob_active" in out.columns:
            eligible_cols.append("prob_active")
        eligible = out[eligible_cols].drop_duplicates(subset=["player_id", "team_id"]).reset_index(drop=True).copy()
        if "prob_active_current" in eligible.columns:
            eligible["prob_active"] = pd.to_numeric(eligible.pop("prob_active_current"), errors="coerce")
        elif "prob_active" in eligible.columns:
            eligible["prob_active"] = pd.to_numeric(eligible["prob_active"], errors="coerce")
        try:
            prior = build_projected_starter_frame(
                repo_root=repo_root,
                slate_date=date,
                eligible_players=eligible,
                config=ProjectedStarterConfig(),
            )
            out = out.merge(
                prior,
                on=["player_id", "team_id"],
                how="left",
                suffixes=("", "_prior"),
            )
            for col in (
                "expected_starter",
                "expected_starter_prob",
                "expected_lineup_confidence",
                "expected_rotation_rank",
                "expected_bench_role",
                "projected_rotation_slot",
                "projected_closing_lineup_flag",
                "projected_blowout_rotation_risk",
            ):
                prior_col = f"{col}_prior"
                if prior_col in out.columns:
                    out[col] = out[prior_col]
                    out = out.drop(columns=[prior_col])
            projected_prior_used = True
        except Exception:
            projected_prior_used = False

    if not projected_prior_used:
        out["expected_starter"] = False
        out["expected_bench_role"] = True
        out["expected_rotation_rank"] = 8
        out["expected_lineup_confidence"] = 0.5
        out["expected_starter_prob"] = 0.5
        out["projected_rotation_slot"] = "rotation"
        out["projected_closing_lineup_flag"] = False
        out["projected_blowout_rotation_risk"] = 0.1
        out["feature_freshness"] = "projected_lineup"
        out["expected_lineup_source"] = str(
            status_blob.get("expected_lineup_source") or "projected_lineup"
        )
    else:
        out["expected_starter"] = out["expected_starter"].fillna(False).astype(bool)
        out["expected_bench_role"] = out["expected_bench_role"].fillna(True).astype(bool)
        out["expected_rotation_rank"] = (
            pd.to_numeric(out["expected_rotation_rank"], errors="coerce").fillna(15).astype(int)
        )
        out["expected_lineup_confidence"] = (
            pd.to_numeric(out["expected_lineup_confidence"], errors="coerce").fillna(0.5).astype(float)
        )
        out["expected_starter_prob"] = (
            pd.to_numeric(out["expected_starter_prob"], errors="coerce").fillna(0.5).astype(float)
        )
        out["projected_rotation_slot"] = out["projected_rotation_slot"].fillna("deep_bench").astype(str)
        out["projected_closing_lineup_flag"] = out["projected_closing_lineup_flag"].fillna(False).astype(bool)
        out["projected_blowout_rotation_risk"] = (
            pd.to_numeric(out["projected_blowout_rotation_risk"], errors="coerce").fillna(0.1).astype(float)
        )
        if "feature_freshness" not in out.columns:
            out["feature_freshness"] = f"projected_starter_rolling_N{ProjectedStarterConfig().window_n}"
        else:
            out["feature_freshness"] = out["feature_freshness"].fillna(
                f"projected_starter_rolling_N{ProjectedStarterConfig().window_n}"
            )
        if "expected_lineup_source_internal" in out.columns:
            out = out.drop(columns=["expected_lineup_source_internal"])
        legacy_source = str(status_blob.get("expected_lineup_source") or "projected_starter_rolling")
        out["expected_lineup_source"] = (
            f"projected_starter_rolling_N{ProjectedStarterConfig().window_n}"
            if legacy_source in {"projected_lineup", "projected_starter_rolling"}
            else legacy_source
        )
    out["official_lineup_available"] = has_official
    out["official_lineup_source"] = str(status_blob.get("official_lineup_source") or "source_unavailable")
    out["official_lineup_asof_utc"] = out["source_data_asof_utc"]
    out["official_lineup_last_updated_utc"] = out["source_data_asof_utc"]
    out["official_lineup_freshness_minutes"] = 0 if has_official else pd.NA
    out["official_lineup_freshness_status"] = "fresh" if has_official else "source_unavailable"
    out["official_starter"] = False
    out["confirmed_starter"] = False
    out["official_lineup_status"] = official_status if has_official else "not_available_yet"
    out["official_lineup_override_used"] = has_official and run_mode in (RunMode.T25, RunMode.T5)
    out["lineup_changed_since_morning"] = False
    out["projected_to_official_role_delta"] = 0.0
    out["expected_lineup_mislabeled_as_official_flag"] = False
    out["stale_lineup_flag"] = not has_official and run_mode in (RunMode.T25, RunMode.T5)
    out["lineup_source"] = out["official_lineup_source"].where(out["official_lineup_available"], out["expected_lineup_source"])
    out["lineup_last_updated_utc"] = out["source_data_asof_utc"]
    out["expected_lineup_status"] = expected_status
    return out


def assert_availability_confidence_is_numeric(snapshot: pd.DataFrame) -> None:
    """Final pre-parquet guard: ``availability_confidence`` must be numeric.

    Surfaces a structured ``AVAILABILITY_CONFIDENCE_NON_NUMERIC`` failure
    instead of letting pyarrow raise a raw ``ArrowInvalid`` on
    ``to_parquet`` (the tier-string regression that took down run
    25950902639).
    """
    if "availability_confidence" not in snapshot.columns:
        return
    col = snapshot["availability_confidence"]
    if pd.api.types.is_numeric_dtype(col):
        return
    coerced = pd.to_numeric(col, errors="coerce")
    bad_mask = coerced.isna() & col.notna()
    sample = (
        col[bad_mask]
        .astype("string")
        .head(5)
        .tolist()
    )
    raise RuntimeError(
        "AVAILABILITY_CONFIDENCE_NON_NUMERIC "
        f"dtype={col.dtype} n_bad={int(bad_mask.sum())} sample={sample}"
    )


def build_feature_snapshot(
    repo_root: Path,
    date: str,
    run_mode: RunMode,
    *,
    precanonical_seed_path: Path | None = None,
) -> SnapshotResult:
    """Build the as-of-safe feature snapshot for ``date`` / ``run_mode``.

    ``precanonical_seed_path`` is an opt-in identity-only seed used
    only to break the early-pipeline ordering problem (the canonical
    MODEL_ONLY parquet is downstream of stat_grid which itself needs
    the feature snapshot). When canonical MODEL_ONLY exists on disk
    it is always preferred; the seed is consulted only as a fallback,
    and only when the caller explicitly opts in by passing the path.
    """
    generated_at = _now_utc()
    run_id = f"{date}_{run_mode.value}_{uuid.uuid4().hex[:10]}"
    base = _load_base_universe(
        repo_root, date, precanonical_seed_path=precanonical_seed_path
    )
    if base.empty:
        raise MissingSourceInputsError(
            f"SAME_DAY_SOURCE_INPUTS_MISSING: missing canonical_source/player_prop_pmfs_tonight_MODEL_ONLY for {date}"
        )
    snapshot = _add_family_placeholders(base)
    snapshot = _populate_identity(snapshot, date, run_mode, run_id, generated_at)
    snapshot = _populate_availability(snapshot, _load_availability(repo_root, date))
    snapshot = _populate_lineup(
        snapshot,
        run_mode,
        _load_lineup_status(repo_root, date),
        repo_root=repo_root,
        date=date,
    )
    if "unavailable_reason" in snapshot.columns:
        snapshot["unavailable_reason"] = snapshot["unavailable_reason"].fillna("source_unavailable")
    assert_availability_confidence_is_numeric(snapshot)
    metadata = {
        "date": date,
        "run_mode": run_mode.value,
        "n_rows": int(len(snapshot)),
        "generated_at_utc": generated_at,
    }
    return SnapshotResult(snapshot=snapshot, metadata=metadata)
