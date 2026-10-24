"""Calibration parameter registry for HY-RUE and EWSI models.

Registers every parameter that affects HY-RUE yield predictions and EWSI
computation, with metadata about its source, calibration status, allowed
range, and calibration method. Parameters are classified as:

* FIXED — scientific constants or unit definitions; not calibrated.
* CALIBRATABLE — may be estimated from development data using a documented
  method; never tuned on test data.
* UNCALIBRATED — project defaults with no published source; must be either
  calibrated on development data or flagged as uncalibrated in reports.

No parameter value may be changed on test data. All changes must be
recorded with rationale, method, and version.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ParameterStatus(StrEnum):
    """Calibration status of a parameter."""

    FIXED = "fixed"
    CALIBRATABLE = "calibratable"
    UNCALIBRATED = "uncalibrated"
    CALIBRATED = "calibrated"


class ParameterGroup(StrEnum):
    """Parameter grouping for HY-RUE / EWSI."""

    HYRUE_BIOMASS = "hyrue_biomass"
    HYRUE_THERMAL = "hyrue_thermal"
    HYRUE_HARVEST = "hyrue_harvest"
    EWSI_WEIGHTS = "ewsi_weights"
    EWSI_ANCHORS = "ewsi_anchors"
    EWSI_SOIL = "ewsi_soil"
    UNIT_CONVERSION = "unit_conversion"


@dataclass
class ParameterEntry:
    """A single registered parameter.

    Attributes:
        parameter_name: Unique parameter name.
        parameter_value: Current value (default or calibrated).
        unit: Physical unit of the parameter.
        model_component: Which model component uses this parameter.
        parameter_group: High-level group for reporting.
        parameter_status: Calibration status.
        parameter_source: Source of the value (literature, preset, default).
        allowed_min: Minimum allowed value (None = no bound).
        allowed_max: Maximum allowed value (None = no bound).
        calibration_method: Method used to estimate (None if not calibrated).
        calibration_dataset: Dataset used for calibration (None if not calibrated).
        calibration_version: Version tag for the calibration run.
        last_updated: ISO timestamp of last value change.
        rationale: Human-readable rationale for the current value.
    """

    parameter_name: str
    parameter_value: float
    unit: str
    model_component: str
    parameter_group: ParameterGroup
    parameter_status: ParameterStatus
    parameter_source: str
    allowed_min: float | None = None
    allowed_max: float | None = None
    calibration_method: str | None = None
    calibration_dataset: str | None = None
    calibration_version: str | None = None
    last_updated: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    rationale: str = ""


class CalibrationParameterRegistry:
    """Registry of all HY-RUE and EWSI parameters.

    Provides methods to register, retrieve, update, and validate parameters.
    All parameter changes must go through this registry to ensure
    traceability.
    """

    def __init__(self) -> None:
        self._parameters: dict[str, ParameterEntry] = {}
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Register all default parameters from HYRUEParams and EWSI.

        Values are taken from the actual code defaults. Status is set based
        on whether each parameter has a published scientific source.
        """
        # --- HYRUE biomass parameters ---
        self.register(
            parameter_name="epsilon",
            parameter_value=2.2,
            unit="g/MJ IPAR",
            model_component="HYRUE biomass",
            parameter_group=ParameterGroup.HYRUE_BIOMASS,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="HYRUEParams CROP_PRESETS['wheat']",
            allowed_min=0.5,
            allowed_max=5.0,
            rationale=(
                "Wheat preset value from Steduto et al. (2009) AquaCrop; "
                "not calibrated to CIMMYT data."
            ),
        )

        # --- HYRUE thermal parameters ---
        self.register(
            parameter_name="t_opt",
            parameter_value=20.0,
            unit="degC",
            model_component="HYRUE temperature stress",
            parameter_group=ParameterGroup.HYRUE_THERMAL,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="HYRUEParams CROP_PRESETS['wheat']",
            allowed_min=10.0,
            allowed_max=30.0,
            rationale=(
                "Wheat preset value; Gaussian thermal response width is "
                "hard-coded at 8 C in stress_temperature()."
            ),
        )
        self.register(
            parameter_name="t_min",
            parameter_value=5.0,
            unit="degC",
            model_component="HYRUE temperature stress",
            parameter_group=ParameterGroup.HYRUE_THERMAL,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="HYRUEParams default",
            allowed_min=0.0,
            allowed_max=10.0,
            rationale=(
                "Lower temperature cutoff; below this, f_temp = 0."
            ),
        )
        self.register(
            parameter_name="t_max",
            parameter_value=35.0,
            unit="degC",
            model_component="HYRUE temperature stress",
            parameter_group=ParameterGroup.HYRUE_THERMAL,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="HYRUEParams default",
            allowed_min=30.0,
            allowed_max=45.0,
            rationale=(
                "Upper temperature cutoff; above this, f_temp = 0."
            ),
        )
        self.register(
            parameter_name="thermal_gaussian_width",
            parameter_value=8.0,
            unit="degC",
            model_component="HYRUE temperature stress",
            parameter_group=ParameterGroup.HYRUE_THERMAL,
            parameter_status=ParameterStatus.UNCALIBRATED,
            parameter_source="Hard-coded in stress_temperature(); no source",
            allowed_min=3.0,
            allowed_max=15.0,
            rationale=(
                "Hard-coded constant; no published source for wheat in "
                "eastern India."
            ),
        )

        # --- HYRUE structural parameters ---
        self.register(
            parameter_name="k",
            parameter_value=0.65,
            unit="dimensionless",
            model_component="HYRUE f_IPAR (Beer-Lambert)",
            parameter_group=ParameterGroup.HYRUE_BIOMASS,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="HYRUEParams default",
            allowed_min=0.3,
            allowed_max=1.0,
            rationale=(
                "Light extinction coefficient; conventional range 0.46-0.75 "
                "depending on canopy architecture."
            ),
        )
        self.register(
            parameter_name="lai_max",
            parameter_value=6.0,
            unit="m^2/m^2",
            model_component="HYRUE f_IPAR",
            parameter_group=ParameterGroup.HYRUE_BIOMASS,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="HYRUEParams default",
            allowed_min=3.0,
            allowed_max=8.0,
            rationale=(
                "Maximum canopy LAI fed to the light-interception curve."
            ),
        )

        # --- HYRUE harvest parameters ---
        self.register(
            parameter_name="hi",
            parameter_value=0.45,
            unit="dimensionless",
            model_component="HYRUE yield conversion",
            parameter_group=ParameterGroup.HYRUE_HARVEST,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="HYRUEParams CROP_PRESETS['wheat']",
            allowed_min=0.2,
            allowed_max=0.6,
            rationale=(
                "Harvest index (grain yield / aboveground biomass)."
            ),
        )

        # --- Unit conversion parameters ---
        self.register(
            parameter_name="shortwave_to_par_factor",
            parameter_value=0.5,
            unit="dimensionless",
            model_component="PAR resolution",
            parameter_group=ParameterGroup.UNIT_CONVERSION,
            parameter_status=ParameterStatus.FIXED,
            parameter_source=(
                "Stage 36 pilot error analysis; shortwave radiation is "
                "roughly 2x PAR; factor is an estimate, not a measurement."
            ),
            allowed_min=0.4,
            allowed_max=0.6,
            rationale=(
                "Conversion factor from shortwave radiation to PAR. "
                "Documented as estimated, not measured."
            ),
        )

        # --- EWSI weights ---
        self.register(
            parameter_name="ewsi_weight_ndmi",
            parameter_value=0.4,
            unit="dimensionless",
            model_component="EWSI composite",
            parameter_group=ParameterGroup.EWSI_WEIGHTS,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="EWSIWeights default (project default)",
            allowed_min=0.0,
            allowed_max=1.0,
            rationale=(
                "NDMI component weight; project default, not calibrated."
            ),
        )
        self.register(
            parameter_name="ewsi_weight_vpd",
            parameter_value=0.3,
            unit="dimensionless",
            model_component="EWSI composite",
            parameter_group=ParameterGroup.EWSI_WEIGHTS,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="EWSIWeights default (project default)",
            allowed_min=0.0,
            allowed_max=1.0,
            rationale=(
                "VPD component weight; project default, not calibrated."
            ),
        )
        self.register(
            parameter_name="ewsi_weight_soil",
            parameter_value=0.3,
            unit="dimensionless",
            model_component="EWSI composite",
            parameter_group=ParameterGroup.EWSI_WEIGHTS,
            parameter_status=ParameterStatus.CALIBRATABLE,
            parameter_source="EWSIWeights default (project default)",
            allowed_min=0.0,
            allowed_max=1.0,
            rationale=(
                "Soil moisture component weight; project default, "
                "not calibrated."
            ),
        )

        # --- EWSI NDMI anchors ---
        self.register(
            parameter_name="ndmi_ref",
            parameter_value=0.3,
            unit="dimensionless",
            model_component="EWSI NDMI stress",
            parameter_group=ParameterGroup.EWSI_ANCHORS,
            parameter_status=ParameterStatus.UNCALIBRATED,
            parameter_source="ewsi_pipeline.py default",
            allowed_min=0.0,
            allowed_max=0.7,
            rationale=(
                "Reference NDMI under non-stressed conditions; project "
                "default, no published source for wheat."
            ),
        )
        self.register(
            parameter_name="ndmi_crit",
            parameter_value=-0.2,
            unit="dimensionless",
            model_component="EWSI NDMI stress",
            parameter_group=ParameterGroup.EWSI_ANCHORS,
            parameter_status=ParameterStatus.UNCALIBRATED,
            parameter_source="ewsi_pipeline.py default",
            allowed_min=-0.8,
            allowed_max=0.0,
            rationale=(
                "Critical NDMI at maximal stress; project default, "
                "no published source."
            ),
        )

        # --- EWSI VPD anchors ---
        self.register(
            parameter_name="vpd_low",
            parameter_value=0.5,
            unit="kPa",
            model_component="EWSI VPD stress",
            parameter_group=ParameterGroup.EWSI_ANCHORS,
            parameter_status=ParameterStatus.UNCALIBRATED,
            parameter_source="ewsi_pipeline.py default",
            allowed_min=0.0,
            allowed_max=2.0,
            rationale=(
                "VPD below which water stress is zero; project default."
            ),
        )
        self.register(
            parameter_name="vpd_high",
            parameter_value=4.0,
            unit="kPa",
            model_component="EWSI VPD stress",
            parameter_group=ParameterGroup.EWSI_ANCHORS,
            parameter_status=ParameterStatus.UNCALIBRATED,
            parameter_source="ewsi_pipeline.py default",
            allowed_min=2.0,
            allowed_max=8.0,
            rationale=(
                "VPD above which water stress is maximal (1.0); "
                "project default."
            ),
        )

        # --- EWSI soil parameters ---
        self.register(
            parameter_name="soil_field_capacity",
            parameter_value=0.35,
            unit="m^3/m^3",
            model_component="EWSI soil moisture stress",
            parameter_group=ParameterGroup.EWSI_SOIL,
            parameter_status=ParameterStatus.UNCALIBRATED,
            parameter_source="EWSIInputSeries default",
            allowed_min=0.2,
            allowed_max=0.5,
            rationale=(
                "Field capacity for soil moisture stress ratio; "
                "project default, not site-specific."
            ),
        )

    def register(
        self,
        parameter_name: str,
        parameter_value: float,
        unit: str,
        model_component: str,
        parameter_group: ParameterGroup,
        parameter_status: ParameterStatus,
        parameter_source: str,
        allowed_min: float | None = None,
        allowed_max: float | None = None,
        calibration_method: str | None = None,
        calibration_dataset: str | None = None,
        calibration_version: str | None = None,
        rationale: str = "",
    ) -> None:
        """Register or update a parameter.

        Raises:
            ValueError: if the value is outside allowed bounds.
        """
        if allowed_min is not None and parameter_value < allowed_min:
            raise ValueError(
                f"Parameter {parameter_name}={parameter_value} "
                f"below allowed_min={allowed_min}"
            )
        if allowed_max is not None and parameter_value > allowed_max:
            raise ValueError(
                f"Parameter {parameter_name}={parameter_value} "
                f"above allowed_max={allowed_max}"
            )

        entry = ParameterEntry(
            parameter_name=parameter_name,
            parameter_value=parameter_value,
            unit=unit,
            model_component=model_component,
            parameter_group=parameter_group,
            parameter_status=parameter_status,
            parameter_source=parameter_source,
            allowed_min=allowed_min,
            allowed_max=allowed_max,
            calibration_method=calibration_method,
            calibration_dataset=calibration_dataset,
            calibration_version=calibration_version,
            last_updated=datetime.now(UTC).isoformat(),
            rationale=rationale,
        )
        self._parameters[parameter_name] = entry

    def get(self, parameter_name: str) -> ParameterEntry | None:
        """Retrieve a parameter entry by name."""
        return self._parameters.get(parameter_name)

    def get_value(self, parameter_name: str) -> float | None:
        """Retrieve just the value of a parameter."""
        entry = self._parameters.get(parameter_name)
        return entry.parameter_value if entry else None

    def get_all(self) -> dict[str, ParameterEntry]:
        """Return all parameter entries."""
        return dict(self._parameters)

    def get_by_group(self, group: ParameterGroup) -> dict[str, ParameterEntry]:
        """Return all parameters in a group."""
        return {
            k: v for k, v in self._parameters.items()
            if v.parameter_group == group
        }

    def get_by_status(self, status: ParameterStatus) -> dict[str, ParameterEntry]:
        """Return all parameters with a given status."""
        return {
            k: v for k, v in self._parameters.items()
            if v.parameter_status == status
        }

    def update_value(
        self,
        parameter_name: str,
        new_value: float,
        calibration_method: str | None = None,
        calibration_dataset: str | None = None,
        calibration_version: str | None = None,
        rationale: str = "",
    ) -> None:
        """Update a parameter value with full traceability.

        Raises:
            KeyError: if the parameter is not registered.
            ValueError: if the value is outside allowed bounds.
        """
        if parameter_name not in self._parameters:
            raise KeyError(f"Parameter {parameter_name} not registered")

        entry = self._parameters[parameter_name]

        # Validate bounds
        if entry.allowed_min is not None and new_value < entry.allowed_min:
            raise ValueError(
                f"New value {new_value} below allowed_min={entry.allowed_min}"
            )
        if entry.allowed_max is not None and new_value > entry.allowed_max:
            raise ValueError(
                f"New value {new_value} above allowed_max={entry.allowed_max}"
            )

        entry.parameter_value = new_value
        entry.last_updated = datetime.now(UTC).isoformat()
        if calibration_method is not None:
            entry.calibration_method = calibration_method
        if calibration_dataset is not None:
            entry.calibration_dataset = calibration_dataset
        if calibration_version is not None:
            entry.calibration_version = calibration_version
        if rationale:
            entry.rationale = rationale
        if calibration_method is not None:
            entry.parameter_status = ParameterStatus.CALIBRATED

    def to_dict(self) -> dict[str, Any]:
        """Serialize the registry to a dictionary."""
        return {
            name: {
                "parameter_value": entry.parameter_value,
                "unit": entry.unit,
                "model_component": entry.model_component,
                "parameter_group": entry.parameter_group.value,
                "parameter_status": entry.parameter_status.value,
                "parameter_source": entry.parameter_source,
                "allowed_min": entry.allowed_min,
                "allowed_max": entry.allowed_max,
                "calibration_method": entry.calibration_method,
                "calibration_dataset": entry.calibration_dataset,
                "calibration_version": entry.calibration_version,
                "last_updated": entry.last_updated,
                "rationale": entry.rationale,
            }
            for name, entry in self._parameters.items()
        }

    def summary(self) -> dict[str, Any]:
        """Return a summary of the registry."""
        status_counts: dict[str, int] = {}
        for entry in self._parameters.values():
            s = entry.parameter_status.value
            status_counts[s] = status_counts.get(s, 0) + 1
        return {
            "total_parameters": len(self._parameters),
            "status_counts": status_counts,
            "groups": {
                g.value: len(self.get_by_group(g))
                for g in ParameterGroup
            },
        }


def build_registry() -> CalibrationParameterRegistry:
    """Build and return a fresh parameter registry with defaults."""
    return CalibrationParameterRegistry()


if __name__ == "__main__":
    registry = build_registry()
    print("=" * 60)
    print("Calibration Parameter Registry")
    print("=" * 60)
    summary = registry.summary()
    print(f"Total parameters: {summary['total_parameters']}")
    print(f"Status counts: {summary['status_counts']}")
    print()
    for name, entry in registry.get_all().items():
        print(
            f"  {name}: {entry.parameter_value} {entry.unit} "
            f"[{entry.parameter_status.value}]"
        )
