"""Shared lineup-freshness helpers.

Centralizes the row-level lineup metadata stamping used by:

  * scripts/build_stat_grid_pmfs.py    — upstream injection
  * scripts/build_daily_pmf_delivery.py — downstream enrichment
  * scripts/build_derek_forward_feed.py — feed-level surfacing

Single source of truth for the 5 lineup metadata fields each
delivery row must carry:

  * ``expected_lineup_status``      — projected | confirmed | not_available_yet
  * ``official_lineup_status``      — confirmed | projected | not_available_yet
  * ``lineup_source``                — bdl_lineup_freshness_manifest | ...
  * ``lineup_last_updated_utc``      — ISO 8601 UTC string (or None)
  * ``lineup_freshness_status``      — confirmed | projected | unknown

By stamping these at stat-grid time, they propagate naturally to
canonical MODEL_ONLY, market_comparison, and Derek's forward feed
without each downstream consumer needing to re-derive them.

Contract rules:

  * Morning runs default to ``expected_lineup_status="projected"`` +
    ``official_lineup_status="not_available_yet"`` — official lineups
    typically post ~30 minutes before tipoff, so the day-before /
    morning slate cannot legitimately stamp
    ``official_lineup_status="confirmed"`` even if the BDL endpoint
    happens to return rows.
  * Pre-tipoff / close-lock runs may pass
    ``allow_official_confirmation=True`` to promote
    ``official_lineup_status`` to ``"confirmed"`` when the BDL
    freshness manifest's ``lineup_confirmed=True`` for the game.
  * ``lineup_last_updated_utc`` reflects the per-game
    ``lineup_status.json#fetched_at_utc`` when present; ``None``
    otherwise (a forced-manual run before any lineup snapshot has
    been written).
  * ``lineup_source`` is always ``"bdl_lineup_freshness_manifest"``
    in the morning path — the lineup freshness manifest is the only
    upstream lineup signal we trust for projected lineups.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

LINEUP_SOURCE_DEFAULT = "bdl_lineup_freshness_manifest"


@dataclass
class LineupFreshnessSnapshot:
    """Per-(game_id, player_id) lineup context from the freshness manifest."""

    player_lookup: dict[tuple[str, int], dict[str, Any]]
    game_lookup: dict[str, dict[str, Any]]
    manifest_last_updated_utc: str | None

    @property
    def has_any_rows(self) -> bool:
        return bool(self.game_lookup)


def load_bdl_lineup_freshness_snapshot(
    repo_root: Path, delivery_date: str
) -> LineupFreshnessSnapshot:
    """Load per-player and per-game BDL lineup context from
    ``artifacts/live_lineups/<delivery_date>/``.

    Returns a :class:`LineupFreshnessSnapshot` with empty lookups and
    a ``None`` timestamp when the directory does not yet exist (the
    typical state for a morning forced-manual run on the day before
    a slate).
    """
    root = repo_root / "artifacts" / "live_lineups" / delivery_date
    if not root.is_dir():
        return LineupFreshnessSnapshot({}, {}, None)

    player_lookup: dict[tuple[str, int], dict[str, Any]] = {}
    game_lookup: dict[str, dict[str, Any]] = {}
    fetched_iso_values: list[str] = []

    for game_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        gid = str(game_dir.name)
        status_path = game_dir / "lineup_status.json"
        status: dict[str, Any] = {}
        if status_path.is_file():
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
            except Exception:
                status = {}
        confirmed = bool(status.get("lineup_confirmed"))
        total_rows = int(status.get("total_rows") or 0)
        fetched_iso = status.get("fetched_at_utc") or None
        if isinstance(fetched_iso, str) and fetched_iso.strip():
            fetched_iso_values.append(fetched_iso.strip())
        game_lookup[gid] = {
            "confirmed": confirmed,
            "has_rows": total_rows > 0,
            "source": str(status.get("source") or LINEUP_SOURCE_DEFAULT),
            "fetched_at_utc": fetched_iso,
            "lineup_blocker": status.get("lineup_blocker"),
        }

        norm_parquet = game_dir / "bdl_lineups_normalized.parquet"
        norm_csv = game_dir / "bdl_lineups_normalized.csv"
        lineup_df: pd.DataFrame | None = None
        try:
            if norm_parquet.is_file():
                lineup_df = pd.read_parquet(norm_parquet)
            elif norm_csv.is_file():
                lineup_df = pd.read_csv(norm_csv)
        except Exception:
            lineup_df = None
        if lineup_df is None or lineup_df.empty:
            continue
        for _, row in lineup_df.iterrows():
            try:
                pid = int(row.get("player_id"))
            except Exception:
                continue
            player_lookup[(gid, pid)] = {
                "starter": bool(row.get("starter")),
                "lineup_position": row.get("lineup_position"),
                "source": str(row.get("source") or LINEUP_SOURCE_DEFAULT),
            }

    manifest_last_updated_utc = (
        max(fetched_iso_values) if fetched_iso_values else None
    )
    return LineupFreshnessSnapshot(
        player_lookup=player_lookup,
        game_lookup=game_lookup,
        manifest_last_updated_utc=manifest_last_updated_utc,
    )


def derive_lineup_metadata_for_row(
    *,
    game_id: int | str | None,
    player_id: int | None,
    role_source: str | None,
    snapshot: LineupFreshnessSnapshot,
    allow_official_confirmation: bool = False,
) -> dict[str, Any]:
    """Return the 5-field lineup metadata dict (plus possibly upgraded
    ``role_source``) for one delivery row.

    ``allow_official_confirmation=False`` (the default for the
    morning / forced-manual path) forces ``official_lineup_status``
    to remain ``"projected"`` even when the BDL freshness manifest
    has ``lineup_confirmed=True`` for the game. This honors the
    contract that morning output must remain provisional / projected
    until the pre-tipoff or close-lock window. Pre-tipoff / close-
    lock modes may pass ``allow_official_confirmation=True`` so that
    confirmed lineups can promote ``official_lineup_status`` to
    ``"confirmed"`` and ``role_source`` to
    ``"confirmed_bdl_lineup"``.
    """
    role_source = role_source or "unknown"

    expected_lineup_status = "projected"
    official_lineup_status = "not_available_yet"
    lineup_last_updated_utc: str | None = None
    derived_role_source = role_source

    if game_id is not None and snapshot.has_any_rows:
        try:
            game_key = str(int(game_id))
        except Exception:
            game_key = str(game_id)
        game_ctx = snapshot.game_lookup.get(game_key)
        player_ctx = None
        if player_id is not None and snapshot.player_lookup:
            try:
                pid_int = int(player_id)
            except Exception:
                pid_int = None
            if pid_int is not None:
                player_ctx = snapshot.player_lookup.get((game_key, pid_int))
        if game_ctx:
            expected_lineup_status = "projected"
            lineup_last_updated_utc = game_ctx.get("fetched_at_utc")
            if game_ctx.get("confirmed") and allow_official_confirmation:
                official_lineup_status = "confirmed"
                if player_ctx and bool(player_ctx.get("starter")):
                    derived_role_source = "confirmed_bdl_lineup"
            elif game_ctx.get("confirmed"):
                # Confirmed by BDL but caller refuses to promote
                # (morning contract). Surface as projected so the
                # final lineup contract is honored.
                official_lineup_status = "projected"
                if derived_role_source in (
                    "unknown", "derived_from_projected_minutes",
                ):
                    derived_role_source = "projected_bdl_lineup"
            elif game_ctx.get("has_rows"):
                official_lineup_status = "projected"
                if derived_role_source in (
                    "unknown", "derived_from_projected_minutes",
                ):
                    derived_role_source = "projected_bdl_lineup"

    lineup_freshness_status = compute_lineup_freshness_status(
        official_lineup_status=official_lineup_status,
        expected_lineup_status=expected_lineup_status,
        role_source=derived_role_source,
    )

    return {
        "expected_lineup_status": expected_lineup_status,
        "official_lineup_status": official_lineup_status,
        "lineup_source": LINEUP_SOURCE_DEFAULT,
        "lineup_last_updated_utc": lineup_last_updated_utc,
        "lineup_freshness_status": lineup_freshness_status,
        "role_source": derived_role_source,
    }


def compute_lineup_freshness_status(
    *,
    official_lineup_status: str | None,
    expected_lineup_status: str | None,
    role_source: str | None,
) -> str:
    """Row-level flag describing how trustworthy the lineup signal is.

    Returns one of:

      * ``"confirmed"`` — BDL endpoint reports confirmed lineup AND
        caller promoted it.
      * ``"projected"`` — morning / pre-confirmation snapshot.
      * ``"unknown"`` — no usable signal.
    """
    official = (official_lineup_status or "").lower().strip()
    expected = (expected_lineup_status or "").lower().strip()
    src = (role_source or "").lower()
    if official in {"confirmed", "official_confirmed", "available"}:
        return "confirmed"
    if official in {"projected", "partial"}:
        return "projected"
    if expected in {"projected", "expected_probable"}:
        return "projected"
    if "confirmed" in src:
        return "confirmed"
    if (
        "projected" in src
        or "minutes_distribution" in src
        or "derived_from_projected_minutes" in src
    ):
        return "projected"
    return "unknown"
