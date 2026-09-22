"""Carbon credit integration module.

Provides bridge between off-chain CarbonService and on-chain
CarbonTokenService with double-counting prevention.
"""

from services.carbon.integration.credit_bridge import (
    BridgeStatus,
    CreditBridge,
    DoubleCountingRisk,
    get_credit_bridge,
    set_credit_bridge,
)

__all__ = [
    "BridgeStatus",
    "CreditBridge",
    "DoubleCountingRisk",
    "get_credit_bridge",
    "set_credit_bridge",
]
