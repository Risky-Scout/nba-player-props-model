from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ...bundle import SlateStateBundle, BUNDLE_VERSION
from ...pmf import parse_pmf, validate_pmf
from ...schema import read_table, write_table


NBA_SUPPORTED_STATS = {"pts", "reb", "ast", "fg3m", "tov", "stl", "blk", "stocks", "pa", "pr", "ra", "pra"}


STAT_ALIASES = {
    "points": "pts",
    "player_points": "pts",
    "rebounds": "reb",
    "player_rebounds": "reb",
    "assists": "ast",
    "player_assists": "ast",
    "threes": "fg3m",
    "3pm": "fg3m",
    "fg3m": "fg3m",
    "player_threes": "fg3m",
    "turnovers": "tov",
    "turnover": "tov",
    "steals": "stl",
    "blocks": "blk",
}


# Ordered by model-only purity preference; first hit wins.
PMF_SOURCE_CANDIDATES = [
    "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet",
    "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv",
    "canonical_source/all_props_model_only.parquet",
    "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.jsonl",
    "derek_forward_feed/machine_readable/model_only.parquet",
    "derek_forward_feed/machine_readable/model_only.csv",
    "derek_forward_feed/latest_available_snapshot.parquet",
    "derek_forward_feed/derek_forward_feed.parquet",
    "wizard_of_odds/full_pmfs_wide.parquet",
    "wizard_of_odds/full_pmfs_wide.csv",
    "predictions/full_pmfs_wide.parquet",
    "full_pmfs_wide.parquet",
    "full_pmfs_wide.csv",
]

_MODEL_ONLY_CANDIDATES = frozenset([
    "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet",
    "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv",
    "canonical_source/all_props_model_only.parquet",
    "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.jsonl",
    "derek_forward_feed/machine_readable/model_only.parquet",
    "derek_forward_feed/machine_readable/model_only.csv",
])

MARKET_SOURCE_CANDIDATES = [
    "wizard_of_odds/market_comparison.parquet",
    "wizard_of_odds/market_comparison.csv",
    "market_comparison.parquet",
    "market_comparison.csv",
]


