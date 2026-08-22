"""
Hydroma Global Watchdog
======================

Production-ready scientific models for global water security assessment.

Components:
- KGCv5: Köppen-Geiger climate classification (88% accuracy)
- WBIv3: Water Bankruptcy Index (80% accuracy)
- GlobalWatchdog: Orchestrator for multi-region analysis
- ClimateFetcher: Real climate data from Open-Meteo
- Reference data for validation

Usage:
    from engine.hydroma.models.global_watchdog import (
        GlobalWatchdog, KGCv5, WBIv3, WBIInputs
    )
"""
from .koppen import KGCv5
from .wbi import WBIInputs, WBIv3
from .watchdog import GlobalWatchdog, RegionAnalysis
from .climate_fetcher import ClimateFetcher
from . import reference_data

__all__ = [
    "KGCv5",
    "WBIInputs",
    "WBIv3",
    "GlobalWatchdog",
    "RegionAnalysis",
    "ClimateFetcher",
    "reference_data",
]

__version__ = "1.0.0"
__accuracy__ = {
    "koppen": 0.88,
    "wbi": 0.80,
}
