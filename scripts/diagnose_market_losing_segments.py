#!/usr/bin/env python3
"""Deep diagnosis for the 12 eligible stat-role segments that fail market logloss."""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

FAILING = [
    ("pts", "core"),
    ("pts", "starter"),
    ("reb", "core"),
    ("reb", "rotation"),
    ("ast", "core"),
    ("ast", "starter"),
    ("fg3m", "core"),
    ("fg3m", "starter"),
    ("pa", "starter"),
    ("pr", "starter"),
    ("ra", "core"),
    ("pra", "starter"),
]


def _parse_pmf(cell) -> dict[int, float] | None:
    if cell is None or (isinstance(cell, float) and math.isnan(cell)):
        return None
    if isinstance(cell, dict):
        raw = cell
    else:
        s = str(cell)
        if not s.startswith("{"):
            return None
        raw = json.loads(s)
    out: dict[int, float] = {}
    for k, v in raw.items():
        try:
            out[int(k)] = float(v)
        except Exception:
            continue
    s = sum(out.values())
    if s <= 0:
        return None
    return {k: p / s for k, p in out.items()}


def _pmf_mean_var_p0(d: dict[int, float]) -> tuple[float, float, float]:
    m = sum(k * p for k, p in d.items())
    m2 = sum(k * k * p for k, p in d.items())
    v = max(m2 - m * m, 0.0)
    return m, v, float(d.get(0, 0.0))


def _classify_row(r: pd.Series) -> str:
    """Heuristic row-level root-cause tag (best-effort, not contractual)."""
    mp = float(r.get("model_prob_over") or np.nan)
    mk = float(r.get("market_probability_for_side") or np.nan)
    nv = float(r.get("market_prob_over_no_vig") or np.nan)
    mkt = mk if np.isfinite(mk) else nv
    y = float(r.get("hit_result") or np.nan)
    if not np.isfinite(mp) or not np.isfinite(y):
        return "unknown"
    err = mp - y
    merr = (mp - mkt) if np.isfinite(mkt) else np.nan
    if np.isfinite(merr):
        if merr > 0.12:
            return "model_prob_too_high"
        if merr < -0.12:
            return "model_prob_too_low"
    if err > 0.2:
        return "model_prob_too_high"
    if err < -0.2:
        return "model_prob_too_low"
    mm = float(r.get("model_mean") or np.nan)
    act = float(r.get("actual") or np.nan)
    if np.isfinite(mm) and np.isfinite(act):
        if mm - act > 1.5:
            return "mean_too_high"
        if mm - act < -1.5:
            return "mean_too_low"
    mv = float(r.get("model_variance") or np.nan)
    if np.isfinite(mv) and np.isfinite(act):
        if mv < 1.0 and abs(act - mm) > 4:
            return "variance_too_narrow"
        if mv > 80:
            return "variance_too_wide"
    return "unknown"


