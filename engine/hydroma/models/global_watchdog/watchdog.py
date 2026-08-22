"""
Hydroma Global Watchdog — Orchestrator
=======================================

Top-level integration of Köppen-Geiger classification and Water Bankruptcy Index.

Usage:
    from engine.hydroma.models.global_watchdog import GlobalWatchdog, WBIInputs

    watchdog = GlobalWatchdog()
    result = watchdog.analyze(
        region_name="Yemen_Sanaa",
        climate=(t_min, t_max, p),  # monthly arrays
        water_inputs=WBIInputs(...),
    )
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple
import numpy as np

from .koppen import KGCv5
from .wbi import WBIInputs, WBIv3


@dataclass
class RegionAnalysis:
    """Result of a region analysis."""
    region_name: str
    kgc: Dict[str, Any]
    wbi: Dict[str, Any]
    timestamp: str


class GlobalWatchdog:
    """
    Hydroma Global Watchdog.

    Combines Köppen-Geiger climate classification with Water Bankruptcy Index
    for comprehensive regional water security assessment.
    """

    VERSION = "1.0.0"
    DISCLAIMER = (
        "This analysis is a probabilistic scientific assessment based on "
        "peer-reviewed methodologies and publicly available data. It is NOT "
        "a deterministic prediction. Policy decisions must be validated by "
        "local authorities and consider socio-economic context."
    )

    def analyze(
        self,
        region_name: str,
        climate: Tuple[np.ndarray, np.ndarray, np.ndarray],
        water_inputs: WBIInputs,
    ) -> RegionAnalysis:
        """
        Analyze a region's climate and water security.

        Parameters
        ----------
        region_name : str
        climate : tuple of (t_min, t_max, p) monthly arrays
        water_inputs : WBIInputs

        Returns
        -------
        RegionAnalysis
        """
        from datetime import datetime, timezone

        t_min, t_max, p = climate
        kgc = KGCv5.classify(t_min, t_max, p)
        wbi = WBIv3.compute(water_inputs)

        return RegionAnalysis(
            region_name=region_name,
            kgc=kgc,
            wbi=wbi,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def analyze_many(
        self,
        regions: Dict[str, Tuple[Tuple[np.ndarray, np.ndarray, np.ndarray], WBIInputs]],
    ) -> Dict[str, RegionAnalysis]:
        """Analyze multiple regions in batch."""
        return {
            name: self.analyze(name, climate, water_inputs)
            for name, (climate, water_inputs) in regions.items()
        }

    def rank_regions(
        self,
        analyses: Dict[str, RegionAnalysis],
        by: str = "wbi",
        ascending: bool = False,
    ) -> list:
        """
        Rank regions by a metric (default: WBI, descending = most critical first).
        """
        items = list(analyses.items())
        if by == "wbi":
            items.sort(key=lambda x: x[1].wbi["wbi"], reverse=not ascending)
        elif by == "kgc":
            # Group order: E, B, A, D, C
            group_order = {"E": 0, "B": 1, "A": 2, "D": 3, "C": 4}
            items.sort(key=lambda x: group_order.get(x[1].kgc["group"], 5))
        return items
