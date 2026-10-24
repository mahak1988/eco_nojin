"""Reference basket pricing for the input credit instrument.

Purpose
-------
Give the redemption mechanism a value that is *external, published, and
reproducible*, so the platform never has to promise a price itself. The
platform's obligation is limited to publishing a formula and a current number;
the number comes from the World Bank.

Price anchor
------------
World Bank "Pink Sheet" (CMO), published monthly, CC-BY 4.0, no registration,
no API key. It is used rather than the FAO Food Price Index because the FAO
index is an *output* index and contains **no fertilizer and no seed** at all,
while every component of an input basket does.

Agronomic ratios used here come from the platform's own existing price
defaults (`engine/hydroma/carbon/calculator.py` and
`services/scientific_motors/economy_motor.py`) so the module is consistent
with the rest of the codebase. They are planning ratios, not recommendations.

Honesty contract
----------------
This module computes an *illustrative planning value*. It is not a quotation,
not a valuation, not a price guarantee, and not a VVB determination. The
instrument's terms must phrase the figure as a **ceiling on redemption value**,
never as a guaranteed amount. See
`reports/HYDROMA_NOJIN_EXECUTION_PLAN_FA.md` §3 and
`reports/HYDROMA_NOJIN_CONSULTING_FRAMEWORK_FA.md` §0.2.
"""

from __future__ import annotations

import csv
import io
import logging
import math
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum

logger = logging.getLogger(__name__)

#: World Bank CMO Pink Sheet, monthly PDF/XLSX, CC-BY 4.0, no registration.
#: The historical monthly workbook is the machine-readable form.
PINK_SHEET_MONTHLY_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)
PINK_SHEET_ATTRIBUTION = "World Bank Commodity Markets Outlook (Pink Sheet), CC-BY 4.0"

#: Fertilizer benchmark series, USD per metric tonne. The Pink Sheet quotes
#: these at different terminals, which is why the landed-cost multiplier
#: below exists and why it is the platform's real cost model.
#:
#: Keys are the canonical short identifiers used everywhere in this module.
#: `pink_sheet_series` is the label the published sheet uses, and is what
#: `parse_pink_sheet_csv` matches columns against.
FERTILIZER_SERIES: dict[str, dict[str, str]] = {
    "dap": {"label": "DAP", "terminal": "fob US Gulf", "pink_sheet_series": "DAP"},
    "urea": {
        "label": "Urea, E. Europe",
        "terminal": "fob E. Europe",
        "pink_sheet_series": "Urea",
    },
    "mop": {
        "label": "Potassium chloride, granular",
        "terminal": "CFR Brazil",
        "pink_sheet_series": "Potassium chloride",
    },
    "tsp": {"label": "TSP", "terminal": "import US Gulf", "pink_sheet_series": "TSP"},
}

#: Cost of getting a tonne of the above to a landlocked smallholder: freight,
#: marine insurance, port handling, inland haulage, finance cost, FX risk.
#:
#: This is the platform's defensible number. A single global index cannot
#: produce it; it is country-specific and is the reason the design is not
#: trivially copied. Values are planning ranges, to be replaced by measured
#: figures.
LANDED_COST_MULTIPLIER = {
    "coastal_low_income": (1.15, 1.35),
    "coastal_middle_income": (1.10, 1.25),
    "landlocked_neighbouring": (1.35, 1.65),
    "landlocked_remote": (1.65, 2.10),
    "pastoralist_mobile": (1.80, 2.40),
}

#: Used for the audit-trail record. Recorded but never used for valuation.
_LAST_FETCH: dict[str, object] = {"at": None, "source": None, "rows": 0, "ok": False}


class DataMode(StrEnum):
    FIELD_VERIFIED = "field_verified"
    MODELLED_ESTIMATE = "modelled_estimate"


class BasketError(RuntimeError):
    """Raised when a basket cannot be computed."""


@dataclass(frozen=True)
class InputItem:
    """One line of a base basket.

    `kg_per_ha` is the agronomic rate. `unit` is either a Pink Sheet series
    name, or a local item whose price is supplied by the caller.
    """

    name: str
    kg_per_ha: float
    unit: str
    local_price_usd_per_tonne: float | None = None

    def __post_init__(self) -> None:
        if self.kg_per_ha <= 0:
            raise ValueError(f"{self.name}: kg_per_ha must be > 0")
        if self.unit not in FERTILIZER_SERIES and self.local_price_usd_per_tonne is None:
            raise ValueError(
                f"{self.name}: unit {self.unit!r} is not a reference series and no "
                f"local_price_usd_per_tonne was supplied"
            )


