"""
Tests for GBIF Connector
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from engine.hydroma.data_pipeline.pipeline import (
    DataAsset,
    GBIFConnector,
    get_pipeline,
)


class TestGBIFConnector:
    """Tests for GBIFConnector."""

    def setup_method(self):
        """Setup test fixtures."""
        self.connector = GBIFConnector(cache_dir=Path("data/cache/test_gbif"))

    def test_connector_initialization(self):
        """Test connector initializes with correct source config."""
        assert self.connector.source.source_id == "gbif"
        assert self.connector.source.name == "GBIF"
        assert self.connector.source.base_url == "https://api.gbif.org/v1"
        assert self.connector.source.auth_type == "none"
        assert self.connector.source.format == "json"

    def test_build_occurrence_query_bbox(self):
        """Test building occurrence query with bbox."""
        query = {
            "bbox": [44.0, 25.0, 63.0, 40.0],  # Iran bbox
            "taxon_key": 2435099,  # Panthera
            "year": "2020,2024",
            "has_coordinate": True,
        }
        params = self.connector._build_occurrence_query(query)

        assert "geometry" in params
        assert "POLYGON" in params["geometry"]
        assert params["taxonKey"] == 2435099
        assert params["year"] == "2020,2024"
        assert params["hasCoordinate"] == "true"

    def test_build_occurrence_query_country(self):
        """Test building occurrence query with country."""
        query = {
            "country": "IR",
            "basis_of_record": "HUMAN_OBSERVATION",
            "has_geospatial_issue": False,
        }
        params = self.connector._build_occurrence_query(query)

        assert params["country"] == "IR"
        assert params["basisOfRecord"] == "HUMAN_OBSERVATION"
        assert params["hasGeospatialIssue"] == "false"

    def test_build_occurrence_query_scientific_name(self):
        """Test building occurrence query with scientific name."""
        query = {
            "scientific_name": "Panthera leo",
            "rank": "SPECIES",
        }
        params = self.connector._build_occurrence_query(query)

        assert params["scientificName"] == "Panthera leo"
        assert params["rank"] == "SPECIES"

    @patch("requests.get")
    def test_fetch_occurrences_success(self, mock_get):
        """Test successful occurrence fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "count": 150,
            "results": [
                {
                    "key": 1,
                    "scientificName": "Panthera leo",
                    "decimalLatitude": 35.0,
                    "decimalLongitude": 51.0,
                },
                {
                    "key": 2,
                    "scientificName": "Panthera pardus",
                    "decimalLatitude": 36.0,
                    "decimalLongitude": 52.0,
                },
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        query = {
            "type": "occurrence",
            "bbox": [44.0, 25.0, 63.0, 40.0],
            "taxon_key": 2435099,
            "max_records": 500,
        }
        assets = self.connector.fetch(query)

        assert len(assets) == 1
        assert assets[0].source_id == "gbif"
        assert "occurrence" in assets[0].asset_id
        assert assets[0].metadata["total_results"] == 150
        assert assets[0].metadata["returned"] == 2

    @patch("requests.get")
    def test_fetch_checklist_country(self, mock_get):
        """Test fetching country checklist."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "count": 5000,
            "results": [
                {"key": 1, "scientificName": "Quercus brantii", "rank": "SPECIES"},
                {"key": 2, "scientificName": "Pistacia atlantica", "rank": "SPECIES"},
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        query = {
            "type": "checklist",
            "country": "IR",
        }
        assets = self.connector.fetch(query)

        assert len(assets) == 1
        assert assets[0].source_id == "gbif"
        assert "checklist" in assets[0].asset_id
        assert assets[0].metadata["country"] == "IR"
        assert assets[0].metadata["total_species"] == 5000

    @patch("requests.get")
    def test_fetch_species_by_key(self, mock_get):
        """Test fetching species by key."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "key": 2435099,
            "scientificName": "Panthera",
            "rank": "GENUS",
            "phylum": "Chordata",
            "class": "Mammalia",
            "order": "Carnivora",
            "family": "Felidae",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        query = {
            "type": "species",
            "species_key": 2435099,
        }
        assets = self.connector.fetch(query)

        assert len(assets) == 1
        assert assets[0].source_id == "gbif"
        assert "species" in assets[0].asset_id
        assert assets[0].metadata["species_key"] == 2435099

    @patch("requests.get")
    def test_fetch_species_by_name(self, mock_get):
        """Test fetching species by scientific name."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "usageKey": 2435099,
            "scientificName": "Panthera leo",
            "rank": "SPECIES",
            "status": "ACCEPTED",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        query = {
            "type": "species",
            "scientific_name": "Panthera leo",
        }
        assets = self.connector.fetch(query)

        assert len(assets) == 1
        assert assets[0].metadata["scientific_name"] == "Panthera leo"

    @patch("requests.get")
    def test_fetch_dataset(self, mock_get):
        """Test fetching dataset metadata."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "key": "50c9509d-22c7-4a22-a47d-8c48425ef4a7",
            "title": "Mammals of Iran",
            "publisher": "Iran Department of Environment",
            "type": "OCCURRENCE",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        query = {
            "type": "dataset",
            "dataset_key": "50c9509d-22c7-4a22-a47d-8c48425ef4a7",
        }
        assets = self.connector.fetch(query)

        assert len(assets) == 1
        assert assets[0].source_id == "gbif"
        assert "dataset" in assets[0].asset_id
        assert assets[0].metadata["dataset_key"] == "50c9509d-22c7-4a22-a47d-8c48425ef4a7"

    def test_validate_valid_asset(self):
        """Test validation of valid asset."""
        # Create a temp file with GBIF-like data
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"results": [], "count": 0}, f)
            temp_path = Path(f.name)

        try:
            asset = DataAsset(
                asset_id="test",
                source_id="gbif",
                name="test",
                description="test",
                file_path=temp_path,
                format="json",
                size_bytes=temp_path.stat().st_size,
                checksum="abc",
            )
            assert self.connector.validate(asset) is True
        finally:
            temp_path.unlink()

    def test_validate_invalid_asset(self):
        """Test validation of invalid asset."""
        asset = DataAsset(
            asset_id="test",
            source_id="gbif",
            name="test",
            description="test",
            file_path=Path("nonexistent.json"),
            format="json",
            size_bytes=0,
            checksum="abc",
        )
        assert self.connector.validate(asset) is False


class TestGBIFPipelineIntegration:
    """Integration tests for GBIF in pipeline."""

    def test_gbif_registered_in_pipeline(self):
        """Test GBIF connector is registered in global pipeline."""
        pipeline = get_pipeline()
        assert "gbif" in pipeline.connectors
        assert isinstance(pipeline.connectors["gbif"], GBIFConnector)

    @patch("requests.get")
    def test_pipeline_fetch_gbif_occurrences(self, mock_get):
        """Test fetching GBIF data through pipeline."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "count": 10,
            "results": [{"key": 1, "scientificName": "Test species"}],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        pipeline = get_pipeline()
        assets = pipeline.fetch_data(
            "gbif",
            {
                "type": "occurrence",
                "country": "IR",
                "max_records": 10,
            },
        )

        assert len(assets) >= 1
        assert assets[0].source_id == "gbif"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
