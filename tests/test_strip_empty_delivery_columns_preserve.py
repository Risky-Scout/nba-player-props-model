"""Tests for ``scripts/strip_empty_delivery_columns.py`` preserve set.

The Derek builder always emits ``lineup_last_updated_utc`` on the
public Derek forward feed (real timestamp when official lineup
metadata exists; pandas ``pd.NA`` in projected/morning mode). The
post-builder hygiene step ``scripts/strip_empty_delivery_columns.py``
removes any all-null column unless it appears in the per-path
preserve set ``PRESERVE_BY_PATH_SUBSTRING`` for the matching delivery
file. This module pins the contract that:

1. The full Derek feed retains ``lineup_last_updated_utc`` after the
   strip step even when every value is null/blank — preventing the
   ``DEREK_FORWARD_FEED_CONTRACT_FAIL missing_columns=['lineup_last_updated_utc']``
   regression observed in production run 26186630356.
2. The strip step still removes ordinary all-null columns that are
   neither in the contract nor in the preserve set — so the strip
   script is not silently turned into a no-op.

Companion tests for the validator-side surface (Derek full feed
contract pass with null values, fail when the column is missing,
compact ``derek_unique_props_summary.csv`` six-column schema
unchanged) live in ``tests/test_derek_forward_feed_contract.py``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
STRIP_SCRIPT = REPO / "scripts" / "strip_empty_delivery_columns.py"


def _required_contract_columns() -> tuple[str, ...]:
    """Import ``DEREK_UNIFIED_REQUIRED_COLUMNS`` from the canonical
    delivery-contract module.

    Read-only import; the test never mutates it.
    """
    src = REPO / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from nba_props_model.delivery.delivery_contract import (
        DEREK_UNIFIED_REQUIRED_COLUMNS,
    )

    return DEREK_UNIFIED_REQUIRED_COLUMNS


def _seed_minimal_derek_feed(
    feed_dir: Path,
    *,
    extra_all_null_columns: tuple[str, ...] = (),
    rows: int = 2,
) -> tuple[Path, Path]:
    """Write a minimal ``derek_forward_feed.{parquet,csv}`` containing
    every contract-required column, with ``lineup_last_updated_utc``
    intentionally all-null (mirrors projected/morning-mode upstream).

    ``extra_all_null_columns`` lets a test add non-contract null
    columns that the strip step should still remove.
    """
    feed_dir.mkdir(parents=True, exist_ok=True)

    cols = list(_required_contract_columns()) + list(extra_all_null_columns)
    rows_payload: list[dict] = []
    for i in range(rows):
        row = {c: None for c in cols}
        row.update(
            {
                "game_date": "2099-06-15",
                "run_date": "2099-06-15",
                "run_id": "test-run-id",
                "run_mode": "morning_expected",
                "generated_at_utc": "2099-06-15T13:00:00Z",
                "pipeline_version": "test-pipe",
                "model_version": "test-model",
                "model_artifact_hash": None,
                "source_data_asof_utc": "2099-06-15T12:30:00Z",
                "player_id": 1000 + i,
                "player_name": f"Tester {i}",
                "team": "TST",
                "opponent": "OPP",
                "game_id": 999000 + i,
                "stat": "pts",
                "line": 12.5,
                "role_bucket": "starter",
                "hard_role_bucket": "starter",
                "role_mixture_enabled": True,
                "role_bucket_confidence": 0.9,
                "projected_minutes": 30.0,
                "minutes_q50": 30.0,
                "inactive_risk": 0.0,
                "expected_lineup_status": "projected",
                "official_lineup_status": "not_available_yet",
                "injury_status": "ok",
                "injury_source": "test_source",
                "lineup_source": "bdl_lineup_freshness_manifest",
                "stale_injury_flag": False,
                "stale_lineup_flag": False,
                "market_line": 12.5,
                "p_over": 0.55,
                "model_prob_under_active": 0.45,
                "fair_over_odds": -110,
                "fair_under_odds": -110,
                "pmf_mean": 12.4,
                "pmf_variance": 8.1,
                "pmf_p10": 6.0,
                "pmf_p50": 12.0,
                "pmf_p90": 18.0,
                "edge": 0.01,
                "market_status": "full",
                "delivery_status": "ready",
                "calculation_source": "test",
                "calculation_status": "ok",
            }
        )
        rows_payload.append(row)

    df = pd.DataFrame(rows_payload, columns=cols)
    pq_path = feed_dir / "derek_forward_feed.parquet"
    csv_path = feed_dir / "derek_forward_feed.csv"
    df.to_parquet(pq_path, index=False)
    df.to_csv(csv_path, index=False)
    return pq_path, csv_path


def _run_strip(cwd: Path, root: Path, date: str) -> subprocess.CompletedProcess:
    """Invoke the strip script via subprocess against an isolated
    delivery root. ``cwd`` should point at a tmp directory because
    the strip script writes its hygiene report under
    ``<cwd>/artifacts/automation_health/`` — running with
    ``cwd=tmp_path`` keeps the real ``artifacts/`` folder untouched
    during tests.
    """
    return subprocess.run(
        [
            sys.executable,
            str(STRIP_SCRIPT),
            "--date",
            date,
            "--root",
            str(root),
            "--write",
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_strip_preserves_lineup_last_updated_utc_when_all_null(
    tmp_path: Path,
):
    """The full Derek feed must keep ``lineup_last_updated_utc`` after
    the strip step even when every row is null (projected/morning
    mode). No fabrication.
    """
    date = "2099-06-15"
    delivery_root = tmp_path / "deliveries"
    feed_dir = delivery_root / date / "derek_forward_feed"
    pq_path, csv_path = _seed_minimal_derek_feed(feed_dir)

    pre = pd.read_parquet(pq_path)
    assert "lineup_last_updated_utc" in pre.columns, (
        "fixture must seed the column before the strip step"
    )
    assert pre["lineup_last_updated_utc"].isna().all(), (
        "fixture must keep the column all-null to mirror morning mode"
    )

    res = _run_strip(tmp_path, delivery_root, date)
    assert res.returncode == 0, res.stdout + res.stderr

    post_pq = pd.read_parquet(pq_path)
    assert "lineup_last_updated_utc" in post_pq.columns, (
        "strip step removed contract-required column "
        f"lineup_last_updated_utc; remaining cols={sorted(post_pq.columns)}\n"
        f"stdout={res.stdout}\nstderr={res.stderr}"
    )
    assert post_pq["lineup_last_updated_utc"].isna().all(), (
        "strip step must NOT fabricate values for projected mode"
    )

    csv_header = csv_path.read_text().splitlines()[0]
    csv_cols = csv_header.split(",")
    assert "lineup_last_updated_utc" in csv_cols, (
        "strip step removed lineup_last_updated_utc from CSV header; "
        f"got {csv_cols}"
    )
    csv_df = pd.read_csv(csv_path)
    assert csv_df["lineup_last_updated_utc"].isna().all(), (
        "CSV must render the column with empty/null values, never a "
        "fabricated timestamp"
    )


def test_strip_still_removes_unrelated_all_null_columns(
    tmp_path: Path,
):
    """Safety net: the strip step must not become a no-op. A non-
    contract all-null column must still be removed.
    """
    date = "2099-06-16"
    delivery_root = tmp_path / "deliveries"
    feed_dir = delivery_root / date / "derek_forward_feed"
    pq_path, csv_path = _seed_minimal_derek_feed(
        feed_dir,
        extra_all_null_columns=("bogus_all_null",),
    )

    pre = pd.read_parquet(pq_path)
    assert "bogus_all_null" in pre.columns, (
        "fixture must include the bogus column before the strip step"
    )

    res = _run_strip(tmp_path, delivery_root, date)
    assert res.returncode == 0, res.stdout + res.stderr

    post_pq = pd.read_parquet(pq_path)
    assert "bogus_all_null" not in post_pq.columns, (
        "strip step failed to remove a non-contract all-null column "
        "(would silently regress hygiene). "
        f"post-strip cols={sorted(post_pq.columns)}"
    )
    # Sanity: we didn't accidentally drop the contract column we just
    # added to the preserve set in the same patch.
    assert "lineup_last_updated_utc" in post_pq.columns, (
        "strip step removed contract-required column "
        "lineup_last_updated_utc when it should have preserved it"
    )


def test_strip_preserve_set_lists_lineup_last_updated_utc():
    """Static guard: the per-path preserve set for the Derek forward
    feed must include ``lineup_last_updated_utc`` (paired with the
    seven other contract-required columns). Catches accidental
    deletions of the preserve entry.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_strip_module_under_test",
        str(STRIP_SCRIPT),
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    preserve = mod.PRESERVE_BY_PATH_SUBSTRING.get(
        "derek_forward_feed/derek_forward_feed"
    )
    assert preserve is not None, (
        "PRESERVE_BY_PATH_SUBSTRING lost its derek_forward_feed entry"
    )
    assert "lineup_last_updated_utc" in preserve, (
        "preserve set for derek_forward_feed/derek_forward_feed must "
        "include lineup_last_updated_utc; "
        f"got {sorted(preserve)}"
    )
    # Spot-check that the other seven contract columns are still
    # in the preserve set; if any of them disappeared we'd want to
    # know about it.
    for col in (
        "model_artifact_hash",
        "event_id",
        "role_mixture_weights_json",
        "role_entropy",
        "role_bucket_confidence",
        "minutes_q10",
        "minutes_q90",
        "unavailable_reason",
    ):
        assert col in preserve, (
            f"preserve set lost previously-listed column {col!r}; "
            f"got {sorted(preserve)}"
        )


