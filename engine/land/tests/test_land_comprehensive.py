"""
Comprehensive Tests for Land Intelligence Engine
================================================

Tests all modules:
- models.py: Pydantic models
- dem_processor.py: DEM processing
- slope_aspect.py: Slope calculations
- terrain_analysis.py: Terrain analysis
- drainage.py: Drainage analysis
- capability.py: Capability assessment
- reference/: Reference data

Run: python -m pytest engine/land/tests/ -v
"""

import numpy as np
import pytest

from engine.land.slope_aspect import SlopeAspectAnalyzer


class MockDEMProcessor:
    """Mock DEMProcessor for tests."""
    def __init__(self, data=None, resolution=30.0):
        import numpy as np
        self._data = data if data is not None else np.full((10, 10), 1000.0)
        self._dataset = None
        self.resolution = resolution
        self.dem_file_path = None




class TestModels:
    """Test Pydantic models."""

    def test_land_profile_creation(self):
        """Test LandProfile creation."""
        from engine.land.models import LandProfile

        profile = LandProfile(
            id="test-001",
            name="Test Farm",
            location_lat=32.65,
            location_lon=51.67,
            country="Iran",
            region="Isfahan"
        )

        assert profile.id == "test-001"
        assert profile.location_lat == 32.65
        assert profile.location_lon == 51.67

    def test_terrain_analysis_creation(self):
        """Test TerrainAnalysis creation."""
        from engine.land.models import TerrainAnalysis, TerrainType

        analysis = TerrainAnalysis(
            profile_id="test-001",
            terrain_type=TerrainType.ROLLING,
            elevation_min=1000,
            elevation_max=1500,
            elevation_mean=1250,
            slope_mean=12.5,
            slope_max=25.0,
            aspect_dominant="S"
        )

        assert analysis.terrain_type == TerrainType.ROLLING
        assert analysis.slope_mean == 12.5

    def test_capability_assessment_creation(self):
        """Test CapabilityAssessment creation."""
        from engine.land.models import CapabilityAssessment, LandCapabilityClass

        assessment = CapabilityAssessment(
            profile_id="test-001",
            capability_class=LandCapabilityClass.CLASS_III,
            subclass="e",
            limiting_factors=["slope", "erosion_risk"],
            suitable_uses=["rainfed_agriculture"],
            confidence_score=0.85
        )

        assert assessment.capability_class == LandCapabilityClass.CLASS_III
        assert assessment.confidence_score == 0.85


