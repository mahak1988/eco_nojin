"""
Hybrid ML Module for Eco Nojin
===============================

Exports:
- PINN models (HeatEquationPINN, RichardsEquationPINN)
- GP Surrogate models (GPSurrogateModel)
"""

from engine.hydroma.hybrid_ml.gp_surrogate import (
    ExactGPModel,
    GPConfig,
    GPSurrogateModel,
)
from engine.hydroma.hybrid_ml.pinn import (
    PINN,
    HeatEquationPINN,
    PINNConfig,
    PINNModel,
    RichardsEquationPINN,
)

__all__ = [
    "PINN",
    "ExactGPModel",
    "GPConfig",
    "GPSurrogateModel",
    "HeatEquationPINN",
    "PINNConfig",
    "PINNModel",
    "RichardsEquationPINN",
]
