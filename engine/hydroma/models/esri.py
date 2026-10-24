"""
ESRI — EcoNojin Salinity Risk Index

Spectral band-ratio sub-index + soil EC + irrigation management.

Reference: Ayers & Westcot (1985) FAO-29 for the leaching requirement only.
The band-ratio sub-index and the three-factor composition have no published
source -- see `ESRI.salinity_index_s2`.
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np

from .base import ScientificModel, ValidationResult, validate_finite


class ESRI(ScientificModel):
    """EcoNojin Salinity Risk Index"""

    name = "ESRI"
    version = "1.0.0"
    description = "Salinity Risk Index (spectral + soil + irrigation)"

    #: The leaching requirement is FAO-29. The spectral sub-index, the two
    #: normalisations, the weights and the leaching-deficit factor are this
    #: project's own, so the record is a composite and not a standard.
    PROVENANCE: ClassVar[str] = "composite"

    REFERENCES: ClassVar[dict] = {
        "Ayers1985": "Ayers, R.S. & Westcot, D.W. (1985). Water quality for agriculture. FAO Irrigation and Drainage Paper 29.",
        "Richards1954": (
            "Richards, L.A. (1954). Diagnosis and improvement of saline and alkali "
            "soils. USDA Agriculture Handbook 60. Cited here for the soil "
            "salinity context only: this module implements no expression from it."
        ),
    }

    # The ScientificModel ABC declares **inputs / dict-based signatures; the
    # concrete model API in this package is a positional typed inputs object.
    # Unifying the two is a cross-hierarchy API decision, so the divergence is
    # marked rather than silently rewritten here.
    def validate_inputs(  # type: ignore[override]
        self,
        blue,
        red,
        nir,
        swir,
        ec_soil_dsm,
        ec_irrigation_dsm,
    ) -> tuple[bool, list[str]]:
        errors = validate_finite(
            "ESRI",
            {
                "blue": blue,
                "red": red,
                "nir": nir,
                "swir": swir,
                "ec_soil_dsm": ec_soil_dsm,
                "ec_irrigation_dsm": ec_irrigation_dsm,
            },
        )
        if errors:
            return False, errors
        for band_name, band in [("blue", blue), ("red", red), ("nir", nir), ("swir", swir)]:
            if np.any(band < 0) or np.any(band > 1):
                errors.append(f"{band_name} band reflectance out of range [0, 1]")
        if ec_soil_dsm < 0 or ec_soil_dsm > 30:
            errors.append("Soil EC out of range [0, 30] dS/m")
        if ec_irrigation_dsm < 0 or ec_irrigation_dsm > 10:
            errors.append("Irrigation EC out of range [0, 10] dS/m")
        return len(errors) == 0, errors

    @staticmethod
    def salinity_index_s2(
        blue: np.ndarray, red: np.ndarray, nir: np.ndarray, swir: np.ndarray
    ) -> np.ndarray:
        """Sentinel-2 band-ratio salinity sub-index.

            SI = sqrt(B * R) / [ (N / SW) * (B / R) ]

        NO PUBLISHED SOURCE. A review checked this expression against both
        references this module claims and neither contains it: Ayers & Westcot
        (1985) FAO-29 is an irrigation-water-quality manual and carries no
        band-ratio formula, and Richards (1954) is a soil-physics textbook on
        saline and alkali soils with no remote-sensing content whatsoever.
        Neither paper mentions Sentinel-2, which did not exist in 1954 or
        1985. It is recorded here as this project's own construction rather
        than left attached to two citations it does not come from.

        Replacing it with a ratio that has a source is model work and was not
        done unilaterally: it would change every reported ESRI value. The
        candidates, none of which is a drop-in replacement, are documented in
        the research definition
        `engine/hydroma/formulas/research/__init__.py::esri_salinity_risk`.

        The previous implementation ended with ``np.nan_to_num(si, nan=np.nan)``,
        which replaces NaN with NaN and therefore does nothing -- it reads as an
        intent to sanitise the result while leaving every NaN in place. A genuine
        undefined result is propagated explicitly instead.
        """
        with np.errstate(divide="ignore", invalid="ignore"):
            numerator = np.sqrt(blue * red)
            ratio1 = nir / (swir + 1e-6)
            ratio2 = blue / (red + 1e-6)
            si: np.ndarray = numerator / (ratio1 * ratio2 + 1e-6)
        return si

    @staticmethod
    def leaching_requirement(ec_w: float, ec_e: float) -> float:
        """Leaching requirement, FAO-29 (Ayers & Westcot 1985), after Rhoades (1974).

            LR = ECw / (5 * ECe - ECw)

        ``ec_w`` is the electrical conductivity of the irrigation water and
        ``ec_e`` the target soil saturation-extract conductivity, both dS/m.
        The factor 5 multiplies the **soil** term: it converts the
        saturation-extract EC the crop is judged against into the average
        root-zone salinity that actually has to be held down, so omitting it
        over-estimates LR by roughly a factor of five.

        CITATION CORRECTION 2026-10-01. The docstring here said "FAO-32", and
        no FAO-32 exists in this repository or in the FAO Irrigation and
        Drainage Paper series. The cited work is FAO-29.

        VERIFIED, NOT CHANGED 2026-10-01. A review proposed rewriting the
        denominator as ``5 * ec_w - ec_e``, i.e. moving the factor 5 onto the
        irrigation-water term. That was rejected on two grounds. FAO-29 places
        the factor on the soil term, which is what this function already
        does, and `engine/hydroma/soil/salinity.py:190-194` and the catalogue
        record for `esri_salinity_risk`
        (`engine/hydroma/formulas/catalog.py:801`) both state it that way.
        Numerically the proposal is also absurd for this model's own
        defaults: with ECw = 0.5 and ECe = 2.0 dS/m it returns
        0.5 / (2.5 - 2.0) = 1.0, i.e. every millimetre of applied water must
        percolate, to hold soil that is already eight times saltier than the
        water. The published relation gives 0.5 / (10.0 - 0.5) = 0.0526, a
        5 % extra leaching, which is the agronomically expected answer.

        Returns a fraction of the applied irrigation water, in [0, 1]. A
        non-positive denominator means the irrigation water is saltier than a
        fifth of the target soil EC, so no achievable leaching fraction exists
        and 1.0 is reported.
        """
        if ec_w <= 0:
            return 0.0
        denominator = 5 * ec_e - ec_w
        if denominator <= 0:
            return 1.0
        return min(1.0, ec_w / denominator)

    def compute(  # type: ignore[override]
        self,
        blue: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir: np.ndarray,
        ec_soil_dsm: float = 2.0,
        ec_irrigation_dsm: float = 0.5,
        actual_leaching_fraction: float = 0.2,
        weights: tuple[float, float, float] = (0.3, 0.5, 0.2),
    ) -> dict[str, Any]:
        """Compute ESRI"""
        alpha, beta, gamma = weights

        si = self.salinity_index_s2(blue, red, nir, swir)
        si_norm = np.clip(si / 10, 0, 1)

        ec_norm = np.clip(ec_soil_dsm / 16, 0, 1)

        lr_required = self.leaching_requirement(ec_irrigation_dsm, ec_soil_dsm)
        lr_deficit = np.clip(lr_required - actual_leaching_fraction, 0, 1)

        esri = alpha * si_norm + beta * ec_norm + gamma * lr_deficit
        # Classify the value that is actually returned. This read the UNCLIPPED
        # `esri` while returning `np.clip(esri, 0, 1)`, so the number and the
        # label in one result dict were derived from different quantities.
        #
        # HOW REACHABLE WAS THAT? Checked, 2026-10-01: with non-negative
        # weights it is not. si_norm, ec_norm and lr_deficit are each clipped
        # into [0, 1] and each carries a non-negative weight, so the raw sum
        # cannot go below 0. Above 1 it can, and clipping it to 1.0 leaves the
        # label "severe", which is also what classify() returns for any raw
        # value >= 0.8 -- the two bands only diverge if the raw sum drops below
        # 0, which needs a negative weight. The fixture's own default weights
        # cannot reach it. Fixed anyway because the two lines must not read
        # different variables: it costs one clip, and a caller supplying
        # `weights` is not bound by the defaults.
        esri_clipped = np.clip(esri, 0, 1)

        return {
            "esri": esri_clipped,
            "classification": self.classify(esri_clipped),
            "salinity_index": si,
            "ec_norm": ec_norm,
            "leaching_requirement": lr_required,
            "leaching_deficit": lr_deficit,
        }

    @staticmethod
    def classify(esri: np.ndarray) -> np.ndarray:
        """طبقه‌بندی ریسک شوری"""
        return np.select(
            [esri < 0.3, esri < 0.6, esri < 0.8], ["low", "moderate", "high"], default="severe"
        )

    def validate_against_reference(
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.15,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["esri"]))

        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)

        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="ESRI",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
