"""NBA official injury report (PDF) fetch with structured failure reasons.

Avoids nbainjuries' stdout ``Failed validation`` noise by downloading PDFs
directly, then invoking ``get_reportdata(..., local=True)``.

Reason strings are stable manifest / CI contract keys.
"""
from __future__ import annotations

import json
import logging
from io import BytesIO
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import AbstractSet, Any, Callable
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)

_ET = ZoneInfo("America/New_York")

# Manifest / log contract — lowercase snake keys
FUTURE_REPORT = "future_report_time_or_not_yet_available"
MISSING_FILE = "missing_file"
EMPTY_FILE = "empty_file"
MALFORMED_PDF = "malformed_pdf"
MISSING_REQUIRED_COLUMNS = "missing_required_columns"
NO_MATCHING_SLATE_TEAMS = "no_matching_slate_teams"
PARSE_ERROR = "parse_error"
STALE_OR_INCOMPLETE = "stale_or_incomplete"

_REASONS_NEEDING_ATTENTION = frozenset(
    {
        MISSING_FILE,
        EMPTY_FILE,
        MALFORMED_PDF,
        MISSING_REQUIRED_COLUMNS,
        NO_MATCHING_SLATE_TEAMS,
        PARSE_ERROR,
        STALE_OR_INCOMPLETE,
    }
)


def _repo_root_default() -> Path:
    return Path(__file__).resolve().parents[3]


def injury_report_stem_from_url(url: str) -> str:
    base = url.rsplit("/", 1)[-1]
    return base.removesuffix(".pdf") if base.endswith(".pdf") else base


def _default_candidate_hours_local(now_et: datetime) -> list[int]:
    """Return distinct ET hours, newest-first (typical release cadence)."""
    hours = {19, 17, 15, 13, 11}
    hours.add(now_et.hour)
    return sorted(hours, reverse=True)


def _nominal_report_dt(report_day: date, hour: int) -> datetime:
    return datetime.combine(report_day, time(hour, 0), tzinfo=_ET)


def _df_to_injury_dict(df: Any) -> dict[str, dict[str, str]]:
    injury_dict: dict[str, dict[str, str]] = {}
    for _, row in df.iterrows():
        name = str(row.get("Player Name", "")).strip()
        status = str(row.get("Current Status", "")).strip()
        reason = str(row.get("Reason", "")).strip()
        team = str(row.get("Team", "")).strip()
        if not name or name == "nan":
            continue
        parts = name.split(",")
        if len(parts) == 2:
            name_lower = f"{parts[1].strip()} {parts[0].strip()}".lower()
        else:
            name_lower = name.lower()
        payload: dict[str, str] = {"status": status, "reason": reason}
        if team and team != "nan":
            payload["team"] = team
        injury_dict[name_lower] = payload
    return injury_dict


def _slate_team_overlap_ok(df: Any, slate_team_full_names: AbstractSet[str]) -> bool:
    if not slate_team_full_names or df is None or df.empty:
        return True
    if "Team" not in df.columns:
        return False
    teams = {str(x).strip() for x in df["Team"].dropna().unique()}
    return bool(teams & slate_team_full_names)


@dataclass
class NBAOfficialInjuryReportResult:
    """Structured outcome for one fetch + select loop."""

    injury_dict: dict[str, dict[str, str]]
    selected_injury_report: str | None
    selected_injury_report_time: str | None
    injury_report_fallback_used: bool
    failed_injury_report_candidates: list[dict[str, str]] = field(default_factory=list)
    injury_freshness_status: str = "nba_official_report_unavailable"
    fetched_at_utc: str = ""

    def to_json_manifest(self) -> dict[str, Any]:
        return {
            "selected_injury_report": self.selected_injury_report,
            "selected_injury_report_time": self.selected_injury_report_time,
            "injury_report_fallback_used": self.injury_report_fallback_used,
            "failed_injury_report_candidates": list(self.failed_injury_report_candidates),
            "injury_freshness_status": self.injury_freshness_status,
            "fetched_at_utc": self.fetched_at_utc,
        }

    def write_artifact(self, repo_root: Path, slate_date: str) -> Path:
        out_dir = repo_root / "artifacts" / "injury_report_selection"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{slate_date}.json"
        out_path.write_text(json.dumps(self.to_json_manifest(), indent=2) + "\n")
        logger.info("Wrote NBA injury report selection manifest to %s", out_path)
        return out_path


_last_fetch_result: NBAOfficialInjuryReportResult | None = None


