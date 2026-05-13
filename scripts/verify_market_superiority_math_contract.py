#!/usr/bin/env python3
"""Independent math checks on event-market side probabilities (no fabricated rows)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]


def _bootstrap_upper_mean(x: np.ndarray, *, rng: np.random.Generator, reps: int) -> float:
    n = len(x)
    if n < 2:
        return float(np.mean(x))
    means = np.empty(reps, dtype=float)
    for i in range(reps):
        idx = rng.integers(0, n, size=n)
        means[i] = float(np.mean(x[idx]))
    return float(np.percentile(means, 95))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--min-scored-rows", type=int, default=100)
    ap.add_argument("--bootstrap-reps", type=int, default=1000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--allow-provisional-block", action="store_true")
    ap.add_argument("--diagnostics-meta", type=Path, default=None)
    ap.add_argument(
        "--event-calibration-model",
        default=None,
        help="Optional guarded event calibration JSON; merged into math contract summary.json.",
    )
    args = ap.parse_args()

    label = args.label.strip()
    if args.event_calibration_model:
        p = Path(args.event_calibration_model)
        if not p.is_absolute():
            p = REPO_ROOT / p
        if not p.is_file():
            print(f"FATAL: --event-calibration-model not found: {p}", file=sys.stderr)
            return 2
    eml_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    sr_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_superiority_{label}" / "stat_role_market_superiority.csv"
    prom_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_superiority_{label}" / "summary.json"
    if not eml_path.exists() or not sr_path.exists():
        print(f"MISSING_INPUT {eml_path} or {sr_path}", file=sys.stderr)
        return 2

    combo = pd.read_parquet(eml_path)
    sr = pd.read_csv(sr_path)
    rng = np.random.default_rng(42)

    market_pmf_used = bool("market_rps" in combo.columns and combo["market_rps"].notna().any())

    failures: list[dict] = []
    boot_rows: list[dict] = []

    elig = sr[(sr.get("market_superiority_eligible") == True)]
    for _, row in elig.iterrows():
        stat = str(row["stat"]).lower()
        role = str(row["role_bucket"])
        sub = combo[(combo["stat"].astype(str).str.lower() == stat) & (combo["role_bucket"].astype(str) == role)]
        if not all(c in sub.columns for c in ("model_probability_for_side", "market_probability_for_side", "hit_result")):
            failures.append({"stat": stat, "role_bucket": role, "reason": "join_incomplete"})
            continue
        m = pd.to_numeric(sub["model_probability_for_side"], errors="coerce")
        q = pd.to_numeric(sub["market_probability_for_side"], errors="coerce")
        o = pd.to_numeric(sub["hit_result"], errors="coerce")
        mask = m.notna() & q.notna() & o.notna() & o.isin([0.0, 1.0])
        sub2 = sub.loc[mask]
        if len(sub2) < args.min_scored_rows:
            failures.append({"stat": stat, "role_bucket": role, "reason": "insufficient_scored_rows"})
            continue
        m = m[mask].to_numpy(dtype=float)
        q = q[mask].to_numpy(dtype=float)
        o = o[mask].to_numpy(dtype=float)
        d_brier = (m - o) ** 2 - (q - o) ** 2
        eps = 1e-12
        ll_m = -(o * np.log(np.clip(m, eps, 1 - eps)) + (1 - o) * np.log(np.clip(1 - m, eps, 1 - eps)))
        ll_q = -(o * np.log(np.clip(q, eps, 1 - eps)) + (1 - o) * np.log(np.clip(1 - q, eps, 1 - eps)))
        d_ll = ll_m - ll_q
        mean_b = float(np.mean(d_brier))
        mean_l = float(np.mean(d_ll))
        ub_b = _bootstrap_upper_mean(d_brier, rng=rng, reps=args.bootstrap_reps)
        ub_l = _bootstrap_upper_mean(d_ll, rng=rng, reps=args.bootstrap_reps)
        boot_rows.append(
            {
                "stat": stat,
                "role_bucket": role,
                "n": len(sub2),
                "mean_delta_brier": mean_b,
                "bootstrap_upper95_mean_delta_brier": ub_b,
                "mean_delta_logloss": mean_l,
                "bootstrap_upper95_mean_delta_logloss": ub_l,
            }
        )
        if mean_b >= 0 or mean_l >= 0:
            failures.append({"stat": stat, "role_bucket": role, "reason": "mean_delta_not_negative"})
        if ub_b >= 0 or ub_l >= 0:
            failures.append({"stat": stat, "role_bucket": role, "reason": "bootstrap_ci_not_better"})

    failures = list({(f.get("stat"), f.get("role_bucket"), f.get("reason")): f for f in failures}.values())

    summ: dict = {}
    if prom_path.exists():
        summ = json.loads(prom_path.read_text(encoding="utf-8"))

    calib_ok = True
    calib_detail: dict = {"status": "not_evaluated_fold_diagnostics_required"}
    meta_path = args.diagnostics_meta
    if meta_path and meta_path.is_file():
        dm = json.loads(meta_path.read_text(encoding="utf-8"))
        calib_detail = {
            "status": "meta_attached",
            "calibration_constant_prob_summary": dm.get("calibration_constant_prob_summary"),
            "note": "Fold-level PIT / mean / variance PMF gates are not re-derived here.",
        }

    required_miss = summ.get("required_stats_missing_in_event_rows") or []
    no_mkt = summ.get("required_stats_without_event_market_coverage") or []

    out_root = REPO_ROOT / "artifacts" / "model_diagnostics" / f"market_superiority_math_contract_{label}"
    out_root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(boot_rows).to_csv(out_root / "bootstrap_deltas.csv", index=False)
    pd.DataFrame(failures).to_csv(out_root / "stat_role_inequality_failures.csv", index=False)

    global_pass = (
        len(failures) == 0
        and len(required_miss) == 0
        and len(no_mkt) == 0
        and len(elig) > 0
        and not market_pmf_used
    )

    summary = {
        "label": label,
        "market_pmf_used": market_pmf_used,
        "eligible_segments": int(len(elig)),
        "failures_n": len(failures),
        "required_stats_missing_in_event_rows": required_miss,
        "required_stats_without_event_market_coverage": no_mkt,
        "calibration_gate": calib_detail,
        "calibration_contract_pass": calib_ok,
        "global_math_pass": global_pass,
    }
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from event_line_calibration import merge_event_calibration_report_meta  # noqa: E402

    summary.update(merge_event_calibration_report_meta(REPO_ROOT, label, args.event_calibration_model))
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    readme = [
        "# Market superiority math contract",
        "",
        f"- Label: `{label}`",
        f"- market_pmf_used: {market_pmf_used}",
        f"- failures: {len(failures)}",
        "",
        "Negative mean delta = model better (Brier / logloss convention).",
    ]
    (out_root / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    if args.allow_provisional_block and not global_pass:
        print("MARKET_SUPERIORITY_MATH_CONTRACT_BLOCKED")
        return 0

    if global_pass:
        print("MARKET_SUPERIORITY_MATH_CONTRACT_PASS")
        return 0
    print("MARKET_SUPERIORITY_MATH_CONTRACT_FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
