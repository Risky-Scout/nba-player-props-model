from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]


def test_feature_gap_audit_outputs(tmp_path: Path):
    training = pd.DataFrame(
        {
            "player_id": [1, 2],
            "injury_status_current": ["healthy", "questionable"],
            "projected_minutes": [31.0, 26.0],
            "market_prob_over": [0.55, 0.48],
        }
    )
    event = pd.DataFrame({"player_id": [1], "stat": ["pts"], "pmf_mean": [21.4]})
    training_path = tmp_path / "training.parquet"
    event_path = tmp_path / "event.parquet"
    out_dir = tmp_path / "out"
    training.to_parquet(training_path, index=False)
    event.to_parquet(event_path, index=False)

    cmd = [
        "python3",
        str(REPO / "scripts" / "audit_player_prop_feature_gaps.py"),
        "--training-table",
        str(training_path),
        "--event-market-rows",
        str(event_path),
        "--out-dir",
        str(out_dir),
    ]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "PLAYER_PROP_FEATURE_GAP_AUDIT_PASS" in proc.stdout

    required = [
        "feature_inventory_training_table.csv",
        "feature_inventory_event_market_rows.csv",
        "feature_gap_summary.csv",
        "high_priority_missing_features.csv",
        "leakage_risk_features.csv",
        "summary.json",
        "summary.md",
    ]
    for name in required:
        assert (out_dir / name).is_file()

    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert "expected_findings" in summary
    assert summary["pass"] is True