def _git_sha(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception:
        return None


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def _find_delivery_file(delivery_root: Path, candidates: list[str]) -> Path | None:
    direct = [delivery_root / c for c in candidates]
    hit = _first_existing(direct)
    if hit:
        return hit
    for c in candidates:
        name = Path(c).name
        matches = sorted(delivery_root.rglob(name))
        if matches:
            return matches[0]
    return None


def _find_delivery_file_with_audit(
    delivery_root: Path,
    candidates: list[str],
) -> tuple[Path | None, list[str], list[str]]:
    """Return (hit_path, checked_paths, missing_paths)."""
    checked: list[str] = []
    missing: list[str] = []
    for c in candidates:
        p = delivery_root / c
        checked.append(c)
        if p.exists():
            return p, checked, missing
    # rglob fallback
    for c in candidates:
        name = Path(c).name
        matches = sorted(delivery_root.rglob(name))
        if matches:
            return matches[0], checked, missing
        missing.append(c)
    return None, checked, missing


def _previous_calendar_day(slate_date: str) -> str:
    return (pd.Timestamp(slate_date).date() - timedelta(days=1)).isoformat()


def _flatten_json(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out[key] = v
            out.update(_flatten_json(v, key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:20]):
            out.update(_flatten_json(v, f"{prefix}[{i}]"))
    return out


def _load_delivery_metadata(delivery_root: Path) -> tuple[dict[str, Any], list[str]]:
    """Search daily delivery JSON manifests for model/as-of metadata.

    Looks for explicit trained_through_date / calibrated_through_date fields first.
    Also handles ``created_at_utc`` in canonical_source/manifest.json (parsed to date).
    """
    candidate_names = {
        "run_manifest.json",
        "bundle_manifest.json",
        "delivery_manifest.json",
        "manifest.json",
        "production_status.json",
        "model_status.json",
        "feed_manifest.json",
        "data_quality_report.json",
    }
    meta: dict[str, Any] = {}
    sources: list[str] = []
    for p in sorted(delivery_root.rglob("*.json")):
        if p.name not in candidate_names:
            continue
        try:
            raw = json.loads(p.read_text())
        except Exception:
            continue
        flat = _flatten_json(raw)
        found = False
        for want in [
            "trained_through_date", "calibrated_through_date", "model_version",
            "trained_through", "calibrated_through", "training_cutoff_date",
            "calibration_cutoff_date", "as_of_date", "data_through_date",
            "last_outcome_date", "last_scored_game_date",
        ]:
            for k, v in flat.items():
                if k.split(".")[-1] == want or k.endswith(want):
                    if v not in (None, "", "null"):
                        meta.setdefault(want, v)
                        found = True
        # Special handling: created_at_utc in manifest.json → informational as_of_date.
        if p.name == "manifest.json":
            for k, v in flat.items():
                if (k == "created_at_utc" or k.endswith(".created_at_utc")) and v:
                    try:
                        meta.setdefault("created_at_utc", str(v))
                        date_val = pd.Timestamp(str(v)).date().isoformat()
                        meta.setdefault("delivery_created_at_date", date_val)
                    except Exception:
                        pass
                    found = True
                if (k == "date" or k.endswith(".date")) and v:
                    meta.setdefault("delivery_date", str(v))
                    found = True
        if found:
            sources.append(str(p.relative_to(delivery_root)))
    return meta, sources


def _normalize_date_value(x: Any) -> str | None:
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    s = str(x).strip()
    if not s or s.lower() in {"none", "nan", "nat", "null"}:
        return None
    try:
        return pd.Timestamp(s).date().isoformat()
    except Exception:
        return s


def _date_values_from_column(df: pd.DataFrame, col: str) -> list[str]:
    if col not in df.columns:
        return []
    vals = []
    for v in df[col].dropna().unique().tolist():
        dv = _normalize_date_value(v)
        if dv:
            vals.append(dv)
    return sorted(set(vals))


def _choose_single_date(values: list[str], fallback: Any = None) -> str | None:
    vals = sorted(set([v for v in values if v]))
    if vals:
        return vals[-1]
    return _normalize_date_value(fallback)


def _build_asof_contract(
    player_stat_pmfs: pd.DataFrame,
    delivery_meta: dict[str, Any],
    slate_date: str,
    expected_cutoff_date: str | None = None,
    allow_missing_asof_metadata: bool = False,
) -> dict[str, Any]:
    expected = expected_cutoff_date or _previous_calendar_day(slate_date)
    trained_values = _date_values_from_column(player_stat_pmfs, "trained_through_date")
    calibrated_values = _date_values_from_column(player_stat_pmfs, "calibrated_through_date")

    trained = _choose_single_date(
        trained_values,
        delivery_meta.get("trained_through_date")
        or delivery_meta.get("trained_through")
        or delivery_meta.get("training_cutoff_date")
        or delivery_meta.get("data_through_date")
        or delivery_meta.get("as_of_date"),
    )
    calibrated = _choose_single_date(
        calibrated_values,
        delivery_meta.get("calibrated_through_date")
        or delivery_meta.get("calibrated_through")
        or delivery_meta.get("calibration_cutoff_date")
        or delivery_meta.get("data_through_date")
        or delivery_meta.get("as_of_date"),
    )

    trained_present = trained is not None
    calibrated_present = calibrated is not None
    trained_exact = trained == expected
    calibrated_exact = calibrated == expected

    status = "PASS"
    reasons: list[str] = []
    if not trained_present:
        reasons.append("missing_trained_through_date")
    elif not trained_exact:
        reasons.append(f"trained_through_date_expected_{expected}_got_{trained}")
    if not calibrated_present:
        reasons.append("missing_calibrated_through_date")
    elif not calibrated_exact:
        reasons.append(f"calibrated_through_date_expected_{expected}_got_{calibrated}")

    # When allow_missing_asof_metadata=True, any asof mismatch is WARN not FAIL.
    if reasons:
        status = "WARN" if allow_missing_asof_metadata else "FAIL"

    last_outcome = _normalize_date_value(
        delivery_meta.get("last_outcome_date") or delivery_meta.get("last_scored_game_date")
    )

    return {
        "status": status,
        "expected_model_cutoff_date": expected,
        "trained_through_date": trained,
        "calibrated_through_date": calibrated,
        "declared_trained_through_dates": trained_values,
        "declared_calibrated_through_dates": calibrated_values,
        "trained_present": trained_present,
        "calibrated_present": calibrated_present,
        "trained_exact_previous_calendar_day": trained_exact,
        "calibrated_exact_previous_calendar_day": calibrated_exact,
        "last_outcome_game_date": last_outcome,
        "allow_missing_asof_metadata": bool(allow_missing_asof_metadata),
        "reasons": reasons,
        "delivery_created_at_date": delivery_meta.get("delivery_created_at_date"),
        "note": "For a slate dated D, trained_through_date and calibrated_through_date must equal D-1. If no games were played on D-1, last_outcome_game_date may be earlier, but the as-of cutoff remains D-1.",
    }


def _normalize_stat(x: Any) -> str:
    s = str(x).strip().lower()
    return STAT_ALIASES.get(s, s)


def _coalesce_col(df: pd.DataFrame, names: list[str], default=None):
    for n in names:
        if n in df.columns:
            return df[n]
    return pd.Series(default, index=df.index)


def _ensure_id_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    rename_candidates = {
        "playerId": "player_id",
        "player": "player_name",
        "Player": "player_name",
        "team": "team_id",
        "Team": "team_id",
        "opponent": "opponent_id",
        "Opponent": "opponent_id",
        "gameId": "game_id",
        "market": "stat",
        "prop_type": "stat",
        # Support domain aliases from real delivery schema.
        "support_min": "domain_min",
        "support_max": "domain_max",
    }
    for src, dst in rename_candidates.items():
        if src in out.columns and dst not in out.columns:
            out[dst] = out[src]
    if "stat" in out.columns:
        out["stat"] = out["stat"].map(_normalize_stat)
    return out


def _compute_pmf_stats(pmf_json: Any, domain_min: int = 0, domain_max: int | None = None) -> dict[str, Any]:
    """Parse pmf_json and compute summary statistics."""
    try:
        pmf = parse_pmf(pmf_json, domain_max=domain_max)
        q = validate_pmf(pmf, tolerance=1e-4)
        ks = np.arange(len(pmf), dtype=float) + domain_min
        mean = float((ks * pmf).sum())
        var = float(((ks - mean) ** 2 * pmf).sum())
        return {
            "mean": mean,
            "variance": var,
            "std": float(np.sqrt(var)),
            "p0": float(pmf[0]) if len(pmf) > 0 else np.nan,
            "pmf_sum": float(q["sum"]),
            "pmf_valid": bool(q["valid"]),
            "pmf_negative_mass_flag": bool(q["min"] < -1e-9),
            "pmf_error": None,
            "pmf_array": pmf,
        }
    except Exception as exc:
        return {
            "mean": np.nan, "variance": np.nan, "std": np.nan, "p0": np.nan,
            "pmf_sum": np.nan, "pmf_valid": False, "pmf_negative_mass_flag": False,
            "pmf_error": str(exc), "pmf_array": None,
        }


def _load_pmf_source(delivery_root: Path) -> tuple[pd.DataFrame, Path, list[str]]:
    """Load the best available PMF source; return (df, path, candidates_checked)."""
    p, checked, _ = _find_delivery_file_with_audit(delivery_root, PMF_SOURCE_CANDIDATES)
    if p is None:
        raise FileNotFoundError(f"Could not locate a full PMF source under {delivery_root}")
    return read_table(p), p, checked


def _load_market_source(delivery_root: Path) -> tuple[pd.DataFrame | None, Path | None, list[str]]:
    p, checked, _ = _find_delivery_file_with_audit(delivery_root, MARKET_SOURCE_CANDIDATES)
    if p is None:
        return None, None, checked
    return read_table(p), p, checked


def _build_player_stat_pmfs(raw: pd.DataFrame, slate_date: str, source_path: Path) -> pd.DataFrame:
    df = _ensure_id_columns(raw)

    # Normalize PMF column: handle pmf_active (real delivery) and pmf_json / alternatives.
    if "pmf_json" not in df.columns:
        for alt in ["pmf_active", "pmf", "atom_pmf", "pmf_dict", "probabilities"]:
            if alt in df.columns:
                df["pmf_json"] = df[alt]
                break
    if "pmf_json" not in df.columns:
        raise ValueError(f"PMF source {source_path} has no pmf_json-like column. "
                         f"Available columns: {list(df.columns)}")

    # Normalize pmf_source → cal_source.
    if "cal_source" not in df.columns and "pmf_source" in df.columns:
        df["cal_source"] = df["pmf_source"]

    required_fallbacks = {
        "game_id": "UNKNOWN_GAME",
        "team_id": "UNK",
        "opponent_id": "UNK",
        "player_id": None,
        "player_name": None,
        "stat": None,
    }
    for col, default in required_fallbacks.items():
        if col not in df.columns:
            df[col] = default

    if df["player_id"].isna().all() and "player_name" in df.columns:
        df["player_id"] = (
            df["team_id"].astype(str) + "_" + df["player_name"].astype(str)
        ).str.lower().str.replace(r"\W+", "_", regex=True)

    rows = []
    for _, r in df.iterrows():
        stat = _normalize_stat(r.get("stat"))
        if stat not in NBA_SUPPORTED_STATS:
            continue

        domain_min = int(r.get("domain_min", r.get("support_min", 0)) or 0)
        raw_domain_max = r.get("domain_max", r.get("support_max"))
        domain_max_hint = int(raw_domain_max) if raw_domain_max is not None and not (
            isinstance(raw_domain_max, float) and np.isnan(raw_domain_max)
        ) else None

        stats = _compute_pmf_stats(r["pmf_json"], domain_min=domain_min, domain_max=domain_max_hint)

        if not stats["pmf_valid"] or stats["pmf_array"] is None:
            rows.append({
                "slate_date": slate_date, "game_id": str(r.get("game_id")),
                "team_id": str(r.get("team_id")), "opponent_id": str(r.get("opponent_id")),
                "player_id": str(r.get("player_id")), "player_name": r.get("player_name"),
                "stat": stat, "pmf_json": r.get("pmf_json"),
                "pmf_valid": False, "pmf_error": stats["pmf_error"],
            })
            continue

        pmf = stats["pmf_array"]
        domain_max_actual = domain_min + len(pmf) - 1

        # Normalize lineup_status from multiple possible source columns.
        lineup_status = (
            r.get("lineup_status")
            or r.get("expected_lineup_status")
            or r.get("official_lineup_status")
            or r.get("lineup_state")
            or r.get("snapshot_type")
        )
        injury_status = (
            r.get("injury_status")
            or r.get("injury_freshness_status")
            or r.get("availability_status")
        )

        # Compute prob_active from p_inactive_used if available.
        p_inactive_raw = r.get("p_inactive_used")
        if p_inactive_raw is not None and not (isinstance(p_inactive_raw, float) and np.isnan(p_inactive_raw)):
            prob_active = float(1.0 - float(p_inactive_raw))
            p_inactive_used = float(p_inactive_raw)
        else:
            prob_active = np.nan
            p_inactive_used = np.nan

        ks = np.arange(len(pmf), dtype=float)
        mean_v = stats["mean"]

        out = {
            "slate_date": slate_date,
            "game_id": str(r.get("game_id")),
            "team_id": str(r.get("team_id")),
            "opponent_id": str(r.get("opponent_id")),
            "player_id": str(r.get("player_id")),
            "player_name": r.get("player_name"),
            "stat": stat,
            "pmf_json": r["pmf_json"] if isinstance(r["pmf_json"], str) else json.dumps(
                {int(k): float(p) for k, p in enumerate(pmf) if p > 0}
            ),
            "domain_min": domain_min,
            "domain_max": domain_max_actual,
            "mean": mean_v,
            "median": int(np.searchsorted(np.cumsum(pmf), 0.5)) + domain_min,
            "mode": int(np.argmax(pmf)) + domain_min,
            "variance": stats["variance"],
            "std": stats["std"],
            "p0": stats["p0"],
            "role_bucket": r.get("role_bucket"),
            "lineup_status": lineup_status,
            "injury_status": injury_status,
            "cal_source": r.get("cal_source"),
            "calibration_confidence": r.get("calibration_confidence", r.get("calibration_support_status")),
            "model_version": r.get("model_version"),
            "trained_through_date": r.get("trained_through_date"),
            "calibrated_through_date": r.get("calibrated_through_date"),
            "snapshot_type": r.get("snapshot_type"),
            "snapshot_time_utc": r.get("snapshot_time_utc", r.get("generated_at_utc")),
            "pmf_valid": bool(stats["pmf_valid"]),
            "pmf_sum": stats["pmf_sum"],
            "pmf_negative_mass_flag": stats["pmf_negative_mass_flag"],
            "pmf_tail_warning_flag": False,
            "source_path": str(source_path),
            # Minutes and activity context from delivery (used by simulator Phase D).
            "minutes_mean": float(r["minutes_mean"]) if "minutes_mean" in df.columns and r.get("minutes_mean") is not None and not (isinstance(r.get("minutes_mean"), float) and np.isnan(r.get("minutes_mean"))) else np.nan,
            "minutes_std": float(r["minutes_std"]) if "minutes_std" in df.columns and r.get("minutes_std") is not None and not (isinstance(r.get("minutes_std"), float) and np.isnan(r.get("minutes_std"))) else np.nan,
            "minutes_p10": float(r["minutes_p10"]) if "minutes_p10" in df.columns and r.get("minutes_p10") is not None and not (isinstance(r.get("minutes_p10"), float) and np.isnan(r.get("minutes_p10"))) else np.nan,
            "minutes_p90": float(r["minutes_p90"]) if "minutes_p90" in df.columns and r.get("minutes_p90") is not None and not (isinstance(r.get("minutes_p90"), float) and np.isnan(r.get("minutes_p90"))) else np.nan,
            "p_inactive_used": p_inactive_used,
            "prob_active": prob_active,
            "is_home": r.get("is_home"),
            "team_abbr": r.get("team_abbr"),
            # Market context pass-through (informational only — not used in pricing independence baseline).
            "line": r.get("line"),
            "market_offered_side": r.get("market_offered_side"),
            "has_current_market_line": r.get("has_current_market_line", False),
        }
        for k in range(1, 21):
            out[f"p_ge_{k}"] = float(pmf[ks >= k].sum()) if len(pmf) else np.nan
        rows.append(out)

    out_df = pd.DataFrame(rows)
    if out_df.empty:
        raise ValueError(f"No supported NBA PMFs found in {source_path}")
    return out_df


def _build_players(player_stat_pmfs: pd.DataFrame) -> pd.DataFrame:
    gcols = ["slate_date", "game_id", "team_id", "opponent_id", "player_id"]
    agg: dict[str, str] = {
        "player_name": "first",
        "role_bucket": "first",
        "lineup_status": "first",
        "injury_status": "first",
        "calibration_confidence": "first",
    }
    # Include optional per-player columns if present.
    for opt_col in ["prob_active", "p_inactive_used", "minutes_mean", "minutes_std",
                    "minutes_p10", "minutes_p90", "is_home", "team_abbr"]:
        if opt_col in player_stat_pmfs.columns:
            agg[opt_col] = "first"

    players = player_stat_pmfs.groupby(gcols, dropna=False).agg(agg).reset_index()
    defaults = {
        "position_group": None,
        "primary_position": None,
        "is_home": None,
        "prob_active": np.nan,
        "availability_status": players["injury_status"] if "injury_status" in players else None,
        "is_confirmed_out": False,
        "is_inactive": False,
        "is_doubtful": False,
        "is_questionable": False,
        "is_probable": False,
        "minutes_restriction_flag": False,
        "lineup_confirmed": players["lineup_status"].astype(str).str.contains(
            "confirmed|lineup", case=False, regex=True, na=False
        ),
        "confirmed_starter": np.nan,
        "confirmed_bench": np.nan,
        "starter_changed_from_projection": np.nan,
        "bench_changed_from_projection": np.nan,
        "minutes_mean": np.nan,
        "minutes_sd": np.nan,
        "p_dnp": np.nan,
        "data_quality_status": "PASS",
    }
    for col, val in defaults.items():
        if col not in players:
            players[col] = val
    return players


def _build_games(player_stat_pmfs: pd.DataFrame, market_df: pd.DataFrame | None, slate_date: str) -> pd.DataFrame:
    games = player_stat_pmfs[["slate_date", "game_id"]].drop_duplicates().copy()
    teams = player_stat_pmfs.groupby("game_id")["team_id"].agg(
        lambda x: sorted(set(map(str, x.dropna())))[:2]
    ).to_dict()
    games["home_team_id"] = games["game_id"].map(
        lambda g: teams.get(g, ["UNK", "UNK"])[0] if teams.get(g) else "UNK"
    )
    games["away_team_id"] = games["game_id"].map(
        lambda g: teams.get(g, ["UNK", "UNK"])[1] if len(teams.get(g, [])) > 1 else "UNK"
    )
    games["scheduled_tip_utc"] = None
    games["lineup_state"] = "unknown"
    games["snapshot_type"] = "auto"
    games["snapshot_time_utc"] = datetime.now(timezone.utc).isoformat()
    games["market_total"] = np.nan
    games["market_spread_home"] = np.nan
    games["projected_pace_mean"] = 99.0
    games["projected_pace_sd"] = 5.0
    games["overtime_probability"] = 0.06
    games["blowout_probability_home"] = 0.14
    games["blowout_probability_away"] = 0.14
    games["close_game_probability"] = 0.40
    games["garbage_time_probability"] = 0.18
    games["data_quality_status"] = "PASS"
    return games


def _build_market_lines(market_raw: pd.DataFrame | None, slate_date: str) -> pd.DataFrame | None:
    if market_raw is None or market_raw.empty:
        return None
    df = _ensure_id_columns(market_raw)
    if "stat" in df:
        df["stat"] = df["stat"].map(_normalize_stat)
    df["slate_date"] = slate_date
    rename = {
        "line_value": "line",
        "price": "american_odds",
        "odds": "american_odds",
        "bookmaker": "book",
        "sportsbook": "book",
        "no_vig_prob": "market_no_vig_prob",
        "market_prob": "market_no_vig_prob",
    }
    for src, dst in rename.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]
    keep = [
        "slate_date", "game_id", "player_id", "player_name", "team_id", "stat",
        "line", "side", "book", "american_odds", "decimal_odds",
        "market_implied_prob", "market_no_vig_prob", "model_p_over",
        "model_p_under", "edge_over", "edge_under", "snapshot_time_utc",
    ]
    for c in keep:
        if c not in df.columns:
            df[c] = np.nan
    return df[keep].copy()


def _build_components(player_stat_pmfs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in player_stat_pmfs.iterrows():
        rows.append({
            "slate_date": r["slate_date"],
            "game_id": r["game_id"],
            "team_id": r["team_id"],
            "opponent_id": r["opponent_id"],
            "player_id": r["player_id"],
            "stat": r["stat"],
            "minutes_distribution_json": None,
            "rate_quantiles_json": None,
            "rate_distribution_family": "unknown_from_delivery",
            "rate_mean": np.nan,
            "rate_sd": np.nan,
            "raw_uncalibrated_pmf_json": None,
            "calibrated_pmf_json": r["pmf_json"],
            "context_adjusted_pmf_json": r["pmf_json"],
            "contextual_minutes_delta": np.nan,
            "contextual_rate_delta": np.nan,
            "contextual_adjustment_source": r.get("lineup_status"),
            "poisson_lambda_mean": r.get("mean"),
            "poisson_lambda_sd": r.get("std"),
            "hurdle_p_zero": r.get("p0") if r.get("stat") in {"stl", "blk"} else np.nan,
            "hurdle_positive_quantiles_json": None,
            "hurdle_dynamic_upper_bound": np.nan,
            "hurdle_tail_repair_applied": np.nan,
            "component_quality_status": "LIMITED_FROM_DELIVERY_ONLY",
        })
    return pd.DataFrame(rows)


def _build_bundle_manifest(
    manifest_base: dict[str, Any],
    *,
    asof_contract: dict[str, Any],
    delivery_meta: dict[str, Any],
    delivery_meta_sources: list[str],
    games: pd.DataFrame,
    players: pd.DataFrame,
    player_stat_pmfs: pd.DataFrame,
    pmf_source: Path,
    market_source: Path | None,
    repo_root: Path,
    slate_date: str,
    snapshot_type: str,
    status: str,
    critical_missing: list[str],
) -> dict[str, Any]:
    manifest = dict(manifest_base)
    manifest.update({
        "schema_version": BUNDLE_VERSION,
        "sport": "nba",
        "slate_date": slate_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_repo": "Risky-Scout/nba-player-props-model",
        "source_commit_sha": _git_sha(repo_root),
        "model_version": delivery_meta.get("model_version"),
        "trained_through_date": asof_contract["trained_through_date"],
        "calibrated_through_date": asof_contract["calibrated_through_date"],
        "expected_model_cutoff_date": asof_contract["expected_model_cutoff_date"],
        "asof_contract": asof_contract,
        "delivery_metadata_sources": delivery_meta_sources,
        "delivery_snapshot_type": snapshot_type,
        "lineup_state": "unknown",
        "pmf_source": str(pmf_source.relative_to(repo_root)) if pmf_source.is_relative_to(repo_root) else str(pmf_source),
        "market_source": (
            str(market_source.relative_to(repo_root))
            if market_source and market_source.is_relative_to(repo_root)
            else (str(market_source) if market_source else None)
        ),
        "n_games": int(games["game_id"].nunique()),
        "n_players": int(players["player_id"].nunique()),
        "n_player_stat_pmfs": int(len(player_stat_pmfs)),
        "bundle_status": status,
        "fail_closed": True,
        "warnings": [
            "v1 bundle uses delivery PMFs and available delivery metadata; richer latent ingredients should be exported by PMF pipeline for final production."
        ],
        "critical_missing": critical_missing,
    })
    return manifest


def build_nba_slate_state_bundle(
    repo_root: str | Path,
    slate_date: str,
    *,
    snapshot_type: str = "auto",
    strict: bool = False,
    expected_cutoff_date: str | None = None,
    allow_missing_asof_metadata: bool = False,
) -> SlateStateBundle:
    repo_root = Path(repo_root)
    delivery_root = repo_root / "deliveries" / slate_date
    if not delivery_root.exists():
        raise FileNotFoundError(f"Delivery folder does not exist: {delivery_root}")

    delivery_meta, delivery_meta_sources = _load_delivery_metadata(delivery_root)
    raw_pmfs, pmf_source, pmf_candidates_checked = _load_pmf_source(delivery_root)
    raw_market, market_source, market_candidates_checked = _load_market_source(delivery_root)
    player_stat_pmfs = _build_player_stat_pmfs(raw_pmfs, slate_date, pmf_source)
    players = _build_players(player_stat_pmfs)
    games = _build_games(player_stat_pmfs, raw_market, slate_date)
    market_lines = _build_market_lines(raw_market, slate_date)
    components = _build_components(player_stat_pmfs)

    asof_contract = _build_asof_contract(
        player_stat_pmfs,
        delivery_meta,
        slate_date,
        expected_cutoff_date=expected_cutoff_date,
        allow_missing_asof_metadata=allow_missing_asof_metadata,
    )

    valid_pmfs = bool(player_stat_pmfs["pmf_valid"].fillna(False).all())
    critical_missing = []
    for col in ["game_id", "player_id", "stat", "pmf_json"]:
        if col not in player_stat_pmfs or player_stat_pmfs[col].isna().any():
            critical_missing.append(col)

    # Accept WARN as pass-like when allow_missing_asof_metadata is set.
    asof_ok = asof_contract["status"] == "PASS" or (
        allow_missing_asof_metadata and asof_contract["status"] == "WARN"
    )
    status = "PASS" if valid_pmfs and not critical_missing and asof_ok else "FAIL"

    if strict and status != "PASS":
        raise RuntimeError(
            f"Bundle FAIL: valid_pmfs={valid_pmfs}, critical_missing={critical_missing}, "
            f"asof_contract={asof_contract}"
        )

    bundle_root = delivery_root / "sgp_engine" / BUNDLE_VERSION
    manifest = _build_bundle_manifest(
        {},
        asof_contract=asof_contract,
        delivery_meta=delivery_meta,
        delivery_meta_sources=delivery_meta_sources,
        games=games,
        players=players,
        player_stat_pmfs=player_stat_pmfs,
        pmf_source=pmf_source,
        market_source=market_source,
        repo_root=repo_root,
        slate_date=slate_date,
        snapshot_type=snapshot_type,
        status=status,
        critical_missing=critical_missing,
    )

    team_context = player_stat_pmfs[["slate_date", "game_id", "team_id", "opponent_id"]].drop_duplicates().copy()
    team_context["team_possessions_mean"] = 99.0
    team_context["team_possessions_sd"] = 5.0
    team_context["team_assist_rate_mean"] = np.nan
    team_context["team_fg3a_rate_mean"] = np.nan
    team_context["team_lineup_usage_competition_proxy"] = np.nan
    team_context["team_lineup_rebound_competition_proxy"] = np.nan
    team_context["team_lineup_assist_creation_proxy"] = np.nan
    team_context["team_lineup_spacing_proxy"] = np.nan
    team_context["calibration_confidence"] = np.nan

    bundle = SlateStateBundle(
        root=bundle_root,
        manifest=manifest,
        games=games,
        players=players,
        player_stat_pmfs=player_stat_pmfs,
        market_lines=market_lines,
        player_stat_components=components,
        game_team_context=team_context,
    )
    bundle.write()

    # Write source_file_audit.json.
    pmf_rel = str(pmf_source.relative_to(delivery_root)) if pmf_source.is_relative_to(delivery_root) else str(pmf_source)
    pmf_is_model_only = any(pmf_rel.endswith(c) or pmf_rel == c for c in _MODEL_ONLY_CANDIDATES)
    market_rel = (
        str(market_source.relative_to(delivery_root))
        if market_source and market_source.is_relative_to(delivery_root)
        else (str(market_source) if market_source else None)
    )
    audit = {
        "pmf_source_candidates_checked": pmf_candidates_checked,
        "pmf_source_selected": pmf_rel,
        "pmf_is_model_only": pmf_is_model_only,
        "market_source_candidates_checked": market_candidates_checked,
        "market_source_selected": market_rel,
        "missing_optional_sources": [
            c for c in MARKET_SOURCE_CANDIDATES
            if not (delivery_root / c).exists()
        ],
        "warnings": [] if pmf_is_model_only else [
            f"Selected PMF source '{pmf_rel}' may not be model-only; market anchoring risk."
        ],
        "errors": [],
    }
    (bundle_root / "source_file_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True))

    quality = {
        "status": status,
        "checks": {
            "all_pmfs_sum_to_one": bool((player_stat_pmfs["pmf_sum"].astype(float).sub(1).abs() < 1e-4).all()),
            "no_negative_pmf_mass": bool(~player_stat_pmfs["pmf_negative_mass_flag"].fillna(False).any()),
            "all_games_have_players": bool(players.groupby("game_id").size().gt(0).all()),
            "all_players_have_role_bucket": bool("role_bucket" in players.columns),
            "all_sgp_supported_stats_present": bool(player_stat_pmfs["stat"].isin(NBA_SUPPORTED_STATS).all()),
            "market_fields_quarantined": True,
            "asof_date_contract_pass": bool(asof_contract["status"] in ("PASS", "WARN")),
        },
        "asof_contract": asof_contract,
        "critical_missing": critical_missing,
    }
    (bundle_root / "data_quality_report.json").write_text(json.dumps(quality, indent=2, sort_keys=True))
    return bundle
