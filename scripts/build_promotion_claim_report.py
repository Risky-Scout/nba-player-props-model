#!/usr/bin/env python3
"""M8.6Q B3 — promotion claim report. Negative deltas = model better.

Reads artifacts/model_diagnostics/event_market_loss_rows_<date>.parquet.

6-enum promotion statuses per FINAL CORRECTION:
  fail_same_sample_or_leakage_risk
  fail_invalid_pmf
  valid_pmf_not_event_market_superior
  calibrated_but_not_more_accurate_than_market
  accurate_but_not_well_calibrated
  market_superior_event_accuracy_and_calibration   (only enum permitting claim)

Promotion gate: mean(delta) + z·SE ≤ −tau  (NEGATIVE deltas are better).

Pass marker: M8_6Q_PROMOTION_CLAIM_REPORT_BUILD_PASS
"""
from __future__ import annotations
import argparse, json, sys, math
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

PROMOTION_ENUM = (
    "fail_same_sample_or_leakage_risk",
    "fail_invalid_pmf",
    "valid_pmf_not_event_market_superior",
    "calibrated_but_not_more_accurate_than_market",
    "accurate_but_not_well_calibrated",
    "market_superior_event_accuracy_and_calibration",
)
CLAIM_ALLOWED_ENUM = "market_superior_event_accuracy_and_calibration"
FORBIDDEN_PUBLIC_COPY = (
    "accurate", "well calibrated", "well-calibrated",
    "better than market", "profitable", "lock", "guaranteed",
    "sharp", "proven edge",
)


def _summary(sub: pd.DataFrame) -> dict:
    settled = sub[sub["settled"] == True]
    n = int(len(settled))
    if n == 0:
        return {"n_settled": 0,
                "model_logloss_mean": None, "market_logloss_mean": None,
                "logloss_delta_mean": None, "logloss_delta_se": None,
                "logloss_delta_lower95": None,
                "model_brier_mean": None, "market_brier_mean": None,
                "brier_delta_mean": None, "brier_delta_se": None,
                "brier_delta_lower95": None}
    def _m(c):
        s = settled[c].dropna(); return float(s.mean()) if len(s) else None
    def _se(c):
        s = settled[c].dropna()
        if len(s) < 5: return None
        sd = float(s.std(ddof=1))
        return sd / math.sqrt(len(s)) if sd > 0 else None
    ll_mean = _m("event_logloss_delta"); ll_se = _se("event_logloss_delta")
    br_mean = _m("brier_delta"); br_se = _se("brier_delta")
    # 95% CI lower bound assuming normality (z = 1.96).
    # For "model better" we want UPPER bound (most-pessimistic-for-model) to be ≤ -tau.
    # That's mean + z*SE ≤ -tau  (since negative = better).
    ll_upper95 = (ll_mean + 1.96 * ll_se) if (ll_mean is not None and ll_se is not None) else None
    br_upper95 = (br_mean + 1.96 * br_se) if (br_mean is not None and br_se is not None) else None
    return {
        "n_settled": n,
        "model_logloss_mean": _m("model_event_logloss"),
        "market_logloss_mean": _m("market_event_logloss"),
        "logloss_delta_mean": ll_mean,
        "logloss_delta_se": ll_se,
        "logloss_delta_upper95": ll_upper95,
        "model_brier_mean": _m("model_brier"),
        "market_brier_mean": _m("market_brier"),
        "brier_delta_mean": br_mean,
        "brier_delta_se": br_se,
        "brier_delta_upper95": br_upper95,
    }


