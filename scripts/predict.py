"""CLI entrypoint for the NBA Props Model daily prediction pipeline.

Default invocation (no args): unchanged from pre-13M behavior — runs the
full daily slate for ``date.today()`` and writes
``predictions/all_props_<date>.parquet`` plus the WoO/canonical
side-effect files (singles_*.json, sgps_*.json, paper_trade_log.csv).
WoO callers must keep using this default.

Phase 13M-bis Derek live-snapshot invocation (when ``--derek-live-snapshot``
is supplied): override target_date, filter to a single game_id, join a
BDL lineup-context parquet into the prediction dataframe, and write a
single output file under ``--snapshot-output-dir`` without touching the
canonical predictions/all_props_*.parquet or the WoO side-effect files.

Pass lines (Derek mode):
    PREDICT_DEREK_LIVE_ARGS_PASS                    (CLI surface validated)
    PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_PASS (lineup join applied)

Fail lines (Derek mode):
    PREDICT_DEREK_LIVE_ARGS_FAILED
    PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_FAILED
"""
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
    raise SystemExit(main(sys.argv[1:]))
