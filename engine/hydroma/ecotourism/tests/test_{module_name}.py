"""
Unit tests for ecotourism module.
"""
import pytest
from engine.hydroma.ecotourism import EcotourismService


class TestEcotourismService:
    """Tests for EcotourismService."""
    
    @pytest.fixture
    def service(self):
        """Create service instance."""
        return EcotourismService()
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service is not None
    
    def test_process_valid_data(self, service):
        """Test processing valid data."""
        data = {"key": "value"}
        result = service.process(data)
        assert result["status"] == "success"
    
    def test_process_empty_data(self, service):
        """Test processing empty data raises error."""
        with pytest.raises(ValueError):
            service.process({})
    
    def test_validate_input_valid(self, service):
        """Test input validation with valid data."""
        data = {"key": "value"}
        assert service.validate_input(data) is True
    
    def test_validate_input_empty(self, service):
        """Test input validation with empty data."""
        assert service.validate_input({}) is False


class TestUtils:
    """Tests for utility functions."""
    
    def test_validate_range_valid(self):
        """Test range validation with valid value."""
        from engine.hydroma.ecotourism.utils import validate_range
        validate_range(50, 0, 100, "test")  # Should not raise
    
    def test_validate_range_invalid(self):
        """Test range validation with invalid value."""
        from engine.hydroma.ecotourism.utils import validate_range
        with pytest.raises(ValueError):
            validate_range(150, 0, 100, "test")
    
    def test_normalize_percentage_valid(self):
        """Test percentage normalization."""
        from engine.hydroma.ecotourism.utils import normalize_percentage
        assert normalize_percentage(50) == 50
        assert normalize_percentage(150) == 100
    
    def test_normalize_percentage_negative(self):
        """Test percentage normalization with negative value."""
        from engine.hydroma.ecotourism.utils import normalize_percentage
        with pytest.raises(ValueError):
            normalize_percentage(-10)
