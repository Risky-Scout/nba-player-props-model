"""Optional temperature / identity calibration for model-only PMFs (OOF evaluation)."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _renorm(pmf: dict[int, float]) -> dict[int, float]:
    s = sum(pmf.values())
    if s <= 0:
        return {}
    return {int(k): float(v) / s for k, v in pmf.items()}


def apply_model_only_segment_calibration(
    pmf: dict[int, float] | None,
    *,
    stat: str,
    role_bucket: str,
    cal: dict[str, Any] | None,
) -> tuple[dict[int, float] | None, bool, str | None]:
    """Return (pmf_out, applied, segment_id).

    Supported segment ``type``:
      - ``temperature``: p'(k) ∝ p(k)^(1/T) then renormalize.
      - ``identity``: no-op (explicit pass-through).
    """
    if not pmf or not cal:
        return pmf, False, None
    st = str(stat).lower()
    rb = str(role_bucket or "unknown")
    segs = cal.get("segments") or {}
    order = (f"{st}|{rb}", f"{st}|*", "global")
    seg_id = None
    spec = None
    for k in order:
        if k in segs:
            seg_id = k
            spec = segs[k]
            break
    if not spec:
        return pmf, False, None
    t = str(spec.get("type") or "").lower()
    if t == "identity":
        return dict(pmf), True, seg_id
    if t != "temperature":
        return pmf, False, None
    temp = float(spec.get("T", 1.0))
    if not math.isfinite(temp) or temp <= 0:
        return pmf, False, None
    inv_t = 1.0 / temp
    out = {k: float(p) ** inv_t for k, p in pmf.items()}
    out = _renorm(out)
    return (out if out else None), True, seg_id


def load_model_only_calibration(path: Path | str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
