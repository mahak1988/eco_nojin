"""WaterML 2.0 (subset) — time-series exchange for drought indices.

Implements a scoped WaterML 2.0 response (OGC WaterML 2.0 Part 1: Timeseries,
OGC 14-111r1): om:Observation containing a wml2:MeasurementTimeseries of
SPI/SPEI values produced by the real drought motor (ERA5 via Open-Meteo).

Honesty: this is a subset (no SamplingFeatures / ComplexFeatures); the XML
declares the namespaces and structure so standard clients can parse it.
"""
import xml.etree.ElementTree as ET

WML_NS = "http://www.opengis.net/waterml/2.0"
OM_NS = "http://www.opengis.net/om/2.0"
GML_NS = "http://www.opengis.net/gml/3.2"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


def _register_ns() -> None:
    ET.register_namespace("wml2", WML_NS)
    ET.register_namespace("om", OM_NS)
    ET.register_namespace("gml", GML_NS)
    ET.register_namespace("xsi", XSI_NS)


def _timestamp(month: str) -> str:
    return f"{month[:4]}-{month[5:7]}-01T00:00:00Z"


def build_timeseries(series: list[dict], index: str = "spi", title: str = "SPI") -> str:
    """Build a WaterML 2.0 MeasurementTimeseries XML string from the motor series."""
    _register_ns()
    wml2 = "{%s}" % WML_NS
    om = "{%s}" % OM_NS
    gml = "{%s}" % GML_NS

    obs = ET.Element(om + "OM_Observation")
    obs.set("{%s}schemaLocation" % XSI_NS, f"{OM_NS} http://schemas.opengis.net/om/2.0/observation.xsd {WML_NS} http://schemas.opengis.net/waterml/2.0/waterml2.xsd")
    ET.SubElement(obs, om + "phenomenonTime").set(gml + "id", "phenTime")
    ET.SubElement(obs, om + "resultTime").set(gml + "id", "resultTime")
    ET.SubElement(obs, om + "procedure").set("{%s}href" % "{http://www.w3.org/1999/xlink}", "urn:ogc:def:procedure:EcoNojin:drought")
    ET.SubElement(obs, om + "observedProperty").set("{%s}href" % "{http://www.w3.org/1999/xlink}", f"urn:ogc:def:property:OGC:{index}")
    ET.SubElement(obs, om + "featureOfInterest").set("{%s}href" % "{http://www.w3.org/1999/xlink}", "urn:ogc:def:feature:EcoNojin:landscape")

    result = ET.SubElement(obs, om + "result")
    ts = ET.SubElement(result, wml2 + "MeasurementTimeseries")
    ts.set(gml + "id", f"ts_{index}")
    ET.SubElement(ts, wml2 + "pointMetadata")
    for point in series:
        val = point.get(index)
        if val is None:
            continue
        try:
            fval = float(val)
        except (TypeError, ValueError):
            continue
        if fval != fval:  # NaN (rolling window warm-up) is omitted honestly
            continue
        member = ET.SubElement(ts, wml2 + "point")
        meas = ET.SubElement(member, wml2 + "MeasurementTimeseriesPoint")
        ET.SubElement(meas, wml2 + "time").text = _timestamp(point.get("month", "2000-01"))
        ET.SubElement(meas, wml2 + "value").text = f"{fval:.3f}"
        ET.SubElement(meas, wml2 + "metadata").text = title

    ET.indent(obs, space="  ")
    return ET.tostring(obs, encoding="unicode", xml_declaration=True)
