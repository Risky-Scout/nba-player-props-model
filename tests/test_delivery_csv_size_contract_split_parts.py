"""Tests for the CSV size contract's split-parts discovery filter.

Regression: WoO morning monetization smoke (RUN_ID 26173162428) failed
with ``FileNotFoundError`` because the contract's top-level CSV iterator
captured a stale generated ``*_csv_parts/*.csv`` path that an earlier
iteration in the same loop removed during a re-split.

The narrow fix: exclude any CSV whose path contains a ``*_csv_parts/``
directory from the top-level source scan. Generated parts are still
produced and validated from disk by the source-CSV processing branch.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "enforce_delivery_csv_size_contract.py"
DATE = "2099-12-31"
MAX_BYTES = 16 * 1024


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "_enforce_delivery_csv_size_contract_under_test", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def delivery_tree(tmp_path: Path) -> Path:
    root = tmp_path / "deliveries" / DATE
    for sub in ("wizard_of_odds", "derek_forward_feed", "canonical_source"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "automation_health").mkdir(parents=True, exist_ok=True)
    return root


def _run_contract(
    delivery_root: Path,
    *extra_args: str,
    write: bool = True,
    max_bytes: int = MAX_BYTES,
    preserve: list[str] | None = None,
) -> subprocess.CompletedProcess:
    artifacts_dir = delivery_root.parent.parent / "artifacts" / "automation_health"
    args = [
        sys.executable,
        str(SCRIPT),
        "--date", DATE,
        "--delivery-root", str(delivery_root),
        "--artifacts-dir", str(artifacts_dir),
        "--max-bytes", str(max_bytes),
    ]
    if write:
        args.append("--write")
    for p in preserve or []:
        args.extend(["--preserve", p])
    args.extend(extra_args)
    return subprocess.run(args, capture_output=True, text=True)


def _write_oversized_csv(path: Path, rows: int = 3000, ncols: int = 10) -> int:
    header = ",".join(f"col_{i:02d}" for i in range(ncols))
    lines = [header]
    for r in range(rows):
        lines.append(",".join(f"row{r:05d}_col{c}" for c in range(ncols)))
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    return path.stat().st_size


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_contract_json(delivery_root: Path) -> dict:
    artifacts = delivery_root.parent.parent / "artifacts" / "automation_health"
    json_path = artifacts / f"delivery_csv_size_contract_{DATE}.json"
    assert json_path.exists(), f"missing artifact JSON: {json_path}"
    return json.loads(json_path.read_text(encoding="utf-8"))


def test_generated_parts_excluded_from_initial_scan(delivery_tree: Path):
    module = _load_script_module()

    source = delivery_tree / "wizard_of_odds" / "fair_odds_board.csv"
    source.write_text("a,b,c\n1,2,3\n", encoding="utf-8")

    parts_dir = delivery_tree / "wizard_of_odds" / "fair_odds_board_csv_parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    part_000 = parts_dir / "fair_odds_board_part_000.csv"
    part_007 = parts_dir / "fair_odds_board_part_007.csv"
    part_000.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    part_007.write_text("a,b,c\n7,8,9\n", encoding="utf-8")

    assert module._is_generated_csv_part(part_000) is True
    assert module._is_generated_csv_part(part_007) is True
    assert module._is_generated_csv_part(source) is False

    discovered = sorted(
        p for p in delivery_tree.rglob("*.csv")
        if not module._is_generated_csv_part(p)
    )
    assert source in discovered
    assert part_000 not in discovered
    assert part_007 not in discovered


def test_stale_split_part_does_not_crash_after_rebuild(delivery_tree: Path):
    source = delivery_tree / "wizard_of_odds" / "fair_odds_board.csv"
    size = _write_oversized_csv(source, rows=3000, ncols=10)
    assert size > MAX_BYTES, "fixture must exceed max_bytes to force a split"

    parts_dir = delivery_tree / "wizard_of_odds" / "fair_odds_board_csv_parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    stale_part = parts_dir / "fair_odds_board_part_007.csv"
    stale_part.write_text("col_00,col_01\nstale,stale\n", encoding="utf-8")

    proc = _run_contract(delivery_tree)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)

    rebuilt = sorted(parts_dir.glob("fair_odds_board_part_*.csv"))
    rebuilt_names = [p.name for p in rebuilt]
    assert rebuilt, "expected at least one part to be generated"
    if "fair_odds_board_part_007.csv" not in rebuilt_names:
        assert not stale_part.exists(), (
            "stale part_007.csv must not survive the re-split when the "
            "new split produced fewer parts"
        )

    combined = proc.stdout + proc.stderr
    assert "DELIVERY_CSV_SPLIT_PARTS_VALIDATED" in combined, combined
    assert "FileNotFoundError" not in combined, combined


def test_split_parts_list_derived_from_disk(delivery_tree: Path):
    source = delivery_tree / "wizard_of_odds" / "fair_odds_board.csv"
    _write_oversized_csv(source, rows=3000, ncols=10)

    proc = _run_contract(delivery_tree)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)

    payload = _load_contract_json(delivery_tree)

    referenced: list[str] = []
    for rec in payload.get("records", []):
        referenced.extend(rec.get("parts", []))

    assert referenced, f"contract JSON had no parts manifest: {payload}"
    missing = [p for p in referenced if not (delivery_tree / p).exists()]
    assert not missing, (
        f"contract referenced non-existent parts: {missing}; payload={payload}"
    )


def test_zero_column_csv_fails(delivery_tree: Path):
    bad = delivery_tree / "canonical_source" / "broken.csv"
    bad.write_text("", encoding="utf-8")

    proc = _run_contract(delivery_tree)
    assert proc.returncode != 0, (proc.stdout, proc.stderr)
    combined = proc.stdout + proc.stderr
    assert "DELIVERY_CSV_SCHEMA_ZERO_COLUMNS_FAIL" in combined, combined


def test_header_only_csv_passes(delivery_tree: Path):
    header_only = delivery_tree / "canonical_source" / "header_only.csv"
    header_only.write_text("a,b,c\n", encoding="utf-8")

    proc = _run_contract(delivery_tree)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)


def test_protected_derek_summary_unchanged(delivery_tree: Path):
    derek = delivery_tree / "derek_forward_feed" / "derek_unique_props_summary.csv"
    derek.write_text(
        "player_name,projected_minutes,stat,pmf_mean,market_line,p_over\n"
        "Alice,32.5,pts,21.4,20.5,0.58\n"
        "Bob,28.1,ast,5.9,5.5,0.62\n",
        encoding="utf-8",
    )
    before_hash = _hash(derek)

    proc = _run_contract(
        delivery_tree,
        preserve=["derek_forward_feed/derek_unique_props_summary.csv"],
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)

    after_hash = _hash(derek)
    assert before_hash == after_hash, (
        "preserved Derek summary must not be rewritten by the size contract"
    )
