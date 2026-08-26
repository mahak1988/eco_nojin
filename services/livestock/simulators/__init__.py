from services.livestock.simulators.base import BaseLivestockSimulator
from services.livestock.simulators.cattle import CattleSimulator
from services.livestock.simulators.sheep import SheepSimulator
from services.livestock.simulators.goat import GoatSimulator
from services.livestock.simulators.poultry import PoultrySimulator

SIMULATOR_REGISTRY = {
    "cattle": CattleSimulator,
    "sheep": SheepSimulator,
    "goat": GoatSimulator,
    "poultry": PoultrySimulator,
}

__all__ = [
    "BaseLivestockSimulator",
    "CattleSimulator", "SheepSimulator", "GoatSimulator", "PoultrySimulator",
    "SIMULATOR_REGISTRY",
]
    