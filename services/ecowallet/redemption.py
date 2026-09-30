"""ECO Redemption System.

Honesty contract (revised 2026-09-26):

The platform is an intermediary and a service provider. It does NOT sell
inputs, does NOT hold inventory, does NOT underwrite a cash value, and does
NOT grant any insurance or credit benefit it does not itself control.

Therefore every redemption option below is a *service or access right
redeemed inside our own network*, never a promise of a third-party benefit.
`guaranteed_value` is the value WE can deliver; `third_party_value` is
deliberately absent from this table.
"""

# RUF001 flags extended Arabic-Indic digits as "ambiguous" against Latin
# lookalikes. In this file the Persian strings are Persian prose and must use
# Persian digits; converting them would corrupt the user-facing text.

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .ledger import EcoTransaction, get_eco_ledger


class RedemptionCategory(Enum):
    SEED_PURCHASE = "seed_purchase"
    CONSULTATION = "consultation"
    MARKET_FEE_DISCOUNT = "market_fee_discount"
    TRAINING_COURSE = "training_course"
    EQUIPMENT_RENTAL = "equipment_rental"
    VETERINARY_SERVICE = "veterinary_service"


class RedemptionKind(Enum):
    """What kind of thing the redemption actually is.

    This distinction is the compliance boundary. An option is either a service
    we perform, or an access right inside our own network. It is never a
    third-party benefit, because we cannot deliver one.
    """

    SERVICE = "service"
    NETWORK_ACCESS = "network_access"


@dataclass
class RedemptionOption:
    category: RedemptionCategory
    #: What it costs to redeem. Decimal, not float: this is compared against a
    #: ``Decimal`` ledger balance and written to a ``Numeric(19, 4)`` column.
    eco_cost: Decimal
    description: str
    description_fa: str
    #: What the platform itself can deliver. NOT a cash amount, NOT a discount
    #: promised by a third party. For access options this is the reduction in
    #: the platform's own marketplace commission rate.
    delivered_value: str
    delivered_value_fa: str
    kind: RedemptionKind
    #: Human-readable boundary of what is NOT included.
    not_included: str
    not_included_fa: str


REDEMPTION_OPTIONS: dict[RedemptionCategory, RedemptionOption] = {
    # --- Access inside our own marketplace. We control the commission rate,
    #     so this is the one benefit we can actually stand behind. ---
    RedemptionCategory.MARKET_FEE_DISCOUNT: RedemptionOption(
        category=RedemptionCategory.MARKET_FEE_DISCOUNT,
        eco_cost=Decimal("50.0"),
        description=(
            "Marketplace commission reduced from the standard rate for the "
            "next N listings. Applied to commissions collected by the "
            "platform itself."
        ),
        description_fa=(
            "کاهش نرخ کارمزد بازارگاه از نرخ استاندارد برای N فهرست بعدی. "
            "روی کارمزدی که خودِ پلتفرم وصول می‌کند اعمال می‌شود."
        ),
        delivered_value="50% reduction of our own marketplace commission, 5 listings",
        delivered_value_fa="۵۰٪ کاهش کارمزد بازارگاه خودمان، برای ۵ فهرست",
        kind=RedemptionKind.NETWORK_ACCESS,
        not_included=(
            "Does not change product prices, does not guarantee a buyer, does "
            "not guarantee any sale."
        ),
        not_included_fa=("قیمت کالا را تغییر نمی‌دهد · خریدار تضمین نمی‌کند · فروش تضمین نمی‌شود."),
    ),
    # --- Services the platform delivers or coordinates directly. ---
    RedemptionCategory.CONSULTATION: RedemptionOption(
        category=RedemptionCategory.CONSULTATION,
        eco_cost=Decimal("20.0"),
        description="Advisory session with a platform agronomist",
        description_fa="جلسه مشاوره با کارشناس زراعی پلتفرم",
        delivered_value="One advisory session (60 min)",
        delivered_value_fa="یک جلسه مشاوره (۶۰ دقیقه)",
        kind=RedemptionKind.SERVICE,
        not_included=("Not investment advice. Does not guarantee yield, price, or outcome."),
        not_included_fa=("مشاورهٔ سرمایه‌گذاری نیست · عملکرد، قیمت یا نتیجه را تضمین نمی‌کند."),
    ),
    RedemptionCategory.TRAINING_COURSE: RedemptionOption(
        category=RedemptionCategory.TRAINING_COURSE,
        eco_cost=Decimal("50.0"),
        description="Platform training course seat",
        description_fa="صندلی دورهٔ آموزشی پلتفرم",
        delivered_value="One course seat",
        delivered_value_fa="یک صندلی دوره",
        kind=RedemptionKind.SERVICE,
        not_included=("Completion does not certify the holder. No yield claim is made."),
        not_included_fa=("پایان دوره گواهی‌نامه صادر نمی‌کند · هیچ ادعای بازدهی نمی‌شود."),
    ),
    RedemptionCategory.VETERINARY_SERVICE: RedemptionOption(
        category=RedemptionCategory.VETERINARY_SERVICE,
        eco_cost=Decimal("25.0"),
        description="Listing and introduction to veterinary providers in the network",
        description_fa="ثبت و معرفی به ارائه‌دهندگان دامپزشکی شبکه",
        delivered_value="Introduction to one provider",
        delivered_value_fa="معرفی به یک ارائه‌دهنده",
        kind=RedemptionKind.SERVICE,
        not_included=(
            "The platform is an intermediary. It is not the veterinary provider "
            "and does not deliver veterinary care."
        ),
        not_included_fa=(
            "پلتفرم واسطه است. ارائه‌دهندهٔ خدمات دامپزشکی نیست و خدمات درمانی ارائه نمی‌دهد."
        ),
    ),
    RedemptionCategory.SEED_PURCHASE: RedemptionOption(
        category=RedemptionCategory.SEED_PURCHASE,
        eco_cost=Decimal("100.0"),
        description=(
            "Access to seed listings from sellers in the marketplace. The "
            "farmer buys from the seller; the platform does not sell or supply."
        ),
        description_fa=(
            "دسترسی به فهرست فروشندگان بذر در بازارگاه. کشاورز از فروشنده خرید "
            "می‌کند؛ پلتفرم فروشنده یا تأمین‌کننده نیست."
        ),
        delivered_value="Marketplace listing access only — no supply guarantee",
        delivered_value_fa="فقط دسترسی به فهرست بازارگاه — بدون تضمین تأمین",
        kind=RedemptionKind.NETWORK_ACCESS,
        not_included=(
            "The platform does not supply seed, does not hold inventory, does "
            "not guarantee availability, quality, germination, or price."
        ),
        not_included_fa=(
            "پلتفرم بذر تأمین نمی‌کند · موجودی نگه نمی‌دارد · موجودی، کیفیت، "
            "قوه نامیه یا قیمت را تضمین نمی‌کند."
        ),
    ),
    RedemptionCategory.EQUIPMENT_RENTAL: RedemptionOption(
        category=RedemptionCategory.EQUIPMENT_RENTAL,
        eco_cost=Decimal("40.0"),
        description="Listing and introduction to equipment rental providers in the network",
        description_fa="ثبت و معرفی به ارائه‌دهندگان اجارهٔ تجهیزات در شبکه",
        delivered_value="Introduction to one provider",
        delivered_value_fa="معرفی به یک ارائه‌دهنده",
        kind=RedemptionKind.SERVICE,
        not_included=(
            "The platform does not own, rent, or warrant the equipment. The "
            "rental contract is between the farmer and the provider."
        ),
        not_included_fa=(
            "پلتفرم مالک یا موجر تجهیزات نیست و آن را ضمانت نمی‌کند. "
            "قرارداد اجاره بین کشاورز و ارائه‌دهنده است."
        ),
    ),
}

