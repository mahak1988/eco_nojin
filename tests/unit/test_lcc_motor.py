"""Land Capability Classification motor tests.

This module replaced ``services/scientific_motors/test_lcc.py``. That file sat
inside the production package, so it was shipped in builds and pytest collected
its module-level ``async def test_lcc()`` as a genuine test. It contained no
assertion of any kind — it was an ``asyncio.run`` smoke script that logged a
class distribution — so pytest recorded a vacuous pass.

Everything the old script printed is asserted here instead.
"""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from services.scientific_motors.base import MotorParameters, MotorStatus, MotorType
from services.scientific_motors.land_capability import LandCapabilityMotor


def _raster(values: np.ndarray, shape: tuple[int, int]) -> xr.DataArray:
    """Build a synthetic raster on a fixed lon/lat grid."""
    coords = {
        "y": np.linspace(35.0, 35.1, shape[0]),
        "x": np.linspace(51.0, 51.1, shape[1]),
    }
    return xr.DataArray(values, dims=["y", "x"], coords=coords)


def _field(
    shape: tuple[int, int] = (20, 20),
    dem_range: tuple[float, float] = (1000.0, 1500.0),
    soil_depth_range: tuple[float, float] = (20.0, 120.0),
) -> dict[str, xr.DataArray]:
    rng = np.random.default_rng(20260928)
    return {
        "dem": _raster(rng.uniform(*dem_range, shape), shape),
        "soil_depth": _raster(rng.uniform(*soil_depth_range, shape), shape),
        "soil_texture": _raster(rng.integers(1, 12, shape).astype(float), shape),
    }


def _params(scenario: str) -> MotorParameters:
    return MotorParameters(
        start_date="2026-01-01",
        end_date="2026-12-31",
        time_step="daily",
        scenario_name=scenario,
    )


class TestLandCapabilityMotor:
    async def test_completes_and_declares_itself(self):
        motor = LandCapabilityMotor()

        result = await motor.execute(_field(), _params("lcc_unit"))

        assert result.status is MotorStatus.COMPLETED
        assert result.motor_type is MotorType.LAND_CAPABILITY
        assert result.error_message is None
        assert result.run_id.startswith("LCC_")

    async def test_class_raster_matches_the_input_grid(self):
        shape = (16, 16)
        motor = LandCapabilityMotor()

        result = await motor.execute(_field(shape), _params("lcc_grid"))

        lcc = result.outputs["lcc_class"]
        assert lcc.dims == ("y", "x")
        assert lcc.shape == shape

    async def test_classes_stay_inside_the_usda_range(self):
        motor = LandCapabilityMotor()

        result = await motor.execute(_field(), _params("lcc_range"))

        classes = result.outputs["lcc_class"].values
        assert classes.min() >= 1
        assert classes.max() <= 8
        assert np.all(np.isin(classes, np.arange(1, 9)))

    async def test_distribution_percentages_account_for_every_pixel(self):
        motor = LandCapabilityMotor()
        field = _field()

        result = await motor.execute(field, _params("lcc_distribution"))

        total_pixels = int(result.summary["total_pixels"])
        assert total_pixels == field["dem"].size

        distribution = result.summary["distribution"]
        assert distribution, "a classification must report a class distribution"
        assert sum(int(entry["pixels"]) for entry in distribution.values()) == total_pixels
        assert sum(float(entry["percent"]) for entry in distribution.values()) == pytest.approx(
            100.0, abs=0.5
        )

    async def test_every_reported_class_carries_a_usda_description(self):
        motor = LandCapabilityMotor()

        result = await motor.execute(_field(), _params("lcc_descriptions"))

        descriptions = LandCapabilityMotor.LCC_DESCRIPTIONS
        for class_key, entry in result.summary["distribution"].items():
            class_number = int(class_key.split()[-1])
            assert entry["description"] == descriptions[class_number]
            assert 1 <= class_number <= 8

    async def test_cultivable_percent_is_consistent_with_its_own_classes(self):
        """Classes I-IV are cultivable; the summary must agree with the raster."""
        motor = LandCapabilityMotor()

        result = await motor.execute(_field(), _params("lcc_cultivable"))

        classes = result.outputs["lcc_class"].values
        from_raster = float(np.mean((classes >= 1) & (classes <= 4)) * 100.0)
        assert result.summary["cultivable_percent"] == pytest.approx(from_raster, abs=0.01)

    async def test_suitable_crops_are_offered_for_the_classes_produced(self):
        motor = LandCapabilityMotor()

        result = await motor.execute(_field(), _params("lcc_crops"))

        suitable = result.outputs["suitable_crops"]
        assert suitable, "the motor must report crops for the classes it assigned"
        # Keys are ints in Python and only become strings on JSON round-trip.
        present = set(np.unique(result.outputs["lcc_class"].values).tolist())
        assert present <= set(suitable)
        assert all(crops for crops in suitable.values())

    async def test_missing_required_input_fails_loudly(self):
        """A missing raster is a FAILED result, not a silently classified grid."""
        motor = LandCapabilityMotor()
        field = _field()
        del field["soil_depth"]

        result = await motor.execute(field, _params("lcc_missing"))

        assert result.status is MotorStatus.FAILED
        assert "soil_depth" in (result.error_message or "")
        assert not result.outputs

    def test_required_inputs_are_the_ones_execute_demands(self):
        motor = LandCapabilityMotor()
        required = {req.name for req in motor.get_input_requirements() if req.required}

        assert required == {"dem", "soil_depth", "soil_texture"}
        assert motor.validate_inputs(_field()) is True
        assert motor.validate_inputs({"dem": None}) is False

    def test_declared_outputs_cover_what_execute_returns(self):
        motor = LandCapabilityMotor()

        declared = {out.name for out in motor.get_outputs()}

        assert declared == {
            "lcc_class",
            "lcc_description",
            "limiting_factor",
            "suitable_crops",
        }
