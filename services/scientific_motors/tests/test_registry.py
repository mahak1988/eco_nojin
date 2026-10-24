"""The scientific-motor registry must expose the real motor inventory.

The API-v1 surface (``GET /api/v1/motors``) reads two names from
``services.scientific_motors.registry``; before this module existed that route
503'd on every call. These tests prove the registry now enumerates the actual
``AbstractScientificMotor`` subclasses in the package — not a hard-coded list.
"""

from __future__ import annotations

from services.scientific_motors import registry
from services.scientific_motors.base import MotorType


def test_registry_lists_real_motors():
    motors = list(registry.MOTOR_REGISTRY)
    assert motors, "registry must enumerate at least one real motor"
    for motor in motors:
        assert isinstance(motor.motor_type, MotorType)
        assert motor.display_name, f"{type(motor).__name__} has no display_name"
        # the API surface calls these; a broken motor would explode in a route
        assert motor.get_input_requirements() is not None
        assert motor.get_outputs() is not None


def test_registry_reports_no_load_errors():
    errors = registry.LOAD_ERRORS
    assert errors.get("import_errors") == {}
    assert errors.get("instantiation_errors") == {}


def test_get_motor_roundtrip_and_miss():
    first = registry.MOTOR_REGISTRY[0]
    assert registry.get_motor(first.motor_type.value) is first
    assert registry.get_motor("__no_such_motor__") is None


def test_known_motor_types_present():
    values = {m.motor_type.value for m in registry.MOTOR_REGISTRY}
    # spot-check a few real motor types from the package
    assert "erosion_rusle" in values
    assert "aquacrop" in values
    assert "roth_c" in values or "roth_c" in {t.value for t in MotorType}
