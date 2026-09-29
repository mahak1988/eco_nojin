"""Tests for the S-MONEY contract module.

Pins the rules that end the four-``LedgerService`` divergence: ``Decimal``
only, one sign convention, ISO 4217 asset codes, and four-decimal precision
matching the ``Numeric(19, 4)`` column.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from services._contracts.money import (
    ALLOWED_ASSETS,
    Asset,
    Money,
    MoneyError,
    balanced,
    dec,
    require_asset,
    require_positive,
    signed,
)


class TestDecimalOnly:
    def test_accepts_int_str_and_decimal(self):
        assert dec(5) == Decimal("5")
        assert dec("5.25") == Decimal("5.25")
        assert dec(Decimal("5.25")) == Decimal("5.25")

    def test_rejects_float(self):
        """Decimal(0.1) is not 0.1; that gap becomes an unreproducible ledger gap."""
        with pytest.raises(MoneyError, match="refusing to build money from a float"):
            dec(0.1)

    def test_rejects_bool(self):
        with pytest.raises(MoneyError, match="bool is not a monetary value"):
            dec(True)

    def test_rejects_unparseable_string(self):
        with pytest.raises(MoneyError, match="cannot parse"):
            dec("twelve")

    def test_rejects_unknown_type(self):
        with pytest.raises(MoneyError, match="cannot coerce"):
            dec(object())


class TestSignConvention:
    def test_credit_is_positive(self):
        assert signed("credit", "100.50") == Decimal("100.50")

    def test_debit_is_negative(self):
        assert signed("debit", "100.50") == Decimal("-100.50")

    def test_is_case_and_whitespace_insensitive(self):
        assert signed(" CREDIT ", "10") == Decimal("10")
        assert signed("Debit", "10") == Decimal("-10")

    def test_accepts_enum_members(self):
        class EntryType:
            value = "debit"

        assert signed(EntryType(), "10") == Decimal("-10")

    def test_rejects_an_unknown_entry_type(self):
        with pytest.raises(MoneyError, match="must be 'credit' or 'debit'"):
            signed("transfer", "10")

    def test_the_two_surviving_conventions_agree(self):
        """The bug: wallet_service used debits - credits, the exact negation."""
        credits = [("credit", "100.00"), ("debit", "30.00")]
        assert sum((signed(k, v) for k, v in credits), Decimal("0")) == Decimal("70.00")


class TestAssetCodes:
    def test_iso_4217_irr_is_allowed(self):
        assert require_asset("IRR") == "IRR"
        assert require_asset(Asset.IRR) == "IRR"

    def test_irt_is_not_a_currency_code(self):
        with pytest.raises(MoneyError, match="asset must be one of"):
            require_asset("IRT")

    def test_fiat_placeholder_is_rejected(self):
        with pytest.raises(MoneyError):
            require_asset("fiat")

    def test_allowed_set_is_closed(self):
        assert {"IRR", "ECO", "CARBON_tCO2e", "USD"} == ALLOWED_ASSETS


class TestPrecision:
    def test_four_decimal_places_are_accepted(self):
        assert Money(amount=Decimal("1.2345"), asset="IRR").amount == Decimal("1.2345")

    def test_five_decimal_places_are_refused(self):
        """The column is Numeric(19, 4); more would be silently truncated."""
        with pytest.raises(MoneyError, match="more than 4 decimal places"):
            Money(amount=Decimal("1.23456"), asset="IRR")

    def test_require_positive_rejects_zero_and_negative(self):
        assert require_positive("0.01") == Decimal("0.01")
        with pytest.raises(MoneyError, match="must be positive"):
            require_positive(0)
        with pytest.raises(MoneyError, match="must be positive"):
            require_positive("-1")


class TestMoney:
    def test_credit_and_debit_constructors(self):
        assert Money.credit("10", "IRR").amount == Decimal("10")
        assert Money.debit("10", "IRR").amount == Decimal("-10")

    def test_str_includes_the_asset(self):
        assert str(Money.credit("10.5", "ECO")) == "10.5 ECO"

    def test_to_json_is_serialisable(self):
        assert Money.debit("2.5", "USD").to_json() == {"amount": "-2.5", "asset": "USD"}

    def test_constructor_validates_the_asset(self):
        with pytest.raises(MoneyError):
            Money(amount=Decimal("1"), asset="IRT")


class TestBalanced:
    def test_a_balanced_batch(self):
        entries = [
            {"entry_type": "debit", "asset": "IRR", "amount": "100.00"},
            {"entry_type": "credit", "asset": "IRR", "amount": "100.00"},
        ]
        assert balanced(entries)

    def test_an_unbalanced_batch_is_caught(self):
        """wallet_service.create_journal_batch had no check at all."""
        entries = [
            {"entry_type": "debit", "asset": "IRR", "amount": "100.00"},
            {"entry_type": "credit", "asset": "IRR", "amount": "99.99"},
        ]
        assert not balanced(entries)

    def test_balanced_per_asset_not_in_aggregate(self):
        entries = [
            {"entry_type": "debit", "asset": "IRR", "amount": "100.00"},
            {"entry_type": "credit", "asset": "IRR", "amount": "40.00"},
            {"entry_type": "debit", "asset": "USD", "amount": "40.00"},
            {"entry_type": "credit", "asset": "USD", "amount": "100.00"},
        ]
        assert not balanced(entries), "opposite imbalances must not cancel across assets"

    def test_an_empty_batch_is_balanced(self):
        assert balanced([])


class TestAccountReferenceIsSolved:
    """``account_id`` was written as both an id and a code; both must resolve."""

    def test_join_condition_is_an_or_not_an_equality(self):
        from sqlalchemy.sql.elements import BooleanClauseList

        from services.finance.account_ref import account_join_condition

        clause = account_join_condition()
        assert isinstance(clause, BooleanClauseList), (
            "account_id (String) == FinAccount.id (Integer) can never match; "
            "the join must accept either convention"
        )
        assert clause.operator.__name__ == "or_"

    def test_module_docstring_records_both_conventions(self):
        from pathlib import Path

        import services.finance.account_ref as mod

        text = Path(mod.__file__).read_text(encoding="utf-8")
        assert "FinAccount.id" in text
        assert "code" in text
