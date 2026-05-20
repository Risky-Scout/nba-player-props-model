"""Tests for ``scripts/build_combo_oof_pmfs_from_base_oof.py``.

Regression: Phase 8 of run 26178439866 crashed with
``IndexError: list index out of range`` because the combo OOF builder
required EVERY player-game record to contain all five base stats
(``pts, reb, ast, stl, blk``) before that record could contribute to ANY
combo. When the aggregate OOF input only contained ``pts/reb/ast`` the
builder ended up with zero eligible records and then crashed accessing
``unique_dates[0]`` / ``unique_dates[-1]`` on an empty list.

The fix is per-combo component eligibility:

  pr     = pts + reb
  pa     = pts + ast
  ra     = reb + ast
  pra    = pts + reb + ast
  stocks = stl + blk

A record contributes to whichever combos its ``pmf`` subset satisfies;
``stocks`` is skipped (not fabricated) when ``stl``/``blk`` are absent.

These tests exercise the patched builder end-to-end via ``subprocess``
against synthetic in-memory base-OOF parquet fixtures (no real OOF
files, no network, no real artifacts).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build_combo_oof_pmfs_from_base_oof.py"

REQUIRED_INPUT_COLUMNS = (
    "stat",
    "player_id",
    "game_id",
    "game_date",
    "outcome",
    "pmf",
    "role_bucket",
)

MANIFEST_REQUIRED_FIELDS = (
    "available_base_stats",
    "combo_requirements",
    "combos_attempted",
    "combos_built",
    "combos_skipped",
    "skip_reasons",
    "n_rows_written",
    "status",
)

EXPECTED_COMBO_REQUIREMENTS = {
    "pr":     ["pts", "reb"],
    "pa":     ["pts", "ast"],
    "ra":     ["reb", "ast"],
    "pra":    ["pts", "reb", "ast"],
    "stocks": ["stl", "blk"],
}


# ── Fixture helpers ──────────────────────────────────────────────────────


def _flat_pmf(support_max: int) -> np.ndarray:
    """Tiny normalised PMF over [0, support_max] for synthetic fixtures."""
    n = int(support_max) + 1
    arr = np.full(n, 1.0 / n, dtype=np.float64)
    return arr


_STAT_SUPPORT_MAX = {
    "pts": 5,
    "reb": 3,
    "ast": 2,
    "stl": 2,
    "blk": 2,
    "tov": 2,
    "fg3m": 2,
}


def _build_base_oof_df(
    stats: list[str],
    *,
    n_players: int = 6,
    n_dates: int = 2,
    role_bucket: str = "rotation",
) -> pd.DataFrame:
    """Build a synthetic base-OOF DataFrame for the given stats.

    Each (player, date) pair becomes one player-game with rows for every
    requested stat. The PMF shape per stat is a flat distribution sized
    by ``_STAT_SUPPORT_MAX`` so the test can recompute the expected combo
    ``support_max`` without depending on the sampling implementation.
    """
    rows: list[dict] = []
    for d_idx in range(n_dates):
        game_date = f"2026-01-{1 + d_idx:02d}"
        for player_idx in range(n_players):
            player_id = 1000 + player_idx
            game_id = 50_000 + d_idx * 100 + player_idx
            for stat in stats:
                smax = _STAT_SUPPORT_MAX[stat]
                pmf = _flat_pmf(smax)
                outcome = int(player_idx % (smax + 1))
                rows.append({
                    "stat": stat,
                    "player_id": int(player_id),
                    "game_id": int(game_id),
                    "game_date": game_date,
                    "outcome": int(outcome),
                    "pmf": pmf.tolist(),
                    "role_bucket": role_bucket,
                })
    df = pd.DataFrame(rows)
    for col in REQUIRED_INPUT_COLUMNS:
        assert col in df.columns, f"fixture missing required column {col}"
    return df


def _write_input_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _run_builder(
    tmp_path: Path,
    *,
    in_path: Path,
    out_path: Path,
    manifest_path: Path,
    as_of_date: str = "2026-01-05",
    n_draws: int = 256,
    min_prior_rows: int = 10_000,  # force cold-start for synthetic scale
    extra: list[str] | None = None,
) -> subprocess.CompletedProcess:
    args = [
        sys.executable,
        str(SCRIPT),
        "--in", str(in_path),
        "--out", str(out_path),
        "--manifest", str(manifest_path),
        "--as-of-date", as_of_date,
        "--n-draws", str(n_draws),
        "--min-prior-rows", str(min_prior_rows),
    ]
    if extra:
        args.extend(extra)
    return subprocess.run(args, capture_output=True, text=True, cwd=str(tmp_path))


def _load_manifest(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ── Tests ────────────────────────────────────────────────────────────────


def test_pts_reb_ast_only_builds_pr_pa_ra_pra_skips_stocks(tmp_path: Path) -> None:
    """The exact production failure case: aggregate OOF has only pts/reb/ast.

    Phase 8 of run 26178439866 had this exact shape. We assert the builder
    now builds ``pr``, ``pa``, ``ra``, ``pra`` and skips ``stocks`` with a
    structured manifest reason instead of crashing.
    """
    in_path = tmp_path / "in.parquet"
    out_path = tmp_path / "out.parquet"
    manifest_path = tmp_path / "out.manifest.json"

    df = _build_base_oof_df(["pts", "reb", "ast"], n_players=4, n_dates=2)
    _write_input_parquet(df, in_path)

    result = _run_builder(
        tmp_path,
        in_path=in_path,
        out_path=out_path,
        manifest_path=manifest_path,
    )
    assert result.returncode == 0, f"builder failed: {result.stderr}\n{result.stdout}"

    out_df = pd.read_parquet(out_path)
    stats_built = set(out_df["stat"].astype(str).unique())
    assert {"pr", "pa", "ra", "pra"}.issubset(stats_built), stats_built
    assert "stocks" not in stats_built, stats_built
    stocks_rows = out_df[out_df["stat"] == "stocks"]
    assert len(stocks_rows) == 0

    manifest = _load_manifest(manifest_path)
    assert manifest["status"] == "partial", manifest["status"]
    built_combos = {entry["combo"] for entry in manifest["combos_built"]}
    assert built_combos == {"pr", "pa", "ra", "pra"}, built_combos
    skipped = {entry["combo"]: entry["reason"] for entry in manifest["combos_skipped"]}
    assert "stocks" in skipped
    reason = skipped["stocks"].lower()
    assert "stl" in reason and "blk" in reason, skipped["stocks"]
    assert manifest["skip_reasons"]["stocks"] == skipped["stocks"]


def test_pts_reb_only_builds_pr_skips_pa_ra_pra_stocks(tmp_path: Path) -> None:
    """When only pts/reb are present, only ``pr`` is eligible."""
    in_path = tmp_path / "in.parquet"
    out_path = tmp_path / "out.parquet"
    manifest_path = tmp_path / "out.manifest.json"

    df = _build_base_oof_df(["pts", "reb"], n_players=3, n_dates=2)
    _write_input_parquet(df, in_path)

    result = _run_builder(
        tmp_path,
        in_path=in_path,
        out_path=out_path,
        manifest_path=manifest_path,
    )
    assert result.returncode == 0, f"builder failed: {result.stderr}\n{result.stdout}"

    out_df = pd.read_parquet(out_path)
    assert set(out_df["stat"].astype(str).unique()) == {"pr"}

    manifest = _load_manifest(manifest_path)
    assert manifest["status"] == "partial", manifest["status"]
    built = {entry["combo"] for entry in manifest["combos_built"]}
    assert built == {"pr"}, built
    skipped = {entry["combo"]: entry["reason"] for entry in manifest["combos_skipped"]}
    for combo in ("pa", "ra", "pra", "stocks"):
        assert combo in skipped, (combo, skipped)
        # Every skip reason must explicitly name at least one missing component.
        assert "missing components" in skipped[combo].lower(), (combo, skipped[combo])


def test_stocks_built_when_stl_and_blk_present(tmp_path: Path) -> None:
    """All five combos build when every base stat is present (status=ok)."""
    in_path = tmp_path / "in.parquet"
    out_path = tmp_path / "out.parquet"
    manifest_path = tmp_path / "out.manifest.json"

    df = _build_base_oof_df(
        ["pts", "reb", "ast", "stl", "blk"], n_players=4, n_dates=2
    )
    _write_input_parquet(df, in_path)

    result = _run_builder(
        tmp_path,
        in_path=in_path,
        out_path=out_path,
        manifest_path=manifest_path,
    )
    assert result.returncode == 0, f"builder failed: {result.stderr}\n{result.stdout}"

    out_df = pd.read_parquet(out_path)
    assert set(out_df["stat"].astype(str).unique()) == {
        "pr", "pa", "ra", "pra", "stocks",
    }

    manifest = _load_manifest(manifest_path)
    assert manifest["status"] == "ok", manifest["status"]
    built = {entry["combo"] for entry in manifest["combos_built"]}
    assert built == {"pr", "pa", "ra", "pra", "stocks"}, built
    assert manifest["combos_skipped"] == [], manifest["combos_skipped"]


def test_no_eligible_records_does_not_raise_indexerror(tmp_path: Path) -> None:
    """No base stats anywhere → no IndexError, status=no_eligible_records.

    Uses ``tov`` which is NOT a component for any combo, so every combo
    will be skipped without invoking the unique_dates code path.
    """
    in_path = tmp_path / "in.parquet"
    out_path = tmp_path / "out.parquet"
    manifest_path = tmp_path / "out.manifest.json"

    df = _build_base_oof_df(["tov"], n_players=3, n_dates=2)
    _write_input_parquet(df, in_path)

    result = _run_builder(
        tmp_path,
        in_path=in_path,
        out_path=out_path,
        manifest_path=manifest_path,
    )
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    assert "IndexError" not in combined, combined
    assert "list index out of range" not in combined, combined
    assert "COMBO_OOF_NO_ELIGIBLE_RECORDS" in combined, combined
    assert result.returncode != 0, (
        "expected non-zero exit for no_eligible_records "
        f"(got {result.returncode})"
    )

    manifest = _load_manifest(manifest_path)
    assert manifest["status"] == "no_eligible_records", manifest["status"]
    assert manifest["n_rows_written"] == 0
    built = {entry["combo"] for entry in manifest["combos_built"]}
    assert built == set(), built
    skipped = {entry["combo"] for entry in manifest["combos_skipped"]}
    assert skipped == {"pr", "pa", "ra", "pra", "stocks"}, skipped
    # Output parquet intentionally not written on the fail-closed path.
    assert not out_path.exists()


def test_correlation_dimensions_are_combo_specific(tmp_path: Path) -> None:
    """Verify per-combo construction via support_max evidence.

    ``support_max`` for ``pr`` rows must equal ``pts_max + reb_max`` (2 components)
    and ``support_max`` for ``pra`` rows must equal ``pts_max + reb_max + ast_max``
    (3 components). This proves each combo is built ONLY from its own
    component PMFs (not from a global 5-component construction).
    """
    in_path = tmp_path / "in.parquet"
    out_path = tmp_path / "out.parquet"
    manifest_path = tmp_path / "out.manifest.json"

    df = _build_base_oof_df(["pts", "reb", "ast"], n_players=3, n_dates=2)
    _write_input_parquet(df, in_path)

    result = _run_builder(
        tmp_path,
        in_path=in_path,
        out_path=out_path,
        manifest_path=manifest_path,
    )
    assert result.returncode == 0, f"builder failed: {result.stderr}\n{result.stdout}"

    out_df = pd.read_parquet(out_path)

    pts_max = _STAT_SUPPORT_MAX["pts"]
    reb_max = _STAT_SUPPORT_MAX["reb"]
    ast_max = _STAT_SUPPORT_MAX["ast"]

    pr_rows = out_df[out_df["stat"] == "pr"]
    pra_rows = out_df[out_df["stat"] == "pra"]
    pa_rows = out_df[out_df["stat"] == "pa"]
    ra_rows = out_df[out_df["stat"] == "ra"]

    assert len(pr_rows) > 0 and len(pra_rows) > 0
    assert (pr_rows["support_max"] == pts_max + reb_max).all()
    assert (pra_rows["support_max"] == pts_max + reb_max + ast_max).all()
    assert (pa_rows["support_max"] == pts_max + ast_max).all()
    assert (ra_rows["support_max"] == reb_max + ast_max).all()

    # Every row's PMF length equals support_max + 1; pr is 2-component, pra is 3.
    pr_pmf_len = pr_rows["pmf"].iloc[0]
    pra_pmf_len = pra_rows["pmf"].iloc[0]
    assert len(pr_pmf_len) == pts_max + reb_max + 1
    assert len(pra_pmf_len) == pts_max + reb_max + ast_max + 1

    # Per-combo eligibility marker present in stdout.
    assert "COMBO_OOF_ELIGIBILITY combo=pr" in result.stdout, result.stdout
    assert "COMBO_OOF_ELIGIBILITY combo=pra" in result.stdout, result.stdout


def test_manifest_contract(tmp_path: Path) -> None:
    """All required structured manifest fields are present."""
    in_path = tmp_path / "in.parquet"
    out_path = tmp_path / "out.parquet"
    manifest_path = tmp_path / "out.manifest.json"

    df = _build_base_oof_df(["pts", "reb", "ast"], n_players=2, n_dates=2)
    _write_input_parquet(df, in_path)

    result = _run_builder(
        tmp_path,
        in_path=in_path,
        out_path=out_path,
        manifest_path=manifest_path,
    )
    assert result.returncode == 0, f"builder failed: {result.stderr}\n{result.stdout}"

    manifest = _load_manifest(manifest_path)
    for field in MANIFEST_REQUIRED_FIELDS:
        assert field in manifest, f"manifest missing required field: {field}"

    assert manifest["combos_attempted"] == ["stocks", "pa", "pr", "ra", "pra"]
    assert manifest["combo_requirements"] == EXPECTED_COMBO_REQUIREMENTS
    assert sorted(manifest["available_base_stats"]) == ["ast", "pts", "reb"]
    assert manifest["n_rows_written"] == len(pd.read_parquet(out_path))
    assert isinstance(manifest["combos_built"], list)
    assert isinstance(manifest["combos_skipped"], list)
    assert isinstance(manifest["skip_reasons"], dict)


def test_unique_dates_empty_does_not_crash(tmp_path: Path) -> None:
    """Specifically exercise the empty-data path through the script.

    Source OOF parquet has the required columns but ZERO rows. The patched
    builder must NOT raise IndexError on ``unique_dates[0]``; it must emit
    a structured ``no_eligible_records`` manifest and exit cleanly with the
    documented marker.
    """
    in_path = tmp_path / "in.parquet"
    out_path = tmp_path / "out.parquet"
    manifest_path = tmp_path / "out.manifest.json"

    empty_df = pd.DataFrame({
        "stat": pd.Series([], dtype="object"),
        "player_id": pd.Series([], dtype="int64"),
        "game_id": pd.Series([], dtype="int64"),
        "game_date": pd.Series([], dtype="object"),
        "outcome": pd.Series([], dtype="int64"),
        "pmf": pd.Series([], dtype="object"),
        "role_bucket": pd.Series([], dtype="object"),
    })
    _write_input_parquet(empty_df, in_path)

    result = _run_builder(
        tmp_path,
        in_path=in_path,
        out_path=out_path,
        manifest_path=manifest_path,
    )
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    assert "IndexError" not in combined, combined
    assert "list index out of range" not in combined, combined
    assert "COMBO_OOF_NO_ELIGIBLE_RECORDS" in combined, combined

    manifest = _load_manifest(manifest_path)
    assert manifest["status"] == "no_eligible_records", manifest["status"]
    assert manifest["n_rows_written"] == 0
    assert manifest["available_base_stats"] == []
    # Every combo must appear in skip_reasons with an explanatory string.
    assert set(manifest["skip_reasons"].keys()) == {
        "pr", "pa", "ra", "pra", "stocks",
    }
