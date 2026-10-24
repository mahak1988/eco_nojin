"""
Groundwater Module - Phase 3 Water Intelligence
================================================
"""

from .models import (
    GroundwaterBucketInput,
    GroundwaterBucketOutput,
    run_groundwater_bucket,
)
from .service import (
    AquiferType,
    GroundwaterInput,
    GroundwaterResult,
    GroundwaterService,
    WaterQualityClass,
)

__all__ = [
    "AquiferType",
    "GroundwaterBucketInput",
    "GroundwaterBucketOutput",
    "GroundwaterInput",
    "GroundwaterResult",
    "GroundwaterService",
    "WaterQualityClass",
    "run_groundwater_bucket",
]
