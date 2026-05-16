"""Row-level injury freshness helpers.

Centralizes the *row-level* injury-freshness verdict used by
``scripts/build_daily_pmf_delivery.py`` when deciding whether the
canonical delivery quality rollup should raise
``injury_very_stale``.

Historically the rollup decision was made by stamping every row's
``injury_freshness_status`` to whatever ``_injury_freshness(path)``
returned for ``data/player_availability_asof.parquet`` — i.e. a
**file mtime** classification. This led to "false positive" stale
flags: an upstream stat-grid run that legitimately selected a
fresh NBA official injury PDF could still have its rows tagged as
stale just because the disk file backing
``player_availability_asof.parquet`` was older than the freshness
window. Worse, when stat-grid stamps a successful status like
``latest_valid_report_selected`` on every row, the rollup's
"is any row 'fresh'?" check used the string ``"fresh"`` literally
and did not recognize the NBA-fetcher taxonomy at all.

This module replaces the file-mtime decision with a strict
*row-level* one:

  * The status strings emitted by the NBA official-report fetcher
    (`latest_valid_report_selected`, `fallback_used`) are treated
    as fresh-equivalent.
  * The file-mtime taxonomy string `"fresh"` is also accepted for
    backwards compatibility with the rare path that still stamps
    that value.
  * As a tertiary signal — when status alone is inconclusive — we
    use the row's ``injury_report_fetched_at_utc`` timestamp and a
    short freshness window to determine fresh-equivalence.
  * Every other status (`unknown`, `nba_official_report_unavailable`,
    `parser_failure_needs_attention`, `none`, missing/null) is
    treated as **not fresh**. The rollup keeps
    ``injury_very_stale`` and ``market_superiority_claim_allowed``
    must remain ``False`` when the NBA injury report has not yet
    been published for the slate.

The companion ``classify_canonical_injury_freshness`` returns a
breakdown of (`is_fresh`, `reason`, `evidence`) so the manifest
can carry an informative `detail` field instead of a vague
"injury_very_stale".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

INJURY_FRESH_WINDOW_HOURS = 12.0

FRESH_EQUIVALENT_STATUSES = frozenset(
    {
        "fresh",
        "latest_valid_report_selected",
        "fallback_used",
    }
)

# Statuses that explicitly indicate the NBA official report is not
# available right now (either truly unpublished, or the fetcher
# could not parse it). These can never be promoted to fresh based
# on a timestamp alone.
NOT_FRESH_STATUSES = frozenset(
    {
        "unknown",
        "none",
        "nba_official_report_unavailable",
        "parser_failure_needs_attention",
        "stale",
        "very_stale",
        "missing",
    }
)


@dataclass
class CanonicalInjuryFreshnessVerdict:
    """Outcome of evaluating the canonical injury rollup row-by-row."""

    is_fresh_overall: bool
    fresh_row_count: int
    total_row_count: int
    dominant_status: str | None
    dominant_status_count: int
    sample_fetched_at_utc: str | None
    reason: str

    def to_manifest_detail(self) -> str:
        """Human-readable explanation for the manifest blocker."""
        if self.is_fresh_overall:
            return (
                f"row_level_injury_fresh_rows={self.fresh_row_count}/"
                f"{self.total_row_count}"
            )
        return (
            "No canonical delivery row had a row-level injury freshness "
            f"verdict of fresh. row_level_injury_fresh_rows="
            f"{self.fresh_row_count}/{self.total_row_count}; "
            f"dominant_status={self.dominant_status!r} "
            f"(count={self.dominant_status_count}); "
            f"sample_injury_report_fetched_at_utc="
            f"{self.sample_fetched_at_utc!r}; "
            f"reason={self.reason}"
        )


def _parse_iso_utc(value: Any) -> datetime | None:
    """Parse an ISO 8601 UTC string into an aware datetime.

    Returns ``None`` for empty/invalid values. Accepts the trailing
    ``Z`` shorthand and offsetless forms.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def row_injury_freshness_verdict(
    *,
    injury_freshness_status: Any,
    injury_report_fetched_at_utc: Any,
    now_utc: datetime | None = None,
    fresh_window_hours: float = INJURY_FRESH_WINDOW_HOURS,
) -> bool:
    """Decide whether a single canonical row qualifies as fresh.

    Priority:

      1. If ``injury_freshness_status`` is in
         ``FRESH_EQUIVALENT_STATUSES``, the row is fresh.
      2. If ``injury_freshness_status`` is in
         ``NOT_FRESH_STATUSES`` (or null/empty), the row is **not**
         fresh — no timestamp promotion allowed. This is the
         "report not yet published" case.
      3. Otherwise (some unknown future status string) fall back to
         the ``injury_report_fetched_at_utc`` recency check.

    Note: this function deliberately does NOT consult any file
    mtime. Manifest-level freshness must be a function of row-level
    evidence, not how recently we happened to write the on-disk
    availability table.
    """
    status_raw = injury_freshness_status
    status = str(status_raw or "").strip().lower()
    if status in FRESH_EQUIVALENT_STATUSES:
        return True
    if status in NOT_FRESH_STATUSES:
        return False
    if not status:
        return False
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    fetched = _parse_iso_utc(injury_report_fetched_at_utc)
    if fetched is None:
        return False
    age_hours = (now - fetched).total_seconds() / 3600.0
    return age_hours <= fresh_window_hours


