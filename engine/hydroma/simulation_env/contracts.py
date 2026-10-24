"""Shared data contracts for the Eco Nojin simulation environment.

Every contract in this module carries an explicit *provenance* block so that
synthetic/simulated outputs can never be presented interchangeably with
measured data.  The ``data_source`` field is forced to ``"simulated"`` and a
``SYNTHETIC`` sentinel is propagated by every simulator.

:class:`SimulationProvenance` is not the repository's value-origin
``Provenance``. It is the same fact set as a *pydantic model*, so a simulator
can flatten it into its output the way ``ResultProvenance`` does in
``engine/hydroma/provenance.py``, plus the RNG ``seed`` that makes a synthetic
run reproducible. It was renamed from ``Provenance`` on 2026-10-01 because the
name was declared four times in the tree with four different field sets, so a
reader of ``provenance.synthetic`` could not tell which of them they held. The
one value-origin record is ``services/_contracts/status.py::Provenance``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# Provenance marker reused by every simulator output.  Keeping it as a single
# constant makes it trivial to grep the codebase for honest data-labelling.
SYNTHETIC: Literal["simulated"] = "simulated"

# All simulation models are versioned here so results carry a reproducible tag.
ENGINE_VERSION = "simulation_env-v0.1"
ENGINE_LABEL = "Eco Nojin Synthetic Simulation Engine (no measured data)"


class Severity(StrEnum):
    """Qualitative severity bands shared across simulators."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


class SimulationProvenance(BaseModel):
    """Provenance / honesty block attached to every synthetic result.

    Field reconciliation against the canonical value-origin record
    (``services/_contracts/status.py::Provenance``):

    ==============  ==============  =========================================
    This block      Canonical       Why
    ==============  ==============  =========================================
    ``data_source`` ``source``      pinned to ``"simulated"``; the canonical
                                    record maps that label to ``"synthetic"``
    ``model``       ``engine``      same fact, under the engine's column name
    ``label``       ``engine``      ``ENGINE_LABEL`` is an engine name, not a
                                    separate fact -- a consumer must not read
                                    both and treat them as independent
    ``synthetic``   ``synthetic``   identical meaning
    ``computed``    ``computed``    added 2026-10-01 so this block satisfies the
                                    same structural type as the engine's
                                    ``ResultProvenance`` and converts to the
                                    canonical record with nothing dropped. It
                                    is ``True`` for any simulation that
                                    returned; ``False`` marks a result that
                                    exists only to explain its own absence.
    ``note``        ``detail``      same fact, different word
    ``seed``        ``seed``        the only field here with no counterpart,
                                    and the reason a synthetic value can be
                                    reproduced at all
    ==============  ==============  =========================================

    The ``model``/``label`` pair is the part that had no justification: both were
    fixed constants differing in capitalization, so a consumer could read
    either and both were equally true. ``label`` is kept because it is exported
    and because its constant is part of the module's public surface, but it is
    documentation rather than a claim about the run.
    """

    data_source: Literal["simulated"] = Field(
        default="simulated", description="Always 'simulated' for synthetic outputs."
    )
    model: str = Field(default=ENGINE_VERSION)
    label: str = Field(default=ENGINE_LABEL)
    seed: int | None = Field(default=None, description="RNG seed for reproducibility.")
    synthetic: bool = Field(default=True)
    computed: bool = Field(
        default=True,
        description="False when the run produced nothing and this block only says why.",
    )
    note: str = Field(default="Synthetic output; not field measurement.")


class SimulationMetadata(BaseModel):
    """Metadata describing a single simulation execution."""

    scenario: str
    site_id: str
    seed: int
    start_year: int
    end_year: int
    provenance: SimulationProvenance = Field(default_factory=SimulationProvenance)
    parameters: dict[str, Any] = Field(default_factory=dict)


def make_provenance(seed: int | None) -> SimulationProvenance:
    """Build a provenance block for a seeded run."""
    return SimulationProvenance(seed=seed)


class AnnualImpact(BaseModel):
    """Per-year aggregate impact from a stressor simulation."""

    year: int
    temperature_c: float
    precipitation_mm: float
    et0_mm: float
    soil_moisture_mm: float
    soil_moisture_fraction: float
    ndvi: float = Field(..., ge=-1.0, le=1.0)
    crop_yield_kg_ha: float | None = None
    erosion_t_ha: float | None = None
    drought_stress: float = Field(..., ge=0.0, le=1.0)
    severity: str = Severity.MILD.value


class ClimateProfile(BaseModel):
    """A full synthetic climate time-series snapshot."""

    data_source: str = "simulated"
    model: str = "simulation_env synthetic climate"

    lat: float | None = None
    lon: float | None = None
    baseline_temp_c: float | None = None
    baseline_precip_mm: float | None = None
    years: list[AnnualImpact] | None = None
    metadata: SimulationMetadata | None = None

    @field_validator("years")
    @classmethod
    def _sorted_years(cls, v: list[AnnualImpact]) -> list[AnnualImpact]:
        return sorted(v, key=lambda a: a.year)


class DisasterImpact(BaseModel):
    """Impact summary for a natural-disaster simulation."""

    hazard: str
    severity: str
    affected_area_ha: float
    mean_intensity: float
    economic_loss_usd: float
    key_metrics: dict[str, float] = Field(default_factory=dict)
    metadata: SimulationMetadata


class StressTestResult(SimulationProvenance, BaseModel):
    """Result of a single stress-test injection."""

    test_name: str
    scenario: str
    passed: bool
    detail: str
    metric: float | None = None
    metadata: SimulationMetadata


# Sentinel values for the seasonal calendar of a Mediterranean-like baseline.
# These are reference fractions of annual precipitation falling per month
# (sum to 1.0).  They are synthetic reference data, not measured.
DEFAULT_MONTHLY_PRECT_FRAC: list[float] = [
    0.07,
    0.06,
    0.05,
    0.04,
    0.04,
    0.03,
    0.02,
    0.02,
    0.03,
    0.06,
    0.08,
    0.09,
]
