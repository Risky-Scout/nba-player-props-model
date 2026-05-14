#!/usr/bin/env python3
"""Post-repair failure ledger: stat×role blockers after event-neutral + PMF mean-shift."""
from __future__ import annotations

import argparse
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


def _primary_blocker(
    *,
    n_scored: int,
    n_joined: int,
    failure_reason: str,
    cal_pass: bool,
    ms_pass: bool,
    boot_fail: bool,
    mean_fail: bool,
    delta_ll: float | None,
    delta_br: float | None,
    dom: str,
) -> str:
    if n_joined < 100:
        return "low_market_coverage"
    if n_scored < 100:
        return "insufficient_sample"
    if failure_reason == "insufficient_scored_rows":
        return "insufficient_sample"
    if failure_reason == "insufficient_market_overlap":
        return "low_market_coverage"
    if "variance" in str(dom).lower() or "variance_too" in str(dom):
        return "variance_too_narrow"
    if "sparse" in str(dom).lower() or "p0" in str(dom).lower():
        return "sparse_p0_tail"
    if "pit" in str(dom).lower() or ("calibration" in str(dom).lower() and not cal_pass):
        if delta_ll is not None and delta_br is not None and delta_ll < 0 and delta_br < 0:
            return "PIT_shape"
        if not cal_pass:
            return "calibration_pass_false"
    if boot_fail and mean_fail:
        return "bootstrap_ci_not_better"
    if boot_fail:
        return "bootstrap_ci_not_better"
    if failure_reason == "model_logloss_not_better":
        return "model_logloss_not_better"
    if failure_reason == "model_brier_not_better":
        return "model_brier_not_better"
    if "mean_too" in str(dom) or "mean_bias" in str(dom):
        return "mean_bias_still_present"
    if "overconfident" in str(dom) or "prob_too_high" in str(dom):
        return "overconfidence_still_present"
    if not cal_pass:
        return "calibration_pass_false"
    return "model_feature_work_required"


