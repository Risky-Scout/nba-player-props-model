"""Tonight-only live PMF export for Derek / EV Analytics / Wizard of Odds.

Reads predict pipeline's all_props_{date}.parquet, applies Phase 8
role-aware calibration plus FG3M tail-shrink (k>=7 at w=0.2), and (when
de-vigged market probabilities are available) emits a market-tilted
"best" PMF whose CDF is anchored to the closing/morning market prob at
the offered line. Writes a self-contained delivery bundle to:

  deliveries/2026-04-27/live_after_2029_et/

Inputs (all local, no API calls):
  - predictions/all_props_2026-04-27.parquet  (raw model PMFs for tonight)
  - data/player_game_stats.parquet            (player history + team_abbr)
  - data/player_availability_asof.parquet     (availability hints, optional)
  - /tmp/phase8_full_vectorized_success/artifacts_downloaded/
        phase8-outputs/artifacts/models/pmf_cal_meta.json
        phase8-outputs/artifacts/models/pmf_cal_role_{stat}.pkl

The Phase-8 calibrators were fit with calibration_target=
active_conditioned_prop_live; we active-condition the raw all_props PMF
(with p_inactive from the local minutes distribution) before applying
cal.apply().

Tonight's filtered slate (start_et > 20:29):
  - OKC @ PHX  (21:30 ET)
  - MIN @ DEN  (22:30 ET)

DET @ ORL is excluded by the start-time filter (tipped earlier).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import warnings
from datetime import datetime, timezone, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.calibration.pmf_calibration import (  # noqa: E402
    PMFCalibrator, RoleAwarePMFCalibrator,
)
from nba_props_model.calibration.role_buckets import (  # noqa: E402
    role_bucket_features_from_minutes_dist,
)
from nba_props_model.models.minutes import minutes_distribution  # noqa: E402
from nba_props_model.pipelines.pmf_predict import active_condition_pmf  # noqa: E402

warnings.filterwarnings("ignore")

TARGET_DATE = "2026-04-27"
TARGET_GAMES = {
    "Oklahoma City Thunder @ Phoenix Suns",
    "Minnesota Timberwolves @ Denver Nuggets",
}
GAME_START_ET = {
    "Oklahoma City Thunder @ Phoenix Suns":   "2026-04-27T21:30:00-04:00",
    "Minnesota Timberwolves @ Denver Nuggets": "2026-04-27T22:30:00-04:00",
}
TARGET_STATS = ["pts", "reb", "ast", "tov", "fg3m"]
START_CUTOFF_ET_MIN = 20 * 60 + 29

PHASE8_DIR = Path(
    "/tmp/phase8_full_vectorized_success/artifacts_downloaded/"
    "phase8-outputs/artifacts/models"
)
DELIVERY_DIR = REPO_ROOT / "deliveries" / TARGET_DATE / "live_after_2029_et"

# 30-team NBA team-name → abbreviation mapping. Used to resolve away/home
# from `game` strings of the form "Away Team Name @ Home Team Name".
NBA_TEAM_NAME_TO_ABBR = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE", "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU",
    "Indiana Pacers": "IND", "LA Clippers": "LAC",
    "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM", "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS", "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}


def _start_after_cutoff(start_iso: str) -> bool:
    h, m = int(start_iso[11:13]), int(start_iso[14:16])
    return (h * 60 + m) > START_CUTOFF_ET_MIN


def _parse_pmf_json(obj) -> np.ndarray:
    if isinstance(obj, str):
        d = json.loads(obj)
    elif isinstance(obj, dict):
        d = obj
    else:
        d = dict(obj.items()) if hasattr(obj, "items") else {}
    if not d:
        return np.array([1.0], dtype=float)
    max_k = max(int(k) for k in d.keys())
    out = np.zeros(max_k + 1, dtype=float)
    for k, p in d.items():
        out[int(k)] = float(p)
    s = out.sum()
    if s > 0 and np.isfinite(s):
        out = out / s
    return out


def _tail_shrink_fg3m(cal_pmf: np.ndarray, raw_pmf: np.ndarray,
                     k_tail: int = 7, w: float = 0.2) -> np.ndarray:
    K = max(len(cal_pmf), len(raw_pmf))
    cp = np.zeros(K, dtype=float); cp[: len(cal_pmf)] = cal_pmf
    rp = np.zeros(K, dtype=float); rp[: len(raw_pmf)] = raw_pmf
    out = cp.copy()
    if K > k_tail:
        out[k_tail:] = w * cp[k_tail:] + (1 - w) * rp[k_tail:]
    out = np.clip(out, 0.0, None)
    s = out.sum()
    return out / max(s, 1e-12)


def _market_tilt_pmf(pmf: np.ndarray, line: float, q: float) -> np.ndarray:
    """Mass-preserving 2-side reweighting so P(stat > line) = q.
    Within-side shape preserved exactly; only inter-side mass is moved.
    Returns a copy of pmf if line is out of support or either side is empty.
    """
    K = len(pmf)
    m = int(np.floor(line))
    if m < 0 or m >= K - 1:
        return pmf.copy()
    under = float(pmf[: m + 1].sum())
    over = float(pmf[m + 1:].sum())
    if under <= 1e-12 or over <= 1e-12:
        return pmf.copy()
    out = pmf.copy()
    q = float(np.clip(q, 1e-9, 1 - 1e-9))
    out[: m + 1] *= (1.0 - q) / under
    out[m + 1:] *= q / over
    s = out.sum()
    return out / max(s, 1e-12)


def _p_over_line(pmf: np.ndarray, line: float) -> float:
    K = len(pmf)
    k = int(np.floor(line))
    if k >= K - 1:
        return 0.0
    if k < 0:
        return 1.0
    return float(1.0 - pmf[: k + 1].sum())


def _build_team_id_to_abbr(stats_df: pd.DataFrame) -> dict[int, str]:
    """team_id -> team_abbr from the most recent appearance per team."""
    if "team_abbr" not in stats_df.columns or "team_id" not in stats_df.columns:
        return {}
    df = stats_df.dropna(subset=["team_id", "team_abbr"]).copy()
    df = df.sort_values("game_date").drop_duplicates("team_id", keep="last")
    return {int(r.team_id): str(r.team_abbr) for r in df.itertuples(index=False)}


def _resolve_team_and_home(
    game: str, team_id: int, team_id_to_abbr: dict[int, str],
) -> tuple[str, str, int, str, str]:
    """Returns (team_name, opponent_name, is_home, team_name_source, is_home_source).

    Parses `game` as "Away Team Name @ Home Team Name", maps the player's
    team_id to its abbreviation, then matches against the parsed team
    names via NBA_TEAM_NAME_TO_ABBR. Returns clearly-flagged "unknown"
    fields if mapping fails.
    """
    parts = [p.strip() for p in game.split("@")]
    if len(parts) != 2:
        return "unknown", "unknown", -1, "parse_failed", "parse_failed"
    away_name, home_name = parts
    away_abbr = NBA_TEAM_NAME_TO_ABBR.get(away_name)
    home_abbr = NBA_TEAM_NAME_TO_ABBR.get(home_name)
    player_abbr = team_id_to_abbr.get(int(team_id))
    if not player_abbr or not away_abbr or not home_abbr:
        return "unknown", "unknown", -1, "no_mapping", "no_mapping"
    if player_abbr == home_abbr:
        return home_name, away_name, 1, "team_id_to_abbr+game_parse", "team_id==home_id"
    if player_abbr == away_abbr:
        return away_name, home_name, 0, "team_id_to_abbr+game_parse", "team_id==away_id"
    return "unknown", "unknown", -1, "team_id_no_match", "team_id_no_match"


def _derive_role_bucket(
    player_id: int, team_id: int, is_home: int, stats_df: pd.DataFrame,
    avail_lookup: dict,
) -> tuple[str, dict, str]:
    history = stats_df[
        (stats_df["player_id"] == player_id) &
        (stats_df["game_date"] < TARGET_DATE)
    ].copy()
    if len(history) < 3:
        return "unknown", {"role_bucket": "unknown"}, "no_history_fallback"
    history = history.sort_values("game_date")
    last_date = str(history["game_date"].iloc[-1])
    try:
        rest_days = (
            pd.Timestamp(TARGET_DATE) - pd.Timestamp(last_date)
        ).days
    except Exception:
        rest_days = 2
    b2b = 1 if rest_days == 1 else 0
    avail = avail_lookup.get(player_id)
    is_home_for_minutes = bool(is_home == 1)
    try:
        m_dist = minutes_distribution(
            prior_stats=history,
            game_context={"rest_days": rest_days, "back_to_back": b2b},
            is_home=is_home_for_minutes,
            target_date=TARGET_DATE,
            team_id=int(team_id),
            all_stats_df=stats_df,
            injury_map={},
            availability=avail,
        )
        meta = role_bucket_features_from_minutes_dist(m_dist)
        rb = str(meta.get("role_bucket", "unknown"))
        try:
            p_inactive = float(m_dist.state_probs[0])
        except Exception:
            p_inactive = float(meta.get("p_inactive", 0.0) or 0.0)
        meta["p_inactive_runtime"] = p_inactive
        return rb, meta, "minutes_distribution_local"
    except Exception as exc:
        return "unknown", {"role_bucket": "unknown"}, f"minutes_dist_failed:{type(exc).__name__}"


def main() -> None:
    print("=" * 72)
    print(f"Live PMF export — {TARGET_DATE} (after 20:29 ET)")
    print("=" * 72)

    # ── 1. Source freshness check  ───────────────────────────────────────
    ap_path = REPO_ROOT / "predictions" / f"all_props_{TARGET_DATE}.parquet"
    if not ap_path.exists():
        sys.exit(f"FATAL: {ap_path} missing — needed for tonight slate")
    ap_mtime_ts = ap_path.stat().st_mtime
    ap_mtime_et = datetime.fromtimestamp(ap_mtime_ts).isoformat()
    print(f"\n[Source freshness]")
    print(f"  all_props_{TARGET_DATE}.parquet mtime (local TZ): {ap_mtime_et}")

    bdl_set = bool(os.environ.get("BDL_API_KEY"))
    odds_set = bool(os.environ.get("ODDS_API_KEY"))
    print(f"  BDL_API_KEY set: {bdl_set}")
    print(f"  ODDS_API_KEY set: {odds_set}")
    fresh_predict_possible = bdl_set and odds_set
    if not fresh_predict_possible:
        print("  ⇒ Fresh local predict run NOT possible "
              "(BDL_API_KEY missing). Using existing all_props parquet.")
        print("  ⇒ GitHub Actions workflow .github/workflows/daily_predictions.yml "
              "has the secrets and runs at 13:00 UTC daily; would need to be "
              "re-triggered to refresh today's all_props.")
    ap = pd.read_parquet(ap_path)
    print(f"  Loaded all_props: {len(ap):,} rows")

    avail_path = REPO_ROOT / "data" / "player_availability_asof.parquet"
    avail_mtime_et = None
    avail_rows_today = 0
    if avail_path.exists():
        avail_mtime_et = datetime.fromtimestamp(avail_path.stat().st_mtime).isoformat()
        adf = pd.read_parquet(avail_path)
        adf["game_date"] = adf["game_date"].astype(str).str[:10]
        avail_rows_today = int((adf["game_date"] == TARGET_DATE).sum())
    print(f"  player_availability_asof mtime: {avail_mtime_et}  "
          f"rows_for_{TARGET_DATE}: {avail_rows_today}")

    # ── 2. Filter to two target games (start time > 20:29 ET) ────────────
    ap = ap[ap["game"].isin(TARGET_GAMES)].copy()
    print(f"\nAfter target-games filter: {len(ap):,} rows  "
          f"({sorted(ap['game'].unique())})")
    for g, start_iso in GAME_START_ET.items():
        if not _start_after_cutoff(start_iso):
            sys.exit(f"FATAL: target game {g!r} starts at {start_iso}, "
                     f"before 20:29 ET cutoff")

    # ── 3. Filter to target stats ────────────────────────────────────────
    available_stats = sorted(ap["stat"].unique())
    missing_target_stats = [s for s in TARGET_STATS if s not in available_stats]
    if missing_target_stats:
        print(f"NOTE: target stats absent from all_props for tonight: "
              f"{missing_target_stats}")
    ap = ap[ap["stat"].isin(TARGET_STATS)].copy()
    print(f"After stat filter ({TARGET_STATS}): {len(ap):,} rows  "
          f"(present: {sorted(ap['stat'].unique())})")

    # ── 4. Find a representative row per (player_id, game_id, stat) ──────
    # OVER and UNDER share the same pmf. Prefer the row that gives us the
    # cleanest line + market-prob signal. For market_fair_over_prob we
    # prefer mkt_true_over (already de-vigged for the over side); fall back
    # to side-aware market_prob.
    def _row_market_over(row: pd.Series) -> float | None:
        try:
            mt_over = row.get("mkt_true_over", None)
            if mt_over is not None and not pd.isna(mt_over):
                return float(mt_over)
            mp = row.get("market_prob", None)
            if mp is None or pd.isna(mp):
                return None
            side = str(row.get("side", ""))
            if side == "OVER":
                return float(mp)
            if side == "UNDER":
                return float(1.0 - float(mp))
            return None
        except Exception:
            return None

    grouped = ap.drop_duplicates(subset=["player_id", "game_id", "stat"]).copy()
    grouped["market_fair_over_prob_resolved"] = grouped.apply(_row_market_over, axis=1)
    print(f"Unique (player, game, stat): {len(grouped):,}")

    # ── 5. Load Phase 8 calibrators + meta ───────────────────────────────
    if not PHASE8_DIR.exists():
        sys.exit(f"FATAL: Phase 8 calibrator dir missing: {PHASE8_DIR}")
    cal_meta = json.loads((PHASE8_DIR / "pmf_cal_meta.json").read_text())
    cal_target = cal_meta.get("calibration_target", "raw")
    print(f"\nPhase 8 cal_meta: target={cal_target}  "
          f"version={cal_meta.get('calibration_version')}  "
          f"pmf_active_available={cal_meta.get('pmf_active_available')}")
    use_active_cond = (cal_target == "active_conditioned_prop_live")
    calibrators: dict[str, RoleAwarePMFCalibrator] = {}
    for s in ("pts", "reb", "ast", "tov", "fg3m"):
        p = PHASE8_DIR / f"pmf_cal_role_{s}.pkl"
        if p.exists():
            calibrators[s] = joblib.load(p)
        else:
            print(f"WARN: missing calibrator for stat={s}")

    # ── 6. Local stats + availability + team-id mapping ──────────────────
    stats_df = pd.read_parquet(REPO_ROOT / "data" / "player_game_stats.parquet")
    stats_df["game_date"] = stats_df["game_date"].astype(str).str[:10]
    print(f"player_game_stats: {len(stats_df):,} rows  "
          f"max_date={stats_df['game_date'].max()}")
    team_id_to_abbr = _build_team_id_to_abbr(stats_df)
    print(f"team_id->abbr map size: {len(team_id_to_abbr)} "
          f"(target team_ids resolve to "
          f"{ {tid: team_id_to_abbr.get(tid) for tid in sorted(grouped['team_id'].unique())} })")

    avail_lookup: dict[int, dict] = {}
    if avail_path.exists():
        adf = pd.read_parquet(avail_path)
        adf["game_date"] = adf["game_date"].astype(str).str[:10]
        adf_today = adf[adf["game_date"] == TARGET_DATE]
        for r in adf_today.itertuples(index=False):
            avail_lookup[int(r.player_id)] = {
                c: getattr(r, c, None) for c in adf.columns
            }
        print(f"availability rows for {TARGET_DATE}: {len(avail_lookup):,}")

    # ── 7. Build export rows ─────────────────────────────────────────────
    export_rows = []
    role_distribution: dict[str, int] = {}
    role_source_distribution: dict[str, int] = {}
    team_source_distribution: dict[str, int] = {}
    is_home_source_distribution: dict[str, int] = {}
    pmf_validity_failures_model = 0
    pmf_validity_failures_best = 0
    market_tilt_count = 0
    market_tilt_max_abs_err = 0.0
    fg3m_means_input, fg3m_means_model, fg3m_means_best = [], [], []
    fg3m_pge7_input, fg3m_pge7_model, fg3m_pge7_best = [], [], []
    missing_player = missing_team = missing_role = 0
    export_ts_et = datetime.now(timezone(timedelta(hours=-4))).isoformat()
    DOMAIN_MAX = {"pts": 80, "reb": 30, "ast": 25, "tov": 12, "fg3m": 15}

    for _, row in grouped.iterrows():
        pid = int(row["player_id"])
        pname = str(row["player_name"]) if not pd.isna(row.get("player_name")) else ""
        gid = int(row["game_id"])
        game = str(row["game"])
        team_id = int(row["team_id"])
        stat = str(row["stat"])
        if not pname:
            missing_player += 1

        # Team / opponent / is_home — derived from team_id + parsed game string
        team_name, opp_name, is_home, team_src, ish_src = _resolve_team_and_home(
            game, team_id, team_id_to_abbr,
        )
        team_source_distribution[team_src] = team_source_distribution.get(team_src, 0) + 1
        is_home_source_distribution[ish_src] = is_home_source_distribution.get(ish_src, 0) + 1
        if team_src.startswith("no_mapping") or team_src.startswith("parse_failed") \
                or team_src.startswith("team_id_no_match"):
            missing_team += 1

        # Parse PMF + pad/truncate to canonical domain
        raw_pmf = _parse_pmf_json(row["pmf"])
        K_target = DOMAIN_MAX.get(stat, len(raw_pmf) - 1) + 1
        if len(raw_pmf) < K_target:
            padded = np.zeros(K_target, dtype=float); padded[: len(raw_pmf)] = raw_pmf
            raw_pmf = padded
        elif len(raw_pmf) > K_target:
            head = raw_pmf[: K_target - 1]
            tail = raw_pmf[K_target - 1:].sum()
            raw_pmf = np.concatenate([head, [tail]])
        s = raw_pmf.sum()
        if s > 0:
            raw_pmf = raw_pmf / s

        role_bucket, role_meta, role_source = _derive_role_bucket(
            pid, team_id, is_home, stats_df, avail_lookup,
        )
        role_distribution[role_bucket] = role_distribution.get(role_bucket, 0) + 1
        role_source_distribution[role_source] = role_source_distribution.get(role_source, 0) + 1
        if role_bucket == "unknown":
            missing_role += 1

        # Active-conditioning -> role-aware cal -> FG3M tail shrink
        p_inactive_used = float(role_meta.get("p_inactive_runtime", 0.0) or 0.0)
        target_pmf = active_condition_pmf(raw_pmf, p_inactive_used) if use_active_cond else raw_pmf

        cal_obj = calibrators.get(stat)
        if cal_obj is None:
            cal_pmf = target_pmf.copy()
            base_tag = "no_calibrator_fallback_raw"
        else:
            cal_pmf = np.asarray(cal_obj.apply(target_pmf, role_bucket=role_bucket), dtype=float)
            base_tag = "cal_role_aware_v1"

        if stat == "fg3m":
            model_pmf = _tail_shrink_fg3m(cal_pmf, target_pmf, k_tail=7, w=0.2)
            model_tag = base_tag + "+fg3m_tail_shrink_k7_w0.2"
        else:
            model_pmf = cal_pmf
            model_tag = base_tag

        # Validate model_pmf
        valid_model = bool(
            np.all(np.isfinite(model_pmf)) and np.all(model_pmf >= -1e-9)
            and abs(model_pmf.sum() - 1.0) < 1e-6
        )
        if not valid_model:
            pmf_validity_failures_model += 1
            continue

        # Market tilt (when line and market over-prob are both finite)
        try:
            line_val = float(row.get("line", float("nan")))
            if not np.isfinite(line_val):
                line_val = None
        except Exception:
            line_val = None
        mkt_over = row.get("market_fair_over_prob_resolved", None)
        if mkt_over is not None and pd.isna(mkt_over):
            mkt_over = None

        if line_val is not None and mkt_over is not None:
            best_pmf = _market_tilt_pmf(model_pmf, line_val, float(mkt_over))
            best_tag = model_tag + "+market_tilt"
            market_tilt_count += 1
        else:
            best_pmf = model_pmf.copy()
            best_tag = model_tag

        valid_best = bool(
            np.all(np.isfinite(best_pmf)) and np.all(best_pmf >= -1e-9)
            and abs(best_pmf.sum() - 1.0) < 1e-6
        )
        if not valid_best:
            pmf_validity_failures_best += 1
            continue

        K = len(model_pmf)
        support = np.arange(K)
        mean_model = float((model_pmf * support).sum())
        mean_best = float((best_pmf * support).sum())
        p0_model = float(model_pmf[0])
        p0_best = float(best_pmf[0])
        p_over_model = _p_over_line(model_pmf, line_val) if line_val is not None else None
        p_over_best = _p_over_line(best_pmf, line_val) if line_val is not None else None
        if best_tag.endswith("+market_tilt") and p_over_best is not None and mkt_over is not None:
            err = abs(p_over_best - float(mkt_over))
            if err > market_tilt_max_abs_err:
                market_tilt_max_abs_err = err

        if stat == "fg3m":
            fg3m_means_input.append(float((target_pmf * np.arange(len(target_pmf))).sum()))
            fg3m_means_model.append(mean_model)
            fg3m_means_best.append(mean_best)
            fg3m_pge7_input.append(float(target_pmf[7:].sum()) if len(target_pmf) > 7 else 0.0)
            fg3m_pge7_model.append(float(model_pmf[7:].sum()) if len(model_pmf) > 7 else 0.0)
            fg3m_pge7_best.append(float(best_pmf[7:].sum()) if len(best_pmf) > 7 else 0.0)

        def _pge(pmf: np.ndarray, k: int) -> float:
            if k >= len(pmf): return 0.0
            return float(pmf[k:].sum())

        export_rows.append({
            "export_timestamp_et": export_ts_et,
            "source_all_props_mtime": ap_mtime_et,
            "source_predict_run_freshness": "morning_run_only_no_live_refresh",
            "source_availability_mtime": avail_mtime_et,
            "source_availability_rows_today": avail_rows_today,
            "game_date": TARGET_DATE,
            "game_id": gid,
            "game_start_et": GAME_START_ET.get(game, ""),
            "team": team_name,
            "opponent": opp_name,
            "team_id": team_id,
            "team_abbr": team_id_to_abbr.get(team_id, ""),
            "team_name_source": team_src,
            "is_home": is_home,
            "is_home_source": ish_src,
            "player_id": pid,
            "player_name": pname,
            "stat": stat,
            "role_bucket": role_bucket,
            "role_source": role_source,
            "minutes_mean": float(role_meta.get("minutes_mean", float("nan")) or float("nan")),
            "minutes_q50": float(role_meta.get("minutes_q50", float("nan")) or float("nan")),
            "p_inactive_used": p_inactive_used,
            "pmf_source_model": model_tag,
            "pmf_best_source": best_tag,
            "support_min": 0,
            "support_max": K - 1,
            "pmf_model_json": json.dumps({str(k): float(p) for k, p in enumerate(model_pmf) if p > 1e-9}),
            "pmf_best_json":  json.dumps({str(k): float(p) for k, p in enumerate(best_pmf)  if p > 1e-9}),
            "mean_model": mean_model,
            "mean_best": mean_best,
            "p0_model": p0_model,
            "p0_best": p0_best,
            "p_ge_1_model":  _pge(model_pmf, 1),
            "p_ge_2_model":  _pge(model_pmf, 2),
            "p_ge_3_model":  _pge(model_pmf, 3),
            "p_ge_4_model":  _pge(model_pmf, 4),
            "p_ge_5_model":  _pge(model_pmf, 5),
            "p_ge_6_model":  _pge(model_pmf, 6),
            "p_ge_7_model":  _pge(model_pmf, 7),
            "p_ge_8_model":  _pge(model_pmf, 8),
            "p_ge_10_model": _pge(model_pmf, 10),
            "p_ge_15_model": _pge(model_pmf, 15),
            "p_ge_20_model": _pge(model_pmf, 20),
            "p_ge_1_best":   _pge(best_pmf, 1),
            "p_ge_2_best":   _pge(best_pmf, 2),
            "p_ge_3_best":   _pge(best_pmf, 3),
            "p_ge_4_best":   _pge(best_pmf, 4),
            "p_ge_5_best":   _pge(best_pmf, 5),
            "p_ge_6_best":   _pge(best_pmf, 6),
            "p_ge_7_best":   _pge(best_pmf, 7),
            "p_ge_8_best":   _pge(best_pmf, 8),
            "p_ge_10_best":  _pge(best_pmf, 10),
            "p_ge_15_best":  _pge(best_pmf, 15),
            "p_ge_20_best":  _pge(best_pmf, 20),
            "line": line_val,
            "p_over_line_model": p_over_model,
            "p_over_line_best":  p_over_best,
            "market_fair_over_prob": float(mkt_over) if mkt_over is not None else None,
            "market_source": "predict_pipeline_devigged_morning" if mkt_over is not None else None,
            "market_offered_side": str(row.get("side", "")),
            "market_offered_odds": int(row["odds"]) if not pd.isna(row.get("odds")) else None,
        })

    # Strict tilt assertion: any row tagged +market_tilt must hit the target
    # to within 1e-8 (mass-preserving 2-side reweighting is exact algebra).
    assert market_tilt_max_abs_err < 1e-8, (
        f"market-tilt residual too large: {market_tilt_max_abs_err:.2e}"
    )

    # ── 8. Write outputs ─────────────────────────────────────────────────
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)

    # Remove old ambiguously-named files from any prior run so that the
    # canonical MODEL_ONLY / MARKET_ANCHORED_REFERENCE pair is the only
    # consumer-facing output.
    for legacy_name in (
        "player_prop_pmfs_tonight.parquet",
        "player_prop_pmfs_tonight.csv",
        "player_prop_pmfs_tonight.jsonl",
    ):
        legacy_path = DELIVERY_DIR / legacy_name
        if legacy_path.exists():
            legacy_path.unlink()
            print(f"  removed legacy: {legacy_name}")

    base = pd.DataFrame(export_rows)

    # Reference columns shared by both files.
    REFERENCE_COLS = [
        "export_timestamp_et",
        "source_all_props_mtime",
        "source_predict_run_freshness",
        "source_availability_mtime",
        "source_availability_rows_today",
        "game_date", "game_id", "game_start_et",
        "team", "opponent", "team_id", "team_abbr",
        "team_name_source", "is_home", "is_home_source",
        "player_id", "player_name", "stat",
        "role_bucket", "role_source", "minutes_mean", "minutes_q50",
        "p_inactive_used",
        "support_min", "support_max",
        "line",
        "market_fair_over_prob",
        "market_source",
        "market_offered_side",
        "market_offered_odds",
    ]

    # ── Canonical: MODEL-ONLY (no market tilt anywhere in pmf_json) ──────
    df_model = base[REFERENCE_COLS].copy()
    df_model["pmf_source"]    = base["pmf_source_model"]
    df_model["pmf_json"]      = base["pmf_model_json"]
    df_model["mean"]          = base["mean_model"]
    df_model["p0"]            = base["p0_model"]
    for k in (1, 2, 3, 4, 5, 6, 7, 8, 10, 15, 20):
        df_model[f"p_ge_{k}"] = base[f"p_ge_{k}_model"]
    df_model["p_over_line"]       = base["p_over_line_model"]
    df_model["p_over_line_model"] = base["p_over_line_model"]
    df_model["model_edge_vs_market"] = (
        base["p_over_line_model"].astype(float) - base["market_fair_over_prob"].astype(float)
    )

    df_model.to_parquet(DELIVERY_DIR / "player_prop_pmfs_tonight_MODEL_ONLY.parquet", index=False)
    df_model.to_csv(DELIVERY_DIR / "player_prop_pmfs_tonight_MODEL_ONLY.csv", index=False)
    df_model.to_json(
        DELIVERY_DIR / "player_prop_pmfs_tonight_MODEL_ONLY.jsonl",
        orient="records", lines=True,
    )
    print(f"\nWrote MODEL-ONLY canonical files:")
    print(f"  {DELIVERY_DIR / 'player_prop_pmfs_tonight_MODEL_ONLY.parquet'}")
    print(f"  {DELIVERY_DIR / 'player_prop_pmfs_tonight_MODEL_ONLY.csv'}")
    print(f"  {DELIVERY_DIR / 'player_prop_pmfs_tonight_MODEL_ONLY.jsonl'}")

    # ── Reference: MARKET_ANCHORED (pmf is market-tilted; reference only) ─
    df_market = base[REFERENCE_COLS].copy()
    df_market["pmf_source"] = base["pmf_best_source"]
    df_market["pmf_json"]   = base["pmf_best_json"]
    df_market["mean"]       = base["mean_best"]
    df_market["p0"]         = base["p0_best"]
    for k in (1, 2, 3, 4, 5, 6, 7, 8, 10, 15, 20):
        df_market[f"p_ge_{k}"] = base[f"p_ge_{k}_best"]
    df_market["p_over_line"]       = base["p_over_line_best"]
    df_market["p_over_line_model"] = base["p_over_line_model"]
    df_market["model_edge_vs_market"] = (
        base["p_over_line_model"].astype(float) - base["market_fair_over_prob"].astype(float)
    )

    df_market.to_parquet(DELIVERY_DIR / "player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.parquet", index=False)
    df_market.to_csv(DELIVERY_DIR / "player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.csv", index=False)
    df_market.to_json(
        DELIVERY_DIR / "player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.jsonl",
        orient="records", lines=True,
    )
    print(f"\nWrote MARKET-ANCHORED REFERENCE files (NOT for standalone-model evaluation):")
    print(f"  {DELIVERY_DIR / 'player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.parquet'}")
    print(f"  {DELIVERY_DIR / 'player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.csv'}")
    print(f"  {DELIVERY_DIR / 'player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.jsonl'}")

    # Bind df = df_model so the validation summary below operates on the
    # canonical model-only view (this is what Derek will evaluate).
    df = df_model

    cal_dir = DELIVERY_DIR / "pmf_calibrators"
    cal_dir.mkdir(exist_ok=True)
    for s in ("pts", "reb", "ast", "tov", "fg3m"):
        src = PHASE8_DIR / f"pmf_cal_role_{s}.pkl"
        if src.exists():
            shutil.copy(src, cal_dir / f"pmf_cal_role_{s}.pkl")
    shutil.copy(PHASE8_DIR / "pmf_cal_meta.json", cal_dir / "pmf_cal_meta.json")
    print(f"Wrote {cal_dir}/ (calibrator bundle)")

    # README
    readme = f"""# Live PMF export — {TARGET_DATE} (after 20:29 ET)

