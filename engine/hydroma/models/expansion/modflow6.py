"""
MODFLOW 6 Integration for Eco Nojin
====================================

MODFLOW 6 is the USGS modular groundwater flow model. This integration
provides a Python interface via flopy for groundwater modeling.

References:
- Langevin et al. (2017) MODFLOW 6: A modular framework for groundwater flow simulation
- Hughes et al. (2020) flopy: A Python package for MODFLOW
- MODFLOW 6 Documentation: https://www.usgs.gov/software/modflow-6
"""

from __future__ import annotations

import importlib.util
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from engine.hydroma.models.base import (
    ModelInput,
    ModelOutput,
    ScientificModel,
    ValidationResult,
)
from engine.hydroma.models.expansion.registry import (
    ModelDomain,
    ModelFidelity,
    ModelStatus,
    register_model,
)

logger = logging.getLogger(__name__)

# Optional flopy import. The flag is the point: callers branch on it to fall
# back to mock mode, so ask whether it is installed rather than importing a
# heavyweight package at module scope.
FLOPY_AVAILABLE = importlib.util.find_spec("flopy") is not None
if not FLOPY_AVAILABLE:
    logger.warning("flopy not available - MODFLOW 6 integration will use mock mode")


@dataclass
class MODFLOW6Config:
    """Configuration for MODFLOW 6 model."""

    model_name: str = "ecojin_gwf"
    workspace: Path = Path("data/modflow_models")
    exe_name: str = "mf6"
    length_units: str = "meters"
    time_units: str = "days"
    nper: int = 1  # Number of stress periods
    perlen: list[float] = field(default_factory=lambda: [365.0])
    nstp: list[int] = field(default_factory=lambda: [10])
    tsmult: list[float] = field(default_factory=lambda: [1.0])
    steady: list[bool] = field(default_factory=lambda: [False])


@dataclass
class MODFLOW6Inputs:
    """Inputs for MODFLOW 6 model."""

    # Grid
    nlay: int = 3
    nrow: int = 100
    ncol: int = 100
    delr: float = 100.0  # Column width
    delc: float = 100.0  # Row width
    top: float | np.ndarray = 100.0
    botm: float | list[float] | np.ndarray = field(default_factory=lambda: [50.0, 0.0, -50.0])

    # Hydraulic properties
    hk: float | np.ndarray = 10.0  # Horizontal K
    vka: float | np.ndarray = 1.0  # Vertical K
    sy: float = 0.2  # Specific yield
    ss: float = 1e-4  # Specific storage

    # Boundary conditions
    ibound: np.ndarray | None = None
    strt: float | np.ndarray = 90.0  # Starting heads

    # Stress period data
    recharge: np.ndarray | None = None
    wells: list[dict] | None = None
    rivers: list[dict] | None = None
    drains: list[dict] | None = None
    ghb: list[dict] | None = None  # General head boundaries

    # Output control
    save_head: bool = True
    save_budget: bool = True
    output_format: str = "binary"


@dataclass
class MODFLOW6Outputs:
    """Outputs from MODFLOW 6 model."""

    heads: np.ndarray  # (nlay, nrow, ncol, nper)
    budget: dict[str, np.ndarray]
    drawdown: np.ndarray | None = None
    cell_by_cell: dict | None = None
    summary: dict[str, Any] = field(default_factory=dict)


