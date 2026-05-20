"""Tests for ``scripts/round_delivery_csv_numeric_display.py``.

The script normalizes display precision for user-facing CSVs under
``deliveries/<date>/`` to ``<= --places`` decimal places. These tests
cover:

* float rounding and ``float_format`` display,
* protective skips for ID-like and JSON/weights columns,
* dtype preservation (ints never gain ``.0000``),
* preservation of ``--preserve`` paths (Derek unique summary),
* exclusion of generated ``*_csv_parts/*.csv`` files,
* dry-run reporting without disk writes,
* the success / zero-columns markers,
* header-only CSVs (>=1 column, 0 rows) being valid.

Convention mirrors ``tests/test_delivery_csv_size_contract_split_parts.py``:
CLI surface is exercised via ``subprocess.run`` with the script path
passed verbatim; internal helpers are loaded via ``importlib.util`` only
when needed.
"""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "round_delivery_csv_numeric_display.py"
DATE = "2099-12-31"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "_round_delivery_csv_numeric_display_under_test", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def delivery_tree(tmp_path: Path) -> Path:
    """Return the ``<delivery-root>/<date>/`` folder for tests."""

    root = tmp_path / "deliveries" / DATE
    for sub in ("wizard_of_odds", "derek_forward_feed", "canonical_source"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def _run_script(
    delivery_root: Path,
    *,
    write: bool = False,
    preserve: list[str] | None = None,
    places: int = 4,
    date: str = DATE,
) -> subprocess.CompletedProcess:
    """Invoke the script with ``--delivery-root`` set to the directory that
    directly contains the ``<date>/`` folder (i.e. the ``deliveries`` dir).
    """

    args = [
        sys.executable,
        str(SCRIPT),
        "--date", date,
        "--delivery-root", str(delivery_root),
        "--places", str(places),
    ]
    if write:
        args.append("--write")
    for p in preserve or []:
        args.extend(["--preserve", p])
    return subprocess.run(args, capture_output=True, text=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# ── Tests ───────────────────────────────────────────────────────────


def test_rounds_floats_to_four_decimals(delivery_tree: Path) -> None:
    csv = delivery_tree / "wizard_of_odds" / "fair_odds_board.csv"
    csv.write_text(
        "pmf_mean,market_line\n"
        "1.234567,5.5\n"
        "9.876543210,7.5\n",
        encoding="utf-8",
    )

    result = _run_script(delivery_tree.parent, write=True)
    assert result.returncode == 0, result.stderr

    out = csv.read_text(encoding="utf-8")
    assert "1.2346" in out
    assert "9.8765" in out
    assert "1.234567" not in out
    assert "9.876543210" not in out


def test_integer_column_not_promoted_to_float_display(
    delivery_tree: Path,
) -> None:
    """``int64`` columns must remain integer-formatted (no ``.0000``)."""

    csv = delivery_tree / "wizard_of_odds" / "board.csv"
    csv.write_text(
        "game_id,pmf_mean\n"
        "21713529,1.234567\n"
        "21713530,2.345678\n",
        encoding="utf-8",
    )

    result = _run_script(delivery_tree.parent, write=True)
    assert result.returncode == 0, result.stderr

    out = csv.read_text(encoding="utf-8")
    assert "21713529" in out
    assert "21713530" in out
    assert "21713529.0000" not in out
    assert "21713530.0000" not in out
    assert "1.2346" in out
    assert "2.3457" in out


def test_id_columns_skipped_even_when_float_typed(
    delivery_tree: Path,
) -> None:
    """Float-typed ID columns (NaN forces float dtype) keep their values."""

    csv = delivery_tree / "canonical_source" / "rows.csv"
    csv.write_text(
        "player_id,game_id,event_id,team_id,pmf_mean\n"
        "12345,21713529,99001,1610612747,1.234567\n"
        ",21713530,99002,1610612750,2.345678\n",
        encoding="utf-8",
    )

    result = _run_script(delivery_tree.parent, write=True)
    assert result.returncode == 0, result.stderr

    import pandas as pd

    original = pd.read_csv(csv)
    expected = pd.DataFrame(
        {
            "player_id": [12345.0, float("nan")],
            "game_id": [21713529, 21713530],
            "event_id": [99001, 99002],
            "team_id": [1610612747, 1610612750],
        }
    )
    for col in ("player_id", "game_id", "event_id", "team_id"):
        original_vals = original[col].tolist()
        expected_vals = expected[col].tolist()
        for got, want in zip(original_vals, expected_vals):
            if pd.isna(want):
                assert pd.isna(got), f"{col}: expected NaN, got {got!r}"
            else:
                assert float(got) == float(want), (
                    f"{col}: ID value drifted: {got!r} != {want!r}"
                )


def test_json_and_weights_columns_skipped_byte_for_byte(
    delivery_tree: Path,
) -> None:
    """JSON / weights columns must not be reformatted by the rounding step.

    The CSV is built up by pandas (rather than hand-rolling escape rules)
    so the comparison is robust to whatever quoting convention pandas uses
    to round-trip embedded double-quotes.
    """

    import pandas as pd

    csv = delivery_tree / "derek_forward_feed" / "derek_forward_feed.csv"
    json_val = '{"bench": 0.5, "rotation": 0.5}'
    weights_val = "[0.1, 0.2, 0.7]"
    pd.DataFrame(
        {
            "role_mixture_weights_json": [json_val],
            "custom_weights": [weights_val],
            "pmf_mean": [1.234567],
        }
    ).to_csv(csv, index=False)

    result = _run_script(delivery_tree.parent, write=True)
    assert result.returncode == 0, result.stderr

    df = pd.read_csv(csv)
    assert df.loc[0, "role_mixture_weights_json"] == json_val
    assert df.loc[0, "custom_weights"] == weights_val
    # pmf_mean was rounded and re-serialized in 4dp display form.
    assert float(df.loc[0, "pmf_mean"]) == pytest.approx(1.2346)
    assert "1.2346" in csv.read_text(encoding="utf-8")


def test_header_only_csv_passes(delivery_tree: Path) -> None:
    csv = delivery_tree / "wizard_of_odds" / "header_only.csv"
    csv.write_text("pmf_mean,market_line\n", encoding="utf-8")

    result = _run_script(delivery_tree.parent, write=True)
    assert result.returncode == 0, result.stderr
    assert "DELIVERY_CSV_NUMERIC_ROUNDING_PASS" in result.stdout


def test_zero_column_csv_fails(delivery_tree: Path) -> None:
    csv = delivery_tree / "wizard_of_odds" / "broken_empty.csv"
    csv.write_bytes(b"")

    result = _run_script(delivery_tree.parent, write=True)
    assert result.returncode != 0, result.stdout
    assert "DELIVERY_CSV_ROUNDING_ZERO_COLUMNS_FAIL" in result.stderr


def test_generated_csv_parts_excluded(delivery_tree: Path) -> None:
    source = delivery_tree / "wizard_of_odds" / "fair_odds_board.csv"
    source.write_text(
        "pmf_mean,market_line\n"
        "1.234567,5.5\n",
        encoding="utf-8",
    )

    part_dir = delivery_tree / "wizard_of_odds" / "fair_odds_board_csv_parts"
    part_dir.mkdir(parents=True, exist_ok=True)
    part = part_dir / "fair_odds_board_part_000.csv"
    part_original_bytes = (
        b"pmf_mean,market_line\n"
        b"7.7777777,8.8888888\n"
    )
    part.write_bytes(part_original_bytes)
    part_hash_before = _sha256(part)

    result = _run_script(delivery_tree.parent, write=True)
    assert result.returncode == 0, result.stderr

    out = source.read_text(encoding="utf-8")
    assert "1.2346" in out

    assert _sha256(part) == part_hash_before, "generated part must not change"
    assert part.read_bytes() == part_original_bytes


def test_protected_derek_unique_summary_byte_identical(
    delivery_tree: Path,
) -> None:
    derek = (
        delivery_tree / "derek_forward_feed" / "derek_unique_props_summary.csv"
    )
    derek.write_text(
        "player_name,projected_minutes,stat,pmf_mean,market_line,p_over\n"
        "LeBron James,34.567891,pts,25.6789012,24.5,0.5123456\n"
        "Anthony Davis,32.123456789,reb,11.987654321,10.5,0.6789012\n",
        encoding="utf-8",
    )
    hash_before = _sha256(derek)

    result = _run_script(
        delivery_tree.parent,
        write=True,
        preserve=["derek_forward_feed/derek_unique_props_summary.csv"],
    )
    assert result.returncode == 0, result.stderr
    assert _sha256(derek) == hash_before, (
        "preserved Derek unique summary must not be modified"
    )


def test_dry_run_does_not_write(delivery_tree: Path) -> None:
    csv = delivery_tree / "wizard_of_odds" / "fair_odds_board.csv"
    original_bytes = (
        b"pmf_mean,market_line\n"
        b"1.234567,5.5\n"
        b"9.876543210,7.5\n"
    )
    csv.write_bytes(original_bytes)
    hash_before = _sha256(csv)

    result = _run_script(delivery_tree.parent, write=False)
    assert result.returncode == 0, result.stderr

    assert _sha256(csv) == hash_before, "dry-run must not modify the file"
    assert csv.read_bytes() == original_bytes

    assert "files_changed=1" in result.stdout, result.stdout


def test_success_marker_format(delivery_tree: Path) -> None:
    csv = delivery_tree / "wizard_of_odds" / "fair_odds_board.csv"
    csv.write_text(
        "pmf_mean,market_line\n"
        "1.234567,5.5\n",
        encoding="utf-8",
    )

    result = _run_script(delivery_tree.parent, write=True)
    assert result.returncode == 0, result.stderr

    marker = (
        f"DELIVERY_CSV_NUMERIC_ROUNDING_PASS date={DATE} "
        "files_checked=1 files_changed=1 places=4"
    )
    assert marker in result.stdout, result.stdout


def test_skip_no_date_marker_on_missing_folder(tmp_path: Path) -> None:
    """When the delivery folder does not exist the script must valid-skip."""

    result = _run_script(tmp_path, write=True)
    assert result.returncode == 0, result.stderr
    assert (
        f"DELIVERY_CSV_NUMERIC_ROUNDING_SKIP_NO_DATE date={DATE}"
        in result.stdout
    )


def test_helpers_filter_generated_parts_and_id_columns() -> None:
    mod = _load_script_module()

    assert mod._is_generated_csv_part(
        Path("deliveries/2099-12-31/woo/board_csv_parts/board_part_000.csv")
    )
    assert not mod._is_generated_csv_part(
        Path("deliveries/2099-12-31/woo/board.csv")
    )

    for col in (
        "id",
        "Season",
        "year",
        "count",
        "rows",
        "player_id",
        "game_id",
        "id_lineup",
        "stat_id_role",
    ):
        assert mod._is_id_column(col), col

    for col in ("pmf_mean", "market_line", "p_over"):
        assert not mod._is_id_column(col), col

    assert mod._is_json_or_weights_column("role_mixture_weights_json")
    assert mod._is_json_or_weights_column("custom_weights")
    assert not mod._is_json_or_weights_column("pmf_mean")
