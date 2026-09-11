"""Phenology module based on Growing Degree Days (GDD).

Implements stage-specific GDD accumulation for major crops, mapping thermal
time to phenological stages used by AquaCrop and FAO-56.

Honesty: GDD parameters are generic averages from FAO literature; local
calibration is required for production use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class CropPhenology:
    """GDD thresholds and stage durations for a crop."""

    name: str
    t_base: float = 10.0
    gdd_emergence: float = 100.0
    gdd_tillering: float = 300.0
    gdd_flowering: float = 600.0
    gdd_maturity: float = 900.0


# Reference GDD parameters (FAO literature averages)
CROP_PHENOLOGY: dict[str, CropPhenology] = {
    "wheat": CropPhenology(name="wheat", t_base=10.0, gdd_emergence=120.0, gdd_tillering=350.0, gdd_flowering=650.0, gdd_maturity=950.0),
    "maize": CropPhenology(name="maize", t_base=10.0, gdd_emergence=90.0, gdd_tillering=280.0, gdd_flowering=550.0, gdd_maturity=850.0),
    "rice": CropPhenology(name="rice", t_base=10.0, gdd_emergence=80.0, gdd_tillering=250.0, gdd_flowering=500.0, gdd_maturity=800.0),
    "soybean": CropPhenology(name="soybean", t_base=10.0, gdd_emergence=100.0, gdd_tillering=300.0, gdd_flowering=580.0, gdd_maturity=880.0),
    "potato": CropPhenology(name="potato", t_base=7.0, gdd_emergence=110.0, gdd_tillering=320.0, gdd_flowering=600.0, gdd_maturity=900.0),
    "tomato": CropPhenology(name="tomato", t_base=10.0, gdd_emergence=90.0, gdd_tillering=260.0, gdd_flowering=520.0, gdd_maturity=820.0),
    "cotton": CropPhenology(name="cotton", t_base=15.0, gdd_emergence=100.0, gdd_tillering=300.0, gdd_flowering=580.0, gdd_maturity=880.0),
    "sorghum": CropPhenology(name="sorghum", t_base=12.0, gdd_emergence=95.0, gdd_tillering=290.0, gdd_flowering=560.0, gdd_maturity=860.0),
    "barley": CropPhenology(name="barley", t_base=10.0, gdd_emergence=115.0, gdd_tillering=340.0, gdd_flowering=640.0, gdd_maturity=940.0),
    "default": CropPhenology(name="default", t_base=10.0, gdd_emergence=100.0, gdd_tillering=300.0, gdd_flowering=580.0, gdd_maturity=880.0),
}


@dataclass
class PhenologyInput:
    """Inputs for a phenology run."""

    crop: str = "wheat"
    tmin_daily: list[float] = field(default_factory=list)
    tmax_daily: list[float] = field(default_factory=list)
    planting_date_doy: int = 90
    harvest_date_doy: int = 280


@dataclass
class PhenologyOutput:
    """Phenology simulation result."""

    crop: str
    gdd_series: list[float] = field(default_factory=list)
    cumulative_gdd: list[float] = field(default_factory=list)
    stages: list[str] = field(default_factory=list)
    current_stage: str = "pre_planting"
    days_to_flowering: int = -1
    days_to_maturity: int = -1
    data_source: str = "simulated"
    model: str = "GDD phenology (FAO literature parameters)"


def _daily_gdd(tmin: float, tmax: float, t_base: float) -> float:
    """Daily GDD = max(0, (Tmax+Tmin)/2 - Tbase)."""
    t_mean = (tmin + tmax) / 2.0
    return max(0.0, t_mean - t_base)


def _stage_from_gdd(gdd: float, pheno: CropPhenology) -> str:
    if gdd < pheno.gdd_emergence:
        return "pre_emergence"
    if gdd < pheno.gdd_tillering:
        return "emergence"
    if gdd < pheno.gdd_flowering:
        return "vegetative"
    if gdd < pheno.gdd_maturity:
        return "reproductive"
    return "maturity"


def run_phenology(inputs: PhenologyInput) -> PhenologyOutput:
    """Run GDD-based phenology simulation.

    Args:
        inputs: crop choice, daily temperatures, planting/harvest window.

    Returns:
        PhenologyOutput with daily GDD, cumulative GDD, and stage labels.
    """
    pheno = CROP_PHENOLOGY.get(inputs.crop.lower(), CROP_PHENOLOGY["default"])
    tmin = inputs.tmin_daily
    tmax = inputs.tmax_daily
    n = min(len(tmin), len(tmax))

    gdd_series: list[float] = []
    cum_gdd: list[float] = []
    stages: list[str] = []
    cumulative = 0.0
    stage = "pre_planting"
    days_to_flowering = -1
    days_to_maturity = -1

    for i in range(n):
        gdd = _daily_gdd(tmin[i], tmax[i], pheno.t_base)
        cumulative += gdd
        stage = _stage_from_gdd(cumulative, pheno)

        gdd_series.append(round(gdd, 4))
        cum_gdd.append(round(cumulative, 4))
        stages.append(stage)

        if days_to_flowering == -1 and cumulative >= pheno.gdd_flowering:
            days_to_flowering = i + 1
        if days_to_maturity == -1 and cumulative >= pheno.gdd_maturity:
            days_to_maturity = i + 1

    return PhenologyOutput(
        crop=inputs.crop,
        gdd_series=gdd_series,
        cumulative_gdd=cum_gdd,
        stages=stages,
        current_stage=stages[-1] if stages else "pre_planting",
        days_to_flowering=days_to_flowering,
        days_to_maturity=days_to_maturity,
    )