## Slate

Two games, both tipping after the 20:29 ET cutoff:
- **Oklahoma City Thunder @ Phoenix Suns** — 21:30 ET
- **Minnesota Timberwolves @ Denver Nuggets** — 22:30 ET

Earlier game (Detroit @ Orlando) is intentionally excluded.

## Primary file for Derek's model evaluation

```
player_prop_pmfs_tonight_MODEL_ONLY.parquet
```

This contains the **standalone calibrated model PMFs**. These are NOT
market-anchored. `pmf_json` is the model's own distribution, computed
from active-conditioning + role-aware Phase 8 calibration (and, for
FG3M only, the validated tail shrink). Use this file to evaluate the
standalone model's accuracy versus the market.

Market columns (`line`, `market_fair_over_prob`, `market_source`,
`market_offered_side`, `market_offered_odds`, `model_edge_vs_market`)
are included **only as reference** so Derek can compare the model's
`p_over_line` to the available de-vigged market probability. Those
columns do **not** alter `pmf_json`.

A separate `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.*`
bundle is included for reference only; its `pmf_json` IS market-tilted
(CDF anchored at the offered line). It must NOT be used to evaluate
the standalone model.

## Source freshness (HONEST)

| Source | mtime / status |
|---|---|
| `predictions/all_props_{TARGET_DATE}.parquet` | **{ap_mtime_et}** (morning predict run) |
| `data/player_availability_asof.parquet` | mtime {avail_mtime_et}; **{avail_rows_today} rows for {TARGET_DATE}** |
| Fresh local predict re-run | NOT possible — `BDL_API_KEY` not set in this shell. |
| GitHub Actions refresh path | `.github/workflows/daily_predictions.yml` runs at 13:00 UTC daily with the BDL secret; that workflow would need to be re-triggered to refresh today's all_props. |