#: Categories removed on 2026-09-26 and why. Kept so the removal is auditable
#: rather than silent — see reports/HYDROMA_NOJIN_EXECUTION_PLAN_FA.md §5.
REMOVED_REDEMPTIONS: dict[str, str] = {
    "insurance_discount": (
        "Removed: the platform has no insurance product and does not intend to "
        "acquire one. Promising a crop-insurance discount was a false "
        "commitment to the holder."
    ),
    "market_access": (
        "Replaced by 'market_fee_discount': the platform cannot promise buyer "
        "access or sale outcomes, because it neither buys nor sells. It can "
        "only commit to its own commission rate, which it controls."
    ),
}

#: Cross-check: every enum member must have a live option. Prevents the
#: mismatch where a category is declared but not redeemable.
assert set(RedemptionCategory) == set(REDEMPTION_OPTIONS), (
    f"RedemptionCategory and REDEMPTION_OPTIONS are out of sync: "
    f"{set(RedemptionCategory) ^ set(REDEMPTION_OPTIONS)}"
)


class RedemptionEngine:
    def __init__(self):
        self.ledger = get_eco_ledger()

    def process_redemption(self, user_id: str, category: RedemptionCategory) -> EcoTransaction:
        option = REDEMPTION_OPTIONS.get(category)
        if not option:
            raise ValueError(f"Unknown category: {category}")
        balance = self.ledger.get_balance(user_id)
        if balance < option.eco_cost:
            raise ValueError(f"Insufficient balance: {balance} < {option.eco_cost}")
        tx = self.ledger.redeem(
            user_id, option.eco_cost, option.delivered_value, option.description
        )
        return tx

    def get_available_redemptions(self) -> list[dict]:
        return [
            {
                "category": opt.category.value,
                "kind": opt.kind.value,
                "eco_cost": opt.eco_cost,
                "description": opt.description,
                "description_fa": opt.description_fa,
                "delivered_value": opt.delivered_value,
                "delivered_value_fa": opt.delivered_value_fa,
                "not_included": opt.not_included,
                "not_included_fa": opt.not_included_fa,
            }
            for opt in REDEMPTION_OPTIONS.values()
        ]


_redemption_engine: RedemptionEngine | None = None


def get_redemption_engine() -> RedemptionEngine:
    global _redemption_engine
    if _redemption_engine is None:
        _redemption_engine = RedemptionEngine()
    return _redemption_engine
