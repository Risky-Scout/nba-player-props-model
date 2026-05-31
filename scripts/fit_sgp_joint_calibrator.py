#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from sgp_engine.calibration import fit_global_joint_calibrator, reliability_table, expected_calibration_error


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--backtest-rows", required=True, help="Parquet/CSV with raw_joint_probability and hit_result columns.")
    p.add_argument("--out", required=True)
    p.add_argument("--pred-col", default="raw_joint_probability")
    p.add_argument("--y-col", default="hit_result")
    p.add_argument("--min-n", type=int, default=300)
    args = p.parse_args()

    path = Path(args.backtest_rows)
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    cal = fit_global_joint_calibrator(df, pred_col=args.pred_col, y_col=args.y_col, min_n=args.min_n, out_path=args.out)
    df["calibrated_joint_probability"] = cal.predict(df[args.pred_col].to_numpy())
    rel = reliability_table(df, pred_col="calibrated_joint_probability", y_col=args.y_col)
    rel_path = Path(args.out).with_suffix(".reliability.csv")
    rel.to_csv(rel_path, index=False)
    report = {
        "status": "PASS",
        "calibrator_id": cal.calibrator_id,
        "n_train": cal.n_train,
        "ece": expected_calibration_error(df, pred_col="calibrated_joint_probability", y_col=args.y_col),
        "reliability_table": str(rel_path),
    }
    Path(args.out).with_suffix(".report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
