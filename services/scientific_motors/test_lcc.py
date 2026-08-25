"""Test Land Capability Classification motor."""
import sys
sys.path.insert(0, '.')

import asyncio
import numpy as np
import xarray as xr
from services.scientific_motors.land_capability import LandCapabilityMotor
from services.scientific_motors.base import MotorParameters


async def test_lcc():
    """Test LCC motor."""
    print("=" * 70)
    print("🌍 Testing Land Capability Classification (USDA)")
    print("=" * 70)

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

    print(f"\nStatus: {result.status.value}")
    print(f"Execution time: {result.execution_time_seconds:.2f}s")

    if result.status.value == "completed":
        summary = result.summary
        cultivable = summary.get("cultivable_percent", 0)
        
        print(f"\n🌱 Cultivable land (Class I-IV): {cultivable:.1f}%")
        print(f"\n📊 Distribution:")
        
        for class_key, data in summary.get("distribution", {}).items():
            pct = data.get("percent", 0)
            desc = data.get("description", "")
            pixels = data.get("pixels", 0)
            print(f"\n  {class_key}: {pixels} pixels ({pct:.1f}%)")
            print(f"    → {desc}")

        # Show suitable crops for most common class
        suitable_crops = result.outputs.get("suitable_crops", {})
        if suitable_crops:
            print(f"\n🌾 Suitable crops by class:")
            for class_num, crops in sorted(suitable_crops.items())[:4]:
                print(f"  Class {class_num}: {', '.join(crops[:3])}...")


if __name__ == "__main__":
    asyncio.run(test_lcc())
    print("\n" + "=" * 70)
    print("✅ LCC motor test completed")
    print("=" * 70)