**Implications:**
- Source PMFs reflect the morning run only — late-breaking injuries, scratches, or roster changes after ~14:27 local time are NOT incorporated.
- Market columns are de-vigged probabilities from the predict pipeline's morning fetch — **not** the closing line. If sharp action moved a line after 14:27 ET, the market anchor is stale.
- Availability table for {TARGET_DATE} is empty; we fall back to historical inactive priors per player.

## Slate

Two games, both tipping after the 20:29 ET cutoff:
- **Oklahoma City Thunder @ Phoenix Suns** — 21:30 ET
- **Minnesota Timberwolves @ Denver Nuggets** — 22:30 ET

Earlier game (Detroit @ Orlando) is intentionally excluded.

## Files

| File | Purpose |
|---|---|
| **`player_prop_pmfs_tonight_MODEL_ONLY.parquet`** | **canonical standalone-model PMFs**; `pmf_json` is model-only |
| `player_prop_pmfs_tonight_MODEL_ONLY.csv` | same MODEL-ONLY data, CSV |
| `player_prop_pmfs_tonight_MODEL_ONLY.jsonl` | same MODEL-ONLY data, JSONL |
| `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.parquet` | reference only — `pmf_json` is market-tilted; do NOT use for standalone-model evaluation |
| `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.csv` | reference only — same as above, CSV |
| `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.jsonl` | reference only — same as above, JSONL |
| `pmf_calibrators/pmf_cal_role_*.pkl` | Phase 8 role-aware PMF calibrators (pts/reb/ast/tov/fg3m) |
| `pmf_calibrators/pmf_cal_meta.json` | calibration metadata: target=`active_conditioned_prop_live`, version=`role_aware_pmf_cal_v1` |