def test_strip_does_not_touch_unique_props_summary(
    tmp_path: Path,
):
    """Sanity: the Derek compact summary lives at
    ``derek_forward_feed/derek_unique_props_summary.csv`` (a path that
    does NOT match the ``derek_forward_feed/derek_forward_feed``
    preserve key). The strip step's per-path preserve change for the
    full feed must not affect that summary; its six-column schema
    stays exactly as published. This protects against a future typo
    in the preserve-key string accidentally widening the match.
    """
    date = "2099-06-17"
    delivery_root = tmp_path / "deliveries"
    feed_dir = delivery_root / date / "derek_forward_feed"
    feed_dir.mkdir(parents=True, exist_ok=True)

    six_cols = [
        "player_name",
        "projected_minutes",
        "stat",
        "pmf_mean",
        "market_line",
        "p_over",
    ]
    summary = pd.DataFrame(
        [
            {
                "player_name": "Tester",
                "projected_minutes": 30.0,
                "stat": "pts",
                "pmf_mean": 18.5,
                "market_line": 17.5,
                "p_over": 0.62,
            }
        ],
        columns=six_cols,
    )
    summary_path = feed_dir / "derek_unique_props_summary.csv"
    summary.to_csv(summary_path, index=False)

    # Also seed the full Derek feed so the strip step has work to do
    # in this delivery folder; the assertion is about the compact
    # summary, not the full feed.
    _seed_minimal_derek_feed(feed_dir)

    res = _run_strip(tmp_path, delivery_root, date)
    assert res.returncode == 0, res.stdout + res.stderr

    post = pd.read_csv(summary_path)
    assert list(post.columns) == six_cols, (
        "derek_unique_props_summary.csv six-column schema must stay "
        f"exactly {six_cols}; got {list(post.columns)}"
    )


