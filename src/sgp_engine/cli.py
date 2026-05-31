from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bundle import SlateStateBundle
from .calibration import JointProbabilityCalibrator
from .pricing import load_ticket, price_ticket
from .simulation import SimulationTape
from .sports.nba.adapter import build_nba_slate_state_bundle
from .sports.nba.simulator import NBASimulator


def verify_sgp_delivery_outputs(
    repo_root,
    date: str,
    *,
    require_price_grid: bool = False,
) -> dict:
    """Verify SGP delivery outputs for a given date.

    Returns a dict with status, hard_failures, and warnings.
    Raises FileNotFoundError if require_price_grid=True and the price grid is absent.
    """
    import json as _json
    root = Path(repo_root)
    sgp_dir = root / "deliveries" / date / "sgp_engine"

    hard: list[str] = []
    warns: list[str] = []

    if require_price_grid:
        price_grid = sgp_dir / "prices" / "sgp_price_grid.parquet"
        if not price_grid.exists():
            hard.append(f"sgp_price_grid.parquet missing at {price_grid}")

    gate_file = sgp_dir / "calibration" / "sgp_gate_status.json"
    if gate_file.exists():
        gj = _json.loads(gate_file.read_text())
        if gj.get("gate_status") not in ("PASS", "CERTIFIED"):
            warns.append(f"calibration_gate_status={gj.get('gate_status')}")

    result = {
        "status": "FAIL" if hard else "PASS",
        "hard_failures": hard,
        "warnings": warns,
    }
    if hard:
        raise FileNotFoundError(hard[0])
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser("sgp-engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build-nba-bundle")
    p.add_argument("--date", required=True)
    p.add_argument("--repo-root", default=".")
    p.add_argument("--snapshot-type", default="auto")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--expected-cutoff-date", default=None,
                   help="Expected trained/calibrated through date. Defaults to slate_date - 1 calendar day.")
    p.add_argument("--allow-missing-asof-metadata", action="store_true",
                   help="DEV ONLY: warn instead of fail when trained/calibrated through metadata is missing.")

    p = sub.add_parser("simulate-nba")
    p.add_argument("--date", required=True)
    p.add_argument("--repo-root", default=".")
    p.add_argument("--n-sims", type=int, default=200000)
    p.add_argument("--seed", type=int, default=20260530)
    p.add_argument("--allow-non-pass", action="store_true")

    p = sub.add_parser("price-ticket")
    p.add_argument("--date", required=True)
    p.add_argument("--repo-root", default=".")
    p.add_argument("--ticket-json", required=True)
    p.add_argument("--n-sims", type=int, default=200000)
    p.add_argument("--seed", type=int, default=20260530)
    p.add_argument("--calibrator", default=None)
    p.add_argument("--out", default=None)

    args = parser.parse_args(argv)
    repo = Path(args.repo_root)

    if args.cmd == "build-nba-bundle":
        bundle = build_nba_slate_state_bundle(
            repo,
            args.date,
            snapshot_type=args.snapshot_type,
            strict=args.strict,
            expected_cutoff_date=args.expected_cutoff_date,
            allow_missing_asof_metadata=args.allow_missing_asof_metadata,
        )
        print(json.dumps({"status": bundle.status, "bundle_root": str(bundle.root)}, indent=2))
        return 0

    if args.cmd == "simulate-nba":
        bundle_root = repo / "deliveries" / args.date / "sgp_engine" / "slate_state_bundle_v1"
        if not bundle_root.exists():
            bundle = build_nba_slate_state_bundle(repo, args.date, snapshot_type="auto", strict=False)
        else:
            bundle = SlateStateBundle.load(bundle_root)
        if not args.allow_non_pass:
            bundle.assert_pass()
        sim = NBASimulator(bundle, n_sims=args.n_sims, seed=args.seed).run()
        out = repo / "deliveries" / args.date / "sgp_engine" / "simulations" / f"nba_sim_tape_{args.n_sims}.npz"
        sim.save_npz(out)
        print(json.dumps({"simulation_tape": str(out), "n_sims": args.n_sims}, indent=2))
        return 0

    if args.cmd == "price-ticket":
        bundle_root = repo / "deliveries" / args.date / "sgp_engine" / "slate_state_bundle_v1"
        if not bundle_root.exists():
            bundle = build_nba_slate_state_bundle(repo, args.date, snapshot_type="auto", strict=False)
        else:
            bundle = SlateStateBundle.load(bundle_root)
        bundle.assert_pass()

        tape_path = repo / "deliveries" / args.date / "sgp_engine" / "simulations" / f"nba_sim_tape_{args.n_sims}.npz"
        if tape_path.exists():
            tape = SimulationTape.load_npz(tape_path)
        else:
            tape = NBASimulator(bundle, n_sims=args.n_sims, seed=args.seed).run()
            tape.save_npz(tape_path)

        cal = JointProbabilityCalibrator.load(args.calibrator) if args.calibrator else None
        ticket = load_ticket(args.ticket_json)
        result = price_ticket(ticket, tape, bundle.player_stat_pmfs, joint_calibrator=cal)
        out_path = Path(args.out) if args.out else repo / "deliveries" / args.date / "sgp_engine" / "prices" / f"{ticket.ticket_id or 'ticket'}_price.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True))
        print(json.dumps({"price_file": str(out_path), "calibrated_joint_probability": result["calibrated_joint_probability"], "fair_american_odds": result["fair_american_odds"]}, indent=2))
        return 0

    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
