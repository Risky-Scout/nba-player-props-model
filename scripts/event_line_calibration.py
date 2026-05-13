"""Guarded line-probability calibration for event-market evaluation (actuals-only targets)."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def load_event_calibration(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def segment_key(stat: str, role_bucket: str) -> str:
    return f"{str(stat).lower()}|{str(role_bucket)}"


def logit(p: float) -> float:
    p = max(min(float(p), 1.0 - 1e-12), 1e-12)
    return math.log(p / (1.0 - p))


def sigmoid(z: float) -> float:
    if z > 35:
        return 1.0 - 1e-12
    if z < -35:
        return 1e-12
    return 1.0 / (1.0 + math.exp(-z))


def apply_segment_calibration(
    p_over: float | None,
    *,
    stat: str,
    role_bucket: str,
    cal: dict[str, Any],
    line: float | None = None,
) -> tuple[float | None, bool, str | None]:
    """Return (p_over_calibrated, applied, segment_id_used).

    Hierarchical lookup: stat|role → stat|* → global
    """
    if p_over is None or not math.isfinite(float(p_over)):
        return None, False, None
    p0 = float(p_over)
    segs = cal.get("segments") or {}
    order = (
        segment_key(stat, role_bucket),
        f"{str(stat).lower()}|*",
        "global",
    )
    seg_id = None
    spec = None
    for k in order:
        if k in segs:
            seg_id = k
            spec = segs[k]
            break
    if not spec:
        return p0, False, None
    t = str(spec.get("type") or "").lower()
    if t == "platt":
        a = float(spec.get("a", 0.0))
        b = float(spec.get("b", 1.0))
        z = a + b * logit(p0)
        return sigmoid(z), True, seg_id
    if t == "identity":
        return p0, True, seg_id
    return p0, False, None


def merge_event_calibration_report_meta(
    repo_root: Path,
    label: str,
    calibration_model_path: str | Path | None,
) -> dict[str, Any]:
    """Metadata block for superiority / promotion summaries (CLI or loss-row meta)."""
    keys = (
        "event_calibration_applied",
        "event_calibration_version",
        "event_calibration_stage",
        "event_calibration_source",
        "market_pmf_used",
        "market_prob_used_as_training_label",
    )
    out: dict[str, Any] = {
        "event_calibration_applied": False,
        "event_calibration_version": None,
        "event_calibration_stage": None,
        "event_calibration_source": None,
        "market_pmf_used": False,
        "market_prob_used_as_training_label": False,
    }
    src: dict[str, Any] | None = None
    if calibration_model_path:
        p = Path(calibration_model_path)
        if not p.is_absolute():
            p = repo_root / p
        if p.is_file():
            src = json.loads(p.read_text(encoding="utf-8"))
    if src is None:
        mp = repo_root / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet.meta.json"
        if mp.is_file():
            try:
                src = json.loads(mp.read_text(encoding="utf-8"))
            except Exception:
                src = None
    if not src:
        return out
    for k in keys:
        if k in src:
            out[k] = src[k]
    return out
