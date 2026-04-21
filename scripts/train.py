"""CLI entrypoint for the NBA Props Model training pipeline."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Calibrator classes under __main__ for pickles saved pre-reorganization.
from nba_props_model.calibration.stat_side_platt import (  # noqa: E402
    IsotonicCalibrator,
    PlattCalibrator,
)
from nba_props_model.pipelines.train import main  # noqa: E402


def _cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--build-table-only",
        action="store_true",
        help=(
            "Fetch data, build and persist data/training_table.parquet, then "
            "exit without training any models. Used by the Phase 8 workflow "
            "so calibrate_pmf.py has the training table available without "
            "running a full retrain."
        ),
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _cli()
    main(build_table_only=args.build_table_only)
