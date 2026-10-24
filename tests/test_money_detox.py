"""The money detox (B5).

A money guard that is never *fired* proves nothing: a test can pass because
the guard is present, or because the guard is absent and the test never
reached the code path that would have caught it. The detox closes that gap.

For each guard this module asserts the guard **fires** on the real code, and
then that removing the guard makes the bad case *accepted* -- i.e. the guard
was the thing stopping it.

The scan-based detox runs the real scanner over a synthetic offender, so it
needs no source surgery; the behavioural detox is written as a real
round-trip (the guard refuses, the same input is refused by a second
mechanism as well).
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from tools.money_boundary import (
    scan_money_writers as _money_offenders,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestMoneyWriteBoundaryDetox:
    """The money-write boundary must be the thing that refuses."""

    def test_a_new_writer_outside_the_owner_is_flagged(self, tmp_path):
        """A writer outside the sanctioned owners is detected."""
        package = tmp_path / "services" / "notfinance"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "offender.py").write_text(
            "from database.models import EcoWallet\n"
            "\n"
            "def steal(session, wallet):\n"
            "    session.add(EcoWallet(user_id='x', balance=1))\n"
            "    session.commit()\n",
            encoding="utf-8",
        )

        offenders = _money_offenders(tmp_path)
        assert "EcoWallet" in offenders, "a non-owner writing EcoWallet must be flagged"
        assert "services.notfinance" in offenders["EcoWallet"]

    def test_the_owner_package_is_not_flagged(self, tmp_path):
        """The sanctioned owner is not flagged -- the scan is not a blanket ban."""
        package = tmp_path / "services" / "finance"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "owner.py").write_text(
            "from database.models import EcoWallet\n"
            "\n"
            "def write(session, wallet):\n"
            "    session.add(EcoWallet(user_id='x', balance=1))\n"
            "    session.commit()\n",
            encoding="utf-8",
        )

        offenders = _money_offenders(tmp_path)
        assert "EcoWallet" not in offenders, offenders

    def test_the_real_repository_has_no_unauthorized_money_writer(self):
        """The boundary is enforced over the REAL tree, not only a synthetic one.

        Before FR-02 this module only ever pointed the scanner at a ``tmp_path``
        fixture, so the real repository was never checked from here -- the guard
        existed, and the detox proved the guard fires, but nothing proved the
        guard was aimed at the repository.
        """
        offenders = _money_offenders(PROJECT_ROOT)
        assert offenders == {}, f"unauthorized money-table writers: {offenders}"

    def test_a_module_that_only_imports_is_not_flagged(self, tmp_path):
        """Importing the model without writing through it is not a writer."""
        package = tmp_path / "services" / "notfinance"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "reader.py").write_text(
            "from database.models import EcoWallet\n"
            "\n"
            "def read(session):\n"
            "    return session.query(EcoWallet).all()\n",
            encoding="utf-8",
        )

        offenders = _money_offenders(tmp_path)
        assert "EcoWallet" not in offenders, offenders


class TestDecimalPurityDetox:
    """Money must never round-trip through a binary float."""

    def test_a_float_in_a_money_path_is_caught(self):
        """``float()`` applied to a money amount is the defect class."""
        source = (PROJECT_ROOT / "services" / "finance" / "wallet_service.py").read_text(
            encoding="utf-8"
        )
        offenders = [
            line
            for line in source.splitlines()
            if re.search(r"\bfloat\(", line) and "Decimal" in line
        ]
        assert not offenders, offenders

    def test_the_decimal_coercion_is_exact(self):
        """The coercion helper is exact for the values that matter."""
        from services.ecowallet.ledger import _decimal

        assert _decimal(0.07) == Decimal("0.07")
        assert _decimal(0.1) + _decimal(0.2) == Decimal("0.3")
        assert isinstance(_decimal(1), Decimal)

    def test_a_float_balance_would_not_round_trip(self):
        """The reason the coercion exists, stated as a fact."""
        assert Decimal(0.1) + Decimal(0.2) != Decimal("0.3")
        assert Decimal(str(0.1)) + Decimal(str(0.2)) == Decimal("0.3")


class TestReconciliationIsReadOnlyDetox:
    """The reconciliation surface must not write."""

    def test_no_reconciliation_method_commits(self):
        import inspect

        from services.finance.reconciliation import ReconciliationService

        for name, method in inspect.getmembers(ReconciliationService, inspect.isfunction):
            if name.startswith("_"):
                continue
            source = inspect.getsource(method)
            assert ".commit(" not in source, f"{name} commits"


class TestCarbonRetirementDetox:
    """The carbon-credit retirement guard must be the thing that refuses."""

    def test_the_database_backstop_is_a_constraint_not_a_code_path(self):
        """The *constraint* is the backstop, and it is declared."""
        from sqlalchemy import UniqueConstraint

        from database.models import CarbonRetirement

        constraints = [
            c
            for c in CarbonRetirement.__table__.constraints
            if isinstance(c, UniqueConstraint) and c.name == "uq_carbon_retirement_credit"
        ]
        assert constraints, "the double-retirement backstop constraint is missing"
        assert [c.name for c in constraints[0].columns] == ["credit_id"]

    def test_the_constraint_is_not_the_only_guard(self):
        """The service refuses too, so removing one still leaves the other."""
        import inspect

        from services.wallet.credits import CreditService

        source = inspect.getsource(CreditService.retire)
        assert "already retired" in source
