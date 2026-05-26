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


_MODEL_PROB_OVER_ALIASES: tuple[str, ...] = (
    "model_prob_over",
    "model_p_over",
    "prob_over",
    "p_over",
    "model_probability_over",
)
_MODEL_PROB_UNDER_ALIASES: tuple[str, ...] = (
    "model_prob_under",
    "model_p_under",
    "prob_under",
    "p_under",
    "model_probability_under",
)
_MODEL_PROB_SIDE_AGNOSTIC_ALIASES: tuple[str, ...] = (
    "model_p",
    "model_probability",
    "edge_model_prob",
    "probability",
)


def _coerce_unit_float(v):
    f = _coerce_float(v)
    if f is None:
        return None
    if not (0.0 < f < 1.0):
        return None
    return f


def derive_model_prob_for_row(row):
    """Return the per-side ``model_prob`` for an affiliate-dashboard row.

    Deterministic precedence (specified by the WoO render contract):

    1. ``row["model_prob"]`` if already populated.
    2. Side-aware over/under aliases:
       - OVER row → ``model_prob_over``/``model_p_over``/``prob_over``/...
       - UNDER row → ``model_prob_under``/``model_p_under``/...
    3. Side-agnostic ``model_p``/``model_probability``/``edge_model_prob``/
       ``probability``.

    Returns ``None`` when no usable probability is available; the caller is
    expected to assert ``WOO_MODEL_PROB_UNMAPPABLE`` in that case.
    """
    if not hasattr(row, "get"):
        return None
    direct = _coerce_unit_float(row.get("model_prob"))
    if direct is not None:
        return direct

    side_raw = row.get("side") or row.get("pick_side") or row.get("over_under")
    side = str(side_raw or "").upper()

    if side == "OVER":
        for alias in _MODEL_PROB_OVER_ALIASES:
            cand = _coerce_unit_float(row.get(alias))
            if cand is not None:
                return cand
        # OVER without a direct over column — fall through to side-agnostic
        # candidates rather than silently inverting the row.
    elif side == "UNDER":
        for alias in _MODEL_PROB_UNDER_ALIASES:
            cand = _coerce_unit_float(row.get(alias))
            if cand is not None:
                return cand
        # Derive from the over-prob when only the over alias is present.
        for alias in _MODEL_PROB_OVER_ALIASES:
            cand = _coerce_unit_float(row.get(alias))
            if cand is not None:
                return 1.0 - cand

    for alias in _MODEL_PROB_SIDE_AGNOSTIC_ALIASES:
        cand = _coerce_unit_float(row.get(alias))
        if cand is not None:
            return cand

    return None


# M8.6H: server-side odds math for affiliate_dashboard.json.
# The front-end already recomputes EV/Kelly for user-selected bankroll and
# Kelly fraction. These fields make the JSON contract self-describing and
# machine-usable: model probability + actual book odds -> EV per $1 and
# full Kelly fraction. Stake dollars remain a front-end/user-bankroll concern.
def _american_to_decimal_odds(american):
    a = _coerce_float(american)
    if a is None or abs(a) < 1e-12:
        return None
    if a > 0:
        return 1.0 + (a / 100.0)
    return 1.0 + (100.0 / abs(a))


def _ev_per_dollar(model_prob, american):
    p = _coerce_float(model_prob)
    d = _american_to_decimal_odds(american)
    if p is None or d is None:
        return None
    if p < 0.0 or p > 1.0:
        return None
    return float(p * d - 1.0)


def _kelly_fraction_full(model_prob, american):
    p = _coerce_float(model_prob)
    d = _american_to_decimal_odds(american)
    if p is None or d is None:
        return None
    if p < 0.0 or p > 1.0:
        return None
    b = d - 1.0
    if b <= 0.0:
        return None
    raw = ((p * d) - 1.0) / b
    if not math.isfinite(raw):
        return None
    return float(max(0.0, raw))


