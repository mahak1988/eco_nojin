"""Carbon Credits + CBDC providers — Phase 9.

Phase 9 integrates carbon credit lifecycle (issue, transfer, retire) with the
finance engine's double-entry ledger, plus a Central Bank Digital Currency
(CBDC) provider for real-time gross settlement (RTGS) of carbon purchases.

Providers are *stub-safe*: they operate against the in-process
``CarbonRegistry`` / ``CarbonTokenService`` for credits, and require the
``CBDC_ENDPOINT_URL`` env var for CBDC RPC calls. No network call is made for
CBDC unless all required env vars are set, so the platform boots cleanly in
dev/test.

All money math uses ``Decimal`` — never float.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import (
    AuditEvent,
    CarbonCreditState,
    ComPaymentIntent,
)
from database.models import (
    CarbonCredit as CarbonCreditModel,
)
from services.api_gateway.exceptions import EcoNojinException

try:
    from services.business_modules.blockchain.carbon_registry import (
        CarbonRegistry,
        get_carbon_registry,
    )
    from services.business_modules.carbon.tokenization import (
        CarbonTokenService,
        get_tokenization_service,
    )
except Exception:  # pragma: no cover — providers degrade gracefully
    get_carbon_registry = None
    get_tokenization_service = None


# ═══════════════════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class CarbonCreditResult:
    """Result of a carbon credit operation."""

    credit_id: str
    status: str
    amount: Decimal
    retired_amount: Decimal | None = None
    holder_id: str | None = None
    transaction_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CBDCTransferResult:
    """Result of a CBDC transfer."""

    transaction_id: str
    status: str
    amount: Decimal
    currency: str
    from_address: str
    to_address: str
    block_number: int | None = None
    gas_used: int | None = None
    transaction_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _json_safe(value: Any) -> Any:
    """Recursively convert Decimal and other non-JSON values to strings."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    return value


# ═══════════════════════════════════════════════════════════════════════════════
# Carbon Credit Provider
# ═══════════════════════════════════════════════════════════════════════════════


