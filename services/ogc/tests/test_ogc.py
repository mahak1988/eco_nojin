"""Tests for the OGC API — Features and WaterML."""

import json
import xml.etree.ElementTree as ET

from services.ogc import features, waterml


class TestWaterML:
    """Tests for the WaterML 2.0 timeseries builder."""

    SERIES = [
        {"month": "2024-01", "spi": 1.25},
        {"month": "2024-02", "spi": -0.5},
        {"month": "2024-03", "spi": 0.0},
    ]

    def test_builds_wellformed_xml(self):
        xml = waterml.build_timeseries(self.SERIES, index="spi", title="SPI")
        root = ET.fromstring(xml)
        assert root.tag.endswith("OM_Observation")

    def test_declares_the_waterml_namespace(self):
        xml = waterml.build_timeseries(self.SERIES)
        assert "http://www.opengis.net/waterml/2.0" in xml

    def test_emits_one_point_per_value(self):
        xml = waterml.build_timeseries(self.SERIES, index="spi")
        root = ET.fromstring(xml)
        wml2 = f"{{{waterml.WML_NS}}}"
        points = root.iter(wml2 + "point")
        assert len(list(points)) == 3

    def test_formats_the_values_to_three_decimals(self):
        xml = waterml.build_timeseries(self.SERIES, index="spi")
        root = ET.fromstring(xml)
        wml2 = f"{{{waterml.WML_NS}}}"
        values = [e.text for e in root.iter(wml2 + "value")]
        assert values == ["1.250", "-0.500", "0.000"]

    def test_timestamps_are_iso_zulu(self):
        xml = waterml.build_timeseries(self.SERIES, index="spi")
        root = ET.fromstring(xml)
        wml2 = f"{{{waterml.WML_NS}}}"
        times = [e.text for e in root.iter(wml2 + "time")]
        assert times[0] == "2024-01-01T00:00:00Z"
        assert times[1] == "2024-02-01T00:00:00Z"

    def test_skips_points_with_a_missing_value(self):
        series = [{"month": "2024-01", "spi": 1.0}, {"month": "2024-02"}]
        xml = waterml.build_timeseries(series, index="spi")
        root = ET.fromstring(xml)
        wml2 = f"{{{waterml.WML_NS}}}"
        assert len(list(root.iter(wml2 + "point"))) == 1

    def test_omits_nan_values_honestly(self):
        """A rolling-window warm-up NaN must not be published as a number."""
        series = [{"month": "2024-01", "spi": float("nan")}, {"month": "2024-02", "spi": 1.0}]
        xml = waterml.build_timeseries(series, index="spi")
        root = ET.fromstring(xml)
        wml2 = f"{{{waterml.WML_NS}}}"
        values = [e.text for e in root.iter(wml2 + "value")]
        assert "nan" not in " ".join(v for v in values if v)
        assert len(list(root.iter(wml2 + "point"))) == 1

    def test_skips_unparseable_values(self):
        series = [{"month": "2024-01", "spi": "not-a-number"}]
        xml = waterml.build_timeseries(series, index="spi")
        root = ET.fromstring(xml)
        wml2 = f"{{{waterml.WML_NS}}}"
        assert len(list(root.iter(wml2 + "point"))) == 0

    def test_empty_series_still_produces_a_document(self):
        xml = waterml.build_timeseries([], index="spi")
        root = ET.fromstring(xml)
        assert root.tag.endswith("OM_Observation")

    def test_index_selects_the_observed_property(self):
        xml = waterml.build_timeseries(self.SERIES, index="spei", title="SPEI")
        assert "property:OGC:spei" in xml
        assert "ts_spei" in xml

    def test_title_is_carried_in_the_point_metadata(self):
        series = [{"month": "2024-01", "spei": 0.5}]
        xml = waterml.build_timeseries(series, index="spei", title="SPEI")
        assert "SPEI" in xml


class TestOgcFeatures:
    """Tests for the OGC API — Features landing/conformance/collection payloads."""

    def test_landing_page_is_json_serialisable(self):
        assert json.dumps(features._LANDING)

    def test_landing_page_has_a_self_link(self):
        hrefs = [link["href"] for link in features._LANDING["links"]]
        assert "/ogc/features/v1/" in hrefs

    def test_conformance_declares_the_core_class(self):
        classes = features._CONFORMANCE["conformsTo"]
        assert any("conf/core" in c for c in classes)

    def test_collection_id_is_the_landscape_points(self):
        assert features.COLLECTION_ID == "landscape-points"
