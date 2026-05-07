"""Compatibility shim for lineup context feature imports.

Concrete implementations live in live_context.py and direct_lineup_context.py.
"""

from nba_props_model.features.live_context import *  # noqa: F401,F403
from nba_props_model.features.direct_lineup_context import *  # noqa: F401,F403