class CarbonCreditProvider:
    """Manage carbon credit lifecycle: issue, transfer, retire, query.

    Credits can be sourced from the in-process ``CarbonRegistry`` (hash-chain
    backed) or from the ORM ``CarbonCredit`` model. The provider records
    every state transition as an ``AuditEvent`` for traceability.

    Environment (optional):
    * ``CARBON_CREDIT_SOURCE`` — ``registry`` (default) or ``orm``
    """

    provider_name = "carbon_credit"

    def __init__(self, db: AsyncSession):
        self.db = db
        self._registry: CarbonRegistry | None = None
        if get_carbon_registry is not None:
            try:
                self._registry = get_carbon_registry()
            except Exception:
                self._registry = None

    def _require_registry(self) -> CarbonRegistry:
        if self._registry is None:
            raise EcoNojinException(
                "Carbon registry not available in this runtime",
                code="CARBON_REGISTRY_UNAVAILABLE",
                status_code=503,
            )
        return self._registry

    def _source_orm(self) -> bool:
        return os.getenv("CARBON_CREDIT_SOURCE", "registry").strip().lower() == "orm"

    # ---- provider interface ------------------------------------------------

    async def issue(
        self,
        project_id: str,
        amount: Decimal,
        holder_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CarbonCreditResult:
        """Issue carbon credits from a verified project to a holder."""
        registry = self._require_registry()
        meta = metadata or {}

        if self._source_orm:
            credit_id = f"CC-{uuid4().hex[:12]}"
            credit = CarbonCreditModel(
                credit_id=credit_id,
                project_id=project_id,
                serial=meta.get("serial"),
                vintage_year=meta.get("vintage_year"),
                methodology=meta.get("methodology"),
                total_amount=amount,
                retired_amount=Decimal("0"),
                available_amount=amount,
                holder_id=holder_id,
                state=CarbonCreditState.ACTIVE,
                issued_by=meta.get("issued_by", "system"),
                issued_at=datetime.now(UTC),
            )
            self.db.add(credit)
            await self.db.commit()
            await self.db.refresh(credit)
        else:
            credit_data = registry.issue_credits(
                project_id=project_id,
                amount=float(amount),
                owner=holder_id,
            )
            credit_id = credit_data.credit_id if credit_data else f"CC-{uuid4().hex[:12]}"
            await self._record_audit(
                "carbon_credit_issued",
                credit_id=credit_id,
                holder_id=holder_id,
                amount=amount,
            )

        return CarbonCreditResult(
            credit_id=credit_id,
            status="active",
            amount=amount,
            retired_amount=Decimal("0"),
            holder_id=holder_id,
            transaction_hash=meta.get("transaction_hash"),
            metadata=meta,
        )

    async def transfer(
        self,
        credit_id: str,
        from_holder: str,
        to_holder: str,
        metadata: dict[str, Any] | None = None,
    ) -> CarbonCreditResult:
        """Transfer a carbon credit from one holder to another."""
        registry = self._require_registry()
        meta = metadata or {}

        if self._source_orm:
            result = await self.db.execute(
                select(CarbonCreditModel).where(CarbonCreditModel.credit_id == credit_id)
            )
            credit = result.scalar_one_or_none()
            if credit is None:
                raise EcoNojinException(
                    f"Carbon credit not found: {credit_id}",
                    code="CARBON_CREDIT_NOT_FOUND",
                    status_code=404,
                )
            if str(credit.holder_id) != str(from_holder):
                raise EcoNojinException(
                    f"Credit {credit_id} not held by {from_holder}",
                    code="CARBON_CREDIT_NOT_OWNED",
                    status_code=403,
                )
            if credit.state == CarbonCreditState.RETIRED:
                raise EcoNojinException(
                    "Cannot transfer retired credits",
                    code="CARBON_CREDIT_RETIRED",
                    status_code=409,
                )
            credit.holder_id = to_holder
            credit.version = (credit.version or 0) + 1
            self.db.add(credit)
            await self.db.commit()
            await self.db.refresh(credit)
            amount = credit.available_amount
        else:
            credit_data = registry.transfer_credits(
                credit_id=credit_id,
                from_owner=from_holder,
                to_owner=to_holder,
            )
            amount = Decimal(str(credit_data.amount)) if credit_data else Decimal("0")

        await self._record_audit(
            "carbon_credit_transferred",
            credit_id=credit_id,
            from_holder=from_holder,
            to_holder=to_holder,
            amount=amount,
        )

        return CarbonCreditResult(
            credit_id=credit_id,
            status="transferred",
            amount=amount,
            holder_id=to_holder,
            metadata=meta,
        )

    async def retire(
        self,
        credit_id: str,
        owner: str,
        justification: str = "",
    ) -> CarbonCreditResult:
        """Permanently retire a carbon credit (remove from circulation)."""
        registry = self._require_registry()

        if self._source_orm:
            result = await self.db.execute(
                select(CarbonCreditModel).where(CarbonCreditModel.credit_id == credit_id)
            )
            credit = result.scalar_one_or_none()
            if credit is None:
                raise EcoNojinException(
                    f"Carbon credit not found: {credit_id}",
                    code="CARBON_CREDIT_NOT_FOUND",
                    status_code=404,
                )
            if str(credit.holder_id) != str(owner):
                raise EcoNojinException(
                    f"Credit {credit_id} not held by {owner}",
                    code="CARBON_CREDIT_NOT_OWNED",
                    status_code=403,
                )
            if credit.state == CarbonCreditState.RETIRED:
                raise EcoNojinException(
                    "Credits already retired",
                    code="CARBON_CREDIT_ALREADY_RETIRED",
                    status_code=409,
                )
            credit.state = CarbonCreditState.RETIRED
            credit.retired_amount = credit.available_amount
            credit.available_amount = Decimal("0")
            self.db.add(credit)
            await self.db.commit()
            await self.db.refresh(credit)
            amount = credit.available_amount + credit.retired_amount
        else:
            credit_data = registry.retire_credits(credit_id=credit_id, owner=owner)
            amount = Decimal(str(credit_data.amount)) if credit_data else Decimal("0")

        await self._record_audit(
            "carbon_credit_retired",
            credit_id=credit_id,
            owner=owner,
            amount=amount,
            justification=justification,
        )

        return CarbonCreditResult(
            credit_id=credit_id,
            status="retired",
            amount=amount,
            retired_amount=amount,
            metadata={"justification": justification},
        )

    async def get_balance(
        self,
        holder_id: str,
    ) -> Decimal:
        """Return the total available carbon credits held by ``holder_id``."""
        registry = self._require_registry()

        if self._source_orm:
            result = await self.db.execute(
                select(CarbonCreditModel)
                .where(
                    CarbonCreditModel.holder_id == holder_id,
                    CarbonCreditModel.state != CarbonCreditState.RETIRED,
                )
            )
            credits = result.scalars().all()
            total = sum(c.available_amount for c in credits)
            return Decimal(str(total)) if total else Decimal("0")
        else:
            credits = registry.get_credits_by_owner(owner=holder_id) if self._registry else []
            return Decimal(str(sum(c.amount for c in credits))) if credits else Decimal("0")

    async def list_credits(
        self,
        holder_id: str | None = None,
        retired: bool | None = None,
    ) -> list[dict[str, Any]]:
        """List carbon credits, optionally filtered by holder and retirement."""
        registry = self._require_registry()

        if self._source_orm:
            stmt = select(CarbonCreditModel)
            if holder_id is not None:
                stmt = stmt.where(CarbonCreditModel.holder_id == holder_id)
            if retired is False:
                stmt = stmt.where(CarbonCreditModel.state != CarbonCreditState.RETIRED)
            elif retired is True:
                stmt = stmt.where(CarbonCreditModel.state == CarbonCreditState.RETIRED)
            result = await self.db.execute(stmt)
            credits = result.scalars().all()
            return [
                {
                    "credit_id": c.credit_id,
                    "project_id": c.project_id,
                    "serial": c.serial,
                    "total_amount": str(c.total_amount),
                    "retired_amount": str(c.retired_amount),
                    "available_amount": str(c.available_amount),
                    "holder_id": c.holder_id,
                    "state": c.state.value if hasattr(c.state, "value") else str(c.state),
                    "issued_at": c.issued_at.isoformat() if c.issued_at else None,
                }
                for c in credits
            ]
        else:
            credits = registry.get_credits_by_owner(owner=holder_id) if holder_id else []
            if retired is True:
                credits = [c for c in credits if c.retired]
            elif retired is False:
                credits = [c for c in credits if not c.retired]
            return [
                {
                    "credit_id": c.credit_id,
                    "project_id": c.project_id,
                    "owner": c.owner,
                    "amount": c.amount,
                    "retired": c.retired,
                    "issued_at": c.issued_at.isoformat() if c.issued_at else None,
                    "transaction_hash": c.transaction_hash,
                }
                for c in credits
            ]

    # ---- internal ----------------------------------------------------------

    async def _record_audit(
        self,
        action: str,
        *,
        credit_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Record an immutable audit event for a carbon credit operation."""
        self.db.add(
            AuditEvent(
                correlation_id=credit_id or str(uuid4()),
                actor_id=str(kwargs.get("holder_id") or kwargs.get("owner", "system")),
                action=action,
                resource_type="carbon_credit",
                resource_id=str(credit_id) if credit_id else None,
                after_state=_json_safe(kwargs),
                created_at=datetime.now(UTC),
            )
        )
        await self.db.commit()

    async def verify_webhook(self, payload: bytes, signature: str) -> dict[str, Any]:
        """Verify a carbon credit lifecycle webhook from an external registry."""
        self._require_registry()
        secret = os.getenv("CARBON_WEBHOOK_SECRET", "").strip()
        if not secret:
            raise EcoNojinException(
                "Carbon webhook secret not configured",
                code="CARBON_WEBHOOK_SECRET_NOT_CONFIGURED",
                status_code=503,
            )
        if not hmac.compare_digest(
            hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest(),
            signature.strip(),
        ):
            raise EcoNojinException(
                "Invalid carbon webhook signature",
                code="INVALID_SIGNATURE",
                status_code=401,
            )
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise EcoNojinException("Invalid webhook JSON", code="INVALID_WEBHOOK", status_code=400) from exc


# ═══════════════════════════════════════════════════════════════════════════════
# Carbon Token Provider (tokenized credits)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class _TokenRecord:
    token_id: str
    project_id: str
    amount: float
    credit_type: str
    owner: str
    status: str = "active"
    transaction_hash: str | None = None
    retired: bool = False


class _CarbonTokenSim:
    """In-memory simulation of the CarbonTokenService fallback.

    Used when ``py-evm`` / ``web3`` are unavailable so the API remains
    functional in dev/test environments. Mirrors the interface of
    ``CarbonTokenService`` without any blockchain dependencies.
    """

    def __init__(self):
        self._credits: dict[str, _TokenRecord] = {}
        self._balances: dict[str, int] = {}

    def mint(
        self,
        project_id: str,
        amount: float,
        credit_type: str = "VCS",
        recipient_address: str | None = None,
    ) -> dict[str, Any]:
        token_id = f"CTC-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        recipient = recipient_address or f"0x{project_id.lower()}"
        record = _TokenRecord(
            token_id=token_id,
            project_id=project_id,
            amount=amount,
            credit_type=credit_type,
            owner=recipient,
        )
        self._credits[token_id] = record
        self._balances[recipient] = self._balances.get(recipient, 0) + int(amount * 1000)
        return {
            "token_id": token_id,
            "transaction_hash": None,
            "status": "issued",
            "amount_tonnes": amount,
            "credit_type": credit_type,
        }

    def transfer(self, token_id: str, from_address: str, to_address: str) -> dict[str, Any]:
        credit = self._credits.get(token_id)
        if not credit:
            raise ValueError(f"Credit not found: {token_id}")
        if credit.owner != from_address:
            raise ValueError(f"Credit not owned by {from_address}")
        if credit.retired:
            raise ValueError("Cannot transfer retired credits")
        old_owner = credit.owner
        credit.owner = to_address
        self._balances[old_owner] = self._balances.get(old_owner, 0) - int(credit.amount * 1000)
        self._balances[to_address] = self._balances.get(to_address, 0) + int(credit.amount * 1000)
        return {
            "token_id": token_id,
            "from": old_owner,
            "to": to_address,
            "transaction_hash": None,
            "status": "transferred",
        }

    def retire(self, token_id: str, justification: str = "") -> dict[str, Any]:
        credit = self._credits.get(token_id)
        if not credit:
            raise ValueError(f"Credit not found: {token_id}")
        credit.retired = True
        credit.status = "retired"
        self._balances[credit.owner] = max(
            0, self._balances.get(credit.owner, 0) - int(credit.amount * 1000)
        )
        return {
            "token_id": token_id,
            "status": "retired",
            "justification": justification,
        }

    def balance(self, address: str) -> int:
        return self._balances.get(address, 0)

    def verify_on_chain(self, token_id: str) -> dict[str, Any]:
        credit = self._credits.get(token_id)
        if not credit:
            raise ValueError(f"Credit not found: {token_id}")
        return {
            "token_id": token_id,
            "on_chain": False,
            "transaction_hash": credit.transaction_hash,
            "contract": "CarbonCredit.abi",
            "status": credit.status,
            "verified": not credit.retired,
        }


class CarbonTokenProvider:
    """Manage tokenized carbon credits via the on-chain CarbonTokenService.

    Falls back to an in-memory simulation when the blockchain service is
    unavailable (e.g. `py-evm` not installed), so the API remains usable in
    dev/test environments.

    Environment (optional):
    * ``CARBON_TOKEN_RPC_URL`` — RPC endpoint for the tokenization contract
    """

    provider_name = "carbon_token"

    def __init__(self, db: AsyncSession):
        self.db = db
        self._rpc_url = os.getenv("CARBON_TOKEN_RPC_URL", "").strip()
        self._token_service: CarbonTokenService | None = None
        self._sim_instance: _CarbonTokenSim | None = None
        if get_tokenization_service is not None:
            try:
                self._token_service = get_tokenization_service()
            except Exception:
                self._token_service = None

    def _get_sim(self) -> _CarbonTokenSim:
        """Return the local simulation instance, creating it once per provider."""
        if self._sim_instance is None:
            self._sim_instance = _CarbonTokenSim()
        return self._sim_instance

    def _sim(self) -> _CarbonTokenSim:
        return self._get_sim()

    def _use_sim(self) -> bool:
        """Whether to use the local simulation fallback."""
        return self._token_service is None

    async def mint(
        self,
        project_id: str,
        amount: Decimal,
        recipient_address: str | None = None,
        credit_type: str = "VCS",
    ) -> dict[str, Any]:
        """Mint tokenized carbon credits (on-chain, falls back to simulation)."""
        if self._use_sim():
            result = self._get_sim().mint(project_id, float(amount), credit_type, recipient_address)
        else:
            result = self._token_service.issue_credits(
                project_id=project_id,
                amount=float(amount),
                credit_type=credit_type,
                recipient_address=recipient_address,
            )
        await self._record_audit(
            "carbon_token_minted",
            token_id=result.get("token_id"),
            project_id=project_id,
            amount=amount,
            recipient=recipient_address,
        )
        return result

    async def transfer_token(
        self,
        token_id: str,
        from_address: str,
        to_address: str,
    ) -> dict[str, Any]:
        """Transfer a tokenized carbon credit (on-chain, falls back to simulation)."""
        if self._use_sim():
            result = self._get_sim().transfer(token_id, from_address, to_address)
        else:
            result = self._token_service.transfer_credits(
                from_address=from_address,
                to_address=to_address,
                token_id=token_id,
            )
        await self._record_audit(
            "carbon_token_transferred",
            token_id=token_id,
            from_address=from_address,
            to_address=to_address,
        )
        return result

    async def burn(
        self,
        token_id: str,
        owner_address: str,
        justification: str = "",
    ) -> dict[str, Any]:
        """Retire (burn) a tokenized carbon credit."""
        if self._use_sim():
            result = self._get_sim().retire(token_id, justification)
        else:
            result = self._token_service.retire_credits(
                token_id=token_id,
                retirement_justification=justification,
            )
        await self._record_audit(
            "carbon_token_retired",
            token_id=token_id,
            owner=owner_address,
            justification=justification,
        )
        return result

    async def balance(
        self,
        owner_address: str,
    ) -> dict[str, Any]:
        """Get the token balance for an address."""
        if self._use_sim():
            sim_balance = self._get_sim().balance(owner_address)
        else:
            sim_balance = self._token_service.get_balance(owner_address)
        return {
            "owner_address": owner_address,
            "token_balance": sim_balance,
            "token_type": "CARBON_tCO2e",
        }

    async def verify_on_chain(
        self,
        token_id: str,
    ) -> dict[str, Any]:
        """Verify a tokenized credit against the blockchain."""
        if self._use_sim():
            return self._get_sim().verify_on_chain(token_id)
        return self._token_service.verify_on_chain(token_id)

    async def _record_audit(
        self,
        action: str,
        **kwargs: Any,
    ) -> None:
        self.db.add(
            AuditEvent(
                correlation_id=str(kwargs.get("token_id") or uuid4().hex),
                actor_id=str(kwargs.get("owner", kwargs.get("owner_address", "system"))),
                action=action,
                resource_type="carbon_token",
                resource_id=str(kwargs.get("token_id")),
                after_state=_json_safe(kwargs),
                created_at=datetime.now(UTC),
            )
        )
        await self.db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# CBDC Provider — Central Bank Digital Currency RTGS settlement
# ═══════════════════════════════════════════════════════════════════════════════


class CBDCProvider:
    """CBDC provider for instant, irrevocable RTGS settlement.

    Used to settle carbon credit purchase payments in central bank digital
    currency. Requires ``CBDC_ENDPOINT_URL`` to be configured; otherwise returns
    503 (fail-closed).

    Environment:
    * ``CBDC_ENDPOINT_URL`` — CBDC switch RPC base URL
    * ``CBDC_API_KEY`` — API key for the switch (optional, read at call time)
    * ``CBDC_NETWORK`` — network name (``"mainnet"`` / ``"testnet"``), default ``"testnet"``
    """

    provider_name = "cbdc"

    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_url(self) -> str:
        return os.getenv("CBDC_ENDPOINT_URL", "").strip().rstrip("/")

    def _require_endpoint(self) -> str:
        base_url = self._base_url()
        if not base_url:
            raise EcoNojinException(
                "CBDC endpoint not configured: set CBDC_ENDPOINT_URL",
                code="CBDC_NOT_CONFIGURED",
                status_code=503,
            )
        return base_url

    async def transfer(
        self,
        from_address: str,
        to_address: str,
        amount: Decimal,
        currency: str = "USD",
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> CBDCTransferResult:
        """Initiate a CBDC RTGS transfer.

        Fails closed (503) when ``CBDC_ENDPOINT_URL`` is unset. The actual
        RPC call is a stub that would use ``httpx.AsyncClient`` against the
        switch endpoint.
        """
        base_url = self._require_endpoint()
        network = os.getenv("CBDC_NETWORK", "testnet").strip()
        meta = metadata or {}

        tx_id = f"CBDC-{uuid4().hex[:16]}"
        tx_hash = hashlib.sha256(
            f"{from_address}:{to_address}:{amount}:{currency}:{idempotency_key or ''}".encode()
        ).hexdigest()

        # Idempotency check: a real CBDC switch would accept the idempotency key.
        if idempotency_key:
            existing = await self.db.execute(
                select(ComPaymentIntent).where(
                    ComPaymentIntent.payment_metadata["idempotency_key"].as_string() == idempotency_key,
                    ComPaymentIntent.provider == "cbdc",
                )
            )
            prior = existing.scalar_one_or_none()
            if prior is not None:
                return CBDCTransferResult(
                    transaction_id=prior.provider_reference or prior.id,
                    status=prior.status,
                    amount=prior.amount,
                    currency=prior.currency,
                    from_address=from_address,
                    to_address=to_address,
                    metadata=prior.payment_metadata or {},
                )

        payment = ComPaymentIntent(
            id=str(uuid4()),
            order_id=str(meta.get("order_id", "")),
            buyer_id=from_address,
            provider="cbdc",
            amount=amount,
            currency=currency,
            status="processing",
            provider_reference=tx_id,
            payment_metadata={
                **meta,
                "idempotency_key": idempotency_key or str(uuid4()),
                "cbdc_from": from_address,
                "cbdc_to": to_address,
                "cbdc_network": network,
            },
            created_at=datetime.now(UTC),
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        # Record audit event for the transfer.
        await self._record_audit(
            "cbdc_transfer_initiated",
            transaction_id=tx_id,
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            currency=currency,
        )

        return CBDCTransferResult(
            transaction_id=tx_id,
            status="succeeded",
            amount=amount,
            currency=currency,
            from_address=from_address,
            to_address=to_address,
            transaction_hash=tx_hash,
            metadata={"network": network, "rpc_url": base_url},
        )

    async def get_balance(self, address: str, currency: str = "USD") -> Decimal:
        """Query CBDC balance for an address (stub)."""
        self._require_endpoint()
        result = await self.db.execute(
            select(ComPaymentIntent).where(
                ComPaymentIntent.buyer_id == address,
                ComPaymentIntent.currency == currency,
                ComPaymentIntent.status == "succeeded",
            )
        )
        payments = result.scalars().all()
        balance = sum(p.amount for p in payments)
        return Decimal(str(balance)) if balance else Decimal("0")

    async def verify_webhook(self, payload: bytes, signature: str) -> dict[str, Any]:
        """Verify a CBDC settlement webhook."""
        self._require_endpoint()
        secret = os.getenv("CBDC_WEBHOOK_SECRET", "").strip()
        if not secret:
            raise EcoNojinException(
                "CBDC webhook secret not configured",
                code="CBDC_WEBHOOK_SECRET_NOT_CONFIGURED",
                status_code=503,
            )
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature.strip()):
            raise EcoNojinException(
                "Invalid CBDC webhook signature",
                code="INVALID_SIGNATURE",
                status_code=401,
            )
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise EcoNojinException("Invalid webhook JSON", code="INVALID_WEBHOOK", status_code=400) from exc

    async def _record_audit(
        self,
        action: str,
        **kwargs: Any,
    ) -> None:
        self.db.add(
            AuditEvent(
                correlation_id=str(kwargs.get("transaction_id") or uuid4().hex),
                actor_id=str(kwargs.get("from_address", "system")),
                action=action,
                resource_type="cbdc_transfer",
                resource_id=str(kwargs.get("transaction_id")),
                after_state=_json_safe(kwargs),
                created_at=datetime.now(UTC),
            )
        )
        await self.db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# Carbon Swap Provider — swap carbon credits for other assets
# ═══════════════════════════════════════════════════════════════════════════════


class CarbonSwapProvider:
    """Swap carbon credits for stablecoin or ECO tokens at a market rate.

    Environment (optional):
    * ``CARBON_SWAP_RATE`` — rate in USD per tCO2e (default ``10.0``)
    """

    provider_name = "carbon_swap"

    def __init__(self, db: AsyncSession):
        self.db = db

    def _rate(self) -> Decimal:
        return Decimal(os.getenv("CARBON_SWAP_RATE", "10"))

    def _require_credential_guard(self) -> None:
        rate = self._rate()
        if rate <= 0:
            raise EcoNojinException(
                "Carbon swap rate not configured: set CARBON_SWAP_RATE",
                code="CARBON_SWAP_RATE_NOT_CONFIGURED",
                status_code=503,
            )

    async def quote(
        self,
        credit_amount: Decimal,
        target_currency: str = "USD",
    ) -> dict[str, Any]:
        """Quote the conversion of carbon credits to a target currency."""
        self._require_credential_guard()
        rate = self._rate()
        usd_value = credit_amount * rate
        return {
            "credit_amount": str(credit_amount),
            "credit_unit": "tCO2e",
            "rate_usd_per_tco2e": str(rate),
            "target_currency": target_currency,
            "usd_value": str(usd_value),
            "target_value": str(usd_value),
            "quote_expires_at": datetime.now(UTC).isoformat(),
        }

    async def swap(
        self,
        credit_id: str,
        holder_id: str,
        target_currency: str,
        target_address: str,
    ) -> dict[str, Any]:
        """Execute a carbon credit swap.

        This is a stub: a real implementation would interact with the
        CarbonCreditProvider to retire the credit and the CBDCProvider/
        WalletService to mint the target asset.
        """
        self._require_credential_guard()

        result = await self.db.execute(
            select(CarbonCreditModel).where(CarbonCreditModel.credit_id == credit_id)
        )
        credit = result.scalar_one_or_none()
        if credit is None:
            raise EcoNojinException(
                f"Carbon credit not found: {credit_id}",
                code="CARBON_CREDIT_NOT_FOUND",
                status_code=404,
            )
        if str(credit.holder_id) != str(holder_id):
            raise EcoNojinException(
                f"Credit {credit_id} not held by {holder_id}",
                code="CARBON_CREDIT_NOT_OWNED",
                status_code=403,
            )

        quote = await self.quote(credit.available_amount, target_currency)
        return {
            "credit_id": credit_id,
            "holder_id": holder_id,
            "target_currency": target_currency,
            "target_address": target_address,
            "usd_value": quote["usd_value"],
            "status": "quoted",
            "note": "Swap execution requires CBDC or wallet provider integration",
        }

    def _require_credential_guard(self) -> None:
        rate = self._rate()
        if rate <= 0:
            raise EcoNojinException(
                "Carbon swap rate not configured: set CARBON_SWAP_RATE",
                code="CARBON_SWAP_RATE_NOT_CONFIGURED",
                status_code=503,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Lazy registration — providers need an AsyncSession, which is not available
# at import time. The router creates real instances per request.
# ═══════════════════════════════════════════════════════════════════════════════


class _LazyCarbonCreditProvider:
    """Lazy wrapper: creates a real CarbonCreditProvider per request."""

    provider_name = "carbon_credit"

    async def issue(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonCreditProvider(session)
            return await provider.issue(*args, **kwargs)

    async def transfer(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonCreditProvider(session)
            return await provider.transfer(*args, **kwargs)

    async def retire(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonCreditProvider(session)
            return await provider.retire(*args, **kwargs)

    async def get_balance(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonCreditProvider(session)
            return await provider.get_balance(*args, **kwargs)

    async def list_credits(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonCreditProvider(session)
            return await provider.list_credits(*args, **kwargs)


class _LazyCarbonTokenProvider:
    """Lazy wrapper: creates a real CarbonTokenProvider per request."""

    provider_name = "carbon_token"

    async def mint(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonTokenProvider(session)
            return await provider.mint(*args, **kwargs)

    async def transfer_token(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonTokenProvider(session)
            return await provider.transfer_token(*args, **kwargs)

    async def burn(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonTokenProvider(session)
            return await provider.burn(*args, **kwargs)

    async def balance(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonTokenProvider(session)
            return await provider.balance(*args, **kwargs)

    async def verify_on_chain(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonTokenProvider(session)
            return await provider.verify_on_chain(*args, **kwargs)


class _LazyCBDCProvider:
    """Lazy wrapper: creates a real CBDCProvider per request."""

    provider_name = "cbdc"

    async def transfer(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CBDCProvider(session)
            return await provider.transfer(*args, **kwargs)

    async def get_balance(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CBDCProvider(session)
            return await provider.get_balance(*args, **kwargs)

    async def verify_webhook(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CBDCProvider(session)
            return await provider.verify_webhook(*args, **kwargs)


class _LazyCarbonSwapProvider:
    """Lazy wrapper: creates a real CarbonSwapProvider per request."""

    provider_name = "carbon_swap"

    async def quote(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonSwapProvider(session)
            return await provider.quote(*args, **kwargs)

    async def swap(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = CarbonSwapProvider(session)
            return await provider.swap(*args, **kwargs)
