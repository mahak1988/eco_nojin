"""hydroma.core package for the HyDroMa engine.

Re-exports the public API from ``engine.hydroma.core.core`` so that
``from engine.hydroma.core import HydromaCore`` works despite this being a
package directory (which shadows the sibling ``core.py`` module).
"""

from engine.hydroma.core.core import (
    EngineContext,
    EngineVersion,
    HydromaCore,
    core_engine,
)

__all__ = ["EngineContext", "EngineVersion", "HydromaCore", "core_engine"]