class TestSlopeAspect:
    """Tests for slope/aspect calculations using SlopeAspectAnalyzer.analyze()."""

    @pytest.fixture
    def calculator(self):
        """SlopeAspectAnalyzer with MockDEMProcessor."""
        import numpy as np

        class MockDEMProcessor:
            def __init__(self, data, resolution=30.0):
                self._data = data
                self._dataset = None
                self.resolution = resolution
                self.dem_file_path = None

        flat = np.full((15, 15), 1000.0)
        return SlopeAspectAnalyzer(MockDEMProcessor(flat, resolution=30.0))

    @pytest.fixture
    def sloped_calculator(self):
        """SlopeAspectAnalyzer with sloped DEM."""
        import numpy as np

        class MockDEMProcessor:
            def __init__(self, data, resolution=30.0):
                self._data = data
                self._dataset = None
                self.resolution = resolution
                self.dem_file_path = None

        dem = np.zeros((15, 15))
        for i in range(15):
            dem[i, :] = 1000.0 - i * 10.0
        return SlopeAspectAnalyzer(MockDEMProcessor(dem, resolution=30.0))

    def test_flat_terrain_zero_slope(self, calculator):
        """Flat terrain should have near-zero slope in interior."""
        result = calculator.analyze(cell_size_meters=30.0)
        slope_arr = result[0]

        # Interior only (edges have NaN)
        interior = slope_arr[2:-2, 2:-2]
        valid = interior[~np.isnan(interior)]

        assert len(valid) > 0
        assert np.allclose(valid, 0, atol=1e-3)

    def test_sloped_terrain_positive_slope(self, sloped_calculator):
        """Sloped terrain should have positive slope."""
        result = sloped_calculator.analyze(cell_size_meters=30.0)
        slope_arr = result[0]

        interior = slope_arr[2:-2, 2:-2]
        valid = interior[~np.isnan(interior)]

        assert len(valid) > 0
        assert np.mean(valid) > 0

    def test_slope_to_percent(self, calculator):
        """Slope conversion to percent."""
        result = calculator.analyze(cell_size_meters=30.0)
        slope_arr = result[0]

        slope_pct = np.tan(np.radians(np.nan_to_num(slope_arr, nan=0.0))) * 100.0
        assert slope_pct.shape == slope_arr.shape

    def test_aspect_cardinal(self, sloped_calculator):
        """Aspect should map to cardinal directions."""
        from engine.land.terrain_analysis import aspect_to_cardinal

        result = sloped_calculator.analyze(cell_size_meters=30.0)
        aspect_arr = result[1]

        # Test a few interior values
        interior = aspect_arr[5:10, 5:10]
        for val in interior.flatten()[:5]:
            if not np.isnan(val):
                card = aspect_to_cardinal(float(val))
                assert card in ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "unknown"]

    def test_slope_classification_usda(self, sloped_calculator):
        """Slope should classify correctly per USDA using SlopeClass enum."""
        from engine.land.models import SlopeClass
        from engine.land.terrain_analysis import classify_slope_usda

        # CLASS_0: <2% (flat)
        assert classify_slope_usda(1.0) == SlopeClass.CLASS_0

        # CLASS_1: 2-5% (gentle)
        assert classify_slope_usda(3.0) == SlopeClass.CLASS_1

        # CLASS_2: 5-10% (moderate)
        assert classify_slope_usda(7.0) == SlopeClass.CLASS_2

        # CLASS_3: 10-20% (strong)
        assert classify_slope_usda(15.0) == SlopeClass.CLASS_3

        # CLASS_4: 20-40% (very strong)
        assert classify_slope_usda(30.0) == SlopeClass.CLASS_4

        # CLASS_5: >40% (steep)
        assert classify_slope_usda(50.0) == SlopeClass.CLASS_5
    def analyzer(self):
        """Create analyzer with 30m resolution."""
        from engine.land.terrain_analysis import (
            TerrainAnalyzer,
        )
        return TerrainAnalyzer(resolution=30.0)

    @pytest.fixture
    def rolling_dem(self):
        """Create rolling terrain DEM."""
        np.random.seed(42)
        x = np.linspace(0, 2 * np.pi, 10)
        y = np.linspace(0, 2 * np.pi, 10)
        X, Y = np.meshgrid(x, y)
        return 1000 + 50 * np.sin(X) * np.cos(Y)

class TestDrainageAnalysis:
    """Test drainage analysis."""

    @pytest.fixture
    def analyzer(self):
        """Create drainage analyzer."""
        from engine.land.drainage import DrainageAnalyzer
        return DrainageAnalyzer(resolution=30.0)

    @pytest.fixture
    def sloped_dem(self):
        """Create sloped DEM for drainage."""
        dem = np.zeros((10, 10))
        for i in range(10):
            for j in range(10):
                dem[i, j] = 1000 - i * 10 - j * 5
        return dem

    def test_drainage_analysis_basic(self, analyzer, sloped_dem):
        """Test basic drainage analysis."""
        analysis = analyzer.analyze(sloped_dem, profile_id="test")

        assert analysis.profile_id == "test"
        assert analysis.drainage_density >= 0
        assert analysis.watershed_area_km2 > 0

    def test_flow_direction_calculation(self, analyzer, sloped_dem):
        """Test D8 flow direction calculation."""
        flow_dir = analyzer._calculate_flow_direction(sloped_dem)

        assert flow_dir.shape == sloped_dem.shape
        # Interior cells should have flow direction
        assert np.any(flow_dir[1:-1, 1:-1] > 0)


class TestCapabilityAssessment:
    """Test capability assessment."""

    @pytest.fixture
    def assessor(self):
        """Create capability assessor."""
        from engine.land.capability import CapabilityAssessor
        return CapabilityAssessor()

    def test_flat_land_high_capability(self, assessor):
        """Flat land with good soil should have high capability."""
        assessment = assessor.assess(
            slope_degrees=1.0,
            soil_depth_m=1.5,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="temperate"
        )

        assert assessment.capability_class.value in ["I", "II"]
        assert assessment.confidence_score > 0.7

    def test_steep_land_low_capability(self, assessor):
        """Steep land should have low capability."""
        assessment = assessor.assess(
            slope_degrees=35.0,
            soil_depth_m=0.3,
            erosion_risk="very_high",
            drainage_class="well_drained",
            climate_zone="temperate"
        )

        assert assessment.capability_class.value in ["V", "VI", "VII", "VIII"]

    def test_arid_land_climate_limitation(self, assessor):
        """Arid land should have climate limitation."""
        assessment = assessor.assess(
            slope_degrees=1.0,
            soil_depth_m=1.5,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="arid",
            profile_id="test"
        )

        assert "water_scarcity" in assessment.limiting_factors
        assert assessment.subclass == "c"


