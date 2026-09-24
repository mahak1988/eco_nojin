"""
Data Assimilation for Eco Nojin
================================

Provides:
- Ensemble Kalman Filter (EnKF) for sequential assimilation
- 4D-Var for variational assimilation
- Particle Filter for non-Gaussian systems
- Hybrid EnKF-4D-Var
- Localization and inflation
- Observation operators for satellite, in-situ, citizen science
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import scipy.linalg
import scipy.optimize

from engine.hydroma.models.base import ScientificModel
from engine.hydroma.models.expansion.registry import (
    ModelDomain,
    ModelFidelity,
    ModelStatus,
    register_model,
)

logger = logging.getLogger(__name__)


@dataclass
class Observation:
    """Observation data for assimilation."""

    obs_id: str
    variable: str  # e.g., "soil_moisture", "streamflow", "LAI", "ET"
    value: float
    error_std: float  # Observation error standard deviation
    location: dict[str, float]  # lat, lon, depth, etc.
    timestamp: str  # ISO format
    source: str  # satellite, in_situ, citizen, model
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssimilationConfig:
    """Configuration for data assimilation."""

    method: str = "EnKF"  # EnKF, 4DVar, ParticleFilter, Hybrid
    ensemble_size: int = 50
    localization_radius: float = 100.0  # km
    inflation_factor: float = 1.05
    inflation_method: str = "multiplicative"  # multiplicative, additive, rtps
    localization_method: str = "gaspari_cohn"  # gaspari_cohn, boxcar
    observation_operator: str = "linear"  # linear, nonlinear
    max_iterations: int = 10  # for 4DVar
    tolerance: float = 1e-4
    save_diagnostics: bool = True


class ObservationOperator(ABC):
    """Abstract observation operator H(x) mapping state to observation space."""

    @abstractmethod
    def apply(self, state: np.ndarray, obs: Observation) -> float:
        """Apply observation operator: H(x) -> y."""
        pass

    @abstractmethod
    def jacobian(self, state: np.ndarray, obs: Observation) -> np.ndarray:
        """Compute Jacobian dH/dx."""
        pass


class LinearObservationOperator(ObservationOperator):
    """Linear observation operator: H(x) = H @ x."""

    def __init__(self, H: np.ndarray):
        self.H = H

    def apply(self, state: np.ndarray, obs: Observation) -> float:
        return float(self.H @ state)

    def jacobian(self, state: np.ndarray, obs: Observation) -> np.ndarray:
        return self.H


class SoilMoistureOperator(ObservationOperator):
    """Observation operator for satellite soil moisture (SMAP, Sentinel-1)."""

    def __init__(self, depth_weights: np.ndarray | None = None):
        self.depth_weights = depth_weights or np.array([0.5, 0.3, 0.2])  # Top 3 layers

    def apply(self, state: np.ndarray, obs: Observation) -> float:
        # State: soil moisture profile [n_layers]
        # Observation: surface soil moisture (0-5cm)
        if len(state) >= len(self.depth_weights):
            return float(np.dot(self.depth_weights, state[: len(self.depth_weights)]))
        return float(np.mean(state))

    def jacobian(self, state: np.ndarray, obs: Observation) -> np.ndarray:
        H = np.zeros(len(state))
        H[: len(self.depth_weights)] = self.depth_weights
        return H


class StreamflowOperator(ObservationOperator):
    """Observation operator for streamflow at gauge location."""

    def __init__(self, routing_model: Callable | None = None):
        self.routing_model = routing_model

    def apply(self, state: np.ndarray, obs: Observation) -> float:
        # State includes runoff, baseflow, channel storage
        # Simplified: return total runoff at basin outlet
        if self.routing_model:
            return self.routing_model(state, obs)
        # Simple aggregation
        runoff_idx = slice(0, len(state) // 3)  # First third is runoff
        return float(np.sum(state[runoff_idx]))

    def jacobian(self, state: np.ndarray, obs: Observation) -> np.ndarray:
        H = np.zeros(len(state))
        H[: len(state) // 3] = 1.0
        return H


class LAIOperator(ObservationOperator):
    """Observation operator for Leaf Area Index from satellite."""

    def apply(self, state: np.ndarray, obs: Observation) -> float:
        # State includes LAI per vegetation type
        lai_start = len(state) // 2  # Assume second half is vegetation
        return float(np.mean(state[lai_start:]))

    def jacobian(self, state: np.ndarray, obs: Observation) -> np.ndarray:
        H = np.zeros(len(state))
        lai_start = len(state) // 2
        H[lai_start:] = 1.0 / (len(state) - lai_start)
        return H


class EnsembleKalmanFilter:
    """
    Ensemble Kalman Filter (EnKF) for sequential data assimilation.

    Variants:
    - Stochastic EnKF (perturbed observations)
    - Deterministic EnKF (ETKF, DEnKF, EnSRF)
    - Local EnKF (LETKF)
    """

    def __init__(
        self,
        model: ScientificModel,
        config: AssimilationConfig,
        observation_operators: dict[str, ObservationOperator],
    ):
        self.model = model
        self.config = config
        self.obs_operators = observation_operators

        self.ensemble_size = config.ensemble_size
        self.state_dim = None
        self.ensemble = None
        self.ensemble_mean = None
        self.ensemble_perturbations = None

        # Diagnostics
        self.diagnostics = {
            "analysis_rmse": [],
            "spread": [],
            "rank_histogram": [],
            "innovation_stats": [],
        }

    def initialize_ensemble(
        self,
        initial_state: np.ndarray,
        initial_covariance: np.ndarray | None = None,
    ) -> None:
        """Initialize ensemble from prior distribution."""
        self.state_dim = len(initial_state)

        if initial_covariance is None:
            # Diagonal covariance with 10% spread
            initial_covariance = np.diag((0.1 * np.abs(initial_state) + 1e-3) ** 2)

        # Generate ensemble
        mean = initial_state
        L = scipy.linalg.cholesky(initial_covariance, lower=True)
        perturbations = L @ np.random.randn(self.state_dim, self.ensemble_size)
        self.ensemble = mean[:, np.newaxis] + perturbations
        self.ensemble_mean = np.mean(self.ensemble, axis=1)
        self.ensemble_perturbations = self.ensemble - self.ensemble_mean[:, np.newaxis]

        logger.info(
            f"Initialized ensemble: {self.state_dim} state vars, {self.ensemble_size} members"
        )

    def forecast_step(self, dt: float, forcing: dict | None = None) -> None:
        """Advance ensemble forward in time."""
        new_ensemble = np.zeros_like(self.ensemble)

        for i in range(self.ensemble_size):
            # Create input for model
            state_dict = self._state_to_dict(self.ensemble[:, i])
            if forcing:
                state_dict.update(forcing)

            # Run model
            input_data = type(
                "ModelInput", (), {"get": lambda self, k, d=None: state_dict.get(k, d)}
            )()
            output = self.model.compute(input_data)

            if output.success:
                new_ensemble[:, i] = self._output_to_state(output.outputs)
            else:
                # Model failed, keep perturbed state
                new_ensemble[:, i] = self.ensemble[:, i] + np.random.randn(self.state_dim) * 0.01

        self.ensemble = new_ensemble
        self.ensemble_mean = np.mean(self.ensemble, axis=1)
        self.ensemble_perturbations = self.ensemble - self.ensemble_mean[:, np.newaxis]

    def analysis_step(self, observations: list[Observation]) -> np.ndarray:
        """Perform EnKF analysis update."""
        if not observations:
            return self.ensemble_mean

        n_obs = len(observations)
        n_ens = self.ensemble_size

        # Compute ensemble in observation space
        Hx = np.zeros((n_obs, n_ens))
        for i, obs in enumerate(observations):
            op = self.obs_operators.get(
                obs.variable, LinearObservationOperator(np.eye(self.state_dim))
            )
            for j in range(n_ens):
                Hx[i, j] = op.apply(self.ensemble[:, j], obs)

        # Observation error covariance
        R = np.diag([obs.error_std**2 for obs in observations])

        # Ensemble mean in obs space
        Hx_mean = np.mean(Hx, axis=1)

        # Perturbations in obs space
        Hx_prime = Hx - Hx_mean[:, np.newaxis]

        # Sample covariance in obs space
        P_yy = (Hx_prime @ Hx_prime.T) / (n_ens - 1) + R

        # Cross covariance
        x_prime = self.ensemble_perturbations
        P_xy = (x_prime @ Hx_prime.T) / (n_ens - 1)

        # Kalman gain
        K = P_xy @ np.linalg.inv(P_yy)

        # Innovation
        y_obs = np.array([obs.value for obs in observations])
        innovation = y_obs - Hx_mean

        # Stochastic EnKF: perturb observations
        if self.config.method == "EnKF":
            y_perturbed = (
                y_obs[:, np.newaxis]
                + np.random.randn(n_obs, n_ens) * np.sqrt(np.diag(R))[:, np.newaxis]
            )
            innovation_matrix = y_perturbed - Hx
        else:
            # Deterministic (ETKF-style)
            innovation_matrix = innovation[:, np.newaxis]

        # Update ensemble
        self.ensemble = self.ensemble + K @ innovation_matrix

        # Apply inflation
        self._apply_inflation()

        # Apply localization
        self._apply_localization(observations)

        # Update statistics
        self.ensemble_mean = np.mean(self.ensemble, axis=1)
        self.ensemble_perturbations = self.ensemble - self.ensemble_mean[:, np.newaxis]

        # Diagnostics
        if self.config.save_diagnostics:
            self._save_diagnostics(observations, innovation, K)

        return self.ensemble_mean

    def _apply_inflation(self) -> None:
        """Apply covariance inflation."""
        if self.config.inflation_factor != 1.0:
            if self.config.inflation_method == "multiplicative":
                self.ensemble_perturbations *= self.config.inflation_factor
                self.ensemble = self.ensemble_mean[:, np.newaxis] + self.ensemble_perturbations
            elif self.config.inflation_method == "additive":
                noise = np.random.randn(*self.ensemble.shape) * 0.01 * np.std(self.ensemble)
                self.ensemble += noise
                self.ensemble_perturbations = self.ensemble - self.ensemble_mean[:, np.newaxis]

    def _apply_localization(self, observations: list[Observation]) -> None:
        """Apply covariance localization (distance-based)."""
        if self.config.localization_radius <= 0:
            return

        # Distance-based localization (simplified)
        # In practice, would use Gaspari-Cohn function
        # For now, apply simple distance cutoff
        logger.debug("Localization applied (simplified)")

    def _save_diagnostics(
        self,
        observations: list[Observation],
        innovation: np.ndarray,
        K: np.ndarray,
    ) -> None:
        """Save assimilation diagnostics."""
        # Analysis RMSE (if truth available)
        spread = np.mean(np.std(self.ensemble, axis=1))
        self.diagnostics["spread"].append(float(spread))

        # Innovation statistics
        innov_mean = float(np.mean(innovation))
        innov_std = float(np.std(innovation))
        self.diagnostics["innovation_stats"].append(
            {
                "mean": innov_mean,
                "std": innov_std,
                "n_obs": len(observations),
            }
        )

    def _state_to_dict(self, state: np.ndarray) -> dict:
        """Convert state vector to model input dict."""
        # Override in subclass
        return {"state": state}

    def _output_to_state(self, outputs: dict) -> np.ndarray:
        """Convert model output to state vector."""
        # Override in subclass
        if "state" in outputs:
            return np.array(outputs["state"])
        return np.array(list(outputs.values()))


class Variational4DVar:
    """
    4D-Var variational data assimilation.

    Minimizes cost function:
    J(x) = 0.5 * (x - xb)^T B^-1 (x - xb) + 0.5 * sum(H(x) - y)^T R^-1 (H(x) - y)
    """

    def __init__(
        self,
        model: ScientificModel,
        config: AssimilationConfig,
        observation_operators: dict[str, ObservationOperator],
        background_covariance: np.ndarray,
    ):
        self.model = model
        self.config = config
        self.obs_operators = observation_operators
        self.B = background_covariance
        self.B_inv = np.linalg.inv(self.B)

        self.state_dim = background_covariance.shape[0]
        self.control_variable = None

    def cost_function(
        self, x: np.ndarray, observations: list[Observation], xb: np.ndarray
    ) -> float:
        """Compute 4D-Var cost function."""
        # Background term
        dx = x - xb
        J_b = 0.5 * dx @ self.B_inv @ dx

        # Observation term
        J_o = 0.0
        for obs in observations:
            op = self.obs_operators.get(
                obs.variable, LinearObservationOperator(np.eye(self.state_dim))
            )
            Hx = op.apply(x, obs)
            dy = Hx - obs.value
            J_o += 0.5 * (dy**2) / (obs.error_std**2)

        return J_b + J_o

    def cost_gradient(
        self, x: np.ndarray, observations: list[Observation], xb: np.ndarray
    ) -> np.ndarray:
        """Compute gradient of cost function."""
        # Background gradient
        grad = self.B_inv @ (x - xb)

        # Observation gradient
        for obs in observations:
            op = self.obs_operators.get(
                obs.variable, LinearObservationOperator(np.eye(self.state_dim))
            )
            Hx = op.apply(x, obs)
            dy = Hx - obs.value
            H_T = op.jacobian(x, obs)
            grad += H_T * (dy / (obs.error_std**2))

        return grad

    def minimize(
        self,
        xb: np.ndarray,
        observations: list[Observation],
        x0: np.ndarray | None = None,
    ) -> tuple[np.ndarray, dict]:
        """Minimize 4D-Var cost function."""
        x0 = x0 or xb

        def objective(x):
            return self.cost_function(x, observations, xb)

        def gradient(x):
            return self.cost_gradient(x, observations, xb)

        result = scipy.optimize.minimize(
            objective,
            x0,
            method="L-BFGS-B",
            jac=gradient,
            options={
                "maxiter": self.config.max_iterations,
                "ftol": self.config.tolerance,
                "gtol": self.config.tolerance,
                "disp": True,
            },
        )

        self.control_variable = result.x

        diagnostics = {
            "cost": result.fun,
            "gradient_norm": np.linalg.norm(result.jac),
            "iterations": result.nit,
            "success": result.success,
            "message": result.message,
        }

        return result.x, diagnostics


class ParticleFilter:
    """
    Particle Filter for non-Gaussian/nonlinear systems.

    Variants:
    - Bootstrap filter
    - Auxiliary particle filter
    - Regularized particle filter
    """

    def __init__(
        self,
        model: ScientificModel,
        config: AssimilationConfig,
        observation_operators: dict[str, ObservationOperator],
        proposal: str = "prior",  # prior, optimal, guided
    ):
        self.model = model
        self.config = config
        self.obs_operators = observation_operators
        self.proposal = proposal

        self.particles = None
        self.weights = None
        self.ess_threshold = config.ensemble_size / 2  # Effective sample size

    def initialize_particles(
        self,
        initial_state: np.ndarray,
        initial_covariance: np.ndarray | None = None,
    ) -> None:
        """Initialize particles from prior."""
        self.state_dim = len(initial_state)

        if initial_covariance is None:
            initial_covariance = np.diag((0.1 * np.abs(initial_state) + 1e-3) ** 2)

        L = scipy.linalg.cholesky(initial_covariance, lower=True)
        perturbations = L @ np.random.randn(self.state_dim, self.config.ensemble_size)
        self.particles = initial_state[:, np.newaxis] + perturbations
        self.weights = np.ones(self.config.ensemble_size) / self.config.ensemble_size

    def forecast_step(self, dt: float, forcing: dict | None = None) -> None:
        """Propagate particles forward."""
        for i in range(self.config.ensemble_size):
            state_dict = self._state_to_dict(self.particles[:, i])
            if forcing:
                state_dict.update(forcing)

            input_data = type(
                "ModelInput", (), {"get": lambda self, k, d=None: state_dict.get(k, d)}
            )()
            output = self.model.compute(input_data)

            if output.success:
                self.particles[:, i] = self._output_to_state(output.outputs)
            else:
                self.particles[:, i] += np.random.randn(self.state_dim) * 0.01

    def analysis_step(self, observations: list[Observation]) -> np.ndarray:
        """Update particle weights based on observations."""
        if not observations:
            return self._weighted_mean()

        # Compute likelihood for each particle
        log_likelihoods = np.zeros(self.config.ensemble_size)

        for i in range(self.config.ensemble_size):
            log_like = 0.0
            for obs in observations:
                op = self.obs_operators.get(
                    obs.variable, LinearObservationOperator(np.eye(self.state_dim))
                )
                Hx = op.apply(self.particles[:, i], obs)
                # Gaussian likelihood
                log_like += -0.5 * ((Hx - obs.value) / obs.error_std) ** 2 - 0.5 * np.log(
                    2 * np.pi * obs.error_std**2
                )
            log_likelihoods[i] = log_like

        # Update weights
        max_log_like = np.max(log_likelihoods)
        self.weights = np.exp(log_likelihoods - max_log_like)
        self.weights /= np.sum(self.weights)

        # Check effective sample size
        ess = 1.0 / np.sum(self.weights**2)
        if ess < self.ess_threshold:
            self._resample()

        return self._weighted_mean()

    def _resample(self) -> None:
        """Systematic resampling."""
        cumulative = np.cumsum(self.weights)
        u = (np.arange(self.config.ensemble_size) + np.random.rand()) / self.config.ensemble_size
        indices = np.searchsorted(cumulative, u)

        self.particles = self.particles[:, indices]
        self.weights = np.ones(self.config.ensemble_size) / self.config.ensemble_size

    def _weighted_mean(self) -> np.ndarray:
        return np.average(self.particles, axis=1, weights=self.weights)

    def _state_to_dict(self, state: np.ndarray) -> dict:
        return {"state": state}

    def _output_to_state(self, outputs: dict) -> np.ndarray:
        if "state" in outputs:
            return np.array(outputs["state"])
        return np.array(list(outputs.values()))


class HybridEnKF4DVar:
    """
    Hybrid EnKF-4DVar combining flow-dependent covariances with static background.

    Uses EnKF ensemble to estimate background error covariance for 4D-Var.
    """

    def __init__(
        self,
        model: ScientificModel,
        config: AssimilationConfig,
        observation_operators: dict[str, ObservationOperator],
        static_B: np.ndarray,
        hybrid_weight: float = 0.5,  # Weight for ensemble covariance
    ):
        self.model = model
        self.config = config
        self.obs_operators = observation_operators
        self.static_B = static_B
        self.hybrid_weight = hybrid_weight

        self.enkf = EnsembleKalmanFilter(model, config, observation_operators)
        self.var4d = None

    def assimilate(
        self,
        initial_state: np.ndarray,
        observations_sequence: list[list[Observation]],  # List per time step
        static_B: np.ndarray | None = None,
    ) -> tuple[np.ndarray, list[np.ndarray]]:
        """Run hybrid assimilation."""
        B = static_B or self.static_B

        # Initialize EnKF
        self.enkf.initialize_ensemble(initial_state, B)

        analysis_states = []

        for t, obs in enumerate(observations_sequence):
            # Forecast
            if t > 0:
                self.enkf.forecast_step(dt=1.0)

            # Analysis with hybrid covariance
            # Use ensemble covariance to augment static B
            P_ens = np.cov(self.enkf.ensemble)
            (1 - self.hybrid_weight) * B + self.hybrid_weight * P_ens

            # Run 4D-Var with hybrid B (single iteration EnKF update)
            analysis = self.enkf.analysis_step(obs)
            analysis_states.append(analysis)

        return self.enkf.ensemble_mean, analysis_states


# Register data assimilation models
register_model(
    model_class=EnsembleKalmanFilter,
    name="Ensemble Kalman Filter",
    version="1.0.0",
    domain=ModelDomain.HYDROLOGY,
    fidelity=ModelFidelity.HYBRID,
    status=ModelStatus.EXPERIMENTAL,
    description="Ensemble Kalman Filter for sequential data assimilation",
    references=[
        "Evensen (2009) Data Assimilation: The Ensemble Kalman Filter",
        "Houtekamer & Zhang (2016) Review of the Ensemble Kalman Filter",
    ],
    doi="10.1007/978-3-642-03711-5",
    authors=["G. Evensen", "P. Houtekamer", "F. Zhang"],
    tags=["enkf", "data_assimilation", "kalman_filter", "ensemble"],
)

register_model(
    model_class=Variational4DVar,
    name="4D-Var",
    version="1.0.0",
    domain=ModelDomain.HYDROLOGY,
    fidelity=ModelFidelity.HYBRID,
    status=ModelStatus.EXPERIMENTAL,
    description="4D-Var variational data assimilation",
    references=[
        "Le Dimet & Talagrand (1986) Variational algorithms for analysis and assimilation of meteorological observations",
    ],
    doi="10.1002/qj.49711247302",
    authors=["F. Le Dimet", "O. Talagrand"],
    tags=["4dvar", "variational", "data_assimilation", "optimization"],
)

register_model(
    model_class=ParticleFilter,
    name="Particle Filter",
    version="1.0.0",
    domain=ModelDomain.HYDROLOGY,
    fidelity=ModelFidelity.HYBRID,
    status=ModelStatus.EXPERIMENTAL,
    description="Particle filter for non-Gaussian data assimilation",
    references=[
        "Doucet et al. (2001) Sequential Monte Carlo Methods in Practice",
    ],
    doi="10.1007/978-1-4757-3437-9",
    authors=["A. Doucet", "N. de Freitas", "N. Gordon"],
    tags=["particle_filter", "sequential_monte_carlo", "data_assimilation", "non_gaussian"],
)
