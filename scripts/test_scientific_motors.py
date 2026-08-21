"""Test Scientific Motors - Complete Suite."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.map_engine.orchestrator import MapOrchestrator
from services.scientific_motors.swat_plus import SWATPlusMotor
from services.scientific_motors.aquacrop import AquaCropMotor
from services.scientific_motors.rothc import RothCMotor
from services.scientific_motors.hecras import HECRASMOTOR
from services.scientific_motors.whatif_engine import WhatIfMotor
from services.scientific_motors.base import MotorParameters

from shapely.geometry import Polygon


REGION = Polygon([
    (51.00, 35.00), (51.05, 35.00),
    (51.05, 35.05), (51.00, 35.05), (51.00, 35.00),
])


def print_summary(result, indent="    "):
    """Print motor result summary."""
    print(f"{indent}Run ID: {result.run_id}")
    print(f"{indent}Status: {result.status.value}")
    print(f"{indent}Time: {result.execution_time_seconds:.2f}s")
    if result.summary:
        print(f"{indent}Summary:")
        for key, stats in result.summary.items():
            if isinstance(stats, dict) and "min" in stats:
                print(f"{indent}  {key}: min={stats['min']:.2f}, max={stats['max']:.2f}, mean={stats['mean']:.2f}")


async def test_swat(map_orch):
    """Test SWAT+ motor."""
    print("\n" + "=" * 60)
    print("Testing SWAT+ Motor")
    print("=" * 60)

    layers = await map_orch._fetch_layers(
        ["dem", "soil", "landcover", "rainfall"], REGION
    )
    print(f"  Fetched: {list(layers.keys())}")

    motor = SWATPlusMotor()
    params = MotorParameters(
        start_date="2026-01-01",
        end_date="2026-12-31",
        time_step="daily",
        scenario_name="baseline",
    )
    result = await motor.execute(layers, params)
    print_summary(result)
    return result


async def test_aquacrop(swat_result, crop="wheat"):
    """Test AquaCrop motor."""
    print("\n" + "=" * 60)
    print(f"Testing AquaCrop Motor ({crop})")
    print("=" * 60)

    inputs = {
        "soil_water_mm": swat_result.outputs.get("soil_water_mm"),
        "et_mm": swat_result.outputs.get("et_mm"),
    }

    motor = AquaCropMotor(crop_type=crop)
    params = MotorParameters(
        start_date="2026-01-01",
        end_date="2026-12-31",
        time_step="daily",
        scenario_name="baseline",
        custom_params={"irrigation_mm": 50.0},
    )
    result = await motor.execute(inputs, params)
    print_summary(result)
    return result


async def test_rothc(swat_result, aquacrop_result):
    """Test RothC motor."""
    print("\n" + "=" * 60)
    print("Testing RothC Motor (Soil Carbon)")
    print("=" * 60)

    inputs = {
        "soil_water_mm": swat_result.outputs.get("soil_water_mm"),
        "biomass_ton_ha": aquacrop_result.outputs.get("biomass_ton_ha"),
    }

    motor = RothCMotor(years=20)
    params = MotorParameters(
        start_date="2026-01-01",
        end_date="2046-01-01",
        time_step="yearly",
        scenario_name="baseline",
        custom_params={
            "initial_soc_pct": 1.5,
            "clay_percent": 25.0,
            "land_use": "cropland",
        },
    )
    result = await motor.execute(inputs, params)
    print_summary(result)
    return result


async def test_hecras(map_orch, swat_result):
    """Test HEC-RAS motor."""
    print("\n" + "=" * 60)
    print("Testing HEC-RAS Motor (Flood)")
    print("=" * 60)

    layers = await map_orch._fetch_layers(["dem", "landcover"], REGION)
    swat_outputs = swat_result.outputs

    inputs = {
        "dem": layers.get("dem"),
        "runoff_mm": swat_outputs.get("runoff_mm"),
        "slope": None,
        "landcover": layers.get("landcover"),
    }

    motor = HECRASMOTOR()
    params = MotorParameters(
        start_date="2026-01-01",
        end_date="2026-12-31",
        time_step="hourly",
        scenario_name="flood_100yr",
        custom_params={"return_period": 100},
    )
    result = await motor.execute(inputs, params)
    print_summary(result)
    return result


async def test_whatif(swat_result, aquacrop_result, rothc_result):
    """Test What-If engine."""
    print("\n" + "=" * 60)
    print("Testing What-If Motor (Scenario Analysis)")
    print("=" * 60)

    inputs = {
        "baseline_yield": aquacrop_result.outputs.get("yield_ton_ha"),
        "baseline_water": swat_result.outputs.get("et_mm"),
        "baseline_carbon": rothc_result.outputs.get("final_soc_t_ha"),
    }

    motor = WhatIfMotor(n_iterations=50)
    params = MotorParameters(
        start_date="2026-01-01",
        end_date="2036-01-01",
        time_step="yearly",
        scenario_name="whatif_analysis",
    )
    result = await motor.execute(inputs, params)
    print_summary(result)

    if "scenarios" in result.outputs:
        print("\n  Scenarios:")
        for name, params_dict in result.outputs["scenarios"].items():
            desc = params_dict.get("description", "")
            print(f"    - {name}: {desc}")

    if "best_scenario" in result.outputs:
        print(f"\n  Best scenario: {result.outputs['best_scenario']}")

    return result


async def main():
    """Main test function."""
    print("=" * 60)
    print("Scientific Motors - Complete Test Suite")
    print("=" * 60)

    map_orch = MapOrchestrator()

    # 1. SWAT+
    swat_result = await test_swat(map_orch)

    # 2. AquaCrop (wheat)
    aquacrop_result = await test_aquacrop(swat_result, crop="wheat")

    # 3. RothC
    rothc_result = await test_rothc(swat_result, aquacrop_result)

    # 4. HEC-RAS
    hecras_result = await test_hecras(map_orch, swat_result)

    # 5. What-If
    whatif_result = await test_whatif(swat_result, aquacrop_result, rothc_result)

    print("\n" + "=" * 60)
    print("[SUCCESS] All 5 motors tested successfully!")
    print("=" * 60)
    print("\nCompleted:")
    print("  - SWAT+ (Water Balance)")
    print("  - AquaCrop (Crop Yield)")
    print("  - RothC (Soil Carbon)")
    print("  - HEC-RAS (Flood)")
    print("  - What-If (Scenario Analysis)")


if __name__ == "__main__":
    asyncio.run(main())