#!/usr/bin/env python3
"""Build Derek per-game snapshots directly from corrected WoO PMF delivery.

Source of truth:
  deliveries/{date}/wizard_of_odds/full_pmfs_wide.parquet

Hard guards:
  - production stats must be exactly the mission canonical 11
    (pts/reb/ast/fg3m/tov/stl/blk/stocks/pa/pr/pra)
  - role_bucket must be present
  - no_games_today.json is illegal when PMF delivery has games
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys  # M8.1: defensive — already imported elsewhere is fine
sys.path.insert(0, str(REPO_ROOT / "src"))  # noqa: E402

from nba_props_model.targets import (  # noqa: E402
    MISSION_REQUIRED_TARGETS_CANONICAL,
)

CORE_STATS = MISSION_REQUIRED_TARGETS_CANONICAL  # M8.1: was 5-stat literal
CORE_SET = set(CORE_STATS)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_pmf(x: Any) -> dict[int, float]:
    if isinstance(x, dict):
        raw = x
    else:
        s = "" if x is None else str(x).strip()
        if not s or s in {"nan", "None", "{}"}:
            return {}
        try:
            raw = json.loads(s)
        except Exception:
            raw = json.loads(s.replace("'", '"'))

    out: dict[int, float] = {}
    for k, v in raw.items():
        ki = int(float(k))
        pv = float(v)
        if math.isfinite(pv) and pv >= 0:
            out[ki] = out.get(ki, 0.0) + pv
    total = sum(out.values())
    return {k: v / total for k, v in out.items()} if total > 0 else {}


def _validate_wide(df: pd.DataFrame, path: Path) -> None:
    if df.empty:
        raise SystemExit(f"FATAL: empty PMF delivery source: {path}")

    stats = set(df["stat"].astype(str).str.lower())
    extra = sorted(stats - CORE_SET)
    missing = sorted(CORE_SET - stats)
    if extra or missing:
        raise SystemExit(
            f"FATAL: bad Derek PMF source stats: missing={missing} extra={extra} path={path}"
        )

    counts = df["stat"].astype(str).str.lower().value_counts()
    if counts.min() != counts.max():
        raise SystemExit(f"FATAL: uneven stat coverage in {path}: {counts.sort_index().to_dict()}")

    if "role_bucket" not in df.columns:
        raise SystemExit(f"FATAL: missing role_bucket in {path}")

    role_missing = df["role_bucket"].isna() | df["role_bucket"].astype(str).str.lower().isin(
        ["", "none", "nan", "unknown"]
    )
    if bool(role_missing.any()):
        raise SystemExit(f"FATAL: missing role_bucket rows: {int(role_missing.sum())}/{len(df)}")


QUARANTINED_PUBLIC_COLUMNS: tuple[str, ...] = (
    "model_projected_mean",
    "model_probability_over_market_line",
    "model_prob_over_raw",
    "model_prob_over_active",
    "model_p_over",
)


def _drop_quarantined_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    cols = [c for c in QUARANTINED_PUBLIC_COLUMNS if c in df.columns]
    if not cols:
        return df
    return df.drop(columns=cols)


def _pmf_array_from_jsonish(x: Any) -> list[float] | None:
    d = _parse_pmf(x)
    if not d:
        return None
    arr = [0.0] * (max(d) + 1)
    for k, v in d.items():
        arr[k] = v
    s = sum(arr)
    if s <= 0:
        return None
    return [v / s for v in arr]


def _pmf_direct_mean(pmf_arr: list[float]) -> float:
    return float(sum(i * p for i, p in enumerate(pmf_arr)))


def _pmf_direct_p_over(pmf_arr: list[float], line: Any) -> float | None:
    try:
        line_f = float(line)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(line_f):
        return None
    return float(sum(p for i, p in enumerate(pmf_arr) if i > line_f))


def _stamp_pmf_native_public_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure ``pmf_mean`` and ``p_over`` are present on public rows.

    Recomputes both directly from the row PMF surface so the public
    columns never inherit values from a renamed legacy field. ``p_over``
    is populated only when both a parseable PMF and a numeric
    ``line`` / ``market_line`` are present on the row.
    """
    if df is None or df.empty:
        return df
    df = df.copy()
    if "pmf_json" in df.columns:
        pmf_col = "pmf_json"
    elif "pmf" in df.columns:
        pmf_col = "pmf"
    else:
        pmf_col = None

    pmf_means: list[float | None] = []
    p_overs: list[float | None] = []
    market_lines: list[float | None] = []
    line_series = df.get("line")
    market_line_series = df.get("market_line")
    pmf_series = df.get(pmf_col) if pmf_col else None
    for idx in range(len(df)):
        arr = _pmf_array_from_jsonish(
            pmf_series.iloc[idx] if pmf_series is not None else None
        )
        pmf_means.append(_pmf_direct_mean(arr) if arr is not None else None)
        ml = None
        if market_line_series is not None:
            v = market_line_series.iloc[idx]
            if pd.notna(v):
                ml = float(v)
        if ml is None and line_series is not None:
            v = line_series.iloc[idx]
            if pd.notna(v):
                ml = float(v)
        market_lines.append(ml)
        if arr is not None and ml is not None:
            p_overs.append(_pmf_direct_p_over(arr, ml))
        else:
            p_overs.append(None)

    df["pmf_mean"] = pmf_means
    df["market_line"] = market_lines
    df["p_over"] = p_overs
    return df


