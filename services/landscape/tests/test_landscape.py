"""Tests for the Landscape service — land profile analysis and terrain evaluation."""

from __future__ import annotations


class TestLandscapeModels:
    def test_land_profile_create_request(self):
        from services.land.land_profile import LandProfileCreateRequest

        req = LandProfileCreateRequest(
            project_id="proj-001",
            latitude=32.654,
            longitude=51.654,
            area_hectares=10.0,
        )
        assert req.project_id == "proj-001"
        assert req.latitude == 32.654

    def test_land_profile_response(self):
        from services.land.land_profile import LandProfileResponse

        resp = LandProfileResponse(
            id="lp-001",
            project_id="proj-001",
            location={"lat": 32.0, "lng": 51.0},
            boundary=None,
            area_hectares=10.0,
            elevation_min=100.0,
            elevation_max=250.0,
            elevation_mean=175.0,
            slope_mean_degrees=15.5,
            aspect_dominant="S",
            terrain_type="rolling",
            drainage_pattern="dendritic",
            erosion_risk_level="moderate",
            accessibility_score=0.75,
            land_capability_class="III",
            development_constraints={},
            dem_source="SRTM",
            dem_resolution=30.0,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )
        assert resp.terrain_type == "rolling"
        assert resp.area_hectares == 10.0


class TestLandscapeService:
    def test_calculate_land_profile(self):
        from services.land.land_profile import (
            LandProfileCreateRequest,
            LandProfileResponse,
            calculate_land_profile,
        )

        req = LandProfileCreateRequest(
            project_id="proj-002",
            latitude=30.0,
            longitude=50.0,
            area_hectares=5.0,
        )
        resp = calculate_land_profile(req)
        assert isinstance(resp, LandProfileResponse)
        assert resp.project_id == "proj-002"
        assert resp.terrain_type is not None
        assert resp.dem_source == "SRTM"

    def test_calculate_land_profile_with_boundary(self):
        from services.land.land_profile import (
            LandProfileCreateRequest,
            calculate_land_profile,
        )

        boundary = {
            "type": "Polygon",
            "coordinates": [[[50, 30], [51, 30], [51, 31], [50, 31], [50, 30]]],
        }
        req = LandProfileCreateRequest(
            project_id="proj-003",
            latitude=30.5,
            longitude=50.5,
            boundary_geojson=boundary,
            area_hectares=12.0,
        )
        resp = calculate_land_profile(req)
        assert resp.boundary == boundary
        assert resp.area_hectares == 12.0