@dataclass(frozen=True)
class BaseBasket:
    """A base basket for one hectare of one cropping system."""

    crop: str
    market_class: str
    items: tuple[InputItem, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.market_class not in LANDED_COST_MULTIPLIER:
            raise ValueError(
                f"unknown market_class {self.market_class!r}; known: "
                f"{sorted(LANDED_COST_MULTIPLIER)}"
            )
        if not self.items:
            raise ValueError("a base basket must contain at least one item")


@dataclass(frozen=True)
class BasketValuation:
    """Result of valuing a basket. All money fields are USD per hectare."""

    crop: str | None = None
    market_class: str | None = None
    data_mode: DataMode | None = None
    valued_at: datetime | None = None
    #: USD/t for each input used, keyed by item name.
    unit_prices: dict[str, float] | None = None
    #: USD/ha contribution of each input, keyed by item name.
    line_values: dict[str, float] | None = None
    international_subtotal_usd_ha: float | None = None
    landed_multiplier: float | None = None
    landed_value_usd_ha: float | None = None
    platform_share: float | None = None
    #: What the platform can actually deliver: a ceiling, not a guarantee.
    redemption_ceiling_usd_ha: float | None = None
    provenance: str | None = None
    data_mode_note: str | None = None
    data_source: str = "modelled"
    model: str = "reference basket valuation"
    computed: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)


#: Sanity band. Outside this range a computed basket indicates a bad price
#: fetch or a bad agronomic ratio, and should not be published.
PLAUSIBLE_USD_HA_RANGE = (50.0, 2000.0)


def _resolve_unit_price(item: InputItem, quotes: dict[str, float]) -> float:
    """Resolve a unit price.

    `quotes` is keyed by the canonical short identifier (`dap`, `urea`, ...),
    the same vocabulary `InputItem.unit` uses. Mapping between the published
    Pink Sheet labels and these keys happens in exactly one place,
    `parse_pink_sheet_csv`, so the two can never disagree.
    """
    if item.local_price_usd_per_tonne is not None:
        return item.local_price_usd_per_tonne
    if item.unit not in FERTILIZER_SERIES:
        raise BasketError(
            f"{item.name}: unresolved unit {item.unit!r}; known units: {sorted(FERTILIZER_SERIES)}"
        )
    if item.unit not in quotes:
        raise BasketError(
            f"{item.name}: quote {item.unit!r} missing from the fetched price "
            f"set. Available: {sorted(quotes)}"
        )
    price = quotes[item.unit]
    if not math.isfinite(price) or price <= 0:
        raise BasketError(f"{item.name}: non-positive quote {price!r} for unit {item.unit!r}")
    return price


def _quality_factor(data_mode: DataMode) -> float:
    """Multiplier reflecting verification depth, not tonnage."""
    return 1.00 if data_mode is DataMode.FIELD_VERIFIED else 0.60


def value_basket(
    basket: BaseBasket,
    quotes: dict[str, float],
    *,
    platform_share: float = 0.05,
    as_of: date | None = None,
) -> BasketValuation:
    """Value a base basket at the supplied reference quotes.

    `quotes` maps Pink Sheet series names (see FERTILIZER_SERIES) to USD per
    metric tonne. Callers that fetched the sheet live pass the parsed values;
    tests pass a fixed dict. Keeping the price source an explicit argument is
    what makes the resulting number reproducible and auditable.

    `platform_share` is the fraction of the basket the platform retains. It is
    capped at 0.08 in year one and 0.05 thereafter; see
    reports/HYDROMA_NOJIN_EXECUTION_PLAN_FA.md §2.5.
    """
    if not quotes:
        raise BasketError("no reference quotes supplied; cannot value a basket")
    if not 0.0 <= platform_share <= 0.08:
        raise BasketError(
            f"platform_share must be within 0.00-0.08 to stay a service fee "
            f"rather than a markup on farmer inputs; got {platform_share}"
        )

    lo, hi = LANDED_COST_MULTIPLIER[basket.market_class]
    landed = (lo + hi) / 2.0

    unit_prices: dict[str, float] = {}
    line_values: dict[str, float] = {}
    subtotal = 0.0
    for item in basket.items:
        price = _resolve_unit_price(item, quotes)
        line = (item.kg_per_ha * price) / 1000.0
        unit_prices[item.name] = price
        line_values[item.name] = line
        subtotal += line

    landed_value = subtotal * landed
    ceiling = landed_value * (1.0 - platform_share)

    if not (PLAUSIBLE_USD_HA_RANGE[0] <= landed_value <= PLAUSIBLE_USD_HA_RANGE[1]):
        raise BasketError(
            f"computed basket value {landed_value:.2f} USD/ha for crop "
            f"{basket.crop!r} falls outside the plausible range "
            f"{PLAUSIBLE_USD_HA_RANGE}. Refusing to publish. Check the price "
            f"fetch and the agronomic ratios."
        )

    return BasketValuation(
        crop=basket.crop,
        market_class=basket.market_class,
        data_mode=DataMode.FIELD_VERIFIED,
        valued_at=datetime.combine(as_of or date.today(), datetime.min.time(), tzinfo=UTC),
        unit_prices=unit_prices,
        line_values=line_values,
        international_subtotal_usd_ha=round(subtotal, 2),
        landed_multiplier=landed,
        landed_value_usd_ha=round(landed_value, 2),
        platform_share=platform_share,
        redemption_ceiling_usd_ha=round(ceiling, 2),
        provenance=PINK_SHEET_ATTRIBUTION,
        data_mode_note=(
            "Quality factor 1.00 applies to field-verified records. A modelled "
            "estimate is valued at 0.60 and may not back a tokenised issuance; "
            "see services/carbon/integration/credit_bridge.py."
        ),
        notes=(
            f"landed multiplier midpoint for {basket.market_class!r}: {lo}-{hi}",
            "value is a ceiling on redemption, not a guaranteed amount",
            "local seed and chemistry prices are caller-supplied, not indexed",
        ),
    )


