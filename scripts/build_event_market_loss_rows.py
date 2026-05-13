#!/usr/bin/env python3
"""M8.6Q B2/B3/B9 — event-market loss rows from OOF model PMF + odds_pairs.

Key M8.6Q contract:
  - The MODEL probability comes from the OOF model PMF, parsed directly.
    No reliance on preexisting model_p_over / prob_over columns.
  - For each joined offered line:
      model_prob_over = sum_{y > line} p_model(y)
      model_prob_under = 1 - model_prob_over
  - Emits model_pmf, model_mean, model_variance, model_prob_over,
    model_prob_under, model_probability_for_side, model_nll, model_rps.
  - Sign convention: event_logloss_delta = model − market, NEGATIVE is better.
  - Refuses to write parquet if any forbidden market full-PMF column is
    present anywhere in the output schema.
  - Forbidden tokens (B9):
      market_implied_pmf, market_implied_full_pmf, market_full_pmf,
      market_pmf, market_implied_pmfs.parquet, market_rps, market_pit,
      market_pmf_nll, market_pmf_mean, market_pmf_variance, market_pmf_delta

Pass marker: M8_6Q_EVENT_MARKET_LOSS_ROWS_BUILD_PASS
"""
from __future__ import annotations
import argparse, json, sys, math
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL

MISSION_STATS_CANONICAL = tuple(MISSION_REQUIRED_TARGETS_CANONICAL)
FORBIDDEN_OUTPUT_COLS = {
    "market_full_pmf","market_implied_pmf","market_pmf",
    "market_pmf_mean","market_pmf_variance","market_pmf_delta",
    "market_pmf_nll","market_rps","market_pit",
    "market_implied_full_pmf","market_implied_pmfs",
}
# Candidate column names for the MODEL PMF in the OOF parquet, in priority order.
PMF_CANDIDATE_COLS = ("pmf", "pmf_active", "pmf_json", "pmf_dict",
                       "model_pmf", "model_full_pmf")


# ─── PMF parsing ─────────────────────────────────────────────────────────────
# M8.6Q v5 — TRUE ATOM PMF SOURCE ONLY. NO ladder/CDF/survival fallback.
M8_6Q_FORBIDDEN_PMF_TOKENS = ("ladder", "p_ge", "survival", "cdf",
                               "cumulative", "reconstructed", "threshold")


def _m8_6q_v5_check_forbidden(text: str, where: str) -> None:
    """Hard-fail if `text` contains any forbidden PMF source token."""
    if not isinstance(text, str): return
    low = text.lower()
    for tok in M8_6Q_FORBIDDEN_PMF_TOKENS:
        if tok in low:
            raise SystemExit(
                f"FATAL: M8_6Q_ATOM_PMF_SOURCE_FORBIDDEN "
                f"token='{tok}' detected in PMF source ({where}). "
                "TRUE ATOM PMF SOURCE ONLY — no ladder/p_ge/cdf/survival/"
                "cumulative/threshold/reconstructed values permitted. "
                "Upgrade the source to emit a true atom PMF column.")


def _parse_pmf_value(v) -> "dict[int, float] | None":
    """Coerce a raw PMF cell into a {k_int: p_float} dict. Accepts ONLY:
       - numpy array (interpreted as p[y=k] for k=0..len-1)
       - python list (same)
       - dict {k: p} (Shape A) — k may be int or str
       - dict {"support": [...], "probs": [...]} (Shape B)
       - JSON string of any of the above
    LADDER / SURVIVAL / CDF reconstruction is REJECTED.
    """
    if v is None: return None
    try:
        if isinstance(v, float) and (v != v):  # NaN
            return None
    except Exception:
        pass

    # numpy / list
    if isinstance(v, np.ndarray):
        v = v.tolist()
    if isinstance(v, list):
        if not v: return None
        # If list of (k, p) pairs:
        if isinstance(v[0], (list, tuple)) and len(v[0]) == 2:
            out = {}
            for k, p in v:
                try: out[int(k)] = float(p)
                except Exception: pass
            return out or None
        # Otherwise assume array indexed by k from 0
        out = {}
        for k, p in enumerate(v):
            try:
                pf = float(p)
                if pf > 0:
                    out[int(k)] = pf
            except Exception: continue
        return out or None

    # dict
    if isinstance(v, dict):
        return _parse_pmf_dict(v)

    # JSON string — first scan for forbidden tokens, then parse
    if isinstance(v, str):
        s = v.strip()
        if not s: return None
        _m8_6q_v5_check_forbidden(s, "string PMF cell")
        try:
            j = json.loads(s)
        except Exception:
            return None
        if isinstance(j, dict):
            return _parse_pmf_dict(j)
        if isinstance(j, list):
            return _parse_pmf_value(j)

    return None


