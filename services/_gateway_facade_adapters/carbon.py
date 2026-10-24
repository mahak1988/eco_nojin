"""Carbon and MRV engine bindings for the gateway facade.

Owns the facade's engine imports from ``engine.hydroma.carbon.calculator``
(``CarbonProjectType``) and the ``engine.hydroma.mrv`` package: the
``satellite_cdse`` module object, the IoT ingest helpers, the CDSE client
contracts and the MRV Pydantic request/response schemas.

Every module name imported here was previously imported directly by
``services/_gateway_facade.py``; nothing here re-implements computation.
``engine.hydroma.carbon.calculator`` is the one import the policy records as a
POLICY GAP (a computation module that should be reached through the Gateway's
``CARBON_SEQ`` handler instead); it is retained here as that debt, unchanged.
"""

from __future__ import annotations

from engine.hydroma.carbon.calculator import CarbonProjectType
from engine.hydroma.mrv import satellite_cdse
from engine.hydroma.mrv.iot_ingest import (
    parse_ttn_v3,
    persist_iot_reading,
    webhook_key_ok,
)
from engine.hydroma.mrv.satellite_cdse import (
    CdseConfig,
    CdseUnavailable,
    build_bbox,
    retrieve_ndvi,
)
from engine.hydroma.mrv.schemas import (
    CitizenBatch,
    CitizenReport,
    IoTReading,
    SatelliteIndex,
)

__all__ = [
    "CarbonProjectType",
    "CdseConfig",
    "CdseUnavailable",
    "CitizenBatch",
    "CitizenReport",
    "IoTReading",
    "SatelliteIndex",
    "build_bbox",
    "parse_ttn_v3",
    "persist_iot_reading",
    "retrieve_ndvi",
    "satellite_cdse",
    "webhook_key_ok",
]
