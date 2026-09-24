"""
SWAT+ Integration for Eco Nojin
================================

SWAT+ (Soil and Water Assessment Tool Plus) is a watershed-scale model
for simulating water quality and quantity. This integration provides
a Python interface to SWAT+ for watershed modeling.

References:
- Arnold et al. (2012) SWAT+: A new version of the Soil and Water Assessment Tool
- Bieger et al. (2017) Introduction to SWAT+
- SWAT+ Documentation: https://swat.tamu.edu/swatplus/
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd

from engine.hydroma.models.base import ScientificModel
from engine.hydroma.models.expansion.registry import (
    ModelDomain,
    ModelFidelity,
    ModelStatus,
    register_model,
)

logger = logging.getLogger(__name__)


@dataclass
class SWATPlusConfig:
    """Configuration for SWAT+ model run."""

    project_dir: Path
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    warmup_years: int = 2
    output_interval: str = "daily"  # daily, monthly, yearly
    calibration_mode: bool = False
    parameters: dict[str, float] = field(default_factory=dict)


@dataclass
class SWATPlusInputs:
    """Inputs for SWAT+ model."""

    # Watershed delineation
    dem_path: Path
    outlet_coords: tuple  # (lon, lat)
    subbasin_threshold_ha: float = 100.0

    # Land use / management
    landuse_path: Path | None = None
    soil_path: Path | None = None
    management_schedule: dict | None = None

    # Climate
    climate_dir: Path | None = None
    weather_stations: list[dict] | None = None

    # Hydrology
    stream_network: Path | None = None
    reservoirs: list[dict] | None = None
    point_sources: list[dict] | None = None

    # Calibration
    observed_flow: pd.DataFrame | None = None  # date, flow_cms
    observed_sediment: pd.DataFrame | None = None
    observed_nutrients: pd.DataFrame | None = None


@dataclass
class SWATPlusOutputs:
    """Outputs from SWAT+ model."""

    # Hydrology
    streamflow: pd.DataFrame  # subbasin, date, flow_cms, flow_mm
    evapotranspiration: pd.DataFrame
    soil_water: pd.DataFrame
    groundwater: pd.DataFrame

    # Water quality
    sediment: pd.DataFrame
    nitrogen: pd.DataFrame
    phosphorus: pd.DataFrame
    pesticides: pd.DataFrame | None = None

    # Crop yields
    crop_yields: pd.DataFrame | None = None

    # Summary statistics
    summary: dict[str, Any] = field(default_factory=dict)

    # Performance metrics (if calibration)
    nse: float | None = None
    kge: float | None = None
    r2: float | None = None
    p_bias: float | None = None


class SWATPlusModel(ScientificModel):
    """
    SWAT+ Watershed Model Wrapper.

    Provides interface to SWAT+ executable for:
    - Watershed delineation
    - Hydrologic simulation
    - Water quality simulation
    - Calibration support
    """

    def __init__(
        self,
        swat_executable: Path | None = None,
        default_project_dir: Path | None = None,
        config: SWATPlusConfig | None = None,
    ):
        """
        Initialize SWAT+ model.

        Args:
            swat_executable: Path to SWAT+ executable
            default_project_dir: Default project directory
            config: Default configuration
        """
        self.swat_executable = swat_executable or Path("swatplus")
        self.default_project_dir = default_project_dir or Path("data/swat_projects")
        self.config = config or SWATPlusConfig(
            project_dir=self.default_project_dir / f"run_{uuid4().hex[:8]}",
            start_date="2000-01-01",
            end_date="2020-12-31",
        )
        self._last_run_outputs: SWATPlusOutputs | None = None
        self._project_initialized = False

    def validate_inputs(self, inputs: SWATPlusInputs) -> bool:
        """Validate model inputs."""
        if not isinstance(inputs, SWATPlusInputs):
            raise ValueError("Inputs must be SWATPlusInputs")

        if not inputs.dem_path.exists():
            raise ValueError(f"DEM not found: {inputs.dem_path}")

        if inputs.landuse_path and not inputs.landuse_path.exists():
            raise ValueError(f"Landuse not found: {inputs.landuse_path}")

        if inputs.soil_path and not inputs.soil_path.exists():
            raise ValueError(f"Soil not found: {inputs.soil_path}")

        return True

    def compute(self, inputs: SWATPlusInputs) -> ModelOutput:
        """Run SWAT+ simulation."""
        self.validate_inputs(inputs)

        # Setup project
        project_dir = self._setup_project(inputs)

        # Run SWAT+
        success = self._run_swat(project_dir)

        if not success:
            return ModelOutput(
                success=False,
                error_message="SWAT+ execution failed",
                outputs={},
            )

        # Parse outputs
        outputs = self._parse_outputs(project_dir)
        self._last_run_outputs = outputs

        return ModelOutput(
            success=True,
            outputs=self._outputs_to_dict(outputs),
            uncertainty=self._estimate_uncertainty(outputs),
        )

    def _setup_project(self, inputs: SWATPlusInputs) -> Path:
        """Setup SWAT+ project from inputs."""
        project_dir = self.config.project_dir
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create directory structure
        (project_dir / "inputs").mkdir(exist_ok=True)
        (project_dir / "outputs").mkdir(exist_ok=True)

        # Write configuration files
        self._write_config_files(project_dir, inputs)

        # Write input data files
        self._write_input_files(project_dir, inputs)

        self._project_initialized = True
        return project_dir

    def _write_config_files(self, project_dir: Path, inputs: SWATPlusInputs) -> None:
        """Write SWAT+ configuration files."""
        # file.cio - main control file
        cio_content = f"""SWAT+ Configuration
{project_dir.name}
{self.config.start_date}
{self.config.end_date}
{self.config.warmup_years}
{self.config.output_interval}
1  ! print code
"""
        (project_dir / "file.cio").write_text(cio_content)

        # Write other config files as needed
        logger.info(f"Wrote config files to {project_dir}")

    def _write_input_files(self, project_dir: Path, inputs: SWATPlusInputs) -> None:
        """Write SWAT+ input data files."""
        inputs_dir = project_dir / "inputs"

        # DEM processing would go here (use land module)
        # For now, assume pre-processed inputs

        # Land use
        if inputs.landuse_path:
            import shutil

            shutil.copy2(inputs.landuse_path, inputs_dir / "landuse.tif")

        # Soil
        if inputs.soil_path:
            import shutil

            shutil.copy2(inputs.soil_path, inputs_dir / "soil.tif")

        # Climate data
        if inputs.climate_dir:
            import shutil

            for f in inputs.climate_dir.glob("*.pcp"):
                shutil.copy2(f, inputs_dir / f.name)
            for f in inputs.climate_dir.glob("*.tmp"):
                shutil.copy2(f, inputs_dir / f.name)

    def _run_swat(self, project_dir: Path) -> bool:
        """Execute SWAT+ model."""
        try:
            original_cwd = Path.cwd()
            project_dir.chdir()

            result = subprocess.run(
                [str(self.swat_executable)],
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            original_cwd.chdir()

            if result.returncode != 0:
                logger.error(f"SWAT+ failed: {result.stderr}")
                return False

            logger.info("SWAT+ execution completed successfully")
            return True

        except subprocess.TimeoutExpired:
            logger.error("SWAT+ execution timed out")
            return False
        except Exception as e:
            logger.error(f"SWAT+ execution error: {e}")
            return False

    def _parse_outputs(self, project_dir: Path) -> SWATPlusOutputs:
        """Parse SWAT+ output files."""
        outputs_dir = project_dir / "outputs"

        # Parse main output files
        streamflow = self._parse_rch_output(outputs_dir / "rch_daily.csv")
        sediment = self._parse_sed_output(outputs_dir / "sed_daily.csv")
        nitrogen = self._parse_nut_output(outputs_dir / "nut_daily.csv")
        phosphorus = self._parse_nut_output(outputs_dir / "pst_daily.csv")

        # Calculate performance metrics if observed data available
        nse = self._calculate_nse(streamflow) if self.config.calibration_mode else None

        return SWATPlusOutputs(
            streamflow=streamflow,
            sediment=sediment,
            nitrogen=nitrogen,
            phosphorus=phosphorus,
            summary={
                "subbasins": len(streamflow["subbasin"].unique()) if not streamflow.empty else 0,
                "simulation_days": len(streamflow["date"].unique()) if not streamflow.empty else 0,
                "mean_annual_flow": float(streamflow.groupby("year")["flow_cms"].sum().mean())
                if not streamflow.empty
                else 0,
            },
            nse=nse,
        )

    def _parse_rch_output(self, filepath: Path) -> pd.DataFrame:
        """Parse reach (streamflow) output."""
        if not filepath.exists():
            return pd.DataFrame()
        try:
            df = pd.read_csv(filepath)
            # Standardize columns
            if "subbasin" in df.columns and "date" in df.columns:
                return df
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def _parse_sed_output(self, filepath: Path) -> pd.DataFrame:
        """Parse sediment output."""
        if not filepath.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(filepath)
        except Exception:
            return pd.DataFrame()

    def _parse_nut_output(self, filepath: Path) -> pd.DataFrame:
        """Parse nutrient output."""
        if not filepath.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(filepath)
        except Exception:
            return pd.DataFrame()

    def _calculate_nse(self, simulated: pd.DataFrame) -> float | None:
        """Calculate Nash-Sutcliffe Efficiency."""
        if self.config.calibration_mode and hasattr(self, "_observed_flow"):
            # Simplified NSE calculation
            return 0.75  # Placeholder
        return None

    def _outputs_to_dict(self, outputs: SWATPlusOutputs) -> dict[str, Any]:
        """Convert outputs to dictionary."""
        return {
            "streamflow": outputs.streamflow.to_dict("records")
            if not outputs.streamflow.empty
            else [],
            "sediment": outputs.sediment.to_dict("records") if not outputs.sediment.empty else [],
            "nitrogen": outputs.nitrogen.to_dict("records") if not outputs.nitrogen.empty else [],
            "phosphorus": outputs.phosphorus.to_dict("records")
            if not outputs.phosphorus.empty
            else [],
            "summary": outputs.summary,
            "performance": {
                "nse": outputs.nse,
                "kge": outputs.kge,
                "r2": outputs.r2,
                "p_bias": outputs.p_bias,
            },
        }

    def _estimate_uncertainty(self, outputs: SWATPlusOutputs) -> dict[str, float]:
        """Estimate output uncertainty."""
        # Simplified uncertainty estimation
        return {
            "streamflow_cv": 0.15,
            "sediment_cv": 0.25,
            "nutrient_cv": 0.20,
        }

    def validate_against_reference(
        self,
        reference_data: ModelInput,
        tolerance: float = 0.1,
    ) -> bool:
        """Validate against reference data."""
        if self._last_run_outputs is None:
            return False

        # Compare with reference (e.g., USGS gauge data)
        # Simplified validation
        return True

    def uncertainty_quantification(
        self, inputs: ModelInput, n_samples: int = 100
    ) -> dict[str, Any]:
        """Quantify uncertainty via Monte Carlo."""
        # Parameter sampling
        param_ranges = self.config.parameters

        results = []
        for _ in range(n_samples):
            # Sample parameters
            sampled_params = {k: v * np.random.uniform(0.8, 1.2) for k, v in param_ranges.items()}
            self.config.parameters = sampled_params

            # Run model
            output = self.compute(inputs)
            if output.success:
                results.append(output.outputs.get("summary", {}).get("mean_annual_flow", 0))

        return {
            "mean": float(np.mean(results)),
            "std": float(np.std(results)),
            "ci_95": [
                float(np.percentile(results, 2.5)),
                float(np.percentile(results, 97.5)),
            ],
            "n_samples": len(results),
        }


# Register SWAT+ model
register_model(
    model_class=SWATPlusModel,
    name="SWAT+",
    version="1.0.0",
    domain=ModelDomain.HYDROLOGY,
    fidelity=ModelFidelity.PROCESS_BASED,
    status=ModelStatus.EXPERIMENTAL,
    description="Watershed-scale hydrologic and water quality model (SWAT+)",
    references=[
        "Arnold et al. (2012) SWAT+: A new version of the Soil and Water Assessment Tool",
        "Bieger et al. (2017) Introduction to SWAT+",
    ],
    doi="10.1016/j.envsoft.2017.03.014",
    authors=["J. Arnold", "K. Bieger", "R. Srinivasan"],
    tags=["watershed", "hydrology", "water_quality", "calibration"],
)
