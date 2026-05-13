#!/usr/bin/env python3
"""M8.6Q B2/B3/B9 — event-market loss rows from OOF model PMF + odds_pairs.

Key M8.6Q contract:
  - The MODEL probability comes from the OOF model PMF when available for the
    slate date; if the OOF slice is empty for `--as-of-date`, the builder falls
    back to the same-day **model-only canonical** atom PMF (`pmf_active`), which
    is still a model PMF (never market-implied PMF).
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
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from event_line_calibration import apply_segment_calibration  # noqa: E402
from odds_snapshot_selection import select_odds_pairs_parquet  # noqa: E402
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


def _canonical_delivery_path(date: str) -> Path:
    return (
        REPO_ROOT
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )


def _enrich_odds_player_ids(odds: pd.DataFrame, date: str) -> pd.DataFrame:
    """Odds pairs often lack player_id; map from same-slate canonical model rows."""
    odds = odds.copy()
    if "player_id" not in odds.columns:
        odds["player_id"] = pd.NA
    cpath = _canonical_delivery_path(date)
    if not cpath.exists():
        return odds
    can = pd.read_parquet(cpath, columns=["player_id", "player_name", "stat"])
    can["stat_canonical"] = can["stat"].apply(_norm_stat)
    can["_player_name_norm"] = (
        can["player_name"].astype(str).str.lower().str.strip()
    )
    mp = can.drop_duplicates(subset=["_player_name_norm", "stat_canonical"])[
        ["_player_name_norm", "stat_canonical", "player_id"]
    ]
    odds = odds.merge(
        mp,
        left_on=["_player_name_norm", "stat_canonical"],
        right_on=["_player_name_norm", "stat_canonical"],
        how="left",
        suffixes=("", "_canon"),
    )
    pid_new = odds.get("player_id_canon")
    if pid_new is not None:
        odds["player_id"] = odds["player_id"].where(
            odds["player_id"].notna(), pid_new
        )
        odds = odds.drop(columns=["player_id_canon"], errors="ignore")
    return odds


def _load_canonical_model_pmfs(date: str) -> pd.DataFrame:
    """Same-day atom PMFs from model-only canonical (not market-implied PMF)."""
    cpath = _canonical_delivery_path(date)
    if not cpath.exists():
        return pd.DataFrame()
    can = pd.read_parquet(cpath)
    pmf_col = _resolve_pmf_column(can) or "pmf_active"
    can = can.copy()
    can["stat_canonical"] = can["stat"].apply(_norm_stat)
    can = can[can["stat_canonical"].isin(MISSION_STATS_CANONICAL)].copy()
    can["player_id"] = pd.to_numeric(can["player_id"], errors="coerce").astype("Int64")
    can["pmf_kind"] = "delivery_atom_canonical"
    can["_pmf_col_used"] = pmf_col
    if "role_bucket" not in can.columns:
        can["role_bucket"] = None
    if "game_id" not in can.columns:
        can["game_id"] = None
    can["game_date"] = date
    return can


def _load_player_actuals_long(date: str) -> dict[tuple[int, str], int]:
    """Box-score outcomes for slate date (empty dict if no rows locally)."""
    pgs = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not pgs.exists():
        return {}
    bx = pd.read_parquet(pgs)
    bx = bx[bx["game_date"].astype(str).str.startswith(date)].copy()
    if bx.empty:
        return {}
    bx["tov"] = bx["turnover"]
    bx["stocks"] = bx["stl"] + bx["blk"]
    bx["pa"] = bx["pts"] + bx["ast"]
    bx["pr"] = bx["pts"] + bx["reb"]
    bx["ra"] = bx["reb"] + bx["ast"]
    bx["pra"] = bx["pts"] + bx["reb"] + bx["ast"]
    out: dict[tuple[int, str], int] = {}
    stat_cols = [s for s in MISSION_STATS_CANONICAL if s in bx.columns]
    for _, r in bx.iterrows():
        try:
            pid = int(r["player_id"])
        except Exception:
            continue
        for st in stat_cols:
            try:
                out[(pid, st)] = int(r[st])
            except Exception:
                continue
    return out


def _box_score_rows_for_date(date: str) -> int:
    """Count rows in player_game_stats for calendar date (local parquet)."""
    pgs = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not pgs.exists():
        return 0
    bx = pd.read_parquet(pgs, columns=["game_date"])
    return int(bx["game_date"].astype(str).str.startswith(date).sum())


def _binary_over_hit(actual: int | None, line: float | None) -> int | None:
    """OVER hit for settled props: half-lines strict >; integer lines exclude push."""
    if actual is None or line is None:
        return None
    try:
        a = int(actual)
        L = float(line)
    except Exception:
        return None
    if L != L:  # NaN
        return None
    frac2 = abs(L * 2.0 % 2.0 - 1.0) < 0.25  # .5 line
    if frac2:
        if a > L:
            return 1
        if a < L:
            return 0
        return None
    if a > L:
        return 1
    if a < L:
        return 0
    return None  # push on integer line


def _main_single_date(date: str, snapshot_substr: str, event_cal: dict | None = None) -> int:
    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"event_market_loss_rows_{date}.parquet"

    odds_path, odds_sel_meta = select_odds_pairs_parquet(REPO_ROOT, date, snapshot_substr)
    snap_cols = {k: v for k, v in odds_sel_meta.items() if str(k).startswith("odds_snapshot")}
    oof_single_path = REPO_ROOT / "data" / "oof_pmfs.parquet"
    oof_combo_path = REPO_ROOT / "data" / "oof_combo_pmfs.parquet"

    early_meta = {
        "as_of_date": date,
        "schema_version": "m8_6q_v2",
        "m8_6q_delta_sign_convention": "model_minus_market (negative=model_better)",
        "forbidden_columns_check": "no_market_full_pmf_columns",
        **snap_cols,
    }
    if event_cal:
        early_meta = {
            **early_meta,
            "event_calibration_applied": True,
            "event_calibration_version": event_cal.get("event_calibration_version"),
            "event_calibration_stage": event_cal.get("event_calibration_stage"),
            "event_calibration_source": event_cal.get("event_calibration_source"),
            "market_pmf_used": bool(event_cal.get("market_pmf_used", False)),
            "market_prob_used_as_training_label": bool(
                event_cal.get("market_prob_used_as_training_label", False)
            ),
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

    can_path = _canonical_delivery_path(date)
    if not (
        oof_single_path.exists()
        or oof_combo_path.exists()
        or can_path.exists()
    ):
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

    oof_frames: list[pd.DataFrame] = []
    for df, kind, pmf_col in (
        (oof_single, "oof_single", pmf_col_single),
        (oof_combo, "oof_combo", pmf_col_combo),
    ):
        if df.empty:
            continue
        df = df.copy()
        df["stat_canonical"] = (
            df["stat"].apply(_norm_stat) if "stat" in df.columns else None
        )
        df = df[df["stat_canonical"].isin(MISSION_STATS_CANONICAL)].copy()
        df["pmf_kind"] = kind
        df["_pmf_col_used"] = pmf_col
        oof_frames.append(df)

    model_source_mode = "oof_date_slice"
    if oof_frames:
        model_df = pd.concat(oof_frames, ignore_index=True)
    else:
        model_df = pd.DataFrame()

    if model_df.empty:
        model_df = _load_canonical_model_pmfs(date)
        model_source_mode = (
            "delivery_canonical_fallback"
            if (oof_single_path.exists() or oof_combo_path.exists())
            else "delivery_canonical_only"
        )

    if model_df.empty:
        empty = pd.DataFrame(columns=[
            "date","stat","line","model_prob_over","join_status","m8_6q_schema_version",
        ])
        empty.to_parquet(out_path, index=False)
        Path(str(out_path) + ".meta.json").write_text(
            json.dumps(
                {
                    **early_meta,
                    "rows": 0,
                    "join_status": "no_model_pmf_rows",
                    "pmf_col_single": pmf_col_single,
                    "pmf_col_combo": pmf_col_combo,
                    "canonical_path": str(can_path) if can_path.exists() else None,
                },
                indent=2,
            )
            + "\n",
        )
        print("M8_6Q_EVENT_MARKET_LOSS_ROWS_BUILD_PASS rows=0 status=no_model_pmf_rows")
        return 0

    # Prefer base OOF over combo OOF when both exist for same (player, stat).
    _prio = {"oof_single": 0, "oof_combo": 1, "delivery_atom_canonical": 2}
    model_df = model_df.assign(
        _pmf_kind_prio=model_df["pmf_kind"].map(lambda x: _prio.get(str(x), 9))
    )
    model_df = model_df.sort_values(
        by=["_pmf_kind_prio"],
        ascending=True,
        kind="mergesort",
    ).drop(columns=["_pmf_kind_prio"])
    model_df = model_df.drop_duplicates(
        subset=["player_id", "stat_canonical"], keep="first"
    )

    model_df = _norm_player(model_df)
    odds = _norm_player(odds)
    odds = _enrich_odds_player_ids(odds, date)
    odds["_player_id_str"] = pd.to_numeric(
        odds["player_id"], errors="coerce"
    ).astype("Int64").astype(str)

    if "line" in odds.columns:
        odds["_line_f"] = pd.to_numeric(odds["line"], errors="coerce")
    else:
        odds["_line_f"] = np.nan

    join_keys_id = ["stat_canonical", "_player_id_str"]
    mdl = model_df.dropna(subset=["stat_canonical", "_player_id_str"]).drop_duplicates(
        subset=join_keys_id
    )
    merged_id = odds.merge(
        mdl,
        on=join_keys_id,
        how="left",
        suffixes=("", "_mdl"),
        indicator=True,
    )
    matched_id = merged_id[merged_id["_merge"] == "both"].copy()
    matched_id = matched_id.drop(columns=["_merge"], errors="ignore")
    unmatched_id = merged_id[merged_id["_merge"] == "left_only"].copy()

    if not unmatched_id.empty:
        unmatched_id = unmatched_id.drop(columns=["_merge"], errors="ignore")
        drop_cols = [
            c
            for c in model_df.columns
            if c not in odds.columns and c not in join_keys_id
        ]
        unmatched_id = unmatched_id.drop(
            columns=[c for c in drop_cols if c in unmatched_id.columns],
            errors="ignore",
        )
        mdl_name = model_df.dropna(
            subset=["stat_canonical", "_player_name_norm"]
        ).drop_duplicates(subset=["stat_canonical", "_player_name_norm"])
        merged_name = unmatched_id.merge(
            mdl_name,
            on=["stat_canonical", "_player_name_norm"],
            how="left",
            suffixes=("", "_mdl2"),
            indicator=True,
        )
        matched_name = merged_name[merged_name["_merge"] == "both"].copy()
        matched_name = matched_name.drop(columns=["_merge"], errors="ignore")
        unmatched_total = merged_name[merged_name["_merge"] == "left_only"].copy()
        unmatched_total["join_status"] = "no_oof_match"
        unmatched_total["join_blockers"] = "player_id_and_name_no_match"
        matched = pd.concat([matched_id, matched_name], ignore_index=True)
    else:
        matched = matched_id
        unmatched_total = pd.DataFrame()
    matched["join_status"] = "matched"

    actual_lookup = _load_player_actuals_long(date)
    n_box_rows_date = _box_score_rows_for_date(date)
    n_odds_rows = int(len(odds))

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
        mp_over_raw = mp_over
        cal_applied = False
        cal_seg_id = None
        if event_cal is not None and mp_over is not None:
            stc = str(rd.get("stat_canonical") or "").lower()
            rb = str(rd.get("role_bucket_mdl") or rd.get("role_bucket") or "unknown")
            line_f = None
            try:
                if line is not None and line == line:
                    line_f = float(line)
            except Exception:
                line_f = None
            mp2, cal_applied, cal_seg_id = apply_segment_calibration(
                float(mp_over), stat=stc, role_bucket=rb, cal=event_cal, line=line_f,
            )
            if cal_applied and mp2 is not None:
                mp_over = mp2
        mp_under = (1.0 - mp_over) if mp_over is not None else None
        m_mean, m_var = _pmf_mean_variance(pmf)
        # Actual outcome (for scoring): OOF row if present, else box score lookup
        actual = rd.get("actual_value")
        if actual is None:
            actual = rd.get("settled_value")
        if actual is None:
            actual = rd.get("actual")
        if actual is None:
            actual = rd.get("y")
        pid_raw = rd.get("player_id")
        st_raw = rd.get("stat_canonical")
        if actual is None and pid_raw is not None and st_raw is not None:
            try:
                actual = actual_lookup.get((int(pid_raw), str(st_raw)))
            except Exception:
                pass

        try:
            actual_int = int(actual) if actual is not None and pd.notna(actual) else None
        except Exception:
            actual_int = None

        hit_result = rd.get("hit_result")
        if hit_result is None:
            hit_result = _binary_over_hit(actual_int, line)

        # Market no-vig
        mkt_over = rd.get("no_vig_over_prob")
        mkt_under = rd.get("no_vig_under_prob")
        try: mkt_over_f = float(mkt_over) if mkt_over is not None and pd.notna(mkt_over) else None
        except Exception: mkt_over_f = None
        try: mkt_under_f = float(mkt_under) if mkt_under is not None and pd.notna(mkt_under) else None
        except Exception: mkt_under_f = None
        if mkt_under_f is None and mkt_over_f is not None:
            mkt_under_f = 1.0 - mkt_over_f

        two_way_ok = (
            mkt_over_f is not None
            and mkt_under_f is not None
            and math.isfinite(mkt_over_f)
            and math.isfinite(mkt_under_f)
        )

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

        rps = _rps(pmf, actual_int)

        # NLL of model PMF at the observed outcome (used for distributional fit)
        model_nll_dist = None
        if pmf and actual_int is not None and actual_int in pmf:
            p_obs = max(min(pmf[actual_int], 1.0 - 1e-12), 1e-12)
            model_nll_dist = -math.log(p_obs)

        scoring_blocker = None
        if not two_way_ok:
            scoring_blocker = "missing_two_way_odds"
        elif mp_over is None:
            scoring_blocker = "model_pmf_unusable"
        elif hit_result is None:
            if n_box_rows_date <= 0:
                scoring_blocker = "no_actuals_for_date"
            elif actual_int is None:
                scoring_blocker = "player_actual_missing"
            else:
                scoring_blocker = "push_or_nonbinary_outcome"

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
            "role_bucket": rd.get("role_bucket_mdl") or rd.get("role_bucket"),
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

            "walk_forward_only": str(rd.get("pmf_kind", "")).startswith("oof"),
            "same_sample_predictions_used": False,
            "join_status": rd.get("join_status", "matched"),
            "join_blockers": rd.get("join_blockers"),
            "scoring_blocker": scoring_blocker,

            "model_prob_over_pre_event_calibration": mp_over_raw,
            "event_calibration_applied": bool(cal_applied),
            "event_calibration_version": (event_cal or {}).get("event_calibration_version"),
            "event_calibration_stage": (event_cal or {}).get("event_calibration_stage"),
            "event_calibration_source": (event_cal or {}).get("event_calibration_source"),
            "event_calibration_segment": cal_seg_id,
            "market_pmf_used": False,
            "market_prob_used_as_training_label": False,

            "m8_6q_schema_version": "v2",
            "m8_6q_delta_sign_convention": "model_minus_market_negative_better",
            **snap_cols,
        }
        rows_out.append(out_row)

    # Emit unmatched rows (no-PMF placeholder) so the diagnostic is complete
    for _, r in unmatched_total.iterrows():
        rd = r.to_dict()
        line = rd.get("_line_f")
        mkt_over = rd.get("no_vig_over_prob")
        try: mkt_over_f = float(mkt_over) if mkt_over is not None and pd.notna(mkt_over) else None
        except Exception: mkt_over_f = None
        mkt_under_f = (1.0 - mkt_over_f) if mkt_over_f is not None else None
        sb_un = "market_join_failed"
        if mkt_over_f is None or mkt_under_f is None:
            sb_un = "missing_two_way_odds"
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
            "scoring_blocker": sb_un,
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

            "model_prob_over_pre_event_calibration": None,
            "event_calibration_applied": False,
            "event_calibration_version": (event_cal or {}).get("event_calibration_version"),
            "event_calibration_stage": (event_cal or {}).get("event_calibration_stage"),
            "event_calibration_source": (event_cal or {}).get("event_calibration_source"),
            "event_calibration_segment": None,
            "market_pmf_used": False,
            "market_prob_used_as_training_label": False,

            "m8_6q_schema_version": "v2",
            "m8_6q_delta_sign_convention": "model_minus_market_negative_better",
            **snap_cols,
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

    overlap_ratio = (matched_count / n_odds_rows) if n_odds_rows else 0.0
    sb_counts = {}
    if len(out) and "scoring_blocker" in out.columns:
        sb_counts = out["scoring_blocker"].fillna("none").astype(str).value_counts().to_dict()

    Path(str(out_path) + ".meta.json").write_text(json.dumps({
        **early_meta,
        "rows": int(len(out)),
        "matched_rows": matched_count,
        "scored_rows_all_fields_nonnull": scored_count,
        "odds_rows": n_odds_rows,
        "market_overlap_ratio": round(overlap_ratio, 6),
        "insufficient_market_overlap": bool(overlap_ratio < 0.35 and n_odds_rows > 10),
        "scoring_blocker_counts": sb_counts,
        "odds_pairs_source": str(odds_path.relative_to(REPO_ROOT)),
        "oof_single_rows": int(len(oof_single)),
        "oof_combo_rows": int(len(oof_combo)),
        "model_source_mode": model_source_mode,
        "box_score_rows_for_as_of_date": int(n_box_rows_date),
        "box_score_actual_lookup_keys": len(actual_lookup),
        "pmf_col_single": pmf_col_single,
        "pmf_col_combo": pmf_col_combo,
    }, indent=2) + "\n")

    print(f"M8_6Q_EVENT_MARKET_LOSS_ROWS_BUILD_PASS")
    print(f"  rows={len(out)} matched={matched_count} scored_all_fields={scored_count}")
    print(f"  wrote: {out_path.relative_to(REPO_ROOT)}")
    print(f"  pmf_col_single={pmf_col_single} pmf_col_combo={pmf_col_combo}")
    print(f"  sign_convention=model_minus_market_negative_better")
    return 0


def _main_date_range(start: str, end: str, snapshot_substr: str, event_cal: dict | None = None) -> int:
    from datetime import date as dt_date, timedelta

    frames: list[pd.DataFrame] = []
    metas: list[dict] = []
    cur = dt_date.fromisoformat(start)
    end_d = dt_date.fromisoformat(end)
    while cur <= end_d:
        s = cur.isoformat()
        rc = _main_single_date(s, snapshot_substr, event_cal)
        if rc != 0:
            return rc
        p = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{s}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p))
            mp = Path(str(p) + ".meta.json")
            if mp.exists():
                try:
                    metas.append(json.loads(mp.read_text(encoding="utf-8")))
                except Exception:
                    metas.append({})
        cur += timedelta(days=1)
    if not frames:
        print("FATAL: date range produced no daily event_market_loss_rows", file=sys.stderr)
        return 1
    combo = pd.concat(frames, ignore_index=True)
    leaked = [c for c in combo.columns if c.lower() in {x.lower() for x in FORBIDDEN_OUTPUT_COLS}]
    if leaked:
        raise SystemExit(f"FATAL: M8_6Q_FORBIDDEN_COLUMNS_LEAKED {leaked}")
    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_path = out_dir / f"event_market_loss_rows_{start}_{end}.parquet"
    combo.to_parquet(out_path, index=False)
    matched_count = int((combo["join_status"] == "matched").sum()) if len(combo) else 0
    scored_count = 0
    if len(combo):
        scored_mask = (
            combo["model_prob_over"].notna()
            & combo["market_prob_over_no_vig"].notna()
            & combo["hit_result"].notna()
            & combo["model_event_logloss"].notna()
            & combo["market_event_logloss"].notna()
            & combo["event_logloss_delta"].notna()
            & combo["model_brier"].notna()
            & combo["market_brier"].notna()
            & combo["brier_delta"].notna()
        )
        scored_count = int(scored_mask.sum())
    agg_meta = {
        "schema_version": "m8_6q_v2",
        "date_range": {"start": start, "end": end},
        "rows": int(len(combo)),
        "matched_rows": matched_count,
        "scored_rows_all_fields_nonnull": scored_count,
        "daily_meta": metas,
        "combined_output": str(out_path.relative_to(REPO_ROOT)),
    }
    if event_cal:
        agg_meta.update(
            {
                "event_calibration_applied": True,
                "event_calibration_version": event_cal.get("event_calibration_version"),
                "event_calibration_stage": event_cal.get("event_calibration_stage"),
                "event_calibration_source": event_cal.get("event_calibration_source"),
                "market_pmf_used": bool(event_cal.get("market_pmf_used", False)),
                "market_prob_used_as_training_label": bool(
                    event_cal.get("market_prob_used_as_training_label", False)
                ),
            }
        )
    Path(str(out_path) + ".meta.json").write_text(json.dumps(agg_meta, indent=2) + "\n", encoding="utf-8")
    print("M8_6Q_EVENT_MARKET_LOSS_ROWS_BUILD_PASS (range)")
    print(f"  rows={len(combo)} matched={matched_count} scored_all_fields={scored_count}")
    print(f"  wrote: {out_path.relative_to(REPO_ROOT)}")
    return 0


def _main_dates_file_list(
    dates: list[str], snapshot_substr: str, label: str, event_cal: dict | None = None
) -> int:
    """Concatenate daily event_market_loss rows for explicit date list (inventory-driven)."""
    frames: list[pd.DataFrame] = []
    metas: list[dict] = []
    for d in sorted(set(dates)):
        rc = _main_single_date(d, snapshot_substr, event_cal)
        if rc != 0:
            return rc
        p = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{d}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p))
            mp = Path(str(p) + ".meta.json")
            if mp.exists():
                try:
                    metas.append(json.loads(mp.read_text(encoding="utf-8")))
                except Exception:
                    metas.append({})
    if not frames:
        print("FATAL: dates-file produced no daily event_market_loss_rows", file=sys.stderr)
        return 1
    combo = pd.concat(frames, ignore_index=True)
    leaked = [c for c in combo.columns if c.lower() in {x.lower() for x in FORBIDDEN_OUTPUT_COLS}]
    if leaked:
        raise SystemExit(f"FATAL: M8_6Q_FORBIDDEN_COLUMNS_LEAKED {leaked}")
    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_path = out_dir / f"event_market_loss_rows_{label}.parquet"
    combo.to_parquet(out_path, index=False)
    matched_count = int((combo["join_status"] == "matched").sum()) if len(combo) else 0
    scored_count = 0
    if len(combo):
        scored_mask = (
            combo["model_prob_over"].notna()
            & combo["market_prob_over_no_vig"].notna()
            & combo["hit_result"].notna()
            & combo["model_event_logloss"].notna()
            & combo["market_event_logloss"].notna()
            & combo["event_logloss_delta"].notna()
            & combo["model_brier"].notna()
            & combo["market_brier"].notna()
            & combo["brier_delta"].notna()
        )
        scored_count = int(scored_mask.sum())
    agg_meta = {
        "schema_version": "m8_6q_v2",
        "dates_used": sorted(set(dates)),
        "label": label,
        "rows": int(len(combo)),
        "matched_rows": matched_count,
        "scored_rows_all_fields_nonnull": scored_count,
        "daily_meta": metas,
        "combined_output": str(out_path.relative_to(REPO_ROOT)),
    }
    if event_cal:
        agg_meta.update(
            {
                "event_calibration_applied": True,
                "event_calibration_version": event_cal.get("event_calibration_version"),
                "event_calibration_stage": event_cal.get("event_calibration_stage"),
                "event_calibration_source": event_cal.get("event_calibration_source"),
                "market_pmf_used": bool(event_cal.get("market_pmf_used", False)),
                "market_prob_used_as_training_label": bool(
                    event_cal.get("market_prob_used_as_training_label", False)
                ),
            }
        )
    Path(str(out_path) + ".meta.json").write_text(json.dumps(agg_meta, indent=2) + "\n", encoding="utf-8")
    print("M8_6Q_EVENT_MARKET_LOSS_ROWS_BUILD_PASS (dates-file)")
    print(f"  rows={len(combo)} matched={matched_count} scored_all_fields={scored_count}")
    print(f"  wrote: {out_path.relative_to(REPO_ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of-date", "--date", dest="as_of_date", default=None)
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--dates-file", default=None)
    ap.add_argument("--include-ineligible", action="store_true")
    ap.add_argument("--snapshot-substr", default="auto")
    ap.add_argument(
        "--event-calibration-model",
        default=None,
        help="Optional JSON from fit_guarded_event_market_calibration (Platt on line prob, eval only).",
    )
    args = ap.parse_args()

    event_cal: dict | None = None
    if args.event_calibration_model:
        pcal = Path(args.event_calibration_model)
        if not pcal.is_absolute():
            pcal = REPO_ROOT / pcal
        if not pcal.is_file():
            print(f"FATAL: --event-calibration-model not found: {pcal}", file=sys.stderr)
            return 2
        event_cal = json.loads(pcal.read_text(encoding="utf-8"))

    modes = sum(
        bool(x) for x in (args.as_of_date, (args.start_date and args.end_date), args.dates_file)
    )
    if modes > 1:
        print("FATAL: use only one of --as-of-date, --start-date/--end-date, --dates-file", file=sys.stderr)
        return 2

    if args.dates_file:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from event_market_date_selection import (  # noqa: WPS433
            resolve_event_market_label,
        )

        dates, label, _meta = resolve_event_market_label(
            date=None,
            start_date=None,
            end_date=None,
            dates_file=args.dates_file,
            include_ineligible=args.include_ineligible,
        )
        return _main_dates_file_list(dates, args.snapshot_substr, label, event_cal)

    if args.start_date or args.end_date:
        if not (args.start_date and args.end_date):
            print("FATAL: --start-date and --end-date must be used together", file=sys.stderr)
            return 2
        return _main_date_range(args.start_date, args.end_date, args.snapshot_substr, event_cal)
    if not args.as_of_date:
        print("FATAL: pass --as-of-date, --start-date/--end-date, or --dates-file", file=sys.stderr)
        return 2
    return _main_single_date(args.as_of_date, args.snapshot_substr, event_cal)


if __name__ == "__main__":
    raise SystemExit(main())