def peek_last_nba_official_injury_fetch() -> NBAOfficialInjuryReportResult | None:
    """Most recent ``fetch_nba_official_injury_report`` result in-process."""
    return _last_fetch_result


def _set_last_fetch_result(res: NBAOfficialInjuryReportResult) -> NBAOfficialInjuryReportResult:
    global _last_fetch_result
    _last_fetch_result = res
    return res


def fetch_nba_official_injury_report(
    *,
    report_day: date,
    now_utc: datetime | None = None,
    slate_team_full_names: AbstractSet[str] | None = None,
    repo_root: Path | None = None,
    slate_date_for_artifact: str | None = None,
    candidate_hours: list[int] | None = None,
    requests_get: Callable[..., Any] | None = None,
    get_reportdata: Callable[..., Any] | None = None,
) -> NBAOfficialInjuryReportResult:
    """Try NBA injury PDFs newest-first; return diagnostics + player map.

    ``slate_date_for_artifact`` when set triggers writing
    ``artifacts/injury_report_selection/{slate_date}.json`` under ``repo_root``.
    """
    from datetime import timezone as _tz

    get = requests_get or requests.get
    now_uc = (now_utc or datetime.now(_tz.utc)).astimezone(_tz.utc)
    now_et = now_uc.astimezone(_ET)
    fetched_iso = now_uc.isoformat(timespec="seconds").replace("+00:00", "Z")

    failed: list[dict[str, str]] = []
    root = repo_root or _repo_root_default()

    def _finalize_empty(
        status: str,
    ) -> NBAOfficialInjuryReportResult:
        out = NBAOfficialInjuryReportResult(
            injury_dict={},
            selected_injury_report=None,
            selected_injury_report_time=None,
            injury_report_fallback_used=False,
            failed_injury_report_candidates=failed,
            injury_freshness_status=status,
            fetched_at_utc=fetched_iso,
        )
        if slate_date_for_artifact:
            out.write_artifact(root, slate_date_for_artifact)
        return _set_last_fetch_result(out)

    try:
        from nbainjuries import _constants as _nb_const  # type: ignore
        from nbainjuries._exceptions import (  # type: ignore
            DataValidationError,
            LocalRetrievalError,
        )
        from nbainjuries.injury import gen_url, get_reportdata as _nb_get_reportdata  # type: ignore
    except Exception as exc:
        logger.warning("NBA injury report unavailable (nbainjuries import): %s", exc)
        failed.append({"report": "nbainjuries_unavailable", "reason": PARSE_ERROR})
        return _finalize_empty("parser_failure_needs_attention")

    _get = get_reportdata or _nb_get_reportdata
    headers = dict(_nb_const.requestheaders)
    hours = candidate_hours if candidate_hours is not None else _default_candidate_hours_local(now_et)
    tried_nonfuture = False

    for hour in hours:
        cand = _nominal_report_dt(report_day, hour)
        stem = injury_report_stem_from_url(gen_url(cand.replace(tzinfo=None)))

        if cand > now_et:
            failed.append({"report": stem, "reason": FUTURE_REPORT})
            logger.warning(
                "NBA injury report candidate skipped (not yet valid at runtime): report=%s reason=%s",
                stem,
                FUTURE_REPORT,
            )
            continue

        tried_nonfuture = True
        url = gen_url(cand.replace(tzinfo=None))

        try:
            resp = get(url, headers=headers, timeout=45)
        except requests.RequestException as exc:
            failed.append({"report": stem, "reason": MISSING_FILE})
            logger.warning(
                "NBA injury report candidate HTTP error: report=%s reason=%s detail=%s",
                stem,
                MISSING_FILE,
                exc,
            )
            continue

        if resp.status_code == 404:
            failed.append({"report": stem, "reason": MISSING_FILE})
            logger.warning(
                "NBA injury report candidate missing (404): report=%s reason=%s",
                stem,
                MISSING_FILE,
            )
            continue

        if resp.status_code >= 400:
            failed.append({"report": stem, "reason": MISSING_FILE})
            logger.warning(
                "NBA injury report candidate HTTP %s: report=%s reason=%s",
                resp.status_code,
                stem,
                MISSING_FILE,
            )
            continue

        if not resp.content:
            failed.append({"report": stem, "reason": EMPTY_FILE})
            logger.warning(
                "NBA injury report candidate empty body: report=%s reason=%s",
                stem,
                EMPTY_FILE,
            )
            continue

        df = None
        try:
            import PyPDF2  # type: ignore

            PyPDF2.PdfReader(BytesIO(resp.content))
        except Exception:
            failed.append({"report": stem, "reason": MALFORMED_PDF})
            logger.warning(
                "NBA injury report candidate unreadable PDF: report=%s reason=%s",
                stem,
                MALFORMED_PDF,
            )
            continue

        filename = url.rsplit("/", 1)[-1]
        try:
            with TemporaryDirectory() as tmp:
                (Path(tmp) / filename).write_bytes(resp.content)
                df = _get(
                    cand.replace(tzinfo=None),
                    local=True,
                    localdir=tmp,
                    return_df=True,
                )
        except DataValidationError as exc:
            reason = MISSING_REQUIRED_COLUMNS
            failed.append({"report": stem, "reason": reason})
            logger.warning(
                "NBA injury report candidate schema/header mismatch: report=%s reason=%s detail=%s",
                stem,
                reason,
                exc,
            )
            continue
        except LocalRetrievalError as exc:
            failed.append({"report": stem, "reason": MISSING_FILE})
            logger.warning(
                "NBA injury report candidate local read failed: report=%s reason=%s detail=%s",
                stem,
                MISSING_FILE,
                exc,
            )
            continue
        except Exception as exc:
            failed.append({"report": stem, "reason": PARSE_ERROR})
            logger.warning(
                "NBA injury report candidate parse failure: report=%s reason=%s detail=%s",
                stem,
                PARSE_ERROR,
                exc,
            )
            continue

        if df is None or df.empty:
            failed.append({"report": stem, "reason": STALE_OR_INCOMPLETE})
            logger.warning(
                "NBA injury report candidate empty table after parse: report=%s reason=%s",
                stem,
                STALE_OR_INCOMPLETE,
            )
            continue

        if slate_team_full_names and not _slate_team_overlap_ok(df, slate_team_full_names):
            failed.append({"report": stem, "reason": NO_MATCHING_SLATE_TEAMS})
            logger.warning(
                "NBA injury report candidate has no slate teams: report=%s reason=%s",
                stem,
                NO_MATCHING_SLATE_TEAMS,
            )
            continue

        injury_dict = _df_to_injury_dict(df)
        if not injury_dict:
            failed.append({"report": stem, "reason": STALE_OR_INCOMPLETE})
            logger.warning(
                "NBA injury report candidate parsed but no player rows: report=%s reason=%s",
                stem,
                STALE_OR_INCOMPLETE,
            )
            continue

        # Success on this candidate.
        fallback_used = len(failed) > 0
        parser_attention = any(
            entry["reason"] in _REASONS_NEEDING_ATTENTION for entry in failed
        )
        if parser_attention:
            freshness = "parser_failure_needs_attention"
        elif fallback_used:
            freshness = "fallback_used"
        else:
            freshness = "latest_valid_report_selected"

        time_iso = cand.isoformat(timespec="seconds")

        result = NBAOfficialInjuryReportResult(
            injury_dict=injury_dict,
            selected_injury_report=stem,
            selected_injury_report_time=time_iso,
            injury_report_fallback_used=fallback_used,
            failed_injury_report_candidates=failed,
            injury_freshness_status=freshness,
            fetched_at_utc=fetched_iso,
        )

        logger.info(
            "NBA injury report selected: report=%s fallback_used=%s freshness=%s",
            stem,
            fallback_used,
            freshness,
        )

        if slate_date_for_artifact:
            result.write_artifact(root, slate_date_for_artifact)
        return _set_last_fetch_result(result)

    # Exhausted candidates
    if not tried_nonfuture:
        status = "nba_official_report_unavailable"
    elif any(entry["reason"] in _REASONS_NEEDING_ATTENTION for entry in failed):
        status = "parser_failure_needs_attention"
    else:
        status = "nba_official_report_unavailable"

    return _finalize_empty(status)


def load_injury_report_selection(repo_root: Path, slate_date: str) -> dict[str, Any] | None:
    p = repo_root / "artifacts" / "injury_report_selection" / f"{slate_date}.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


INJURY_FRAGMENT_KEYS = (
    "selected_injury_report",
    "selected_injury_report_time",
    "injury_report_fallback_used",
    "failed_injury_report_candidates",
    "injury_freshness_status",
    "fetched_at_utc",
)


def merge_manifest_injury_fields(base: dict[str, Any], slate_date: str, repo_root: Path | None = None) -> None:
    """In-place merge of injury selection JSON into a manifest-style dict."""
    root = repo_root or _repo_root_default()
    blob = load_injury_report_selection(root, slate_date)
    if not blob:
        return
    for key in INJURY_FRAGMENT_KEYS:
        if key in blob:
            base[key] = blob[key]
