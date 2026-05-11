#!/usr/bin/env python3
"""Phase 13AK — generate the Wizard of Odds public-export JSON contract
files (``affiliate_dashboard.json`` + ``pmf_research.json``) for one
delivery date.

Output layout (mirrors what the deployed front-end fetches):

  public_export/wizard_of_odds/<date>/affiliate_dashboard.json
  public_export/wizard_of_odds/<date>/pmf_research.json
  public_export/wizard_of_odds/latest/affiliate_dashboard.json
  public_export/wizard_of_odds/latest/pmf_research.json
  public_export/wizard_of_odds/affiliate_dashboard.json   (root copy)
  public_export/wizard_of_odds/pmf_research.json          (root copy)

Source data:
  deliveries/<date>/wizard_of_odds/full_pmfs_wide.parquet plus
  market_comparison.parquet. These are the dated Derek/WoO PMF delivery
  artifacts. The generator is a structural projection, not a model rerun.

Hard rules:
  - PMF / model / market probabilities are NOT modified.
  - Terminal survival-ladder mass (the rare tail above the dense PMF
    support) is rendered as ``"20+"`` style tail buckets in
    pmf_research.json — never as ``P(X=20)`` masquerading as a single-
    point probability. This addresses the PMF research tail-bucket bug
    explicitly called out in the production contract.
  - When the parquet is missing or empty, the generator writes honest
    no-data files with a ``reason`` field rather than a partial /
    blank export.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys  # M8.1: defensive — already imported elsewhere is fine
sys.path.insert(0, str(REPO_ROOT / "src"))  # noqa: E402

from nba_props_model.targets import (  # noqa: E402
    MISSION_REQUIRED_TARGETS_CANONICAL,
)

PRED_DIR = REPO_ROOT / "predictions"
DELIVERY_ROOT = REPO_ROOT / "deliveries"
EXPORT_ROOT = REPO_ROOT / "public_export" / "wizard_of_odds"


def _utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _coerce_float(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return f


def _parse_pmf(blob):
    if blob is None or (isinstance(blob, float) and math.isnan(blob)):
        return None
    if isinstance(blob, dict):
        raw = blob
    else:
        s = str(blob).strip()
        if not s or s in {"nan", "None"}:
            return None
        try:
            raw = json.loads(s)
        except Exception:
            try:
                raw = json.loads(s.replace("'", '"'))
            except Exception:
                return None
    out = {}
    for k, v in raw.items():
        try:
            ki = int(float(k))
            pv = float(v)
        except Exception:
            continue
        if pv < 0 or not math.isfinite(pv):
            continue
        out[ki] = out.get(ki, 0.0) + pv
    return out or None


def _build_affiliate_rows(df: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for _, r in df.iterrows():
        pid = r.get("player_id")
        stat = r.get("stat")
        line = _coerce_float(r.get("line"))
        if pid is None or stat is None or line is None:
            continue
        side = str(r.get("side", "")).upper()
        model_prob = _coerce_float(r.get("model_prob_cal")) or _coerce_float(r.get("model_prob"))
        market_prob = _coerce_float(r.get("market_prob"))
        ev = _coerce_float(r.get("ev"))
        edge = _coerce_float(r.get("raw_edge"))
        rows.append({
            "player_id": int(pid),
            "player": r.get("player_name"),
            "game": r.get("game"),
            "team_id": int(r["team_id"]) if pd.notna(r.get("team_id")) else None,
            "stat": stat,
            "side": side,
            "line": line,
            "book": r.get("bet_vendor"),
            "over_odds": _coerce_float(r.get("over_odds")),
            "under_odds": _coerce_float(r.get("under_odds")),
            "model_prob": model_prob,
            "market_prob": market_prob,
            "raw_edge": edge,
            "ev": ev,
            "edge_publish_status": r.get("edge_publish_status"),
            "calibration_support_status": r.get("calibration_support_status"),
            "lineup_confirmed": (
                bool(r.get("lineup_confirmed"))
                if "lineup_confirmed" in r.index else None
            ),
            "feature_set_id": r.get("contextual_feature_set_id"),
        })
    return rows


def _pmf_to_research_points(pmf: dict[int, float], terminal_threshold: float = 0.005) -> list[dict]:
    """Project a PMF into ``[{"k": 0, "p": 0.18, "label": "0"},
    {"k": 1, "p": ...}, ..., {"k_min": 18, "label": "18+",
    "p": <tail mass>, "is_tail": true}]``.

    Terminal tail bucket: when the cumulative probability above the
    largest "dense" support point is small (< ``terminal_threshold``)
    AND there is genuine mass above, fold it into a labeled tail
    bucket instead of emitting it as P(X=k_max). This avoids the
    front-end bug where a single-point P(X=20) was rendered as a
    discrete bar at 20 even though it represented all outcomes >= 20.
    """
    if not pmf:
        return []
    keys = sorted(pmf)
    points: list[dict] = []
    for k in keys:
        p = pmf[k]
        points.append({"k": int(k), "p": float(p), "label": str(int(k)),
                        "is_tail": False})
    # Identify a tail. We treat the LAST support point as a tail bucket
    # if the gap between it and the second-to-last support point is > 1
    # (i.e. there is no dense ladder leading up to it) AND the PMF
    # carries a non-trivial mass at that point.
    if len(keys) >= 2:
        last = keys[-1]
        second_last = keys[-2]
        gap = last - second_last
        last_mass = pmf[last]
        # Phase 13AK: ALWAYS label the last point as a tail bucket when
        # the support has a gap > 1. The previous threshold-gated logic
        # left small-mass tails unlabeled (e.g. PMF mass at k=80 with
        # P=0.001), which downstream front-ends rendered as a discrete
        # bar at 80. Tail labeling is a *schema* convention, not a
        # mass-cutoff decision.
        if gap > 1:
            points[-1] = {
                "k_min": int(last),
                "label": f"{int(last)}+",
                "p": float(last_mass),
                "is_tail": True,
            }
    return points


def _build_research_players(df: pd.DataFrame) -> list[dict]:
    players: dict[int, dict] = {}
    for _, r in df.iterrows():
        pid = r.get("player_id")
        if pid is None:
            continue
        try:
            pid_int = int(pid)
        except Exception:
            continue
        rec = players.setdefault(pid_int, {
            "player_id": pid_int,
            "player": r.get("player_name"),
            "game": r.get("game"),
            "team_id": int(r["team_id"]) if pd.notna(r.get("team_id")) else None,
            "stats": {},
        })
        stat = r.get("stat")
        if not stat:
            continue
        if stat in rec["stats"]:
            continue  # one PMF per player/stat — first row wins
        pmf = _parse_pmf(r.get("pmf"))
        if not pmf:
            continue
        s = sum(pmf.values()) or 1.0
        norm = {k: v / s for k, v in pmf.items()}
        rec["stats"][stat] = {
            "support_points": _pmf_to_research_points(norm),
            "expected_mean": float(sum(k * v for k, v in norm.items())),
            "median": _coerce_float(r.get("pmf_median") or r.get("q50")),
            "p0": float(norm.get(0, 0.0)),
        }
    out = list(players.values())
    out.sort(key=lambda p: p["player_id"])
    return out



PRODUCTION_TARGET_STATS = MISSION_REQUIRED_TARGETS_CANONICAL  # M8.1: was 5-stat literal
PRODUCTION_TARGET_STAT_SET = set(PRODUCTION_TARGET_STATS)


def _delivery_paths(date: str) -> tuple[Path, Path]:
    woo_dir = DELIVERY_ROOT / date / "wizard_of_odds"
    return woo_dir / "full_pmfs_wide.parquet", woo_dir / "market_comparison.parquet"


def _validate_delivery_wide(df: pd.DataFrame, path: Path) -> None:
    if "stat" not in df.columns:
        raise SystemExit(f"WoO full_pmfs_wide missing stat column: {path}")

    stats = set(df["stat"].astype(str).str.lower())
    extra = sorted(stats - PRODUCTION_TARGET_STAT_SET)
    missing = sorted(PRODUCTION_TARGET_STAT_SET - stats)
    if extra or missing:
        raise SystemExit(
            "FATAL: public WoO export source has wrong production stat set: "
            f"{path} expected={list(PRODUCTION_TARGET_STATS)} "
            f"missing={missing} extra={extra}"
        )

    counts = df["stat"].astype(str).str.lower().value_counts()
    if counts.empty or counts.min() != counts.max():
        raise SystemExit(
            "FATAL: public WoO export source has uneven stat coverage: "
            f"{path} counts={counts.sort_index().to_dict()}"
        )

    if "role_bucket" in df.columns:
        missing_roles = df["role_bucket"].isna() | (
            df["role_bucket"].astype(str).str.lower().isin(["", "none", "nan", "unknown"])
        )
        if bool(missing_roles.any()):
            raise SystemExit(
                "FATAL: public WoO export source has missing role_bucket rows: "
                f"{int(missing_roles.sum())}/{len(df)} in {path}"
            )


def _build_affiliate_rows_from_delivery(df: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    if df is None or df.empty:
        return rows

    df = df.copy()
    if "stat" in df.columns:
        df = df[df["stat"].astype(str).str.lower().isin(PRODUCTION_TARGET_STAT_SET)]

    for _, r in df.iterrows():
        pid = r.get("player_id")
        stat = r.get("stat")
        line = _coerce_float(r.get("line"))
        if pid is None or stat is None or line is None:
            continue

        rows.append({
            "player_id": int(pid),
            "player": r.get("player_name"),
            "game": r.get("game"),
            "team_id": int(r["team_id"]) if "team_id" in r.index and pd.notna(r.get("team_id")) else None,
            "stat": stat,
            "side": "OVER",
            "line": line,
            "book": r.get("book"),
            "over_odds": _coerce_float(r.get("market_over_odds")),
            "under_odds": _coerce_float(r.get("market_under_odds")),
            "model_prob": _coerce_float(r.get("model_p_over")),
            "market_prob": _coerce_float(r.get("market_no_vig_over_prob")),
            "raw_edge": _coerce_float(r.get("edge")),
            "ev": None,
            "edge_publish_status": r.get("edge_publish_status"),
            "calibration_support_status": r.get("calibration_support_status"),
            "lineup_confirmed": (
                r.get("lineup_freshness_status") == "confirmed"
                if "lineup_freshness_status" in r.index else None
            ),
            "feature_set_id": r.get("contextual_feature_set_id"),
        })
    return rows


def _build_research_players_from_delivery(df: pd.DataFrame) -> list[dict]:
    players: dict[int, dict] = {}
    if df is None or df.empty:
        return []

    df = df.copy()
    df = df[df["stat"].astype(str).str.lower().isin(PRODUCTION_TARGET_STAT_SET)]

    for _, r in df.iterrows():
        pid = r.get("player_id")
        if pid is None:
            continue
        try:
            pid_int = int(pid)
        except Exception:
            continue

        team = r.get("team")
        opponent = r.get("opponent")
        game = r.get("game")
        if not game and team and opponent:
            game = f"{team} vs {opponent}"

        rec = players.setdefault(pid_int, {
            "player_id": pid_int,
            "player": r.get("player_name"),
            "game": game,
            "team_id": int(r["team_id"]) if "team_id" in r.index and pd.notna(r.get("team_id")) else None,
            "stats": {},
        })

        stat = r.get("stat")
        if not stat or stat in rec["stats"]:
            continue

        pmf = _parse_pmf(r.get("pmf_json") if "pmf_json" in r.index else r.get("pmf"))
        if not pmf:
            continue

        total = sum(pmf.values()) or 1.0
        norm = {k: v / total for k, v in pmf.items()}

        rec["stats"][stat] = {
            "support_points": _pmf_to_research_points(norm),
            "expected_mean": float(sum(k * v for k, v in norm.items())),
            "median": _coerce_float(r.get("median") or r.get("pmf_median") or r.get("q50")),
            "p0": float(norm.get(0, 0.0)),
        }

    out = list(players.values())
    out.sort(key=lambda p: p["player_id"])
    return out


def _write_export(date: str, payload_aff: dict, payload_pmf: dict) -> None:
    for parent in (EXPORT_ROOT / date,
                   EXPORT_ROOT / "latest",
                   EXPORT_ROOT):
        parent.mkdir(parents=True, exist_ok=True)
        (parent / "affiliate_dashboard.json").write_text(
            json.dumps(payload_aff, indent=2, default=str), encoding="utf-8"
        )
        (parent / "pmf_research.json").write_text(
            json.dumps(payload_pmf, indent=2, default=str), encoding="utf-8"
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    ap.add_argument("--allow-empty-affiliate", action="store_true",
                    help=("allow affiliate_dashboard.json with zero rows; "
                          "default refuses because daily WoO affiliate output "
                          "must have market rows"))
    args = ap.parse_args(argv)
    date = args.date

    wide_path, market_path = _delivery_paths(date)
    if not wide_path.exists():
        payload = {
            "schema_version": "1.0",
            "date": date,
            "generated_at": _utc_iso(),
            "rows": [],
            "count": 0,
            "reason": (f"deliveries/{date}/wizard_of_odds/full_pmfs_wide.parquet "
                       "does not exist; dated Derek/WoO delivery has not been built."),
        }
        payload_pmf = {**payload, "players": []}
        _write_export(date, payload, payload_pmf)
        print(f"WOO_PUBLIC_EXPORT_PUBLISH_NODATA  date={date}  "
              f"reason=missing_delivery_full_pmfs_wide")
        return 0

    wide_df = pd.read_parquet(wide_path)
    _validate_delivery_wide(wide_df, wide_path)

    market_df = (pd.read_parquet(market_path)
                 if market_path.exists() else pd.DataFrame())

    aff_rows = _build_affiliate_rows_from_delivery(market_df)
    pmf_players = _build_research_players_from_delivery(wide_df)

    if not aff_rows and not args.allow_empty_affiliate:
        raise SystemExit(
            "FATAL: affiliate_dashboard would have zero rows. "
            "Attach a valid odds snapshot and rebuild the dated WoO delivery, "
            "or pass --allow-empty-affiliate only for explicit PMF-only emergency publication."
        )

    payload_aff = {
        "schema_version": "1.0",
        "date": date,
        "generated_at": _utc_iso(),
        "rows": aff_rows,
        "count": len(aff_rows),
        "games": int(wide_df["game_id"].nunique()) if "game_id" in wide_df.columns else 0,
        "source": str(wide_path.relative_to(REPO_ROOT)),
    }
    payload_pmf = {
        "schema_version": "1.0",
        "date": date,
        "generated_at": _utc_iso(),
        "players": pmf_players,
        "count_players": len(pmf_players),
        "count_props": len(aff_rows),
        "source": str(wide_path.relative_to(REPO_ROOT)),
        "tail_bucket_convention": (
            "PMF support points beyond the dense ladder are rendered as "
            "labeled tail buckets (e.g. '20+'), never as discrete "
            "P(X=k_max)."
        ),
    }
    _write_export(date, payload_aff, payload_pmf)

    print(f"WOO_PUBLIC_EXPORT_PUBLISH_PASS  date={date}  "
          f"affiliate_rows={len(aff_rows)}  pmf_players={len(pmf_players)}  "
          f"source={wide_path.relative_to(REPO_ROOT)}  "
          f"out={(EXPORT_ROOT / date).relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
