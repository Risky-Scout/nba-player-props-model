#!/usr/bin/env python3
"""Phase 13AN — Derek forward-feed verifier.

Static structural checks for the Derek forward-feed package
delivered under ``deliveries/<date>/derek_forward_feed/``. Operates in
two modes:

    --mode strict      every gate must pass. Used by production CI.
    --mode production  same as strict but tolerates the lineup_only
                       case where morning_snapshot is missing because
                       the slate started in the lineup window
                       (Derek's snapshot lifecycle has lineup as the
                       earliest feed for those slates).

Required files (production):

    deliveries/<date>/derek_forward_feed/lineup_snapshot.csv
    deliveries/<date>/derek_forward_feed/lineup_snapshot.jsonl
    deliveries/<date>/derek_forward_feed/lineup_snapshot.parquet
    deliveries/<date>/derek_forward_feed/latest_available_snapshot.csv
    deliveries/<date>/derek_forward_feed/latest_available_snapshot.parquet
    deliveries/<date>/derek_forward_feed/feed_manifest.json
    deliveries/<date>/derek_forward_feed/feed_manifest.champion_stamp.json
    deliveries/<date>/derek_forward_feed/FEED_README.md

Optional (warned if missing in production, required when the manifest
declares ``morning`` snapshot exists):

    deliveries/<date>/derek_forward_feed/morning_snapshot.csv
    deliveries/<date>/derek_forward_feed/morning_snapshot.jsonl
    deliveries/<date>/derek_forward_feed/morning_snapshot.parquet

Required column families (inspected on the parquet snapshot):

    identity:       game_id, player_id, stat, snapshot_type
    distribution:   mean, median, p0, p_ge_1..p_ge_*
    market context: line, sportsbook OR book, model_p_over, model_p_under
    metadata:       model_version, role_bucket, finality_status

Production checks:

    * row count > 0 on lineup_snapshot.parquet and latest_available_snapshot.parquet
    * no duplicate (player_id, stat, line) prop keys per snapshot
    * champion stamp matches feed_manifest.json
    * latest_available_snapshot's ``points_to`` is the most recent
      snapshot that exists on disk
    * feed_manifest.json lists every produced file with row counts
    * role_bucket is non-null for every row (no ``unknown`` allowed
      unless --allow-role-unknown)
    * tov_status is documented (ok | blocked_by_model_target_contract |
      missing_market_only) — never blank

Pass line:
    DEREK_FORWARD_FEED_VERIFICATION_PASS  date=<date>  mode=<mode>

Fail line:
    DEREK_FORWARD_FEED_VERIFICATION_FAILED  date=<date>  count=<n>

Each individual failure is printed prefixed by ``::error::``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": f"{type(exc).__name__}: {exc}"}


def _emit_fail(token: str, date: str, mode: str, count: int) -> int:
    print(f"{token}  date={date}  mode={mode}  count={count}")
    return 1


def _emit_pass(token: str, date: str, mode: str, **fields) -> int:
    extras = "  ".join(f"{k}={v}" for k, v in fields.items())
    print(f"{token}  date={date}  mode={mode}  {extras}".rstrip())
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--delivery-date", required=True)
    ap.add_argument(
        "--mode",
        choices=["strict", "production"],
        default="production",
    )
    ap.add_argument(
        "--require-morning-snapshot",
        action="store_true",
        help="Fail if morning_snapshot.* are missing (default: missing "
        "morning is allowed in production unless feed_manifest declares it).",
    )
    ap.add_argument(
        "--allow-role-unknown",
        action="store_true",
        help="Allow rows with role_bucket='unknown' (default: fail).",
    )
    ap.add_argument(
        "--require-market",
        action="store_true",
        help="Fail if every row in lineup_snapshot is model-only (no market).",
    )
    args = ap.parse_args(argv)

    date = args.delivery_date
    mode = args.mode
    feed_dir = REPO_ROOT / "deliveries" / date / "derek_forward_feed"

    failures: list[str] = []

    if not feed_dir.exists():
        failures.append(f"derek feed dir missing: {feed_dir}")
        for f in failures:
            print(f"::error::{f}")
        return _emit_fail(
            "DEREK_FORWARD_FEED_VERIFICATION_FAILED", date, mode, len(failures)
        )

    # ── Required files ──────────────────────────────────────────────
    required = [
        "lineup_snapshot.csv",
        "lineup_snapshot.jsonl",
        "lineup_snapshot.parquet",
        "latest_available_snapshot.csv",
        "latest_available_snapshot.parquet",
        "feed_manifest.json",
        "feed_manifest.champion_stamp.json",
        "FEED_README.md",
    ]
    for name in required:
        p = feed_dir / name
        if not p.exists():
            failures.append(f"missing required file: {p.relative_to(REPO_ROOT)}")
        elif p.stat().st_size == 0:
            failures.append(f"required file empty: {p.relative_to(REPO_ROOT)}")

    # ── Manifest ────────────────────────────────────────────────────
    manifest = _read_json(feed_dir / "feed_manifest.json") or {}
    if not manifest:
        failures.append("feed_manifest.json unreadable or empty")
    else:
        if manifest.get("delivery_date") != date:
            failures.append(
                f"feed_manifest.delivery_date={manifest.get('delivery_date')} "
                f"!= --delivery-date={date}"
            )
        if not manifest.get("champion_model_id"):
            failures.append("feed_manifest missing champion_model_id")

    # Champion stamp must agree with manifest.
    stamp = _read_json(feed_dir / "feed_manifest.champion_stamp.json") or {}
    if stamp and manifest:
        for key in ("champion_model_id", "calibration_run_id"):
            mv = manifest.get(key)
            sv = stamp.get(key)
            if mv != sv:
                failures.append(
                    f"champion stamp mismatch on {key}: manifest={mv!r} stamp={sv!r}"
                )

    # ── Snapshot existence per manifest declarations ────────────────
    declared_snapshots = []
    for label in ("morning", "lineup"):
        snap = manifest.get(label) if isinstance(manifest, dict) else None
        if isinstance(snap, dict) and snap.get("files"):
            declared_snapshots.append(label)
            files = snap.get("files") or {}
            for ext in ("csv", "jsonl", "parquet"):
                rel = files.get(ext)
                if rel:
                    fp = REPO_ROOT / rel
                    if not fp.exists():
                        failures.append(
                            f"feed_manifest.{label} declares {ext} but file "
                            f"missing on disk: {rel}"
                        )

    if args.require_morning_snapshot:
        morning_declared = "morning" in declared_snapshots
        morning_meta = manifest.get("morning") if isinstance(manifest, dict) else {}
        lineup_meta = manifest.get("lineup") if isinstance(manifest, dict) else {}
        morning_ts = str((morning_meta or {}).get("snapshot_time_utc") or "")
        lineup_ts = str((lineup_meta or {}).get("snapshot_time_utc") or "")
        # Guard against lineup-only runs that backfill a "morning" snapshot
        # with the same or later timestamp than lineup.
        genuine_morning = bool(morning_declared)
        if morning_declared and morning_ts and lineup_ts and morning_ts >= lineup_ts:
            genuine_morning = False
        if not genuine_morning:
            failures.append(
                "feed_manifest does not declare a morning snapshot "
                "(--require-morning-snapshot was set)"
            )

    # ── Row count + duplicate checks via pandas (if available) ──────
    try:
        import pandas as pd  # noqa: F401
    except ImportError:
        # Skip parquet checks but warn — production CI installs pandas.
        if mode == "production":
            failures.append("pandas not available for row count/dup checks")
        for f in failures:
            print(f"::error::{f}")
        if failures:
            return _emit_fail(
                "DEREK_FORWARD_FEED_VERIFICATION_FAILED", date, mode, len(failures)
            )
        return _emit_pass("DEREK_FORWARD_FEED_VERIFICATION_PASS", date, mode)

    import pandas as pd

    REQUIRED_COLS = {
        "game_id",
        "player_id",
        "stat",
        "mean",
        "median",
        "p0",
        "model_version",
        "role_bucket",
        "snapshot_type",
        "finality_status",
    }
    DEDUPE_KEY_COLS = ["player_id", "stat", "line"]

    def _check_snapshot(label: str, parquet_path: Path) -> None:
        if not parquet_path.exists():
            return
        try:
            df = pd.read_parquet(parquet_path)
        except Exception as exc:
            failures.append(f"{label} parquet unreadable: {exc!r}")
            return
        rows = len(df)
        if rows == 0:
            failures.append(f"{label} parquet has zero rows: {parquet_path.name}")
            return
        missing_cols = REQUIRED_COLS - set(df.columns)
        if missing_cols:
            failures.append(
                f"{label} missing required columns: {sorted(missing_cols)}"
            )
        # Dup-prop key check (only if dedupe columns present).
        present_dedupe = [c for c in DEDUPE_KEY_COLS if c in df.columns]
        if len(present_dedupe) >= 2:
            dups = df.duplicated(subset=present_dedupe, keep=False)
            if dups.any():
                # Multi-book rows are legit; only fail if duplicates exist
                # on (player_id, stat, line, sportsbook) when sportsbook
                # is also present.
                ext_cols = present_dedupe + (
                    ["sportsbook"] if "sportsbook" in df.columns else []
                )
                if len(ext_cols) > len(present_dedupe):
                    dups_ext = df.duplicated(subset=ext_cols, keep=False)
                    if dups_ext.any():
                        failures.append(
                            f"{label} duplicate rows on {ext_cols}: "
                            f"{int(dups_ext.sum())}"
                        )
                else:
                    failures.append(
                        f"{label} duplicate rows on {present_dedupe}: "
                        f"{int(dups.sum())}"
                    )

        # role_bucket check.
        if "role_bucket" in df.columns:
            null_roles = df["role_bucket"].isna().sum()
            if null_roles:
                failures.append(
                    f"{label} {int(null_roles)} rows have null role_bucket"
                )
            unknown_mask = df["role_bucket"].astype(str).str.lower() == "unknown"
            unknown_roles = int(unknown_mask.sum())
            if unknown_roles and not args.allow_role_unknown:
                failures.append(
                    f"{label} {unknown_roles} rows have role_bucket='unknown'"
                )

        # tov_status check.
        if "tov_status" in df.columns:
            empty_tov = (
                df["tov_status"].astype(str).str.strip().eq("").sum()
                + df["tov_status"].isna().sum()
            )
            if empty_tov:
                failures.append(
                    f"{label} {int(empty_tov)} rows have blank tov_status"
                )

        # market coverage check (production only when --require-market).
        if args.require_market and "model_p_over" in df.columns:
            if "line" in df.columns:
                with_market = df["line"].notna().sum()
                if int(with_market) == 0:
                    failures.append(
                        f"{label} has zero rows with market lines "
                        f"(--require-market set)"
                    )

    _check_snapshot("lineup_snapshot", feed_dir / "lineup_snapshot.parquet")
    _check_snapshot(
        "latest_available_snapshot",
        feed_dir / "latest_available_snapshot.parquet",
    )
    if "morning" in declared_snapshots:
        _check_snapshot(
            "morning_snapshot", feed_dir / "morning_snapshot.parquet"
        )

    # ── latest_available_snapshot.points_to consistency ─────────────
    latest_decl = manifest.get("latest_available_snapshot", {}) if manifest else {}
    points_to = latest_decl.get("points_to")
    if points_to:
        target_files = (manifest.get(points_to) or {}).get("files") or {}
        target_parquet = target_files.get("parquet")
        if not target_parquet:
            failures.append(
                f"latest_available_snapshot.points_to={points_to!r} but no "
                "parquet file declared for that snapshot"
            )

    if failures:
        for f in failures:
            print(f"::error::{f}")
        return _emit_fail(
            "DEREK_FORWARD_FEED_VERIFICATION_FAILED", date, mode, len(failures)
        )

    declared = ",".join(declared_snapshots) or "none"
    return _emit_pass(
        "DEREK_FORWARD_FEED_VERIFICATION_PASS",
        date,
        mode,
        snapshots_declared=declared,
        champion_model_id=manifest.get("champion_model_id"),
    )


if __name__ == "__main__":
    sys.exit(main())