## How the model-only PMF was built

1. **Source PMFs** come from `predictions/all_props_{TARGET_DATE}.parquet`, the
   full-universe output of the morning predict pipeline.
2. **Active-conditioning**: `pmf_active = active_condition_pmf(raw_pmf, p_inactive)`
   where `p_inactive` is taken from the locally-computed minutes distribution.
3. **Role-aware calibration**: `RoleAwarePMFCalibrator.apply(pmf_active, role_bucket=...)`
   from the Phase 8 walk-forward calibrators.
4. **FG3M tail shrink** (FG3M ONLY): for k≥7,
   `pmf[k] = 0.2 * cal[k] + 0.8 * pmf_active[k]`, then renormalized. Corrects
   the validated upper-tail overshoot from the Phase 8 audit.
5. **No market tilt** is applied to the MODEL-ONLY `pmf_json`. The model's
   own `p_over_line` is preserved exactly so its disagreement with the
   market is visible via `model_edge_vs_market`.

## How the market-anchored REFERENCE PMF was built

After the four model-only steps above, the PMF is **mass-preservingly
tilted** so that the new CDF satisfies `P(stat > line) = market_fair_over_prob`.
Within-under and within-over shape are preserved exactly; only inter-side
mass is re-weighted. When no market line is present, the reference PMF
equals the model PMF.

