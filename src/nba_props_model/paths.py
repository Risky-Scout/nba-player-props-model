"""Canonical filesystem paths for the NBA Props Model.

Every module imports from here so repo-relative paths stay consistent whether
the entrypoint is invoked from the repo root, from scripts/, or via a test.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR      = REPO_ROOT / "data"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
MODEL_DIR     = ARTIFACTS_DIR / "models"
GRADED_DIR    = ARTIFACTS_DIR / "graded"
PRED_DIR      = REPO_ROOT / "predictions"

for _d in (DATA_DIR, MODEL_DIR, GRADED_DIR, PRED_DIR):
    _d.mkdir(parents=True, exist_ok=True)
