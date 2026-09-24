"""Scenario Agent — What-if analysis with drought indices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from services.analysis.drought_agent import get_drought_agent


@dataclass
class ScenarioConfig:
    base_lat: float
    base_lon: float
    precip_change_pct: float = 0.0  # e.g., -20 for 20% reduction
    temp_change_c: float = 0.0
    months: int = 6


class ScenarioAgent:
    """Runs what-if scenarios by modifying weather inputs and recalculating indices."""

    def __init__(self, config: ScenarioConfig | None = None):
        self.config = config
        self.drought_agent = get_drought_agent()

    async def run_scenario(
        self,
        precip_change_pct: float = 0.0,
        temp_change_c: float = 0.0,
        months: int = 6,
    ) -> dict[str, Any]:
        """Run a single scenario with modified weather."""
        # Get baseline data
        baseline = await self.drought_agent.analyze(
            self.config.base_lat,
            self.config.base_lon,
            months=months,
        )

        if "error" in baseline:
            return baseline

        # We need raw data to modify - fetch again
        from services.analysis.drought_agent import DroughtAgent
        agent = DroughtAgent()
        df = await agent._fetch_weather(self.config.base_lat, self.config.base_lon, months)
        await agent.close()

        if df.empty:
            return {"error": "No data for scenario"}

        # Modify data
        precip_modified = df["precip"].values * (1 + precip_change_pct / 100)
        temp_modified = df.get("t2m_mean", (df["t2m_max"] + df["t2m_min"]) / 2).values + temp_change_c

        # Recalculate PET if temperature changed
        if temp_change_c != 0:
            tmax = df["t2m_max"].values + temp_change_c
            tmin = df["t2m_min"].values + temp_change_c
            tmean = (tmax + tmin) / 2
            if "solar" in df.columns:
                ra = df["solar"].values * 0.0864
            else:
                ra = np.ones_like(tmean) * 15  # Default
            pet_modified = 0.0023 * (tmean + 17.8) * np.sqrt(np.maximum(tmax - tmin, 0)) * ra
        else:
            pet_modified = df.get("et0", df.get("solar", np.ones_like(precip) * 5)).values

        # Calculate indices with modified data
        from xclim.indices import spi as spi_fn, spei as spei_fn
        import xarray as xr

        def calc_spi(data, scale):
            da = xr.DataArray(data, dims=["time"], coords={"time": np.arange(len(data))})
            return float(spi_fn(da, freq=f"{scale}MS").values[-1])

        def calc_spei(precip, pet, scale):
            da_p = xr.DataArray(precip, dims=["time"], coords={"time": np.arange(len(precip))})
            da_pe = xr.DataArray(pet, dims=["time"], coords={"time": np.arange(len(pet))})
            return float(spei_fn(da_p, da_pe, freq=f"{scale}MS").values[-1])

        scales = [1, 3, 6, 12]
        scenario_results = {
            "parameters": {
                "precip_change_pct": precip_change_pct,
                "temp_change_c": temp_change_c,
            },
            "spi": {},
            "spei": {},
            "changes": {},
        }

        for scale in scales:
            if len(precip_modified) >= scale * 30:
                base_spi = baseline["spi"].get(f"{scale}month", {}).get("value", 0)
                base_spei = baseline["spei"].get(f"{scale}month", {}).get("value", 0)

                new_spi = calc_spi(precip_modified, scale)
                new_spei = calc_spei(precip_modified, pet_modified, scale)

                scenario_results["spi"][f"{scale}month"] = {
                    "value": round(new_spi, 2),
                    "change": round(new_spi - base_spi, 2),
                }
                scenario_results["spei"][f"{scale}month"] = {
                    "value": round(new_spei, 2),
                    "change": round(new_spei - base_spei, 2),
                }
                scenario_results["changes"][f"{scale}month"] = {
                    "spi_delta": round(new_spi - base_spi, 2),
                    "spei_delta": round(new_spei - base_spei, 2),
                }

        return scenario_results

    async def run_multiple_scenarios(
        self,
        scenarios: list[dict[str, float]],
        months: int = 6,
    ) -> list[dict[str, Any]]:
        """Run multiple scenarios and return ranked results."""
        results = []
        for s in scenarios:
            result = await self.run_scenario(
                precip_change_pct=s.get("precip_change_pct", 0),
                temp_change_c=s.get("temp_change_c", 0),
                months=months,
            )
            result["scenario_name"] = s.get("name", f"Scenario {len(results)+1}")
            results.append(result)

        # Rank by SPI change (more negative = worse drought)
        for r in results:
            r["severity_score"] = r.get("changes", {}).get("3month", {}).get("spi_delta", 0)

        results.sort(key=lambda x: x.get("severity_score", 0))
        return results


def get_scenario_agent(lat: float, lon: float) -> ScenarioAgent:
    return ScenarioAgent(lat, lon)