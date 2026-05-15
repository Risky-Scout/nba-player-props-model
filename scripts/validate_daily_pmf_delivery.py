#!/usr/bin/env python3
"""Daily PMF delivery validation gate (M8.9 root-cause rewire).

Runs end-to-end checks across every artifact the public delivery
publishes, writes ``deliveries/{date}/manifest.json`` with an authoritative
``status`` field, and exits non-zero if any of the 14 documented fail
conditions is hit.

Status values written to the manifest:

    passed              every validation passed
    failed              at least one fail condition tripped
    source_unavailable  required source artifact missing
    empty_slate         no games scheduled for this date

This is the gate Derek/WoO publishing should consult; only
``passed`` deliveries are safe to ship.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.pipelines.player_game_eligibility import (  # noqa: E402
    REQUIRED_MINUTES_COLUMNS,
)
from nba_props_model.data.nba_official_injury_report_fetch import (  # noqa: E402
    merge_manifest_injury_fields,
)


REQUIRED_CANONICAL_COLUMNS = [
    "slate_date",
    "minutes_mean",
    "minutes_p10",
    "minutes_p50",
    "minutes_p90",
    "minutes_std",
    "p_inactive_used",
    "rotation_probability",
    "starter_probability",
    "projected_role",
    "player_game_eligible",
    "eligibility_reason",
    "has_current_market_line",
]


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _path(rel: str) -> Path:
    return REPO_ROOT / rel


def _safe_read(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        if path.suffix == ".parquet":
            return pd.read_parquet(path)
        if path.suffix == ".csv":
            return pd.read_csv(path)
    except Exception as exc:
        print(f"  warn: could not read {path}: {exc}")
        return None
    return None


def _add_failure(failures: list[dict], code: str, detail: str) -> None:
    failures.append({"code": code, "detail": detail})
    print(f"  FAIL [{code}]: {detail}")


def _is_role_bucket_missing(df: pd.DataFrame) -> bool:
    if "role_bucket" not in df.columns:
        return True
    bad = df["role_bucket"].isna() | df["role_bucket"].astype(str).str.lower().isin(
        ["", "none", "nan", "unknown"]
    )
    return bool(bad.any())


def _check_deep_bench(df: pd.DataFrame) -> int:
    needed = ["has_current_market_line", "minutes_mean", "rotation_probability", "starter_probability"]
    if not all(c in df.columns for c in needed):
        return -1
    mask = (
        ~df["has_current_market_line"].fillna(False).astype(bool)
        & (df["minutes_mean"].astype(float) < 12.0)
        & (df["rotation_probability"].astype(float) < 0.50)
        & (df["starter_probability"].astype(float) < 0.50)
    )
    return int(mask.sum())


def _check_universe_contract(
    df: pd.DataFrame, *, label: str, failures: list[dict]
) -> None:
    """Universe-artifact gate: schema + uniqueness + non-null minutes/role
    quantiles + probability/minute ranges. NO deep-bench gate. The
    universe artifact (``minutes_predictions.parquet``) is allowed to
    contain deep-bench rows by design — the eligible view filters them
    out for publication.
    """
    missing_min_cols = [c for c in REQUIRED_MINUTES_COLUMNS if c not in df.columns]
    if missing_min_cols:
        _add_failure(
            failures, f"{label}_schema_missing",
            f"missing columns {missing_min_cols}",
        )

    if not df.empty and all(
        c in df.columns for c in ("slate_date", "game_id", "player_id")
    ):
        dupes = int(df.duplicated(["slate_date", "game_id", "player_id"]).sum())
        if dupes:
            _add_failure(
                failures, f"{label}_duplicate_keys",
                f"{dupes} duplicate slate_date/game_id/player_id rows",
            )

    if df.empty:
        return

    import numpy as _np

    for col in (
        "minutes_mean",
        "minutes_p10",
        "minutes_p50",
        "minutes_p90",
        "minutes_std",
        "rotation_probability",
        "starter_probability",
    ):
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        bad = int(s.isna().sum() + (~_np.isfinite(s.astype(float))).sum())
        if bad > 0:
            _add_failure(
                failures, f"{label}_null_or_nonfinite_{col}",
                f"{bad} {label} rows with null/non-finite {col}",
            )

    for col in ("minutes_mean", "minutes_p10", "minutes_p50", "minutes_p90"):
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        bad = int(((s < 0.0) | (s > 60.0)).sum())
        if bad > 0:
            _add_failure(
                failures, f"{label}_{col}_out_of_range",
                f"{bad} {label} rows have {col} outside [0, 60]",
            )

    for col in ("rotation_probability", "starter_probability"):
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        bad = int(((s < 0.0) | (s > 1.0)).sum())
        if bad > 0:
            _add_failure(
                failures, f"{label}_{col}_out_of_range",
                f"{bad} {label} rows have {col} outside [0, 1]",
            )


def _check_publication_contract(
    df: pd.DataFrame, *, label: str, failures: list[dict]
) -> None:
    """Publication-artifact gate: every row must be eligible (if a
    ``player_game_eligible`` column is present) AND no deep-bench
    no-line rows. Applies to the canonical, the model-review package,
    Derek's forward feed, and the filtered ``minutes_predictions_eligible``
    artifact.
    """
    if df.empty:
        return
    if "player_game_eligible" in df.columns:
        bad = int(df["player_game_eligible"].astype(bool).eq(False).sum())
        if bad > 0:
            _add_failure(
                failures, f"{label}_ineligible_rows",
                f"{bad} {label} rows with player_game_eligible=False",
            )
    deep_bench = _check_deep_bench(df)
    if deep_bench > 0:
        _add_failure(
            failures, f"{label}_deep_bench_no_line_PMFs",
            f"{deep_bench} {label} rows are no-line, sub-12-min, "
            "sub-50% rotation/starter",
        )


def _key_set(df: pd.DataFrame, keys: list[str]) -> set[tuple]:
    df2 = df.dropna(subset=keys)
    return set(zip(*[df2[k].astype(int) if df2[k].dtype != "object" else df2[k] for k in keys]))


def validate(date: str, train_through_date: str) -> dict:
    failures: list[dict] = []
    notes: dict[str, Any] = {}
    print(f"validate_daily_pmf_delivery date={date} train_through={train_through_date}")

    minutes_path = _path(f"artifacts/minutes_predictions/{date}/minutes_predictions.parquet")
    minutes_eligible_path = _path(
        f"artifacts/minutes_predictions/{date}/minutes_predictions_eligible.parquet"
    )
    canonical_path = _path(f"deliveries/{date}/canonical_source/all_props_model_only.parquet")
    review_path = _path(
        f"deliveries/{date}/pmf_model_review_package/machine_readable/model_only.parquet"
    )
    market_pq_path = _path(f"deliveries/{date}/wizard_of_odds/market_comparison.parquet")
    market_csv_path = _path(f"deliveries/{date}/wizard_of_odds/market_comparison.csv")
    derek_path = _path(f"deliveries/{date}/derek_forward_feed/derek_forward_feed.parquet")

    # 1. minutes UNIVERSE artifact missing
    minutes_df = _safe_read(minutes_path)
    if minutes_df is None:
        _add_failure(
            failures, "minutes_artifact_missing",
            f"missing {minutes_path.relative_to(REPO_ROOT)}",
        )

    # 2-3. universe-gate proof: schema + uniqueness + null/range checks.
    # Deep-bench rows in the universe artifact are EXPECTED (by design); the
    # eligible view filters them for publication. No deep-bench gate here.
    if minutes_df is not None:
        _check_universe_contract(
            minutes_df, label="minutes_universe", failures=failures,
        )

    # 3b. eligible-view artifact: must exist, must pass publication gate.
    minutes_eligible_df = _safe_read(minutes_eligible_path)
    if minutes_eligible_df is None:
        _add_failure(
            failures, "minutes_eligible_artifact_missing",
            f"missing {minutes_eligible_path.relative_to(REPO_ROOT)} — "
            "rebuild via scripts/build_minutes_predictions.py",
        )
    else:
        _check_publication_contract(
            minutes_eligible_df, label="minutes_eligible", failures=failures,
        )
        if "eligibility_reason" in minutes_eligible_df.columns:
            valid_reasons = {
                "current_market_line",
                "starter_probability",
                "rotation_probability",
                "minutes_floor",
            }
            bad_reason = int(
                (~minutes_eligible_df["eligibility_reason"].astype(str).isin(valid_reasons))
                .sum()
            )
            if bad_reason > 0:
                _add_failure(
                    failures, "minutes_eligible_invalid_reason",
                    f"{bad_reason} eligible rows with eligibility_reason not in "
                    f"{sorted(valid_reasons)}",
                )

    # 4. canonical missing required columns
    canonical_df = _safe_read(canonical_path)
    if canonical_df is None:
        _add_failure(
            failures, "canonical_missing",
            f"missing {canonical_path.relative_to(REPO_ROOT)}",
        )
    else:
        missing_canon_cols = [c for c in REQUIRED_CANONICAL_COLUMNS if c not in canonical_df.columns]
        if missing_canon_cols:
            _add_failure(
                failures, "canonical_schema_missing",
                f"missing columns {missing_canon_cols}",
            )

        # 5. canonical with player_game_eligible=False
        if "player_game_eligible" in canonical_df.columns:
            bad = int(canonical_df["player_game_eligible"].astype(bool).eq(False).sum())
            if bad > 0:
                _add_failure(
                    failures, "canonical_ineligible_rows",
                    f"{bad} canonical rows with player_game_eligible=False",
                )

        # 6. canonical null minutes_mean
        if "minutes_mean" in canonical_df.columns:
            null_min = int(canonical_df["minutes_mean"].isna().sum())
            if null_min > 0:
                _add_failure(
                    failures, "canonical_null_minutes_mean",
                    f"{null_min} canonical rows with null minutes_mean",
                )

        # 7. canonical null role_bucket
        if _is_role_bucket_missing(canonical_df):
            _add_failure(
                failures, "canonical_null_role_bucket",
                "canonical contains rows with missing role_bucket",
            )

        # 8. canonical deep bench no-line low-minute low-rotation
        deep_bench = _check_deep_bench(canonical_df)
        if deep_bench > 0:
            _add_failure(
                failures, "canonical_deep_bench_no_line_PMFs",
                f"{deep_bench} canonical rows are no-line, sub-12-min, sub-50% rotation/starter",
            )

    # 9. review keys mismatch canonical on (slate_date, game_id, player_id, stat)
    review_df = _safe_read(review_path)
    if canonical_df is not None and review_df is not None:
        keys = ["slate_date", "game_id", "player_id", "stat"]
        present = [k for k in keys if k in canonical_df.columns and k in review_df.columns]
        if len(present) >= 3:
            try:
                canon_keys = _key_set(canonical_df, present)
                review_keys = _key_set(review_df, present)
                missing_in_review = canon_keys - review_keys
                extra_in_review = review_keys - canon_keys
                if missing_in_review or extra_in_review:
                    _add_failure(
                        failures, "review_keys_mismatch_canonical",
                        f"review keys differ from canonical: "
                        f"missing_in_review={len(missing_in_review)} "
                        f"extra_in_review={len(extra_in_review)}",
                    )
            except Exception as exc:
                print(f"  warn: key compare canonical vs review failed: {exc}")

    # 10. Derek non-eligible rows
    derek_df = _safe_read(derek_path)
    if derek_df is not None:
        if "player_game_eligible" in derek_df.columns:
            bad = int(derek_df["player_game_eligible"].astype(bool).eq(False).sum())
            if bad > 0:
                _add_failure(
                    failures, "derek_ineligible_rows",
                    f"{bad} Derek rows with player_game_eligible=False",
                )

    # 11. wizard tiny/empty with scheduled games
    market_df = _safe_read(market_pq_path)
    if market_df is None:
        market_df = _safe_read(market_csv_path)
    if canonical_df is not None and not canonical_df.empty:
        if market_df is None or market_df.empty:
            _add_failure(
                failures, "wizard_empty_with_scheduled_games",
                "market_comparison artifact is missing/empty though canonical has rows",
            )
        elif len(market_df) < max(5, int(0.05 * len(canonical_df))):
            _add_failure(
                failures, "wizard_tiny_with_scheduled_games",
                f"market_comparison row count {len(market_df)} suspiciously small "
                f"vs canonical {len(canonical_df)}",
            )

    # 12. source readiness failed
    readiness_path = _path(f"artifacts/source_readiness/{date}/source_readiness.json")
    if readiness_path.exists():
        try:
            data = json.loads(readiness_path.read_text())
            if str(data.get("source_readiness_status", "")).lower() == "failed":
                _add_failure(
                    failures, "source_readiness_failed",
                    f"source readiness status=failed: blockers={data.get('blockers')}",
                )
        except Exception as exc:
            print(f"  warn: could not parse readiness: {exc}")

    # 14. market-superiority claim true when validation says false (read
    # artifacts/market_benchmark/{train_through_date}/rolling_market_benchmark.json
    # if present).
    market_bench_path = _path(
        f"artifacts/market_benchmark/{train_through_date}/rolling_market_benchmark.json"
    )
    if failures and market_bench_path.exists():
        try:
            bench = json.loads(market_bench_path.read_text())
            if bool(bench.get("market_superiority_claim", False)):
                _add_failure(
                    failures, "market_superiority_claim_with_failures",
                    "market-superiority claim is true while validation reports failures",
                )
        except Exception as exc:
            print(f"  warn: could not parse market_benchmark: {exc}")

    # 13. manifest says passed when any validation failed — enforced by
    # this script's own status emission below.

    if minutes_df is not None and minutes_df.empty:
        status = "empty_slate"
    elif minutes_df is None or canonical_df is None:
        status = "source_unavailable"
    elif failures:
        status = "failed"
    else:
        status = "passed"

    notes["minutes_predictions_rows"] = int(0 if minutes_df is None else len(minutes_df))
    notes["minutes_eligible_rows"] = int(
        0 if minutes_eligible_df is None else len(minutes_eligible_df)
    )
    notes["canonical_rows"] = int(0 if canonical_df is None else len(canonical_df))
    notes["review_rows"] = int(0 if review_df is None else len(review_df))
    notes["market_rows"] = int(0 if market_df is None else len(market_df))
    notes["derek_rows"] = int(0 if derek_df is None else len(derek_df))
    notes["proof_gates"] = {
        "minutes_universe": "schema+uniqueness+null/range checks (NO deep-bench gate)",
        "minutes_eligible_and_publication": (
            "schema + deep-bench gate + player_game_eligible==True"
        ),
    }

    return {
        "delivery_date": date,
        "train_through_date": train_through_date,
        "status": status,
        "failures": failures,
        "notes": notes,
        "checked_at_utc": _now_utc_iso(),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True, help="YYYY-MM-DD slate date")
    ap.add_argument("--train-through-date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args(argv)

    manifest = validate(args.date, args.train_through_date)
    merge_manifest_injury_fields(manifest, args.date, REPO_ROOT)
    out_path = REPO_ROOT / "deliveries" / args.date / "manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"  wrote {out_path.relative_to(REPO_ROOT)}")
    print(f"  status: {manifest['status']} failures={len(manifest['failures'])}")
    if manifest["status"] == "passed":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
