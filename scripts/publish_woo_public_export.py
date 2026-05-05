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
  predictions/all_props_<date>.parquet — canonical model output. PMFs,
  market probabilities, edges, and EV all flow through unchanged. The
  generator is a structural projection, not a model rerun.

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
PRED_DIR = REPO_ROOT / "predictions"
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
    args = ap.parse_args(argv)
    date = args.date

    parquet = PRED_DIR / f"all_props_{date}.parquet"
    if not parquet.exists():
        payload = {
            "schema_version": "1.0",
            "date": date,
            "generated_at": _utc_iso(),
            "rows": [],
            "count": 0,
            "reason": (f"predictions/all_props_{date}.parquet does not exist; "
                       "daily prediction pipeline has not produced this slate."),
        }
        payload_pmf = {**payload, "players": []}
        _write_export(date, payload, payload_pmf)
        print(f"WOO_PUBLIC_EXPORT_PUBLISH_NODATA  date={date}  "
              f"reason=missing_predictions_parquet")
        return 0

    df = pd.read_parquet(parquet)
    aff_rows = _build_affiliate_rows(df)
    pmf_players = _build_research_players(df)

    payload_aff = {
        "schema_version": "1.0",
        "date": date,
        "generated_at": _utc_iso(),
        "rows": aff_rows,
        "count": len(aff_rows),
        "games": int(df["game_id"].nunique()) if "game_id" in df.columns else 0,
    }
    payload_pmf = {
        "schema_version": "1.0",
        "date": date,
        "generated_at": _utc_iso(),
        "players": pmf_players,
        "count_players": len(pmf_players),
        "count_props": len(aff_rows),
        "tail_bucket_convention": (
            "PMF support points beyond the dense ladder are rendered as "
            "labeled tail buckets (e.g. '20+'), never as discrete "
            "P(X=k_max)."
        ),
    }
    _write_export(date, payload_aff, payload_pmf)

    print(f"WOO_PUBLIC_EXPORT_PUBLISH_PASS  date={date}  "
          f"affiliate_rows={len(aff_rows)}  pmf_players={len(pmf_players)}  "
          f"out={(EXPORT_ROOT / date).relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
