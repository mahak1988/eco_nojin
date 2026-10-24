"""Daily LAI (Leaf Area Index) model with data source priority.

This module provides LAI trajectories for the seasonal HYRUE computation
pipeline.  It supports multiple data source priorities:

1. **observed** — if observed LAI data is provided (field measurements,
   satellite-derived LAI products).
2. **empirical** — if NDVI data is provided, apply the empirical
   relationship LAI = 3.5 * NDVI (Monteith, 1993; see also
   ``services/map_engine/pipelines/vegetation.py``).
3. **model_generated** — GDD-accumulated sigmoid growth curve using
   thresholds from ``engine/hydroma/phenology.py``.  This is a placeholder
   growth curve, not a validated crop model.
4. **unavailable** — no LAI data of any kind is available.

Provenance is tracked per-source so downstream consumers can distinguish
measured data from model-generated values.

Honesty: the GDD sigmoid trajectory is a **placeholder growth curve**, not a
validated crop model.  It produces a plausible LAI series for testing the
seasonal pipeline; it must not be presented as a field-measured or calibrated
prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from engine.hydroma.phenology import CROP_PHENOLOGY

# Empirical conversion: LAI = 3.5 * NDVI
# Source: Monteith, J.L. (1993), "The interpretation of optical leaf
# area indicators as crop vigour indicators." Journal of Agricultural Science,
# Cambridge, 121 (1): 1-4.  Used in services/map_engine/pipelines/vegetation.py
# This coefficient converts the dimensionless NDVI ([-1,1] range, typically
# [0,1] for vegetation) to LAI (m²/m²).
NDVI_TO_LAI_COEFFICIENT = 3.5

# Valid range for empirical LAI derived from NDVI
LAI_MIN = 0.1
LAI_MAX = 8.0


@dataclass
class LAIModelConfig:
    """Configuration for the LAI model."""

    crop: str = "wheat"
    lai_max: float = 4.0
    lai_min: float = 0.1
    gdd_sigmoid_steepness: float = 0.008
    gdd_sigmoid_center: float = 500.0


class LAIModel:
    """Generate daily LAI series from multiple data sources.

    The LAI curve follows a sigmoid growth pattern:
    - Emergence to tillering: slow initial growth
    - Tillering to flowering: rapid LAI increase
    - Flowering to maturity: plateau then senescence

    Data source priority when calling :meth:`compute`:
        1. ``observed_lai`` array — used as-is, provenance="observed"
        2. ``ndvi`` array — converted to LAI via 3.5 * NDVI, provenance="empirical"
        3. GDD sigmoid from daily temperature — provenance="model_generated"
        4. None of the above — returns None, source="unavailable"
    """

    def __init__(self, config: LAIModelConfig | None = None):
        self.config = config or LAIModelConfig()
        self._phenology = CROP_PHENOLOGY.get(
            self.config.crop,
            CROP_PHENOLOGY["wheat"],
        )

    def compute(
        self,
        daily_tmean: np.ndarray,
        planting_doy: int = 1,
    ) -> np.ndarray:
        """Compute daily LAI for a growing season using the GDD model.

        This is the backward-compatible signature: returns only the LAI
        array with ``model_generated`` provenance.  For source priority with
        provenance tracking, use :meth:`compute_with_provenance`.

        Args:
            daily_tmean: Array of daily mean temperatures (°C).
            planting_doy: Day of year for planting (1-365).

        Returns:
            Array of daily LAI values (m²/m²), same length as input.
            Returns an empty array for empty input.
            Provenance: ``model_generated``.
        """
        lai, _ = self.compute_with_provenance(daily_tmean, planting_doy)
        if lai is None:
            return np.array([], dtype=float)
        return lai

    def compute_with_provenance(
        self,
        daily_tmean: np.ndarray,
        planting_doy: int = 1,
        observed_lai: np.ndarray | None = None,
        ndvi: np.ndarray | None = None,
    ) -> tuple[np.ndarray | None, dict[str, Any]]:
        """Compute daily LAI with source priority: observed > NDVI > GDD model.

        Args:
            daily_tmean: Array of daily mean temperatures (°C).
            planting_doy: Day of year for planting (1-365).
            observed_lai: Optional observed LAI array (highest priority).
            ndvi: Optional NDVI array (converted via 3.5 * NDVI).

        Returns:
            Tuple of (lai_array_or_none, provenance_dict).
            lai_array is None when source="unavailable".
        """
        n_days = len(daily_tmean)
        if n_days == 0:
            return None, self._provenance_unavailable()

        # Priority 1: Observed LAI
        if observed_lai is not None:
            lai = np.asarray(observed_lai, dtype=float)
            if lai.shape != (n_days,):
                raise ValueError(
                    f"observed_lai length {lai.size} does not match "
                    f"daily_tmean length {n_days}"
                )
            lai = np.clip(lai, LAI_MIN, LAI_MAX)
            return lai.astype(float), self._provenance_observed()

        # Priority 2: Empirical LAI from NDVI
        if ndvi is not None:
            ndvi_arr = np.asarray(ndvi, dtype=float)
            if ndvi_arr.shape != (n_days,):
                raise ValueError(
                    f"ndvi length {ndvi_arr.size} does not match "
                    f"daily_tmean length {n_days}"
                )
            lai = np.clip(
                NDVI_TO_LAI_COEFFICIENT * ndvi_arr, LAI_MIN, LAI_MAX
            )
            return lai.astype(float), self._provenance_empirical()

        # Priority 3: GDD-based model
        lai = self._compute_gdd_lai(daily_tmean)
        return lai, self.provenance()

    def _compute_gdd_lai(self, daily_tmean: np.ndarray) -> np.ndarray:
        """Compute LAI using GDD-accumulated sigmoid growth curve."""
        n_days = len(daily_tmean)
        if n_days == 0:
            return np.array([], dtype=float)

        t_base = self._phenology.t_base
        gdd = np.cumsum(np.maximum(0.0, daily_tmean - t_base))

        lai_min = self.config.lai_min
        lai_max = self.config.lai_max
        steepness = self.config.gdd_sigmoid_steepness
        center = self.config.gdd_sigmoid_center

        sigmoid = 1.0 / (1.0 + np.exp(-steepness * (gdd - center)))
        lai = lai_min + (lai_max - lai_min) * sigmoid
        lai = np.clip(lai, lai_min, lai_max)

        return lai.astype(float)

    def _provenance_observed(self) -> dict[str, Any]:
        """Provenance for observed LAI data."""
        return {
            "source_model": "LAIModel",
            "source_date": "user_provided_observed_data",
            "unit": "m²/m²",
            "quality_status": "observed",
            "scientific_status": "observed",
            "method": "direct field or satellite measurement",
            "reference": "field measurement or validated satellite product",
            "valid_range": (LAI_MIN, LAI_MAX),
        }

    def _provenance_empirical(self) -> dict[str, Any]:
        """Provenance for NDVI-derived LAI."""
        return {
            "source_model": "LAIModel",
            "source_date": "derived_from_ndvi",
            "unit": "m²/m²",
            "quality_status": "empirical",
            "scientific_status": "empirical",
            "method": f"LAI = {NDVI_TO_LAI_COEFFICIENT} * NDVI",
            "reference": (
                "Monteith, J.L. (1993), The interpretation of optical leaf "
                "area indicators as crop vigour indicators. "
                "Journal of Agricultural Science, Cambridge, 121(1): 1-4."
            ),
            "valid_range": (LAI_MIN, LAI_MAX),
        }

    def _provenance_unavailable(self) -> dict[str, Any]:
        """Provenance for unavailable LAI."""
        return {
            "source_model": "LAIModel",
            "source_date": "unavailable",
            "unit": "m²/m²",
            "quality_status": "unavailable",
            "scientific_status": "unavailable",
            "method": "none — no LAI data source available",
            "reference": "N/A",
            "valid_range": (LAI_MIN, LAI_MAX),
        }

    def provenance(self) -> dict[str, Any]:
        """Return provenance metadata for the GDD model output."""
        return {
            "source_model": "LAIModel",
            "source_date": "computed_from_daily_temperatures",
            "unit": "m²/m²",
            "quality_status": "model_generated",
            "crop": self.config.crop,
            "lai_max": self.config.lai_max,
            "method": "GDD-accumulated sigmoid growth curve",
            "reference": (
                "GDD thresholds from engine/hydroma/phenology.py (FAO literature "
                "averages). LAI curve shape is a placeholder sigmoid, not a "
                "validated crop model."
            ),
            "valid_range": (self.config.lai_min, self.config.lai_max),
            "scientific_status": "model_generated",
        }


def compute_daily_lai(
    daily_tmean: np.ndarray,
    crop: str = "wheat",
    lai_max: float = 4.0,
    observed_lai: np.ndarray | None = None,
    ndvi: np.ndarray | None = None,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    """Convenience function: compute daily LAI with source priority and provenance.

    Args:
        daily_tmean: Array of daily mean temperatures (°C).
        crop: Crop name for GDD thresholds.
        lai_max: Maximum LAI for the crop.
        observed_lai: Optional observed LAI array (highest priority).
        ndvi: Optional NDVI array (converted via 3.5 * NDVI).

    Returns:
        Tuple of (lai_array_or_none, provenance_dict).
    """
    config = LAIModelConfig(crop=crop, lai_max=lai_max)
    model = LAIModel(config=config)
    lai, provenance = model.compute_with_provenance(
        daily_tmean, observed_lai=observed_lai, ndvi=ndvi,
    )
    return lai, provenance