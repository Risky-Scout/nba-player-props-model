"""CLI entrypoint for the NBA Props Model daily prediction pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Expose calibrator classes under __main__ for pickles saved pre-reorganization.
# joblib records the serializing module; pickles written by
# calibrate_stat_side.py-as-__main__ before the reorg record these classes
# at __main__.{IsotonicCalibrator,PlattCalibrator}.
from nba_props_model.calibration.stat_side_platt import (  # noqa: E402
    IsotonicCalibrator,
    PlattCalibrator,
)
from nba_props_model.pipelines.predict import main  # noqa: E402

if __name__ == "__main__":
    main()
