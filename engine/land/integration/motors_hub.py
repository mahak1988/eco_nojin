"""
Scientific Motors Hub
======================
Unified interface to all scientific motors with graceful degradation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MotorStatus(str, Enum):
    """Motor availability status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class MotorResult:
    """Standard result from any scientific motor"""
    motor_name: str
    status: MotorStatus
    success: bool = False
    data: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    error_message: str | None = None


@dataclass
class UnifiedLandAnalysis:
    """Complete unified analysis from all motors"""
    soil_analysis: MotorResult | None = None
    climate_analysis: MotorResult | None = None
    crop_recommendations: MotorResult | None = None
    irrigation_plan: MotorResult | None = None
    erosion_risk: MotorResult | None = None
    carbon_sequestration: MotorResult | None = None
    overall_confidence: float = 0.0
    motors_available: int = 0
    motors_total: int = 7


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
            "irrigation_scheduler": ("services.scientific_motors.irrigation_scheduler", "IrrigationSchedulerMotor"),
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
        return [name for name, status in self._motor_status.items()
                if status == MotorStatus.AVAILABLE]

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

            motor_input = {
                "soil_ph": inputs.get("soil_ph", 6.5),
                "soil_depth_cm": inputs.get("soil_depth_cm", 100),
                "annual_precip_mm": inputs.get("annual_precip_mm", 600),
                "mean_temp_c": inputs.get("mean_temp_c", 20),
            }

            output = motor.execute(**motor_input)

            return MotorResult(
                motor_name="crop_advisor",
                status=MotorStatus.AVAILABLE,
                success=True,
                data=output if isinstance(output, dict) else {"result": str(output)},
                recommendations=output.get("recommended_crops", []) if isinstance(output, dict) else [],
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

            motor_input = {
                "soil_type": inputs.get("soil_type", "loam"),
                "soil_depth_cm": inputs.get("soil_depth_cm", 100),
                "annual_precip_mm": inputs.get("annual_precip_mm", 600),
            }

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

            motor_input = {
                "rainfall_erosivity": inputs.get("rainfall_erosivity", 100),
                "soil_erodibility": inputs.get("soil_erodibility", 0.3),
                "slope_pct": inputs.get("slope_pct", 3.0),
            }

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

            motor_input = {
                "initial_soc": inputs.get("initial_soc", 30),
                "mean_temp_c": inputs.get("mean_temp_c", 20),
                "clay_pct": inputs.get("clay_pct", 25),
            }

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
