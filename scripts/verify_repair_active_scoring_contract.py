#!/usr/bin/env python3
"""Verify strict superiority report scores repaired active probabilities."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ART = REPO_ROOT / "artifacts" / "model_diagnostics"


def _ll(p: float, y: float) -> float:
    p = max(min(float(p), 1.0 - 1e-12), 1e-12)
    yy = float(y)
    return float(-(yy * math.log(p) + (1.0 - yy) * math.log(1.0 - p)))


def _brier(p: float, y: float) -> float:
    return float((float(p) - float(y)) ** 2)


def _scoring_mask(sub: pd.DataFrame) -> pd.Series:
    m = pd.Series(True, index=sub.index)
    for c in ("model_event_logloss", "market_event_logloss", "model_brier", "market_brier"):
        if c in sub.columns:
            m &= sub[c].notna()
    return m


def _finite_mean(s: pd.Series) -> float | None:
    x = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if x.empty:
        return None
    return float(x.mean())


def _build_script_has_flags() -> tuple[bool, str]:
    p = REPO_ROOT / "scripts" / "build_event_market_loss_rows.py"
    t = p.read_text(encoding="utf-8")
    ok_e = "--event-prob-calibration-manifest" in t
    ok_m = "--pmf-mean-shift-manifest" in t
    return ok_e and ok_m, "build_event_market_loss_rows.py missing manifest CLI flags"


def _canonical_hashes_from_inventory(inv: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not inv.is_file():
        return out
    df = pd.read_csv(inv)
    for _, r in df.iterrows():
        cp = r.get("canonical_path")
        if cp is None or (isinstance(cp, float) and pd.isna(cp)):
            continue
        p = REPO_ROOT / str(cp)
        if p.is_file():
            out[str(cp)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def compare_strict_report_to_active_probs(combo: pd.DataFrame, sr: pd.DataFrame) -> tuple[list[tuple], list[tuple]]:
    """Return (metric_mismatches, raw_traps) for strict CSV vs recomputed active/raw logloss."""
    mismatches: list[tuple] = []
    raw_traps: list[tuple] = []
    for _, row in sr.iterrows():
        stat = str(row["stat"]).lower()
        role = str(row["role_bucket"])
        sub = combo[
            (combo["stat"].astype(str).str.lower() == stat)
            & (combo["role_bucket"].astype(str) == role)
        ]
        if sub.empty:
            continue
        msk = _scoring_mask(sub)
        if int(msk.sum()) == 0:
            continue
        s2 = sub.loc[msk]
        csv_ll = row.get("model_logloss_avg")
        csv_br = row.get("model_brier_avg")
        if pd.isna(csv_ll) and pd.isna(csv_br):
            continue
        ll_act = [_ll(float(a), float(h)) for a, h in zip(s2["model_prob_over_active"], s2["hit_result"])]
        br_act = [_brier(float(a), float(h)) for a, h in zip(s2["model_prob_over_active"], s2["hit_result"])]
        m_ll_a = float(np.mean(ll_act)) if ll_act else None
        m_br_a = float(np.mean(br_act)) if br_act else None
        m_ll_st = _finite_mean(s2["model_event_logloss"])
        m_br_st = _finite_mean(s2["model_brier"])
        if m_ll_st is not None and m_ll_a is not None and abs(m_ll_st - m_ll_a) > 5e-4:
            mismatches.append((stat, role, "logloss", m_ll_st, m_ll_a))
        if m_br_st is not None and m_br_a is not None and abs(m_br_st - m_br_a) > 5e-4:
            mismatches.append((stat, role, "brier", m_br_st, m_br_a))

        ll_raw = [_ll(float(a), float(h)) for a, h in zip(s2["model_prob_over_raw"], s2["hit_result"])]
        m_ll_r = float(np.mean(ll_raw)) if ll_raw else None
        if (
            m_ll_st is not None
            and m_ll_r is not None
            and m_ll_a is not None
            and csv_ll is not None
            and not pd.isna(csv_ll)
            and abs(m_ll_r - m_ll_a) > 1e-3
            and abs(float(csv_ll) - m_ll_r) < 5e-4
            and abs(float(csv_ll) - m_ll_a) > 5e-4
        ):
            raw_traps.append((stat, role, float(csv_ll), m_ll_r, m_ll_a))
    return mismatches, raw_traps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--dates-file", required=True)
    ap.add_argument("--event-prob-calibration-manifest", required=True)
    ap.add_argument("--pmf-mean-shift-manifest", required=True)
    args = ap.parse_args()
    label = str(args.label)

    ok_cli, cli_msg = _build_script_has_flags()
    if not ok_cli:
        print(f"FATAL: {cli_msg}", file=sys.stderr)
        return 2

    loss_path = ART / f"event_market_loss_rows_{label}.parquet"
    sr_path = ART / f"event_market_superiority_{label}" / "stat_role_market_superiority.csv"
    if not loss_path.is_file() or not sr_path.is_file():
        print(f"FATAL: missing {loss_path} or {sr_path}", file=sys.stderr)
        return 2

    combo = pd.read_parquet(loss_path)
    sr = pd.read_csv(sr_path)

    required = (
        "model_prob_over_raw",
        "model_prob_over_active",
        "model_event_logloss",
        "model_brier",
        "market_event_logloss",
        "market_brier",
        "hit_result",
        "stat",
        "role_bucket",
    )
    miss = [c for c in required if c not in combo.columns]
    if miss:
        print(f"FATAL: ACTIVE_PROB_COLUMNS_MISSING {miss}", file=sys.stderr)
        return 2

    if "model_prob_over_after_pmf_mean_shift" not in combo.columns:
        print("FATAL: ACTIVE_PROB_COLUMNS_MISSING model_prob_over_after_pmf_mean_shift", file=sys.stderr)
        return 2
    if "probability_scale_repair_method" not in combo.columns:
        print("FATAL: ACTIVE_PROB_COLUMNS_MISSING probability_scale_repair_method", file=sys.stderr)
        return 2
    if "pmf_mean_shift_repair_applied" not in combo.columns:
        print("FATAL: ACTIVE_PROB_COLUMNS_MISSING pmf_mean_shift_repair_applied", file=sys.stderr)
        return 2

    ev_man = Path(args.event_prob_calibration_manifest)
    if not ev_man.is_absolute():
        ev_man = REPO_ROOT / ev_man
    ms_man = Path(args.pmf_mean_shift_manifest)
    if not ms_man.is_absolute():
        ms_man = REPO_ROOT / ms_man
    if not ev_man.is_file() or not ms_man.is_file():
        print("FATAL: MANIFEST_NOT_APPLIED missing manifest file(s)", file=sys.stderr)
        return 2

    ev = json.loads(ev_man.read_text(encoding="utf-8"))
    ms = json.loads(ms_man.read_text(encoding="utf-8"))
    n_ev = sum(
        1
        for s in (ev.get("segments") or {}).values()
        if isinstance(s, dict) and s.get("accepted")
    )
    n_ms = sum(
        1
        for s in (ms.get("segments") or {}).values()
        if isinstance(s, dict) and s.get("accepted")
    )
    if n_ev == 0 and n_ms == 0:
        print("WARN: both manifests have zero accepted segments — contract checks relaxed", file=sys.stderr)

    m_active = combo["model_prob_over_active"].dropna()
    if len(m_active) and ((m_active < 0) | (m_active > 1)).any():
        print("FATAL: model_prob_over_active out of [0,1]", file=sys.stderr)
        return 2

    diff = (pd.to_numeric(combo["model_prob_over_active"], errors="coerce") - pd.to_numeric(
        combo["model_prob_over_raw"], errors="coerce"
    )).abs()
    matched = combo.get("join_status", pd.Series(["matched"] * len(combo))) == "matched"
    n_changed = int((matched & (diff > 1e-8)).sum())
    if n_ev + n_ms > 0 and n_changed == 0:
        print("FATAL: ACTIVE_PROB_NOT_DIFFERENT_WHEN_REPAIR_APPLIES", file=sys.stderr)
        return 2

    if "model_probability_for_side" in combo.columns:
        d2 = (
            pd.to_numeric(combo.loc[matched, "model_prob_over_active"], errors="coerce")
            - pd.to_numeric(combo.loc[matched, "model_probability_for_side"], errors="coerce")
        ).abs()
        if d2.notna().any() and float(d2.fillna(0).max()) > 1e-6:
            print("FATAL: model_probability_for_side != model_prob_over_active on matched rows", file=sys.stderr)
            return 2

    inv = Path(args.dates_file)
    if not inv.is_absolute():
        inv = REPO_ROOT / inv
    canon_hashes = _canonical_hashes_from_inventory(inv)

    mismatches, raw_traps = compare_strict_report_to_active_probs(combo, sr)

    canon_hashes_end = _canonical_hashes_from_inventory(inv)
    if canon_hashes != canon_hashes_end:
        print("FATAL: CANONICAL_PMF_MUTATED canonical_path files changed during verify", file=sys.stderr)
        return 2

    if mismatches:
        print(f"FATAL: STRICT_REPORT_METRICS_MISMATCH {mismatches[:8]}", file=sys.stderr)
        return 2
    if raw_traps:
        print(f"FATAL: STRICT_REPORT_USED_RAW_PROBABILITY {raw_traps[:8]}", file=sys.stderr)
        return 2

    print("REPAIR_ACTIVE_SCORING_CONTRACT_PASS")
    print(json.dumps({"n_rows_loss": len(combo), "n_prob_changed_rows": n_changed, "canonical_files_hashed": len(canon_hashes)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
