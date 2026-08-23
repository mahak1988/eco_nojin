"""Unit tests for the LandService using mocked dependencies."""

import unittest
from unittest.mock import Mock, MagicMock
from services.land.service import LandService
from interfaces.land_engine_interface import ILandEngine
from interfaces.hydroma_engine_interface import IHydromaEngine
import numpy as np

class TestLandService(unittest.TestCase):

    def setUp(self):
        """Set up a LandService instance with mocked engines for each test."""
        self.mock_land_engine = Mock(spec=ILandEngine)
        self.mock_hydroma_engine = Mock(spec=IHydromaEngine)
        self.service = LandService(engine=self.mock_land_engine, hydroma_engine=self.mock_hydroma_engine)

    def test_analyze_terrain_delegates_to_engine(self):
        """Test that analyze_terrain calls the injected engine."""
        profile_id = "test-profile-1"
        dem_array = np.array([[1, 2], [3, 4]])
        
        mock_result = {
            "profile_id": profile_id,
            "slope_mean": 10.0,
            "aspect_dominant": "N"
        }
        self.mock_land_engine.analyze_terrain.return_value = mock_result

        result = self.service.analyze_terrain(profile_id, dem_array, resolution=30.0)

        # Assert the engine was called
        self.mock_land_engine.analyze_terrain.assert_called_once_with(dem_array, profile_id)
        # Assert the service returned a correctly structured object
        self.assertEqual(result.profile_id, profile_id)
        self.assertEqual(result.mean_slope_degrees, 10.0)

    def test_analyze_soil_delegates_to_hydroma_engine(self):
        """Test that analyze_soil calls the injected hydroma engine."""
        profile_id = "test-profile-2"
        soil_data = {"ec": 2.5, "texture_class": "Clay"}
        
        mock_result = {
            "salinity_classification": "Low",
            "texture_class": "Clay"
        }
        self.mock_hydroma_engine.analyze_soil.return_value = mock_result

        result = self.service.analyze_soil(profile_id, soil_data)

        # Assert the hydroma engine was called
        self.mock_hydroma_engine.analyze_soil.assert_called_once_with(soil_data)
        # Assert the service returned a correctly structured object
        self.assertIsNotNone(result)
        self.assertEqual(result["profile_id"], profile_id)
        self.assertEqual(result["salinity_classification"], "Low")


if __name__ == '__main__':
    unittest.main()