def test_strip_emits_hygiene_report_listing_preserved_column(
    tmp_path: Path,
):
    """When ``lineup_last_updated_utc`` is null on the full feed and
    the strip step runs, the hygiene report must NOT list the column
    in ``removed_columns`` for the Derek forward feed file. Mirrors
    the production failure-mode fingerprint we observed in
    ``artifacts/automation_health/delivery_empty_column_hygiene_2026-05-20.json``
    (where the column WAS in ``removed_columns`` for the parquet,
    csv, and jsonl variants).
    """
    date = "2099-06-18"
    delivery_root = tmp_path / "deliveries"
    feed_dir = delivery_root / date / "derek_forward_feed"
    _seed_minimal_derek_feed(feed_dir)

    res = _run_strip(tmp_path, delivery_root, date)
    assert res.returncode == 0, res.stdout + res.stderr

    # Strip script writes the hygiene report under
    # ``<cwd>/artifacts/automation_health/`` — and we ran with
    # ``cwd=tmp_path``, so the real workspace ``artifacts/`` is
    # untouched.
    report_path = (
        tmp_path
        / "artifacts"
        / "automation_health"
        / f"delivery_empty_column_hygiene_{date}.json"
    )
    assert report_path.is_file(), (
        f"strip script did not emit the hygiene JSON at {report_path}"
    )
    payload = json.loads(report_path.read_text())
    for change in payload.get("reports", [{}])[0].get("changes", []):
        file_path = change.get("file", "")
        if "derek_forward_feed/derek_forward_feed" in file_path:
            assert "lineup_last_updated_utc" not in change.get(
                "removed_columns", []
            ), (
                "strip hygiene report still lists lineup_last_updated_utc "
                f"as removed for {file_path}; "
                f"removed={change.get('removed_columns')}"
            )


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-q"])
