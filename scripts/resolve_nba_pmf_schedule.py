#!/usr/bin/env python3
"""Single source of truth for the consolidated NBA PMF Delivery workflow.

This script replaces inline YAML schedule routing in
``.github/workflows/nba_pmf_delivery.yml``. Given the GitHub Actions
event context (``--event-name``, ``--schedule``, plus manual
``workflow_dispatch`` inputs), it resolves:

- ``delivery_date``: slate ET date (YYYY-MM-DD)
- ``as_of_date``: training as-of ET date (YYYY-MM-DD)
- ``stage``: high-level pipeline stage label
- ``mode``: delivery-pipeline mode label (e.g. ``derek_near_lineup``)
- ``run_predict``, ``run_training``, ``run_phase8``, ``run_phase13``,
  ``run_delivery``, ``run_after_game``, ``run_verifiers``:
  per-job gate, "true" or "false"
- ``allow_promote``: champion-promotion permission, "true" / "false"
- ``force_run``: manual bypass of delivery time-window gates
- ``valid_skip_reason``: non-empty string when a scheduled cron must
  cleanly valid-skip (e.g. outside Derek window). Downstream jobs gate
  on this so they exit success-skipped instead of failing.

The script writes every output to ``$GITHUB_OUTPUT`` (when provided) in
``key=value`` format. It also prints exactly one human-readable summary
line to stdout: ``NBA_PMF_SCHEDULE_RESOLVED ...``.

Critical design constraints (from ``.cursor/rules/01_production_schedule.mdc``
and ``CURSOR_TASK_NBA_PMF_PRODUCTION_PIPELINE.md``):

- All slate logic runs in ``America/New_York``. UTC dates are never
  used for ``delivery_date`` / ``as_of_date`` reasoning.
- 06:30 UTC ``after_game`` scores the **previous** ET slate.
- 07:30/12:30 UTC ``model_chain`` runs may promote.
- 14:30 UTC is the promotion cutoff (15:30/18:30/21:30 UTC ``model_chain_no_promote``).
- 14:00 UTC ``predict`` runs the daily prediction pipeline.
- 15:00 UTC ``woo_morning_monetization``, 18:00/20:00 UTC
  ``woo_afternoon_refresh`` deliver to Wizard of Odds.
- 22:25 UTC through 03:25 UTC Derek-candidate crons valid-skip unless
  ``now`` is 35→0 minutes pre-tip for an actual scheduled game.
- Manual ``workflow_dispatch`` runs honor explicit ``delivery_date`` /
  ``as_of_date`` overrides and ``force_run=true`` bypasses the
  Derek-window gate for manual smoke tests/backfills.

The script must only use the Python standard library — no third-party
imports — so it can run during ``readiness`` before pip-installed
dependencies are available.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date as date_cls
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
UTC = timezone.utc

REPO_ROOT = Path(__file__).resolve().parents[1]

# Window definitions (minutes pre-tip, inclusive).
DEREK_NEAR_LINEUP_WINDOW = (11, 35)   # 35→11 min pre-tip
DEREK_CLOSE_LOCK_WINDOW = (0, 10)     # 10→0 min pre-tip

# Derek candidate cron strings. Used to know "this is a Derek-window
# cron whose run_delivery decision depends on the slate tip time".
DEREK_CANDIDATE_CRONS = frozenset({
    "25 22 * * *",
    "40,55 22 * * *",
    "10,25,40,55 23,0,1,2 * * *",
    "10 3 * * *",
    "25 3 * * *",
})

# Scheduled delivery crons that ALWAYS run regardless of tip time
# (they target WoO publishing windows, not tipoff windows).
SCHEDULED_DELIVERY_CRONS = {
    "0 15 * * *": "woo_morning_monetization",
    "0 18 * * *": "woo_afternoon_refresh",
    "0 20 * * *": "woo_afternoon_refresh",
}

# Scheduled model_chain crons with promotion allowed.
# 07:30 UTC (3:30 AM ET) is primary — fires ~1 h after after-game scoring
# (06:30 UTC) so Phase 8 + Phase 13 (~6 h total) completes by 13:30 UTC
# (9:30 AM ET), before the 14:00 UTC morning prediction run.
# 12:30 UTC is the backup retry if the 07:30 UTC run fails early.
MODEL_CHAIN_PROMOTE_CRONS = frozenset({
    "30 7 * * *",
    "30 12 * * *",
})

# Scheduled model_chain crons WITHOUT promotion (post-14:30 UTC cutoff).
MODEL_CHAIN_NO_PROMOTE_CRONS = frozenset({
    "30 15 * * *",
    "30 18 * * *",
    "30 21 * * *",
})


@dataclass
class ResolverOutputs:
    """Structured resolver outputs.

    Order matches the documented contract in
    ``CURSOR_TASK_NBA_PMF_PRODUCTION_PIPELINE.md`` Phase 1.
    """

    delivery_date: str = ""
    as_of_date: str = ""
    stage: str = ""
    mode: str = ""
    run_predict: bool = False
    run_training: bool = False
    run_phase8: bool = False
    run_phase13: bool = False
    run_delivery: bool = False
    run_after_game: bool = False
    run_verifiers: bool = False
    allow_promote: bool = False
    force_run: bool = False
    valid_skip_reason: str = ""

    # Diagnostic-only fields (not written to GITHUB_OUTPUT but emitted
    # on the human-readable summary line so logs are self-explanatory).
    notes: list[str] = field(default_factory=list)

    def as_output_dict(self) -> dict[str, str]:
        """Return only the brief-required outputs as string key/value."""

        return {
            "delivery_date": self.delivery_date,
            "as_of_date": self.as_of_date,
            "stage": self.stage,
            "mode": self.mode,
            "run_predict": _bool_str(self.run_predict),
            "run_training": _bool_str(self.run_training),
            "run_phase8": _bool_str(self.run_phase8),
            "run_phase13": _bool_str(self.run_phase13),
            "run_delivery": _bool_str(self.run_delivery),
            "run_after_game": _bool_str(self.run_after_game),
            "run_verifiers": _bool_str(self.run_verifiers),
            "allow_promote": _bool_str(self.allow_promote),
            "force_run": _bool_str(self.force_run),
            "valid_skip_reason": self.valid_skip_reason,
        }


# ── Helpers ─────────────────────────────────────────────────────────


def _bool_str(value) -> str:
    """Coerce arbitrary input to the literal ``"true"`` or ``"false"``."""

    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return "true" if value.strip().lower() == "true" else "false"
    return "true" if bool(value) else "false"


def _parse_bool_input(value: str) -> bool:
    """Parse a GitHub Actions boolean-ish string ('true'/'false'/'')."""

    if value is None:
        return False
    return value.strip().lower() == "true"


def _to_et_date(now_utc: datetime) -> date_cls:
    """Return the ET calendar date of a UTC datetime."""

    return now_utc.astimezone(ET).date()


def _yesterday_et(now_utc: datetime) -> date_cls:
    """Return the ET calendar date of the day before now."""

    return _to_et_date(now_utc) - timedelta(days=1)


def _parse_now_utc(now_str: Optional[str]) -> datetime:
    """Parse an ISO-8601 ``--now-utc`` argument, defaulting to wall clock.

    Accepts e.g. ``2026-05-20T14:00:00Z`` and ``2026-05-20T14:00:00+00:00``.
    """

    if not now_str:
        return datetime.now(UTC)
    s = now_str.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(UTC)


def _resolve_repo_root(repo_root: Optional[Path] = None) -> Path:
    """Return the repo root for on-disk lookups.

    Resolution order:

    1. Explicit ``repo_root`` argument (used by tests that thread a tmp
       path directly through the resolver helpers).
    2. ``NBA_PMF_TEST_REPO_ROOT`` env var — test-only override so unit
       tests can point both ``_resolve_slate_tipoff`` and
       ``_slate_exists_for_date`` at a controlled fixture directory
       without touching the real repo workspace.
    3. Module-level ``REPO_ROOT``.
    """

    if repo_root is not None:
        return Path(repo_root)
    env_override = os.environ.get("NBA_PMF_TEST_REPO_ROOT", "").strip()
    if env_override:
        return Path(env_override)
    return REPO_ROOT


def _resolve_slate_tipoff(
    delivery_date: str,
    *,
    repo_root: Optional[Path] = None,
) -> Optional[datetime]:
    """Return the earliest scheduled tipoff for ``delivery_date`` as UTC.

    Resolution order:

    1. ``NBA_PMF_TEST_TIPOFF_ET`` env var (test-only override). Accepted
       formats: ISO-8601 with explicit offset (e.g.
       ``2026-05-20T20:30:00-04:00``) or without offset (interpreted as
       America/New_York wall clock).
    2. On-disk ``artifacts/live_schedule/<delivery_date>/game_start_times.json``
       written by ``scripts/resolve_game_start_times.py``. Each entry is
       expected to carry ``game_start_time_utc`` (preferred),
       ``start_time_utc``, ``tipoff_utc``, ``scheduled_start_utc``,
       ``commence_time``, or ``game_start_time_et`` (case-insensitive
       lookup). We pick the EARLIEST tip for the slate.
    3. Return ``None`` so the caller decides whether to valid-skip
       (``no_tip_time_resolved``) or emit a loud failure
       (``tip_time_unresolved_but_slate_exists``) based on whether
       slate-presence signals exist on disk for ``delivery_date``.

    This function never fabricates a tip time. If the on-disk JSON
    cannot be parsed or contains no recognizable timestamps it returns
    ``None`` and lets the caller decide.
    """

    test_env = os.environ.get("NBA_PMF_TEST_TIPOFF_ET", "").strip()
    if test_env:
        return _parse_tip_string(test_env)

    repo_root = _resolve_repo_root(repo_root)
    candidate = repo_root / "artifacts" / "live_schedule" / delivery_date / "game_start_times.json"
    if not candidate.is_file():
        return None
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    games = _extract_games_list(payload)
    if not games:
        return None

    tip_keys = (
        "game_start_time_utc",
        "start_time_utc",
        "tipoff_utc",
        "scheduled_start_utc",
        "commence_time",
        "game_start_time_et",
        "start_time_et",
        "tipoff_et",
    )

    tips: list[datetime] = []
    for g in games:
        if not isinstance(g, dict):
            continue
        for key in tip_keys:
            for k in (key, key.upper()):
                if k in g and g[k]:
                    parsed = _parse_tip_string(str(g[k]))
                    if parsed is not None:
                        tips.append(parsed)
                    break
            else:
                continue
            break
    if not tips:
        return None
    return min(tips)


def _parse_tip_string(s: str) -> Optional[datetime]:
    """Parse a tip-time string into a UTC datetime.

    Accepts ISO-8601 with or without timezone offset. Strings without
    offset are interpreted as America/New_York wall clock.
    Returns ``None`` on failure.
    """

    s = s.strip()
    if not s:
        return None
    iso = s[:-1] + "+00:00" if s.endswith("Z") else s
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ET)
    return dt.astimezone(UTC)


def _extract_games_list(payload) -> list:
    """Return the list of games from a permissive JSON shape."""

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("games", "game_start_times", "scheduled_games", "rows", "data"):
            v = payload.get(key)
            if isinstance(v, list):
                return v
        # Fallback: if it looks like a single game dict, wrap it.
        return [payload]
    return []


def _default_tip_time_generator(
    delivery_date: str,
    *,
    repo_root: Path,
) -> int:
    """Invoke ``scripts/resolve_game_start_times.py`` as a subprocess.

    Used as the production implementation of the in-resolver tip-time
    recovery hook. Returns the subprocess exit code (0 == success).
    Inherits the parent process environment so ``BDL_API_KEY`` /
    ``ODDS_API_KEY`` reach the generator when the workflow exposes them.

    A non-zero exit, a generator that exits 0 but writes no usable
    file, or any failure to spawn the subprocess (``FileNotFoundError``,
    ``PermissionError``) all collapse to "recovery did not produce a
    usable tip time" — the caller re-attempts :func:`_resolve_slate_tipoff`
    and falls back to PR #31's loud-failure path when that re-attempt
    still returns ``None``.
    """

    script = repo_root / "scripts" / "resolve_game_start_times.py"
    if not script.is_file():
        return 127
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--delivery-date", delivery_date],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return 1
    return int(result.returncode or 0)


# Module-level seam so tests can monkeypatch the recovery hook without
# touching ``subprocess``. Production code calls ``TIP_TIME_GENERATOR``;
# tests replace it with a fake that writes a controlled fixture or
# raises to simulate provider failures.
TIP_TIME_GENERATOR: Callable[..., int] = _default_tip_time_generator


def _slate_exists_for_date(
    delivery_date: str,
    *,
    repo_root: Optional[Path] = None,
) -> bool:
    """Return ``True`` if any on-disk signal proves a real slate exists.

    We treat the existence of any of the following files as unambiguous
    proof that the workflow's prior runs already concluded a real NBA
    slate exists for ``delivery_date``:

    - ``deliveries/<delivery_date>/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet``
      (canonical model-only PMF — only emitted when the daily delivery
      pipeline's ``games_exist`` branch ran).
    - ``deliveries/<delivery_date>/canonical_source/all_props_model_only.parquet``
      (companion canonical artifact, same gate).
    - ``predictions/all_props_<delivery_date>.parquet``
      (written by the 14:00 UTC daily prediction cron when the slate is
      non-empty).
    - ``predictions/pmf_display_<delivery_date>.json``
      (written by the same daily prediction step).

    None of these supply a tip-time *value*; they only prove that a
    slate exists. Callers that need a tip time must still defer to
    :func:`_resolve_slate_tipoff` and refuse to fabricate.
    """

    repo_root = _resolve_repo_root(repo_root)
    candidates = (
        repo_root / "deliveries" / delivery_date / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet",
        repo_root / "deliveries" / delivery_date / "canonical_source" / "all_props_model_only.parquet",
        repo_root / "predictions" / f"all_props_{delivery_date}.parquet",
        repo_root / "predictions" / f"pmf_display_{delivery_date}.json",
    )
    return any(p.is_file() for p in candidates)


# ── Stage resolvers ─────────────────────────────────────────────────


def _resolve_scheduled(args, now_utc: datetime) -> ResolverOutputs:
    """Resolve outputs for a scheduled cron event."""

    sched = (args.schedule or "").strip()
    out = ResolverOutputs()
    today_et = _to_et_date(now_utc).isoformat()
    yesterday_et = _yesterday_et(now_utc).isoformat()

    # 06:30 UTC — after-game scores PREVIOUS ET slate.
    if sched == "30 6 * * *":
        out.stage = "after_game"
        out.mode = "after_game"
        out.delivery_date = yesterday_et
        out.as_of_date = yesterday_et
        out.run_after_game = True
        out.run_verifiers = True
        out.allow_promote = False
        return out

    # 07:30 / 12:30 UTC — model chain WITH promotion permission.
    if sched in MODEL_CHAIN_PROMOTE_CRONS:
        out.stage = "model_chain"
        out.mode = "model_chain"
        out.delivery_date = today_et
        out.as_of_date = yesterday_et
        out.run_training = True
        out.run_phase8 = True
        out.run_phase13 = True
        out.run_verifiers = True
        out.allow_promote = True
        return out

    # 15:30 / 18:30 / 21:30 UTC — model chain post 14:30 cutoff, NO promotion.
    if sched in MODEL_CHAIN_NO_PROMOTE_CRONS:
        out.stage = "model_chain_no_promote"
        out.mode = "model_chain_no_promote"
        out.delivery_date = today_et
        out.as_of_date = yesterday_et
        out.run_training = True
        out.run_phase8 = True
        out.run_phase13 = True
        out.run_verifiers = True
        out.allow_promote = False
        return out

    # 14:00 UTC — daily prediction.
    if sched == "0 14 * * *":
        out.stage = "predict"
        out.mode = "predict"
        out.delivery_date = today_et
        out.as_of_date = yesterday_et
        out.run_predict = True
        out.run_verifiers = True
        out.allow_promote = False
        return out

    # 15:00 / 18:00 / 20:00 UTC — WoO delivery windows.
    if sched in SCHEDULED_DELIVERY_CRONS:
        out.stage = "delivery"
        out.mode = SCHEDULED_DELIVERY_CRONS[sched]
        out.delivery_date = today_et
        out.as_of_date = yesterday_et
        out.run_delivery = True
        out.run_verifiers = True
        out.allow_promote = False
        return out

    # 22:25 / 22:40 / 22:55 / 23:10/25/40/55 / 00:10/25/40/55 /
    # 01:10/25/40/55 / 02:10/25/40/55 / 03:10 / 03:25 UTC —
    # Derek candidate windows. Resolve tip time and gate.
    if sched in DEREK_CANDIDATE_CRONS:
        out.stage = "delivery"
        out.delivery_date = today_et
        out.as_of_date = yesterday_et
        out.run_verifiers = True
        out.allow_promote = False
        _gate_on_tipoff(out, now_utc)
        return out

    # Unknown schedule — emit valid_skip rather than crash so a stray
    # cron addition can't take down the workflow.
    out.delivery_date = today_et
    out.as_of_date = yesterday_et
    out.valid_skip_reason = f"unknown_schedule_{sched.replace(' ', '_')}"
    return out


def _gate_on_tipoff(out: ResolverOutputs, now_utc: datetime) -> None:
    """Mutate ``out`` based on minutes-before-tipoff for the slate.

    Resolution order for tipoff (newly extended for upstream recovery):

    1. Read the on-disk cache
       ``artifacts/live_schedule/<date>/game_start_times.json`` via
       :func:`_resolve_slate_tipoff`. This is the fast path used when
       the Derek live-snapshots workflow's generator already wrote a
       fresh cache for this slate.
    2. If the cache is missing AND :func:`_slate_exists_for_date`
       confirms a real slate exists for ``delivery_date``, invoke the
       :data:`TIP_TIME_GENERATOR` recovery hook
       (production: subprocess-out to
       ``scripts/resolve_game_start_times.py``). The hook is responsible
       for writing the cache file from real upstream sources
       (Odds API events / BDL ``/v1/games``); we then re-attempt step 1.
       This is the new automation path that prevents scheduled
       ``morning`` / ``derek_near_lineup`` / ``close_lock`` windows from
       silently green-skipping when the upstream Derek live-snapshots
       commit chain has not landed yet. The hook is never invoked when
       no slate-presence signal exists, so dark-slate days still skip
       legitimately.
    3. After step 2's attempted recovery, if tipoff is still ``None``:
       - If a slate clearly exists →
         ``valid_skip_reason="tip_time_unresolved_but_slate_exists"`` and
         ``main()`` exits non-zero (PR #31's loud-failure safety net for
         genuine provider failure / missing secrets / API outage).
       - If no slate-presence signal exists → legitimate
         ``valid_skip_reason="no_tip_time_resolved"`` green-skip
         preserved for empty slate days.

    No tip time is ever fabricated. The recovery hook only invokes a
    real-source generator; if every honest source returns nothing, the
    loud failure path takes over.
    """

    tipoff_utc = _resolve_slate_tipoff(out.delivery_date)
    slate_present = _slate_exists_for_date(out.delivery_date)

    if tipoff_utc is None and slate_present:
        # Upstream tip-time recovery: cache is missing but a real slate
        # exists. Invoke the recovery hook (subprocess-out to the
        # generator in production, monkeypatched stub in tests) and
        # re-attempt cache resolution exactly once.
        try:
            recovery_rc = TIP_TIME_GENERATOR(
                out.delivery_date,
                repo_root=_resolve_repo_root(),
            )
        except Exception as exc:  # noqa: BLE001
            recovery_rc = 1
            out.notes.append(
                f"tip_time_recovery_raised={type(exc).__name__}:{exc}"
            )
        else:
            out.notes.append(f"tip_time_recovery_rc={recovery_rc}")
        if recovery_rc == 0:
            tipoff_utc = _resolve_slate_tipoff(out.delivery_date)
            if tipoff_utc is not None:
                out.notes.append("tip_time_recovery_source=generator")

    if tipoff_utc is None:
        out.run_delivery = False
        out.mode = "derek_near_lineup"  # placeholder so logs are stable
        if slate_present:
            out.valid_skip_reason = "tip_time_unresolved_but_slate_exists"
            out.notes.append(
                "loud_failure=tip_time_unresolved_but_slate_exists "
                f"delivery_date={out.delivery_date}"
            )
        else:
            out.valid_skip_reason = "no_tip_time_resolved"
        return

    delta_min = (tipoff_utc - now_utc).total_seconds() / 60.0
    out.notes.append(f"tipoff_utc={tipoff_utc.isoformat()} delta_min={delta_min:.1f}")

    # ``derek_near_lineup``: 35 → 11 minutes pre-tip (inclusive).
    if DEREK_NEAR_LINEUP_WINDOW[0] <= delta_min <= DEREK_NEAR_LINEUP_WINDOW[1]:
        out.mode = "derek_near_lineup"
        out.run_delivery = True
        return

    # ``close_lock``: 10 → 0 minutes pre-tip (inclusive). Treat negative
    # deltas (already tipped off) as still in the close_lock window only
    # for the first 5 minutes after tip — anything past +5 min is
    # outside the slate window because the close has locked.
    if 0 <= delta_min < DEREK_CLOSE_LOCK_WINDOW[1] + 0.0001:
        out.mode = "close_lock"
        out.run_delivery = True
        return
    if -5 <= delta_min < 0:
        # We're 0→5 minutes past tip — still inside close_lock for the
        # purposes of writing the final pre-tip snapshot. Defensive only.
        out.mode = "close_lock"
        out.run_delivery = True
        return

    out.run_delivery = False
    out.valid_skip_reason = "outside_slate_delivery_window"
    out.mode = "derek_near_lineup"  # canonical placeholder mode


def _resolve_manual(args, now_utc: datetime) -> ResolverOutputs:
    """Resolve outputs for a ``workflow_dispatch`` event."""

    out = ResolverOutputs()
    today_et = _to_et_date(now_utc).isoformat()
    yesterday_et = _yesterday_et(now_utc).isoformat()

    stage = (args.manual_stage or "").strip().lower()
    mode = (args.manual_mode or "").strip().lower()
    delivery_date = (args.manual_delivery_date or "").strip()
    as_of_date = (args.manual_as_of_date or "").strip()
    force_run = _parse_bool_input(args.manual_force_run or "")
    no_promote = _parse_bool_input(getattr(args, "manual_no_promote", "") or "")

    out.delivery_date = delivery_date or today_et
    out.as_of_date = as_of_date or yesterday_et
    out.force_run = force_run

    if stage == "predict":
        out.stage = "predict"
        out.mode = mode or "predict"
        out.run_predict = True
        out.run_verifiers = True
        out.allow_promote = False
        return out

    if stage == "delivery":
        out.stage = "delivery"
        out.mode = mode or "derek_near_lineup"
        out.run_delivery = True
        out.run_verifiers = True
        out.allow_promote = False
        # Manual delivery never auto-gates on Derek tipoff window;
        # operator must opt-in to force_run for windows outside the
        # normal close_or_lock gate inside run_daily_delivery_pipeline.
        return out

    if stage == "after_game":
        out.stage = "after_game"
        out.mode = mode or "after_game"
        out.run_after_game = True
        out.run_verifiers = True
        out.allow_promote = False
        return out

    if stage in ("training", "model_chain"):
        out.stage = "model_chain"
        out.mode = mode or "model_chain"
        out.run_training = True
        out.run_phase8 = True
        out.run_phase13 = True
        out.run_verifiers = True
        # Promotion allowed only when the operator explicitly says so
        # (no_promote=false) AND stage is the promote variant.
        out.allow_promote = not no_promote
        return out

    if stage == "model_chain_no_promote":
        out.stage = "model_chain_no_promote"
        out.mode = mode or "model_chain_no_promote"
        out.run_training = True
        out.run_phase8 = True
        out.run_phase13 = True
        out.run_verifiers = True
        out.allow_promote = False
        return out

    if stage == "phase8":
        out.stage = "phase8"
        out.mode = mode or "phase8"
        out.run_phase8 = True
        out.run_verifiers = True
        out.allow_promote = False
        return out

    if stage == "phase13_context":
        out.stage = "phase13_context"
        out.mode = mode or "phase13_context"
        out.run_phase13 = True
        out.run_verifiers = True
        out.allow_promote = False
        return out

    if stage == "full_cycle":
        out.stage = "full_cycle"
        out.mode = mode or "full_cycle"
        out.run_training = True
        out.run_phase8 = True
        out.run_phase13 = True
        out.run_predict = True
        out.run_delivery = True
        out.run_after_game = False
        out.run_verifiers = True
        out.allow_promote = not no_promote
        return out

    if stage == "verifiers":
        out.stage = "verifiers"
        out.mode = mode or "verifiers"
        out.run_verifiers = True
        out.allow_promote = False
        return out

    if stage in ("", "auto"):
        # No explicit stage — default to delivery in the current mode if
        # operator gave one, otherwise valid-skip with explanation.
        if mode:
            out.stage = "delivery"
            out.mode = mode
            out.run_delivery = True
            out.run_verifiers = True
            return out
        out.stage = "auto"
        out.mode = "auto"
        out.valid_skip_reason = "manual_dispatch_without_stage_or_mode"
        return out

    out.stage = stage
    out.mode = mode or stage
    out.valid_skip_reason = f"unknown_manual_stage_{stage}"
    return out


def _resolve_workflow_run(args, now_utc: datetime) -> ResolverOutputs:
    """Resolve outputs for a ``workflow_run`` chained trigger.

    The brief's primary chained trigger is the WoO/Derek follow-on
    after the Daily Pipeline. Behave like the matching scheduled
    ``woo_morning_monetization`` delivery slot.
    """

    out = ResolverOutputs()
    today_et = _to_et_date(now_utc).isoformat()
    yesterday_et = _yesterday_et(now_utc).isoformat()
    out.delivery_date = today_et
    out.as_of_date = yesterday_et
    out.stage = "delivery"
    out.mode = "woo_morning_monetization"
    out.run_delivery = True
    out.run_verifiers = True
    out.allow_promote = False
    return out


# ── CLI entrypoint ──────────────────────────────────────────────────


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Resolve the NBA PMF Delivery consolidated workflow context "
            "(delivery_date, as_of_date, per-job gates, allow_promote, "
            "valid_skip_reason, etc.) from a single GitHub Actions event."
        )
    )
    p.add_argument("--event-name", default="", help="GitHub event name (schedule, workflow_dispatch, workflow_run, push, pull_request).")
    p.add_argument("--schedule", default="", help="Cron string for scheduled runs (e.g. '0 14 * * *').")
    p.add_argument("--manual-stage", default="", help="workflow_dispatch input: stage (predict, delivery, after_game, training, model_chain, model_chain_no_promote, phase8, phase13_context, full_cycle, verifiers, auto).")
    p.add_argument("--manual-mode", default="", help="workflow_dispatch input: delivery mode (e.g. derek_near_lineup, close_lock, woo_morning_monetization, woo_afternoon_refresh, after_game, predict).")
    p.add_argument("--manual-delivery-date", default="", help="workflow_dispatch input: delivery_date YYYY-MM-DD (blank = today ET).")
    p.add_argument("--manual-as-of-date", default="", help="workflow_dispatch input: as_of_date YYYY-MM-DD (blank = yesterday ET).")
    p.add_argument("--manual-force-run", default="false", help="workflow_dispatch input: force_run ('true'/'false'). Bypasses delivery time-window gates.")
    p.add_argument("--manual-no-promote", default="true", help="workflow_dispatch input: no_promote ('true'/'false'). Defaults to 'true' for manual safety.")
    p.add_argument("--github-output", default="", help="Path to GITHUB_OUTPUT file. If blank, only stdout summary is printed.")
    p.add_argument("--now-utc", default="", help="Override the current UTC time (ISO-8601). Test-only.")
    return p.parse_args(argv)


def resolve(args: argparse.Namespace) -> ResolverOutputs:
    """Pure-function dispatcher used by tests."""

    now_utc = _parse_now_utc(args.now_utc or None)
    event = (args.event_name or "").strip().lower()
    if event == "schedule":
        return _resolve_scheduled(args, now_utc)
    if event == "workflow_dispatch":
        return _resolve_manual(args, now_utc)
    if event == "workflow_run":
        return _resolve_workflow_run(args, now_utc)

    # Default: unknown event → valid_skip with diagnostic reason but
    # populate stable defaults so downstream YAML conditionals don't
    # blow up on empty strings.
    out = ResolverOutputs()
    out.delivery_date = _to_et_date(now_utc).isoformat()
    out.as_of_date = _yesterday_et(now_utc).isoformat()
    out.valid_skip_reason = f"unknown_event_{event or 'empty'}"
    return out


def _dbg(message: str, data: dict) -> None:
    """Append one NDJSON line to the session debug log (silent on failure)."""
    import json as _json
    import time as _time
    _log_path = REPO_ROOT / ".cursor" / "debug-cd71ad.log"
    try:
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"sessionId": "cd71ad", "location": "resolve_nba_pmf_schedule.py",
                 "message": message, "data": data, "timestamp": int(_time.time() * 1000)}
        with open(_log_path, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps(entry) + "\n")
    except Exception:
        pass


def emit(outputs: ResolverOutputs, github_output_path: str) -> None:
    """Write outputs to ``$GITHUB_OUTPUT`` and print the summary line."""

    # #region agent log H1
    _dbg("emit: final resolved outputs", {
        "hypothesisId": "H1",
        "stage": outputs.stage,
        "mode": outputs.mode,
        "allow_promote": outputs.allow_promote,
        "run_training": outputs.run_training,
        "run_phase8": outputs.run_phase8,
        "run_phase13": outputs.run_phase13,
        "as_of_date": outputs.as_of_date,
        "delivery_date": outputs.delivery_date,
        "valid_skip_reason": outputs.valid_skip_reason,
    })
    # #endregion

    payload = outputs.as_output_dict()
    if github_output_path:
        p = Path(github_output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            for k, v in payload.items():
                # GITHUB_OUTPUT does not allow embedded newlines in
                # single-line values; everything we emit is short.
                v = (v or "").replace("\n", " ").strip()
                f.write(f"{k}={v}\n")

    summary = " ".join(f"{k}={payload[k]}" for k in payload)
    notes = ""
    if outputs.notes:
        notes = " " + " ".join(f"note={n}" for n in outputs.notes)
    print(f"NBA_PMF_SCHEDULE_RESOLVED {summary}{notes}")


LOUD_FAILURE_TIP_TIME_WITH_SLATE = "tip_time_unresolved_but_slate_exists"


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    outputs = resolve(args)
    emit(outputs, args.github_output)
    if outputs.valid_skip_reason == LOUD_FAILURE_TIP_TIME_WITH_SLATE:
        # Loud, non-zero exit so the resolve_context workflow step
        # turns the run RED instead of silently green-skipping a slate.
        # See diagnosis: a slate clearly exists on disk for this
        # delivery_date but no tip-time source was available, so the
        # honest outcome is to fail the run rather than fabricate a tip
        # or pretend no slate existed.
        print(
            "SCHEDULER_TIP_TIME_UNRESOLVABLE_WITH_SLATE "
            f"delivery_date={outputs.delivery_date} "
            f"as_of_date={outputs.as_of_date} "
            f"stage={outputs.stage} mode={outputs.mode}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
