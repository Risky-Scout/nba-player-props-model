"""Phase 13A — daily training readiness checker.

Verifies that the data needed for nightly training/calibration is present,
honest, and final enough to use, before any challenger run is started. If the
checks fail, the orchestrator must keep the champion unchanged and exit safely.

Usage:
    python3 scripts/check_daily_training_readiness.py --date YYYY-MM-DD
    python3 scripts/check_daily_training_readiness.py --from-date YYYY-MM-DD --to-date YYYY-MM-DD

Outputs:
    artifacts/training_readiness/<date>/readiness_report.json
    artifacts/training_readiness/<date>/readiness_summary.md

Hard rules:
- Never fabricates outcomes / odds / lineups / player stats.
- Never reads or stages secrets or raw API blobs.
- Never references Phase 10D / 10D.2 overlays.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    SUPPORTED_STATS,
    git_commit,
    md_table,
    parse_date,
    readiness_dir,
    utcnow_iso,
    write_json_atomic,
)

DATA_DIR = REPO_ROOT / "data"
PLAYER_GAME_STATS_PARQUET = DATA_DIR / "player_game_stats.parquet"
ODDS_API_PROCESSED = DATA_DIR / "odds_api" / "processed"
FRESHNESS_MANIFEST_DIR = DATA_DIR / "freshness_manifest"

# Minimum samples for honest training/calibration. These are conservative
# floors; real promotion gates live in scripts/validate_champion_vs_challenger.py.
MIN_TRAINING_ROWS = 5_000
MIN_PER_STAT_ROWS = 1_000


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    severity: str = "blocking"  # "blocking" or "advisory"


@dataclass
class ReadinessReport:
    as_of_date: str
    generated_at_utc: str
    code_commit: str
    checks: list[CheckResult] = field(default_factory=list)
    counts: dict = field(default_factory=dict)

    def overall_pass(self) -> bool:
        return all(c.passed for c in self.checks if c.severity == "blocking")

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "as_of_date": self.as_of_date,
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "overall_pass": self.overall_pass(),
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "detail": c.detail,
                    "severity": c.severity,
                }
                for c in self.checks
            ],
            "counts": self.counts,
        }


def _load_player_game_stats():
    try:
        import pandas as pd
    except ImportError:
        return None, "pandas not installed"
    if not PLAYER_GAME_STATS_PARQUET.exists():
        return None, f"missing {PLAYER_GAME_STATS_PARQUET.relative_to(REPO_ROOT)}"
    try:
        df = pd.read_parquet(PLAYER_GAME_STATS_PARQUET)
    except Exception as exc:  # pragma: no cover - depends on local file
        return None, f"failed to read parquet: {exc}"
    return df, ""


def _detect_date_column(df) -> str | None:
    candidates = ("game_date", "date", "GAME_DATE", "Date")
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _detect_stat_columns(df, stats: Iterable[str]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    cols_lower = {c.lower(): c for c in df.columns}
    for s in stats:
        # Try exact, lowercase, and common variants.
        for cand in (s, s.lower(), s.upper(), {"fg3m": "fg3", "tov": "to"}.get(s, "")):
            if not cand:
                continue
            if cand in df.columns:
                out[s] = cand
                break
            if cand.lower() in cols_lower:
                out[s] = cols_lower[cand.lower()]
                break
        else:
            out[s] = None
    return out


def check_outcomes(report: ReadinessReport, as_of: dt.date) -> None:
    df, err = _load_player_game_stats()
    if err:
        report.checks.append(
            CheckResult(
                name="outcomes_present",
                passed=False,
                detail=err,
                severity="blocking",
            )
        )
        return
    date_col = _detect_date_column(df)
    if date_col is None:
        report.checks.append(
            CheckResult(
                name="outcomes_present",
                passed=False,
                detail="no recognizable date column in player_game_stats.parquet",
                severity="blocking",
            )
        )
        return

    import pandas as pd  # noqa: F401  (guaranteed by _load_player_game_stats)

    # Coerce dates.
    try:
        ds = pd.to_datetime(df[date_col]).dt.date
    except Exception as exc:
        report.checks.append(
            CheckResult(
                name="outcomes_present",
                passed=False,
                detail=f"could not coerce {date_col} to dates: {exc}",
                severity="blocking",
            )
        )
        return

    n_total = int(len(df))
    n_through = int((ds <= as_of).sum())
    n_future = int((ds > as_of).sum())
    n_on_date = int((ds == as_of).sum())
    report.counts["player_game_stats_total_rows"] = n_total
    report.counts["player_game_stats_rows_through_as_of"] = n_through
    report.counts["player_game_stats_rows_on_as_of_date"] = n_on_date
    report.counts["player_game_stats_rows_after_as_of"] = n_future

    report.checks.append(
        CheckResult(
            name="outcomes_through_as_of_date",
            passed=n_through > 0,
            detail=f"rows through {as_of}: {n_through}",
            severity="blocking",
        )
    )
    # Future-leak guard: rows with a date > as_of are allowed (later games may
    # exist), but they must NOT be used for training. Training scripts enforce
    # the cutoff; readiness only flags it.
    report.checks.append(
        CheckResult(
            name="future_dates_present_advisory",
            passed=True,
            detail=f"{n_future} rows have date > {as_of}; trainer must filter them out",
            severity="advisory",
        )
    )

    stat_cols = _detect_stat_columns(df, SUPPORTED_STATS)
    found = {s: c for s, c in stat_cols.items() if c}
    missing = [s for s, c in stat_cols.items() if not c]
    report.counts["stat_columns_present"] = found
    report.checks.append(
        CheckResult(
            name="required_stat_columns_present",
            passed=len(found) >= 5,  # core five must be present; stl/blk advisory
            detail=f"present={sorted(found)} missing={sorted(missing)}",
            severity="blocking" if len(found) < 5 else "advisory",
        )
    )

    # Per-stat row count + impossible-value check on rows through as_of.
    df_train = df[ds <= as_of]
    per_stat_counts: dict[str, int] = {}
    impossible: list[str] = []
    for stat, col in stat_cols.items():
        if not col:
            continue
        s = df_train[col]
        finite = s.notna()
        per_stat_counts[stat] = int(finite.sum())
        # All seven supported stats are non-negative integers in NBA box scores.
        bad = ((s < 0) | (s > 200)).fillna(False)
        if bool(bad.any()):
            impossible.append(f"{stat}: {int(bad.sum())} impossible values")
    report.counts["per_stat_rows_through_as_of"] = per_stat_counts
    report.checks.append(
        CheckResult(
            name="no_impossible_stat_values",
            passed=not impossible,
            detail="; ".join(impossible) if impossible else "ok",
            severity="blocking",
        )
    )

    # Min sample threshold.
    enough_total = n_through >= MIN_TRAINING_ROWS
    report.checks.append(
        CheckResult(
            name="min_training_rows",
            passed=enough_total,
            detail=f"{n_through} >= {MIN_TRAINING_ROWS}",
            severity="blocking",
        )
    )
    enough_per_stat = [s for s, n in per_stat_counts.items() if n >= MIN_PER_STAT_ROWS]
    thin_per_stat = [s for s, n in per_stat_counts.items() if n < MIN_PER_STAT_ROWS]
    report.checks.append(
        CheckResult(
            name="min_per_stat_rows",
            passed=len(enough_per_stat) >= 5,
            detail=f"enough={enough_per_stat} thin={thin_per_stat}",
            severity="blocking" if len(enough_per_stat) < 5 else "advisory",
        )
    )

    # Duplicate game/player rows on the as_of date (advisory; many BDL tables
    # have player+game uniqueness implicitly).
    if "player_id" in df.columns and date_col:
        on_date = df_train[ds == as_of] if n_on_date > 0 else df_train.iloc[0:0]
        if "game_id" in on_date.columns and not on_date.empty:
            dup = on_date.duplicated(subset=["player_id", "game_id"]).sum()
            report.checks.append(
                CheckResult(
                    name="no_duplicate_player_game_rows_on_date",
                    passed=int(dup) == 0,
                    detail=f"{int(dup)} duplicates on {as_of}",
                    severity="blocking",
                )
            )


def check_odds_snapshots(report: ReadinessReport, as_of: dt.date) -> None:
    if not ODDS_API_PROCESSED.exists():
        report.checks.append(
            CheckResult(
                name="odds_snapshots_present",
                passed=False,
                detail=(
                    f"{ODDS_API_PROCESSED.relative_to(REPO_ROOT)} missing — "
                    "market comparison will be skipped (advisory only)"
                ),
                severity="advisory",
            )
        )
        return
    iso = as_of.isoformat()
    day_dir = ODDS_API_PROCESSED / iso
    parquets: list[Path] = []
    if day_dir.exists():
        parquets = sorted(day_dir.glob("*.parquet"))
    report.counts["odds_snapshot_files_on_date"] = len(parquets)
    report.checks.append(
        CheckResult(
            name="odds_snapshots_for_date",
            passed=len(parquets) > 0,
            detail=f"{len(parquets)} parquet snapshot(s) for {iso}",
            severity="advisory",
        )
    )


def check_freshness_manifest(report: ReadinessReport, as_of: dt.date) -> None:
    if not FRESHNESS_MANIFEST_DIR.exists():
        report.checks.append(
            CheckResult(
                name="freshness_manifest_present",
                passed=False,
                detail="data/freshness_manifest/ missing (advisory)",
                severity="advisory",
            )
        )
        return
    candidate = FRESHNESS_MANIFEST_DIR / f"{as_of.isoformat()}.json"
    report.checks.append(
        CheckResult(
            name="freshness_manifest_for_date",
            passed=candidate.exists(),
            detail=("present" if candidate.exists() else "missing"),
            severity="advisory",
        )
    )


def check_no_active_delivery(report: ReadinessReport) -> None:
    """Best-effort check that no delivery job is currently running.

    We only have local signals here: the promotion lockfile, and the absence of
    the delivery in-progress markers (none currently exist). The real isolation
    comes from the cron schedule (training at 09:30 UTC, deliveries at 15:00+).
    """
    from nba_props_model.training_automation import PROMOTION_LOCK_PATH

    locked = PROMOTION_LOCK_PATH.exists()
    report.checks.append(
        CheckResult(
            name="no_promotion_lock_held",
            passed=not locked,
            detail=("lock file present" if locked else "ok"),
            severity="blocking",
        )
    )


def write_summary(out_dir: Path, report: ReadinessReport) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    blocking_failed = [c for c in report.checks if c.severity == "blocking" and not c.passed]
    advisory_failed = [c for c in report.checks if c.severity == "advisory" and not c.passed]

    lines = [
        f"# Daily Training Readiness — {report.as_of_date}",
        "",
        md_table(
            [
                ("Generated (UTC)", report.generated_at_utc),
                ("Code commit", report.code_commit[:12]),
                ("Overall pass", "yes" if report.overall_pass() else "no"),
                ("Blocking failed", str(len(blocking_failed))),
                ("Advisory failed", str(len(advisory_failed))),
            ]
        ),
        "",
        "## Checks",
        "",
        "| Check | Severity | Pass | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for c in report.checks:
        safe_detail = c.detail.replace("|", "\\|")
        lines.append(
            f"| {c.name} | {c.severity} | {'yes' if c.passed else 'NO'} | {safe_detail} |"
        )
    if report.counts:
        lines += ["", "## Counts", "", "```", json.dumps(report.counts, indent=2), "```"]

    (out_dir / "readiness_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_for_date(as_of: dt.date) -> ReadinessReport:
    report = ReadinessReport(
        as_of_date=as_of.isoformat(),
        generated_at_utc=utcnow_iso(),
        code_commit=git_commit(),
    )
    check_outcomes(report, as_of)
    check_odds_snapshots(report, as_of)
    check_freshness_manifest(report, as_of)
    check_no_active_delivery(report)
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Daily training readiness checker.")
    p.add_argument("--date", help="Single as-of date YYYY-MM-DD")
    p.add_argument("--from-date", help="Inclusive start of date range")
    p.add_argument("--to-date", help="Inclusive end of date range")
    args = p.parse_args(argv)

    if args.date and (args.from_date or args.to_date):
        p.error("--date is mutually exclusive with --from-date/--to-date")

    if args.date:
        dates = [parse_date(args.date)]
    elif args.from_date and args.to_date:
        a = parse_date(args.from_date)
        b = parse_date(args.to_date)
        if a > b:
            p.error("--from-date must be <= --to-date")
        dates = [a + dt.timedelta(days=i) for i in range((b - a).days + 1)]
    else:
        p.error("provide --date or --from-date and --to-date")
        return 2  # unreachable

    overall_ok = True
    for d in dates:
        report = run_for_date(d)
        out_dir = readiness_dir(d.isoformat())
        write_json_atomic(out_dir / "readiness_report.json", report.to_dict())
        write_summary(out_dir, report)
        ok = report.overall_pass()
        overall_ok = overall_ok and ok
        print(
            json.dumps(
                {
                    "date": d.isoformat(),
                    "overall_pass": ok,
                    "blocking_failed": [
                        c.name for c in report.checks if c.severity == "blocking" and not c.passed
                    ],
                }
            )
        )

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
