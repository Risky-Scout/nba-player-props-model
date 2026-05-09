#!/usr/bin/env python3
"""Production PMF math validator (date-scoped).

Independently audits PMF files written by the production pipeline to verify
mathematical correctness. Does NOT trust schema-only checks — recomputes
sums and validity from atom probabilities.

Per-file validation priority:
  1. pmf_json / pmf_active (atom dict/list per row)
  2. outcome-level long form (one row per (prop, k) with p_k / probability)
  3. true atom columns (p_0, p_1, ...)
  4. survival columns (p_ge_*) — checked for monotonicity only

NEVER sums p_ge_* survival columns as atom probabilities.
Cross-checks reported pmf_valid / pmf_sum_error against recomputed values.

Date scope:
  --date YYYY-MM-DD  validate only that delivery date.
  --latest           (default) validate only the latest delivery date.
  --all-history      validate every delivery date on disk.
  --strict-history   with --all-history, treat legacy placeholder files
                     as hard failures.

Legacy detection: a Derek outcome-level file with exactly the columns
{player_id, player_name, stat, line, book, k, p_k} where every k=0 and
every p_k=0 is classified as LEGACY_DEREK_PLACEHOLDER_OUTCOME_LEVEL.
Such files are produced by historical pre-Phase-13AB Derek snapshot
runs and are NOT a current pipeline defect.

Output:
  artifacts/pmf_math_validation/<timestamp>/pmf_math_validation.json
  artifacts/pmf_math_validation/<timestamp>/pmf_math_validation.md
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SUM_TOLERANCE = 1e-6
REPORTED_SUM_TOLERANCE = 1e-9

GLOB_PATTERNS = [
    "deliveries/*/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet",
    "deliveries/*/wizard_of_odds/full_pmfs_wide.parquet",
    "deliveries/*/wizard_of_odds/full_pmfs_outcome_level.parquet",
    "deliveries/*/pmf_model_review_package/05_FULL_PMF_WIDE.parquet",
    "deliveries/*/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.parquet",
    "deliveries/*/derek_game_snapshots/**/*.parquet",
]

ATOM_COL_RE = re.compile(r"^p_(\d+)$")
SURVIVAL_COL_RE = re.compile(r"^p_ge_(\d+)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

LEGACY_DEREK_PLACEHOLDER_COLS = frozenset({
    "player_id", "player_name", "stat", "line", "book", "k", "p_k"
})


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _extract_date_from_path(p: Path) -> str | None:
    parts = p.parts
    for i, part in enumerate(parts):
        if part == "deliveries" and i + 1 < len(parts):
            d = parts[i + 1]
            if DATE_RE.match(d):
                return d
    return None


def _is_legacy_derek_placeholder(path: Path, df: pd.DataFrame) -> bool:
    if "derek_game_snapshots" not in str(path):
        return False
    if set(df.columns) != LEGACY_DEREK_PLACEHOLDER_COLS:
        return False
    if "k" not in df.columns or "p_k" not in df.columns or len(df) == 0:
        return False
    try:
        k_all_zero = bool((pd.to_numeric(df["k"], errors="coerce").fillna(-1) == 0).all())
        p_all_zero = bool((pd.to_numeric(df["p_k"], errors="coerce").fillna(-1) == 0).all())
    except Exception:
        return False
    return k_all_zero and p_all_zero


def _parse_pmf_cell(cell: Any) -> tuple[np.ndarray | None, str | None]:
    if cell is None:
        return None, "null"
    if isinstance(cell, float) and not math.isfinite(cell):
        return None, "nonfinite_scalar"
    obj = cell
    if isinstance(cell, (bytes, bytearray)):
        try:
            obj = cell.decode("utf-8")
        except Exception:
            return None, "bytes_decode_error"
    if isinstance(obj, str):
        s = obj.strip()
        if not s:
            return None, "empty_string"
        try:
            obj = json.loads(s)
        except Exception as e:
            return None, f"json_parse:{type(e).__name__}"
    if isinstance(obj, dict):
        if not obj:
            return None, "empty_dict"
        try:
            keys = [int(k) for k in obj.keys()]
        except Exception:
            return None, "non_integer_keys"
        K = max(keys) + 1 if keys else 0
        if K <= 0:
            return None, "zero_length"
        a = np.zeros(K, dtype=float)
        for k, v in obj.items():
            try:
                a[int(k)] = float(v)
            except Exception:
                return None, "non_numeric_value"
        return a, None
    if isinstance(obj, (list, tuple, np.ndarray)):
        try:
            a = np.asarray([float(v) for v in obj], dtype=float)
        except Exception:
            return None, "non_numeric_seq"
        if a.size == 0:
            return None, "zero_length"
        return a, None
    return None, f"unsupported_type:{type(obj).__name__}"


def _classify(atoms: np.ndarray) -> dict:
    finite = bool(np.all(np.isfinite(atoms)))
    if not finite:
        return {"finite": False, "nonneg": False, "sum": float("nan"),
                "sum_error": float("nan"), "valid": "non_finite"}
    nonneg = bool(np.all(atoms >= -1e-9))
    s = float(atoms.sum())
    sum_err = float(abs(s - 1.0))
    if not nonneg:
        valid = "negative_prob"
    elif sum_err > SUM_TOLERANCE:
        valid = "bad_shape"
    else:
        valid = "ok"
    return {"finite": True, "nonneg": nonneg, "sum": s,
            "sum_error": sum_err, "valid": valid}


def _detect_atom_cols(cols):
    out = []
    for c in cols:
        m = ATOM_COL_RE.match(c)
        if m:
            out.append((c, int(m.group(1))))
    out.sort(key=lambda x: x[1])
    return out


def _detect_survival_cols(cols):
    out = []
    for c in cols:
        m = SURVIVAL_COL_RE.match(c)
        if m:
            out.append((c, int(m.group(1))))
    out.sort(key=lambda x: x[1])
    return out


def _detect_outcome_level(df: pd.DataFrame):
    cols = set(df.columns)
    k_col = next((c for c in ("k", "outcome", "outcome_value", "support_k") if c in cols), None)
    p_col = next((c for c in ("p_k", "probability", "p", "prob") if c in cols), None)
    if k_col and p_col:
        return k_col, p_col
    return None


def _detect_group_keys(df: pd.DataFrame):
    cands = ["player_id", "player_name", "stat", "game_id", "line", "book",
            "snapshot_type", "snapshot_time_utc"]
    return [c for c in cands if c in df.columns]


def _validate_file(path: Path) -> dict:
    rec = {
        "file": str(path),
        "rel_file": str(path.relative_to(REPO_ROOT)) if str(path).startswith(str(REPO_ROOT)) else str(path),
        "delivery_date": _extract_date_from_path(path),
        "is_legacy_placeholder": False,
        "legacy_classification": None,
        "mode": None,
        "rows": 0, "groups": 0,
        "rows_checked": 0, "groups_checked": 0,
        "valid_ok": 0, "valid_bad_shape": 0,
        "valid_negative_prob": 0, "valid_non_finite": 0,
        "bad_parse": 0,
        "negative_count": 0, "nonfinite_count": 0,
        "reported_valid_mismatch": 0,
        "reported_sum_error_mismatch": 0,
        "survival_only_tail_unverifiable": 0,
        "sum_abs_errors": [],
        "by_target_stat": defaultdict(lambda: {"checked": 0, "valid_ok": 0, "valid_bad": 0}),
        "errors": [],
    }
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        rec["errors"].append(f"read_error:{type(e).__name__}:{e}")
        return rec
    rec["rows"] = int(len(df))
    cols = list(df.columns)

    # Legacy detection FIRST — short-circuit before any validation
    if _is_legacy_derek_placeholder(path, df):
        rec["mode"] = "legacy_derek_placeholder"
        rec["is_legacy_placeholder"] = True
        rec["legacy_classification"] = "LEGACY_DEREK_PLACEHOLDER_OUTCOME_LEVEL"
        return rec

    has_pmf_valid = "pmf_valid" in cols
    has_pmf_sum_error = "pmf_sum_error" in cols
    stat_col = "stat" if "stat" in cols else ("target_stat" if "target_stat" in cols else None)

    pmf_col = "pmf_json" if "pmf_json" in cols else ("pmf_active" if "pmf_active" in cols else None)

    # Mode 1: row-level pmf_json/pmf_active
    if pmf_col is not None:
        rec["mode"] = f"row_{pmf_col}"
        for idx in range(len(df)):
            row = df.iloc[idx]
            atoms, err = _parse_pmf_cell(row[pmf_col])
            if atoms is None:
                rec["bad_parse"] += 1
                continue
            cls = _classify(atoms)
            rec["rows_checked"] += 1
            if math.isfinite(cls["sum_error"]):
                rec["sum_abs_errors"].append(cls["sum_error"])
            if not cls["finite"]:
                rec["nonfinite_count"] += 1
            elif not cls["nonneg"]:
                rec["negative_count"] += int(np.sum(atoms < -1e-9))
            v = cls["valid"]
            if v == "ok":
                rec["valid_ok"] += 1
            elif v == "bad_shape":
                rec["valid_bad_shape"] += 1
            elif v == "negative_prob":
                rec["valid_negative_prob"] += 1
            elif v == "non_finite":
                rec["valid_non_finite"] += 1
            if has_pmf_valid:
                rep = row.get("pmf_valid")
                if rep is not None and not (isinstance(rep, float) and math.isnan(rep)):
                    if str(rep) != v:
                        rec["reported_valid_mismatch"] += 1
            if has_pmf_sum_error and cls["finite"]:
                rep_err = row.get("pmf_sum_error")
                if rep_err is not None and not (isinstance(rep_err, float) and math.isnan(rep_err)):
                    try:
                        if abs(float(rep_err) - cls["sum_error"]) > REPORTED_SUM_TOLERANCE:
                            rec["reported_sum_error_mismatch"] += 1
                    except Exception:
                        rec["reported_sum_error_mismatch"] += 1
            if stat_col is not None:
                sv = str(row.get(stat_col))
                rec["by_target_stat"][sv]["checked"] += 1
                if v == "ok":
                    rec["by_target_stat"][sv]["valid_ok"] += 1
                else:
                    rec["by_target_stat"][sv]["valid_bad"] += 1
        return rec

    # Mode 2: outcome-level long form
    ol = _detect_outcome_level(df)
    if ol is not None:
        k_col, p_col = ol
        keys = _detect_group_keys(df)
        if not keys:
            rec["errors"].append("outcome_level_no_grouping_keys")
            return rec
        rec["mode"] = f"outcome_level k={k_col} p={p_col}"
        probs = pd.to_numeric(df[p_col], errors="coerce")
        rec["nonfinite_count"] += int(((~np.isfinite(probs.fillna(np.inf)))).sum() - probs.isna().sum())
        rec["negative_count"] += int((probs < -1e-9).sum())
        try:
            grouped = df.groupby(keys, dropna=False)
        except Exception as e:
            rec["errors"].append(f"groupby_error:{type(e).__name__}:{e}")
            return rec
        rec["groups"] = int(grouped.ngroups)
        for _, g in grouped:
            gp = pd.to_numeric(g[p_col], errors="coerce").to_numpy()
            rec["groups_checked"] += 1
            if not np.all(np.isfinite(gp)):
                rec["valid_non_finite"] += 1
                v = "non_finite"
                sum_err = None
            elif np.any(gp < -1e-9):
                rec["valid_negative_prob"] += 1
                v = "negative_prob"
                sum_err = None
            else:
                s = float(gp.sum())
                sum_err = float(abs(s - 1.0))
                rec["sum_abs_errors"].append(sum_err)
                if sum_err <= SUM_TOLERANCE:
                    rec["valid_ok"] += 1
                    v = "ok"
                else:
                    rec["valid_bad_shape"] += 1
                    v = "bad_shape"
            if has_pmf_valid:
                rep_set = set(g["pmf_valid"].dropna().astype(str).unique())
                if len(rep_set) == 1:
                    rep_val = next(iter(rep_set))
                    if rep_val != v:
                        rec["reported_valid_mismatch"] += 1
            if has_pmf_sum_error and sum_err is not None:
                rep_errs = pd.to_numeric(g["pmf_sum_error"], errors="coerce").dropna()
                if len(rep_errs) > 0:
                    rep_max = float(rep_errs.abs().max())
                    if abs(rep_max - sum_err) > REPORTED_SUM_TOLERANCE:
                        rec["reported_sum_error_mismatch"] += 1
            if stat_col is not None and stat_col in g.columns:
                sv = str(g[stat_col].iloc[0])
                rec["by_target_stat"][sv]["checked"] += 1
                if v == "ok":
                    rec["by_target_stat"][sv]["valid_ok"] += 1
                else:
                    rec["by_target_stat"][sv]["valid_bad"] += 1
        return rec

    # Mode 3: true atom columns p_0, p_1, ...
    atom_cols = _detect_atom_cols(cols)
    if atom_cols and atom_cols[0][1] == 0:
        ks = [k for _, k in atom_cols]
        if ks == list(range(len(ks))) and len(atom_cols) >= 3:
            rec["mode"] = f"true_atoms p_0..p_{ks[-1]}"
            atom_names = [c for c, _ in atom_cols]
            arr = df[atom_names].to_numpy(dtype=float)
            for i in range(arr.shape[0]):
                cls = _classify(arr[i])
                rec["rows_checked"] += 1
                if math.isfinite(cls["sum_error"]):
                    rec["sum_abs_errors"].append(cls["sum_error"])
                if not cls["finite"]:
                    rec["nonfinite_count"] += 1
                elif not cls["nonneg"]:
                    rec["negative_count"] += int(np.sum(arr[i] < -1e-9))
                v = cls["valid"]
                if v == "ok":
                    rec["valid_ok"] += 1
                elif v == "bad_shape":
                    rec["valid_bad_shape"] += 1
                elif v == "negative_prob":
                    rec["valid_negative_prob"] += 1
                elif v == "non_finite":
                    rec["valid_non_finite"] += 1
            return rec

    # Mode 4: survival-only (p_ge_*). Check monotonicity; never sum as atoms.
    surv_cols = _detect_survival_cols(cols)
    if surv_cols:
        rec["mode"] = f"survival_only p_ge_{surv_cols[0][1]}..p_ge_{surv_cols[-1][1]}"
        surv_names = [c for c, _ in surv_cols]
        S = df[surv_names].to_numpy(dtype=float)
        if S.shape[1] >= 2:
            mono_ok_per_row = np.all(np.diff(S, axis=1) <= 1e-9, axis=1)
        else:
            mono_ok_per_row = np.ones(S.shape[0], dtype=bool)
        finite_per_row = np.all(np.isfinite(S), axis=1)
        nonneg_per_row = np.all(S >= -1e-9, axis=1)
        ok_mask = mono_ok_per_row & finite_per_row & nonneg_per_row
        rec["valid_ok"] += int(ok_mask.sum())
        rec["valid_bad_shape"] += int((~mono_ok_per_row & finite_per_row & nonneg_per_row).sum())
        rec["valid_non_finite"] += int((~finite_per_row).sum())
        rec["valid_negative_prob"] += int((finite_per_row & ~nonneg_per_row).sum())
        rec["nonfinite_count"] += int((~np.isfinite(S)).sum())
        rec["negative_count"] += int((S < -1e-9).sum())
        rec["rows_checked"] = int(len(df))
        rec["survival_only_tail_unverifiable"] = int(len(df))
        return rec

    rec["errors"].append("no_pmf_data_columns_detected")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sg = ap.add_mutually_exclusive_group()
    sg.add_argument("--date", help="Validate only this delivery date (YYYY-MM-DD).")
    sg.add_argument("--latest", action="store_true",
                    help="Validate only the latest delivery date (default).")
    sg.add_argument("--all-history", action="store_true",
                    help="Validate every delivery date on disk.")
    ap.add_argument("--strict-history", action="store_true",
                    help="With --all-history, treat legacy placeholder files as hard failures.")
    args = ap.parse_args(argv)

    all_files: list[Path] = []
    for pat in GLOB_PATTERNS:
        for p in sorted(REPO_ROOT.glob(pat)):
            if p.is_file():
                all_files.append(p)
    all_files = sorted(set(all_files))

    all_dates = set()
    for p in all_files:
        d = _extract_date_from_path(p)
        if d:
            all_dates.add(d)

    if args.date:
        if not DATE_RE.match(args.date):
            print(f"PRODUCTION_PMF_MATH_VALIDATION_FAIL  bad --date format: {args.date}", file=sys.stderr)
            return 2
        date_scope = {args.date}
        scope_mode = "date"
        scope_label = f"date={args.date}"
    elif args.all_history:
        date_scope = set(all_dates)
        scope_mode = "all_history"
        scope_label = f"all_history(n_dates={len(all_dates)})"
    else:
        if not all_dates:
            print("PRODUCTION_PMF_MATH_VALIDATION_FAIL")
            print("  files_checked: 0")
            print("  reason: no_delivery_dates_found_on_disk")
            return 2
        latest = max(all_dates)
        date_scope = {latest}
        scope_mode = "latest"
        scope_label = f"latest={latest}"

    files_in_scope: list[Path] = []
    for p in all_files:
        d = _extract_date_from_path(p)
        if d is None:
            continue
        if d in date_scope:
            files_in_scope.append(p)

    if not files_in_scope:
        print("PRODUCTION_PMF_MATH_VALIDATION_FAIL")
        print(f"  scope: {scope_label}")
        print(f"  files_checked: 0")
        print(f"  reason: no_files_in_scope")
        return 2

    file_recs = [_validate_file(p) for p in files_in_scope]

    legacy_recs = [r for r in file_recs if r.get("is_legacy_placeholder")]
    non_legacy_recs = [r for r in file_recs if not r.get("is_legacy_placeholder")]

    files_checked = len(non_legacy_recs)
    rows_checked = sum(r["rows_checked"] for r in non_legacy_recs)
    groups_checked = sum(r["groups_checked"] for r in non_legacy_recs)
    valid_ok = sum(r["valid_ok"] for r in non_legacy_recs)
    valid_bad_shape = sum(r["valid_bad_shape"] for r in non_legacy_recs)
    valid_negative = sum(r["valid_negative_prob"] for r in non_legacy_recs)
    valid_nonfinite = sum(r["valid_non_finite"] for r in non_legacy_recs)
    bad_parse = sum(r["bad_parse"] for r in non_legacy_recs)
    negative_count = sum(r["negative_count"] for r in non_legacy_recs)
    nonfinite_count = sum(r["nonfinite_count"] for r in non_legacy_recs)
    rep_valid_mm = sum(r["reported_valid_mismatch"] for r in non_legacy_recs)
    rep_sum_err_mm = sum(r["reported_sum_error_mismatch"] for r in non_legacy_recs)
    surv_unver = sum(r["survival_only_tail_unverifiable"] for r in non_legacy_recs)

    all_errs = []
    for r in non_legacy_recs:
        all_errs.extend(e for e in r["sum_abs_errors"] if math.isfinite(e))
    sum_max = float(max(all_errs)) if all_errs else 0.0
    sum_p99 = float(np.percentile(all_errs, 99)) if all_errs else 0.0

    total = rows_checked + groups_checked
    pmf_valid_rate = (valid_ok / total) if total > 0 else 0.0

    failed = False
    fail_reasons = []
    if files_checked == 0 and not legacy_recs:
        failed = True; fail_reasons.append("no_files_scanned")
    if files_checked > 0 and total == 0:
        failed = True; fail_reasons.append("no_rows_or_groups_checked")
    if bad_parse > 0:
        failed = True; fail_reasons.append(f"bad_parse_count={bad_parse}")
    if negative_count > 0:
        failed = True; fail_reasons.append(f"negative_probability_count={negative_count}")
    if nonfinite_count > 0:
        failed = True; fail_reasons.append(f"nonfinite_probability_count={nonfinite_count}")
    if sum_max > SUM_TOLERANCE:
        failed = True; fail_reasons.append(f"pmf_sum_abs_err_max={sum_max:.3e}>{SUM_TOLERANCE:.0e}")
    if rep_valid_mm > 0:
        failed = True; fail_reasons.append(f"reported_valid_mismatch_count={rep_valid_mm}")
    if rep_sum_err_mm > 0:
        failed = True; fail_reasons.append(f"reported_sum_error_mismatch_count={rep_sum_err_mm}")

    legacy_count = len(legacy_recs)
    if legacy_count > 0:
        if scope_mode == "all_history" and not args.strict_history:
            legacy_failed = 0
        else:
            legacy_failed = legacy_count
            failed = True
            fail_reasons.append(f"legacy_derek_placeholder_in_scope={legacy_count}")
    else:
        legacy_failed = 0

    status = "PRODUCTION_PMF_MATH_VALIDATION_FAIL" if failed else "PRODUCTION_PMF_MATH_VALIDATION_PASS"

    agg_by_stat: dict[str, dict] = {}
    for r in non_legacy_recs:
        for stat, sub in r["by_target_stat"].items():
            d = agg_by_stat.setdefault(stat, {"checked": 0, "valid_ok": 0, "valid_bad": 0})
            d["checked"] += sub.get("checked", 0)
            d["valid_ok"] += sub.get("valid_ok", 0)
            d["valid_bad"] += sub.get("valid_bad", 0)

    by_file = []
    for r in file_recs:
        by_file.append({
            "rel_file": r["rel_file"],
            "delivery_date": r["delivery_date"],
            "mode": r["mode"],
            "is_legacy_placeholder": bool(r.get("is_legacy_placeholder", False)),
            "legacy_classification": r.get("legacy_classification"),
            "rows": r["rows"], "rows_checked": r["rows_checked"],
            "groups_checked": r["groups_checked"],
            "valid_ok": r["valid_ok"], "valid_bad_shape": r["valid_bad_shape"],
            "valid_negative_prob": r["valid_negative_prob"],
            "valid_non_finite": r["valid_non_finite"],
            "bad_parse": r["bad_parse"],
            "negative_count": r["negative_count"],
            "nonfinite_count": r["nonfinite_count"],
            "reported_valid_mismatch": r["reported_valid_mismatch"],
            "reported_sum_error_mismatch": r["reported_sum_error_mismatch"],
            "survival_only_tail_unverifiable": r["survival_only_tail_unverifiable"],
            "sum_abs_err_max": float(max(r["sum_abs_errors"])) if r["sum_abs_errors"] else 0.0,
            "errors": r["errors"],
        })

    summary = {
        "status": status, "fail_reasons": fail_reasons,
        "scope_mode": scope_mode, "scope_label": scope_label,
        "scope_dates": sorted(date_scope),
        "strict_history": bool(args.strict_history),
        "files_checked": files_checked,
        "rows_checked": rows_checked, "groups_checked": groups_checked,
        "pmf_valid_rate": pmf_valid_rate,
        "valid_ok": valid_ok, "valid_bad_shape": valid_bad_shape,
        "valid_negative_prob": valid_negative, "valid_non_finite": valid_nonfinite,
        "bad_parse_count": bad_parse,
        "negative_probability_count": negative_count,
        "nonfinite_probability_count": nonfinite_count,
        "pmf_sum_abs_err_max": sum_max, "pmf_sum_abs_err_p99": sum_p99,
        "reported_valid_mismatch_count": rep_valid_mm,
        "reported_sum_error_mismatch_count": rep_sum_err_mm,
        "survival_only_tail_unverifiable_count": surv_unver,
        "legacy_historical_files": legacy_count,
        "legacy_historical_failures": legacy_failed,
        "sum_tolerance": SUM_TOLERANCE,
        "reported_sum_tolerance": REPORTED_SUM_TOLERANCE,
        "by_target_stat": agg_by_stat,
        "by_file": by_file,
    }

    ts = _utc_ts()
    out_dir = REPO_ROOT / "artifacts" / "pmf_math_validation" / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pmf_math_validation.json").write_text(
        json.dumps(summary, indent=2, default=str))

    md = ["# Production PMF Math Validation", "",
          f"**Status: {status}**", "",
          f"- timestamp_utc: {ts}",
          f"- scope_mode: {scope_mode}",
          f"- scope_label: {scope_label}",
          f"- strict_history: {args.strict_history}",
          f"- files_checked (non-legacy): {files_checked}",
          f"- rows_checked: {rows_checked}",
          f"- groups_checked: {groups_checked}",
          f"- pmf_valid_rate: {pmf_valid_rate:.6f}",
          f"- pmf_sum_abs_err_max: {sum_max:.3e}",
          f"- pmf_sum_abs_err_p99: {sum_p99:.3e}",
          f"- bad_parse_count: {bad_parse}",
          f"- negative_probability_count: {negative_count}",
          f"- nonfinite_probability_count: {nonfinite_count}",
          f"- reported_valid_mismatch_count: {rep_valid_mm}",
          f"- reported_sum_error_mismatch_count: {rep_sum_err_mm}",
          f"- survival_only_tail_unverifiable_count: {surv_unver}",
          f"- legacy_historical_files: {legacy_count}",
          f"- legacy_historical_failures: {legacy_failed}", ""]
    if fail_reasons:
        md.append("## Fail reasons")
        for fr in fail_reasons:
            md.append(f"- {fr}")
        md.append("")
    if legacy_recs:
        md.append("## Legacy historical placeholder files (LEGACY_DEREK_PLACEHOLDER_OUTCOME_LEVEL)")
        for r in legacy_recs:
            md.append(f"- `{r['rel_file']}` (date={r['delivery_date']}, rows={r['rows']})")
        md.append("")
    md.append("## By-file (non-legacy)")
    md.append("")
    for f in by_file:
        if f["is_legacy_placeholder"]:
            continue
        md.append(f"### `{f['rel_file']}`")
        md.append(f"- date: {f['delivery_date']}, mode: {f['mode']}")
        md.append(f"- rows: {f['rows']}, rows_checked: {f['rows_checked']}, groups_checked: {f['groups_checked']}")
        md.append(f"- valid_ok: {f['valid_ok']}, bad_shape: {f['valid_bad_shape']}, neg: {f['valid_negative_prob']}, nonfinite: {f['valid_non_finite']}")
        md.append(f"- bad_parse: {f['bad_parse']}, sum_abs_err_max: {f['sum_abs_err_max']:.3e}")
        md.append(f"- reported_valid_mismatch: {f['reported_valid_mismatch']}, reported_sum_error_mismatch: {f['reported_sum_error_mismatch']}")
        if f["errors"]:
            md.append(f"- errors: {f['errors']}")
        md.append("")
    if agg_by_stat:
        md.append("## By target_stat")
        md.append("")
        for stat, d in sorted(agg_by_stat.items()):
            md.append(f"- {stat}: checked={d['checked']}, valid_ok={d['valid_ok']}, valid_bad={d['valid_bad']}")
        md.append("")
    (out_dir / "pmf_math_validation.md").write_text("\n".join(md))

    print(status)
    print(f"  output_dir: {out_dir.relative_to(REPO_ROOT)}")
    print(f"  scope_mode: {scope_mode}")
    print(f"  scope_label: {scope_label}")
    print(f"  strict_history: {args.strict_history}")
    print(f"  files_checked: {files_checked}")
    print(f"  rows_checked: {rows_checked}")
    print(f"  groups_checked: {groups_checked}")
    print(f"  pmf_valid_rate: {pmf_valid_rate:.6f}")
    print(f"  pmf_sum_abs_err_max: {sum_max:.3e}")
    print(f"  pmf_sum_abs_err_p99: {sum_p99:.3e}")
    print(f"  bad_parse_count: {bad_parse}")
    print(f"  negative_probability_count: {negative_count}")
    print(f"  nonfinite_probability_count: {nonfinite_count}")
    print(f"  reported_valid_mismatch_count: {rep_valid_mm}")
    print(f"  reported_sum_error_mismatch_count: {rep_sum_err_mm}")
    print(f"  survival_only_tail_unverifiable_count: {surv_unver}")
    print(f"  legacy_historical_files: {legacy_count}")
    print(f"  legacy_historical_failures: {legacy_failed}")
    if legacy_recs:
        print("  legacy_historical_files_list:")
        for r in legacy_recs[:20]:
            print(f"    - {r['rel_file']} (LEGACY_DEREK_PLACEHOLDER_OUTCOME_LEVEL)")
        if len(legacy_recs) > 20:
            print(f"    ... and {len(legacy_recs) - 20} more")
    if fail_reasons:
        print("  fail_reasons:")
        for fr in fail_reasons:
            print(f"    - {fr}")
        bad_files = [f for f in by_file
                     if (not f["is_legacy_placeholder"] and (
                         f["bad_parse"] or f["valid_bad_shape"] or
                         f["valid_negative_prob"] or f["valid_non_finite"] or
                         f["reported_valid_mismatch"] or
                         f["reported_sum_error_mismatch"]))]
        if bad_files:
            print("  first failing non-legacy files:")
            for f in bad_files[:5]:
                print(f"    - {f['rel_file']} (date={f['delivery_date']}, mode={f['mode']}, "
                      f"bad_parse={f['bad_parse']}, bad_shape={f['valid_bad_shape']}, "
                      f"neg={f['valid_negative_prob']}, nf={f['valid_non_finite']}, "
                      f"rep_valid_mm={f['reported_valid_mismatch']}, "
                      f"rep_sum_mm={f['reported_sum_error_mismatch']})")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
