"""
Hydroma Nojin - Core Engine Integration Layer

This module bridges scientific motors with the core engine in engine/hydroma/.
Ensures no logic duplication and unified scientific computations.
"""
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "engine"))

try:
    from hydroma.carbon.calculator import CarbonCalculator
    from hydroma.simulation.runners.rothc_runner import RothCRunner
    from hydroma.blockchain.carbon_registry import CarbonRegistry
    from hydroma.mrv.metrics import MRVMetrics
    
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Core engine not available: {e}")
    CORE_AVAILABLE = False


class CoreEngineWrapper:
    """
    Wrapper for Hydroma core engine.
    
    Provides unified interface for scientific motors to use core logic.
    """

    def __init__(self):
        if not CORE_AVAILABLE:
            raise RuntimeError("Core engine not available. Check imports.")
        
        self.carbon_calc = CarbonCalculator()
        self.rothc = RothCRunner()
        self.carbon_registry = CarbonRegistry()
        self.mrv = MRVMetrics()

    def calculate_carbon_sequestration(
        self,
        initial_soc: float,
        clay_fraction: float,
        method: str,
        years: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Calculate carbon sequestration using core engine."""
        return self.carbon_calc.calculate(
            initial_soc=initial_soc,
            clay=clay_fraction,
            method=method,
            years=years,
            **kwargs
        )

    def run_rothc_simulation(
        self,
        initial_soc: float,
        clay: float,
        c_input: float,
        years: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Run RothC simulation."""
        return self.rothc.run(
            initial_soc=initial_soc,
            clay=clay,
            c_input=c_input,
            years=years,
            **kwargs
        )

    def register_carbon_credits(
        self,
        credits_tCO2e: float,
        standard: str,
        project_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Register carbon credits on blockchain."""
        return self.carbon_registry.register(
            credits=credits_tCO2e,
            standard=standard,
            project_id=project_id,
            **kwargs
        )

    def generate_mrv_report(
        self,
        project_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate MRV report."""
        return self.mrv.generate_report(
            data=project_data,
            **kwargs
        )


# Singleton instance
core_wrapper: Optional[CoreEngineWrapper] = None

def get_core_engine() -> CoreEngineWrapper:
    """Get core engine wrapper (singleton)."""
    global core_wrapper
    if core_wrapper is None:
        core_wrapper = CoreEngineWrapper()
    return core_wrapper