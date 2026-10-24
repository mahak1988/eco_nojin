"""Unit-scaling machinery for the Engine Gateway (A-1 step 4).

The gateway's only honest unit handling is multiplicative ``si_equivalent``
scaling applied to *scalar* inputs. That arithmetic — the ``scaled = value *
si_equivalent`` rule with the non-finite rejection — lives here so every
``unit`` concern is in one module, and ``input_validator._normalize_inputs``
delegates the scalar branch to :func:`scale_scalar_to_si`. The behaviour is
byte-identical to the arithmetic the gateway has always owned.

The pint-based audit (``engine.gateway.pint_audit``) is surfaced through
:func:`audit_input_units` for later wiring. It RECORDS problems and never
rescales (mirroring the brake-2 constraint recorded on that module), so calling
it changes no computed result and nothing in the normalize path depends on it.
"""

from __future__ import annotations

import math
from typing import Any

from engine.gateway.contracts import UnitSpec


def scale_scalar_to_si(name: str, value: float, unit_spec: UnitSpec) -> float:
    """Multiply a scalar input by its declared ``si_equivalent`` factor.

    A verbatim continuation of the multiplicative path the gateway has always
    owned: a non-finite product is rejected here rather than propagating
    NaN/inf into a downstream computation.
    """
    scaled = value * unit_spec.si_equivalent
    if not math.isfinite(scaled):
        raise ValueError(
            f"input '{name}' must be a finite number, "
            f"got {value!r} (unit scale {unit_spec.si_equivalent!r})"
        )
    return scaled


def audit_input_units(input_units: dict[str, UnitSpec]) -> list[str]:
    """One problem string per unparseable declared unit, via ``pint_audit``.

    Records problems WITHOUT rescaling: the ``si_equivalent`` path this module
    owns is untouched, so calling this helper changes no computed result.
    Imported lazily so a gateway that never audits never loads ``pint``.
    """
    from engine.gateway.pint_audit import audit as _audit

    specs: dict[str, Any] = {name: spec.unit for name, spec in input_units.items()}
    return _audit(specs)


__all__: list[str] = []
