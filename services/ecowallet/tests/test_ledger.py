"""Tests for the ECO wallet ledger, earning rules, and redemption."""

from decimal import Decimal

import pytest

from services.ecowallet.earning_rules import EARNING_RULES, EarningCategory
from services.ecowallet.ledger import (
    EcoLedger,
    TransactionType,
    _decimal,
)


@pytest.fixture
def ledger():
    led = EcoLedger()
    led.create_wallet("user-1")
    return led


class TestDecimalCoercion:
    """The ledger must never round-trip money through binary floats."""

    def test_float_becomes_exact_decimal(self):
        """0.07 must not become 0.070000000000000007."""
        assert _decimal(0.07) == Decimal("0.07")

    def test_decimal_passes_through(self):
        assert _decimal(Decimal("3.500")) == Decimal("3.500")

    def test_string_becomes_decimal(self):
        assert _decimal("12.34") == Decimal("12.34")

    def test_none_is_zero(self):
        assert _decimal(None) == Decimal("0")

    def test_int_becomes_decimal(self):
        assert _decimal(5) == Decimal("5")


class TestEcoLedgerWallet:
    """Tests for wallet lifecycle."""

    def test_create_wallet(self, ledger):
        wallet = ledger.get_wallet("user-1")
        assert wallet is not None
        assert wallet.user_id == "user-1"
        assert wallet.balance == Decimal("0")
        assert wallet.is_active is True

    def test_duplicate_wallet_is_rejected(self, ledger):
        with pytest.raises(ValueError, match="already exists"):
            ledger.create_wallet("user-1")

    def test_missing_wallet_returns_none(self, ledger):
        assert ledger.get_wallet("nobody") is None

    def test_missing_wallet_balance_is_zero(self, ledger):
        assert ledger.get_balance("nobody") == Decimal("0")


class TestEcoLedgerEarn:
    """Tests for earning."""

    def test_earn_credits_the_balance(self, ledger):
        tx = ledger.earn("user-1", Decimal("50.00"), "tree_planting", "Planted 100 trees")
        assert tx.amount == Decimal("50.00")
        assert tx.transaction_type == TransactionType.EARN
        assert ledger.get_balance("user-1") == Decimal("50.00")

    def test_earn_updates_the_totals(self, ledger):
        ledger.earn("user-1", Decimal("10.00"), "training_completion", "Course")
        ledger.earn("user-1", Decimal("5.00"), "referral", "Referral")
        wallet = ledger.get_wallet("user-1")
        assert wallet.total_earned == Decimal("15.00")
        assert wallet.total_redeemed == Decimal("0")
        assert wallet.balance == Decimal("15.00")

    def test_earn_records_the_running_balance(self, ledger):
        ledger.earn("user-1", Decimal("10.00"), "training_completion", "First")
        tx = ledger.earn("user-1", Decimal("2.50"), "referral", "Second")
        assert tx.balance_after == Decimal("12.50")

    def test_earn_from_a_float_keeps_the_written_value(self, ledger):
        ledger.earn("user-1", 0.07, "other", "tiny")
        assert ledger.get_balance("user-1") == Decimal("0.07")

    def test_earn_rejects_a_non_positive_amount(self, ledger):
        with pytest.raises(ValueError, match="must be positive"):
            ledger.earn("user-1", Decimal("0"), "tree_planting", "Zero")
        with pytest.raises(ValueError, match="must be positive"):
            ledger.earn("user-1", Decimal("-5"), "tree_planting", "Negative")

    def test_earn_on_a_missing_wallet_raises(self, ledger):
        with pytest.raises(ValueError, match="Wallet not found"):
            ledger.earn("nobody", Decimal("10"), "tree_planting", "Nope")

    def test_transactions_are_recorded(self, ledger):
        ledger.earn("user-1", Decimal("1.00"), "other", "A")
        ledger.earn("user-1", Decimal("2.00"), "other", "B")
        assert len(ledger.transactions["user-1"]) == 2


class TestEcoLedgerRedeem:
    """Tests for redemption."""

    def test_redeem_debits_the_balance(self, ledger):
        ledger.earn("user-1", Decimal("100.00"), "tree_planting", "Trees")
        tx = ledger.redeem("user-1", Decimal("30.00"), "reward", "Discount")
        assert tx.amount == Decimal("30.00")
        assert tx.transaction_type == TransactionType.REDEEM
        assert ledger.get_balance("user-1") == Decimal("70.00")

    def test_redeem_updates_the_totals(self, ledger):
        ledger.earn("user-1", Decimal("100.00"), "tree_planting", "Trees")
        ledger.redeem("user-1", Decimal("30.00"), "reward", "Discount")
        wallet = ledger.get_wallet("user-1")
        assert wallet.total_earned == Decimal("100.00")
        assert wallet.total_redeemed == Decimal("30.00")

    def test_redeem_cannot_exceed_the_balance(self, ledger):
        ledger.earn("user-1", Decimal("10.00"), "tree_planting", "Trees")
        with pytest.raises(ValueError, match="Insufficient balance"):
            ledger.redeem("user-1", Decimal("10.01"), "reward", "Too much")
        assert ledger.get_balance("user-1") == Decimal("10.00")

    def test_redeem_rejects_a_non_positive_amount(self, ledger):
        ledger.earn("user-1", Decimal("10.00"), "tree_planting", "Trees")
        with pytest.raises(ValueError, match="must be positive"):
            ledger.redeem("user-1", Decimal("0"), "reward", "Zero")

    def test_redeem_on_a_missing_wallet_raises(self, ledger):
        with pytest.raises(ValueError, match="Wallet not found"):
            ledger.redeem("nobody", Decimal("1"), "reward", "Nope")


class TestEarningRules:
    """Tests for the earning-rule table."""

    def test_every_category_has_a_rule(self):
        for category in EarningCategory:
            assert category in EARNING_RULES

    def test_rule_amounts_are_decimal(self):
        """The rates must be Decimal, not float."""
        for rule in EARNING_RULES.values():
            assert isinstance(rule.eco_amount, Decimal)

    def test_rule_amounts_are_positive(self):
        for rule in EARNING_RULES.values():
            assert rule.eco_amount > 0

    def test_rules_carry_both_languages(self):
        for rule in EARNING_RULES.values():
            assert rule.description
            assert rule.description_fa

    def test_rule_category_matches_its_key(self):
        for category, rule in EARNING_RULES.items():
            assert rule.category == category