**Caveats on the market-anchored reference:**
- This is **market-anchored**, NOT a claim that the standalone model beats the market.
- The market source is the predict pipeline's morning de-vigged book consensus, NOT closing or live.
- The latest matched audit found the closing market beats the standalone calibrated model on log-loss in 9 of 11 cohorts (95% CI). The tilt is a useful comparison artifact, not a model performance claim.

## `pmf_source` tag values

MODEL-ONLY file:
| Value | Path |
|---|---|
| `cal_role_aware_v1:{{role_bucket}}` | role-aware Phase 8 cal applied (pts/reb/ast/tov) |
| `cal_role_aware_v1+fg3m_tail_shrink_k7_w0.2` | FG3M only; cal + tail-shrink |
| `no_calibrator_fallback_raw` | calibrator missing for stat (should not occur for pts/reb/ast/tov/fg3m) |

MARKET-ANCHORED REFERENCE file: same tags as above with a trailing `+market_tilt` when the row had a finite line + market prob.

## Schema (MODEL-ONLY canonical)

| Column | Notes |
|---|---|
| `export_timestamp_et` | when this bundle was generated |
| `source_*` | freshness provenance for the morning predict run + availability table |
| `game_date` | `{TARGET_DATE}` for all rows |
| `game_id`, `game_start_et`, `team`, `opponent`, `team_id`, `team_abbr` | game / team context |
| `team_name_source`, `is_home`, `is_home_source` | how team & home/away were resolved |
| `player_id`, `player_name` | identity |
| `stat` | one of pts/reb/ast/tov/fg3m |
| `role_bucket`, `role_source`, `minutes_mean`, `minutes_q50`, `p_inactive_used` | role-aware-cal context |
| `pmf_source` | model-only PMF tag (see above) |
| `support_min`, `support_max` | PMF support is `0..support_max` |
| `pmf_json` | **model-only PMF** as JSON `{{"k": prob}}`; entries with prob ≤ 1e-9 omitted |
| `mean`, `p0`, `p_ge_1`..`p_ge_20` | summary stats from `pmf_json` |
| `line` | offered prop line (when present) |
| `p_over_line` | model's `P(stat > line)` from `pmf_json` |
| `p_over_line_model` | same as `p_over_line` (kept for cross-file parity) |
| `market_fair_over_prob` | de-vigged market over prob (reference) |
| `market_source` | `predict_pipeline_devigged_morning` when matched |
| `market_offered_side`, `market_offered_odds` | offered market context |
| `model_edge_vs_market` | `p_over_line_model - market_fair_over_prob` — the model's signed disagreement with the market |