def _dominant(c: Counter) -> str:
    if not c:
        return "unknown"
    return c.most_common(1)[0][0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    label = args.label.strip()

    eml = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    sr_csv = (
        REPO_ROOT
        / "artifacts"
        / "model_diagnostics"
        / f"event_market_superiority_{label}"
        / "stat_role_market_superiority.csv"
    )
    if not eml.is_file():
        print(f"MISSING {eml}", file=sys.stderr)
        return 2
    if not sr_csv.is_file():
        print(f"MISSING {sr_csv}", file=sys.stderr)
        return 2

    em = pd.read_parquet(eml)
    sr = pd.read_csv(sr_csv)

    pgs_path = REPO_ROOT / "data" / "player_game_stats.parquet"
    pgs = None
    if pgs_path.is_file():
        try:
            pgs = pd.read_parquet(pgs_path, columns=["player_id", "game_id", "min"])
        except Exception:
            pgs = None

    base = em[
        (em["join_status"] == "matched")
        & (em["settled"] == True)
        & em["model_event_logloss"].notna()
        & em["market_event_logloss"].notna()
    ].copy()

    if pgs is not None and "game_id" in base.columns:
        pgs2 = pgs.copy()
        pgs2["game_id"] = pgs2["game_id"].astype(str)
        pgs2["player_id"] = pgs2["player_id"].astype(str)
        base["game_id"] = base["game_id"].astype(str)
        base["player_id"] = base["player_id"].astype(str)
        base = base.merge(
            pgs2[["player_id", "game_id", "min"]],
            on=["player_id", "game_id"],
            how="left",
            suffixes=("", "_actual"),
        )
        base.rename(columns={"min": "actual_minutes"}, inplace=True)
    else:
        base["actual_minutes"] = np.nan

    pmf_means: list[float] = []
    pmf_vars: list[float] = []
    pmf_p0s: list[float] = []
    for cell in base.get("model_pmf", []):
        d = _parse_pmf(cell)
        if d is None:
            pmf_means.append(np.nan)
            pmf_vars.append(np.nan)
            pmf_p0s.append(np.nan)
        else:
            m, v, p0 = _pmf_mean_var_p0(d)
            pmf_means.append(m)
            pmf_vars.append(v)
            pmf_p0s.append(p0)
    base["model_pmf_mean"] = pmf_means
    base["model_pmf_variance"] = pmf_vars
    base["model_p0"] = pmf_p0s

    base["logloss_gap"] = base["model_event_logloss"] - base["market_event_logloss"]
    base["row_rc"] = base.apply(_classify_row, axis=1)

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"market_losing_segments_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    seg_rows: list[dict] = []
    bin_parts: list[pd.DataFrame] = []
    summ_by_seg: dict[str, dict] = {}

    for stat, role in FAILING:
        sub = base[
            (base["stat"].astype(str).str.lower() == stat)
            & (base["role_bucket"].astype(str) == role)
        ].copy()
        if sub.empty:
            continue
        hit = pd.to_numeric(sub["hit_result"], errors="coerce")
        mpo = pd.to_numeric(sub["model_prob_over"], errors="coerce")
        mkt = pd.to_numeric(sub.get("market_probability_for_side"), errors="coerce")
        if not mkt.notna().any():
            mkt = pd.to_numeric(sub.get("market_prob_over_no_vig"), errors="coerce")
        line = pd.to_numeric(sub["line"], errors="coerce")
        summ = {
            "stat": stat,
            "role_bucket": role,
            "n": int(len(sub)),
            "model_logloss": float(sub["model_event_logloss"].mean()),
            "market_logloss": float(sub["market_event_logloss"].mean()),
            "delta_logloss": float(sub["logloss_gap"].mean()),
            "model_brier": float(sub["model_brier"].mean()),
            "market_brier": float(sub["market_brier"].mean()),
            "delta_brier": float((sub["model_brier"] - sub["market_brier"]).mean()),
            "actual_hit_rate": float(hit.mean()),
            "mean_model_prob": float(mpo.mean()),
            "mean_market_prob": float(mkt.mean()) if mkt.notna().any() else None,
            "model_prob_bias": float((mpo - hit).mean()),
            "market_prob_bias": float((mkt - hit).mean()) if mkt.notna().any() else None,
            "mean_line": float(line.mean()) if line.notna().any() else None,
            "line_p25": float(line.quantile(0.25)) if line.notna().any() else None,
            "line_p50": float(line.quantile(0.50)) if line.notna().any() else None,
            "line_p75": float(line.quantile(0.75)) if line.notna().any() else None,
            "line_min": float(line.min()) if line.notna().any() else None,
            "line_max": float(line.max()) if line.notna().any() else None,
            "model_pmf_mean_avg": float(np.nanmean(sub["model_pmf_mean"].to_numpy())),
            "model_pmf_variance_avg": float(np.nanmean(sub["model_pmf_variance"].to_numpy())),
            "model_p0_avg": float(np.nanmean(sub["model_p0"].to_numpy())),
            "actual_stat_mean": float(pd.to_numeric(sub["actual"], errors="coerce").mean()),
            "mean_error": float(
                (pd.to_numeric(sub["model_mean"], errors="coerce")
                 - pd.to_numeric(sub["actual"], errors="coerce")).mean()
            ),
            "minutes_pred_mean": None,
            "actual_minutes_mean": float(sub["actual_minutes"].mean())
            if "actual_minutes" in sub.columns and sub["actual_minutes"].notna().any()
            else None,
            "top_book_share": float(sub["bookmaker_key"].value_counts(normalize=True).iloc[0])
            if "bookmaker_key" in sub.columns and len(sub)
            else None,
            "top_date_share": float(sub["date"].astype(str).value_counts(normalize=True).iloc[0])
            if len(sub)
            else None,
            "dominant_row_root_cause": _dominant(Counter(sub["row_rc"].astype(str))),
        }
        mpb = summ["model_prob_bias"]
        mmb = summ.get("mean_market_prob")
        dll = summ["delta_logloss"]
        if summ["dominant_row_root_cause"] == "unknown":
            if mmb is not None and summ["mean_model_prob"] > float(mmb) + 0.03 and dll > 0.02:
                summ["dominant_segment_heuristic"] = "model_prob_too_high_vs_market"
            elif mpb < -0.05 and dll > 0.02:
                summ["dominant_segment_heuristic"] = "model_prob_too_low_vs_outcome"
            elif summ.get("mean_error") is not None and abs(summ["mean_error"]) > 2.0:
                summ["dominant_segment_heuristic"] = "mean_bias_pmf_vs_actual"
            elif summ.get("top_book_share") and summ["top_book_share"] > 0.55:
                summ["dominant_segment_heuristic"] = "book_or_snapshot_concentration"
            else:
                summ["dominant_segment_heuristic"] = "distribution_mismatch_unclassified"
        else:
            summ["dominant_segment_heuristic"] = summ["dominant_row_root_cause"]
        summ_by_seg[f"{stat}|{role}"] = summ
        seg_rows.append(summ)

        # decile bins for calibration table
        if mpo.notna().sum() >= 30:
            try:
                sub2 = sub.assign(_bin=pd.qcut(mpo.rank(method="first"), 10, duplicates="drop"))
            except Exception:
                sub2 = sub.assign(_bin=pd.cut(mpo, 10, duplicates="drop"))
            g = sub2.groupby("_bin", observed=False)
            for b, chunk in g:
                hit_b = pd.to_numeric(chunk["hit_result"], errors="coerce")
                bin_parts.append(
                    pd.DataFrame(
                        {
                            "stat": stat,
                            "role_bucket": role,
                            "bin": [str(b)],
                            "n": [len(chunk)],
                            "mean_model_prob": [float(chunk["model_prob_over"].mean())],
                            "mean_market_prob": [
                                float(chunk["market_probability_for_side"].mean())
                                if "market_probability_for_side" in chunk.columns
                                else float("nan")
                            ],
                            "actual_rate": [float(hit_b.mean())],
                        }
                    )
                )

    worst = base.nlargest(100, "logloss_gap", keep="all")
    worst_cols = [
        "date",
        "game_id",
        "player_id",
        "player_name",
        "stat",
        "role_bucket",
        "line",
        "model_prob_over",
        "market_probability_for_side",
        "market_prob_over_no_vig",
        "hit_result",
        "actual",
        "model_mean",
        "model_variance",
        "model_p0",
        "actual_minutes",
        "odds_snapshot_family",
        "bookmaker_key",
        "model_event_logloss",
        "market_event_logloss",
        "logloss_gap",
    ]
    worst = worst[[c for c in worst_cols if c in worst.columns]]

    pd.DataFrame(seg_rows).to_csv(out_dir / "segment_summary.csv", index=False)
    if bin_parts:
        pd.concat(bin_parts, ignore_index=True).to_csv(out_dir / "bin_calibration.csv", index=False)
    else:
        (out_dir / "bin_calibration.csv").write_text("stat,role_bucket,bin,n,mean_model_prob,mean_market_prob,actual_rate\n")
    worst.to_csv(out_dir / "worst_rows.csv", index=False)

    # recommendations
    lines = [
        f"# Root-cause recommendations — `{label}`",
        "",
        "Heuristic tags aggregate row-level `_classify_row` outputs; validate on held-out dates before model changes.",
        "",
    ]
    for s in seg_rows:
        key = f"{s['stat']}|{s['role_bucket']}"
        dom = s["dominant_row_root_cause"]
        heur = s.get("dominant_segment_heuristic", dom)
        lines.append(f"## {key}")
        lines.append(
            f"- **Dominant row tag:** `{dom}`; **segment heuristic:** `{heur}` "
            f"(Δlogloss={s['delta_logloss']:.4f}, ΔBrier={s['delta_brier']:.4f}, n={s['n']})."
        )
        tag = heur if heur != "unknown" else dom
        if tag in (
            "model_prob_too_high",
            "mean_too_high",
            "model_prob_too_high_vs_market",
        ):
            lines.append(
                "  - **Repair:** deflate over-side tail / temperature or shrink line-aware "
                "calibration for high-volume roles; check sparse prop lines vs model mean."
            )
        elif tag in ("model_prob_too_low", "mean_too_low", "model_prob_too_low_vs_outcome"):
            lines.append(
                "  - **Repair:** lift under-side probability mass; review hurdle/p0 for low props."
            )
        elif tag == "mean_bias_pmf_vs_actual":
            lines.append(
                "  - **Repair:** align PMF location/shape with realized box scores; check role-aware means."
            )
        elif tag == "book_or_snapshot_concentration":
            lines.append(
                "  - **Repair:** diversify book coverage or stabilize no-vig extraction for concentrated books."
            )
        elif dom == "variance_too_narrow":
            lines.append(
                "  - **Repair:** widen PMF dispersion (negative binomial / tail lift) for this stat-role."
            )
        elif dom == "variance_too_wide":
            lines.append("  - **Repair:** tighten variance / tail calibration for this stat-role.")
        else:
            lines.append(
                "  - **Repair:** inspect top `worst_rows` for book/snapshot concentration; "
                "consider line transform audit and minutes/role join quality."
            )
        if s.get("top_book_share") and s["top_book_share"] > 0.5:
            lines.append(
                f"  - **Concentration:** book share {s['top_book_share']:.2f} — verify multi-book de-vig stability."
            )
        lines.append("")

    (out_dir / "root_cause_recommendations.md").write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "label": label,
        "n_failing_segments_diagnosed": len(seg_rows),
        "dominant_root_causes": {
            f"{r['stat']}|{r['role_bucket']}": r.get("dominant_segment_heuristic", r["dominant_row_root_cause"])
            for r in seg_rows
        },
        "artifacts": {
            "segment_summary_csv": str(out_dir / "segment_summary.csv"),
            "bin_calibration_csv": str(out_dir / "bin_calibration.csv"),
            "worst_rows_csv": str(out_dir / "worst_rows.csv"),
            "recommendations_md": str(out_dir / "root_cause_recommendations.md"),
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"MARKET_LOSING_SEGMENTS_DIAGNOSE_PASS out={out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
