"""Tests for Phase 9 — Carbon Credits + CBDC providers."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from services.api_gateway.exceptions import EcoNojinException
from services.finance.carbon_cbdc import (
    CarbonCreditProvider,
    CarbonSwapProvider,
    CarbonTokenProvider,
    CBDCProvider,
)

pytestmark = pytest.mark.asyncio


def _unique_holder() -> str:
    return f"user-{uuid.uuid4().hex[:10]}"


class TestCarbonCreditProvider:
    """Tests for CarbonCreditProvider using the in-process CarbonRegistry."""

    @pytest.fixture
    def provider(self, db_session, monkeypatch):
        monkeypatch.setenv("CARBON_CREDIT_SOURCE", "registry")
        return CarbonCreditProvider(db_session)

    async def test_issue_credit_registry(self, provider):
        """Issue a carbon credit via the in-process registry."""
        result = await provider.issue(
            project_id="PROJ-001",
            amount=Decimal("100.50"),
            holder_id=_unique_holder(),
            metadata={"serial": "VCS-001", "vintage_year": 2024},
        )
        assert result.status == "active"
        assert result.amount == Decimal("100.50")
        assert result.holder_id is not None

    async def test_get_balance_empty(self, provider):
        """An unknown holder has zero balance."""
        balance = await provider.get_balance(_unique_holder())
        assert balance == Decimal("0")

    async def test_get_balance_after_issue(self, provider):
        """Balance reflects issued credits."""
        holder = _unique_holder()
        await provider.issue(
            project_id="PROJ-001",
            amount=Decimal("100"),
            holder_id=holder,
        )
        await provider.issue(
            project_id="PROJ-002",
            amount=Decimal("50"),
            holder_id=holder,
        )
        balance = await provider.get_balance(holder)
        assert balance == Decimal("150")

    async def test_retire_credit(self, provider):
        """Retiring a credit returns success."""
        holder = _unique_holder()
        issued = await provider.issue(
            project_id="PROJ-001",
            amount=Decimal("100"),
            holder_id=holder,
        )
        result = await provider.retire(
            credit_id=issued.credit_id,
            owner=holder,
            justification="offset scope 1 emissions",
        )
        assert result.status == "retired"
        assert result.retired_amount == Decimal("100")

    async def test_retire_non_owned_raises(self, provider):
        """Retiring a credit held by another party raises 403."""
        holder_a = _unique_holder()
        holder_b = _unique_holder()
        issued = await provider.issue(
            project_id="PROJ-001",
            amount=Decimal("100"),
            holder_id=holder_a,
        )
        with pytest.raises(Exception):
            await provider.retire(
                credit_id=issued.credit_id,
                owner=holder_b,
            )


class TestCBDCProvider:
    """Tests for CBDCProvider — fail-closed when unconfigured."""

    @pytest.fixture
    def provider(self, db_session):
        return CBDCProvider(db_session)

    async def test_transfer_fail_closed_without_endpoint(self, provider):
        """CBDC transfer raises 503 when CBDC_ENDPOINT_URL is unset."""
        with pytest.raises(EcoNojinException) as exc_info:
            await provider.transfer(
                from_address="addr-1",
                to_address="addr-2",
                amount=Decimal("100.00"),
                currency="USD",
            )
        assert exc_info.value.code == "CBDC_NOT_CONFIGURED"
        assert exc_info.value.status_code == 503

    async def test_get_balance_fail_closed_without_endpoint(self, provider):
        """CBDC balance raises 503 when CBDC_ENDPOINT_URL is unset."""
        with pytest.raises(EcoNojinException) as exc_info:
            await provider.get_balance("addr-1", "USD")
        assert exc_info.value.code == "CBDC_NOT_CONFIGURED"

    async def test_transfer_with_endpoint(self, provider, db_session, monkeypatch):
        """CBDC transfer succeeds when CBDC_ENDPOINT_URL is set."""
        monkeypatch.setenv("CBDC_ENDPOINT_URL", "https://cbdc.test")
        result = await provider.transfer(
            from_address="addr-1",
            to_address="addr-2",
            amount=Decimal("100.00"),
            currency="USD",
        )
        assert result.status == "succeeded"
        assert result.amount == Decimal("100.00")
        assert result.from_address == "addr-1"
        assert result.to_address == "addr-2"
        assert result.transaction_id.startswith("CBDC-")

    async def test_transfer_idempotent(self, provider, db_session, monkeypatch):
        """A second transfer with the same idempotency key returns the prior intent."""
        monkeypatch.setenv("CBDC_ENDPOINT_URL", "https://cbdc.test")
        idem_key = str(uuid.uuid4())
        await provider.transfer(
            from_address="addr-1",
            to_address="addr-2",
            amount=Decimal("100.00"),
            currency="USD",
            idempotency_key=idem_key,
        )
        second = await provider.transfer(
            from_address="addr-1",
            to_address="addr-2",
            amount=Decimal("200.00"),
            currency="USD",
            idempotency_key=idem_key,
        )
        # Second call reuses prior intent; amount stays 100, status is processing
        assert second.status == "processing"
        assert second.amount == Decimal("100.00")


class TestCarbonSwapProvider:
    """Tests for CarbonSwapProvider."""

    @pytest.fixture
    def provider(self, db_session):
        return CarbonSwapProvider(db_session)

    async def test_quote(self, provider):
        """Quote returns the USD value of carbon credits."""
        result = await provider.quote(
            credit_amount=Decimal("100"),
            target_currency="USD",
        )
        assert result["target_currency"] == "USD"
        assert Decimal(result["usd_value"]) == Decimal("1000")
        assert Decimal(result["credit_amount"]) == Decimal("100")

    async def test_quote_custom_rate(self, provider, monkeypatch):
        """Quote uses CARBON_SWAP_RATE if set."""
        monkeypatch.setenv("CARBON_SWAP_RATE", "15")
        provider2 = CarbonSwapProvider(provider.db)
        result = await provider2.quote(
            credit_amount=Decimal("100"),
            target_currency="USD",
        )
        assert Decimal(result["usd_value"]) == Decimal("1500")

    async def test_quote_zero_rate_fail_closed(self, provider, monkeypatch):
        """A zero swap rate raises 503."""
        monkeypatch.setenv("CARBON_SWAP_RATE", "0")
        provider2 = CarbonSwapProvider(provider.db)
        with pytest.raises(EcoNojinException) as exc_info:
            await provider2.quote(credit_amount=Decimal("100"), target_currency="USD")
        assert exc_info.value.code == "CARBON_SWAP_RATE_NOT_CONFIGURED"


class TestCarbonTokenProvider:
    """Tests for CarbonTokenProvider (simulation mode)."""

    @pytest.fixture
    def provider(self, db_session):
        return CarbonTokenProvider(db_session)

    async def test_mint_falls_back_to_simulation(self, provider):
        """Mint succeeds via in-memory simulation when no RPC is configured."""
        result = await provider.mint(
            project_id="PROJ-001",
            amount=Decimal("100"),
            recipient_address="0xabc",
            credit_type="VCS",
        )
        assert result["status"] == "issued"
        assert "token_id" in result
        assert Decimal(str(result["amount_tonnes"])) == Decimal("100")

    async def test_transfer_token(self, provider):
        """Transfer a tokenized credit."""
        minted = await provider.mint(
            project_id="PROJ-001",
            amount=Decimal("100"),
            recipient_address="0xabc",
        )
        result = await provider.transfer_token(
            token_id=minted["token_id"],
            from_address="0xabc",
            to_address="0xdef",
        )
        assert result["status"] == "transferred"
        assert result["from"] == "0xabc"
        assert result["to"] == "0xdef"

    async def test_balance(self, provider):
        """Token balance returns the issued amount in base units."""
        await provider.mint(
            project_id="PROJ-001",
            amount=Decimal("100"),
            recipient_address="0xabc",
        )
        result = await provider.balance("0xabc")
        assert result["owner_address"] == "0xabc"
        assert result["token_type"] == "CARBON_tCO2e"
        assert result["token_balance"] == 100000

    async def test_burn(self, provider):
        """Burn (retire) a tokenized credit."""
        minted = await provider.mint(
            project_id="PROJ-001",
            amount=Decimal("100"),
            recipient_address="0xabc",
        )
        result = await provider.burn(
            token_id=minted["token_id"],
            owner_address="0xabc",
            justification="carbon offset",
        )
        assert result["status"] == "retired"
        assert result["justification"] == "carbon offset"

    async def test_transfer_non_owner_raises(self, provider):
        """Transferring from the wrong owner raises."""
        minted = await provider.mint(
            project_id="PROJ-001",
            amount=Decimal("100"),
            recipient_address="0xabc",
        )
        with pytest.raises(ValueError):
            await provider.transfer_token(
                token_id=minted["token_id"],
                from_address="0xwrong",
                to_address="0xdef",
            )

    async def test_burn_nonexistent_raises(self, provider):
        """Burning a nonexistent token raises."""
        with pytest.raises(ValueError):
            await provider.burn(
                token_id="NONEXISTENT",
                owner_address="0xabc",
                justification="test",
            )
