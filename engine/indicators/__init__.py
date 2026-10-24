"""Indicators — a navigable mirror of the spec §3.1 chain (re-export layer).

What this package is
--------------------
``engine/indicators`` is the spec §3.1 *indicators* node. Today it is a
re-export layer: every name below is imported, never re-implemented, so the
scientific indicator chain — the drought index (SPI), the field water balance,
water productivity and the eight hydroma index/landscape models — becomes
navigable from one place without moving a single module.

Module migration happens later, behind a mandate: A-4 step 2 migrates
``spi_calculator`` / ``water_balance`` / ``water_productivity`` and
``engine/hydroma/models/{hdvi,epia,ewsi,esri,ecsi,hyrue,hlhs,hpheno}.py``
into this package one family at a time, each behind a parity test, with the old
path kept as a re-export for two releases. Nothing here has started that
migration: this file holds no algorithm, no scientific constant and no branch.
It is navigation, and nothing in it may be read as computation.

The TODAY-correct modules mirrored here
---------------------------------------
* ``engine.hydroma.spi_calculator`` — Standardised Precipitation Index (SPI).
* ``engine.hydroma.water_balance`` — field-scale water balance.
* ``engine.hydroma.water_productivity`` — water productivity.
* ``engine.hydroma.models`` index models — ``hdvi`` (drought vulnerability),
  ``epia`` (precision irrigation advisor), ``ewsi`` (multi-source water
  stress), ``esri`` (salinity risk), ``ecsi`` (carbon sequestration),
  ``hyrue`` (radiation use efficiency), ``hlhs`` (landscape health),
  ``hpheno`` (phenology detection).

Every re-exported name is the *same object* as the one its home module
defines, so identity checks against the originals keep holding.
"""

from __future__ import annotations

from engine.hydroma.models.ecsi import ECSI
from engine.hydroma.models.epia import EPIA
from engine.hydroma.models.esri import ESRI
from engine.hydroma.models.ewsi import EWSI, EWSIWeights
from engine.hydroma.models.hdvi import HDVI
from engine.hydroma.models.hlhs import HLHS, LandscapeMetrics
from engine.hydroma.models.hpheno import HPheno
from engine.hydroma.models.hyrue import HYRUE, HYRUEParams
from engine.hydroma.spi_calculator import SUPPORTED_SCALES, calculate_spi
from engine.hydroma.water_balance import water_balance
from engine.hydroma.water_productivity import water_productivity, water_productivity_from_m3

__all__ = [
    "ECSI",
    "EPIA",
    "ESRI",
    "EWSI",
    "EWSIWeights",
    "HDVI",
    "HLHS",
    "HPheno",
    "HYRUE",
    "HYRUEParams",
    "LandscapeMetrics",
    "SUPPORTED_SCALES",
    "calculate_spi",
    "water_balance",
    "water_productivity",
    "water_productivity_from_m3",
]
