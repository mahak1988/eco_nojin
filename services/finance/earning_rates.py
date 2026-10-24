"""Single source of truth for ECO earning and redemption rates.

Consolidated in phase 4 (S-MONEY). There were two rate tables with the same
economic values under different names:

* ``services/finance/wallet_service.py`` — 11 categories, ``Decimal``
* ``services/ecowallet/service.py`` — 6 categories, ``float``, and a comment
  saying it was "kept in sync with the router"

They were not in sync. ``soil_health``/``water_saving``/``carbon_credit`` were
the same values as ``soil_restoration``/``water_conservation``/
``carbon_verification`` under different names, so an event emitted under one
name was invisible to a system keyed on the other.

Both now read from this module. The legacy names remain as aliases so existing
clients keep working.
"""

from __future__ import annotations

from decimal import Decimal

__all__ = [
    "DAILY_EARN_CAP",
    "EARNING_RATES",
    "LEGACY_CATEGORY_ALIASES",
    "REDEMPTION_RATES",
    "resolve_category",
    "transfer_min_balance",
]

#: ECO per unit, by activity. Decimal, never float: ``Decimal(0.1)`` is
#: ``0.1000000000000000055...`` and the wallet column is ``Numeric(19, 4)``.
EARNING_RATES: dict[str, Decimal] = {
    "tree_planting": Decimal("50.0"),
    "soil_restoration": Decimal("30.0"),
    "water_conservation": Decimal("25.0"),
    "biodiversity": Decimal("40.0"),
    "cleanup": Decimal("15.0"),
    "regenerative_farming": Decimal("35.0"),
    "carbon_verification": Decimal("100.0"),
    "education": Decimal("10.0"),
    "community": Decimal("5.0"),
    "satellite_verification": Decimal("30.0"),
    "mrv_submission": Decimal("20.0"),
}

#: ECO spent, by benefit. Signs are implicit: these are costs.
REDEMPTION_RATES: dict[str, Decimal] = {
    "consultation": Decimal("20.0"),
    "satellite_report": Decimal("30.0"),
    "marketplace_discount": Decimal("10.0"),
    "training": Decimal("15.0"),
    "certification": Decimal("50.0"),
}

#: Legacy category names from ``services/ecowallet/service.py``, mapped to the
#: canonical name. Removing these would break existing clients, so they are
#: translated rather than dropped.
LEGACY_CATEGORY_ALIASES: dict[str, str] = {
    "soil_health": "soil_restoration",
    "water_saving": "water_conservation",
    "carbon_credit": "carbon_verification",
}

DAILY_EARN_CAP: Decimal = Decimal("200.0")
TRANSFER_MIN_BALANCE: Decimal = Decimal("10.0")


def transfer_min_balance() -> Decimal:
    return TRANSFER_MIN_BALANCE


def resolve_category(category: str) -> str:
    """Translate a possibly-legacy category name to its canonical form.

    Raises:
        ValueError: if the category is not a known earning category.
    """
    canonical = LEGACY_CATEGORY_ALIASES.get(category, category)
    if canonical not in EARNING_RATES:
        known = sorted(set(EARNING_RATES) | set(LEGACY_CATEGORY_ALIASES))
        raise ValueError(f"unknown earning category: {category!r}; known: {known}")
    return canonical
