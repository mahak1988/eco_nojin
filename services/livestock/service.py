"""LivestockService - لایه کسب‌وکار"""
from services.livestock.schemas import (
    LivestockSimulationRequest, LivestockSimulationResult, AnimalType,
)
from services.livestock.simulators import SIMULATOR_REGISTRY

class LivestockService:
    def __init__(self, db=None):
        self.db = db
    
    def simulate(self, request: LivestockSimulationRequest) -> LivestockSimulationResult:
        simulator_cls = SIMULATOR_REGISTRY.get(request.herd.animal_type.value)
        if not simulator_cls:
            raise ValueError(f"Unknown animal type: {request.herd.animal_type}")
        
        simulator = simulator_cls()
        return simulator.simulate(request)
    
    def list_animal_types(self):
        return [{"type": t, "simulator": cls.name} for t, cls in SIMULATOR_REGISTRY.items()]
    
    def compare_scenarios(self, requests):
        """مقایسه چند سناریو"""
        return [self.simulate(req) for req in requests]
    