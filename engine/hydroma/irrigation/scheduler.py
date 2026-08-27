"""
Irrigation Scheduler
منبع: FAO-56 + Keller & Bliesner (1990)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IrrigationEvent:
    date: str
    depth_mm: float
    method: str
    efficiency: float  # 0.0 to 1.0
    duration_hours: float

def calculate_interval(etc_mm_per_day: float, raw_mm: float, allowable_depletion: float) -> int:
    """محاسبه دور آبیاری (روز)"""
    if etc_mm_per_day <= 0:
        return 0
    interval = (raw_mm * allowable_depletion) / etc_mm_per_day
    return max(1, int(round(interval)))

def calculate_application_depth(etc_mm: float, efficiency: float, effective_rain_mm: float) -> float:
    """محاسبه عمق آبیاری مورد نیاز"""
    net_need = max(0, etc_mm - effective_rain_mm)
    return net_need / efficiency if efficiency > 0 else 0.0
