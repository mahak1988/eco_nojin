"""
HDVI — Hydroma Drought Vulnerability Index

Multi-scale drought index combining:
- SPI (Standardized Precipitation Index)
- SPEI (Standardized Precipitation-Evapotranspiration Index)
- VHI (Vegetation Health Index)
- SMI (Soil Moisture Index)

Reference: Kogan (1995) for the VHI, which is the only component with an
implemented method here.

CITATIONS REMOVED 2026-10-01. McKee et al. (1993) and Vicente-Serrano et al.
(2010) were attached to `spi()` and to the `spei_value` input respectively.
Neither is implemented:

* `spi()` is a rolling-window z-score of the raw precipitation series. SPI as
  McKee defines it fits a GAMMA distribution to the accumulated precipitation
  over a timescale and transforms the resulting cumulative probability to the
  standard normal. There is no distribution fit and no probability transform
  here. What the code computes is a real and useful quantity, but it is not
  SPI, and reporting it under that name with that citation is the defect.
* There is no SPEI implementation anywhere in this repository. `spei_value`
  is a plain input, exactly as `spi_value` and `smi_value` are.

`spi()` is therefore kept, under its own name, as the platform's own rolling
z-score index. A true SPI is tractable -- fit a gamma to the accumulated
totals per McKee's Table 2 timescales, then Phi^-1(CDF) -- but it needs a
decision about zero-precipitation handling (McKee's zero-probability term),
a minimum record length and a choice of timescales, none of which exist in
this package, so it was not written unilaterally. The SPEI additionally
needs an evapotranspiration series the module does not accept.
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np

from .base import ScientificModel, ValidationResult, validate_finite


class HDVI(ScientificModel):
    """Hydroma Drought Vulnerability Index"""

    name = "HDVI"
    version = "1.0.0"
    description = "Multi-scale Drought Vulnerability Index"

    #: VHI is Kogan's and implemented as such. Everything else -- the two
    #: unit-bridging rescalings, the equal weighting, the class thresholds, and
    #: the rolling z-score the `spi` name is attached to -- is this project's.
    PROVENANCE: ClassVar[str] = "composite"

    REFERENCES: ClassVar[dict] = {
        "Kogan1995": "Kogan, F.N. (1995). Application of vegetation index for drought monitoring.",
    }

    # The ScientificModel ABC declares **inputs / dict-based signatures; the
    # concrete model API in this package is a positional typed inputs object.
    # Unifying the two is a cross-hierarchy API decision, so the divergence is
    # marked rather than silently rewritten here.
    def validate_inputs(  # type: ignore[override]
        self,
        spi_value,
        spei_value,
        vhi_value,
        smi_value,
    ) -> tuple[bool, list[str]]:
        errors = validate_finite(
            "HDVI",
            {
                "spi_value": spi_value,
                "spei_value": spei_value,
                "vhi_value": vhi_value,
                "smi_value": smi_value,
            },
        )
        if errors:
            return False, errors
        if not (-5 <= spi_value <= 5):
            errors.append("SPI out of typical range [-5, 5]")
        if not (-5 <= spei_value <= 5):
            errors.append("SPEI out of typical range")
        if np.any((vhi_value < 0) | (vhi_value > 100)):
            errors.append("VHI out of range [0, 100]")
        if np.any((smi_value < 0) | (smi_value > 1)):
            errors.append("SMI out of range [0, 1]")
        return len(errors) == 0, errors

    @staticmethod
    def spi(precip_series: np.ndarray, window: int = 3) -> np.ndarray:
        """Rolling-window z-score of a precipitation series.

            z[i] = (P[i] - mean(P[i-window:i])) / std(P[i-window:i])

        THIS IS NOT SPI, and the name is a legacy label. SPI as McKee et al.
        (1993) defines it is a two-stage construction that this function does
        not perform:

            1. accumulate precipitation over the timescale of interest;
            2. fit a gamma distribution to the accumulated totals, with a
               zero-probability term for the fraction of totals that are
               exactly zero;
            3. transform the cumulative probability to the standard normal,
               SPI = Phi^-1(F(x)).

        The difference is not cosmetic. A z-score divides by the sample
        standard deviation, so a dry spell inside an otherwise wet record
        produces a large negative value; the gamma transform is asymptotic at
        zero, so it cannot. The two series are also not comparable in shape:
        the z-score is bounded by the sample size, the SPI is unbounded.
        Indices calibrated on one are not valid on the other.

        The function is kept because a rolling z-score is the right cheap
        substitute for a drought screen and the shape is useful. It is
        documented as what it is.

        RECORDED DEFECT 2026-10-01, not changed. A window with zero variance
        has ``std == 0``, and the guard is ``+ 1e-6`` on the denominator rather
        than a zero-variance test, so the score becomes the raw difference over
        1e-6. Measured: a window of ten identical 10.0 mm values followed by
        five 0.001 mm values gives ``z = -9999000.000000002`` at the first dry
        step. That value then enters ``compute`` as an SPI component and is
        silently clipped to -3. A real SPI is asymptotic at zero and would
        produce a large but finite, physically interpretable number; nothing
        in the SPI literature produces a seven-digit standardised anomaly.
        The fix is a zero-variance branch, not a smaller epsilon, and it
        changes values, so it is recorded rather than applied unilaterally.

        The method parameter has no meaning here and is not offered.

        It takes the previous `window` observations and scores the observation
        after them, so the first `window` entries are NaN; any window containing
        a non-positive accumulation is also left NaN, because a gamma fit is
        undefined at zero and a mean is not a substitute for one.
        """
        spi_values = np.full_like(precip_series, np.nan, dtype=float)

        for i in range(window, len(precip_series)):
            window_data = precip_series[i - window : i]
            if np.any(window_data <= 0):
                continue
            mu = np.mean(window_data)
            sigma = np.std(window_data) + 1e-6
            spi_values[i] = (precip_series[i] - mu) / sigma

        return spi_values

    @staticmethod
    def vhi(
        ndvi: np.ndarray,
        lst: np.ndarray,
        ndvi_min: float = 0.1,
        ndvi_max: float = 0.9,
        lst_min: float = 270.0,
        lst_max: float = 330.0,
    ) -> np.ndarray:
        """Vegetation Health Index (Kogan 1995)"""
        vci = np.clip((ndvi - ndvi_min) / (ndvi_max - ndvi_min + 1e-9), 0, 1) * 100
        tci = np.clip((lst_max - lst) / (lst_max - lst_min + 1e-9), 0, 1) * 100
        return 0.5 * vci + 0.5 * tci

    @staticmethod
    def smi(soil_moisture: np.ndarray, wilting_point: float, field_capacity: float) -> np.ndarray:
        """Soil Moisture Index"""
        return np.clip(
            (soil_moisture - wilting_point) / (field_capacity - wilting_point + 1e-9), 0, 1
        )

    # The ScientificModel ABC declares **inputs / dict-based signatures; the
    # concrete model API in this package is a positional typed inputs object.
    # Unifying the two is a cross-hierarchy API decision, so the divergence is
    # marked rather than silently rewritten here.
    def compute(  # type: ignore[override]
        self,
        spi_value: float,
        spei_value: float,
        vhi_value: np.ndarray,
        smi_value: np.ndarray,
        weights: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25),
    ) -> dict[str, Any]:
        """Compute HDVI.

        ``vhi_value`` is the VHI on the 0-100 scale Kogan publishes and the
        one ``validate_inputs`` range-checks, so ``vhi_norm`` below centres it
        on 50 and rescales by 3 to land in the same roughly [-3, 3] band as the
        standardised components. A value near 0.6 is therefore a VHI of 0.6
        PER CENT, i.e. near-total vegetation failure -- ``vhi_norm`` is then
        about -2.96, not near zero. The fixture in
        ``validation/test_cases/hdvi.yaml`` fed 0.60/0.30/0.10 and called the
        case "near_average_drought", which described a uniformly stressed
        landscape and was corrected on 2026-10-01.

        ``spi_value`` and ``spei_value`` are expected on a standardised
        z-like scale. Nothing in this module produced them: `spi` is a
        rolling z-score, not SPI, and there is no SPEI implementation in the
        repository at all. The caller owns both.
        """
        w1, w2, w3, w4 = weights

        # Normalize VHI and SMI to SPI-like scale
        vhi_norm = (vhi_value - 50) / 50 * 3
        smi_norm = (smi_value - 0.5) * 6

        hdvi = w1 * spi_value + w2 * spei_value + w3 * vhi_norm + w4 * smi_norm

        hdvi_clipped = np.clip(hdvi, -3, 3)

        return {
            "hdvi": hdvi_clipped,
            "classification": self.classify(hdvi_clipped),
            "spi": spi_value,
            "spei": spei_value,
            "vhi_norm": vhi_norm,
            "smi_norm": smi_norm,
        }

    @staticmethod
    def classify(hdvi: np.ndarray) -> np.ndarray:
        """طبقه‌بندی شدت خشکسالی"""
        return np.select(
            [hdvi > 0, hdvi > -1, hdvi > -2],
            ["normal", "mild_drought", "moderate_drought"],
            default="severe_drought",
        )

    def validate_against_reference(
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.5,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["hdvi"]))

        # HDVI range is [-3, 3], so tolerance is absolute
        absolute_error = abs(computed_value - reference_output)

        return ValidationResult(
            passed=absolute_error <= tolerance,
            metric_name="HDVI",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=absolute_error,
            reference_source=reference_source,
        )
