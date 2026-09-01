"""Map Generation Orchestrator - Coordinates pipelines and fetchers."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

import asyncio
import hashlib
import json
from pathlib import Path

import xarray as xr
from shapely.geometry import Polygon

from .base import MapPipeline, MapRequest, MapResult, MapType
from .fetchers.dem_fetcher import DEMFetcher
from .fetchers.landcover_fetcher import LandCoverFetcher
from .fetchers.rainfall_fetcher import RainfallFetcher
from .fetchers.runoff_fetcher import RunoffFetcher
from .fetchers.soil_fetcher import SoilErodibilityFetcher
from .fetchers.vegetation_fetcher import VegetationFetcher
from .pipelines.runoff import RunoffPipeline
from .pipelines.rusle import RUSLEPipeline
from .pipelines.topographic import TopographicPipeline
from .pipelines.vegetation import VegetationPipeline


class MapOrchestrator:
    """
    Coordinates map generation pipelines.

    Features:
    - Lazy loading of base layers
    - Multi-level caching (memory + disk)
    - Pipeline registry for extensibility
    - Graceful error handling

    Usage:
        orchestrator = MapOrchestrator()
        request = MapRequest(
            map_type=MapType.M_TOP,
            region=Polygon([...]),
            resolution=10.0,
        )
        result = await orchestrator.generate(request)
    """

    def __init__(self, cache_dir: Path = Path("data/maps/cache")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize fetchers registry
        self.fetchers: dict[str, object] = {
            "dem": DEMFetcher(cache_dir=self.cache_dir / "dem"),
            "rainfall": RainfallFetcher(cache_dir=self.cache_dir / "rainfall"),
            "soil": SoilErodibilityFetcher(cache_dir=self.cache_dir / "soil"),
            "vegetation": VegetationFetcher(cache_dir=self.cache_dir / "vegetation"),
            "landcover": LandCoverFetcher(cache_dir=self.cache_dir / "landcover"),
            "runoff": RunoffFetcher(cache_dir=self.cache_dir / "runoff"),
        }

        # Initialize pipelines registry
        self.pipelines: dict[MapType, MapPipeline] = {
            MapType.M_TOP: TopographicPipeline(cache_dir=self.cache_dir),
            MapType.M_ERS: RUSLEPipeline(cache_dir=self.cache_dir),
            MapType.M_VEG: VegetationPipeline(cache_dir=self.cache_dir),
            MapType.M_RUN: RunoffPipeline(cache_dir=self.cache_dir),
        }

        # Optional: Try to register SlopeAspectPipeline if available
        try:
            from .pipelines.slope_aspect import SlopeAspectPipeline
            self.pipelines[MapType.M_SLP] = SlopeAspectPipeline(
                cache_dir=self.cache_dir
            )
        except ImportError:
            pass  # SlopeAspectPipeline not yet implemented

    async def generate(self, request: MapRequest) -> MapResult:
        """
        Generate a map based on the request.

        Workflow:
        1. Check cache (with proper time tracking)
        2. Get pipeline for map type
        3. Fetch required base layers
        4. Execute pipeline
        5. Save metadata and cache result
        """
        logger.info(f"[INFO] Generating {request.map_type.value} map...")

        # 1. Check cache
        cached = await self._check_cache(request)
        if cached:
            logger.info(f"[OK] Cache hit: {cached.map_id}")
            return cached

        # 2. Get pipeline
        pipeline = self.pipelines.get(request.map_type)
        if not pipeline:
            available = [m.value for m in self.pipelines.keys()]
            raise ValueError(
                f"No pipeline for map type: {request.map_type.value}. "
                f"Available: {available}"
            )

        # 3. Fetch base layers
        required_layers = pipeline.get_required_layers()
        logger.info(f"[INFO] Fetching layers: {required_layers}")
        base_layers = await self._fetch_layers(required_layers, request.region, **request.parameters)

        # 4. Execute pipeline
        logger.info(f"[INFO] Executing pipeline: {pipeline.map_type.value}")
        result = await pipeline.execute(base_layers, request)

        # 5. Save metadata
        await self._save_metadata(result)

        # 6. Cache result
        await self._cache_result(request, result)

        print(
            f"[OK] Map generated: {result.map_id} "
            f"in {result.processing_time_seconds:.2f}s"
        )
        return result

    async def generate_batch(
        self,
        requests: list[MapRequest],
        max_concurrent: int = 3,
    ) -> list[MapResult]:
        """Generate multiple maps concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_generate(req: MapRequest):
            async with semaphore:
                try:
                    return await self.generate(req)
                except Exception as e:
                    logger.error(f"[ERROR] Failed to generate {req.map_type.value}: {e}")
                    return None

        tasks = [bounded_generate(req) for req in requests]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def _check_cache(self, request: MapRequest) -> MapResult | None:
        """Check if result is cached. Returns result with near-zero time on hit."""
        cache_key = self._cache_key(request)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))

            # Verify COG still exists
            cog_path = Path(data["cog_path"])
            if not cog_path.exists():
                logger.warning(f"[WARN] Cached COG missing: {cog_path}")
                cache_file.unlink()
                return None

            # Return cached result with near-zero time to indicate cache hit
            return MapResult(
                map_id=data["map_id"],
                map_type=MapType(data["map_type"]),
                cog_path=cog_path,
                vector_tiles_path=(
                    Path(data["vector_tiles_path"])
                    if data.get("vector_tiles_path")
                    else None
                ),
                metadata=data["metadata"],
                # PATCH: Cache hits report near-zero time
                processing_time_seconds=0.001,
                data_sources=data.get("data_sources", []) + ["[cached]"],
                crs=data.get("crs", ""),
                bounds=tuple(data.get("bounds", ())),
                resolution=data.get("resolution", 0.0),
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"[WARN] Cache read failed: {e}")
            cache_file.unlink(missing_ok=True)
            return None

    async def _fetch_layers(
        self,
        layers: list[str],
        region: Polygon,
        **kwargs,
    ) -> dict[str, xr.DataArray]:
        """Fetch required base layers concurrently."""
        result = {}

        async def fetch_one(name: str):
            fetcher = self.fetchers.get(name)
            if not fetcher:
                available = list(self.fetchers.keys())
                raise ValueError(
                    f"No fetcher for layer: {name}. Available: {available}"
                )
            return name, await fetcher.fetch(region, **kwargs)

        # Fetch concurrently
        tasks = [fetch_one(layer) for layer in layers]
        fetched = await asyncio.gather(*tasks, return_exceptions=True)

        for item in fetched:
            if isinstance(item, Exception):
                raise item
            name, data = item
            result[name] = data

        return result

    async def _save_metadata(self, result: MapResult) -> None:
        """Save metadata JSON next to COG."""
        metadata_path = result.cog_path.parent / "metadata.json"
        metadata_path.write_text(
            json.dumps(result.to_dict(), indent=2, default=str),
            encoding="utf-8",
        )

    async def _cache_result(self, request: MapRequest, result: MapResult) -> None:
        """Cache result for future requests."""
        cache_key = self._cache_key(request)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            cache_file.write_text(
                json.dumps(result.to_dict(), indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"[WARN] Cache write failed: {e}")

    def _cache_key(self, request: MapRequest) -> str:
        """Generate deterministic cache key for request."""
        bounds = request.region.bounds
        key_parts = [
            request.map_type.value,
            f"{bounds[0]:.6f}",
            f"{bounds[1]:.6f}",
            f"{bounds[2]:.6f}",
            f"{bounds[3]:.6f}",
            f"{request.resolution}",
            request.target_crs,
            json.dumps(request.parameters, sort_keys=True),
        ]
        key_str = "|".join(key_parts)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def register_pipeline(self, pipeline: MapPipeline) -> None:
        """Register a new pipeline. Overrides existing for same map_type."""
        self.pipelines[pipeline.map_type] = pipeline
        logger.info(f"[OK] Registered pipeline: {pipeline.map_type.value}")

    def register_fetcher(self, fetcher) -> None:
        """Register a new fetcher. Overrides existing for same layer_name."""
        self.fetchers[fetcher.layer_name] = fetcher
        logger.info(f"[OK] Registered fetcher: {fetcher.layer_name}")

    def list_pipelines(self) -> list[str]:
        """List available pipeline types."""
        return [m.value for m in self.pipelines.keys()]

    def list_fetchers(self) -> list[str]:
        """List available fetchers."""
        return list(self.fetchers.keys())

    async def clear_cache(self, map_type: MapType | None = None) -> int:
        """Clear cache. If map_type specified, clear only that type."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                if map_type:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    if data.get("map_type") != map_type.value:
                        continue
                cache_file.unlink()
                count += 1
            except Exception:
                pass
        logger.info(f"[OK] Cleared {count} cached entries")
        return count
