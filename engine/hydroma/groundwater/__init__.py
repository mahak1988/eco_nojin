"""
Groundwater Module - Phase 3 Water Intelligence
================================================
"""

from .service import (
    AquiferType,
    GroundwaterInput,
    GroundwaterResult,
    GroundwaterService,
    WaterQualityClass,
)
from .models import (
    GroundwaterBucketInput,
    GroundwaterBucketOutput,
    run_groundwater_bucket,
)

__all__ = [
    "AquiferType",
    "GroundwaterInput",
    "GroundwaterResult",
    "GroundwaterService",
    "WaterQualityClass",
    "GroundwaterBucketInput",
    "GroundwaterBucketOutput",
    "run_groundwater_bucket",
]