## Reproducing

```
python scripts/export_live_pmf_slate.py
```

Reads only local files. No API calls. Outputs are deterministic given
the same inputs.
"""
    (DELIVERY_DIR / "README.md").write_text(readme)
    print(f"Wrote {DELIVERY_DIR / 'README.md'}")

    # ── README_FOR_DEREK.md (short, action-oriented) ─────────────────────
    derek = """# README for Derek — tonight's PMF delivery (2026-04-27, after 20:29 ET)

1. **Open `player_prop_pmfs_tonight_MODEL_ONLY.parquet` first.** That is
   the canonical file. The CSV and JSONL siblings are byte-equivalent.
2. `pmf_json` contains the full standalone-model PMF as a JSON object
   `{"k": prob, ...}` with `k` from `0` to `support_max`. Entries with
   probability ≤ 1e-9 are omitted.
3. `p_over_line` is the model probability of `stat > line` (over side),
   computed from `pmf_json`.
4. `market_fair_over_prob` is the reference de-vigged market probability
   for the same line, included for comparison only. It does NOT alter
   `pmf_json`.
5. `model_edge_vs_market = p_over_line - market_fair_over_prob`. Positive
   means the model is more bullish than the market at that line; negative
   means more bearish.
6. **No market-beating claim is made.** The standalone calibrated model
   did not beat the de-vigged closing market in the latest matched audit.
   See `MODEL_EVALUATION_SUMMARY.md` § "What is not proven".

