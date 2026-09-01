"""Test Land Capability Classification motor."""
import structlog

logger = structlog.get_logger()
import sys

sys.path.insert(0, '.')

import asyncio

import numpy as np
import xarray as xr

from services.scientific_motors.base import MotorParameters
from services.scientific_motors.land_capability import LandCapabilityMotor


async def test_lcc():
    """Test LCC motor."""
    logger.info("=" * 70)
    logger.info("🌍 Testing Land Capability Classification (USDA)")
    logger.info("=" * 70)

    # Create synthetic data
    shape = (50, 50)
    coords = {
        "y": np.linspace(35.0, 35.1, shape[0]),
        "x": np.linspace(51.0, 51.1, shape[1]),
    }

    dem = xr.DataArray(
        np.random.uniform(1000, 1500, shape),
        dims=["y", "x"], coords=coords,
    )

    soil_depth = xr.DataArray(
        np.random.uniform(20, 120, shape),
        dims=["y", "x"], coords=coords,
    )

    soil_texture = xr.DataArray(
        np.random.randint(1, 12, shape),
        dims=["y", "x"], coords=coords,
    )

    # Run motor
    motor = LandCapabilityMotor()
    params = MotorParameters(
        start_date="2026-01-01",
        end_date="2026-12-31",
        time_step="daily",
        scenario_name="lcc_test",
    )

    result = await motor.execute(
        {
            "dem": dem,
            "soil_depth": soil_depth,
            "soil_texture": soil_texture,
        },
        params,
    )

    logger.info(f"\nStatus: {result.status.value}")
    logger.info(f"Execution time: {result.execution_time_seconds:.2f}s")

    if result.status.value == "completed":
        summary = result.summary
        cultivable = summary.get("cultivable_percent", 0)

        logger.info(f"\n🌱 Cultivable land (Class I-IV): {cultivable:.1f}%")
        logger.info("\n📊 Distribution:")

        for class_key, data in summary.get("distribution", {}).items():
            pct = data.get("percent", 0)
            desc = data.get("description", "")
            pixels = data.get("pixels", 0)
            logger.info(f"\n  {class_key}: {pixels} pixels ({pct:.1f}%)")
            logger.info(f"    → {desc}")

        # Show suitable crops for most common class
        suitable_crops = result.outputs.get("suitable_crops", {})
        if suitable_crops:
            logger.info("\n🌾 Suitable crops by class:")
            for class_num, crops in sorted(suitable_crops.items())[:4]:
                logger.info(f"  Class {class_num}: {', '.join(crops[:3])}...")


if __name__ == "__main__":
    asyncio.run(test_lcc())
    logger.info("\n" + "=" * 70)
    logger.info("✅ LCC motor test completed")
    logger.info("=" * 70)
