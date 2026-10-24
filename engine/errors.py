#!/usr/bin/env python3
"""engine.errors
=============

Structured error contract for the HyDroMA processing engine, implementing
section 5.3 of the ECO-NOJIN Master Execution Specification
("قرارداد خطای ساختاریافته").

Exports:

* :class:`HydromaError` -- an exception carrying a machine-readable
  ``error_code``, a human-readable message, and an optional structured
  ``context`` payload;
* ``ERROR_CODES`` -- the canonical ``error_code`` -> Persian description
  table, copied verbatim from the specification.

Coexistence with the gateway
----------------------------
The Engine Gateway already exposes its own error value object,
:class:`engine.gateway.GatewayError`. That class stays untouched and this
module coexists with it: nothing here changes, re-exports, or migrates the
gateway's existing contract. Migrating ``GatewayError`` (or any other
caller) to ``HydromaError`` is a Wave 3 decision that is deliberately not
taken now.

This module is definitional only: it never raises.
"""

from __future__ import annotations

__all__ = ["HydromaError", "ERROR_CODES"]


class HydromaError(Exception):
    """Structured error defined by the spec section 5.3 error contract.

    Attributes:
        error_code: Machine-readable code, one of the :data:`ERROR_CODES`
            keys (e.g. ``"INPUT_INVALID"``).
        message: Human-readable description passed to ``Exception.__init__``.
        context: Optional structured payload (variable names, bounds,
            model ids, ...). Defaults to a fresh empty dict per instance.
    """

    def __init__(
        self, error_code: str, message: str, context: dict | None = None
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.context: dict = context or {}

    def __repr__(self) -> str:
        return f"HydromaError(error_code={self.error_code!r}, message={self.args[0]!r})"


# Canonical error code -> Persian description table (spec section 5.3).
ERROR_CODES: dict[str, str] = {
    "INPUT_INVALID": "ورودی نامعتبر",
    "UNIT_INCOMPATIBLE": "واحد ناسازگار",
    "MODEL_UNKNOWN": "مدل ناشناخته",
    "MODEL_VERSION_INVALID": "نسخه نامعتبر",
    "OUT_OF_DOMAIN": "خارج از دامنه کاربرد",
    "DATA_INSUFFICIENT": "داده ناکافی",
    "NUMERICAL_ERROR": "خطای عددی",
    "EXECUTION_FAILED": "خطای اجرای مدل",
    "PERSISTENCE_ERROR": "خطای ذخیره‌سازی",
    "UNCERTAINTY_NOT_ESTIMATED": "عدم‌قطعیت محاسبه‌نشده",
    "VALIDATION_FAILED": "اعتبارسنجی ناموفق",
    "NOT_IMPLEMENTED": "پیاده‌سازی نده",
    "ARCHITECTURE_VIOLATION": "نقض معماری"
}
