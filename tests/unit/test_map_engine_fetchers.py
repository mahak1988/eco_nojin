"""Map-engine motor coverage, moved out of ``services/``.

This module replaced ``services/map_engine/test_hydroma_motors.py``. That file
sat inside the production package, so it was shipped in builds and pytest
collected its two module-level ``test_*`` functions as genuine tests. Neither
had a single assertion: both were ``__main__`` smoke scripts whose output went
to a structlog logger, so pytest recorded three vacuous passes.

The code under test is unchanged and still exercised; what moved is the
*assertion*. Every test below checks a value the motor computed. The
``sys.path.insert(0, ".")`` import side effect is gone: the repo root is
already importable because pytest runs from the project root, and
``conftest.py``/``pytest.ini`` set ``rootdir`` there.
"""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from services.map_engine.smart_mapper import SmartMapGenerator
from services.scientific_motors.base import MotorParameters, MotorStatus, MotorType
from services.scientific_motors.biofertilizer import BiofertilizerMotor


def _raster(values: np.ndarray, shape: tuple[int, int]) -> xr.DataArray:
    """Build a synthetic raster on a fixed lon/lat grid."""
    coords = {
        "y": np.linspace(35.0, 35.1, shape[0]),
        "x": np.linspace(51.0, 51.1, shape[1]),
    }
    return xr.DataArray(values, dims=["y", "x"], coords=coords)


@pytest.fixture
def deficient_soils() -> dict[str, xr.DataArray]:
    """A low-nitrogen, low-phosphorus, low-organic-matter wheat field."""
    shape = (10, 10)
    rng = np.random.default_rng(20260928)
    return {
        "soil_ph": _raster(rng.uniform(6.5, 7.5, shape), shape),
        "soil_nitrogen": _raster(rng.uniform(80.0, 120.0, shape), shape),
        "soil_phosphorus": _raster(rng.uniform(30.0, 50.0, shape), shape),
        "soil_potassium": _raster(rng.uniform(25.0, 40.0, shape), shape),
        "soil_organic_matter": _raster(rng.uniform(1.0, 2.0, shape), shape),
    }


class TestSmartMapGenerator:
    """Static methods on the smart map generator."""

    def test_ndvi_matches_the_band_formula(self):
        shape = (5, 5)
        red = _raster(np.full(shape, 0.2), shape)
        nir = _raster(np.full(shape, 0.6), shape)

        ndvi = SmartMapGenerator.calculate_ndvi(red, nir)

        # (0.6 - 0.2) / (0.6 + 0.2) = 0.5
        assert float(ndvi.mean()) == pytest.approx(0.5, abs=1e-6)
        assert ndvi.dims == red.dims

    def test_ndvi_stays_inside_the_index_range(self):
        """Red-dominant input still lands on a legal index value.

        (1 - 10) / (1 + 10) is -0.818, not below -1: with positive reflectance
        the ratio is mathematically bounded, so the clip is a guard rather than
        something this test can provoke. It is pinned here because a change to
        the epsilon or the clip would break the bound.
        """
        shape = (4, 4)
        red = _raster(np.full(shape, 10.0), shape)
        nir = _raster(np.full(shape, 1.0), shape)

        ndvi = SmartMapGenerator.calculate_ndvi(red, nir)

        assert float(ndvi.min()) >= -1.0
        assert float(ndvi.max()) <= 1.0
        assert float(ndvi.max()) == pytest.approx(-9.0 / 11.0, abs=1e-6)

    def test_identical_bands_give_near_zero_not_a_division_error(self):
        """The +1e-10 epsilon exists for exactly this case."""
        shape = (3, 3)
        band = _raster(np.zeros(shape), shape)

        ndvi = SmartMapGenerator.calculate_ndvi(band, band)

        assert np.all(np.isfinite(ndvi.values))
        assert float(ndvi.max()) == pytest.approx(0.0, abs=1e-6)

    @pytest.mark.parametrize(
        ("ndvi_value", "expected_class"),
        [
            (0.0, 1),  # bare soil / water
            (0.09, 1),  # still class 1, just below the 0.1 break
            (0.1, 2),  # stressed, lower edge
            (0.3, 3),  # moderate, lower edge
            (0.6, 4),  # healthy, lower edge
            (0.8, 5),  # very healthy
            (0.95, 5),
        ],
    )
    def test_health_class_boundaries(self, ndvi_value, expected_class):
        shape = (2, 2)
        ndvi = _raster(np.full(shape, ndvi_value), shape)

        health = SmartMapGenerator.classify_vegetation_health(ndvi)

        assert set(np.unique(health.values)) == {expected_class}
        assert health.dtype == np.int32

    def test_health_classification_partitions_every_pixel(self):
        shape = (8, 8)
        ndvi = _raster(np.linspace(0.0, 1.0, shape[0] * shape[1]).reshape(shape), shape)

        health = SmartMapGenerator.classify_vegetation_health(ndvi)

        assert health.shape == ndvi.shape
        assert set(np.unique(health.values)) <= {1, 2, 3, 4, 5}

    def test_biomass_uses_the_documented_crop_coefficients(self):
        shape = (4, 4)
        ndvi = _raster(np.full(shape, 0.5), shape)

        wheat = SmartMapGenerator.estimate_biomass(ndvi, crop_type="wheat")
        maize = SmartMapGenerator.estimate_biomass(ndvi, crop_type="maize")

        # wheat: a=8.5, b=0.5  ->  4.75 ; maize: a=12.0, b=0.8  ->  6.8
        assert float(wheat.mean()) == pytest.approx(8.5 * 0.5 + 0.5, abs=1e-6)
        assert float(maize.mean()) == pytest.approx(12.0 * 0.5 + 0.8, abs=1e-6)
        assert float(maize.mean()) > float(wheat.mean())

    def test_unknown_crop_falls_back_to_wheat_rather_than_raising(self):
        shape = (4, 4)
        ndvi = _raster(np.full(shape, 0.4), shape)

        unknown = SmartMapGenerator.estimate_biomass(ndvi, crop_type="sorghum")
        wheat = SmartMapGenerator.estimate_biomass(ndvi, crop_type="wheat")

        assert float(unknown.mean()) == pytest.approx(float(wheat.mean()))


