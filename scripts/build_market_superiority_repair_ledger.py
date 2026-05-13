#!/usr/bin/env python3
"""M8.7 — consolidate market-superiority diagnostics into a single repair ledger."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ART = REPO_ROOT / "artifacts" / "model_diagnostics"


def _read_csv(p: Path) -> pd.DataFrame:
    if not p.is_file():
        return pd.DataFrame()
    return pd.read_csv(p)


def _read_json(p: Path) -> dict:
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _segment_key(stat: str, role: str) -> str:
    return f"{str(stat).lower()}|{str(role).lower()}"


def _allowed_blocked_families(dominant: str, secondary: list[str]) -> tuple[str, str]:
    dom = str(dominant or "").strip()
    allowed = "do_not_claim"
    blocked = "event_neutral_temperature|shrunk_isotonic|hierarchical_logit_shrinkage|pmf_mean_shift|pmf_variance_temperature|sparse_p0_tail_calibration|monotone_pit_repair|needs_more_data"

    if dom == "model_prob_too_high_or_overconfident_side":
        allowed = "event_neutral_temperature|shrunk_isotonic|hierarchical_logit_shrinkage"
        blocked = "pmf_mean_shift|pmf_variance_temperature|sparse_p0_tail_calibration|monotone_pit_repair"
    elif dom == "mean_too_low":
        allowed = "pmf_mean_shift"
        blocked = "event_neutral_temperature|shrunk_isotonic|hierarchical_logit_shrinkage|pmf_variance_temperature|sparse_p0_tail_calibration|monotone_pit_repair"
    elif dom == "variance_too_narrow":
        allowed = "pmf_variance_temperature"
        blocked = "event_neutral_temperature|shrunk_isotonic|hierarchical_logit_shrinkage|pmf_mean_shift|sparse_p0_tail_calibration|monotone_pit_repair"
    elif dom == "PIT_shape":
        allowed = "monotone_pit_repair"
        blocked = "event_neutral_temperature|shrunk_isotonic|hierarchical_logit_shrinkage|pmf_mean_shift|pmf_variance_temperature|sparse_p0_tail_calibration"
    elif dom in ("p0_bias", "p0_error"):
        allowed = "sparse_p0_tail_calibration"
        blocked = "event_neutral_temperature|shrunk_isotonic|hierarchical_logit_shrinkage|pmf_mean_shift|pmf_variance_temperature|monotone_pit_repair"
    elif dom in ("model_logloss_not_better", "insufficient_scored_rows", "none", ""):
        allowed = "needs_more_data|do_not_claim"
        blocked = "event_neutral_temperature|shrunk_isotonic|hierarchical_logit_shrinkage|pmf_mean_shift|pmf_variance_temperature|sparse_p0_tail_calibration|monotone_pit_repair"

    # Secondary hints from no-market calibration failures
    for s in secondary:
        sl = str(s).lower()
        if "pit" in sl or "pit_shape" in sl:
            if "monotone_pit_repair" not in allowed.split("|"):
                allowed = allowed + "|monotone_pit_repair" if allowed else "monotone_pit_repair"
        if "p0" in sl:
            if "sparse_p0_tail_calibration" not in allowed.split("|"):
                allowed = allowed + "|sparse_p0_tail_calibration" if allowed else "sparse_p0_tail_calibration"

    return allowed, blocked


def _claim_status(
    *,
    market_superiority_pass: bool,
    calibration_pass: bool,
    mean_delta_pass: bool,
    bootstrap_ci_pass: bool,
    in_passing_but_not_claimable: bool,
) -> str:
    parts: list[str] = []
    if not market_superiority_pass:
        parts.append("BLOCKED_MARKET_SUPERIORITY")
    if not calibration_pass:
        parts.append("BLOCKED_CALIBRATION")
    if not mean_delta_pass:
        parts.append("BLOCKED_MEAN_DELTA")
    if not bootstrap_ci_pass:
        parts.append("BLOCKED_BOOTSTRAP")
    if in_passing_but_not_claimable:
        parts.append("BLOCKED_CALIBRATION")
    if not parts:
        return "CLAIMABLE"
    return "|".join(parts)


def _next_action(allowed: str, dominant: str) -> str:
    if "event_neutral_temperature" in allowed:
        return "fit_event_neutral_probability_scale_repair"
    if "pmf_mean_shift" in allowed:
        return "fit_pmf_mean_shift_repair"
    if "pmf_variance_temperature" in allowed:
        return "fit_pmf_variance_temperature_repair"
    if "sparse_p0_tail_calibration" in allowed:
        return "fit_sparse_p0_tail_calibration_repair"
    if "monotone_pit_repair" in allowed:
        return "fit_monotone_pit_repair"
    if dominant in ("model_logloss_not_better",):
        return "collect_more_oof_data_or_retrain"
    return "review_segment_diagnostics"


def build_ledger(label: str) -> pd.DataFrame:
    base = ART / f"event_market_superiority_{label}"
    stat_role_path = base / "stat_role_market_superiority.csv"
    loss_path = ART / f"event_market_loss_rows_{label}.parquet"
    fm_root = ART / f"market_superiority_failure_modes_{label}"
    seg_sum_path = fm_root / "segment_summary.csv"
    pbn_path = fm_root / "passing_but_not_claimable.csv"
    math_root = ART / f"market_superiority_math_failure_diag_{label}"
    math_csv = math_root / "math_failure_breakdown.csv"
    guarded = ART / f"guarded_event_calibration_{label}"
    guarded_sum = guarded / "summary.json"
    guarded_rb = guarded / "rollback_report.csv"
    nm_root = ART / f"model_only_no_market_calibration_{label}"
    nm_stat = nm_root / "stat_role.csv"

    sr = _read_csv(stat_role_path)
    if sr.empty:
        raise SystemExit(f"FATAL: missing stat_role_market_superiority: {stat_role_path}")

    seg = _read_csv(seg_sum_path)
    dom_map: dict[str, str] = {}
    if not seg.empty and "dominant_failure_mode" in seg.columns:
        for _, r in seg.iterrows():
            k = _segment_key(r["stat"], r["role_bucket"])
            dom_map[k] = str(r.get("dominant_failure_mode") or "")

    math_df = _read_csv(math_csv)
    mean_fail: set[str] = set()
    boot_fail: set[str] = set()
    boot_types: dict[str, str] = {}
    if not math_df.empty:
        for _, r in math_df.iterrows():
            k = _segment_key(r["stat"], r["role_bucket"])
            reason = str(r.get("inequality_reason") or "")
            if reason == "mean_delta_not_negative":
                mean_fail.add(k)
            elif reason == "bootstrap_ci_not_better":
                boot_fail.add(k)
                boot_types[k] = "bootstrap_ci_not_better"

    pbn_keys: set[str] = set()
    pbn_df = _read_csv(pbn_path)
    if not pbn_df.empty:
        for _, r in pbn_df.iterrows():
            if pd.notna(r.get("stat")) and pd.notna(r.get("role_bucket")):
                pbn_keys.add(_segment_key(r["stat"], r["role_bucket"]))

    nm_secondary: dict[str, list[str]] = {}
    nm_df = _read_csv(nm_stat)
    if not nm_df.empty:
        for _, r in nm_df.iterrows():
            k = _segment_key(r.get("stat"), r.get("role_bucket"))
            reasons = []
            for col in ("failure_reason", "pit_status", "calibration_gate"):
                if col in r and pd.notna(r[col]):
                    reasons.append(str(r[col]))
            nm_secondary[k] = reasons

    loss_n: dict[str, int] = {}
    if loss_path.is_file():
        try:
            lf = pd.read_parquet(loss_path, columns=["stat", "role_bucket"])
            lf = lf.dropna(subset=["stat", "role_bucket"])
            lf["_k"] = lf.apply(lambda x: _segment_key(x["stat"], x["role_bucket"]), axis=1)
            vc = lf["_k"].value_counts()
            loss_n = {str(k): int(v) for k, v in vc.items()}
        except Exception:
            loss_n = {}

    rows: list[dict] = []
    sr2 = sr.copy()
    sr2 = sr2[sr2["role_bucket"].notna() & (sr2["role_bucket"].astype(str) != "None")]

    for _, r in sr2.iterrows():
        stat = str(r["stat"]).lower()
        role = str(r["role_bucket"]).lower()
        sk = _segment_key(stat, role)
        dominant = dom_map.get(sk, str(r.get("failure_reason") or ""))
        secondary = list(nm_secondary.get(sk, []))

        def _bool_cell(x) -> bool:
            if isinstance(x, bool):
                return x
            s = str(x).strip().lower()
            return s in ("true", "1", "yes")

        market_superiority_pass = _bool_cell(r.get("market_superiority_pass", False))
        calibration_pass = _bool_cell(r.get("calibration_pass", False))
        model_better_calibrated = _bool_cell(r.get("model_better_calibrated", False))

        mean_delta_pass = sk not in mean_fail
        bootstrap_ci_pass = sk not in boot_fail

        in_pbn = sk in pbn_keys

        allowed, blocked = _allowed_blocked_families(dominant, secondary)
        sec_list = []
        if sk in mean_fail:
            sec_list.append("mean_delta_not_negative")
        if sk in boot_fail:
            sec_list.append("bootstrap_ci_not_better")
        if secondary:
            sec_list.extend(secondary)
        secondary_failures = "|".join(sec_list) if sec_list else ""

        claim = _claim_status(
            market_superiority_pass=market_superiority_pass,
            calibration_pass=calibration_pass,
            mean_delta_pass=mean_delta_pass,
            bootstrap_ci_pass=bootstrap_ci_pass,
            in_passing_but_not_claimable=in_pbn,
        )

        n = int(loss_n.get(sk, r.get("n_scored") or r.get("n_rows") or 0))

        mll = float(r["model_logloss_avg"]) if pd.notna(r.get("model_logloss_avg")) else float("nan")
        mkll = float(r["market_logloss_avg"]) if pd.notna(r.get("market_logloss_avg")) else float("nan")
        mbr = float(r["model_brier_avg"]) if pd.notna(r.get("model_brier_avg")) else float("nan")
        mkbr = float(r["market_brier_avg"]) if pd.notna(r.get("market_brier_avg")) else float("nan")

        rows.append(
            {
                "stat": stat,
                "role_bucket": role,
                "segment_key": sk,
                "n": n,
                "market_superiority_pass": market_superiority_pass,
                "calibration_pass": calibration_pass,
                "model_better_calibrated": model_better_calibrated,
                "model_logloss": mll,
                "market_logloss": mkll,
                "delta_logloss": (mll - mkll) if (mll == mll and mkll == mkll) else float("nan"),
                "model_brier": mbr,
                "market_brier": mkbr,
                "delta_brier": (mbr - mkbr) if (mbr == mbr and mkbr == mkbr) else float("nan"),
                "bootstrap_ci_pass": bootstrap_ci_pass,
                "bootstrap_failure_type": boot_types.get(sk, ""),
                "dominant_failure": dominant,
                "secondary_failures": secondary_failures,
                "allowed_repair_family": allowed,
                "blocked_repair_family": blocked,
                "next_action": _next_action(allowed, dominant),
                "claim_status": claim,
            }
        )

    out = pd.DataFrame(rows)
    return out


def _write_plan_md(path: Path, df: pd.DataFrame, label: str) -> None:
    lines = [
        f"# Market superiority repair plan ({label})",
        "",
        f"- Segments: **{len(df)}**",
        f"- Dominant failure counts:",
    ]
    if len(df):
        vc = df["dominant_failure"].fillna("unknown").value_counts()
        for k, v in vc.items():
            lines.append(f"  - `{k}`: {int(v)}")
    lines.extend(["", "## Highest-priority next actions", ""])
    na = df["next_action"].value_counts().head(10)
    for k, v in na.items():
        lines.append(f"- `{k}`: {int(v)} segments")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    label = str(args.label)

    df = build_ledger(label)
    out_dir = ART / f"market_superiority_repair_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "repair_ledger.csv"
    json_path = out_dir / "repair_ledger.json"
    md_path = out_dir / "repair_plan.md"

    df.to_csv(csv_path, index=False)
    json_path.write_text(df.to_json(orient="records", indent=2) + "\n", encoding="utf-8")
    _write_plan_md(md_path, df, label)

    # Recompute strict mean-delta pass for validation (not emitted as its own column).
    math_df = _read_csv(ART / f"market_superiority_math_failure_diag_{label}" / "math_failure_breakdown.csv")
    mean_fail_keys: set[str] = set()
    if not math_df.empty:
        for _, r in math_df.iterrows():
            if str(r.get("inequality_reason") or "") == "mean_delta_not_negative":
                mean_fail_keys.add(_segment_key(r["stat"], r["role_bucket"]))

    def _row_mean_ok(row: pd.Series) -> bool:
        return _segment_key(row["stat"], row["role_bucket"]) not in mean_fail_keys

    mean_ok_s = df.apply(_row_mean_ok, axis=1)
    bad_claim = df[
        (df["claim_status"] == "CLAIMABLE")
        & (
            (~df["market_superiority_pass"])
            | (~df["calibration_pass"])
            | (~df["bootstrap_ci_pass"])
            | (~mean_ok_s)
        )
    ]
    if len(bad_claim):
        raise SystemExit(f"FATAL: invalid CLAIMABLE rows: {len(bad_claim)}")

    print("MARKET_SUPERIORITY_REPAIR_LEDGER_PASS")
    print(f"  wrote: {csv_path.relative_to(REPO_ROOT)}")
    print(f"  segments={len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