def classify_canonical_injury_freshness(
    *,
    statuses: Iterable[Any],
    fetched_at_values: Iterable[Any],
    now_utc: datetime | None = None,
    fresh_window_hours: float = INJURY_FRESH_WINDOW_HOURS,
) -> CanonicalInjuryFreshnessVerdict:
    """Run :func:`row_injury_freshness_verdict` across the whole
    canonical frame and roll the result up.

    ``statuses`` and ``fetched_at_values`` are parallel iterables —
    one entry per canonical row — so we never need to materialize
    the full DataFrame here. The caller is expected to pass the
    canonical's ``injury_freshness_status`` and
    ``injury_report_fetched_at_utc`` columns.
    """
    statuses_list = [s for s in statuses]
    fetched_list = [f for f in fetched_at_values]

    if len(statuses_list) != len(fetched_list):
        raise ValueError(
            "statuses and fetched_at_values must be the same length "
            f"(got {len(statuses_list)} and {len(fetched_list)})"
        )

    fresh_count = 0
    status_counts: dict[str, int] = {}
    sample_fetched: str | None = None
    for status_raw, fetched_raw in zip(statuses_list, fetched_list):
        if row_injury_freshness_verdict(
            injury_freshness_status=status_raw,
            injury_report_fetched_at_utc=fetched_raw,
            now_utc=now_utc,
            fresh_window_hours=fresh_window_hours,
        ):
            fresh_count += 1
        key = (str(status_raw).strip() if status_raw not in (None, "") else "<null>")
        status_counts[key] = status_counts.get(key, 0) + 1
        if sample_fetched is None and isinstance(fetched_raw, str) and fetched_raw.strip():
            sample_fetched = fetched_raw.strip()

    dominant_status: str | None = None
    dominant_count = 0
    for k, v in status_counts.items():
        if v > dominant_count:
            dominant_status, dominant_count = k, v

    total = len(statuses_list)
    is_fresh = fresh_count > 0
    if is_fresh:
        reason = "row_level_fresh_status_or_recent_timestamp"
    elif total == 0:
        reason = "canonical_has_no_rows"
    elif dominant_status in {"unknown", "<null>", "none", "nba_official_report_unavailable"}:
        reason = "injury_report_not_yet_published_or_unavailable"
    elif dominant_status == "parser_failure_needs_attention":
        reason = "injury_report_parser_failure_needs_attention"
    else:
        reason = "row_level_injury_status_not_fresh"

    return CanonicalInjuryFreshnessVerdict(
        is_fresh_overall=is_fresh,
        fresh_row_count=fresh_count,
        total_row_count=total,
        dominant_status=dominant_status,
        dominant_status_count=dominant_count,
        sample_fetched_at_utc=sample_fetched,
        reason=reason,
    )
