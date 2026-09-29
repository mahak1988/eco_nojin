"""Canonical status envelope — standard S-HONEST.

The rule this module exists to enforce:

    A path that cannot produce the full result it advertises must say so.

The failure mode it replaces is the most dangerous class of defect in this
codebase: silent success. Concrete instances, all of which returned
success-shaped data while doing nothing or failing:

* ``services/backup/service.py`` wrote a three-line SQL comment and reported
  ``verification_status="passed"``; both restore paths were ``pass`` while
  ``run_restore`` still set ``COMPLETED`` and ``restored_objects=1``.
* ``services/marketplace/traceability.py:119`` computed a SHA-256 digest,
  discarded it, and returned ``True``.
* ``services/ledger/service.py`` returned ``{"status": "memory_only"}`` for a
  lost accounting write, and ``Decimal("0")`` for a failed balance query.
* ``services/ecosystem/trust_score.py`` returned ``True`` from ``record_event``
  after discarding the event, and gave every user a score of exactly 0.5.
* ``services/ai/nlg.py:140-148`` fabricated an evidence record and echoed the
  user's own question back as the answer.
* ``services/land/land_profile.py:57-78`` returned an elevation range and
  ``dem_source="SRTM"`` for terrain it invented.
* ``services/alerting/service.py:289-300`` had ``evaluate_rules`` return
  ``{"fired": 0, "resolved": 0}`` from a ``# This is a placeholder``.

Usage
-----
Wrap anything whose provenance is not simply "computed correctly":

    return Tainted(
        data=rows,
        status=Status.DEGRADED,
        reason="pg_dump absent; substituted SCAN-CN surrogate",
        fallback_used="scs_curve_number",
        provenance=Provenance(source="derived", engine="swat_plus.py:88", synthetic=False),
    )

``Tainted.ok`` is a convenience for "status is OK". A result that claims ``OK``
while ``provenance.synthetic`` is true is a contract violation, and
:func:`assert_honest` raises on it — that is the mechanical half of the gate
that phase 3 wires into CI.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any

__all__ = [
    "Provenance",
    "Status",
    "Tainted",
    "assert_honest",
    "degraded",
    "not_implemented",
    "ok",
    "unavailable",
]


class Status(enum.StrEnum):
    """How much of the promised result is actually present."""

    OK = "ok"
    """Data is complete and real."""

    DEGRADED = "degraded"
    """Real data, but a named substitute was used for part of the computation."""

    STALE = "stale"
    """Data is real but older than the caller can accept."""

    UNAVAILABLE = "unavailable"
    """A required external dependency is unreachable."""

    NOT_IMPLEMENTED = "not_implemented"
    """The capability does not exist. Must be stated, never hidden."""

    # Deliberately absent: FAILED. A failure is an exception or an explicit
    # error response, not a status. Encoding failure as data is what let
    # `{"status": "memory_only"}` look like a result.


@dataclass(frozen=True)
class Provenance:
    """Where a value came from.

    ``synthetic=True`` means the number was invented. It is the single most
    important field in this module: the difference between a real
    ``land_profile`` and a fabricated one is entirely this flag.
    """

    source: str
    """``computed``, ``derived``, ``measured``, ``external``, ``synthetic``..."""

    engine: str | None = None
    """``path.py:line`` or an external engine name, so the value is traceable."""

    synthetic: bool = False
    """True when the value was fabricated rather than computed or measured."""

    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "engine": self.engine,
            "synthetic": self.synthetic,
            "detail": self.detail,
        }


#: Provenance for a value produced by real computation from real inputs.
COMPUTED = Provenance(source="computed", synthetic=False)
#: Provenance for a value this service invented.
SYNTHETIC = Provenance(source="synthetic", synthetic=True)


@dataclass(frozen=True)
class Tainted[T]:
    """A value plus the honest description of how it was obtained."""

    data: T
    status: Status = Status.OK
    reason: str | None = None
    fallback_used: str | None = None
    provenance: Provenance | None = None

    def __post_init__(self) -> None:
        if self.status is Status.OK and (self.reason or self.fallback_used):
            raise ValueError(
                "Status.OK cannot carry a reason or fallback_used; that would hide a "
                "degradation. Use Status.DEGRADED."
            )
        if self.status is not Status.OK and not self.reason:
            raise ValueError(
                f"status={self.status.value} requires a non-empty reason stating what was "
                "not done, so the caller is not misled into reading data as complete"
            )
        if self.status is Status.OK and self.provenance is not None and self.provenance.synthetic:
            raise ValueError(
                "synthetic data cannot be reported as Status.OK; use Status.DEGRADED and "
                "describe the substitution"
            )

    @property
    def ok(self) -> bool:
        return self.status is Status.OK

    def unwrap(self) -> T:
        """Return the value, or raise if it is not a complete result.

        Prefer this at call sites that cannot tolerate degradation, so a
        degraded result becomes a 503 rather than a plausible wrong number.
        """
        if self.status is not Status.OK:
            raise IncompleteResultError(self)
        return self.data

    def as_dict(self) -> dict[str, Any]:
        return {
            "data": self.data,
            "status": self.status.value,
            "reason": self.reason,
            "fallback_used": self.fallback_used,
            "provenance": self.provenance.as_dict() if self.provenance else None,
        }


class IncompleteResultError(RuntimeError):
    """Raised by :meth:`Tainted.unwrap` for a non-OK result."""

    def __init__(self, tainted: Tainted[Any]) -> None:
        self.status = tainted.status
        self.reason = tainted.reason
        self.fallback_used = tainted.fallback_used
        super().__init__(f"{tainted.status.value}: {tainted.reason}")


def assert_honest(value: Any) -> None:
    """Raise if a dict claims success while carrying fabricated content.

    The mechanical check behind the S-HONEST gate. Intended for response
    builders: it inspects the serialised shape rather than the call graph, so
    it catches a hardcoded return value that no refactor would flag.
    """
    if isinstance(value, Tainted):
        if value.provenance is not None and value.provenance.synthetic and value.ok:
            raise ValueError("synthetic data reported as ok")
        return

    if isinstance(value, dict):
        for key in ("status", "verification_status"):
            declared = value.get(key)
            if isinstance(declared, str) and declared in ("passed", "ok", "completed", "COMPLETED"):
                provenance = value.get("provenance") or value.get("data_provenance")
                if isinstance(provenance, dict) and provenance.get("synthetic") is True:
                    raise ValueError(f"{key}={declared!r} contradicts synthetic provenance")
        for nested in value.values():
            assert_honest(nested)
        return

    if isinstance(value, (list, tuple)):
        for item in value:
            assert_honest(item)


def ok[T](data: T, *, provenance: Provenance | None = None) -> Tainted[T]:
    """A complete, real result."""
    return Tainted(data=data, status=Status.OK, provenance=provenance)


def degraded[T](
    data: T,
    reason: str,
    *,
    fallback_used: str | None = None,
    provenance: Provenance | None = None,
) -> Tainted[T]:
    """Real data, computed with a named substitute."""
    return Tainted(
        data=data,
        status=Status.DEGRADED,
        reason=reason,
        fallback_used=fallback_used,
        provenance=provenance,
    )


def unavailable[T](data: T | None, reason: str) -> Tainted[T | None]:
    """A required external dependency is unreachable."""
    return Tainted(data=data, status=Status.UNAVAILABLE, reason=reason)


def not_implemented(reason: str) -> Tainted[Any]:
    """The capability does not exist.

    Preferred over returning a plausible default: a caller that needs the real
    thing gets an error, and one that does not can branch on the status.
    """
    return Tainted(data=None, status=Status.NOT_IMPLEMENTED, reason=reason)
