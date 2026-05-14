from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]


def test_feature_snapshot_parity_pass(tmp_path: Path):
    cols = [
        "injury_status_current",
        "official_lineup_status",
        "expected_lineup_status",
        "projected_minutes",
        "minutes_q10",
        "minutes_q50",
        "minutes_q90",
        "p_starter",
        "p_inactive",
        "usage_projection",
        "opponent_def_rating_recent",
        "expected_steal_opportunities",
        "cov_pts_reb_player",
    ]
    train = pd.DataFrame({c: [1] for c in cols})
    pred = pd.DataFrame({c: [1] for c in cols})
    event = pd.DataFrame({c: [1] for c in cols})
    train_path = tmp_path / "train.parquet"
    pred_path = tmp_path / "pred.parquet"
    event_path = tmp_path / "event.parquet"
    train.to_parquet(train_path, index=False)
    pred.to_parquet(pred_path, index=False)
    event.to_parquet(event_path, index=False)

    out = tmp_path / "diag"
    cmd = [
        "python3",
        str(REPO / "scripts" / "verify_feature_snapshot_training_prediction_parity.py"),
        "--training-table",
        str(train_path),
        "--prediction-features",
        str(pred_path),
        "--event-market-rows",
        str(event_path),
        "--out-dir",
        str(out),
    ]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    assert "FEATURE_SNAPSHOT_TRAINING_PREDICTION_PARITY_PASS" in proc.stdout
    payload = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert payload["pass"] is True