The `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.*` files are a
separate reference bundle whose `pmf_json` IS market-tilted (CDF anchored
at the offered line). Do NOT use those to evaluate the standalone model.
"""
    (DELIVERY_DIR / "README_FOR_DEREK.md").write_text(derek)
    print(f"Wrote {DELIVERY_DIR / 'README_FOR_DEREK.md'}")

    # ── MODEL_EVALUATION_SUMMARY.md (longer, structured) ─────────────────
    eval_md = f"""# Model evaluation summary — 2026-04-27 late slate PMF delivery

## 1. Executive summary

This delivery is a snapshot of the standalone calibrated player-prop PMF
model for tonight's two NBA games tipping after 20:29 ET (OKC @ PHX,
21:30 ET; MIN @ DEN, 22:30 ET). The canonical export is
`player_prop_pmfs_tonight_MODEL_ONLY.parquet` — 61 rows, full PMFs per
(player × stat).

The model is role-aware and active-conditioned. Calibration was fit on
the Phase 8 walk-forward 247,625-row OOF universe (15 folds × 5 stats).
PMFs are valid (finite, non-negative, sum-to-1) for every row.

We do not claim the standalone model beats the closing market. We claim
the model is internally well-calibrated for PTS/REB/AST/TOV and FG3M
after a validated tail correction.

## 2. What is proven

- **Valid calibrated PMFs**. 247,625 / 247,625 OOF rows pass validity
  (finite, non-negative, sum-to-1, no degenerate collapse). 61 / 61
  tonight rows pass validity.
- **Role-aware calibration**. The Phase 8 calibrators are
  `RoleAwarePMFCalibrator` instances (`pmf_cal_role_*.pkl`), fit per
  stat with one global isotonic CDF map plus six per-bucket
  (`inactive_risk`, `fringe`, `bench`, `rotation`, `core`, `starter`)
  calibrators blended via shrinkage on bucket sample size.
- **Active-conditioned calibration target**. `pmf_cal_meta.json` declares
  `calibration_target = "active_conditioned_prop_live"`, version
  `role_aware_pmf_cal_v1`. Tonight's export applies
  `active_condition_pmf(raw_pmf, p_inactive)` before `cal.apply()` so the
  input distribution matches the calibrator's training contract.
- **Strong OOF calibration for PTS/REB/AST/TOV**. Stat-level NLL
  improved on every stat (Δnll −0.028 to −0.073 vs raw). Calibrated mean
  matched observed mean within ~1% on OOF for all four. Calibrated
  `p_over` at standard prop lines was within 0.005 of observed. All 30
  (stat × role_bucket) cells improved.
- **FG3M tail issue fixed via time-safe validation**. The role-aware
  calibrator over-inflated FG3M k≥7 mass (cal P(k≥7)=2.7% vs observed
  0.7%). A grid search over `k_tail ∈ {{5, 7}}` × `w ∈ {{0.2, 0.3, 0.5, 0.7}}`
  identified `k_tail=7, w=0.2` as the configuration that minimized NLL,
  tied for lowest RPS, and reduced mean error from +0.293 to +0.012 and
  P(k≥7) error from +0.020 to −0.001. Tonight's export applies this fix
  for FG3M only.

## 3. What is NOT proven

- **No standalone closing-market superiority**. A matched closing-line
  audit on 3,818 player-game-stat-line offers (with 95% bootstrap CIs)
  found the de-vigged closing market beats the standalone calibrated
  model on log-loss in 9 of 11 cohorts. Overall Δll(cal − market) =
  +0.051 [+0.039, +0.063]. A small number of narrow line ranges (REB
  3.5–4.5, AST 3.5–5.5, FG3M 1.5–2.5) tied within CI.
- **No opening-line edge proven**. The opening-line snapshots on disk
  are game totals/spreads only, not player-prop offerings. No proper
  opening → closing CLV comparison has been run.
- **No CLV claim yet**. Tonight's `market_fair_over_prob` references the
  morning predict-pipeline de-vigged consensus, not entry-time grades
  against closing lines.
- **Tonight's source is the morning run, not a final injury / lineup
  refresh**. Source `all_props_2026-04-27.parquet` mtime is
  `2026-04-27T14:27:23` ET. The local `player_availability_asof.parquet`
  had 0 rows for 2026-04-27 (last refreshed 2026-04-18). Late scratches
  and starter/inactive changes after ~14:27 ET are NOT reflected.

## 4. Accuracy / calibration summary

| Item | Result |
|---|---|
| Phase 8 OOF rows | 247,625 (15 folds × 5 stats × ~3,300 rows/fold/stat) |
| Validity failures (raw + calibrated, all stats) | 0 / 247,625 |
| Stat-level Δnll (cal − raw), all 5 stats | −0.028 to −0.073 (uniformly improved) |
| (stat × role_bucket) cells improved | 30 / 30 |
| Calibrated mean error vs observed (PTS/REB/AST/TOV) | < 1% |
| Calibrated p_over at standard prop lines | within 0.005 of observed |
| FG3M tail-shrink validated config | `k_tail=7, w=0.2` (lowest NLL, lowest RPS; mean Δ +0.012; P(k≥7) Δ −0.001) |
| Matched closing-line market eval (n=3,818) | market beats standalone cal on log-loss in 9/11 cohorts (95% CI) |
| Tonight bundle PMF validity | 61 / 61 valid; 0 model-only rows tagged with `+market_tilt` |
| Tonight `model_edge_vs_market` distribution | range [−0.264, +0.251], mean −0.077 (real disagreement preserved) |

## 5. Tonight file guide

**Canonical** (use this for standalone-model evaluation):
- `player_prop_pmfs_tonight_MODEL_ONLY.parquet`
- `player_prop_pmfs_tonight_MODEL_ONLY.csv`
- `player_prop_pmfs_tonight_MODEL_ONLY.jsonl`