class TestReferenceData:
    """Test reference data."""

    def test_countries_data_exists(self):
        """Test that countries data exists."""
        from engine.land.reference.data import COUNTRIES

        assert len(COUNTRIES) >= 25

    def test_iran_in_countries(self):
        """Test that Iran is in countries."""
        from engine.land.reference.data import get_country

        iran = get_country("IR")
        assert iran.name == "Iran"
        assert iran.continent.value == "asia"

    def test_cities_data_exists(self):
        """Test that cities data exists."""
        from engine.land.reference.data import CITIES

        assert len(CITIES) >= 25

    def test_isfahan_city(self):
        """Test Isfahan city data."""
        from engine.land.reference.data import get_city

        isfahan = get_city("Isfahan")
        assert isfahan.country_code == "IR"
        assert 32 < isfahan.lat < 33

    def test_find_nearest_city(self):
        """Test find nearest city function."""
        from engine.land.reference.data import find_nearest_city

        # Near Tehran
        city = find_nearest_city(35.69, 51.39)
        assert city.name == "Tehran"

    def test_list_countries_by_continent(self):
        """Test filtering countries by continent."""
        from engine.land.reference.data import list_countries

        asia_countries = list_countries("asia")
        assert len(asia_countries) >= 5

    def test_terrain_classifications(self):
        """Test terrain classification standards."""
        from engine.land.reference.data import TERRAIN_CLASSIFICATIONS

        assert len(TERRAIN_CLASSIFICATIONS) == 7

    def test_drainage_standards(self):
        """Test drainage density standards."""
        from engine.land.reference.data import DRAINAGE_STANDARDS

        assert len(DRAINAGE_STANDARDS) == 5


class TestIntegration:
    """Integration tests."""

    def test_full_land_analysis_workflow(self):
        """Test complete land analysis workflow."""
        from engine.land.terrain_analysis import (
            TerrainAnalyzer,
        )

        # Create DEM
        np.random.seed(42)
        dem = np.random.rand(10, 10) * 100 + 1000

        # Terrain analysis
        terrain_analyzer = TerrainAnalyzer(resolution=30.0)
        terrain = terrain_analyzer.analyze(dem, profile_id="test")

        # Basic assertions
        assert terrain.profile_id == "test"
        assert hasattr(terrain, 'slope_mean')
        assert hasattr(terrain, 'terrain_type')

        print(f"  ✅ Terrain analysis: slope_mean={terrain.slope_mean:.2f}, type={terrain.terrain_type}")

    @pytest.fixture
    def analyzer(self):
        """TerrainAnalyzer for terrain analysis tests."""
        from engine.land.terrain_analysis import TerrainAnalyzer
        return TerrainAnalyzer(resolution=30.0)

    @pytest.fixture
    def rolling_dem(self):
        """Rolling DEM for testing."""
        import numpy as np
        dem = np.zeros((15, 15))
        for i in range(15):
            for j in range(15):
                dem[i, j] = 1000.0 + 50.0 * np.sin(i / 3.0) * np.cos(j / 3.0)
        return dem

    def test_terrain_analysis_basic(self, analyzer, rolling_dem):
        """Test basic terrain analysis."""
        analysis = analyzer.analyze(rolling_dem, profile_id="test")

        assert analysis.profile_id == "test"
        assert analysis.elevation_min < analysis.elevation_max
        assert 0 <= analysis.slope_mean <= 90
        assert analysis.aspect_dominant in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


    def test_terrain_type_classification(self, analyzer):
        """Test terrain type classification."""
        from engine.land.models import TerrainType

        # Flat terrain
        flat_dem = np.full((10, 10), 1000.0)
        analysis = analyzer.analyze(flat_dem)
        assert analysis.terrain_type == TerrainType.FLAT

