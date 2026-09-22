"""
Hybrid ML Module for Eco Nojin
===============================

Exports:
- PINN models (HeatEquationPINN, RichardsEquationPINN)
- GP Surrogate models (GPSurrogateModel)
"""

from engine.hydroma.hybrid_ml.pinn import (
    PINNConfig,
    PINN,
    PINNModel,
    HeatEquationPINN,
    RichardsEquationPINN,
)

from engine.hydroma.hybrid_ml.gp_surrogate import (
    GPConfig,
    ExactGPModel,
    GPSurrogateModel,
)

__all__ = [
    "PINNConfig",
    "PINN",
    "PINNModel",
    "HeatEquationPINN",
    "RichardsEquationPINN",
    "GPConfig",
    "ExactGPModel",
    "GPSurrogateModel",
]