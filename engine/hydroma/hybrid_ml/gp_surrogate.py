"""
Gaussian Process Surrogates for Fast Model Emulation
=====================================================

Provides GP-based emulators for:
- Fast approximation of expensive process models
- Uncertainty quantification
- Bayesian calibration
- Sensitivity analysis
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from engine.hydroma.models.base import ScientificModel
from engine.hydroma.models.expansion.registry import (
    ModelDomain,
    ModelFidelity,
    ModelStatus,
    register_model,
)

logger = logging.getLogger(__name__)

# Optional GPyTorch import
try:
    import gpytorch

    GPYTORCH_AVAILABLE = True
except ImportError:
    GPYTORCH_AVAILABLE = False
    gpytorch = None
    logger.warning("gpytorch not available - GP surrogates disabled")


@dataclass
class GPConfig:
    """Configuration for GP surrogate."""

    kernel: str = "matern"  # rbf, matern, rq, spectral
    nu: float = 2.5  # For Matern kernel
    ard: bool = True  # Automatic relevance determination
    normalize_y: bool = True
    noise_prior: tuple[float, float] | None = None  # (concentration, rate) for Gamma prior
    learning_rate: float = 0.1
    training_iterations: int = 200
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


if GPYTORCH_AVAILABLE:

    class ExactGPModel(gpytorch.models.ExactGP):
        """Exact Gaussian Process Model."""

        def __init__(
            self,
            train_x: torch.Tensor,
            train_y: torch.Tensor,
            likelihood: gpytorch.likelihoods.GaussianLikelihood,
            kernel_type: str = "matern",
            ard: bool = True,
            nu: float = 2.5,
        ):
            super().__init__(train_x, train_y, likelihood)
            self.mean_module = gpytorch.means.ConstantMean()

            if kernel_type == "rbf":
                base_kernel = gpytorch.kernels.RBFKernel(
                    ard_num_dims=train_x.shape[1] if ard else None
                )
            elif kernel_type == "matern":
                base_kernel = gpytorch.kernels.MaternKernel(
                    nu=nu, ard_num_dims=train_x.shape[1] if ard else None
                )
            elif kernel_type == "rq":
                base_kernel = gpytorch.kernels.RQKernel(
                    ard_num_dims=train_x.shape[1] if ard else None
                )
            elif kernel_type == "spectral":
                base_kernel = gpytorch.kernels.SpectralMixtureKernel(
                    num_mixtures=4, ard_num_dims=train_x.shape[1] if ard else None
                )
            else:
                base_kernel = gpytorch.kernels.MaternKernel(
                    nu=nu, ard_num_dims=train_x.shape[1] if ard else None
                )

            self.covar_module = gpytorch.kernels.ScaleKernel(base_kernel)

        def forward(self, x: torch.Tensor) -> gpytorch.distributions.MultivariateNormal:
            mean_x = self.mean_module(x)
            covar_x = self.covar_module(x)
            return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)
else:

    class ExactGPModel:
        """Mock class when gpytorch not available."""

        def __init__(self, *args, **kwargs):
            pass

        def forward(self, x):
            return None


class GPSurrogateModel(ScientificModel):
    """
    Gaussian Process Surrogate Model.

    Provides fast emulation of expensive process models with:
    - Predictive mean and variance
    - Gradient information
    - Sensitivity indices
    - Bayesian calibration support
    """

    def __init__(
        self,
        base_model: ScientificModel | None = None,
        config: GPConfig | None = None,
        input_dim: int | None = None,
        output_dim: int = 1,
    ):
        """
        Initialize GP surrogate.

        Args:
            base_model: Optional base model to emulate
            config: GP configuration
            input_dim: Input dimension (required if no base_model)
            output_dim: Output dimension
        """
        self.base_model = base_model
        self.config = config or GPConfig()
        self.input_dim = input_dim
        self.output_dim = output_dim

        self._model: ExactGPModel | None = None
        self._likelihood: Any | None = None
        self._trained = False
        self._train_x: torch.Tensor | None = None
        self._train_y: torch.Tensor | None = None
        self._y_mean: float = 0.0
        self._y_std: float = 1.0

        if not GPYTORCH_AVAILABLE:
            logger.warning("GPyTorch not available - using mock mode")

    def validate_inputs(self, inputs: ModelInput) -> bool:
        """Validate inputs."""
        if self.input_dim is not None:
            query_points = inputs.get("query_points")
            if query_points is not None and isinstance(query_points, np.ndarray):
                if query_points.shape[1] != self.input_dim:
                    raise ValueError(
                        f"Expected {self.input_dim} input dimensions, got {query_points.shape[1]}"
                    )
        return True

    def train_on_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        optimize: bool = True,
    ) -> dict[str, Any]:
        """
        Train GP on provided data.

        Args:
            X: Training inputs (n_samples, n_features)
            y: Training outputs (n_samples,) or (n_samples, n_outputs)
            optimize: Whether to optimize hyperparameters

        Returns:
            Training metrics
        """
        if not GPYTORCH_AVAILABLE:
            return self._train_mock(X, y)

        import gpytorch

        # Convert to tensors
        X_tensor = torch.tensor(X, dtype=torch.float32, device=self.config.device)
        y_tensor = torch.tensor(y, dtype=torch.float32, device=self.config.device)

        # Normalize outputs
        if self.config.normalize_y:
            self._y_mean = float(y_tensor.mean())
            self._y_std = float(y_tensor.std() + 1e-6)
            y_tensor = (y_tensor - self._y_mean) / self._y_std

        # Likelihood
        self._likelihood = gpytorch.likelihoods.GaussianLikelihood()
        if self.config.noise_prior:
            self._likelihood.noise_covar.register_prior(
                "noise_prior",
                gpytorch.priors.GammaPrior(*self.config.noise_prior),
                "noise",
            )

        # Model
        self._model = ExactGPModel(
            X_tensor,
            y_tensor,
            self._likelihood,
            kernel_type=self.config.kernel,
            ard=self.config.ard,
            nu=self.config.nu,
        )

        self._model.to(self.config.device)
        self._likelihood.to(self.config.device)

        # Store training data
        self._train_x = X_tensor
        self._train_y = y_tensor

        if optimize:
            return self._optimize()

        self._trained = True
        return {"status": "initialized"}

    def _train_mock(self, X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """Mock training for when GPyTorch unavailable."""
        self._train_x = torch.tensor(X, dtype=torch.float32)
        self._train_y = torch.tensor(y, dtype=torch.float32)
        self._trained = True
        return {"status": "mock_trained", "n_samples": len(X)}

    def _optimize(self) -> dict[str, Any]:
        """Optimize hyperparameters."""
        if not GPYTORCH_AVAILABLE:
            return {}

        import gpytorch

        self._model.train()
        self._likelihood.train()

        optimizer = torch.optim.Adam(
            [
                {"params": self._model.parameters()},
            ],
            lr=self.config.learning_rate,
        )

        mll = gpytorch.mlls.ExactMarginalLogLikelihood(self._likelihood, self._model)

        losses = []
        for i in range(self.config.training_iterations):
            optimizer.zero_grad()
            output = self._model(self._train_x)
            loss = -mll(output, self._train_y)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())

            if i % 50 == 0:
                logger.info(f"Iter {i}/{self.config.training_iterations}: Loss = {loss.item():.4f}")

        self._trained = True
        self._model.eval()
        self._likelihood.eval()

        return {
            "final_loss": losses[-1],
            "loss_history": losses,
            "lengthscales": self._model.covar_module.base_kernel.lengthscale.detach()
            .cpu()
            .numpy()
            .tolist(),
            "outputscale": self._model.covar_module.outputscale.item(),
            "noise": self._likelihood.noise.item(),
        }

    def train_from_base_model(
        self,
        n_samples: int = 500,
        bounds: list[tuple[float, float]] | None = None,
        sampler: str = "lhs",
    ) -> dict[str, Any]:
        """
        Train surrogate by sampling from base model.

        Args:
            n_samples: Number of training samples
            bounds: Parameter bounds [(min, max), ...]
            sampler: Sampling method (lhs, random, sobol)
        """
        if self.base_model is None:
            raise ValueError("No base model provided")

        if bounds is None:
            raise ValueError("Parameter bounds required")

        # Generate samples
        if sampler == "lhs":
            X = self._latin_hypercube_sampling(n_samples, bounds)
        elif sampler == "sobol":
            X = self._sobol_sampling(n_samples, bounds)
        else:
            X = np.random.uniform(
                [b[0] for b in bounds], [b[1] for b in bounds], size=(n_samples, len(bounds))
            )

        # Run base model
        y = []
        for i, x in enumerate(X):
            if i % 50 == 0:
                logger.info(f"Running base model {i + 1}/{n_samples}")
            try:
                input_data = ModelInput(
                    **dict(zip([f"param_{j}" for j in range(len(x))], x, strict=False))
                )
                output = self.base_model.compute(input_data)
                if output.success:
                    # Extract scalar output
                    if isinstance(output.outputs, dict):
                        val = next(iter(output.outputs.values()))
                        if isinstance(val, (list, np.ndarray)):
                            val = np.mean(val)
                        y.append(float(val))
                    else:
                        y.append(float(output.outputs))
                else:
                    y.append(np.nan)
            except Exception as e:
                logger.warning(f"Base model failed at sample {i}: {e}")
                y.append(np.nan)

        y = np.array(y)
        valid = ~np.isnan(y)
        logger.info(f"Valid samples: {valid.sum()}/{n_samples}")

        return self.train_on_data(X[valid], y[valid])

    def _latin_hypercube_sampling(self, n: int, bounds: list[tuple[float, float]]) -> np.ndarray:
        """Latin Hypercube Sampling."""
        from scipy.stats import qmc

        sampler = qmc.LatinHypercube(d=len(bounds))
        sample = sampler.random(n=n)
        # Scale to bounds
        lbs = np.array([b[0] for b in bounds])
        ubs = np.array([b[1] for b in bounds])
        return qmc.scale(sample, lbs, ubs)

    def _sobol_sampling(self, n: int, bounds: list[tuple[float, float]]) -> np.ndarray:
        """Sobol sequence sampling."""
        from scipy.stats import qmc

        sampler = qmc.Sobol(d=len(bounds), scramble=True)
        sample = sampler.random(n=n)
        lbs = np.array([b[0] for b in bounds])
        ubs = np.array([b[1] for b in bounds])
        return qmc.scale(sample, lbs, ubs)

    def compute(self, inputs: ModelInput) -> ModelOutput:
        """Predict using trained GP."""
        if not self._trained:
            return ModelOutput(
                success=False,
                error_message="GP not trained",
                outputs={},
            )

        query_points = inputs.get("query_points")
        if query_points is None:
            return ModelOutput(
                success=False,
                error_message="query_points required",
                outputs={},
            )

        X = np.array(query_points)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        mean, std = self.predict(X)

        return ModelOutput(
            success=True,
            outputs={
                "mean": mean.tolist(),
                "std": std.tolist(),
            },
            uncertainty={
                "epistemic": std.tolist(),
                "aleatoric": [0.0] * len(std),
            },
        )

    def predict(
        self,
        X: np.ndarray,
        return_std: bool = True,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """
        Predict at new points.

        Args:
            X: Query points (n_query, n_features)
            return_std: Whether to return standard deviation

        Returns:
            (mean, std) if return_std else mean
        """
        if not GPYTORCH_AVAILABLE:
            return self._predict_mock(X)

        import gpytorch

        self._model.eval()
        self._likelihood.eval()

        X_tensor = torch.tensor(X, dtype=torch.float32, device=self.config.device)

        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            preds = self._likelihood(self._model(X_tensor))
            mean = preds.mean.cpu().numpy()
            if return_std:
                std = preds.stddev.cpu().numpy()
                # Denormalize
                if self.config.normalize_y:
                    mean = mean * self._y_std + self._y_mean
                    std = std * self._y_std
                return mean, std
            else:
                if self.config.normalize_y:
                    mean = mean * self._y_std + self._y_mean
                return mean, None

    def _predict_mock(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Mock prediction."""
        n = X.shape[0]
        mean = np.random.randn(n) * 10
        std = np.abs(np.random.randn(n)) + 0.1
        return mean, std

    def predict_with_gradients(
        self,
        X: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict with gradients.

        Returns:
            (mean, std, gradients) where gradients is (n, d)
        """
        if not GPYTORCH_AVAILABLE:
            n, d = X.shape
            return np.random.randn(n), np.abs(np.random.randn(n)) + 0.1, np.random.randn(n, d)

        import gpytorch

        self._model.eval()
        self._likelihood.eval()

        X_tensor = torch.tensor(
            X, dtype=torch.float32, device=self.config.device, requires_grad=True
        )

        with gpytorch.settings.fast_pred_var():
            preds = self._likelihood(self._model(X_tensor))
            mean = preds.mean

            # Compute gradients
            gradients = torch.autograd.grad(mean.sum(), X_tensor, create_graph=True)[0]

        mean_np = mean.detach().cpu().numpy()
        std_np = preds.stddev.detach().cpu().numpy()
        grad_np = gradients.detach().cpu().numpy()

        if self.config.normalize_y:
            mean_np = mean_np * self._y_std + self._y_mean
            std_np = std_np * self._y_std
            grad_np = grad_np * self._y_std

        return mean_np, std_np, grad_np

    def sensitivity_indices(self, n_samples: int = 10000) -> dict[str, np.ndarray]:
        """
        Compute Sobol sensitivity indices.

        Returns:
            Dict with 'S1' (first-order) and 'ST' (total-order) indices
        """
        if self._train_x is None:
            return {}

        # Use Saltelli's method via SALib if available
        try:
            from SALib.analyze import sobol
            from SALib.sample import saltelli

            # Define problem
            problem = {
                "num_vars": self.input_dim,
                "names": [f"x{i}" for i in range(self.input_dim)],
                "bounds": [[0, 1]] * self.input_dim,  # Normalized bounds
            }

            # Generate samples
            param_values = saltelli.sample(problem, n_samples, calc_second_order=False)

            # Evaluate GP
            Y = self.predict(param_values)[0]

            # Analyze
            Si = sobol.analyze(problem, Y, calc_second_order=False, print_to_console=False)

            return {
                "S1": Si["S1"],
                "ST": Si["ST"],
                "S1_conf": Si["S1_conf"],
                "ST_conf": Si["ST_conf"],
            }
        except ImportError:
            logger.warning("SALib not available for sensitivity analysis")
            return {}

    def validate_against_reference(
        self,
        reference_data: ModelInput,
        tolerance: float = 0.1,
    ) -> bool:
        """Validate against reference data."""
        if not self._trained:
            return False

        query_points = reference_data.get("query_points")
        reference_values = reference_data.get("reference_values")

        if query_points is None or reference_values is None:
            return False

        mean, _std = self.predict(query_points)
        errors = np.abs(mean - reference_values) / (np.abs(reference_values) + 1e-6)

        return np.mean(errors) <= tolerance

    def uncertainty_quantification(
        self, inputs: ModelInput, n_samples: int = 100
    ) -> dict[str, Any]:
        """Full UQ including epistemic and aleatoric uncertainty."""
        query_points = inputs.get("query_points")
        if query_points is None:
            return {}

        mean, std = self.predict(query_points)

        # Sample from predictive distribution
        samples = np.random.normal(mean, std, size=(n_samples, len(mean)))

        return {
            "mean": mean.tolist(),
            "std": std.tolist(),
            "samples": samples.tolist(),
            "ci_95": [
                np.percentile(samples, 2.5, axis=0).tolist(),
                np.percentile(samples, 97.5, axis=0).tolist(),
            ],
            "ci_50": [
                np.percentile(samples, 25, axis=0).tolist(),
                np.percentile(samples, 75, axis=0).tolist(),
            ],
        }

    def save(self, path: Path) -> None:
        """Save GP model."""
        if not GPYTORCH_AVAILABLE:
            return

        torch.save(
            {
                "model_state_dict": self._model.state_dict(),
                "likelihood_state_dict": self._likelihood.state_dict(),
                "config": self.config,
                "input_dim": self.input_dim,
                "output_dim": self.output_dim,
                "y_mean": self._y_mean,
                "y_std": self._y_std,
            },
            path,
        )

    @classmethod
    def load(cls, path: Path) -> GPSurrogateModel:
        """Load GP model."""
        if not GPYTORCH_AVAILABLE:
            return cls()

        import gpytorch

        checkpoint = torch.load(path, map_location="cpu")

        model = cls(
            config=checkpoint["config"],
            input_dim=checkpoint["input_dim"],
            output_dim=checkpoint["output_dim"],
        )

        model._y_mean = checkpoint["y_mean"]
        model._y_std = checkpoint["y_std"]
        model._trained = True

        model._likelihood = gpytorch.likelihoods.GaussianLikelihood()
        model._model = ExactGPModel(
            torch.empty(0, checkpoint["input_dim"]),
            torch.empty(0),
            model._likelihood,
            kernel_type=model.config.kernel,
            ard=model.config.ard,
            nu=model.config.nu,
        )

        model._model.load_state_dict(checkpoint["model_state_dict"])
        model._likelihood.load_state_dict(checkpoint["likelihood_state_dict"])

        return model


# Register GP Surrogate
register_model(
    model_class=GPSurrogateModel,
    name="Gaussian Process Surrogate",
    version="1.0.0",
    domain=ModelDomain.HYDROLOGY,
    fidelity=ModelFidelity.HYBRID,
    status=ModelStatus.EXPERIMENTAL,
    description="Gaussian Process emulator for fast model approximation",
    references=[
        "Rasmussen & Williams (2006) Gaussian Processes for Machine Learning",
        "Kennedy & O'Hagan (2001) Bayesian calibration of computer models",
    ],
    doi="10.1111/1467-9868.00294",
    authors=["C. Rasmussen", "C. Williams", "M. Kennedy", "A. O'Hagan"],
    tags=["gp", "surrogate", "emulator", "bayesian", "uq"],
)
