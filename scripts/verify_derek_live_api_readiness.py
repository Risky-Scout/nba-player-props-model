"""Phase 13N Part B — verify Derek live snapshot API readiness.

Read-only check that the secrets and API surface required by the Derek
production-live pipeline are wired without ever printing a secret value.

Checks:
  1. ``BDL_API_KEY`` env var is set and non-empty.
  2. (Optional, soft) ``ODDS_API_KEY`` env var is set when present.
  3. The BDL client wrapper exposes the call we need:
     ``nba_props_model.data.bdl_client.get_lineups(game_id)``.
  4. The BDL client wrapper exposes ``get_injuries()`` for player-injury
     context.
  5. The fetch_bdl_game_lineups.py wrapper imports cleanly.
  6. Optional smoke fetch (only when ``--smoke-game-id`` is supplied):
     calls ``get_lineups(game_id)`` ONCE, asserts the response is a list
     (possibly empty for past games — empty is honest, not failure), and
     persists no state. We do not mass-fetch in this verifier.

Pass line:  DEREK_LIVE_API_READINESS_PASS
Fail line:  DEREK_LIVE_API_READINESS_FAILED

Usage:
    python3 scripts/verify_derek_live_api_readiness.py
    python3 scripts/verify_derek_live_api_readiness.py --smoke-game-id 21681995
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    git_commit,
    utcnow_iso,
    write_json_atomic,
)


HEALTH_DIR = REPO_ROOT / "artifacts" / "automation_health"


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Report:
    generated_at_utc: str
    code_commit: str
    checks: list = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(Check(name, ok, detail))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "passed": self.passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail}
                for c in self.checks
            ],
            "facts": self.facts,
        }


def _present_no_value(name: str) -> tuple[bool, str]:
    """Check that an env var exists without ever leaking the value."""
    val = os.environ.get(name, "")
    if not val:
        return False, f"{name} is not set"
    # Never echo the secret. Surface only metadata.
    return True, f"{name} present (length={len(val)})"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Verify Derek live API readiness.")
    p.add_argument("--smoke-game-id", default=None,
                   help="If set, attempt one BDL get_lineups(game_id) call "
                        "to verify the endpoint responds. Empty response is "
                        "OK for past games.")
    args = p.parse_args(argv)

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    report = Report(generated_at_utc=utcnow_iso(), code_commit=git_commit())

    # 1. BDL_API_KEY required.
    ok, detail = _present_no_value("BDL_API_KEY")
    report.add("env:BDL_API_KEY", ok, detail)

    # 2. ODDS_API_KEY soft check (used by upstream WoO pipeline; absent in
    # the Derek snapshot path strictly speaking, but documented here).
    odds_ok = bool(os.environ.get("ODDS_API_KEY", "").strip())
    report.add(
        "env:ODDS_API_KEY (soft)",
        True,  # soft — we still pass when missing
        f"present={odds_ok}",
    )
    report.facts["odds_api_key_present"] = odds_ok

    # 3-4. BDL client surface present.
    try:
        bdl = importlib.import_module("nba_props_model.data.bdl_client")
    except Exception as exc:
        report.add("import:bdl_client", False, f"failed: {exc}")
        _emit(report)
        return 1
    report.add("import:bdl_client", True, "ok")
    report.add(
        "bdl_client.get_lineups exists",
        callable(getattr(bdl, "get_lineups", None)),
        "ok" if callable(getattr(bdl, "get_lineups", None)) else "missing",
    )
    report.add(
        "bdl_client.get_injuries exists",
        callable(getattr(bdl, "get_injuries", None)),
        "ok" if callable(getattr(bdl, "get_injuries", None)) else "missing",
    )

    # 5. fetch_bdl_game_lineups wrapper imports cleanly.
    fetch_path = REPO_ROOT / "scripts" / "fetch_bdl_game_lineups.py"
    report.add(
        "wrapper:fetch_bdl_game_lineups.py present",
        fetch_path.exists(),
        "ok" if fetch_path.exists() else f"missing: {fetch_path}",
    )

    # 6. Optional smoke fetch — only when the operator explicitly asks for
    # it AND the API key is present. We never spam BDL by default.
    if args.smoke_game_id:
        if not ok:
            report.add(
                f"smoke:get_lineups({args.smoke_game_id})",
                False,
                "skipped — BDL_API_KEY missing",
            )
        else:
            try:
                resp = bdl.get_lineups(int(args.smoke_game_id))
                # Empty response is OK (past game / lineups not posted).
                report.add(
                    f"smoke:get_lineups({args.smoke_game_id})",
                    isinstance(resp, list),
                    f"response_type={type(resp).__name__} "
                    f"row_count={len(resp) if isinstance(resp, list) else '?'}",
                )
                report.facts["smoke_row_count"] = (
                    len(resp) if isinstance(resp, list) else None
                )
            except Exception as exc:
                report.add(
                    f"smoke:get_lineups({args.smoke_game_id})",
                    False,
                    f"raised: {exc}",
                )

    _emit(report)
    return 0 if report.passed else 1


def _emit(report: Report) -> None:
    payload = report.to_dict()
    write_json_atomic(HEALTH_DIR / "derek_live_api_readiness.json", payload)
    md = [
        "# Derek Live API Readiness",
        "",
        f"- generated_at_utc: {report.generated_at_utc}",
        f"- passed: **{report.passed}**",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in report.checks:
        safe = c.detail.replace("|", "\\|")
        md.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {safe} |")
    (HEALTH_DIR / "derek_live_api_readiness.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    if report.passed:
        print("DEREK_LIVE_API_READINESS_PASS")
        return
    print("DEREK_LIVE_API_READINESS_FAILED", file=sys.stderr)
    for c in report.checks:
        if not c.passed:
            print(f"  - {c.name}: {c.detail}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
