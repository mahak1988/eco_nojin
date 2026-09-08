"""Unit tests for the LandService using mocked dependencies."""

import unittest
from unittest.mock import Mock
from services.land.service import LandService
from interfaces.land_engine_interface import ILandEngine
import numpy as np


class TestLandService(unittest.TestCase):

    def setUp(self):
        """Set up a LandService instance with mocked engine for each test."""
        self.mock_land_engine = Mock(spec=ILandEngine)
        self.service = LandService(engine=self.mock_land_engine)

    def test_analyze_terrain_delegates_to_engine(self):
        """Test that analyze_terrain calls the injected engine."""
        profile = self.service.create_profile(name="test", location_lat=0, location_lon=0)
        dem_array = np.array([[1, 2], [3, 4]])

        from engine.land.models import TerrainAnalysis
        mock_result = TerrainAnalysis(
            profile_id=profile.id,
            elevation_min=1.0,
            elevation_max=4.0,
            elevation_mean=2.5,
            slope_mean=10.0,
            slope_max=15.0,
        )
        self.mock_land_engine.analyze_terrain.return_value = mock_result

        result = self.service.analyze_terrain(profile.id, dem_array, resolution=30.0)

        self.mock_land_engine.analyze_terrain.assert_called_once()
        self.assertEqual(result.profile_id, profile.id)
        self.assertEqual(result.slope_mean, 10.0)

    def test_analyze_drainage_delegates_to_engine(self):
        """Test that analyze_drainage calls the injected engine."""
        profile = self.service.create_profile(name="test", location_lat=0, location_lon=0)
        dem_array = np.array([[1, 2], [3, 4]])

        from engine.land.models import DrainageAnalysis, DrainagePattern
        mock_result = DrainageAnalysis(
            profile_id=profile.id,
            drainage_pattern=DrainagePattern.DENDRITIC,
            drainage_density=1.5,
        )
        self.mock_land_engine.analyze_drainage.return_value = mock_result

        result = self.service.analyze_drainage(profile.id, dem_array, resolution=30.0, area_km2=1.0)

        self.mock_land_engine.analyze_drainage.assert_called_once()
        self.assertEqual(result.profile_id, profile.id)
        self.assertEqual(result.drainage_pattern, DrainagePattern.DENDRITIC)

    def test_assess_capability_delegates_to_engine(self):
        """Test that assess_capability calls the injected engine."""
        profile = self.service.create_profile(name="test", location_lat=0, location_lon=0)

        from engine.land.models import CapabilityAssessment, LandCapabilityClass
        mock_result = CapabilityAssessment(
            profile_id=profile.id,
            capability_class=LandCapabilityClass.CLASS_II,
            confidence_score=0.85,
        )
        self.mock_land_engine.assess_capability.return_value = mock_result

        result = self.service.assess_capability(
            profile_id=profile.id,
            slope_degrees=8.0,
            soil_depth_m=1.5,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="temperate",
        )

        self.mock_land_engine.assess_capability.assert_called_once()
        self.assertEqual(result.profile_id, profile.id)
        self.assertEqual(result.capability_class, LandCapabilityClass.CLASS_II)


if __name__ == '__main__':
    unittest.main()
