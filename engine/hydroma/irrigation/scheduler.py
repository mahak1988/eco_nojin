"""
Irrigation Scheduler
منبع: FAO-56 + Keller & Bliesner (1990)

FAO-56 (Allen et al., 1998) Annex 2, and Keller & Bliesner (1990):

    NIR = ETc - Pe          net irrigation requirement  [mm]
    GAR = NIR / Ea          gross application depth     [mm]
    I   = (TAW * p) / ETc   irrigation interval         [days]

``Ea`` is an application efficiency and ``p`` is the management-allowed
depletion. Both are FRACTIONS: Ea in (0, 1] and p in (0, 1]. A percentage
written where a fraction belongs is not a small error but a factor of 100 on
the schedule, so both bounds are enforced instead of merely documented.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class IrrigationEvent:
    date: str
    depth_mm: float
    method: str
    efficiency: float  # 0.0 to 1.0
    duration_hours: float


def calculate_interval(etc_mm_per_day: float, raw_mm: float, allowable_depletion: float) -> int:
    """محاسبه دور آبیاری (روز)

    I = (TAW * p) / ETc, where ``raw_mm`` is the total available water TAW in
    the root zone [mm] and ``allowable_depletion`` is p, the management-allowed
    depletion FRACTION.

    ETc <= 0 has no finite answer. At ETc = 0 the next application is
    arbitrarily far away, and a negative demand is not a quantity at all, so
    both are rejected rather than reported as a zero-day interval, which a
    scheduler driven by this number reads as "no irrigation needed".
    """
    if etc_mm_per_day <= 0:
        raise ValueError(
            f"Crop water demand ETc must be positive to define an interval (got {etc_mm_per_day})"
        )
    if raw_mm < 0:
        raise ValueError(f"Total available water TAW must be non-negative (got {raw_mm})")
    if not 0.0 < allowable_depletion <= 1.0:
        raise ValueError(
            "allowable_depletion is the management-allowed depletion FRACTION and must lie "
            f"in (0, 1] (got {allowable_depletion}); pass 0.55 for 55 %, not 55"
        )
    interval = (raw_mm * allowable_depletion) / etc_mm_per_day
    return max(1, round(interval))


def calculate_application_depth(
    etc_mm: float, efficiency: float, effective_rain_mm: float
) -> float:
    """محاسبه عمق آبیاری مورد نیاز

    GAR = (ETc - Pe) / Ea.

    Ea = 0 delivers no water to the root zone at all, so the required gross
    depth is unbounded, not zero: reporting 0.0 would tell a scheduler the
    field needs no water. Ea > 1 would have the field receive more water than
    the system delivers. A negative Pe is a corrupted rain reading, not a
    drought, and it would otherwise inflate the requirement without limit.
    """
    if not 0.0 < efficiency <= 1.0:
        raise ValueError(
            "Application efficiency Ea must lie in (0, 1] (got "
            f"{efficiency}); at Ea = 0 no water reaches the root zone, so the required "
            "gross depth is unbounded rather than zero"
        )
    if effective_rain_mm < 0:
        raise ValueError(f"Effective rainfall cannot be negative (got {effective_rain_mm} mm)")
    net_need = max(0, etc_mm - effective_rain_mm)
    return net_need / efficiency


def next_event(
    event_date: date | str,
    etc_mm: float,
    efficiency: float,
    effective_rain_mm: float = 0.0,
    method: str = "drip",
    application_rate_mm_per_hour: float = 20.0,
) -> IrrigationEvent:
    """The single application a scheduler falls due on ``event_date``.

    ``etc_mm`` is the demand since the last application, i.e. over one
    irrigation interval, not a daily rate. ``duration_hours`` is the pump
    runtime needed to place the gross depth at the system's application rate;
    the rate does not enter the FAO-56 depth calculation.
    """
    if application_rate_mm_per_hour <= 0:
        raise ValueError(
            f"Application rate must be positive to give a runtime (got {application_rate_mm_per_hour} mm/hr)"
        )
    day = event_date if isinstance(event_date, date) else date.fromisoformat(event_date)
    depth_mm = calculate_application_depth(etc_mm, efficiency, effective_rain_mm)
    return IrrigationEvent(
        date=day.isoformat(),
        depth_mm=depth_mm,
        method=method,
        efficiency=efficiency,
        duration_hours=depth_mm / application_rate_mm_per_hour,
    )


def build_schedule(
    start_date: date | str,
    season_days: int,
    etc_mm_per_day: float,
    raw_mm: float,
    allowable_depletion: float,
    effective_rain_mm: float = 0.0,
    efficiency: float = 0.8,
    method: str = "drip",
    application_rate_mm_per_hour: float = 20.0,
) -> list[IrrigationEvent]:
    """The season's applications, one every I days from ``start_date``.

    The interval and the depth are the only two numbers FAO-56 gives a
    scheduler; a schedule is those two applied to a calendar. Each application
    covers I days of demand, so its gross depth is (ETc * I - Pe) / Ea. A
    season shorter than one interval still gets one application, because the
    crop has to be watered at least once.
    """
    if season_days <= 0:
        raise ValueError(f"Season length must be positive (got {season_days} days)")
    if application_rate_mm_per_hour <= 0:
        raise ValueError(
            f"Application rate must be positive to give a runtime (got {application_rate_mm_per_hour} mm/hr)"
        )

    interval = calculate_interval(etc_mm_per_day, raw_mm, allowable_depletion)
    first = start_date if isinstance(start_date, date) else date.fromisoformat(start_date)
    demand_mm = etc_mm_per_day * interval
    depth_mm = calculate_application_depth(demand_mm, efficiency, effective_rain_mm)
    duration_hours = depth_mm / application_rate_mm_per_hour
    n_events = max(1, math.ceil(season_days / interval))

    return [
        IrrigationEvent(
            date=(first + timedelta(days=index * interval)).isoformat(),
            depth_mm=depth_mm,
            method=method,
            efficiency=efficiency,
            duration_hours=duration_hours,
        )
        for index in range(n_events)
    ]