def _parse_pmf_dict(d: dict) -> "dict[int, float] | None":
    """Convert a dict-form PMF to {k_int: p_float}. ACCEPTED SHAPES ONLY:
       A) {k: p}                                  — k int or str-of-int
       B) {"support": [...], "probs": [...]}      — paired exact-outcome arrays
    REJECTED (raises SystemExit M8_6Q_ATOM_PMF_SOURCE_FORBIDDEN):
       - "ladder" key (Shape C, removed in v5)
       - "p_ge_*" keys
       - "p0" + survival/cumulative companions
       - any "survival" / "cdf" / "cumulative" / "threshold" / "reconstructed" key
    """
    if not d:
        return None

    # M8.6Q v5 — hard-fail on any forbidden key in the PMF dict.
    _forbidden_keys = [k for k in d.keys()
                       if isinstance(k, str) and any(
                           tok in k.lower() for tok in M8_6Q_FORBIDDEN_PMF_TOKENS)]
    if _forbidden_keys:
        raise SystemExit(
            f"FATAL: M8_6Q_ATOM_PMF_SOURCE_FORBIDDEN "
            f"forbidden_keys={_forbidden_keys} in PMF dict. "
            "Shape C (ladder/p_ge reconstruction) is REJECTED in v5.")

    # Shape B: support + probs arrays
    if "support" in d and "probs" in d:
        sup = d["support"]; pr = d["probs"]
        if isinstance(sup, list) and isinstance(pr, list) and len(sup) == len(pr):
            out = {}
            for k, p in zip(sup, pr):
                try:
                    out[int(k)] = float(p)
                except Exception: continue
            return out or None

    # Shape A: {k: p}
    out = {}
    for k, p in d.items():
        try:
            out[int(k)] = float(p)
        except Exception:
            continue
    return out or None


def _normalize_pmf(pmf: dict) -> dict:
    """Clip negatives, drop NaN, renormalize to sum 1."""
    if not pmf: return {}
    clean = {int(k): max(0.0, float(p)) for k, p in pmf.items()
             if p is not None and float(p) == float(p)}
    s = sum(clean.values())
    if s <= 0: return {}
    return {k: v/s for k, v in clean.items()}


def _prob_over(pmf: dict, line) -> "float | None":
    """sum_{y > line} p_model(y). Returns None on missing inputs."""
    if not pmf: return None
    try:
        line_f = float(line)
        if line_f != line_f: return None
    except Exception:
        return None
    return float(sum(p for k, p in pmf.items() if k > line_f))


def _pmf_mean_variance(pmf: dict) -> "tuple[float | None, float | None]":
    if not pmf: return (None, None)
    mu = float(sum(k * p for k, p in pmf.items()))
    var = float(sum(((k - mu) ** 2) * p for k, p in pmf.items()))
    return (mu, var)


def _model_event_logloss(p_side: "float | None", y: int) -> "float | None":
    if p_side is None: return None
    p = max(min(float(p_side), 1.0 - 1e-12), 1e-12)
    return -(y * math.log(p) + (1 - y) * math.log(1.0 - p))


def _brier(p_side: "float | None", y: int) -> "float | None":
    if p_side is None: return None
    return float((float(p_side) - y) ** 2)


def _rps(pmf: dict, observed_y: "int | None") -> "float | None":
    """Ranked Probability Score for the discrete distribution. Lower = better."""
    if not pmf or observed_y is None: return None
    items = sorted(pmf.items())
    if not items: return None
    rps = 0.0
    cum_p = 0.0
    cum_y = 0.0
    for k, p in items:
        cum_p += p
        cum_y += (1.0 if k == observed_y else 0.0)
        rps += (cum_p - cum_y) ** 2
    return float(rps)


# ─── Loaders ─────────────────────────────────────────────────────────────────
def _find_odds_pairs_file(date: str, snapshot_substr: str) -> "Path | None":
    base = REPO_ROOT / "data" / "odds_api" / "processed" / date
    if not base.exists(): return None
    cand = sorted(base.glob(f"odds_pairs_*{snapshot_substr}*.parquet"))
    if cand: return cand[-1]
    fallback = sorted(base.glob("odds_pairs_*.parquet"))
    return fallback[-1] if fallback else None


