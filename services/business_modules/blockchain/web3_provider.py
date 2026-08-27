"""Web3 provider for blockchain interactions.

Uses EthereumTester for testing (no external dependencies).
For production, replace with:
- Infura/Alchemy (Ethereum mainnet)
- Hyperledger Fabric
- Local Ethereum node

NOTE: ``eth-tester`` is imported lazily inside :meth:`Web3Provider.connect`
so that importing this module (and therefore the whole API surface) does not
hard-require the optional blockchain-simulation dependency. The dependency is
declared in ``requirements.txt`` (Blockchain section) and installed with::

    pip install "eth-tester[py-evm]"
"""

from web3 import Web3


class Web3Provider:
    """Web3 provider with test blockchain."""

    def __init__(self):
        self.w3: Web3 | None = None
        self.accounts: list = []

    def connect(self) -> Web3:
        """Connect to test blockchain (lazy eth-tester import)."""
        try:
            from eth_tester import EthereumTester, PyEVMBackend
            from web3.providers.eth_tester import EthereumTesterProvider
        except ImportError as exc:
            raise ImportError(
                "eth-tester[py-evm] is required for the simulated blockchain. "
                "Install it with: pip install 'eth-tester[py-evm]'"
            ) from exc

        eth_tester = EthereumTester(backend=PyEVMBackend())
        provider = EthereumTesterProvider(eth_tester)
        self.w3 = Web3(provider)

        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to test blockchain")

        self.accounts = self.w3.eth.accounts
        return self.w3

    def get_accounts(self) -> list:
        """Get available test accounts."""
        if not self.accounts:
            self.connect()
        return self.accounts[:10]  # Return first 10 accounts

    def get_balance(self, address: str) -> int:
        """Get account balance in wei."""
        if not self.w3:
            self.connect()
        return self.w3.eth.get_balance(address)


# Singleton
_web3_provider: Web3Provider | None = None


def get_web3_provider() -> Web3Provider:
    """Get singleton Web3 provider."""
    global _web3_provider
    if _web3_provider is None:
        _web3_provider = Web3Provider()
    return _web3_provider