def _next_family(pb: str) -> str:
    m = {
        "active_prob_not_used": "integration_fix",
        "overconfidence_still_present": "stronger_hierarchical_probability_shrinkage",
        "mean_bias_still_present": "revisit_pmf_mean_shift_or_feature_model",
        "variance_too_narrow": "pmf_variance_temperature",
        "sparse_p0_tail": "sparse_p0_tail_calibration",
        "PIT_shape": "monotone_pit_repair",
        "calibration_pass_false": "monotone_pit_repair",
        "bootstrap_ci_not_better": "needs_more_data_or_more_stable_edges",
        "model_logloss_not_better": "model_feature_work_required",
        "model_brier_not_better": "model_feature_work_required",
        "insufficient_sample": "needs_more_data_or_more_stable_edges",
        "low_market_coverage": "no_repair_allowed_without_feature_model_work",
    }
    return m.get(pb, "model_feature_work_required")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    label = str(args.label)

    loss_path = ART / f"event_market_loss_rows_{label}.parquet"
    sr_path = ART / f"event_market_superiority_{label}" / "stat_role_market_superiority.csv"
    led_path = ART / f"market_superiority_repair_{label}" / "repair_ledger.csv"
    math_fail = ART / f"market_superiority_math_contract_{label}" / "stat_role_inequality_failures.csv"
    prom_path = ART / f"event_market_superiority_{label}" / f"promotion_claim_report_{label}.json"

    if not loss_path.is_file() or not sr_path.is_file():
        print(f"FATAL: missing {loss_path} or {sr_path}", file=sys.stderr)
        return 2

    combo = pd.read_parquet(loss_path)
    sr = pd.read_csv(sr_path)
    led = pd.read_csv(led_path) if led_path.is_file() else pd.DataFrame()
    mf = pd.read_csv(math_fail) if math_fail.is_file() else pd.DataFrame()

    boot_keys: set[tuple[str, str]] = set()
    mean_keys: set[tuple[str, str]] = set()
    if len(mf):
        for _, r in mf.iterrows():
            st = str(r.get("stat", "")).lower()
            rb = str(r.get("role_bucket", ""))
            rs = str(r.get("reason", ""))
            if "bootstrap" in rs:
                boot_keys.add((st, rb))
            if "mean_delta" in rs:
                mean_keys.add((st, rb))

    prom = {}
    if prom_path.is_file():
        prom = json.loads(prom_path.read_text(encoding="utf-8"))
    claim_allowed = bool(prom.get("claim_allowed", False))

    rows_out: list[dict] = []
    for _, row in sr.iterrows():
        stat = str(row["stat"]).lower()
        role = str(row["role_bucket"])
        sub = combo[
            (combo["stat"].astype(str).str.lower() == stat)
            & (combo["role_bucket"].astype(str) == role)
        ]
        m_joined = int(row.get("n_market_joined") or 0)
        n_scored = int(row.get("n_scored") or 0)
        elig = bool(row.get("market_superiority_eligible", False))

        sm = sub[sub.get("join_status", "") == "matched"] if "join_status" in sub.columns else sub
        en_cnt = (
            int(sm["probability_scale_repair_method"].notna().sum())
            if "probability_scale_repair_method" in sm.columns
            else 0
        )
        ms_cnt = (
            int(sm["pmf_mean_shift_repair_applied"].astype(bool).sum())
            if "pmf_mean_shift_repair_applied" in sm.columns
            else 0
        )

        raw_ll = act_ll = mkt_ll = raw_br = act_br = mkt_br = None
        mask = pd.Series(True, index=sm.index)
        for c in ("model_event_logloss", "market_event_logloss", "model_brier", "market_brier"):
            if c in sm.columns:
                mask &= sm[c].notna()
        s2 = sm.loc[mask] if int(mask.sum()) else sm.iloc[0:0]
        if len(s2) and "hit_result" in s2.columns:
            hr = pd.to_numeric(s2["hit_result"], errors="coerce")
            ok = hr.isin([0.0, 1.0])
            s3 = s2.loc[ok]
            if len(s3):
                raw_ll = float(np.mean([_ll(float(a), float(h)) for a, h in zip(s3["model_prob_over_raw"], s3["hit_result"])]))
                act_ll = float(np.mean([_ll(float(a), float(h)) for a, h in zip(s3["model_prob_over_active"], s3["hit_result"])]))
                mkt_ll = float(np.mean([_ll(float(a), float(h)) for a, h in zip(s3["market_prob_over_no_vig"], s3["hit_result"])]))
                raw_br = float(np.mean([_brier(float(a), float(h)) for a, h in zip(s3["model_prob_over_raw"], s3["hit_result"])]))
                act_br = float(np.mean([_brier(float(a), float(h)) for a, h in zip(s3["model_prob_over_active"], s3["hit_result"])]))
                mkt_br = float(np.mean([_brier(float(a), float(h)) for a, h in zip(s3["market_prob_over_no_vig"], s3["hit_result"])]))

        mb_before = mb_after = None
        if "pmf_mean_raw" in sm.columns and "actual" in sm.columns:
            a = pd.to_numeric(sm["actual"], errors="coerce")
            r = pd.to_numeric(sm["pmf_mean_raw"], errors="coerce")
            rp = (
                pd.to_numeric(sm["pmf_mean_repaired"], errors="coerce")
                if "pmf_mean_repaired" in sm.columns
                else r
            )
            m = a.notna() & r.notna()
            if int(m.sum()):
                mb_before = float((r[m] - a[m]).mean())
                mb_after = float((rp[m] - a[m]).mean()) if rp.notna().any() else None

        lr = led[(led["stat"].astype(str).str.lower() == stat) & (led["role_bucket"].astype(str) == role)]
        dom = str(lr.iloc[0].get("dominant_failure", "")) if len(lr) else ""
        sec = str(lr.iloc[0].get("secondary_failures", "")) if len(lr) else ""

        fr = str(row.get("failure_reason") or "")
        cal_pass = bool(row.get("calibration_pass", False))
        ms_pass = bool(row.get("market_superiority_pass", False))
        boot_math = (stat, role) in boot_keys
        mean_math = (stat, role) in mean_keys
        boot_fail = boot_math
        mean_fail = mean_math

        d_ll = (act_ll - mkt_ll) if (act_ll is not None and mkt_ll is not None) else None
        d_br = (act_br - mkt_br) if (act_br is not None and mkt_br is not None) else None

        pb = _primary_blocker(
            n_scored=n_scored,
            n_joined=m_joined,
            failure_reason=fr,
            cal_pass=cal_pass,
            ms_pass=ms_pass,
            boot_fail=boot_fail,
            mean_fail=mean_fail,
            delta_ll=d_ll,
            delta_br=d_br,
            dom=dom,
        )
        strict_claim = bool(row.get("market_superiority_claim_allowed", False)) and ms_pass and cal_pass

        do_not = []
        if not ms_pass:
            do_not.append("market_superiority_fail")
        if not cal_pass:
            do_not.append("calibration_fail")
        if boot_math:
            do_not.append("bootstrap_math_fail")
        if mean_math:
            do_not.append("mean_delta_math_fail")

        rows_out.append(
            {
                "stat": stat,
                "role_bucket": role,
                "n": n_scored,
                "raw_model_logloss": raw_ll,
                "active_model_logloss": act_ll,
                "market_logloss": mkt_ll,
                "raw_model_brier": raw_br,
                "active_model_brier": act_br,
                "market_brier": mkt_br,
                "delta_logloss_active_vs_market": d_ll,
                "delta_brier_active_vs_market": d_br,
                "event_neutral_applied_count": en_cnt,
                "pmf_mean_shift_applied_count": ms_cnt,
                "mean_bias_before": mb_before,
                "mean_bias_after": mb_after,
                "calibration_pass": cal_pass,
                "model_better_calibrated": bool(row.get("model_better_calibrated", False)),
                "market_superiority_pass": ms_pass,
                "bootstrap_ci_pass": not boot_math,
                "strict_claimable": strict_claim,
                "remaining_primary_blocker": pb,
                "remaining_secondary_blockers": sec,
                "next_repair_family": _next_family(pb),
                "do_not_claim_reason": "|".join(do_not) if do_not else "",
                "market_superiority_eligible": elig,
                "ledger_dominant_failure": dom,
            }
        )

    out_df = pd.DataFrame(rows_out)
    out_dir = ART / f"post_repair_failure_ledger_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_dir / "post_repair_failure_ledger.csv", index=False)

    elig_df = out_df[out_df["market_superiority_eligible"] == True]
    counts = elig_df["remaining_primary_blocker"].value_counts().to_dict() if len(elig_df) else {}
    top = max(counts, key=counts.get) if counts else None
    summ = {
        "label": label,
        "eligible_segments": int(len(elig_df)),
        "blocker_counts_eligible": counts,
        "recommended_next_repair_family_mode": top,
        "claim_allowed_global": claim_allowed,
    }
    (out_dir / "post_repair_summary.json").write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8")

    md = [
        f"# Post-repair failure ledger (`{label}`)",
        "",
        f"- Eligible segments: **{summ['eligible_segments']}**",
        f"- Blocker counts (eligible): `{json.dumps(counts)}`",
        f"- Mode blocker: **{top}**",
        f"- Suggested next family (mode mapping): **{_next_family(top or '')}**",
        "",
    ]
    (out_dir / "post_repair_next_actions.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("POST_REPAIR_FAILURE_LEDGER_PASS")
    print(f"  wrote: {out_dir.relative_to(REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
