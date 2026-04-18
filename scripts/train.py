"""CLI entrypoint for the NBA Props Model training pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Calibrator classes under __main__ for pickles saved pre-reorganization.
from nba_props_model.calibration.stat_side_platt import (  # noqa: E402
    IsotonicCalibrator,
    PlattCalibrator,
)
from nba_props_model.pipelines.train import main  # noqa: E402

if __name__ == "__main__":
    main()
