"""Abstract base class for all scientific motors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class MotorType(StrEnum):
    """Supported scientific motor types.

    Extended during the phase 4 S-SCI consolidation. The enum previously had
    six members, and eleven motors were forced to report a wrong one — seven
    claimed ``BIOFERTILIZER`` and two claimed ``WHAT_IF``, one of them with the
    comment ``# reuse enum slot``. A consumer filtering by motor type therefore
    received erosion, land-capability and irrigation motors filed as
    biofertilizer work.

    Every value here is a distinct scientific domain. If a new motor does not
    fit any of them, add a member rather than borrowing one.
    """

    # --- hydrology -----------------------------------------------------
    SWAT_PLUS = "swat_plus"
    HEC_RAS = "hec_ras"

    # --- crop ----------------------------------------------------------
    AQUACROP = "aquacrop"

    # --- soil and carbon -----------------------------------------------
    ROTH_C = "roth_c"
    CARBON_SEQ = "carbon_seq"
    LAND_CAPABILITY = "land_capability"
    EROSION_RUSLE = "erosion_rusle"

    # --- agronomy ------------------------------------------------------
    BIOFERTILIZER = "biofertilizer"
    IRRIGATION = "irrigation"
    CROP_ADVISOR = "crop_advisor"
    PLANTING_CALENDAR = "planting_calendar"
    CROP_DATABASE = "crop_database"

    # --- climate and risk ---------------------------------------------
    DROUGHT = "drought"
    CLIMATE = "climate"
    WHAT_IF = "what_if"

    # --- measurement, reporting and planning --------------------------
    MRV = "mrv"
    CARBON_MRV = "carbon_mrv"
    SATELLITE = "satellite"
    ECONOMY = "economy"
    OPTIMIZER = "optimizer"
    CALIBRATION = "calibration"
    MAP_ENGINE = "map_engine"


class MotorStatus(StrEnum):
    """Motor execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MotorInput:
    """Input requirement for a motor."""

    name: str
    data_type: str  # "raster", "vector", "timeseries", "scalar"
    required: bool = True
    description: str = ""


@dataclass
class MotorOutput:
    """Output produced by a motor."""

    name: str
    data_type: str
    units: str
    description: str


@dataclass
class MotorParameters:
    """Parameters for motor execution."""

    start_date: str
    end_date: str
    time_step: str = "daily"
    scenario_name: str = "baseline"
    custom_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class MotorResult:
    """Result of motor execution."""

    run_id: str
    motor_type: MotorType
    status: MotorStatus
    outputs: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "run_id": self.run_id,
            "motor_type": self.motor_type.value,
            "status": self.status.value,
            "outputs": self.outputs,
            "summary": self.summary,
            "execution_time_seconds": self.execution_time_seconds,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }


class AbstractScientificMotor(ABC):
    """Abstract base class for scientific motors."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path("data/motors/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    @abstractmethod
    def motor_type(self) -> MotorType:
        """Type of this motor."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name."""
        pass

    @abstractmethod
    def get_input_requirements(self) -> list[MotorInput]:
        """Return list of required inputs."""
        pass

    @abstractmethod
    def get_outputs(self) -> list[MotorOutput]:
        """Return list of outputs."""
        pass

    @abstractmethod
    async def execute(
        self,
        inputs: dict[str, Any],
        parameters: MotorParameters,
    ) -> MotorResult:
        """Execute the motor with given inputs and parameters."""
        pass

    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """Validate that all required inputs are present."""
        requirements = self.get_input_requirements()
        return all(not (req.required and req.name not in inputs) for req in requirements)
