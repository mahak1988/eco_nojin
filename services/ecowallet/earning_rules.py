"""ECO Earning Rules Engine.

Phase 4 consolidation (S-MONEY): the rates here are ``Decimal``, like the
canonical table in ``services/finance/earning_rates.py`` and the ledger they
feed. They used to be ``float``, so ``rule.eco_amount * quantity`` was binary
floating-point multiplication and the ledger then stored whatever garbage the
product produced: a tree-planting earning of 0.07 units credited
``Decimal("3.5000000000000004")`` into a ``Numeric(19, 4)`` column instead of
``Decimal("3.500")``.
"""

# RUF001 flags extended Arabic-Indic digits as "ambiguous" against Latin
# lookalikes. The description_fa strings below are Persian prose and must use
# Persian digits; converting them would corrupt the user-facing text. Same
# rationale as services/ecowallet/redemption.py.

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .ledger import EcoTransaction, get_eco_ledger


class EarningCategory(Enum):
    TREE_PLANTING = "tree_planting"
    TRAINING_COMPLETION = "training_completion"
    MARKET_SALE = "market_sale"
    CARBON_VERIFICATION = "carbon_verification"
    REFERRAL = "referral"
    REGENERATIVE_FARMING = "regenerative_farming"
    SOIL_IMPROVEMENT = "soil_improvement"
    WATER_CONSERVATION = "water_conservation"


@dataclass
class EarningRule:
    category: EarningCategory
    eco_amount: Decimal
    description: str
    description_fa: str
    verification_required: bool = True
    max_per_month: int | None = None


EARNING_RULES: dict[EarningCategory, EarningRule] = {
    EarningCategory.TREE_PLANTING: EarningRule(
        category=EarningCategory.TREE_PLANTING,
        eco_amount=Decimal("50.0"),
        description="Plant 100 trees (verified by satellite)",
        description_fa="کاشت ۱۰۰ درخت (تأیید ماهواره)",
        max_per_month=4,
    ),
    EarningCategory.TRAINING_COMPLETION: EarningRule(
        category=EarningCategory.TRAINING_COMPLETION,
        eco_amount=Decimal("20.0"),
        description="Complete a training course",
        description_fa="تکمیل یک دوره آموزشی",
        verification_required=False,
        max_per_month=2,
    ),
    EarningCategory.MARKET_SALE: EarningRule(
        category=EarningCategory.MARKET_SALE,
        eco_amount=Decimal("1.0"),
        description="Sell products (per 100,000 IRR)",
        description_fa="فروش محصول (به ازای هر ۱۰۰,۰۰۰ تومان)",
    ),
    EarningCategory.CARBON_VERIFICATION: EarningRule(
        category=EarningCategory.CARBON_VERIFICATION,
        eco_amount=Decimal("80.0"),
        description="Carbon verified by satellite",
        description_fa="تأیید کربن توسط ماهواره",
        max_per_month=1,
    ),
    EarningCategory.REFERRAL: EarningRule(
        category=EarningCategory.REFERRAL,
        eco_amount=Decimal("5.0"),
        description="Refer a new farmer",
        description_fa="معرفی یک کشاورز جدید",
        verification_required=False,
        max_per_month=10,
    ),
    EarningCategory.REGENERATIVE_FARMING: EarningRule(
        category=EarningCategory.REGENERATIVE_FARMING,
        eco_amount=Decimal("30.0"),
        description="Regenerative farming practices",
        description_fa="کشاورزی احیاکننده",
        max_per_month=2,
    ),
    EarningCategory.SOIL_IMPROVEMENT: EarningRule(
        category=EarningCategory.SOIL_IMPROVEMENT,
        eco_amount=Decimal("25.0"),
        description="Improve soil health",
        description_fa="بهبود سلامت خاک",
        max_per_month=1,
    ),
    EarningCategory.WATER_CONSERVATION: EarningRule(
        category=EarningCategory.WATER_CONSERVATION,
        eco_amount=Decimal("25.0"),
        description="Water conservation practices",
        description_fa="صرفه‌جویی در مصرف آب",
        max_per_month=2,
    ),
}


class EarningEngine:
    def __init__(self):
        self.ledger = get_eco_ledger()
        self.monthly_earnings: dict[str, dict[str, int]] = {}

    def process_earning(
        self, user_id: str, category: EarningCategory, quantity: float | Decimal = 1.0
    ) -> EcoTransaction:
        rule = EARNING_RULES.get(category)
        if not rule:
            raise ValueError(f"Unknown category: {category}")

        # Decimalise the quantity *before* multiplying. Coercing the product
        # instead would keep the binary-float error: 50.0 * 0.07 is
        # 3.5000000000000004 in binary, and no later conversion recovers 3.500.
        # The non-positive-total check stays in the ledger, where it already was;
        # moving it here would change which error a zero-quantity earning raises.
        quantity_d = quantity if isinstance(quantity, Decimal) else Decimal(str(quantity))

        if rule.max_per_month is not None:
            if user_id not in self.monthly_earnings:
                self.monthly_earnings[user_id] = {}
            current_count = self.monthly_earnings[user_id].get(category.value, 0)
            if current_count >= rule.max_per_month:
                raise ValueError(f"Monthly limit reached: {rule.max_per_month}")
            self.monthly_earnings[user_id][category.value] = current_count + 1

        eco_amount = rule.eco_amount * quantity_d
        tx = self.ledger.earn(user_id, eco_amount, category.value, rule.description)
        return tx

    def get_available_earnings(self) -> list[dict]:
        return [
            {
                "category": rule.category.value,
                "eco_amount": rule.eco_amount,
                "description": rule.description,
                "description_fa": rule.description_fa,
                "verification_required": rule.verification_required,
                "max_per_month": rule.max_per_month,
            }
            for rule in EARNING_RULES.values()
        ]


_earning_engine: EarningEngine | None = None


def get_earning_engine() -> EarningEngine:
    global _earning_engine
    if _earning_engine is None:
        _earning_engine = EarningEngine()
    return _earning_engine
