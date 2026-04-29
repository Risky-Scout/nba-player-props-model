"""Evaluate Phase 8 OOF model PMFs against Odds API paired no-vig market lines.

Read-only against:
  - Phase 8 OOF fold parquets (model PMFs + outcomes per (player_id, game_id, stat))
  - Odds API processed pairs parquet (no-vig over/under per book × line × player × stat)
  - OOF market manifest (player_id ↔ player_name ↔ team ↔ opponent for the target date)

Writes a per-day proof bundle to:
  artifacts/phase9_market_eval/{TARGET_DATE}/
    oof_market_matches.parquet
    oof_market_matches.csv
    market_eval_summary.md
    market_eval_by_stat.csv
    market_eval_by_book.csv
    alternate_line_ladder_eval.csv

Leakage guard: evaluator drops any odds row whose `snapshot_time_utc >
commence_time_utc`. The OOF outcome is the realized stat from the
post-game box score; we do not show closing-line CLV here, only
matched-line evaluation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
OOF_ROOT_DEFAULT = Path("/tmp/phase8_full_vectorized_success/artifacts_downloaded")
ODDS_PROCESSED_DEFAULT = REPO_ROOT / "data" / "odds_api" / "processed"
MANIFEST_DEFAULT = REPO_ROOT / "artifacts" / "market_manifest" / "oof_market_match_manifest.parquet"
OUT_ROOT = REPO_ROOT / "artifacts" / "phase9_market_eval"

STAT_TO_MARKET = {
    "pts": ("player_points", "player_points_alternate"),
    "reb": ("player_rebounds", "player_rebounds_alternate"),
    "ast": ("player_assists", "player_assists_alternate"),
    "tov": ("player_turnovers", "player_turnovers_alternate"),
    "fg3m": ("player_threes", "player_threes_alternate"),
}
MARKET_TO_STAT = {m: s for s, ms in STAT_TO_MARKET.items() for m in ms}


def _norm_name(s: str) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"[\.\,\']", "", s)
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\b\.?", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _load_oof_for_date(oof_root: Path, target_date: str) -> pd.DataFrame:
    folds = sorted(oof_root.glob("fold-*-oof/fold_*.parquet"),
                   key=lambda p: int(p.parent.name.split("-")[1]))
    df = pd.concat([pd.read_parquet(p) for p in folds], ignore_index=True)
    df["game_date"] = df["game_date"].astype(str).str[:10]
    return df[df.game_date == target_date].reset_index(drop=True)


def _parse_pmf(pmf_obj) -> np.ndarray:
    if isinstance(pmf_obj, str):
        d = json.loads(pmf_obj)
        max_k = max(int(k) for k in d.keys())
        arr = np.zeros(max_k + 1, dtype=float)
        for k, p in d.items():
            arr[int(k)] = float(p)
    else:
        arr = np.asarray(pmf_obj, dtype=float)
    s = arr.sum()
    if s > 0:
        arr = arr / s
    return arr


def _p_over_line(pmf: np.ndarray, line: float) -> float:
    """Strict discrete-integer settlement of P(stat > line).

    Half-point line: P(over) + P(under) = 1, no push.
    Whole-number line: push mass at k == line is excluded from the
    over/under denominator (sportsbook settlement convention).

    Normalizing by (p_over + p_under) avoids the FP-epsilon trap where
    `1 - sum(pmf[:k+1])` returns -2.22e-16 on PMFs fully concentrated
    below the line.
    """
    arr = np.asarray(pmf, dtype=float)
    arr = np.clip(arr, 0.0, None)
    s = arr.sum()
    if s <= 0 or not np.isfinite(s):
        return float("nan")
    arr = arr / s
    values = np.arange(len(arr))
    p_over = float(arr[values > line].sum())
    p_under = float(arr[values < line].sum())
    denom = p_over + p_under
    if denom <= 0 or not np.isfinite(denom):
        return float("nan")
    p = p_over / denom
    if -1e-12 <= p <= 1 + 1e-12:
        return min(1.0, max(0.0, p))
    return p


def _logloss(p: np.ndarray, y: np.ndarray) -> float:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def _md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavored markdown table without
    requiring the optional `tabulate` package."""
    if df is None or df.empty:
        return "_(no rows)_"
    cols = list(df.columns)
    def _fmt(v):
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            return ""
        if isinstance(v, float):
            return f"{v:.4f}"
        return str(v)
    head = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = ["| " + " | ".join(_fmt(r[c]) for c in cols) + " |"
            for _, r in df.iterrows()]
    return "\n".join([head, sep] + rows)


