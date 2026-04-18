"""CLI entrypoint for walk-forward stat x side Platt calibration."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nba_props_model.calibration.stat_side_platt import main  # noqa: E402

if __name__ == "__main__":
    main()
