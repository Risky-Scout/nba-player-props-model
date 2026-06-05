#!/usr/bin/env python3
"""M8.7 — OOF PMF mean-shift repair fit (actual outcomes only)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from build_event_market_loss_rows import (  # noqa: E402
    _parse_pmf_value,
)
from nba_props_model.calibration.event_neutral_probability_scale import (  # noqa: E402
    chronological_date_folds,
)
from nba_props_model.calibration.pmf_mean_shift_repair import (  # noqa: E402
    ALPHA_GRID,
    GAMMA_GRID,
    aggregate_row_metrics,
    assert_fit_columns_allowed,
    delta_grid_for_stat,
    eval_candidate_on_rows,
    passes_rollback,
    segment_key,
    normalize_pmf,
)

ART = REPO_ROOT / "artifacts" / "model_diagnostics"
MODELS = REPO_ROOT / "artifacts" / "models"


def _pmf_cell(row) -> dict[int, float]:
    raw = row.get("model_pmf_raw")
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        raw = row.get("model_pmf")
    p = _parse_pmf_value(raw)
    return normalize_pmf(p) if p else {}


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["date"] = d["date"].astype(str)
    d["_pmf"] = [_pmf_cell(r) for _, r in d.iterrows()]
    d = d[d["_pmf"].apply(lambda x: len(x) > 0)]
    d = d[d["actual"].notna()]
    try:
        d["_act"] = d["actual"].astype(int)
    except Exception:
        return pd.DataFrame()
    d["_line"] = pd.to_numeric(d["line"], errors="coerce")
    d["_hit"] = pd.to_numeric(d["hit_result"], errors="coerce")
    d = d[d["_hit"].isin([0.0, 1.0])]
    return d


def _cv_metrics_for_param(
    d_all: pd.DataFrame,
    *,
    method: str,
    delta: float | None,
    gamma: float | None,
    alpha: float | None,
    d_stat: float | None,
) -> tuple[bool, float, dict[str, Any]]:
    dates = d_all["date"].unique()
    folds = chronological_date_folds(np.array(sorted(dates), dtype=object), n_folds=4)
    if not folds:
        return False, float("inf"), {}
    fold_abs_bias: list[float] = []
    agg_raw: dict[str, list[float]] = {
        k: [] for k in ("mean_bias", "mean_nll", "mean_rps", "mean_event_ll", "mean_event_brier", "mean_abs_error")
    }
    agg_cal: dict[str, list[float]] = {k: [] for k in agg_raw}
    for _train_d, val_d in folds:
        va = d_all[d_all["date"].isin(val_d)]
        if len(va) < 15:
            continue
        pmfs = [dict(x) for x in va["_pmf"].tolist()]
        acts = va["_act"].tolist()
        lines = va["_line"].tolist()
        overs = [int(x) for x in va["_hit"].tolist()]
        raw_m = aggregate_row_metrics(pmfs, acts, lines, overs)
        cal_m = eval_candidate_on_rows(
            pmfs, acts, lines, overs, method=method, delta=delta, gamma=gamma, alpha=alpha, d_stat=d_stat
        )
        if cal_m is None:
            return False, float("inf"), {}
        ok, _rr = passes_rollback(raw_m, cal_m, require_bias_improve=True)
        if not ok:
            return False, float("inf"), {}
        fold_abs_bias.append(abs(float(cal_m.get("mean_bias", float("nan")))))
        for k in agg_raw:
            agg_raw[k].append(float(raw_m.get(k, float("nan"))))
            agg_cal[k].append(float(cal_m.get(k, float("nan"))))
    if not fold_abs_bias:
        return False, float("inf"), {}
    score = float(np.mean(fold_abs_bias))
    summary = {
        "raw_mean_bias": float(np.nanmean(agg_raw["mean_bias"])),
        "repaired_mean_bias": float(np.nanmean(agg_cal["mean_bias"])),
        "raw_nll": float(np.nanmean(agg_raw["mean_nll"])),
        "repaired_nll": float(np.nanmean(agg_cal["mean_nll"])),
        "raw_rps": float(np.nanmean(agg_raw["mean_rps"])),
        "repaired_rps": float(np.nanmean(agg_cal["mean_rps"])),
        "raw_event_logloss": float(np.nanmean(agg_raw["mean_event_ll"])),
        "repaired_event_logloss": float(np.nanmean(agg_cal["mean_event_ll"])),
        "raw_event_brier": float(np.nanmean(agg_raw["mean_event_brier"])),
        "repaired_event_brier": float(np.nanmean(agg_cal["mean_event_brier"])),
    }
    return True, score, summary


def _fit_delta_stat_for_stat(d_stat_df: pd.DataFrame, stat: str) -> float | None:
    if d_stat_df.empty or len(d_stat_df) < 120:
        return None
    best_d = None
    best_score = float("inf")
    for d in delta_grid_for_stat(stat):
        ok, sc, _ = _cv_metrics_for_param(
            d_stat_df, method="additive", delta=d, gamma=None, alpha=None, d_stat=None
        )
        if ok and sc < best_score:
            best_score = sc
            best_d = d
    return best_d


def _fit_segment(
    d_seg: pd.DataFrame,
    stat: str,
    role: str,
    d_stat_df: pd.DataFrame,
) -> dict[str, Any]:
    n_dates = int(d_seg["date"].nunique())
    n_all = len(d_seg)
    d_stat = _fit_delta_stat_for_stat(d_stat_df, stat) if not d_stat_df.empty else None

    candidates: list[dict[str, Any]] = []

    for d in delta_grid_for_stat(stat):
        ok, sc, summ = _cv_metrics_for_param(
            d_seg, method="additive", delta=d, gamma=None, alpha=None, d_stat=None
        )
        if ok:
            candidates.append(
                {
                    "selected_scope": "stat_role",
                    "selected_method": "additive",
                    "delta": d,
                    "gamma": None,
                    "alpha": None,
                    "delta_stat": d_stat,
                    "score": sc,
                    "tie": abs(d),
                    "summary": summ,
                }
            )

    for g in GAMMA_GRID:
        ok, sc, summ = _cv_metrics_for_param(
            d_seg, method="multiplicative_gamma", delta=None, gamma=g, alpha=None, d_stat=None
        )
        if ok:
            candidates.append(
                {
                    "selected_scope": "stat_role",
                    "selected_method": "multiplicative_gamma",
                    "delta": None,
                    "gamma": g,
                    "alpha": None,
                    "delta_stat": d_stat,
                    "score": sc,
                    "tie": abs(g - 1.0),
                    "summary": summ,
                }
            )

    if d_stat is not None and n_all >= 250 and n_dates >= 10:
        for d in delta_grid_for_stat(stat):
            for a in ALPHA_GRID:
                ok, sc, summ = _cv_metrics_for_param(
                    d_seg,
                    method="shrink_parent_additive",
                    delta=d,
                    gamma=None,
                    alpha=a,
                    d_stat=d_stat,
                )
                if ok:
                    candidates.append(
                        {
                            "selected_scope": "stat_role",
                            "selected_method": "shrink_parent_additive",
                            "delta_stat_role": d,
                            "delta_stat": d_stat,
                            "alpha": a,
                            "gamma": None,
                            "delta": d,
                            "score": sc,
                            "tie": abs(a - 0.5) + abs(d),
                            "summary": summ,
                        }
                    )

    if not candidates:
        return {
            "stat": stat,
            "role_bucket": role,
            "accepted": False,
            "rollback_reason": "all_candidates_failed_cv_rollback",
            "n_train": n_all,
            "n_val": n_all,
            "n_dates": n_dates,
        }

    best = sorted(candidates, key=lambda c: (c["score"], c["tie"]))[0]

    summ = best["summary"]
    raw_bias = float(summ.get("raw_mean_bias", float("nan")))
    rep_bias = float(summ.get("repaired_mean_bias", float("nan")))

    scope = "stat_role"
    if n_all < 250 or n_dates < 10:
        scope = "stat"

    out = {
        "stat": stat,
        "role_bucket": role,
        "selected_scope": scope,
        "selected_method": best["selected_method"],
        "delta": best.get("delta"),
        "gamma": best.get("gamma"),
        "alpha": best.get("alpha"),
        "delta_stat": best.get("delta_stat"),
        "delta_stat_role": best.get("delta_stat_role", best.get("delta")),
        "n_train": n_all,
        "n_val": n_all,
        "n_dates": n_dates,
        "raw_mean_bias": raw_bias,
        "repaired_mean_bias": rep_bias,
        "raw_nll": summ.get("raw_nll"),
        "repaired_nll": summ.get("repaired_nll"),
        "raw_rps": summ.get("raw_rps"),
        "repaired_rps": summ.get("repaired_rps"),
        "raw_event_logloss": summ.get("raw_event_logloss"),
        "repaired_event_logloss": summ.get("repaired_event_logloss"),
        "raw_event_brier": summ.get("raw_event_brier"),
        "repaired_event_brier": summ.get("repaired_event_brier"),
        "accepted": True,
        "rollback_reason": "",
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--ledger", required=True)
    args = ap.parse_args()
    label = str(args.label)
    ledger_path = Path(args.ledger)
    if not ledger_path.is_file():
        ledger_path = REPO_ROOT / ledger_path
    loss_path = ART / f"event_market_loss_rows_{label}.parquet"
    if not loss_path.is_file():
        raise SystemExit(f"FATAL: missing {loss_path}")

    cols = list(pd.read_parquet(loss_path).columns)
    assert_fit_columns_allowed(cols)

    led = pd.read_csv(ledger_path)
    loss = pd.read_parquet(loss_path)
    loss = _prepare_df(loss)
    if loss.empty:
        raise SystemExit("FATAL: no usable loss rows")

    targets = led[
        (led["dominant_failure"].astype(str).isin(["mean_too_low", "mean_too_high"]))
        | led["allowed_repair_family"].astype(str).str.contains("pmf_mean_shift", na=False)
    ]

    out_dir = ART / f"pmf_mean_shift_repair_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    roll_rows: list[dict[str, Any]] = []
    sel_rows: list[dict[str, Any]] = []
    segments: dict[str, Any] = {}

    for _, lr in targets.iterrows():
        stat = str(lr["stat"]).lower()
        role = str(lr["role_bucket"]).lower()
        sk = segment_key(stat, role)
        d_seg = loss[
            (loss["stat"].astype(str).str.lower() == stat)
            & (loss["role_bucket"].astype(str).str.lower() == role)
        ]
        d_stat_df = loss[loss["stat"].astype(str).str.lower() == stat]
        rep = _fit_segment(d_seg, stat, role, d_stat_df)
        rep["segment_key"] = sk
        if rep.get("accepted"):
            sm = rep["selected_method"]
            seg_payload = {
                "stat": stat,
                "role_bucket": role,
                "selected_scope": rep["selected_scope"],
                "selected_method": sm,
                "delta": rep.get("delta") if sm == "additive" else None,
                "gamma": rep.get("gamma") if sm == "multiplicative_gamma" else None,
                "alpha": rep.get("alpha") if sm == "shrink_parent_additive" else None,
                "delta_stat": rep.get("delta_stat") if sm == "shrink_parent_additive" else None,
                "delta_stat_role": rep.get("delta_stat_role")
                if sm == "shrink_parent_additive"
                else None,
                "n_train": rep["n_train"],
                "n_val": rep["n_val"],
                "n_dates": rep["n_dates"],
                "raw_mean_bias": rep.get("raw_mean_bias"),
                "repaired_mean_bias": rep.get("repaired_mean_bias"),
                "raw_nll": rep.get("raw_nll"),
                "repaired_nll": rep.get("repaired_nll"),
                "raw_rps": rep.get("raw_rps"),
                "repaired_rps": rep.get("repaired_rps"),
                "raw_event_logloss": rep.get("raw_event_logloss"),
                "repaired_event_logloss": rep.get("repaired_event_logloss"),
                "raw_event_brier": rep.get("raw_event_brier"),
                "repaired_event_brier": rep.get("repaired_event_brier"),
                "accepted": True,
                "rollback_reason": "",
            }
            segments[sk] = seg_payload
            sel_rows.append(rep)
        else:
            roll_rows.append(rep)

    manifest = {
        "version": "1.0",
        "label": label,
        "fit_type": "OOF_actual_outcome_pmf_mean_shift_repair",
        "uses_market_probability_as_label": False,
        "uses_market_probability_as_feature": False,
        "fold_key": "game_date",
        "segments": segments,
    }
    MODELS.mkdir(parents=True, exist_ok=True)
    man_path = MODELS / f"pmf_mean_shift_repair_{label}.json"
    man_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    pd.DataFrame(roll_rows).to_csv(out_dir / "rollback_report.csv", index=False)
    pd.DataFrame(sel_rows).to_csv(out_dir / "selected_transforms.csv", index=False)
    summ = {
        "label": label,
        "n_accepted": int(len(segments)),
        "n_rolled_back": int(len(roll_rows)),
    }
    (out_dir / "summary.json").write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8")

    by_seg = pd.DataFrame(sel_rows + roll_rows)
    by_seg.to_csv(out_dir / "by_segment.csv", index=False)

    print("PMF_MEAN_SHIFT_REPAIR_PASS")
    print(f"  manifest: {man_path.relative_to(REPO_ROOT)}")
    print(f"  accepted={len(segments)} rolled_back={len(roll_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
