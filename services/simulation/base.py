"""Base classes for all simulators"""
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type
import time

from services.simulation.schemas import (
    SimulationContext, SimulationResult, SimulationStatus, SimulationType,
)

class BaseSimulator(ABC):
    """کلاس پایه برای تمام شبیه‌سازها - Adapter Pattern"""
    
    simulator_type: SimulationType = SimulationType.COMPREHENSIVE
    name: str = "Base"
    version: str = "1.0.0"
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    @abstractmethod
    async def validate_context(self, ctx: SimulationContext) -> List[str]:
        """اعتبارسنجی context - لیست خطاها را برمی‌گرداند"""
        pass
    
    @abstractmethod
    async def run(self, ctx: SimulationContext) -> SimulationResult:
        """اجرای شبیه‌سازی"""
        pass
    
    async def execute(self, ctx: SimulationContext) -> SimulationResult:
        """اجرای امن با handling خطا"""
        start = time.time()
        started_at = datetime.now(timezone.utc)
        sim_id = ctx.simulation_id or str(uuid.uuid4())
        
        errors = await self.validate_context(ctx)
        if errors:
            return SimulationResult(
                simulation_id=sim_id,
                simulation_type=self.simulator_type,
                status=SimulationStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=time.time() - start,
                error=f"Validation failed: {'; '.join(errors)}",
            )
        
        try:
            result = await self.run(ctx)
            result.duration_seconds = time.time() - start
            result.completed_at = datetime.now(timezone.utc)
            return result
        except Exception as e:
            return SimulationResult(
                simulation_id=sim_id,
                simulation_type=self.simulator_type,
                status=SimulationStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=time.time() - start,
                error=f"{type(e).__name__}: {str(e)}",
            )

class SimulatorRegistry:
    """رجیستری تمام شبیه‌سازها - Singleton Pattern"""
    _instance: Optional['SimulatorRegistry'] = None
    _simulators: Dict[SimulationType, Type[BaseSimulator]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, simulator_cls: Type[BaseSimulator]):
        """Decorator برای ثبت شبیه‌ساز"""
        cls._simulators[simulator_cls.simulator_type] = simulator_cls
        return simulator_cls
    
    def get(self, sim_type: SimulationType) -> Optional[BaseSimulator]:
        cls = self._simulators.get(sim_type)
        return cls() if cls else None
    
    def list_all(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": t.value,
                "name": cls.name,
                "version": cls.version,
            }
            for t, cls in self._simulators.items()
        ]
    