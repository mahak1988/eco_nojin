"""Adapters for external simulation libraries"""
from services.simulation.adapters.carbon_adapter import RothCAdapter
from services.simulation.adapters.crop_adapter import AquaCropAdapter
from services.simulation.adapters.erosion_adapter import (
    WaterErosionAdapter,
    WindErosionAdapter,
)
from services.simulation.adapters.hydrology_adapter import SWATPlusAdapter
from services.simulation.adapters.infiltration_adapter import InfiltrationAdapter
from services.simulation.adapters.multilayer_adapter import MultiLayerAdapter
from services.simulation.adapters.windbreak_adapter import WindbreakAdapter

__all__ = [
    "AquaCropAdapter",
    "InfiltrationAdapter",
    "MultiLayerAdapter",
    "RothCAdapter",
    "SWATPlusAdapter",
    "WaterErosionAdapter",
    "WindErosionAdapter",
    "WindbreakAdapter",
]