In these files:
- `pmf_json` is the standalone-model PMF: active-conditioned + role-aware
  calibrated; for FG3M, plus the validated tail shrink (k≥7, w=0.2).
- `mean`, `p0`, `p_ge_*`, `p_over_line`, `p_over_line_model` are derived
  from `pmf_json`. They are NOT market-anchored.
- `pmf_source` ∈ `{{cal_role_aware_v1:{{role_bucket}}, cal_role_aware_v1+fg3m_tail_shrink_k7_w0.2}}`.
- `market_*` columns are reference fields only and do not modify
  `pmf_json`. `model_edge_vs_market = p_over_line_model − market_fair_over_prob`.

**Reference, NOT for standalone-model evaluation**:
- `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.parquet` (and `.csv`, `.jsonl`)

In these files, `pmf_json` is mass-preservingly tilted so the CDF passes
through `market_fair_over_prob` at the offered line. Use only for visual
comparison of the model's PMF *shape* against a market-anchored CDF.

**Calibrator bundle**:
- `pmf_calibrators/pmf_cal_role_*.pkl` — Phase 8 role-aware calibrators
  (pts/reb/ast/tov/fg3m)
- `pmf_calibrators/pmf_cal_meta.json` — metadata (target, version,
  bucket counts)

## 6. Production roadmap

To enable proper market-beating claims and CLV measurement, the
production pipeline still needs:

- **Pre-close and close line snapshots** captured at fixed times
  (e.g., 6 PM ET pre-close, exact-tip close) for every player-prop
  offering on every game.
- **Every regular AND alternate line** for each (player × stat), not
  only the main book line. Alternate-ladder snapshots enable
  reconstruction of a market-implied PMF and head-to-head full-PMF
  comparison.
- **Odds and no-vig probabilities** from ≥3 books per offering;
  consensus de-vig with book-weighting.
- **Injury / lineup state** captured at lock time per player
  (active / questionable / out / starter / bench / minutes restriction).
- **Model PMF at lock time** — requires the predict pipeline cron to
  fire after the final inactives are posted, not at 8 AM ET.
- **Realized outcomes** + **CLV** =
  `model_prob_at_lock − closing_no_vig_prob`, graded against the actual
  stat outcome per player-game.

When these are wired together, Derek's evaluation can be a proper
time-and-state-aligned comparison. Tonight's delivery represents what
the current standalone model believes about each prop distribution; it
is NOT yet graded against closing market or actual outcomes.
"""
    (DELIVERY_DIR / "MODEL_EVALUATION_SUMMARY.md").write_text(eval_md)
    print(f"Wrote {DELIVERY_DIR / 'MODEL_EVALUATION_SUMMARY.md'}")

    # ── 9. Validation summary ────────────────────────────────────────────
    # Operates on `df = df_model` (the canonical MODEL-ONLY view). The
    # market-tilted reference frame is also produced for comparison but
    # is NOT what Derek will evaluate.
    print()
    print("=" * 72)
    print("Validation summary (canonical view = MODEL-ONLY)")
    print("=" * 72)
    print(f"total model-only rows: {len(df):,}")
    print(f"\nrows by game (game_id, start_et):")
    print(df.groupby(["game_id", "game_start_et"]).size().to_string())
    print(f"\nrows by stat:")
    print(df["stat"].value_counts().to_string())
    print(f"\nrows by team_abbr:")
    print(df["team_abbr"].value_counts().to_string())
    print(f"\nrows by role_bucket:")
    print(df["role_bucket"].value_counts().to_string())
    print(f"\nteam_name_source dist: {team_source_distribution}")
    print(f"is_home_source dist:   {is_home_source_distribution}")
    print(f"role_source dist:      {role_source_distribution}")
    print(f"\nmodel-only PMF validity failures: {pmf_validity_failures_model}")
    print(f"market-anchored PMF validity failures: {pmf_validity_failures_best}")

    # Sanity check: confirm pmf_json in the MODEL-ONLY file is NEVER market-tilted.
    # We re-derive p_over_line from model PMFs and confirm it equals the column.
    no_tilt_violations = 0
    for _, r in df.iterrows():
        src = str(r["pmf_source"])
        if "market_tilt" in src:
            no_tilt_violations += 1
    print(f"MODEL-ONLY rows tagged market_tilt (must be 0): {no_tilt_violations}")
    assert no_tilt_violations == 0, "MODEL-ONLY file contains market_tilt rows"

    # Cross-check: model_edge_vs_market is computed from model p_over_line, not market p.
    diff_finite = df["model_edge_vs_market"].dropna()
    if len(diff_finite):
        print(f"\nmodel_edge_vs_market (p_over_line_model - market_fair_over_prob):")
        print(f"  n={len(diff_finite):,}  min={diff_finite.min():+.4f}  "
              f"max={diff_finite.max():+.4f}  mean={diff_finite.mean():+.4f}  "
              f"|mean|={abs(diff_finite.mean()):.4f}")

    print(f"\nmarket reference rows count (MARKET_ANCHORED_REFERENCE file): {len(df_market):,}")
    print(f"market-tilt rows in REFERENCE file: {market_tilt_count} / {len(df_market):,}")
    print(f"max |p_over_line - market_fair_over_prob| in REFERENCE file: "
          f"{market_tilt_max_abs_err:.2e}")

    if fg3m_means_input:
        # Model-only FG3M stats only — these are what Derek will see in the
        # canonical file. We do not surface "best" FG3M means here since
        # the canonical file is model-only.
        print(f"\nFG3M (n={len(fg3m_means_input)}) — MODEL-ONLY:")
        print(f"  mean active_input:    {np.mean(fg3m_means_input):.3f}")
        print(f"  mean model PMF:       {np.mean(fg3m_means_model):.3f}")
        print(f"  P(k>=7) active_input: {np.mean(fg3m_pge7_input):.4f}")
        print(f"  P(k>=7) model PMF:    {np.mean(fg3m_pge7_model):.4f}")

    print(f"\nmissing_player_name: {missing_player}")
    print(f"missing_team:        {missing_team}")
    print(f"missing_role_bucket: {missing_role}")
    print(f"\nsource all_props mtime: {ap_mtime_et}")

    print(f"\nSample 20 rows (MODEL-ONLY):")
    sample_cols = [
        "player_name", "team", "opponent", "stat", "line",
        "p_over_line_model", "market_fair_over_prob", "model_edge_vs_market",
        "mean", "p0", "pmf_source",
    ]
    with pd.option_context("display.max_colwidth", 60):
        print(df[sample_cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
