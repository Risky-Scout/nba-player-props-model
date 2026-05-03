"""Phase 13R — contextual PMF engine wiring.

Loads the trained Phase 13Q contextual challenger (Ridge minutes +
per-stat rate adjustments) and exposes a small, side-effect-free helper
that maps a per-row context-feature dict to:

    * minutes_delta              (additive vs. mp_mean_last10 baseline)
    * rate_delta_<stat>          (additive vs. <stat>_rate_mean_last10
                                  baseline) for each fitted target.

It is the **only** module that is allowed to load
``phase13q_<stat>_adjustment_model.pkl`` /
``phase13q_<stat>_adjustment_features.pkl``. Every PMF-estimating path
that wants a contextual adjustment imports from here.

Pass token (consumed by verifiers): PHASE13R_CONTEXTUAL_SCORE_HELPER_READY
"""
from .score import (  # noqa: F401
    CONTEXTUAL_FEATURE_SET_ID,
    ContextualEngine,
    build_context_feature_row,
    load_contextual_engine,
    resolve_contextual_challenger_dir,
)
