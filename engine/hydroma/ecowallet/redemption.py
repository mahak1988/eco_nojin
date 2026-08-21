"""ECO Redemption System."""

from dataclasses import dataclass
from enum import Enum

from .ledger import EcoTransaction, get_eco_ledger


class RedemptionCategory(Enum):
    SEED_PURCHASE = "seed_purchase"
    CONSULTATION = "consultation"
    INSURANCE_DISCOUNT = "insurance_discount"
    MARKET_ACCESS = "market_access"
    TRAINING_COURSE = "training_course"
    EQUIPMENT_RENTAL = "equipment_rental"
    VETERINARY_SERVICE = "veterinary_service"


@dataclass
class RedemptionOption:
    category: RedemptionCategory
    eco_cost: float
    description: str
    description_fa: str
    value_irr: float


REDEMPTION_OPTIONS: dict[RedemptionCategory, RedemptionOption] = {
    RedemptionCategory.SEED_PURCHASE: RedemptionOption(
        category=RedemptionCategory.SEED_PURCHASE,
        eco_cost=100.0,
        description="Purchase seeds (1,000,000 IRR discount)",
        description_fa="خرید بذر (تخفیف ۱,۰۰۰,۰۰۰ تومان)",
        value_irr=1000000.0,
    ),
    RedemptionCategory.CONSULTATION: RedemptionOption(
        category=RedemptionCategory.CONSULTATION,
        eco_cost=20.0,
        description="Expert consultation session",
        description_fa="جلسه مشاوره با کارشناس",
        value_irr=200000.0,
    ),
    RedemptionCategory.INSURANCE_DISCOUNT: RedemptionOption(
        category=RedemptionCategory.INSURANCE_DISCOUNT,
        eco_cost=50.0,
        description="10% discount on crop insurance",
        description_fa="۱۰٪ تخفیف بیمه محصول",
        value_irr=500000.0,
    ),
    RedemptionCategory.MARKET_ACCESS: RedemptionOption(
        category=RedemptionCategory.MARKET_ACCESS,
        eco_cost=30.0,
        description="Free market access",
        description_fa="دسترسی رایگان به بازار",
        value_irr=300000.0,
    ),
    RedemptionCategory.TRAINING_COURSE: RedemptionOption(
        category=RedemptionCategory.TRAINING_COURSE,
        eco_cost=50.0,
        description="Full training course",
        description_fa="دوره آموزشی کامل",
        value_irr=500000.0,
    ),
    RedemptionCategory.EQUIPMENT_RENTAL: RedemptionOption(
        category=RedemptionCategory.EQUIPMENT_RENTAL,
        eco_cost=40.0,
        description="One day equipment rental",
        description_fa="یک روز اجاره تجهیزات",
        value_irr=400000.0,
    ),
    RedemptionCategory.VETERINARY_SERVICE: RedemptionOption(
        category=RedemptionCategory.VETERINARY_SERVICE,
        eco_cost=25.0,
        description="Veterinary consultation",
        description_fa="مشاوره دامپزشکی",
        value_irr=250000.0,
    ),
}


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
        tx = self.ledger.redeem(user_id, option.eco_cost, category.value, option.description)
        return tx

    def get_available_redemptions(self) -> list[dict]:
        return [
            {
                "category": opt.category.value,
                "eco_cost": opt.eco_cost,
                "description": opt.description,
                "description_fa": opt.description_fa,
                "value_irr": opt.value_irr,
            }
            for opt in REDEMPTION_OPTIONS.values()
        ]


_redemption_engine: RedemptionEngine | None = None


def get_redemption_engine() -> RedemptionEngine:
    global _redemption_engine
    if _redemption_engine is None:
        _redemption_engine = RedemptionEngine()
    return _redemption_engine
