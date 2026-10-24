"""Three-level MRV (EM-01): Measurement, Reporting, Verification.

Level 1 - satellite indices (real or simulated; provenance always labeled).
Level 2 - IoT field sensor readings with QA/QC screening.
Level 3 - citizen field reports (KoboToolbox-style offline forms).

The module also computes transparent dashboard metrics (erosion reduction,
SOC change, CO2e sequestration, restored area, household income) that never
present simulated inputs as measured data.
"""

from engine.hydroma.mrv.qa import (
    QAReport,
    is_usable,
    validate_reading,
    validate_satellite_index,
)
from engine.hydroma.mrv.schemas import CitizenReport, IoTReading, SatelliteIndex

__all__ = [
    "CitizenReport",
    "IoTReading",
    "QAReport",
    "SatelliteIndex",
    "is_usable",
    "validate_reading",
    "validate_satellite_index",
]
