"""First-class odds_pairs selection for event-market tooling (supports `auto`)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Literal template tokens that must never be treated as real calendar paths.
PLACEHOLDER_PATH_SUBSTRINGS = (
    "YYYY-MM-DDTHH:MM:SSZ",
    "YYYY-MM-DDTHHMMSSZ",
    "YYYY-MM-DD",
    "THH:MM:SSZ",
)


def path_contains_placeholder_token(p: Path) -> bool:
    s = str(p)
    return any(tok in s for tok in PLACEHOLDER_PATH_SUBSTRINGS)


def _family_and_rank(name: str) -> tuple[str, int]:
    """Return (family, rank) where lower rank is higher priority."""
    n = name.lower()
    if "close_or_lock" in n:
        return "close_or_lock", 0
    if "live_slate" in n and "close_or_lock" in n:
        return "close_or_lock", 0
    if "live_slate" in n and "close" in n and "lock" in n:
        return "close_or_lock", 0
    if "hist_lockday" in n:
        return "hist_lockday", 1
    if "hist_slate" in n:
        return "hist_slate", 2
    return "other", 3


def _lock_offset_from_name(name: str) -> int | None:
    m = re.search(r"minus_(\d+)m", name.lower())
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    if "hist_lockday" in name.lower():
        return 5
    return None


def select_odds_pairs_parquet(
    repo_root: Path,
    date: str,
    snapshot_substr: str,
) -> tuple[Path | None, dict[str, Any]]:
    """Pick processed odds_pairs parquet for `date`.

    `snapshot_substr`:
      - ``"auto"`` — tiered preference: close_or_lock → hist_lockday → hist_slate → other
      - any other string — glob ``odds_pairs_*{substr}*.parquet`` then legacy fallback
    """
    base = repo_root / "data" / "odds_api" / "processed" / date
    empty_meta: dict[str, Any] = {
        "odds_snapshot_family": None,
        "odds_snapshot_path": None,
        "odds_snapshot_type": None,
        "odds_snapshot_substr_used": snapshot_substr,
        "odds_snapshot_rank": None,
        "odds_snapshot_is_historical": False,
        "odds_snapshot_lock_offset_minutes": None,
    }
    if not base.is_dir() or path_contains_placeholder_token(base):
        return None, empty_meta

    files = sorted(base.glob("odds_pairs_*.parquet"))
    files = [f for f in files if not path_contains_placeholder_token(f)]
    if not files:
        return None, empty_meta

    chosen: Path | None = None
    meta = dict(empty_meta)

    if snapshot_substr == "auto":
        chosen = None
        fam = "other"
        rnk = 3
        for tier_rank in range(4):
            tier = [f for f in files if _family_and_rank(f.name)[1] == tier_rank]
            if not tier:
                continue
            chosen = sorted(tier, key=lambda p: p.name)[-1]
            fam, rnk = _family_and_rank(chosen.name)
            break
        if chosen is None:
            return None, empty_meta
        meta["odds_snapshot_rank"] = int(rnk)
        meta["odds_snapshot_family"] = fam
        meta["odds_snapshot_path"] = str(chosen.relative_to(repo_root))
        meta["odds_snapshot_substr_used"] = "auto"
        meta["odds_snapshot_type"] = fam
        meta["odds_snapshot_is_historical"] = fam in ("hist_lockday", "hist_slate")
        meta["odds_snapshot_lock_offset_minutes"] = _lock_offset_from_name(chosen.name)
        return chosen, meta

    cand = sorted(base.glob(f"odds_pairs_*{snapshot_substr}*.parquet"))
    cand = [f for f in cand if not path_contains_placeholder_token(f)]
    if cand:
        chosen = cand[-1]
        fam, rnk = _family_and_rank(chosen.name)
        meta.update(
            {
                "odds_snapshot_rank": int(rnk),
                "odds_snapshot_family": fam,
                "odds_snapshot_path": str(chosen.relative_to(repo_root)),
                "odds_snapshot_substr_used": snapshot_substr,
                "odds_snapshot_type": fam,
                "odds_snapshot_is_historical": fam in ("hist_lockday", "hist_slate"),
                "odds_snapshot_lock_offset_minutes": _lock_offset_from_name(chosen.name),
            }
        )
        return chosen, meta

    chosen = files[-1]
    fam, rnk = _family_and_rank(chosen.name)
    meta.update(
        {
            "odds_snapshot_rank": int(rnk),
            "odds_snapshot_family": fam,
            "odds_snapshot_path": str(chosen.relative_to(repo_root)),
            "odds_snapshot_substr_used": snapshot_substr,
            "odds_snapshot_type": fam,
            "odds_snapshot_is_historical": fam in ("hist_lockday", "hist_slate"),
            "odds_snapshot_lock_offset_minutes": _lock_offset_from_name(chosen.name),
        }
    )
    return chosen, meta


def odds_selection_meta_json(meta: dict[str, Any]) -> str:
    return json.dumps(meta, sort_keys=True)
