"""Phase 4 group 4 — marketplace pricing and AML risk ordering.

Two defects pinned here:

* ``MarketplaceService.create_order`` computed the order total, the platform
  fee and the landscape fee from a ``price`` supplied in the request body. A
  buyer could post ``price: 1`` for a 350,000 IRR product and the order would
  be created at that number.
* ``RiskLevel`` was a string enum compared with ``>``, which orders
  ``critical < high < low < medium``. A CRITICAL finding — a sanctioned
  jurisdiction, the exact case the AML screen exists for — was downgraded to
  LOW, and MEDIUM could never win over HIGH.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


class TestServerIsTheOnlyPricingAuthority:
    def _read(self) -> str:
        return (ROOT / "services" / "marketplace" / "service.py").read_text(encoding="utf-8")

    def test_subtotal_is_not_built_from_a_request_supplied_price(self):
        """Regression: `subtotal += Decimal(str(item["price"])) * item["quantity"]`."""
        source = self._read()
        body = source.split("async def create_order", 1)[-1].split("async def ", 1)[0]
        assert 'Decimal(str(item["price"]))' not in body, (
            "the order subtotal must come from the catalogue, not the request body"
        )
        assert "catalogue_price" in body

    def test_the_product_is_looked_up_before_pricing(self):
        source = self._read()
        assert "_get_product_for_pricing" in source
        assert "await self.db.get(MarketplaceProduct" in source

    def test_a_claimed_price_that_disagrees_is_refused(self):
        source = self._read()
        body = source.split("async def create_order", 1)[-1].split("async def ", 1)[0]
        assert "refresh the cart" in body, (
            "a stale or tampered client price must be reported, not silently overwritten"
        )

    def test_an_unpriceable_product_raises(self):
        source = self._read()
        body = source.split("async def _get_product_for_pricing", 1)[-1].split("async def ", 1)[0]
        assert "product not found" in body
        assert "no catalogue price" in body

    def test_no_other_order_path_reads_a_client_price(self):
        offenders: list[str] = []
        for path in (ROOT / "services" / "marketplace").rglob("*.py"):
            if "__pycache__" in path.parts or "tests" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            except (SyntaxError, ValueError):
                continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Subscript)
                and isinstance(node.slice, ast.Constant)
                and node.slice.value == "price"
            ):
                source = ast.unparse(node)
                if "item" in source or "payload" in source or "body" in source:
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
        assert not offenders, f"client-supplied price still read: {offenders}"


class TestRiskLevelIsOrderedBySeverity:
    def test_critical_outranks_everything(self):
        from services.carbon.compliance.kyc_aml import RiskLevel

        assert RiskLevel.CRITICAL > RiskLevel.HIGH
        assert RiskLevel.CRITICAL > RiskLevel.MEDIUM
        assert RiskLevel.CRITICAL > RiskLevel.LOW

    def test_the_ordering_is_the_intended_one(self):
        from services.carbon.compliance.kyc_aml import RiskLevel

        ordered = sorted(RiskLevel, key=lambda r: r.value)
        assert [r.label for r in ordered] == ["low", "medium", "high", "critical"]

    def test_the_old_string_ordering_would_have_been_wrong(self):
        """Documents *why* the enum changed, so it is not reverted.

        String order is ``critical < high < low < medium``, so the three
        comparisons the aggregation performed were all wrong: CRITICAL lost to
        both HIGH and LOW, and MEDIUM beat HIGH.
        """
        levels = ["low", "medium", "high", "critical"]
        assert max(levels) == "medium", (
            "string comparison ranks MEDIUM as the worst level, which is the bug"
        )
        assert ("critical" > "high") is False, "CRITICAL lost to HIGH"
        assert ("critical" > "low") is False, "CRITICAL lost to LOW"
        assert ("medium" > "high") is True, "MEDIUM was ranked above HIGH"

    def test_labels_survive_for_the_api(self):
        from services.carbon.compliance.kyc_aml import RiskLevel

        assert RiskLevel.LOW.label == "low"
        assert RiskLevel.CRITICAL.label == "critical"
        assert RiskLevel.from_label("critical") is RiskLevel.CRITICAL
        assert RiskLevel.from_label(4) is RiskLevel.CRITICAL

    def test_an_unknown_label_is_rejected(self):
        from services.carbon.compliance.kyc_aml import RiskLevel

        with pytest.raises(ValueError, match="unknown risk level"):
            RiskLevel.from_label("catastrophic")

    def test_the_aggregation_compares_members_not_strings(self):
        source = (ROOT / "services" / "carbon" / "compliance" / "kyc_aml.py").read_text(
            encoding="utf-8"
        )
        body = source.split("def run_aml_checks", 1)[-1].split("def ", 1)[0]
        assert "check.risk_level > max_risk" in body
        assert "check.risk_level.value > max_risk.value" not in body

    def test_the_router_serialises_the_label_not_the_rank(self):
        source = (ROOT / "services" / "api_gateway" / "routers" / "compliance.py").read_text(
            encoding="utf-8"
        )
        assert "risk_level.value" not in source, (
            ".value is now the integer rank; the API must emit the label"
        )
        assert "risk_level.label" in source


class TestPriceArithmeticStaysDecimal:
    def test_money_is_decimal_in_the_order_path(self):
        source = (ROOT / "services" / "marketplace" / "service.py").read_text(encoding="utf-8")
        body = source.split("async def create_order", 1)[-1].split("async def ", 1)[0]
        assert "Decimal" in body
        assert "float(" not in body

    def test_the_catalogue_price_is_coerced_from_numeric(self):
        """product.price is Numeric(12,2); reading it yields a Decimal."""
        source = (ROOT / "services" / "marketplace" / "service.py").read_text(encoding="utf-8")
        assert "Decimal(str(product.price))" in source
        assert isinstance(Decimal("1.00"), Decimal)
