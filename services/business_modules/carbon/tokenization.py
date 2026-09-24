"""Carbon credit tokenization — on-chain ERC-20 credit management.

Integrates with:
- ``services.business_modules.blockchain.carbon_registry`` (CarbonRegistry, CarbonCredit)
- ``services.business_modules.blockchain.ledger`` (BlockchainLedger)
- ``services.business_modules.blockchain.web3_provider`` (get_web3)

Requirements (optional):
- ``pip install web3`` (already in pyproject.toml)
- A running Ethereum-compatible node or Polygon RPC endpoint

When the node/contract is unavailable, all operations fall back to
in-memory simulation with a logged warning.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from services.business_modules.blockchain.carbon_registry import (
    CarbonProject,
    CarbonRegistry,
)
from services.business_modules.blockchain.ledger import BlockchainLedger
from services.business_modules.blockchain.web3_integration import get_web3

logger = logging.getLogger(__name__)


class CreditType(StrEnum):
    VCS = "VCS"
    GOLD_STANDARD = "Gold Standard"
    CARBON_OFFSET = "Carbon Offset"
    CCS = "CCS"


class TokenStatus(StrEnum):
    ACTIVE = "active"
    RETIRED = "retired"
    TRANSFERRED = "transferred"
    FROZEN = "frozen"


@dataclass
class TokenizedCredit:
    token_id: str
    project_id: str
    amount_tonnes: float
    credit_type: CreditType
    owner_address: str
    status: TokenStatus = TokenStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    retired_at: datetime | None = None
    retirement_justification: str | None = None
    transaction_hash: str | None = None
    history: list[dict] = field(default_factory=list)


class CarbonTokenService:
    """Service for minting, transferring, and retiring tokenized carbon credits."""

    def __init__(self):
        self._registry = CarbonRegistry()
        self._ledger = BlockchainLedger()
        self._credits: dict[str, TokenizedCredit] = {}
        self._balances: dict[str, int] = {}

    def issue_credits(
        self,
        project_id: str,
        amount: float,
        credit_type: str = CreditType.VCS,
        recipient_address: str | None = None,
    ) -> dict:
        """Mint carbon credits and optionally transfer to recipient.

        Returns dict with token_id, transaction_hash, status.
        Falls back to in-memory simulation when on-chain is unavailable.
        """
        try:
            project = self._registry.get_project(project_id)
        except Exception as exc:
            logger.warning("Carbon registry unavailable, using simulation: %s", exc)
            project = CarbonProject(
                project_id=project_id,
                project_type="afforestation",
                area_hectares=100,
                status="active",
            )

        credit_type_enum = (
            CreditType(credit_type) if credit_type in CreditType.__members__ else CreditType.VCS
        )

        token_id = f"CTC-{project_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        tx_hash = None

        try:
            web3 = get_web3()
            if web3 is not None:
                tx_hash = self._ledger.deploy_contract(
                    "CarbonCredit",
                    {
                        "project_id": project_id,
                        "amount": amount,
                        "credit_type": credit_type_enum.value,
                        "recipient": recipient_address or project.project_id,
                    },
                )
        except Exception as exc:
            logger.warning("On-chain mint failed, using simulation: %s", exc)

        credit = TokenizedCredit(
            token_id=token_id,
            project_id=project_id,
            amount_tonnes=amount,
            credit_type=credit_type_enum,
            owner_address=recipient_address or project.project_id,
            transaction_hash=tx_hash,
        )
        credit.history.append(
            {
                "event": "issued",
                "timestamp": datetime.now(UTC).isoformat(),
                "amount": amount,
                "to": credit.owner_address,
                "tx_hash": tx_hash,
            }
        )
        self._credits[token_id] = credit
        self._balances[credit.owner_address] = self._balances.get(credit.owner_address, 0) + int(
            amount * 1000
        )

        return {
            "token_id": token_id,
            "transaction_hash": tx_hash,
            "status": "issued",
            "amount_tonnes": amount,
            "credit_type": credit_type_enum.value,
        }

    def transfer_credits(self, from_address: str, to_address: str, token_id: str) -> dict:
        """Transfer credits from one address to another."""
        credit = self._credits.get(token_id)
        if not credit:
            raise ValueError(f"Credit not found: {token_id}")
        if credit.owner_address != from_address:
            raise ValueError(f"Address {from_address} does not own {token_id}")
        if credit.status == TokenStatus.RETIRED.value:
            raise ValueError("Cannot transfer retired credits")

        tx_hash = None
        try:
            web3 = get_web3()
            if web3 is not None:
                tx_hash = self._ledger.get_transaction(token_id)
        except Exception as exc:
            logger.warning("On-chain transfer failed, using simulation: %s", exc)

        old_owner = credit.owner_address
        credit.owner_address = to_address
        credit.status = TokenStatus.TRANSFERRED
        credit.transaction_hash = tx_hash or credit.transaction_hash
        credit.history.append(
            {
                "event": "transferred",
                "timestamp": datetime.now(UTC).isoformat(),
                "from": old_owner,
                "to": to_address,
                "tx_hash": credit.transaction_hash,
            }
        )
        self._balances[old_owner] = self._balances.get(old_owner, 0) - int(
            credit.amount_tonnes * 1000
        )
        self._balances[to_address] = self._balances.get(to_address, 0) + int(
            credit.amount_tonnes * 1000
        )

        return {
            "token_id": token_id,
            "from": old_owner,
            "to": to_address,
            "transaction_hash": credit.transaction_hash,
            "status": "transferred",
        }

    def retire_credits(self, token_id: str, retirement_justification: str = "") -> dict:
        """Retire credits (permanent removal from circulation)."""
        credit = self._credits.get(token_id)
        if not credit:
            raise ValueError(f"Credit not found: {token_id}")
        if credit.status == TokenStatus.RETIRED:
            raise ValueError("Credits already retired")

        credit.status = TokenStatus.RETIRED
        credit.retired_at = datetime.now(UTC)
        credit.retirement_justification = retirement_justification
        self._balances[credit.owner_address] = max(
            0, self._balances.get(credit.owner_address, 0) - int(credit.amount_tonnes * 1000)
        )
        credit.history.append(
            {
                "event": "retired",
                "timestamp": datetime.now(UTC).isoformat(),
                "justification": retirement_justification,
            }
        )

        return {
            "token_id": token_id,
            "retired_at": credit.retired_at.isoformat(),
            "justification": retirement_justification,
            "status": "retired",
        }

    def get_balance(self, address: str) -> int:
        """Returns token balance (in base units) for address."""
        return self._balances.get(address, 0)

    def get_credit_history(self, token_id: str) -> list[dict]:
        """Returns full credit lifecycle history."""
        credit = self._credits.get(token_id)
        if not credit:
            raise ValueError(f"Credit not found: {token_id}")
        return credit.history

    def verify_on_chain(self, token_id: str) -> dict:
        """Returns on-chain verification data."""
        credit = self._credits.get(token_id)
        if not credit:
            raise ValueError(f"Credit not found: {token_id}")

        on_chain = False
        tx_data = None
        try:
            web3 = get_web3()
            if web3 is not None and credit.transaction_hash:
                tx_data = self._ledger.get_transaction(credit.transaction_hash)
                on_chain = tx_data is not None
        except Exception as exc:
            logger.warning("On-chain verification failed: %s", exc)

        return {
            "token_id": token_id,
            "on_chain": on_chain,
            "transaction_hash": credit.transaction_hash,
            "transaction_data": tx_data,
            "contract": "CarbonCredit.abi",
            "status": credit.status.value,
            "verified": credit.status != TokenStatus.RETIRED,
        }

    def list_credits(
        self, owner_address: str | None = None, status: str | None = None
    ) -> list[dict]:
        """List credits optionally filtered by owner or status."""
        results = []
        for credit in self._credits.values():
            if owner_address and credit.owner_address != owner_address:
                continue
            if status and credit.status.value != status:
                continue
            results.append(
                {
                    "token_id": credit.token_id,
                    "project_id": credit.project_id,
                    "amount_tonnes": credit.amount_tonnes,
                    "credit_type": credit.credit_type.value,
                    "owner": credit.owner_address,
                    "status": credit.status.value,
                    "transaction_hash": credit.transaction_hash,
                }
            )
        return results


_tokenization_service: CarbonTokenService | None = None


def get_tokenization_service() -> CarbonTokenService:
    """Return the singleton carbon tokenization service instance."""
    global _tokenization_service
    if _tokenization_service is None:
        _tokenization_service = CarbonTokenService()
    return _tokenization_service
