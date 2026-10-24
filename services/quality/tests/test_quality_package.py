"""Tests for the ``services.quality`` package marker."""

import pathlib


class TestQualityPackage:
    """``services/quality`` is a marker package; the contract is that it
    imports cleanly and that pytest can collect a module beneath it."""

    def test_the_package_imports(self):
        import services.quality
        assert services.quality is not None

    def test_the_package_has_a_marker(self):
        """Without a marker this resolved as a PEP 420 namespace package and
        ``services/map_engine/tests/test_integration.py`` failed collection."""
        marker = pathlib.Path(__file__).resolve().parents[1] / "__init__.py"
        assert marker.exists()

    def test_the_marker_documents_why_it_exists(self):
        marker = pathlib.Path(__file__).resolve().parents[1] / "__init__.py"
        text = marker.read_text(encoding="utf-8")
        assert "namespace package" in text
