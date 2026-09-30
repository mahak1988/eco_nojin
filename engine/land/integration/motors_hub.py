"""
Scientific Motors Hub
======================
Unified interface to all scientific motors with graceful degradation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class MotorStatus(StrEnum):
    """Motor availability status"""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class MotorResult:
    """Standard result from any scientific motor"""

    data_source: str = "simulated"
    model: str = ""
    computed: bool = True

    motor_name: str | None = None
    status: MotorStatus = None
    success: bool = False
    data: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    error_message: str | None = None


@dataclass
class UnifiedLandAnalysis:
    """Complete unified analysis from all motors"""

    data_source: str = "modelled"
    model: str = "motors_hub facade"
    computed: bool = True

    soil_analysis: MotorResult | None = None
    climate_analysis: MotorResult | None = None
    crop_recommendations: MotorResult | None = None
    irrigation_plan: MotorResult | None = None
    erosion_risk: MotorResult | None = None
    carbon_sequestration: MotorResult | None = None
    overall_confidence: float = 0.0
    motors_available: int = 0
    motors_total: int = 7


#: Site attributes each motor genuinely needs. A motor handed a default for
#: one of these is advising on a site that was never described, so the motor is
#: skipped rather than run on invented values.
REQUIRED_SITE_INPUTS: dict[str, tuple[str, ...]] = {
    "crop_advisor": ("soil_ph", "annual_precip_mm", "mean_temp_c"),
    "erosion": ("annual_precip_mm", "slope_pct", "rainfall_erosivity", "soil_erodibility"),
    "irrigation": ("soil_type", "soil_depth_cm", "annual_precip_mm"),
}


class _MissingSiteInput(RuntimeError):
    """Raised when a motor has no measured value for a required attribute."""


def _site_inputs(motor: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """The motor's inputs, refusing to invent a site.

    The four motors each filled their missing attributes with plausible
    constants: pH 6.5, 600 mm of rain, 20 C, 100 cm of soil. A crop
    recommendation for a site whose rainfall was invented is not a
    recommendation, and nothing in the result said so.
    """
    required = REQUIRED_SITE_INPUTS.get(motor, ())
    missing = [name for name in required if inputs.get(name) is None]
    if missing:
        raise _MissingSiteInput(
            f"{motor} needs measured site values for {', '.join(missing)}; no "
            "default is assumed, because a fabricated site produces advice "
            "that looks site-specific"
        )
    return {name: inputs.get(name) for name in required}


class ScientificMotorsHub:
    """
    Unified interface to all scientific motors.

    Features:
    - Graceful degradation (motors can be unavailable)
    - Standard result format
    - Error isolation (one motor failure doesn't affect others)
    """

    def __init__(self):
        """Initialize motors hub with lazy loading"""
        self._motors: dict[str, Any] = {}
        self._motor_status: dict[str, MotorStatus] = {}
        self._load_motors()

    def _load_motors(self):
        """Load scientific motors with error handling"""
        motor_imports = {
            "crop_advisor": ("services.scientific_motors.crop_advisor", "CropAdvisorMotor"),
            "irrigation_scheduler": (
                "services.scientific_motors.irrigation_scheduler",
                "IrrigationSchedulerMotor",
            ),
            "erosion_rusle": ("services.scientific_motors.erosion_rusle", "RUSLEMotor"),
            "rothc": ("services.scientific_motors.rothc", "RothCMotor"),
        }

        for name, (module_path, class_name) in motor_imports.items():
            try:
                import importlib

                module = importlib.import_module(module_path)
                motor_class = getattr(module, class_name)
                self._motors[name] = motor_class()
                self._motor_status[name] = MotorStatus.AVAILABLE
            except Exception:
                self._motors[name] = None
                self._motor_status[name] = MotorStatus.UNAVAILABLE

    def get_motor_status(self) -> dict[str, MotorStatus]:
        """Get status of all motors"""
        return self._motor_status.copy()

    def get_available_motors(self) -> list[str]:
        """Get list of available motor names"""
        return [
            name for name, status in self._motor_status.items() if status == MotorStatus.AVAILABLE
        ]

    def analyze_land(self, inputs: dict[str, Any]) -> UnifiedLandAnalysis:
        """Perform unified land analysis using all available motors."""
        result = UnifiedLandAnalysis()
        results_list = []

        # Run each motor with error isolation
        if self._motor_status.get("crop_advisor") == MotorStatus.AVAILABLE:
            result.crop_recommendations = self._run_crop_advisor(inputs)
            results_list.append(result.crop_recommendations)

        if self._motor_status.get("irrigation_scheduler") == MotorStatus.AVAILABLE:
            result.irrigation_plan = self._run_irrigation_scheduler(inputs)
            results_list.append(result.irrigation_plan)

        if self._motor_status.get("erosion_rusle") == MotorStatus.AVAILABLE:
            result.erosion_risk = self._run_erosion_rusle(inputs)
            results_list.append(result.erosion_risk)

        if self._motor_status.get("rothc") == MotorStatus.AVAILABLE:
            result.carbon_sequestration = self._run_rothc(inputs)
            results_list.append(result.carbon_sequestration)

        result.motors_available = len(results_list)

        if results_list:
            result.overall_confidence = sum(
                r.confidence for r in results_list if r and r.confidence
            ) / max(len(results_list), 1)

        return result

    def _run_crop_advisor(self, inputs: dict[str, Any]) -> MotorResult:
        """Run CropAdvisor motor"""
        try:
            motor = self._motors.get("crop_advisor")
            if motor is None:
                return MotorResult(
                    motor_name="crop_advisor",
                    status=MotorStatus.UNAVAILABLE,
                    error_message="Motor not loaded",
                )

            motor_input = _site_inputs("crop_advisor", inputs)

            output = motor.execute(**motor_input)

            return MotorResult(
                motor_name="crop_advisor",
                status=MotorStatus.AVAILABLE,
                success=True,
                data=output if isinstance(output, dict) else {"result": str(output)},
                recommendations=output.get("recommended_crops", [])
                if isinstance(output, dict)
                else [],
                confidence=0.8,
            )

        except Exception as e:
            return MotorResult(
                motor_name="crop_advisor",
                status=MotorStatus.ERROR,
                error_message=str(e),
            )

    def _run_irrigation_scheduler(self, inputs: dict[str, Any]) -> MotorResult:
        """Run IrrigationScheduler motor"""
        try:
            motor = self._motors.get("irrigation_scheduler")
            if motor is None:
                return MotorResult(
                    motor_name="irrigation_scheduler",
                    status=MotorStatus.UNAVAILABLE,
                    error_message="Motor not loaded",
                )

            motor_input = _site_inputs("irrigation", inputs)

            output = motor.execute(**motor_input)

            return MotorResult(
                motor_name="irrigation_scheduler",
                status=MotorStatus.AVAILABLE,
                success=True,
                data=output if isinstance(output, dict) else {"result": str(output)},
                recommendations=[],
                confidence=0.8,
            )

        except Exception as e:
            return MotorResult(
                motor_name="irrigation_scheduler",
                status=MotorStatus.ERROR,
                error_message=str(e),
            )

    def _run_erosion_rusle(self, inputs: dict[str, Any]) -> MotorResult:
        """Run RUSLE erosion motor"""
        try:
            motor = self._motors.get("erosion_rusle")
            if motor is None:
                return MotorResult(
                    motor_name="erosion_rusle",
                    status=MotorStatus.UNAVAILABLE,
                    error_message="Motor not loaded",
                )

            motor_input = _site_inputs("erosion", inputs)

            output = motor.execute(**motor_input)

            return MotorResult(
                motor_name="erosion_rusle",
                status=MotorStatus.AVAILABLE,
                success=True,
                data=output if isinstance(output, dict) else {"result": str(output)},
                recommendations=[],
                confidence=0.8,
            )

        except Exception as e:
            return MotorResult(
                motor_name="erosion_rusle",
                status=MotorStatus.ERROR,
                error_message=str(e),
            )

    def _run_rothc(self, inputs: dict[str, Any]) -> MotorResult:
        """Run RothC carbon sequestration motor"""
        try:
            motor = self._motors.get("rothc")
            if motor is None:
                return MotorResult(
                    motor_name="rothc",
                    status=MotorStatus.UNAVAILABLE,
                    error_message="Motor not loaded",
                )

            motor_input = _site_inputs("irrigation", inputs)

            output = motor.execute(**motor_input)

            return MotorResult(
                motor_name="rothc",
                status=MotorStatus.AVAILABLE,
                success=True,
                data=output if isinstance(output, dict) else {"result": str(output)},
                recommendations=[],
                confidence=0.8,
            )

        except Exception as e:
            return MotorResult(
                motor_name="rothc",
                status=MotorStatus.ERROR,
                error_message=str(e),
            )
