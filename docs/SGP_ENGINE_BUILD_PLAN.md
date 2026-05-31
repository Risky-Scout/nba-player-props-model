# SGP Engine Build Plan

## Mission

Build a same-game joint probability engine that consumes daily full-PMF deliveries and produces calibrated SGP fair odds inside `deliveries/<date>/sgp_engine/`.

## Architecture

1. Build `slate_state_bundle_v1` from the daily PMF delivery.
2. Run sport-specific full-game simulation.
3. Generate a reusable simulation tape.
4. Evaluate SGP tickets directly against simulated box scores.
5. Apply out-of-sample joint probability calibrators where available.
6. Write fair odds, diagnostics, and manifest outputs into the same daily delivery folder.

## NBA v1 mechanics

The first NBA simulator is a marginal-anchored game-mechanism factor simulator:
- game factors: pace, total, close-game, blowout, overtime
- team factors: offense, shooting, threes, assists, rebound pool, turnovers, defensive activity
- player factors: minutes, usage, shooting, energy, defense, foul risk
- PMF anchoring: final calibrated atom PMFs define the marginal distribution
- joint structure: shared factors create same-game dependency

This is designed to be enriched with possession-level simulation as the PMF repo exports more latent ingredients.

## Production promotion rule

Do not claim market superiority until:
- historical backtest rows are generated point-in-time
- joint reliability buckets pass
- calibrated joint probability beats raw simulator out-of-sample
- raw/calibrated simulator beats independence baseline
- comparison to market SGP prices, if available, passes bootstrap gates
