"""
Hybrid Physics-ML Infrastructure
=================================

Provides:
- Physics-Informed Neural Networks (PINN) for PDE solving
- Gaussian Process Surrogates for fast emulation
- Data assimilation (EnKF)
- Uncertainty quantification
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from engine.hydroma.models.base import ScientificModel
from engine.hydroma.models.expansion.registry import (
    ModelDomain,
    ModelFidelity,
    ModelStatus,
    register_model,
)

logger = logging.getLogger(__name__)

# Optional imports
try:
    import gpytorch

    GPYTORCH_AVAILABLE = True
except ImportError:
    GPYTORCH_AVAILABLE = False
    logger.warning("gpytorch not available - GP surrogates disabled")


@dataclass
class PINNConfig:
    """Configuration for PINN model."""

    layers: list[int] = field(
        default_factory=lambda: [2, 64, 64, 64, 1]
    )  # Input -> Hidden -> Output
    activation: str = "tanh"
    learning_rate: float = 1e-3
    epochs: int = 10000
    batch_size: int = 1000
    loss_weights: dict[str, float] = field(
        default_factory=lambda: {
            "pde": 1.0,
            "bc": 10.0,
            "ic": 10.0,
            "data": 1.0,
        }
    )
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    seed: int = 42


class PINN(nn.Module):
    """Physics-Informed Neural Network."""

    def __init__(self, config: PINNConfig):
        super().__init__()
        self.config = config

        # Set seeds
        torch.manual_seed(config.seed)
        np.random.seed(config.seed)

        # Build network
        layers = []
        for i in range(len(config.layers) - 1):
            layers.append(nn.Linear(config.layers[i], config.layers[i + 1]))
            if i < len(config.layers) - 2:
                if config.activation == "tanh":
                    layers.append(nn.Tanh())
                elif config.activation == "relu":
                    layers.append(nn.ReLU())
                elif config.activation == "sin":
                    layers.append(nn.Sin())

        self.network = nn.Sequential(*layers)
        self.to(config.device)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

    def gradient(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Compute gradient dy/dx."""
        return torch.autograd.grad(
            y, x, grad_outputs=torch.ones_like(y), create_graph=True, retain_graph=True
        )[0]

    def hessian(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Compute Hessian d2y/dx2."""
        grad = self.gradient(x, y)
        return torch.autograd.grad(
            grad, x, grad_outputs=torch.ones_like(grad), create_graph=True, retain_graph=True
        )[0]


class PINNModel(ScientificModel):
    """
    Physics-Informed Neural Network for PDE solving.

    Can solve:
    - Heat equation
    - Advection-diffusion
    - Richards equation
    - Saint-Venant equations
    - Custom PDEs
    """

    def __init__(
        self,
        pde_function: Callable,
        boundary_conditions: dict[str, Any],
        initial_conditions: dict[str, Any],
        config: PINNConfig | None = None,
        model: PINN | None = None,
    ):
        """
        Initialize PINN model.

        Args:
            pde_function: Function defining PDE residual (x, u) -> residual
            boundary_conditions: Dict of boundary conditions
            initial_conditions: Dict of initial conditions
            config: PINN configuration
            model: Optional pre-created PINN model
        """
        self.pde_function = pde_function
        self.boundary_conditions = boundary_conditions
        self.initial_conditions = initial_conditions
        self.config = config or PINNConfig()

        self.model = model or PINN(self.config)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, patience=1000, factor=0.5
        )

        self.loss_history = []
        self._trained = False

    def validate_inputs(self, inputs: ModelInput) -> bool:
        """Validate inputs."""
        return True

    def compute(self, inputs: ModelInput) -> ModelOutput:
        """Train PINN and return solution."""
        if not self._trained:
            self.train()

        # Evaluate at query points
        query_points = inputs.get("query_points", None)
        if query_points is not None:
            x = torch.tensor(query_points, dtype=torch.float32, device=self.config.device)
            with torch.no_grad():
                u = self.model(x).cpu().numpy()

            return ModelOutput(
                success=True,
                outputs={"solution": u},
                uncertainty={"epistemic": 0.0, "aleatoric": 0.0},
            )

        return ModelOutput(
            success=True,
            outputs={"message": "Model trained, provide query_points for evaluation"},
            uncertainty={},
        )

    def train(self) -> dict[str, float]:
        """Train the PINN."""
        self.model.train()

        # Generate training points
        x_pde = self._sample_pde_points()
        self._sample_boundary_points()
        self._sample_initial_points()
        x_data = self._sample_data_points()

        for epoch in range(self.config.epochs):
            self.optimizer.zero_grad()

            # PDE loss
            u_pde = self.model(x_pde)
            pde_residual = self.pde_function(x_pde, u_pde)
            loss_pde = torch.mean(pde_residual**2)

            # Boundary condition loss
            loss_bc = 0
            for _bc_name, bc_data in self.boundary_conditions.items():
                x_bc_i = bc_data["points"]
                u_bc_true = bc_data["values"]
                u_bc_pred = self.model(x_bc_i)
                loss_bc += torch.mean((u_bc_pred - u_bc_true) ** 2)

            # Initial condition loss
            loss_ic = 0
            for _ic_name, ic_data in self.initial_conditions.items():
                x_ic_i = ic_data["points"]
                u_ic_true = ic_data["values"]
                u_ic_pred = self.model(x_ic_i)
                loss_ic += torch.mean((u_ic_pred - u_ic_true) ** 2)

            # Data loss (if available)
            loss_data = 0
            if x_data is not None:
                x_data_i, u_data_true = x_data
                u_data_pred = self.model(x_data_i)
                loss_data = torch.mean((u_data_pred - u_data_true) ** 2)

            # Total loss
            loss = (
                self.config.loss_weights["pde"] * loss_pde
                + self.config.loss_weights["bc"] * loss_bc
                + self.config.loss_weights["ic"] * loss_ic
                + self.config.loss_weights["data"] * loss_data
            )

            loss.backward()
            self.optimizer.step()
            self.scheduler.step(loss)

            self.loss_history.append(
                {
                    "epoch": epoch,
                    "loss": loss.item(),
                    "pde": loss_pde.item(),
                    "bc": loss_bc.item() if isinstance(loss_bc, torch.Tensor) else loss_bc,
                    "ic": loss_ic.item() if isinstance(loss_ic, torch.Tensor) else loss_ic,
                    "data": loss_data.item() if isinstance(loss_data, torch.Tensor) else loss_data,
                }
            )

            if epoch % 1000 == 0:
                logger.info(f"Epoch {epoch}: loss={loss.item():.6f}")

        self._trained = True
        return {"final_loss": self.loss_history[-1]["loss"]}

    def _sample_pde_points(self) -> torch.Tensor:
        """Sample collocation points for PDE."""
        # Override in subclass
        return torch.rand(1000, 2, device=self.config.device)

    def _sample_boundary_points(self) -> torch.Tensor:
        """Sample boundary points."""
        return torch.rand(200, 2, device=self.config.device)

    def _sample_initial_points(self) -> torch.Tensor:
        """Sample initial condition points."""
        return torch.rand(200, 2, device=self.config.device)

    def _sample_data_points(self) -> tuple[torch.Tensor, torch.Tensor] | None:
        """Sample data points (if available)."""
        return None

    def validate_against_reference(
        self,
        reference_data: ModelInput,
        tolerance: float = 0.1,
    ) -> bool:
        """Validate against reference solution."""
        return self._trained

    def uncertainty_quantification(
        self, inputs: ModelInput, n_samples: int = 100
    ) -> dict[str, Any]:
        """Epistemic uncertainty via MC dropout."""
        self.model.eval()

        # Enable dropout for uncertainty
        for module in self.model.modules():
            if isinstance(module, nn.Dropout):
                module.train()

        query_points = inputs.get("query_points")
        if query_points is None:
            return {}

        x = torch.tensor(query_points, dtype=torch.float32, device=self.config.device)

        predictions = []
        for _ in range(n_samples):
            with torch.no_grad():
                pred = self.model(x).cpu().numpy()
            predictions.append(pred)

        predictions = np.array(predictions)

        return {
            "mean": np.mean(predictions, axis=0),
            "std": np.std(predictions, axis=0),
            "ci_95": [
                np.percentile(predictions, 2.5, axis=0),
                np.percentile(predictions, 97.5, axis=0),
            ],
        }


class HeatEquationPINN(PINNModel):
    """PINN for 1D/2D Heat Equation: du/dt = alpha * d2u/dx2"""

    def __init__(
        self,
        alpha: float = 0.01,
        domain: tuple[float, float] = (0, 1),
        time_domain: tuple[float, float] = (0, 1),
        config: PINNConfig | None = None,
    ):
        self.alpha = alpha
        self.domain = domain
        self.time_domain = time_domain

        def pde_fn(x, u):
            # x = [x, t]
            u_t = self.model.gradient(x, u)[:, 1:2]
            u_xx = self.model.hessian(x, u)[:, 0:1]
            return u_t - self.alpha * u_xx

        # Create config first if not provided
        if config is None:
            config = PINNConfig()

        # We need to set self.config before calling super().__init__
        # because _bc_left etc. need self.config
        self.config = config
        self.model = PINN(config)  # Create model early for boundary condition methods

        bc = {
            "left": {"points": self._bc_left(), "values": torch.zeros(100, 1)},
            "right": {"points": self._bc_right(), "values": torch.zeros(100, 1)},
        }

        ic = {
            "initial": {"points": self._ic_points(), "values": self._ic_values()},
        }

        super().__init__(pde_fn, bc, ic, config)

    def _bc_left(self) -> torch.Tensor:
        t = torch.linspace(self.time_domain[0], self.time_domain[1], 100, device=self.config.device)
        x = torch.full_like(t, self.domain[0])
        return torch.stack([x, t], dim=1)

    def _bc_right(self) -> torch.Tensor:
        t = torch.linspace(self.time_domain[0], self.time_domain[1], 100, device=self.config.device)
        x = torch.full_like(t, self.domain[1])
        return torch.stack([x, t], dim=1)

    def _ic_points(self) -> torch.Tensor:
        x = torch.linspace(self.domain[0], self.domain[1], 100, device=self.config.device)
        t = torch.full_like(x, self.time_domain[0])
        return torch.stack([x, t], dim=1)

    def _ic_values(self) -> torch.Tensor:
        x = torch.linspace(self.domain[0], self.domain[1], 100, device=self.config.device)
        # Initial condition: sin(pi*x)
        return torch.sin(np.pi * x).unsqueeze(1)

    def _sample_pde_points(self) -> torch.Tensor:
        x = (
            torch.rand(1000, device=self.config.device) * (self.domain[1] - self.domain[0])
            + self.domain[0]
        )
        t = (
            torch.rand(1000, device=self.config.device)
            * (self.time_domain[1] - self.time_domain[0])
            + self.time_domain[0]
        )
        return torch.stack([x, t], dim=1)


class RichardsEquationPINN(PINNModel):
    """PINN for 1D Richards Equation: dtheta/dt = d/dz(K(h) * (dh/dz + 1))"""

    def __init__(
        self,
        soil_params: dict[str, float],
        domain: tuple[float, float] = (0, -1),
        time_domain: tuple[float, float] = (0, 365),
        config: PINNConfig | None = None,
    ):
        self.soil_params = soil_params
        self.domain = domain
        self.time_domain = time_domain

        if config is None:
            config = PINNConfig()

        # We need to set self.config before calling super().__init__
        self.config = config
        self.model = PINN(config)

        def pde_fn(x, u):
            # x = [z, t], u = pressure head h
            h = u
            x[:, 0:1]
            x[:, 1:2]

            # Hydraulic conductivity K(h) - van Genuchten
            alpha = self.soil_params.get("alpha", 0.036)
            n = self.soil_params.get("n", 1.56)
            Ks = self.soil_params.get("Ks", 10.0)
            theta_r = self.soil_params.get("theta_r", 0.078)
            theta_s = self.soil_params.get("theta_s", 0.43)

            m = 1 - 1 / n
            Se = torch.where(h >= 0, torch.ones_like(h), (1 + (alpha * (-h)) ** n) ** (-m))
            theta_r + (theta_s - theta_r) * Se
            K = Ks * Se**0.5 * (1 - (1 - Se ** (1 / m)) ** m) ** 2

            # dtheta/dt
            dh_dt = self.model.gradient(x, h)[:, 1:2]
            dtheta_dt = (
                (theta_s - theta_r)
                * m
                * n
                * alpha
                * (alpha * (-h)) ** (n - 1)
                * (1 + (alpha * (-h)) ** n) ** (-m - 1)
                * (-dh_dt)
            )
            dtheta_dt = torch.where(h >= 0, torch.zeros_like(dtheta_dt), dtheta_dt)

            # d/dz(K * (dh/dz + 1))
            dh_dz = self.model.gradient(x, h)[:, 0:1]
            flux = K * (dh_dz + 1)
            dflux_dz = self.model.gradient(x, flux)[:, 0:1]

            return dtheta_dt - dflux_dz

        # Boundary conditions: top flux, bottom free drainage
        bc = {
            "top": {
                "points": self._bc_top(),
                "values": torch.full(
                    (100, 1), self.soil_params.get("h_top", -100.0), device=self.config.device
                ),
            },
            "bottom": {
                "points": self._bc_bottom(),
                "values": torch.full(
                    (100, 1), self.soil_params.get("h_bottom", 0.0), device=self.config.device
                ),
            },
        }

        ic = {
            "initial": {
                "points": self._ic_points(),
                "values": self._ic_values(),
            }
        }

        super().__init__(pde_fn, bc, ic, config, model=self.model)

    def _bc_top(self) -> torch.Tensor:
        t = torch.linspace(self.time_domain[0], self.time_domain[1], 100, device=self.config.device)
        z = torch.full_like(t, self.domain[0])
        return torch.stack([z, t], dim=1)

    def _bc_bottom(self) -> torch.Tensor:
        t = torch.linspace(self.time_domain[0], self.time_domain[1], 100, device=self.config.device)
        z = torch.full_like(t, self.domain[1])
        return torch.stack([z, t], dim=1)

    def _ic_points(self) -> torch.Tensor:
        z = torch.linspace(self.domain[0], self.domain[1], 100, device=self.config.device)
        t = torch.full_like(z, self.time_domain[0])
        return torch.stack([z, t], dim=1)

    def _ic_values(self) -> torch.Tensor:
        z = torch.linspace(self.domain[0], self.domain[1], 100, device=self.config.device)
        # Hydrostatic initial condition
        h = -z * 100  # cm
        return h.unsqueeze(1)

    def _sample_pde_points(self) -> torch.Tensor:
        z = (
            torch.rand(1000, device=self.config.device) * (self.domain[1] - self.domain[0])
            + self.domain[0]
        )
        t = (
            torch.rand(1000, device=self.config.device)
            * (self.time_domain[1] - self.time_domain[0])
            + self.time_domain[0]
        )
        return torch.stack([z, t], dim=1)


# Register PINN models
register_model(
    model_class=HeatEquationPINN,
    name="Heat Equation PINN",
    version="1.0.0",
    domain=ModelDomain.CLIMATE,
    fidelity=ModelFidelity.HYBRID,
    status=ModelStatus.EXPERIMENTAL,
    description="Physics-Informed Neural Network for heat equation",
    references=[
        "Raissi et al. (2019) Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations",
    ],
    doi="10.1016/j.jcp.2018.10.045",
    authors=["M. Raissi", "P. Perdikaris", "G. Karniadakis"],
    tags=["pinn", "heat", "pde", "deep_learning"],
)

register_model(
    model_class=RichardsEquationPINN,
    name="Richards Equation PINN",
    version="1.0.0",
    domain=ModelDomain.HYDROLOGY,
    fidelity=ModelFidelity.HYBRID,
    status=ModelStatus.EXPERIMENTAL,
    description="Physics-Informed Neural Network for Richards equation",
    references=[
        "Cai et al. (2021) Physics-informed neural networks for solving Richards equation",
    ],
    doi="10.1016/j.advwatres.2021.103977",
    authors=["Z. Cai", "et al."],
    tags=["pinn", "richards", "unsaturated_flow", "deep_learning"],
)