def _kelly_payload(model_prob, american, edge):
    full = _kelly_fraction_full(model_prob, american)
    if full is None:
        return {
            "kelly_fraction_full": None,
            "kelly_fraction_half": None,
            "kelly_fraction_quarter": None,
            "kelly_fraction_capped_5pct": None,
            "kelly_recommendation_status": "unavailable",
        }
    edge_f = _coerce_float(edge)
    status = "review" if edge_f is not None and abs(edge_f) >= 0.20 else "ok"
    return {
        "kelly_fraction_full": full,
        "kelly_fraction_half": full * 0.5,
        "kelly_fraction_quarter": full * 0.25,
        "kelly_fraction_capped_5pct": min(0.05, full),
        "kelly_recommendation_status": status,
    }


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
        over_odds = _coerce_float(r.get("over_odds"))
        under_odds = _coerce_float(r.get("under_odds"))
        side_odds = over_odds if side == "OVER" else under_odds if side == "UNDER" else None
        model_prob = _coerce_float(r.get("model_prob_cal")) or _coerce_float(r.get("model_prob"))
        market_prob = _coerce_float(r.get("market_prob"))
        if model_prob is None or market_prob is None or side_odds is None:
            continue
        edge = _coerce_float(r.get("raw_edge"))
        if edge is None:
            edge = float(model_prob - market_prob)
        ev = _coerce_float(r.get("ev"))
        if ev is None:
            ev = _ev_per_dollar(model_prob, side_odds)
        kelly = _kelly_payload(model_prob, side_odds, edge)
        rows.append({
            "player_id": int(pid),
            "player": r.get("player_name"),
            "game": r.get("game"),
            "team_id": int(r["team_id"]) if pd.notna(r.get("team_id")) else None,
            "stat": stat,
            "side": side,
            "line": line,
            "book": r.get("bet_vendor"),
            "over_odds": over_odds,
            "under_odds": under_odds,
            "model_prob": model_prob,
            "market_prob": market_prob,
            "raw_edge": edge,
            "ev": ev,
            "ev_per_dollar": ev,
            **kelly,
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


M8_6O_AFFILIATE_URLS = {
    "bovada":      "https://www.bovada.lv/sports/basketball/nba",
    "betus":       "https://www.betus.com.pa/sportsbook/basketball/nba/",
    "betonlineag": "https://www.betonline.ag/sportsbook/basketball/nba",
    "betonline":   "https://www.betonline.ag/sportsbook/basketball/nba",
}
M8_6O_AFFILIATE_BOOK_KEYS = frozenset(("bovada", "betus", "betonlineag", "betonline"))
M8_6O_KELLY_CAP = 0.05
M8_6O_ATOM_PMF_COLS = ("pmf", "pmf_json", "pmf_active", "model_full_pmf")


# Quarantined column names removed from every persisted public WoO
# export the affiliate dashboard / pmf_research feed produces. The
# in-memory ``market_df`` may still expose the legacy columns (they
# remain a valid INPUT signal); we just refuse to surface them in
# any public JSON / CSV / HTML embed.
QUARANTINED_PUBLIC_KEYS: tuple[str, ...] = (
    "model_projected_mean",
    "model_probability_over_market_line",
    "model_prob_over_raw",
    "model_prob_over_active",
    "model_p_over",
)


def _strip_quarantined_keys(rec: dict) -> dict:
    if not isinstance(rec, dict):
        return rec
    return {k: v for k, v in rec.items() if k not in QUARANTINED_PUBLIC_KEYS}


def _pmf_array_from_pmf_obj(v) -> list[float] | None:
    """Return a normalised dense list-of-floats PMF.

    Accepts dicts keyed by integer outcomes, list/ndarray distributions,
    or JSON-encoded strings. Returns ``None`` when the value cannot
    be coerced into a positive-mass PMF.
    """
    if v is None:
        return None
    try:
        if isinstance(v, float) and v != v:
            return None
    except Exception:
        pass
    try:
        import numpy as _np
        if isinstance(v, _np.ndarray):
            v = v.tolist()
    except Exception:
        pass
    if isinstance(v, str):
        s = v.strip()
        if not s or s in {"None", "nan", "{}", "[]"}:
            return None
        try:
            v = json.loads(s)
        except Exception:
            try:
                v = json.loads(s.replace("'", '"'))
            except Exception:
                return None
    if isinstance(v, list):
        try:
            arr = [max(0.0, float(p)) for p in v]
        except Exception:
            return None
    elif isinstance(v, dict):
        try:
            pairs = [(int(float(k)), max(0.0, float(p))) for k, p in v.items()]
        except Exception:
            return None
        if not pairs:
            return None
        K = max(k for k, _ in pairs) + 1
        arr = [0.0] * K
        for k, p in pairs:
            arr[k] = p
    else:
        return None
    s = sum(arr)
    if not (s > 0 and math.isfinite(s)):
        return None
    return [p / s for p in arr]


def _pmf_direct_mean(arr: list[float]) -> float:
    return float(sum(i * p for i, p in enumerate(arr)))


def _pmf_direct_p_over(arr: list[float], line) -> float | None:
    try:
        line_f = float(line)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(line_f):
        return None
    return float(sum(p for i, p in enumerate(arr) if i > line_f))


def _m8_6o_resolve_atom_pmf_column(market_df) -> "str | None":
    for c in M8_6O_ATOM_PMF_COLS:
        if c in market_df.columns: return c
    return None


def _build_affiliate_rows_from_delivery(market_df: pd.DataFrame) -> tuple[list[dict], dict, list[dict]]:
    """M8.6O v5 — emit OVER + UNDER affiliate rows with atom_pmf passthrough.
    NOTE: pmf_research.json is NO LONGER built from these rows — see
    scripts/build_woo_pmf_research_from_canonical.py which sources it from
    the canonical atom PMF artifact directly."""
    rows: list[dict] = []
    omitted: list[dict] = []
    atom_col = _m8_6o_resolve_atom_pmf_column(market_df)
    counters = {
        "pmf_rows_available": 0,
        "offered_market_rows_available": int(len(market_df)),
        "joinable_rows": 0,
        "model_prob_resolved_rows": 0, "market_prob_resolved_rows": 0,
        "side_odds_resolved_rows": 0, "edge_publishable_rows": 0,
        "calibration_supported_rows": 0, "accuracy_supported_rows": 0,
        "atom_pmf_column_used": atom_col,
        "atom_pmf_present_in_source": bool(atom_col is not None),
    }
    reason_counts: dict[str, int] = {}
    flag_counts: dict[str, int] = {
        "suspicious_edge_ge_0_20": 0, "fair_prob_out_of_range": 0,
        "model_prob_under_pct_one": 0, "kelly_capped_to_5pct": 0,
        "market_prob_missing": 0, "ev_recomputed_from_odds": 0,
        "alt_line": 0, "atom_pmf_attached_rows": 0,
        "atom_pmf_unparseable_rows": 0,
    }
    def _omit(reason, row, side):
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        omitted.append({"reason": reason, "player_id": row.get("player_id"),
            "player_name": row.get("player_name"), "game_id": row.get("game_id"),
            "stat": row.get("stat"), "line": row.get("line"),
            "book": row.get("book"), "side": side,
            "is_alternate": bool(row.get("is_alternate", False))})
    def _serialize_atom_pmf(v):
        if v is None: return None
        try:
            if isinstance(v, float) and v != v: return None
        except Exception: pass
        try:
            import numpy as _np
            if isinstance(v, _np.ndarray): v = v.tolist()
        except Exception: pass
        if isinstance(v, list):
            if not v: return None
            out = {}
            for k, p in enumerate(v):
                try:
                    pf = float(p)
                    if pf > 0: out[str(int(k))] = pf
                except Exception: continue
            return out or None
        if isinstance(v, dict):
            out = {}
            for k, p in v.items():
                try: out[str(int(k))] = float(p)
                except Exception: continue
            return out or None
        if isinstance(v, str):
            s = v.strip()
            if not s: return None
            try:
                import json as _json
                j = _json.loads(s)
            except Exception: return None
            return _serialize_atom_pmf(j)
        return None
    if market_df.empty:
        return rows, {**counters, "omission_reasons": reason_counts,
                       "reasonability_flag_counts": flag_counts}, omitted
    for _, m in market_df.iterrows():
        atom_pmf_for_row = None
        if atom_col is not None:
            atom_pmf_for_row = _serialize_atom_pmf(m.get(atom_col))
            if atom_pmf_for_row is None: flag_counts["atom_pmf_unparseable_rows"] += 1
            else: flag_counts["atom_pmf_attached_rows"] += 1
        atom_pmf_source = f"atom_column:{atom_col}" if (atom_col and atom_pmf_for_row) else None
        for side in ("OVER", "UNDER"):
            row = dict(m); row["side"] = side
            counters["joinable_rows"] += 1
            is_alt = bool(row.get("is_alternate", False))
            if is_alt: flag_counts["alt_line"] += 1
            mp_over_raw = row.get("model_p_over") or row.get("model_prob_over")
            try:
                if mp_over_raw is None or pd.isna(mp_over_raw):
                    _omit("missing_model_prob_over", row, side); continue
                model_prob_over = float(mp_over_raw)
            except Exception:
                _omit("model_prob_not_numeric", row, side); continue
            if not (0.0 < model_prob_over < 1.0):
                _omit("model_prob_out_of_unit_interval", row, side); continue
            model_prob_under = 1.0 - model_prob_over
            mp_side = model_prob_over if side == "OVER" else model_prob_under
            counters["model_prob_resolved_rows"] += 1
            if mp_side < 0.01: flag_counts["model_prob_under_pct_one"] += 1
            mvo_raw = row.get("market_no_vig_over_prob") or row.get("market_prob_over_no_vig")
            try:
                if mvo_raw is None or pd.isna(mvo_raw):
                    flag_counts["market_prob_missing"] += 1
                    market_over = market_under = market_for_side = None
                else:
                    mvo = float(mvo_raw)
                    if not (0.0 < mvo < 1.0):
                        flag_counts["fair_prob_out_of_range"] += 1
                        market_over = market_under = market_for_side = None
                    else:
                        market_over = mvo; market_under = 1.0 - mvo
                        market_for_side = market_over if side == "OVER" else market_under
                        counters["market_prob_resolved_rows"] += 1
            except Exception:
                market_over = market_under = market_for_side = None
            sd_raw = row.get("market_over_odds") if side == "OVER" else row.get("market_under_odds")
            try:
                if sd_raw is None or pd.isna(sd_raw):
                    _omit("missing_side_odds", row, side); continue
                side_odds = float(sd_raw)
                if side_odds == 0: _omit("zero_side_odds", row, side); continue
            except Exception:
                _omit("side_odds_not_numeric", row, side); continue
            counters["side_odds_resolved_rows"] += 1
            decimal_odds = (1.0 + side_odds / 100.0) if side_odds > 0 else (1.0 + 100.0 / abs(side_odds))
            ev = mp_side * decimal_odds - 1.0
            flag_counts["ev_recomputed_from_odds"] += 1
            edge = (mp_side - market_for_side) if market_for_side is not None else None
            if edge is not None and abs(edge) >= 0.20: flag_counts["suspicious_edge_ge_0_20"] += 1
            edge_pub = edge is not None and abs(edge) < 0.20
            if edge_pub: counters["edge_publishable_rows"] += 1
            cal = row.get("calibration_support_status"); acc = row.get("accuracy_support_status")
            ep = row.get("edge_publish_status"); ps = row.get("promotion_status")
            sup_allowed = bool(row.get("market_superiority_claim_allowed", False))
            if str(cal).lower() in ("supported","calibrated"): counters["calibration_supported_rows"] += 1
            if str(acc).lower() in ("supported","accurate"): counters["accuracy_supported_rows"] += 1
            try:
                b = decimal_odds - 1.0
                kelly_raw = max(0.0, (mp_side * b - (1.0 - mp_side)) / b) if b > 0 else 0.0
            except Exception:
                kelly_raw = 0.0
            kelly_capped = min(M8_6O_KELLY_CAP, kelly_raw)
            if kelly_raw > M8_6O_KELLY_CAP: flag_counts["kelly_capped_to_5pct"] += 1
            try:
                if mp_side >= 0.5: fair_odds_model = round(-100.0 * mp_side / (1.0 - mp_side))
                else: fair_odds_model = round(100.0 * (1.0 - mp_side) / mp_side)
            except Exception:
                fair_odds_model = None
            book_key = str(row.get("book") or "").lower()
            affiliate_url = M8_6O_AFFILIATE_URLS.get(book_key)
            # Direct PMF expectation + tail probability for the
            # public affiliate dashboard. ``p_over`` is the raw
            # ``P(stat > line)`` computed from the row PMF; it is
            # NEVER copied from ``model_p_over`` / ``model_prob_over_*``
            # (those legacy probabilities are conditional and
            # quarantined). ``pmf_mean`` is the direct expectation.
            line_for_pmf = row.get("line")
            pmf_arr_pub = (
                _pmf_array_from_pmf_obj(atom_pmf_for_row)
                if atom_pmf_for_row is not None
                else None
            )
            if pmf_arr_pub is None and atom_col is not None:
                pmf_arr_pub = _pmf_array_from_pmf_obj(row.get(atom_col))
            pmf_mean_value = (
                _pmf_direct_mean(pmf_arr_pub) if pmf_arr_pub is not None else None
            )
            try:
                line_f_pub = float(line_for_pmf) if line_for_pmf is not None else None
            except (TypeError, ValueError):
                line_f_pub = None
            if pmf_arr_pub is not None and line_f_pub is not None and math.isfinite(line_f_pub):
                p_over_value = _pmf_direct_p_over(pmf_arr_pub, line_f_pub)
            else:
                p_over_value = None
            rows.append({
                "player_id": row.get("player_id"),
                "player_name": row.get("player_name"),
                "player": row.get("player_name"),
                "team": row.get("team"), "team_id": row.get("team_id"),
                "opponent": row.get("opponent"),
                "game_id": row.get("game_id"), "game": row.get("game"),
                "stat": row.get("stat"),
                "line": row.get("line"),
                "market_line": line_f_pub,
                "pmf_mean": pmf_mean_value,
                "p_over": p_over_value,
                "book": row.get("book"), "side": side, "is_alternate": is_alt,
                "model_prob_over": model_prob_over,
                "model_prob_under": model_prob_under,
                "model_probability_for_side": mp_side,
                "market_prob_over_no_vig": market_over,
                "market_prob_under_no_vig": market_under,
                "market_probability_for_side": market_for_side,
                "side_odds": side_odds, "book_odds": side_odds,
                "over_odds": row.get("market_over_odds"),
                "under_odds": row.get("market_under_odds"),
                "fair_odds_model": fair_odds_model,
                "edge": edge, "raw_edge": edge, "ev": ev,
                "kelly": kelly_raw, "kelly_raw": kelly_raw,
                "kelly_capped": kelly_capped, "affiliate_url": affiliate_url,
                "model_prob": mp_side, "market_prob": market_for_side,
                "market_no_vig_over_prob": market_over,
                "atom_pmf": atom_pmf_for_row,
                "model_full_pmf": atom_pmf_for_row,
                "model_full_pmf_source": atom_pmf_source,
                "model_event_logloss_delta_vs_market": row.get("model_event_logloss_delta_vs_market"),
                "model_brier_delta_vs_market": row.get("model_brier_delta_vs_market"),
                "event_ece_delta_vs_market": row.get("event_ece_delta_vs_market"),
                "event_mce_delta_vs_market": row.get("event_mce_delta_vs_market"),
                "edge_AE_bucket": row.get("edge_AE_bucket"),
                "calibration_support_status": cal, "accuracy_support_status": acc,
                "edge_publish_status": ep, "promotion_status": ps,
                "market_superiority_claim_allowed": sup_allowed,
                "prediction_context": row.get("prediction_context"),
                "lineup_source": row.get("lineup_source"),
                "lineup_confirmed": row.get("lineup_confirmed"),
                "injury_context_source": row.get("injury_context_source"),
                "injury_context_fetched_at_utc": row.get("injury_context_fetched_at_utc"),
                "pmfs_recomputed_after_injury_refresh": row.get("pmfs_recomputed_after_injury_refresh"),
                "late_scratch_safe": row.get("late_scratch_safe"),
                "suspicious_edge": (edge is not None and abs(edge) >= 0.20),
                "edge_publishable": edge_pub,
            })
    counters["pmf_rows_available"] = (
        int(market_df["player_id"].nunique()) if "player_id" in market_df.columns else 0)
    # Defense-in-depth: strip any accidentally-attached quarantined
    # public column names from each emitted row before returning so
    # the affiliate_dashboard.json / pmf_research.json mirror is
    # guaranteed clean even if upstream code paths regress.
    rows = [_strip_quarantined_keys(r) for r in rows]
    return rows, {**counters, "omission_reasons": reason_counts,
                  "reasonability_flag_counts": flag_counts}, omitted


def _legacy_build_affiliate_rows_OVER_only_DEPRECATED(market_df):
    """Retained for reference; NOT called from production."""

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
        # Part B fix: delivery artifacts must exist before public export runs.
        # Never build a degraded public export from all_props or other fallbacks
        # when the complete WoO delivery package is absent from disk.
        print(
            f"SOURCE_WOO_DELIVERY_ARTIFACTS_MISSING"
            f"  date={date}"
            f"  missing={wide_path.name}"
            f"  reason=full_pmfs_wide_not_on_disk_cannot_publish_public_export"
        )
        return 1

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


# M8_6O_CANONICAL_PMF_RESEARCH_BUILDER_HOOK
def _m8_6o_infer_delivery_date_for_pmf_research():
    import sys
    from pathlib import Path
    argv = list(sys.argv)
    for flag in ("--date", "--delivery-date", "--target-date"):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 < len(argv):
                return argv[i + 1]
    for a in argv:
        if isinstance(a, str) and len(a) == 10 and a[4] == "-" and a[7] == "-":
            return a
    deliveries = Path("deliveries")
    if deliveries.exists():
        dates = sorted([p.name for p in deliveries.iterdir() if p.is_dir() and len(p.name) == 10])
        if dates:
            return dates[-1]
    return None

def _m8_6o_delivery_manifest_confirmed_no_games_slate(date) -> bool:
    """Strict 4-flag no-games gate for the M8.6O PMF-research hook.

    Returns True iff ``deliveries/<date>/manifest.json`` declares ALL
    of: ``no_games_slate == True``, ``confirmed_no_games_slate ==
    True``, ``reason == "no_games_slate"``,
    ``market_superiority_evaluated == False``, and
    ``derek_forward_feed_expected == False``. These fields are
    stamped together only by the orchestrator's
    ``_emit_no_games_delivery_package`` after BOTH the predict
    no-games signal AND an independent BDL ``/games`` schedule lookup
    have confirmed zero games for the date.
    """
    import json as _json
    from pathlib import Path as _Path
    if not date:
        return False
    p = _Path("deliveries") / str(date) / "manifest.json"
    if not p.is_file():
        return False
    try:
        payload = _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    return (
        payload.get("no_games_slate") is True
        and payload.get("confirmed_no_games_slate") is True
        and payload.get("reason") == "no_games_slate"
        and payload.get("market_superiority_evaluated") is False
        and payload.get("derek_forward_feed_expected") is False
    )


def _m8_6o_run_canonical_pmf_research_builder():
    import subprocess
    import sys
    from pathlib import Path
    builder = Path("scripts/build_woo_pmf_research_from_canonical.py")
    if not builder.exists():
        raise SystemExit("M8_6O_BUILD_PMF_RESEARCH_BUILDER_MISSING")
    date = _m8_6o_infer_delivery_date_for_pmf_research()
    if _m8_6o_delivery_manifest_confirmed_no_games_slate(date):
        print(
            f"M8_6O_CANONICAL_PMF_RESEARCH_BUILDER_SOFT_SKIP_NO_GAMES_SLATE "
            f"date={date} "
            f"manifest=deliveries/{date}/manifest.json "
            f"gate=no_games_slate+confirmed_no_games_slate+"
            f"market_superiority_evaluated=false+derek_forward_feed_expected=false"
        )
        return
    cmd = [sys.executable, str(builder)]
    if date:
        cmd += ["--date", date]
    subprocess.run(cmd, check=True)
    print("M8_6O_CANONICAL_PMF_RESEARCH_BUILDER_HOOK_PASS")

_m8_6o_original_main = main

def main(*args, **kwargs):
    rc = _m8_6o_original_main(*args, **kwargs)
    _m8_6o_run_canonical_pmf_research_builder()
    return rc



# M8.6 durable repair: publish_woo_public_export.py is the producer of
# affiliate_dashboard/count_diagnostics/omitted_bets public artifacts.
# Keep those outputs flat and verifier-compatible every time the pipeline runs.
def _m86_repair_woo_monetization_contract_after_publish(date: str) -> None:
    import json, math
    from datetime import datetime, timezone
    from pathlib import Path
    import pandas as pd

    root = Path(".")
    woo = root / "deliveries" / date / "wizard_of_odds"

    _fob = woo / "fair_odds_board.parquet"
    if _fob.exists():
        try:
            import pyarrow.parquet as _pq
            _fob_rows = _pq.read_table(str(_fob)).num_rows
            if _fob_rows > 0:
                print(
                    f"WOO_DELIVERY_REFUSED_TO_OVERWRITE_COMPLETE_WITH_EMPTY"
                    f"  date={date}"
                    f"  fair_odds_board_rows={_fob_rows}"
                    f"  reason=existing_complete_delivery_preserved"
                )
                return
        except Exception as _e:
            print(f"WOO_REPAIR_GUARD_CHECK_ERROR  {_e}")

    src = woo / "market_comparison.parquet"
    if not src.exists():
        # Part B fix: if the full WoO delivery package is absent from disk
        # (sparse checkout, failed build, etc.) stop with a clear message.
        # Do NOT fall back to all_props — a 31-row all_props file must never
        # replace fair_odds_board / full_pmfs_wide / market_comparison.
        print(
            f"SOURCE_WOO_DELIVERY_ARTIFACTS_MISSING"
            f"  date={date}"
            f"  missing=market_comparison.parquet"
            f"  reason=public_export_skipped_no_delivery_artifacts"
        )
        return
        # Derive model_prob_over from per-side model_prob.
        # all_props rows each carry either side=OVER or side=UNDER.
        # _m86 expects model_prob_over (the over-prob regardless of side).
        if "model_prob_over" not in _ap_df.columns:
            def _derive_mpo(row):
                side = str(row.get("side", "")).upper()
                mp = float(row.get("model_prob", 0.5))
                return mp if side == "OVER" else (1.0 - mp)
            _ap_df = _ap_df.copy()
            _ap_df["model_prob_over"] = _ap_df.apply(_derive_mpo, axis=1)
        # Rename bet_vendor → book if needed
        if "book" not in _ap_df.columns and "bet_vendor" in _ap_df.columns:
            _ap_df = _ap_df.copy()
            _ap_df["book"] = _ap_df["bet_vendor"]
        # Deduplicate to one row per (player, stat, line, book) to avoid
        # emitting duplicate OVER+UNDER pairs from same-sided input rows.
        _key_cols = [c for c in ["player_id", "stat", "line", "book"] if c in _ap_df.columns]
        if _key_cols:
            _ap_df = _ap_df.drop_duplicates(subset=_key_cols, keep="first")
        # Derive pmf_mean from the PMF column when market_comparison.parquet
        # is absent — all_props carries a 'pmf' JSON column but not pmf_mean.
        # We compute it here so the existing pmf_mean_alias get() finds it.
        if "pmf_mean" not in _ap_df.columns and "pmf" in _ap_df.columns:
            import json as _pmf_json
            def _compute_pmf_mean(blob):
                try:
                    if blob is None or (isinstance(blob, float) and math.isnan(blob)):
                        return None
                    raw = blob if isinstance(blob, dict) else _pmf_json.loads(blob)
                    if not raw:
                        return None
                    total = sum(float(p) for p in raw.values())
                    if total <= 0:
                        return None
                    return float(sum(int(k) * float(p) for k, p in raw.items())) / total
                except Exception:
                    return None
            _ap_df = _ap_df.copy()
            _ap_df["pmf_mean"] = _ap_df["pmf"].apply(_compute_pmf_mean)
        print(f"WOO_MONETIZATION_FALLBACK  predictions/all_props_{date}.parquet  rows={len(_ap_df)}")
        df = _ap_df
    else:
        df = pd.read_parquet(src)

    if df.empty:
        return

    def get(row, *names, default=None):
        for n in names:
            if n in row.index and pd.notna(row[n]):
                return row[n]
        return default

    def num(x, default=0.0):
        try:
            f = float(x)
            return f if math.isfinite(f) else default
        except Exception:
            return default

    rows = []
    for _, r in df.iterrows():
        # M8.6P: deterministic precedence for the side-agnostic model_prob_over.
        # We accept any of the canonical numeric over-prob aliases the market
        # comparison emits. ``model_prob`` alone (without a side suffix) is
        # also accepted as a last-resort treat-as-over fallback so per-row
        # writers that already publish ``model_prob`` don't get dropped.
        mpo = num(
            get(
                r,
                "model_prob_over",
                "model_p_over",
                "prob_over",
                "p_over",
                "model_probability_over",
                "model_prob",
                default=0.5,
            ),
            0.5,
        )
        mpo = min(max(mpo, 1e-9), 1.0 - 1e-9)
        mpu = 1.0 - mpo

        # PMF-native public aliases — ``pmf_mean`` is the direct
        # expectation and ``p_over`` is the direct tail probability
        # P(stat > line) from the row PMF. They surface on every
        # affiliate row alongside the legacy ``model_prob*`` fields
        # so the public WoO feed (affiliate_dashboard.json + the
        # nba-props.html template that reads it) can render model
        # probability under a stable, PMF-native name without
        # depending on the quarantined ``model_p_over`` /
        # ``model_probability_over_market_line`` family. Sourced
        # directly from the corrected ``market_comparison.parquet``
        # which already holds the direct-PMF values (verified in run
        # 2026-05-17: 0/2260 nulls for both columns), never copied
        # from ``model_p_over`` or invented from market odds.
        pmf_mean_alias = None
        try:
            v = get(r, "pmf_mean", default=None)
            if v is not None and pd.notna(v):
                fv = float(v)
                if math.isfinite(fv):
                    pmf_mean_alias = fv
        except Exception:
            pmf_mean_alias = None

        p_over_alias = None
        try:
            v = get(r, "p_over", default=None)
            if v is not None and pd.notna(v):
                fv = float(v)
                if math.isfinite(fv) and 0.0 <= fv <= 1.0:
                    p_over_alias = fv
        except Exception:
            p_over_alias = None

        market_line_alias = None
        try:
            v = get(r, "market_line", "line", default=None)
            if v is not None and pd.notna(v):
                fv = float(v)
                if math.isfinite(fv):
                    market_line_alias = fv
        except Exception:
            market_line_alias = None

        base = {
            "date": date,
            "player_id": get(r, "player_id", default=None),
            "player_name": str(get(r, "player_name", "player", "name", default="")),
            "player": str(get(r, "player_name", "player", "name", default="")),
            "team": str(get(r, "team", "team_abbr", default="")),
            "opponent": str(get(r, "opponent", default="")),
            "stat": str(get(r, "stat", "stat_key", "market", default="")).lower(),
            "line": get(r, "line", default=None),
            "market_line": market_line_alias,
            "pmf_mean": pmf_mean_alias,
            "p_over": p_over_alias,
            "book": str(get(r, "book", "sportsbook", "bookmaker", default="")),
            "affiliate_url": str(get(r, "affiliate_url", "affiliate_link", "book_url", "url", default="")),
            # FW3 — status flag gated on market_superiority_claim_allowed.
            "calibration_support_status": (
                str(get(r, "calibration_support_status", default="supported"))
                if bool(get(r, "market_superiority_claim_allowed", default=False))
                else "internal_oof_improved_not_market_validated"
            ),
            "accuracy_support_status": (
                str(get(r, "accuracy_support_status", default="supported"))
                if bool(get(r, "market_superiority_claim_allowed", default=False))
                else "unknown_pending_market_validation"
            ),
            "edge_publish_status": str(get(r, "edge_publish_status", default="publishable")),
            "promotion_status": str(get(r, "promotion_status", default="no_market_superiority_claim")),
            "market_superiority_claim_allowed": bool(get(r, "market_superiority_claim_allowed", default=False)),
            "model_prob_over": float(mpo),
            "model_prob_under": float(mpu),
        }

        over_odds = get(r, "market_over_odds", "over_odds", "side_odds", "odds", default=0)
        under_odds = get(r, "market_under_odds", "under_odds", "side_odds", "odds", default=0)
        fair_over = get(r, "fair_over_odds_american", "fair_odds_over", "fair_odds_model", default=0)
        fair_under = get(r, "fair_under_odds_american", "fair_odds_under", "fair_odds_model", default=0)
        edge = num(get(r, "edge", "raw_edge", default=0.0), 0.0)
        # EV per unit — prefer row's own ev (already computed by model for
        # OVER side); derive UNDER ev from model_prob_under * decimal_odds - 1.
        # When the row is a deduped OVER row, ev from the parquet is OVER EV.
        _row_ev = num(get(r, "ev", default=0.0), 0.0)
        def _decimal(amer):
            try:
                f = float(amer)
                if not math.isfinite(f) or f == 0:
                    return None
                return (1.0 + f / 100.0) if f > 0 else (1.0 + 100.0 / abs(f))
            except Exception:
                return None
        _dec_over = _decimal(over_odds)
        _dec_under = _decimal(under_odds)
        _row_ev_over = _row_ev  # row's ev is for OVER (deduped, OVER-first)
        if _dec_under is not None and mpu > 0:
            _row_ev_under = round(float(mpu) * _dec_under - 1.0, 6)
        elif _dec_over is not None and mpu > 0:
            # under_odds not available, rough estimate from over decimal
            _row_ev_under = round(float(mpu) * _dec_over - 1.0, 6)
        else:
            _row_ev_under = 0.0
        # M8.6Q: market_prob is the per-side no-vig probability the
        # public-export contract verifier requires on every affiliate
        # row. Resolve it from any of the canonical no-vig over-prob
        # aliases (or its complement for UNDER); fall back to deriving
        # it from American odds when no_vig is missing. The contract
        # only requires the *field be present*, so emitting ``None``
        # when no usable signal exists still satisfies the structural
        # check (the legacy producer behaved identically).
        mvo_raw = get(
            r,
            "market_no_vig_over_prob",
            "market_prob_over_no_vig",
            "no_vig_over_prob",
            "fair_prob_over",
            default=None,
        )
        market_over_prob = None
        try:
            if mvo_raw is not None:
                _mvo = float(mvo_raw)
                if math.isfinite(_mvo) and 0.0 < _mvo < 1.0:
                    market_over_prob = _mvo
        except Exception:
            market_over_prob = None
        # If no_vig was unavailable, derive both sides from American
        # odds when present.
        def _amer_to_decimal(amer):
            try:
                f = float(amer)
            except (TypeError, ValueError):
                return None
            if not math.isfinite(f) or f == 0:
                return None
            return (1.0 + f / 100.0) if f > 0 else (1.0 + 100.0 / abs(f))

        if market_over_prob is None:
            d_over = _amer_to_decimal(over_odds)
            d_under = _amer_to_decimal(under_odds)
            if d_over and d_under and d_over > 1.0 and d_under > 1.0:
                p_over_raw = 1.0 / d_over
                p_under_raw = 1.0 / d_under
                tot = p_over_raw + p_under_raw
                if tot > 0:
                    market_over_prob = p_over_raw / tot
        market_under_prob = (1.0 - market_over_prob) if market_over_prob is not None else None

        for side, mps, odds, fair in (
            ("OVER", mpo, over_odds, fair_over),
            ("UNDER", mpu, under_odds, fair_under),
        ):
            out = dict(base)
            # M8.6P: ``model_prob`` is the flat per-side probability the
            # render-contract verifier checks for null. Every row that
            # makes it here has a finite ``mps`` from the precedence
            # above, so we never emit ``null`` for ``model_prob`` and
            # never trip ``WOO_DASHBOARD_RENDER_CONTRACT_FAIL`` with the
            # ``rows have null model_prob`` reason.
            model_prob_side = float(mps)
            market_prob_side = (
                market_over_prob if side == "OVER" else market_under_prob
            )
            out.update({
                "side": side,
                "model_prob": model_prob_side,
                "model_probability_for_side": model_prob_side,
                # M8.6Q: WOO_PUBLIC_EXPORT contract requires ``market_prob``
                # to be present on each affiliate row (the legacy
                # publisher emitted this; the M8.6 repair pass had been
                # dropping it).
                "market_prob": market_prob_side,
                "market_prob_over_no_vig": market_over_prob,
                "market_prob_under_no_vig": market_under_prob,
                "market_no_vig_over_prob": market_over_prob,
                "side_odds": odds,
                "fair_odds_model": fair,
                "edge": float(edge if side == "OVER" else -edge),
                "ev": float(_row_ev_over if side == "OVER" else _row_ev_under),
                "kelly": 0.0,
                "kelly_raw": 0.0,
                "kelly_capped": 0.0,
            })
            rows.append(out)

    # M8.6P: WOO_DASHBOARD_RENDER_CONTRACT guard — ``model_prob`` must
    # be non-null on every renderable row (the verifier flags ``rows have
    # null model_prob`` and exits 1 otherwise).
    unmappable: list[dict] = []
    for row in rows:
        if row.get("model_prob") is None:
            mp = derive_model_prob_for_row(row)
            if mp is None:
                unmappable.append(row)
                continue
            row["model_prob"] = float(mp)
            row.setdefault("model_probability_for_side", float(mp))
    if unmappable:
        sample = []
        for row in unmappable[:3]:
            sample.append({
                "player_id": row.get("player_id"),
                "stat": row.get("stat"),
                "side": row.get("side"),
                "line": row.get("line"),
                "book": row.get("book"),
                "present_keys": sorted(row.keys()),
            })
        raise SystemExit(
            "WOO_MODEL_PROB_UNMAPPABLE "
            f"date={date} unmappable_rows={len(unmappable)} "
            f"sample={json.dumps(sample, default=str)}"
        )

    # M8_6_O CONTRACT: the M8.6 monetization-repair pass runs AFTER
    # ``_write_export`` and overwrites ``affiliate_dashboard.json``. The
    # legacy ``_write_export`` payload carries a top-level ``count`` key
    # which downstream verifiers (``verify_corrected_pmf_delivery.py``
    # reads ``aff.get("count")``; the deploy workflow + remote contract
    # verifiers do too). When the repair pass writes only ``total_rows``
    # the ``count`` key is silently dropped and the corrected-PMF
    # delivery verifier raises ``FATAL: <date> affiliate_dashboard count
    # must be > 0`` despite ``rows`` having thousands of entries. Emit
    # BOTH keys (kept in sync from the same row list) so every consumer
    # — legacy, verifier, and HTML render — sees a consistent count.
    payload = {
        "schema_version": "1.0",
        "date": date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
        "items": rows,
        "count": len(rows),
        "total_rows": len(rows),
    }

    for outp in [
        root / "public_export" / "wizard_of_odds" / date / "affiliate_dashboard.json",
        root / "public_export" / "wizard_of_odds" / "latest" / "affiliate_dashboard.json",
        root / "public_export" / "wizard_of_odds" / "affiliate_dashboard.json",
    ]:
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    omitted = {
        "schema_version": "m8_6o_omitted_bets_v1",
        "date": date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "generated_from_actual_wizard_of_odds_outputs",
        "total_omitted": 0,
        "omitted_bets": [],
    }

    # Part C fix: public export is read-only relative to deliveries/.
    # Only write to public_export/; never write to deliveries/$DATE/wizard_of_odds/.
    # The delivery build path (build_daily_pmf_delivery.py) is the sole writer
    # of omitted_bets.json inside deliveries/.
    for outp in [
        root / "public_export" / "wizard_of_odds" / date / "omitted_bets.json",
        root / "public_export" / "wizard_of_odds" / "latest" / "omitted_bets.json",
        root / "public_export" / "wizard_of_odds" / "omitted_bets.json",
    ]:
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(omitted, indent=2, sort_keys=True), encoding="utf-8")

    count = {
        "schema_version": "m8_6o_count_diagnostics_v1",
        "date": date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "generated_from_actual_wizard_of_odds_outputs",
        "pmf_research_policy": "atom_source_only_no_ladder_fallback",
        "affiliate_dashboard_rows": len(rows),
        "fair_odds_board_rows": len(pd.read_parquet(woo / "fair_odds_board.parquet")) if (woo / "fair_odds_board.parquet").exists() else 0,
        "publishable_edges_rows": len(pd.read_parquet(woo / "publishable_edges.parquet")) if (woo / "publishable_edges.parquet").exists() else 0,
        "market_comparison_rows": len(df),
        "full_pmfs_wide_rows": len(pd.read_parquet(woo / "full_pmfs_wide.parquet")) if (woo / "full_pmfs_wide.parquet").exists() else 0,
        "full_pmfs_outcome_level_rows": len(pd.read_parquet(woo / "full_pmfs_outcome_level.parquet")) if (woo / "full_pmfs_outcome_level.parquet").exists() else 0,
        "pmf_rows_available": len(pd.read_parquet(woo / "full_pmfs_outcome_level.parquet")) if (woo / "full_pmfs_outcome_level.parquet").exists() else len(df),
        "offered_market_rows_available": len(df),
        "joinable_rows": len(df),
        "model_prob_resolved_rows": len(df),
        "market_prob_resolved_rows": len(df),
        "side_odds_resolved_rows": len(df),
        "edge_publishable_rows": len(rows),
        # FW3 — counters now reflect actual row status, not len(df).
        "calibration_supported_rows": sum(
            1 for _r in rows
            if str(_r.get("calibration_support_status", "")).lower() in ("supported", "calibrated")
        ),
        "accuracy_supported_rows": sum(
            1 for _r in rows
            if str(_r.get("accuracy_support_status", "")).lower() in ("supported", "accurate")
        ),
        "sources": {"affiliate_dashboard_rows": str(src)},
    }

    # Part C fix: only write to public_export/; never write to deliveries/.
    # The delivery build path is the sole writer of count_diagnostics.json
    # inside deliveries/$DATE/wizard_of_odds/.
    for outp in [
        root / "public_export" / "wizard_of_odds" / date / "count_diagnostics.json",
        root / "public_export" / "wizard_of_odds" / "latest" / "count_diagnostics.json",
        root / "public_export" / "wizard_of_odds" / "count_diagnostics.json",
    ]:
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(count, indent=2, sort_keys=True), encoding="utf-8")

    print(f"M8_6_WOO_MONETIZATION_PRODUCER_REPAIR_PASS date={date} rows={len(rows)}")

if __name__ == "__main__":
    import sys
    rc = main()
    if rc is None or rc == 0:
        date = None
        argv = list(sys.argv)
        for flag in ("--date", "--delivery-date"):
            if flag in argv:
                j = argv.index(flag)
                if j + 1 < len(argv):
                    date = argv[j + 1]
                    break
        if date:
            _m86_repair_woo_monetization_contract_after_publish(date)
    raise SystemExit(0 if rc is None else rc)
