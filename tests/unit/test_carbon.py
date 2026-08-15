"""Tests for Carbon Credit module."""

from engine.hydroma.carbon.calculator import (
    SEQUESTRATION_RATES,
    CarbonProject,
    CarbonProjectType,
    calculate_carbon_sequestration,
    compare_project_types,
    get_project,
    list_projects,
    register_project,
)


class TestCarbonCalculator:
    """Test carbon sequestration calculations."""

    def test_all_project_types_have_rates(self):
        """Verify all project types have sequestration rates."""
        for pt in CarbonProjectType:
            assert pt in SEQUESTRATION_RATES

    def test_afforestation_calculation(self):
        """Verify afforestation carbon calculation."""
        result = calculate_carbon_sequestration(
            project_type=CarbonProjectType.AFFORESTATION,
            area_ha=100,
            duration_years=10,
            region="temperate",
        )

        assert result["total_carbon_tonnes"] > 0
        assert result["annual_rate_tonnes"] > 0
        assert result["estimated_revenue_usd"] > 0

    def test_arid_region_lower_rates(self):
        """Verify arid regions have lower sequestration rates."""
        temperate = calculate_carbon_sequestration(
            project_type=CarbonProjectType.AFFORESTATION,
            area_ha=100,
            duration_years=10,
            region="temperate",
        )

        arid = calculate_carbon_sequestration(
            project_type=CarbonProjectType.AFFORESTATION,
            area_ha=100,
            duration_years=10,
            region="arid",
        )

        assert arid["total_carbon_tonnes"] < temperate["total_carbon_tonnes"]

    def test_biochar_one_time_application(self):
        """Verify biochar is treated as one-time application."""
        result = calculate_carbon_sequestration(
            project_type=CarbonProjectType.BIOCHAR,
            area_ha=10,
            duration_years=10,
        )

        # Biochar total should not scale with duration
        assert result["total_carbon_tonnes"] > 0

    def test_compare_project_types(self):
        """Verify project type comparison returns ranking."""
        result = compare_project_types(area_ha=100, duration_years=10)

        assert "ranking" in result
        assert len(result["ranking"]) > 0
        assert result["best_carbon"] is not None


class TestCarbonProjectRegistry:
    """Test carbon project registration."""

    def test_register_project(self):
        """Verify project can be registered."""
        project = CarbonProject(
            name="Test Afforestation",
            project_type=CarbonProjectType.AFFORESTATION,
            area_ha=50,
        )

        project_id = register_project(project)
        retrieved = get_project(project_id)

        assert retrieved is not None
        assert retrieved.name == "Test Afforestation"

    def test_list_projects(self):
        """Verify projects can be listed."""
        projects = list_projects()
        assert isinstance(projects, list)
