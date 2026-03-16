"""
retrain_report.py — Post-Retrain Red-Flag Audit

Generates a comprehensive JSON report after every retrain:
  - Feature count and opponent feature count per stat
  - MAE and calibration error per stat
  - Top 10 features by gain per stat
  - Non-null rate by feature family
  - Missing feature audit vs expected feature list
  - CLV and line delta from most recent graded picks

Run automatically at end of retrain workflow.
Output: graded/retrain_report_{date}.json
"""

import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date

MODEL_DIR  = Path("model_cache")
GRADED_DIR = Path("graded")
DATA_DIR   = Path("data")

# Expected opponent features per stat — the key integration check
EXPECTED_OPP = {
    "pts":    ["opp_allowed_pts_ewma",  "opp_allowed_pts_mean",  "opp_allowed_pts_factor"],
    "reb":    ["opp_allowed_reb_ewma",  "opp_allowed_reb_mean",  "opp_allowed_reb_factor"],
    "ast":    ["opp_allowed_ast_ewma",  "opp_allowed_ast_mean",  "opp_allowed_ast_factor"],
    "fg3m":   ["opp_allowed_fg3m_ewma", "opp_allowed_fg3m_mean", "opp_allowed_fg3m_factor"],
    "blk":    ["opp_allowed_blk_ewma",  "opp_allowed_blk_mean",  "opp_allowed_blk_factor"],
    "stl":    ["opp_allowed_stl_ewma",  "opp_allowed_stl_mean",  "opp_allowed_stl_factor"],
    "stocks": ["opp_allowed_blk_ewma",  "opp_allowed_stl_ewma"],
    "tov":    ["opp_allowed_pts_ewma"],
}

STATS = ["pts", "reb", "ast", "fg3m", "blk", "stl", "stocks", "tov"]


