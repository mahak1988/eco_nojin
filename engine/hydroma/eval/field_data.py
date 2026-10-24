"""Field data contracts for HY-RUE evaluation against empirical observations.

Defines the structured schemas for site metadata, seasonal information, and
individual field observations.  All contracts use pydantic for validation
(consistent with the rest of the codebase) and are pure data — no network or
service imports.

Provenance vocabulary:
    ``field_measured``     instrument deployed at the site.
    ``satellite_retrieved`` satellite product (e.g. Landsat NDVI, Sentinel-2 LAI).
    ``analysis_product``   reanalysis / analysis gridded product.
    ``model_generated``    derived by a model (not a measurement or satellite retrieval).
    ``synthetic``          generated for testing (SB-06 compliant when not mixed into
                            validation corpora).
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ObservationSourceLiteral = Literal[
    "field_measured",
    "satellite_retrieved",
    "analysis_product",
    "model_generated",
]

#: Units accepted for yield observations.
YIELD_UNIT = Literal["t/ha", "kg/ha", "g/m2"]

#: Units accepted for biomass observations.
BIOMASS_UNIT = Literal["t/ha", "kg/ha", "g/m2"]

#: Units accepted for LAI observations.
LAI_UNIT = Literal["index", "m2/m2"]


class VariableType(StrEnum):
    """The scientific variables that can appear in a field observation."""

    YIELD = "yield"
    BIOMASS = "biomass"
    LAI = "lai"
    PAR = "par"
    VPD = "vpd"
    SHORTWAVE = "shortwave_radiation"
    TEMPERATURE = "temperature"
    EWSI = "ewsi"
    ET = "evapotranspiration"
    SOIL_MOISTURE = "soil_moisture"
    PRECIPITATION = "precipitation"


class ObservationSource(StrEnum):
    """Source provenance for a field observation.

    Extends the string-based :data:`ObservationSourceLiteral` with a richer
    enum so that downstream code can branch on a stable type rather than
    comparing raw strings.
    """

    FIELD_MEASURED = "field_measured"
    SATELLITE_RETRIEVED = "satellite_retrieved"
    ANALYSIS_PRODUCT = "analysis_product"
    MODEL_GENERATED = "model_generated"

    @classmethod
    def from_label(cls, value: str) -> ObservationSource:
        """Map a string label to the matching enum member.

        Raises ``ValueError`` for unknown labels so typos are caught early.
        """
        try:
            return cls(value)
        except ValueError:
            valid = ", ".join(m.value for m in cls)
            raise ValueError(
                f"Unknown observation source {value!r}; expected one of: {valid}"
            ) from None


class SiteInfo(BaseModel):
    """Metadata for a field observation site.

    Attributes:
        site_id: Stable, unique identifier for the site within a dataset.
        name: Human-readable site name (optional).
        latitude: Decimal degrees, WGS84 (positive = north).
        longitude: Decimal degrees, WGS84 (positive = east).
        elevation_m: Elevation above sea level in metres.
        country: ISO country code or name.
        admin_region: State / province / district (optional).
        dataset: Name of the originating dataset or network.
    """

    model_config = {"extra": "forbid"}

    site_id: str = Field(min_length=1, description="Unique site identifier.")
    name: str | None = None
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    elevation_m: float = Field(ge=-500.0, le=8000.0)
    country: str = Field(min_length=2, max_length=2)
    admin_region: str | None = None
    dataset: str = Field(description="Originating dataset or network.")


class SeasonInfo(BaseModel):
    """Metadata describing a growing season.

    Attributes:
        crop: Crop name (e.g. ``"wheat"``, ``"maize"``, ``"rice"``).
        planting_date: ISO date string of planting.
        harvest_date: ISO date string of harvest.
        season_length_days: Number of days in the growing season.
        growing_degree_days: Accumulated GDD (optional, °C-days).
    """

    model_config = {"extra": "forbid"}

    crop: str = Field(min_length=1, description="Crop name.")
    planting_date: date
    harvest_date: date
    season_length_days: int = Field(ge=1, le=366, description="Days in growing season.")
    growing_degree_days: float | None = None

    @field_validator("harvest_date")
    @classmethod
    def harvest_after_planting(cls, v: date, info) -> date:
        planting = info.data.get("planting_date")
        if planting is not None and v < planting:
            raise ValueError(
                f"harvest_date ({v}) must not precede planting_date ({planting})"
            )
        return v

    @field_validator("season_length_days", mode="after")
    @classmethod
    def season_length_matches(cls, v: int, info) -> int:
        planting = info.data.get("planting_date")
        harvest = info.data.get("harvest_date")
        if planting is not None and harvest is not None:
            computed = (harvest - planting).days
            if abs(computed - v) > 1:
                raise ValueError(
                    f"season_length_days ({v}) does not match planting→harvest "
                    f"delta ({computed} days)"
                )
        return v


class FieldObservation(BaseModel):
    """A single field observation record.

    Attributes:
        site: Link to :class:`SiteInfo` (by ``site_id``).
        season: Link to :class:`SeasonInfo`.
        observation_id: Unique identifier for this observation.
        variable: Which variable is observed (see :class:`VariableType`).
        value: Observed numeric value.
        unit: Unit of the value.
        observation_date: When the observation was made.
        source: Provenance of the observation.
        method: Method or instrument used (optional, descriptive).
        uncertainty: Estimated uncertainty of the observation (optional).
        uncertainty_unit: Unit of the uncertainty, if provided.
        quality_flag: Quality control flag (e.g. ``"good"``, ``"suspect"``, ``"bad"``).
        metadata: Additional free-form metadata (optional).
    """

    model_config = {"extra": "forbid"}

    site: str = Field(description="Site_id linking to SiteInfo.")
    season: str = Field(description="Season identifier (crop + year).")
    observation_id: str = Field(min_length=1)
    variable: VariableType
    value: float
    unit: str = Field(min_length=1)
    observation_date: date
    source: ObservationSource = ObservationSource.FIELD_MEASURED
    method: str | None = None
    uncertainty: float | None = Field(default=None, ge=0.0)
    uncertainty_unit: str | None = None
    quality_flag: str = Field(default="good", description="QC flag: good/suspect/bad")
    metadata: dict[str, Any] | None = None

    @field_validator("value")
    @classmethod
    def reject_nan(cls, v: float) -> float:
        import math
        if math.isnan(v) or math.isinf(v):
            raise ValueError(f"value must be finite, got {v}")
        return v

    @field_validator("quality_flag")
    @classmethod
    def valid_quality_flag(cls, v: str) -> str:
        valid = {"good", "suspect", "bad", "missing", "estimated"}
        if v.lower() not in valid:
            raise ValueError(
                f"quality_flag {v!r} not in {valid}; use 'good', 'suspect', 'bad', "
                f"'missing', or 'estimated'"
            )
        return v.lower()


class EvaluationDataset(BaseModel):
    """A named, versioned collection of field observations.

    Provides a container that ties sites, seasons, and observations together
    and carries dataset-level metadata (version, citation, license).

    Attributes:
        name: Human-readable dataset name.
        version: Semantic version string.
        citation: BibTeX or plain-text citation for the dataset.
        license: License under which the data is distributed.
        sites: Dict of site_id → SiteInfo.
        seasons: Dict of season_id → SeasonInfo.
        observations: List of FieldObservation records.
    """

    model_config = {"extra": "forbid"}

    name: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+")
    citation: str | None = None
    license: str | None = None
    sites: dict[str, SiteInfo] = Field(default_factory=dict)
    seasons: dict[str, SeasonInfo] = Field(default_factory=dict)
    observations: list[FieldObservation] = Field(default_factory=list)

    def get_observations(
        self,
        variable: VariableType | str | None = None,
        site_id: str | None = None,
        min_quality: str | None = None,
    ) -> list[FieldObservation]:
        """Filter observations by variable, site, and/or quality.

        ``min_quality`` filters out observations that fail the quality gate:
        ``"good"`` keeps only ``good``; ``"suspect"`` keeps ``good`` and
        ``"suspect``; ``"bad"`` keeps everything.
        """
        quality_rank = {"good": 0, "suspect": 1, "bad": 2, "missing": 3, "estimated": -1}
        rank = quality_rank.get(min_quality, -1) if min_quality else -1

        results = self.observations
        if variable is not None:
            var_str = variable.value if isinstance(variable, VariableType) else variable
            results = [o for o in results if o.variable.value == var_str]
        if site_id is not None:
            results = [o for o in results if o.site == site_id]
        if min_quality is not None:
            results = [o for o in results if quality_rank.get(o.quality_flag, 0) <= rank]
        return results
