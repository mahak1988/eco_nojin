"""Clock port.

Time-dependent scientific results are otherwise not reproducible or testable.
A calibration record stamped ``date.today()`` cannot be asserted against, a
model version cannot be dated deterministically, and a field trial window
cannot be tested without waiting for the calendar.

Real call sites this port replaces
----------------------------------
============================================  ==========================
Call site                                     Current call
============================================  ==========================
hydroma/calibration/calibrator.py:165         ``date.today()``
hydroma/calibration/validator.py:141          ``date.today()``
hydroma/calibration/version_manager.py:59     ``date.today()``
hydroma/biofertilizer/calibration.py:99       ``date.today()``
hydroma/biofertilizer/trials.py:85            ``date.today()``
hydroma/biofertilizer/services.py:288         ``date.today()``
hydroma/biofertilizer/services.py:352,395,    ``datetime.now()``
451,497
hydroma/biofertilizer/repositories.py:268     ``date.today()``
hydroma/biofertilizer/repositories.py:99,     ``datetime.now()``
194,584
hydroma/biofertilizer/calculator.py:682       ``datetime.now()``
============================================  ==========================

Note the two methods are not interchangeable and the port keeps them distinct:
``date.today()`` is a *local* calendar date and ``datetime.now()`` is a local
wall-clock timestamp. Collapsing them into one ``now()`` would change the
values written to the database, so :class:`Clock` exposes both.

``now()`` is naive local time, matching what the call sites used before.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, runtime_checkable

__all__ = ["Clock", "FixedClock", "SystemClock"]


@runtime_checkable
class Clock(Protocol):
    """Source of the current date and time."""

    def today(self) -> date:
        """Current local calendar date."""

    def now(self) -> datetime:
        """Current local wall-clock timestamp."""


class SystemClock:
    """Production clock. Delegates to the standard library.

    The default everywhere in the engine, so behaviour is unchanged: every
    value produced here equals the ``date.today()`` / ``datetime.now()`` call
    it replaced.
    """

    __slots__ = ()

    def today(self) -> date:
        return date.today()

    def now(self) -> datetime:
        return datetime.now()

    def __repr__(self) -> str:
        return "SystemClock()"


class FixedClock:
    """Test clock pinned to a single instant.

    Lets a calibration date or an application window be asserted exactly
    instead of compared against whatever day the suite happens to run on.
    """

    __slots__ = ("_instant",)

    def __init__(self, instant: datetime) -> None:
        self._instant = instant

    @classmethod
    def at(cls, year: int, month: int, day: int) -> FixedClock:
        """Pin to midnight on the given calendar date."""
        return cls(datetime(year, month, day))

    def today(self) -> date:
        return self._instant.date()

    def now(self) -> datetime:
        return self._instant

    def advance(self, **timedelta_kwargs: float) -> None:
        """Move the clock forward by a ``datetime.timedelta(**kwargs)``."""
        from datetime import timedelta

        self._instant += timedelta(**timedelta_kwargs)

    def __repr__(self) -> str:
        return f"FixedClock({self._instant.isoformat()!r})"
