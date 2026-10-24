"""Reward retention: how much of what was earned is still in circulation.

Added 2026-10-03. There was no way to answer "does the reward economy keep its
users" from the code. This module defines the indicators and computes the ones
that need no database, so the definitions are fixed before anyone populates them.

Pure functions over ``Decimal``. No ORM, no network, no settings. Where an
indicator needs transaction history it is stated as such rather than faked.

The three movements a balance can have, from the code:

  ``earn``     ``wallet.balance = balance + amount``        services/ecowallet/service.py:106
  ``redeem``   ``wallet.balance = balance - amount``        services/ecowallet/service.py:127
  ``retire``   sets ``retired_at``; does not delete the row  services/wallet/eco_balance.py

Note that ``retire`` is not a burn. The row survives and the amount stays in the
balance column, so a "retired" unit is neither circulating nor destroyed unless
something else moves it. That is why ``retired`` is tracked as its own
indicator rather than being folded into a burn rate -- folding them would report
scarcity that did not happen.
"""

from __future__ import annotations

from decimal import Decimal

ZERO = Decimal("0")


def circulating_ratio(issued: Decimal, redeemed: Decimal, burned: Decimal) -> Decimal | None:
    """Share still in circulation, as a percentage of issued."""
    if issued <= ZERO:
        return None
    remaining = issued - redeemed - burned
    return (remaining / issued * Decimal("100")).quantize(Decimal("0.01"))


def redemption_rate(issued: Decimal, redeemed: Decimal) -> Decimal | None:
    """Share of issued rewards actually redeemed."""
    if issued <= ZERO:
        return None
    return (redeemed / issued * Decimal("100")).quantize(Decimal("0.01"))


def burn_ratio(burned: Decimal, issued: Decimal) -> Decimal | None:
    """Share destroyed against the configured burn rate."""
    if issued <= ZERO:
        return None
    return (burned / issued * Decimal("100")).quantize(Decimal("0.01"))


def retention_report(
    issued: Decimal,
    redeemed: Decimal,
    burned: Decimal = ZERO,
    retired: Decimal = ZERO,
) -> dict[str, Decimal | None]:
    """Every retention indicator from one set of totals.

    ``retired`` is reported but deliberately excluded from every ratio: retiring
    a credit is a bookkeeping event in this codebase, not a supply change, so
    including it would invent scarcity. It appears as its own line so the number
    is visible without contaminating the rates.
    """
    return {
        "issued": issued,
        "redeemed": redeemed,
        "burned": burned,
        "retired": retired,
        "out_of_circulation": redeemed + burned,
        "still_circulating": issued - redeemed - burned,
        "redemption_rate_pct": redemption_rate(issued, redeemed),
        "burn_ratio_pct": burn_ratio(burned, issued),
        "circulating_pct": circulating_ratio(issued, redeemed, burned),
    }


def configured_burn_rate_pct() -> Decimal:
    """The burn rate the distribution config declares, as a percentage."""
    import yaml

    from services.ecowallet.distribution import CONFIG_PATH

    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return (Decimal(str(data["BURN_RATE_BPS"])) / Decimal("100")).quantize(Decimal("0.01"))


def platform_share_pct() -> Decimal:
    """The platform's cut of a distribution event, from the shared config."""
    import yaml

    from services.ecowallet.distribution import CONFIG_PATH

    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    bps = data["DISTRIBUTION_BPS"]
    return (Decimal(str(bps["platform"])) / Decimal("100")).quantize(Decimal("0.01"))


def distribution_sums_to_unity() -> bool:
    """Whether the declared split is a whole.

    ``distribution.py:132`` raises if the shares do not sum to 10000. This
    exposes the same invariant as an indicator so a config edit that breaks it
    fails a named check rather than an import.
    """
    import yaml

    from services.ecowallet.distribution import CONFIG_PATH

    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return sum(Decimal(str(v)) for v in data["DISTRIBUTION_BPS"].values()) == Decimal("10000")


def redeemable_value_of(catalogue_cost: Decimal, bps_share: Decimal) -> Decimal:
    """How much nominal commerce volume a reward balance can buy.

    ``bps_share`` is the commission the platform keeps, so a reward spent to
    waive a slice of it is worth the volume that slice represents. At 50% of the
    400 bps commerce commission (200 bps), 50 ECO covers a nominal 2,500 ECO of
    merchandise commission; waiving only 50 bps would cover 10,000. The value
    therefore falls as the waived share rises -- a narrower waiver is a cheaper
    promise and costs the platform less.

    This is a *foregone* revenue figure, not a cash saving to the holder, and the
    two must never be added together.
    """
    if bps_share <= ZERO:
        return ZERO
    return (catalogue_cost * Decimal("10000") / bps_share).quantize(Decimal("0.01"))