class TestBiofertilizerMotor:
    async def test_completes_and_declares_itself(self, deficient_soils):
        motor = BiofertilizerMotor()
        params = MotorParameters(
            start_date="2026-01-01",
            end_date="2026-12-31",
            time_step="daily",
            scenario_name="biofertilizer_unit",
            custom_params={"crop_type": "wheat"},
        )

        result = await motor.execute(deficient_soils, params)

        assert result.status is MotorStatus.COMPLETED
        assert result.motor_type is MotorType.BIOFERTILIZER
        assert result.error_message is None
        assert result.run_id.startswith("BIOFERT_")

    async def test_reports_a_deficit_for_the_deficient_field(self, deficient_soils):
        motor = BiofertilizerMotor()
        params = MotorParameters(
            start_date="2026-01-01",
            end_date="2026-12-31",
            scenario_name="biofertilizer_deficit",
            custom_params={"crop_type": "wheat"},
        )

        result = await motor.execute(deficient_soils, params)

        # Wheat needs 150 kg N/ha; the field supplies 80-120 plus 20-40 from
        # organic matter, so some pixels clear the bar and some do not. The
        # deficit is floored at zero, never negative.
        nitrogen_deficit = result.outputs["nitrogen_deficit"]
        assert float(nitrogen_deficit.min()) >= 0.0
        assert float(nitrogen_deficit.mean()) > 0.0
        assert float(nitrogen_deficit.max()) > float(nitrogen_deficit.min())

        # Wheat needs 60 kg P/ha and this field holds 30-50 kg/ha, so every
        # pixel is short.
        phosphorus_deficit = result.outputs["phosphorus_deficit"]
        assert float(phosphorus_deficit.min()) > 0.0

    async def test_a_fertile_field_reports_no_deficit(self):
        """The deficit is a difference, not a constant."""
        shape = (10, 10)
        rng = np.random.default_rng(7)
        abundant = {
            "soil_ph": _raster(np.full(shape, 6.8), shape),
            "soil_nitrogen": _raster(rng.uniform(200.0, 260.0, shape), shape),
            "soil_phosphorus": _raster(rng.uniform(80.0, 120.0, shape), shape),
            "soil_potassium": _raster(rng.uniform(120.0, 180.0, shape), shape),
            "soil_organic_matter": _raster(rng.uniform(3.0, 5.0, shape), shape),
        }
        motor = BiofertilizerMotor()

        result = await motor.execute(
            abundant,
            MotorParameters(
                start_date="2026-01-01",
                end_date="2026-12-31",
                scenario_name="biofertilizer_fertile",
                custom_params={"crop_type": "wheat"},
            ),
        )

        assert float(result.outputs["nitrogen_deficit"].max()) == 0.0
        assert float(result.outputs["phosphorus_deficit"].max()) == 0.0
        assert float(result.outputs["soil_health_score"].mean()) > 80.0

    async def test_soil_health_score_is_a_bounded_percentage(self, deficient_soils):
        motor = BiofertilizerMotor()
        params = MotorParameters(
            start_date="2026-01-01",
            end_date="2026-12-31",
            scenario_name="biofertilizer_health",
            custom_params={"crop_type": "wheat"},
        )

        result = await motor.execute(deficient_soils, params)

        score = result.outputs["soil_health_score"]
        assert 0.0 <= float(score.min()) <= 100.0
        assert 0.0 <= float(score.max()) <= 100.0

    async def test_summary_counts_the_recommendations_it_returned(self, deficient_soils):
        motor = BiofertilizerMotor()
        params = MotorParameters(
            start_date="2026-01-01",
            end_date="2026-12-31",
            scenario_name="biofertilizer_summary",
            custom_params={"crop_type": "wheat"},
        )

        result = await motor.execute(deficient_soils, params)

        recommendations = result.outputs["recommendations"]
        assert recommendations, "a deficient field must produce at least one recommendation"
        assert result.summary["total_recommendations"] == len(recommendations)
        assert result.summary["crop_type"] == "wheat"

    async def test_every_recommendation_is_dosed_and_confident(self, deficient_soils):
        motor = BiofertilizerMotor()
        params = MotorParameters(
            start_date="2026-01-01",
            end_date="2026-12-31",
            scenario_name="biofertilizer_dosage",
            custom_params={"crop_type": "wheat"},
        )

        result = await motor.execute(deficient_soils, params)

        for rec in result.outputs["recommendations"]:
            assert rec.dosage_kg_ha > 0.0
            assert 0.0 <= rec.confidence <= 1.0
            assert rec.name
            assert rec.timing
            assert rec.application_method
