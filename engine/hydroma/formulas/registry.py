"""Formula registry: one record per physical quantity, with its proof attached.

Four rules, enforced here rather than by convention:

1. A record without ``parity_tests`` cannot be registered (``FormulaRecord``).
2. A record cannot claim ``verified`` without ``reference_values`` -- agreement
   with another implementation of the same formula is a closed loop and proves
   nothing, so the check must be against a published number.
3. ``status="divergent"`` is refused for any quantity listed in
   ``REQUEST_PATH_FORMULAS``. A formula that two backends compute differently is
   not usable where a client will see the answer.
4. Registering the same quantity twice is an error unless ``replace=True`` is
   passed explicitly, so a second implementation cannot quietly become the
   canonical one.

These rules are what stopped NDVI from having five independent
implementations, Penman-Monteith from disagreeing with itself by 36%, and the
Python fallback of ``penman_monteith_et0`` from silently swapping wind speed
for solar radiation.
"""

from __future__ import annotations

from .records import FormulaRecord

_REGISTRY: dict[str, FormulaRecord] = {}

#: Quantities whose result reaches a client. A divergent value here is a wrong
#: answer delivered with a 200, so registration is refused.
REQUEST_PATH_FORMULAS = frozenset(
    {
        "et0_reference",
        "ndvi",
        "evi",
        "savi",
        "ndwi",
        "nbr",
        "muskingum_cunge_routing",
        "richards_1d",
        "saint_venant_1d",
        "fao56_dual_kc",
        "rusle_soil_loss",
        "van_genuchten_theta",
        "rothc_moisture_modifier",
        "hargreaves_et0",
    }
)


class DuplicateFormulaError(ValueError):
    """Raised when a quantity is registered twice without ``replace=True``."""


class DivergentOnRequestPathError(ValueError):
    """Raised when a divergent formula would be served to a client."""


def register(record: FormulaRecord, *, replace: bool = False) -> FormulaRecord:
    """Register ``record``, enforcing the registration rules.

    Registration is documentation, so a ``divergent`` record is allowed: hiding a
    known conflict is what makes it dangerous. The rule that a divergent formula
    must not be *served* is enforced by :func:`require_servable`, which the
    dispatch layer calls.
    """
    if record.quantity in _REGISTRY and not replace:
        existing = _REGISTRY[record.quantity]
        raise DuplicateFormulaError(
            f"{record.quantity} is already registered (canonical={existing.canonical}, "
            f"status={existing.status}). A quantity has exactly one canonical "
            f"implementation; pass replace=True only when you are deliberately "
            f"changing which module owns it."
        )

    _REGISTRY[record.quantity] = record
    return record


def require_servable(quantity: str) -> FormulaRecord:
    """Return the record, refusing if it would put a known conflict on a client.

    This is the rule that actually protects a caller. Registering a divergent
    formula is how the conflict becomes visible; this is what stops the
    dispatcher from selecting it.
    """
    record = _REGISTRY.get(quantity)
    if record is None:
        raise KeyError(f"{quantity} is not a registered formula")
    if record.status == "divergent" and quantity in REQUEST_PATH_FORMULAS:
        raise DivergentOnRequestPathError(
            f"{quantity} is divergent and is served to a client. Reconcile the "
            f"backends before routing traffic to it. Recorded divergence: {record.notes}"
        )
    return record


def unservable_on_request_path() -> dict[str, FormulaRecord]:
    """Divergent quantities that a client would see -- the outstanding work list."""
    return {
        q: r for q, r in _REGISTRY.items() if r.status == "divergent" and q in REQUEST_PATH_FORMULAS
    }


def get(quantity: str) -> FormulaRecord | None:
    return _REGISTRY.get(quantity)


def all_records() -> dict[str, FormulaRecord]:
    return dict(_REGISTRY)


def verified() -> dict[str, FormulaRecord]:
    return {k: v for k, v in _REGISTRY.items() if v.is_verified}


def divergent() -> dict[str, FormulaRecord]:
    return {k: v for k, v in _REGISTRY.items() if v.status == "divergent"}


def on_request_path(quantity: str) -> bool:
    return quantity in REQUEST_PATH_FORMULAS


def summary() -> dict[str, int]:
    counts = {
        "total": len(_REGISTRY),
        "verified": sum(1 for r in _REGISTRY.values() if r.is_verified),
        "divergent": sum(1 for r in _REGISTRY.values() if r.status == "divergent"),
        "stub": sum(1 for r in _REGISTRY.values() if r.status == "stub"),
    }
    for origin in ("standard", "novel", "composite"):
        counts[f"by_{origin}"] = sum(1 for r in _REGISTRY.values() if r.provenance == origin)
    return counts


def novel() -> dict[str, FormulaRecord]:
    """Formulas that are this project's own contributions.

    These are not expected to have published standards. They are expected to
    have a written research definition and to clear the same internal bar every
    other formula does.
    """
    return {k: r for k, r in _REGISTRY.items() if r.provenance == "novel"}


def composite() -> dict[str, FormulaRecord]:
    """Formulas assembled here from published factors, where the product is ours."""
    return {k: r for k, r in _REGISTRY.items() if r.provenance == "composite"}


def research_definition(quantity: str) -> str | None:
    """The written definition backing a novel or composite formula."""
    from .research import DEFINITIONS

    return DEFINITIONS.get(quantity)


def _load_default_records() -> None:
    from . import catalog

    for record in catalog.RECORDS:
        register(record, replace=True)


_load_default_records()
