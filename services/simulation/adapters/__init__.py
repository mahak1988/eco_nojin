"""Adapters for external simulation libraries"""
from services.simulation.adapters.crop_adapter import AquaCropAdapter
from services.simulation.adapters.carbon_adapter import RothCAdapter
from services.simulation.adapters.hydrology_adapter import SWATPlusAdapter
from services.simulation.adapters.erosion_adapter import (
    WindErosionAdapter, WaterErosionAdapter,
)
from services.simulation.adapters.infiltration_adapter import InfiltrationAdapter
from services.simulation.adapters.windbreak_adapter import WindbreakAdapter
from services.simulation.adapters.multilayer_adapter import MultiLayerAdapter

__all__ = [
    "AquaCropAdapter", "RothCAdapter", "SWATPlusAdapter",
    "WindErosionAdapter", "WaterErosionAdapter",
    "InfiltrationAdapter", "WindbreakAdapter", "MultiLayerAdapter",
]
    