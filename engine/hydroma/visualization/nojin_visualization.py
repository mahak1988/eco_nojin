"""
Nojin Visualization Layer - Maps and Charts
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GeoJSONFeature:
    type: str = "Feature"
    geometry: dict[str, Any] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)

@dataclass
class GeoJSONCollection:
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature] = field(default_factory=list)

@dataclass
class ChartDataset:
    label: str
    data: list[float]
    borderColor: str = "#3b82f6"
    backgroundColor: str = "rgba(59, 130, 246, 0.1)"
    fill: bool = True

@dataclass
class ChartConfig:
    type: str
    labels: list[str]
    datasets: list[ChartDataset]
    title: str = ""
    x_label: str = ""
    y_label: str = ""

class ProjectMapper:
    def __init__(self):
        pass

    def create_project_geojson(self, projects: list[dict]) -> GeoJSONCollection:
        features = []
        for proj in projects:
            feature = GeoJSONFeature(
                geometry={"type": "Point", "coordinates": [proj["lon"], proj["lat"]]},
                properties={
                    "project_id": proj["id"], "name": proj["name"],
                    "area_ha": proj["area_ha"], "status": proj["status"],
                    "soil_type": proj.get("soil_type", "Unknown"),
                    "carbon_sequestered_t": proj.get("carbon_t", 0)
                }
            )
            features.append(feature)
        return GeoJSONCollection(features=features)

    def create_heatmap_data(self, projects: list[dict], weight_field: str = "carbon_sequestered_t") -> dict:
        points = []
        for proj in projects:
            points.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [proj["lon"], proj["lat"]]},
                "properties": {"weight": proj.get(weight_field, 1)}
            })
        return {"type": "FeatureCollection", "features": points}

class TimeSeriesChartBuilder:
    def create_ndvi_chart(self, observations: list[dict]) -> ChartConfig:
        labels = [obs["date"].isoformat() for obs in observations]
        values = [obs.get("ndvi", 0) for obs in observations]
        dataset = ChartDataset(
            label="NDVI", data=values, borderColor="#22c55e",
            backgroundColor="rgba(34, 197, 94, 0.1)"
        )
        return ChartConfig(
            type="line", labels=labels, datasets=[dataset],
            title="NDVI Over Time", x_label="Date", y_label="NDVI"
        )

    def create_carbon_chart(self, yearly_data: list[dict]) -> ChartConfig:
        labels = [str(d["year"]) for d in yearly_data]
        values = [d["co2_tons"] for d in yearly_data]
        dataset = ChartDataset(
            label="CO2 Sequestered (tons)", data=values, borderColor="#10b981",
            backgroundColor="rgba(16, 185, 129, 0.7)", fill=False
        )
        return ChartConfig(
            type="bar", labels=labels, datasets=[dataset],
            title="Annual Carbon Sequestration", x_label="Year", y_label="CO2 (tons)"
        )

class EconomicChartBuilder:
    def create_roi_comparison(self, scenarios: list[dict]) -> ChartConfig:
        labels = [s["name"] for s in scenarios]
        roi_values = [s["roi_percent"] for s in scenarios]
        dataset = ChartDataset(
            label="ROI %", data=roi_values, borderColor="#f59e0b",
            backgroundColor="rgba(245, 158, 11, 0.7)", fill=False
        )
        return ChartConfig(
            type="bar", labels=labels, datasets=[dataset],
            title="ROI Comparison Across Scenarios", x_label="Scenario", y_label="ROI %"
        )

    def create_cost_benefit_breakdown(self, breakdown: dict) -> ChartConfig:
        labels = list(breakdown.keys())
        values = list(breakdown.values())
        dataset = ChartDataset(
            label="Cost/Benefit Breakdown", data=values,
            borderColor="#ffffff", backgroundColor="rgba(59, 130, 246, 0.7)"
        )
        return ChartConfig(type="doughnut", labels=labels, datasets=[dataset],
                          title="Cost vs Benefit Breakdown")

class WaterVisualization:
    def create_water_savings_chart(self, monthly_data: list[dict]) -> ChartConfig:
        labels = [d["month"] for d in monthly_data]
        baseline = [d["baseline_m3"] for d in monthly_data]
        optimized = [d["optimized_m3"] for d in monthly_data]
        baseline_dataset = ChartDataset(
            label="Baseline Irrigation", data=baseline, borderColor="#ef4444",
            backgroundColor="rgba(239, 68, 68, 0.3)"
        )
        optimized_dataset = ChartDataset(
            label="With Nojin", data=optimized, borderColor="#10b981",
            backgroundColor="rgba(16, 185, 129, 0.3)"
        )
        return ChartConfig(
            type="bar", labels=labels, datasets=[baseline_dataset, optimized_dataset],
            title="Monthly Water Usage Comparison", x_label="Month", y_label="Water (m3/ha)"
        )

__all__ = [
    "ChartConfig",
    "EconomicChartBuilder",
    "GeoJSONCollection",
    "ProjectMapper",
    "TimeSeriesChartBuilder",
    "WaterVisualization"
]
