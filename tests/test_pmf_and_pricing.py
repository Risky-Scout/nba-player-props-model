import numpy as np
import pandas as pd

from sgp_engine.pmf import event_probability, parse_pmf
from sgp_engine.schema import SGPTicket
from sgp_engine.simulation import SimulationTape
from sgp_engine.pricing import price_ticket


def test_event_probability():
    pmf = parse_pmf({"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4})
    assert abs(event_probability(pmf, 1.5, "over") - 0.7) < 1e-9
    assert abs(event_probability(pmf, 1.5, "under") - 0.3) < 1e-9


def test_price_ticket_basic():
    n = 1000
    stats = {
        ("G", "P1", "pts"): np.arange(n) % 40,
        ("G", "P2", "ast"): np.arange(n) % 12,
    }
    tape = SimulationTape(n_sims=n, stats=stats, factors={}, metadata={})
    pmf_df = pd.DataFrame([
        {"game_id": "G", "player_id": "P1", "stat": "pts", "pmf_json": {str(i): 1/40 for i in range(40)}, "domain_max": 39},
        {"game_id": "G", "player_id": "P2", "stat": "ast", "pmf_json": {str(i): 1/12 for i in range(12)}, "domain_max": 11},
    ])
    ticket = SGPTicket.from_dict({
        "game_id": "G",
        "legs": [
            {"player_id": "P1", "stat": "pts", "line": 19.5, "side": "over"},
            {"player_id": "P2", "stat": "ast", "line": 5.5, "side": "over"},
        ],
    })
    out = price_ticket(ticket, tape, pmf_df)
    assert 0 <= out["calibrated_joint_probability"] <= 1
    assert out["n_legs"] == 2
