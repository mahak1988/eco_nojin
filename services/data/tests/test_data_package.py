"""Tests for the ``services.data`` package (map/report assets)."""

import pathlib


class TestDataPackage:
    """The data package holds static assets, so the contract is its layout."""

    def test_the_package_imports(self):
        import services.data
        assert services.data is not None

    def test_the_package_has_a_marker(self):
        """A PEP 420 namespace package would break pytest collection."""
        marker = pathlib.Path(__file__).resolve().parents[1] / "__init__.py"
        assert marker.exists()

    def test_the_maps_directory_exists(self):
        maps = pathlib.Path(__file__).resolve().parents[1] / "maps"
        assert maps.is_dir()

    def test_the_reports_directory_exists(self):
        reports = pathlib.Path(__file__).resolve().parents[1] / "reports"
        assert reports.is_dir()
