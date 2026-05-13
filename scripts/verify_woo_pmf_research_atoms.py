#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

FORBIDDEN = ("ladder", "p_ge", "survival", "cdf", "cumulative", "reconstructed", "threshold")


def _fail(msg: str) -> None:
    raise SystemExit(f"M8_6O_WOO_PMF_RESEARCH_ATOMS_FAIL: {msg}")


def _candidate_paths(date: str | None) -> list[Path]:
    paths: list[Path] = []
    if date:
        paths.append(Path("public_export/wizard_of_odds") / date / "pmf_research.json")
    paths.extend([
        Path("public_export/wizard_of_odds/latest/pmf_research.json"),
        Path("public_export/wizard_of_odds/pmf_research.json"),
        Path("predictions/pmf_research.json"),
    ])
    return paths


def _load_json(date: str | None) -> tuple[Path, dict[str, Any]]:
    for p in _candidate_paths(date):
        if p.exists():
            return p, json.loads(p.read_text())
    _fail("pmf_research.json not found in expected public_export/predictions paths")


def _parse_atoms(obj: Any) -> dict[int, float]:
    if isinstance(obj, str):
        obj = json.loads(obj)

    if isinstance(obj, dict):
        keys = set(str(k).lower() for k in obj.keys())
        if any(tok in keys for tok in FORBIDDEN):
            _fail(f"forbidden PMF source key found: {sorted(keys & set(FORBIDDEN))}")

        if "atom_pmf" in obj:
            return _parse_atoms(obj["atom_pmf"])

        if "support" in obj and "probs" in obj:
            support = obj["support"]
            probs = obj["probs"]
            if len(support) != len(probs):
                _fail("support/probs length mismatch")
            return {int(k): float(v) for k, v in zip(support, probs)}

        out: dict[int, float] = {}
        for k, v in obj.items():
            ks = str(k)
            if any(tok in ks.lower() for tok in FORBIDDEN):
                _fail(f"forbidden atom key/token: {ks}")
            out[int(float(ks))] = float(v)
        return out

    if isinstance(obj, list):
        return {i: float(v) for i, v in enumerate(obj)}

    _fail(f"unsupported atom PMF shape: {type(obj).__name__}")


def _validate_atoms(atoms: dict[int, float], context: str) -> None:
    if not atoms:
        _fail(f"{context}: empty atom PMF")
    if min(atoms) < 0:
        _fail(f"{context}: negative outcome key")
    if sorted(atoms) != list(range(min(atoms), max(atoms) + 1)):
        _fail(f"{context}: atom outcome keys are not consecutive integers")

    vals = list(atoms.values())
    if not all(math.isfinite(v) for v in vals):
        _fail(f"{context}: non-finite probability")
    if any(v < -1e-12 for v in vals):
        _fail(f"{context}: negative probability")
    s = sum(vals)
    if abs(s - 1.0) > 1e-6:
        _fail(f"{context}: probabilities sum to {s}, not 1")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    args = ap.parse_args()

    path, data = _load_json(args.date)

    if data.get("atom_pmf_policy") != "atom_source_only_no_ladder_fallback":
        _fail("atom_pmf_policy missing or wrong")

    players = data.get("players")
    if not isinstance(players, list) or not players:
        _fail("top-level players array missing or empty")

    checked = 0
    for pi, player in enumerate(players):
        stats = player.get("stats") or player.get("pmfs") or player.get("props")
        if not isinstance(stats, list) or not stats:
            _fail(f"player[{pi}] missing stats/pmfs/props array")

        for si, row in enumerate(stats):
            row_text = json.dumps(row).lower()
            if any(tok in row_text for tok in ("ladder", "p_ge", "survival", "cumulative", "reconstructed")):
                _fail(f"player[{pi}].stats[{si}] contains forbidden PMF token")

            atom_obj = (
                row.get("atom_pmf")
                or row.get("model_full_pmf")
                or row.get("pmf")
                or row.get("pmf_json")
                or ({"support": row.get("support"), "probs": row.get("probs")} if row.get("support") is not None and row.get("probs") is not None else None)
            )
            if atom_obj is None:
                _fail(f"player[{pi}].stats[{si}] missing atom PMF field")

            atoms = _parse_atoms(atom_obj)
            _validate_atoms(atoms, f"player[{pi}].stats[{si}]")
            checked += 1

    if checked <= 0:
        _fail("zero PMFs checked")

    print(f"M8_6O_WOO_PMF_RESEARCH_ATOMS_PASS path={path} pmfs_checked={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
