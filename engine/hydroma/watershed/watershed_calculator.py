"""Preliminary screening estimate for a check dam.

Status
------
**Screening only. Not a design.** This module used to export a function called
``design_check_dam``, identical in name to the real one in
``engine/hydroma/watershed/calculator.py``, in the same package, with different
physics and a disjoint result schema, and the only production caller,
``adapters/hydroma_adapter.py``, was wired to this one.

It is renamed here rather than deleted, and the name now says what it is. For
an actual design use ``engine.hydroma.watershed.calculator.design_check_dam``,
which implements the FAO manual: sediment yield, Brune trap efficiency,
trapezoidal storage, a broad-crested spillway at Cd = 1.7 and freeboard.

The coefficients now agree with that design
-------------------------------------------
Two constants made this estimate answer differently from the design it appears
to implement, with nothing in the output saying so. Both are now the canonical
values, and the reason is recorded rather than dropped:

* **Weir coefficient.** Was 1.84. No source for it exists anywhere in the
  repository. It is now 1.7, the value in SI for a broad-crested weir in the
  FAO Watershed Management Field Manual, which is the source the canonical
  design cites for the same equation.
* **Rational-method runoff coefficient.** Was ``0.6 + (slope_pct / 100) * 0.2``,
  so a 30 % slope reported 10 % more runoff and a 10 % larger peak flow than a
  flat 0.6. The rational-method C is a land-use property, tabulated per
  surface; neither FAO-56 nor the FAO Watershed Management Field Manual gives
  a linear-in-slope form for it, and no source for this particular linear term
  exists in the repository. It is therefore removed rather than carried under a
  citation it does not have. Both functions now use a flat C = 0.6, and in both
  it is a design input to be site-calibrated, not a result.

Result schema
-------------
Every key this estimate returns that the canonical design also returns now
carries the canonical's name for the same physical quantity, so a caller can
move between the two without translating:

    screening (None)      canonical (str)
    structure_type        structure_type
    dam_height_m          dam_height_m
    dam_length_m          dam_length_m
    dam_volume_m3         dam_volume_m3
    materials             materials
    peak_flow_m3s         peak_flow_m3s
    spillway_width_m      spillway_width_m
    design_standard       design_standard

The estimate is a **subset**. The canonical's storage, trap-efficiency, spacing
and cost keys have no screening counterpart and are simply absent, which a
caller can detect with a key lookup; that is a legitimate shape for a
screening tool. What it is not entitled to do is rename a quantity, and it
previously did: the same numbers came back as ``height_m``, ``width_m``,
``length_m``, ``estimated_discharge_m3s``, ``material_estimate_m3`` and
``material``, none of which is a name the canonical uses. Those six names are
gone.

Three keys are the estimate's own and mark it as what it is: ``screening_estimate``,
``use_instead`` and ``notes``. ``design_standard`` is present and ``None``,
which is itself the marker. The result is not accepted by any validation layer.

Known differences from the canonical that remain
------------------------------------------------
* ``rainfall_mm`` is a design rainfall INTENSITY in mm/hour here, whereas the
  canonical takes a storm total in mm and divides it by ``storm_duration_h``.
  The same number therefore means a different storm in the two signatures, and
  the peak flows differ by that ratio, about 6x for the canonical default of a
  6-hour storm. This is an input-semantics difference and is not reconciled
  here; closing it needs a signature change on both sides.
* ``dam_volume_m3`` is a screening proxy, ``height x length x 0.5``, with no
  cross-section basis. The canonical solves a trapezoidal section.
* A fixed 0.3 m design head and 0.3 m freeboard, against a head of 0.4 x the
  solved dam height and a freeboard that grows past 3 m.
* No sediment yield, no storage requirement, no trap efficiency, and no spillway
  sizing beyond the weir itself.
"""

from typing import Any

#: Weir coefficient, dimensionless. Broad-crested weir in SI: 1.7 in the FAO
#: Watershed Management Field Manual, the source the canonical design in
#: engine.hydroma.watershed.calculator cites for the same equation. This module
#: used 1.84 and cited nothing.
WEIR_COEFFICIENT = 1.7

#: Rational-method runoff coefficient, dimensionless. Flat, and the same value
#: the canonical design uses. This module used ``0.6 + (slope_pct/100) * 0.2``,
#: a linear slope term with no source in the repository and none in the FAO
#: sources this package cites; it is removed rather than attributed.
RUNOFF_COEFFICIENT = 0.6

#: Assumed head over the weir [m]. Fixed, not derived.
DESIGN_HEAD_M = 0.3

#: Freeboard above the design head [m]. Fixed, not derived.
FREEBOARD_M = 0.3


def design_check_dam_screening(
    slope_pct: float, area_m2: float, rainfall_mm: float
) -> dict[str, Any]:
    """Preliminary check-dam screening estimate. Not a design.

    Args:
        slope_pct: average slope of the area, percent. Retained in the
            signature for callers that pass a site description; it no longer
            adjusts any coefficient, because the linear slope term it used to
            drive had no source.
        area_m2: contributing area upstream, square metres
        rainfall_mm: design rainfall intensity, mm/hour. Note this is an
            intensity, where the canonical design takes a storm total in mm and
            divides it by its storm duration.

    Returns:
        A screening proposal, carrying the canonical design's key names for
        every quantity it computes and flagged with ``screening_estimate`` so a
        caller cannot mistake it for the FAO design. Use
        ``engine.hydroma.watershed.calculator.design_check_dam`` for that.
    """
    rainfall_m_per_hour = rainfall_mm / 1000.0
    effective_area_m2 = max(area_m2, 1.0)
    peak_flow_m3_per_sec = (RUNOFF_COEFFICIENT * rainfall_m_per_hour * effective_area_m2) / 3600.0

    weir_length_m = peak_flow_m3_per_sec / (WEIR_COEFFICIENT * (DESIGN_HEAD_M**1.5))

    dam_height_m = DESIGN_HEAD_M + FREEBOARD_M
    # Screening proxy for the built volume, not a solved trapezoidal section.
    material_volume_m3 = dam_height_m * weir_length_m * 0.5

    return {
        # --- keys shared with watershed.calculator.design_check_dam ---
        "structure_type": "check_dam",
        "dam_height_m": round(dam_height_m, 2),
        # The estimate is a single weir wall, so the dam length and the spillway
        # width are the same solved number. The canonical sizes them separately
        # from the channel geometry.
        "dam_length_m": round(weir_length_m, 2),
        "dam_volume_m3": round(material_volume_m3, 2),
        "materials": ["concrete"],
        "peak_flow_m3s": round(peak_flow_m3_per_sec, 4),
        "spillway_width_m": round(weir_length_m, 2),
        "design_standard": None,
        # --- this estimate's own keys ---
        "screening_estimate": True,
        "use_instead": "engine.hydroma.watershed.calculator.design_check_dam",
        "notes": (
            "Screening estimate only, not a design. A detailed engineering study "
            "is required for construction. This module omits sediment yield, "
            "storage volume, trap efficiency and spillway sizing, fixes the weir "
            "head and freeboard, and approximates the built volume as "
            "height x length x 0.5 with no cross-section basis. Use "
            "engine.hydroma.watershed.calculator.design_check_dam for a design."
        ),
    }


if __name__ == "__main__":
    print(design_check_dam_screening(slope_pct=15.0, area_m2=5000.0, rainfall_mm=50.0))
