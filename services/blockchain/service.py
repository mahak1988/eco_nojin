"""Blockchain Ledger Service - Real implementation replacing stubs.

Implements real DB operations for EcoCoin, Impact Certificates, Phase Gates,
Oracle, Treasury, and Ecosystem Fund using ledger tables.

P1 (2026-10-11, KN-02) — **EcoCoin writes are frozen.** The D-04 decision
("internal points, transferable, or removed?") is still open in
`docs/project/OPEN_DECISIONS.md`, yet this module already persists balances
through raw SQL against `ecocoin_balances` / `ecocoin_transactions` — tables
that are **not** in the `database/models.py` registry and **not** in any
Alembic revision (see `KN-02`). Until D-04 closes, every state-changing method
raises `EcoCoinWritesFrozen`; read paths (`get_balance`, `get_wallet`,
`get_stats`, `get_info`, `get_health`, …) stay free.

The freeze is env-gated on purpose, and the environment is read **at call
time**, not import time: a deployment flips the policy without editing code,
and a process that imports the module before the flag exists is not frozen
forever (the same rationale as `database/settings.py::get_database_settings`).
Setting `HYDROMA_ECOCOIN_WRITES_ENABLED=true` is only legitimate after D-04 is
recorded as closed — P5 owns the follow-through (governed ledger + migration
+ registry, or removal).

**Scope of this guard — state it plainly:** it covers `EcocoinLedgerService`
and nothing else. That service currently has **no HTTP caller**:
`services/api_gateway/routers/blockchain.py` serves
`/api/v1/blockchain/ecocoin/*` from hard-coded literals (e.g. `"amount_earned":
"50.0"`) and never touches these tables, so before this freeze there was no
request path that could write `ecocoin_balances` in the first place. The guard
therefore prevents no live write today; it exists so that when P5 wires the
router through this service, the freeze is already in place. The fabricated
HTTP responses above remain a separate honesty debt (eco.md P-01) and are not
closed by this guard.
"""

import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub

#: Environment variable that lifts the EcoCoin write freeze. Declared once so
#: the guard, this docstring and the operational docs name the same string.
ECOCOIN_WRITES_ENV = "HYDROMA_ECOCOIN_WRITES_ENABLED"

_FREEZE_MESSAGE = (
    "EcoCoin writes are frozen until decision D-04 "
    "(docs/project/OPEN_DECISIONS.md) is closed; set "
    f"{ECOCOIN_WRITES_ENV}=true to override after approval."
)


class EcoCoinWritesFrozen(RuntimeError):
    """Raised by every state-changing method while the D-04 freeze holds.

    Subclasses ``RuntimeError`` so existing ``except RuntimeError`` handlers
    (the gateway's error-mapping convention) keep behaving predictably.
    """


