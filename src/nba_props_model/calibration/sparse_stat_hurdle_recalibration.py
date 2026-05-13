"""Sparse stat hurdle: empirical p0 shift with renormalization (no market PMF)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def apply_p0_shift(pmf: dict[int, float], delta: float) -> dict[int, float]:
    """Move mass at k=0 by delta (clipped), renormalize. delta>0 increases p0."""
    if not pmf:
        return {}
    pmf = {int(k): float(v) for k, v in pmf.items()}
    p0 = pmf.get(0, 0.0)
    new0 = max(1e-12, min(1.0 - 1e-12, p0 + delta))
    rest = {k: v for k, v in pmf.items() if k != 0}
    s_rest = sum(rest.values())
    if s_rest <= 0:
        return {0: 1.0}
    scale = (1.0 - new0) / s_rest
    out = {0: new0}
    for k, v in rest.items():
        out[k] = v * scale
    tot = sum(out.values())
    return {k: v / tot for k, v in out.items()}


def load_offsets(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