def build_report() -> dict:
    report = {
        "date": str(date.today()),
        "stats": {},
        "red_flags": [],
        "performance": {},
        "feature_coverage": {},
    }

    # ── 1. Feature audit per stat ──────────────────────────────────────────
    print("=== FEATURE AUDIT ===")
    for stat in STATS:
        feat_path = MODEL_DIR / f"features_{stat}.pkl"
        fi_path   = MODEL_DIR / f"feature_importance_{stat}.csv"
        if not feat_path.exists():
            continue

        feats = joblib.load(feat_path)
        expected_opp = EXPECTED_OPP.get(stat, [])
        present_opp  = [f for f in feats if 'opp' in f]
        missing_opp  = [f for f in expected_opp if f not in feats]

        stat_report = {
            "feature_count":  len(feats),
            "opp_count":      len(present_opp),
            "opp_present":    present_opp,
            "opp_missing":    missing_opp,
        }

        # Top features
        if fi_path.exists():
            fi = pd.read_csv(fi_path).sort_values('importance', ascending=False)
            stat_report["top_features"] = fi.head(10)[['feature','importance']].to_dict('records')
            stat_report["top_feature"] = str(fi.iloc[0]['feature']) if len(fi) > 0 else "?"

        # Red flags
        if len(present_opp) == 0:
            report["red_flags"].append(f"🚨 {stat}: ZERO opponent features in model")
        elif len(missing_opp) > 0:
            report["red_flags"].append(f"⚠️  {stat}: missing opp features: {missing_opp}")

        if len(feats) < 10:
            report["red_flags"].append(f"⚠️  {stat}: only {len(feats)} features — may be undertrained")

        report["stats"][stat] = stat_report
        print(f"  {stat:8s}: {len(feats):3d} total | {len(present_opp):2d} opp | missing: {missing_opp or 'none'}")

    # ── 2. Training meta (MAE, cal_err) ────────────────────────────────────
    meta_path = MODEL_DIR / "training_meta.json"
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
        print("\n=== TRAINING QUALITY ===")
        for stat, info in meta.items():
            if isinstance(info, dict):
                mae     = info.get("mae",     info.get("MAE", "?"))
                cal_err = info.get("cal_err", "?")
                n_feats = info.get("feature_count", "?")
                print(f"  {stat:8s}: MAE={mae}  cal_err={cal_err}  feats={n_feats}")
                if stat in report["stats"]:
                    report["stats"][stat]["mae"]     = mae
                    report["stats"][stat]["cal_err"] = cal_err

                # Red flags
                if isinstance(cal_err, (int, float)) and cal_err > 0.15:
                    report["red_flags"].append(
                        f"🚨 {stat}: calibration error {cal_err:.3f} > 0.15 threshold")
                if isinstance(mae, (int, float)):
                    thresholds = {"pts": 6, "reb": 3, "ast": 2.5, "fg3m": 1.5,
                                  "blk": 1.0, "stl": 1.0}
                    if mae > thresholds.get(stat, 999):
                        report["red_flags"].append(
                            f"⚠️  {stat}: MAE {mae:.3f} above threshold {thresholds.get(stat)}")

    # ── 3. Performance from recent graded picks ────────────────────────────
    log_path = GRADED_DIR / "performance_log.csv"
    if log_path.exists():
        df = pd.read_csv(log_path)
        df['hit'] = (df['result'] == 'HIT').astype(float)
        df['ld']  = df['line'] - df['q50']

        recent = df[df['grade_date'] >= df['grade_date'].max()]

        perf = {
            "total_picks":  len(df),
            "date_range":   f"{df['grade_date'].min()} → {df['grade_date'].max()}",
            "over_clv":     round(float(df[df['side']=='OVER']['clv_proxy'].mean()), 4),
            "under_clv":    round(float(df[df['side']=='UNDER']['clv_proxy'].mean()), 4),
            "over_hr":      round(float(df[df['side']=='OVER']['hit'].mean()), 4),
            "under_hr":     round(float(df[df['side']=='UNDER']['hit'].mean()), 4),
            "line_delta":   {},
            "clv_by_stat":  {},
        }

        print("\n=== PERFORMANCE SUMMARY ===")
        print(f"  Picks: {perf['total_picks']} | {perf['date_range']}")
        print(f"  OVER CLV: {perf['over_clv']:+.3f} | UNDER CLV: {perf['under_clv']:+.3f}")

        for stat in ['pts','reb','ast','fg3m','blk','stl']:
            s = df[df['stat']==stat]
            if len(s) == 0: continue
            ld  = round(float(s['ld'].mean()), 3)
            clv = round(float(s['clv_proxy'].mean()), 4)
            perf["line_delta"][stat]  = ld
            perf["clv_by_stat"][stat] = clv
            print(f"  {stat:6s}: ld={ld:+.3f}  CLV={clv:+.4f}")

            if abs(ld) > 0.5:
                report["red_flags"].append(
                    f"🚨 {stat}: line delta {ld:+.3f} — q50 significantly off center")
            if clv < -0.05:
                report["red_flags"].append(
                    f"⚠️  {stat}: CLV {clv:+.4f} — market beating model on this stat")

        # Under CLV red flag
        if perf["under_clv"] < -0.08:
            report["red_flags"].append(
                f"🚨 UNDER CLV {perf['under_clv']:+.3f} — under-side calibration broken")

        report["performance"] = perf

    # ── 4. Feature coverage in training data ───────────────────────────────
    training_path = DATA_DIR / "training_table.parquet"
    if training_path.exists():
        try:
            sample = pd.read_parquet(training_path).sample(min(1000, 10000))
            opp_cols = [c for c in sample.columns if 'opp_allowed' in c]
            coverage = {}
            for col in opp_cols:
                coverage[col] = round(float(sample[col].notna().mean()), 3)
            report["feature_coverage"] = coverage
            print(f"\n=== OPP FEATURE COVERAGE (sample) ===")
            for col, cov in sorted(coverage.items()):
                flag = "✓" if cov > 0.8 else "⚠️"
                print(f"  {flag} {col}: {cov:.1%}")
                if cov < 0.5:
                    report["red_flags"].append(
                        f"⚠️  {col}: only {cov:.0%} non-null in training — sparse feature")
        except Exception as e:
            print(f"  Could not read training table: {e}")

    # ── 5. Print red flags ─────────────────────────────────────────────────
    print(f"\n=== RED FLAGS ({len(report['red_flags'])}) ===")
    if report["red_flags"]:
        for flag in report["red_flags"]:
            print(f"  {flag}")
    else:
        print("  ✓ No red flags")

    return report


def save_report(report: dict) -> Path:
    today = date.today().strftime("%Y-%m-%d")
    path = GRADED_DIR / f"retrain_report_{today}.json"
    GRADED_DIR.mkdir(exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n✓ Report saved: {path}")
    return path


if __name__ == "__main__":
    report = build_report()
    save_report(report)

    # Summary
    n_flags = len(report["red_flags"])
    if n_flags == 0:
        print("\n✅ RETRAIN PASSED — no red flags")
    elif n_flags <= 3:
        print(f"\n⚠️  RETRAIN PASSED WITH WARNINGS — {n_flags} flags")
    else:
        print(f"\n🚨 RETRAIN HAS ISSUES — {n_flags} red flags — review before deploying")