class MODFLOW6Model(ScientificModel):
    """
    MODFLOW 6 Groundwater Flow Model Wrapper.

    Provides interface to MODFLOW 6 via flopy for:
    - Groundwater flow simulation
    - Transient and steady-state simulations
    - Conjunctive use modeling
    - Calibration support
    """

    def __init__(
        self,
        config: MODFLOW6Config | None = None,
        mock_mode: bool = False,
    ):
        """
        Initialize MODFLOW 6 model.

        Args:
            config: Model configuration
            mock_mode: Run in mock mode (without flopy/MODFLOW)
        """
        self.config = config or MODFLOW6Config()
        self.mock_mode = mock_mode or not FLOPY_AVAILABLE
        self._simulation = None
        self._last_outputs: MODFLOW6Outputs | None = None

        if self.mock_mode:
            logger.info("MODFLOW 6 running in mock mode")

    def validate_inputs(self, inputs: MODFLOW6Inputs) -> bool:
        """Validate model inputs."""
        if not isinstance(inputs, MODFLOW6Inputs):
            raise ValueError("Inputs must be MODFLOW6Inputs")

        if inputs.nlay <= 0 or inputs.nrow <= 0 or inputs.ncol <= 0:
            raise ValueError("Grid dimensions must be positive")

        if inputs.delr <= 0 or inputs.delc <= 0:
            raise ValueError("Cell dimensions must be positive")

        return True

    def compute(self, inputs: MODFLOW6Inputs) -> ModelOutput:
        """Run a MODFLOW 6 simulation, or an explicitly labelled stand-in.

        MODFLOW 6 is reached through flopy, which is an optional dependency and
        is not installed in this deployment. Without it ``mock_mode`` is on and
        ``_run_mock`` fills the head array with generated values.

        The previous version returned ``success=True`` with
        ``data_source="modelled"`` for both paths, so a caller had no way to
        tell a real simulation from a generated one. ``S-HONEST`` requires the
        status envelope to match reality, so the mock path is now labelled
        ``simulated``, carries a note, and names the model it actually came
        from. ``success`` stays True: the call did not fail, and the point of
        the label is that ``success`` was never the honest signal.
        """
        self.validate_inputs(inputs)

        is_mock = bool(self.mock_mode)
        outputs = self._run_mock(inputs) if is_mock else self._run_flopy(inputs)

        self._last_outputs = outputs

        note = ""
        if is_mock:
            note = (
                "SYNTHETIC. flopy is not installed, so this is not a "
                "groundwater simulation. The head array was generated by "
                "_run_mock. Do not use these numbers for hydrology, irrigation "
                "or any carbon claim. Install flopy to run the real solver."
            )

        return ModelOutput(
            success=True,
            outputs=self._outputs_to_dict(outputs),
            uncertainty=self._estimate_uncertainty(outputs),
            data_source="simulated" if is_mock else "modelled",
            model="MODFLOW 6 (mock)" if is_mock else "MODFLOW 6 (flopy)",
            notes=note,
        )

    def _run_mock(self, inputs: MODFLOW6Inputs) -> MODFLOW6Outputs:
        """Run mock simulation for testing."""
        nlay, nrow, ncol = inputs.nlay, inputs.nrow, inputs.ncol
        nper = self.config.nper

        # Generate mock heads
        heads = np.zeros((nlay, nrow, ncol, nper))
        for k in range(nlay):
            for i in range(nrow):
                for j in range(ncol):
                    # Simple linear gradient
                    heads[k, i, j, :] = inputs.strt - k * 10 - i * 0.1 - j * 0.1

        # Mock budget
        budget = {
            "IN": np.random.uniform(1000, 2000, nper),
            "OUT": np.random.uniform(1000, 2000, nper),
            "STORAGE": np.random.uniform(-100, 100, nper),
        }

        return MODFLOW6Outputs(
            heads=heads,
            budget=budget,
            summary={
                "model_name": self.config.model_name,
                "grid": f"{nlay}x{nrow}x{ncol}",
                "stress_periods": nper,
                "max_head": float(np.max(heads)),
                "min_head": float(np.min(heads)),
                "mean_head": float(np.mean(heads)),
            },
        )

    def _run_flopy(self, inputs: MODFLOW6Inputs) -> MODFLOW6Outputs:
        """Run MODFLOW 6 via flopy."""
        if not FLOPY_AVAILABLE:
            raise RuntimeError("flopy not available")

        import flopy

        # Create simulation
        sim = flopy.mf6.MFSimulation(
            sim_name=self.config.model_name,
            version="mf6",
            exe_name=self.config.exe_name,
            sim_ws=str(self.config.workspace),
        )

        # TDIS package
        flopy.mf6.ModflowTdis(
            sim,
            time_units=self.config.time_units,
            nper=self.config.nper,
            perioddata=[
                (self.config.perlen[i], self.config.nstp[i], self.config.tsmult[i])
                for i in range(self.config.nper)
            ],
        )

        # IMS package
        flopy.mf6.ModflowIms(sim, print_option="SUMMARY")

        # GWF model
        gwf = flopy.mf6.ModflowGwf(sim, modelname=self.config.model_name, save_flows=True)

        # DIS package
        flopy.mf6.ModflowGwfdis(
            gwf,
            nlay=inputs.nlay,
            nrow=inputs.nrow,
            ncol=inputs.ncol,
            delr=inputs.delr,
            delc=inputs.delc,
            top=inputs.top,
            botm=inputs.botm,
            length_units=self.config.length_units,
        )

        # IC package
        flopy.mf6.ModflowGwfic(gwf, strt=inputs.strt)

        # NPF package
        flopy.mf6.ModflowGwfnpf(
            gwf,
            save_flows=True,
            icelltype=1,
            k=inputs.hk,
            k33=inputs.vka,
        )

        # STO package
        flopy.mf6.ModflowGwfsto(
            gwf,
            save_flows=True,
            iconvert=1,
            ss=inputs.ss,
            sy=inputs.sy,
            steady_state=self.config.steady,
            transient=not self.config.steady[0],
        )

        # OC package
        flopy.mf6.ModflowGwfoc(
            gwf,
            budget_filerecord=f"{self.config.model_name}.cbc",
            head_filerecord=f"{self.config.model_name}.hds",
            saverecord=[
                ("HEAD", "ALL"),
                ("BUDGET", "ALL"),
            ],
        )

        # RCH package
        if inputs.recharge is not None:
            flopy.mf6.ModflowGwfrcha(gwf, recharge=inputs.recharge)

        # WEL package
        if inputs.wells:
            wel_spd = {}
            for w in inputs.wells:
                per = w.get("period", 0)
                if per not in wel_spd:
                    wel_spd[per] = []
                wel_spd[per].append([w["layer"], w["row"], w["col"], w["rate"]])
            flopy.mf6.ModflowGwfwel(gwf, stress_period_data=wel_spd)

        # RIV package
        if inputs.rivers:
            riv_spd = {}
            for r in inputs.rivers:
                per = r.get("period", 0)
                if per not in riv_spd:
                    riv_spd[per] = []
                riv_spd[per].append(
                    [r["layer"], r["row"], r["col"], r["stage"], r["cond"], r["rbot"]]
                )
            flopy.mf6.ModflowGwfriv(gwf, stress_period_data=riv_spd)

        # DRN package
        if inputs.drains:
            drn_spd = {}
            for d in inputs.drains:
                per = d.get("period", 0)
                if per not in drn_spd:
                    drn_spd[per] = []
                drn_spd[per].append([d["layer"], d["row"], d["col"], d["elev"], d["cond"]])
            flopy.mf6.ModflowGwfdrn(gwf, stress_period_data=drn_spd)

        # GHB package
        if inputs.ghb:
            ghb_spd = {}
            for g in inputs.ghb:
                per = g.get("period", 0)
                if per not in ghb_spd:
                    ghb_spd[per] = []
                ghb_spd[per].append([g["layer"], g["row"], g["col"], g["bhead"], g["cond"]])
            flopy.mf6.ModflowGwfghb(gwf, stress_period_data=ghb_spd)

        # Write and run
        sim.write_simulation()
        success, buff = sim.run_simulation()

        if not success:
            raise RuntimeError(f"MODFLOW 6 failed: {buff}")

        # Read outputs
        heads = gwf.output.head().get_alldata()
        budget = gwf.output.budget().get_data()

        return MODFLOW6Outputs(
            heads=heads,
            budget=budget,
            summary={
                "model_name": self.config.model_name,
                "grid": f"{inputs.nlay}x{inputs.nrow}x{inputs.ncol}",
                "stress_periods": self.config.nper,
                "max_head": float(np.max(heads)),
                "min_head": float(np.min(heads)),
                "mean_head": float(np.mean(heads)),
            },
        )

    def _outputs_to_dict(self, outputs: MODFLOW6Outputs) -> dict[str, Any]:
        """Convert outputs to dictionary."""
        return {
            "heads_shape": outputs.heads.shape,
            "heads_mean": float(np.mean(outputs.heads)),
            "heads_std": float(np.std(outputs.heads)),
            "heads_min": float(np.min(outputs.heads)),
            "heads_max": float(np.max(outputs.heads)),
            "budget": {k: v.tolist() for k, v in outputs.budget.items()},
            "summary": outputs.summary,
        }

    def _estimate_uncertainty(self, outputs: MODFLOW6Outputs) -> dict[str, float]:
        """Uncertainty of the run, as coefficients of variation.

        The previous version returned fixed values (0.05, 0.10) for every
        run. Those are not estimates. Publishing them as ``uncertainty``
        beside a result tells a caller the head is accurate to 5% when
        nothing was fitted, and in this deployment the head is synthetic to
        begin with.
        """
        del outputs
        return {
            "head_cv": float("nan"),
            "budget_cv": float("nan"),
            "method": "not estimated: flopy is absent, so the run is synthetic "
            "and no ensemble or residual series exists from which to derive a "
            "coefficient of variation",
        }

    def validate_against_reference(
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.1,
    ) -> ValidationResult:
        """Compare simulated heads against an observed series.

        The previous version took ``reference_data`` and returned ``bool``,
        which is not the base signature: a caller following
        ``ScientificModel.validate_against_reference`` raised ``TypeError``,
        and the function returned True for any run that produced output,
        having compared nothing.

        There is a second reason it cannot pass here. flopy is absent, so
        every head in this deployment is synthetic. Validating synthetic heads
        against an observed series would produce a number that looks like a
        model-performance score and is not one.
        """
        del inputs, reference_output, reference_source
        return ValidationResult(
            passed=False,
            metric_name="head (m)",
            computed_value=float("nan"),
            reference_value=float("nan"),
            tolerance=tolerance,
            relative_error=float("nan"),
            reference_source=(
                "not validated: flopy is not installed, so the simulated heads "
                "are synthetic, and no observed series is registered"
            ),
        )

    def uncertainty_quantification(self, inputs: ModelInput, n_samples: int = 50) -> dict[str, Any]:
        """Quantify uncertainty via Monte Carlo on K, S, R."""
        if not FLOPY_AVAILABLE:
            return {"mock": True, "message": "flopy required for UQ"}

        results = []
        for _ in range(n_samples):
            # Sample parameters
            hk_factor = np.random.lognormal(0, 0.3)
            rch_factor = np.random.lognormal(0, 0.2)

            inputs.hk *= hk_factor
            if inputs.recharge is not None:
                inputs.recharge *= rch_factor

            output = self.compute(inputs)
            if output.success:
                results.append(output.outputs.get("heads_mean", 0))

            # Reset
            inputs.hk /= hk_factor
            if inputs.recharge is not None:
                inputs.recharge /= rch_factor

        return {
            "mean": float(np.mean(results)),
            "std": float(np.std(results)),
            "ci_95": [
                float(np.percentile(results, 2.5)),
                float(np.percentile(results, 97.5)),
            ],
            "n_samples": len(results),
        }


# Register MODFLOW 6 model
register_model(
    model_class=MODFLOW6Model,
    name="MODFLOW 6",
    version="6.2.0",
    domain=ModelDomain.GROUNDWATER,
    fidelity=ModelFidelity.PROCESS_BASED,
    status=ModelStatus.EXPERIMENTAL,
    description="USGS modular groundwater flow model (MODFLOW 6) via flopy",
    references=[
        "Langevin et al. (2017) MODFLOW 6: A modular framework for groundwater flow simulation",
        "Hughes et al. (2020) flopy: A Python package for MODFLOW",
    ],
    doi="10.5066/P9FQ0YGF",
    authors=["C. Langevin", "J. Hughes", "A. White"],
    tags=["groundwater", "flow", "transient", "calibration", "flopy"],
)
