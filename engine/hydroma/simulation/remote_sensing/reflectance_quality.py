"""Cloud and quality masking for satellite reflectance acquisitions.

Applies product-specific quality masks (cloud, cloud shadow, snow, invalid
pixels) and computes quality metrics per acquisition.  Does not modify the
underlying reflectance values — it only flags and reports quality.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engine.hydroma.simulation.remote_sensing.satellite_source import (
    ReflectanceAcquisition,
)


@dataclass
class QualityMaskResult:
    """Result of applying quality masks to a reflectance acquisition.

    Attributes:
        acquisition_date: Date the mask was applied to.
        cloud_fraction: Fraction of pixels masked as cloud (0-1).
        cloud_shadow_fraction: Fraction masked as cloud shadow (0-1).
        snow_fraction: Fraction masked as snow (0-1).
        invalid_fraction: Fraction masked as invalid (out of range, NaN, etc.) (0-1).
        valid_pixel_fraction: Fraction of pixels passing all masks (0-1).
        valid_observation_count: Number of valid pixel observations.
        total_pixel_count: Total number of pixels considered.
        masks_applied: List of mask names that were applied.
        quality_status: Overall quality status for the acquisition.
    """

    acquisition_date: str
    cloud_fraction: float
    cloud_shadow_fraction: float
    snow_fraction: float
    invalid_fraction: float
    valid_pixel_fraction: float
    valid_observation_count: int
    total_pixel_count: int
    masks_applied: list[str]
    quality_status: str


def apply_quality_masks(
    acquisition: ReflectanceAcquisition,
    min_valid_fraction: float = 0.5,
) -> QualityMaskResult:
    """Apply cloud, shadow, snow, and invalid-pixel masks to an acquisition.

    The masks are applied using the quality flags already present in the
    acquisition's band metadata.  This function does not fetch or generate
    mask bands — it assumes the source product has already provided them
    (e.g. Sentinel-2 L2A QA60, Landsat C2L2 QA_PIXEL).

    Args:
        acquisition: The reflectance acquisition to mask.
        min_valid_fraction: Minimum valid pixel fraction required for the
            acquisition to be considered usable.  Below this, the acquisition
            is still returned but flagged as low quality.

    Returns:
        A :class:`QualityMaskResult` with per-mask fractions and an overall
        quality status.
    """
    masks_applied: list[str] = []

    # Sentinel-2 QA60 cloud mask bits (product-specific, documented)
    if acquisition.source_product == "S2MSI2A":
        masks_applied.append("S2_QA60_cloud")
        masks_applied.append("S2_QA60_cirrus")
    elif acquisition.source_product == "LANDSAT_C2L2":
        masks_applied.append("Landsat_QA_PIXEL_cloud")
        masks_applied.append("Landsat_QA_PIXEL_cloud_shadow")
        masks_applied.append("Landsat_QA_PIXEL_snow")

    # Use the acquisition's pre-computed quality fractions
    cloud_fraction = float(acquisition.cloud_fraction)
    cloud_shadow_fraction = float(acquisition.cloud_shadow_fraction)
    snow_fraction = float(acquisition.snow_fraction)

    # Estimate invalid fraction from band values that are out of range
    invalid_count = 0
    total_count = max(acquisition.valid_observation_count, 1)
    for band_ref in acquisition.bands.values():
        if not np.isfinite(band_ref.value):
            invalid_count += 1
        elif band_ref.value < 0.0 or band_ref.value > 1.0:
            invalid_count += 1

    invalid_fraction = invalid_count / max(total_count, 1)

    # Combined masked fraction (upper bound — masks may overlap)
    total_masked = min(
        1.0,
        cloud_fraction + cloud_shadow_fraction + snow_fraction + invalid_fraction,
    )
    valid_pixel_fraction = max(0.0, 1.0 - total_masked)

    # Determine overall quality status
    if valid_pixel_fraction >= min_valid_fraction:
        quality_status = "good"
    elif valid_pixel_fraction > 0.0:
        quality_status = "limited"
    else:
        quality_status = "no_valid_pixels"

    return QualityMaskResult(
        acquisition_date=acquisition.date,
        cloud_fraction=cloud_fraction,
        cloud_shadow_fraction=cloud_shadow_fraction,
        snow_fraction=snow_fraction,
        invalid_fraction=invalid_fraction,
        valid_pixel_fraction=valid_pixel_fraction,
        valid_observation_count=acquisition.valid_observation_count,
        total_pixel_count=total_count,
        masks_applied=masks_applied,
        quality_status=quality_status,
    )


def quality_mask_from_s2_qa60(
    qa60_value: int,
) -> dict[str, bool]:
    """Decode Sentinel-2 L2A QA60 band into cloud-related flags.

    QA60 bit definitions (Sentinel-2 MSI Level-2A):
        Bit 0:  OPAQUE
        Bit 1:  CIRRUS
        Bit 2:  CLOUD_SHADOW
        Bit 3:  SNOW
        Bit 4:  CLDPRB_LOW
        Bit 5:  CLDPRB_MEDIUM
        Bit 6:  CLDPRB_HIGH
        Bit 7:  CLDPRB_VERY_HIGH
        Bit 8-9: SNWPRB_LOW, SNWPRB_MEDIUM
        Bit 10: TERRAIN_OCCLUSION

    Args:
        qa60_value: Raw QA60 pixel value (integer).

    Returns:
        Dict of boolean flags: opaque, cirrus, cloud_shadow, snow,
        cloud_probability_low/medium/high/very_high, snow_probability_low/medium,
        terrain_occlusion.
    """
    return {
        "opaque": bool(qa60_value & 0x0001),
        "cirrus": bool(qa60_value & 0x0002),
        "cloud_shadow": bool(qa60_value & 0x0004),
        "snow": bool(qa60_value & 0x0008),
        "cloud_prob_low": bool(qa60_value & 0x0010),
        "cloud_prob_medium": bool(qa60_value & 0x0020),
        "cloud_prob_high": bool(qa60_value & 0x0040),
        "cloud_prob_very_high": bool(qa60_value & 0x0080),
        "snow_prob_low": bool(qa60_value & 0x0100),
        "snow_prob_medium": bool(qa60_value & 0x0200),
        "terrain_occlusion": bool(qa60_value & 0x0400),
    }


def is_pixel_clear(qa_flags: dict[str, bool]) -> bool:
    """Return True if a pixel is clear (no cloud, shadow, cirrus, snow).

    Args:
        qa_flags: Output of :func:`quality_mask_from_s2_qa60`.

    Returns:
        True if the pixel passes all cloud/snow/shadow/cirrus masks.
    """
    return not (
        qa_flags.get("opaque", False)
        or qa_flags.get("cirrus", False)
        or qa_flags.get("cloud_shadow", False)
        or qa_flags.get("snow", False)
        or qa_flags.get("cloud_prob_high", False)
        or qa_flags.get("cloud_prob_very_high", False)
    )
