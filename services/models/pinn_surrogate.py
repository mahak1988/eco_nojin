"""
PINN Surrogate scaffold (Phase 7 — fast physics-informed surrogates).

Goal: replace slow iterative solvers with a trained neural surrogate so
the bot/USSD answers in milliseconds. PyTorch is OPTIONAL — without it the
module imports cleanly and reports ``available=False`` (honest, no crash).

Status: scaffold + toy training loop. Training a production surrogate for
a specific model (e.g. crop yield vs AquaCrop) is the next work item.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:  # pragma: no cover - environment dependent
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except Exception:
    torch = None  # type: ignore
    nn = None  # type: ignore
    TORCH_AVAILABLE = False


def available() -> bool:
    """Whether PyTorch is installed (the surrogate can actually run)."""
    return TORCH_AVAILABLE


class PINNSurrogate:
    """Small MLP surrogate with optional physics-informed regularization.

    Args:
        n_inputs: number of model inputs.
        n_outputs: number of model outputs.
        hidden: hidden layer sizes.
    """

    def __init__(self, n_inputs: int, n_outputs: int = 1, hidden: list[int] | None = None) -> None:
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "PyTorch is not installed — pip install torch to use PINNSurrogate"
            )
        layers: list[nn.Module] = []
        sizes = [n_inputs, *(hidden or [32, 32]), n_outputs]
        for i in range(len(sizes) - 1):
            layers.append(nn.Linear(sizes[i], sizes[i + 1]))
            if i < len(sizes) - 2:
                layers.append(nn.Tanh())
        self.net = nn.Sequential(*layers)
        self.n_inputs = n_inputs

    def predict(self, x: Any) -> Any:
        """Forward pass on a tensor or list of floats."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed")
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        with torch.no_grad():
            return self.net(x)

    def fit(
        self,
        x_train: Any,
        y_train: Any,
        epochs: int = 200,
        lr: float = 1e-3,
    ) -> dict[str, float]:
        """Train on (x, y); returns final loss. Physics term can be added."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed")
        x = torch.tensor(x_train, dtype=torch.float32)
        y = torch.tensor(y_train, dtype=torch.float32).unsqueeze(-1)
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        loss_fn = torch.nn.MSELoss()
        final_loss = 0.0
        for _ in range(epochs):
            opt.zero_grad()
            pred = self.net(x)
            loss = loss_fn(pred, y)
            loss.backward()
            opt.step()
            final_loss = float(loss.item())
        return {"final_loss": final_loss, "epochs": epochs}


def status() -> dict[str, Any]:
    """Honest capability report for the API/UI."""
    return {
        "available": TORCH_AVAILABLE,
        "note": (
            "PINN surrogate scaffold ready"
            if TORCH_AVAILABLE
            else "PyTorch not installed — surrogate disabled (pip install torch)"
        ),
    }