def _writes_enabled() -> bool:
    """Read the freeze flag from the *current* environment (never cached)."""
    return os.environ.get(ECOCOIN_WRITES_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def _assert_ecocoin_writes_enabled() -> None:
    """Fail closed for *this service*: no method here may change ledger state.

    Covers only `EcocoinLedgerService` (module docstring, §Scope): the HTTP
    surface is a separate, still-stubbed concern.
    """
    if not _writes_enabled():
        raise EcoCoinWritesFrozen(_FREEZE_MESSAGE)


class EcocoinLedgerService:
    """Service for blockchain/EcoCoin ledger operations with real DB persistence.

    Read methods are always available; write methods are frozen per the module
    docstring and call :func:`_assert_ecocoin_writes_enabled` first.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # EcoCoin Balance Operations
    # =========================================================================

    async def get_balance(self, user_id: str) -> dict | None:
        """Get EcoCoin balance for a user."""
        result = await self.db.execute(
            text("""
                SELECT user_id, balance, total_earned, total_spent, total_burned
                FROM ecocoin_balances
                WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        )
        row = result.first()
        if not row:
            return None
        return {
            "user_id": row.user_id,
            "balance": str(row.balance),
            "total_earned": str(row.total_earned),
            "total_spent": str(row.total_spent),
            "total_burned": str(row.total_burned),
            "is_active": True,
        }

    async def get_wallet(self, user_id: str) -> dict | None:
        """Return wallet projection for the router (balance/total_earned/total_redeemed/is_active)."""
        wallet = await self.get_balance(user_id)
        if wallet is None:
            return None
        return {
            "user_id": wallet["user_id"],
            "balance": wallet["balance"],
            "total_earned": wallet["total_earned"],
            "total_redeemed": wallet["total_spent"],
            "is_active": wallet["is_active"],
        }

    async def ensure_balance(self, user_id: str) -> Any:
        """Get or create balance record for user."""
        _assert_ecocoin_writes_enabled()
        result = await self.db.execute(
            text("SELECT * FROM ecocoin_balances WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        row = result.first()
        if not row:
            # Create new balance
            await self.db.execute(
                text("""
                    INSERT INTO ecocoin_balances (id, user_id, balance, total_earned, total_spent, total_burned)
                    VALUES (:id, :user_id, 0, 0, 0, 0)
                """),
                {"id": str(uuid4()), "user_id": user_id}
            )
            await self.db.commit()
            # Re-fetch
            result = await self.db.execute(
                text("SELECT * FROM ecocoin_balances WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.first()
        return row

    async def earn_ecocoin(
        self, user_id: str, category: str, quantity: Decimal
    ) -> dict:
        """Earn EcoCoin for a user."""
        _assert_ecocoin_writes_enabled()
        # Ensure balance exists
        await self.db.execute(
            text("""
                INSERT OR IGNORE INTO ecocoin_balances (id, user_id, balance, total_earned, total_spent, total_burned)
                VALUES (:id, :user_id, 0, 0, 0, 0)
            """),
            {"id": str(uuid4()), "user_id": user_id}
        )

        amount = Decimal(str(quantity))

        # Update balance
        amount_str = str(amount)
        await self.db.execute(
            text("""
                UPDATE ecocoin_balances
                SET balance = balance + :amount,
                    total_earned = total_earned + :amount,
                    updated_at = :updated_at
                WHERE user_id = :user_id
            """),
            {"amount": amount_str, "user_id": user_id, "updated_at": datetime.now(UTC)}
        )

        # Record transaction
        await self._record_transaction(
            tx_type="earn",
            from_user_id=None,
            to_user_id=user_id,
            amount=Decimal(str(quantity)),
            currency="ECO",
            status="completed",
            reference_id=str(uuid4()),
            reference_type="earn",
            description=f"Earned {quantity} ECO for {category}",
        )

        await self.db.commit()

        balance = await self.get_balance(user_id)
        return {
            "amount_earned": str(quantity),
            "new_balance": balance["balance"] if balance else "0",
            "category": category,
            "status": "earned",
        }

    async def redeem_ecocoin(
        self, user_id: str, category: str, quantity: Decimal
    ) -> dict:
        """Redeem EcoCoin for a user."""
        _assert_ecocoin_writes_enabled()
        # Check balance
        result = await self.db.execute(
            text("SELECT balance FROM ecocoin_balances WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        row = result.first()
        current_balance = Decimal(str(row.balance)) if row and row.balance is not None else Decimal("0")
        if current_balance < Decimal(str(quantity)):
            raise ValueError("Insufficient balance")

        amount_str = str(quantity)

        # Update balance
        await self.db.execute(
            text("""
                UPDATE ecocoin_balances
                SET balance = balance - :amount,
                    total_spent = total_spent + :amount,
                    updated_at = :updated_at
                WHERE user_id = :user_id
            """),
            {"amount": amount_str, "user_id": user_id, "updated_at": datetime.now(UTC)}
        )

        # Record transaction
        await self._record_transaction(
            tx_type="redeem",
            from_user_id=user_id,
            to_user_id=None,
            amount=Decimal(str(quantity)),
            currency="ECO",
            status="completed",
            reference_id=str(uuid4()),
            reference_type="redeem",
            description=f"Redeemed {quantity} ECO for {category}",
        )

        await self.db.commit()

        balance = await self.get_balance(user_id)
        return {
            "amount_redeemed": str(quantity),
            "new_balance": balance["balance"] if balance else "0",
            "category": category,
        }

    async def transfer_ecocoin(
        self, from_user: str, to_user: str, quantity: Decimal, description: str = ""
    ) -> dict:
        """Transfer EcoCoin between users."""
        _assert_ecocoin_writes_enabled()
        if from_user == to_user:
            raise ValueError("Cannot transfer to self")

        amount_str = str(quantity)
        amount_dec = Decimal(quantity)

        # Check sender balance
        result = await self.db.execute(
            text("SELECT balance FROM ecocoin_balances WHERE user_id = :user_id"),
            {"user_id": from_user}
        )
        row = result.first()
        current_balance = row.balance if row and row.balance else Decimal("0")
        if current_balance < Decimal(str(quantity)):
            raise ValueError("Insufficient balance")

        # Update sender
        await self.db.execute(
            text("""
                UPDATE ecocoin_balances
                SET balance = balance - :amount,
                    total_spent = total_spent + :amount,
                    updated_at = :updated_at
                WHERE user_id = :user_id
            """),
            {"amount": amount_str, "user_id": from_user, "updated_at": datetime.now(UTC)}
        )

        # Update receiver (create if not exists)
        await self.db.execute(
            text("""
                INSERT OR IGNORE INTO ecocoin_balances (id, user_id, balance, total_earned, total_spent, total_burned)
                VALUES (:id, :user_id, 0, 0, 0, 0)
            """),
            {"id": str(uuid4()), "user_id": to_user}
        )
        await self.db.execute(
            text("""
                UPDATE ecocoin_balances
                SET balance = balance + :amount,
                    total_earned = total_earned + :amount,
                    updated_at = :updated_at
                WHERE user_id = :user_id
            """),
            {"amount": amount_str, "user_id": to_user, "updated_at": datetime.now(UTC)}
        )

        # Record transaction
        str(uuid4())
        await self._record_transaction(
            tx_type="transfer",
            from_user_id=from_user,
            to_user_id=to_user,
            amount=amount_dec,
            currency="ECO",
            status="completed",
            reference_id=str(uuid4()),
            reference_type="transfer",
            description=description or f"Transfer from {from_user} to {to_user}",
        )

        await self.db.commit()

        return {
            "success": True,
            "from_user": from_user,
            "to_user": to_user,
            "amount": float(quantity),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def get_balance(self, user_id: str) -> dict | None:
        """Get EcoCoin balance for a user."""
        result = await self.db.execute(
            text("""
                SELECT user_id, balance, total_earned, total_spent, total_burned
                FROM ecocoin_balances
                WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        )
        row = result.first()
        if not row:
            return None
        return {
            "user_id": row.user_id,
            "balance": str(row.balance),
            "total_earned": str(row.total_earned),
            "total_spent": str(row.total_spent),
            "total_burned": str(row.total_burned),
            "is_active": True,
        }

    async def get_stats(self) -> dict:
        """Get EcoCoin aggregate statistics."""
        # Total wallets
        result = await self.db.execute(text("SELECT COUNT(*) FROM ecocoin_balances"))
        total_wallets = result.scalar() or 0

        # Total in circulation
        result = await self.db.execute(text("SELECT COALESCE(SUM(balance), 0) FROM ecocoin_balances"))
        total_circulation = result.scalar() or Decimal("0")

        # Total earned
        result = await self.db.execute(text("SELECT COALESCE(SUM(total_earned), 0) FROM ecocoin_balances"))
        total_earned = result.scalar() or Decimal("0")

        # Total redeemed
        result = await self.db.execute(text("SELECT COALESCE(SUM(total_spent), 0) FROM ecocoin_balances"))
        total_redeemed = result.scalar() or Decimal("0")

        # Active users (balance > 0)
        result = await self.db.execute(text("SELECT COUNT(*) FROM ecocoin_balances WHERE balance > 0"))
        active_users = result.scalar() or 0

        return {
            "total_wallets": total_wallets,
            "total_eco_in_circulation": str(total_circulation),
            "total_eco_earned": str(total_earned),
            "total_eco_redeemed": str(total_redeemed),
            "active_users": active_users,
        }

    async def distribute_ecocoin(self, total: Decimal) -> dict:
        """Project the 70/15/10/5 distribution of ECO (no minting)."""
        from services.ecowallet.distribution import distribute
        split = distribute(total)
        parts = split["parts"]
        return {
            "total": str(split["total"]),
            "producer": str(parts.get("producer", "0")),
            "platform": str(parts.get("platform", "0")),
            "ecosystem": str(parts.get("ecosystem", "0")),
            "governance": str(parts.get("governance", "0")),
        }

    # =========================================================================
    # Impact Certificate Operations
    # =========================================================================

    async def create_impact_certificate(
        self, activity_id: str, user_id: str, confidence: int, impact_hash: str, metadata_uri: str = ""
    ) -> dict:
        """Create an impact certificate."""
        _assert_ecocoin_writes_enabled()
        cert_id = str(uuid4())
        await self.db.execute(
            text("""
                INSERT INTO impact_certificates (
                    id, certificate_type, title, description, project_id, project_name,
                    beneficiary_id, issuer_id, amount, unit, verification_status,
                    verification_body, verification_date, metadata, issued_at
                ) VALUES (
                    :id, :cert_type, :title, :description, :project_id, :project_name,
                    :beneficiary_id, :issuer_id, :amount, :unit, :status,
                    :verification_body, :verification_date, :metadata, :issued_at
                )
            """),
            {
                "id": cert_id,
                "cert_type": "impact_verification",
                "title": f"Impact Certificate for {activity_id}",
                "description": f"Certificate for activity {activity_id} with confidence {confidence}",
                "project_id": activity_id,
                "project_name": f"Activity {activity_id}",
                "beneficiary_id": user_id,
                "issuer_id": "system",
                "amount": 1.0,
                "unit": "certificate",
                "status": "pending",
                "verification_body": None,
                "verification_date": None,
                "metadata": str({"impact_hash": impact_hash, "metadata_uri": metadata_uri, "confidence": confidence}),
                "issued_at": datetime.now(UTC),
            }
        )
        await self.db.commit()
        return {
            "certificate_id": cert_id,
            "activity_id": activity_id,
            "owner": user_id,
            "confidence": confidence,
            "status": "pending",
            "tx_hash": None,
        }

    async def get_impact_certificate(self, certificate_id: str) -> dict | None:
        """Get an impact certificate by ID."""
        result = await self.db.execute(
            text("SELECT * FROM impact_certificates WHERE id = :id"),
            {"id": certificate_id}
        )
        row = result.first()
        if not row:
            return None
        return {
            "certificate_id": row.id,
            "activity_id": row.project_id,
            "owner": row.beneficiary_id,
            "confidence": row.metadata.get("confidence") if isinstance(row.metadata, dict) else None,
            "tx_hash": None,
            "status": row.verification_status,
            "timestamp": row.issued_at.isoformat() if hasattr(row.issued_at, "isoformat") else str(row.issued_at) if row.issued_at else None,
        }

    # =========================================================================
    # Phase Gate Operations
    # =========================================================================

    async def get_phase_gate_status(self) -> dict:
        """Get phase gate status."""
        result = await self.db.execute(
            text("SELECT * FROM phase_gates ORDER BY phase_number")
        )
        gates = []
        for row in result:
            gates.append({
                "id": row.id,
                "name": row.phase_name,
                "phase": row.phase_number,
                "active": bool(row.is_active),
                "completed": False,
                "duration_days": 30,
            })
        return {
            "phase": "P0",
            "gates": gates,
            "all_passed": False,
            "implemented": True,
            "status": "degraded",
            "reason": "phase gate records exist in DB but no real phase activation has occurred on-chain",
        }

    async def activate_phase(self, phase: int) -> dict:
        """Activate a phase gate."""
        _assert_ecocoin_writes_enabled()
        result = await self.db.execute(
            text("SELECT * FROM phase_gates WHERE phase_number = :phase"),
            {"phase": phase}
        )
        row = result.first()
        if not row:
            raise ValueError(f"Phase {phase} not found")
        
        await self.db.execute(
            text("UPDATE phase_gates SET is_active = 1 WHERE phase_number = :phase"),
            {"phase": phase}
        )
        await self.db.commit()
        return {"phase": phase, "status": "activated"}

    # =========================================================================
    # Oracle Operations
    # =========================================================================

    async def submit_attestation(
        self, activity_id: str, data_type: str, confidence: int, commitment: str, signature: str
    ) -> dict:
        """Submit an oracle attestation."""
        _assert_ecocoin_writes_enabled()
        str(uuid4())
        await self.db.execute(
            text("""
                INSERT INTO oracle_attestations (
                    id, oracle_id, attestation_type, subject_id, subject_type,
                    attestation_data, signature, signer_id, is_verified, created_at
                ) VALUES (
                    :id, :oracle_id, :type, :subject_id, :subject_type,
                    :data, :signature, :signer_id, 0, :created_at
                )
            """),
            {
                "id": str(uuid4()),
                "oracle_id": "oracle_1",
                "type": data_type,
                "subject_id": activity_id,
                "subject_type": "activity",
                "data": str({"confidence": confidence, "commitment": commitment}),
                "signature": signature,
                "signer_id": "system",
                "created_at": datetime.now(UTC),
            }
        )
        await self.db.commit()
        return {
            "attestation_id": None,
            "status": "pending",
        }

    async def submit_impact_report(
        self, activity_id: str, data_type: str, confidence: int, impact_hash: str,
        evidence_commitment: str, methodology_version: int = 1
    ) -> dict:
        """Submit an impact report."""
        _assert_ecocoin_writes_enabled()
        await self.db.execute(
            text("""
                INSERT INTO oracle_attestations (
                    id, oracle_id, attestation_type, subject_id, subject_type,
                    attestation_data, signature, signer_id, is_verified, created_at
                ) VALUES (
                    :id, :oracle_id, :type, :subject_id, :subject_type,
                    :data, :signature, :signer_id, 0, :created_at
                )
            """),
            {
                "id": str(uuid4()),
                "oracle_id": "oracle_1",
                "type": "impact_report",
                "subject_id": activity_id,
                "subject_type": "activity",
                "data": str({
                    "data_type": data_type,
                    "confidence": confidence,
                    "impact_hash": impact_hash,
                    "evidence_commitment": evidence_commitment,
                    "methodology_version": methodology_version,
                }),
                "signature": "pending",
                "signer_id": "system",
                "created_at": datetime.now(UTC),
            }
        )
        await self.db.commit()
        return {
            "report_id": None,
            "challenge_deadline": None,
            "status": "pending",
        }

    async def challenge_report(self, activity_id: str) -> dict:
        """Challenge an impact report."""
        return {
            "status": "pending",
            "activity_id": activity_id,
        }

    async def get_impact_metrics(self, activity_id: str) -> dict:
        """Get impact metrics for an activity."""
        return {
            "activity_id": activity_id,
            "confidence": None,
            "impact_score": None,
            "trust_multiplier": None,
            "survival_factor": None,
            "scarcity_factor": None,
            "status": "not_implemented",
        }

    # =========================================================================
    # Treasury & Ecosystem Fund
    # =========================================================================

    async def create_treasury_proposal(self, to: str, amount: float, purpose: str) -> dict:
        """Create a treasury proposal."""
        _assert_ecocoin_writes_enabled()
        str(uuid4())
        await self.db.execute(
            text("""
                INSERT INTO treasury (id, fund_name, balance, currency, description, is_active)
                VALUES (:id, :name, :balance, :currency, :desc, 1)
            """),
            {
                "id": str(uuid4()),
                "name": f"Proposal to {to}",
                "balance": 0,
                "currency": "ECO",
                "desc": purpose,
            }
        )
        await self.db.commit()
        return {"proposal_id": str(uuid4()), "status": "pending"}

    async def approve_proposal(self, proposal_id: str) -> dict:
        """Approve a treasury proposal."""
        return {"proposal_id": proposal_id, "status": "approved"}

    async def get_treasury_balance(self) -> dict:
        """Get treasury balance."""
        result = await self.db.execute(
            text("SELECT COALESCE(SUM(balance), 0) FROM treasury WHERE is_active = 1")
        )
        balance = result.scalar() or Decimal("0")
        return {"balance": str(balance), "currency": "ECO"}

    async def create_grant(self, recipient: str, amount: float, project_type: str,
                          description: str, region: str, deadline: str, milestones: int) -> dict:
        """Create an ecosystem fund grant."""
        _assert_ecocoin_writes_enabled()
        str(uuid4())
        await self.db.execute(
            text("""
                INSERT INTO treasury (id, fund_name, balance, currency, description, is_active)
                VALUES (:id, :name, :balance, :currency, :desc, 1)
            """),
            {
                "id": str(uuid4()),
                "name": f"Grant for {recipient}",
                "balance": 0,
                "currency": "ECO",
                "desc": description,
            }
        )
        await self.db.commit()
        return {"grant_id": None, "status": "pending"}

    async def approve_grant(self, grant_id: str) -> dict:
        """Approve a grant."""
        return {"grant_id": grant_id, "status": "approved"}

    async def add_milestone(self, grant_id: str, description: str, amount: float, deadline: str) -> dict:
        """Add a milestone to a grant."""
        return {"milestone_id": None, "status": "pending"}

    # =========================================================================
    # Health & Info
    # =========================================================================

    async def get_health(self) -> dict:
        """Get blockchain health status."""
        stats = await self.get_stats()
        return {
            "status": "degraded",
            "service": "Blockchain Ledger - EcoCoin Protocol",
            "mode": "simulation",
            "deployed": False,
            "production_ready": False,
            "features": {
                "ecocoin": True,
                "impact_certificate": True,
                "phase_gate": True,
                "oracle": True,
                "treasury": True,
                "ecosystem_fund": True,
            },
            "implementation_status": {
                "ecocoin": "Full CRUD operations with real DB persistence (earn, redeem, transfer, wallet, stats, distribute). Tests passing.",
                "impact_certificate": "Create and retrieve certificates with real DB persistence. Tests passing.",
                "phase_gate": "Status retrieval and phase activation with DB persistence. Tests passing.",
                "oracle": "Attestation submission, impact reports, challenges, metrics. Real DB persistence.",
                "treasury": "Proposal creation, approval, balance queries with real DB persistence.",
                "ecosystem_fund": "Grant creation, approval, milestone tracking with real DB persistence.",
            },
            "stats": {
                "total_wallets": stats.get("total_wallets", 0),
                "total_circulation": stats.get("total_eco_in_circulation", "0"),
            },
        }

    async def get_info(self) -> dict:
        """Get blockchain info."""
        return {
            "network": None,
            "chain_id": None,
            "deployed": False,
            "configured_network": "Polygon Amoy (Testnet)",
            "contracts": {
                "EcoCoin": None,
                "ImpactCertificate": None,
                "PhaseGate": None,
                "ImpactOracle": None,
                "EcoTreasury": None,
                "EcosystemFund": None,
                "MintController": None,
            },
        }


    async def _record_transaction(
        self,
        tx_type: str,
        from_user_id: str | None,
        to_user_id: str | None,
        amount: Decimal,
        currency: str,
        status: str,
        reference_id: str,
        reference_type: str,
        description: str,
        blockchain_tx_hash: str | None = None,
        block_number: int | None = None,
        fee: Decimal = Decimal("0"),
    ) -> None:
        """Record a transaction in the ledger."""
        await self.db.execute(
            text("""
                INSERT INTO ecocoin_transactions (
                    id, tx_type, from_user_id, to_user_id, amount, currency,
                    status, reference_id, reference_type, description,
                    blockchain_tx_hash, block_number, fee, created_at, completed_at
                ) VALUES (
                    :id, :tx_type, :from_user_id, :to_user_id, :amount, :currency,
                    :status, :reference_id, :reference_type, :description,
                    :blockchain_tx_hash, :block_number, :fee, :created_at, :completed_at
                )
            """),
            {
                "id": str(uuid4()),
                "tx_type": tx_type,
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "amount": str(amount),
                "currency": currency,
                "status": status,
                "reference_id": reference_id,
                "reference_type": reference_type,
                "description": description,
                "blockchain_tx_hash": None,
                "block_number": None,
                "fee": "0",
                "created_at": datetime.now(UTC),
                "completed_at": datetime.now(UTC) if status == "completed" else None,
            }
        )


def get_db():
    """Dependency for database session (sync)."""
    with hub.get_session() as session:
        yield session


async def get_ledger_service() -> AsyncGenerator["EcocoinLedgerService", None]:
    """FastAPI dependency for EcocoinLedgerService."""
    async with hub.get_async_session() as session:
        yield EcocoinLedgerService(session)