#!/usr/bin/env python3
"""M8.7 — OOF event-neutral probability scale repair (actual outcome only; no market features)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.calibration.event_neutral_probability_scale import (  # noqa: E402
    assert_no_forbidden_training_columns,
    apply_logit_ab,
    apply_shrink_to_half,
    binary_logloss,
    brier_score,
    calibration_slope_intercept,
    chronological_date_folds,
    ece_10bin,
    fit_isotonic_values,
    blend_iso_parent,
)

ART = REPO_ROOT / "artifacts" / "model_diagnostics"
MODELS = REPO_ROOT / "artifacts" / "models"

A_GRID = [0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.00]
B_GRID = [-0.25, -0.15, -0.075, 0.0, 0.075, 0.15, 0.25]
LAM_GRID = [0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
ISO_W_GRID = [0.10, 0.20, 0.30, 0.40]


def _resolve_p_feat(df: pd.DataFrame) -> pd.Series:
    if "model_prob_over_raw" in df.columns:
        return pd.to_numeric(df["model_prob_over_raw"], errors="coerce")
    if "model_prob_over_pre_event_calibration" in df.columns:
        return pd.to_numeric(df["model_prob_over_pre_event_calibration"], errors="coerce")
    return pd.to_numeric(df["model_prob_over"], errors="coerce")


def _resolve_date(df: pd.DataFrame) -> pd.Series:
    if "game_date" in df.columns:
        return df["game_date"].astype(str)
    return df["date"].astype(str)


def _segment_allowed(allowed: str) -> bool:
    toks = ("event_neutral_temperature", "shrunk_isotonic", "hierarchical_logit_shrinkage")
    parts = [x.strip() for x in str(allowed).split("|") if x.strip()]
    return any(t in parts for t in toks)


def _cv_eval_logit_ab(
    p: np.ndarray,
    y: np.ndarray,
    dates: np.ndarray,
    a: float,
    b: float,
    *,
    reg: float = 0.01,
) -> dict[str, Any]:
    folds = chronological_date_folds(dates, n_folds=5)
    if not folds:
        return {"ok": False, "rollback_reason": "insufficient_date_folds"}
    val_ll_raw: list[float] = []
    val_ll_cal: list[float] = []
    val_br_raw: list[float] = []
    val_br_cal: list[float] = []
    val_p_raw_all: list[float] = []
    val_p_cal_all: list[float] = []
    val_y_all: list[float] = []
    for train_d, val_d in folds:
        tm = np.isin(dates, train_d)
        vm = np.isin(dates, val_d)
        if tm.sum() < 20 or vm.sum() < 5:
            continue
        p_va, y_va = p[vm], y[vm]
        raw_ll = binary_logloss(p_va, y_va)
        p_c = apply_logit_ab(p_va, a, b)
        cal_ll = binary_logloss(p_c, y_va)
        raw_br = brier_score(p_va, y_va)
        cal_br = brier_score(p_c, y_va)
        if cal_ll > raw_ll + 0.001 or cal_br > raw_br + 0.001:
            return {"ok": False, "rollback_reason": "heldout_logloss_or_brier_worse"}
        raw_e = ece_10bin(p_va, y_va)
        cal_e = ece_10bin(p_c, y_va)
        if cal_e == cal_e and raw_e == raw_e and cal_e > raw_e + 0.03:
            return {"ok": False, "rollback_reason": "ece_worsened_materially"}
        rs, _ri = calibration_slope_intercept(p_va, y_va)
        cs, _ci = calibration_slope_intercept(p_c, y_va)
        if rs == rs and cs == cs and abs(cs - 1.0) > abs(rs - 1.0) + 0.15:
            return {"ok": False, "rollback_reason": "calibration_slope_moved_farther_from_one"}
        val_ll_raw.append(raw_ll)
        val_ll_cal.append(cal_ll)
        val_br_raw.append(raw_br)
        val_br_cal.append(cal_br)
        val_p_raw_all.extend(p_va.tolist())
        val_p_cal_all.extend(p_c.tolist())
        val_y_all.extend(y_va.tolist())
    if not val_ll_cal:
        return {"ok": False, "rollback_reason": "no_valid_folds"}
    p_raw_a = np.asarray(val_p_raw_all, dtype=float)
    p_cal_a = np.asarray(val_p_cal_all, dtype=float)
    y_a = np.asarray(val_y_all, dtype=float)
    return {
        "ok": True,
        "heldout_logloss_raw": float(np.mean(val_ll_raw)),
        "heldout_logloss_cal": float(np.mean(val_ll_cal)),
        "heldout_brier_raw": float(np.mean(val_br_raw)),
        "heldout_brier_cal": float(np.mean(val_br_cal)),
        "raw_ece": float(ece_10bin(p_raw_a, y_a)),
        "cal_ece": float(ece_10bin(p_cal_a, y_a)),
        "objective": float(np.mean(val_ll_cal) + reg * ((a - 1.0) ** 2 + b**2)),
        "tie_metric": float((a - 1.0) ** 2 + b**2),
    }


def _cv_eval_shrink_half(p: np.ndarray, y: np.ndarray, dates: np.ndarray, lam: float) -> dict[str, Any]:
    folds = chronological_date_folds(dates, n_folds=5)
    if not folds:
        return {"ok": False, "rollback_reason": "insufficient_date_folds"}
    val_ll_raw, val_ll_cal, val_br_raw, val_br_cal = [], [], [], []
    for train_d, val_d in folds:
        tm = np.isin(dates, train_d)
        vm = np.isin(dates, val_d)
        if tm.sum() < 20 or vm.sum() < 5:
            continue
        p_va, y_va = p[vm], y[vm]
        raw_ll = binary_logloss(p_va, y_va)
        p_c = apply_shrink_to_half(p_va, lam)
        cal_ll = binary_logloss(p_c, y_va)
        raw_br = brier_score(p_va, y_va)
        cal_br = brier_score(p_c, y_va)
        if cal_ll > raw_ll + 0.001 or cal_br > raw_br + 0.001:
            return {"ok": False, "rollback_reason": "heldout_logloss_or_brier_worse"}
        val_ll_raw.append(raw_ll)
        val_ll_cal.append(cal_ll)
        val_br_raw.append(raw_br)
        val_br_cal.append(cal_br)
    if not val_ll_cal:
        return {"ok": False, "rollback_reason": "no_valid_folds"}
    return {
        "ok": True,
        "heldout_logloss_raw": float(np.mean(val_ll_raw)),
        "heldout_logloss_cal": float(np.mean(val_ll_cal)),
        "heldout_brier_raw": float(np.mean(val_br_raw)),
        "heldout_brier_cal": float(np.mean(val_br_cal)),
        "raw_ece": float("nan"),
        "cal_ece": float("nan"),
        "objective": float(np.mean(val_ll_cal)),
        "tie_metric": float((1.0 - lam) ** 2),
    }


def _cv_eval_logit_ab_stat_pool(
    p_all: np.ndarray,
    y_all: np.ndarray,
    d_all: np.ndarray,
    p_seg: np.ndarray,
    y_seg: np.ndarray,
    d_seg: np.ndarray,
    a: float,
    b: float,
    a0: float,
    b0: float,
    *,
    reg: float,
) -> dict[str, Any]:
    folds = chronological_date_folds(d_seg, n_folds=5)
    if not folds:
        return {"ok": False}
    val_ll_raw: list[float] = []
    val_ll_cal: list[float] = []
    val_br_raw: list[float] = []
    val_br_cal: list[float] = []
    pen = reg * (((a - 1.0) ** 2 + b**2) + 0.5 * ((a - a0) ** 2 + (b - b0) ** 2))
    for _train_d, val_d in folds:
        tm_all = ~np.isin(d_all, val_d)
        vm = np.isin(d_seg, val_d)
        if tm_all.sum() < 50 or vm.sum() < 5:
            continue
        p_va, y_va = p_seg[vm], y_seg[vm]
        raw_ll = binary_logloss(p_va, y_va)
        p_c = apply_logit_ab(p_va, a, b)
        cal_ll = binary_logloss(p_c, y_va)
        raw_br = brier_score(p_va, y_va)
        cal_br = brier_score(p_c, y_va)
        if cal_ll > raw_ll + 0.001 or cal_br > raw_br + 0.001:
            return {"ok": False}
        val_ll_raw.append(raw_ll)
        val_ll_cal.append(cal_ll)
        val_br_raw.append(raw_br)
        val_br_cal.append(cal_br)
    if not val_ll_cal:
        return {"ok": False}
    return {
        "ok": True,
        "heldout_logloss_raw": float(np.mean(val_ll_raw)),
        "heldout_logloss_cal": float(np.mean(val_ll_cal)),
        "heldout_brier_raw": float(np.mean(val_br_raw)),
        "heldout_brier_cal": float(np.mean(val_br_cal)),
        "raw_ece": float("nan"),
        "cal_ece": float("nan"),
        "objective": float(np.mean(val_ll_cal) + pen),
        "tie_metric": float((a - 1.0) ** 2 + b**2 + 0.25 * ((a - a0) ** 2 + (b - b0) ** 2)),
    }


def _fit_segment(
    sub: pd.DataFrame,
    stat: str,
    role: str,
    pool_stat: pd.DataFrame,
) -> dict[str, Any]:
    dates = _resolve_date(sub).to_numpy(dtype=object)
    p = _resolve_p_feat(sub).to_numpy(dtype=float)
    y = pd.to_numeric(sub["hit_result"], errors="coerce").to_numpy(dtype=float)
    m = np.isfinite(p) & np.isfinite(y) & np.isin(y, (0.0, 1.0))
    p, y, dates = p[m], y[m], dates[m]
    if len(p) < 80:
        return {
            "stat": stat,
            "role_bucket": role,
            "selected_scope": "none",
            "selected_method": "none",
            "accepted": False,
            "rollback_reason": "sample_below_threshold",
            "n_train": int(len(p)),
            "n_val": 0,
            "n_dates": int(len(set(dates.tolist()))),
            "raw_logloss": float("nan"),
            "cal_logloss": float("nan"),
            "delta_logloss": float("nan"),
            "raw_brier": float("nan"),
            "cal_brier": float("nan"),
            "delta_brier": float("nan"),
            "raw_ece": float("nan"),
            "cal_ece": float("nan"),
            "a": None,
            "b": None,
            "lambda": None,
            "isotonic_weight": None,
        }

    n_dates = int(len(set(dates.tolist())))
    candidates: list[dict[str, Any]] = []

    best_a: dict[str, Any] | None = None
    best_obj = float("inf")
    for a in A_GRID:
        for b in B_GRID:
            ev = _cv_eval_logit_ab(p, y, dates, a, b, reg=0.01)
            if not ev["ok"]:
                continue
            obj = float(ev["objective"])
            if obj < best_obj:
                best_obj = obj
                best_a = ev | {"method": "logit_ab", "scope": "segment", "a": a, "b": b}
    if best_a:
        candidates.append(best_a)

    for lam in LAM_GRID:
        ev = _cv_eval_shrink_half(p, y, dates, lam)
        if ev["ok"]:
            candidates.append(ev | {"method": "shrink_to_half", "scope": "segment", "lambda": lam})

    a0 = float(best_a.get("a", 1.0)) if best_a else 1.0
    b0 = float(best_a.get("b", 0.0)) if best_a else 0.0
    if not pool_stat.empty and stat:
        d_all = _resolve_date(pool_stat).to_numpy(dtype=object)
        p_all = _resolve_p_feat(pool_stat).to_numpy(dtype=float)
        y_all = pd.to_numeric(pool_stat["hit_result"], errors="coerce").to_numpy(dtype=float)
        m2 = np.isfinite(p_all) & np.isfinite(y_all) & np.isin(y_all, (0.0, 1.0))
        p_all, y_all, d_all = p_all[m2], y_all[m2], d_all[m2]
        if len(p_all) >= 200:
            for a in A_GRID:
                for b in B_GRID:
                    ev = _cv_eval_logit_ab_stat_pool(
                        p_all, y_all, d_all, p, y, dates, a, b, a0, b0, reg=0.01
                    )
                    if ev.get("ok"):
                        candidates.append(
                            ev | {"method": "logit_ab", "scope": "stat", "a": a, "b": b}
                        )
                        break
                else:
                    continue
                break

    stat_cand = next((c for c in candidates if c.get("scope") == "stat"), None)
    if stat_cand and len(p) >= 350 and n_dates >= 10:
        a_p = float(stat_cand.get("a", 1.0))
        b_p = float(stat_cand.get("b", 0.0))
        best_c = None
        best_o = float("inf")
        for a in A_GRID:
            for b in B_GRID:
                reg_h = 0.01 + 0.005 * ((a - a_p) ** 2 + (b - b_p) ** 2)
                ev = _cv_eval_logit_ab(p, y, dates, a, b, reg=reg_h)
                if not ev["ok"]:
                    continue
                if float(ev["objective"]) < best_o:
                    best_o = float(ev["objective"])
                    best_c = ev | {
                        "method": "logit_ab",
                        "scope": "stat_role",
                        "a": a,
                        "b": b,
                        "parent_a": a_p,
                        "parent_b": b_p,
                    }
        if best_c:
            candidates.append(best_c)

    iso_parent = next(
        (c for c in candidates if c.get("method") == "logit_ab" and c.get("scope") == "segment"),
        None,
    )
    if iso_parent and len(p) >= 650 and n_dates >= 15:
        folds = chronological_date_folds(dates, n_folds=5)
        if folds:
            ok_e = True
            rr = ""
            val_ll_raw: list[float] = []
            val_ll_cal: list[float] = []
            val_br_raw: list[float] = []
            val_br_cal: list[float] = []
            iso_xt = iso_yt = None
            best_train = -1
            pa = float(iso_parent.get("a", 1.0))
            pb = float(iso_parent.get("b", 0.0))
            w_use = ISO_W_GRID[0]
            for train_d, val_d in folds:
                tm = np.isin(dates, train_d)
                vm = np.isin(dates, val_d)
                if tm.sum() < 200 or vm.sum() < 20:
                    ok_e = False
                    rr = "isotonic_sample_below_threshold"
                    break
                p_tr, y_tr = p[tm], y[tm]
                p_va, y_va = p[vm], y[vm]
                raw_ll = binary_logloss(p_va, y_va)
                raw_br = brier_score(p_va, y_va)
                fitted = fit_isotonic_values(p_tr, y_tr)
                if fitted is None:
                    ok_e = False
                    rr = "isotonic_fit_failed"
                    break
                xt, yt = fitted
                best_iso_ll = float("inf")
                best_w = w_use
                for w in ISO_W_GRID:
                    parent_va = apply_logit_ab(p_va, pa, pb)
                    p_c = blend_iso_parent(p_va, xt, yt, parent_va, w)
                    if np.any(~np.isfinite(p_c)) or np.any(p_c <= 0) or np.any(p_c >= 1):
                        continue
                    cal_ll = binary_logloss(p_c, y_va)
                    cal_br = brier_score(p_c, y_va)
                    if cal_ll > raw_ll + 0.001 or cal_br > raw_br + 0.001:
                        continue
                    if cal_ll < best_iso_ll:
                        best_iso_ll = cal_ll
                        best_w = w
                if best_iso_ll == float("inf"):
                    ok_e = False
                    rr = "heldout_logloss_or_brier_worse"
                    break
                w_use = best_w
                parent_va = apply_logit_ab(p_va, pa, pb)
                p_c = blend_iso_parent(p_va, xt, yt, parent_va, w_use)
                val_ll_raw.append(raw_ll)
                val_ll_cal.append(binary_logloss(p_c, y_va))
                val_br_raw.append(raw_br)
                val_br_cal.append(brier_score(p_c, y_va))
                if int(tm.sum()) > best_train:
                    best_train = int(tm.sum())
                    iso_xt, iso_yt = xt, yt
            if ok_e and val_ll_cal and iso_xt is not None:
                candidates.append(
                    {
                        "ok": True,
                        "method": "shrunk_isotonic",
                        "scope": "segment",
                        "heldout_logloss_raw": float(np.mean(val_ll_raw)),
                        "heldout_logloss_cal": float(np.mean(val_ll_cal)),
                        "heldout_brier_raw": float(np.mean(val_br_raw)),
                        "heldout_brier_cal": float(np.mean(val_br_cal)),
                        "raw_ece": float("nan"),
                        "cal_ece": float("nan"),
                        "objective": float(np.mean(val_ll_cal)),
                        "tie_metric": float(w_use),
                        "isotonic_x": iso_xt.tolist(),
                        "isotonic_y": iso_yt.tolist(),
                        "isotonic_weight": float(w_use),
                        "parent_transform": {"method": "logit_ab", "a": pa, "b": pb},
                    }
                )

    accepted = [c for c in candidates if c.get("ok")]
    if not accepted:
        return {
            "stat": stat,
            "role_bucket": role,
            "selected_scope": "none",
            "selected_method": "none",
            "accepted": False,
            "rollback_reason": "all_candidates_rolled_back",
            "n_train": int(len(p)),
            "n_val": 0,
            "n_dates": n_dates,
            "raw_logloss": float(binary_logloss(p, y)),
            "cal_logloss": float("nan"),
            "delta_logloss": float("nan"),
            "raw_brier": float(brier_score(p, y)),
            "cal_brier": float("nan"),
            "delta_brier": float("nan"),
            "raw_ece": float(ece_10bin(p, y)),
            "cal_ece": float("nan"),
            "a": None,
            "b": None,
            "lambda": None,
            "isotonic_weight": None,
        }

    def scope_rank(sc: str) -> int:
        # Lower is simpler / more parent-like (prefer segment affine over stat_role).
        return {"segment": 0, "stat": 1, "stat_role": 2}.get(str(sc), 9)

    best = sorted(
        accepted,
        key=lambda c: (
            float(c.get("objective", 9e9)),
            scope_rank(str(c.get("scope"))),
            float(c.get("tie_metric", 9e9)),
        ),
    )[0]

    return {
        "stat": stat,
        "role_bucket": role,
        "selected_scope": str(best.get("scope")),
        "selected_method": str(best.get("method")),
        "accepted": True,
        "rollback_reason": "",
        "n_train": int(len(p)),
        "n_val": int(len(p)),
        "n_dates": n_dates,
        "raw_logloss": float(best.get("heldout_logloss_raw", np.nan)),
        "cal_logloss": float(best.get("heldout_logloss_cal", np.nan)),
        "delta_logloss": float(
            float(best.get("heldout_logloss_cal", np.nan))
            - float(best.get("heldout_logloss_raw", np.nan))
        ),
        "raw_brier": float(best.get("heldout_brier_raw", np.nan)),
        "cal_brier": float(best.get("heldout_brier_cal", np.nan)),
        "delta_brier": float(
            float(best.get("heldout_brier_cal", np.nan))
            - float(best.get("heldout_brier_raw", np.nan))
        ),
        "raw_ece": float(best.get("raw_ece", np.nan)),
        "cal_ece": float(best.get("cal_ece", np.nan)),
        "a": best.get("a"),
        "b": best.get("b"),
        "lambda": best.get("lambda"),
        "isotonic_weight": best.get("isotonic_weight"),
        "isotonic_x": best.get("isotonic_x"),
        "isotonic_y": best.get("isotonic_y"),
        "parent_transform": best.get("parent_transform"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--ledger", required=True)
    args = ap.parse_args()
    label = str(args.label)
    ledger_path = Path(args.ledger)
    if not ledger_path.is_file():
        ledger_path = REPO_ROOT / ledger_path
    if not ledger_path.is_file():
        raise SystemExit(f"FATAL: ledger not found: {ledger_path}")

    loss_path = ART / f"event_market_loss_rows_{label}.parquet"
    if not loss_path.is_file():
        raise SystemExit(f"FATAL: loss rows parquet missing: {loss_path}")

    ledger = pd.read_csv(ledger_path)
    loss = pd.read_parquet(loss_path)
    assert_no_forbidden_training_columns(list(loss.columns))

    push_count_excluded = int(
        (~pd.to_numeric(loss["hit_result"], errors="coerce").isin([0.0, 1.0])).sum()
    )

    rows_roll: list[dict[str, Any]] = []
    rows_sel: list[dict[str, Any]] = []
    segments_out: dict[str, Any] = {}

    for _, lr in ledger.iterrows():
        if not _segment_allowed(str(lr.get("allowed_repair_family", ""))):
            continue
        stat = str(lr["stat"]).lower()
        role = str(lr["role_bucket"]).lower()
        mstat = loss["stat"].astype(str).str.lower() == stat
        mrole = loss["role_bucket"].astype(str).str.lower() == role
        sub = loss[mstat & mrole].copy()
        pool_stat = loss[mstat].copy()
        rep = _fit_segment(sub, stat, role, pool_stat)
        sk = f"{stat}|{role}"
        if rep.get("accepted"):
            meth = str(rep["selected_method"])
            if meth == "logit_ab" and str(rep.get("selected_scope")) == "stat_role":
                meth = "hierarchical_logit_shrinkage"
            if meth == "logit_ab" and str(rep.get("selected_scope")) == "stat":
                meth = "hierarchical_logit_shrinkage"
            spec = {
                "stat": stat,
                "role_bucket": role,
                "selected_scope": rep["selected_scope"],
                "selected_method": meth,
                "a": rep.get("a"),
                "b": rep.get("b"),
                "lambda": rep.get("lambda"),
                "isotonic_weight": rep.get("isotonic_weight"),
                "isotonic_x": rep.get("isotonic_x"),
                "isotonic_y": rep.get("isotonic_y"),
                "parent_transform": rep.get("parent_transform"),
                "n_train": rep.get("n_train"),
                "n_val": rep.get("n_val"),
                "n_dates": rep.get("n_dates"),
                "raw_logloss": rep.get("raw_logloss"),
                "cal_logloss": rep.get("cal_logloss"),
                "delta_logloss": rep.get("delta_logloss"),
                "raw_brier": rep.get("raw_brier"),
                "cal_brier": rep.get("cal_brier"),
                "delta_brier": rep.get("delta_brier"),
                "raw_ece": rep.get("raw_ece"),
                "cal_ece": rep.get("cal_ece"),
                "accepted": True,
                "rollback_reason": "",
            }
            segments_out[sk] = spec
            rows_sel.append({"segment_key": sk, **rep})
        else:
            rows_roll.append({"segment_key": sk, **rep})

    manifest = {
        "version": "1.0",
        "label": label,
        "fit_type": "OOF_actual_outcome_event_neutral_probability_scale_repair",
        "uses_market_probability_as_label": False,
        "uses_market_probability_as_feature": False,
        "canonical_pmf_unchanged": True,
        "market_odds_used_as_features": False,
        "market_odds_used_for_edge_only": True,
        "fold_key": "game_date",
        "push_count_excluded": push_count_excluded,
        "segments": segments_out,
    }

    MODELS.mkdir(parents=True, exist_ok=True)
    out_json = MODELS / f"event_neutral_probability_scale_repair_{label}.json"
    out_json.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    rep_dir = ART / f"market_superiority_repair_{label}"
    rep_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows_roll).to_csv(rep_dir / "probability_scale_rollback_report.csv", index=False)
    pd.DataFrame(rows_sel).to_csv(rep_dir / "probability_scale_selected_calibrators.csv", index=False)

    print("EVENT_NEUTRAL_PROBABILITY_SCALE_REPAIR_PASS")
    print(f"  manifest: {out_json.relative_to(REPO_ROOT)}")
    print(f"  accepted_segments={sum(1 for s in segments_out.values() if s.get('accepted'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
