#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sgp_engine.bundle import SlateStateBundle
from sgp_engine.calibration import JointProbabilityCalibrator
from sgp_engine.pricing import load_ticket, price_ticket
from sgp_engine.simulation import SimulationTape
from sgp_engine.sports.nba.adapter import build_nba_slate_state_bundle
from sgp_engine.sports.nba.simulator import NBASimulator


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True)
    p.add_argument("--repo-root", default=".")
    p.add_argument("--ticket-json", required=True)
    p.add_argument("--n-sims", type=int, default=200000)
    p.add_argument("--seed", type=int, default=20260530)
    p.add_argument("--calibrator", default=None)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    repo = Path(args.repo_root)
    bundle_root = repo / "deliveries" / args.date / "sgp_engine" / "slate_state_bundle_v1"
    bundle = SlateStateBundle.load(bundle_root) if bundle_root.exists() else build_nba_slate_state_bundle(repo, args.date)
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
    out = Path(args.out) if args.out else repo / "deliveries" / args.date / "sgp_engine" / "prices" / f"{ticket.ticket_id or 'ticket'}_price.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
