"""Structured error contract test suite (spec section 5.3).

Covers ``engine/errors.py``:

* ``ERROR_CODES`` is exactly the canonical code set from spec section 5.3
  -- every code present, and no code beyond it. The spec table enumerates
  13 codes; the test names follow the task wording that expected 14.
* ``HydromaError`` carries ``error_code`` / ``context`` and surfaces the
  message through ``str()`` and the ``Exception`` interface;
* the context payload defaults to a fresh empty dict per instance, so two
  instances never share mutable state;
* every ``ERROR_CODES`` entry maps to a non-empty Persian description.

The gateway's existing ``GatewayError`` value object is not touched by
this contract.
"""

from __future__ import annotations

from engine.errors import ERROR_CODES, HydromaError

# Canonical code set, copied from spec section 5.3.
EXPECTED_ERROR_CODES = {
    "ARCHITECTURE_VIOLATION",
    "DATA_INSUFFICIENT",
    "EXECUTION_FAILED",
    "INPUT_INVALID",
    "MODEL_UNKNOWN",
    "MODEL_VERSION_INVALID",
    "NOT_IMPLEMENTED",
    "NUMERICAL_ERROR",
    "OUT_OF_DOMAIN",
    "PERSISTENCE_ERROR",
    "UNCERTAINTY_NOT_ESTIMATED",
    "UNIT_INCOMPATIBLE",
    "VALIDATION_FAILED",
}


def test_all_14_codes_present():
    assert set(ERROR_CODES) == EXPECTED_ERROR_CODES
    assert len(ERROR_CODES) == len(EXPECTED_ERROR_CODES)


def test_error_carries_code_and_context():
    err = HydromaError("INPUT_INVALID", "bad input", {"field": "tmax"})

    assert err.error_code == "INPUT_INVALID"
    assert err.context == {"field": "tmax"}
    assert "bad input" in str(err)
    assert isinstance(err, Exception)
    assert "INPUT_INVALID" in repr(err)


def test_context_defaults_empty():
    err = HydromaError("MODEL_UNKNOWN", "x")

    assert err.context == {}

    other = HydromaError("MODEL_UNKNOWN", "y")
    err.context["field"] = "tmax"
    assert other.context == {}


def test_known_code_description_lookup():
    for code, description in ERROR_CODES.items():
        assert isinstance(description, str)
        assert description.strip()
        assert isinstance(code, str)
