"""Test Map Generation Engine - M-TOP and M-SLP."""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shapely.geometry import Polygon

from services.map_engine.base import MapRequest, MapType
from services.map_engine.orchestrator import MapOrchestrator


async def test_pipeline(
    orchestrator: MapOrchestrator,
    map_type: MapType,
    region: Polygon,
    resolution: float,
    parameters: dict = None,
) -> None:
    """Test a single pipeline with cache hit detection."""
    print(f"\n{'='*60}")
    print(f"Testing {map_type.value} pipeline")
    print(f"{'='*60}")

    request = MapRequest(
        map_type=map_type,
        region=region,
        target_crs="auto",
        resolution=resolution,
        parameters=parameters or {},
    )

    # First run (cache miss)
    start = time.time()
    result1 = await orchestrator.generate(request)
    real_time = time.time() - start

    print(f"\n[Run 1 - Generation]")
    print(f"  Map ID:      {result1.map_id}")
    print(f"  COG:         {result1.cog_path}")
    print(f"  Vector:      {result1.vector_tiles_path or 'None'}")
    print(f"  Real time:   {real_time:.3f}s")
    print(f"  Sources:     {', '.join(result1.data_sources)}")

    # Verify COG
    if result1.cog_path.exists():
        size_mb = result1.cog_path.stat().st_size / (1024 * 1024)
        print(f"  COG size:    {size_mb:.2f} MB [OK]")
    else:
        print(f"  COG size:    NOT FOUND [FAIL]")
        return

    # Second run (cache hit)
    start = time.time()
    result2 = await orchestrator.generate(request)
    cache_lookup_time = time.time() - start

    print(f"\n[Run 2 - Cache Hit]")
    print(f"  Lookup time: {cache_lookup_time*1000:.1f} ms")
    print(f"  Reported:    {result2.processing_time_seconds*1000:.1f} ms")
    print(f"  Sources:     {', '.join(result2.data_sources)}")

    if cache_lookup_time < 0.1:
        print(f"  Status:      [OK] Cache hit confirmed")
    else:
        print(f"  Status:      [FAIL] Too slow for cache hit")

    # Metadata check
    if result1.metadata:
        print(f"\n[Metadata]")
        for key in ["title", "bands", "slope_classes", "elevation_range"]:
            if key in result1.metadata:
                val = result1.metadata[key]
                if isinstance(val, dict):
                    print(f"  {key}: {val}")
                else:
                    print(f"  {key}: {val}")


async def main():
    print("="*60)
    print("Eco Nojin Map Engine - Comprehensive Test")
    print("="*60)

    # Test region (~5km x 5km)
    region = Polygon([
        (51.00, 35.00),
        (51.05, 35.00),
        (51.05, 35.05),
        (51.00, 35.05),
        (51.00, 35.00),
    ])

    print(f"\n[Region] Bounds: {region.bounds}")

    # Initialize orchestrator
    orchestrator = MapOrchestrator()

    print(f"\n[Available Pipelines]")
    for p in orchestrator.list_pipelines():
        print(f"  - {p}")

    print(f"\n[Available Fetchers]")
    for f in orchestrator.list_fetchers():
        print(f"  - {f}")

    # Test M-TOP (Topographic)
    await test_pipeline(
        orchestrator=orchestrator,
        map_type=MapType.M_TOP,
        region=region,
        resolution=30.0,
        parameters={"contour_interval": 5.0},
    )

    # Test M-SLP (Slope & Aspect) - if registered
    if MapType.M_SLP in orchestrator.pipelines:
        await test_pipeline(
            orchestrator=orchestrator,
            map_type=MapType.M_SLP,
            region=region,
            resolution=30.0,
        )
    else:
        print(f"\n[SKIP] M-SLP not yet registered")

    # Test M-ERS (RUSLE) - Soil erosion
    if MapType.M_ERS in orchestrator.pipelines:
        await test_pipeline(
            orchestrator=orchestrator,
            map_type=MapType.M_ERS,
            region=region,
            resolution=30.0,
            parameters={"c_factor": 0.3, "p_factor": 1.0},
        )
    else:
        print(f"\n[SKIP] M-ERS not yet registered")

    # Test M-VEG (Vegetation) - multi-season
    if MapType.M_VEG in orchestrator.pipelines:
        for season in ["spring", "summer", "autumn"]:
            print(f"\n--- Testing M-VEG for {season} ---")
            await test_pipeline(
                orchestrator=orchestrator,
                map_type=MapType.M_VEG,
                region=region,
                resolution=10.0,
                parameters={"season": season, "cloud_cover_pct": 10.0},
            )
    else:
        print(f"\n[SKIP] M-VEG not yet registered")

    # Test M-RUN (Runoff - SCS-CN) with different storm intensities
    if MapType.M_RUN in orchestrator.pipelines:
        for storm_mm in [25.0, 50.0, 100.0]:
            print(f"\n--- Testing M-RUN for {storm_mm}mm storm ---")
            await test_pipeline(
                orchestrator=orchestrator,
                map_type=MapType.M_RUN,
                region=region,
                resolution=30.0,
                parameters={"precipitation_mm": storm_mm, "amc": "II"},
            )
    else:
        print(f"\n[SKIP] M-RUN not yet registered")

    print("\n" + "="*60)
    print("[SUCCESS] All tests complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
