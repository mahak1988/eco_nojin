"""Canonical money and quantity handling — standard S-MONEY.

The rule this module exists to enforce:

    Money is ``Decimal``, carries an ISO 4217 code, and has exactly one sign
    convention across the whole codebase.

The failure mode it replaces: four ``LedgerService`` implementations with three
mutually contradictory sign conventions, plus ``float`` in the wallet path, so
reconciliation compared a balance against its own negation and flagged every
account as discrepant.

Sign convention
---------------
**Credit is positive, debit is negative.**

This is the convention already implemented and documented in
``services/finance/ledger_service.py::get_account_balance``, which is the
designated source of truth under the integration plan. The two others are
wrong, not merely different:

* ``services/finance/wallet_service.py`` computed ``debits - credits`` — the
  exact negation — so ``reconcile_wallet_ledger`` compared a balance against
  its own inverse and could never agree.
* ``services/ledger/service.py`` summed raw magnitudes with no sign at all,
  so debits and credits cancelled nothing and merely added up.

Asset codes
-----------
ISO 4217. ``IRR`` is the Iranian rial. ``"IRT"`` — which appeared as a default
in one path — is not a currency code, and neither is the ``"fiat"`` placeholder
that was also used as a default.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

__all__ = [
    "ALLOWED_ASSETS",
    "Asset",
    "Money",
    "MoneyError",
    "dec",
    "require_asset",
    "require_positive",
    "signed",
]

#: Assets this platform may book. Anything else is a data error, not a new
#: currency: adding one is a schema and compliance decision, not a constant edit.
ALLOWED_ASSETS = frozenset({"IRR", "ECO", "CARBON_tCO2e", "USD"})

#: Carbon is measured in tonnes of CO2-equivalent and is not a currency.
_QUANTITY = "CARBON_tCO2e"

_SCALE = Decimal("0.0001")


class MoneyError(ValueError):
    """Raised for a malformed or out-of-policy monetary value."""


class Asset(enum.StrEnum):
    """Assets the ledger may hold."""

    IRR = "IRR"
    ECO = "ECO"
    CARBON = _QUANTITY
    USD = "USD"


def dec(value: Any) -> Decimal:
    """Coerce to ``Decimal``, rejecting floats.

    ``Decimal(0.1)`` is ``0.1000000000000000055511151231257827``, and a float
    that round-trips through a JSON payload can land on a different float
    entirely. Accepting a float here is how a rounding error becomes a
    ledger discrepancy that nobody can reproduce.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise MoneyError("bool is not a monetary value")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise MoneyError(f"cannot parse {value!r} as a decimal") from exc
    if isinstance(value, float):
        raise MoneyError(
            "refusing to build money from a float; pass a str or Decimal "
            "(float 0.1 is not 0.1 in binary floating point)"
        )
    raise MoneyError(f"cannot coerce {type(value).__name__} to Decimal")


def require_asset(asset: str | Asset) -> str:
    """Validate an asset code, or raise."""
    code = asset.value if isinstance(asset, Asset) else str(asset)
    if code not in ALLOWED_ASSETS:
        raise MoneyError(f"asset must be one of {sorted(ALLOWED_ASSETS)}, got {code!r}")
    return code


def require_positive(amount: Any) -> Decimal:
    """Validate a strictly positive amount, or raise."""
    value = dec(amount)
    if value <= 0:
        raise MoneyError(f"amount must be positive, got {value}")
    return value


def signed(entry_type: str, amount: Any) -> Decimal:
    """Apply the sign convention: credit positive, debit negative.

    ``entry_type`` is compared case-insensitively because callers pass both
    ``"credit"`` and enum members whose ``.value`` is ``"credit"``.
    """
    value = dec(amount)
    kind = getattr(entry_type, "value", entry_type)
    kind = str(kind).strip().lower()
    if kind == "credit":
        return value
    if kind == "debit":
        return -value
    raise MoneyError(f"entry_type must be 'credit' or 'debit', got {entry_type!r}")


def balanced(entries: list[dict[str, Any]]) -> bool:
    """True when debits and credits cancel for every asset."""
    totals: dict[str, Decimal] = {}
    for entry in entries:
        asset = require_asset(entry["asset"])
        totals[asset] = totals.get(asset, Decimal("0")) + signed(
            entry["entry_type"], entry["amount"]
        )
    return all(total == 0 for total in totals.values())


@dataclass(frozen=True)
class Money:
    """A signed monetary amount in a named asset."""

    amount: Decimal
    asset: str = Asset.IRR.value

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", dec(self.amount))
        object.__setattr__(self, "asset", require_asset(self.asset))
        if self.amount != self.amount.quantize(_SCALE, rounding=ROUND_HALF_UP):
            raise MoneyError(
                f"{self.amount} has more than 4 decimal places; the ledger column is Numeric(19, 4)"
            )

    @classmethod
    def credit(cls, amount: Any, asset: str | Asset = Asset.IRR) -> Money:
        return cls(amount=require_positive(amount), asset=require_asset(asset))

    @classmethod
    def debit(cls, amount: Any, asset: str | Asset = Asset.IRR) -> Money:
        return cls(amount=-require_positive(amount), asset=require_asset(asset))

    def __str__(self) -> str:
        return f"{self.amount} {self.asset}"

    def to_json(self) -> dict[str, str]:
        return {"amount": str(self.amount), "asset": self.asset}
