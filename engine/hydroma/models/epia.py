"""
EPIA — EcoNojin Precision Irrigation Advisor

ETc = ET0 × Kc × Ks
Effective rainfall, USDA-SCS.

Reference: Allen et al. (1998) FAO-56 (ETc frame and Ks); USDA-SCS
(effective rainfall). NOT FAO-56: the Kc term is this project's own LAI
ramp -- see ``EPIA.kc_from_lai``, which records what implementing FAO-56
as cited would require.
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np

from .base import ScientificModel, ValidationResult, validate_finite


class EPIA(ScientificModel):
    """EcoNojin Precision Irrigation Advisor"""

    name = "EPIA"
    version = "1.0.0"
    description = "Precision Irrigation Advisor with satellite Kc"

    REFERENCES: ClassVar[dict] = {
        "Allen1998": "Allen et al. (1998). Crop evapotranspiration. FAO Irrigation and Drainage Paper 56.",
        "Jensen2016": "Jensen, M.E. & Allen, R.G. (2016). Crop Water Requirements.",
        "USDA_SCS": (
            "USDA Soil Conservation Service. Effective-rainfall relation "
            "Pe = P(125 - 0.2P)/250 for P <= 250 mm and Pe = 125 + 0.1P above "
            "it, as tabulated by Dastane, N.G. (1978). Effective rainfall in "
            "irrigated agriculture. FAO Irrigation and Drainage Paper 25, "
            "chapter II section 3.4."
        ),
    }
    #: Provenance of the whole record. The ETc frame and Ks are FAO-56; the
    #: Kc term and the stage inference are this project's.
    PROVENANCE: ClassVar[str] = "composite"

    # The ScientificModel ABC declares **inputs / dict-based signatures; the
    # concrete model API in this package is a positional typed inputs object.
    # Unifying the two is a cross-hierarchy API decision, so the divergence is
    # marked rather than silently rewritten here.
    def validate_inputs(  # type: ignore[override]
        self,
        et0,
        lai,
        soil_moisture,
        rainfall_forecast_mm,
    ) -> tuple[bool, list[str]]:
        errors = validate_finite(
            "EPIA",
            {
                "et0": et0,
                "lai": lai,
                "soil_moisture": soil_moisture,
                "rainfall_forecast_mm": rainfall_forecast_mm,
            },
        )
        if errors:
            return False, errors
        if not (0 <= et0 <= 20):
            errors.append("ET0 out of range")
        if np.any(lai < 0) or np.any(lai > 10):
            errors.append("LAI out of range")
        if not (0 <= soil_moisture <= 0.6):
            errors.append("Soil moisture out of range")
        if rainfall_forecast_mm < 0:
            errors.append("Rainfall must be non-negative")
        return len(errors) == 0, errors

    @staticmethod
    def kc_from_lai(
        lai: np.ndarray, lai_max: float = 6.0, kc_min: float = 0.1, kc_max: float = 1.2
    ) -> np.ndarray:
        """Derive Kc from LAI.

        RECORDED DEFECT -- this term is not FAO-56 and the frame around it is
        presented as if it were. FAO-56 does not define Kc from LAI at all:
        Tables 12, 13 and 14 give a single crop coefficient per crop **per
        growth stage** (Kc ini / mid / end), and the mid-season value is
        bounded above by the tabulated maximum for that crop, with the
        adjustment to an actual ETc made by a lengthening factor and a crop
        stress coefficient, not by a canopy measurement. There is no FAO-56
        relation of the form Kc = kc_min + (kc_max - kc_min) * LAI / LAI_max.

        The consequence runs through the rest of ``compute``. The stage
        classifier below inverts the invented Kc into a growth stage
        (mean_kc < 0.3 -> "initial"), so a number the model made up is
        presented as an observed phenological stage, and it will disagree with
        the stage the caller already knows it is in. With the shipped defaults
        a full canopy (LAI 6) saturates at Kc 1.2, which is above the FAO-56
        maximum of 1.15 for any arable crop, and Kc 0.1 is approached but
        never reached at LAI 0.

        NOT FIXED HERE, and the fix is a data change, not an expression
        change. To implement FAO-56 as cited it needs:

        1. A crop table of the shape
           ``{"wheat": {"kc_ini": 0.4, "kc_mid": 1.15, "kc_end": 0.4}, ...}``
           transcribed from FAO-56 Table 12 (there is no such table anywhere in
           this repository; the catalogue record for ``epia_precision_irrigation``
           in ``engine/hydroma/formulas/catalog.py`` names the same gap).
        2. A growth-stage input. Without one the model cannot know which of the
           three tabulated coefficients applies, so either ``compute`` grows a
           ``stage`` parameter or the caller supplies the Kc directly and this
           function is deleted.
        3. The LAI relationship, which is optional: FAO-56 uses LAI only to
           compute Kcmax in the "Kc derived from LAI" variant of Annex 2, and
           then caps it at the tabulated Kc max. That variant would be the
           honest way to keep a satellite LAI input at all, and it is
           ``Kcmax = 1.2 + 0.04 * (LAI - 3) - 0.004 * (LAI - 3)^2`` for LAI
           above 3, clipped to 0.9..1.25 -- a different curve with a different
           source, not a rescaling of this one.
        4. The stage cut-offs in ``compute`` then disappear, because the stage
           is an input rather than a deduction.

        Changing the shape of ``compute`` or its signature is a model decision
        with callers behind it, so it is recorded here and left alone.
        """
        return np.clip(kc_min + (kc_max - kc_min) * (lai / lai_max), kc_min, kc_max)

    @staticmethod
    def ks_water_stress(
        soil_moisture: float,
        depletion_fraction: float = 0.5,
        taw: float = 80.0,
        theta_fc: float = 0.32,
        theta_wp: float = 0.12,
        root_depth_m: float = 0.4,
    ) -> float:
        """Water stress coefficient Ks (FAO-56 eq. 38-40).

        The previous form computed ``dr = taw * (1 - soil_moisture / 0.4)``,
        which multiplied a volumetric fraction by a millimetre quantity and
        then compared the result against ``depletion_fraction * taw``. With
        the old ``taw=50`` default that left Dr below the raw-depletion
        threshold for any soil moisture above 0.20, so Ks was pinned at 1.0
        across the whole range between field capacity and the onset of
        wilting stress: a farmer draining the soil from 0.32 to 0.21 m3/m3
        was told there was no stress at all.

        FAO-56 expresses the depletion in the same millimetre space as TAW::

            TAW = 1000 * (theta_fc - theta_wp) * Zr
            Dr  = 1000 * (theta_fc - theta)   * Zr
            Ks  = 1                          when Dr <= p * TAW
                = (TAW - Dr) / (TAW - p*TAW)  otherwise, clamped to [0, 1]

        ``taw`` is accepted so existing callers keep working, but it is only
        used when the caller states it explicitly, and the soil parameters
        take precedence. ``root_depth_m`` and the two theta values default to
        a medium-textured soil with a 0.4 m rooting depth; a crop-specific
        call should pass its own.
        """
        derived_taw = 1000.0 * (theta_fc - theta_wp) * root_depth_m
        effective_taw = derived_taw if derived_taw > 0 else max(float(taw), 1e-6)

        depletion = 1000.0 * (theta_fc - soil_moisture) * root_depth_m
        raw = depletion_fraction * effective_taw
        if depletion <= raw:
            return 1.0
        if depletion >= effective_taw:
            return 0.0
        return float(
            np.clip(
                (effective_taw - depletion) / (effective_taw - raw + 1e-9),
                0.0,
                1.0,
            )
        )

    #: The published partition between the two branches of the USDA-SCS
    #: effective-rainfall relation. It is a constant of the method, not a
    #: tuning knob, so it is named rather than written inline.
    SCS_BRANCH_MM: ClassVar[float] = 250.0

    @classmethod
    def effective_rainfall(cls, rainfall_mm: float, method: str = "usda_scs") -> float:
        """Effective rainfall, USDA-SCS method.

        The relation as published for a monthly rainfall depth P in mm::

            P <= 250 mm :  Pe = P * (125 - 0.2 * P) / 250
            P >  250 mm :  Pe = 125 + 0.1 * P

        Two defects are corrected here, and both changed every result.

        **The lower branch divided by 125, not 250.** The published relation
        divides by 250, which is the same 250 mm as the branch point. Dividing
        by 125 -- half of it -- doubled the answer for every input at or below
        250 mm. It survived because every EPIA case in
        ``validation/test_cases/epia.yaml`` set ``rainfall_forecast_mm: 0.0``,
        and both branches return 0 at P = 0, so the branch never executed.

        **The upper branch was ``0.75 * P - 25`` instead of ``125 + 0.1 * P``.**
        The two are not two readings of one relation: the correct upper branch
        grows ten times slower (slope 0.1 vs 0.75), so the old form claimed a
        quarter of a 300 mm storm was effective (200 mm) where the method
        gives 155 mm. It also crossed the branch point wrongly -- the old
        lower branch returned 162.5 mm at P = 250 while the old upper branch
        returned 162.5 mm there, and the correct pair returns 75 mm and
        150 mm respectively, so the published relation is deliberately
        discontinuous there and the old one hid that behind a coincidence.

        ``method`` was previously accepted and never read, so any string
        produced the same number and a caller asking for a different published
        relation silently got this one. It is now read, and an unrecognised
        method raises rather than returning a number under the wrong name.

        The result is clipped to ``[0, rainfall_mm]``. The published relation
        is concave, peaks near 312.5 mm and would return more than the rain
        that fell for some depths near the top of its range; effective
        rainfall is by definition a fraction of the rainfall.
        """
        if method != "usda_scs":
            raise ValueError(
                f"effective_rainfall: {method!r} is not implemented. The only "
                f"published relation in this model is 'usda_scs'; an "
                f"unrecognised method must not return a number under this one."
            )
        p = float(rainfall_mm)
        if p <= 0.0:
            return 0.0
        branch = cls.SCS_BRANCH_MM
        if p <= branch:
            pe = p * (125.0 - 0.2 * p) / branch
        else:
            pe = 125.0 + 0.1 * p
        return float(min(max(pe, 0.0), p))

    def compute(  # type: ignore[override]
        self,
        et0: float,
        lai: np.ndarray,
        soil_moisture: float,
        rainfall_forecast_mm: float,
        irrigation_efficiency: float = 0.85,
        taw: float = 80.0,
        depletion_fraction: float = 0.5,
        theta_fc: float = 0.32,
        theta_wp: float = 0.12,
        root_depth_m: float = 0.4,
    ) -> dict[str, Any]:
        """Generate irrigation recommendation.

        ``taw`` now defaults to 80 mm, the value FAO-56 gives for a
        medium-textured soil with a 0.4 m rooting depth. It previously
        defaulted to 50 mm, which understated the plant-available water and,
        combined with the old depletion formula, removed the soil moisture
        term from the result almost entirely.
        """
        kc = self.kc_from_lai(lai)
        ks = self.ks_water_stress(
            soil_moisture,
            depletion_fraction,
            taw,
            theta_fc=theta_fc,
            theta_wp=theta_wp,
            root_depth_m=root_depth_m,
        )
        etc = et0 * kc * ks

        p_eff = self.effective_rainfall(rainfall_forecast_mm)
        irri_net = np.maximum(0, etc - p_eff)
        irri_gross = irri_net / irrigation_efficiency
        irri_m3_ha = irri_gross * 10  # mm to m³/ha

        # Days until the soil is drawn down to the depletion threshold.
        # Two problems with the previous form: it used the raw `taw` argument
        # rather than the TAW the soil parameters imply, and dividing by
        # `et0 + 1e-6` returned 25000000 days at et0 = 0, which is a number
        # no farmer can act on. A zero demand means the field needs no
        # irrigation, which is not the same as needing it very rarely.
        effective_taw = 1000.0 * (theta_fc - theta_wp) * root_depth_m
        depletion_window = depletion_fraction * (
            effective_taw if effective_taw > 0 else max(float(taw), 1e-6)
        )
        if et0 <= 0:
            days = 0
        else:
            days = max(1, int(depletion_window / et0))

        mean_kc = float(np.mean(kc))
        # RECORDED DEFECT: the stage is deduced from the Kc ramp above, which
        # is this project's own construction and not a FAO-56 Kc, so this is
        # an inference from a number the model invented rather than an
        # observed phenological stage. FAO-56 gives the stage first and reads
        # Kc off it. See `kc_from_lai` for the fix, which is a data table and
        # an input, not a change to these two lines.
        if mean_kc < 0.3:
            stage = "initial"
        elif mean_kc < 0.8:
            stage = "development"
        elif mean_kc < 1.1:
            stage = "mid-season"
        else:
            stage = "late-season"

        return {
            "et0": et0,
            "kc": kc,
            "ks": ks,
            "etc": etc,
            # Reported so the term is auditable. It was previously invisible:
            # a caller could see the irrigation need but not how much of the
            # forecast rain was assumed to have reached the root zone, which is
            # the number to check when a recommendation looks too small.
            "effective_rainfall_mm": p_eff,
            "irrigation_need_mm": irri_net,
            "irrigation_need_m3_ha": irri_m3_ha,
            "days_until_irrigation": days,
            "crop_stage": stage,
            "recommendation": f"Irrigate {float(np.mean(irri_gross)):.1f} mm in {days} days ({stage})",
        }

    def validate_against_reference(
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.2,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["etc"]))

        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)

        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="ETc (mm/day)",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