def _write_outputs(out_dir: Path, wide_game: pd.DataFrame, market_game: pd.DataFrame) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, int] = {}

    # Stamp PMF-native public fields (pmf_mean, market_line, p_over)
    # directly from the row PMF surface and strip quarantined public
    # column names from the persisted Derek game-snapshot artifacts.
    wide_game = _drop_quarantined_columns(
        _stamp_pmf_native_public_columns(wide_game)
    )
    market_game = _drop_quarantined_columns(
        _stamp_pmf_native_public_columns(market_game)
    )

    summary_cols = [
        c for c in [
            "player_id", "player_name", "team", "opponent", "team_id", "game_id", "game",
            "is_home", "stat", "side", "line", "market_line", "book", "market_over_odds",
            "market_under_odds", "market_no_vig_over_prob",
            "pmf_mean", "p_over",
            "fair_over_odds", "fair_under_odds", "edge", "abs_edge", "role_bucket",
            "injury_freshness_status", "lineup_freshness_status", "market_coverage_status",
        ]
        if c in wide_game.columns
    ]

    prop_summary = wide_game[summary_cols].copy() if summary_cols else wide_game.copy()
    prop_summary.to_csv(out_dir / "prop_summary.csv", index=False)
    prop_summary.to_parquet(out_dir / "prop_summary.parquet", index=False)
    outputs["prop_summary"] = int(len(prop_summary))

    wide_game.to_csv(out_dir / "full_pmf_wide.csv", index=False)
    wide_game.to_parquet(out_dir / "full_pmf_wide.parquet", index=False)
    outputs["full_pmf_wide"] = int(len(wide_game))

    market_game.to_csv(out_dir / "market_comparison.csv", index=False)
    market_game.to_parquet(out_dir / "market_comparison.parquet", index=False)
    outputs["market_comparison"] = int(len(market_game))

    id_cols = [
        c for c in [
            "player_id", "player_name", "team_id", "game_id", "game", "stat", "side",
            "line", "role_bucket", "injury_freshness_status", "lineup_freshness_status",
            "market_coverage_status",
        ]
        if c in wide_game.columns
    ]

    rows = []
    pmf_col = "pmf_json" if "pmf_json" in wide_game.columns else "pmf"
    for idx, r in wide_game.reset_index(drop=True).iterrows():
        pmf = _parse_pmf(r.get(pmf_col))
        base = {c: r.get(c) for c in id_cols}
        base["source_row_id"] = int(idx)
        for k, p in sorted(pmf.items()):
            rows.append({**base, "k": int(k), "p_k": float(p)})

    outcome = pd.DataFrame(rows)
    outcome.to_csv(out_dir / "outcome_level_probabilities.csv", index=False)
    outcome.to_parquet(out_dir / "outcome_level_probabilities.parquet", index=False)
    outputs["outcome_level_probabilities"] = int(len(outcome))

    return outputs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--snapshot-type", default="close_lock")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    date = args.date
    source = REPO_ROOT / "deliveries" / date / "wizard_of_odds" / "full_pmfs_wide.parquet"
    market_path = REPO_ROOT / "deliveries" / date / "wizard_of_odds" / "market_comparison.parquet"
    root = REPO_ROOT / "deliveries" / date / "derek_game_snapshots"

    wide = pd.read_parquet(source)
    _validate_wide(wide, source)

    market = pd.read_parquet(market_path) if market_path.exists() else pd.DataFrame()

    game_ids = sorted(wide["game_id"].astype(str).unique().tolist())
    if not game_ids:
        raise SystemExit(f"FATAL: no games in PMF delivery source: {source}")

    false_no_games = root / "no_games_today.json"
    if false_no_games.exists():
        false_no_games.unlink()

    built = []
    for gid in game_ids:
        out_dir = root / str(gid) / args.snapshot_type
        if out_dir.exists() and args.force:
            shutil.rmtree(out_dir)

        wide_game = wide[wide["game_id"].astype(str) == gid].copy()
        market_game = (
            market[market["game_id"].astype(str) == gid].copy()
            if not market.empty and "game_id" in market.columns
            else pd.DataFrame()
        )

        outputs = _write_outputs(out_dir, wide_game, market_game)

        generated_at_utc = _utc_iso()

        def first_value(*cols):
            for col in cols:
                if col in wide_game.columns:
                    vals = wide_game[col].dropna()
                    if len(vals):
                        return str(vals.iloc[0])
            return None

        def bool_any(*cols) -> bool:
            for col in cols:
                if col in wide_game.columns:
                    vals = wide_game[col].dropna()
                    if len(vals):
                        return bool(vals.astype(bool).any())
            return False

        lineup_confirmed = bool_any("lineup_confirmed", "confirmed_lineup")
        lineup_source = first_value("lineup_source", "confirmed_lineup_source") or "not_wired"
        lineup_blocker = (
            None if lineup_confirmed
            else first_value("lineup_blocker", "lineup_status_reason")
            or "no confirmed lineup source in corrected delivery"
        )

        manifest = {
            "schema_version": "1.0",
            "delivery_date": date,
            "game_id": gid,
            "snapshot_type": args.snapshot_type,
            "snapshot_mode": "production_live_current" if args.snapshot_type == "current_live" else "production_live",
            "generated_at_utc": generated_at_utc,
            "snapshot_time_utc": generated_at_utc,
            "game_start_time_utc": first_value("game_start_time_utc", "start_time_utc", "commence_time"),
            "source": str(source.relative_to(REPO_ROOT)),
            "pmf_source": "corrected_wizard_of_odds_full_pmfs_wide",
            "lineup_confirmed": lineup_confirmed,
            "lineup_source": lineup_source,
            "lineup_blocker": lineup_blocker,
            "injury_source": first_value("injury_source", "availability_source") or "corrected_pmf_delivery",
            "availability_source": first_value("availability_source", "injury_source") or "corrected_pmf_delivery",
            "stats": sorted(wide_game["stat"].astype(str).unique().tolist()),
            "rows": int(len(wide_game)),
            "market_rows": int(len(market_game)),
            "outputs": outputs,
            "lineup_freshness_status": wide_game.get("lineup_freshness_status", pd.Series(dtype=str)).astype(str).value_counts().to_dict(),
            "injury_freshness_status": wide_game.get("injury_freshness_status", pd.Series(dtype=str)).astype(str).value_counts().to_dict(),
            "role_bucket": wide_game.get("role_bucket", pd.Series(dtype=str)).astype(str).value_counts().to_dict(),
        }
        (out_dir / "snapshot_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
        (out_dir / "snapshot_report.md").write_text(
            f"# Derek PMF snapshot\n\n"
            f"- date: `{date}`\n"
            f"- game_id: `{gid}`\n"
            f"- snapshot_type: `{args.snapshot_type}`\n"
            f"- source: `{manifest['source']}`\n"
            f"- rows: **{manifest['rows']}**\n"
            f"- market_rows: **{manifest['market_rows']}**\n"
            f"- stats: `{manifest['stats']}`\n",
            encoding="utf-8",
        )
        built.append({"game_id": gid, "rows": len(wide_game), "market_rows": len(market_game), "out": str(out_dir.relative_to(REPO_ROOT))})

    print("DEREK_SNAPSHOTS_FROM_CORRECTED_DELIVERY_PASS")
    print(json.dumps({"date": date, "snapshot_type": args.snapshot_type, "games": built}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
