"""Abstract base class for all scientific motors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class MotorType(str, Enum):
    """Supported scientific motor types."""
    SWAT_PLUS = "swat_plus"
    AQUACROP = "aquacrop"
    ROTH_C = "roth_c"
    HEC_RAS = "hec_ras"
    WHAT_IF = "what_if"
    BIOFERTILIZER = "biofertilizer"


class MotorStatus(str, Enum):
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
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MotorResult:
    """Result of motor execution."""
    run_id: str
    motor_type: MotorType
    status: MotorStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
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

    def __init__(self, cache_dir: Optional[Path] = None):
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
    def get_input_requirements(self) -> List[MotorInput]:
        """Return list of required inputs."""
        pass

    @abstractmethod
    def get_outputs(self) -> List[MotorOutput]:
        """Return list of outputs."""
        pass

    @abstractmethod
    async def execute(
        self,
        inputs: Dict[str, Any],
        parameters: MotorParameters,
    ) -> MotorResult:
        """Execute the motor with given inputs and parameters."""
        pass

    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate that all required inputs are present."""
        requirements = self.get_input_requirements()
        for req in requirements:
            if req.required and req.name not in inputs:
                return False
        return True