def denomination_plan(
    basket_value_usd_ha: float, units_per_basket: int = 100
) -> list[tuple[float, str]]:
    """Split a basket into redeemable denominations.

    Design requirement, not a nicety: in Zambia 84% of e-voucher farmers left a
    balance because no SKU was priced to absorb the remainder. At least 10% of
    the network's catalogue must be purchasable below `smallest` so the residual
    is spendable rather than forfeited.
    """
    if units_per_basket <= 0:
        raise ValueError("units_per_basket must be > 0")
    small = basket_value_usd_ha * 0.08
    return [
        (round(basket_value_usd_ha, 2), f"{units_per_basket} units = 1 base basket"),
        (round(basket_value_usd_ha * 0.25, 2), f"{units_per_basket // 4} units = 1/4 basket"),
        (round(small, 2), f"{max(1, units_per_basket // 12)} units = small purchase"),
    ]


def quality_factor(data_mode: DataMode) -> float:
    """Public accessor for the verification-depth multiplier."""
    return _quality_factor(data_mode)


# --------------------------------------------------------------------------- #
# Reference price ingestion
# --------------------------------------------------------------------------- #


def parse_pink_sheet_csv(payload: str) -> dict[str, float]:
    """Extract the most recent complete month of fertilizer quotes from a CSV.

    The Pink Sheet's machine-readable monthly workbook is wide: one column per
    series, one row per month, prefixed 'Unnamed: ' where headers spill. This
    parser matches on a normalised series label so it survives header renaming,
    and returns the last row in which every matched series has a value, so a
    partially-published month is never used.
    """
    # published series label -> canonical short key
    label_to_key: dict[str, str] = {
        spec["pink_sheet_series"]: key for key, spec in FERTILIZER_SERIES.items()
    }

    reader = csv.DictReader(io.StringIO(payload))
    if not reader.fieldnames:
        raise BasketError("pink sheet CSV has no header row")

    header_map: dict[str, str] = {}
    for col in reader.fieldnames:
        flat = col.replace(" ", "").replace("(", "").replace(")", "").strip().lower()
        for label, key in label_to_key.items():
            if label.replace(" ", "").lower() in flat and key not in header_map.values():
                header_map[col] = key

    missing = set(label_to_key.values()) - set(header_map.values())
    if missing:
        raise BasketError(
            f"pink sheet CSV is missing required series: {sorted(missing)}; "
            f"columns seen: {reader.fieldnames}"
        )

    best: dict[str, float] | None = None
    for row in reader:
        parsed: dict[str, float] = {}
        for col, key in header_map.items():
            raw = (row.get(col) or "").strip()
            if not raw:
                continue
            try:
                parsed[key] = float(raw)
            except ValueError:
                continue
        if set(parsed) == set(header_map.values()):
            best = parsed

    if best is None:
        raise BasketError("no row in the pink sheet CSV had a complete price set")
    return best


def fetch_reference_prices(payload: str | None = None) -> dict[str, float]:
    """Return the current fertilizer quotes and record provenance.

    `payload` lets a caller supply a previously downloaded sheet, which keeps
    this function testable without network access and lets the scheduled job
    cache its input. The audit trail is written to `_LAST_FETCH`.
    """
    global _LAST_FETCH
    if payload is None:
        raise BasketError(
            "no pink sheet payload supplied. Pass the downloaded sheet via "
            f"`payload`; the reference location is {PINK_SHEET_MONTHLY_URL}"
        )
    try:
        quotes = parse_pink_sheet_csv(payload)
    except BasketError:
        _LAST_FETCH = {
            "at": datetime.now(UTC).isoformat(),
            "source": PINK_SHEET_MONTHLY_URL,
            "rows": 0,
            "ok": False,
        }
        raise
    _LAST_FETCH = {
        "at": datetime.now(UTC).isoformat(),
        "source": PINK_SHEET_MONTHLY_URL,
        "attribution": PINK_SHEET_ATTRIBUTION,
        "rows": len(quotes),
        "ok": True,
    }
    logger.info("Loaded %d reference fertilizer quotes", len(quotes))
    return quotes


def last_fetch_audit() -> dict[str, object]:
    """Audit record for the most recent ingestion attempt."""
    return dict(_LAST_FETCH)
