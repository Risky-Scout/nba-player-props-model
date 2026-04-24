"""Rate-bias decomposition for PTS/REB/AST on fold_1 (READ-ONLY).

Decision pass: determine whether the rate bias observed in fold_1 is a
globally uniform shift or is segmented by context. Outcome classification:
  - GLOBAL_SHARED_RATE_BIAS  → proceed to bounded OOF PMF correction pass
  - SEGMENTED_RATE_BIAS      → do not universalize; inspect per-context
  - MIXED                    → narrow PTS-only correction pass + per-stat
                                 context investigation for REB/AST

Operates on the audited keyed row set only. No retraining, no model edits,
no workflow changes. Uses existing public helpers verbatim:
  - nba_props_model.models.minutes.minutes_distribution
  - nba_props_model.models.minutes.MinutesDistribution (.mean())

CLI:
    python scripts/diagnostics/rate_bias_decomposition.py \\
        --fold-oof artifacts/fold_1.parquet \\
        --stats-df data/player_game_stats.parquet \\
        --features-df data/training_table.parquet \\
        --minutes-models-dir artifacts/models \\
        --closing-lines-dir artifacts/graded \\
        --output-dir artifacts/diagnostics/fold_1_rate_bias \\
        --stats pts reb ast
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


SHIP_STATS_DEFAULT = ("pts", "reb", "ast")
MINUTES_BUCKETS = (
    ("0-11", 0, 12), ("12-17", 12, 18), ("18-23", 18, 24),
    ("24-29", 24, 30), ("30-35", 30, 36), ("36+", 36, 100),
)
MAJOR_BUCKET_MIN_ROWS = 100
GLOBAL_WITHIN_PP = 3.0
SEGMENTED_DEVIATION_PP = 5.0
GLOBAL_COVERAGE_THRESHOLD = 0.80


# ── utilities ──────────────────────────────────────────────────────────────


def _die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _require_path(p: Path, label: str) -> None:
    if not p.exists():
        _die(f"{label} not found: {p}")


# ── preflight ──────────────────────────────────────────────────────────────


FOLD_OOF_REQUIRED = ["player_id", "game_id", "game_date", "stat", "pmf", "outcome"]
STATS_REQUIRED = [
    "player_id", "game_id", "game_date", "min", "pts", "reb", "ast",
    "home_team_id", "team_id",
]
FEATURES_REQUIRED = [
    "player_id", "game_id", "game_date",
    "is_home", "back_to_back", "mp_starter_prob", "rest_days", "mp_mean_last10",
]


def _preflight(
    fold_oof_path: Path,
    stats_df_path: Path,
    features_df_path: Path,
    minutes_models_dir: Path,
) -> dict:
    """Check files + minimum required columns + dynamic minutes-feature
    list. Returns a preflight record; fails loud on any missing input."""
    _require_path(fold_oof_path, "--fold-oof")
    _require_path(stats_df_path, "--stats-df")
    _require_path(features_df_path, "--features-df")
    _require_path(minutes_models_dir, "--minutes-models-dir")

    fold_schema = pd.read_parquet(fold_oof_path).columns.tolist()
    stats_schema = pd.read_parquet(stats_df_path).columns.tolist()
    features_schema = pd.read_parquet(features_df_path).columns.tolist()

    missing_fold = [c for c in FOLD_OOF_REQUIRED if c not in fold_schema]
    missing_stats = [c for c in STATS_REQUIRED if c not in stats_schema]
    missing_features_min = [c for c in FEATURES_REQUIRED if c not in features_schema]
    hard_missing = {
        "fold_oof": missing_fold,
        "stats_df": missing_stats,
        "features_df_minimum": missing_features_min,
    }
    if any(hard_missing.values()):
        _die(
            "preflight failed — missing minimum required columns: "
            + json.dumps(hard_missing)
        )

    feat_pkl = minutes_models_dir / "minutes_state_aware_features.pkl"
    feat_meta = minutes_models_dir / "minutes_state_aware_meta.json"
    minutes_feature_source = None
    minutes_feature_list: list[str] = []
    if feat_pkl.exists():
        try:
            loaded = joblib.load(feat_pkl)
            if isinstance(loaded, (list, tuple)):
                minutes_feature_list = [str(x) for x in loaded]
                minutes_feature_source = str(feat_pkl)
        except Exception as e:
            print(
                f"WARN: failed to load minutes feature pkl {feat_pkl}: {e}; "
                "trying JSON meta fallback"
            )
    if not minutes_feature_list and feat_meta.exists():
        try:
            meta = json.loads(feat_meta.read_text())
            feats = meta.get("features")
            if isinstance(feats, list):
                minutes_feature_list = [str(x) for x in feats]
                minutes_feature_source = str(feat_meta)
        except Exception as e:
            print(f"WARN: failed to read minutes feature meta {feat_meta}: {e}")

    missing_minutes_feats: list[str] = []
    if minutes_feature_list:
        missing_minutes_feats = [
            f for f in minutes_feature_list if f not in features_schema
        ]
        if missing_minutes_feats:
            _die(
                "preflight failed — features_df is missing minutes model "
                f"features (source={minutes_feature_source}, "
                f"count={len(missing_minutes_feats)}): "
                f"{missing_minutes_feats}"
            )
    else:
        print(
            "WARN: no minutes feature list available "
            "(minutes_state_aware_features.pkl and "
            "minutes_state_aware_meta.json both absent or unreadable); "
            "falling back to minimum-column check only"
        )

    return {
        "fold_oof_columns_ok": True,
        "stats_df_columns_ok": True,
        "features_df_minimum_columns_ok": True,
        "minutes_feature_source": minutes_feature_source,
        "minutes_feature_count": len(minutes_feature_list),
        "minutes_features_missing_count": len(missing_minutes_feats),
    }


def _print_preflight(p: dict) -> None:
    print("\n=== PREFLIGHT ===")
    print(f"  fold_oof columns OK                 = {p['fold_oof_columns_ok']}")
    print(f"  stats_df columns OK                 = {p['stats_df_columns_ok']}")
    print(f"  features_df minimum columns OK      = {p['features_df_minimum_columns_ok']}")
    print(f"  minutes feature source              = {p['minutes_feature_source']}")
    print(f"  minutes feature count               = {p['minutes_feature_count']}")
    print(f"  minutes features missing            = {p['minutes_features_missing_count']}")


# ── loaders (post-preflight) ───────────────────────────────────────────────


def _load_fold_oof(path: Path, stats: tuple[str, ...]) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df = df.copy()
    df["stat"] = df["stat"].astype(str).str.lower()
    df["game_date"] = df["game_date"].astype(str).str.slice(0, 10)
    df["player_id"] = df["player_id"].astype(int)
    df["game_id"] = df["game_id"].astype(int)
    df["outcome"] = df["outcome"].astype(int)
    df = df[df["stat"].isin([s.lower() for s in stats])].reset_index(drop=True)
    return df


def _load_stats(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path, columns=STATS_REQUIRED)
    df["game_date"] = df["game_date"].astype(str).str.slice(0, 10)
    df["player_id"] = df["player_id"].astype(int)
    df["game_id"] = df["game_id"].astype(int)
    df["min"] = pd.to_numeric(df["min"], errors="coerce").fillna(0.0)
    for c in ("pts", "reb", "ast"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["home_team_id"] = pd.to_numeric(df["home_team_id"], errors="coerce").fillna(0).astype(int)
    df["team_id"] = pd.to_numeric(df["team_id"], errors="coerce").fillna(0).astype(int)
    return df


def _load_features(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "stat" not in df.columns:
        _die("features_df missing 'stat' column")
    df = df[df["stat"].astype(str).str.lower() == "pts"].copy()
    df["player_id"] = df["player_id"].astype(int)
    df["game_id"] = df["game_id"].astype(int)
    df["game_date"] = df["game_date"].astype(str).str.slice(0, 10)
    for c in ("is_home", "back_to_back", "rest_days"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    for c in ("mp_starter_prob", "mp_mean_last10"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _load_availability_lookup() -> dict:
    from nba_props_model.paths import DATA_DIR
    p = DATA_DIR / "player_availability_asof.parquet"
    if not p.exists():
        print(
            f"WARN: {p} missing; availability will be passed as None "
            f"(matches phase-8 behavior when artifact absent)."
        )
        return {}
    df = pd.read_parquet(p)
    df["game_date"] = df["game_date"].astype(str).str.slice(0, 10)
    cols = [c for c in df.columns if c not in ("player_id", "game_date", "team_id")]
    out: dict = {}
    for r in df.itertuples(index=False):
        out[(int(r.player_id), str(r.game_date))] = {
            c: getattr(r, c, None) for c in cols
        }
    return out


# ── match audit ────────────────────────────────────────────────────────────


def _match_audit(
    universe: pd.DataFrame,
    stats_df: pd.DataFrame,
    features_df: pd.DataFrame,
    stats_by_player: dict[int, pd.DataFrame],
) -> dict:
    n_universe = int(len(universe))
    stats_keys = set(
        (int(p), int(g))
        for p, g in zip(stats_df["player_id"], stats_df["game_id"])
    )
    feat_keys = set(
        (int(p), int(g))
        for p, g in zip(features_df["player_id"], features_df["game_id"])
    )
    rows_no_box: list[tuple] = []
    rows_no_features: list[tuple] = []
    rows_no_prior_history: list[tuple] = []
    rows_other: list[tuple] = []
    auditable: list[tuple] = []
    for u in universe.itertuples(index=False):
        pid = int(u.player_id); gid = int(u.game_id); gdate = str(u.game_date)
        key = (pid, gid)
        has_box = key in stats_keys
        has_feat = key in feat_keys
        hist = stats_by_player.get(pid)
        has_prior = bool(
            hist is not None and len(hist[hist["game_date"] < gdate]) >= 1
        )
        if has_box and has_feat and has_prior:
            auditable.append((pid, gid, gdate))
            continue
        if not has_box:
            rows_no_box.append((pid, gid, gdate))
        elif not has_feat:
            rows_no_features.append((pid, gid, gdate))
        elif not has_prior:
            rows_no_prior_history.append((pid, gid, gdate))
        else:
            rows_other.append((pid, gid, gdate))
    audit = {
        "n_fold_universe": n_universe,
        "n_matched_stats": int(sum(
            1 for u in universe.itertuples(index=False)
            if (int(u.player_id), int(u.game_id)) in stats_keys
        )),
        "n_matched_features": int(sum(
            1 for u in universe.itertuples(index=False)
            if (int(u.player_id), int(u.game_id)) in feat_keys
        )),
        "n_fully_auditable_rows": int(len(auditable)),
        "n_dropped_rows": int(n_universe - len(auditable)),
        "dropped_reasons": {
            "no_box_score_row": int(len(rows_no_box)),
            "no_feature_row": int(len(rows_no_features)),
            "no_strictly_prior_history": int(len(rows_no_prior_history)),
            "other": int(len(rows_other)),
        },
        "dropped_samples": {
            "no_box_score_row": rows_no_box[:5],
            "no_feature_row": rows_no_features[:5],
            "no_strictly_prior_history": rows_no_prior_history[:5],
            "other": rows_other[:5],
        },
    }
    return {"audit": audit, "auditable_keys": set((p, g) for p, g, _ in auditable)}


def _print_match_audit(audit: dict) -> None:
    print("\n=== MATCH AUDIT ===")
    print(f"  n_fold_universe           = {audit['n_fold_universe']:,}")
    print(f"  n_matched_stats           = {audit['n_matched_stats']:,}")
    print(f"  n_matched_features        = {audit['n_matched_features']:,}")
    print(f"  n_fully_auditable_rows    = {audit['n_fully_auditable_rows']:,}")
    print(f"  n_dropped_rows            = {audit['n_dropped_rows']:,}")
    print("  dropped_reasons:")
    for k, v in audit["dropped_reasons"].items():
        print(f"    {k:<28}  {v:,}")


# ── minutes reconstruction ────────────────────────────────────────────────


def _reconstruct_inputs(
    pid: int, gid: int, gdate: str,
    stats_df: pd.DataFrame,
    stats_by_player: dict[int, pd.DataFrame],
    avail_lookup: dict,
) -> dict:
    hist = stats_by_player.get(pid)
    if hist is None:
        _die(f"no history rows in stats_df for player_id={pid}")
    prior = hist[hist["game_date"] < gdate]
    if len(prior) < 1:
        _die(f"no strictly-prior game for (pid={pid}, gdate={gdate})")
    row = hist[hist["game_date"] == gdate]
    row = row[row["game_id"] == gid]
    if row.empty:
        _die(f"no box-score row for (pid={pid}, gid={gid}, gdate={gdate})")
    row = row.iloc[0]
    team_id = int(row["team_id"])
    home_team_id = int(row["home_team_id"])
    is_home = (team_id == home_team_id)
    prev = prior.tail(1)
    rest_days = 2
    if len(prev):
        prev_date = pd.to_datetime(prev.iloc[-1]["game_date"])
        rest_days = int((pd.to_datetime(gdate) - prev_date).days)
    b2b = 1 if rest_days == 1 else 0
    return {
        "prior_stats": prior,
        "game_context": {"rest_days": rest_days, "back_to_back": b2b},
        "is_home": bool(is_home),
        "target_date": gdate,
        "team_id": team_id,
        "all_stats_df": stats_df,
        "injury_map": {},
        "availability": avail_lookup.get((pid, gdate)),
        "realized_min": float(row["min"]),
        "realized_pts": int(row["pts"]),
        "realized_reb": int(row["reb"]),
        "realized_ast": int(row["ast"]),
    }


# ── per-stat row assembly ─────────────────────────────────────────────────


def _pmf_mean_scalar(pmf: np.ndarray) -> float:
    return float(np.sum(pmf * np.arange(pmf.size)))


def _build_stat_row_tables(
    fold_oof: pd.DataFrame,
    stats: tuple[str, ...],
    auditable_keys: set[tuple[int, int]],
    pred_minutes_by_key: dict[tuple[int, int], float],
    realized_by_key: dict[tuple[int, int], dict],
    features_by_key: dict[tuple[int, int], dict],
) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for stat in stats:
        sub = fold_oof[fold_oof["stat"] == stat]
        rows: list[dict] = []
        for r in sub.itertuples(index=False):
            key = (int(r.player_id), int(r.game_id))
            if key not in auditable_keys:
                continue
            pmf = np.asarray(r.pmf, dtype=np.float64)
            pred_stat_mean = _pmf_mean_scalar(pmf)
            pred_p0 = float(pmf[0]) if pmf.size >= 1 else float("nan")
            pred_p_le1 = (
                float(pmf[0] + pmf[1]) if pmf.size >= 2
                else (float(pmf[0]) if pmf.size >= 1 else float("nan"))
            )
            realized = realized_by_key[key]
            feats = features_by_key[key]
            rows.append({
                "player_id": key[0], "game_id": key[1],
                "pred_stat_mean": pred_stat_mean,
                "pred_p0": pred_p0,
                "pred_p_le1": pred_p_le1,
                "outcome": int(r.outcome),
                "pred_minutes": float(pred_minutes_by_key[key]),
                "realized_minutes": float(realized["min"]),
                "realized_stat": int(realized[stat]),
                "is_home": int(feats["is_home"]),
                "back_to_back": int(feats["back_to_back"]),
                "mp_starter_prob": float(feats["mp_starter_prob"]),
                "rest_days": int(feats["rest_days"]),
                "mp_mean_last10": float(feats["mp_mean_last10"]),
            })
        tables[stat] = pd.DataFrame(rows)
    return tables


# ── bucket metric + summary ────────────────────────────────────────────────


def _metrics_on_subset(sub: pd.DataFrame) -> dict:
    n = int(len(sub))
    if n == 0:
        nan = float("nan")
        return {
            "n_rows": 0,
            "pred_stat_mean": nan, "realized_stat_mean": nan,
            "pred_minutes_mean": nan, "realized_minutes_mean": nan,
            "implied_pred_rate_per_minute": nan,
            "realized_rate_per_minute": nan,
            "rate_bias_pct": nan,
            "pred_p0": nan, "realized_p0": nan,
            "pred_p_le1": nan, "realized_p_le1": nan,
        }
    pred_stat_mean = float(sub["pred_stat_mean"].mean())
    realized_stat_mean = float(sub["realized_stat"].mean())
    pred_minutes_mean = float(sub["pred_minutes"].mean())
    realized_minutes_mean = float(sub["realized_minutes"].mean())
    implied_rpm = pred_stat_mean / max(pred_minutes_mean, 1e-6)
    realized_rpm = realized_stat_mean / max(realized_minutes_mean, 1e-6)
    rate_bias_pct = 100.0 * (realized_rpm - implied_rpm) / max(realized_rpm, 1e-9)
    pred_p0 = float(sub["pred_p0"].mean())
    realized_p0 = float((sub["outcome"] == 0).mean())
    pred_p_le1 = float(sub["pred_p_le1"].mean())
    realized_p_le1 = float((sub["outcome"] <= 1).mean())
    return {
        "n_rows": n,
        "pred_stat_mean": pred_stat_mean,
        "realized_stat_mean": realized_stat_mean,
        "pred_minutes_mean": pred_minutes_mean,
        "realized_minutes_mean": realized_minutes_mean,
        "implied_pred_rate_per_minute": implied_rpm,
        "realized_rate_per_minute": realized_rpm,
        "rate_bias_pct": rate_bias_pct,
        "pred_p0": pred_p0, "realized_p0": realized_p0,
        "pred_p_le1": pred_p_le1, "realized_p_le1": realized_p_le1,
    }


def _print_bucket_table(family: str, rows: list[dict]) -> None:
    print(f"\n  [{family}]")
    print(
        f"    {'bucket':<16} {'n':>6} "
        f"{'pred_stat':>9} {'real_stat':>9} "
        f"{'pred_min':>9} {'real_min':>9} "
        f"{'pred_rpm':>9} {'real_rpm':>9} "
        f"{'bias_%':>8} "
        f"{'p0(p/r)':>13} "
        f"{'p<=1(p/r)':>15}"
    )
    for r in rows:
        m = r["metrics"]
        print(
            f"    {r['bucket']:<16} {m['n_rows']:>6} "
            f"{m['pred_stat_mean']:>9.3f} {m['realized_stat_mean']:>9.3f} "
            f"{m['pred_minutes_mean']:>9.2f} {m['realized_minutes_mean']:>9.2f} "
            f"{m['implied_pred_rate_per_minute']:>9.4f} "
            f"{m['realized_rate_per_minute']:>9.4f} "
            f"{m['rate_bias_pct']:>+8.2f} "
            f"{m['pred_p0']:>6.3f}/{m['realized_p0']:<6.3f} "
            f"{m['pred_p_le1']:>7.3f}/{m['realized_p_le1']:<7.3f}"
        )


# ── bucket family builders ─────────────────────────────────────────────────


def _bucket_minutes_pred(df: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    out = []
    m = df["pred_minutes"].to_numpy()
    for name, lo, hi in MINUTES_BUCKETS:
        mask = (m >= lo) & (m < hi)
        out.append((name, df.loc[mask]))
    return out


def _bucket_home_away(df: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    return [
        ("home", df[df["is_home"] == 1]),
        ("away", df[df["is_home"] == 0]),
    ]


def _bucket_b2b(df: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    return [
        ("b2b", df[df["back_to_back"] == 1]),
        ("not_b2b", df[df["back_to_back"] == 0]),
    ]


def _qcut_labels(
    values: np.ndarray, q: int, label_names: list[str],
) -> tuple[np.ndarray, list[float]]:
    """Deterministic qcut with duplicates='drop'. If the distribution
    collapses to fewer than `q` bins, return fewer labels rather than
    silently recycle names. On total degeneracy (single value), return
    a single bucket labeled label_names[0] covering [min, max]."""
    if len(values) == 0:
        return np.array([], dtype=object), []
    uniq = np.unique(
        values[~np.isnan(values)] if np.issubdtype(values.dtype, np.floating) else values
    )
    if len(uniq) < 2:
        lo = float(uniq[0]) if len(uniq) else 0.0
        return np.array([label_names[0]] * len(values), dtype=object), [lo, lo]
    try:
        codes, bins = pd.qcut(
            pd.Series(values), q=q, labels=False, retbins=True, duplicates="drop",
        )
    except ValueError:
        return np.array([label_names[0]] * len(values), dtype=object), [
            float(np.nanmin(values)), float(np.nanmax(values)),
        ]
    n_buckets = len(bins) - 1
    if n_buckets < 1:
        return np.array([label_names[0]] * len(values), dtype=object), list(map(float, bins))
    used = label_names[:n_buckets]
    codes = codes.fillna(0).astype(int).to_numpy()
    codes = np.clip(codes, 0, n_buckets - 1)
    mapped = np.array([used[c] for c in codes], dtype=object)
    return mapped, list(map(float, bins))


def _bucket_starter_prob(
    df: pd.DataFrame,
) -> tuple[list[tuple[str, pd.DataFrame]], list[float]]:
    labels, bins = _qcut_labels(
        df["mp_starter_prob"].to_numpy(), 3, ["low", "medium", "high"],
    )
    df_l = df.copy()
    df_l["_bucket"] = labels
    out: list[tuple[str, pd.DataFrame]] = []
    for name in ("low", "medium", "high"):
        sub = df_l[df_l["_bucket"] == name]
        if len(sub):
            out.append((name, sub.drop(columns=["_bucket"])))
    return out, bins


def _bucket_rest_days(df: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    r = df["rest_days"].to_numpy()
    return [
        ("0", df[r <= 0]),
        ("1", df[r == 1]),
        ("2", df[r == 2]),
        ("3+", df[r >= 3]),
    ]


def _bucket_role_proxy(
    df: pd.DataFrame,
) -> tuple[list[tuple[str, pd.DataFrame]], list[float]]:
    labels, bins = _qcut_labels(
        df["mp_mean_last10"].to_numpy(), 4, ["bench", "rotation", "starter", "star"],
    )
    df_l = df.copy()
    df_l["_bucket"] = labels
    out: list[tuple[str, pd.DataFrame]] = []
    for name in ("bench", "rotation", "starter", "star"):
        sub = df_l[df_l["_bucket"] == name]
        if len(sub):
            out.append((name, sub.drop(columns=["_bucket"])))
    return out, bins


# ── classification ─────────────────────────────────────────────────────────


DECISION_RULE_TEXT = (
    "GLOBAL_SHARED_RATE_BIAS if for ALL three ship stats: "
    "(a) every major bucket (n_rows >= 100) has the same sign of "
    "rate_bias_pct as the overall rate_bias_pct for that stat, "
    "(b) in EVERY bucket family (each family is a partition of the "
    "audited row set), the share of audited rows whose bucket "
    "rate_bias_pct is within 3 absolute percentage points of the "
    "overall rate_bias_pct is >= 80% — we take the minimum across "
    "families as the stat-level coverage and require it to meet the "
    "threshold (the stricter of the two choices considered), "
    "(c) no major bucket flips sign relative to the overall, and "
    "(d) no major bucket deviates by more than 5 absolute percentage "
    "points from the overall rate_bias_pct. "
    "SEGMENTED_RATE_BIAS if ANY major bucket flips sign vs overall, OR "
    "deviates > 5 absolute percentage points from overall, OR the TRUE "
    "GLOBAL top 5 worst buckets pooled across all stats (deterministic "
    "sort; not the concatenation of per-stat top 5s) concentrate >= 3 "
    "entries in a single bucket family. "
    "Classification cascade: SEGMENTED is evaluated first; GLOBAL is "
    "only reached when no SEGMENTED signal fires AND every stat is "
    "global_ok; MIXED otherwise."
)


def _classify(
    per_stat_overall: dict[str, dict],
    per_stat_bucket_tables: dict[str, dict[str, list[dict]]],
    worst_rankings: dict[str, list[dict]],
    n_audited_rows: int,
) -> dict:
    global_ok_by_stat: dict[str, bool] = {}
    segmented_signals: dict[str, list[str]] = {}
    per_family_coverage_by_stat: dict[str, dict[str, float]] = {}
    min_family_coverage_by_stat: dict[str, float] = {}
    for stat in per_stat_overall:
        overall_bias = float(per_stat_overall[stat]["rate_bias_pct"])
        overall_sign = np.sign(overall_bias)
        # Per-family coverage: each family is a partition of the audited
        # row set, so within-family row counts are non-duplicated by
        # construction. We compute the fraction of audited rows that sit
        # in buckets within GLOBAL_WITHIN_PP of the overall bias, then
        # take the minimum across families — the stricter choice.
        per_family_coverage: dict[str, float] = {}
        for fam, rows in per_stat_bucket_tables[stat].items():
            fam_total = sum(int(r["metrics"]["n_rows"]) for r in rows)
            if fam_total == 0:
                per_family_coverage[fam] = 0.0
                continue
            fam_within = sum(
                int(r["metrics"]["n_rows"]) for r in rows
                if np.isfinite(r["metrics"]["rate_bias_pct"])
                and abs(r["metrics"]["rate_bias_pct"] - overall_bias) <= GLOBAL_WITHIN_PP
            )
            per_family_coverage[fam] = float(fam_within / fam_total)
        per_family_coverage_by_stat[stat] = per_family_coverage
        min_family_coverage = min(per_family_coverage.values()) if per_family_coverage else 0.0
        min_family_coverage_by_stat[stat] = float(min_family_coverage)

        all_bucket_rows: list[dict] = []
        for fam, rows in per_stat_bucket_tables[stat].items():
            for r in rows:
                all_bucket_rows.append({**r, "family": fam})
        major = [
            r for r in all_bucket_rows
            if int(r["metrics"]["n_rows"]) >= MAJOR_BUCKET_MIN_ROWS
        ]
        flips = [
            r for r in major
            if np.sign(r["metrics"]["rate_bias_pct"]) != 0
            and np.sign(r["metrics"]["rate_bias_pct"]) != overall_sign
        ]
        deviants = [
            r for r in major
            if abs(r["metrics"]["rate_bias_pct"] - overall_bias) > SEGMENTED_DEVIATION_PP
        ]
        # GLOBAL-ok gates: no sign flips in majors, no >5pp deviations in
        # majors, and the MIN per-family coverage meets the threshold.
        global_ok = (
            len(flips) == 0
            and len(deviants) == 0
            and min_family_coverage >= GLOBAL_COVERAGE_THRESHOLD
        )
        global_ok_by_stat[stat] = bool(global_ok)
        stat_signals: list[str] = []
        if flips:
            stat_signals.append(f"{len(flips)} major buckets flip sign")
        if deviants:
            stat_signals.append(
                f"{len(deviants)} major buckets deviate >{SEGMENTED_DEVIATION_PP}pp"
            )
        segmented_signals[stat] = stat_signals

    # TRUE GLOBAL top-5: pool every stat's full worst-bucket list into
    # one table, tagged with its stat, sort once using the same
    # deterministic key already used per-stat, and take the first 5.
    combined_pool: list[dict] = []
    for stat, rows in worst_rankings.items():
        for entry in rows:
            combined_pool.append({"stat": stat, **entry})
    combined_pool.sort(
        key=lambda r: (
            -abs(float(r["rate_bias_pct"])), -int(r["n_rows"]),
            r["bucket_family"], r["bucket_name"],
        )
    )
    true_global_top5 = combined_pool[:5]
    family_counts: dict[str, int] = {}
    for entry in true_global_top5:
        family_counts[entry["bucket_family"]] = (
            family_counts.get(entry["bucket_family"], 0) + 1
        )
    concentrated_family = None
    if family_counts:
        cand, count = max(family_counts.items(), key=lambda kv: kv[1])
        if count >= 3:
            concentrated_family = cand

    # Cascade: SEGMENTED is evaluated first. GLOBAL is reached only when
    # NO stat has a segmented signal AND the true-global top-5 shows no
    # family concentration AND every stat is global_ok. Otherwise MIXED.
    any_segmented = (
        any(bool(v) for v in segmented_signals.values())
        or concentrated_family is not None
    )
    all_global_ok = all(global_ok_by_stat.values())
    if any_segmented:
        classification = "SEGMENTED_RATE_BIAS"
    elif all_global_ok:
        classification = "GLOBAL_SHARED_RATE_BIAS"
    else:
        classification = "MIXED"
    return {
        "classification": classification,
        "global_ok_by_stat": global_ok_by_stat,
        "segmented_signals": segmented_signals,
        "per_family_coverage_by_stat": per_family_coverage_by_stat,
        "min_family_coverage_by_stat": min_family_coverage_by_stat,
        "true_global_top5": true_global_top5,
        "top5_family_counts": family_counts,
        "concentrated_family": concentrated_family,
        "decision_rule": DECISION_RULE_TEXT,
    }


def _recommendation(classification: str) -> str:
    if classification == "GLOBAL_SHARED_RATE_BIAS":
        return (
            "RECOMMEND: proceed immediately to bounded OOF PMF correction proof pass"
        )
    if classification == "SEGMENTED_RATE_BIAS":
        return (
            "RECOMMEND: do not use universal correction; inspect shared rate "
            "pipeline / feature drift in the flagged contexts"
        )
    return (
        "RECOMMEND: run a narrow OOF PMF correction proof pass for PTS only, "
        "and context-targeted investigation for REB/AST"
    )


# ── main ───────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold-oof", required=True, type=Path)
    ap.add_argument("--stats-df", required=True, type=Path)
    ap.add_argument("--features-df", required=True, type=Path)
    ap.add_argument("--minutes-models-dir", required=True, type=Path)
    ap.add_argument("--closing-lines-dir", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--stats", nargs="+", default=list(SHIP_STATS_DEFAULT))
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    preflight = _preflight(
        args.fold_oof, args.stats_df, args.features_df, args.minutes_models_dir,
    )
    _print_preflight(preflight)

    stats_tuple = tuple(s.lower() for s in args.stats)
    fold_oof = _load_fold_oof(args.fold_oof, stats_tuple)
    stats_df = _load_stats(args.stats_df)
    features_df = _load_features(args.features_df)
    avail_lookup = _load_availability_lookup()

    universe = (
        fold_oof[["player_id", "game_id", "game_date"]]
        .drop_duplicates().reset_index(drop=True)
    )
    print(f"\nLoaded fold universe: {len(universe):,} unique (player_id, game_id, game_date)")

    stats_by_player = {
        int(pid): g.sort_values("game_date").reset_index(drop=True)
        for pid, g in stats_df.groupby("player_id")
    }

    match_out = _match_audit(
        universe=universe, stats_df=stats_df,
        features_df=features_df, stats_by_player=stats_by_player,
    )
    _print_match_audit(match_out["audit"])
    if match_out["audit"]["n_fully_auditable_rows"] == 0:
        _die("n_fully_auditable_rows=0; cannot proceed.")
    auditable_keys: set[tuple[int, int]] = match_out["auditable_keys"]

    # Per-audited-row predicted minutes, realized box-score, feature row.
    from nba_props_model.models.minutes import minutes_distribution

    pred_minutes_by_key: dict[tuple[int, int], float] = {}
    realized_by_key: dict[tuple[int, int], dict] = {}
    for u in universe.itertuples(index=False):
        key = (int(u.player_id), int(u.game_id))
        if key not in auditable_keys:
            continue
        inputs = _reconstruct_inputs(
            key[0], key[1], str(u.game_date), stats_df, stats_by_player, avail_lookup,
        )
        try:
            dist = minutes_distribution(
                prior_stats=inputs["prior_stats"],
                game_context=inputs["game_context"],
                is_home=inputs["is_home"],
                target_date=inputs["target_date"],
                team_id=inputs["team_id"],
                all_stats_df=inputs["all_stats_df"],
                injury_map=inputs["injury_map"],
                availability=inputs["availability"],
            )
            pred_minutes_by_key[key] = float(dist.mean())
        except Exception as e:
            _die(
                f"minutes_distribution raised for (pid={key[0]}, gid={key[1]}, "
                f"date={u.game_date}): {type(e).__name__}: {e}"
            )
        realized_by_key[key] = {
            "min": float(inputs["realized_min"]),
            "pts": int(inputs["realized_pts"]),
            "reb": int(inputs["realized_reb"]),
            "ast": int(inputs["realized_ast"]),
        }

    feat_idx = features_df.set_index(["player_id", "game_id"], drop=False)
    features_by_key: dict[tuple[int, int], dict] = {}
    for key in auditable_keys:
        row = feat_idx.loc[key]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        features_by_key[key] = {
            "is_home": int(row["is_home"]),
            "back_to_back": int(row["back_to_back"]),
            "mp_starter_prob": float(row["mp_starter_prob"]),
            "rest_days": int(row["rest_days"]),
            "mp_mean_last10": float(row["mp_mean_last10"]),
        }

    stat_tables = _build_stat_row_tables(
        fold_oof=fold_oof, stats=stats_tuple,
        auditable_keys=auditable_keys,
        pred_minutes_by_key=pred_minutes_by_key,
        realized_by_key=realized_by_key,
        features_by_key=features_by_key,
    )

    # ── overall per-stat summary ──
    per_stat_overall: dict[str, dict] = {}
    print("\n=== OVERALL PER-STAT SUMMARY (audited universe) ===")
    for stat in stats_tuple:
        t = stat_tables[stat]
        metrics = _metrics_on_subset(t)
        per_stat_overall[stat] = metrics
        print(
            f"  [{stat}] n={metrics['n_rows']}  "
            f"pred_stat={metrics['pred_stat_mean']:.3f}  "
            f"real_stat={metrics['realized_stat_mean']:.3f}  "
            f"pred_min={metrics['pred_minutes_mean']:.2f}  "
            f"real_min={metrics['realized_minutes_mean']:.2f}  "
            f"pred_rpm={metrics['implied_pred_rate_per_minute']:.4f}  "
            f"real_rpm={metrics['realized_rate_per_minute']:.4f}  "
            f"bias={metrics['rate_bias_pct']:+.2f}%  "
            f"p0(p/r)={metrics['pred_p0']:.3f}/{metrics['realized_p0']:.3f}  "
            f"p<=1(p/r)={metrics['pred_p_le1']:.3f}/{metrics['realized_p_le1']:.3f}"
        )

    # ── bucket families ──
    bucket_cutpoints: dict[str, list[float]] = {}
    bucket_tables_by_stat: dict[str, dict[str, list[dict]]] = {s: {} for s in stats_tuple}
    for stat in stats_tuple:
        t = stat_tables[stat]
        print(f"\n=== BUCKET TABLES — {stat} ===")
        fam_builders = [
            ("minutes_pred", lambda d: (_bucket_minutes_pred(d), None)),
            ("home_away", lambda d: (_bucket_home_away(d), None)),
            ("b2b", lambda d: (_bucket_b2b(d), None)),
            ("starter_prob", lambda d: _bucket_starter_prob(d)),
            ("rest_days", lambda d: (_bucket_rest_days(d), None)),
            ("role_proxy", lambda d: _bucket_role_proxy(d)),
        ]
        for fam, fn in fam_builders:
            out = fn(t)
            buckets, cutpoints = out
            if cutpoints is not None:
                bucket_cutpoints[fam] = cutpoints
            rows: list[dict] = []
            for name, sub in buckets:
                rows.append({
                    "bucket_family": fam,
                    "bucket": name,
                    "metrics": _metrics_on_subset(sub),
                })
            bucket_tables_by_stat[stat][fam] = rows
            _print_bucket_table(fam, rows)
    if bucket_cutpoints:
        print("\n  cutpoints (from qcut):")
        for k, v in bucket_cutpoints.items():
            print(f"    {k}: {[round(x, 4) for x in v]}")

    # ── worst-bucket ranking ──
    worst_rankings: dict[str, list[dict]] = {}
    print("\n=== TOP OFFENDING BUCKETS (per stat) ===")
    for stat in stats_tuple:
        all_rows: list[dict] = []
        for fam, rows in bucket_tables_by_stat[stat].items():
            for r in rows:
                m = r["metrics"]
                if m["n_rows"] == 0 or not np.isfinite(m["rate_bias_pct"]):
                    continue
                all_rows.append({
                    "bucket_family": fam,
                    "bucket_name": r["bucket"],
                    "n_rows": int(m["n_rows"]),
                    "rate_bias_pct": float(m["rate_bias_pct"]),
                    "sign": int(np.sign(m["rate_bias_pct"])),
                })
        all_rows.sort(
            key=lambda r: (
                -abs(r["rate_bias_pct"]), -r["n_rows"],
                r["bucket_family"], r["bucket_name"],
            )
        )
        top = all_rows[:10]
        worst_rankings[stat] = top
        print(f"  [{stat}]")
        for entry in top:
            print(
                f"    {entry['bucket_family']:<14} {entry['bucket_name']:<14} "
                f"n={entry['n_rows']:>5}  "
                f"bias={entry['rate_bias_pct']:+.2f}%  sign={entry['sign']:+d}"
            )

    # ── classification + recommendation ──
    cls = _classify(
        per_stat_overall=per_stat_overall,
        per_stat_bucket_tables=bucket_tables_by_stat,
        worst_rankings=worst_rankings,
        n_audited_rows=int(match_out["audit"]["n_fully_auditable_rows"]),
    )
    rec = _recommendation(cls["classification"])
    print("\n=== CLASSIFICATION ===")
    print(f"  decision rule: {DECISION_RULE_TEXT}")
    print(f"  global_ok_by_stat: {cls['global_ok_by_stat']}")
    print(f"  segmented_signals: {cls['segmented_signals']}")
    print("  per-family coverage (share of audited rows in buckets "
          f"within ±{GLOBAL_WITHIN_PP}pp of overall):")
    for stat, fam_cov in cls["per_family_coverage_by_stat"].items():
        parts = "  ".join(f"{fam}={cov:.3f}" for fam, cov in fam_cov.items())
        min_cov = cls["min_family_coverage_by_stat"][stat]
        print(f"    [{stat}]  min_family_coverage={min_cov:.3f}   {parts}")
    print("  true-global top-5 worst buckets (pooled across stats):")
    for entry in cls["true_global_top5"]:
        print(
            f"    {entry['stat']:<4}  {entry['bucket_family']:<14} "
            f"{entry['bucket_name']:<14} n={entry['n_rows']:>5}  "
            f"bias={entry['rate_bias_pct']:+.2f}%  sign={entry['sign']:+d}"
        )
    print(f"  top5_family_counts: {cls['top5_family_counts']}")
    print(f"  concentrated_family: {cls['concentrated_family']}")
    print(f"  classification: {cls['classification']}")
    print(f"\n{rec}")

    report = {
        "metadata": {
            "git_sha": _git_sha(),
            "run_timestamp": datetime.utcnow().isoformat() + "Z",
            "n_rows": int(match_out["audit"]["n_fully_auditable_rows"]),
            "stats": list(stats_tuple),
            "fold_oof_path": str(args.fold_oof),
        },
        "preflight": preflight,
        "match_audit": match_out["audit"],
        "overall_per_stat": per_stat_overall,
        "bucket_cutpoints": bucket_cutpoints,
        "bucket_tables_by_stat": bucket_tables_by_stat,
        "worst_bucket_rankings": worst_rankings,
        "classification": cls,
        "decision_rule": DECISION_RULE_TEXT,
        "recommendation": rec,
    }
    out_json = args.output_dir / "rate_bias_decomposition.json"
    out_json.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nWrote {out_json}")


if __name__ == "__main__":
    main()