def _calibration_bins(p: np.ndarray, y: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    edges = np.linspace(0, 1, n_bins + 1)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        n = int(mask.sum())
        if n == 0:
            rows.append({"bin": f"[{lo:.1f},{hi:.1f}]", "n": 0,
                         "mean_pred": np.nan, "mean_obs": np.nan})
            continue
        rows.append({"bin": f"[{lo:.1f},{hi:.1f}]", "n": n,
                     "mean_pred": float(p[mask].mean()),
                     "mean_obs": float(y[mask].mean())})
    return pd.DataFrame(rows)


def _select_pairs_files(processed_dir: Path, target_date: str,
                        explicit_pairs: Path | None) -> list[Path]:
    if explicit_pairs:
        return [explicit_pairs]
    day_dir = processed_dir / target_date
    if not day_dir.exists():
        return []
    return sorted(day_dir.glob("odds_pairs_*.parquet"))


def _load_pairs(paths: list[Path]) -> pd.DataFrame:
    if not paths:
        return pd.DataFrame()
    frames = []
    for p in paths:
        try:
            df = pd.read_parquet(p)
            df["__source_file"] = str(p.name)
            frames.append(df)
        except Exception as e:
            print(f"  WARN: could not read {p.name}: {e}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target-date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--oof-root", default=str(OOF_ROOT_DEFAULT))
    ap.add_argument("--processed-dir", default=str(ODDS_PROCESSED_DEFAULT))
    ap.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
    ap.add_argument("--pairs", default=None,
                    help="explicit odds_pairs_*.parquet (else all under processed/{target_date}/)")
    args = ap.parse_args()

    target = args.target_date
    out_dir = OUT_ROOT / target
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"PHASE 9B PROOF — Phase 8 OOF vs Odds API market — {target}")
    print("=" * 72)

    # 1. Load OOF for the date.
    oof = _load_oof_for_date(Path(args.oof_root), target)
    print(f"\n[OOF] rows on {target}: {len(oof):,}")
    if oof.empty:
        print(f"  ERROR: no OOF rows on {target}; nothing to evaluate.")
        return 1
    print(f"  by stat: {dict(oof.stat.value_counts())}")
    print(f"  unique games: {oof.game_id.nunique()}; unique players: {oof.player_id.nunique()}")

    # 2. Load manifest (for player_name + team_abbr per (game_id, player_id, stat))
    manifest = pd.read_parquet(args.manifest) if Path(args.manifest).exists() else pd.DataFrame()
    if not manifest.empty:
        manifest = manifest[manifest.game_date == target].copy()
        manifest["player_name_norm"] = manifest["player_name"].map(_norm_name)
    print(f"[MANIFEST] rows for date: {len(manifest)}")

    # 3. Load Odds API paired files for the date.
    pair_paths = _select_pairs_files(Path(args.processed_dir), target,
                                     Path(args.pairs) if args.pairs else None)
    print(f"[ODDS] pair files found for {target}: {len(pair_paths)}")
    for p in pair_paths:
        print(f"  - {p.name}")
    pairs = _load_pairs(pair_paths)
    print(f"[ODDS] paired rows: {len(pairs)}")
    if pairs.empty:
        print(f"  ERROR: no Odds API pair rows for {target}; cannot match.")
        # Still write an empty bundle for downstream consistency.
        pd.DataFrame().to_parquet(out_dir / "oof_market_matches.parquet", index=False)
        pd.DataFrame().to_csv(out_dir / "oof_market_matches.csv", index=False)
        (out_dir / "market_eval_summary.md").write_text(
            f"# Market eval summary — {target}\n\n"
            "Phase 8 OOF rows present, but no Odds API paired rows for this "
            "date. Likely cause: capture not yet run, or capture quota-blocked.\n"
        )
        return 2

    # 4. Leakage filter: snapshot_time_utc <= commence_time_utc
    leakage_violations = 0
    if "snapshot_time_utc" in pairs.columns and "commence_time_utc" in pairs.columns:
        sm = pairs["snapshot_time_utc"].astype(str)
        cm = pairs["commence_time_utc"].astype(str)
        bad = sm > cm
        leakage_violations = int(bad.sum())
        if leakage_violations:
            print(f"  WARN: dropping {leakage_violations} pair rows with "
                  f"snapshot_time_utc > commence_time_utc (leakage guard)")
            pairs = pairs[~bad].reset_index(drop=True)

    # 5. Map market_key -> stat (already in market_stat column).
    pairs["market_stat"] = pairs["market_stat"].astype(str)
    pairs["player_name_norm"] = pairs["player_name"].map(_norm_name)
    print(f"[ODDS] post-leakage paired rows: {len(pairs)}")
    print(f"  by market_stat: {dict(pairs.market_stat.value_counts())}")

    # 6. Join: (game_date, normalized player_name, stat). The manifest is
    # stored with one row per (game_id, player_id, stat). Projecting it
    # WITHOUT deduplication on (game_id, player_id) was the source of the
    # 5x match-explosion bug: each OOF row joined against 5 identical
    # name-only manifest rows (one per stat), so the (player_name_norm,
    # market_stat) merge below produced 5 hits per odds pair. Player name
    # / team / opponent are stat-invariant — dedupe on (game_id, player_id)
    # is lossless and required.
    name_proj = (manifest[["game_id", "player_id", "player_name",
                           "player_name_norm", "team_abbr", "opponent_team_abbr"]]
                  .drop_duplicates(["game_id", "player_id"])
                  if not manifest.empty
                  else oof.assign(player_name=None, player_name_norm=None,
                                  team_abbr=None, opponent_team_abbr=None)
                          [["game_id", "player_id", "player_name",
                            "player_name_norm", "team_abbr", "opponent_team_abbr"]]
                          .drop_duplicates(["game_id", "player_id"]))
    oof_keyed = oof.merge(name_proj, on=["game_id", "player_id"], how="left")
    if "player_name_norm" not in oof_keyed.columns:
        oof_keyed["player_name_norm"] = ""
    # Sanity: oof_keyed must have the same row count as oof (no duplication).
    if len(oof_keyed) != len(oof):
        raise SystemExit(
            f"INTERNAL: oof_keyed row count {len(oof_keyed)} != oof "
            f"row count {len(oof)} — name-projection dedupe failed"
        )
    oof_keyed["game_date"] = oof_keyed["game_date"].astype(str).str[:10]
    pairs["commence_date"] = pairs["commence_time_utc"].astype(str).str[:10]

    # Primary join: (game_date, normalized name, stat). market_stat on
    # the odds side is mapped to model stat by the capture script — this
    # keeps a one-to-one mapping per (player, stat) on the OOF side.
    matches = pairs.merge(
        oof_keyed[["game_id", "player_id", "player_name", "player_name_norm",
                   "team_abbr", "opponent_team_abbr",
                   "stat", "game_date", "outcome", "pmf", "pmf_active",
                   "role_bucket"]],
        left_on=["commence_date", "player_name_norm", "market_stat"],
        right_on=["game_date", "player_name_norm", "stat"], how="inner",
    )
    # Hard sanity: every matched row must have market_stat == stat.
    if not matches.empty:
        bad_stat_join = int((matches["market_stat"] != matches["stat"]).sum())
        if bad_stat_join:
            raise SystemExit(
                f"FAIL: {bad_stat_join} matched rows have market_stat != stat "
                f"(join did not respect stat). This is gate B."
            )
    print(f"[MATCH] joined rows: {len(matches)}")
    print(f"  unique players matched: {matches.player_id.nunique() if 'player_id' in matches else 0}")
    if matches.empty:
        msg = (f"No (name, stat) matches between OOF rows on {target} and the "
               f"available Odds API pairs. Possible causes: name normalization "
               f"mismatch (the Odds API may format names differently); the "
               f"odds capture covers a different date; or no overlapping "
               f"(player, stat) pairs exist.")
        (out_dir / "market_eval_summary.md").write_text(
            f"# Market eval summary — {target}\n\n{msg}\n"
        )
        print(f"  ERROR: 0 matches. Wrote empty bundle and summary.")
        return 3

    # 7. Compute model_p_over_line per matched row + run hard validation gates.
    #    Gates fail-loud rather than silently produce bad numbers.
    pmf_sum_failures = 0
    pmf_missing_count = 0
    pov_oor_count = 0

    def _model_pov(row) -> float | None:
        nonlocal pmf_sum_failures, pmf_missing_count, pov_oor_count
        line = row.get("line")
        if line is None or (isinstance(line, float) and not np.isfinite(line)):
            return None
        src = row["pmf_active"] if row.get("pmf_active") is not None else row.get("pmf")
        if src is None:
            pmf_missing_count += 1
            return None
        pmf = _parse_pmf(src)
        s = float(np.asarray(pmf, dtype=float).sum())
        if abs(s - 1.0) > 1e-6:
            pmf_sum_failures += 1
        pov = _p_over_line(pmf, float(line))
        if pov is None or not np.isfinite(pov) or pov < 0.0 or pov > 1.0:
            pov_oor_count += 1
            return None
        return pov

    matches["model_p_over_line"] = matches.apply(_model_pov, axis=1)

    # ── Hard gates ──────────────────────────────────────────────────────
    n_pairs_post = int(len(pairs))
    n_matches = int(len(matches))
    print(f"\n[GATES — strict checks]")
    print(f"  pairs_after_leakage:   {n_pairs_post}")
    print(f"  matched_rows:          {n_matches}")
    if n_pairs_post and n_matches > int(n_pairs_post * 1.10):
        raise SystemExit(
            f"FAIL gate A: matched_rows ({n_matches}) > "
            f"odds_pairs_rows × 1.10 ({n_pairs_post * 1.10:.1f}). "
            f"Likely cause: join key did not include `stat` or OOF was "
            f"row-multiplied by a stat-keyed manifest projection."
        )
    bad_stat = int((matches["market_stat"] != matches["stat"]).sum()) if not matches.empty else 0
    if bad_stat:
        raise SystemExit(
            f"FAIL gate B: {bad_stat} matched rows have market_stat != stat."
        )
    if pmf_missing_count:
        raise SystemExit(
            f"FAIL gate C: {pmf_missing_count} matched rows have missing PMF."
        )
    if pmf_sum_failures:
        raise SystemExit(
            f"FAIL gate D: {pmf_sum_failures} matched PMFs do not sum to 1 "
            f"within 1e-6."
        )
    if pov_oor_count:
        raise SystemExit(
            f"FAIL gate E: {pov_oor_count} matched rows produced "
            f"model_p_over_line outside [0,1]."
        )
    if leakage_violations:
        raise SystemExit(
            f"FAIL gate F: {leakage_violations} pair rows had snapshot_time "
            f"> commence_time. (Should have been pre-dropped at the leakage "
            f"filter; this gate is a defensive guard.)"
        )
    print(f"  gate A  matched ≤ pairs × 1.10:   PASS  "
          f"(matched/pairs ratio={n_matches/max(n_pairs_post,1):.2f})")
    print(f"  gate B  market_stat == stat:      PASS")
    print(f"  gate C  PMF present:              PASS  (0 missing)")
    print(f"  gate D  PMF sum-to-1 ≤ 1e-6:      PASS  (0 failures)")
    print(f"  gate E  model p_over ∈ [0,1]:     PASS  (0 out-of-range)")
    print(f"  gate F  leakage (snap > commence): PASS  ({leakage_violations} dropped pre-merge)")

    # Duplicate-match diagnostic: each odds pair has a unique pair_key in
    # the source pairs file (verified at capture time). After the join we
    # expect each match to map to exactly one OOF row. Count any matches
    # collapsed onto duplicates of the OOF identity tuple.
    pair_key_cols = ["event_id", "bookmaker_key", "market_key",
                     "player_name_norm", "line", "snapshot_time_utc"]
    pair_key_cols = [c for c in pair_key_cols if c in matches.columns]
    dup_match_count = 0
    if pair_key_cols:
        dup_match_count = int(matches.duplicated(subset=pair_key_cols + ["stat"]).sum())
    print(f"  duplicate (pair-identity + stat) matches: {dup_match_count}")

    # 8. Realized over indicator + push handling.
    matches["over_realized"] = (matches["outcome"].astype(int) > matches["line"].astype(float)).astype(int)
    matches["is_push"] = (matches["line"].astype(float).round() == matches["line"].astype(float)) \
                        & (matches["outcome"].astype(int) == matches["line"].astype(float).astype(int))

    # 9. Edge.
    matches["edge"] = matches["model_p_over_line"] - matches["no_vig_over_prob"]

    # 10. Save match-level table.
    keep_cols = [
        "snapshot_id", "snapshot_time_utc", "snapshot_type", "api_mode",
        "event_id", "commence_time_utc", "home_team", "away_team",
        "bookmaker_key", "market_key", "market_stat", "is_alternate",
        "player_name", "player_name_norm", "player_id", "team_abbr",
        "opponent_team_abbr", "stat", "line", "outcome",
        "over_realized", "is_push",
        "no_vig_over_prob", "no_vig_under_prob",
        "model_p_over_line", "edge",
        "over_odds_american", "under_odds_american", "role_bucket",
    ]
    keep_cols = [c for c in keep_cols if c in matches.columns]
    matches_out = matches[keep_cols].copy()
    matches_out.to_parquet(out_dir / "oof_market_matches.parquet", index=False)
    matches_out.to_csv(out_dir / "oof_market_matches.csv", index=False)
    print(f"[OUTPUT] wrote {(out_dir / 'oof_market_matches.parquet').relative_to(REPO_ROOT)} "
          f"({len(matches_out)} rows)")

    # 11. Score (excluding pushes).
    eval_set = matches_out[~matches_out["is_push"]
                            & matches_out["model_p_over_line"].notna()
                            & matches_out["no_vig_over_prob"].notna()].copy()
    print(f"[SCORE] eval set (non-push, both probs finite): {len(eval_set)} of {len(matches_out)}")

    overall = {}
    if not eval_set.empty:
        y = eval_set["over_realized"].to_numpy().astype(int)
        p_model = eval_set["model_p_over_line"].to_numpy().astype(float)
        p_market = eval_set["no_vig_over_prob"].to_numpy().astype(float)
        overall = {
            "n": len(eval_set),
            "model_logloss": _logloss(p_model, y),
            "market_logloss": _logloss(p_market, y),
            "model_brier": _brier(p_model, y),
            "market_brier": _brier(p_market, y),
            "obs_over_rate": float(y.mean()),
        }
        print(f"\n[OVERALL]")
        print(f"  n={overall['n']}  obs_over_rate={overall['obs_over_rate']:.4f}")
        print(f"  logloss  model={overall['model_logloss']:.4f}  "
              f"market={overall['market_logloss']:.4f}  "
              f"Δ(model−market)={overall['model_logloss']-overall['market_logloss']:+.4f}")
        print(f"  brier    model={overall['model_brier']:.4f}  "
              f"market={overall['market_brier']:.4f}  "
              f"Δ(model−market)={overall['model_brier']-overall['market_brier']:+.4f}")

    # 12. By stat.
    by_stat_rows = []
    for stat_key, sub in eval_set.groupby("stat"):
        if len(sub) < 5:
            continue
        y = sub["over_realized"].to_numpy().astype(int)
        pm = sub["model_p_over_line"].to_numpy().astype(float)
        pk = sub["no_vig_over_prob"].to_numpy().astype(float)
        by_stat_rows.append({
            "stat": stat_key, "n": int(len(sub)),
            "model_logloss": _logloss(pm, y),
            "market_logloss": _logloss(pk, y),
            "model_brier": _brier(pm, y),
            "market_brier": _brier(pk, y),
            "obs_over_rate": float(y.mean()),
        })
    by_stat_df = pd.DataFrame(by_stat_rows)
    if not by_stat_df.empty:
        by_stat_df["d_logloss"] = by_stat_df["model_logloss"] - by_stat_df["market_logloss"]
        by_stat_df["d_brier"] = by_stat_df["model_brier"] - by_stat_df["market_brier"]
    by_stat_df.to_csv(out_dir / "market_eval_by_stat.csv", index=False)
    print(f"\n[BY STAT]")
    if not by_stat_df.empty:
        print(by_stat_df.to_string(index=False))

    # 13. By book.
    by_book_rows = []
    for book, sub in eval_set.groupby("bookmaker_key"):
        if len(sub) < 5:
            continue
        y = sub["over_realized"].to_numpy().astype(int)
        pm = sub["model_p_over_line"].to_numpy().astype(float)
        pk = sub["no_vig_over_prob"].to_numpy().astype(float)
        by_book_rows.append({
            "bookmaker_key": book, "n": int(len(sub)),
            "model_logloss": _logloss(pm, y),
            "market_logloss": _logloss(pk, y),
            "model_brier": _brier(pm, y),
            "market_brier": _brier(pk, y),
        })
    by_book_df = pd.DataFrame(by_book_rows)
    by_book_df.to_csv(out_dir / "market_eval_by_book.csv", index=False)
    print(f"\n[BY BOOK]")
    if not by_book_df.empty:
        print(by_book_df.to_string(index=False))

    # 14a. By main vs alternate (eval set).
    by_alt_rows = []
    if "is_alternate" in eval_set.columns:
        for is_alt_val, sub in eval_set.groupby(eval_set["is_alternate"].astype(bool)):
            label = "alternate" if is_alt_val else "main"
            if len(sub) < 5:
                continue
            y = sub["over_realized"].to_numpy().astype(int)
            pm = sub["model_p_over_line"].to_numpy().astype(float)
            pk = sub["no_vig_over_prob"].to_numpy().astype(float)
            by_alt_rows.append({
                "kind": label, "n": int(len(sub)),
                "model_logloss": _logloss(pm, y),
                "market_logloss": _logloss(pk, y),
                "model_brier": _brier(pm, y),
                "market_brier": _brier(pk, y),
                "obs_over_rate": float(y.mean()),
            })
    by_alt_df = pd.DataFrame(by_alt_rows)
    by_alt_df.to_csv(out_dir / "market_eval_by_main_vs_alternate.csv", index=False)
    print(f"\n[BY MAIN vs ALTERNATE]")
    if not by_alt_df.empty:
        print(by_alt_df.to_string(index=False))

    # 14b. Alternate-line ladder eval (per player × stat × book × snapshot
    # group with ≥ 2 offered lines).
    ladder_rows = []
    monot_violations_total = 0
    if "is_alternate" in eval_set.columns:
        groups = eval_set.groupby(
            ["player_name_norm", "stat", "bookmaker_key", "snapshot_time_utc"],
            dropna=False,
        )
        for (pname, stat_key, book, snap), g in groups:
            g_sorted = g.sort_values("line").reset_index(drop=True)
            if len(g_sorted) < 2:
                continue
            err = (g_sorted["model_p_over_line"]
                   - g_sorted["no_vig_over_prob"]).abs().median()
            # A correct CDF satisfies p_over(line) non-increasing as line rises.
            mkt = g_sorted["no_vig_over_prob"].to_numpy()
            mod = g_sorted["model_p_over_line"].to_numpy()
            mkt_violations = int(np.sum(np.diff(mkt) > 1e-9))
            mod_violations = int(np.sum(np.diff(mod) > 1e-9))
            monot_violations_total += max(mkt_violations, mod_violations)
            ladder_rows.append({
                "player_name_norm": pname, "stat": stat_key, "bookmaker_key": book,
                "snapshot_time_utc": snap, "n_lines": int(len(g_sorted)),
                "median_abs_diff_p_over": float(err),
                "min_line": float(g_sorted["line"].min()),
                "max_line": float(g_sorted["line"].max()),
                "market_monotonicity_violations": mkt_violations,
                "model_monotonicity_violations": mod_violations,
            })
    ladder_df = pd.DataFrame(ladder_rows)
    ladder_df.to_csv(out_dir / "alternate_line_ladder_eval.csv", index=False)
    print(f"\n[ALT LADDER]")
    print(f"  number of ladder groups:                {len(ladder_df)}")
    if not ladder_df.empty:
        print(f"  average ladder size (n_lines):          {ladder_df.n_lines.mean():.2f}")
        print(f"  median |Δ p_over|: median across groups: "
              f"{ladder_df.median_abs_diff_p_over.median():.4f}  "
              f"(min={ladder_df.median_abs_diff_p_over.min():.4f}  "
              f"max={ladder_df.median_abs_diff_p_over.max():.4f})")
        print(f"  monotonicity violations (sum across groups, "
              f"market or model): {monot_violations_total}")

    # 15. Validation gates report.
    print(f"\n[GATES]")
    print(f"  selected target date:                 {target}")
    print(f"  OOF rows on target:                   {len(oof):,}")
    print(f"  odds pair rows (post-leakage):        {len(pairs):,}")
    print(f"  matched rows:                         {len(matches_out):,}")
    print(f"  match rate (matches / odds pairs):    "
          f"{len(matches_out) / max(len(pairs), 1):.2%}")
    print(f"  unique players matched:               "
          f"{matches_out['player_id'].nunique() if 'player_id' in matches_out.columns else 0}")
    print(f"  matched rows by stat:                 "
          f"{dict(matches_out.stat.value_counts()) if not matches_out.empty else {}}")
    print(f"  matched rows by book:                 "
          f"{dict(matches_out.bookmaker_key.value_counts()) if not matches_out.empty else {}}")
    if "is_alternate" in matches_out.columns and not matches_out.empty:
        ma_alt = int(matches_out["is_alternate"].astype(bool).sum())
        ma_main = int((~matches_out["is_alternate"].astype(bool)).sum())
        print(f"  matched rows main vs alternate:       main={ma_main}  alternate={ma_alt}")
    print(f"  duplicate (pair_key + stat) matches:  {dup_match_count}")
    print(f"  leakage_violations_dropped:           {leakage_violations}")
    print(f"  PMF sum failures:                     {pmf_sum_failures}")
    print(f"  market_stat != stat failures:         "
          f"{int((matches_out['market_stat'] != matches_out['stat']).sum()) if not matches_out.empty else 0}")
    print(f"  non-push scoring rows (eval set):     {len(eval_set)}")
    if "tov" not in dict(matches_out.market_stat.value_counts() if not matches_out.empty else {}):
        print(f"  WARN: zero matched TOV rows (books may not offer turnovers).")
    print(f"  alternate-line ladder groups:         {len(ladder_df)}")

    # 16. Write summary markdown.
    md = [f"# Phase 9B market eval — {target}", "",
          f"- OOF rows on date: **{len(oof):,}**",
          f"- Odds pair rows (post-leakage): **{len(pairs):,}**",
          f"- Matched rows: **{len(matches_out):,}**",
          f"- Eval set (non-push): **{len(eval_set):,}**",
          f"- Leakage rows dropped: **{leakage_violations}**", ""]
    if overall:
        md += ["## Overall (non-push)", "",
               f"| Metric | Model | Market (no-vig) | Δ(model−market) |",
               f"|---|---:|---:|---:|",
               f"| logloss | {overall['model_logloss']:.4f} | "
               f"{overall['market_logloss']:.4f} | "
               f"{overall['model_logloss']-overall['market_logloss']:+.4f} |",
               f"| Brier   | {overall['model_brier']:.4f} | "
               f"{overall['market_brier']:.4f} | "
               f"{overall['model_brier']-overall['market_brier']:+.4f} |",
               f"| obs over rate | — | — | {overall['obs_over_rate']:.4f} |",
               ""]
    md += ["## By stat", "", _md_table(by_stat_df), ""]
    md += ["## By book", "", _md_table(by_book_df), ""]
    md += ["## By main vs alternate", "", _md_table(by_alt_df), ""]
    md += ["## Alternate-line ladder", "",
           f"- ladder groups: **{len(ladder_df)}**",
           (f"- average ladder size: **{ladder_df.n_lines.mean():.2f}**"
            if not ladder_df.empty else "- average ladder size: n/a"),
           (f"- median |Δ p_over| across groups: "
            f"**{ladder_df.median_abs_diff_p_over.median():.4f}**"
            if not ladder_df.empty else "- median |Δ p_over|: n/a"),
           f"- monotonicity violations (sum across groups): **{monot_violations_total}**",
           ""]
    md += ["## Honest caveats", "",
           "- This is a **single-day proof**; do not generalize to a "
           "market-beating claim. The matched closing-line audit on the full "
           "Phase 8 OOF (n=3,818) found the de-vigged closing market beats the "
           "standalone calibrated model on log-loss in 9 of 11 cohorts.",
           "- TOV may not appear in matches because books did not offer it.",
           "- Alternate-line ladder analysis here is the mean absolute "
           "deviation between model `p_over_line` and market `no_vig_over_prob` "
           "across each player×stat×book ladder; reconstruction of a "
           "market-implied PMF over the ladder is the next step.",
           ""]
    (out_dir / "market_eval_summary.md").write_text("\n".join(md))
    print(f"\nWrote {(out_dir / 'market_eval_summary.md').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
