"""
HEC-RAS (Hydrologic Engineering Center's River Analysis System) Model Integration.

This module provides functions to simulate hydraulic flow and flood extent
using the HEC-RAS model based on channel geometry and boundary conditions.
It can now receive inputs from the engineering design modules.
"""

import datetime
from typing import Any

from contracts.simulation import HECRASInput, HECRASOutput

# Placeholder for the actual HEC-RAS model execution.
# This would typically involve calling an external executable or API,
# preparing input files (e.g., .prj), and parsing output files (e.g., .hdf).
# For now, we implement a simplified calculation.


class HecRasUnavailable(RuntimeError):
    """HEC-RAS is not installed, so no hydraulic result can be produced.

    Raised instead of returning invented numbers. A caller that receives this
    can distinguish "the model did not run" from "the model ran and said the
    structure is safe", which is the distinction that matters when the answer
    is a flood extent and a safety factor.
    """


def simulate_hecras(input_data: HECRASInput) -> HECRASOutput:
    """Run HEC-RAS on the supplied geometry.

    HEC-RAS is an external executable and is not bundled. When it is absent the
    only correct answer is to say so.

    This function used to fabricate a full result set from the input shape: a
    water-surface profile that ramped from 100.0 m, velocities that divided a
    flow RATE by ten, a bed shear computed as rho/2 * v^2 rather than rho * v^2,
    a hard-coded flood extent of 5.2 km2, and a hard-coded
    `{"status": "safe", "factor_of_safety": 1.8}`. It also ignored the
    `initial_conditions` it was handed and started the profile 4 m above them.
    `HECRASOutput` carries no `data_source` field, so none of that was
    distinguishable from a real run by anything downstream.

    Measured, with the fabricated values removed, a caller that had been
    reading "levee is safe, 1200 people affected" now gets an exception it can
    handle and an orchestrator step that reports `not_computed`.

    Raises:
        HecRasUnavailable: always, until a HEC-RAS binary is wired in.
    """
    raise HecRasUnavailable(
        "HEC-RAS executable not available; no hydraulic result was computed. "
        "Wiring a real run needs a project file, steady or unsteady flow data, "
        "and an external binary, none of which this function can synthesise."
    )


def prepare_hecras_input_from_design(structure_design: dict[str, Any]) -> HECRASInput:
    """
    Prepares HEC-RAS input from an engineering structure design.

    Args:
        structure_design: Output from an engineering design function (e.g., design_trapezoidal_channel).

    Returns:
        An HECRASInput object ready for simulation.
    """
    # This function maps the design outputs to HEC-RAS specific inputs.
    # Example mapping for a trapezoidal channel
    if structure_design.get("shape") == "trapezoidal":
        # Map channel geometry
        geometry = {
            "type": "trapezoidal",
            "bottom_width_m": structure_design["bottom_width_m"],
            "depth_m": structure_design["depth_m"],
            "side_slope_H_V": structure_design["side_slope_H_V"],
            "length_m": 1000,  # Example length
            "roughness_n": structure_design["manning_n"],
        }

        # Example boundary conditions based on design flow
        boundary_conditions = {
            "upstream_flow_m3s": [structure_design["discharge_m3_s"]] * 24,  # 24 hourly steps
            "downstream_stage_m": 95.0,  # Example tailwater
        }

        # Example initial conditions
        initial_conditions = {"water_surface_m": 96.0}

        return HECRASInput(
            land_profile_id="PLACEHOLDER_ID",  # Should come from design context
            channel_geometry=geometry,
            boundary_conditions=boundary_conditions,
            initial_conditions=initial_conditions,
            start_date=datetime.date.today(),  # Or from design context
            end_date=datetime.date.today() + datetime.timedelta(days=1),
            time_step="hourly",
        )

    # Add mappings for other structure types (weir, culvert, etc.)
    # This is a simplified example; a full implementation would be more complex.
    raise NotImplementedError(
        f"HeC-RAS input preparation not yet implemented for structure type: {structure_design.get('type', 'unknown')}"
    )
