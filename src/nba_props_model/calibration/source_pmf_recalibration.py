"""Wrapper for stat-grid / source PMF delivery recalibration (M8.6).

Importers should use this module so the recalibration entrypoint stays stable
if the underlying implementation file is reorganized.
"""
from __future__ import annotations

from nba_props_model.calibration.stat_grid_delivery_recalibration import (
    StatGridDeliveryRecalibrator,
    load_stat_grid_delivery_recalibrator,
)

__all__ = ["StatGridDeliveryRecalibrator", "load_stat_grid_delivery_recalibrator"]
