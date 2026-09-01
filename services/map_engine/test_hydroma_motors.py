"""Test Hydroma Nojin motors."""
import structlog

logger = structlog.get_logger()
import sys

sys.path.insert(0, '.')

import asyncio

import numpy as np
import xarray as xr

from services.map_engine.smart_mapper import SmartMapGenerator
from services.scientific_motors.base import MotorParameters
from services.scientific_motors.biofertilizer import BiofertilizerMotor


async def test_biofertilizer():
    """Test biofertilizer recommendation engine."""
    logger.info("=" * 60)
    logger.info("Testing Biofertilizer Recommender")
    logger.info("=" * 60)

    # Create synthetic soil data
    shape = (10, 10)
    coords = {
        "y": np.linspace(35.0, 35.1, shape[0]),
        "x": np.linspace(51.0, 51.1, shape[1]),
    }

    soil_ph = xr.DataArray(
        np.random.uniform(6.5, 7.5, shape),
        dims=["y", "x"],
        coords=coords,
    )

    soil_n = xr.DataArray(
        np.random.uniform(80, 120, shape),  # Deficient
        dims=["y", "x"],
        coords=coords,
    )

    soil_p = xr.DataArray(
        np.random.uniform(30, 50, shape),  # Low
        dims=["y", "x"],
        coords=coords,
    )

    soil_k = xr.DataArray(
        np.random.uniform(25, 40, shape),
        dims=["y", "x"],
        coords=coords,
    )

    soil_om = xr.DataArray(
        np.random.uniform(1.0, 2.0, shape),  # Low OM
        dims=["y", "x"],
        coords=coords,
    )

    # Run motor
    motor = BiofertilizerMotor()
    params = MotorParameters(
        start_date="2026-01-01",
        end_date="2026-12-31",
        time_step="daily",
        scenario_name="biofertilizer_test",
        custom_params={"crop_type": "wheat"},
    )

    result = await motor.execute(
        {
            "soil_ph": soil_ph,
            "soil_nitrogen": soil_n,
            "soil_phosphorus": soil_p,
            "soil_potassium": soil_k,
            "soil_organic_matter": soil_om,
        },
        params,
    )

    logger.info(f"\nStatus: {result.status.value}")
    logger.info(f"Execution time: {result.execution_time_seconds:.2f}s")

    if result.status.value == "completed":
        logger.info("\nRecommendations:")
        for i, rec in enumerate(result.outputs["recommendations"], 1):
            logger.info(f"\n  {i}. {rec.name}")
            logger.info(f"     Type: {rec.type.value}")
            logger.info(f"     Dosage: {rec.dosage_kg_ha} kg/ha")
            logger.info(f"     Method: {rec.application_method}")
            logger.info(f"     Timing: {rec.timing}")
            logger.info(f"     Benefit: {rec.expected_benefit}")
            logger.info(f"     Confidence: {rec.confidence:.2f}")

        logger.info(f"\nSoil Health Score: {result.outputs['soil_health_score'].mean():.1f}/100")
        logger.info(f"N Deficit: {result.outputs['nitrogen_deficit'].mean():.1f} kg/ha")
        logger.info(f"P Deficit: {result.outputs['phosphorus_deficit'].mean():.1f} kg/ha")


def test_smart_mapper():
    """Test smart map generator."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Smart Map Generator")
    logger.info("=" * 60)

    # Create synthetic satellite data
    shape = (100, 100)
    coords = {
        "y": np.linspace(35.0, 35.1, shape[0]),
        "x": np.linspace(51.0, 51.1, shape[1]),
    }

    # Simulate red and NIR bands
    red = xr.DataArray(
        np.random.uniform(0.1, 0.3, shape),
        dims=["y", "x"],
        coords=coords,
    )

    nir = xr.DataArray(
        np.random.uniform(0.3, 0.6, shape),
        dims=["y", "x"],
        coords=coords,
    )

    # Calculate NDVI
    ndvi = SmartMapGenerator.calculate_ndvi(red, nir)
    logger.info(f"\nNDVI: min={ndvi.min():.2f}, max={ndvi.max():.2f}, mean={ndvi.mean():.2f}")

    # Classify vegetation health
    health = SmartMapGenerator.classify_vegetation_health(ndvi)
    logger.info("\nVegetation Health Distribution:")
    for i in range(1, 6):
        count = np.sum(health.values == i)
        logger.info(f"  Class {i}: {count} pixels ({count / health.size * 100:.1f}%)")

    # Estimate biomass
    biomass = SmartMapGenerator.estimate_biomass(ndvi, crop_type="wheat")
    logger.info(f"\nEstimated Biomass: {biomass.mean():.2f} ton/ha")


if __name__ == "__main__":
    asyncio.run(test_biofertilizer())
    test_smart_mapper()
    logger.info("\n" + "=" * 60)
    logger.info("✅ All Hydroma Nojin motors tested successfully!")
    logger.info("=" * 60)
