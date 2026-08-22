"""Core blockchain ledger interface.

Provides low-level blockchain operations.
"""

from typing import Any

from web3 import Web3
from web3.contract import Contract

from .web3_provider import get_web3_provider


class BlockchainLedger:
    """Core blockchain ledger."""

    def __init__(self):
        self.provider = get_web3_provider()
        self.w3: Web3 = self.provider.connect()
        self.contracts: dict[str, Contract] = {}

    def deploy_contract(self, contract_name: str, abi: list, bytecode: str) -> Contract:
        """Deploy a smart contract."""
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        tx_hash = contract.constructor().transact(
            {
                "from": self.provider.get_accounts()[0],
                "gas": 5000000,
            }
        )
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        deployed_contract = self.w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

        self.contracts[contract_name] = deployed_contract
        return deployed_contract

    def get_contract(self, name: str) -> Contract | None:
        """Get deployed contract by name."""
        return self.contracts.get(name)

    def get_block_info(self, block_number: int = None) -> dict[str, Any]:
        """Get block information."""
        if block_number is None:
            block_number = self.w3.eth.block_number

        block = self.w3.eth.get_block(block_number)
        return {
            "number": block.number,
            "timestamp": block.timestamp,
            "hash": block.hash.hex(),
            "transactions": len(block.transactions),
        }

    def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        """Get transaction details."""
        tx = self.w3.eth.get_transaction(tx_hash)
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)

        return {
            "hash": tx.hash.hex(),
            "from": tx["from"],
            "to": tx["to"],
            "value": tx.value,
            "gas_used": receipt.gasUsed,
            "status": receipt.status,
            "block_number": receipt.blockNumber,
        }


# Singleton
_ledger: BlockchainLedger | None = None


def get_ledger() -> BlockchainLedger:
    """Get singleton ledger."""
    global _ledger
    if _ledger is None:
        _ledger = BlockchainLedger()
    return _ledger
