"""
Web3 integration for Eco Nojin blockchain layer.

This module EXTENDS the existing blockchain module without modifying it.
It provides real blockchain connectivity (Polygon) while the existing
carbon_registry.py continues to work as-is.

Usage:
    from services.business_modules.blockchain.web3_integration import get_web3
    
    w3 = get_web3()
    balance = w3.eth.get_balance(address)
"""
import os

try:
    from web3 import Web3
except ImportError:
    raise ImportError("web3 is required. Install with: pip install web3")


_web3: Web3 | None = None


def get_web3(network: str = "polygon_amoy") -> Web3:
    """Get Web3 instance for the specified network."""
    global _web3

    if _web3 is not None:
        return _web3

    rpc_urls = {
        "polygon_amoy": os.getenv(
            "POLYGON_AMOY_RPC_URL",
            "https://rpc-amoy.polygon.technology"
        ),
        "polygon_mainnet": os.getenv(
            "POLYGON_RPC_URL",
            "https://polygon-rpc.com"
        ),
        "os.environ.get('HOST', 'localhost')": "http://os.environ.get('HOST', '127.0.0.1'):8545",
    }

    rpc_url = rpc_urls.get(network, rpc_urls["polygon_amoy"])
    _web3 = Web3(Web3.HTTPProvider(rpc_url))

    if not _web3.is_connected():
        raise ConnectionError(f"Cannot connect to {network} at {rpc_url}")

    return _web3


def get_wallet_address() -> str | None:
    """Get the configured wallet address."""
    return os.getenv("BLOCKCHAIN_WALLET_ADDRESS")


def get_gas_price_gwei() -> float:
    """Get current gas price in Gwei."""
    w3 = get_web3()
    return w3.from_wei(w3.eth.gas_price, 'gwei')


def sign_and_send(tx: dict, private_key: str | None = None) -> str:
    """Sign and send a transaction."""
    w3 = get_web3()
    key = private_key or os.getenv("BLOCKCHAIN_PRIVATE_KEY")

    if not key:
        raise ValueError("BLOCKCHAIN_PRIVATE_KEY not set")

    signed = w3.eth.account.sign_transaction(tx, private_key=key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()