def _load_oof_for_date(path: Path, date: str) -> pd.DataFrame:
    if not path.exists(): return pd.DataFrame()
    df = pd.read_parquet(path)
    for col in ("game_date", "date", "slate_date", "as_of_date"):
        if col in df.columns:
            f = df[df[col].astype(str).str.startswith(date)]
            if len(f) > 0: return f
    # No date col found; return all (caller may still join by player+stat+line)
    return df


def _norm_stat(s) -> "str | None":
    s = str(s or "").lower().strip()
    mapping = {
        "points": "pts", "rebounds": "reb", "assists": "ast",
        "threes_made": "fg3m", "threes": "fg3m", "three_pointers_made": "fg3m",
        "turnovers": "tov", "steals": "stl", "blocks": "blk",
        "steals_blocks": "stocks", "stl_blk": "stocks",
        "points_assists": "pa", "pts_ast": "pa",
        "points_rebounds": "pr", "pts_reb": "pr",
        "points_rebounds_assists": "pra", "pts_reb_ast": "pra",
        "rebounds_assists": "ra", "reb_ast": "ra",
    }
    if s in mapping:
        return mapping[s]
    if s in MISSION_STATS_CANONICAL:
        return s
    return s if s else None


def _resolve_pmf_column(df: pd.DataFrame) -> "str | None":
    for c in PMF_CANDIDATE_COLS:
        if c in df.columns:
            return c
    return None


