#!/usr/bin/env python3
"""Deep diagnosis for segments with model_logloss_not_better (Phase 8 follow-up)."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p.astype(float), 1e-12, 1.0 - 1e-12)
    return np.log(p / (1.0 - p))


def _event_ll(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(p.astype(float), 1e-12, 1.0 - 1e-12)
    return -(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))


def _brier(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    return (p - y) ** 2


def _suspected_cause(
    m_bias: float,
    mk_bias: float,
    mean_m: float,
    mean_mk: float,
    hit_rate: float,
) -> str:
    if abs(m_bias) > abs(mk_bias) + 0.05:
        if m_bias > 0:
            return "model_prob_too_high"
        return "model_prob_too_low"
    if abs(mean_m - mean_mk) > 0.08:
        return "mean_bias"
    if abs(hit_rate - 0.5) < 0.02:
        return "sparse_sample_noise"
    return "calibration_map_worsened_logloss"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument(
        "--diagnostics-meta",
        type=Path,
        default=REPO_ROOT / "artifacts" / "docs" / "diagnostics_2026-05-13.meta.json",
        help="Optional diagnostics meta JSON (fold / calibration context).",
    )
    args = ap.parse_args()
    label = args.label.strip()

    meta_diag = args.diagnostics_meta
    eml = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    seg_fail = (
        REPO_ROOT
        / "artifacts"
        / "model_diagnostics"
        / f"event_market_superiority_{label}"
        / "segment_failure_diagnosis.csv"
    )
    sr_path = (
        REPO_ROOT
        / "artifacts"
        / "model_diagnostics"
        / f"event_market_superiority_{label}"
        / "stat_role_market_superiority.csv"
    )
    tt_path = REPO_ROOT / "data" / "training_table.parquet"

    for p in (eml, seg_fail, sr_path):
        if not p.exists():
            print(f"MISSING {p}", file=sys.stderr)
            return 2

    combo = pd.read_parquet(eml)
    fails = pd.read_csv(seg_fail)
    fails = fails[fails.get("precise_failure_reason", "") == "model_logloss_not_better"]
    tt = pd.read_parquet(tt_path) if tt_path.exists() else None

    out_root = REPO_ROOT / "artifacts" / "model_diagnostics" / f"market_losing_segments_{label}"
    out_root.mkdir(parents=True, exist_ok=True)

    seg_rows: list[dict] = []
    bin_rows: list[dict] = []
    worst_parts: list[pd.DataFrame] = []

    for _, fr in fails.iterrows():
        stat = str(fr["stat"]).lower()
        role = str(fr["role_bucket"])
        sub = combo[
            (combo["stat"].astype(str).str.lower() == stat)
            & (combo["role_bucket"].astype(str) == role)
            & (combo["join_status"] == "matched")
            & (combo["settled"] == True)
        ].copy()
        if sub.empty:
            continue
        p_m = pd.to_numeric(sub["model_probability_for_side"], errors="coerce")
        p_k = pd.to_numeric(sub["market_probability_for_side"], errors="coerce")
        y = pd.to_numeric(sub["hit_result"], errors="coerce")
        mask = p_m.notna() & p_k.notna() & y.notna() & y.isin([0.0, 1.0])
        sub = sub.loc[mask]
        p_m = p_m[mask].to_numpy()
        p_k = p_k[mask].to_numpy()
        y = y[mask].to_numpy()
        n = len(sub)
        hit_rate = float(np.mean(y)) if n else float("nan")
        mean_m = float(np.mean(p_m)) if n else float("nan")
        mean_mk = float(np.mean(p_k)) if n else float("nan")
        m_ll = float(np.mean(_event_ll(p_m, y))) if n else float("nan")
        k_ll = float(np.mean(_event_ll(p_k, y))) if n else float("nan")
        m_br = float(np.mean(_brier(p_m, y))) if n else float("nan")
        k_br = float(np.mean(_brier(p_k, y))) if n else float("nan")
        line = pd.to_numeric(sub["line"], errors="coerce")
        mmean = pd.to_numeric(sub.get("model_mean"), errors="coerce")
        mvar = pd.to_numeric(sub.get("model_variance"), errors="coerce")
        p0s = []
        if "model_pmf" in sub.columns:
            for js in sub["model_pmf"].dropna().head(5000):
                try:
                    d = json.loads(js) if isinstance(js, str) else js
                    if isinstance(d, dict) and d:
                        ks = sorted(int(k) for k in d)
                        p0s.append(float(d.get(str(ks[0]), d.get(ks[0], 0)) or 0))
                except Exception:
                    pass
        avg_p0 = float(np.mean(p0s)) if p0s else float("nan")
        mm_mean = float(mmean.mean()) if mmean is not None and mmean.notna().any() else float("nan")
        mm_var = float(mvar.mean()) if mvar is not None and mvar.notna().any() else float("nan")
        minutes_mean = float("nan")
        actual_minutes_mean = float("nan")
        if tt is not None and "minutes_mean" in tt.columns and "actual" in tt.columns:
            tts = tt[tt["stat"].astype(str).str.lower() == stat]
            if len(tts) and "player_id" in sub.columns and "game_id" in sub.columns:
                key = sub.merge(
                    tts[["player_id", "game_id", "minutes_mean", "actual"]],
                    on=["player_id", "game_id"],
                    how="left",
                )
                minutes_mean = float(pd.to_numeric(key["minutes_mean"], errors="coerce").mean())
                actual_minutes_mean = float(pd.to_numeric(key["actual"], errors="coerce").mean())

        seg_rows.append(
            {
                "stat": stat,
                "role_bucket": role,
                "n": n,
                "model_logloss": m_ll,
                "market_logloss": k_ll,
                "delta_logloss": m_ll - k_ll,
                "model_brier": m_br,
                "market_brier": k_br,
                "delta_brier": m_br - k_br,
                "actual_hit_rate": hit_rate,
                "mean_model_prob": mean_m,
                "mean_market_prob": mean_mk,
                "model_prob_bias": mean_m - hit_rate,
                "market_prob_bias": mean_mk - hit_rate,
                "mean_line": float(line.mean()) if n else float("nan"),
                "line_min": float(line.min()) if n else float("nan"),
                "line_p25": float(line.quantile(0.25)) if n else float("nan"),
                "line_p50": float(line.quantile(0.50)) if n else float("nan"),
                "line_p75": float(line.quantile(0.75)) if n else float("nan"),
                "line_max": float(line.max()) if n else float("nan"),
                "avg_model_mean": mm_mean,
                "avg_model_variance": mm_var,
                "avg_model_p0": avg_p0,
                "avg_minutes_mean": minutes_mean,
                "actual_minutes_mean": actual_minutes_mean,
                "minutes_bias": (minutes_mean - actual_minutes_mean)
                if math.isfinite(minutes_mean) and math.isfinite(actual_minutes_mean)
                else float("nan"),
                "suspected_cause": _suspected_cause(mean_m - hit_rate, mean_mk - hit_rate, mean_m, mean_mk, hit_rate),
            }
        )

        # decile bins on model prob
        if n >= 10:
            sub2 = sub.copy()
            sub2["_pm"] = p_m
            sub2["_pk"] = p_k
            sub2["_y"] = y
            try:
                sub2["prob_bin"] = pd.qcut(sub2["_pm"], q=min(10, n), duplicates="drop")
            except Exception:
                sub2["prob_bin"] = "all"
            for bin_id, g in sub2.groupby("prob_bin", observed=False):
                pm = g["_pm"].to_numpy()
                pk = g["_pk"].to_numpy()
                yy = g["_y"].to_numpy()
                bn = len(g)
                bin_rows.append(
                    {
                        "stat": stat,
                        "role_bucket": role,
                        "prob_bin": str(bin_id),
                        "n": bn,
                        "mean_model_prob": float(np.mean(pm)),
                        "mean_market_prob": float(np.mean(pk)),
                        "actual_hit_rate": float(np.mean(yy)),
                        "model_logloss": float(np.mean(_event_ll(pm, yy))),
                        "market_logloss": float(np.mean(_event_ll(pk, yy))),
                        "delta_logloss": float(np.mean(_event_ll(pm, yy) - _event_ll(pk, yy))),
                        "model_brier": float(np.mean(_brier(pm, yy))),
                        "market_brier": float(np.mean(_brier(pk, yy))),
                        "delta_brier": float(np.mean(_brier(pm, yy) - _brier(pk, yy))),
                    }
                )

        d_ll = _event_ll(p_m, y) - _event_ll(p_k, y)
        sub_w = sub.assign(_dll=d_ll).sort_values("_dll", ascending=False).head(50)
        worst_parts.append(sub_w)

    worst = pd.concat(worst_parts, ignore_index=True) if worst_parts else pd.DataFrame()
    keep_cols = [
        c
        for c in [
            "date",
            "game_id",
            "player_id",
            "player_name",
            "stat",
            "role_bucket",
            "line",
            "model_prob_over",
            "market_prob_over_no_vig",
            "hit_result",
            "actual",
            "model_mean",
            "model_variance",
            "model_pmf",
            "bookmaker_key",
        ]
        if c in worst.columns
    ]
    if keep_cols:
        worst = worst[keep_cols]

    pd.DataFrame(seg_rows).to_csv(out_root / "segment_summary.csv", index=False)
    pd.DataFrame(bin_rows).to_csv(out_root / "bin_calibration.csv", index=False)
    worst.to_csv(out_root / "worst_rows.csv", index=False)

    meta_extra = {}
    if meta_diag.exists():
        try:
            meta_extra = json.loads(meta_diag.read_text(encoding="utf-8"))
        except Exception:
            pass
    summary = {
        "label": label,
        "n_losing_segments": len(seg_rows),
        "diagnostics_meta_keys": list(meta_extra.keys())[:40],
        "training_table_used": tt_path.exists(),
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    readme = [
        "# Market losing segments diagnosis",
        "",
        f"Label `{label}` — segments with `model_logloss_not_better` from segment_failure_diagnosis.csv.",
        "",
        "- `segment_summary.csv` — segment aggregates",
        "- `bin_calibration.csv` — decile bins on model probability",
        "- `worst_rows.csv` — top loss-gap rows per segment",
    ]
    (out_root / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    print(f"Wrote {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
