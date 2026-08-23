"""Unit tests for TopographyAnalyzer."""
import pytest
from unittest.mock import Mock, patch
from engine.hydroma.analyses.topography_analysis import TopographyAnalyzer, TopographyInput
from sqlalchemy.orm import Session

@pytest.fixture
def mock_db_session():
    return Mock(spec=Session)

@patch('engine.hydroma.analyses.topography_analysis.rioxarray.open_rasterio') # Mock the file loader
@patch('engine.hydroma.analyses.topography_analysis.TopographyAnalyzer._save_geotiff') # Mock the file saver
def test_topography_analyzer_execute(mock_save_geotiff, mock_open_rasterio, mock_db_session):
    # Arrange
    mock_dem_data = Mock()
    mock_dem_data.rio.crs.to_string.return_value = 'EPSG:4326'
    mock_dem_data.rio.reproject.return_value = mock_dem_data
    mock_dem_data.squeeze.return_value = mock_dem_data
    mock_open_rasterio.return_value = mock_dem_data

    analyzer = TopographyAnalyzer(db_session=mock_db_session)
    input_data = TopographyInput(
        site_id="test_site",
        dem_path="dummy/path.tif",
        analysis_types=["slope", "aspect"]
    )

    # Act
    result = analyzer.execute(input_data)

    # Assert
    assert result.slope is not None
    assert result.aspect is not None
    # Verify the DB session methods were called
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    # Verify the save function was called for slope and aspect
    assert mock_save_geotiff.call_count == 2