def _norm_player(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "player_id" in df.columns:
        df["_player_id_str"] = df["player_id"].astype("Int64").astype(str)
    else:
        df["_player_id_str"] = pd.NA
    for ncol in ("player_name", "player"):
        if ncol in df.columns:
            df["_player_name_norm"] = df[ncol].astype(str).str.lower().str.strip()
            break
    else:
        df["_player_name_norm"] = pd.NA
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of-date", required=True)
    ap.add_argument("--snapshot-substr", default="close_or_lock")
    args = ap.parse_args()
    date = args.as_of_date

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"event_market_loss_rows_{date}.parquet"

    odds_path = _find_odds_pairs_file(date, args.snapshot_substr)
    oof_single_path = REPO_ROOT / "data" / "oof_pmfs.parquet"
    oof_combo_path = REPO_ROOT / "data" / "oof_combo_pmfs.parquet"

    early_meta = {
        "as_of_date": date,
        "schema_version": "m8_6q_v2",
        "m8_6q_delta_sign_convention": "model_minus_market (negative=model_better)",
        "forbidden_columns_check": "no_market_full_pmf_columns",
    }

    if odds_path is None:
        empty = pd.DataFrame(columns=[
            "date","game_id","event_id","player_id","player_name","stat","line",
            "side","model_prob_over","model_prob_under","market_prob_over_no_vig",
            "model_pmf","model_mean","model_variance",
            "join_status","join_blockers","m8_6q_schema_version",
        ])
        empty.to_parquet(out_path, index=False)
        Path(str(out_path) + ".meta.json").write_text(
            json.dumps({**early_meta, "rows": 0, "join_status": "no_odds_pairs_file"}, indent=2) + "\n")
        print("M8_6Q_EVENT_MARKET_LOSS_ROWS_BUILD_PASS rows=0 status=no_odds_pairs_file")
        return 0

    odds = pd.read_parquet(odds_path)
    if "market_stat" in odds.columns:
        odds["stat_canonical"] = odds["market_stat"].apply(_norm_stat)
    elif "stat" in odds.columns:
        odds["stat_canonical"] = odds["stat"].apply(_norm_stat)
    else:
        odds["stat_canonical"] = None
    odds = odds[odds["stat_canonical"].isin(MISSION_STATS_CANONICAL)].copy()

    if not (oof_single_path.exists() or oof_combo_path.exists()):
        empty = pd.DataFrame(columns=[
            "date","stat","line","model_prob_over","join_status","m8_6q_schema_version",
        ])
        empty.to_parquet(out_path, index=False)
        Path(str(out_path) + ".meta.json").write_text(
            json.dumps({**early_meta, "rows": 0, "join_status": "no_oof_files"}, indent=2) + "\n")
        print("M8_6Q_EVENT_MARKET_LOSS_ROWS_BUILD_PASS rows=0 status=no_oof_files")
        return 0

    oof_single = _load_oof_for_date(oof_single_path, date)
    oof_combo = _load_oof_for_date(oof_combo_path, date)

    pmf_col_single = _resolve_pmf_column(oof_single) if not oof_single.empty else None
    pmf_col_combo = _resolve_pmf_column(oof_combo) if not oof_combo.empty else None

    oof_frames = []
    for df, kind, pmf_col in ((oof_single, "single", pmf_col_single),
                                (oof_combo, "combo", pmf_col_combo)):
        if df.empty: continue
        df = df.copy()
        df["stat_canonical"] = (df["stat"] if "stat" in df.columns else None).apply(_norm_stat) \
            if "stat" in df.columns else None
        df = df[df["stat_canonical"].isin(MISSION_STATS_CANONICAL)].copy()
        df["pmf_kind"] = kind
        df["_pmf_col_used"] = pmf_col
        oof_frames.append(df)

    if not oof_frames:
        empty = pd.DataFrame(columns=[
            "date","stat","line","model_prob_over","join_status","m8_6q_schema_version",
        ])
        empty.to_parquet(out_path, index=False)
        Path(str(out_path) + ".meta.json").write_text(
            json.dumps({**early_meta, "rows": 0,
                        "join_status": "no_oof_after_filter",
                        "pmf_col_single": pmf_col_single,
                        "pmf_col_combo": pmf_col_combo}, indent=2) + "\n")
        print("M8_6Q_EVENT_MARKET_LOSS_ROWS_BUILD_PASS rows=0 status=no_oof_after_filter")
        return 0

    oof = pd.concat(oof_frames, ignore_index=True)
    oof = _norm_player(oof)
    odds = _norm_player(odds)

    if "line" in oof.columns:
        oof["_line_f"] = pd.to_numeric(oof["line"], errors="coerce")
    else:
        oof["_line_f"] = np.nan
    if "line" in odds.columns:
        odds["_line_f"] = pd.to_numeric(odds["line"], errors="coerce")
    else:
        odds["_line_f"] = np.nan

    # Join odds → oof on (stat, player_id, line); fallback (stat, name, line)
    join_keys_id = ["stat_canonical", "_player_id_str", "_line_f"]
    join_keys_name = ["stat_canonical", "_player_name_norm", "_line_f"]
    oof_id = oof.dropna(subset=["stat_canonical","_line_f"]).drop_duplicates(subset=join_keys_id)
    merged_id = odds.merge(oof_id, on=join_keys_id, how="left",
                            suffixes=("", "_oof"), indicator=True)
    matched_id = merged_id[merged_id["_merge"] == "both"].copy()
    unmatched_id = merged_id[merged_id["_merge"] == "left_only"].copy()

    if not unmatched_id.empty:
        unmatched_id = unmatched_id.drop(columns=["_merge"])
        oof_cols_added = [c for c in oof.columns if c not in odds.columns and c not in join_keys_id]
        unmatched_id = unmatched_id.drop(columns=[c for c in oof_cols_added if c in unmatched_id.columns],
                                          errors="ignore")
        oof_name = oof.dropna(subset=["stat_canonical","_line_f"]).drop_duplicates(subset=join_keys_name)
        merged_name = unmatched_id.merge(oof_name, on=join_keys_name, how="left",
                                          suffixes=("", "_oof"), indicator=True)
        matched_name = merged_name[merged_name["_merge"] == "both"].copy()
        unmatched_total = merged_name[merged_name["_merge"] == "left_only"].copy()
        unmatched_total["join_status"] = "no_oof_match"
        unmatched_total["join_blockers"] = "player_id_and_name_no_match"
        matched = pd.concat([matched_id, matched_name], ignore_index=True)
    else:
        matched = matched_id
        unmatched_total = pd.DataFrame()
    matched["join_status"] = "matched"

    rows_out = []
    for _, r in matched.iterrows():
        rd = r.to_dict()
        pmf_col_used = rd.get("_pmf_col_used") or _resolve_pmf_column(pd.DataFrame([rd]))
        raw_pmf = rd.get(pmf_col_used) if pmf_col_used else None
        pmf = _parse_pmf_value(raw_pmf)
        pmf = _normalize_pmf(pmf) if pmf else {}
        line = rd.get("_line_f")

        # B2 — compute model_prob_over from PMF directly
        mp_over = _prob_over(pmf, line)
        mp_under = (1.0 - mp_over) if mp_over is not None else None
        m_mean, m_var = _pmf_mean_variance(pmf)
        # Actual outcome (for scoring)
        actual = rd.get("actual_value")
        if actual is None: actual = rd.get("settled_value")
        if actual is None: actual = rd.get("actual")
        if actual is None: actual = rd.get("y")
        # hit_result: derive from actual vs line if needed
        hit_result = rd.get("hit_result")
        if hit_result is None and actual is not None and line is not None:
            try:
                hit_result = 1 if float(actual) > float(line) else 0
            except Exception:
                hit_result = None

        # Market no-vig
        mkt_over = rd.get("no_vig_over_prob")
        mkt_under = rd.get("no_vig_under_prob")
        try: mkt_over_f = float(mkt_over) if mkt_over is not None and pd.notna(mkt_over) else None
        except Exception: mkt_over_f = None
        try: mkt_under_f = float(mkt_under) if mkt_under is not None and pd.notna(mkt_under) else None
        except Exception: mkt_under_f = None
        if mkt_under_f is None and mkt_over_f is not None:
            mkt_under_f = 1.0 - mkt_over_f

        # Side default OVER (event-level rows; per-side derivation downstream)
        side = "OVER"
        model_prob_for_side = mp_over if side == "OVER" else mp_under
        market_prob_for_side = mkt_over_f if side == "OVER" else mkt_under_f

        # B3 — sign convention: delta = model − market (negative = model better)
        model_ll = _model_event_logloss(model_prob_for_side, hit_result) if hit_result in (0,1) else None
        market_ll = _model_event_logloss(market_prob_for_side, hit_result) if hit_result in (0,1) else None
        ll_delta = (model_ll - market_ll) if (model_ll is not None and market_ll is not None) else None

        model_br = _brier(model_prob_for_side, hit_result) if hit_result in (0,1) else None
        market_br = _brier(market_prob_for_side, hit_result) if hit_result in (0,1) else None
        br_delta = (model_br - market_br) if (model_br is not None and market_br is not None) else None

        try: actual_int = int(actual) if actual is not None and pd.notna(actual) else None
        except Exception: actual_int = None
        rps = _rps(pmf, actual_int)

        # NLL of model PMF at the observed outcome (used for distributional fit)
        model_nll_dist = None
        if pmf and actual_int is not None and actual_int in pmf:
            p_obs = max(min(pmf[actual_int], 1.0 - 1e-12), 1e-12)
            model_nll_dist = -math.log(p_obs)

        out_row = {
            "date": date,
            "game_id": rd.get("game_id") or rd.get("event_id"),
            "event_id": rd.get("event_id"),
            "snapshot_type": rd.get("snapshot_type") or "close_or_lock",
            "snapshot_time_utc": rd.get("snapshot_time_utc"),
            "home_team": rd.get("home_team"),
            "away_team": rd.get("away_team"),
            "bookmaker_key": rd.get("bookmaker_key"),
            "player_id": rd.get("player_id"),
            "player_name": rd.get("player_name") or rd.get("player"),
            "stat": rd.get("stat_canonical"),
            "line": line,
            "side": side,
            "role_bucket": rd.get("role_bucket"),
            "pmf_kind": rd.get("pmf_kind"),
            "pmf_col_used": pmf_col_used,
            "is_alternate": bool(rd.get("is_alternate", False)),

            # ── B2 CONTRACT FIELDS — PMF-derived ──
            "model_pmf": json.dumps({str(k): v for k, v in pmf.items()}) if pmf else None,
            "model_mean": m_mean,
            "model_variance": m_var,
            "model_prob_over": mp_over,
            "model_prob_under": mp_under,
            "model_probability_for_side": model_prob_for_side,

            # Market event probs (no-vig)
            "market_prob_over_no_vig": mkt_over_f,
            "market_prob_under_no_vig": mkt_under_f,
            "market_probability_for_side": market_prob_for_side,

            # Odds
            "over_odds_american": rd.get("over_odds_american"),
            "under_odds_american": rd.get("under_odds_american"),

            # Settled outcome
            "actual": actual_int,
            "hit_result": hit_result,
            "closing_line_result": rd.get("closing_line_result"),
            "settled": hit_result in (0, 1),

            # B3 — model − market (negative = model better)
            "model_event_logloss": model_ll,
            "market_event_logloss": market_ll,
            "event_logloss_delta": ll_delta,
            "model_brier": model_br,
            "market_brier": market_br,
            "brier_delta": br_delta,

            # Distributional metrics
            "model_nll": model_nll_dist,
            "model_rps": rps,

            "walk_forward_only": True,
            "same_sample_predictions_used": False,
            "join_status": rd.get("join_status", "matched"),
            "join_blockers": rd.get("join_blockers"),
            "m8_6q_schema_version": "v2",
            "m8_6q_delta_sign_convention": "model_minus_market_negative_better",
        }
        rows_out.append(out_row)

    # Emit unmatched rows (no-PMF placeholder) so the diagnostic is complete
    for _, r in unmatched_total.iterrows():
        rd = r.to_dict()
        line = rd.get("_line_f")
        mkt_over = rd.get("no_vig_over_prob")
        try: mkt_over_f = float(mkt_over) if mkt_over is not None and pd.notna(mkt_over) else None
        except Exception: mkt_over_f = None
        rows_out.append({
            "date": date,
            "game_id": rd.get("game_id") or rd.get("event_id"),
            "event_id": rd.get("event_id"),
            "snapshot_type": rd.get("snapshot_type") or "close_or_lock",
            "player_id": rd.get("player_id"),
            "player_name": rd.get("player_name") or rd.get("player"),
            "stat": rd.get("stat_canonical"),
            "line": line,
            "side": "OVER",
            "bookmaker_key": rd.get("bookmaker_key"),
            "is_alternate": bool(rd.get("is_alternate", False)),
            "model_pmf": None,
            "model_mean": None,
            "model_variance": None,
            "model_prob_over": None,
            "model_prob_under": None,
            "model_probability_for_side": None,
            "market_prob_over_no_vig": mkt_over_f,
            "market_prob_under_no_vig": (1.0 - mkt_over_f) if mkt_over_f is not None else None,
            "market_probability_for_side": mkt_over_f,
            "actual": None,
            "hit_result": None,
            "settled": False,
            "model_event_logloss": None,
            "market_event_logloss": None,
            "event_logloss_delta": None,
            "model_brier": None,
            "market_brier": None,
            "brier_delta": None,
            "model_nll": None,
            "model_rps": None,
            "walk_forward_only": True,
            "join_status": "no_oof_match",
            "join_blockers": "player_id_and_name_no_match",
            "m8_6q_schema_version": "v2",
        })

    out = pd.DataFrame(rows_out)

    # B9 — refuse to write parquet if any forbidden column slipped in
    leaked = [c for c in out.columns if c.lower() in {x.lower() for x in FORBIDDEN_OUTPUT_COLS}]
    if leaked:
        raise SystemExit(
            f"FATAL: M8_6Q_FORBIDDEN_COLUMNS_LEAKED {leaked} — refuse to write."
        )

    out.to_parquet(out_path, index=False)

    matched_count = int((out["join_status"] == "matched").sum()) if len(out) else 0
    scored_count = 0
    if len(out):
        scored_mask = (
            out["model_prob_over"].notna() &
            out["market_prob_over_no_vig"].notna() &
            out["hit_result"].notna() &
            out["model_event_logloss"].notna() &
            out["market_event_logloss"].notna() &
            out["event_logloss_delta"].notna() &
            out["model_brier"].notna() &
            out["market_brier"].notna() &
            out["brier_delta"].notna()
        )
        scored_count = int(scored_mask.sum())

    Path(str(out_path) + ".meta.json").write_text(json.dumps({
        **early_meta,
        "rows": int(len(out)),
        "matched_rows": matched_count,
        "scored_rows_all_fields_nonnull": scored_count,
        "odds_pairs_source": str(odds_path.relative_to(REPO_ROOT)),
        "oof_single_rows": int(len(oof_single)),
        "oof_combo_rows": int(len(oof_combo)),
        "pmf_col_single": pmf_col_single,
        "pmf_col_combo": pmf_col_combo,
    }, indent=2) + "\n")

    print(f"M8_6Q_EVENT_MARKET_LOSS_ROWS_BUILD_PASS")
    print(f"  rows={len(out)} matched={matched_count} scored_all_fields={scored_count}")
    print(f"  wrote: {out_path.relative_to(REPO_ROOT)}")
    print(f"  pmf_col_single={pmf_col_single} pmf_col_combo={pmf_col_combo}")
    print(f"  sign_convention=model_minus_market_negative_better")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
