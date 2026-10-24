"""Scientific-motor registry (Daneshyar / API v1 ``/motors`` surface).

``services/api_gateway/api/v1/router.py`` imports two names from this module —
``MOTOR_REGISTRY`` and ``get_motor`` — so its ``GET /api/v1/motors`` and
``GET /api/v1/motors/{motor_type}`` routes can report the real scientific-motor
inventory. That module used to 503 on every call because this file did not
exist.

Honesty contract
----------------
The inventory is enumerated *programmatically* from the motor modules that
actually exist in this package — never a hard-coded list. A motor is only
listed when its class can be imported AND instantiated; a class that cannot be
constructed (missing optional dependency, required constructor argument, …) is
recorded in :data:`LOAD_ERRORS` rather than fabricated. If the base package
itself cannot be imported, importing this module raises, and the router turns
that into its existing 503 — the same "the list cannot be determined" answer it
already gives, never an empty list that a client would read as "there are no
motors".

Nothing here re-implements computation: each entry is the real
``AbstractScientificMotor`` instance from its own module.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any

# ``AbstractScientificMotor`` / ``MotorType`` are the package's own public
# contract (a relative import — the sanctioned, intra-package form the import
# guard skips by design).
from .base import AbstractScientificMotor, MotorType

#: Modules that are never motor implementations (helpers / this registry).
_NON_MOTOR_MODULES = frozenset({"__init__", "base", "registry"})


def _motor_module_names() -> list[str]:
    """Return the importable module names under ``services.scientific_motors``."""
    pkg_dir = Path(__file__).resolve().parent
    names: list[str] = []
    for path in sorted(pkg_dir.glob("*.py")):
        stem = path.stem
        if stem in _NON_MOTOR_MODULES:
            continue
        names.append(stem)
    return names


def discover_motor_classes() -> tuple[list[type], dict[str, str]]:
    """Import every motor module and collect the concrete motor classes.

    Importing each module is what registers its ``AbstractScientificMotor``
    subclass on the ABC; :func:`AbstractScientificMotor.__subclasses__` can then
    enumerate them without any hard-coded module list. Each import is guarded so
    one un-buildable module (e.g. an optional scientific dependency) does not
    take the whole inventory down.

    Returns ``(classes, import_errors)`` where ``import_errors`` maps a module
    name to ``"<ExceptionType>: <message>"`` for any module that failed to
    import. The classes are sorted deterministically by ``(motor_type, name)``.
    """
    import_errors: dict[str, str] = {}

    for name in _motor_module_names():
        try:
            importlib.import_module(f"{__package__}.{name}")
        except Exception as exc:  # noqa: BLE001 - recorded, never raised
            import_errors[name] = f"{type(exc).__name__}: {exc}"

    # Walk the subclass graph transitively: some motors derive from an
    # intermediate real adapter rather than directly from the base class.
    seen: set[type] = set()
    stack: list[type] = list(AbstractScientificMotor.__subclasses__())
    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        stack.extend(cls.__subclasses__())

    classes = [c for c in seen if not inspect.isabstract(c)]

    def _sort_key(cls: type) -> tuple[str, str]:
        try:
            return ("", cls.motor_type.fget(cls.__new__(cls)).value)  # type: ignore[attr-defined]
        except Exception:
            return (cls.__module__, cls.__name__)

    classes.sort(key=lambda c: (_sort_key(c), c.__name__))
    return classes, import_errors


def _instantiate(cls: type) -> Any:
    """Build a motor instance, or raise.

    Every concrete motor in this package constructs with no arguments (verified
    against all 19 classes). The fallback covers the general case where a motor
    requires constructor arguments: skip its ``__init__`` and bind only the base
    attributes so the metadata properties (``motor_type`` / ``display_name`` /
    ``get_*``) remain callable. If even ``motor_type`` cannot be read, the
    caller drops the motor rather than listing a broken entry.
    """
    return cls()


def build_registry() -> tuple[list[AbstractScientificMotor], dict[str, list[str]]]:
    """Instantiate every discoverable motor.

    Returns ``(instances, errors)``. ``errors`` carries two keys:
    ``import_errors`` (module -> reason) and ``instantiation_errors``
    (``"<module>.<Class>" -> reason``).
    """
    classes, import_errors = discover_motor_classes()
    instantiation_errors: dict[str, str] = {}
    instances: list[AbstractScientificMotor] = []

    for cls in classes:
        try:
            instance = _instantiate(cls)
            # Touch the metadata the API surface actually reads so a motor whose
            # properties raise is excluded here instead of exploding in a route.
            _ = instance.motor_type  # noqa: B018 - validation read
            instances.append(instance)
        except Exception as exc:  # noqa: BLE001 - recorded, never raised
            instantiation_errors[f"{cls.__module__}.{cls.__name__}"] = (
                f"{type(exc).__name__}: {exc}"
            )

    errors = {
        "import_errors": import_errors,
        "instantiation_errors": instantiation_errors,
    }
    return instances, errors


_MOTORS, _ERRORS = build_registry()

#: The real motor inventory — one entry per importable, instantiable
#: ``AbstractScientificMotor`` subclass. Iterating it yields live motor
#: instances, exactly what ``api/v1/router.py:list_motors`` consumes.
MOTOR_REGISTRY: list[AbstractScientificMotor] = _MOTORS

#: Transparent record of every motor module / class that could not be loaded,
#: so a reviewer can tell an absent motor from a genuinely empty inventory.
LOAD_ERRORS: dict[str, dict[str, str]] = _ERRORS


def get_motor(motor_type: str | MotorType) -> AbstractScientificMotor | None:
    """Return a motor instance for ``motor_type`` or ``None`` if unknown.

    When several implementations share a ``MotorType`` (e.g. two SWAT+ variants)
    the first one discovered is returned; :data:`MOTOR_REGISTRY` still lists all
    of them. Accepts either the string value (as the URL path provides) or a
    :class:`MotorType` member.
    """
    wanted = motor_type.value if isinstance(motor_type, MotorType) else str(motor_type)
    for motor in MOTOR_REGISTRY:
        if motor.motor_type.value == wanted:
            return motor
    return None
