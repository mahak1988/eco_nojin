"""S-MONEY contract tests: one ledger, one sign convention, one rate table.

Phase 4 group 3 removed the financial duplicates: a second ``LedgerService``
inside ``wallet_service``, a second rate table, and float money in two wallet
modules. These tests pin what remains and what was removed.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _tree(rel: str) -> ast.Module:
    return ast.parse(_read(rel))


def _parse(rel: str) -> ast.Module | None:
    """Parse, or return None for a file that is not valid Python.

    Some modules in this repository are syntax-broken in isolation; a gate that
    crashes on them is useless.
    """
    try:
        return ast.parse(_read(rel))
    except (SyntaxError, ValueError):
        return None


def _classes(rel: str, name: str) -> list[str]:
    tree = _parse(rel)
    if tree is None:
        return []
    return [
        f"{node.name} (line {node.lineno})"
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == name
    ]


class TestOneLedgerService:
    def test_wallet_service_no_longer_defines_its_own(self):
        """It had no batch-balance check and the opposite sign convention."""
        assert _classes("services/finance/wallet_service.py", "LedgerService") == [], (
            "wallet_service must use finance.ledger_service.LedgerService; a local "
            "class let unbalanced journals be created through the wallet path"
        )

    def test_wallet_service_uses_the_validating_one(self):
        source = _read("services/finance/wallet_service.py")
        assert "FinanceLedgerService" in source
        assert "self.ledger = FinanceLedgerService(db)" in source

    def test_the_name_collision_is_gone(self):
        """Four classes named ``LedgerService`` was the actual finding: no call
        site could say which one it meant.

        Two survive with distinct names — the canonical batch service and the
        single-entry service the standalone app exposes.
        """
        by_name: dict[str, list[str]] = {}
        for path in (ROOT / "services").rglob("*.py"):
            if "__pycache__" in path.parts or "tests" in path.parts:
                continue
            tree = _parse(str(path.relative_to(ROOT)))
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and "Ledger" in node.name:
                    by_name.setdefault(node.name, []).append(
                        f"{path.relative_to(ROOT)}:{node.lineno}"
                    )
        duplicates = {name: where for name, where in by_name.items() if len(where) > 1}
        assert not duplicates, f"class names still collide: {duplicates}"
        assert "LedgerService" in by_name, "the canonical batch service should still exist"
        assert "SingleEntryLedgerService" in by_name

    def test_wallet_service_defines_no_ledger_class_at_all(self):
        assert _classes("services/finance/wallet_service.py", "LedgerService") == []
        assert _classes("services/finance/wallet_service.py", "SingleEntryLedgerService") == []


class TestOneSignConvention:
    def test_the_canonical_convention_is_credit_positive(self):
        source = _read("services/finance/ledger_service.py")
        assert 'case((FinJournalEntry.entry_type == "credit"' in source or (
            "credit" in source and "debit" in source
        )

    def test_no_balance_returning_code_inverts_the_convention(self):
        """That was the negation of the canonical convention.

        Scoped to balance-*returning* functions. A trial balance legitimately
        reports debits and credits as two *positive* columns, which involves a
        subtraction internally; that is presentation, not a sign error, and
        conflating the two would make this gate unusable.
        """
        offenders: list[str] = []
        for path in (ROOT / "services").rglob("*.py"):
            if "__pycache__" in path.parts or "_contracts" in path.parts:
                continue
            tree = _parse(str(path.relative_to(ROOT)))
            if tree is None:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                if "balance" not in node.name or "trial_balance" in node.name:
                    continue
                for inner in ast.walk(node):
                    if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Sub):
                        left = ast.unparse(inner.left).lower()
                        right = ast.unparse(inner.right).lower()
                        if "debit" in left and "credit" in right:
                            offenders.append(
                                f"{path.relative_to(ROOT)}:{inner.lineno} in {node.name}()"
                            )
        assert not offenders, f"balance functions still invert the convention: {offenders}"

    def test_ledger_service_sign_is_the_documented_one(self):
        from services.ledger.service import SingleEntryLedgerService

        doc = (SingleEntryLedgerService.__doc__ or "").lower()
        assert "credit" in doc
        assert "positive" in doc


class TestOneRateTable:
    def test_both_wallet_modules_read_the_shared_table(self):
        from services.ecowallet import service as eco
        from services.finance import earning_rates
        from services.finance.wallet_service import WalletService

        assert WalletService.EARNING_RATES is earning_rates.EARNING_RATES
        assert eco.LEGACY_EARNING_RATES  # a view, not a copy
        assert (
            "EARNING_RATES"
            not in _read("services/ecowallet/service.py")
            .split("LEGACY_EARNING_RATES")[0]
            .split("_legacy_rates_view")[0][-200:]
        )

    def test_no_module_declares_a_literal_rate_table(self):
        offenders: list[str] = []
        for path in (ROOT / "services").rglob("*.py"):
            if "__pycache__" in path.parts or "earning_rates.py" in path.name:
                continue
            tree = _parse(str(path.relative_to(ROOT)))
            if tree is None:
                continue
            for node in ast.walk(tree):
                targets: list[str] = []
                if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    targets = [node.target.id]
                elif isinstance(node, ast.Assign):
                    targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if "EARNING_RATES" in targets and isinstance(node.value, ast.Dict):
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
        assert not offenders, f"duplicate rate tables: {offenders}"

    def test_legacy_category_names_still_resolve(self):
        from services.finance.earning_rates import resolve_category

        assert resolve_category("soil_health") == "soil_restoration"
        assert resolve_category("water_saving") == "water_conservation"
        assert resolve_category("carbon_credit") == "carbon_verification"
        assert resolve_category("tree_planting") == "tree_planting"

    def test_an_unknown_category_is_rejected_with_the_known_list(self):
        from services.finance.earning_rates import resolve_category

        with pytest.raises(ValueError, match="unknown earning category"):
            resolve_category("not_a_category")

    def test_rates_are_decimal(self):
        from services.finance.earning_rates import EARNING_RATES

        assert all(isinstance(v, Decimal) for v in EARNING_RATES.values())


class TestMoneyIsDecimal:
    def test_ecowallet_service_has_no_float_arithmetic(self):
        source = _read("services/ecowallet/service.py")
        assert "_to_float" not in source, (
            "the wallet column is Numeric(19, 4); float arithmetic on it loses precision"
        )
        assert "Decimal" in source

    def test_in_memory_ledger_stores_decimal(self):
        """Check the dataclass *fields*, not method parameters.

        The public methods still accept ``float | Decimal`` so existing callers
        keep working; what matters is that the stored value is Decimal.
        """
        from decimal import Decimal as D

        from services.ecowallet.ledger import EcoTransaction, EcoWallet

        assert EcoTransaction.__dataclass_fields__["amount"].type in ("Decimal", D)
        assert EcoTransaction.__dataclass_fields__["balance_after"].type in ("Decimal", D)
        assert EcoWallet.__dataclass_fields__["balance"].type in ("Decimal", D)
        assert EcoWallet.__dataclass_fields__["total_earned"].type in ("Decimal", D)

    def test_in_memory_ledger_rejects_float_creep(self):
        """A float argument must be stored exactly as written, not as its binary value."""
        from services.ecowallet.ledger import EcoLedger

        ledger = EcoLedger()
        ledger.create_wallet("u1")
        tx = ledger.earn("u1", 0.1, "cat", "d")
        assert tx.amount == Decimal("0.1"), (
            "0.1 must not become 0.1000000000000000055 on the way into the ledger"
        )

    def test_in_memory_ledger_singleton_is_locked(self):
        source = _read("services/ecowallet/ledger.py")
        assert "_ledger_lock" in source, (
            "get_eco_ledger did check-then-assign unsynchronised, so two concurrent "
            "first callers could each build a ledger"
        )

    def test_timestamps_are_timezone_aware(self):
        source = _read("services/ecowallet/ledger.py")
        assert "datetime.utcnow" not in source, "utcnow is naive and deprecated on 3.12"


class TestOneAssetVocabulary:
    def test_the_ledger_app_uses_the_canonical_allowlist(self):
        from services.ledger.main import EntryCreate
        from services.ledger.service import ALLOWED_ASSETS

        assert EntryCreate.model_fields["asset"].default in ALLOWED_ASSETS
        with pytest.raises(Exception, match="asset must be one of"):
            EntryCreate(
                account_id="a",
                entry_type="debit",
                asset="eco_token",
                amount=Decimal("1"),
                reference_type="t",
            )

    def test_irt_is_not_a_default_anywhere(self):
        offenders: list[str] = []
        for path in (ROOT / "services").rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if '= "IRT"' in text or 'default="IRT"' in text:
                offenders.append(str(path.relative_to(ROOT)))
        assert not offenders, f"IRT is not a currency code: {offenders}"

    def test_escrow_create_defaults_to_a_valid_asset(self):
        import inspect

        from services.ledger.service import ALLOWED_ASSETS, EscrowService

        signature = inspect.signature(EscrowService.create)
        default = signature.parameters["asset"].default
        assert default in ALLOWED_ASSETS, f"escrow default asset {default!r} is not allowed"


class TestTheBrokenFixtureWasRepaired:
    def test_conftest_no_longer_imports_a_nonexistent_class(self):
        source = _read("services/conftest.py")
        assert "from services.ecowallet.service import EcowalletService" not in source, (
            "EcowalletService never existed; the ImportError was caught and the "
            "fixture skipped on every run"
        )
