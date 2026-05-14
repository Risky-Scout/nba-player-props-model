"""Ex-ante role bucketing for PMF calibration.

Provides the shared language for splitting player-games into role buckets
based on the predicted minutes distribution. Used by:

  - OOF calibration data (persisted alongside each PMF row)
  - Role-aware stat PMF calibrators (one isotonic per stat per role bucket,
    shrunk back to a global stat calibrator)
  - Role-aware minutes calibrator
  - Diagnostics stratified by role
  - Live prediction at inference time

Role buckets are derived ONLY from the predicted minutes distribution.
Actual minutes are never used here — using them would leak information
during OOF calibration.
"""
from __future__ import annotations


ROLE_BUCKETS = (
    "inactive_risk",
    "fringe",
    "bench",
    "rotation",
    "core",
    "starter",
)


def role_bucket_from_minutes_dist(
    minutes_dist,
    *,
    suppress_inactive_risk: bool = False,
) -> str:
    """Ex-ante role bucket for PMF calibration.

    Uses only the predicted minutes distribution (mean, q25, p_inactive),
    never actual minutes. Safe for OOF calibration and live inference.

    When ``suppress_inactive_risk`` is True (e.g. availability inputs are
    stale for this run), the ``inactive_risk`` bucket is never returned;
    the player is mapped to ``bench`` instead so downstream pipelines
    do not treat DNP-risk as fully identified from stale injury data.

    Bucket definitions (predicted-minutes mean μ) when inactive_risk is
    not suppressed:
      inactive_risk  P(inactive) >= 0.12 OR predicted q25 <= 3.0
      fringe         μ < 12.0
      bench          12.0 <= μ < 18.0
      rotation       18.0 <= μ < 24.0
      core           24.0 <= μ < 30.0
      starter        μ >= 30.0
    """
    try:
        mu = float(minutes_dist.mean())
    except Exception:
        mu = 24.0
    try:
        q25 = float(minutes_dist.quantile(0.25))
    except Exception:
        q25 = mu
    try:
        p_inactive = float(minutes_dist.state_probs[0])
    except Exception:
        p_inactive = 0.0

    # High DNP / role-collapse risk dominates.
    if p_inactive >= 0.12 or q25 <= 3.0:
        if suppress_inactive_risk:
            return "bench"
        return "inactive_risk"
    if mu < 12.0:
        return "fringe"
    if mu < 18.0:
        return "bench"
    if mu < 24.0:
        return "rotation"
    if mu < 30.0:
        return "core"
    return "starter"


def role_bucket_features_from_minutes_dist(
    minutes_dist,
    *,
    suppress_inactive_risk: bool = False,
) -> dict:
    """Persistable metadata for OOF calibration rows.

    Returns the role bucket plus the predicted minutes summary statistics
    needed to fit role-aware calibrators in Stage 4 and to run role-stratified
    diagnostics in Stage 6.

    All values are derived from the predicted minutes distribution.
    No actual-minutes leakage.

    The state_probs extraction uses defensive indexing so this module
    remains compatible if the minutes-model state space later expands
    beyond three states.
    """
    try:
        state_probs = list(minutes_dist.state_probs)
        p0 = float(state_probs[0]) if len(state_probs) > 0 else 0.0
        p_limited = float(state_probs[1]) if len(state_probs) > 1 else 0.0
        p_normal = float(state_probs[2]) if len(state_probs) > 2 else 1.0
    except Exception:
        p0, p_limited, p_normal = 0.0, 0.0, 1.0
    try:
        mu = float(minutes_dist.mean())
    except Exception:
        mu = float("nan")
    try:
        sd = float(minutes_dist.std())
    except Exception:
        sd = float("nan")
    try:
        q10 = float(minutes_dist.quantile(0.10))
        q25 = float(minutes_dist.quantile(0.25))
        q50 = float(minutes_dist.quantile(0.50))
        q75 = float(minutes_dist.quantile(0.75))
        q90 = float(minutes_dist.quantile(0.90))
    except Exception:
        q10 = q25 = q50 = q75 = q90 = float("nan")

    return {
        "role_bucket": role_bucket_from_minutes_dist(
            minutes_dist, suppress_inactive_risk=suppress_inactive_risk,
        ),
        "minutes_mean": mu,
        "minutes_std": sd,
        "minutes_q10": q10,
        "minutes_q25": q25,
        "minutes_q50": q50,
        "minutes_q75": q75,
        "minutes_q90": q90,
        "p_inactive": p0,
        "p_limited": p_limited,
        "p_normal": p_normal,
    }
