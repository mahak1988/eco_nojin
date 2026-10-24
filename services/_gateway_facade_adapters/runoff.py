"""Surface-runoff engine bindings for the gateway facade.

Owns the facade's engine import from ``engine.hydroma.runoff`` (the grid
vectorised SCS-CN triplet). The scalar path stays the gateway CANON-004
dispatch; this is the batch counterpart: one call carries the engine's
relation over an entire raster instead of one gateway round trip per
distinct (precipitation, curve number) pair. Nothing here re-implements
computation — the equation lives once, in the engine.
"""

from __future__ import annotations

from engine.hydroma.runoff import scs_cn_raster_depth_mm

__all__ = ["scs_cn_raster_depth_mm"]