def _classify(summary: dict, *, min_n: int, tau: float, z: float) -> str:
    """Classify per the 6-enum rules. mean(delta) + z*SE ≤ -tau is the
    "model strictly better" promotion gate (since negative = better)."""
    n = summary.get("n_settled") or 0
    if n < min_n:
        return "valid_pmf_not_event_market_superior"
    ll_mean = summary.get("logloss_delta_mean")
    ll_se = summary.get("logloss_delta_se")
    br_mean = summary.get("brier_delta_mean")
    br_se = summary.get("brier_delta_se")

    def _better(mean, se):
        if mean is None or se is None: return False
        # mean + z*SE <= -tau  ⇒  model better with confidence
        return (mean + z * se) <= -tau

    accurate = _better(ll_mean, ll_se)    # logloss → accuracy proxy
    calibrated = _better(br_mean, br_se)  # brier   → calibration proxy
    if accurate and calibrated:
        return "market_superior_event_accuracy_and_calibration"
    if calibrated and not accurate:
        return "calibrated_but_not_more_accurate_than_market"
    if accurate and not calibrated:
        return "accurate_but_not_well_calibrated"
    return "valid_pmf_not_event_market_superior"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of-date", required=True)
    ap.add_argument("--min-n", type=int, default=30)
    ap.add_argument("--tau", type=float, default=0.0)
    ap.add_argument("--z", type=float, default=1.96)
    args = ap.parse_args()
    date = args.as_of_date

    in_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{date}.parquet"
    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / f"promotion_claim_report_{date}.json"
    out_md = out_dir / f"promotion_claim_report_{date}.md"

    if not in_path.exists():
        report = {
            "as_of_date": date, "schema_version": "m8_6q_v2",
            "status": "no_event_market_loss_rows_input",
            "input_path": str(in_path.relative_to(REPO_ROOT)),
            "overall_promotion_status": "fail_invalid_pmf",
            "market_superiority_claim_allowed": False,
            "per_bucket": {},
            "claim_allowed_enum": CLAIM_ALLOWED_ENUM,
            "delta_sign_convention": "model_minus_market_negative_better",
            "promotion_gate_formula": "mean(delta) + z*SE <= -tau",
            "tau": args.tau, "z": args.z, "min_n_threshold": args.min_n,
            "forbidden_public_copy_tokens": list(FORBIDDEN_PUBLIC_COPY),
        }
        out_json.write_text(json.dumps(report, indent=2, default=str) + "\n")
        out_md.write_text(
            f"# Promotion Claim Report — {date}\n\n"
            f"**Status:** no event_market_loss_rows input.\n\n"
            f"**Overall promotion status:** `fail_invalid_pmf`\n\n"
            f"**Market superiority claim allowed:** NO.\n\n"
            f"**Sign convention:** delta = model − market (negative = model better).\n"
        )
        print("M8_6Q_PROMOTION_CLAIM_REPORT_BUILD_PASS")
        print(f"  wrote: {out_json.relative_to(REPO_ROOT)} (no-input fallback)")
        return 0

    df = pd.read_parquet(in_path)
    per_bucket: dict = {}

    # Same-sample / leakage check
    if "walk_forward_only" in df.columns and (df["walk_forward_only"] == False).any():
        overall = "fail_same_sample_or_leakage_risk"
    elif "same_sample_predictions_used" in df.columns and (df["same_sample_predictions_used"] == True).any():
        overall = "fail_same_sample_or_leakage_risk"
    elif df.empty:
        overall = "valid_pmf_not_event_market_superior"
    else:
        # PMF validity check
        if "model_prob_over" in df.columns:
            mp = df["model_prob_over"].dropna()
            if len(mp) > 0 and ((mp <= 0) | (mp >= 1)).any():
                overall = "fail_invalid_pmf"
            else:
                overall = None
        else:
            overall = "fail_invalid_pmf"

        if overall is None:
            grouping_cols = [c for c in ("stat", "role_bucket") if c in df.columns]
            if not grouping_cols:
                grouping_cols = ["stat"] if "stat" in df.columns else []
            if grouping_cols:
                for keys, sub in df.groupby(grouping_cols, dropna=False):
                    if not isinstance(keys, tuple): keys = (keys,)
                    summary = _summary(sub)
                    status = _classify(summary, min_n=args.min_n, tau=args.tau, z=args.z)
                    per_bucket["|".join(str(k) for k in keys)] = {"summary": summary, "status": status}
            statuses = [v["status"] for v in per_bucket.values()]
            if CLAIM_ALLOWED_ENUM in statuses:
                overall = CLAIM_ALLOWED_ENUM
            elif "calibrated_but_not_more_accurate_than_market" in statuses:
                overall = "calibrated_but_not_more_accurate_than_market"
            elif "accurate_but_not_well_calibrated" in statuses:
                overall = "accurate_but_not_well_calibrated"
            else:
                overall = "valid_pmf_not_event_market_superior"

    claim_allowed = (overall == CLAIM_ALLOWED_ENUM)
    report = {
        "as_of_date": date,
        "schema_version": "m8_6q_v2",
        "input_path": str(in_path.relative_to(REPO_ROOT)),
        "overall_promotion_status": overall,
        "market_superiority_claim_allowed": bool(claim_allowed),
        "claim_allowed_enum": CLAIM_ALLOWED_ENUM,
        "delta_sign_convention": "model_minus_market_negative_better",
        "promotion_gate_formula": "mean(delta) + z*SE <= -tau",
        "tau": args.tau, "z": args.z, "min_n_threshold": int(args.min_n),
        "per_bucket": per_bucket,
        "promotion_enum": list(PROMOTION_ENUM),
        "forbidden_public_copy_tokens": list(FORBIDDEN_PUBLIC_COPY),
    }
    out_json.write_text(json.dumps(report, indent=2, default=str) + "\n")

    md = [f"# Promotion Claim Report — {date}\n",
          f"**Overall promotion status:** `{overall}`",
          f"**Market superiority claim allowed:** {'YES' if claim_allowed else 'NO'}",
          f"**Sign convention:** `event_logloss_delta = model − market` "
          f"(NEGATIVE deltas mean the model is better)",
          f"**Promotion gate:** `mean(delta) + z·SE ≤ −tau` "
          f"(tau={args.tau}, z={args.z}, min_n={args.min_n})",
          f"**Input:** `{in_path.relative_to(REPO_ROOT)}`\n",
          "## Forbidden public copy (do NOT use in marketing):"]
    for tok in FORBIDDEN_PUBLIC_COPY: md.append(f"- `{tok}`")
    md.append("\n## Per-bucket statuses\n")
    md.append("| Bucket | n_settled | logloss_delta_mean | logloss_delta_upper95 | brier_delta_mean | Status |")
    md.append("|---|---|---|---|---|---|")
    for key, v in per_bucket.items():
        s = v["summary"]
        md.append(f"| {key} | {s['n_settled']} | {s['logloss_delta_mean']} | "
                  f"{s.get('logloss_delta_upper95')} | {s['brier_delta_mean']} | `{v['status']}` |")
    out_md.write_text("\n".join(md) + "\n")

    print("M8_6Q_PROMOTION_CLAIM_REPORT_BUILD_PASS")
    print(f"  overall={overall} claim_allowed={claim_allowed}")
    print(f"  wrote: {out_json.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
