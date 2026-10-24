from services.livestock.simulators.base import BaseLivestockSimulator
from services.livestock.simulators.cattle import CattleSimulator
from services.livestock.simulators.goat import GoatSimulator
from services.livestock.simulators.poultry import PoultrySimulator
from services.livestock.simulators.sheep import SheepSimulator

SIMULATOR_REGISTRY = {
    "cattle": CattleSimulator,
    "sheep": SheepSimulator,
    "goat": GoatSimulator,
    "poultry": PoultrySimulator,
}

__all__ = [
    "SIMULATOR_REGISTRY",
    "BaseLivestockSimulator",
    "CattleSimulator",
    "GoatSimulator",
    "PoultrySimulator",
    "SheepSimulator",
]
