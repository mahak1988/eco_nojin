"""Integration tests for Map Engine"""
import pytest
from services.map_engine.smart_service import (
    SmartMapService, MapRequest, MapLayer, OutputFormat,
)

@pytest.mark.asyncio
class TestMapEngineIntegration:
    async def test_generate_map(self, db_session):
        service = SmartMapService(db_session)
        request = MapRequest(
            bbox={"north": 35.5, "south": 35.4, "east": 51.5, "west": 51.4},
            layers=[MapLayer.DEM, MapLayer.VEGETATION],
            resolution=30.0,
            output_format=OutputFormat.GEOTIFF,
        )
        result = await service.generate_map(request)
        assert result.map_id
        assert len(result.layers_included) == 2
        assert result.processing_time_ms >= 0
    
    async def test_available_layers(self, db_session):
        service = SmartMapService(db_session)
        bbox = {"north": 35.5, "south": 35.4, "east": 51.5, "west": 51.4}
        layers = await service.get_available_layers(bbox)
        assert len(layers) >= 1
    