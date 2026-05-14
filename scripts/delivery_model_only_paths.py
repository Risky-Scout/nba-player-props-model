"""Shared MODEL_ONLY parquet discovery for daily delivery and verifiers.

Prefer ``deliveries/{date}/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet``
(stat_grid / rectangular canonical). Fall back to lexicographic last rglob match
only when canonical_source is absent (legacy layouts).
"""
from __future__ import annotations

from pathlib import Path


def _rel(repo_root: Path, p: Path) -> str:
    try:
        return str(p.resolve().relative_to(repo_root.resolve()))
    except Exception:
        return str(p)


def find_model_only_parquet_for_date(
    repo_root: Path, date: str,
) -> tuple[Path | None, list[Path], str | None]:
    """Return ``(chosen, all_candidates_sorted, warn_or_none)``."""
    base = repo_root / "deliveries" / date
    if not base.exists():
        return None, [], None
    preferred = base / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    candidates = sorted(base.rglob("player_prop_pmfs_tonight_MODEL_ONLY.parquet"))
    if preferred.is_file():
        warn = None
        if len(candidates) > 1:
            lines = "\n".join(f"  candidate: {_rel(repo_root, p)}" for p in candidates)
            warn = (
                f"MODEL_ONLY_PARQUET_WARN deliveries/{date}: "
                f"{len(candidates)} MODEL_ONLY parquets; "
                f"using canonical_source (preferred).\n{lines}"
            )
        return preferred.resolve(), candidates, warn
    if not candidates:
        return None, [], None
    chosen = candidates[-1]
    warn = None
    if len(candidates) > 1:
        lines = "\n".join(f"  candidate: {_rel(repo_root, p)}" for p in candidates)
        warn = (
            f"MODEL_ONLY_PARQUET_WARN deliveries/{date}: canonical_source missing; "
            f"{len(candidates)} MODEL_ONLY parquets; using lexicographic last.\n"
            f"{lines}\n"
            f"  chosen: {_rel(repo_root, chosen)}"
        )
    return chosen.resolve(), candidates, warn
